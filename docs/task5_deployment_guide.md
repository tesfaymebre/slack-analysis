# Task 5: Deployment Guide

Quick reference for running and shipping the Slack Analysis stack.

## Local Docker

```bash
# Build dashboard image
make docker-build

# Run dashboard (needs databases — run make db-up && make db-load first)
make docker-run

# Full stack: MongoDB + PostgreSQL + dashboard + API
make stack-up
```

Dashboard: http://localhost:8501  
API: http://localhost:8000/docs

## GitHub CD setup

1. Create a [Docker Hub](https://hub.docker.com) account
2. Create an access token (read/write)
3. In your GitHub repo → **Settings → Secrets → Actions**, add:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
4. Push to `main` or `task-5` — workflow `.github/workflows/cd_docker.yml` runs tests, then pushes the image

Pull your image anywhere:

```bash
docker pull YOUR_USERNAME/slack-analysis:latest
docker run -p 8501:8501 \
  -e POSTGRES_DSN=postgresql://slack:slack@host.docker.internal:5433/slack_features \
  -e MONGO_URI=mongodb://host.docker.internal:27017 \
  YOUR_USERNAME/slack-analysis:latest
```

## Terraform (AWS)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Set a globally unique artifact_bucket_name

terraform init
terraform plan
terraform apply
```

Outputs include ECR URLs for future ECS/Kubernetes deployment.

## Learn more

See `docs/deployment_summary.md` for how Docker, CI/CD, Terraform, serverless, and Kubernetes relate.
