# Plan: US01b State bucket, singleton and group

| | |
| --- | --- |
| Story | US01b State bucket, singleton and group (`docs/backlog.md#us01b`) |
| Criteria owned | IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01, NET-AC02 (text in `docs/specs/spec-001.md`, "IAC" and "NET") |
| Functions | F-OPS-08 Bootstrap and rebuild (`docs/specs/function-list.md`; Q-D11) |
| Depends on | US01a (`make check`, `.tflint.hcl`, pytest configuration) |
| Dev | **Dev 1** (SP1-D1, lane "Terraform and pipeline") |
| Branch | `feature/US01b_state_singleton_group`, created by the Dev Lead from `develop` **after US01a is merged** (QA's `tests/infra` run through US01a's `make check`) |
| Worktree (story run) | `../wt-US01b-dev1` |
| Size | M (1.5 to 2 days) |
| Author | Dev Lead, 2026-11-02 (task DES03), for G4 |
| Inputs read | `docs/backlog.md` (US01a to US05), spec-001 (IAC, NET, CNT, COST, TDN groups, NFR, BD-1 to BD-9, Decisions log), `docs/specs/function-list.md`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, `docs/kickoff.md`, `docs/project-plan.md`, `reports/sprints/sprint-1-planning.md`, `reports/handoff/PROC08-dev-lead-summary.md`, `reports/handoff/PROC12-pm-scrum-master-summary.md`, `.claude/skills/story/SKILL.md`, `.claude/agents/approver.md`, `.claude/agents/reviewer-infra.md`, `docs/plans/US01a.plan.md`, the current repository (no `modules/`, no `awsenv/` files, no `modules/README_TEMPLATE.md`) |

## 1. Goal

After this story, the repository contains:
- a documented, idempotent script that creates the versioned Terraform state bucket `cms-terraform-state-store`, and its runbook;
- the module README template;
- the singleton root module (ECR repository and Route 53 hosted zone);
- the group root module (VPC across two availability zones with public, private and isolated subnets, NAT count from the profile file).

Every resource is in a documented child module. The project tag comes from provider `default_tags`, and state is locked with the S3 lock file.

Nothing is applied by the story run. After the merge, the Owner runs the script and applies singleton from a local shell. Group is applied only in check sessions (Session 1, Wed 2026-11-18) and destroyed at the end of each.

Out of scope:
- the env layer and `awsenv/dev/env/` (US01c);
- the SNS topic and the budget (US02);
- the OIDC provider and CI roles (US05);
- CloudTrail and GuardDuty (US14);
- the session runbook (US01c), workflows (US03, US05) and the Trivy ignore file (US05).

## 2. Tasks

Each task lists its goal, what to read, what to write, its boundaries, the detailed design and the criteria it serves. Write only the files a task names. Do not edit anything under `tests/` (QA's, committed before you start). Do not run `terraform apply`, `plan` against AWS, `destroy`, `import`, `state`, any AWS CLI command, or the bootstrap script: there is no AWS access in a story run.

### T0 [QA] Tests first (QA, before the Dev starts)

- Goal: `tests/infra/` for the static parts of every criterion, and `tests/dev01/` for the parts that need AWS, committed as `test(US01b): ...` on the story branch. See section 7 "For QA".

### T1 [Infra] Module README template

- Goal: the template every module README follows (IAC-AC04).
- Read: `CLAUDE.md` ("Module Development Guidelines"), `AGENTS.md` ("Terraform").
- Write: `modules/README_TEMPLATE.md`.
- Boundaries: exactly the headings below; no other `##` heading.
- Criteria served: IAC-AC04.

Content, with a one-line instruction under each heading saying what to write there:

```markdown
# <module_name>

<One sentence: what the module creates and why.>

## Purpose
## Layer and callers
## Resources
## Inputs
## Outputs
## Example
## Security
## Cost
## Teardown
```

The headings are the nine `## ` lines. The H1 is the module's directory name and differs per module, so it is not part of the IAC-AC04 comparison.

### T2 [Infra] Singleton modules and root

- Goal: the ECR repository and the hosted zone in the singleton layer, behind two documented modules.
- Read: `AGENTS.md` ("Terraform"), `CLAUDE.md` ("Directory Structure", "State Management", "AWS Provider Configuration"), spec IAC-AC03, IAC-AC14, Q-D6, Q-D9 (ECR AES256), Q-D12, D-DL9, NET-AC11 (zone name).
- Write:
  - `modules/container_registry/main.tf`, `variables.tf`, `outputs.tf`, `README.md`;
  - `modules/dns_zone/main.tf`, `variables.tf`, `outputs.tf`, `README.md`;
  - `awsenv/dev/singleton/versions.tf`, `providers.tf`, `backend.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `.terraform.lock.hcl`.
- Boundaries:
  - no `resource` block in `awsenv/`;
  - no `tags` argument other than the `Name` exception of US01b-D5 (and none is needed in these two modules);
  - no other provider, no `us_east_1` alias (US01c);
  - no `tfvars` directory for singleton (it has no variables);
  - no repository policy and no IAM.
- Criteria served: IAC-AC03, IAC-AC04, IAC-AC07 (backend), IAC-AC14.

Detailed design:

1. `versions.tf` (identical in both roots):

   ```hcl
   terraform {
     required_version = "~> 1.16.4"

     required_providers {
       aws = {
         source  = "hashicorp/aws"
         version = "~> 6.71"
       }
     }
   }
   ```
2. `providers.tf` (identical in both roots). No `profile`: the Owner supplies `AWS_PROFILE=3tier`, CI uses OIDC.

   ```hcl
   provider "aws" {
     region = "ap-southeast-1"

     default_tags {
       tags = {
         Project   = "cms"
         ManagedBy = "terraform"
       }
     }
   }
   ```
3. `backend.tf`:

   ```hcl
   terraform {
     backend "s3" {
       bucket       = "cms-terraform-state-store"
       key          = "singleton/terraform.tfstate"
       region       = "ap-southeast-1"
       use_lockfile = true
       encrypt      = true
     }
   }
   ```

   There is no `dynamodb_table` and no `profile`. The group root uses the same block with `key = "group/terraform.tfstate"`.
4. `main.tf`:

   ```hcl
   module "container_registry" {
     source          = "../../../modules/container_registry"
     repository_name = "cms-api"
   }

   module "dns_zone" {
     source    = "../../../modules/dns_zone"
     zone_name = "cms.imaprof.ink"
   }
   ```
5. `variables.tf` holds only a comment saying singleton has no input variables; tflint's standard module structure expects the file. `outputs.tf`, each with a description:

   | Output | Value |
   | --- | --- |
   | `ecr_repository_name` | `module.container_registry.repository_name` |
   | `ecr_repository_arn` | `module.container_registry.repository_arn` |
   | `ecr_repository_url` | `module.container_registry.repository_url` |
   | `hosted_zone_id` | `module.dns_zone.zone_id` |
   | `hosted_zone_name` | `module.dns_zone.zone_name` |
   | `hosted_zone_name_servers` | `module.dns_zone.name_servers` |
6. `modules/container_registry`:
   - variables `repository_name` (`string`, validated against `^cms-[a-z0-9-]+$`) and `images_to_keep` (`number`, default `5`, validated `>= 1`);
   - `aws_ecr_repository.this` with `name = var.repository_name`, `image_tag_mutability = "IMMUTABLE"`, `force_delete = true` (Q-D12), `image_scanning_configuration { scan_on_push = true }` and `encryption_configuration { encryption_type = "AES256" }` (Q-D9);
   - `aws_ecr_lifecycle_policy.this` with two rules. Priority 1 expires untagged images 1 day after push. Priority 2, `tagStatus = "any"`, expires images beyond the `images_to_keep` most recent;
   - outputs `repository_name`, `repository_arn`, `repository_url`.
7. `modules/dns_zone`:
   - variable `zone_name` (`string`);
   - `aws_route53_zone.this` with `name = var.zone_name`, `comment = "CMS public hosted zone, delegated from Namecheap"` and `force_destroy = false` (US01b-D10);
   - outputs `zone_id`, `zone_name`, `name_servers`.
8. READMEs: each has every heading of `modules/README_TEMPLATE.md`, filled with this module's facts:
   - layer and callers: singleton, called from `awsenv/dev/singleton`;
   - inputs and outputs as tables;
   - security: tag immutability and scan on push for ECR; no DNSSEC for the zone;
   - cost: ECR storage about $0.10 per GB-month for at most 5 images; the zone $0.50 per month (estimates);
   - teardown: `force_delete`; the zone must be empty except NS and SOA; the Namecheap NS records are removed by the Owner (TDN-AC05).
9. Lock file: from the repository root, run `CHECKPOINT_DISABLE=1 terraform -chdir=awsenv/dev/singleton init -backend=false -input=false`, then `terraform -chdir=awsenv/dev/singleton providers lock -platform=darwin_arm64 -platform=linux_amd64`, then `terraform -chdir=awsenv/dev/singleton validate`.
   - `darwin_arm64` is the Owner's machine; `linux_amd64` is GitHub-hosted runners (US05).
   - `CHECKPOINT_DISABLE=1` stops Terraform from writing to `~/.terraform.d`, which the sandbox blocks.
   - Commit `.terraform.lock.hcl`; `.terraform/` stays ignored.

### T3 [Infra] Network module and group root

- Goal: the three-tier VPC across two availability zones, with the NAT count taken from the profile file (Q-O55).
- Read: `AGENTS.md` ("Terraform"), `CLAUDE.md` (principle 7, "Cost"), spec NET-AC01 to NET-AC03, NET-AC05, SCALE-AC01 to SCALE-AC03, Q-O55, BD-8.
- Write:
  - `modules/network/main.tf`, `variables.tf`, `outputs.tf`, `README.md`;
  - `awsenv/dev/group/versions.tf`, `providers.tf`, `backend.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `.terraform.lock.hcl`, `tfvars/lean.tfvars`, `tfvars/full.tfvars`.
- Boundaries:
  - no SNS topic or `alert_email` variable (US02);
  - no VPC endpoints, flow logs or NACL changes;
  - no security group other than closing the default one;
  - no data lookup of singleton (group reads nothing yet);
  - lean and full differ only in `tfvars/` (SCALE-AC03).
- Criteria served: NET-AC01, NET-AC02, IAC-AC03, IAC-AC04, IAC-AC07 (backend), IAC-AC14.

Detailed design:

1. Group root:
   - `versions.tf` and `providers.tf` as in T2. `backend.tf` as in T2 with `key = "group/terraform.tfstate"`.
   - `variables.tf`: `nat_gateway_count` with type `number`, no default, the description "Number of NAT gateways: 1 in the lean profile, 2 in the full profile (one per availability zone).", and a validation that it is 1 or 2.
   - `tfvars/lean.tfvars`: `nat_gateway_count = 1`. `tfvars/full.tfvars`: `nat_gateway_count = 2`. Nothing else in either file.
   - `main.tf`:

   ```hcl
   module "network" {
     source             = "../../../modules/network"
     name_prefix        = "cms"
     vpc_cidr           = "10.20.0.0/16"
     availability_zones = ["ap-southeast-1a", "ap-southeast-1b"]
     nat_gateway_count  = var.nat_gateway_count
   }
   ```
   - `outputs.tf`, each with a description, values from the module outputs of the same name: `vpc_id`, `vpc_cidr_block`, `availability_zones`, `public_subnet_ids`, `private_subnet_ids`, `isolated_subnet_ids`, `nat_gateway_ids`, `nat_public_ips`. Every list is ordered by availability zone (a, then b).
2. `modules/network` variables, all typed and described:
   - `name_prefix` (`string`, `^[a-z][a-z0-9-]*$`);
   - `vpc_cidr` (`string`, validated with `can(cidrhost(var.vpc_cidr, 0))`);
   - `availability_zones` (`list(string)`, length exactly 2);
   - `nat_gateway_count` (`number`, 1 or 2).
3. Address plan (US01b-D6), computed in the module with `cidrsubnet(var.vpc_cidr, 8, n)`. `i` is the zone index (0 for a, 1 for b), and the zone letter comes from the last character of the zone name:

   | Tier | n | ap-southeast-1a | ap-southeast-1b | Name tag |
   | --- | --- | --- | --- | --- |
   | public | `i` | 10.20.0.0/24 | 10.20.1.0/24 | `cms-public-a`, `cms-public-b` |
   | private (app) | `10 + i` | 10.20.10.0/24 | 10.20.11.0/24 | `cms-private-a`, `cms-private-b` |
   | isolated (DB) | `20 + i` | 10.20.20.0/24 | 10.20.21.0/24 | `cms-isolated-a`, `cms-isolated-b` |
4. Resources (a resource that is the only one of its type is `this`; others are named by role):

   | Address | Settings | Name tag |
   | --- | --- | --- |
   | `aws_vpc.this` | `cidr_block = var.vpc_cidr`, `enable_dns_support = true`, `enable_dns_hostnames = true` | `cms-vpc` |
   | `aws_default_security_group.this` | `vpc_id` only: no ingress and no egress rule, so the default group allows nothing | `cms-default-sg` |
   | `aws_internet_gateway.this` | `vpc_id` | `cms-igw` |
   | `aws_subnet.public[i]`, `aws_subnet.private[i]`, `aws_subnet.isolated[i]` (`count = 2` each) | CIDR and zone from the table above; `map_public_ip_on_launch = false` on all six | as above |
   | `aws_eip.nat[k]` (`count = var.nat_gateway_count`) | `domain = "vpc"`, `depends_on = [aws_internet_gateway.this]` | `cms-nat-eip-a`, `cms-nat-eip-b` |
   | `aws_nat_gateway.this[k]` (`count = var.nat_gateway_count`) | `allocation_id = aws_eip.nat[k].id`, `subnet_id = aws_subnet.public[k].id`, `depends_on = [aws_internet_gateway.this]` | `cms-nat-a`, `cms-nat-b` |
   | `aws_route_table.public` | no inline `route` block | `cms-public-rt` |
   | `aws_route.public_internet` | `0.0.0.0/0` to `aws_internet_gateway.this` on `aws_route_table.public` | (not taggable) |
   | `aws_route_table.private[i]` (`count = 2`) | no inline `route` block | `cms-private-rt-a`, `cms-private-rt-b` |
   | `aws_route.private_nat[i]` (`count = 2`) | `0.0.0.0/0` to `aws_nat_gateway.this[min(i, var.nat_gateway_count - 1)]`: lean sends both zones to the NAT gateway in zone a, full sends each zone to its own | (not taggable) |
   | `aws_route_table.isolated` | no route at all: only the implicit local route (NET-AC02) | `cms-isolated-rt` |
   | `aws_route_table_association.public[i]`, `.private[i]`, `.isolated[i]` (`count = 2` each) | each subnet to its tier's table | (not taggable) |

   Routes are separate `aws_route` resources, never inline `route` blocks, so the two styles never fight over a table. No resource refers to `aws_route_table.isolated` except its two associations.
5. Outputs: `vpc_id`, `vpc_cidr_block`, `availability_zones`, `public_subnet_ids`, `private_subnet_ids`, `isolated_subnet_ids`, `nat_gateway_ids`, `nat_public_ips`.
6. README:
   - every template heading;
   - the address plan table;
   - security: the isolated tier has no internet route, `map_public_ip_on_launch` is off, and the default security group is closed;
   - cost: about $0.059 per hour for each NAT gateway plus $0.005 per hour for each public IPv4 address, ap-southeast-1 estimates. Group exists only during a session (Q-O57);
   - teardown: destroyed at the end of every session with the same profile file;
   - Trivy: a MEDIUM finding (AWS-0178, no flow logs) is expected and accepted. It does not fail IAC-AC11, which gates on HIGH and CRITICAL.
7. Lock file: as in T2 step 9, for `awsenv/dev/group`.

### T4 [Infra] State bucket bootstrap script and runbook

- Goal: the one-time, idempotent procedure that creates the state bucket outside every layer, documented with the singleton apply and the NS delegation (IAC-AC08, Q-D11 steps 1, 2 and 4).
- Read: spec IAC-AC06, IAC-AC08, IAC-AC13, Q-D11, Q-O53, TDN-AC05; `CLAUDE.md` ("State Management", "Common Terraform Commands").
- Write: `scripts/bootstrap_state_bucket.sh` (mode 755), `docs/runbooks/bootstrap.md`.
- Boundaries:
  - the script never deletes, empties or disables anything;
  - it never reads or prints a secret, and has no em dash in any name or description;
  - you write it but do not run it (no AWS access); check it with `bash -n` and, if installed, `shellcheck`;
  - it calls the AWS CLI as plain `aws`, resolved from `PATH` (never an absolute path, never an alias), and its output lines are exactly the strings written below. QA's `tests/infra/test_bootstrap.py` runs it against a fake `aws` on `PATH` to test the 403 exit and the second-run branch (US01b-D15), so a changed string or path is a test failure.
- Criteria served: IAC-AC08 (also the documented-steps part of IAC-AC13, owned by US39).

Script behaviour (US01b-D11):

1. Starts with `#!/usr/bin/env bash` and `set -euo pipefail`. Sets `BUCKET="cms-terraform-state-store"` and `REGION="ap-southeast-1"`, `export AWS_PROFILE="${AWS_PROFILE:-3tier}"` and `export AWS_REGION="$REGION"`. Reads `ACCOUNT_ID` with `aws sts get-caller-identity --query Account --output text`.
2. Runs `aws s3api head-bucket --bucket "$BUCKET" --expected-bucket-owner "$ACCOUNT_ID"`:
   - Success prints `Bucket cms-terraform-state-store already exists in account <id>; re-applying its settings.`
   - If stderr contains `(404)`, it creates the bucket with `aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" --create-bucket-configuration LocationConstraint="$REGION" --object-ownership BucketOwnerEnforced`, then runs `aws s3api wait bucket-exists`.
   - Any other error (for example `(403)`: the name is owned by another account, or access is missing) prints the error and exits 1 without changing anything.
3. Then applies these settings on every run (each call is idempotent), each with `--expected-bucket-owner "$ACCOUNT_ID"`:

   | Call | Setting |
   | --- | --- |
   | `put-public-access-block` | all four settings `true` |
   | `put-bucket-ownership-controls` | `BucketOwnerEnforced` (ACLs off) |
   | `put-bucket-encryption` | `SSEAlgorithm=AES256` (SSE-S3, Q-D9) |
   | `put-bucket-versioning` | `Status=Enabled` (IAC-AC08) |
   | `put-bucket-policy` | one statement, `Sid` `DenyInsecureTransport`, `Effect` `Deny`, `Principal` `*`, `Action` `s3:*`, `Resource` the bucket ARN and `<arn>/*`, condition `Bool aws:SecureTransport false` |
   | `put-bucket-tagging` | `Project=cms`, `ManagedBy=bootstrap-script` |

4. Prints the versioning status, the encryption algorithm and the public access block read back with `get-bucket-versioning`, `get-bucket-encryption` and `get-public-access-block`. Ends with `State bucket cms-terraform-state-store is ready (versioning Enabled).` and exit 0.
5. A second run on the same account prints the "already exists" line, applies the same settings and exits 0, so nothing changes.

`docs/runbooks/bootstrap.md` sections:
1. **Purpose.** When the procedure is used: the first build, and a rebuild after teardown (US39).
2. **Prerequisites.** AWS CLI v2, profile `3tier`, `make bootstrap` (Terraform 1.16.4 through `tfenv`), `dig`.
3. **Step 1: state bucket.** `./scripts/bootstrap_state_bucket.sh` from the repo root; expected output; it is safe to re-run.
4. **Step 2: singleton apply.**

   ```bash
   cd awsenv/dev/singleton
   export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1
   terraform init
   terraform apply
   ```

   Review the plan before typing `yes`. No `-out` plan file.
5. **Step 3: NS delegation at Namecheap** (Q-O37):
   - read `terraform output hosted_zone_name_servers`;
   - in Namecheap, Domain List, `imaprof.ink`, Advanced DNS, add four records of type NS with host `cms`, one per name server, TTL automatic;
   - verify from outside AWS with `dig +short NS cms.imaprof.ink @1.1.1.1` and `@8.8.8.8` (both list the four servers);
   - do this right after step 2, so DNS has propagated before US01c's env apply (ACM DNS validation, R-06).
6. **Group layer in a check session.** The commands of `CLAUDE.md` with the lean files (`terraform apply -var-file=tfvars/lean.tfvars`; at the end of the session `terraform destroy -var-file=tfvars/lean.tfvars`), and a pointer to `docs/runbooks/session.md` (US01c), which takes the procedure over.
7. **Steps added by later stories.** The remaining Q-D11 steps, each with the story that documents it:
   - GitHub repository variables, secret and environment `dev01` (US05);
   - SNS subscription confirmation (US02);
   - workspace `dev01` (US03);
   - first image and env apply (US01c, US06);
   - reading the setup token (US08).
8. **What this procedure never does.** It never deletes the bucket or its versions; that is the final teardown (US40, TDN-AC05), by hand and only with the Owner's approval.

### T5 [Infra] Docs touched by the story (DoD item 6)

- Goal: `CLAUDE.md` points to the bootstrap procedure.
- Write: `CLAUDE.md`, one line only. In "State Management", after the "Backend bucket" bullet, add the bullet: "Bootstrap (once per account): `scripts/bootstrap_state_bucket.sh`; procedure in `docs/runbooks/bootstrap.md`."
- Boundaries: no other line of `CLAUDE.md`; `AGENTS.md` unchanged.

## 3. Order of work

T1, T2, T3, T4, T5, all `[Infra]`; there is no DB, BE or FE task. T1 comes first because every README of T2 and T3 follows the template.

After T2 and T3, run from the repository root:
- `make check`;
- in each root, `CHECKPOINT_DISABLE=1 terraform -chdir=<root> init -backend=false -input=false` and `terraform -chdir=<root> validate`;
- if installed, `trivy config --severity HIGH,CRITICAL modules awsenv`. Expected: no finding; LOW AWS-0033 (ECR without a CMK) and MEDIUM AWS-0178 (no flow logs) appear only at lower severities.

Paste the outputs in the handoff.

Proposed commits, one per task:

| Task | Message summary |
| --- | --- |
| T1 | `docs(US01b): add the module README template` |
| T2 | `infra(US01b): add singleton layer with ECR repository and hosted zone` |
| T3 | `infra(US01b): add group layer with three-tier network across two AZs` |
| T4 | `infra(US01b): add state bucket bootstrap script and runbook` |
| T5 | `docs(US01b): point CLAUDE.md to the bootstrap procedure` |

## 4. Traceability

| Criterion | Tasks | At merge: `tests/infra/` (`make check`) | After the Owner's singleton apply: `tests/dev01/test_us01b_singleton.py` | Session 1: `tests/dev01/test_us01b_group.py` |
| --- | --- | --- | --- | --- |
| IAC-AC03 no `resource` in `awsenv/` | T2, T3 | `test_terraform_layout.py`: no line matching `^\s*resource\s+"` in any tracked `*.tf` under `awsenv/` | - | - |
| IAC-AC04 README with every template heading | T1, T2, T3 | `test_terraform_layout.py`: every directory under `modules/` has `README.md` containing each `## ` line of `modules/README_TEMPLATE.md` | - | - |
| IAC-AC07 lock blocks a second run, released after | T2, T3 (`use_lockfile = true`) | `test_terraform_layout.py`: each backend has `use_lockfile = true` and no `dynamodb_table` | lock test on the Owner's first singleton apply, paused at its prompt (section 7, item 5) | the same test on the first group apply of the session. The env workspace part is US01c's |
| IAC-AC08 versioned bucket, outside every layer, documented | T4 | `test_bootstrap.py`: the script and runbook exist with the settings of T4; the 403 exit and the second-run branch with a fake `aws` on `PATH`; no `.tf` declares an `aws_s3_bucket` for `cms-terraform-state-store` | versioning `Enabled` and the other settings; QA's second script run exits 0 with settings unchanged; singleton `terraform state list` does not hold the bucket | group `terraform state list` does not hold the bucket; after US01c's env apply, env (workspace `dev01`) `terraform state list` does not hold it either. US01c keeps the env check as one of its Session 1 items |
| IAC-AC14 common project tag | T2, T3 | `test_terraform_layout.py`: both `providers.tf` have `default_tags` with `Project = "cms"` and `ManagedBy = "terraform"`; no `tags` argument in `modules/` other than one holding only `Name` | every resource with `tags_all` in singleton `terraform show -json` has `Project = cms`, spot-checked with the AWS CLI | the same for group |
| NET-AC01 two zones, three tiers each | T3 | `test_terraform_layout.py`: three subnet resources with `count = 2`, two zones in the group call | - | `aws ec2 describe-subnets` for the VPC returns 6 subnets, one per tier per zone by Name tag, in `ap-southeast-1a` and `ap-southeast-1b` |
| NET-AC02 isolated subnets without an internet route | T3 | `test_terraform_layout.py`: `aws_route_table.isolated` has no `route` block and no `aws_route` refers to it | - | each route table associated with an isolated subnet has only the `local` route |

DoD item 5 applies, because the story changes dev01. The story is done at G6 only when:
- the singleton file has passed after the merge and the group file in Session 1;
- env and group are destroyed at the end of Session 1;
- QA has written the dev01 results to `reports/test-report-US01b-dev01.md`.

## 5. Files to create or change (complete list)

| File | Task |
| --- | --- |
| `modules/README_TEMPLATE.md` | T1 |
| `modules/container_registry/main.tf`, `variables.tf`, `outputs.tf`, `README.md` | T2 |
| `modules/dns_zone/main.tf`, `variables.tf`, `outputs.tf`, `README.md` | T2 |
| `awsenv/dev/singleton/versions.tf`, `providers.tf`, `backend.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `.terraform.lock.hcl` | T2 |
| `modules/network/main.tf`, `variables.tf`, `outputs.tf`, `README.md` | T3 |
| `awsenv/dev/group/versions.tf`, `providers.tf`, `backend.tf`, `main.tf`, `variables.tf`, `outputs.tf`, `.terraform.lock.hcl` | T3 |
| `awsenv/dev/group/tfvars/lean.tfvars`, `awsenv/dev/group/tfvars/full.tfvars` | T3 |
| `scripts/bootstrap_state_bucket.sh` (executable) | T4 |
| `docs/runbooks/bootstrap.md` | T4 |
| `CLAUDE.md` (one line) | T5 |
| `tests/infra/**`, `tests/dev01/**` | T0, QA's commits only |

Nothing else. Not `awsenv/dev/env/`, not `.gitignore` (`.terraform/` is already ignored), not `.tflint.hcl`, not the `Makefile`.

## 6. Interfaces later stories rely on (fixed now)

| Interface | Value | Used by |
| --- | --- | --- |
| State bucket and keys | bucket `cms-terraform-state-store` in ap-southeast-1; keys `singleton/terraform.tfstate`, `group/terraform.tfstate`; env uses `key = "env/terraform.tfstate"` with the default workspace prefix, so workspace `dev01` is stored at `env:/dev01/env/terraform.tfstate`; lock objects `<key>.tflock` | US01c (env backend, `terraform_remote_state` of group), US03 (force-unlock), US05 (plan role: state read and lock object), US40 |
| Root file layout | `versions.tf` (`~> 1.16.4`, `hashicorp/aws ~> 6.71`), `providers.tf`, `backend.tf`, `main.tf`, `variables.tf`, `outputs.tf`, committed `.terraform.lock.hcl` with `darwin_arm64` and `linux_amd64` hashes | US01c (env root copies it, adds the `us_east_1` alias and `Environment = "dev01"`), US02, US05 |
| Tags | provider `default_tags`: `Project = "cms"`, `ManagedBy = "terraform"` (env adds `Environment = "dev01"`, D-DL9); resource `tags` only for `Name` (US01b-D5) | Every Terraform story; TDN-AC04 tag search (US40) |
| Singleton outputs | `ecr_repository_name` (`cms-api`), `ecr_repository_arn`, `ecr_repository_url`, `hosted_zone_id`, `hosted_zone_name` (`cms.imaprof.ink`), `hosted_zone_name_servers` | US01c (image URI, DNS records, ACM validation), US05 and US06 (push target) |
| Group outputs | `vpc_id`, `vpc_cidr_block`, `availability_zones`, `public_subnet_ids`, `private_subnet_ids`, `isolated_subnet_ids`, `nat_gateway_ids`, `nat_public_ips`, lists ordered zone a then b | US01c (remote state with `defaults`, SP1-D9), US11, US34 |
| Group input | `nat_gateway_count` (1 in `lean.tfvars`, 2 in `full.tfvars`), no default | US03 (destroy with the profile file), US34 |
| Module names | `container_registry`, `dns_zone` (singleton), `network` (group); module call names equal the directory names | US02 adds `budget` (singleton) and `alerting` (group) next to them |
| AWS names | `cms-api` (ECR), `cms.imaprof.ink` (zone), `cms-vpc`, `cms-public-a/b`, `cms-private-a/b`, `cms-isolated-a/b`, `cms-igw`, `cms-nat-a/b`, `cms-nat-eip-a/b`, `cms-public-rt`, `cms-private-rt-a/b`, `cms-isolated-rt`, `cms-default-sg` | QA `tests/dev01`, US01c |
| ECR behaviour | tags immutable: a second push of the same 40-character SHA fails. Singleton keeps ECR between sessions, so redeploying an unchanged `develop` head is the normal start of a session, and its image is already in ECR | US06 (CICD-AC06 image build, scan and push step) treats an existing image with the run's SHA tag as a successful push: it checks for the tag first and skips the build and push, without failing the run |
| Bootstrap | `scripts/bootstrap_state_bucket.sh`, idempotent; `docs/runbooks/bootstrap.md` | US39 (rebuild), US40 (teardown checklist entry for the bucket) |
| README template | `modules/README_TEMPLATE.md`, the nine `## ` headings | Every later module |

## 7. For QA

1. **Resource names.** Section 6, "AWS names". The VPC and subnets are found by their `Name` tag, for example `aws ec2 describe-vpcs --filters Name=tag:Name,Values=cms-vpc`.
2. **Terraform outputs.** Section 6 lists the singleton and group outputs. Read them with `terraform -chdir=awsenv/dev/<layer> output -json` after `terraform init` (Owner's profile `3tier`, region ap-southeast-1).
3. **Tags.**
   - Every taggable resource has `Project = cms` and `ManagedBy = terraform`, from `default_tags`.
   - The state bucket, which is outside the layers, has `Project = cms` and `ManagedBy = bootstrap-script`.
   - Resource-level `tags` hold only `Name`.
   - For IAC-AC14 on dev01, a resource "supports tags" when it has a `tags_all` attribute in `terraform show -json`. For singleton those are the ECR repository and the hosted zone. For group: the VPC, default security group, internet gateway, 6 subnets, NAT gateways, EIPs and 4 route tables.
4. **Bootstrap script.**
   - `scripts/bootstrap_state_bucket.sh`, run from the repo root.
   - It honours `AWS_PROFILE` (default `3tier`); the region is fixed to ap-southeast-1.
   - It calls `aws` from `PATH`, so `tests/infra/test_bootstrap.py` may put a fake `aws` executable first on `PATH` (in a temporary directory) and test, with no AWS access:
     - the 403 branch: `head-bucket` fails with `(403)`, the script exits 1 and makes no `put-*` or `create-bucket` call;
     - the second-run branch: `head-bucket` succeeds, so the script prints the "already exists" line, makes no `create-bucket` call, re-applies the six settings and exits 0.

     The output strings below are fixed.
   - Idempotence on AWS: a second run prints `Bucket cms-terraform-state-store already exists in account <id>; re-applying its settings.` and ends with `State bucket cms-terraform-state-store is ready (versioning Enabled).`, exit 0.
   - After either run: `get-bucket-versioning` gives `Status: Enabled`, encryption `AES256`, all four public access block settings `true`, ownership `BucketOwnerEnforced`, and the policy statement `DenyInsecureTransport`.
   - The Owner runs it first. Your singleton dev01 check runs it a second time, a no-change call, which the Owner approves with the check's command list.
5. **Lock test (IAC-AC07).** A real `terraform apply` holds the state lock from before its plan until it ends, including while it waits at its confirmation prompt. Use the Owner's apply as the first run (US01b-D12).
   1. Before: record the state object's version with `aws s3api head-object --bucket cms-terraform-state-store --key <layer>/terraform.tfstate --query VersionId`. On a layer's first apply the object may not exist yet; then record "absent".
   2. The Owner runs the apply: singleton in section 10, after-merge step 2; group in Session 1 with `-var-file=tfvars/lean.tfvars`. The Owner waits at `Enter a value:` until QA says "go".
   3. While the Owner waits, from a second shell on the same layer:
      - `head-object` on `<layer>/terraform.tfstate.tflock` succeeds;
      - `terraform plan -input=false -lock-timeout=0s` (group: plus `-var-file=tfvars/lean.tfvars`) exits non-zero with `Error acquiring the state lock` in its output;
      - the state object's version is unchanged (or still absent).
   4. QA says "go". The Owner types `yes` and the apply completes.
   5. After: the `.tflock` object is gone, and `terraform plan -input=false -detailed-exitcode` exits 0 (no changes) without any `force-unlock`.

   In the test, steps 3 and 5 are separate tests in the layer's file, run in that order. The report records the times.
6. **README template headings (IAC-AC04).** The comparison set is every line of `modules/README_TEMPLATE.md` that starts with `## `: `## Purpose`, `## Layer and callers`, `## Resources`, `## Inputs`, `## Outputs`, `## Example`, `## Security`, `## Cost`, `## Teardown`. Each must appear as a whole line in every `modules/*/README.md`. The H1 is the module name and is not compared.
7. **Static tests (`tests/infra/`).**
   - Files `test_terraform_layout.py` and `test_bootstrap.py`.
   - Read files with the standard library only: text and regular expressions, no HCL parser. The fake `aws` is a small script that the test writes to a temporary directory.
   - Skip `.terraform/` directories, which the Dev creates with `terraform init`.
   - Use `Path(__file__).resolve().parents[2]` as the repository root.
   - These tests run in `make check` and in the story run's test round.
8. **dev01 tests (`tests/dev01/`).**
   - Call the AWS CLI and `terraform` through `subprocess` (US01b-D13); no `boto3`, no new dependency.
   - Two files, selected by file name, not by `-k`:
     - `tests/dev01/test_us01b_singleton.py`: IAC-AC07, IAC-AC08 and IAC-AC14 on singleton;
     - `tests/dev01/test_us01b_group.py`: IAC-AC07, IAC-AC08 (including env), IAC-AC14 on group, NET-AC01, NET-AC02.
   - Run them from `src/api` with `AWS_PROFILE=3tier` and `AWS_REGION=ap-southeast-1`, for example `cd src/api && .venv/bin/pytest ../../tests/dev01/test_us01b_singleton.py`.
   - Results of both runs go to `reports/test-report-US01b-dev01.md`, the evidence for DoD item 5 at G6.
9. **In the story run** (no AWS access): QA's test round runs `make check`, which includes `tests/infra`. `tests/dev01` is not run there; the report lists it under "Not tested, and why", with the dates of item 10.
10. **When the tests run.**

   | When | Files | Criteria (part) |
   | --- | --- | --- |
   | At merge (story run test round, `make check`) | `tests/infra/test_terraform_layout.py`, `tests/infra/test_bootstrap.py` | static parts of IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01, NET-AC02 |
   | After the Owner's bootstrap and singleton apply (target Thu 12 or Fri 13 Nov, no session cost) | `tests/dev01/test_us01b_singleton.py` | IAC-AC07 (on that apply), IAC-AC08, IAC-AC14 |
   | Session 1 (Wed 2026-11-18, office hours, before the destroy) | `tests/dev01/test_us01b_group.py` | IAC-AC07 (on the group apply), IAC-AC08 (group, and env after US01c's env apply), IAC-AC14, NET-AC01, NET-AC02 |

## 8. New dependencies and pins

| Kind | Name and pin | Note |
| --- | --- | --- |
| Terraform provider | `hashicorp/aws ~> 6.71` (latest release 6.71.0 on 2026-11-02), locked in `.terraform.lock.hcl` | New; the approver escalates it (KO-10, "Dependencies") |
| Terraform | `required_version = "~> 1.16.4"`, matching `.terraform-version` from US01a | |
| Python, npm | None. Tests use only the standard library, pytest, the AWS CLI and Terraform | |

## 9. What the approver will escalate, and why

The run ends in `needs-human`, and the Owner decides G5.

| Approver item | Trigger |
| --- | --- |
| Account and network layers | `awsenv/dev/singleton/`, `awsenv/dev/group/` and the three modules only they call |
| Dependencies | The `hashicorp/aws` provider |
| Governance | `CLAUDE.md` (T5) |
| Cost | Always-on singleton resources: hosted zone ($0.50 per month) and ECR storage (a few cents). Both are inside the singleton estimate accepted in OQ-2. Group bills only during sessions: lean about $0.064 per hour for the NAT gateway and its address. Estimates |
| Exposure | An internet gateway and NAT public addresses, as ARCH and NET-AC05 expect. No security group opens anything; the default group is closed |
| Not triggered | Pipeline (no workflow), Identity, Data. Stateful: nothing is destroyed or replaced; the zone is created, not changed |

The approver will also see that the dev01 parts of IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01 and NET-AC02 cannot be proven before the merge. The static parts are proven in the run; the dev01 parts come after the merge and are checked at G6 (DoD item 5).

## 10. Owner actions

Before `/story US01b`:
- US01a is merged;
- G4 for US01b;
- the branch is created from the new `develop`;
- QA's `test(US01b)` commit is reviewed;
- the three summaries `US01b-po-summary.md`, `US01b-dev-lead-summary.md` and `US01b-qa-summary.md` exist.

After the merge, the same day if possible (target Thu 12 or Fri 13 Nov; backlog note of US01b):
1. `./scripts/bootstrap_state_bucket.sh` with `AWS_PROFILE=3tier` (runbook step 1).
2. Singleton: `terraform init` and `terraform apply` in `awsenv/dev/singleton` (runbook step 2). This first apply is also the IAC-AC07 lock test: when the plan is shown, **wait at the `Enter a value:` prompt until QA says "go"**, then type `yes` (section 7, item 5). This starts the always-on cost of section 9.
3. Namecheap: the four NS records for host `cms`, then the two `dig` checks (runbook step 3). DNS needs time to propagate before US01c's env apply.
4. Tell QA that singleton is applied, so the rest of `tests/dev01/test_us01b_singleton.py` can run, including QA's second run of the bootstrap script.

In Session 1 (Wed 2026-11-18, lean):
- apply group with `-var-file=tfvars/lean.tfvars` before env, and wait at the `Enter a value:` prompt until QA says "go" (lock test);
- QA runs `tests/dev01/test_us01b_group.py`; its env state check for IAC-AC08 runs after US01c's env apply;
- at the end, destroy env, then group, with the same files.

## 11. Verified at plan time (2026-11-02)

| Item | Result |
| --- | --- |
| State bucket name free | An unauthenticated request to `https://cms-terraform-state-store.s3.ap-southeast-1.amazonaws.com/` returns 404 `NoSuchBucket`. The name can still be taken by someone else before the Owner runs the script; the script then stops at the `(403)` branch (risk below) |
| Lock held at the apply prompt | `terraform apply` takes the state lock before planning and keeps it until the run ends, including the wait at the confirmation prompt (standard Terraform locking behaviour). The lock test uses this (US01b-D12). `terraform console` also holds the lock (v1.16.x docs), but is no longer used |
| S3 native locking | `use_lockfile` is available in Terraform 1.16.4 (introduced in 1.10, GA in 1.11), matching `CLAUDE.md` |
| AWS provider | Registry lists 6.71.0 as the latest version |
| Trivy on the planned settings | `trivy config` 0.75.0 on a scratch copy of the ECR, zone, VPC, subnet, IGW, NAT and route-table settings above: 0 HIGH, 0 CRITICAL; one LOW (AWS-0033, ECR without a CMK; Q-D9 chose AES256) and one MEDIUM (AWS-0178, no VPC flow logs). Neither fails IAC-AC11, so no ignore entry is needed |
| tflint | The US01a `.tflint.hcl` fails on an undocumented variable (exit 2); notices count as failures |
| Terraform 1.16.4 locally | Installed through `tfenv` |

## 12. Risks

| Risk | Response |
| --- | --- |
| The bucket name is taken by another account before the Owner runs the script | The script exits 1 at `head-bucket` with `(403)` and changes nothing. A different name would change `CLAUDE.md` and every backend, so the PM/SM raises it to the Owner then; it is not decided in this plan |
| NS delegation not propagated before US01c's env apply | The Owner adds the records right after the singleton apply, at least 4 days before Session 1; the runbook gives the `dig` check |
| The provider lock lacks the CI platform | `providers lock` with `darwin_arm64` and `linux_amd64` in T2 and T3 |
| `terraform providers lock` downloads large archives in the sandbox | Network is allowed for story runs (PROC12); if it fails, the Dev reports BLOCKED with the error |
| Immutable ECR tags make CICD-AC06's push step fail when the run's SHA is already in ECR, which is the normal case at the start of a session (unchanged `develop` head, ECR kept in singleton) | Tags stay immutable: mutable tags are a HIGH Trivy finding (AWS-0031), which IAC-AC11 fails on. US06 treats an existing SHA tag as a successful push (section 6) |

## 13. Decisions (Dev Lead tier, workflow section 8; the Owner can override any of them at G4)

| ID | Decision | Reason |
| --- | --- | --- |
| US01b-D1 | This story creates the modules `container_registry`, `dns_zone` and `network` only; the other BD-8 modules come with the stories that own their resources | Keeps the story at M; BD-8 names are kept |
| US01b-D2 | The README template has the nine `##` headings of T1; IAC-AC04 compares exactly those lines | IAC-AC04 needs a fixed, testable heading set, and the template did not exist |
| US01b-D3 | State keys `singleton/terraform.tfstate`, `group/terraform.tfstate`, and for US01c `env/terraform.tfstate` with the default workspace prefix | One object per layer (IAC-AC06); names are stable for remote state, the plan role and force-unlock |
| US01b-D4 | `required_version = "~> 1.16.4"`, `hashicorp/aws ~> 6.71`, lock files with hashes for `darwin_arm64` and `linux_amd64` | `AGENTS.md` asks for `~>` pins and committed lock files; both platforms that run Terraform are covered |
| US01b-D5 | Resource-level `tags` may hold only `Name`, for resources whose AWS console name is that tag (VPC, subnets, gateways, EIPs, route tables, the default security group). All common tags still come only from `default_tags` | The `cms-<resource>` naming rule (Q-D6) and the `default_tags` rule (D-DL9) both apply; `Name` is a name, not a common tag. Reviewers check RV-11 against this |
| US01b-D6 | VPC `10.20.0.0/16`; zones `ap-southeast-1a` and `ap-southeast-1b` written literally; `/24` subnets at offsets 0, 10 and 20 per tier | Room for growth in each tier, readable addresses, and no data lookup, so plans are deterministic |
| US01b-D7 | `nat_gateway_count` (no default, 1 or 2) sets the NAT count; the private route table of zone b uses NAT gateway a in lean and its own in full; routes are separate `aws_route` resources | Q-O55 and SCALE-AC01 to SCALE-AC03 with no `.tf` change between profiles; no profile can be applied without its file |
| US01b-D8 | Network hardening: the default security group is managed and closed; `map_public_ip_on_launch = false` on all subnets; no flow logs, VPC endpoints or NACL changes | CIS-style default; nothing gets a public IP by accident (NET-AC05); flow logs and endpoints add cost and are not in ARCH. Trivy gives them MEDIUM at most |
| US01b-D9 | ECR `cms-api`: tags immutable, scan on push, AES256, `force_delete`, lifecycle that expires untagged images after 1 day and keeps the 5 most recent | SHA tags must never be overwritten (CNT-AC04); cost stays at cents; teardown leaves nothing (Q-D12) |
| US01b-D10 | Hosted zone `cms.imaprof.ink` with `force_destroy = false` | If an env record were left behind, the singleton destroy stops instead of deleting it silently; the zone is destroyed only at final teardown |
| US01b-D11 | The bootstrap script creates or re-applies, idempotently: versioning, SSE-S3, all public access blocked, `BucketOwnerEnforced`, a TLS-only bucket policy and the tags `Project = cms`, `ManagedBy = bootstrap-script`. Every call names the expected bucket owner, and the script stops on any `head-bucket` error other than 404 | Q-D11 step 1 plus common S3 hardening; safe to re-run; never acts on a bucket of another account |
| US01b-D12 | IAC-AC07 is tested with a real `terraform apply` paused at its confirmation prompt as the first run: the Owner's first singleton apply after the merge, and the first group apply of Session 1. While the Owner waits, a second `plan` with `-lock-timeout=0s` must fail with a lock error and the state object's version must be unchanged. After the apply, a plan succeeds without `force-unlock` (PM/SM decision on QA's review) | The criterion is about a run that holds the lock for a change, so a real apply proves it as written; both applies happen anyway, so the test adds no AWS cost |
| US01b-D13 | `tests/dev01` calls the AWS CLI and `terraform` through `subprocess`; `tests/infra` uses only the standard library | No new Python dependency (KO-10); the CLI is what the spec's "Check:" lines use |
| US01b-D14 | `docs/runbooks/bootstrap.md` covers Q-D11 steps 1, 2 and 4 and the group commands for a session, and lists the remaining steps with the stories that add them; `CLAUDE.md` gets one pointer line | SP1-D2 (one file per procedure); DoD item 6 |
| US01b-D15 | The bootstrap script calls `aws` from `PATH` and prints fixed strings, so `tests/infra/test_bootstrap.py` can test its 403 exit and second-run branch with a fake `aws` on `PATH` (PM/SM decision on QA's review) | Proves the idempotence and the safe stop at merge time without AWS access |

## 14. Open questions (Owner tier)

None. The bucket-name fallback (section 12) becomes an Owner question only if the name turns out to be taken.

## 15. G4 review changes (2026-11-02, PO and QA read-only review, DES03 revision round)

| # | From | Change | Why |
| --- | --- | --- | --- |
| 5 | PO | ECR tags stay `IMMUTABLE`. Sections 6 and 12 name CICD-AC06 and the normal case (singleton keeps ECR between sessions, so an unchanged `develop` head is redeployed at the start of a session), and state that US06 treats an existing SHA tag as a successful push | Mutable tags are a HIGH Trivy finding (IAC-AC11); without this rule the first CD run of most sessions would fail |
| 6 | QA, PM/SM decision | The IAC-AC07 lock test holds the lock with a real apply paused at its prompt (Owner's first singleton apply, first group apply of Session 1), not `terraform console`. Updated: US01b-D12, section 4, section 7 item 5, section 10, section 11 | Proves the criterion as written, with a run that holds the lock for a change |
| 7 | QA | IAC-AC08 "in no layer's state" includes env: env state check in Session 1 after US01c's env apply, kept by US01c (section 4, section 7 items 8 and 10, section 10) | The criterion names every layer |
| 8 | QA | dev01 tests are selected by file (`tests/dev01/test_us01b_singleton.py`, `tests/dev01/test_us01b_group.py`), not `-k`. Results go to `reports/test-report-US01b-dev01.md` for G6 (sections 4 and 7) | A stable selection, and one evidence file for DoD item 5 |
| 9 | QA, PM/SM decision | The bootstrap script resolves `aws` from `PATH` and keeps fixed output strings, so `tests/infra/test_bootstrap.py` tests the 403 exit and the second-run branch with a fake `aws` (T4, section 7 item 4, new US01b-D15) | Tests the safe stop and idempotence at merge time, with no AWS access |
| 10 | QA | Section 7 item 10 and the section 4 columns state when each test file runs: at merge (`tests/infra/test_terraform_layout.py`, `test_bootstrap.py`), after the singleton apply (singleton file), in Session 1 (group file) | QA and the Owner plan the checks against fixed moments |
