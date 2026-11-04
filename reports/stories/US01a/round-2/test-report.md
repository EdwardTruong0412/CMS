RESULT: PASS

# Test report: US01a (2026-11-02, branch feature/US01a_repo_tooling_app_skeleton, commit 354a5c6)

Worktree: `/Users/truongquy/Documents/wt-US01a-dev2`, round 2. Working tree clean before and after the run. `tests/` and `testdata/mock/` are unchanged since QA's commit `3d414e1` (`git diff 3d414e1 HEAD -- tests/ testdata/` is empty).

## Commands run

| Command | Result |
| --- | --- |
| `make check` (repo root) | exit 0 |
| - `ruff check .`, `ruff format --check .`, `mypy` (src/api) | all checks passed; 13 files formatted; no mypy issues in 13 files |
| - `pytest` (src/api: `tests/api`, `tests/infra`) | 91 passed, 1 warning |
| - `npm run lint`, `npm run typecheck`, `npm run build` (src/web) | pass; Vite build produced `dist/` |
| - `terraform fmt -check -recursive`, `tflint --init`, `tflint --recursive` | pass |
| `cd src/api && .venv/bin/pytest ../../tests/image` (Docker running) | 3 passed; the test image was removed by the fixture teardown |

## Results by criterion

| Acceptance criterion | Tests | Result |
| --- | --- | --- |
| CNT-AC01 multi-stage, final stage `python:3.13-slim` | `tests/infra/test_dockerfile.py`: `test_cnt_ac01_dockerfile_exists`, `test_cnt_ac01_dockerfile_has_two_or_more_stages`, `test_cnt_ac01_final_stage_is_python_313_slim`; `tests/image/test_image.py`: `test_cnt_ac01_image_layers_start_with_python_313_slim` | PASS (4/4) |
| CNT-AC02 non-root user | `tests/infra/test_dockerfile.py`: `test_cnt_ac02_final_stage_sets_user`, `test_cnt_ac02_last_user_is_10001_not_root`, `test_cnt_ac02_no_user_change_after_last_user`; `tests/image/test_image.py`: `test_cnt_ac02_image_config_user_is_10001`, `test_cnt_ac02_container_runs_as_uid_10001` | PASS (5/5) |

## Enablers (no US01a criterion; named by function or decision ID, plan section 7)

| Enabler | Tests | Result |
| --- | --- | --- |
| F-SYS-01 `GET /api/v1/status` (200 open, 503 `SYSTEM_NOT_READY`, no secret/host/exception text, logs class only, engine disposed) | `tests/api/test_system.py::test_f_sys_01_*` (6) | PASS |
| F-SYS-02 `/healthz`, `/api/healthz` (200 without database, no DB access, no config values) | `tests/api/test_system.py::test_f_sys_02_*` (6 incl. params) | PASS |
| US01a-D2 Makefile targets and order (`bootstrap`, `deps`, `check`, never installs in check) | `tests/infra/test_tooling.py::test_us01a_d2_*` (17) | PASS |
| US01a-D3 tflint with HOME inside the repository, config | `tests/infra/test_tooling.py::test_us01a_d3_*` (2) | PASS |
| SP1-D5 `.terraform-version` pinned | `test_sp1_d5_terraform_version_pinned` | PASS |
| US01a-D6 settings (defaults, CMS_ env, secret password, sslmode/log level validation, engine URL) | `tests/api/test_settings.py::test_us01a_d6_*` (15) | PASS |
| US01a-D7 3-second connect timeout | `test_us01a_d7_connect_timeout_is_3_seconds`, `test_us01a_d7_status_answers_within_connect_timeout` | PASS |
| US01a-D8 API docs off | `test_us01a_d8_docs_off[/docs,/redoc,/openapi.json]` | PASS |
| US01a-D9 error format (404, 405 with Allow, DomainError, validation items, 500 INTERNAL_ERROR, safe logging) | `tests/api/test_errors.py::test_us01a_d9_*` (12) | PASS |
| US01a-D10 injectable clock | `tests/api/test_clock.py::test_us01a_d10_*` (6) | PASS |
| T3 Dockerfile hygiene (no secret ARG/ENV, no HEALTHCHECK, runtime settings, .dockerignore) | `tests/infra/test_dockerfile.py::test_us01a_t3_*` (14 incl. params) | PASS |

Totals: 91 (`make check`) + 3 (`tests/image`) = 94 passed, 0 failed, 0 skipped.

## Failures

None.

## Not tested, and why

- CNT-AC02's ECS test point ("the task definition does not override the user") belongs to US01c (`tests/infra`, `tests/dev01`, Session 1), per the plan section 4. US01a creates no AWS resource.
- The round-2 fixes to `src/web/src/api/client.ts` (malformed non-2xx bodies give `ApiError(status, [])`) have no QA test: US01a has no web test runner and no criterion covers the client; it is checked by lint, typecheck and build only. The Dev reports manual smoke checks.
- The removal of pip from the runtime image (round-1 infra finding) is not asserted by a QA test; no US01a criterion requires it. CNT-AC01 and CNT-AC02 image checks still pass after the change.

## Open questions

None. Non-blocking note: pytest shows `StarletteDeprecationWarning` (httpx with `starlette.testclient`); it does not affect results.
