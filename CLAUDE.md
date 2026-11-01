# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

CMS is a portfolio project: a user management web app on AWS, provisioned
with Terraform, packaged with Docker and delivered through GitHub Actions.

- There is only one environment, `dev01`. It is built, tested and fixed until
  the system works end to end, then destroyed. There is no prd environment.
- Architecture diagram: `20261003_02_high_level_architecture.png` (repo root)

### Tech Stack

- **API** (`src/api`): Python 3.13, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, pytest, ruff, mypy
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

The `Makefile` is still empty: the `bootstrap` and `check` targets are added by the first story (US01).

Terraform version: specified in `.terraform-version`

## Directory Structure and Architecture

The repository follows a hierarchical structure based on resource scope:

```
awsenv/
|-- dev/
    |-- singleton/          # AWS account-level resources
        |-- tfvars/
    |-- group/              # VPC-level resources
        |-- tfvars/         # lean.tfvars (1 NAT gateway), full.tfvars (2 NAT gateways)
    |-- env/                # Smallest environment unit (dev01)
        |-- tfvars/         # dev01.tfvars (lean), dev01_full.tfvars (full)
modules/                    # Reusable Terraform child modules
src/
|-- api/                    # FastAPI backend + Alembic migrations
|-- web/                    # React frontend
tests/                      # QA-owned tests: api/, infra/, web/, dev01/ (layout in AGENTS.md)
docs/specs/                 # Spec and Basic Design (spec-001.md), function list
docs/plans/                 # Story plans with the detailed design (<story>.plan.md)
docs/design/                # Other design documents
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
3. Environment differences are managed using `.tfvars` files: `awsenv/dev/env/tfvars/` for the env layer, and `awsenv/dev/group/tfvars/` for the NAT gateway count of the group layer. A profile (lean or full) is one file in each of the two layers
4. Terraform workspaces manage tfstate for the env layer
5. Modules are organized by **function/purpose**, not by AWS resource type
6. **Dependency rule**: Higher-level modules (singleton) cannot depend on lower-level modules (env), but env can depend on singleton
7. Only CloudFront and the ALB are public; the app runs in private subnets and the database in isolated subnets

### State Management

- Backend: S3 with native state locking (`use_lockfile = true`), no DynamoDB table
- State separation: Uses Terraform workspaces
- Backend bucket: `cms-terraform-state-store` (bootstrapped once, outside the layers), region ap-southeast-1 (`region = "ap-southeast-1"` in every backend block)
- AWS profile: `3tier`

## Common Terraform Commands

### Local development

Navigate to the appropriate directory (`awsenv/dev/env`, `awsenv/dev/group`, `awsenv/dev/singleton`):

```bash
export AWS_PROFILE=3tier
export AWS_REGION=ap-southeast-1

# Initialize (required before first use)
terraform init -upgrade

# Select workspace (for env layer)
export TF_WORKSPACE=dev01
# OR
terraform workspace select dev01

# Plan changes (env layer with tfvars)
terraform plan -var-file=tfvars/dev01.tfvars        # lean sizing, used while fixing bugs
terraform plan -var-file=tfvars/dev01_full.tfvars   # full sizing, final verification only

# Plan changes (group layer with tfvars)
terraform plan -var-file=tfvars/lean.tfvars         # lean: 1 NAT gateway
terraform plan -var-file=tfvars/full.tfvars         # full: 2 NAT gateways, final verification only

# Plan changes (singleton layer without tfvars)
terraform plan

# Apply changes
terraform apply -var-file=tfvars/dev01.tfvars   # for env
terraform apply -var-file=tfvars/lean.tfvars    # for group
terraform apply                                 # for singleton

# Format code
terraform fmt -recursive
```

Apply order: singleton -> group -> env. Destroy in reverse order: env -> group (-> singleton).

- Every build, check and destroy session ends by destroying env, then group, with the same profile files they were applied with. Singleton is destroyed only at the final teardown.
- Profile switch (lean <-> full): apply group, then env, each with that profile's file (`lean.tfvars` with `dev01.tfvars`, `full.tfvars` with `dev01_full.tfvars`). No `.tf` file changes.
- Plans that must report no changes (after an apply or a CD run, or the lean check of COST-AC02) are run during office hours: out of hours the schedule has set the ECS scalable target to 0, and the plan shows it as a change.

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

# Check command (from the repo root): API, web and Terraform lint, type check, tests and build.
# What it runs is defined in AGENTS.md, "The check command"
make check

# API (from src/api)
pytest
ruff check .
ruff format --check .
mypy
alembic upgrade head                            # apply migrations
alembic revision --autogenerate -m "<message>"  # create a migration from model changes

# Web UI (from src/web)
npm run lint
npm run typecheck
npm run build
```

Database schema changes always go through an Alembic migration; never change the schema by hand.

Coding conventions for Python, database and Alembic migrations, Dockerfile, TypeScript/React, Terraform, GitHub Actions and the test layout: `AGENTS.md`, "Coding convention" (one source for Claude Code and Codex). `docs/kickoff.md` summarises them and records the kick-off decisions (KO-n).

Testing notes:
- Hours-long timers (8-hour session, 24-hour temporary password, the lock after 60 minutes) are proven by automated tests with a controlled clock, not waited out on `dev01` (D-PM3).
- The stop and start cycle is checked on `dev01` with a test schedule set a few minutes ahead, not at the real 18:00 and 08:45 ICT times; the schedule is reset to 18:00 and 08:45 afterwards (OQ-1).

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
- `api_test.yml` - API lint and format check (ruff), type check (mypy), tests (pytest): the API part of `make check`
- `web_build.yml` - UI lint, type check and build: the web part of `make check`
- `protect_tests.yml` - Fails a pull request from a `feature/` branch if any commit other than QA's `test(...)` commits changes `tests/`

### Application Delivery
- `image_build_push_dev.yml` - Docker build, Trivy image scan, push to ECR tagged with commit SHA
- `deploy_ecs_dev.yml` - Run Alembic migration task, ECS rolling update, post-deploy smoke test
- `deploy_web_dev.yml` - Sync UI build to S3 and invalidate CloudFront

### Infrastructure Operations
- `create_terraform_workspace_dev.yml` - Create new workspaces

### Pipeline flow
- Pull request: API and UI checks, `terraform fmt` / `validate` / `plan`, tflint, Trivy config and image scans
- Merge to `develop`: no automatic deploy
- CD (manual, started by hand by the Owner on `develop`): pre-flight check first, which stops the run before any change outside office hours (weekend, after 17:30 ICT on a weekday, 0 ECS tasks or RDS not available); then push image, `terraform apply`, migrate, deploy to `dev01`, smoke test
- Every workflow gets AWS credentials through OIDC (`aws-actions/configure-aws-credentials`) with `aws-region: ap-southeast-1`

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

- Default region for everything: ap-southeast-1. This covers the default Terraform provider in every layer, the S3 backend, the AWS CLI (`AWS_REGION=ap-southeast-1` next to `AWS_PROFILE=3tier` locally) and the GitHub Actions OIDC credentials step (`aws-region: ap-southeast-1`)
- Aliased provider `us_east_1`: only for four resources: the CloudFront ACM certificate, the CloudFront WAF web ACL, the CloudWatch alarm on the web ACL's blocked requests, and one EventBridge rule that forwards that alarm's state changes to the default event bus in ap-southeast-1. The alarm and the rule live in `modules/monitoring` (IAC-AC09)
- AWS profile `3tier` for local runs, supplied through `AWS_PROFILE`. Provider and backend blocks name no profile, so GitHub Actions uses its OIDC credentials with the same code

## Monitoring

All alarms, dashboards, log metric filters and EventBridge rules live in `modules/monitoring`, called from the env layer. The SNS alert topic lives in the group layer. See OBS-AC05 in `docs/specs/spec-001.md` for the alarm list and thresholds.

## Cost

- AWS Budget alert: $2 per month (80% at $1.60, 100% at $2). It is an early signal, not a cap: singleton alone uses part of it each month and Budgets data lags several hours
- The env and group layers exist only for a build, check and destroy session and are destroyed at its end. Only singleton stays between sessions
- Lean sizing (`group/tfvars/lean.tfvars` and `env/tfvars/dev01.tfvars`) while iterating; full sizing (`group/tfvars/full.tfvars` and `env/tfvars/dev01_full.tfvars`) only for the final verification, applied and removed within office hours on the same weekday
- Final teardown: destroy env, group and singleton, then follow the clean-up checklist required by TDN-AC02 in `docs/specs/spec-001.md`

## Design Documentation

The Basic Design is in `docs/specs/spec-001.md`, and each story's detailed design is in its plan, `docs/plans/<story>.plan.md`. Other design documents are stored in `docs/design/` with naming convention:
`YYYYMMDD_NN_<description>.md`

Always reference design documents when implementing significant infrastructure changes.

## Main Branch and PRs
Full rules: `docs/kickoff.md`, "Git branching rules".
- Main branch for PRs: `develop`, the only long-lived branch. There is no `main` branch; releases and baselines are annotated tags on `develop` (`baseline-<n>`, `v1.0.0` at G7)
- Branch naming follows format: `feature/<story>_<summary>` (for example `feature/US01_user_list`), one branch per feature, created before implementation. Process, design and fix work uses the same form with its own ID: `PROC<nn>`, `DES<nn>`, `FIX<nn>`, `CR<nnn>` (for example `feature/PROC06_kickoff`)
- Pull requests are merged into `develop` with a merge commit (`gh pr merge --merge`), never squashed or rebased; agents never push to `develop` directly or force-push it, only the Owner may force-push, by hand (KO-23)
- Worktrees sit next to the repository: `wt-<story>-dev<k>` for a Dev (the `protect-tests` hook relies on the `wt-` prefix), `wt-<ID>` for other agent work
- After a merge the local branch and worktree are removed; the remote branch is kept unless the Owner decides otherwise (a `/story` run deletes its own, as the skill describes)
- Global rules for every agent: `.claude/rules/global.md` (Owner approval before any action and any commit; commit messages follow `.gitmessage`)
- Merges to `develop` do not deploy; the Owner runs the CD workflows by hand
- Story runs: `/story <story>` (`.claude/skills/story/SKILL.md`) builds, reviews, tests and, on the approver's `APPROVE`, merges one story's PR into `develop`. `/story next` picks the next ready story from `docs/backlog.md`, claims it and asks the Owner to confirm, so parallel sessions never take the same story. Board: `cd factory && python3 -m http.server`, then open `dashboard.html`
