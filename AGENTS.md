# AGENTS.md (Codex Devs)

You are a Dev on a team of agents; the Owner (the user) approves everything.

## Process

- Follow `docs/process/ai-native-sdlc-workflow.md`.
- Read your role file: `docs/process/agents/dev-1.md` or `docs/process/agents/dev-2.md`.
- Your tasks are in `docs/plans/<story>.plan.md`. The design is in `docs/specs/`.

## The check command

<blank until Basic Design is approved; the Dev Lead then fills in one command that runs test + build + lint + type check>

## Conventions

- Branch: `feat/<story>-<dev>`, for example `feat/US01-dev1`
- One commit per task from the plan
- Order of work: DB, BE, FE, Infra
- Coding convention: <blank until Basic Design is approved>

## Rules for all agents

- Only the Owner approves. Agents do and propose.
- Hand off through files, not messages. Your final message is your handoff report.
- Work only inside the approved baseline; anything else is a Change Request.
- Ambiguous or irreversible: stop and write an open question. Do not guess.

## Never do

- Edit anything in `tests/`
- Touch other branches or worktrees
- Read `.env`, secrets or real data (use `testdata/mock/` only)
- Merge
