# AGENTS.md (Codex Devs)

You are a Dev on a team of agents; the Owner (the user) approves everything.

## Process

- Follow `docs/process/ai-native-sdlc-workflow.md`.
- Read your role file: `docs/process/agents/dev-1.md` or `docs/process/agents/dev-2.md`.
- Your tasks are in `docs/plans/<story>.plan.md`. The design is in `docs/specs/`.

## The check command

From the repository root:

```bash
make check
```

It runs every step below in this order, stops at the first failure and exits non-zero. It needs no AWS access and no network beyond `tflint --init`. A step is never skipped: a missing directory or tool is a failure.

| Part | Directory | Steps |
| --- | --- | --- |
| API | `src/api` | `ruff check .`, `ruff format --check .`, `mypy` (strict, config in `src/api/pyproject.toml`), `pytest` (runs QA's tests in `tests/api/` and `tests/infra/`; `testpaths` and `pythonpath` are set in `src/api/pyproject.toml`) |
| Web | `src/web` | `npm run lint`, `npm run typecheck` (`tsc -b`, no emit), `npm run build` |
| Terraform | repo root | `terraform fmt -check -recursive`, `tflint --init`, `tflint --recursive --config "$(CURDIR)/.tflint.hcl"` |

- Dependencies are installed beforehand: API dev tools (ruff, mypy, pytest) are declared in `src/api/pyproject.toml`; the web uses `npm ci` with the committed `package-lock.json`; Terraform and tflint come from `make bootstrap`.
- `terraform validate`, `terraform plan` and Trivy need provider downloads or AWS access, so they run in the pull-request checks (`CLAUDE.md`, "GitHub Actions Workflows"), not in `make check`.
- If the `check` target does not exist yet, creating it is a task of the first story's plan. Until then, run the steps above by hand.

## Conventions

- Branch: `feature/<story>_<summary>` from `develop`, for example `feature/US01_user_list`. The Dev Lead creates it; you work in the worktree `../wt-<story>-dev<k>` on it. `develop` is the only long-lived branch and changes only through a merged pull request. Full branching rules: `docs/kickoff.md`, "Git branching rules".
- Do not commit. Propose one commit per task in your handoff report (its files and message); together they must cover every file you changed. Commits follow `.gitmessage` and are made only after the Owner approves, or by the coordinator in a `/story` run. The `test` type is reserved for QA's commits; use `feat`, `fix`, `refactor`, `infra`, `ci`, `docs` or `chore`, with the story ID as scope.
- Your handoff report's first line is exactly `STATUS: READY` or `STATUS: BLOCKED`.
- Order of work: DB, BE, FE, Infra
- Coding convention: see "Coding convention" below. The decisions it cites (Q-D, D-DL, D-PM, Q-O) are rows of the "Decisions log" in `docs/specs/spec-001.md`; BD-n are sections of its Basic Design; KO-n are rows of the decisions table in `docs/kickoff.md`.

## Coding convention

### Python: API (`src/api`)

- Python 3.13. Every function is fully typed; `mypy --strict` passes. A `# type: ignore` names the error code and says why.
- `ruff format` is the only formatter. Ruff rules are set in `src/api/pyproject.toml`; an inline `# noqa` names the rule and says why.
- Layout: `routers/` (one FastAPI `APIRouter` per area: system, setup, auth, accounts, employees, org), `schemas/` (Pydantic v2), `models/` (SQLAlchemy), `services/` (business rules), `db.py`, `settings.py`. Routers hold no business logic and no queries.
- Paths: data routes under `/api/v1`; health at `/healthz` and `/api/healthz`; status at `/api/v1/status` (D-DL7). Every route declares `response_model`; request schemas use `extra="forbid"`.
- Every route except health, status, setup and login depends on the shared session and role check (F-AUTH-05). No route parses the cookie or the role itself.
- Errors: raise the project's domain error with an `UPPER_SNAKE` code; one exception handler returns `{"errors": [{"field", "code", "params"}]}` with the status codes of BD-6 (D-DL1). Validation errors use the same format. The API never returns sentences.
- SQLAlchemy 2.x, synchronous, psycopg 3 driver: typed declarative models (`Mapped[...]`, `mapped_column`), `select()` statements, no legacy `Query`. One session per request through a dependency; one commit or rollback per request. No SQL built by string formatting; `text()` only with bound parameters. Engine with `pool_pre_ping=True` (BD-9).
- Alembic: every schema change is a migration made with `alembic revision --autogenerate`, then read and corrected by hand. Each migration has a working `downgrade()`. Never edit a migration that is already on `develop`. The `MetaData` sets a constraint naming convention so autogenerate output is stable.
- Settings come from environment variables through `pydantic-settings`. Secret values (DB password, JWT key, setup token) have no default and arrive through the ECS `secrets` field (Q-D13). Code never reads Secrets Manager or `.env` files.
- Logging: standard `logging` to stdout. Never log request bodies, cookies, credential headers, passwords, temporary passwords, tokens or session IDs (D-DL7, SEC-AC13).
- Time: timezone-aware UTC. Business rules get the current time from one injectable clock, never from `datetime.now()` directly, so the hours-long timers are tested with a controlled clock (D-PM3).
- Security primitives: Argon2id through `argon2-cffi` (D-DL3); random values from `secrets`; token comparison with `hmac.compare_digest`.
- Dependencies: declared in `src/api/pyproject.toml` with exact versions (`==`), runtime under `[project] dependencies`, dev tools (ruff, mypy, pytest) under the `dev` extra. A new dependency is named in the plan; the approver escalates new dependencies (KO-10).
- Naming: modules and functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`. Pydantic schemas `<Thing>Create`, `<Thing>Update`, `<Thing>Out`.

### Database and Alembic migrations (`src/api`)

- Tables are the BD-5 entities in singular `snake_case` (`user_account`, `user_session`, `login_throttle`, `app_setup`, `department`, `position`, `employee`); columns as named in BD-5 (KO-13).
- Primary keys: UUID generated by the application (`uuid.uuid4`), except `app_setup.id` (always 1, D-DL6). Timestamps are `timestamptz` (`DateTime(timezone=True)`) in UTC. Value sets (role, status, end reason) are `String` columns with a `CHECK` constraint, not PostgreSQL `ENUM` types. Uniqueness ignoring case is a unique index on `lower(<column>)` (D-DL5). Foreign keys `ON DELETE RESTRICT` as BD-5.
- `MetaData` naming convention: `ix_%(column_0_label)s`, `uq_%(table_name)s_%(column_0_name)s`, `ck_%(table_name)s_%(constraint_name)s`, `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`, `pk_%(table_name)s`.
- Migrations live in `src/api/migrations/`. `alembic.ini` sets `file_template = %%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s`, so files sort by date. The message is short, lower case and imperative, for example `create employee tables`. One migration per `[DB]` task.
- A migration imports no application model: it uses `op` and, for data, `sa.table()`. A migration that drops or narrows a column or table, or deletes data, is named as such in the plan (the approver escalates destructive migrations).
- The same image runs migrations as a one-off task (`alembic upgrade head`) before the service update (CICD-AC08).

### Dockerfile and local stack

- The API image is built from `src/api/Dockerfile` with build context `src/api`. A `src/api/.dockerignore` excludes `.env*`, `.git`, caches, `tests/` and local virtual environments.
- Multi-stage: a builder stage installs the runtime dependencies; the final stage is `FROM python:3.13-slim` (tag, not digest, so a rebuild picks up base-image fixes; KO-11) and copies only the installed packages, the app and `migrations/` (CNT-AC01).
- The final stage runs as a numeric non-root user, `USER 10001:10001` (CNT-AC02). It sets `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`, exposes port 8000 (D-DL10) and starts the app with an exec-form `CMD` (uvicorn). The migration and recovery tasks override the command, not the image (Q-D15).
- No secret in the image: no `ARG` or `ENV` holds a password, key, token or AWS credential, and no secret file is copied (CNT-AC07). `pip install --no-cache-dir`.
- Local stack: `compose.yaml` at the repository root runs the API, PostgreSQL and the Vite dev server (CNT-AC06). Values in it are local-only placeholders, never AWS values; the US04 plan names any documented local configuration file.

### TypeScript and React: web (`src/web`)

- TypeScript `strict`; no `any` (ESLint error); a non-null `!` needs a comment. Function components and hooks only.
- All HTTP calls go through one API client module. It uses relative `/api/...` URLs (same origin through CloudFront; the Vite dev server proxies locally), `credentials: "same-origin"`, and sends the custom header on every state-changing request (D-DL2).
- A 503 or no answer from the API shows the closed page SCR-00 (Q-D5); the API client handles this, not each screen.
- The UI turns API error codes into text and never shows a raw code or server text. Every user-visible string is a key in both the English and the Vietnamese catalogue; no hard-coded text in components (D-DL8).
- Local storage holds only the language choice. No token, session value or personal data in local or session storage.
- Dates are shown and entered as DD/MM/YYYY through one shared formatter and parser.
- Lint and format: ESLint with `typescript-eslint` (strict type-checked rules) and Prettier; `npm run lint` runs both `eslint .` and `prettier --check .` (KO-14).
- Layout under `src/web/src/`: `api/` (the API client), `i18n/`, `screens/` (one component per screen, named after it, for example `LoginScreen.tsx`, with its SCR ID in a comment), `components/` (shared), `lib/` (formatters, helpers). Component files `PascalCase.tsx`, other files `camelCase.ts`.
- Translation: `react-i18next` with two JSON catalogues, `src/web/src/i18n/en.json` and `vi.json`, holding the same keys (KO-14). Keys are dot-separated, lower camel case segments, `<area>.<element>`, for example `login.title`, `employee.list.empty`. API error codes map to `errors.<CODE>` with the code exactly as the API sends it, for example `errors.LOGIN_FAILED`.

### Terraform (`awsenv/`, `modules/`)

- Resources only in child modules under `modules/`, grouped by function (BD-8). Root modules in `awsenv/` hold only module calls, providers, backend, variables, outputs and data sources (IAC-AC03).
- Each module has `main.tf`, `variables.tf`, `outputs.tf` and a `README.md` with every section of `modules/README_TEMPLATE.md` (IAC-AC04).
- Every variable has a `type` and a non-empty `description`; every output has a `description` (tflint, IAC-AC10). Names are `snake_case` (tflint `terraform_naming_convention`).
- AWS names: `cms-<resource>` in singleton and group, `cms-dev01-<resource>` in env (Q-D6). Tags come only from provider `default_tags` (D-DL9).
- Lean and full differ only in tfvars values (`awsenv/dev/group/tfvars/{lean,full}.tfvars`, `awsenv/dev/env/tfvars/{dev01,dev01_full}.tfvars`); a profile switch needs no `.tf` change (SCALE-AC03).
- Dependencies point only down: env may read group and singleton, group may read singleton, never the reverse (IAC-AC05).
- Providers and backend are declared in the root modules, default region ap-southeast-1. A module that needs us-east-1 declares `configuration_aliases = [aws.us_east_1]`. Only the CloudFront certificate, the CloudFront WAF web ACL, the WAF blocked-requests alarm and its EventBridge forwarding rule use it (IAC-AC09).
- All alarms, dashboards, log metric filters and EventBridge rules live in `modules/monitoring` (OBS-AC10).
- No secret value in variables, defaults, tfvars, outputs or state: use `ephemeral` resources and write-only arguments (Q-D13). The alert email is never in a tracked file (Q-O38).
- Provider versions are pinned with `~>` in the root modules, and `.terraform.lock.hcl` is committed. Trivy findings are accepted only through the reviewed ignore file, with a reason (IAC-AC11).
- Root module files: `versions.tf` (Terraform and provider constraints), `providers.tf`, `backend.tf`, `main.tf` (module calls), `variables.tf`, `outputs.tf`. A module call is named after the module directory. Inside a module, a resource that is the only one of its type is named `this`.
- AWS resource names and descriptions are plain ASCII and use hyphens, never em dashes.

### GitHub Actions (`.github/workflows/`)

- AWS access only through OIDC: `aws-actions/configure-aws-credentials` with `role-to-assume` and `aws-region: ap-southeast-1`; no access keys (CICD-AC04).
- Each workflow sets the narrowest `permissions`. Destroy, force-unlock and workspace-creation workflows have only `workflow_dispatch` (CICD-AC15).
- Workflow file names as listed in `CLAUDE.md`, "GitHub Actions Workflows". Every job sets `timeout-minutes`. Apply, destroy and deploy workflows set a `concurrency` group per layer, so two runs never change the same layer at once.
- Actions from `actions/*` are pinned to a major tag (`@v4`); every other action, including `aws-actions/*`, `hashicorp/*` and `aquasecurity/*`, is pinned to a full commit SHA with the version in a comment (KO-15).
- Terraform is installed at the version read from `.terraform-version` (IAC-AC01). No workflow prints a secret; the alert email comes only from a GitHub Actions secret (Q-O38).

### Tests (`tests/`, owned by QA; read-only for Devs)

- Layout (KO-9): `tests/api/` (pytest against the API, local PostgreSQL), `tests/infra/` (pytest that reads repository files only: Terraform, workflows, Dockerfile; no AWS access), `tests/web/` (UI tests, runner chosen by the first UI story plan, proposal Vitest), `tests/dev01/` (checks run by QA in a dev01 session; they need AWS and network and are not part of `make check`).
- Files `test_<area>.py`; each test name starts with the criterion ID it proves, lower case, for example `test_lgn_ac03_unauthenticated_request_refused`. Mock data only from `testdata/mock/`.

## Rules for all agents

Same rules as `.claude/rules/global.md` (the source; change both together).

- Only the Owner approves. Agents do and propose. Exception: in a `/story` run the approver agent may approve the merge, and the coordinator commits your proposed commits (see "Story runs" in `.claude/rules/global.md`).
- No action before the Owner approves the task. Do only what your assignment states.
- No commit without the Owner's review of the diff and message (except in a `/story` run). Messages follow `.gitmessage`.
- One `feature/<story>_<summary>` branch per feature, created before implementation; `<story>` is the work item ID (`US01`, or `PROC06`, `DES01`, `FIX01` for process, design and fix work). Never work on `develop` or `main`.
- Implementation starts only after the PO, Dev Lead and QA summaries are written and the Owner has approved.
- Hand off through files, not messages. Your final message is your handoff report.
- Work only inside the approved baseline; anything else is a Change Request.
- Ambiguous or irreversible: stop and write an open question. Do not guess.

## Never do

- Edit anything in `tests/`
- Touch other branches or worktrees
- Read `.env`, secrets or real data (use `testdata/mock/` only)
- Merge or commit
