# Deployment stack summary — Slack Analysis

This document explains the deployment technologies used in Task 5 and how they fit together.

## The deployment pipeline

```text
Developer push
     │
     ▼
GitHub Actions (CI) ──► flake8, tests, docstrings
     │
     ▼
GitHub Actions (CD) ──► Docker build ──► Docker Hub
     │
     ▼
Cloud runtime (future) ──► ECS / Kubernetes / Lambda
     ▲
     │
Terraform (AWS) ──► S3 artifacts + ECR repositories
```

## 1. Docker

**What it is:** Packages your app and its dependencies into a portable **image**.

**Why we use it:** The dashboard runs the same on your laptop, in CI, and in the cloud.

| Image | Dockerfile | Runs |
|-------|------------|------|
| Dashboard | `Dockerfile` | Streamlit on port 8501 |
| API | `Dockerfile.api` | FastAPI on port 8000 |

**Local commands:**

```bash
make docker-build
make docker-run
make stack-up    # databases + dashboard + API
```

## 2. Continuous Integration (CI)

Already in `.github/workflows/`:

- `unittests.yml` — pytest on every push
- `flake8_check.yml` — linting
- `docstring_tests.yml` — documentation coverage

**CI answers:** “Is the code safe to merge?”

## 3. Continuous Deployment (CD)

New workflow: `.github/workflows/cd_docker.yml`

**CD answers:** “Can we ship a runnable artifact?”

On push to `main` / `task-*` (after tests pass):

1. Build the dashboard Docker image
2. Push to **Docker Hub** as `YOUR_USERNAME/slack-analysis:latest`

**Required GitHub secrets:**

| Secret | Purpose |
|--------|---------|
| `DOCKER_USERNAME` | Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub access token |

Create token: Docker Hub → Account Settings → Security → New Access Token.

## 4. Terraform (Infrastructure as Code)

**What it is:** Declarative scripts that **create cloud resources** reproducibly.

**Our hello-world stack** (`terraform/`):

| Resource | Purpose |
|----------|---------|
| `aws_s3_bucket` | Store ML artifacts, exports, deployment files |
| `aws_ecr_repository` (×2) | Private Docker registries for dashboard + API images |

**Why S3 + ECR?** Common pattern: build images in CI, push to ECR (or Docker Hub), store data/models in S3.

**Commands:**

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # edit bucket name
terraform init
terraform plan
terraform apply
```

Requires AWS credentials (`aws configure` or environment variables).

## 5. Serverless (AWS Lambda) — future step

**What it is:** Run code without managing servers; pay per invocation.

**Fit for this project:** Lightweight API endpoints (e.g. `/api/overview`) could run on Lambda behind API Gateway. The Streamlit dashboard is less suited to Lambda (long-lived UI); containers (ECS/Kubernetes) fit better.

**CD extension (commented pattern in workflow):** After Docker push, trigger `aws ecs update-service` or deploy a Lambda from the API image.

## 6. Kubernetes / ECS (container orchestration)

**What it is:** Runs multiple Docker containers across machines with scaling, health checks, and rolling updates.

| Option | Owner | Best for |
|--------|-------|----------|
| **Docker Compose** | Local dev | Laptop full stack |
| **ECS (Fargate)** | AWS managed | Production without managing K8s |
| **Kubernetes** | Portable / self-managed | Large teams, multi-cloud |

Our `docker-compose.yml` + Terraform ECR repos are the stepping stones toward ECS/Kubernetes.

## How everything connects

| Layer | Tool | This project |
|-------|------|--------------|
| Code | Python | `src/`, `dashboard/` |
| CI | GitHub Actions | Tests on every push |
| CD | GitHub Actions + Docker | Image to Docker Hub |
| Registry | Docker Hub / ECR | Store built images |
| Data | PostgreSQL + MongoDB | Feature store + archive |
| IaC | Terraform | S3 + ECR on AWS |
| UI | Streamlit container | Port 8501 |
| API | FastAPI container | Port 8000 |

## Task 5 checklist

- [x] Dockerfile for the application
- [x] GitHub Action CD workflow (Docker Hub push)
- [x] Terraform hello-world AWS stack
- [x] Deployment technology summary (this document)

## Suggested commit

```bash
git add Dockerfile Dockerfile.api .dockerignore docker-compose.yml \
  .github/workflows/cd_docker.yml terraform/ docs/deployment_summary.md \
  docs/task5_deployment_guide.md Makefile tests/test_deployment.py
git commit -m "feat: add Docker CD pipeline and AWS Terraform stack for Task 5"
git push -u origin task-5
```
