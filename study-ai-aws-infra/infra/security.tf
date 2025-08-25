# Security Configuration for SageMaker Infrastructure
# This file contains all security-related resources and configurations

# --- VPC Configuration ---
resource "aws_vpc" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  cidr_block           = var.vpc_cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-vpc"
    ResourceType = "VPC"
    Purpose = "SageMaker secure VPC"
  })
}

# --- Internet Gateway ---
resource "aws_internet_gateway" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id = aws_vpc.sagemaker[0].id
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-igw"
    ResourceType = "InternetGateway"
  })
}

# --- Public Subnets (for NAT Gateway) ---
resource "aws_subnet" "public" {
  count = var.enable_sagemaker ? length(var.availability_zones) : 0
  
  vpc_id                  = aws_vpc.sagemaker[0].id
  cidr_block              = cidrsubnet(var.vpc_cidr_block, 8, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-public-${var.availability_zones[count.index]}"
    ResourceType = "Subnet"
    SubnetType = "Public"
    AvailabilityZone = var.availability_zones[count.index]
  })
}

# --- Private Subnets (for SageMaker) ---
resource "aws_subnet" "private" {
  count = var.enable_sagemaker ? length(var.availability_zones) : 0
  
  vpc_id            = aws_vpc.sagemaker[0].id
  cidr_block        = cidrsubnet(var.vpc_cidr_block, 8, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-private-${var.availability_zones[count.index]}"
    ResourceType = "Subnet"
    SubnetType = "Private"
    AvailabilityZone = var.availability_zones[count.index]
  })
}

# --- NAT Gateway ---
resource "aws_eip" "nat" {
  count = var.enable_sagemaker ? 1 : 0
  
  domain = "vpc"
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-nat-eip"
    ResourceType = "ElasticIP"
    Purpose = "NAT Gateway"
  })
}

resource "aws_nat_gateway" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-nat-gateway"
    ResourceType = "NATGateway"
  })
  
  depends_on = [aws_internet_gateway.sagemaker]
}

# --- Route Tables ---
resource "aws_route_table" "public" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id = aws_vpc.sagemaker[0].id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.sagemaker[0].id
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-public-rt"
    ResourceType = "RouteTable"
    RouteTableType = "Public"
  })
}

resource "aws_route_table" "private" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id = aws_vpc.sagemaker[0].id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.sagemaker[0].id
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-private-rt"
    ResourceType = "RouteTable"
    RouteTableType = "Private"
  })
}

# --- Route Table Associations ---
resource "aws_route_table_association" "public" {
  count = var.enable_sagemaker ? length(var.availability_zones) : 0
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_route_table_association" "private" {
  count = var.enable_sagemaker ? length(var.availability_zones) : 0
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

# --- Security Groups ---
resource "aws_security_group" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  name        = "${var.project_short}-${var.env}-sagemaker-sg"
  description = "Security group for ${var.project} SageMaker resources"
  vpc_id      = aws_vpc.sagemaker[0].id
  
  # Allow HTTPS outbound for SageMaker API calls
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS outbound for SageMaker API"
  }
  
  # Allow HTTP outbound for model downloads
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP outbound for model downloads"
  }
  
  # Allow all outbound for SageMaker operations
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound for SageMaker operations"
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-sg"
    ResourceType = "SecurityGroup"
    Service = "SageMaker"
  })
}

resource "aws_security_group" "vpc_endpoints" {
  count = var.enable_sagemaker ? 1 : 0
  
  name        = "${var.project_short}-${var.env}-vpc-endpoints-sg"
  description = "Security group for ${var.project} VPC endpoints"
  vpc_id      = aws_vpc.sagemaker[0].id
  
  # Allow HTTPS inbound from private subnets
  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.sagemaker[0].id]
    description     = "HTTPS from SageMaker security group"
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-vpc-endpoints-sg"
    ResourceType = "SecurityGroup"
    Service = "VPCEndpoints"
  })
}

# --- VPC Endpoints for AWS Services ---
resource "aws_vpc_endpoint" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id              = aws_vpc.sagemaker[0].id
  service_name        = "com.amazonaws.${var.region}.sagemaker"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-endpoint"
    ResourceType = "VPCEndpoint"
    Service = "SageMaker"
  })
}

resource "aws_vpc_endpoint" "sagemaker_runtime" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id              = aws_vpc.sagemaker[0].id
  service_name        = "com.amazonaws.${var.region}.sagemaker-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-runtime-endpoint"
    ResourceType = "VPCEndpoint"
    Service = "SageMakerRuntime"
  })
}

resource "aws_vpc_endpoint" "s3" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id            = aws_vpc.sagemaker[0].id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.private[0].id]
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-s3-endpoint"
    ResourceType = "VPCEndpoint"
    Service = "S3"
  })
}

resource "aws_vpc_endpoint" "ecr" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id              = aws_vpc.sagemaker[0].id
  service_name        = "com.amazonaws.${var.region}.ecr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-ecr-endpoint"
    ResourceType = "VPCEndpoint"
    Service = "ECR"
  })
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id              = aws_vpc.sagemaker[0].id
  service_name        = "com.amazonaws.${var.region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-ecr-dkr-endpoint"
    ResourceType = "VPCEndpoint"
    Service = "ECRDocker"
  })
}

resource "aws_vpc_endpoint" "logs" {
  count = var.enable_sagemaker ? 1 : 0
  
  vpc_id              = aws_vpc.sagemaker[0].id
  service_name        = "com.amazonaws.${var.region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-logs-endpoint"
    ResourceType = "VPCEndpoint"
    Service = "CloudWatchLogs"
  })
}

# --- KMS Key for Encryption ---
resource "aws_kms_key" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  description             = "KMS key for ${var.project} SageMaker encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow SageMaker to use the key"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = "sagemaker.${var.region}.amazonaws.com"
          }
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-kms"
    ResourceType = "KMSKey"
    Purpose = "SageMakerEncryption"
  })
}

resource "aws_kms_alias" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  name          = "alias/${var.project_short}-${var.env}-sagemaker"
  target_key_id = aws_kms_key.sagemaker[0].key_id
}

# --- CloudWatch Log Groups ---
resource "aws_cloudwatch_log_group" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  name              = "/aws/sagemaker/${var.project_short}-${var.env}"
  retention_in_days = var.log_retention_days
  kms_key_id        = aws_kms_key.sagemaker[0].arn
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-logs"
    ResourceType = "CloudWatchLogGroup"
    Service = "SageMaker"
  })
}

# --- CloudWatch Dashboard ---
resource "aws_cloudwatch_dashboard" "sagemaker" {
  count = var.enable_sagemaker ? 1 : 0
  
  dashboard_name = "${var.project_short}-${var.env}-sagemaker-dashboard"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/SageMaker/Endpoints", "Invocations", "EndpointName", "${var.project_short}-${var.env}-ollama-endpoint"],
            [".", "Invocation4XXErrors", ".", "."],
            [".", "Invocation5XXErrors", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "${var.project} SageMaker Endpoint Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/SageMaker/Endpoints", "ModelLatency", "EndpointName", "${var.project_short}-${var.env}-ollama-endpoint"]
          ]
          period = 300
          stat   = "Average"
          region = var.region
          title  = "Model Latency"
        }
      }
    ]
  })
}

# --- CloudWatch Alarms ---
resource "aws_cloudwatch_metric_alarm" "sagemaker_errors" {
  count = var.enable_sagemaker ? 1 : 0
  
  alarm_name          = "${var.project_short}-${var.env}-sagemaker-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Invocation5XXErrors"
  namespace           = "AWS/SageMaker"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "${var.project} SageMaker endpoint 5XX errors"
  
  dimensions = {
    EndpointName = "${var.project_short}-${var.env}-ollama-endpoint"
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-errors-alarm"
    ResourceType = "CloudWatchAlarm"
    Service = "SageMaker"
  })
}

resource "aws_cloudwatch_metric_alarm" "sagemaker_latency" {
  count = var.enable_sagemaker ? 1 : 0
  
  alarm_name          = "${var.project_short}-${var.env}-sagemaker-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ModelLatency"
  namespace           = "AWS/SageMaker"
  period              = "300"
  statistic           = "Average"
  threshold           = "10000"
  alarm_description   = "${var.project} SageMaker endpoint high latency"
  
  dimensions = {
    EndpointName = "${var.project_short}-${var.env}-ollama-endpoint"
  }
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-sagemaker-latency-alarm"
    ResourceType = "CloudWatchAlarm"
    Service = "SageMaker"
  })
}

# --- Data source for current AWS account ---
data "aws_caller_identity" "current" {}
