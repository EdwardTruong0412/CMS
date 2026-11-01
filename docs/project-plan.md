# Project plan: CMS

| | |
| --- | --- |
| Step | Workflow Step 7 (`docs/process/ai-native-sdlc-workflow.md` sections 4, 6, 7 and 8) |
| Author | PM/SM, 2026-11-01 |
| Status | Proposal for the Owner, input to G3. Frozen as part of the baseline at Step 9 (tag `baseline-1`). |
| Scope | intent-001 as approved at G1 and G2: `docs/specs/spec-001.md` (183 criteria), `docs/backlog.md` (US01 to US41) and `docs/release-plan.md` (Releases 1 to 3) |

## 1. Schedule

Two-week sprints (workflow section 6). Sprint Review and Retrospective are on the last Friday of each sprint. The dates below are a proposal; they are re-planned at each Sprint Review from the measured number of stories merged per sprint.

| Milestone | Proposed date | Content | Gate |
| --- | --- | --- | --- |
| Kick-off (Step 8) | week of 2026-11-02 | Conventions, branching, review schedule, `.terraform-version` pinned | |
| Baseline (Step 9) | by 2026-11-06 | Tag `baseline-1` | G3 |
| Sprint 1 | 2026-11-09 to 2026-11-20 | Release 1: US01 to US09 (walking skeleton, budget, teardown, local run, PR checks, CD, secrets, setup, login) | G4 to G6 per story |
| Sprint 2 | 2026-11-23 to 2026-12-04 | Release 1: US10 to US18, then the Release 1 exit session | G4 to G6 per story |
| Sprint 3 | 2026-12-07 to 2026-12-18 | Release 2: US19 to US26 | G4 to G6 per story |
| Sprint 4 | 2026-12-21 to 2027-01-01 | Release 2: US27 to US33, then the Release 2 exit sessions | G4 to G6 per story |
| Sprint 5 | 2027-01-04 to 2027-01-15 | Release 3: US34 to US41, full verification session, rebuild, final teardown | G7 |

Assumption: about 8 to 9 stories per sprint, through `/story` runs with up to 2 Devs in parallel (workflow section 6.4). Sprint 1 measures the real pace. Sprint 4 spans the year end, and the Owner may move it.

Sprint Goals are set at each Sprint Planning (PO, Dev Lead, PM/SM) from the order in `docs/backlog.md`.

## 2. Gates

| Gate | When | File |
| --- | --- | --- |
| G3 Baseline | After Steps 6 to 9 | `docs/gates/G3.md` |
| G4 Plan | Per story, before any test or code | `docs/gates/G4.md` (one section per story) |
| G5 PR | Per story; the approver decides in a story run unless it escalates | `reports/stories/<story>/decision.md` |
| G6 Sprint Review | Per merged story, at the Sprint Review | `docs/gates/G6-sprint-<n>.md` |
| G7 Release | After the Release 3 verification session | `docs/gates/G7.md` |

## 3. Definition of Done (per story, checked at G6)

1. Every criterion the story owns in `docs/backlog.md` has a passing acceptance test written by QA before the code. The test traces to the criterion ID.
2. `make check` passes, and the pull-request checks in CI pass (CICD group).
3. The code lens and every relevant review lens pass, and the approver says APPROVE, or the Owner approves on escalation.
4. The story is merged into `develop`, and `tests/` was changed only by QA's commits.
5. If the story changes dev01, its checks passed in a dev01 check session (release plan RP-D1), and env and group were destroyed at the end of that session.
6. Docs touched by the story are updated: module README, runbook and `CLAUDE.md` where relevant.

## 4. Check sessions on dev01

Rules from Q-O57, OQ-1, OQ-2 and RP-D1:

- Only singleton exists between sessions. A session runs on a weekday during office hours. It builds group, then env, does one CD run, creates the first admin, loads `testdata/mock/`, runs QA's dev01 checks, then destroys env and group.
- About one session per 3 to 5 merged stories that change dev01, plus one exit session per release.
- The PM/SM writes the session runbook before each session and records the session cost after it, from Cost Explorer the next day.
- The AWS Budget alert is $2 per month. It is expected to fire in most months of active work, and the Owner accepted this (OQ-2).

## 5. Change Request process

Applies to any request outside the baseline (`baseline-1`), following workflow section 7:

1. Agents do not start work outside the baseline. The PM/SM records the request in `docs/change-requests/CR-<nnn>.md` from `docs/change-requests/CR-template.md`.
2. The PM/SM and the Dev Lead draft the impact analysis: affected stories and criteria, schedule, cost and risks.
3. The Owner approves or rejects in the CR file.
4. If approved: the PO writes a new intent (and a PRD if the criteria in `.claude/agents/product-owner.md` apply) and adds the stories to the backlog. The PM/SM updates this plan and tags a new baseline (`baseline-<n>`).

Not a CR: a routine decision under workflow section 8, "Decision tiers". The deciding agent logs it, and the Owner can override it at the next gate.

## 6. Risk register

Probability (P) and impact (I) are rated H, M or L. The PM/SM reviews this register at every Sprint Review.

| ID | Risk | P | I | Response | Owner of the response |
| --- | --- | --- | --- | --- | --- |
| R-01 | Cost above expectations: a session left running, a forgotten destroy, or resources that bill after deletion | M | M | Destroy workflows in US03 are proven early. A session checklist ends with destroying env and group. The $2 alert is an early signal, and costs are recorded per session. | PM/SM, Owner |
| R-02 | AWS behaviour assumed at Basic Design turns out wrong: ALB logs with SSE-S3 only, the WAF rate-limit minimum, stopping a Multi-AZ RDS, Budgets with an SNS topic that does not exist yet, Terraform write-only arguments, cross-region EventBridge | M | M | Each item is marked "verify at plan time". The Dev Lead confirms it against AWS documentation in the story plan before G4. A wrong assumption becomes a logged decision or a CR. | Dev Lead |
| R-03 | The Owner is the only approver, so gates and CD runs wait for the Owner | H | M | Routine decisions are made by agents (decision tiers). Story runs let the approver decide G5. Sessions are batched (RP-D1). Questions are filtered before they reach the Owner. | PM/SM |
| R-04 | Codex CLI is unavailable or rate-limited during a story run | M | M | One story per Dev. Runs are resumable (`codex exec resume`). The `/story` skill stops cleanly and reports. | PM/SM |
| R-05 | The first CD run of a session finds no env, so the pre-flight of CICD-AC14 would stop it | H | L | The US06 and US33 plans define the session order (env apply first, then CD) so both criteria hold (backlog open point 1). | Dev Lead |
| R-06 | DNS delegation of `cms.imaprof.ink` breaks at rebuild: the new hosted zone gets new name servers | M | M | The US39 runbook updates the NS records at Namecheap and waits for propagation before validating certificates (RP-D3). | Owner, Dev Lead |
| R-07 | KMS keys or secrets pending deletion clash with names on a quick rebuild | M | L | Handled by the Q-D12 naming decision, and checked in the US39 rehearsal. | Dev Lead |
| R-08 | A real personal data value or secret enters a prompt, fixture or log | L | H | Only `testdata/mock/` is used. Agents never read `.env` or secrets. SEC-AC13 log checks. The security lens runs in every story run. | QA, security lens |
| R-09 | An agent or Dev changes tests to make them pass | L | H | The `protect-tests` CI check, and the code lens confirms that only QA's commits touch `tests/`. | Dev Lead, QA |
| R-10 | The pace of story runs is lower than the schedule assumes | M | M | Re-plan at each Sprint Review. Releases keep their order, so a late release only moves dates. | PM/SM |
| R-11 | The Owner's local staged changes diverge from `develop`, for example the `/story next` work in the main checkout | M | L | Agents work in separate worktrees and never touch the Owner's index. The PM/SM reminds the Owner before kick-off. | PM/SM |

## 7. Mock data

- `testdata/mock/` holds 6 departments, 8 positions and 50 employees. The file `testdata/mock/README.md` lists the rules the data follows and the test points it guarantees.
- No user accounts or passwords are committed; tests create them at run time.
- After every change to the folder, run `python3 -I testdata/mock/check_mock.py testdata/mock`. It checks the format rules (EMP-AC03), the case-insensitive uniqueness of codes and emails, the eight fields, and the search and ORG test points. It is not part of `make check` yet; QA may turn it into a test in US17.

## 8. Communication

- **Dashboard:** `docs/process/visuals/sdlc-path-dashboard.html` (local, not tracked) shows where the project is and what waits on the Owner. The PM/SM updates it after every completed task. The story board (`factory/dashboard.html`) shows story runs.
- **Hand-offs:** only through files, in `reports/handoff/` and `docs/` (global rule 6).
- **Gates:** each gate file has an evidence table, a checklist and `Owner approval: [ ]`.
- **Questions to the Owner:** only Owner-tier items, each with a recommended answer (workflow section 8).

## 9. Decisions log

| ID | Decision | Reason | Decided by |
| --- | --- | --- | --- |
| PP-1 | Sprint dates and the split of releases into sprints above (5 sprints, about 8 to 9 stories each) | A starting estimate to measure in Sprint 1; the Owner can move any date | PM/SM |
| PP-2 | G6 is recorded per sprint in `docs/gates/G6-sprint-<n>.md`, one row per story | Keeps one review file per Sprint Review | PM/SM |
| PP-3 | The mock data has 6 departments and 8 positions, and its names and emails are chosen so that the search test points of EMP-AC17 and EMP-AC20 return only the intended employee | Makes the spec's test points deterministic against the loaded data | PM/SM |
| PP-4 | No mock user accounts or passwords in `testdata/mock/` | No credential-like values in the repository; tests create accounts through the API | PM/SM |
