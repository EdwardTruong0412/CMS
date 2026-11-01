# Handoff: 2026-11-01 DES01 - Dev Lead summary (Steps 4 and 4b, Basic Design, gate G2)

## What was done

- Checked ARCH (`20261003_02_high_level_architecture.png`) against every NFR characteristic and all 183 acceptance criteria of spec-001. ARCH supports every criterion; gaps were design details, resolved as Dev Lead decisions, except four points that need the Owner (below). The check is in spec section "Basic Design", BD-1.
- Resolved Q-D1 to Q-D15 (intent section 9.2): 14 decided and logged, Q-D4 escalated.
- Wrote the two open criteria: CICD-AC14 (pre-flight check, from Q-D3) and SCALE-AC04 (request-count target, from Q-D7). IDs kept, `[OPEN ...]` markers removed, summary table now shows 0 open criteria.
- Added the Basic Design to spec-001: architecture check, business flows, screen list, screen transitions, logical ER diagram, API paths and status-code conventions, functional specification, infrastructure layout and profiles, NFR overview (performance, security, availability). Mermaid for all diagrams.
- Wrote the function list (40 functions: 29 application, 11 operations); all 183 criteria are traced to at least one function (checked by script).
- Wrote the reuse record: nothing reusable in the repository; ARCH reused as-is from UserHub; a short list of AWS-managed and official external assets.

## Files produced or changed

| File | Change |
| --- | --- |
| `docs/specs/spec-001.md` | Header rows updated; CICD-AC14 and SCALE-AC04 written; summary counts; small NFR pointers to resolved Q-Ds; new section "Basic Design" (BD-1 to BD-9); 30 Decisions log rows (Q-D1 to Q-D15 except Q-D4, D-DL1 to D-DL15); "Open questions for the Owner" now holds Q-O54 to Q-O57. No other criterion changed. The spec has no change-history section, so none was added. |
| `docs/specs/function-list.md` | New |
| `docs/reuse-assets.md` | New |
| `docs/intent/intent-001.md` | Section 9.2 only: Status column added for Q-D1 to Q-D15 |
| `reports/handoff/DES01-dev-lead-summary.md` | This file |

## Decisions (Q-D1 to Q-D15)

| ID | Outcome |
| --- | --- |
| Q-D1 | App Auto Scaling scheduled actions set min/max to 0 at 18:00 and to the profile values at 08:45; EventBridge Scheduler stops and starts RDS; both profiles use the same mechanism. |
| Q-D2 | Missing data not breaching; scheduler disables alarm actions 18:00-09:15 for alarms 1-8 and 10; WAF, GuardDuty, rollback and budget alerts stay on. |
| Q-D3 | Every delivery run starts with a pre-flight that fails the run before any change out of hours (weekend, after 17:30, 0 tasks or RDS not available). CICD-AC14 written. |
| Q-D4 | Escalated as Q-O57 (cost). |
| Q-D5 | Closed page is a UI screen served from S3; shown when `/api/v1/status` or any API call answers 503. |
| Q-D6 | PNG untouched; all built names use `cms` / `cms-dev01`; Owner may re-export the diagram optionally. |
| Q-D7 | `ALBRequestCountPerTarget` target 50 per target per minute; cooldowns 60 s out, 300 s in. SCALE-AC04 written. |
| Q-D8 | Multi-region CloudTrail to a singleton S3 bucket, SSE-KMS with a singleton key, 14-day lifecycle. |
| Q-D9 | Access-log bucket SSE-S3 (ALB logs support nothing else); CloudFront legacy standard logging; Trivy finding accepted with reason. |
| Q-D10 | WAF groups Common, KnownBadInputs, SQLi; ALB limited by CloudFront origin-facing prefix list plus secret origin header; no HTTP listener. |
| Q-D11 | Eight-step bootstrap runbook; extra manual steps listed (state bucket script, first local singleton apply, GitHub variables, secret and environment, admin recovery). |
| Q-D12 | KMS 7-day window (aliases free at once); secrets with recovery window 0; account-ID bucket names; force-destroy; Terraform-created log groups. |
| Q-D13 | Ephemeral `random_password` plus write-only arguments; no secret value in state or plan; fallback documented. |
| Q-D14 | Rate rule 20 per 300 s per IP, scope-down on paths starting `/api/v1/auth/login` or `/api/v1/setup`. |
| Q-D15 | Owner-run break-glass workflow: one-off ECS task resets an admin and writes the temporary password to a dedicated secret. |

Also decided (D-DL1 to D-DL15): status codes and error format, server-side sessions behind a signed cookie, Argon2id, throttling per normalised email, diacritics search key, setup race guard, API layout, UI i18n and deep-link rewrite, project tags, sizing and PostgreSQL 17, KMS key split, two OIDC roles (plan and deploy), budget-to-SNS by fixed ARN, module layout, origin TLS.

## Questions escalated to the Owner (spec, "Open questions for the Owner")

| ID | Subject | Recommended answer |
| --- | --- | --- |
| Q-O54 | Criteria approved at G1 say a merge to `develop` starts delivery; CD became manual on 2026-11-01 | PO rewords "Delivery run", CICD-AC06, AC09, AC11, AC16 and CNT-AC04 to a run started by hand by the Owner |
| Q-O55 | NAT gateways are in the group layer, but SCALE-AC03 switches profiles with env tfvars only | Group gets its own lean/full tfvars for the NAT count; PO rewords SCALE-AC03 and COST-AC02 |
| Q-O56 | WAF alarm (OBS-AC05 item 9) must live in us-east-1, which IAC-AC09 forbids | Allow the alarm and a forwarding EventBridge rule in us-east-1; PO rewords IAC-AC09 |
| Q-O57 | Always-on resources cost about $3-3.50 per day, so the $10 alert fires after about 3 days (answers Q-D4) | Keep ARCH and the $10 alert, accept about $3.50 per environment day, destroy env and group when idle 2+ days |

## Unsure or to verify at plan time

- AWS behaviour I relied on but could not confirm here: ALB access logs support only SSE-S3; WAF rate limits down to 10 per window; stopping Multi-AZ PostgreSQL; KMS keys pending deletion not billed; AWS Budgets accepting an SNS topic that does not exist yet (D-DL13); CloudFront origin-facing prefix list weight against the security group rule quota; WAF CloudFront metric location and cross-region EventBridge targets (Q-O56); write-only arguments in the provider versions chosen (Q-D13); PostgreSQL 17 on RDS.
- Cost figures in Q-O57 are estimates from on-demand ap-southeast-1 prices; check with the AWS Pricing Calculator.
- Terraform 1.16.4 (IAC-AC01, from ARCH): `.terraform-version` is still empty; confirm the version exists when it is pinned.
- Q-D15 adds an operational capability (break-glass recovery). I classed it as a routine design choice because it uses AWS access the Owner already holds; the Owner may prefer to treat it as scope.
- Not done, by instruction: `AGENTS.md` and `CLAUDE.md` check command and conventions (after G2 approval); `CLAUDE.md` provider-alias and group-tfvars lines depend on Q-O55 and Q-O56.
- No commit made. Nothing outside the five allowed files was written (scratch files are in the session scratchpad only).
