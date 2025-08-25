# ElastiCache Redis Cluster for Study AI Platform
# Provides Redis-compatible caching and message broker functionality

# Subnet group for ElastiCache
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${var.project_short}-${var.env}-redis-subnet-group"
  subnet_ids = var.enable_sagemaker ? aws_subnet.private[*].id : [data.aws_subnet.default[0].id]
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-redis-subnet-group"
    ResourceType = "ElastiCacheSubnetGroup"
    Service = "Redis"
  })
}

# Security group for ElastiCache
resource "aws_security_group" "redis" {
  name        = "${var.project_short}-${var.env}-redis-sg"
  description = "Security group for ${var.project} ElastiCache Redis cluster"
  vpc_id      = var.enable_sagemaker ? aws_vpc.sagemaker[0].id : data.aws_vpc.default.id

  # Allow Redis access from EC2 instances
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
    description     = "Redis access from EC2 instances"
  }

  # Allow Redis access from your IP (for development/testing)
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.allow_ssh_cidr]
    description = "Redis access from development IP"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-redis-sg"
    ResourceType = "SecurityGroup"
    Service = "Redis"
  })
}

# ElastiCache Redis cluster
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_short}-${var.env}-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"  # Small instance for development
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  security_group_ids   = [aws_security_group.redis.id]
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  
  tags = merge(local.common_tags, {
    Name = "${var.project_short}-${var.env}-redis-cluster"
    ResourceType = "ElastiCacheCluster"
    Service = "Redis"
    Engine = "Redis7"
  })
}

# Outputs
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
