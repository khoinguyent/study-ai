variable "region" {
  type    = string
  default = "ap-southeast-1"
}

variable "project" {
  type    = string
  default = "Studium-app"
}

variable "project_short" {
  type    = string
  default = "studium"
  description = "Short project name for resource naming (lowercase, no spaces)"
}

variable "env" {
  type    = string
  default = "dev"
}

variable "project_owner" {
  type    = string
  default = "Study AI Team"
  description = "Project owner or team name"
}

variable "project_description" {
  type    = string
  default = "Study AI Platform with SageMaker and Ollama Integration"
  description = "Project description for documentation"
}

variable "cost_center" {
  type    = string
  default = "AI-Research"
  description = "Cost center for billing and budget tracking"
}

# Choose CPU architecture for EC2 (x86_64 or ARM/Graviton)
variable "use_arm" {
  type    = bool
  default = true # true = t4g (ARM), false = t3 (x86)
}

variable "ec2_instance_type_arm" {
  type    = string
  default = "t4g.micro"  # Free Tier eligible
}

variable "ec2_instance_type_x86" {
  type    = string
  default = "t3.micro"   # Free Tier eligible
}

variable "allow_ssh_cidr" {
  description = "Your public IP/CIDR for SSH (e.g., 203.0.113.10/32). CHANGE THIS."
  type        = string
  default     = "0.0.0.0/0"
}

variable "enable_sagemaker" {
  type    = bool
  default = false
  description = "Enable full SageMaker deployment (Domain, User Profile, etc.)"
}

variable "enable_sagemaker_minimal" {
  type    = bool
  default = false
  description = "Enable minimal SageMaker deployment (Model + Endpoint only) for quiz generation"
}

# SageMaker Configuration Variables
variable "sagemaker_instance_type" {
  description = "Instance type for SageMaker notebooks and training"
  type        = string
  default     = "ml.t3.medium"
}

variable "sagemaker_image_arn" {
  description = "SageMaker image ARN for notebooks and training"
  type        = string
  default     = "arn:aws:sagemaker:ap-southeast-1:763104351884:image/pytorch-training-1.13.1-cpu-py39-ubuntu20.04-ec2"
}

variable "ollama_image_uri" {
  description = "ECR image URI for Ollama model container"
  type        = string
  default     = "763104351884.dkr.ecr.ap-southeast-1.amazonaws.com/ollama-inference:latest"
}

variable "ollama_model_name" {
  description = "Name of the Ollama model to use for quiz generation"
  type        = string
  default     = "llama2:7b-chat"
}

variable "sagemaker_endpoint_instance_type" {
  description = "Instance type for SageMaker endpoint"
  type        = string
  default     = "ml.t3.medium"
}

variable "sagemaker_endpoint_initial_count" {
  description = "Initial instance count for SageMaker endpoint"
  type        = number
  default     = 1
}

# Minimal SageMaker Configuration Variables
variable "sagemaker_minimal_instance_type" {
  description = "Instance type for minimal SageMaker endpoint (quiz generation only)"
  type        = string
  default     = "ml.t2.medium"  # Supported instance type for SageMaker endpoints
}

variable "sagemaker_minimal_initial_count" {
  description = "Initial instance count for minimal SageMaker endpoint"
  type        = number
  default     = 1
}

variable "sagemaker_minimal_max_count" {
  description = "Maximum instance count for minimal SageMaker endpoint auto-scaling"
  type        = number
  default     = 3
}

variable "sagemaker_minimal_min_count" {
  description = "Minimum instance count for minimal SageMaker endpoint auto-scaling"
  type        = number
  default     = 0  # Scale to zero when not in use
}

# Security Configuration Variables
variable "vpc_cidr_block" {
  description = "CIDR block for the SageMaker VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use for subnets"
  type        = list(string)
  default     = ["ap-southeast-1a", "ap-southeast-1b"]
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for AWS services"
  type        = bool
  default     = true
}

variable "enable_kms_encryption" {
  description = "Enable KMS encryption for SageMaker resources"
  type        = bool
  default     = true
}

variable "enable_cloudwatch_monitoring" {
  description = "Enable CloudWatch monitoring and alarms"
  type        = bool
  default     = true
}

# Advanced Security Variables
variable "enable_waf" {
  description = "Enable WAF for API protection"
  type        = bool
  default     = false
}

variable "enable_guardduty" {
  description = "Enable GuardDuty threat detection"
  type        = bool
  default     = false
}

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = false
}

variable "enable_cloudtrail" {
  description = "Enable CloudTrail for API logging"
  type        = bool
  default     = false
}

variable "enable_security_alerts" {
  description = "Enable security alerts via SNS"
  type        = bool
  default     = false
}

variable "security_alert_email" {
  description = "Email address for security alerts"
  type        = string
  default     = ""
}

variable "enable_strict_password_policy" {
  description = "Enable strict IAM password policy"
  type        = bool
  default     = false
}

variable "enable_access_analyzer" {
  description = "Enable IAM Access Analyzer"
  type        = bool
  default     = false
}

variable "enable_security_hub" {
  description = "Enable Security Hub for security standards"
  type        = bool
  default     = false
}

variable "enable_vpc_flow_logs" {
  description = "Enable VPC Flow Logs for network monitoring"
  type        = bool
  default     = false
}

variable "tags" {
  type    = map(string)
  default = { 
    Project = "Studium-app"
    Environment = "dev"
    Owner = "Study AI Team"
    CostCenter = "AI-Research"
    ManagedBy = "Terraform"
    Purpose = "Study AI Platform"
  }
}
