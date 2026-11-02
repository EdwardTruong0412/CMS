# Handoff: 2026-11-01 PROC08 - Dev Lead summary (Sprint 1 Planning: what can be done, and how)

Branch `feature/PROC08_sprint1_planning`, worktree `wt-PROC08`. I wrote only this file. I committed nothing, created no branch or worktree, and ran no Codex, Terraform, AWS or GitHub command.

Sprint 1 runs from Mon 2026-11-09 to Fri 2026-11-20 (10 working days, D1 to D10) and covers US01 to US09 of Baseline 1. The scope does not change. "Size" uses BL-D4: S about 1 day, M 1 to 2 days, L 2 to 3 days, for one Dev in one `/story` run.

Inputs read: `docs/backlog.md`, `docs/specs/spec-001.md` (criteria, BD-1 to BD-9, Decisions log), `docs/specs/function-list.md`, `docs/release-plan.md`, `docs/project-plan.md`, `docs/kickoff.md`, `AGENTS.md`, `CLAUDE.md`, workflow sections 6.2 to 6.4 and 8, `.claude/skills/story/SKILL.md`, `.claude/agents/approver.md`, `.github/workflows/protect_tests.yml`, and the current state of the repository.

What exists today: `Makefile`, `.tflint.hcl` and `.terraform-version` are empty files. `modules/`, `awsenv/` (as tracked files), `src/` and `tests/` do not exist. `modules/README_TEMPLATE.md`, which `CLAUDE.md` and IAC-AC04 rely on, does not exist either. The only workflow is `protect_tests.yml`. `REVIEW.md` and `docs/gates/G4.md` do not exist.

## 1. What can be done this sprint, and how (Scrum questions 2 and 3)

### Size check: US01 is over 3 days and should be split

As one story, US01 has 23 criteria and needs all of the following:
- the repo tooling (`make check`, `make bootstrap`, the tflint config, the version pin);
- the API skeleton, the Dockerfile and the web skeleton;
- the state bucket bootstrap;
- three Terraform layers with about 10 child modules and their READMEs;
- two ACM certificates, CloudFront with OAC, the ALB, ECS, RDS and DNS;
- the first local image push and the runbook.

My estimate is 6 to 8 Dev days, which is far over the 3-day limit. A diff that size would also be hard for the lenses to review in one round. The backlog note says the Product Owner splits US01 at refinement when this happens. The cut below keeps each of the 23 criteria in exactly one story and changes nothing else. The PO picks the names; the Owner decides whether the split needs a CR (OQ-S1-1 in section 6).

| Part | Content | Criteria (23 in total, unchanged) | Size |
| --- | --- | --- | --- |
| US01a Repo tooling and app skeleton | `make bootstrap` and `make check`, `.terraform-version`, `.tflint.hcl`, API skeleton, Dockerfile, web skeleton | CNT-AC01, CNT-AC02 | M (1 to 1.5 days) |
| US01b State bucket, singleton and group | Bootstrap script and runbook, README template, singleton (ECR, hosted zone), group (network) | IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01, NET-AC02 | M (1.5 to 2 days) |
| US01c Env layer serves the app over HTTPS | Env root and modules, first image push, session runbook | IAC-AC05, IAC-AC06, IAC-AC12, NET-AC03, NET-AC04, NET-AC07 to NET-AC11, CNT-AC03, SEC-AC01, SEC-AC02, SCALE-AC01 | L (2.5 to 3 days, at the limit: watch) |

If the Owner keeps US01 whole, it runs as one story of about 6 to 8 days with Dev 1 alone. Dev 2 can then do nothing until it merges, and the sprint forecast drops to about US01 to US05.

### Tasks per story (by layer; the detailed design goes in each `docs/plans/<story>.plan.md` at G4)

**US01a Repo tooling and app skeleton.** Depends on: none.
- [Infra] `Makefile` with `bootstrap` (tfenv, trivy, tflint, drawio) and `check` exactly as `AGENTS.md` defines it. `.terraform-version` = `1.16.4` (confirm the release exists). `.tflint.hcl` with the rules in `CLAUDE.md` and the AWS ruleset plugin pinned.
- [BE] `src/api`:
  - `pyproject.toml` with exact pins, ruff and mypy strict, and `testpaths` = `tests/api`, `tests/infra`;
  - app factory, `settings.py` (prefix `CMS_`, SP1-D4), `db.py` with `pool_pre_ping`, the error handler and the injectable clock;
  - `GET /healthz` and `/api/healthz` (no database);
  - `GET /api/v1/status` (`SELECT 1`, 503 when the database is unreachable). `setup_required` comes with US08.
- [Infra] `src/api/Dockerfile` (multi-stage, final `python:3.13-slim`, `USER 10001:10001`, port 8000) and `.dockerignore`.
- [FE] `src/web` with Vite, React and strict TypeScript, ESLint and Prettier, the one API client (relative `/api`, 503 leads to a closed-page placeholder), and one start page that calls the status endpoint.
- [QA] `tests/infra` (Dockerfile structure for CNT-AC01 and CNT-AC02, Makefile targets), `tests/api` (health and status).

**US01b State bucket, singleton and group.** Depends on: US01a (`make check`, pytest config).
- [Infra] Bootstrap script for `cms-terraform-state-store` (AWS CLI, profile `3tier`, versioning, SSE-S3, public access blocked) and `docs/runbooks/bootstrap.md` (IAC-AC08, Q-D11).
- [Infra] `modules/README_TEMPLATE.md`, which is missing and which IAC-AC04 needs.
- [Infra] Singleton root: `versions.tf`, `providers.tf` with `default_tags` (D-DL9), `backend.tf` with `use_lockfile` and the region. Modules `container_registry` (ECR, scan on push, lifecycle, `force_delete`, AES256) and `dns_zone` (`cms.imaprof.ink`, name servers as an output).
- [Infra] Group root: module `network` (2 AZs by 3 tiers, IGW, NAT count from `lean.tfvars` = 1 and `full.tfvars` = 2, isolated route tables with the local route only) and outputs for env.
- [QA] `tests/infra`: no `resource` under `awsenv/`, README headings, `default_tags`, backend without DynamoDB. `tests/dev01`: subnets and routes, a second plan stopped by the lock, bucket versioning, tags.
- After the merge, the Owner runs the bootstrap script, applies singleton locally and adds the NS records at Namecheap at once (Thu 12 or Fri 13 Nov), so that DNS has propagated before Session 1.

**US01c Env layer serves the app over HTTPS.** Depends on: US01a, US01b.
- [Infra] Env root:
  - workspace `dev01`;
  - group outputs read through `terraform_remote_state` with `defaults`, so a PR plan works while group is not applied (SP1-D9; verify at plan time);
  - `dev01.tfvars` and `dev01_full.tfvars`;
  - an `image_tag` variable.
- [Infra] Module `edge`: S3 UI bucket with public access blocked, CloudFront with OAC, the us-east-1 certificate, redirect to HTTPS, behaviours `/` and `/api/*` (`/api/*` uses CachingDisabled), 5xx error caching at 0 seconds, and the CloudFront Function for deep links (D-DL8).
- [Infra] Module `load_balancer`: ALB, HTTPS listener only, regional certificate, origin hostname (D-DL15). The CloudFront-only restriction (prefix list and origin header) comes with US11 (SP1-D8).
- [Infra] Module `app_service`: cluster, service (Terraform ignores `desired_count`), task definition with 0.25 vCPU and 0.5 GB, security group from the ALB security group on port 8000 only, log group, execution role, circuit breaker with rollback, health check `/healthz`.
- [Infra] Module `database`: PostgreSQL 17 on `db.t4g.micro`, single-AZ, in the isolated subnets, security group on 5432 from the app security group only. The password is created the Q-D13 way from the start (SP1-D6).
- [Infra] DNS records (app hostname, origin hostname, certificate validation) and `docs/runbooks/session.md`: local image build and push tagged with the 40-character SHA, group apply, env apply, checks, then destroy env and group locally.
- [QA] `tests/infra`: no public IP, security group rules, `publicly_accessible = false`, public access block on buckets. `tests/dev01`: `dig`, TLS and HTTP redirect, one task, one NAT gateway, no-change plans, `/healthz` healthy.
- Plan point: the negative test of CNT-AC03 (API process stopped makes the target unhealthy) needs a method. ECS Exec would widen IAM; an alternative is a task revision whose command does not start the app. The plan decides with QA.

**US02 Budget and alert email.** Depends on: US01b.
- [Infra] Module `alerting` (group): SNS topic `cms-alerts`, email subscription from variable `alert_email`, topic policy for Budgets, CloudWatch and EventBridge.
- [Infra] Module `budget` (singleton): $2 a month, actual cost, notifications at 80% and 100% to the topic ARN built from its fixed name (D-DL13).
- [Infra] Git-ignored local tfvars file and `.gitignore` entry (SP1-D3). `docs/runbooks/alert-email.md` (the Owner sets the address and confirms the subscription).
- [QA] `tests/infra`: no tracked file contains a real address, budget values. `tests/dev01`: subscription confirmed, test message received, budget notifications present.
- Verify at plan time (R-02): AWS Budgets accepts a topic that does not exist yet when singleton is applied (D-DL13).

**US03 Session destroy workflows.** Depends on: US01b (layer paths).
- [CI] Four workflows:
  - `terraform_destroy_dev_env.yml` and `terraform_destroy_dev_group.yml`: `workflow_dispatch` only, profile input, a typed confirmation, environment `dev01`, per-layer `concurrency`, OIDC deploy role;
  - `terraform_force_unlock_dev.yml`: layer and lock ID as inputs;
  - `create_terraform_workspace_dev.yml`.
- [QA] `tests/infra`: the `on:` section of each workflow is `workflow_dispatch` only, plus `permissions`, `concurrency` and `timeout-minutes`.
- The workflows can run on dev01 only after US05 (the role) and US06 (the deploy role's permissions). Until then the session runbook destroys from a local shell. Usage notes go in the workflow files, not in a shared runbook (SP1-D2).

**US04 Local stack.** Depends on: US01a.
- [Infra] `compose.yaml` with `postgres:17` (the same major version as RDS), the API (from `src/api`) and the Vite dev server. Only local placeholders, no `.env` file. `testdata/mock/` mounted read-only.
- [FE] Vite proxy for `/api`.
- [QA] `tests/infra`: compose services, no AWS values, the mock mount. Local `/healthz`.
- The mock data loader comes with US17 (BL-D9), which uses the same loader locally and on dev01 (section 4). US04 also gives the standard way to get the PostgreSQL that `tests/api` needs from US08 on.

**US05 Pull-request checks.** Depends on: US01a, US01b, US01c (it scans and plans all three layers).
- [Infra] Module `github_oidc`, called from singleton: the OIDC provider, `cms-ci-plan` (read-only plus the state lock object) and `cms-ci-deploy` (trust only for `repo:EdwardTruong0412/CMS:environment:dev01`, D-DL12). The deploy role's permission policy comes with US06 (SP1-D7).
- [CI] The following workflows:
  - `api_test.yml` (with a PostgreSQL service) and `web_build.yml`, matching `make check`;
  - `terraform_fmt.yml`;
  - `terraform_validate_dev_*`, `terraform_plan_dev_*`, `tflint_dev_*` and `trivy_dev_*`, each for the three layers;
  - `trivy_modules.yml`;
  - a PR image build with a Trivy image scan and no push.

  Terraform is installed from `.terraform-version` (IAC-AC01). The group plan gets `alert_email` from the secret.
- [Infra] The reviewed Trivy ignore file. Each entry names the finding, the reason and the later story that removes it (SP1-D10).
- [QA] `tests/infra`: triggers, no access keys, `permissions`, the version source, the trust policy conditions. `tests/dev01` (singleton only): CICD-AC03 through CloudTrail Event history (the trail itself is US14), ECR has no image with the PR's SHA. Negative PRs (one ruff violation, one unencrypted bucket) run on throwaway branches.
- There is a chicken-and-egg problem: the PR checks of US05 itself need the plan role that US05 creates. In Q-D11 order, the Owner applies singleton from the US05 branch, sets the GitHub variables and the environment, and re-runs the checks. The approver escalates US05 in any case (pipeline, IAM), so this happens at `needs-human`. After the merge, the Owner makes the checks required (KO-23 step 2).
- Size: M by the backlog, about 2 to 2.5 days. It stays M only if the deploy role's permissions move to US06.

**US06 CD run.** Depends on: US05, US01c.
- [CI] The CD workflow (`workflow_dispatch` on `develop`, environment `dev01`) runs these steps in order:
  1. Pre-flight: office hours in ICT, ECS desired count above 0, RDS available.
  2. `image_build_push_dev`: Trivy fails on fixable HIGH or CRITICAL, secret scan, push with the 40-character SHA.
  3. `terraform_apply_dev_*` with `image_tag`.
  4. Migration task (run, wait, check the exit code).
  5. `deploy_ecs_dev`: update the service, wait until stable.
  6. `deploy_web_dev`: sync and invalidate, wait until completed.
  7. Smoke test, and record the duration.
- [Infra] Migration task definition in `app_service` (same image, command `alembic upgrade head`), and the deploy role's permission policy in `github_oidc`.
- [QA] `tests/infra`: job order through `needs:`, no push trigger. `tests/dev01`: running image = run SHA, `alembic current`, asset names, invalidation completed, duration.
- Size: L at the limit. If the plan finds more than 3 days, the cut is "image and apply" (CNT-AC04, CNT-AC05, CNT-AC07) versus "migrate, roll out, publish, smoke test". That split would be the PO's at refinement.
- The plan must also say which layers the CD run applies. CICD-AC07 (every layer's plan clean after a run) pulls toward all layers. Applying singleton from CI would need the deploy role to manage IAM, which the approver treats as an exposure item. So the plan decides and escalates if needed; I do not decide it here.

**US07 Secrets and encryption.** Depends on: US01c.
- [Infra] Module `encryption`: keys `data` and `logs`, rotation on, key policies for CloudFront OAC and CloudWatch Logs (D-DL11).
- [Infra] Module `app_secrets`: setup token (48 characters) and JWT key through ephemeral `random_password` and `secret_string_wo`. The DB password from US01c is moved under it if the plan prefers.
- [Infra] Database storage and backups on the `data` key, 7-day backups (SCALE-AC09). UI bucket on SSE-KMS. Log group on the `logs` key.
- [Infra] The ECS `secrets` field maps the secrets to `CMS_DB_PASSWORD`, `CMS_JWT_KEY` and `CMS_SETUP_TOKEN` (SP1-D4). The execution and task roles get `GetSecretValue` on the three ARNs only, plus `kms:Decrypt`.
- [QA] `tests/infra`: no `secret_string`, write-only arguments. `tests/dev01`: KeyManager is `CUSTOMER`, `simulate-principal-policy`, a state search for secret values, backup retention.
- The recovery secret (Q-D15) waits for US41, because SEC-AC10 names three secrets.
- Verify at plan time (R-02): ephemeral resources and write-only arguments in Terraform 1.16.4 and the chosen AWS and random provider versions (Q-D13); whether KMS keys pending deletion are billed (Q-D12, OQ-2). Replacing RDS to encrypt it is harmless because env is rebuilt every session, but the approver will escalate it as a stateful change.

**US08 First admin setup.** Depends on: US01a and US04 for the build. It depends on US07 only for dev01 (SP1-D4, SP1-D13).
- [DB] Alembic scaffolding (`src/api/migrations/`, the file template and naming convention from KO-12), then one migration for `user_account` and `app_setup`.
- [BE] Shared password rules (LGN-AC09, LGN-AC10, Unicode letter classes) and Argon2id (LGN-AC18, `argon2-cffi`, a new dependency).
- [BE] `POST /api/v1/setup`: constant-time token comparison, one transaction, the race lost on the `app_setup` primary key (D-DL6). `setup_required` added to the status response.
- [FE] `react-i18next` with `en.json` and `vi.json` and the `errors.<CODE>` keys (D-DL8, KO-14). Routing on load from the status response (SCR-00 placeholder, SCR-01, SCR-02 placeholder). SCR-01 with field errors. The `tests/web` runner is chosen here (proposal: Vitest).
- [QA] `tests/api`: token cases, the password matrix, hash checks, concurrent setups. `tests/web`: SCR-01.

**US09 Log in and log out.** Depends on: US08. It depends on US07 for dev01.
- [DB] Migration for `user_session`. `login_throttle` waits for US13.
- [BE] `POST /api/v1/auth/login`: normalised email, dummy hash for unknown emails, one `LOGIN_FAILED` 401, a session row, JWT HS256 in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie with path `/api` (D-DL2). `PyJWT` is a new dependency.
- [BE] Logout, `me`, and the shared session dependency (F-AUTH-05: signature, ended session, active user). Idle and 8-hour limits go to US10 through the clock. Custom header on state-changing requests. No body, cookie or token in any log (SEC-AC13).
- [FE] SCR-02, a header with log out on every screen, a route guard (LGN-AC04), and a placeholder home in place of SCR-10.
- [QA] `tests/api` and `tests/web`. `tests/dev01`: SEC-AC13 log search, and the NET-AC08 test point (an unauthenticated `/api/` request gets the API's refusal).
- Size: M, about 2 days, at the upper end because of the identity code.

## 2. Order of work, Dev assignment and parallel runs

One story goes to one Dev. Two lanes keep concurrent runs on different files.

| Lane | Dev | Stories, in order | Target merge |
| --- | --- | --- | --- |
| Terraform and pipeline | Dev 1 | US01b, US01c, US05, US06 | US01b Fri 13, US01c Tue 17, US05 Thu 19, US06 carried to about Tue 24 Nov |
| App and small infrastructure | Dev 2 | US01a, US04, US03, US02, US08, US07, US09 | US01a Wed 11, US04 Thu 12, US03 Fri 13, US02 Mon 16, US08 Wed 18 (merge held until after Session 1), US07 Fri 20, US09 carried to about Tue 24 Nov |

**Pairs that run in parallel (no shared files, interfaces fixed beforehand):**
- US01b with US04 and US03. US01b touches singleton and group and their modules. US04 touches `compose.yaml` and the Vite config. US03 touches four workflow files. Runbooks are one file per procedure (SP1-D2).
- US01c with US02, and then with US08. US01c touches env and its modules. US02 touches `modules/budget`, `modules/alerting`, the singleton and group calls, and `.gitignore`. US08 touches only `src/api` and `src/web`.
- US05 with US07. This is allowed only if US05's plan, and with it the ignore list, is approved before US07's plan, and the Owner merges US05 first. Both stories escalate at G5, so the Owner controls the order. After that, US07's PR runs the new checks against its own resources and removes the ignore entries it makes obsolete.
- US06 with US09. US06 touches workflows and `app_service`. US09 touches the API and web auth code.

**Pairs that do not run in parallel:**
- US05 with US01c, or with any story that adds new Terraform. Whichever PR opens second meets checks that the other branch never saw.
- US02 with US05. Both edit `awsenv/dev/singleton/main.tf`. US02 goes first, so that the US05 group plan includes `alert_email`.
- US06 with US07. Both edit `app_service` and the task definitions.

**Critical path:** US01a, US01b, US01c, US05, US06. That is about 10 to 10.5 Dev days against 9 days left after Planning, before G4, review rounds and G5 waits. A second chain is US01c, US07, then US09 on dev01.

**Forecast:**
- Merged by Fri 20 Nov: US01a to US01c, US02 to US05, US08, and probably US07.
- Carried over, in progress: US06 and US09 (about 1.5 days each).
- Done at G6 in Sprint 1, which needs Session 1 for the stories that change dev01: US01, US02, US03, US04, US05.

The order breaks backlog priority only where a dependency forces it (US08 before US06 and US07 in time). Releases and scope stay as they are; R-10 re-plans the dates at the Sprint Review.

**Plans and G4 just in time, in batches to save the Owner's time:**

| Day | Plans for G4 |
| --- | --- |
| D1 | US01a, US01b |
| D2 to D3 | US04, US03, US01c, US02 |
| D5 to D6 | US08, US05 |
| D7 | US07, US06 |
| D8 | US09 |

I create each story branch right after its G4 approval.

## 3. Prerequisites before the first `/story` run, in order

1. The Owner approves the Sprint 1 Planning record (`reports/sprints/sprint-1-planning.md`, PM/SM) and the Sprint Goal. A proposal from the Dev Lead side: "dev01 is built from the repository and serves the walking skeleton over HTTPS, with cost alerts, PR checks guarding `develop`, and every session destroyed at its end."
2. The Owner answers OQ-S1-1 (the US01 split). The PO records the split in `docs/backlog.md` (story lines, Delivers, Depends on, a BL-D row) on its own branch, after the Owner reviews the diff. `/story next` and the preflight read the story lines from `origin/develop`, so this must merge first.
3. The Owner applies branch protection step 1 on `develop` (KO-23): PR required, force push and deletion blocked, the Owner as bypass.
4. `REVIEW.md` (KO-16), as its own PROC task and branch, merged before round 1 of the first run: the code lens reviews against it. In the same or a separate PROC task (PM/SM, governance files), `.claude/agents/approver.md` line 73 and `.claude/agents/reviewer-infra.md` line 81 still say "$10 budget". They should say $2 (Q-O57), or the cost escalation check works against the wrong number.
5. Check the Codex sandbox before US01a (QA or Dev Lead, as an approved check). `make check` needs `pip` and `npm ci` (registry downloads), `tflint --init` (plugin download) and, from US08 on, a local PostgreSQL. `codex exec --sandbox workspace-write` disables network access by default, as far as I know. If the check fails, see OQ-S1-2.
6. The US01a plan, and the G4 section for US01a in `docs/gates/G4.md` (new file, prepared by the PM/SM) showing `Owner approval: [x]`.
7. The Dev Lead creates `feature/US01a_<summary>` from `develop`.
8. QA writes and commits the US01a tests on that branch as `test(US01a): ...`, touching only `tests/` and `testdata/mock/`, after the Owner reviews the diff (global rule 3: this commit is outside a story run).
9. Summaries named exactly as the skill's preflight expects: `reports/handoff/US01a-po-summary.md`, `US01a-dev-lead-summary.md` and `US01a-qa-summary.md`. The earlier PO hand-off used `-product-owner-summary.md`, which the preflight would not find.
10. The PM/SM gives the Owner one combined summary. The Owner types `/story US01a`. From then on, steps 6 to 10 repeat for each story.

Owner actions during the sprint (not questions):
- After the US01b merge (Thu 12 or Fri 13): bootstrap the state bucket, apply singleton locally, add the NS records at Namecheap.
- Before Session 1: re-apply singleton with US02 (budget), and create the local alert-email tfvars file.
- During the US05 run: apply singleton from the US05 branch, set the GitHub repository variables, the secret and the `dev01` environment, and re-run the checks.
- After the US05 merge: KO-23 step 2.
- Hold the G5 of US08 until Session 1 is over (SP1-D13).

## 4. How the US06 plan (and the US33 plan later) settle "Notes for Sprint Planning" points 1 to 3

This section gives the direction only. The decisions go in the plans.

1. **The first CD run of a session (R-05).** Each session starts with an infrastructure step: group apply, then env apply (through their workflows once US05 and US06 exist, from a local shell before that). The env apply uses the newest image already in ECR, which is kept between sessions in singleton. For the very first session, the Owner pushes the first image with the US01c local commands. The Owner then waits until RDS is `available` and the ECS desired count is 1, and only then starts the CD run. So the US33 pre-flight (CICD-AC14) passes for a real reason, and the 30-minute limit of CICD-AC16 covers only the CD run. The env apply (RDS and CloudFront creation) stays outside it. US06 builds the pre-flight step, because CICD-AC06 makes it the first step. US33 adds the stop cases (18:30, weekend, 0 tasks, RDS not available), the migration-failure stop and the rollback alert, and keeps the same session order. Its 18:30 test point runs in the Release 2 evening session. The no-change plans of IAC-AC12 and CICD-AC07 need the same `image_tag` input as the deployed service; the plan says how the plan workflow reads it.
2. **The order of the UI publish and the smoke test.** The UI is built early, in parallel with the image, as an artifact. It is synced to S3 and invalidated, with a wait until the invalidation is completed, after the ECS rollout is stable and before the smoke test. The smoke test runs last, so it checks the deployed UI and API together (CICD-AC12, CICD-AC13), and the UI never goes live before the API it calls. BD-2 shows the opposite order. The US06 plan records the order as a decision, and BD-2 is corrected on the US06 plan branch for the Owner to see at G4. No criterion changes, so this is not a CR.
3. **Per-session setup and mock data.** `docs/runbooks/session.md` (started by US01c) gets one section per capability:
   - "start a session" and "deploy" (US06);
   - "create the first admin" (US08): the Owner reads the setup token with profile `3tier` and fills in SCR-01;
   - "load mock data" (US17, Sprint 2): proposed as a loader run from the Owner's machine through the API as the admin, which keeps `testdata/mock/` out of the image. About 64 requests, under both WAF limits.

   QA's dev01 checks get the admin login from shell variables the Owner sets for the run, never committed or logged. The PM/SM's per-session runbook points to these sections (project plan section 4).

## 5. Check sessions on dev01

Every session uses the lean profile (`group/tfvars/lean.tfvars`, `env/tfvars/dev01.tfvars`), runs on a weekday within office hours with deployments finished before 17:30 ICT, ends with env then group destroyed, and its cost is recorded the next day (RP-D1, Q-O57).

| Session | Proposed date | Stories verified | Contents |
| --- | --- | --- | --- |
| Session 1 | Wed 2026-11-18, about 09:30 to 15:00 ICT. Fallback Thu 19 Nov if US01c merges late | US01a to US01c (as one US01) and US02. US03 and US04 need no session: CICD-AC15 is a static check, US04 is local only | Singleton already applied (zone, ECR, budget). Group apply from a local shell, SNS subscription confirmed, env apply, first image pushed locally from the head of `develop` (US08 not merged yet, SP1-D13). QA's `tests/dev01` for US01 and US02. Lock test, and no-change plans in office hours. Destroy env, then group, from a local shell (the US03 workflows lack a role until US05 and US06) |
| Outside a session | Thu 19 or Fri 20 Nov, no extra cost | US05 | Its AWS checks need only singleton, which always exists: CICD-AC03 through CloudTrail Event history, no ECR image for the PR's SHA, trust policy |
| Session 2 | Proposed for Sprint 2, Wed 2026-11-25 (lean) | US06, US07, US08, US09, and the US03 workflows in use | First session using the "start a session" order of section 4 and a CD run, setup of the first admin, login and logout checks, destroy through the US03 workflows. Five stories, within RP-D1. Sprint 2 Planning confirms the date |

Session 1 has 4 stories if the split is approved (2 if not). I still recommend it: it is the first proof of the layers, and three R-02 items (D-DL13, Q-D13, RDS PostgreSQL 17) are only proven on AWS. It costs about $0.50 to $0.60 in lean (estimate), within the accepted $2 alert (OQ-2). Session 1 must be done by Thu 19 Nov so that its stories can pass DoD item 5 at G6 on Fri 20 Nov.

## 6. Risks, decisions, open questions, files

### Risks for the sprint

| Risk | Detail and response |
| --- | --- |
| R-10 Pace | The critical path (about 10 to 10.5 Dev days) is longer than the 9 working days left. US06 and US09 will probably carry over. Response: the lanes above, G4 in batches, re-plan at the Sprint Review |
| R-03 Owner bottleneck | Almost every Sprint 1 story escalates at G5 (pipeline, singleton or group, IAM, identity code, new dependencies), on top of G4 per story and the Owner's review of each QA test commit. Response: G4 batches, merges of escalated stories reviewed once a day |
| R-02 AWS assumptions | Checked in Sprint 1 plans: D-DL13 (US02); Q-D13 write-only and ephemeral support in Terraform 1.16.4 (US01c, US07); Q-D12 KMS billing (US07); RDS PostgreSQL 17 and D-DL15 (US01c); SP1-D9 remote state `defaults` (US01c) |
| R-05 First CD run | Settled by the session order in section 4 (US06 plan) |
| R-01 Cost | Singleton bills from about Thu 12 Nov (zone $0.50 a month, ECR). Session 1 destroys from a local shell because the US03 workflows cannot run yet; the session runbook ends with the destroy |
| R-06 (sprint form) DNS | NS delegation must propagate before the Session 1 env apply (ACM validation). Response: the Owner adds the NS records right after the US01b merge |
| R-04 Codex | In addition, the sandbox may block network access for `make check` (prerequisite 5, OQ-S1-2) |
| New: CI plans between sessions | Group and env do not exist between sessions, so an env plan that reads group state would fail every PR (CICD-AC02). Response: SP1-D9 in US01c, relied on by US05 |
| New: checks arrive mid-sprint | Modules from US01b and US01c have Trivy HIGH findings (no CMK, no WAF, no access logs) until US07, US11, US12 and US15. Response: SP1-D10 |
| New: secrets required before US07 | The API needs `CMS_SETUP_TOKEN` (and later `CMS_JWT_KEY`) with no default, so an image built after US08 would not start on dev01 before US07. Response: SP1-D13 |

### Decisions made (Dev Lead tier, workflow section 8; the Owner can override any of them at G4)

| ID | Decision | Reason |
| --- | --- | --- |
| SP1-D1 | Two lanes. Dev 1: US01b, US01c, US05, US06. Dev 2: US01a, US04, US03, US02, US08, US07, US09. The parallel and serial rules are those of section 2 | One Dev per story; no shared files between concurrent runs; the critical path stays on one Dev |
| SP1-D2 | Runbooks are one file per procedure in `docs/runbooks/` (`bootstrap.md`, `session.md`, `alert-email.md`). `CLAUDE.md`'s directory tree is updated by the PM/SM in a later governance task | Parallel stories never edit the same runbook file; meets the "documented list" of IAC-AC13 |
| SP1-D3 | GitHub interface: repository variables `CMS_CI_PLAN_ROLE_ARN` and `CMS_CI_DEPLOY_ROLE_ARN`, secret `CMS_ALERT_EMAIL`, environment `dev01`. Terraform variable `alert_email`, local file `awsenv/dev/group/tfvars/alert.local.tfvars` (git-ignored). Region written literally as `ap-southeast-1` | US02, US03 and US05 can be planned and built in parallel against fixed names |
| SP1-D4 | App settings use the prefix `CMS_`. The secrets arrive as `CMS_DB_PASSWORD`, `CMS_JWT_KEY` and `CMS_SETUP_TOKEN` through the ECS `secrets` field (US07). Locally, `compose.yaml` gives placeholders | Lets US08 and US09 be built before US07 merges |
| SP1-D5 | US01a writes `.terraform-version` (local tooling needs it). IAC-AC01 stays with US05, as the backlog assigns it. KO-22's "where IAC-AC01 owns it" is read as "where the pin is first needed" | Backlog and kick-off read together without a change |
| SP1-D6 | US01c creates the DB password with ephemeral `random_password` and `password_wo` (Q-D13) from the first apply. The CMK and the SEC-AC08 and SEC-AC09 proof stay with US07 | No secret ever enters state, not even before US07 |
| SP1-D7 | US05 creates the OIDC provider, the plan role and its policy, and the deploy role's trust policy. The deploy role's permission policy comes with US06, its first user | Keeps US05 at M. CICD-AC04 and CICD-AC05 do not need the deploy permissions |
| SP1-D8 | CloudFront reaches the ALB over HTTPS from US01c (D-DL15). The prefix list and origin header come with US11 | No HTTP listener built only to be removed later; US11 stays a pure restriction |
| SP1-D9 | Env reads group outputs through `terraform_remote_state` with `defaults` (verify at plan time) | PR plans of env pass while group is destroyed between sessions |
| SP1-D10 | Trivy findings of resources that exist before US05 go into the reviewed ignore file with a reason and the story that removes each one. That story's plan removes its entries | IAC-AC11 holds from US05 on without pulling later stories forward |
| SP1-D11 | Each story's plan is written just in time, in the G4 batches of section 2 | Plans reflect the code merged before them |
| SP1-D12 | Session 1 on Wed 18 Nov, before RP-D1's batch would otherwise fill, and Session 2 in Sprint 2 | The first proof of the layers and the R-02 items early; the cost stays within the accepted alert |
| SP1-D13 | The G5 of US08 (an identity-code escalation) is held until Session 1 has ended. Session 1's image is built from the head of `develop` without US08 | A deployed image would otherwise need a setup token that does not exist before US07 |

### Open questions for the Owner (Owner tier only)

- **OQ-S1-1 Split of US01 under the frozen baseline.** Baseline 1 says any change to the stories goes through a CR. The backlog, frozen in the same baseline, also says the PO splits US01 at refinement if it is over 3 days. The split keeps all 23 criteria, the release and the sprint unchanged.
  - **Recommended answer:** treat the split as refinement that `baseline-1` already provides for. No CR and no new tag; the PO records it as a BL-D row in `docs/backlog.md`, which you review at commit.
- **OQ-S1-2 (only if prerequisite 5 fails) Network access in the Codex sandbox.** If `codex exec --sandbox workspace-write` cannot reach the package registries, the tflint plugin source or a local PostgreSQL, the Dev cannot run `make check`. Changing the sandbox setting weakens isolation, so the choice is yours.
  - **Recommended answer:** allow network access for the Dev command of story runs (for example `-c sandbox_workspace_write.network_access=true` in `.claude/skills/story/SKILL.md`, a governance change). Worktrees hold only mock data and no secrets, and the `protect-tests` hook and CI check stay in force.
  - **Alternative:** you pre-install the dependencies and start PostgreSQL in each worktree before a run.

### Files produced

- `/Users/truongquy/Documents/wt-PROC08/reports/handoff/PROC08-dev-lead-summary.md` (this file).

Not changed and left to their owners: `docs/backlog.md` (PO, if the split is approved), `.claude/agents/approver.md` and `reviewer-infra.md` ($10 to $2, PM/SM governance task), `REVIEW.md` (Dev Lead, its own approved task), `docs/gates/G4.md` (PM/SM), `reports/sprints/sprint-1-planning.md` (PM/SM).
