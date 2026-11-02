# Plan: US01a Repo tooling and app skeleton

| | |
| --- | --- |
| Story | US01a Repo tooling and app skeleton (`docs/backlog.md#us01a`) |
| Criteria owned | CNT-AC01, CNT-AC02 (text in `docs/specs/spec-001.md`, "CNT: Container image") |
| Functions | F-SYS-01 System status, F-SYS-02 Health check (`docs/specs/function-list.md`; BD-7) |
| Depends on | None |
| Dev | **Dev 2** (SP1-D1, lane "App and small infrastructure") |
| Branch | `feature/US01a_repo_tooling_app_skeleton`, created by the Dev Lead from `develop` after G4 |
| Worktree (story run) | `../wt-US01a-dev2` |
| Size | M (1 to 1.5 days) |
| Author | Dev Lead, 2026-11-02 (task DES03), for G4 |
| Inputs read | `docs/backlog.md` (US01a to US05), spec-001 (CNT group, NFR, BD-1 to BD-9, Decisions log), `docs/specs/function-list.md`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, `docs/kickoff.md` (KO-1 to KO-24), `docs/project-plan.md` (DoD, check sessions), `reports/sprints/sprint-1-planning.md`, `reports/handoff/PROC08-dev-lead-summary.md`, `reports/handoff/PROC12-pm-scrum-master-summary.md`, `.claude/skills/story/SKILL.md`, the current repository (empty `Makefile`, `.terraform-version`, `.tflint.hcl`; no `src/`, `tests/`, `modules/`, `awsenv/`) |

## 1. Goal

After this story, a clean clone needs only `make bootstrap` (once per machine), `make deps` and `make check` to lint, type-check, test and build the API, the web UI and the (still empty) Terraform tree, with no AWS access. The API answers `GET /healthz`, `GET /api/healthz` and `GET /api/v1/status`. The API image is built from a multi-stage `src/api/Dockerfile` whose final stage is `python:3.13-slim` and which runs as UID 10001. No AWS resource is created.

Out of scope (later stories): `compose.yaml` and the Vite proxy (US04), CI workflows (US05), Alembic and any table (US08), the session dependency (US09), the language switch (US19), the final SCR-00 (US31), any Terraform (US01b on).

## 2. Tasks

Each task lists its goal, what to read, what to write, its boundaries, the detailed design and the criterion it serves. Write only the files a task names. Do not edit anything under `tests/` (QA's, committed before you start).

### T0 [QA] Tests first (QA, before the Dev starts)

- Goal: tests for CNT-AC01 and CNT-AC02, and local tests for the health and status contracts, committed as `test(US01a): ...` on the story branch. See section 7 "For QA".
- Writes: `tests/api/`, `tests/infra/`, `tests/image/` (new folder, US01a-D4). Nothing else.

### T1 [Infra] Repository tooling: `make bootstrap`, `make deps`, `make check`

- Goal: one command checks everything, and it works inside the Codex sandbox (PROC12).
- Read: `AGENTS.md` ("The check command"), `CLAUDE.md` ("Required Tools", "TFLint Configuration"), `reports/handoff/PROC12-pm-scrum-master-summary.md`.
- Write: `Makefile`, `.terraform-version`, `.tflint.hcl`, `.gitignore`.
- Boundaries: no other target than the ones below; no Terraform file; `check` never installs anything and never skips a step; no `-j` parallelism.
- Criteria served: enabler for every criterion (DoD item 2); RV-01 depends on it.

Detailed design:

1. `.terraform-version` contains exactly `1.16.4` and a trailing newline (SP1-D5; IAC-AC01 stays with US05).
2. `.tflint.hcl`:

   ```hcl
   config {
     call_module_type = "local"
   }

   plugin "terraform" {
     enabled = true
     preset  = "recommended"
   }

   plugin "aws" {
     enabled = true
     version = "0.50.0"
     source  = "github.com/terraform-linters/tflint-ruleset-aws"
   }

   rule "terraform_naming_convention" {
     enabled = true
   }

   rule "terraform_documented_variables" {
     enabled = true
   }

   rule "terraform_documented_outputs" {
     enabled = true
   }

   rule "terraform_standard_module_structure" {
     enabled = true
   }

   rule "terraform_required_version" {
     enabled = false
   }

   rule "terraform_required_providers" {
     enabled = false
   }
   ```

   This file was tested in the session scratchpad on 2026-11-02 with tflint 0.64.0: `tflint --init` installs the plugin with `HOME` inside the directory, an empty tree passes, and a variable without a description fails with exit code 2.
3. `Makefile` (behaviour fixed; wording and comments free). Use `SHELL := /bin/bash`, `.SHELLFLAGS := -eu -o pipefail -c`, `.NOTPARALLEL:`, `.DEFAULT_GOAL := check`, and these variables: `PYTHON ?= python3.13`, `API_DIR := $(CURDIR)/src/api`, `WEB_DIR := $(CURDIR)/src/web`, `VENV_BIN := $(API_DIR)/.venv/bin`, `TFLINT_HOME := $(CURDIR)/.cache/home`, `TFLINT_CONFIG := $(CURDIR)/.tflint.hcl`.

   | Target | Runs, in order |
   | --- | --- |
   | `bootstrap` | `brew install tfenv tflint trivy python@3.13`; `brew install --cask drawio`; `tfenv install` (reads `.terraform-version`). macOS and Homebrew only; never run by `check` |
   | `deps` | `$(PYTHON) -m venv $(API_DIR)/.venv`; `$(VENV_BIN)/python -m pip install --disable-pip-version-check -e "$(API_DIR)[dev]"`; `cd $(WEB_DIR) && npm ci` |
   | `check` | `check-api`, then `check-web`, then `check-terraform` |
   | `check-api` | Fails with the message `src/api/.venv is missing: run make deps` when `$(VENV_BIN)/pytest` is not executable. Then, each from `$(API_DIR)`: `$(VENV_BIN)/ruff check .`, `$(VENV_BIN)/ruff format --check .`, `$(VENV_BIN)/mypy`, `$(VENV_BIN)/pytest` |
   | `check-web` | Fails with `src/web/node_modules is missing: run make deps` when the folder is missing. Then, from `$(WEB_DIR)`: `npm run lint`, `npm run typecheck`, `npm run build` |
   | `check-terraform` | From the repo root: `terraform fmt -check -recursive`; `mkdir -p $(TFLINT_HOME)`; `HOME="$(TFLINT_HOME)" tflint --init --config "$(TFLINT_CONFIG)"`; `HOME="$(TFLINT_HOME)" tflint --recursive --config "$(TFLINT_CONFIG)"` |

   `HOME` is changed only on the two `tflint` lines (PROC12-D2): tflint's signature cache otherwise writes to `~/.sigstore`, which the sandbox blocks. The plugin goes to `TFLINT_PLUGIN_DIR` when the story skill sets it, else under `.cache/home/.tflint.d/`. Both are inside the git-ignored `.cache/`.
4. `.gitignore`: append, under a comment per block, `src/api/.venv/`, `__pycache__/`, `*.egg-info/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `src/api/build/`, `src/web/node_modules/`, `src/web/dist/`, `*.tsbuildinfo`. Keep every existing line.

### T2 [BE] API skeleton (`src/api`)

- Goal: the FastAPI app with the health and status endpoints, settings, database engine, error format and injectable clock that every later API story builds on.
- Read: `AGENTS.md` ("Python: API"), spec BD-6, BD-7 (F-SYS-01, F-SYS-02), Decisions log D-DL1, D-DL7, D-PM3, SP1-D4 (in `reports/handoff/PROC08-dev-lead-summary.md`), this section.
- Write: `src/api/pyproject.toml`, `src/api/app/__init__.py`, `src/api/app/main.py`, `src/api/app/settings.py`, `src/api/app/db.py`, `src/api/app/clock.py`, `src/api/app/errors.py`, `src/api/app/routers/__init__.py`, `src/api/app/routers/system.py`, `src/api/app/schemas/__init__.py`, `src/api/app/schemas/errors.py`, `src/api/app/schemas/system.py`, `src/api/app/services/__init__.py`, `src/api/app/services/system.py`.
- Boundaries: no `models/`, no Alembic, no session dependency, no CORS middleware, no other route, no module-level app instance. `datetime.now()` appears only in `SystemClock`. Do not add routes to `src/` only so that the error handlers can be tested (for example a route that raises): QA's tests add their own test-only routes to the app that `create_app` returns.
- Criteria served: enabler; F-SYS-01 and F-SYS-02 are proven on dev01 through CNT-AC03 (US01c) and the SCH group (US30, US31).

Detailed design:

1. `pyproject.toml`

   ```toml
   [build-system]
   requires = ["setuptools==84.2.1"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "cms-api"
   version = "0.1.0"
   requires-python = ">=3.13,<3.14"
   dependencies = [
     "fastapi==0.162.0",
     "uvicorn==0.54.0",
     "sqlalchemy==2.1.6",
     "psycopg[binary]==3.3.6",
     "pydantic==2.14.2",
     "pydantic-settings==2.16.2",
   ]

   [project.optional-dependencies]
   dev = ["ruff==0.17.3", "mypy==2.4.1", "pytest==9.2.0", "httpx==0.28.1"]

   [tool.setuptools.packages.find]
   include = ["app*"]

   [tool.ruff]
   target-version = "py313"
   line-length = 100

   [tool.ruff.lint]
   select = ["E", "W", "F", "I", "B", "UP", "N", "S", "SIM", "C4", "PTH", "RUF"]

   [tool.mypy]
   strict = true
   python_version = "3.13"
   files = ["app"]
   plugins = ["pydantic.mypy"]

   [tool.pytest.ini_options]
   testpaths = ["../../tests/api", "../../tests/infra"]
   pythonpath = ["."]
   addopts = ["--import-mode=importlib", "--strict-markers", "-ra"]
   ```

   These `[tool.*]` settings are the ones RV-03 compares against; any other setting, exclusion or ignore is a finding. If the `pydantic.mypy` plugin does not load with mypy 2.4.1, remove only the `plugins` line and say so in the handoff (US01a-D13); do not lower `strict`.
2. `settings.py`: `class Settings(BaseSettings)` with `model_config = SettingsConfigDict(env_prefix="CMS_", env_file=None, case_sensitive=False, extra="ignore")`. Fields, in this order:

   | Field | Environment variable | Type | Default |
   | --- | --- | --- | --- |
   | `db_host` | `CMS_DB_HOST` | `str` | `"localhost"` |
   | `db_port` | `CMS_DB_PORT` | `int` | `5432` |
   | `db_name` | `CMS_DB_NAME` | `str` | `"cms"` |
   | `db_user` | `CMS_DB_USER` | `str` | `"cms"` |
   | `db_password` | `CMS_DB_PASSWORD` | `SecretStr` | none (required; a secret, Q-D13) |
   | `db_sslmode` | `CMS_DB_SSLMODE` | `Literal["disable", "prefer", "require", "verify-ca", "verify-full"]` | `"require"` |
   | `log_level` | `CMS_LOG_LEVEL` | `Literal["DEBUG", "INFO", "WARNING", "ERROR"]` | `"INFO"` |

   Later stories add `jwt_key` / `CMS_JWT_KEY` (US09) and `setup_token` / `CMS_SETUP_TOKEN` (US08), both `SecretStr` with no default (SP1-D4).
3. `db.py`:
   - `DB_CONNECT_TIMEOUT_SECONDS = 3`.
   - `def create_db_engine(settings: Settings) -> Engine`: builds the URL with `sqlalchemy.engine.URL.create("postgresql+psycopg", username=..., password=settings.db_password.get_secret_value(), host=..., port=..., database=...)` (no string formatting), and returns `create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": DB_CONNECT_TIMEOUT_SECONDS, "sslmode": settings.db_sslmode})`.
   - `def get_engine(request: Request) -> Engine`: returns `request.app.state.engine`.
   - The per-request session dependency comes with the first data route (US08).
4. `clock.py`:
   - `class Clock(Protocol)` with `def now(self) -> datetime` (timezone-aware, UTC).
   - `class SystemClock` whose `now()` returns `datetime.now(UTC)`. This is the only `datetime.now` in the code.
   - `def get_clock(request: Request) -> Clock`: returns `request.app.state.clock`.
   - Rule for later stories: routes take `clock: Annotated[Clock, Depends(get_clock)]` and pass it to services; services never read the time any other way (D-PM3).
5. `errors.py`:
   - `class DomainError(Exception)` with `__init__(self, status_code: int, code: str, *, field: str | None = None, params: Mapping[str, object] | None = None)` and the attributes `status_code` and `errors` (a list holding one `ErrorItem`). A later story may add a way to raise several items at once; this constructor stays.
   - `def register_exception_handlers(app: FastAPI) -> None` installs four handlers. Each returns `ErrorsOut` JSON, `{"errors": [{"field": ..., "code": ..., "params": {...}}]}`:

   | Exception | Status | `code` | `field` | Notes |
   | --- | --- | --- | --- | --- |
   | `DomainError` | its `status_code` | its code | its field | |
   | `RequestValidationError` | 422 | the pydantic error `type` in upper case (`MISSING`, `EXTRA_FORBIDDEN`, `STRING_TOO_SHORT`) | the `loc` joined with `.`, without a leading `body`, `query`, `path`, `header` or `cookie` | `params` = the error `ctx` with every value made JSON-safe (`str()` for anything that is not str, int, float, bool or None); one item per error |
   | `starlette.exceptions.HTTPException` | its status | `NOT_FOUND` for 404, `METHOD_NOT_ALLOWED` for 405, otherwise `HTTP_<status>` | `null` | keep the exception's headers (for example `Allow`) |
   | `Exception` (any other) | 500 | `INTERNAL_ERROR` | `null` | `logger.exception("unhandled error on %s %s", request.method, request.url.path)`; never the body, query string, headers or cookies |
6. `schemas/errors.py`: `ErrorItem` (`field: str | None`, `code: str`, `params: dict[str, object]`) and `ErrorsOut` (`errors: list[ErrorItem]`). `schemas/system.py`: `HealthOut` (`status: Literal["ok"]`) and `StatusOut` (`status: Literal["open"]`). US08 adds `setup_required: bool` to `StatusOut`.
7. `services/system.py`: `def check_status(engine: Engine) -> StatusOut`. It opens a connection, runs `text("SELECT 1")` and returns `StatusOut(status="open")`. On `sqlalchemy.exc.DBAPIError` (which includes `OperationalError`), it logs `logger.warning("database check failed: %s", type(exc).__name__)` and raises `DomainError(503, "SYSTEM_NOT_READY") from exc`. It never logs the URL, the exception message or the password.
8. `routers/system.py`: `router = APIRouter(tags=["system"])`, synchronous `def` handlers, dependencies in `Annotated[..., Depends(...)]` form (this avoids ruff B008):

   | Route | `response_model` | Handler body |
   | --- | --- | --- |
   | `GET /healthz` | `HealthOut` | `return HealthOut(status="ok")`; no dependency, no database |
   | `GET /api/healthz` | `HealthOut` | same |
   | `GET /api/v1/status` | `StatusOut`, plus `responses={503: {"model": ErrorsOut}}` | `return system.check_status(engine)` with `engine: Annotated[Engine, Depends(get_engine)]` |
9. `main.py`:

   ```python
   def create_app(
       settings: Settings | None = None,
       *,
       engine: Engine | None = None,
       clock: Clock | None = None,
   ) -> FastAPI: ...
   ```

   - `settings` defaults to `Settings()`, read from the `CMS_` environment variables. mypy flags the missing `db_password` argument; write `Settings()  # type: ignore[call-arg]  # values come from CMS_ environment variables`.
   - Configures logging with `logging.basicConfig(level=settings.log_level, stream=sys.stdout, format="%(asctime)s %(levelname)s %(name)s %(message)s", force=True)`.
   - `engine` defaults to `create_db_engine(settings)`, and `clock` defaults to `SystemClock()`.
   - Builds `FastAPI(title="CMS API", docs_url=None, redoc_url=None, openapi_url=None, lifespan=...)`. The lifespan calls `engine.dispose()` on shutdown.
   - Sets `app.state.settings`, `app.state.engine` and `app.state.clock`, calls `register_exception_handlers(app)` and `app.include_router(system.router)`.
   - No module-level `app`. Uvicorn starts it with `uvicorn app.main:create_app --factory`.

### T3 [Infra] API container image (`src/api/Dockerfile`)

- Goal: CNT-AC01 and CNT-AC02.
- Read: `AGENTS.md` ("Dockerfile and local stack"), spec CNT-AC01, CNT-AC02, CNT-AC07.
- Write: `src/api/Dockerfile`, `src/api/.dockerignore`.
- Boundaries: no `ARG` or `ENV` holding a secret, no `HEALTHCHECK` (the ALB checks `/healthz`, CNT-AC03), no `apt-get` packages, no digest pin (KO-11).
- Criteria served: CNT-AC01, CNT-AC02.

Detailed design (build context `src/api`):

```dockerfile
FROM python:3.13-slim AS builder
WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir --disable-pip-version-check --prefix=/install .

FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN groupadd --system --gid 10001 cms \
 && useradd --system --uid 10001 --gid 10001 --no-create-home \
      --home-dir /nonexistent --shell /usr/sbin/nologin cms
COPY --from=builder /install /usr/local
WORKDIR /app
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

- The final stage copies only the installed packages, which include the `app` package. US08 adds `COPY alembic.ini migrations/ ./` into `/app`, before `USER`.
- `USER 10001:10001` is the last `USER` line. Nothing after it changes the user.
- `.dockerignore`: `.env*`, `.git`, `.venv/`, `__pycache__/`, `*.pyc`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `*.egg-info/`, `build/`, `tests/`.
- If Docker is reachable from your sandbox, run `docker build -t cms-api:us01a -f src/api/Dockerfile src/api` and `docker run --rm --entrypoint id cms-api:us01a -u` (expect `10001`), and paste the output in the handoff. If it is not reachable, say so; QA's `tests/image` prove both in the test round.

### T4 [FE] Web skeleton (`src/web`)

- Goal: a Vite, React and strict TypeScript app that passes `npm run lint`, `typecheck` and `build`. It has the one API client and a start page that calls the status endpoint and shows the closed-page placeholder on 503 or no answer.
- Read: `AGENTS.md` ("TypeScript and React: web"), spec BD-3 (SCR-00), BD-4, SCH-AC04, Q-D5, D-DL2, D-DL8, KO-14.
- Write: `src/web/package.json`, `src/web/package-lock.json`, `src/web/index.html`, `src/web/vite.config.ts`, `src/web/tsconfig.json`, `src/web/tsconfig.app.json`, `src/web/tsconfig.node.json`, `src/web/eslint.config.js`, `src/web/.prettierignore`, `src/web/src/main.tsx`, `src/web/src/App.tsx`, `src/web/src/api/client.ts`, `src/web/src/i18n/index.ts`, `src/web/src/i18n/en.json`, `src/web/src/i18n/vi.json`, `src/web/src/screens/ClosedScreen.tsx`.
- Boundaries:
  - no router library, no CSS framework, no Vite proxy (US04) and no language switch (US19);
  - no other screen, and no test runner (US08 chooses one);
  - no hard-coded user-visible text in components;
  - local storage is not used.
- Criteria served: enabler. US01c serves this build through CloudFront (NET-AC08); US31 completes SCR-00 against SCH-AC02 to SCH-AC05.

Detailed design:

1. `package.json`:
   - `"name": "cms-web"`, `"private": true`, `"type": "module"`, `"engines": {"node": ">=22.12"}`.
   - Scripts: `"dev": "vite"`, `"build": "vite build"`, `"typecheck": "tsc -b"`, `"lint": "eslint . && prettier --check ."`, `"format": "prettier --write ."`.
   - Exact versions, no `^` or `~`:

   | dependencies | devDependencies |
   | --- | --- |
   | `react` 19.3.1, `react-dom` 19.3.1, `i18next` 26.7.1, `react-i18next` 17.1.11 | `vite` 8.3.5, `@vitejs/plugin-react` 6.1.2, `typescript` 6.0.3, `@types/react` 19.3.0, `@types/react-dom` 19.3.0, `eslint` 10.14.0, `@eslint/js` 10.0.1, `typescript-eslint` 8.72.1, `eslint-plugin-react-hooks` 7.1.1, `globals` 17.14.0, `prettier` 3.9.10 |

   TypeScript stays on 6.0.3: `typescript-eslint` 8.72.1 accepts `>=4.8.4 <6.1.0`, so 7.x would break the lint (US01a-D14). Create `package-lock.json` with `npm install`, then confirm `npm ci` works from it.
2. TypeScript, in the layout of the Vite `react-ts` template:
   - `tsconfig.json` has `"files": []` and references to `tsconfig.app.json` and `tsconfig.node.json`.
   - Both referenced configs set `"strict": true`, `"noEmit": true`, `"noUncheckedIndexedAccess": true`, `"noUnusedLocals": true`, `"noUnusedParameters": true`, `"verbatimModuleSyntax": true`, `"module": "ESNext"`, `"moduleResolution": "bundler"`, `"target": "ES2022"`, `"skipLibCheck": true`, and `"tsBuildInfoFile"` under `node_modules/.tmp/`.
   - The app config also sets `"jsx": "react-jsx"`, `"lib": ["ES2022", "DOM", "DOM.Iterable"]`, `"resolveJsonModule": true`, `"types": ["vite/client"]` and `"include": ["src"]`.
   - The node config includes only `vite.config.ts` and sets `"types": []`.
   - Set `types` explicitly in both: TypeScript 6 no longer includes every `@types` package by default.
3. `eslint.config.js` (flat config):
   - Ignore `dist`.
   - For `**/*.{ts,tsx}`: `@eslint/js` recommended, `tseslint.configs.strictTypeChecked` and `stylisticTypeChecked` with `parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname }`, the react-hooks plugin's flat recommended config, and browser `globals`.
   - For `**/*.js`: `tseslint.configs.disableTypeChecked`.
   - `no-explicit-any` stays an error, as in the strict preset.
   - `.prettierignore`: `dist`, `node_modules`, `package-lock.json`. Prettier runs with its default options (no config file).
4. `vite.config.ts`: `defineConfig({ plugins: [react()] })`. `index.html`: `<html lang="en">`, `<title>CMS</title>`, `<div id="root">`, and a module script `/src/main.tsx`.
5. `src/api/client.ts`, the only module that calls `fetch`:
   - `export type ApiErrorItem = { field: string | null; code: string; params: Record<string, unknown> }`.
   - `export class ApiError extends Error` with `status: number` and `errors: ApiErrorItem[]`.
   - `export class SystemClosedError extends Error`.
   - `export function onSystemClosed(listener: () => void): () => void`. It registers a listener and returns the unsubscribe function.
   - `export async function apiRequest<T>(path: \`/api/${string}\`, options?: { method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"; body?: unknown }): Promise<T>`:
     - calls `fetch(path, { method, credentials: "same-origin", headers })`;
     - the headers always include `Accept: application/json`, add `Content-Type: application/json` when there is a body, and add `X-CMS-Request: 1` on every method other than GET (US01a-D12, D-DL2);
     - a rejected `fetch` (no answer) or a 503 notifies every listener and throws `SystemClosedError`;
     - any other non-2xx parses `{"errors": [...]}` and throws `ApiError`;
     - 204 returns `undefined`, otherwise the JSON body. Read it as `unknown` first, then cast to `T`.
   - `export type StatusOut = { status: "open" }` (US08 adds `setup_required`) and `export function getStatus(): Promise<StatusOut>` (`GET /api/v1/status`).
6. `src/i18n/index.ts`:
   - initialises `i18next` with `initReactI18next` and the resources `{ en: { translation: en }, vi: { translation: vi } }`;
   - sets `lng: "en"`, `fallbackLng: "en"` and `interpolation: { escapeValue: false }`.

   `en.json` and `vi.json` are nested objects with exactly the same keys:

   | Key | en | vi |
   | --- | --- | --- |
   | `app.title` | `CMS` | `CMS` |
   | `app.loading` | `Loading...` | `Đang tải...` |
   | `home.running` | `CMS is running.` | `CMS đang hoạt động.` |
   | `closed.message` | `CMS is closed. Office hours: Monday to Friday, 09:00-18:00 (ICT).` | `CMS đang tạm đóng. Giờ làm việc: Thứ Hai đến Thứ Sáu, 09:00-18:00 (ICT).` |
7. `src/screens/ClosedScreen.tsx`:
   - Starts with the comment `// SCR-00 Closed (placeholder until US31)`.
   - Renders `closed.message` twice, through `i18n.getFixedT("en")` and `i18n.getFixedT("vi")`, in two elements with `lang="en"` and `lang="vi"`. SCR-00 always shows both languages (SCH-AC04).
   - No form, no data and no language switch.
8. `src/App.tsx`:
   - Keeps the state `"loading" | "open" | "closed"`.
   - Subscribes to `onSystemClosed` in an effect and calls `getStatus()` once on mount.
   - Shows `app.loading` while loading, `<ClosedScreen />` when closed, and when open a `<main>` with `app.title` as a heading and `home.running`.
   - Any other error (an `ApiError`) is treated as closed, because the start page can do nothing else with it.
9. `src/main.tsx`:
   - imports `./i18n` and renders `<StrictMode><App /></StrictMode>` into `#root`;
   - if `#root` is missing, it throws an `Error` (no non-null `!`).

### T5 [Infra] Docs touched by the story (DoD item 6)

- Goal: `AGENTS.md` and `CLAUDE.md` describe the new targets and the test folder. Without this, a later Dev or reviewer would not know to run `make deps`.
- Read: `AGENTS.md` ("The check command", "Tests"), `CLAUDE.md` ("Required Tools", "Directory Structure and Architecture").
- Write: `AGENTS.md`, `CLAUDE.md`, only the lines below.
- Boundaries: change no other line. `.claude/rules/global.md` and the "Rules for all agents" section of `AGENTS.md` are not touched.

Changes:

1. `AGENTS.md`, "The check command":
   - Replace the bullet that starts "Dependencies are installed beforehand" with: "Dependencies are installed beforehand with `make deps`. It creates `src/api/.venv` with Python 3.13, installs `src/api` with its `dev` extra (ruff, mypy, pytest, httpx), and runs `npm ci` in `src/web`. Terraform (from `.terraform-version`), tflint, trivy and Python 3.13 come from `make bootstrap`. `make check` runs `tflint` with `HOME` set to `.cache/home` inside the repository, so it works inside the Codex sandbox."
   - Delete the bullet that starts "If the `check` target does not exist yet".
2. `AGENTS.md`, "Tests", first bullet: after the `tests/web/` item, add "`tests/image/` (checks of the built API image that need a local Docker daemon; run by QA in the test round, not part of `make check`)".
3. `CLAUDE.md`, "Required Tools":
   - The code block becomes two lines: `make bootstrap # Installs tfenv and Terraform from .terraform-version, tflint, trivy, python@3.13, drawio` and `make deps      # Creates src/api/.venv and installs the API and web dependencies`.
   - Delete the sentence "The `Makefile` is still empty: the `bootstrap` and `check` targets are added by the first story (US01)."
4. `CLAUDE.md`, the directory tree line for `tests/`: `# QA-owned tests: api/, infra/, web/, image/, dev01/ (layout in AGENTS.md)`.

## 3. Order of work

T1, T2, T3, T4, T5. This differs from the default DB, BE, FE, Infra on purpose (US01a-D1): every later task is checked with `make deps` and `make check`, so the tooling of T1 comes first. There is no `[DB]` task.

Run `make deps` once after T2 and T4 have created `pyproject.toml` and `package.json`, then `make check` until it passes.

Proposed commits, one per task, in this order:

| Task | Type and summary |
| --- | --- |
| T1 | `chore(US01a): add make bootstrap, deps and check with tool pins` |
| T2 | `feat(US01a): add FastAPI skeleton with health and status endpoints` |
| T3 | `infra(US01a): add multi-stage non-root API Dockerfile` |
| T4 | `feat(US01a): add Vite React web skeleton with API client` |
| T5 | `docs(US01a): document make deps and the image test folder` |

## 4. Traceability

| Criterion | Tasks | Test location (QA) | Where it runs |
| --- | --- | --- | --- |
| CNT-AC01 multi-stage, final stage `python:3.13-slim` | T3 | `tests/infra/` (Dockerfile text: two or more `FROM`, last `FROM python:3.13-slim`, optionally `AS <name>`); `tests/image/` (the built image's root layers start with the layers of `python:3.13-slim`) | `make check`; `tests/image` in QA's test round |
| CNT-AC02 non-root user | T3 | `tests/infra/` (the last `USER` is `10001:10001`, after the last `FROM`, not `root` or `0`); `tests/image/` (`Config.User` is `10001:10001`; `docker run --rm --entrypoint id <image> -u` prints `10001`) | same. The ECS test point ("the task definition does not override the user") is US01c's, in `tests/infra` and `tests/dev01` |

CNT-AC01 and CNT-AC02 are also "checked in" US06 for every image the CD run builds (backlog). The US05 plan (PR image build) and the US06 plan (CD image build) keep both checked for each image they build, reusing these checks or equivalent workflow steps.
| Enablers (no US01a criterion): F-SYS-01, F-SYS-02, the error format, settings, clock, `make check` | T1, T2, T4 | `tests/api/` for the contracts in section 7. These tests are **not** named after any criterion (not CNT-AC03, not an SCH criterion): they are named by function ID (`test_f_sys_01_...`, `test_f_sys_02_...`) or by decision ID (`test_us01a_d9_...`), and the test report lists them as enablers. The stories that own CNT-AC03 (US01c) and the SCH criteria (US30, US31) write their own criterion tests | `make check` |

## 5. Files to create or change (complete list)

| File | Task | New or changed |
| --- | --- | --- |
| `Makefile` | T1 | changed (empty file today) |
| `.terraform-version` | T1 | changed (empty today) |
| `.tflint.hcl` | T1 | changed (empty today) |
| `.gitignore` | T1 | changed (lines appended) |
| `src/api/pyproject.toml` | T2 | new |
| `src/api/app/__init__.py`, `main.py`, `settings.py`, `db.py`, `clock.py`, `errors.py` | T2 | new |
| `src/api/app/routers/__init__.py`, `routers/system.py` | T2 | new |
| `src/api/app/schemas/__init__.py`, `schemas/errors.py`, `schemas/system.py` | T2 | new |
| `src/api/app/services/__init__.py`, `services/system.py` | T2 | new |
| `src/api/Dockerfile`, `src/api/.dockerignore` | T3 | new |
| `src/web/package.json`, `package-lock.json`, `index.html`, `vite.config.ts`, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `eslint.config.js`, `.prettierignore` | T4 | new |
| `src/web/src/main.tsx`, `App.tsx`, `api/client.ts`, `i18n/index.ts`, `i18n/en.json`, `i18n/vi.json`, `screens/ClosedScreen.tsx` | T4 | new |
| `AGENTS.md`, `CLAUDE.md` | T5 | changed (only the lines in T5) |
| `tests/api/**`, `tests/infra/**`, `tests/image/**` | T0 | new, QA's commits only |

Nothing else. Git-ignored output (`.venv/`, `node_modules/`, `dist/`, `.cache/`, caches) is not committed.

## 6. Interfaces later stories rely on (fixed now)

| Interface | Value | Used by |
| --- | --- | --- |
| App factory | `app.main.create_app(settings: Settings \| None = None, *, engine: Engine \| None = None, clock: Clock \| None = None) -> FastAPI`; started as `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000` | QA, US01c (task command), US04 (compose), US06, US08 to US41 |
| Settings | `app.settings.Settings`, prefix `CMS_`, the fields in T2; secrets `SecretStr` without default | US01c and US07 (ECS environment and `secrets`), US04 (compose), US08, US09 |
| Engine | `app.db.create_db_engine(settings)`, `app.db.get_engine` dependency, `app.state.engine` | US08 (session dependency built on it) |
| Clock | `app.clock.Clock` (`now() -> datetime`, aware UTC), `SystemClock`, `get_clock` dependency, `app.state.clock`; injection through `create_app(clock=...)` | US08 to US24 (timers, D-PM3) |
| Errors | `app.errors.DomainError(status_code, code, *, field=None, params=None)`; body `{"errors": [{"field", "code", "params"}]}`; codes `SYSTEM_NOT_READY` (503), `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `INTERNAL_ERROR`, validation codes = pydantic type in upper case | Every API story; the web `errors.<CODE>` keys (US08 on) |
| Paths | `GET /healthz`, `GET /api/healthz` -> 200 `{"status": "ok"}`; `GET /api/v1/status` -> 200 `{"status": "open"}` or 503 `SYSTEM_NOT_READY` | US01c (ALB health check, CNT-AC03), US06 (smoke test), US08 (`setup_required` added), US31 |
| Container | `src/api/Dockerfile`, context `src/api`, user `10001:10001`, port 8000, workdir `/app`; the checks in `tests/image/` | US01c, US05 (image scan), US06, US08 (migrations copied into `/app`). The US05 and US06 plans keep CNT-AC01 and CNT-AC02 checked for every image they build |
| Make targets | `bootstrap`, `deps`, `check`, `check-api`, `check-web`, `check-terraform`; venv `src/api/.venv` | Every Dev and lens; US05 (`api_test.yml` and `web_build.yml` mirror `check-api` and `check-web`) |
| Web API client | `src/web/src/api/client.ts`: `apiRequest`, `ApiError`, `SystemClosedError`, `onSystemClosed`, `getStatus`; header `X-CMS-Request: 1` on state-changing requests | US08 to US31; US09 enforces the header in the API, and the US09 plan writes the header name into spec BD-6 and the D-DL2 row, so this plan is not its only record |
| Web catalogues | `src/web/src/i18n/en.json` and `vi.json`, nested keys `<area>.<element>` | US08 on; US19 adds the switch |

## 7. For QA

Answers to the points QA asked to fix before writing tests.

1. **App factory import path.** `from app.main import create_app`. There is no module-level app. Use `with TestClient(create_app(settings, engine=..., clock=...)) as client:`, so the lifespan runs and the engine is disposed. Always pass `settings`: without it, `create_app` reads the `CMS_` environment variables and fails when `CMS_DB_PASSWORD` is not set.
2. **testpaths and pythonpath.** In `src/api/pyproject.toml`:
   - `testpaths = ["../../tests/api", "../../tests/infra"]`, `pythonpath = ["."]` and `addopts = ["--import-mode=importlib", "--strict-markers", "-ra"]`;
   - pytest runs from `src/api`, so rootdir is `src/api` (`make check`, or `cd src/api && .venv/bin/pytest`);
   - `import app` resolves to `src/api/app`.

   With `importlib` mode, test files in different folders may share a basename (both can have `test_system.py`) and no `__init__.py` is needed. Share helpers through `conftest.py` fixtures, not by importing one test module from another. This was checked with pytest 9.2.0 in the scratchpad: both folders were collected, a `conftest.py` fixture was found, and `import app` worked.

   Run the `tests/image/` and `tests/dev01/` folders by explicit path from `src/api`, for example `cd src/api && .venv/bin/pytest ../../tests/image`. Tests in `tests/infra/` find the repository root with `Path(__file__).resolve().parents[2]`. Use only the standard library and pytest there: no new dependency for parsing.
3. **`CMS_` settings names.** `CMS_DB_HOST`, `CMS_DB_PORT`, `CMS_DB_NAME`, `CMS_DB_USER`, `CMS_DB_PASSWORD` (required), `CMS_DB_SSLMODE`, `CMS_LOG_LEVEL`. The table in T2 gives the field names and defaults. Build them in tests as `Settings(db_password=SecretStr("<mock value>"), db_host=..., db_port=...)`; keyword arguments take precedence over the environment. Use an obviously fake password; it is not a secret.
4. **Contracts.**

   | Request | Condition | Status | Body | Also |
   | --- | --- | --- | --- | --- |
   | `GET /healthz` | always, also with the database unreachable | 200 | `{"status": "ok"}` | JSON; no `Set-Cookie`; no database access |
   | `GET /api/healthz` | same | 200 | `{"status": "ok"}` | same |
   | `GET /api/v1/status` | `SELECT 1` succeeds | 200 | `{"status": "open"}` | no `Set-Cookie`. US08 adds `setup_required`, so assert `body["status"] == "open"`, not the whole body |
   | `GET /api/v1/status` | the database cannot be reached or the query fails | 503 | `{"errors": [{"field": null, "code": "SYSTEM_NOT_READY", "params": {}}]}` | no employee, account or configuration data, no password, host or exception text. Answers within about 3 seconds (connect timeout) |
   | any unknown path, for example `GET /api/v1/nothing` | | 404 | `{"errors": [{"field": null, "code": "NOT_FOUND", "params": {}}]}` | |
   | `POST /healthz` | | 405 | code `METHOD_NOT_ALLOWED` | |
   | `GET /docs`, `/redoc`, `/openapi.json` | | 404 | code `NOT_FOUND` | API documentation is off (US01a-D8) |

   - **Test names.** None of these contracts is a US01a criterion. Name the tests by function ID (`test_f_sys_01_status_503_when_database_unreachable`, `test_f_sys_02_healthz_without_database`) or by decision ID (`test_us01a_d8_docs_off`, `test_us01a_d9_unhandled_error_is_internal_error`), never by a criterion ID, and list them as enablers in the report.
   - **Logging.** `create_app` calls `logging.basicConfig(..., force=True)`, which replaces the root handlers, so pytest's `caplog` does not see the records. Check log content with `capsys` (the handler writes to `sys.stdout`), for example that the 503 path logs `database check failed: OperationalError` and no password or host.
   - **Error handlers without a route.** US01a has no route that raises a `DomainError`, a validation error or an unhandled exception. Add test-only routes in your tests to the app that `create_app` returns (for example `app.add_api_route("/test/boom", raise_runtime_error)`), before creating the `TestClient`. The Dev does not add such routes to `src/`.
5. **Database for `tests/api` in US01a.** No PostgreSQL is needed in this story.
   - 200 case: pass a reachable engine, `create_app(settings, engine=sqlalchemy.create_engine("sqlite+pysqlite:///:memory:"))`. The real `SELECT 1` runs on SQLite, from the standard library.
   - 503 case: use the real psycopg path to a port where nothing listens. Pass `Settings(db_password=SecretStr("x"), db_host="127.0.0.1", db_port=9)` and no engine. The connection is refused at once.
   - From US04 on, `compose.yaml` provides PostgreSQL on `localhost:5432` for `tests/api` (needed from US08, the first table). From US05 on, `api_test.yml` provides it as a service. PROC12 confirmed that the Codex sandbox reaches `localhost:5432`.
6. **Injectable clock.**
   - The fixed injection point is the factory argument `create_app(..., clock=<your clock>)`. It sets `app.state.clock`, and routes read it through the dependency `app.clock.get_clock`.
   - Your clock implements the `app.clock.Clock` protocol: `now() -> datetime`, timezone-aware UTC.
   - Proposed fixture: `controlled_clock` in `tests/api/conftest.py`, with `now()` and `advance(delta: timedelta)`. The fixture is QA's code; only the protocol and the injection point are fixed here.
   - `app.dependency_overrides[get_clock]` also works, but use the factory argument so every test injects the clock the same way.
   - No US01a criterion needs the clock. It is fixed now for US08 to US24.
7. **Image tests (`tests/image/`, new folder, US01a-D4).**
   - Command in the story run's test round, after `make check`: `cd <worktree>/src/api && .venv/bin/pytest ../../tests/image`. The test report records it with its result.
   - Order inside the tests: `docker pull python:3.13-slim`, then `docker build -t <your tag> -f src/api/Dockerfile src/api` (repository root as working directory), then the checks, then `docker image rm <your tag>` in a fixture teardown so no test image is left behind.
   - CNT-AC01: `docker image inspect --format '{{json .RootFS.Layers}}'` on the built image and on `python:3.13-slim`; the base layers must be a prefix of the image's layers.
   - CNT-AC02: `docker image inspect --format '{{.Config.User}}'` gives `10001:10001`, and `docker run --rm --entrypoint id <image> -u` prints `10001`.
   - When Docker is not running, these tests fail; they never skip. The report then says Docker was down.
   - Later images: the US05 and US06 plans keep CNT-AC01 and CNT-AC02 checked for every image they build (section 4).
8. **Codex sandbox.**
   - `make check` needs no network except `tflint --init` and writes only inside the worktree: `.venv`, `node_modules`, `dist`, `.cache/` and the tool caches.
   - `make deps` needs the package registries, which the story-run Dev command allows (PROC12).
   - Run the tests on the Owner's machine with Python 3.13, not 3.14.

## 8. New dependencies and pins (KO-10)

All new, so the approver escalates (KO-10, approver "Dependencies"). Versions were checked on PyPI and the npm registry on 2026-11-02.

| Kind | Name and pin | Why |
| --- | --- | --- |
| Python runtime | `fastapi==0.162.0`, `uvicorn==0.54.0`, `sqlalchemy==2.1.6`, `psycopg[binary]==3.3.6`, `pydantic==2.14.2`, `pydantic-settings==2.16.2` | Stack in `CLAUDE.md`; `psycopg[binary]` brings libpq, so the slim image needs no system package (cp313 wheels exist for manylinux x86_64 and macOS arm64) |
| Python dev | `ruff==0.17.3`, `mypy==2.4.1`, `pytest==9.2.0`, `httpx==0.28.1` | Check command; `httpx` is required by FastAPI's `TestClient` |
| Python build | `setuptools==84.2.1` (`[build-system]`) | Builds the package for `pip install -e` and the image |
| npm runtime | `react` 19.3.1, `react-dom` 19.3.1, `i18next` 26.7.1, `react-i18next` 17.1.11 | Stack; i18n required by the no-hard-coded-text rule (US01a-D11) |
| npm dev | `vite` 8.3.5, `@vitejs/plugin-react` 6.1.2, `typescript` 6.0.3, `@types/react` 19.3.0, `@types/react-dom` 19.3.0, `eslint` 10.14.0, `@eslint/js` 10.0.1, `typescript-eslint` 8.72.1, `eslint-plugin-react-hooks` 7.1.1, `globals` 17.14.0, `prettier` 3.9.10 | Build, type check, lint (KO-14) |
| Base image | `python:3.13-slim` (tag, KO-11) | CNT-AC01 |
| tflint plugin | `tflint-ruleset-aws` 0.50.0 | AWS rules for every later Terraform story |
| Local tools | `python@3.13` (Homebrew) added to `make bootstrap`; Terraform 1.16.4 through `tfenv` | Python 3.13 is the stack; the machine has only 3.14 today |

Transitive packages stay unpinned (KO-10, accepted risk).

## 9. What the approver will escalate, and why

The run ends in `needs-human`, and the Owner decides G5. Expected triggers:

| Approver item | Trigger |
| --- | --- |
| Dependencies | Every package in section 8, the base image and the tflint plugin |
| Governance | `AGENTS.md` and `CLAUDE.md` (T5) |
| Pipeline | Not triggered: no workflow changes. The `Makefile` is what US05's CI will mirror, which the Owner sees at US05 |

What the Owner checks at G5:
- the pins in section 8;
- the T5 wording;
- the QA report for `tests/image`.

## 10. Owner actions

Before `/story US01a`:
1. Install Python 3.13: `brew install python@3.13`. This is what `make bootstrap` will do; the Makefile does not exist yet. Terraform 1.16.4 is already installed through `tfenv` (checked), and tflint, trivy and drawio are installed.
2. Keep Docker Desktop running during the run, for QA's `tests/image` in the test round.
3. The usual prerequisites:
   - G4 for US01a in `docs/gates/G4.md`;
   - the branch, created by the Dev Lead;
   - QA's `test(US01a)` commit, after you review its diff;
   - the summaries `reports/handoff/US01a-po-summary.md`, `US01a-dev-lead-summary.md` and `US01a-qa-summary.md`.

After the merge: none. US01a creates no AWS resource and needs no dev01 session; CNT-AC02's ECS test point is checked in Session 1 with US01c.

## 11. Verified at plan time (2026-11-02)

| Item | Result |
| --- | --- |
| Terraform 1.16.4 exists | `releases.hashicorp.com/terraform/1.16.4/` answers 200 (current release 1.17.1; the pin follows Q-O36). `tfenv list` shows 1.16.4 installed locally |
| tflint and the AWS ruleset | tflint 0.64.0 installed (0.65.0 is the latest release); `tflint-ruleset-aws` 0.50.0 is the latest release and installed with `HOME` inside the directory; an empty tree passes; an undocumented variable fails with exit 2 |
| pytest layout | pytest 9.2.0 collects `../../tests/api` and `../../tests/infra` from rootdir `src/api`, with `importlib` mode, a shared basename and a conftest fixture (scratchpad run) |
| Python pins | All versions exist; each declares a `requires_python` that admits 3.13; FastAPI 0.162.0 needs `pydantic>=2.9.0`; `psycopg-binary` 3.3.6 has cp313 wheels for linux x86_64 and macOS arm64 |
| npm pins | Latest versions read from the registry; TypeScript 7.0.2 rejected by the `typescript-eslint` peer range, so 6.0.3; Vite 8.3.5 needs Node `^20.19.0 \|\| >=22.12.0` (local Node 24.13.0) |
| Python on the Owner's machine | Only Python 3.14.4; Homebrew offers `python@3.13` 3.13.18, not installed (Owner action 1) |
| Docker | Daemon 29.7.2 running locally; `python:3.13-slim` tag last updated 2026-10-28 |

Not verified, and how each is handled:
- Whether the Codex sandbox can reach the Docker socket: T3 asks the Dev to try, and `tests/image` runs in QA's round in any case.
- Whether the `tfenv` shim writes outside the worktree when it resolves 1.16.4: if `terraform fmt` fails in the sandbox for that reason, the Dev reports BLOCKED with the message, and the PM/SM raises it.
- Whether the `pydantic.mypy` plugin loads with mypy 2.4.1: US01a-D13 gives the fallback.

## 12. Risks

| Risk | Response |
| --- | --- |
| A newer package breaks a tool at install time (for example the eslint 10 plugin set) | The Dev pins the nearest working version, names it in the handoff, and the approver's dependency escalation shows it to the Owner |
| The status check hangs when the RDS endpoint drops packets instead of refusing | `connect_timeout` 3 s in `create_db_engine`; checked on dev01 in US01c and US31 |
| `make check` is slow because `tflint --recursive` walks `node_modules` | Accepted; it finds no `.tf` there. Revisit in the Sprint 1 retro if it is over a minute |

## 13. Decisions (Dev Lead tier, workflow section 8; the Owner can override any of them at G4)

| ID | Decision | Reason |
| --- | --- | --- |
| US01a-D1 | Order of work T1 (tooling), T2 (API), T3 (image), T4 (web), T5 (docs) instead of DB, BE, FE, Infra | Every task is checked with `make check`, so the tooling must exist first |
| US01a-D2 | A separate `make deps` target installs the API venv (`src/api/.venv`, Python 3.13, editable install with the `dev` extra) and runs `npm ci`; `make check` installs nothing and fails with a clear message when they are missing. `make bootstrap` also installs `python@3.13` | Keeps `check` free of network beyond `tflint --init` (`AGENTS.md`); the venv in the worktree is shared by the Dev, the lenses and QA in a story run |
| US01a-D3 | `.tflint.hcl` adds the `recommended` preset, `terraform_standard_module_structure` and the AWS ruleset 0.50.0 to the `CLAUDE.md` rules; `tflint` runs with `HOME="$(CURDIR)/.cache/home"` | Enforces the module file layout of `AGENTS.md`; PROC12-D2 sandbox workaround |
| US01a-D4 | New test folder `tests/image/` for checks of the built image that need Docker, run by QA by explicit path, outside `make check`. `AGENTS.md` and `CLAUDE.md` list it (T5) | CNT-AC01 and CNT-AC02 name checks on the built image; `tests/infra` must stay readable-files-only, and the sandbox may not reach Docker. Extends KO-9 without changing its four folders |
| US01a-D5 | pytest from `src/api` with `testpaths = ["../../tests/api", "../../tests/infra"]`, `pythonpath = ["."]`, `--import-mode=importlib`, `--strict-markers`, `-ra` | Settles KO-9's open point; `importlib` lets two test folders share file names |
| US01a-D6 | Settings are separate `CMS_DB_*` parts (host, port, name, user, password, sslmode) plus `CMS_LOG_LEVEL`. `CMS_DB_SSLMODE` defaults to `require`; the URL is built with `URL.create` | The password arrives alone through the ECS `secrets` field (Q-D13, SP1-D4), so a single URL setting would put it in a plain value. RDS forces TLS (`rds.force_ssl`), and the local compose sets `disable` (US04) |
| US01a-D7 | Status: 200 `{"status": "open"}` now, with `setup_required` added by US08; 503 with code `SYSTEM_NOT_READY` on any `DBAPIError`; database connect timeout 3 seconds | BD-6 "503 system not ready"; `setup_required` needs the `app_setup` table of US08; the UI must see 503 well before CloudFront's origin timeout |
| US01a-D8 | FastAPI's `/docs`, `/redoc` and `/openapi.json` are off | Only planned routes exist (RV-05); no API description is published through the origin |
| US01a-D9 | One error format for every error path from the start: domain errors, validation errors (code = pydantic type in upper case, field = location without its source), Starlette HTTP errors (`NOT_FOUND`, `METHOD_NOT_ALLOWED`, `HTTP_<status>`) and unhandled errors (`INTERNAL_ERROR`, logged with method and path only) | D-DL1: "the API never returns sentences", including framework errors |
| US01a-D10 | Clock: `Clock` protocol, `SystemClock`, injected through `create_app(clock=...)` and read through the `get_clock` dependency | D-PM3 needs one fixed injection point; the factory argument works the same in tests and in the app |
| US01a-D11 | `react-i18next` and the two catalogues are set up in US01a instead of US08; SCR-00's placeholder shows `closed.message` in both languages through `getFixedT` | `AGENTS.md` forbids hard-coded text, and the start page has text; SCH-AC04 shows both languages on one page |
| US01a-D12 | The custom header of D-DL2 is `X-CMS-Request: 1`, sent by the API client on every method other than GET from now on. The US09 plan writes the name into spec BD-6 and the D-DL2 row | Fixes the name before US09 enforces it; the client exists now; the spec, not only this plan, then records it |
| US01a-D13 | mypy runs with the `pydantic.mypy` plugin; if the plugin does not load with mypy 2.4.1, only the plugin line is removed and the handoff says so | Better typing of settings and schemas without risking a blocked story on a plugin incompatibility |
| US01a-D14 | TypeScript 6.0.3, not 7.x | `typescript-eslint` 8.72.1 supports TypeScript below 6.1 only |
| US01a-D15 | The image builds the package with setuptools in a builder stage (`pip install --prefix=/install .`), copies `/install` into `/usr/local`, creates user and group `cms` with ID 10001, uses workdir `/app` and has no `HEALTHCHECK` | `AGENTS.md` image rules; a named user avoids tools that fail without a passwd entry; the ALB, not Docker, checks health (CNT-AC03) |

## 14. Open questions (Owner tier)

None. Everything above is a routine design choice (workflow section 8). Installing Python 3.13 (section 10) is an Owner action, not a question.

## 15. G4 review changes (2026-11-02, PO and QA read-only review, DES03 revision round)

| # | From | Change | Why |
| --- | --- | --- | --- |
| 1 | QA | Enabler tests are named by function ID (`test_f_sys_01_...`, `test_f_sys_02_...`) or decision ID (`test_us01a_d<n>_...`), never by a criterion ID, and reported as enablers (sections 4 and 7) | A test named after CNT-AC03 or an SCH criterion would claim a criterion this story does not own |
| 2 | QA | Log content is checked with `capsys`, because `basicConfig(force=True)` removes `caplog`'s handler. Error-handler tests use test-only routes added by QA to the app that `create_app` returns; the Dev adds no such routes to `src/` (T2 boundary, section 7) | US01a has no route that raises; test scaffolding stays out of the product code |
| 3 | QA | `tests/image` accepted, with the exact test-round command, pull then build then layer comparison, fail (never skip) when Docker is down, and removal of the test image (section 7) | Makes the test round reproducible and leaves the machine clean |
| 4 | PO | The US09 plan writes `X-CMS-Request` into spec BD-6 and D-DL2 (sections 6 and 13). The US05 and US06 plans keep CNT-AC01 and CNT-AC02 checked for every image they build (sections 4 and 6) | The spec must record an interface, not only a plan; the backlog's "Also checked in" for CNT-AC01 and CNT-AC02 names US06 |
