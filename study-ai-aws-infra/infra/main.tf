terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws   = { source = "hashicorp/aws", version = ">= 5.49.0" }
    tls   = { source = "hashicorp/tls", version = ">= 4.0.5" }
    local = { source = "hashicorp/local", version = ">= 2.4.0" }
  }
}

provider "aws" { region = var.region }

# --- Default VPC ---
data "aws_vpc" "default" { default = true }

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

locals {
  ami_id        = var.use_arm ? data.aws_ami.ubuntu_arm.id : data.aws_ami.ubuntu_x86.id
  instance_type = var.use_arm ? var.ec2_instance_type_arm : var.ec2_instance_type_x86
  bucket_name   = "${var.project}-uploads-${var.env}-${var.region}"
}

# --- SSH key generated locally by Terraform ---
resource "tls_private_key" "ssh" { algorithm = "ED25519" }

resource "local_file" "ssh_key" {
  filename        = "${path.module}/studyai_key"
  content         = tls_private_key.ssh.private_key_openssh
  file_permission = "0600"
}

resource "aws_key_pair" "this" {
  key_name   = "${var.project}-${var.env}-key"
  public_key = tls_private_key.ssh.public_key_openssh
  tags       = var.tags
}

# --- Security Group ---
resource "aws_security_group" "ec2" {
  name        = "${var.project}-${var.env}-sg"
  description = "Allow SSH(22), HTTP(80), HTTPS(443)"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allow_ssh_cidr]
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

# --- S3 bucket (encrypted, versioned, CORS) ---
resource "aws_s3_bucket" "uploads" {
  bucket = local.bucket_name
  tags   = var.tags
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
  name               = "${var.project}-${var.env}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "s3_rw_bucket" {
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.uploads.arn, "${aws_s3_bucket.uploads.arn}/*"]
  }
}

resource "aws_iam_policy" "s3_rw_bucket" {
  name        = "${var.project}-${var.env}-s3-rw"
  description = "EC2 RW to uploads bucket"
  policy      = data.aws_iam_policy_document.s3_rw_bucket.json
}

resource "aws_iam_role_policy_attachment" "ec2_attach_s3" {
  role       = aws_iam_role.ec2.name
  policy_arn = aws_iam_policy.s3_rw_bucket.arn
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project}-${var.env}-instance-profile"
  role = aws_iam_role.ec2.name
}

# --- EC2 instance (ARM or x86 based on use_arm) ---
resource "aws_instance" "app" {
  ami                    = local.ami_id
  instance_type          = local.instance_type
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name               = aws_key_pair.this.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
  user_data              = file("${path.module}/user_data.sh")

  tags = merge(var.tags, { Name = "${var.project}-${var.env}-app" })
}

/* SageMaker omitted for clarity; add later if needed */
