# AWS Configuration
region = "ap-southeast-1"
env = "dev"

# Project Configuration
project = "Studium-app"
project_short = "studium"
project_owner = "AI Team"
project_description = "Study AI Platform with Ollama Integration"
cost_center = "AI-001"

# SageMaker Configuration
enable_sagemaker = false
enable_sagemaker_minimal = true

# Minimal SageMaker Settings
sagemaker_minimal_instance_type = "ml.t2.medium"
ollama_image_uri = "542834090270.dkr.ecr.ap-southeast-1.amazonaws.com/ollama-inference:sm-compat-v2"
ollama_model_name = "llama3:8b-instruct"
sagemaker_minimal_initial_count = 1
sagemaker_minimal_min_count = 1
sagemaker_minimal_max_count = 2

# Security Configuration
vpc_cidr_block = "10.0.0.0/16"
availability_zones = ["ap-southeast-1a", "ap-southeast-1b"]
log_retention_days = 30
enable_vpc_endpoints = true
enable_kms_encryption = true
enable_cloudwatch_monitoring = true
enable_waf = true
enable_guardduty = true
enable_config = true
enable_cloudtrail = true
enable_security_alerts = true
security_alert_email = "admin@studium-app.com"
enable_strict_password_policy = true
enable_access_analyzer = true
enable_security_hub = true
enable_vpc_flow_logs = true

# Tags
tags = {
  Project = "Studium-app"
  Environment = "dev"
  Owner = "AI Team"
  CostCenter = "AI-001"
  ManagedBy = "Terraform"
  Purpose = "Study AI Platform"
}
