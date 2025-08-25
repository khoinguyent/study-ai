# SQS Queues for Study AI Platform
# Provides message queuing for asynchronous task processing

# Dead Letter Queue (DLQ) for failed messages
resource "aws_sqs_queue" "dlq" {
  name = "${var.project_short}-${var.env}-dlq"
  
  # Message retention: 14 days
  message_retention_seconds = 1209600
  
  # Visibility timeout: 30 seconds
  visibility_timeout_seconds = 30
  
  # Receive message wait time: 20 seconds (long polling)
  receive_wait_time_seconds = 20
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-dead-letter-queue"
    ResourceType = "SQSQueue"
    QueueType = "DeadLetterQueue"
    Purpose = "FailedMessageHandling"
  })
}

# Main tasks queue
resource "aws_sqs_queue" "main_tasks" {
  name = "${var.project_short}-${var.env}-main-tasks"
  
  # Message retention: 4 days
  message_retention_seconds = 345600
  
  # Visibility timeout: 30 seconds
  visibility_timeout_seconds = 30
  
  # Receive message wait time: 20 seconds (long polling)
  receive_wait_time_seconds = 20
  
  # Redrive policy to DLQ after 3 failed attempts
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-main-tasks-queue"
    ResourceType = "SQSQueue"
    QueueType = "Standard"
    Purpose = "GeneralTaskProcessing"
  })
}

# Document processing queue
resource "aws_sqs_queue" "document_tasks" {
  name = "${var.project_short}-${var.env}-document-tasks"
  
  # Message retention: 4 days
  message_retention_seconds = 345600
  
  # Visibility timeout: 60 seconds (documents may take longer to process)
  visibility_timeout_seconds = 60
  
  # Receive message wait time: 20 seconds (long polling)
  receive_wait_time_seconds = 20
  
  # Redrive policy to DLQ after 3 failed attempts
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-document-tasks-queue"
    ResourceType = "SQSQueue"
    QueueType = "Standard"
    Purpose = "DocumentProcessing"
  })
}

# Indexing tasks queue
resource "aws_sqs_queue" "indexing_tasks" {
  name = "${var.project_short}-${var.env}-indexing-tasks"
  
  # Message retention: 4 days
  message_retention_seconds = 345600
  
  # Visibility timeout: 120 seconds (indexing may take longer)
  visibility_timeout_seconds = 120
  
  # Receive message wait time: 20 seconds (long polling)
  receive_wait_time_seconds = 20
  
  # Redrive policy to DLQ after 3 failed attempts
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-indexing-tasks-queue"
    ResourceType = "SQSQueue"
    QueueType = "Standard"
    Purpose = "DocumentIndexing"
  })
}

# Quiz generation queue
resource "aws_sqs_queue" "quiz_tasks" {
  name = "${var.project_short}-${var.env}-quiz-tasks"
  
  # Message retention: 4 days
  message_retention_seconds = 345600
  
  # Visibility timeout: 180 seconds (quiz generation may take longer)
  visibility_timeout_seconds = 180
  
  # Receive message wait time: 20 seconds (long polling)
  receive_wait_time_seconds = 20
  
  # Redrive policy to DLQ after 3 failed attempts
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-quiz-tasks-queue"
    ResourceType = "SQSQueue"
    QueueType = "Standard"
    Purpose = "QuizGeneration"
  })
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
