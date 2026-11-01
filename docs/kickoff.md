# Kick-off: CMS

| | |
| --- | --- |
| Step | Workflow Step 8, Kick-off (`docs/process/ai-native-sdlc-workflow.md` section 4) |
| Author | Dev Lead (conventions, branching, Definition of Done reference), 2026-11-01. The PM/SM writes the ceremonies section |
| Status | Draft for Owner approval, input to G3. Frozen with the baseline at Step 9 (tag `baseline-1`) |
| Produces | This file, `CLAUDE.md` v1, `AGENTS.md` v1 |

## Purpose and inputs

Step 8 settles how the team writes code and moves it into `develop`, before Sprint 1 starts. It builds on:

- Process: `docs/process/ai-native-sdlc-workflow.md` (v3.1), `.claude/rules/global.md`, `.claude/skills/story/SKILL.md` (story runs), `.gitmessage`
- Design: `docs/specs/spec-001.md` (acceptance criteria, NFR, Basic Design BD-1 to BD-9, Decisions log), `docs/specs/function-list.md`
- Planning: `docs/backlog.md`, `docs/release-plan.md`, `docs/project-plan.md`, `docs/radio.md`
- Earlier conventions work: `reports/handoff/PROC03-dev-lead-summary.md` (check command and first conventions, PR #5)

## Coding conventions

The single source is `AGENTS.md`, sections "The check command" and "Coding convention". Codex reads only `AGENTS.md`, and `CLAUDE.md` points there, so the rules exist once. This section is a map, not a copy. When a rule changes, change `AGENTS.md` only.

| Area | `AGENTS.md` section | In short |
| --- | --- | --- |
| Check command | "The check command" | `make check` from the repo root: ruff, ruff format, mypy strict, pytest; npm lint, typecheck, build; terraform fmt, tflint. No AWS access, no skipped step |
| Python API | "Python: API" | Python 3.13, fully typed, routers without logic, error codes not sentences, SQLAlchemy 2.x sync, settings from the environment, no secrets or personal data in logs, injectable clock, exact dependency pins |
| Database and Alembic | "Database and Alembic migrations" | Singular `snake_case` tables from BD-5, app-generated UUIDs, `timestamptz`, `CHECK` instead of `ENUM`, constraint naming convention, date-prefixed migration files, working `downgrade()`, no model imports in migrations |
| Dockerfile and local stack | "Dockerfile and local stack" | `src/api/Dockerfile`, multi-stage, final `python:3.13-slim`, numeric non-root user 10001, port 8000, no secret in any layer, `compose.yaml` at the root |
| TypeScript and React | "TypeScript and React: web" | Strict TypeScript, one API client, closed page on 503, ESLint plus Prettier, screen layout, `react-i18next` with `en.json` and `vi.json` and `errors.<CODE>` keys, DD/MM/YYYY |
| Terraform | "Terraform" | Resources only in modules, README per module, documented variables and outputs, `cms-` and `cms-dev01-` names, tags from `default_tags`, profiles only in tfvars, no secret in state, root module file layout |
| GitHub Actions | "GitHub Actions" | OIDC only, narrowest `permissions`, manual-only destroy workflows, timeouts and per-layer concurrency, third-party actions pinned to a commit SHA, Terraform from `.terraform-version` |
| Tests | "Tests" | Owned by QA, read-only for Devs; `tests/api/`, `tests/infra/`, `tests/web/`, `tests/dev01/`; test names start with the criterion ID |

Gaps filled in `AGENTS.md` at this step: database naming and Alembic file naming, Dockerfile and local stack, web lint, layout and translation keys, Terraform root file layout and resource naming, GitHub Actions pinning and concurrency, Python dependency pinning and naming, test layout and naming. Each new rule that is a choice is logged below.

## Git branching rules

### Branches

- **`develop`** is the only long-lived branch and the base of every pull request. It changes only through a merged pull request. There is no `main` branch (the remote has none); if one is ever created, nothing is merged into it without a Change Request.
- **Work branches** all use the form `feature/<ID>_<summary>`, created from `develop` before any work on the item:

  | ID prefix | Used for | Example |
  | --- | --- | --- |
  | `US<nn>` | A backlog story | `feature/US01_walking_skeleton` |
  | `PROC<nn>` | Process, agent and tooling changes | `feature/PROC06_kickoff` |
  | `DES<nn>` | Design and planning documents | `feature/DES01_basic_design` |
  | `FIX<nn>` | A fix outside any story, approved by the Owner (a bug found later is normally a new backlog item, workflow section 9) | `feature/FIX01_cd_preflight_timezone` |
  | `CR<nnn>` | Work from an approved Change Request | `feature/CR001_export_csv` |

  `<summary>` is short, lower case, words joined by `_`. One branch per item; QA's tests and the Dev's code for a story go on the same branch (global rule 4). The `feature/` prefix is kept for every item because the `Protect tests` check and the `/story` preflight look for it.
- The Dev Lead creates story branches after G4 (global rule 4). The PM/SM creates branches for process and design work, after the Owner approves the task.

### Worktrees

- A Dev works in `../wt-<story>-dev<k>` (for example `../wt-US01-dev1`), next to the repository. The `protect-tests.py` hook protects `tests/` only in worktrees with the `wt-` prefix.
- Other agent work that needs its own checkout uses `../wt-<ID>` (for example `../wt-PROC03`).
- A worktree is removed after its branch is merged or dropped.

### Commits

- Every message follows `.gitmessage`: `<type>(<scope>): <summary>`, then `Why:`, `What:`, `Refs:`, `Approved-by: Owner (<date>)` and `Co-Authored-By:`.
- One commit per plan task. The Dev proposes commits in the handoff report and never commits (`AGENTS.md`).
- The `test` type is used only by QA, for commits that touch only `tests/` and `testdata/mock/` (`.github/workflows/protect_tests.yml`).
- No commit without the Owner's review of the staged diff and message (global rule 3), except inside a story run.

### Pull requests and merging

- One pull request per branch, into `develop`. Opened by the PM/SM, or by the coordinator in a story run.
- Merge method: merge commit (`gh pr merge --merge`). No squash or rebase merge, so the per-task commits and their `Approved-by` lines stay in the history.
- A pull request is merged only after its checks pass (CICD-AC02) and its gate is approved: the Owner at G5, or the approver agent in a story run (global rules, "Story runs").
- Agents never force-push `develop`, never push to it directly, never merge with `--admin` or skip a check. Only the Owner may force-push, by hand (KO-OQ1).

### Story runs

A `/story <story>` run (`.claude/skills/story/SKILL.md`) is the one exception to global rules 1 to 3: the coordinator commits the Dev's proposed commits on the story branch, pushes it, opens the PR and merges it on the approver's `APPROVE`. The branch, worktree and commit format rules above still apply. Deployment is never part of a run.

### After the merge

- The local branch is deleted (`git branch -d <branch>`) and its worktree removed.
- The remote branch is kept unless the Owner decides otherwise. A story run deletes its own remote branch, as the skill describes; the Owner approved that with the skill.

### Tags

- `baseline-1`: annotated tag on `develop` at G3 (Step 9). Each approved Change Request that changes the baseline adds `baseline-<n>` (`docs/project-plan.md` section 5).
- `v1.0.0`: annotated tag on `develop` at G7, the release of intent-001. Releases 1 and 2 of `docs/release-plan.md` are delivery increments and are not tagged; their exit checks are recorded at the Sprint Review.
- The PM/SM creates and pushes a tag only after the Owner approves it. Tags are never moved or deleted.

### Branch protection on `develop` (expectation)

GitHub settings are the Owner's, so the Owner applies them (see Open questions):

- Pull request required before merging; no direct push.
- Required status checks: the CICD-AC01 checks and `Protect tests`. The checks exist only after US05, so they are added to the rule when US05 merges.
- Force push and branch deletion blocked for everyone except the Owner. The Owner keeps force push as a bypass (KO-OQ1, answered 2026-11-01), for example in a ruleset with the Owner's account in the bypass list. Because agents act through the Owner's account, GitHub cannot stop an agent's force push; the agent rule below (never force-push `develop`) is the safeguard.
- No required number of approving GitHub reviews: approvals are recorded in the gate files and `decision.md`, and GitHub does not let an account approve its own pull request, which would block every merge in this one-person repository.

## Definition of Done

The Definition of Done for a story lives in `docs/project-plan.md`, section 3, and is checked at G6. It is not repeated here. The project-level done-criteria DC1 to DC4 are in `docs/intent/intent-001.md`, section 8, and are checked at G7 (`docs/release-plan.md`).

Two points from this step support it:

- DoD item 2 relies on `make check`. The target and the CI parity in `api_test.yml` and `web_build.yml` are built in US01 and US05 (KO-17).
- DoD item 3 relies on reviews against `REVIEW.md`, which does not exist yet (KO-16).

## Ceremonies and Sprint Review schedule

Written by the PM/SM, 2026-11-01. Dates come from `docs/project-plan.md` section 1 and stay consistent with it; when the plan is re-planned, this calendar follows it.

### Sprint length

Two weeks, Monday to Friday of the following week (workflow section 6). Sprint Planning is on the first Monday. Sprint Review (G6) and the Retrospective are on the last Friday, Review first.

### Calendar

| Sprint | Dates | Sprint Planning | Sprint Review (G6) and Retrospective | Also in the sprint |
| --- | --- | --- | --- | --- |
| Step 8 and 9 | week of 2026-11-02 | | | Kick-off approval, then baseline freeze and G3 by Fri 2026-11-06 |
| 1 | 2026-11-09 to 2026-11-20 | Mon 2026-11-09 | Fri 2026-11-20 | First measurement of pace (stories merged per sprint) |
| 2 | 2026-11-23 to 2026-12-04 | Mon 2026-11-23 | Fri 2026-12-04 | Release 1 exit session on dev01 before the Review |
| 3 | 2026-12-07 to 2026-12-18 | Mon 2026-12-07 | Fri 2026-12-18 | |
| 4 | 2026-12-21 to 2027-01-01 | Mon 2026-12-21 | Fri 2027-01-01 (see KO-21) | Release 2 exit sessions on dev01 before the Review |
| 5 | 2027-01-04 to 2027-01-15 | Mon 2027-01-04 | Fri 2027-01-15 | Full verification session, rebuild, final teardown; G7 after the verification session |

Check sessions on dev01 (`docs/project-plan.md` section 4) are scheduled inside the sprint on a weekday within office hours, with deployments finished before 17:30 ICT (`docs/release-plan.md`). The PM/SM proposes each session date at Sprint Planning or when 3 to 5 merged stories are waiting for one (RP-D1).

### Timeboxes

Workflow section 6.1 gives the Scrum maximums for a one-month sprint and leaves the two-week values to the project. They are halved for a two-week sprint (KO-18). A timebox limits the Owner's time in the event; agent preparation happens before it.

| Event | Timebox | When |
| --- | --- | --- |
| Sprint Planning | 4 hours max | First Monday of the sprint |
| Daily summary (Daily Scrum) | 15 minutes of the Owner's reading | Each working day with activity |
| Sprint Review (G6) | 2 hours max | Last Friday of the sprint |
| Retrospective | 1.5 hours max | Last Friday, after the Review |
| Backlog refinement | Within the sprint, no fixed slot | As the PO needs, before the next Sprint Planning |

### Who attends and what each event produces

Roles follow `docs/radio.md`. The Owner is the only approver; agents prepare and propose.

| Event | Attends | Produces |
| --- | --- | --- |
| Sprint Planning | Owner (A), PO, Dev Lead, PM/SM (D); QA (I) | `reports/sprints/sprint-<n>-planning.md`: answers to Scrum's three questions (why valuable, what can be done, how), the Sprint Goal, the stories taken in backlog order, the proposed check-session dates. Story plans and G4 follow per story (`docs/plans/<story>.plan.md`, `docs/gates/G4.md`) |
| Daily summary | PM/SM writes; the Owner reads | `reports/daily/<YYYY-MM-DD>.md` (done, in progress, blocked and on whom, waiting for the Owner), from git history and `reports/` |
| Sprint Review | Owner (A), PM/SM, PO (D), Dev Lead, QA (R) | Demo notes `reports/sprints/sprint-<n>-review.md` (each merged story against its acceptance criteria and the Definition of Done, risk register review, re-planned dates) and the gate file `docs/gates/G6-sprint-<n>.md`, one row per story (PP-2) |
| Retrospective | Owner (A), PM/SM (D), Dev Lead, QA (R) | `reports/sprints/sprint-<n>-retro.md`: the metrics of workflow section 11 for the sprint, recurring failures, and one concrete proposed change for each (to `CLAUDE.md`, `AGENTS.md`, an agent file, a hook or an eval). Each change the Owner accepts becomes its own `PROC` task and branch |

The PM/SM prepares every file before the event starts, and tells the Owner when the G6 file is ready. The Owner ticks `Owner approval` in it; the PM/SM never does.

### Daily summary

- Written by the PM/SM at the start of the first agent session of each working day during a sprint, covering everything since the previous summary. No file on a day with no activity.
- The format is the one in `.claude/agents/pm-scrum-master.md`. The PM/SM also updates the dashboard (`docs/process/visuals/sdlc-path-dashboard.html`) at the same time.
- Daily summaries are not committed one by one. They are committed together with the sprint's review and retro files at the Sprint Review, after the Owner reviews the diff (KO-20).

### Re-planning

The schedule is re-planned:

- at every Sprint Review, from the measured number of stories merged per sprint (R-10); the new dates go into `docs/project-plan.md` and this calendar, with the Owner's approval at G6;
- after an approved Change Request that changes the baseline, together with the new `baseline-<n>` tag (`docs/project-plan.md` section 5);
- when the Owner moves a date, for example Sprint 4 at the year end.

A re-plan moves dates only. Releases keep their order and the backlog order stays the PO's proposal.

### Next step

Step 9: freeze the baseline (`docs/project-plan.md`, `docs/backlog.md`, `docs/release-plan.md`, `docs/radio.md`, this file, `CLAUDE.md` v1, `AGENTS.md` v1), tag `baseline-1` on `develop`, and prepare `docs/gates/G3.md` for the Owner's approval. Sprint 1 starts only after G3 is approved.

## Decisions

Routine choices made by the Dev Lead under workflow section 8, "Decision tiers". The Owner can override any of them at G3.

| ID | Decision | Why | Owner |
| --- | --- | --- | --- |
| KO-1 | Coding conventions live only in `AGENTS.md`; `CLAUDE.md` and this file point there | Codex reads only `AGENTS.md`; one source cannot drift | Dev Lead |
| KO-2 | `develop` is the only long-lived branch; no `main` branch; releases and baselines are tags on `develop` | Workflow section 9 puts the release tag on `develop`; there is one environment and no promotion path | Dev Lead |
| KO-3 | Every work branch uses `feature/<ID>_<summary>`, with ID prefixes `US`, `PROC`, `DES`, `FIX`, `CR` | `Protect tests` and the `/story` preflight look for `feature/`; the existing PROC and DES branches already use this form | Dev Lead |
| KO-4 | Pull requests are merged with a merge commit only | Keeps one commit per task and each `Approved-by` line; matches the history and `gh pr merge --merge` in the skill | Dev Lead |
| KO-5 | Tags: annotated `baseline-<n>` at G3 and per baseline-changing CR, `v1.0.0` at G7; created by the PM/SM after Owner approval; never moved | One release of intent-001; tags are the audit points of the baseline and the release | Dev Lead |
| KO-6 | Branch protection on `develop` as listed above, with no required GitHub review count | CICD-AC02 needs required checks; a required review would block every merge in a one-account repository | Dev Lead (applied by the Owner) |
| KO-7 | After a merge, delete the local branch and worktree; keep the remote branch unless the Owner decides otherwise; story runs follow the skill | The Owner asked to keep remote branches; the skill's own clean-up is already Owner-approved | Dev Lead |
| KO-8 | Worktrees `../wt-<story>-dev<k>` for Devs and `../wt-<ID>` for other agent work | The `protect-tests.py` hook protects only `wt-` worktrees | Dev Lead |
| KO-9 | Test layout `tests/api/`, `tests/infra/`, `tests/web/`, `tests/dev01/`; test names start with the criterion ID; `make check` runs `tests/api/` and `tests/infra/`, not `tests/dev01/` | Settles the `testpaths` the US01 plan needs (PROC03 open point) and keeps AWS-dependent checks out of the local check. QA can propose changes in the US01 plan review | Dev Lead, QA reviews |
| KO-10 | Python dependencies pinned exactly (`==`) in `src/api/pyproject.toml` (runtime, and the `dev` extra); no extra lock tool | Reproducible enough for a portfolio project without adding a tool to the toolchain; transitive dependencies stay unpinned, an accepted risk | Dev Lead |
| KO-11 | Dockerfile at `src/api/Dockerfile`, final base `python:3.13-slim` by tag, not digest; user `10001:10001`; one image for the app, migration and recovery tasks | A tag picks up base-image fixes on rebuild, which suits the "fail on fixable HIGH or CRITICAL" scan (Q-O39); a numeric UID lets CNT-AC02 be checked; one image keeps migration and app in step (CICD-AC08) | Dev Lead |
| KO-12 | Alembic directory `src/api/migrations/`, file names `YYYYMMDD_<rev>_<slug>.py`, one migration per `[DB]` task, fixed constraint naming convention | Files sort by date and review shows one migration per change; stable autogenerate output | Dev Lead |
| KO-13 | Tables singular `snake_case` from BD-5; UUIDs generated by the application; `timestamptz` in UTC; `String` plus `CHECK` instead of PostgreSQL `ENUM` | Names match the ER diagram one to one; adding a value to a `CHECK` is a simple migration, an `ENUM` change is not | Dev Lead |
| KO-14 | Web: ESLint (`typescript-eslint` strict) and Prettier in `npm run lint`; `react-i18next` with `en.json` and `vi.json`; keys `<area>.<element>`, API error codes as `errors.<CODE>` | One formatter as on the API side; a standard library for the two catalogues of D-DL8; codes map to text without a lookup table | Dev Lead |
| KO-15 | GitHub Actions: `actions/*` pinned to a major tag, every other action to a full commit SHA; `timeout-minutes` on every job; per-layer `concurrency` for apply, destroy and deploy | Third-party actions run with the CI role's OIDC token; SHA pinning is common practice for that. Concurrency stops two runs changing one layer | Dev Lead |
| KO-16 | `REVIEW.md` (review criteria named by the workflow and the Dev Lead role) does not exist; the Dev Lead writes it before the first review, as its own Owner-approved task next to the US01 plan | The code lens needs written criteria; writing it was not in this step's approved file list | Dev Lead |
| KO-17 | Left to US01: the `Makefile` targets `bootstrap` and `check`, `.terraform-version` = `1.16.4` (IAC-AC01, version confirmed when pinned), `.tflint.hcl` rules. Left to US05: CI parity of `api_test.yml` and `web_build.yml` with `make check` | These files were outside this step's approved file list. `docs/project-plan.md` lists the `.terraform-version` pin under the kick-off milestone: the PM/SM can add it to this branch with the Owner's approval, or leave it to US01 | Dev Lead, PM/SM |
| KO-18 | Timeboxes for a two-week sprint are half of the Scrum one-month maximums: Planning 4 h, Review 2 h, Retrospective 1.5 h; the Daily stays 15 minutes | The Scrum Guide scales shorter events for shorter sprints; workflow section 6.1 leaves the values to the project | PM/SM |
| KO-19 | Sprint event records go in `reports/sprints/sprint-<n>-planning.md`, `-review.md` and `-retro.md`; G6 in `docs/gates/G6-sprint-<n>.md` | One place per sprint, inside the folders the PM/SM writes to; matches PP-2 | PM/SM |
| KO-20 | Daily summaries are written in `reports/daily/` on each working day with activity, and committed in one batch at the Sprint Review | Global rule 3 needs an Owner review per commit; one review per sprint costs the Owner less than one per day | PM/SM |
| KO-21 | Sprint 4 Review and Retrospective stay on Fri 2027-01-01 as the plan says. If the Owner is not available that day, they move to Mon 2027-01-04, before Sprint 5 Planning, and Sprint 5 keeps its dates | 2027-01-01 is New Year's Day; the fallback keeps the calendar without a re-plan. The Owner can pick another date at G3 | PM/SM |
| KO-22 | The `.terraform-version` pin stays in US01 (KO-17), where IAC-AC01 owns it and QA's test comes first. The kick-off milestone text in `docs/project-plan.md` is corrected at Step 9, with the Owner's approval of that edit | Pinning it here would put a US01 deliverable ahead of its plan (G4) and its test | PM/SM |
| KO-23 | Branch protection on `develop` is applied by the Owner in two steps: now, pull request required and force push and deletion blocked, with the Owner keeping force push as a bypass; when US05 merges, the CICD-AC01 checks and `Protect tests` become required checks. No required review count | Owner's answer to KO-OQ1 (2026-11-01): the Owner keeps force-push permission | Owner |
| KO-24 | Workflow section 4, Step 2 corrected: merging to `develop` does not deploy; CD to DEV is run by hand by the Owner, only when needed | Owner's answer to KO-OQ2 (2026-11-01) | Owner |

## Open questions

Only items the Owner must decide or do. Each has a recommended answer.

| ID | Question | Recommended answer |
| --- | --- | --- |
| - | None. KO-OQ1 and KO-OQ2 were answered by the Owner on 2026-11-01 (KO-23, KO-24). | - |
