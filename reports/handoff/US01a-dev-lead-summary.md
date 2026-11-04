# Handoff: 2026-11-02 US01a - Dev Lead summary (repo tooling and app skeleton, before the story run)

| | |
| --- | --- |
| Task | Dev Lead summary for US01a, required by global rule 5 and the `/story` preflight. Approved by the Owner on 2026-11-02 |
| Branch / worktree | `feature/US01a_repo_tooling_app_skeleton`, `/Users/truongquy/Documents/wt-US01a`; commits `ef46e65` (G4 approval), `3d414e1` (QA tests) |
| Read | `docs/plans/US01a.plan.md`, `docs/gates/G4.md` (US01a), `reports/handoff/US01a-qa-summary.md`, `tests/api/conftest.py`, `tests/api/test_system.py`, `tests/api/test_errors.py`, `reports/handoff/PROC12-pm-scrum-master-summary.md`, `REVIEW.md`, `AGENTS.md` |
| Changed | This file only. Nothing committed; no Dev started |

## 1. What was done

1. **Plan.** Wrote `docs/plans/US01a.plan.md` in DES03: tasks T0 to T5, detailed design, traceability, file list, fixed interfaces, pins, 15 Dev Lead decisions (US01a-D1 to D15), no Owner-tier question. Revised it after the PO and QA read-only G4 review; the four changes are in plan section 15.
2. **G4.** The Owner approved the US01a section of `docs/gates/G4.md` (`ef46e65`). I then created the branch from `develop`.
3. **Tests first.** QA committed T0 on the branch (`3d414e1`, only `tests/`). I answer QA's four questions in section 6.

## 2. Design in brief (pointers, not a restatement)

| Topic | Plan section |
| --- | --- |
| Goal and out of scope | 1 |
| T1 tooling (`make bootstrap`, `deps`, `check`, `.tflint.hcl`, `.terraform-version`) | 2, T1; US01a-D2, D3 |
| T2 API skeleton (settings, engine, status, health, error format, clock) | 2, T2; US01a-D6 to D10, D13 |
| T3 Dockerfile and `.dockerignore` | 2, T3; US01a-D15 |
| T4 web skeleton (Vite, React, i18n, API client) | 2, T4; US01a-D11, D12, D14 |
| T5 docs (`AGENTS.md`, `CLAUDE.md`) | 2, T5 |
| Contracts and test hooks for QA | 7 |
| Interfaces later stories rely on | 6 |

## 3. Dev assignment for the run

- **Dev 2**, lane "App and small infrastructure" (SP1-D1, `reports/sprints/sprint-1-planning.md`). One Dev for the whole story.
- **Worktree** `../wt-US01a-dev2`, created by `/story` (`.claude/skills/story/SKILL.md`), not by me. The plan is the whole assignment: each task names its goal, reads, writes and boundaries.
- **Order** (plan section 3, US01a-D1): T1, T2, T3, T4, T5. Run `make deps` once T2 and T4 have created `pyproject.toml` and `package.json`, then run `make check` until it passes. One proposed commit per task, with the messages listed in section 3.
- **Not in `make check`:** `tests/image` runs in QA's test round by explicit path (plan 7.7).

## 4. Dependency pins and escalation

- **Pins** (plan section 8): every Python and npm package is new and pinned exactly, plus the base image tag `python:3.13-slim`, `tflint-ruleset-aws` 0.50.0, Terraform 1.16.4 and `python@3.13` in `make bootstrap`. Transitive packages stay unpinned (KO-10).
- **Approver escalation** (plan section 9): the run is expected to end in `needs-human`, so you decide G5. The triggers are Dependencies (every pin above) and Governance (the T5 edits to `AGENTS.md` and `CLAUDE.md`). At G5 you check the pins, the T5 wording and QA's `tests/image` report.

## 5. Owner actions before `/story US01a`

1. `brew install python@3.13`. Only 3.14 is installed; `make deps` builds the venv with 3.13.
2. Keep Docker Desktop running for the whole run, because QA's `tests/image` needs it in the test round. If Docker is down those tests fail (they never skip).

## 6. Answers to QA's questions (Dev Lead tier)

| ID | Question | Decision | Reason | Test change |
| --- | --- | --- | --- | --- |
| US01a-DL-D1 | US01a-QA-Q1: T3 boundary tests named by task ID | **Accepted.** `test_us01a_t<n>_...` is a valid enabler name for a boundary the plan fixes in a task that has no function ID or decision ID. The test report lists these tests as enablers | Plan 7.4 bans criterion IDs because a test would claim a criterion the story does not own. A task ID makes no such claim and traces to the exact plan line (T3 Boundaries). Inventing a decision ID only to name tests would add an ID with no decision behind it. CNT-AC07 stays with US06 | None |
| US01a-DL-D2 | US01a-QA-Q2: D7 timing bound with 192.0.2.1 and a 6 s limit | **Accepted as written.** It is an upper bound only. A fast rejection passes, and that is correct: the contract is "no hang". The 6 s limit leaves margin above one 3 s attempt | The default `sslmode` is `require` (US01a-D6), so libpq makes one attempt. With `prefer` it would make two, but no test sets that. `test_us01a_d7_connect_timeout_is_3_seconds` checks the configured value, and dev01 checks the drop-packet case in US01c and US31 (plan section 12) | None |
| US01a-DL-D3 | US01a-QA-Q3: the authorizer failure gives `DatabaseError`, not `OperationalError` | **Accepted.** The row tests the breadth of the catch: US01a-D7 and T2 item 7 catch any `sqlalchemy.exc.DBAPIError`. If the code caught only `OperationalError`, this test would fail. Only the refused-connection test checks the exact log text, which is correct | T2 item 7 logs `type(exc).__name__` of the SQLAlchemy wrapper. psycopg's refused connection becomes `OperationalError`, which is the text that test checks. The authorizer case becomes `DatabaseError`. Both are 503 `SYSTEM_NOT_READY` | None |
| US01a-DL-D4 | US01a-QA-Q4: the test raises the `httpx` logger to WARNING | **Accepted.** That logger belongs to the test client (`httpx` is a dev extra, not used by the app). Raising its level for one test, restored by `monkeypatch`, removes client output and keeps the app's own log under test | Filtering lines would depend on httpx's message format and could hide an app line that leaks the query string. The level change cannot hide app output, because the app logs through its own loggers | None |

**No test change is needed.** If the Dev shows that a test conflicts with the plan, the Dev reports it in the handoff. Any change to `tests/` then goes back to QA and needs the Owner's approval (global rule 2, R-09).

## 7. Risks

| Risk | Response |
| --- | --- |
| The Codex sandbox cannot reach the Docker socket, or the `tfenv` shim writes outside the worktree (plan section 11, not verified) | T3: if the Dev cannot reach Docker, it says so and QA's `tests/image` decides. Terraform: if `fmt` fails for this reason, the Dev reports BLOCKED and the PM/SM raises it |
| A pinned package breaks at install time (for example the eslint 10 plugin set), or the `pydantic.mypy` plugin does not load | The Dev pins the nearest working version, or removes only the plugin line (US01a-D13), and names it in the handoff. The approver escalates the change |
| `tests/api` has not yet run against the real FastAPI, pydantic and SQLAlchemy (QA summary) | The first `make check` in the run is the first real run. A test that fails because the test itself is wrong goes back to QA, as in section 6 |
| The uvicorn access log writes the full path, query string included | No US01a route takes query parameters. This is noted for the plan of the first story with query parameters (list and search), not for US01a |

## 8. Open questions (Owner tier)

None.
