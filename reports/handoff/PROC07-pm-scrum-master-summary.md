# Handoff: 2026-11-01 PROC07 - PM/Scrum Master summary (Step 9 baseline freeze, gate G3)

Branch `feature/PROC07_baseline`, main checkout, from `develop` at `b58f91a`. Nothing committed, nothing pushed, no tag created. No other agent started. No Terraform or AWS commands run; only read-only `gh pr list --state merged` for evidence.

## What was done

- Updated `docs/project-plan.md` for the baseline: status, kick-off milestone, and the lines made stale by Steps 6 to 8 (list below).
- Wrote `docs/gates/G3.md` in the G2 format: evidence per step with PR numbers (#4 to #8, verified as merged), what `baseline-1` freezes, decisions to look at, checklist, no open Owner questions, steps after approval, `Owner approval: [ ]` unticked.
- Verified evidence: backlog coverage recounted (183 criterion IDs on the "Delivers" lines, 183 distinct); `python3 -I testdata/mock/check_mock.py testdata/mock` PASS; `REVIEW.md` absent (KO-16); `.terraform-version` still empty (KO-22, US01).

## Files changed

| File | Change |
| --- | --- |
| `docs/project-plan.md` | Ten edits, listed below |
| `docs/gates/G3.md` | New |
| `reports/handoff/PROC07-pm-scrum-master-summary.md` | This file |

## Edits to `docs/project-plan.md`

1. Author row: "(Step 7); updated for the baseline at Step 9, 2026-11-01" added.
2. Status row: now "Baseline 1 (Step 9), frozen by tag `baseline-1` after G3 approval; changes only through a Change Request (section 5)".
3. Section 1 intro: "The dates below are a proposal" became "the baseline dates", with a pointer to `docs/kickoff.md` "Re-planning".
4. Milestone table header: "Proposed date" became "Date".
5. Kick-off row: marked "Done 2026-11-01 (PR #8, merge `b58f91a`)". Content is now conventions, branching, ceremonies and Sprint Review schedule (`docs/kickoff.md`, `CLAUDE.md` v1, `AGENTS.md` v1). "`.terraform-version` pinned" removed, with a note that US01 delivers it (IAC-AC01, KO-22). The Baseline row is unchanged (by 2026-11-06, tag `baseline-1`, G3).
6. Sprint 4 note: points to the KO-21 fallback date for its Review.
7. Section 5 step 4: a new `baseline-<n>` is tagged only after the Owner approves the tag (KO-5).
8. R-05: "backlog open point 1" became `docs/backlog.md`, "Notes for Sprint Planning", point 1. The backlog has no section called "open points".
9. R-11: removed the stale example (the `/story next` work, merged in PR #7) and "reminds the Owner before kick-off" (kick-off is done). The response is now a `git status` check of the main checkout before each Sprint Planning.
10. Decisions log: added PP-5 (below).

Checked and unchanged: the gate table, the Definition of Done, check-session rules (CD is already manual there), the risk register apart from R-05 and R-11, mock data, communication. No auto-deploy wording remains in the plan.

## Decisions (routine, PM/SM tier)

- **PP-5:** the status lines of `docs/backlog.md`, `docs/release-plan.md`, `docs/radio.md` and `docs/kickoff.md` keep their "Proposal" or "Draft, input to G3" wording. `docs/gates/G3.md` and the tag `baseline-1` record the freeze. This avoids editing four approved, merged documents just to change a status word, and those files were not in this task's approved file list. Changed at the Owner's G3 review: the four status lines are set to "Baseline 1" in the G3 commit.
- The G3 "Decisions you may want to look at" list is limited to seven items: sprint calendar, release split, KO-2/KO-4/KO-5, KO-20, KO-21, KO-23 and KO-16.

## Open questions

None for the Owner. These are carried to Sprint 1 and do not block G3: the Owner applies step 1 of the `develop` branch protection (KO-23), the Dev Lead writes `REVIEW.md` (KO-16), and QA reviews KO-9 in the US01 plan review.

## Notes for the main session

- After G3 is approved and the PR is merged, the annotated tag `baseline-1` goes on the merge commit in `develop`, and is pushed only after the Owner approves the tag push.
- The dashboard (`docs/process/visuals/sdlc-path-dashboard.html`) was not in this task's file list and was not updated. Update it after this task.
