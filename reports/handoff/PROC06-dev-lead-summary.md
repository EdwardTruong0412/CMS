# Handoff: 2026-11-01 PROC06 - Dev Lead summary (Step 8 kick-off: conventions and branching)

Branch `feature/PROC06_kickoff`, main checkout. Nothing committed, nothing pushed. No Terraform, AWS or GitHub commands run.

## What was done

- Wrote `docs/kickoff.md`, the Step 8 artifact: purpose and inputs, a map of the coding conventions (pointing to `AGENTS.md` as the single source), the Git branching rules, the Definition of Done reference, the empty ceremonies section for the PM/SM, decisions KO-1 to KO-17 and one Owner question.
- Filled the convention gaps in `AGENTS.md` and brought `CLAUDE.md` and `AGENTS.md` to v1, keeping the Owner's recent `CLAUDE.md` edits (group lean/full tfvars, region, mypy, office hours).
- Changed global rule 4 in `.claude/rules/global.md` and the same rule in `AGENTS.md` together.

## Files changed

| File | Change |
| --- | --- |
| `docs/kickoff.md` | New. Step 8 artifact as described above. `## Ceremonies and Sprint Review schedule` holds only "To be written by the PM/SM." |
| `AGENTS.md` | Check command: pytest runs `tests/api/` and `tests/infra/`. Conventions: worktree name, `develop` changes only through a PR, pointer to the kick-off branching rules, `test` type reserved for QA, KO-n reference. Coding convention: Python dependency pinning and naming; new sections "Database and Alembic migrations", "Dockerfile and local stack" and "Tests"; web lint and format, layout and translation keys; Terraform root file layout, resource naming and ASCII/hyphen names; GitHub Actions file names, timeouts, concurrency, action pinning, Terraform version source. Rules for all agents: rule 4 names the work item ID forms. |
| `CLAUDE.md` | Required Tools: the `Makefile` is empty, targets come with US01. Directory tree: `tests/`, `docs/specs/`, `docs/plans/`. Conventions pointer covers all areas and `docs/kickoff.md`. Code Quality: `api_test.yml` and `web_build.yml` described as the CI side of `make check`; `protect_tests.yml` listed (it existed but was missing). Design Documentation: where the Basic Design and plans are. Main Branch and PRs: no `main`, tags, ID prefixes, merge commit only, no direct or force push, worktree names, branch clean-up, pointer to kick-off. Nothing else changed. |
| `.claude/rules/global.md` | Rule 4: process, design and fix work uses the same branch form with its own ID; pointer to `docs/kickoff.md`. |
| `reports/handoff/PROC06-dev-lead-summary.md` | This file. |

## Decisions (routine, Dev Lead tier; full table in `docs/kickoff.md`)

- KO-1 conventions only in `AGENTS.md`. KO-2 `develop` is the only long-lived branch, no `main`. KO-3 every branch is `feature/<ID>_<summary>` with `US`, `PROC`, `DES`, `FIX`, `CR` IDs. KO-4 merge commits only. KO-5 tags `baseline-<n>` and `v1.0.0` at G7, created by the PM/SM after Owner approval, never moved. KO-6 branch protection expectation (no required GitHub review count). KO-7 local branch deleted after merge, remote kept unless the Owner decides; story runs follow the skill. KO-8 worktree names.
- KO-9 test layout `tests/api|infra|web|dev01`, names start with the criterion ID. KO-10 exact pins in `pyproject.toml`. KO-11 Dockerfile conventions (tag not digest, UID 10001, one image for app, migration and recovery). KO-12 Alembic file naming and constraint naming. KO-13 table and column conventions. KO-14 ESLint plus Prettier, `react-i18next`, key format. KO-15 Actions pinning, timeouts, concurrency.
- KO-16 `REVIEW.md` is missing: the Dev Lead writes it before the first review as its own approved task. KO-17 left to US01: `Makefile` targets, `.terraform-version` = 1.16.4, `.tflint.hcl`; left to US05: CI parity.

## Open questions

- **KO-OQ1 (Owner).** Branch protection on `develop` is a GitHub setting only the Owner can change. Recommended: now, require a pull request and block force push and deletion, also for administrators; after US05 merges, add the CICD-AC01 checks and `Protect tests` as required checks; no required review count.

## Notes for the PM/SM

- `docs/project-plan.md` lists "`.terraform-version` pinned" under the kick-off milestone. It was not in this step's approved file list, so it is not done (KO-17). Either add it to this branch with the Owner's approval, or leave it to US01.
- QA may want to review KO-9 (test layout and naming) before the US01 plan; it affects `testpaths` in `src/api/pyproject.toml`.
- Workflow section 4, Step 2 still says "automatic deploy to DEV when merged to `develop`", which v3.1 superseded (CD is manual). Not changed: the workflow file was outside this task.
