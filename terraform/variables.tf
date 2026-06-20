variable "aws_region" {
  description = "AWS region for deployment resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "slack-analysis"
}

variable "environment" {
  description = "Deployment environment label (dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "artifact_bucket_name" {
  description = "Globally unique S3 bucket name for ML artifacts and deployment files."
  type        = string
}
