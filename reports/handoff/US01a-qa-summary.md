# Handoff: 2026-11-02 US01a - QA summary (tests first, plan task T0)

| | |
| --- | --- |
| Task | US01a T0, tests first. The Owner approved the task and the test commit on 2026-11-02 |
| Branch | `feature/US01a_repo_tooling_app_skeleton`, worktree `wt-US01a`, from `ef46e65` (G4 approval) |
| Commit | `3d414e1` `test(US01a): add tests-first checks for image, tooling and API skeleton` (only `tests/`) |
| Criteria | CNT-AC01, CNT-AC02 |
| Inputs read | `docs/plans/US01a.plan.md` (T0 to T3, sections 4, 6, 7), `AGENTS.md` ("Coding convention", test layout KO-9), `docs/specs/spec-001.md` (CNT-AC01, CNT-AC02, CNT-AC07), `docs/gates/G4.md` (US01a), `docs/backlog.md` (US01a), `docs/process/ai-native-sdlc-workflow.md` |

## What was done

- Wrote the tests for CNT-AC01 and CNT-AC02 in two parts, as plan section 4 asks. `tests/infra` reads the Dockerfile text. `tests/image` checks the built image (new folder, US01a-D4).
- Wrote enabler tests for the contracts in plan section 7.4 and the T1 to T3 designs. They are named by function ID (F-SYS-01, F-SYS-02) or decision ID (US01a-D2, D3, D6 to D10, SP1-D5), never by a criterion ID. The T3 boundary tests use the task ID; see US01a-QA-Q1.
- Added the `controlled_clock` fixture in `tests/api/conftest.py`. It follows the `app.clock.Clock` protocol: `now()` returns an aware UTC time, and only `advance(delta)` moves it. Tests inject it through `create_app(clock=...)` (plan 7.6).
- No mock data file was needed. The only fake values are an obvious mock password literal and `example.test` hosts (plan 7.3).

## Files produced

| File | Content |
| --- | --- |
| `tests/api/conftest.py` | `ControlledClock` and `controlled_clock`; `mock_settings`, `unreachable_settings` (127.0.0.1:9); `sqlite_engine`, `counted_sqlite_engine` (counts connections and statements); `failing_query_engine` (SQLite authorizer denies SELECT); `clean_cms_env` |
| `tests/api/test_system.py` | F-SYS-01, F-SYS-02, US01a-D7, US01a-D8 |
| `tests/api/test_errors.py` | US01a-D9. Test-only routes are added to the app that `create_app` returns |
| `tests/api/test_settings.py` | US01a-D6 |
| `tests/api/test_clock.py` | US01a-D10 |
| `tests/infra/test_dockerfile.py` | CNT-AC01 and CNT-AC02 (static part); T3 boundaries |
| `tests/infra/test_tooling.py` | US01a-D2, US01a-D3, SP1-D5 |
| `tests/image/test_image.py` | CNT-AC01 and CNT-AC02 (built-image part) |

## Tests mapped to IDs

### Criterion tests

| Criterion | Tests | File |
| --- | --- | --- |
| CNT-AC01 | `test_cnt_ac01_dockerfile_exists`, `test_cnt_ac01_dockerfile_has_two_or_more_stages`, `test_cnt_ac01_final_stage_is_python_313_slim` (last FROM is exactly `python:3.13-slim`, `AS <name>` allowed, a digest pin fails) | `tests/infra/test_dockerfile.py` |
| CNT-AC01 | `test_cnt_ac01_image_layers_start_with_python_313_slim` (the base `RootFS.Layers` are a prefix of the image's layers) | `tests/image/test_image.py` |
| CNT-AC02 | `test_cnt_ac02_final_stage_sets_user` (failure path: no USER means root), `test_cnt_ac02_last_user_is_10001_not_root`, `test_cnt_ac02_no_user_change_after_last_user` | `tests/infra/test_dockerfile.py` |
| CNT-AC02 | `test_cnt_ac02_image_config_user_is_10001` (`Config.User` is `10001:10001`), `test_cnt_ac02_container_runs_as_uid_10001` (`docker run --rm --entrypoint id <tag> -u` prints `10001`) | `tests/image/test_image.py` |

The ECS test point of CNT-AC02 (the task definition does not override the user) belongs to US01c and is not tested here.

### Enabler tests (the test report lists them as enablers, not criteria)

| ID | Tests |
| --- | --- |
| F-SYS-02 | `test_f_sys_02_healthz_ok_when_database_unreachable` (both paths), `test_f_sys_02_healthz_without_database_access`, `test_f_sys_02_healthz_body_has_no_configuration_values` |
| F-SYS-01 | `test_f_sys_01_status_open_when_database_reachable`, `test_f_sys_01_status_503_when_database_unreachable`, `test_f_sys_01_status_503_when_query_fails`, `test_f_sys_01_status_503_body_has_no_secret_host_or_exception_text`, `test_f_sys_01_status_503_logs_exception_class_only` (capsys), `test_f_sys_01_engine_disposed_on_shutdown` |
| US01a-D6 | `test_us01a_d6_settings_defaults`, `_settings_read_from_cms_environment`, `_keyword_arguments_take_precedence`, `_db_password_required`, `_db_password_is_secret`, `_sslmode_accepts_libpq_modes`, `_rejects_unknown_sslmode_or_log_level`, `_create_app_reads_cms_environment_without_settings`, `_engine_url_built_from_settings` |
| US01a-D7 | `test_us01a_d7_connect_timeout_is_3_seconds`, `test_us01a_d7_status_answers_within_connect_timeout` |
| US01a-D8 | `test_us01a_d8_docs_off` (`/docs`, `/redoc`, `/openapi.json`) |
| US01a-D9 | `test_us01a_d9_unknown_path_not_found`, `_method_not_allowed_keeps_allow_header`, `_domain_error_with_field_and_params`, `_domain_error_defaults_field_null_params_empty`, `_domain_error_attributes`, `_validation_missing_field`, `_validation_one_item_per_error`, `_validation_nested_field_joined_with_dot`, `_validation_query_parameter_without_source`, `_validation_params_made_json_safe`, `_unhandled_error_is_internal_error`, `_unhandled_error_logs_method_and_path_only` (capsys) |
| US01a-D10 | `test_us01a_d10_create_app_injects_clock`, `_routes_read_injected_clock_through_get_clock`, `_system_clock_is_default`, `_system_clock_is_timezone_aware_utc`, `_controlled_clock_fixture_follows_protocol`, `_datetime_now_only_in_system_clock` |
| US01a-D2 | `test_us01a_d2_makefile_has_target` (6 targets), `_check_is_default_goal`, `_no_parallel_and_stop_on_failure`, `_check_runs_api_web_terraform_in_order`, `_check_api_steps_in_order`, `_check_web_steps_in_order`, `_check_terraform_steps_in_order`, `_check_never_installs`, `_deps_creates_venv_and_installs`, `_bootstrap_installs_tools` |
| US01a-D3 | `test_us01a_d3_tflint_runs_with_home_in_repository`, `test_us01a_d3_tflint_config` |
| SP1-D5 | `test_sp1_d5_terraform_version_pinned` (file content is exactly `1.16.4\n`) |
| Plan T3 boundaries | `test_us01a_t3_no_secret_in_arg_or_env`, `test_us01a_t3_no_healthcheck`, `test_us01a_t3_final_stage_runtime_settings`, `test_us01a_t3_dockerignore_excludes` (11 entries) |

## What was run and what was not

| Check | Result |
| --- | --- |
| `python3 -m py_compile` on all 8 files | pass |
| Infra tests, dry run in the session scratchpad with a pytest stub, against a fake repository built from the plan's Dockerfile, `.tflint.hcl` and a plan-conformant Makefile | all pass |
| Same dry run with the fake Dockerfile changed to a digest pin and `USER root` | the CNT-AC01 and CNT-AC02 tests fail, as they should |
| Infra tests against the worktree today | every test fails for the right reason: Makefile targets missing, `src/api/Dockerfile` missing, `.terraform-version` empty |
| `tests/api` | **not run.** pytest and the API packages are not installed, and no install was approved. They will error at collection with `ModuleNotFoundError: app` until T2 exists. They have not been checked against the real FastAPI, pydantic and SQLAlchemy behaviour |
| `tests/image` | **not run.** Docker was out of scope for T0 |

### How the story run runs the tests

1. `make check` from the worktree root runs `tests/api` and `tests/infra` through `testpaths` (plan 7.2).
2. Then QA runs the image tests by explicit path (plan 7.7). They are not part of `make check`:

   ```bash
   cd <worktree>/src/api && .venv/bin/pytest ../../tests/image
   ```

   **Docker Desktop must be running** (G4 Owner action 2). The tests pull `python:3.13-slim`, build `src/api/Dockerfile` under a unique `cms-api-qa-us01a:<id>` tag and remove it in the fixture teardown. If Docker is down or the pull or build fails, each test fails with the reason; none skips. The test report then says Docker was down.

## Decisions (QA, routine)

| ID | Decision | Reason |
| --- | --- | --- |
| US01a-QA-D1 | `tests/api` files share data only through `conftest.py` fixtures, and mock constants are repeated per file. No test imports `conftest` | With `--import-mode=importlib`, `conftest` cannot be imported as a module (plan 7.2) |
| US01a-QA-D2 | Log checks build the app inside the test, after `capsys` starts, so the `basicConfig(stream=sys.stdout)` handler writes to the captured stream | Plan 7.4 |
| US01a-QA-D3 | Error-handler tests use `TestClient(..., raise_server_exceptions=False)` | Starlette re-raises an unhandled exception after the 500 is sent; the test checks the response |
| US01a-QA-D4 | Image tests record a build failure in the fixture and call `pytest.fail` in each test, rather than erroring in the fixture | They show as FAILED, never as skipped or errored (plan 7.7) |
| US01a-QA-D5 | Infra checks test only behaviour the plan fixes: order of steps, messages, pins and the variables the plan names. Wording and comments are free | Instruction not to over-specify |

## Open questions (for the Dev Lead)

- **US01a-QA-Q1, naming of the T3 boundary tests.** No decision ID covers these checks: no secret ARG or ENV, no HEALTHCHECK, the runtime settings, and the `.dockerignore` entries. CNT-AC07 belongs to US06, and plan 7.4 allows only function or decision IDs. I named them by task ID (`test_us01a_t3_...`). Is a task ID acceptable? If not, should they get a decision ID, or be dropped?
- **US01a-QA-Q2, the D7 timing bound.** `test_us01a_d7_status_answers_within_connect_timeout` connects to 192.0.2.1, a documentation address that is never routed. It requires a 503 in under 6 s to stand for "about 3 seconds". The result depends on the network: if the network rejects the address at once, the test passes immediately. Is 6 s the right bound, and is this approach acceptable?
- **US01a-QA-Q3, simulating "the query fails".** `failing_query_engine` uses SQLite's authorizer to deny `SELECT`. This raises `sqlite3.DatabaseError`, so the logged class would be `DatabaseError`, not `OperationalError`. Only the refused-connection case asserts the log text. Is this simulation acceptable for that row of the plan 7.4 contract table?
- **US01a-QA-Q4, the test client's httpx logger.** `test_us01a_d9_unhandled_error_logs_method_and_path_only` sets the `httpx` logger to WARNING for the test. The test client's httpx logger logs the full request URL, query string included, to the same stdout handler. That is test-client output, not the app's. Is changing it in the test acceptable, or should the check filter lines instead?
