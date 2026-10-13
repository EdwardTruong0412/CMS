# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

UserHub is a portfolio project: a user management web app on AWS, provisioned
with Terraform, packaged with Docker and delivered through GitHub Actions.

- There is only one environment, `dev01`. It is built, tested and fixed until
  the system works end to end, then destroyed. There is no prd environment.
- Architecture diagram: `20261003_02_high_level_architecture.png` (repo root)

### Tech Stack

- **API** (`src/api`): Python 3.13, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, pytest, ruff
- **Web UI** (`src/web`): React + TypeScript, built with Vite
- **Container**: multi-stage Dockerfile on `python:3.13-slim`, non-root user
- **AWS** (ap-southeast-1): Route 53, CloudFront, WAF, ACM, S3, ALB, ECS Fargate,
  RDS PostgreSQL, ECR, Secrets Manager, KMS, CloudWatch, SNS, CloudTrail,
  GuardDuty, AWS Budgets
- **IaC**: Terraform, version pinned in `.terraform-version`
- **CI/CD**: GitHub Actions on GitHub-hosted runners, AWS access through OIDC (no static keys)

## Required Tools

Install required tools using the Makefile:
```bash
make bootstrap # Installs tfenv, trivy, tflint, drawio
```

Terraform version: specified in `.terraform-version`

## Directory Structure and Architecture

The repository follows a hierarchical structure based on resource scope:

```
awsenv/
|-- dev/
    |-- singleton/          # AWS account-level resources
        |-- tfvars/
    |-- group/              # VPC-level resources
        |-- tfvars/
    |-- env/                # Smallest environment unit (dev01)
        |-- tfvars/         # dev01.tfvars (lean), dev01_full.tfvars (full)
modules/                    # Reusable Terraform child modules
src/
|-- api/                    # FastAPI backend + Alembic migrations
|-- web/                    # React frontend
docs/design/                # Design documents
```

### Directory Hierarchy

- **awsenv/**: AWS account environments (dev only)
- **singleton/**: Resources required once per AWS account (GitHub OIDC provider and CI role, CloudTrail, GuardDuty, AWS Budget, ECR repository, Route 53 hosted zone)
- **group/**: Resources shared per VPC (VPC, subnets, NAT gateways, SNS alert topic)
- **env/**: Resources for the environment unit (ACM, CloudFront, WAF, S3 UI bucket, ALB, ECS, RDS, Secrets Manager, KMS, monitoring, DNS records)
- **modules/**: Reusable Terraform module implementations

### Key Architecture Principles

1. **Root modules** are in `awsenv/` directory
2. **Child modules** are in `modules/` directory and called from root modules
3. Environment differences are managed using `.tfvars` files in `awsenv/dev/env/tfvars/`
4. Terraform workspaces manage tfstate for the env layer
5. Modules are organized by **function/purpose**, not by AWS resource type
6. **Dependency rule**: Higher-level modules (singleton) cannot depend on lower-level modules (env), but env can depend on singleton
7. Only CloudFront and the ALB are public; the app runs in private subnets and the database in isolated subnets

### State Management

- Backend: S3 with native state locking (`use_lockfile = true`), no DynamoDB table
- State separation: Uses Terraform workspaces
- Backend bucket: `user-hub-terraform-state-store` (bootstrapped once, outside the layers)
- AWS profile: `3tier`

## Common Terraform Commands

### Local development

Navigate to the appropriate directory (`awsenv/dev/env`, `awsenv/dev/group`, `awsenv/dev/singleton`):

```bash
export AWS_PROFILE=3tier

# Initialize (required before first use)
terraform init -upgrade

# Select workspace (for env layer)
export TF_WORKSPACE=dev01
# OR
terraform workspace select dev01

# Plan changes (env layer with tfvars)
terraform plan -var-file=tfvars/dev01.tfvars        # lean sizing, used while fixing bugs
terraform plan -var-file=tfvars/dev01_full.tfvars   # full sizing, final verification only

# Plan changes (group/singleton layers without tfvars)
terraform plan

# Apply changes
terraform apply -var-file=tfvars/dev01.tfvars   # for env
terraform apply                                 # for group/singleton

# Format code
terraform fmt -recursive
```

Apply order: singleton -> group -> env. Destroy in reverse order: env -> group (-> singleton).

### Validation and Linting

```bash
# Validate Terraform configuration
terraform validate

# Run tflint (from repository root or specific directory)
tflint

# Run security scan with trivy
trivy config .
```

## Application Commands

```bash
# Run API, PostgreSQL and UI dev server locally
docker compose up

# API (from src/api)
pytest
ruff check .
alembic upgrade head                            # apply migrations
alembic revision --autogenerate -m "<message>"  # create a migration from model changes

# Web UI (from src/web)
npm run lint
npm run build
```

Database schema changes always go through an Alembic migration; never change the schema by hand.

## Workspace Management

The env layer has a single workspace: `dev01`.

```bash
# List workspaces
terraform workspace list

# Create new workspace
terraform workspace new <workspace-name>

# Switch workspace
terraform workspace select <workspace-name>
```

Always specify the workspace when working with env layer resources using the `TF_WORKSPACE` environment variable or `terraform workspace select`.

## GitHub Actions Workflows

### Terraform Operation (per layer)
- `terraform_plan_dev_{env|group|singleton}.yml` - Plan changes
- `terraform_apply_dev_{env|group|singleton}.yml` - Apply changes
- `terraform_destroy_dev_{env|group}.yml` - Destroy resources
- `terraform_validate_dev_{env|group|singleton}.yml` - Validate configuration
- `terraform_force_unlock_dev.yml` - Force unlock state

### Code Quality
- `terraform_fmt.yml` - Format checking
- `tflint_dev_{env|group|singleton}.yml` - Linting
- `trivy_dev_{env|group|singleton}.yml` - Security scanning
- `trivy_modules.yml` - Security scan for modules
- `api_test.yml` - API lint (ruff) and tests (pytest)
- `web_build.yml` - UI lint and build

### Application Delivery
- `image_build_push_dev.yml` - Docker build, Trivy image scan, push to ECR tagged with commit SHA
- `deploy_ecs_dev.yml` - Run Alembic migration task, ECS rolling update, post-deploy smoke test
- `deploy_web_dev.yml` - Sync UI build to S3 and invalidate CloudFront

### Infrastructure Operations
- `create_terraform_workspace_dev.yml` - Create new workspaces

### Pipeline flow
- Pull request: API and UI checks, `terraform fmt` / `validate` / `plan`, tflint, Trivy config and image scans
- Merge to `develop`: push image, `terraform apply`, migrate, deploy to `dev01`, smoke test

## Module Development Guidelines

1. Always create child modules in `modules/` directory
2. Never create resources directly in `awsenv/` root modules - always use child modules
3. Group resources by function/purpose, not by AWS resource type (even if it creates some duplication)
4. Prioritize limiting module modification impact and readability over DRY principle
5. Each module should have a README.md following `modules/README_TEMPLATE.md` structure

## TFLint Configuration
`.tflint.hcl` enforces:
- `terraform_naming_convention` - Enable for consistent naming
- `terraform_documented_variables` - Variables must have descriptions
- `terraform_documented_outputs` - Outputs must have descriptions
- `terraform_required_version` - Disabled (managed at module call level)
- `terraform_required_providers` - Disabled (managed at module call level)

## AWS Provider Configuration

- Default provider: ap-southeast-1
- Aliased provider `us_east_1`: only for the CloudFront ACM certificate and the CloudFront WAF web ACL
- All providers use AWS profile: `3tier`

## Monitoring

All alarms, dashboards, log metric filters and EventBridge rules live in `modules/monitoring`, called from the env layer. The SNS alert topic lives in the group layer. See section 8 of the requirements document for the alarm list and thresholds.

## Cost

- Lean sizing (`dev01.tfvars`) while iterating; full sizing (`dev01_full.tfvars`) only for the final verification
- AWS Budget alert: $10
- Destroy the environment after verification and follow the clean-up checklist in the requirements document

## Design Documentation

Design documents are stored in `docs/design/` with naming convention:
`YYYYMMDD_NN_<description>.md`

Always reference design documents when implementing significant infrastructure changes.

## Main Branch and PRs
- Main branch for PRs: `develop`
- Branch naming follows format: `feature/<summary_description>`
- Merges to `develop` deploy to `dev01` automatically
