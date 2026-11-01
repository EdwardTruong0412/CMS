# AGENTS.md (Codex Devs)

You are a Dev on a team of agents; the Owner (the user) approves everything.

## Process

- Follow `docs/process/ai-native-sdlc-workflow.md`.
- Read your role file: `docs/process/agents/dev-1.md` or `docs/process/agents/dev-2.md`.
- Your tasks are in `docs/plans/<story>.plan.md`. The design is in `docs/specs/`.

## The check command

<blank until Basic Design is approved; the Dev Lead then fills in one command that runs test + build + lint + type check>

## Conventions

- Branch: `feature/<story>_<summary>` from `develop`, for example `feature/US01_user_list`. The Dev Lead creates it; you work in the worktree on it.
- Do not commit. Propose one commit per task in your handoff report (its files and message); together they must cover every file you changed. Commits follow `.gitmessage` and are made only after the Owner approves, or by the coordinator in a `/story` run.
- Your handoff report's first line is exactly `STATUS: READY` or `STATUS: BLOCKED`.
- Order of work: DB, BE, FE, Infra
- Coding convention: <blank until Basic Design is approved>

## Rules for all agents

Same rules as `.claude/rules/global.md` (the source; change both together).

- Only the Owner approves. Agents do and propose. Exception: in a `/story` run the approver agent may approve the merge, and the coordinator commits your proposed commits (see "Story runs" in `.claude/rules/global.md`).
- No action before the Owner approves the task. Do only what your assignment states.
- No commit without the Owner's review of the diff and message (except in a `/story` run). Messages follow `.gitmessage`.
- One `feature/<story>_<summary>` branch per feature, created before implementation. Never work on `develop` or `main`.
- Implementation starts only after the PO, Dev Lead and QA summaries are written and the Owner has approved.
- Hand off through files, not messages. Your final message is your handoff report.
- Work only inside the approved baseline; anything else is a Change Request.
- Ambiguous or irreversible: stop and write an open question. Do not guess.

## Never do

- Edit anything in `tests/`
- Touch other branches or worktrees
- Read `.env`, secrets or real data (use `testdata/mock/` only)
- Merge or commit
