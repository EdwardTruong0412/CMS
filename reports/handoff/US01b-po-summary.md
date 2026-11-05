# Handoff: 2026-11-05 US01b - Product Owner summary (state bucket, singleton and group, before the story run)

| | |
| --- | --- |
| Task | Product Owner summary for US01b, required by global rule 5 and the `/story` preflight. Approved by the Owner on 2026-11-05 |
| Branch / worktree | `feature/US01b_state_singleton_group` (QA's tests committed as `cfa91ec`), `/Users/truongquy/Documents/wt-US01b` |
| Read | `docs/backlog.md` (US01b, BL-D10), `docs/specs/spec-001.md` (IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01, NET-AC02, OQ-2), `docs/plans/US01b.plan.md` (sections 1, 4, 10, 15), `docs/gates/G4.md` (US01b, approved), `reports/sprints/sprint-1-planning.md`, `reports/handoff/US01a-po-summary.md` (format) |
| Changed | This file only. Nothing committed |

## 1. What was done (PO side)

1. **Scope.** US01b is the second of the three parts of the former US01, recorded in `docs/backlog.md` in PROC10 (BL-D10, refinement inside `baseline-1`, no CR). It delivers IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01 and NET-AC02, function F-OPS-08, Must, size M, Release 1, depends on US01a (merged).
2. **G4 review (DES03, read-only).** Result CHANGES: ECR tags stay `IMMUTABLE` (mutable tags are a Trivy HIGH, IAC-AC11), and the plan must state that redeploying an unchanged `develop` head is the normal start of a session and that US06 treats an existing SHA tag as a successful push (CICD-AC06). The Dev Lead applied it (plan section 15, row 5). On the lock test the PO accepted `terraform console`; the PM/SM chose QA's method (a real apply paused at its prompt, US01b-D12) because it matches the wording of IAC-AC07. The PO agrees with that choice. The Owner approved the US01b section of `docs/gates/G4.md`.
3. **Sprint 1.** Lane Dev 1 ("Terraform and pipeline"), target merge Fri 13 Nov 2026; dev01 group checks in Session 1, Wed 18 Nov 2026 (fallback Thu 19 Nov) (`reports/sprints/sprint-1-planning.md`).
4. **Owner decision of 2026-11-05.** QA's test that singleton has no variables and no `tfvars` directory was dropped, because US02 adds a singleton variable. No criterion depends on that test, so the traceability of section 3 is unchanged.

## 2. The story in one paragraph

The Owner gets a documented, idempotent script and runbook that create the versioned state bucket `cms-terraform-state-store` outside every layer, a module README template, and two root modules built only from documented child modules: singleton (ECR repository `cms-api` and hosted zone `cms.imaprof.ink`) and group (VPC `cms-vpc` across `ap-southeast-1a` and `ap-southeast-1b`, one public, private and isolated subnet per zone, NAT count from the lean or full profile file). Both backends use S3 native locking, and every resource gets the common tags from provider `default_tags`. The story run applies nothing; the Owner bootstraps and applies singleton after the merge, and group is applied only in check sessions.

## 3. Criteria delivered and what "done" means

Criterion text lives in `docs/specs/spec-001.md`; it is not repeated here. Test files and check points are those of plan section 4.

| Criterion | Done at G5 (merge, static, in `make check`) | Done at G6 (proven on the real account) |
| --- | --- | --- |
| IAC-AC03 | `tests/infra/test_terraform_layout.py`: no `resource` block in any tracked `*.tf` under `awsenv/` | Same test passes on the merged `develop`; nothing on AWS to prove |
| IAC-AC04 | `test_terraform_layout.py`: every `modules/*/README.md` holds each `## ` heading of `modules/README_TEMPLATE.md` | Same test passes on the merged `develop` |
| IAC-AC07 | `test_terraform_layout.py`: both backends have `use_lockfile = true` and no `dynamodb_table` | Lock test on the Owner's first singleton apply (after the bootstrap) and on the first group apply of Session 1: a second plan fails with a lock error while the apply waits, the state version is unchanged, and a plan after the apply succeeds without `force-unlock`. The env workspace part is US01c's |
| IAC-AC08 | `tests/infra/test_bootstrap.py`: script and runbook exist with the planned settings; the 403 exit and the second-run branch pass with a fake `aws`; no `.tf` declares the state bucket | After the bootstrap and singleton apply: versioning `Enabled` and the other settings, QA's second script run exits 0 with nothing changed, singleton state does not hold the bucket. Session 1: group state does not hold it, and env state (workspace `dev01`) after US01c's env apply (see US01b-PO-D1) |
| IAC-AC14 | `test_terraform_layout.py`: both `providers.tf` set `Project = "cms"` and `ManagedBy = "terraform"` in `default_tags`; module `tags` hold only `Name` | Every resource with `tags_all` in singleton state has `Project = cms` (after the singleton apply), and the same for group (Session 1). The env layer is checked in US01c |
| NET-AC01 | `test_terraform_layout.py`: three subnet resources with `count = 2`, two zones in the group call | Session 1: `aws ec2 describe-subnets` returns six subnets, one per tier per zone |
| NET-AC02 | `test_terraform_layout.py`: `aws_route_table.isolated` has no route and no `aws_route` refers to it | Session 1: each route table of an isolated subnet has only the `local` route |

Definition of Done as it applies at G6:

- Item 1: every criterion has passing QA tests written before the code (`cfa91ec`).
- Item 2: `make check` passes; no CI workflow exists until US05 (US01b-PO-D2).
- Items 3 and 4: lenses pass and the approver's escalation (singleton and group layers, the AWS provider, `CLAUDE.md`, always-on cost; plan section 9) is approved by the Owner; `tests/` changed only by QA's `test(US01b): ...` commits.
- Item 5: applies. `tests/dev01/test_us01b_singleton.py` passed after the Owner's singleton apply, `tests/dev01/test_us01b_group.py` passed in Session 1, env and group destroyed at the end of Session 1, results in `reports/test-report-US01b-dev01.md`.
- Item 6: `CLAUDE.md` points to the bootstrap procedure (plan T5).

## 4. Out of scope

- The env layer and `awsenv/dev/env/`, the session runbook, the first image (US01c).
- The budget, the SNS alert topic and the alert email (US02).
- OIDC provider and CI roles, workflows, Trivy ignore file (US03, US05); CloudTrail and GuardDuty (US14).
- Final teardown of the bucket and the zone (US40).

## 5. Also checked in

- IAC-AC03, IAC-AC04, IAC-AC14 in **US01c** and every later story that adds or changes Terraform (US02, US03, US05 to US07, US11, US12, US14, US15, US30, US32 to US34, US41); IAC-AC14 also in **US40** (tag search).
- IAC-AC07 in **US01c** (env layer with workspace `dev01`).
- IAC-AC08 env-state check: run in Session 1 after US01c's env apply, kept by US01c (plan section 15, row 7).

## 6. Owner actions after the merge, and cost

Same day if possible (target Thu 12 or Fri 13 Nov), per `docs/runbooks/bootstrap.md`:

1. Run `./scripts/bootstrap_state_bucket.sh` with `AWS_PROFILE=3tier`.
2. `terraform init` and `terraform apply` in `awsenv/dev/singleton`; wait at `Enter a value:` until QA says "go" (lock test), then type `yes`.
3. Add the four NS records for host `cms` at Namecheap at once, and check with the two `dig` commands, so DNS has propagated before US01c's env apply (R-06).
4. Tell QA singleton is applied.

In Session 1: apply group with `tfvars/lean.tfvars` (again waiting at the prompt for QA), then at the end destroy env, then group, with the same files.

Cost accepted by the Owner (G4, inside the singleton estimate of OQ-2): always-on singleton cost of the hosted zone, $0.50 a month, plus a few cents of ECR storage, starting with the singleton apply. Group bills only during sessions: lean about $0.064 an hour (one NAT gateway and its address). All figures are estimates.

## 7. Decisions (PO tier)

| ID | Decision | Reason |
| --- | --- | --- |
| US01b-PO-D1 | The env-state part of IAC-AC08 (and the env parts of IAC-AC07 and IAC-AC14) count at US01b's G6 when they pass in Session 1. If US01c's env apply does not happen in Session 1, US01b's IAC-AC08 is accepted at G6 on the bucket, singleton and group check points, and the env-state check point moves to US01c's G6 | The env layer does not exist until US01c; BL-D2 places a check point that needs a later capability in the later story, as in US01a-PO-D1 |
| US01b-PO-D2 | DoD item 2 for US01b means `make check` passes; the CI part applies from US05 on | No workflow exists yet; requiring one would pull US05 scope into US01b (same as US01a-PO-D2) |

## 8. Open questions (Owner tier)

None. The bucket-name fallback (plan section 12) becomes an Owner question only if the bootstrap script stops at its 403 branch.
