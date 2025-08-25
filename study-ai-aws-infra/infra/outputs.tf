# S3 Bucket
output "bucket_name" { 
  value = aws_s3_bucket.uploads.bucket 
}

# EC2 Instance
output "ec2_public_ip" { 
  value = aws_instance.app.public_ip 
}

output "ec2_ssh_key" {
  value     = local_file.ssh_key.filename
  sensitive = true
}

# Database configuration (EC2-hosted PostgreSQL)
output "db_endpoint" {
  description = "EC2 PostgreSQL endpoint"
  value       = aws_instance.app.public_ip
}

output "db_port" {
  description = "PostgreSQL port"
  value       = 5432
}

output "db_name" {
  description = "PostgreSQL database name"
  value       = "study_ai"
}

output "db_username" {
  description = "PostgreSQL username"
  value       = "postgres"
}

output "database_url" {
  description = "EC2 PostgreSQL connection URL"
  value       = "postgresql://postgres:password@${aws_instance.app.public_ip}:5432/study_ai"
}

# Summary outputs for easy configuration
output "message_broker_url" {
  description = "Message broker URL for env.cloud"
  value       = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}/0"
}

output "task_queue_url" {
  description = "Main task queue URL for env.cloud"
  value       = aws_sqs_queue.main_tasks.url
}

output "infrastructure_summary" {
  description = "Summary of all infrastructure endpoints"
  value = {
    s3_bucket        = aws_s3_bucket.uploads.bucket
    redis_endpoint   = aws_elasticache_cluster.redis.cache_nodes[0].address
    redis_port       = aws_elasticache_cluster.redis.cache_nodes[0].port
    main_queue_url   = aws_sqs_queue.main_tasks.url
    db_endpoint      = aws_instance.app.public_ip
    ec2_public_ip    = aws_instance.app.public_ip
  }
}

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app.id
}

output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app.public_ip
}

output "instance_public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.app.public_dns
}

output "ssh_key_path" {
  description = "Path to the generated SSH private key"
  value       = local_file.ssh_key.filename
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for uploads"
  value       = aws_s3_bucket.uploads.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for uploads"
  value       = aws_s3_bucket.uploads.arn
}

# SageMaker Outputs
output "sagemaker_domain_id" {
  description = "ID of the SageMaker domain"
  value       = var.enable_sagemaker ? aws_sagemaker_domain.main[0].id : null
}

output "sagemaker_domain_url" {
  description = "URL of the SageMaker domain"
  value       = var.enable_sagemaker ? aws_sagemaker_domain.main[0].url : null
}

output "sagemaker_user_profile_arn" {
  description = "ARN of the SageMaker user profile"
  value       = var.enable_sagemaker ? aws_sagemaker_user_profile.ollama_user[0].id : null
}

output "sagemaker_model_arn" {
  description = "ARN of the SageMaker model"
  value       = var.enable_sagemaker ? aws_sagemaker_model.ollama_model[0].arn : null
}

output "sagemaker_endpoint_name" {
  description = "Name of the SageMaker endpoint"
  value       = var.enable_sagemaker ? aws_sagemaker_endpoint.ollama_endpoint[0].name : null
}

output "sagemaker_endpoint_arn" {
  description = "ARN of the SageMaker endpoint"
  value       = var.enable_sagemaker ? aws_sagemaker_endpoint.ollama_endpoint[0].arn : null
}

output "sagemaker_s3_bucket_name" {
  description = "Name of the S3 bucket for SageMaker models and data"
  value       = var.enable_sagemaker ? aws_s3_bucket.sagemaker[0].bucket : null
}

output "sagemaker_s3_bucket_arn" {
  description = "ARN of the S3 bucket for SageMaker models and data"
  value       = var.enable_sagemaker ? aws_s3_bucket.sagemaker[0].arn : null
}

output "sagemaker_role_arn" {
  description = "ARN of the IAM role for SageMaker"
  value       = var.enable_sagemaker ? aws_iam_role.sagemaker[0].arn : null
}

# Resource Groups (simplified tag-based groups)
output "resource_groups" {
  description = "Names of created resource groups"
  value = {
    main_project_group = aws_resourcegroups_group.studium_app.name
    security_group     = aws_resourcegroups_group.security.name
    monitoring_group   = aws_resourcegroups_group.monitoring.name
  }
}

# SageMaker Console URLs
output "sagemaker_console_endpoint_url" {
  description = "AWS Console URL for the SageMaker endpoint"
  value = var.enable_sagemaker_minimal ? "https://${var.region}.console.aws.amazon.com/sagemaker/home?region=${var.region}#/endpoints/${aws_sagemaker_endpoint.ollama_minimal[0].name}" : null
}

output "sagemaker_console_model_url" {
  description = "AWS Console URL for the SageMaker model"
  value = var.enable_sagemaker_minimal ? "https://${var.region}.console.aws.amazon.com/sagemaker/home?region=${var.region}#/models/${aws_sagemaker_model.ollama_minimal[0].name}" : null
}

# Project Management URLs
output "project_management_urls" {
  description = "AWS Console links for project management"
  value = {
    resource_groups_console = "https://${var.region}.console.aws.amazon.com/resource-groups"
    main_project_group_url  = "https://${var.region}.console.aws.amazon.com/resource-groups/group/${aws_resourcegroups_group.studium_app.name}"
    security_group_url      = "https://${var.region}.console.aws.amazon.com/resource-groups/group/${aws_resourcegroups_group.security.name}"
    monitoring_group_url    = "https://${var.region}.console.aws.amazon.com/resource-groups/group/${aws_resourcegroups_group.monitoring.name}"
  }
}

output "project_tags" {
  description = "Common tags used across all resources"
  value = local.common_tags
}


