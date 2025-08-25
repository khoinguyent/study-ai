terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# AWS Provider Configuration
provider "aws" {
  region = var.region
  
  default_tags {
    tags = local.common_tags
  }
}

# Common tags for all resources
locals {
  common_tags = {
    Name         = "${var.project_short}-${var.env}"
    Project      = var.project
    ProjectShort = var.project_short
    Environment  = var.env
    Owner        = var.project_owner
    CostCenter   = var.cost_center
    ManagedBy    = "Terraform"
    Purpose      = var.project_description
    CreationDate = timestamp()
  }
}

# --- VPC Selection ---
locals {
  # Use custom VPC if SageMaker is enabled, otherwise use default VPC
  vpc_id = var.enable_sagemaker ? aws_vpc.sagemaker[0].id : data.aws_vpc.default.id
  
  # Use custom subnets if SageMaker is enabled, otherwise use default VPC subnets
  subnet_ids = var.enable_sagemaker ? aws_subnet.private[*].id : [data.aws_subnet.default[0].id]
  
  ami_id        = var.use_arm ? data.aws_ami.ubuntu_arm.id : data.aws_ami.ubuntu_x86.id
  instance_type = var.use_arm ? var.ec2_instance_type_arm : var.ec2_instance_type_x86
  bucket_name   = "${var.project_short}-uploads-${var.env}-${var.region}"
  
  # Enhanced tags for better resource grouping
  # Note: common_tags is defined in the locals block above
}

# --- Default VPC (fallback) ---
data "aws_vpc" "default" { 
  default = true 
}

data "aws_subnet" "default" {
  count = var.enable_sagemaker ? 0 : 1
  
  vpc_id            = data.aws_vpc.default.id
  availability_zone = "${var.region}a"
}

# --- Ubuntu 22.04 AMIs for both arches ---
data "aws_ami" "ubuntu_arm" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-arm64-server-*"]
  }
}

data "aws_ami" "ubuntu_x86" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# --- SSH key generated locally by Terraform ---
resource "tls_private_key" "ssh" { algorithm = "ED25519" }

resource "local_file" "ssh_key" {
  filename        = "${path.module}/studium_key"
  content         = tls_private_key.ssh.private_key_openssh
  file_permission = "0600"
}

resource "aws_key_pair" "this" {
  key_name   = "${var.project_short}-${var.env}-key"
  public_key = tls_private_key.ssh.public_key_openssh
  tags       = local.common_tags
}

# --- Security Group ---
resource "aws_security_group" "ec2" {
  name        = "${var.project_short}-${var.env}-ec2-sg"
  description = "Security group for ${var.project} EC2 instances"
  vpc_id      = local.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allow_ssh_cidr]
    description = "SSH access"
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP access"
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-ec2-sg"
    ResourceType = "SecurityGroup"
  })
}

# --- S3 bucket (encrypted, versioned, CORS) ---
resource "aws_s3_bucket" "uploads" {
  bucket = local.bucket_name
  tags   = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-uploads-bucket"
    ResourceType = "S3Bucket"
    BucketPurpose = "UserUploads"
  })
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  cors_rule {
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["http://localhost:5173", "http://localhost:3000"]
    allowed_headers = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# --- SageMaker Infrastructure ---
# S3 bucket for SageMaker models and data
resource "aws_s3_bucket" "sagemaker" {
  count  = var.enable_sagemaker ? 1 : 0
  bucket = "${var.project_short}-sagemaker-${var.env}-${var.region}"
  tags   = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-bucket"
    ResourceType = "S3Bucket"
    BucketPurpose = "SageMakerModels"
  })
}

resource "aws_s3_bucket_versioning" "sagemaker" {
  count  = var.enable_sagemaker ? 1 : 0
  bucket = aws_s3_bucket.sagemaker[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sagemaker" {
  count  = var.enable_sagemaker ? 1 : 0
  bucket = aws_s3_bucket.sagemaker[0].id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = var.enable_kms_encryption ? "aws:kms" : "AES256"
      kms_master_key_id = var.enable_kms_encryption ? aws_kms_key.sagemaker[0].arn : null
    }
  }
}

resource "aws_s3_bucket_public_access_block" "sagemaker" {
  count                   = var.enable_sagemaker ? 1 : 0
  bucket                  = aws_s3_bucket.sagemaker[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM role for SageMaker
resource "aws_iam_role" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  name  = "${var.project_short}-${var.env}-sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-role"
    ResourceType = "IAMRole"
    Service = "SageMaker"
  })
}

# SageMaker execution policy
resource "aws_iam_role_policy" "sagemaker_execution" {
  count = var.enable_sagemaker ? 1 : 0
  name  = "${var.project_short}-${var.env}-sagemaker-execution"
  role  = aws_iam_role.sagemaker[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.sagemaker[0].arn,
          "${aws_s3_bucket.sagemaker[0].arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerVersion",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*"
        ]
        Resource = var.enable_kms_encryption ? aws_kms_key.sagemaker[0].arn : "*"
        Condition = var.enable_kms_encryption ? {
          StringEquals = {
            "kms:ViaService" = "sagemaker.${var.region}.amazonaws.com"
          }
        } : null
      }
    ]
  })
}

# Attach SageMaker full access policy
resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  count      = var.enable_sagemaker ? 1 : 0
  role       = aws_iam_role.sagemaker[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# SageMaker Domain
resource "aws_sagemaker_domain" "main" {
  count = var.enable_sagemaker ? 1 : 0
  
  domain_name = "${var.project_short}-${var.env}-domain"
  auth_mode   = "IAM"
  vpc_id      = local.vpc_id
  subnet_ids  = local.subnet_ids

  default_user_settings {
    execution_role = aws_iam_role.sagemaker[0].arn
    
    jupyter_server_app_settings {
      default_resource_spec {
        instance_type       = var.sagemaker_instance_type
        sagemaker_image_arn = var.sagemaker_image_arn
      }
    }
    
    kernel_gateway_app_settings {
      default_resource_spec {
        instance_type       = var.sagemaker_instance_type
        sagemaker_image_arn = var.sagemaker_image_arn
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-domain"
    ResourceType = "SageMakerDomain"
  })
}

# SageMaker User Profile
resource "aws_sagemaker_user_profile" "ollama_user" {
  count        = var.enable_sagemaker ? 1 : 0
  domain_id    = aws_sagemaker_domain.main[0].id
  user_profile_name = "${var.project_short}-${var.env}-ollama-user"

  user_settings {
    execution_role = aws_iam_role.sagemaker[0].arn
    
    jupyter_server_app_settings {
      default_resource_spec {
        instance_type       = var.sagemaker_instance_type
        sagemaker_image_arn = var.sagemaker_image_arn
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-ollama-user-profile"
    ResourceType = "SageMakerUserProfile"
  })
}

# SageMaker Model
resource "aws_sagemaker_model" "ollama_model" {
  count = var.enable_sagemaker ? 1 : 0
  
  name               = "${var.project_short}-${var.env}-ollama-model"
  execution_role_arn = aws_iam_role.sagemaker[0].arn

  primary_container {
    image = var.ollama_image_uri
    mode  = "SingleModel"
    
    environment = {
      SAGEMAKER_PROGRAM = "inference.py"
      SAGEMAKER_SUBMIT_DIRECTORY = "/opt/ml/code"
      SAGEMAKER_CONTAINER_LOG_LEVEL = "20"
      SAGEMAKER_REGION = var.region
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-ollama-model"
    ResourceType = "SageMakerModel"
  })
}

# SageMaker Endpoint Configuration
resource "aws_sagemaker_endpoint_configuration" "ollama_endpoint" {
  count = var.enable_sagemaker ? 1 : 0
  
  name = "${var.project_short}-${var.env}-ollama-endpoint-config"

  production_variants {
    variant_name           = "default"
    model_name            = aws_sagemaker_model.ollama_model[0].name
    instance_type         = var.sagemaker_endpoint_instance_type
    initial_instance_count = var.sagemaker_endpoint_initial_count
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-ollama-endpoint-config"
    ResourceType = "SageMakerEndpointConfiguration"
  })
}

# SageMaker Endpoint
resource "aws_sagemaker_endpoint" "ollama_endpoint" {
  count = var.enable_sagemaker ? 1 : 0
  
  name                 = "${var.project_short}-${var.env}-ollama-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.ollama_endpoint[0].name

  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-ollama-endpoint"
    ResourceType = "SageMakerEndpoint"
  })
}

# --- IAM: EC2 role with S3 RW on that bucket ---
data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name               = "${var.project_short}-${var.env}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
  tags               = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-ec2-role"
    ResourceType = "IAMRole"
    Service = "EC2"
  })
}

data "aws_iam_policy_document" "s3_rw_bucket" {
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.uploads.arn, "${aws_s3_bucket.uploads.arn}/*"]
  }
}

resource "aws_iam_policy" "s3_rw_bucket" {
  name        = "${var.project_short}-${var.env}-s3-rw"
  description = "EC2 RW access to ${var.project} uploads bucket"
  policy      = data.aws_iam_policy_document.s3_rw_bucket.json
  tags        = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-s3-rw-policy"
    ResourceType = "IAMPolicy"
  })
}

resource "aws_iam_role_policy_attachment" "ec2_attach_s3" {
  role       = aws_iam_role.ec2.name
  policy_arn = aws_iam_policy.s3_rw_bucket.arn
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project_short}-${var.env}-instance-profile"
  role = aws_iam_role.ec2.name
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-instance-profile"
    ResourceType = "IAMInstanceProfile"
  })
}

# --- EC2 instance (ARM or x86 based on use_arm) ---
resource "aws_instance" "app" {
  ami                    = local.ami_id
  instance_type          = local.instance_type
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name               = aws_key_pair.this.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
  user_data              = file("${path.module}/user_data.sh")
  subnet_id              = var.enable_sagemaker ? aws_subnet.private[0].id : data.aws_subnet.default[0].id

  tags = merge(local.common_tags, { 
    Name = "${var.project_short}-${var.env}-app-instance"
    ResourceType = "EC2Instance"
    InstancePurpose = "StudyAIApplication"
  })
}
