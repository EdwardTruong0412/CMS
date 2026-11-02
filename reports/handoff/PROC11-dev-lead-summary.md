# PROC11 Dev Lead summary: REVIEW.md and the Codex sandbox check

Date: 2026-11-02. Branch `feature/PROC11_review_md`, worktree `wt-PROC11`. Approved by the Owner on 2026-11-02 (PROC11 and the sandbox check). Nothing committed; the PM/SM shows the diff to the Owner.

## A. REVIEW.md (KO-16)

### What was done

Wrote `REVIEW.md` at the repo root: the criteria the code lens (Dev Lead) applies in every `/story` round and in reviews outside a run. It closes KO-16 and the dependency of Definition of Done item 3 on it.

Contents:

- **How to review:** what to read, the read-only rule (no fixer commands; `git status --porcelain` stays empty), and which items apply.
- **Severity and verdict:** blocker, major, minor with definitions. CHANGES if there is any blocker or major, or any check that reads `fail` or `not run`. Minors go under Notes and never cause CHANGES. Pre-existing problems go under Notes.
- **Checks:** `make check` (each step by hand until US01 adds the target), the `tests/` commit check, `git diff --check`, and an Alembic upgrade, downgrade, upgrade round trip when migrations changed and a local database exists.
- **Criteria RV-01 to RV-15**, each with what to check and what counts as PASS or CHANGES, with its severity:
  - Gate items: RV-01 check command, RV-02 tests untouched, RV-03 no weakened check.
  - Correctness and plan: RV-04 criteria and tasks done, RV-05 inside the plan, RV-06 earlier findings addressed, RV-07 behaviour matches BD-6, BD-7 and the NFR values, RV-08 handoff and proposed commits.
  - Conventions that tooling cannot catch: RV-09 Python and Alembic, RV-10 TypeScript and React, RV-11 the structure of Terraform, the Dockerfile and workflows.
  - Maintainability: RV-12 readable and lean, RV-13 dependencies, RV-14 docs (DoD item 6), RV-15 logging and errors.
- **Other lenses:** what security, infra, UI and the approver own, so the code lens puts their topics under Notes.
- **Output:** the `review-code.md` format of `.claude/agents/dev-lead.md`, with a worked example. The first line is exactly `VERDICT: PASS` or `VERDICT: CHANGES`, as `SKILL.md` "Review round N" step 3 requires.

### Decisions (Dev Lead, routine tier; the Owner can override them at the next gate)

| ID | Decision | Why |
| --- | --- | --- |
| RV-D1 | REVIEW.md points to `AGENTS.md`, the spec and the plan instead of copying rules; the source wins on conflict | KO-1: one source per rule, so the two cannot drift |
| RV-D2 | Findings holds only blockers and majors; minors go under Notes | Matches dev-lead.md ("Notes: minor issues") and keeps the CHANGES rule mechanical |
| RV-D3 | The finding's RV ID is written at the start of the Issue cell, not in an extra column | Keeps the table columns exactly as dev-lead.md defines them |
| RV-D4 | A check that cannot run on the reviewer's machine (`not run`) makes the verdict CHANGES, with a blocker that names the cause | The code lens does not pass what it has not seen pass. DoD item 2 needs `make check` to pass |
| RV-D5 | RV-03, a weakened check, is a blocker. This covers pytest `addopts`, deselects, `testpaths`, lint or type-check relaxations and ignore files the plan does not name | The Dev cannot edit `tests/`, but changing the pytest config in `src/api/pyproject.toml` skips the tests just as well. That is the gap left after R-09 |
| RV-D6 | The code lens checks the structure of infra code, and the infra lens checks its posture. Personal data and secrets in logs belong to the security lens | Avoids two lenses reporting the same finding. The split follows the lens files |
| RV-D7 | Migration round trip only when a local PostgreSQL is running. Otherwise review the migration by reading it, and record `not run: no local database` | A local PostgreSQL arrives with US04 and US08. Before then, a missing database must not block every round. Without the round trip, RV-09 still requires a working `downgrade()` |

RV-D4 and RV-D7 meet in the verdict rule: `not run` causes CHANGES, except `not run: no local database` on the migration round-trip line when RV-09 was reviewed by reading. REVIEW.md states this exception.

## B. Codex sandbox check (prerequisite 5, OQ-S1-2)

### Setup

- Codex: `codex-cli 0.157.1` at `/opt/homebrew/bin/codex`, `codex login status` reports "Logged in using ChatGPT".
- Directory: `/private/tmp/claude-501/-Users-truongquy-Documents-CMS/5a86055f-3c2d-4ac9-99e7-caec3dd174a0/scratchpad/sandbox-check`, new and empty, outside every repo worktree. I ran `git init` in it, because codex refuses a non-git directory ("Not inside a trusted directory and --skip-git-repo-check was not specified"). Story worktrees are git checkouts, so this matches the run, and the skill's flags stay unchanged.
- The skill's Dev flags (`SKILL.md`, "Build round N", step 2): `codex exec --sandbox workspace-write -o <file> "<prompt>"`.
- Codex config was not changed. `~/.codex/config.toml` has no `[sandbox_workspace_write]` section (only `model` and `model_reasoning_effort`), so the defaults apply. I did not read `auth.json`.

### First attempt: the skill's command as written fails before any probe

```bash
cd <sandbox-check> && codex exec --sandbox workspace-write -o <scratchpad>/sandbox-check-out.md "<probe prompt>" < /dev/null
```

Result: `ERROR ... "The 'gpt-6.1-sol' model is not supported when using Codex with a ChatGPT account." code model_not_found`. The default model in `~/.codex/config.toml` (`model = "gpt-6.1-sol"`) is not available to this account; the account's model list (`~/.codex/models_cache.json`) has `gpt-6-sol`, `gpt-6-astra`, `gpt-6-luna`, `gpt-5.6-*`. **The skill's Dev command would fail the same way at round 1 of every story run today.**

### Second attempt: the same flags, plus a one-off model override

```bash
cd /private/tmp/claude-501/-Users-truongquy-Documents-CMS/5a86055f-3c2d-4ac9-99e7-caec3dd174a0/scratchpad/sandbox-check && \
codex exec -m gpt-6-sol --sandbox workspace-write \
  -o /private/tmp/claude-501/-Users-truongquy-Documents-CMS/5a86055f-3c2d-4ac9-99e7-caec3dd174a0/scratchpad/sandbox-check-out.md \
  "This is a network reachability test. Run each of these three shell commands exactly ... (1) python3 -m pip download --no-deps -d ./dl requests==2.32.3 ; (2) npm view react version ; (3) curl -sI https://github.com ..." < /dev/null
```

Codex reported `sandbox: workspace-write [workdir, /tmp, $TMPDIR]`, `approval: never`.

| Probe | Exit | Result |
| --- | --- | --- |
| `python3 -m pip download --no-deps -d ./dl requests==2.32.3` | 1 | `NameResolutionError ... Failed to resolve 'pypi.org'`, five retries, then `No matching distribution found`. Also: `~/Library/Caches/pip` is not writable, so the cache is disabled |
| `npm view react version` | 1 | `getaddrinfo ENOTFOUND registry.npmjs.org`. Also: npm could not write its logs to `~/.npm/_logs` |
| `curl -sI https://github.com` | 6 | Could not resolve the host, no output |

Control outside codex, on the same machine at the same time: `curl -sI https://github.com` returned `HTTP/2 200`, and `npm view react version` returned `19.3.1`. The host has network access, so the codex `workspace-write` sandbox is what blocks it.

### Conclusion

**OQ-S1-2 applies.** Under `--sandbox workspace-write` with the default settings, Codex has no network access at all (DNS fails). The Dev therefore cannot run `pip install`, `npm ci` or `tflint --init`, which `make check` needs. Two more findings matter for the answer:

1. **Network alone may not be enough.** The sandbox also blocks writes to the home directory caches (`~/Library/Caches/pip`, `~/.npm`). `tflint --init` installs plugins under `~/.tflint.d` by default, which is outside the writable roots too. So with `sandbox_workspace_write.network_access=true`, npm and tflint may still fail. Fixes would be cache directories inside the worktree (for example `npm_config_cache`, `TFLINT_PLUGIN_DIR`, `PIP_CACHE_DIR`), extra `writable_roots`, or the Owner's alternative of pre-installing dependencies in each worktree. Whichever option is chosen, rerun these three probes plus `npm ci` and `tflint --init` in a scratch git repo before US01a.
2. **Local PostgreSQL was not tested.** I expect the sandbox to block loopback connections as well, but I have not verified this. It matters from the first story that runs `tests/api/` against a database (US04 and US08). Add a `localhost:5432` probe to the same rerun.
3. **Separate blocker, model config.** The default model in `~/.codex/config.toml` is rejected for this account. This is the Owner's local configuration, so I did not change it.

## Follow-ups for other files (not changed in this task)

| # | File | Change | Owner |
| --- | --- | --- | --- |
| F1 | - | Resolved in this task: the RV-D4 and RV-D7 exception is written into the REVIEW.md verdict rule | - |
| F2 | `.claude/agents/dev-lead.md`, "Review" and "As the code lens" | Name `REVIEW.md` as the criteria file. "Review" already does ("against `REVIEW.md`"). The code-lens paragraph should add: "Apply `REVIEW.md` (RV-01 to RV-15); start each finding's Issue with its RV ID". Optional: keep the format block there, or point to REVIEW.md "Output" | PM/SM governance task |
| F3 | `.claude/skills/story/SKILL.md`, "Review round N" step 2 | Optionally add `Criteria: REVIEW.md.` to the dev-lead prompt. Not required, because dev-lead.md already points there once F2 is done | PM/SM governance task |
| F4 | `.claude/skills/story/SKILL.md`, "Build round N" step 2 | Depending on the OQ-S1-2 answer: `-c sandbox_workspace_write.network_access=true`, plus cache or plugin directories inside the worktree, or a preflight item "dependencies installed in the worktree". Rerun the probes afterwards | Owner decides (OQ-S1-2), then PM/SM |
| F5 | `~/.codex/config.toml` (Owner's machine, not the repo) | `model = "gpt-6.1-sol"` is not available for the ChatGPT account. Recommended: set it to `gpt-6-sol` (available), or have the skill pass `-m`. I recommend the config, so the repo stays free of account-specific values | Owner |
| F6 | `docs/process/ai-native-sdlc-workflow.md` 10.1 lists `REVIEW.md` at the repo root | No change needed; the file is now there | - |
| F7 | `.claude/agents/approver.md` line 73, `.claude/agents/reviewer-infra.md` line 81 | "$10 budget" should be $2 (Q-O57), already listed in Sprint 1 planning prerequisite 4. REVIEW.md does not repeat the number | PM/SM governance task |

## Open questions for the Owner

- **OQ-S1-2 (now applies).** Allow network access for the Codex Dev command in story runs, or pre-install dependencies in each worktree? Recommended: allow network (`sandbox_workspace_write.network_access=true` in the skill's Dev command), plus cache and plugin directories inside the worktree so npm and tflint can write. Worktrees hold only mock data, and the `protect-tests` hook and the CI checks stay in force. Verify with the probes before US01a.
- **Codex model (F5).** Change `model` in your `~/.codex/config.toml` to a model your account supports (recommended `gpt-6-sol`). Until then every `/story` build round fails at start.

## Files

- `/Users/truongquy/Documents/wt-PROC11/REVIEW.md` (new)
- `/Users/truongquy/Documents/wt-PROC11/reports/handoff/PROC11-dev-lead-summary.md` (new, this file)
- Scratch only, not in the repo: `/private/tmp/claude-501/-Users-truongquy-Documents-CMS/5a86055f-3c2d-4ac9-99e7-caec3dd174a0/scratchpad/sandbox-check/` (git-initialised probe directory) and `/private/tmp/claude-501/-Users-truongquy-Documents-CMS/5a86055f-3c2d-4ac9-99e7-caec3dd174a0/scratchpad/sandbox-check-out.md` (codex's final message)
