# General Variables
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "streamflow"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

# VPC Variables
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.7.0/24", "10.0.8.0/24", "10.0.9.0/24"]
}

# EKS Variables
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "node_capacity_type" {
  description = "Type of capacity associated with the EKS Node Group. Valid values: ON_DEMAND, SPOT"
  type        = string
  default     = "ON_DEMAND"
}

variable "node_instance_types" {
  description = "List of instance types associated with the EKS Node Group"
  type        = list(string)
  default     = ["t3.large"]
}

variable "node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 3
}

variable "node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 10
}

variable "node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}

# RDS Variables
variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.4"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial amount of storage (in GB) to allocate for the DB instance"
  type        = number
  default     = 20
}

variable "db_max_allocated_storage" {
  description = "Maximum amount of storage (in GB) to allocate for the DB instance"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "streamflow"
}

variable "db_username" {
  description = "Username for the DB master user"
  type        = string
  default     = "streamflow_admin"
}

variable "db_password" {
  description = "Password for the DB master user"
  type        = string
  sensitive   = true
  default     = "changeme123!"
}

variable "db_backup_retention_period" {
  description = "Days to retain backups"
  type        = number
  default     = 7
}

variable "db_backup_window" {
  description = "Daily time range for automated backups"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Weekly time range for maintenance"
  type        = string
  default     = "Sun:04:00-Sun:05:00"
}

# Redis Variables
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

variable "redis_auth_token" {
  description = "Auth token for Redis"
  type        = string
  sensitive   = true
  default     = "changeme-redis-auth-token-123456789"
}

# Service Names for ECR
variable "service_names" {
  description = "List of service names for ECR repositories"
  type        = list(string)
  default     = [
    "ingestion",
    "analytics", 
    "dashboard",
    "alerting",
    "storage",
    "web-ui"
  ]
}

# Logging
variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 14
}

# Tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "StreamFlow"
    Environment = "dev"
    Owner       = "DevOps"
    Terraform   = "true"
  }
}

# Domain Configuration (optional)
variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID (required if domain_name is set)"
  type        = string
  default     = ""
}

# Application Configuration
variable "app_config" {
  description = "Application configuration"
  type = object({
    replicas = object({
      ingestion  = number
      analytics  = number
      dashboard  = number
      alerting   = number
      storage    = number
      web_ui     = number
    })
    resources = object({
      ingestion = object({
        cpu_request    = string
        memory_request = string
        cpu_limit      = string
        memory_limit   = string
      })
      analytics = object({
        cpu_request    = string
        memory_request = string
        cpu_limit      = string
        memory_limit   = string
      })
      dashboard = object({
        cpu_request    = string
        memory_request = string
        cpu_limit      = string
        memory_limit   = string
      })
      alerting = object({
        cpu_request    = string
        memory_request = string
        cpu_limit      = string
        memory_limit   = string
      })
      storage = object({
        cpu_request    = string
        memory_request = string
        cpu_limit      = string
        memory_limit   = string
      })
      web_ui = object({
        cpu_request    = string
        memory_request = string
        cpu_limit      = string
        memory_limit   = string
      })
    })
  })
  default = {
    replicas = {
      ingestion  = 2
      analytics  = 2
      dashboard  = 2
      alerting   = 2
      storage    = 2
      web_ui     = 2
    }
    resources = {
      ingestion = {
        cpu_request    = "100m"
        memory_request = "128Mi"
        cpu_limit      = "500m"
        memory_limit   = "512Mi"
      }
      analytics = {
        cpu_request    = "200m"
        memory_request = "256Mi"
        cpu_limit      = "1000m"
        memory_limit   = "1Gi"
      }
      dashboard = {
        cpu_request    = "100m"
        memory_request = "128Mi"
        cpu_limit      = "500m"
        memory_limit   = "512Mi"
      }
      alerting = {
        cpu_request    = "100m"
        memory_request = "128Mi"
        cpu_limit      = "500m"
        memory_limit   = "512Mi"
      }
      storage = {
        cpu_request    = "200m"
        memory_request = "256Mi"
        cpu_limit      = "1000m"
        memory_limit   = "1Gi"
      }
      web_ui = {
        cpu_request    = "50m"
        memory_request = "64Mi"
        cpu_limit      = "200m"
        memory_limit   = "256Mi"
      }
    }
  }
}

# Monitoring and Observability
variable "enable_monitoring" {
  description = "Enable monitoring stack (Prometheus, Grafana)"
  type        = bool
  default     = true
}

variable "enable_logging" {
  description = "Enable centralized logging (ELK stack)"
  type        = bool
  default     = true
}

variable "enable_tracing" {
  description = "Enable distributed tracing (Jaeger)"
  type        = bool
  default     = false
}

# Networking
variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway for all private subnets"
  type        = bool
  default     = false
}

# Security
variable "enable_network_policy" {
  description = "Enable Kubernetes network policies"
  type        = bool
  default     = true
}

variable "enable_pod_security_policy" {
  description = "Enable Pod Security Policies"
  type        = bool
  default     = true
}

# Auto Scaling
variable "enable_cluster_autoscaler" {
  description = "Enable cluster autoscaler"
  type        = bool
  default     = true
}

variable "enable_horizontal_pod_autoscaler" {
  description = "Enable horizontal pod autoscaler"
  type        = bool
  default     = true
}

variable "enable_vertical_pod_autoscaler" {
  description = "Enable vertical pod autoscaler"
  type        = bool
  default     = false
} 