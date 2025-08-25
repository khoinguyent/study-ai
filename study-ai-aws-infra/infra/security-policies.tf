# Additional Security Policies and Configurations
# This file contains enhanced security measures for the SageMaker infrastructure

# --- WAF Web ACL for API Gateway (if needed) ---
resource "aws_wafv2_web_acl" "sagemaker_api" {
  count = var.enable_sagemaker && var.enable_waf ? 1 : 0
  
  name        = "${var.project}-${var.env}-sagemaker-waf"
  description = "WAF for SageMaker API protection"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # Block suspicious IPs
  rule {
    name     = "BlockSuspiciousIPs"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockSuspiciousIPs"
      sampled_requests_enabled   = true
    }
  }

  # Block SQL injection
  rule {
    name     = "BlockSQLInjection"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockSQLInjection"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "SageMakerWAFMetrics"
    sampled_requests_enabled   = true
  }

  tags = var.tags
}

# --- GuardDuty Detector ---
resource "aws_guardduty_detector" "main" {
  count = var.enable_sagemaker && var.enable_guardduty ? 1 : 0
  
  enable = true
  
  tags = var.tags
}

# --- Config Rules for Compliance ---
resource "aws_config_config_rule" "sagemaker_encryption" {
  count = var.enable_sagemaker && var.enable_config ? 1 : 0
  
  name = "${var.project}-${var.env}-sagemaker-encryption-check"
  
  source {
    owner             = "AWS"
    source_identifier = "SAGEMAKER_ENDPOINT_CONFIGURATION_KMS_KEY_CHECK"
  }
  
  scope {
    compliance_resource_types = ["AWS::SageMaker::EndpointConfiguration"]
  }
  
  tags = var.tags
}

resource "aws_config_config_rule" "s3_encryption" {
  count = var.enable_sagemaker && var.enable_config ? 1 : 0
  
  name = "${var.project}-${var.env}-s3-encryption-check"
  
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED"
  }
  
  scope {
    compliance_resource_types = ["AWS::S3::Bucket"]
  }
  
  tags = var.tags
}

# --- CloudTrail for API Logging ---
resource "aws_cloudtrail" "sagemaker" {
  count = var.enable_sagemaker && var.enable_cloudtrail ? 1 : 0
  
  name                          = "${var.project}-${var.env}-sagemaker-trail"
  s3_bucket_name               = aws_s3_bucket.cloudtrail[0].bucket
  include_global_service_events = true
  is_multi_region_trail        = true
  enable_logging               = true
  
  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = ["kms.amazonaws.com"]
  }
  
  tags = var.tags
}

resource "aws_s3_bucket" "cloudtrail" {
  count = var.enable_sagemaker && var.enable_cloudtrail ? 1 : 0
  
  bucket = "${var.project}-cloudtrail-${var.env}-${var.region}"
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "cloudtrail" {
  count = var.enable_sagemaker && var.enable_cloudtrail ? 1 : 0
  
  bucket = aws_s3_bucket.cloudtrail[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail" {
  count = var.enable_sagemaker && var.enable_cloudtrail ? 1 : 0
  
  bucket = aws_s3_bucket.cloudtrail[0].id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  count = var.enable_sagemaker && var.enable_cloudtrail ? 1 : 0
  
  bucket                  = aws_s3_bucket.cloudtrail[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- SNS Topic for Security Alerts ---
resource "aws_sns_topic" "security_alerts" {
  count = var.enable_sagemaker && var.enable_security_alerts ? 1 : 0
  
  name = "${var.project}-${var.env}-security-alerts"
  
  tags = var.tags
}

resource "aws_sns_topic_subscription" "security_alerts_email" {
  count = var.enable_sagemaker && var.enable_security_alerts ? 1 : 0
  
  topic_arn = aws_sns_topic.security_alerts[0].arn
  protocol  = "email"
  endpoint  = var.security_alert_email
}

# --- CloudWatch Alarms for Security Events ---
resource "aws_cloudwatch_metric_alarm" "unauthorized_api_calls" {
  count = var.enable_sagemaker && var.enable_security_alerts ? 1 : 0
  
  alarm_name          = "${var.project}-${var.env}-unauthorized-api-calls"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "UnauthorizedAPICalls"
  namespace           = "AWS/CloudTrail"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Unauthorized API calls detected"
  
  dimensions = {
    LogGroupName = aws_cloudwatch_log_group.sagemaker[0].name
  }
  
  alarm_actions = [aws_sns_topic.security_alerts[0].arn]
  
  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "root_account_usage" {
  count = var.enable_sagemaker && var.enable_security_alerts ? 1 : 0
  
  alarm_name          = "${var.project}-${var.env}-root-account-usage"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "RootAccountUsage"
  namespace           = "AWS/CloudTrail"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Root account usage detected"
  
  dimensions = {
    LogGroupName = aws_cloudwatch_log_group.sagemaker[0].name
  }
  
  alarm_actions = [aws_sns_topic.security_alerts[0].arn]
  
  tags = var.tags
}

# --- IAM Password Policy ---
resource "aws_iam_account_password_policy" "strict" {
  count = var.enable_sagemaker && var.enable_strict_password_policy ? 1 : 0
  
  minimum_password_length        = 12
  require_lowercase_characters  = true
  require_numbers               = true
  require_uppercase_characters  = true
  require_symbols               = true
  allow_users_to_change_password = true
  max_password_age              = 90
  password_reuse_prevention     = 24
}

# --- IAM Access Analyzer ---
resource "aws_accessanalyzer_analyzer" "sagemaker" {
  count = var.enable_sagemaker && var.enable_access_analyzer ? 1 : 0
  
  analyzer_name = "${var.project}-${var.env}-sagemaker-analyzer"
  type          = "ACCOUNT"
  
  tags = var.tags
}

# --- Security Hub ---
resource "aws_securityhub_account" "main" {
  count = var.enable_sagemaker && var.enable_security_hub ? 1 : 0
}

resource "aws_securityhub_standards_subscription" "cis" {
  count = var.enable_sagemaker && var.enable_security_hub ? 1 : 0
  
  depends_on    = [aws_securityhub_account.main]
  standards_arn = "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0"
}

resource "aws_securityhub_standards_subscription" "pci" {
  count = var.enable_sagemaker && var.enable_security_hub ? 1 : 0
  
  depends_on    = [aws_securityhub_account.main]
  standards_arn = "arn:aws:securityhub:${var.region}::standards/pci-dss/v/3.2.1"
}

# --- VPC Flow Logs ---
resource "aws_flow_log" "sagemaker_vpc" {
  count = var.enable_sagemaker && var.enable_vpc_flow_logs ? 1 : 0
  
  iam_role_arn    = aws_iam_role.vpc_flow_logs[0].arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs[0].arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.sagemaker[0].id
  
  tags = var.tags
}

resource "aws_iam_role" "vpc_flow_logs" {
  count = var.enable_sagemaker && var.enable_vpc_flow_logs ? 1 : 0
  
  name = "${var.project}-${var.env}-vpc-flow-logs-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.tags
}

resource "aws_iam_role_policy" "vpc_flow_logs" {
  count = var.enable_sagemaker && var.enable_vpc_flow_logs ? 1 : 0
  
  name = "${var.project}-${var.env}-vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow_logs[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  count = var.enable_sagemaker && var.enable_vpc_flow_logs ? 1 : 0
  
  name              = "/aws/vpc/flow-logs/${var.project}-${var.env}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.enable_kms_encryption ? aws_kms_key.sagemaker[0].arn : null
  
  tags = var.tags
}
