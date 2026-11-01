# Handoff: 2026-11-01 PROC06 - PM/Scrum Master summary (Step 8 kick-off: ceremonies and schedule)

Branch `feature/PROC06_kickoff`, main checkout, on top of the Dev Lead's uncommitted changes. Nothing committed, nothing pushed. No other agent started. No Terraform, AWS or GitHub commands run.

## What was done

- Wrote the `## Ceremonies and Sprint Review schedule` section of `docs/kickoff.md`: sprint length, the calendar of Sprints 1 to 5 (Planning, Review/G6 and Retrospective dates, exit and verification sessions), timeboxes, attendees and outputs per event, the daily summary, when the schedule is re-planned, and the "Next step" line (Step 9, freeze the baseline, tag `baseline-1`, gate G3).
- Added decisions KO-18 to KO-22 to the Decisions table and Owner question KO-OQ2 to the Open questions table.
- Checked every date against `docs/project-plan.md` section 1: all sprints start on a Monday and end on a Friday, and the calendar matches the plan. `docs/project-plan.md` was not changed.

## Files changed

| File | Change |
| --- | --- |
| `docs/kickoff.md` | Ceremonies section written; KO-18 to KO-22; KO-OQ2 |
| `reports/handoff/PROC06-pm-scrum-master-summary.md` | This file |

## Decisions (routine, PM/SM tier; full text in `docs/kickoff.md`)

- KO-18: timeboxes for a two-week sprint are half the Scrum one-month maximums (Planning 4 h, Review 2 h, Retrospective 1.5 h, Daily 15 min).
- KO-19: sprint records in `reports/sprints/sprint-<n>-{planning,review,retro}.md`; G6 in `docs/gates/G6-sprint-<n>.md` (PP-2).
- KO-20: daily summaries in `reports/daily/<YYYY-MM-DD>.md` on working days with activity, committed in one batch at the Sprint Review (one Owner diff review per sprint, not per day).
- KO-21: Sprint 4 Review and Retro stay on Fri 2027-01-01 (New Year's Day); fallback Mon 2027-01-04 before Sprint 5 Planning, with no re-plan needed.
- KO-22: the `.terraform-version` pin stays in US01; the kick-off milestone line in `docs/project-plan.md` is corrected at Step 9 with the Owner's approval of that edit.

## Open questions for the Owner

- **KO-OQ1** (from the Dev Lead, passes the filter: an Owner-only GitHub setting). Recommended: apply branch protection on `develop` in two steps, as KO-6 describes.
- **KO-OQ2** (passes the filter: contradicts an earlier Owner decision). Workflow section 4, Step 2 still says "automatic deploy to DEV when merged to `develop`". Recommended: a one-line correction on this branch before Step 9.

## The Dev Lead's three notes for the PM/SM

| Note | View | Recommendation |
| --- | --- | --- |
| `.terraform-version` pin listed under the kick-off milestone in `docs/project-plan.md` | IAC-AC01 belongs to US01, and the version is confirmed when it is pinned. Pinning now would deliver part of US01 before its plan (G4) and before QA's test, against test-first. | Leave it to US01 (KO-22). At Step 9, correct the milestone line in `docs/project-plan.md` ("`.terraform-version` pinned" moves to US01) as part of the baseline freeze, with the Owner's approval of that edit. Routine; no Owner question. |
| QA review of KO-9 (test layout and naming) | A layout choice, Dev Lead tier, that QA owns in practice. KO-9 already says QA can propose changes. A convention change after `baseline-1` is a logged routine decision, not a CR (`docs/project-plan.md` section 5). | No separate task now. QA reviews KO-9 as part of the US01 plan review before G4; any change goes into `AGENTS.md` and is logged as a new KO decision. The PM/SM puts this in QA's brief for US01. No Owner question. |
| Workflow Step 2 still says auto-deploy on merge to `develop` | Contradicts the Owner's manual-CD decision (workflow section 9, `CLAUDE.md`). If left, `baseline-1` freezes a stale rule. The workflow file was outside this step's approved file list, so it needs the Owner's approval. | Fix it on this branch before Step 9 with a one-line edit (KO-OQ2). Needs the Owner's yes. |

## Next step

After the Owner approves this kick-off (and answers KO-OQ1 and KO-OQ2), the PM/SM shows the staged diff of `feature/PROC06_kickoff` and the commit message for review, then opens the PR. Then Step 9: freeze the baseline, tag `baseline-1`, prepare `docs/gates/G3.md`.
