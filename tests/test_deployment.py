"""Smoke tests for Task 5 deployment artifacts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_exists():
    """Dashboard Dockerfile should be present for CD."""
    assert (ROOT / 'Dockerfile').is_file()


def test_cd_workflow_exists():
    """CD workflow should build and push Docker images."""
    workflow = ROOT / '.github' / 'workflows' / 'cd_docker.yml'
    assert workflow.is_file()
    content = workflow.read_text(encoding='utf-8')
    assert 'docker/build-push-action' in content
    assert 'DOCKER_USERNAME' in content


def test_terraform_main_resources():
    """Terraform should define AWS foundation resources."""
    main_tf = (ROOT / 'terraform' / 'main.tf').read_text(encoding='utf-8')
    assert 'aws_s3_bucket' in main_tf
    assert 'aws_ecr_repository' in main_tf


def test_deployment_summary_exists():
    """Deployment summary document should be available."""
    assert (ROOT / 'docs' / 'deployment_summary.md').is_file()
