# REVIEW.md: code review criteria

The Dev Lead uses these criteria as the code lens in every `/story` round (`.claude/skills/story/SKILL.md`, "Review round N") and in any review outside a run (`docs/reviews/<story>-review.md`, `.claude/agents/dev-lead.md`, "Review"). They cover correctness, plan conformance, protection of the tests, conventions and maintainability. Security, infrastructure posture and UI quality belong to their own lenses (see "Other lenses"). Written for KO-16 (`docs/kickoff.md`). Definition of Done item 3 (`docs/project-plan.md`, section 3) depends on it.

Sources the criteria point to, never copied here: `AGENTS.md` ("The check command", "Coding convention"), `docs/specs/spec-001.md` (acceptance criteria, NFR, BD-5 to BD-9, Decisions log), `docs/plans/<story>.plan.md`, `.gitmessage`. When this file and one of them disagree, the source wins, and the Dev Lead reports the conflict to the PM/SM.

## How to review

1. Read the plan, the acceptance criteria it assigns, `round-<N>/handoff-dev.md`, `git log --oneline <base>..<branch>` and `git diff <base>...<branch>`. Read changed files in full where the diff is not enough.
2. From round 2 on, read your own `round-<N-1>/review-code.md` first (RV-06).
3. Run the checks under "Checks" in the worktree. Every Bash command starts with `cd <worktree> && `.
4. Go through RV-01 to RV-15. Only the items that apply to what the branch changed count. A Python-only story skips RV-10 and RV-11, for example.
5. Write the review file (see "Output").

The review is read-only. Never run a command that rewrites files: no `ruff format` without `--check`, no `ruff check --fix`, no `eslint --fix` or `prettier --write`, no `terraform fmt` without `-check`. After the review, `git status --porcelain` in the worktree must print nothing, the same as before. Never read `.env` or secrets.

## Severity and verdict

| Severity | Meaning | Goes in |
| --- | --- | --- |
| blocker | A check fails, `tests/` was changed outside QA's commits, a check was weakened, an assigned acceptance criterion is not met, data can be lost or corrupted, or a main path behaves wrongly | Findings |
| major | Breaks a written rule (spec, plan, `AGENTS.md` convention) that no check catches, a missing error path, a change outside the plan, a missing `downgrade()`, a missing README, or an earlier blocker or major that was not addressed | Findings |
| minor | Naming, wording, small duplication, a comment, or a preference with no rule behind it | Notes |

- **VERDICT: CHANGES** when Findings has at least one blocker or major, or any line under Checks reads `fail` or `not run`. One exception: `not run: no local database` on the migration round-trip line, when RV-09 was reviewed by reading.
- **VERDICT: PASS** otherwise. Minors alone never cause CHANGES.
- A problem the branch did not cause or make worse goes under Notes, not Findings.
- Every finding names its RV ID, a `file:line`, the problem and the fix you want, precisely enough that a Dev with no memory of the project can act on it. The code lens describes the fix and never makes it.

## Checks

Record each one under "Checks" as `pass`, `fail` or `not run: <reason>`.

| Check | Command (in the worktree) |
| --- | --- |
| Check command | `make check` from the repo root. Until US01 adds the target, run each step of `AGENTS.md`, "The check command", by hand and record each one |
| Tests untouched | `git log --oneline <base>..<branch> -- tests/` (see RV-02) |
| Whitespace | `git diff --check <base>...<branch>` |
| Migration round trip | Only when `src/api/migrations/` changed and a local PostgreSQL is running (`compose.yaml`): `alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head` from `src/api`. Without a database, record `not run: no local database` and review the migration by reading it (RV-09) |

A check that cannot run because the reviewer's machine lacks a tool or a dependency is recorded as `not run: <reason>`. That makes the verdict CHANGES, with a blocker finding that names the environment problem, because the code lens does not pass what it has not seen pass.

## Criteria

### Gate items

| ID | Check | PASS when | CHANGES when (severity) |
| --- | --- | --- | --- |
| RV-01 | The check command passes | Every step passes, none skipped | Any step fails or was not run (blocker) |
| RV-02 | QA's tests were not edited | `git log <base>..<branch> -- tests/` lists only QA's `test(<story>)` commits, made before the Dev's first commit, and no Dev commit touches `tests/` | Any other commit touches `tests/` (blocker) |
| RV-03 | No check was weakened | Changes to `src/api/pyproject.toml` (`[tool.pytest]` `testpaths`, `addopts`, markers; `[tool.ruff]`; `[tool.mypy]`), ESLint, Prettier, `tsconfig*.json`, `.tflint.hcl`, the Trivy ignore file and the `Makefile` `check` target are named in the plan | A skip, deselect, ignore, lowered strictness, removed step or new exclusion that the plan does not name. A `# type: ignore` or `# noqa` without the code and a reason, or an `eslint-disable` without a reason, counts too (blocker for config, major for inline) |

### Correctness and plan

| ID | Check | PASS when | CHANGES when (severity) |
| --- | --- | --- | --- |
| RV-04 | Every acceptance criterion and task the plan assigns is done | Each `[DB]`, `[BE]`, `[FE]`, `[Infra]` task has its change, and the handoff maps each criterion to files and evidence. Spot-check at least one criterion against the code | A task or criterion is missing or only partly done (blocker) |
| RV-05 | The change stays inside the plan | Every changed file is in the plan's "files to write" for a task, or the handoff gives a reason the plan already allows | Files, routes, tables, resources or features the plan does not name (major). A Decisions-tier choice made silently (major) |
| RV-06 | Earlier findings are addressed (round 2 on) | Every blocker and major in `round-<N-1>/review-code.md` is fixed, and the handoff lists each one with what was done | Any one not fixed or not listed: carry it over with its original severity |
| RV-07 | Behaviour matches the spec | Inputs, processing and outputs match BD-7 and `docs/specs/function-list.md`. Status codes and the error body match BD-6 (`{"errors": [{"field", "code", "params"}]}`, codes not sentences). Limits match the NFR measurable values (lengths, counts, timeouts, page size 20). Edge cases are handled: empty, duplicate ignoring case, not found, boundary values, a database that cannot be reached (503). One commit or rollback per request. Time comes from the injectable clock | A wrong result, status code or error code on any path (blocker on a main path, major on an edge path). A missing error path (major). `datetime.now()` in a business rule (major) |
| RV-08 | Handoff and proposed commits | First line `STATUS: READY`. One proposed commit per task, together covering every changed file. Messages follow `.gitmessage`, with a type from `feat`, `fix`, `refactor`, `infra`, `ci`, `docs`, `chore` (never `test`) and the story ID as scope. The commits on the branch match the handoff | A commit mixes tasks, uses the `test` type, or names files the handoff does not explain (major). A message format slip (minor) |

### Conventions (`AGENTS.md`, "Coding convention")

Check the rules that tooling cannot catch. Ruff, mypy, ESLint, tsc and tflint already enforce the rest through RV-01.

| ID | Area | PASS when (each break is major unless marked) |
| --- | --- | --- |
| RV-09 | Python API and Alembic | Layout `routers/`, `schemas/`, `models/`, `services/`; routers hold no logic and no queries. Every route declares `response_model`, request schemas use `extra="forbid"`, and paths follow D-DL7. Every route except health, status, setup and login uses the shared session and role dependency (F-AUTH-05). Errors are the domain error with an `UPPER_SNAKE` code. SQLAlchemy 2.x `select()` and `Mapped[...]`, no legacy `Query`. Settings come from `pydantic-settings`, with no default for secret values. Schema names follow `<Thing>Create`, `<Thing>Update`, `<Thing>Out`. Migrations: one per `[DB]` task, file name from `file_template`, no application model imported, a working `downgrade()` (blocker if missing or broken), constraint names from the naming convention, `String` plus `CHECK` instead of `ENUM`, case-insensitive uniqueness through `lower()` indexes, tables and columns as named in BD-5, no edit to a migration already on `develop` (blocker), and a destructive migration named as such in the plan (blocker if not) |
| RV-10 | TypeScript and React | All HTTP calls go through the one API client, with relative `/api/...` URLs, `credentials: "same-origin"` and the custom header on state-changing requests. 503 or no answer is handled in the client (SCR-00). No `any`, and a non-null `!` has a comment. Screens sit in `screens/` named after the screen with the SCR ID in a comment, and shared code in `components/` and `lib/`. Dates go through the shared DD/MM/YYYY formatter and parser. Every new key exists in both `en.json` and `vi.json`, and API codes map to `errors.<CODE>`. Text quality and translations themselves are the UI lens's |
| RV-11 | Terraform, Dockerfile, workflows (structure only) | Terraform: resources only in `modules/`, root files as listed in `AGENTS.md`, a module call named after its directory, a single resource of a type named `this`, `cms-` and `cms-dev01-` names, no tags outside `default_tags`, and each new module has `main.tf`, `variables.tf`, `outputs.tf` and a README with every section of `modules/README_TEMPLATE.md`. Lean and full differ only in tfvars. Dockerfile: path, build context, `.dockerignore`, stages and `CMD` as in `AGENTS.md`. Workflows: file names as in `CLAUDE.md`, `timeout-minutes` on every job, `concurrency` where required. Posture (IAM, network, encryption, pinning, scans, cost) is the infra lens's |

### Maintainability

| ID | Check | PASS when | CHANGES when (severity) |
| --- | --- | --- | --- |
| RV-12 | Readable and lean | Names follow the spec's terms (BD-5 entities, function IDs, SCR IDs). No dead or commented-out code, no debug output, no `TODO` without a story ID. No new abstraction, layer or generic helper the plan does not call for. An existing helper is reused, not copied | Unused code, a parallel copy of existing logic, or an unplanned framework layer (major). Small naming or structure issues (minor) |
| RV-13 | Dependencies | Each new or upgraded Python, npm or Terraform dependency is named in the plan. Python pins use `==` in `src/api/pyproject.toml` (runtime or `dev` extra), `package-lock.json` changes together with `package.json`, and providers use `~>` with `.terraform.lock.hcl` updated | A dependency the plan does not name, a loose pin, or a lock file out of step (major). The approver escalates new dependencies in any case |
| RV-14 | Docs touched by the story | Definition of Done item 6: the module README, the runbook and `CLAUDE.md` are updated where the change affects them, and the docs the plan lists are written | A new module without a README (major, IAC-AC04). Another doc the plan requires is missing (major). A small doc gap (minor) |
| RV-15 | Logging and errors in code | Logging uses `logging` to stdout. Exceptions are not swallowed silently. Internal errors reach the client only through the shared handler | A bare `except` that hides a failure, or a `print` (major). Anything about what a log contains (personal data, secrets) goes under Notes for the security lens |

## Other lenses

They run beside the code lens in the same round. Problems in their area go under Notes, with `file:line`, so the right lens can confirm them. The code lens does not hold back its own finding when the same line also breaks an RV item.

| Lens | File | Owns |
| --- | --- | --- |
| Security | `.claude/agents/reviewer-security.md` | Access control, input validation and injection, sessions and passwords, data exposure, secrets, personal data in logs, frontend storage and CORS |
| Infra | `.claude/agents/reviewer-infra.md` | Terraform fmt, validate, tflint, trivy and plan; layers, providers, network, IAM, encryption, monitoring placement, container posture, pipeline, cost, teardown |
| UI | `.claude/agents/reviewer-ui.md` (only when `src/web/` changed) | Fit with existing screens, flows and states, roles in the UI, translations, accessibility, phone width |
| Approver | `.claude/agents/approver.md` | The merge decision and the escalation list. The code lens does not escalate. It reports, and the approver decides |

## Output

In a story run, write only `<story folder>/round-<N>/review-code.md`, in the format of `.claude/agents/dev-lead.md`, "As the code lens of a story run":

```markdown
VERDICT: PASS | CHANGES

## Checks
make check: pass
tests untouched (git log <base>..<branch> -- tests/): pass, QA commits only: <hashes>
git diff --check: pass
migration round trip: not run: no migration in this change

## Findings
| # | Severity | File:line | Issue | Why it matters |
| --- | --- | --- | --- | --- |
| 1 | major | src/api/app/routers/employees.py:42 | RV-09: the router runs a `select()` itself; move it into `services/employees.py` | Routers hold no queries (AGENTS.md); the logic cannot be tested apart from HTTP |

## Notes
Minors (with RV ID), pre-existing issues, and items for the security, infra or UI lens.
```

- The first line is exactly `VERDICT: PASS` or `VERDICT: CHANGES`, with nothing before it.
- Findings holds only blockers and majors. Write "None." when there are none.
- Outside a story run, the same criteria apply. The file is `docs/reviews/<story>-review.md` in the format of `.claude/agents/dev-lead.md`, "Review".
