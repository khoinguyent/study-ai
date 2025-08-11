# SQS Queues for Study AI Platform
# Provides message queuing functionality to replace Celery

# Main task queue
resource "aws_sqs_queue" "main_tasks" {
  name                      = "${var.project}-${var.env}-main-tasks"
  delay_seconds             = 0
  max_message_size          = 262144  # 256 KB
  message_retention_seconds = 345600  # 4 days
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 30

  # Dead letter queue configuration
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = var.tags
}

# Dead letter queue for failed messages
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project}-${var.env}-dlq"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600  # 14 days
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 30

  tags = var.tags
}

# Document processing queue
resource "aws_sqs_queue" "document_tasks" {
  name                      = "${var.project}-${var.env}-document-tasks"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 300  # 5 minutes for document processing

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = var.tags
}

# Indexing tasks queue
resource "aws_sqs_queue" "indexing_tasks" {
  name                      = "${var.project}-${var.env}-indexing-tasks"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 600  # 10 minutes for indexing

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = var.tags
}

# Quiz generation tasks queue
resource "aws_sqs_queue" "quiz_tasks" {
  name                      = "${var.project}-${var.env}-quiz-tasks"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 345600
  receive_wait_time_seconds = 0
  visibility_timeout_seconds = 900  # 15 minutes for quiz generation

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = var.tags
}

# Outputs
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
