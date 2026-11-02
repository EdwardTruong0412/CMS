# Sprint 1 Planning

| | |
| --- | --- |
| Sprint | 1, Mon 2026-11-09 to Fri 2026-11-20 (Review G6 and Retrospective Fri 2026-11-20) |
| Held | 2026-11-01, ahead of the calendar date, at the Owner's request ("start phase B"). Sprint dates unchanged |
| Attendees | Owner (A); PO, Dev Lead, PM/SM (D); QA (I) (`docs/kickoff.md`, "Ceremonies") |
| Scope | US01 to US09 of Release 1, Baseline 1 (`baseline-1`), in backlog order |
| Inputs | `reports/handoff/PROC08-product-owner-summary.md`, `reports/handoff/PROC08-dev-lead-summary.md`, QA's read of both (section 6) |
| Status | Decided 2026-11-02 (Owner delegated the open questions, section 10). Story plans and G4 follow per story |

## 1. Why is this sprint valuable

From the PO (summary section 2):

- It turns intent-001 into a running system: the main path of the Owner's architecture (Route 53, ACM, CloudFront, S3, ALB, ECS Fargate, RDS, ECR, Secrets Manager, KMS, GitHub Actions with OIDC) exists end to end.
- It delivers 66 of the 102 criteria of the Release 1 exit check, including the personal-data rules that must hold before any employee data exists (encryption, access only after login, secrets outside state, logs and image, no default admin).
- It puts the $2 cost rule (Q-O57) in force from the first session: budget, alert email and the destroy workflows come straight after the skeleton.
- It retires the highest risks early: DNS delegation and certificates, OIDC, the first CD run of a session (R-05), secrets outside Terraform state (Q-D13).
- It measures the real pace, which re-plans Sprints 2 to 5 at the Review (PP-1, R-10).

## 2. Sprint Goal

The PO and the Dev Lead proposed two wordings. The Dev Lead's forecast (section 4) shows US06 and US09 will probably carry into Sprint 2, so the PO's wording (CD run and login by 2026-11-20) would likely be missed. The PM/SM recommends a goal the sprint can meet, with the stretch named:

> **dev01 is built from the repository and serves the walking skeleton over HTTPS, with cost alerts reaching the Owner, pull-request checks guarding `develop`, and every check session ending with env and group destroyed.** Stretch: one CD run deploys `develop` and the first admin logs in.

## 3. What can be done: stories in backlog order

Criteria counts are the IDs on each story's "Delivers" line. Sizes follow BL-D4 (S about 1 day, M 1 to 2, L 2 to 3).

| Story | Title | Size | Criteria | Done means at the Sprint Review |
| --- | --- | --- | --- | --- |
| US01 | Walking skeleton on dev01 | L, over 3 days: split proposed (OQ-S1-1) | 23 | The Owner bootstraps state and applies singleton, group and env (lean); the app hostname serves the UI over HTTPS, `/healthz` answers from a non-root container, the API reaches the database, and a second plan on each layer shows no changes |
| US02 | Budget and alert email reach the Owner | S | 2 | $2 budget with 80% and 100% notifications to the alert topic; the Owner's subscription confirmed |
| US03 | Owner ends a session by destroying env and group | S | 1 | Manual-only destroy, force-unlock and workspace workflows |
| US04 | Developer runs the whole stack locally | S | 1 | `docker compose up` runs API, PostgreSQL and UI with mock data only |
| US05 | Pull-request checks guard develop | M | 8 | PR checks through OIDC with no change in AWS; a failing check blocks the merge |
| US06 | Owner deploys develop to dev01 with one CD run | L | 9 | One manual CD run deploys the commit and passes the smoke test within 30 minutes |
| US07 | Secrets and stored data protected with project keys | M | 7 | Secrets generated outside state, customer managed keys, least-privilege access, 7-day backups |
| US08 | First admin setup | M | 8 | One-time setup screen creates the first admin, then never appears again |
| US09 | Log in and log out | M | 7 | Login and logout with the session cookie; data only after login |

Total: 66 criteria.

### US01 split (OQ-S1-1)

The PO and the Dev Lead both find US01 over 3 days (Dev Lead estimate: 6 to 8 Dev days). They propose different cuts, each keeping all 23 criteria in exactly one part:

| | PO proposal (2 parts) | Dev Lead proposal (3 parts) |
| --- | --- | --- |
| Parts | US01a UI over HTTPS on the app hostname (9 criteria, M); US01b API answers from the database (14, L) | US01a repo tooling and app skeleton (CNT-AC01, CNT-AC02; M); US01b state bucket, singleton and group (7; M); US01c env layer serves the app over HTTPS (14; L at the limit) |
| Parallel work | Little: both parts need all three layers | Dev 2 starts on US01a while Dev 1 starts on US01b; US04, US03 and US02 can follow on Dev 2 |
| Test-first (QA) | Harder: US01a mixes static checks with dev01-only checks, and its enablers trace to no criterion | Easier: each part maps to one test layer (US01a `make check` only; US01b singleton and group; US01c dev01) |

**PM/SM recommendation:** the Dev Lead's 3-part split, recorded by the PO as refinement that `baseline-1` already provides for (US01 notes: "the Product Owner splits it at refinement"), with no CR and no new tag. The PO and the Dev Lead agree it needs no CR. The PO then edits `docs/backlog.md` (story lines, Delivers, Depends on, a BL-D row, coverage recounted at 183 of 183) on its own branch, for the Owner's review.

## 4. How the work gets done

Detail per story: Dev Lead summary section 1. The detailed design is in each `docs/plans/<story>.plan.md` at G4.

### Lanes (SP1-D1), assuming the 3-part split

| Lane | Dev | Stories, in order | Target merge |
| --- | --- | --- | --- |
| Terraform and pipeline | Dev 1 | US01b, US01c, US05, US06 | US01b Fri 13, US01c Tue 17, US05 Thu 19, US06 about Tue 24 Nov (carried) |
| App and small infrastructure | Dev 2 | US01a, US04, US03, US02, US08, US07, US09 | US01a Wed 11, US04 Thu 12, US03 Fri 13, US02 Mon 16, US08 Wed 18 (G5 held until Session 1 ends, SP1-D13), US07 Fri 20, US09 about Tue 24 Nov (carried) |

- Parallel pairs: US01b with US04 and US03; US01c with US02, then US08; US05 with US07 (US05 merged first); US06 with US09.
- Never in parallel: US05 with any story that adds Terraform; US02 with US05 (both edit singleton `main.tf`; US02 first); US06 with US07 (both edit `app_service`).
- Critical path: US01a, US01b, US01c, US05, US06, about 10 to 10.5 Dev days against 9 working days after Planning.

### Forecast

- Merged by Fri 20 Nov: US01a to US01c, US02 to US05, US08, probably US07.
- Carried into Sprint 2, in progress: US06, US09 (PO S1-PO-D6: US09 slips first in backlog order).
- Done at G6 in Sprint 1 (needs Session 1 for stories that change dev01): US01, US02, US03, US04, US05.

### Plans and G4, just in time (SP1-D11)

| Sprint day | Plans for G4 |
| --- | --- |
| D1 Mon 9 Nov | US01a, US01b |
| D2 to D3 | US04, US03, US01c, US02 |
| D5 to D6 | US08, US05 |
| D7 | US07, US06 |
| D8 | US09 |

### Notes for Sprint Planning (backlog points 1 to 3), direction only

1. First CD run of a session (R-05): each session applies group then env first; the CD run starts only when RDS is available and ECS has one task. Settled in the US06 plan, kept by US33.
2. UI publish and smoke test: UI synced and invalidated after the ECS rollout and before the smoke test; BD-2 is corrected on the US06 plan branch for the Owner to see at G4. No criterion changes.
3. Per-session setup and mock data: `docs/runbooks/session.md` (started by US01c) gets sections for start, deploy, first admin (US08) and mock data (US17).

## 5. Check sessions on dev01 (lean profile)

| Session | Proposed date | Stories verified |
| --- | --- | --- |
| Session 1 | Wed 2026-11-18, about 09:30 to 15:00 ICT; fallback Thu 19 Nov | US01 (all parts), US02. Destroy env then group from a local shell (the US03 workflows lack a role until US05 and US06). Estimated $0.50 to $0.60 |
| Outside a session | Thu 19 or Fri 20 Nov, no extra cost | US05 (its AWS checks need only singleton) |
| Session 2 | Wed 2026-11-25, Sprint 2 (confirmed at Sprint 2 Planning) | US06 to US09, and the US03 workflows in use |

Owner actions during the sprint (not questions): after the US01b merge, bootstrap the state bucket, apply singleton locally and add the NS records at Namecheap; before Session 1, re-apply singleton with US02 and create the git-ignored alert-email tfvars file; during the US05 run, apply singleton from the US05 branch and set the GitHub variables, secret and `dev01` environment; after the US05 merge, KO-23 step 2.

## 6. QA (informed), quoted from QA's read

- The Dev Lead's 3-part split is easier to test first: each part maps to one test layer and can be proven on its own.
- Session 1 is the only time US01b, US01c and US02 can be proven on dev01; a pass at merge covers only the static checks. No-change plans and the lock test run in office hours.
- The US01c plan must choose how the CNT-AC03 negative case stops the API process before QA can write the test.
- `tests/dev01` needs resource names, outputs and hostnames fixed in each plan.
- US07 and US09 cannot be proven on dev01 before Session 2, so they cannot be Done in Sprint 1.
- The injectable clock in US01a needs a fixed injection point; US08 depends on it. The `tests/web` runner (Vitest proposed) is decided before US08.
- Mock data needed in `testdata/mock/`: a fake alert address (`@example.com`) for US02; setup token, password matrix and users for US08 and US09.
- Before US01a's tests: the split decision merged, the branch, the US01a plan at G4 (import paths, `testpaths`, `CMS_` settings, health and status contracts, database for `tests/api`, clock interface), and the Codex sandbox check.

## 7. Prerequisites before the first `/story` run, in order

1. The Owner approves this record and the Sprint Goal.
2. The Owner answers OQ-S1-1; the PO records the split in `docs/backlog.md` on its own branch; merged before `/story next` runs.
3. The Owner turns on branch protection step 1 on `develop` (KO-23).
4. `REVIEW.md` (KO-16), Dev Lead, its own PROC task. In a PM/SM governance task: `.claude/agents/approver.md` and `.claude/agents/reviewer-infra.md` still say "$10 budget" and must say $2 (Q-O57); and the `/story` preflight looks for `<story>-po-summary.md`, so story hand-offs use that name (PM/SM decision SP1-PM-D2).
5. Codex sandbox network check (`make check` needs pip, npm and the tflint plugin). If it fails: OQ-S1-2.
6. US01a plan and its G4 entry in `docs/gates/G4.md` (new file, PM/SM).
7. The Dev Lead creates `feature/US01a_<summary>`; QA writes the tests (`test(US01a): ...`) after the Owner reviews the diff; the three summaries `US01a-po-summary.md`, `US01a-dev-lead-summary.md`, `US01a-qa-summary.md`.
8. The PM/SM gives the Owner one combined summary; the Owner types `/story US01a`.

## 8. Risks for the sprint

| Risk | Response |
| --- | --- |
| R-10 Pace: critical path longer than the sprint | Two lanes, G4 in batches, re-plan at the Review |
| R-03 Owner bottleneck: most Sprint 1 stories escalate at G5 | G4 batches; escalated merges reviewed once a day |
| R-02 AWS assumptions (D-DL13, Q-D13, Q-D12, PostgreSQL 17, D-DL15, SP1-D9) | Verified in each plan |
| R-05 First CD run | Session order in the US06 plan |
| R-06 DNS propagation before Session 1 | NS records added straight after the US01b merge |
| R-04 Codex sandbox may block network for `make check` | Prerequisite 5, OQ-S1-2 |
| New: env PR plans while group is destroyed | SP1-D9 (`terraform_remote_state` with `defaults`) |
| New: Trivy findings before the stories that fix them | SP1-D10 (reviewed ignore file, each entry names its fixing story) |
| New: an image with US08 needs a setup token before US07 | SP1-D13 (US08 G5 held until Session 1 ends) |

## 9. Decisions

Dev Lead SP1-D1 to SP1-D13 and PO S1-PO-D1 to S1-PO-D6 are in their summaries. PM/SM decisions under the decision tiers:

| ID | Decision | Reason |
| --- | --- | --- |
| SP1-PM-D1 | Recommend the Dev Lead's 3-part split over the PO's 2-part split | More parallel work and cleaner test-first, per the Dev Lead and QA; same criteria and order |
| SP1-PM-D2 | Story hand-offs are named `<story>-po-summary.md`, `<story>-dev-lead-summary.md`, `<story>-qa-summary.md`, as the `/story` preflight expects | Avoids a preflight failure; PROC hand-offs keep their current names |
| SP1-PM-D3 | US05's negative PRs (one ruff violation, one unencrypted bucket) are listed in the US05 plan and created by the story-run coordinator on throwaway branches | QA cannot create branches in its write scope (QA open point); the run's approval covers branches named in the plan |
| SP1-PM-D4 | The KO-22 wording ("where IAC-AC01 owns it") is read as SP1-D5 and S1-PO-D4 say: IAC-AC01 stays with US05; the pin file is first created in US01a. The text is corrected in the next approved governance edit | Both frozen statements stay true; no CR needed |

## 10. Open questions for the Owner

1. **OQ-S1-1 US01 split.** Approve the Dev Lead's 3-part split (US01a, US01b, US01c) as refinement without a CR? Recommended: yes. Alternative: the PO's 2-part split, or US01 whole (then about US01 to US05 only this sprint).
2. **Sprint Goal.** Approve the goal in section 2 (with the stretch)? Recommended: yes.
3. **OQ-S1-2 (only if the sandbox check fails).** Allow network access for the Codex Dev command in story runs (`sandbox_workspace_write.network_access=true` in `.claude/skills/story/SKILL.md`)? Recommended: yes; worktrees hold only mock data, and the `protect-tests` hook and CI check stay in force. Alternative: you pre-install dependencies in each worktree before a run.
4. **Session 1 date.** Wed 2026-11-18 (fallback Thu 19)? Recommended: yes.

### Answers (2026-11-02)

The Owner delegated the four questions to the PM/SM ("You can decide what to approach", 2026-11-02). The PM/SM adopted its recommendations:

| Question | Answer |
| --- | --- |
| OQ-S1-1 | Dev Lead's 3-part split (US01a, US01b, US01c), refinement inside `baseline-1`, no CR, no new tag. The PO records it in `docs/backlog.md` as its own task, with the Owner's review of the commit |
| Sprint Goal | As in section 2, with the stretch |
| OQ-S1-2 | Network access for the Codex Dev command if the sandbox check fails, made as its own governance task on `.claude/skills/story/SKILL.md` |
| Session 1 | Wed 2026-11-18, fallback Thu 2026-11-19 |

## Approval

Owner approval: delegated to the PM/SM on 2026-11-02 (answers above). The Owner can override any answer.
