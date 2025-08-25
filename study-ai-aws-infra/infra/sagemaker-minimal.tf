# Minimal SageMaker Configuration for Ollama Model Hosting
# This configuration only deploys what's needed for quiz generation
# No SageMaker Domain, User Profiles, or development environment

# SageMaker Model (Ollama container)
# Note: Currently using OCI manifest format due to Docker Desktop on macOS limitations
# This may require AWS support or building on Linux to achieve Docker v2 Schema 2
resource "aws_sagemaker_model" "ollama_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  name               = "${var.project_short}-${var.env}-ollama-minimal-model"
  execution_role_arn = aws_iam_role.sagemaker_minimal[0].arn

  primary_container {
    image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com/ollama-inference:sm-compat-v2"
    mode  = "SingleModel"

    environment = {
      SAGEMAKER_PROGRAM             = "inference.py"
      SAGEMAKER_SUBMIT_DIRECTORY    = "/opt/ml/code"
      SAGEMAKER_CONTAINER_LOG_LEVEL = "20"
      SAGEMAKER_REGION              = var.region
      OLLAMA_MODEL                  = var.ollama_model_name
      OLLAMA_PRELOAD                = "true"
      PORT                          = "8080"
    }
  }

  tags = local.common_tags
}

# SageMaker Endpoint Configuration
resource "aws_sagemaker_endpoint_configuration" "ollama_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  name = "${var.project_short}-${var.env}-ollama-minimal-config"

  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.ollama_minimal[0].name
    initial_instance_count = var.sagemaker_minimal_initial_count
    instance_type          = var.sagemaker_minimal_instance_type
  }

  tags = local.common_tags
}

# SageMaker Endpoint
resource "aws_sagemaker_endpoint" "ollama_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  name                 = "${var.project_short}-${var.env}-ollama-minimal-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.ollama_minimal[0].name

  tags = local.common_tags

  lifecycle {
    ignore_changes = [tags] # reduce churn
  }
}

# IAM Role for SageMaker execution
resource "aws_iam_role" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  name = "${var.project_short}-${var.env}-sagemaker-minimal-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

# Inline policy for SageMaker execution
resource "aws_iam_role_policy" "sagemaker_minimal_execution" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  name = "${var.project_short}-${var.env}-sagemaker-minimal-execution"
  role = aws_iam_role.sagemaker_minimal[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
          "cloudwatch:PutMetricData",
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach SageMaker full access policy
resource "aws_iam_role_policy_attachment" "sagemaker_minimal_full_access" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  role       = aws_iam_role.sagemaker_minimal[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# S3 Bucket for SageMaker models and data
resource "aws_s3_bucket" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  bucket = "${var.project_short}-sagemaker-minimal-${var.env}-${var.region}"

  tags = local.common_tags
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  bucket = aws_s3_bucket.sagemaker_minimal[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket public access block
resource "aws_s3_bucket_public_access_block" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  bucket = aws_s3_bucket.sagemaker_minimal[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket server side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  bucket = aws_s3_bucket.sagemaker_minimal[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# KMS Key for SageMaker encryption
resource "aws_kms_key" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  description             = "KMS key for SageMaker minimal deployment"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = local.common_tags
}

# KMS Alias
resource "aws_kms_alias" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  name          = "alias/${var.project_short}-${var.env}-sagemaker-minimal"
  target_key_id = aws_kms_key.sagemaker_minimal[0].key_id
}

# CloudWatch Log Group for SageMaker
resource "aws_cloudwatch_log_group" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  name              = "/aws/sagemaker/Endpoints/${var.project_short}-${var.env}-ollama-minimal-endpoint"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# CloudWatch Dashboard for SageMaker
resource "aws_cloudwatch_dashboard" "sagemaker_minimal" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  dashboard_name = "${var.project_short}-${var.env}-sagemaker-minimal-dashboard"

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
            ["AWS/SageMaker", "Invocations", "EndpointName", "${var.project_short}-${var.env}-ollama-minimal-endpoint"],
            [".", "ModelLatency", ".", "."],
            [".", "Invocation4XXErrors", ".", "."],
            [".", "Invocation5XXErrors", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.region
          title  = "SageMaker Endpoint Metrics"
        }
      }
    ]
  })

  tags = local.common_tags
}

# CloudWatch Alarms for SageMaker
resource "aws_cloudwatch_metric_alarm" "sagemaker_minimal_errors" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  alarm_name          = "${var.project_short}-${var.env}-sagemaker-minimal-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Invocation5XXErrors"
  namespace           = "AWS/SageMaker"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors SageMaker endpoint 5XX errors"
  alarm_actions       = []

  dimensions = {
    EndpointName = aws_sagemaker_endpoint.ollama_minimal[0].name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "sagemaker_minimal_latency" {
  count = var.enable_sagemaker_minimal ? 1 : 0

  alarm_name          = "${var.project_short}-${var.env}-sagemaker-minimal-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ModelLatency"
  namespace           = "AWS/SageMaker"
  period              = "300"
  statistic           = "Average"
  threshold           = "30000"
  alarm_description   = "This metric monitors SageMaker endpoint latency"
  alarm_actions       = []

  dimensions = {
    EndpointName = aws_sagemaker_endpoint.ollama_minimal[0].name
  }

  tags = local.common_tags
}

# Outputs for minimal SageMaker
output "sagemaker_minimal_endpoint_name" {
  description = "Name of the minimal SageMaker endpoint"
  value       = var.enable_sagemaker_minimal ? aws_sagemaker_endpoint.ollama_minimal[0].name : null
}

output "sagemaker_minimal_endpoint_arn" {
  description = "ARN of the minimal SageMaker endpoint"
  value       = var.enable_sagemaker_minimal ? aws_sagemaker_endpoint.ollama_minimal[0].arn : null
}

output "sagemaker_minimal_model_arn" {
  description = "ARN of the minimal SageMaker model"
  value       = var.enable_sagemaker_minimal ? aws_sagemaker_model.ollama_minimal[0].arn : null
}

output "sagemaker_minimal_s3_bucket_name" {
  description = "Name of the S3 bucket for minimal SageMaker"
  value       = var.enable_sagemaker_minimal ? aws_s3_bucket.sagemaker_minimal[0].bucket : null
}

output "sagemaker_minimal_role_arn" {
  description = "ARN of the IAM role for minimal SageMaker"
  value       = var.enable_sagemaker_minimal ? aws_iam_role.sagemaker_minimal[0].arn : null
}
