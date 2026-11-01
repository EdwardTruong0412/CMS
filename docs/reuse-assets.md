# Reuse assets

| | |
| --- | --- |
| Step | Phase A, Step 4 (workflow section 4) |
| Author | Dev Lead, 2026-11-01 |
| Status | Draft for Owner review at G2 |

## 1. What was searched

| Location | Result (2026-11-01) |
| --- | --- |
| `assets/` | Does not exist. No earlier project, component or schema has been placed there for reuse. |
| `modules/` | Empty. No Terraform child module to reuse. |
| `awsenv/` | Only the empty directory `awsenv/dev/`. No root module to reuse. |
| `src/` | Empty. No application code to reuse. |
| `tests/`, `testdata/mock/` | Do not exist yet. |

Nothing in the repository can be reused as code.

## 2. Reused: the high-level architecture

| Asset | Origin | How it is reused | Decision |
| --- | --- | --- | --- |
| `20261003_02_high_level_architecture.png` (repo root) | The Owner's earlier project UserHub | Used as-is as the architecture of CMS, renamed to CMS. The file is not edited; every name built from it uses `cms` instead of `userhub` / `user-hub` (spec Decisions log, Q-D6). | Owner decision, 2026-10-13 (intent-001 section 6.1) |
| Layering, state and workflow conventions in `CLAUDE.md` | Same UserHub project, already renamed to CMS in `CLAUDE.md` | Layers singleton / group / env, S3 state with lock file, module rules, workflow names, tflint rules | Part of the same Owner decision |

## 3. Proposed external assets

Only assets that clearly save work or risk are proposed. Each is pinned to a version in the story that first uses it.

| Asset | Origin | Use in CMS | Why it is worth it |
| --- | --- | --- | --- |
| AWS managed WAF rule groups `AWSManagedRulesCommonRuleSet`, `AWSManagedRulesKnownBadInputsRuleSet`, `AWSManagedRulesSQLiRuleSet` | AWS, maintained by AWS | WAF web ACL (SEC-AC04, Q-D10) | Rules kept current by AWS; no rules to write |
| AWS managed prefix list `com.amazonaws.global.cloudfront.origin-facing` | AWS | ALB security group, CloudFront only (NET-AC06, Q-D10) | AWS keeps the CloudFront address ranges current |
| CloudFront managed policies `CachingDisabled`, `CachingOptimized`, `AllViewerExceptHostHeader` | AWS | CloudFront behaviours for `/api/*` and the UI | Standard settings, nothing to maintain |
| `hashicorp/aws` and `hashicorp/random` providers, with ephemeral resources and write-only arguments | HashiCorp registry | Secrets outside Terraform state (Q-D13) | Built-in way to meet SEC-AC09 |
| `aws-actions/configure-aws-credentials` | GitHub Marketplace, maintained by AWS | OIDC login in every workflow (CICD-AC04) | Official action for OIDC; pinned by commit SHA |
| `aquasecurity/trivy-action` | GitHub Marketplace, maintained by Aqua Security | IaC and image scans (IAC-AC11, CNT-AC05) | Official action for the scanner already in `CLAUDE.md`; pinned by commit SHA |
| `hashicorp/setup-terraform` | GitHub Marketplace, maintained by HashiCorp | Terraform 1.16.4 in workflows (IAC-AC01) | Official action; reads the pinned version |
| `argon2-cffi` (Python) | PyPI, maintained by Hynek Schlawack | Password hashing (LGN-AC18, D-DL3) | Reference Argon2 binding; avoids writing crypto |
| `react-i18next` with `i18next` | npm, i18next project | English and Vietnamese UI texts (LNG group, D-DL8) | Standard React i18n library; catalogues as JSON files |

Not proposed: community Terraform modules from the registry (for example `terraform-aws-modules/vpc`). `CLAUDE.md` asks for small modules grouped by function and readable over DRY; large general-purpose modules would hide what each layer creates and make IAC-AC02 and the Trivy reviews harder.
