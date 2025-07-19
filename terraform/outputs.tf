# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.streamflow_vpc.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.streamflow_vpc.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public_subnets[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private_subnets[*].id
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = aws_subnet.database_subnets[*].id
}

# EKS Outputs
output "cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.streamflow_cluster.id
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.streamflow_cluster.arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.streamflow_cluster.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.streamflow_cluster.vpc_config[0].cluster_security_group_id
}

output "cluster_version" {
  description = "EKS cluster version"
  value       = aws_eks_cluster.streamflow_cluster.version
}

output "cluster_platform_version" {
  description = "Platform version for the EKS cluster"
  value       = aws_eks_cluster.streamflow_cluster.platform_version
}

output "cluster_ca_certificate" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.streamflow_cluster.certificate_authority[0].data
}

output "cluster_oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = aws_eks_cluster.streamflow_cluster.identity[0].oidc[0].issuer
}

output "node_group_arn" {
  description = "Amazon Resource Name (ARN) of the EKS Node Group"
  value       = aws_eks_node_group.streamflow_nodes.arn
}

output "node_group_status" {
  description = "Status of the EKS Node Group"
  value       = aws_eks_node_group.streamflow_nodes.status
}

# Database Outputs
output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.streamflow_postgres.endpoint
  sensitive   = true
}

output "db_instance_hosted_zone_id" {
  description = "RDS instance hosted zone ID"
  value       = aws_db_instance.streamflow_postgres.hosted_zone_id
}

output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.streamflow_postgres.id
}

output "db_instance_resource_id" {
  description = "RDS instance resource ID"
  value       = aws_db_instance.streamflow_postgres.resource_id
}

output "db_instance_status" {
  description = "RDS instance status"
  value       = aws_db_instance.streamflow_postgres.status
}

output "db_instance_name" {
  description = "RDS instance name"
  value       = aws_db_instance.streamflow_postgres.db_name
}

output "db_instance_username" {
  description = "RDS instance master username"
  value       = aws_db_instance.streamflow_postgres.username
  sensitive   = true
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = aws_db_instance.streamflow_postgres.port
}

# Redis Outputs
output "redis_cluster_id" {
  description = "ElastiCache Redis cluster ID"
  value       = aws_elasticache_replication_group.streamflow_redis.id
}

output "redis_cluster_address" {
  description = "ElastiCache Redis cluster address"
  value       = aws_elasticache_replication_group.streamflow_redis.primary_endpoint_address
  sensitive   = true
}

output "redis_cluster_port" {
  description = "ElastiCache Redis cluster port"
  value       = aws_elasticache_replication_group.streamflow_redis.port
}

# IAM Outputs
output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = aws_iam_role.eks_cluster_role.name
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN associated with EKS cluster"
  value       = aws_iam_role.eks_cluster_role.arn
}

output "node_group_iam_role_name" {
  description = "IAM role name associated with EKS node group"
  value       = aws_iam_role.eks_node_role.name
}

output "node_group_iam_role_arn" {
  description = "IAM role ARN associated with EKS node group"
  value       = aws_iam_role.eks_node_role.arn
}

output "aws_load_balancer_controller_iam_role_arn" {
  description = "IAM role ARN for AWS Load Balancer Controller"
  value       = aws_iam_role.aws_load_balancer_controller_role.arn
}

output "external_dns_iam_role_arn" {
  description = "IAM role ARN for External DNS"
  value       = aws_iam_role.external_dns_role.arn
}

# S3 Outputs
output "s3_bucket_id" {
  description = "S3 bucket ID for artifacts"
  value       = aws_s3_bucket.streamflow_artifacts.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN for artifacts"
  value       = aws_s3_bucket.streamflow_artifacts.arn
}

output "s3_bucket_domain_name" {
  description = "S3 bucket domain name"
  value       = aws_s3_bucket.streamflow_artifacts.bucket_domain_name
}

output "s3_bucket_hosted_zone_id" {
  description = "S3 bucket hosted zone ID"
  value       = aws_s3_bucket.streamflow_artifacts.hosted_zone_id
}

# ECR Outputs
output "ecr_repository_urls" {
  description = "Map of ECR repository URLs"
  value = {
    for service, repo in aws_ecr_repository.streamflow_services : service => repo.repository_url
  }
}

output "ecr_repository_arns" {
  description = "Map of ECR repository ARNs"
  value = {
    for service, repo in aws_ecr_repository.streamflow_services : service => repo.arn
  }
}

# Security Group Outputs
output "eks_cluster_security_group_id" {
  description = "Security group ID for EKS cluster"
  value       = aws_security_group.eks_cluster_sg.id
}

output "eks_nodes_security_group_id" {
  description = "Security group ID for EKS worker nodes"
  value       = aws_security_group.eks_nodes_sg.id
}

output "rds_security_group_id" {
  description = "Security group ID for RDS database"
  value       = aws_security_group.rds_sg.id
}

output "elasticache_security_group_id" {
  description = "Security group ID for ElastiCache Redis"
  value       = aws_security_group.elasticache_sg.id
}

# CloudWatch Outputs
output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.streamflow_logs.name
}

output "cloudwatch_log_group_arn" {
  description = "CloudWatch log group ARN"
  value       = aws_cloudwatch_log_group.streamflow_logs.arn
}

# Configuration for kubectl
output "kubectl_config" {
  description = "kubectl config as a string"
  value = templatefile("${path.module}/kubeconfig-template.yaml", {
    cluster_name     = aws_eks_cluster.streamflow_cluster.name
    endpoint         = aws_eks_cluster.streamflow_cluster.endpoint
    ca_data          = aws_eks_cluster.streamflow_cluster.certificate_authority[0].data
    aws_region       = var.aws_region
  })
  sensitive = true
}

# Application URLs (when domain is configured)
output "application_urls" {
  description = "Application URLs"
  value = var.domain_name != "" ? {
    web_ui    = "https://streamflow.${var.domain_name}"
    api       = "https://api.streamflow.${var.domain_name}"
    grafana   = "https://grafana.streamflow.${var.domain_name}"
    prometheus = "https://prometheus.streamflow.${var.domain_name}"
  } : {}
}

# Connection strings (sensitive)
output "database_url" {
  description = "Database connection URL"
  value = format("postgresql://%s:%s@%s:%s/%s",
    aws_db_instance.streamflow_postgres.username,
    var.db_password,
    aws_db_instance.streamflow_postgres.endpoint,
    aws_db_instance.streamflow_postgres.port,
    aws_db_instance.streamflow_postgres.db_name
  )
  sensitive = true
}

output "redis_url" {
  description = "Redis connection URL"
  value = format("redis://:%s@%s:%s",
    var.redis_auth_token,
    aws_elasticache_replication_group.streamflow_redis.primary_endpoint_address,
    aws_elasticache_replication_group.streamflow_redis.port
  )
  sensitive = true
}

# Deployment information
output "deployment_info" {
  description = "Information for deploying to the cluster"
  value = {
    cluster_name = aws_eks_cluster.streamflow_cluster.name
    region       = var.aws_region
    environment  = var.environment
    project_name = var.project_name
  }
} 