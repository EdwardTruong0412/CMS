# Handoff: 2026-11-01 PROC03 - Dev Lead summary (post-G2 step 7: check command and conventions)

Branch `feature/PROC03_claude_md_after_g2` (from `origin/develop`), worktree `wt-PROC03`. Nothing committed.

## What was done

Applied the "After approval" items of `docs/gates/G2.md` and the Step 5 decisions to `AGENTS.md` and `CLAUDE.md`, and made ap-southeast-1 the stated default region everywhere (Owner instruction for this task).

## Files changed

| File | Change |
| --- | --- |
| `AGENTS.md` | "The check command": `make check` from the repo root, with a table of what it must run (API, web, Terraform) and rules (stop at first failure, no skipped steps, no AWS access). "Conventions": the coding-convention placeholder now points to a new "Coding convention" section with Python (FastAPI, SQLAlchemy 2.x, Alembic), TypeScript/React, Terraform and GitHub Actions rules, each tied to the decision or criterion it comes from. No other line changed. |
| `CLAUDE.md` | Tech Stack: `mypy` added to the API tools. Directory tree: group `tfvars/` holds `lean.tfvars` and `full.tfvars`. Key Architecture Principle 3: a profile is one file in each of group and env (Q-O55). State Management: backend region ap-southeast-1. Local commands: `AWS_REGION=ap-southeast-1` next to `AWS_PROFILE=3tier`; group plan/apply with its tfvars; singleton alone without tfvars; notes on the session destroy, the profile switch order and office-hours no-change plans (Q-D1). Application Commands: `make check`, `ruff format --check`, `mypy`, `npm run typecheck`; pointer to the conventions in `AGENTS.md`; testing notes for controlled-clock timers (D-PM3) and the test schedule (OQ-1). Pipeline flow: CD started by hand by the Owner on `develop` and begins with the pre-flight check (Q-O54, CICD-AC14); OIDC credentials step uses `aws-region: ap-southeast-1`; "merge does not deploy" kept. AWS Provider Configuration: default region for provider, backend, CLI and GitHub Actions; `us_east_1` alias limited to the four resources of IAC-AC09, two of them in `modules/monitoring` (Q-O56). Cost: $2 alert with 80%/100% (Q-O57, OQ-2), env and group exist only for a session, lean/full files for both layers, full only within one weekday's office hours (COST-AC03), clean-up checklist reference now points to TDN-AC02. Everything else unchanged. |
| `reports/handoff/PROC03-dev-lead-summary.md` | This file |

## Choices made (routine, Dev Lead tier)

| Choice | Reason |
| --- | --- |
| One `make check` target, not a shell script | The repo already uses `make bootstrap`; one name for Devs, the `/story` precondition ("`AGENTS.md` has a real check command") and reviewers. |
| Type checker: mypy (strict), not pyright | Pure Python, installed with the other API dev tools from `pyproject.toml`, so the API check needs no Node runtime; SQLAlchemy 2.x typed models and Pydantic v2 work with it without stubs. Pyright is faster but adds a Node dependency to the API toolchain. |
| Web type check as a separate `npm run typecheck` (`tsc -b`) | Makes the type check an explicit, named step, whatever the `build` script does. |
| `tflint --recursive --config "$(CURDIR)/.tflint.hcl"` after `tflint --init` | Lints all three layers and `modules/` in one run with the single root config; recursive mode otherwise looks for a config per directory. |
| `terraform validate`, `plan` and Trivy not in `make check` | They need provider downloads or AWS access; they stay in the pull-request checks (CICD-AC01). |
| No skipped steps in `make check` | A silent skip would let a story pass without its checks. All three parts exist after US01. |
| SQLAlchemy synchronous with psycopg 3 | 5 concurrent users (Q-O28); sync sessions are simpler to test and type; FastAPI runs sync routes in its thread pool. |
| Injectable clock in business rules | Required for the controlled-clock tests of D-PM3. |
| Coding conventions kept only in `AGENTS.md`; `CLAUDE.md` points there | One source for Claude Code and Codex, so the two cannot drift. |
| Region wording | Followed the Owner instruction: one statement in "AWS Provider Configuration", repeated in the local command block, the backend line and the pipeline flow. |

## Left for Step 8 kick-off or the first story

- **Create the `make check` target (US01).** The `Makefile` is empty (0 bytes). Adding `check` as described in `AGENTS.md` is a task in the US01 plan, together with `src/api/pyproject.toml` (ruff, mypy strict, pytest `testpaths`/`pythonpath`) and the `typecheck` script in `src/web/package.json`. `make bootstrap` does not exist either; it can be added in the same task or at Step 8.
- **Pin `.terraform-version` to 1.16.4** (IAC-AC01, Q-O36). The file is empty. Confirm the version exists when pinning. Owned by Step 8 or US01.
- **`.tflint.hcl` is empty.** It must enable the rules `CLAUDE.md` lists (naming convention, documented variables, documented outputs) and the AWS ruleset. US01 or US05 (IAC-AC10).
- **Test layout under `tests/`.** QA owns `tests/`; the pytest config in `src/api/pyproject.toml` must point at QA's API test folder. QA and the Dev Lead agree the folder (proposal: `tests/api/`) in the US01 plan.
- **UI tests.** The brief did not include a web test runner, and none is in the stack. When the first UI story needs QA tests for the UI, the plan picks a runner (proposal: Vitest) and `make check` gains `npm test`.
- **CI parity (US05).** `CLAUDE.md` describes `api_test.yml` and `web_build.yml` as lint and tests or build. US05 should add `ruff format --check`, `mypy` and `npm run typecheck` to them so CI runs what `make check` runs. I did not change that section (out of this task's scope).

## Open points for the Owner (not blocking)

1. **"All providers use AWS profile: `3tier`" (CLAUDE.md).** If the profile is written into the provider and backend blocks, CI cannot use it: GitHub Actions gets OIDC credentials and has no `3tier` profile. Recommended: providers and backends name no profile; locally `AWS_PROFILE=3tier` (already in the command block) supplies it. Left unchanged here because it is your rule; US01's plan will follow the recommendation unless you say otherwise.
2. **Monitoring section, "section 8 of the requirements document".** That document does not exist; the alarm list is OBS-AC05 in `docs/specs/spec-001.md`. Left unchanged (outside the items of this task); a one-line fix when you next approve a `CLAUDE.md` change.
3. **Alert email in a git-ignored local tfvars file (Q-O38).** `.gitignore` has no pattern for it yet. US02 should add one (for example `*.local.tfvars`) before the group layer takes the address.

## PM/SM follow-up (2026-11-01)

Open points 1 and 2 decided by the PM/SM as routine fixes and applied to `CLAUDE.md`: the `3tier` profile is supplied by `AWS_PROFILE` locally and provider and backend blocks name no profile (CI uses OIDC); the Monitoring section points to OBS-AC05 instead of the missing "section 8 of the requirements document". Open point 3 (gitignore pattern for the local alert-email tfvars) is left to US02.
