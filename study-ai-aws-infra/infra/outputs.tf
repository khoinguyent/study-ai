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

# ElastiCache Redis
output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].port
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}/0"
}

# SQS Queues
output "main_tasks_queue_url" {
  description = "Main tasks queue URL"
  value       = aws_sqs_queue.main_tasks.url
}

output "document_tasks_queue_url" {
  description = "Document processing queue URL"
  value       = aws_sqs_queue.document_tasks.url
}

output "indexing_tasks_queue_url" {
  description = "Indexing tasks queue URL"
  value       = aws_sqs_queue.indexing_tasks.url
}

output "quiz_tasks_queue_url" {
  description = "Quiz generation tasks queue URL"
  value       = aws_sqs_queue.quiz_tasks.url
}

output "dlq_url" {
  description = "Dead letter queue URL"
  value       = aws_sqs_queue.dlq.url
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
