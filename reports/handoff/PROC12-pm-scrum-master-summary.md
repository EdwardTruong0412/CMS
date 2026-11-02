# Handoff: 2026-11-02 PROC12 - PM/SM summary (Codex network for story runs, follow-up wording)

| | |
| --- | --- |
| Task | PROC12, approved by the Owner on 2026-11-02 |
| Branch | `feature/PROC12_codex_network`, worktree `wt-PROC12`, from `develop` at `dda22ce` |
| Decision applied | OQ-S1-2 (Sprint 1 Planning, delegated to the PM/SM): allow network for the Codex Dev command |

## What changed

| File | Change |
| --- | --- |
| `.claude/skills/story/SKILL.md` | Dev command: `-c sandbox_workspace_write.network_access=true`, and `PIP_CACHE_DIR`, `npm_config_cache`, `TFLINT_PLUGIN_DIR` set to `<worktree>/.cache/...`. Code lens prompt names `REVIEW.md` |
| `.claude/agents/dev-lead.md` | Code lens applies RV-01 to RV-15 and the verdict rule of `REVIEW.md`; each finding starts with its RV ID |
| `.gitignore` | `/.cache/` |
| `docs/release-plan.md`, `docs/project-plan.md`, `docs/kickoff.md`, `CLAUDE.md` | "US01" references updated to US01a, US01b, US01c after BL-D10. Decision rows keep their original text with a note |
| `docs/templates/prd-template.md` | "$10 budget" changed to the $2 budget alert (Q-O57) |

## Sandbox check, re-run 2026-11-02

`codex-cli 0.166.0`, model `gpt-6.1-sol` (Owner's default, now accepted). Run in a new empty git directory under the session scratchpad with the new Dev command.

| Probe | Before (PROC11) | Now |
| --- | --- | --- |
| Cache variables visible inside Codex | - | yes, all three |
| `pip download requests==2.32.3` | fail (DNS) | pass |
| `npm view react version` | fail (DNS) | pass |
| `npm ci` (small lockfile) | not run | pass |
| `curl -sI https://github.com` | fail (exit 6) | pass, HTTP/2 200 |
| `tflint --init` (aws ruleset 0.38.0) | not run | **fail**: `mkdir /Users/truongquy/.sigstore: operation not permitted` (signature check cache) |
| `HOME=$PWD/.cache/home tflint --init` | - | pass |
| `localhost:5432` (`nc`, `pg_isready`) | not run | pass (a local PostgreSQL was running) |

`TUF_ROOT` is not honoured by tflint, so the signature cache cannot be moved with a variable.

## Input for the US01a plan (Dev Lead)

- `make check` should run `tflint --init` with `HOME` pointed inside the worktree (for example `HOME="$(CURDIR)/.cache/home" tflint --init`), so it passes inside the Codex sandbox without widening the sandbox to `~/.sigstore`. CI is unaffected.
- `tests/api` can reach a PostgreSQL on `localhost:5432` from inside the sandbox; the plan still says how `tests/api` gets its database (US04 compose, or the Owner's local server).

## Decisions

| ID | Decision | Reason |
| --- | --- | --- |
| PROC12-D1 | Caches inside the worktree through environment variables, not extra writable roots | Keeps the sandbox limited to the worktree; variables reach Codex's shell (checked) |
| PROC12-D2 | The tflint `HOME` workaround goes in the US01a `Makefile`, not in the skill | Only `tflint` needs it; changing `HOME` for Codex would break its login in `~/.codex` |
| PROC12-D3 | Decision rows (KO-9, KO-16, KO-17, RP-D4) keep their text, with a note about the split | They record what was decided at the time |

## Open questions

None.
