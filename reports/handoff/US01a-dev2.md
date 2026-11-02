STATUS: READY

# Handoff: 2026-11-02 US01a - Dev 2, build round 1

Completed T1-T5 on `feature/US01a_repo_tooling_app_skeleton` in the assigned worktree. All changes are uncommitted. No files in `tests/` were edited, and no other branch or worktree was touched.

- T1: Implemented bootstrap, dependency installation and ordered API/web/Terraform checks; pinned Terraform and the tflint AWS plugin; appended generated-file ignores.
- T2: Added the typed FastAPI factory, CMS settings, database engine, injectable UTC clock, standard error handlers and the three health/status routes. Documentation endpoints are disabled; engine disposal runs at shutdown.
- T3: Added the multi-stage Python 3.13 slim image with runtime user `10001:10001` and the restricted build context. Static and built-image checks pass for CNT-AC01 and CNT-AC02. The ECS user override check remains with US01c.
- T4: Added Vite/React with strict TypeScript and lint, the shared API client, matching English/Vietnamese catalogues and the SCR-00 placeholder. API failures close the start page; state-changing calls send `X-CMS-Request: 1`.
- T5: Applied the specified AGENTS.md and CLAUDE.md updates and wrote this handoff.

## Proposed commits

One proposed commit per task, in plan order. The file lists below cover every changed or new tracked candidate, including this report. Approval metadata is to be supplied only when approval is granted.

### T1

Files:

- `Makefile`
- `.terraform-version`
- `.tflint.hcl`
- `.gitignore`

```text
chore(US01a): add make bootstrap, deps and check with tool pins

Why:
- Provide reproducible local checks without AWS access.

What:
- Add bootstrap, dependency setup, ordered checks, tool pins and ignores.

Refs: US01a, intent-001, G4
```

### T2

Files:

- `src/api/app/__init__.py`
- `src/api/app/clock.py`
- `src/api/app/db.py`
- `src/api/app/errors.py`
- `src/api/app/main.py`
- `src/api/app/routers/__init__.py`
- `src/api/app/routers/system.py`
- `src/api/app/schemas/__init__.py`
- `src/api/app/schemas/errors.py`
- `src/api/app/schemas/system.py`
- `src/api/app/services/__init__.py`
- `src/api/app/services/system.py`
- `src/api/app/settings.py`
- `src/api/pyproject.toml`

```text
feat(US01a): add FastAPI skeleton with health and status endpoints

Why:
- Establish the shared API contracts for later stories.

What:
- Add the app factory, settings, engine, clock, errors and system routes.

Refs: US01a, intent-001, G4
```

### T3

Files:

- `src/api/Dockerfile`
- `src/api/.dockerignore`

```text
infra(US01a): add multi-stage non-root API Dockerfile

Why:
- Deliver the CNT-AC01 and CNT-AC02 container requirements.

What:
- Build installed runtime packages on python:3.13-slim and run as UID 10001.

Refs: US01a, intent-001, G4
```

### T4

Files:

- `src/web/.prettierignore`
- `src/web/eslint.config.js`
- `src/web/index.html`
- `src/web/package-lock.json`
- `src/web/package.json`
- `src/web/src/App.tsx`
- `src/web/src/api/client.ts`
- `src/web/src/i18n/en.json`
- `src/web/src/i18n/index.ts`
- `src/web/src/i18n/vi.json`
- `src/web/src/main.tsx`
- `src/web/src/screens/ClosedScreen.tsx`
- `src/web/tsconfig.app.json`
- `src/web/tsconfig.json`
- `src/web/tsconfig.node.json`
- `src/web/vite.config.ts`

```text
feat(US01a): add Vite React web skeleton with API client

Why:
- Establish the typed web app and shared API client.

What:
- Add Vite, strict lint and types, bilingual catalogues and the closed page.

Refs: US01a, intent-001, G4
```

### T5

Files:

- `AGENTS.md`
- `CLAUDE.md`
- `reports/handoff/US01a-dev2.md`

```text
docs(US01a): document make deps and the image test folder

Why:
- Keep developer instructions aligned with the new tooling.

What:
- Document dependency setup, image tests and the build-round handoff.

Refs: US01a, intent-001, G4
```

## Check results

- `make deps`: PASS with Python 3.13.18 and the approved exact package pins; `npm ci` succeeded from the generated lockfile.
- `make check`: PASS, exit 0. Ruff lint and formatting passed; strict mypy with `pydantic.mypy` passed for 13 files; all 91 QA API/infra tests passed; web lint, typecheck and production build passed; Terraform formatting and tflint initialization/recursive lint passed.
- `BUILDX_CONFIG="$PWD/.cache/buildx" src/api/.venv/bin/python -m pytest -c src/api/pyproject.toml tests/image` from the repository root: PASS, 3 tests in 27.88 seconds. Proves base-layer inheritance, configured user and runtime UID. QA fixture removed its image.
- Manual image build: PASS using `BUILDX_CONFIG="$PWD/.cache/buildx" docker build -t cms-api:us01a -f src/api/Dockerfile src/api`. The initial plain command was blocked by a buildx activity write outside the worktree; relocating the buildx cache resolved it.
- `docker run --rm --entrypoint id cms-api:us01a -u`: output `10001`; configured user inspection: `10001:10001`. Removed the manually created image afterward.
- In-memory Node API-client smoke checks: PASS for GET/status, all four mutation methods and their headers/JSON bodies, 204, structured API errors, 503, rejected fetch and listener unsubscription. No test file was added or edited.
- `git diff --check`: PASS. `git diff --name-only -- tests`: empty.
- `make bootstrap` was implemented but not run: the required machine tools were already installed.

Health, status, settings, error, clock, tooling and web checks are enablers, not additional US01a acceptance criteria.

## Trade-offs and deviations

Kept the approved package pins and strict checks. The pydantic mypy plugin loads successfully and recognizes environment-provided settings, so the plan's anticipated `type: ignore[call-arg]` was unnecessary and caused an unused-ignore error. Removed that comment; retained the plugin and strict typing. Quoted the venv directory separately from the ruff executable so QA's textual Makefile checks recognize the command while paths remain safely quoted.

The UI and container remain within the skeleton scope: no tables, migrations, sessions, compose stack, Vite proxy, language switch or AWS resources were introduced.

## Open questions for the Owner

None blocking implementation.

## Risks and next steps

- npm audit reports 11 moderate findings, zero high/critical, in the development lint dependency chain through minimatch (GHSA-g3hv-75wg-m249). No automatic dependency changes were applied; review this with the already-planned dependency escalation at G5.
- Pytest emits a Starlette warning that its httpx TestClient integration is deprecated. Tests pass with the approved httpx pin; no extra dependency was added.
- Proceed to Dev Lead/lens review and QA's formal test round. G5 still requires the planned Owner review of new dependencies and governance-file edits.
