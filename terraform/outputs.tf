output "artifact_bucket_name" {
  description = "S3 bucket storing deployment and ML artifacts."
  value       = aws_s3_bucket.artifacts.bucket
}

output "dashboard_ecr_repository_url" {
  description = "ECR repository URL for the Streamlit dashboard image."
  value       = aws_ecr_repository.dashboard.repository_url
}

output "api_ecr_repository_url" {
  description = "ECR repository URL for the FastAPI backend image."
  value       = aws_ecr_repository.api.repository_url
}

output "aws_region" {
  description = "Region where resources were created."
  value       = var.aws_region
}
