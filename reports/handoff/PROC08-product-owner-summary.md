# Handoff: 2026-11-01 PROC08 - Product Owner summary (Sprint 1 Planning)

| | |
| --- | --- |
| Task | PROC08 Sprint 1 Planning, approved by the Owner on 2026-11-01 |
| Sprint | Sprint 1, Mon 2026-11-09 to Fri 2026-11-20 (Planning Mon 2026-11-09, Review G6 and Retrospective Fri 2026-11-20) |
| Scope | US01 to US09 of Release 1 (`docs/project-plan.md` section 1), Baseline 1 (`baseline-1`), unchanged |
| Read | `docs/backlog.md` (US01 to US09, "Notes for Sprint Planning", decisions log), `docs/release-plan.md`, `docs/project-plan.md`, `docs/kickoff.md` ("Ceremonies and Sprint Review schedule", KO-22), `docs/process/ai-native-sdlc-workflow.md` sections 6 and 8, `docs/intent/intent-001.md`, `docs/specs/spec-001.md` (US01 criteria, IAC-AC01), `docs/gates/G3.md`, `.claude/skills/story/SKILL.md` ("/story next") |
| Changed | Nothing except this file. `docs/backlog.md` is not edited; the US01 split in section 4 is a proposal |

## 1. Proposed Sprint Goal

By Fri 2026-11-20 the Owner can build dev01 from the repository, deliver a commit that passed the pull-request checks to it with one CD run, and log in over HTTPS as the first admin created through the one-time setup screen, with cost alerts reaching the Owner and every check session ending with env and group destroyed.

## 2. Why this sprint is valuable (Scrum question 1)

- **It turns intent-001 into a running system.** Intent section 3 asks for a working CMS on dev01 built on the Owner's architecture. After Sprint 1 the main path of that architecture exists end to end: Route 53, ACM, CloudFront, S3, ALB, ECS Fargate, RDS, ECR, Secrets Manager, KMS, GitHub Actions with OIDC. Sprint 2 adds the remaining Release 1 security, logging and data features (US10 to US18) on top of it.
- **It delivers 66 of the 102 criteria of the Release 1 exit check** (65%), including the personal-data rules of intent section 7 that must hold before any employee data exists: encryption at rest and in transit (item 3), access only after login (item 4, LGN-AC03), secrets never in state, logs or the image (item 5, SEC-AC09), and the first admin without a default account (item 7, SETUP group).
- **It puts the Owner's cost rule (Q-O57) in force from the first session.** The $2 budget and alert email (US02) and the destroy workflows (US03) come right after the skeleton, so no session can leave env and group running unseen (risk R-01).
- **It retires the highest risks early,** while there is time to re-plan: DNS delegation of `cms.imaprof.ink` and certificate validation (US01), OIDC from GitHub Actions (US05), the first CD run of a session (R-05, US06), and secret generation outside Terraform state (Q-D13, US07).
- **It measures the real pace** (stories merged per sprint), which the plan uses to re-plan Sprints 2 to 5 at the Review (PP-1, R-10).
- The Release 1 exit itself (all 102 criteria on dev01 in one lean session) is in Sprint 2; Sprint 1 is its foundation, not its end.

## 3. Stories taken, in backlog order

Criteria counts are the IDs on each story's "Delivers" line in `docs/backlog.md`. Total: 66 criteria, 9 stories (10 if the US01 split is approved).

| Story | Title | Size | Criteria | Done means (for the Sprint Review) |
| --- | --- | --- | --- | --- |
| US01 | Walking skeleton on dev01 | L | 23 | From a state bucket bootstrapped by the documented procedure, the Owner applies singleton, group and env (lean) in order; `https://dev01.cms.imaprof.ink/` shows the UI with a valid certificate, `/healthz` answers healthy from a non-root `python:3.13-slim` container, the API reaches the database, and a second `terraform plan` on each layer shows no changes. |
| US02 | Budget and alert email reach the Owner | S | 2 | The $2 monthly budget exists with 80% and 100% notifications to the SNS alert topic, and the Owner's email subscription to that topic is confirmed. |
| US03 | Owner ends a session by destroying env and group | S | 1 | The Owner ends a session with the manual destroy workflows for env then group, and only singleton is left; force-unlock and workspace-creation workflows run only by hand. |
| US04 | Developer runs the whole stack locally | S | 1 | `docker compose up` starts the API, PostgreSQL and the UI with mock data only, and the UI reaches the API locally without AWS. |
| US05 | Pull-request checks guard develop | M | 8 | A pull request to `develop` runs lint, tests, build, Terraform fmt, validate and plan, tflint and Trivy through OIDC with no change in AWS, and a failing check blocks the merge (shown with one deliberately failing PR). |
| US06 | Owner deploys develop to dev01 with one CD run | L | 9 | One manual CD run on `develop` builds, scans and pushes the image, applies Terraform, migrates, rolls out, publishes the UI and passes the smoke test within 30 minutes, and dev01 runs exactly that commit's image. |
| US07 | Secrets and stored data protected with project keys | M | 7 | The database password, JWT key and setup token exist in Secrets Manager and appear in no state, plan, log or image; every data store is encrypted (customer managed keys where required), each role reads only its own secrets, and RDS keeps 7-day backups. |
| US08 | First admin setup | M | 8 | With the setup token, the Owner creates the first admin with a password meeting the rule; the setup screen and endpoint are refused for good afterwards, and no default account ever existed. |
| US09 | Log in and log out | M | 7 | An admin logs in with email and password, a failed login shows one generic message, log out works from any screen, and every data request without a valid session is refused. |

Dependencies inside the sprint (from the backlog): US01 first; then US02, US03, US04, US05 and US07 can run in parallel; US06 after US05; US08 after US07; US09 after US08. The longest chain is US01, US07, US08, US09 (about 5 to 9 Dev-days at the backlog sizes, before review rounds and dev01 sessions), so US09 is the story most at risk of slipping. If it slips, it stays first in Sprint 2's order; no CR is needed because the order is unchanged (re-planning at the Review, `docs/kickoff.md`).

Points the story plans must settle (owned by the Dev Lead and QA, listed in "Notes for Sprint Planning"): the first CD run of a session (point 1, US06), the order of UI publish and smoke test (point 2, US06), and the per-session setup and mock data steps (point 3, US08).

Owner actions needed during the sprint (values or acts only the Owner holds, not questions): set the NS records for `cms.imaprof.ink` at Namecheap during US01; confirm the SNS email subscription during US02; read the setup token from Secrets Manager in the US08 check; start each CD run by hand from US06 on. Before US03 is merged, the Owner destroys env and group with the documented local commands (US01 notes).

## 4. Refinement check (stories over 3 days)

Size scale (BL-D4): S about 1 day, M 1 to 2 days, L 2 to 3 days for one Dev in one `/story` run.

| Story | Finding |
| --- | --- |
| US01 (L, 23 criteria) | **Likely over 3 days. Split proposed below.** It owns 23 criteria, 2.5 times the next largest story (US06, 9). It spans the state bucket bootstrap, all three layers, two ACM certificates, CloudFront with two origins, S3, VPC with NAT, ALB, ECS, RDS, the Dockerfile, the first API and UI code, the Makefile `bootstrap` and `check` targets and the module READMEs. It also waits on an external step: NS delegation at Namecheap and certificate validation, which can take up to a day to propagate (RP-D3). A 3-day run with a possible 1-day DNS wait has no slack. |
| US06 (L, 9 criteria) | At the upper limit but not split. The criteria form one pipeline that is only valuable whole (one run, 30 minutes, the exact commit). The Dev Lead confirms the size in the US06 plan once Notes 1 and 2 are settled; if the plan shows more than 3 days, the PO refines then. |
| US02 to US05, US07 to US09 | Within the limit (S or M). No change. |

### Proposal P-1: split US01 into two end-to-end stories (not applied)

Each part is a slice the Owner can see working on dev01; it is not a split into technical tasks. All 23 criteria are kept, each in exactly one of the two parts (9 + 14 = 23).

**US01a UI served over HTTPS on the app hostname**
As the Owner, I want to bootstrap the state bucket and build singleton and env from the repository, so that `dev01.cms.imaprof.ink` serves the placeholder UI over HTTPS through CloudFront from a private bucket, and the DNS delegation and certificates are proven before the API work starts.
Delivers (9): IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08, IAC-AC14, NET-AC07, NET-AC11, SEC-AC01, SEC-AC02.
Also delivers the US01 enablers that every later story needs: `.terraform-version` (see S1-PO-D4) and the Makefile `bootstrap` and `check` targets (`CLAUDE.md`).
Depends on: none. Size: M.

**US01b API answers from the database through the app hostname**
As the Owner, I want to add the group layer, the ALB, the ECS service, RDS and the API container, so that requests under `/api/` reach the API, `/healthz` reports healthy from the database-backed service, and all three layers apply in order and plan clean.
Delivers (14): IAC-AC05, IAC-AC06, IAC-AC12, NET-AC01, NET-AC02, NET-AC03, NET-AC04, NET-AC08, NET-AC09, NET-AC10, CNT-AC01, CNT-AC02, CNT-AC03, SCALE-AC01.
Depends on: US01a. Size: L (2 to 3 days).

Why the criteria fall this way (BL-D2, first story where a criterion can be fully proven):
- IAC-AC05 (singleton, group, env applied in order), IAC-AC06 (state of all three layers) and IAC-AC12 (no changes after apply for singleton, group and env lean) need the group layer, so they go to US01b.
- IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08 and IAC-AC14 are cross-cutting and can be proven in full on what US01a builds; US01b and later stories keep them passing, as the existing "Also checked in" line of US01 already says.
- NET-AC08 needs both origins, so it goes to US01b; its `/api/` refusal test point still runs in US09, as now.

Effect on the rest of the backlog: none on scope, criteria or order. Every "Depends on: US01" line (US02, US03, US04, US05, US07, US11, US12, US15) reads as "US01b", since each needs the group layer or the API; the "Also checked in" lines of US01 move with their criterion to the part that owns it. Sprint 1 then holds 10 stories with the same 66 criteria.

Does it need a CR? **No, in the PO's view.** The baseline backlog itself says that US01 is split at refinement if Sprint Planning finds it over 3 days (US01 notes, approved at G3), refinement is the PO's job inside the sprint (workflow section 6.1), and the split changes no scope, criterion, priority order or release (project-plan section 5: a CR is for requests outside the baseline). It is still a change to a frozen file, so it needs the Owner's approval before `docs/backlog.md` is edited (OQ-S1-1), and the edit gets its own reviewed commit.

## 5. Decisions, open questions and files

### Decisions log (PO defaults under workflow section 8, "Decision tiers"; the Owner can override any row)

| ID | Decision | Reason | Affects |
| --- | --- | --- | --- |
| S1-PO-D1 | Sprint Goal as in section 1: build, deliver and log in, with cost alerts and destroy in place. | It names the value of all nine stories in one outcome the Review can check; it follows the backlog order, as `docs/project-plan.md` section 1 requires. | Sprint 1 |
| S1-PO-D2 | US01 is judged likely over 3 days and proposal P-1 is made; US06 is kept whole and re-checked at its plan. | 23 criteria and an external DNS wait (US01); US06 is one pipeline that has value only as a whole. | US01, US06 |
| S1-PO-D3 | The split in P-1 is refinement inside the baseline, not a CR. | Anticipated in the US01 notes approved at G3; no change to scope, criteria, order or release. | US01 |
| S1-PO-D4 | IAC-AC01 stays owned by US05, as the frozen backlog says. US01 (or US01a) creates `.terraform-version` with `1.16.4`, because Terraform cannot run without it, and QA may test its local part there; the criterion as a whole, including "every GitHub Actions workflow uses exactly that version", is proven in US05 when the workflows exist. **Note for the PM/SM:** KO-22 in `docs/kickoff.md` says "US01, where IAC-AC01 owns it"; the ownership part is inaccurate and can be corrected in the next approved docs change. Both statements stay satisfiable, so this is not an Owner question. | Keeps the backlog's single ownership (BL-D1, BL-D2) and the Owner-approved G3 line "the pin moves to US01" both true. | IAC-AC01, US01, US05 |
| S1-PO-D5 | Proposed IDs for the split are `US01a` and `US01b` (branches `feature/US01a_<summary>`, `feature/US01b_<summary>`), so US02 to US41 keep their numbers and every existing reference stays valid. `/story next` reads the story token as given (`.claude/skills/story/SKILL.md`), so a suffix fits its format; the Dev Lead confirms the preflight and the dashboard accept it before the edit. | Renumbering 40 stories would touch every cross-reference in the baseline. | Backlog, `/story` |
| S1-PO-D6 | Order of slip: if the pace is lower than planned, US09 (last in order and at the end of the longest chain) moves to the top of Sprint 2 first. Input to the PM/SM's re-planning, not a change of order. | Follows the backlog order; keeps the build-and-deliver part of the Sprint Goal intact. | Sprint 1, Sprint 2 |

### Open questions for the Owner

1. **OQ-S1-1 Approve the split of US01 into US01a and US01b (proposal P-1)?**
   - Why it matters: the backlog is frozen at `baseline-1`, so even a refinement that keeps every criterion is edited only with your approval. A US01 run over 3 days delays every Sprint 1 story, because all of them depend on it.
   - What it blocks: the US01 plan (G4) and its QA tests, which are written per story. The Dev Lead can draft the plan either way; the split decides whether there is one plan or two.
   - Recommended answer: **Yes.** Approve P-1 as written (US01a with 9 criteria, US01b with 14), as refinement without a CR. The PO then edits `docs/backlog.md` (two story lines and two detail sections in place of US01, "Depends on" lines updated, coverage recounted at 183 of 183), and you review that commit. If you say no, US01 stays one L story and the US01 plan must show it fits in 3 days.

No other Owner-tier question was found. Sizes, criteria assignment, the Sprint Goal wording and the ID format are routine and are in the decisions log above.

### Files produced

| File | State |
| --- | --- |
| `reports/handoff/PROC08-product-owner-summary.md` | New (this file) |
| `docs/backlog.md` | Unchanged; edit only after OQ-S1-1 is approved |
