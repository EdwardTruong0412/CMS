# Global rules for every agent

These rules apply to the main session and every agent: PM/Scrum Master, Product Owner, Dev Lead, QA and the Codex Devs. This file is the source; `AGENTS.md` carries the same rules for Codex, which does not read `.claude/rules/`. Change both together.

## Approval

1. **The Owner (the user) is the only approver** at every gate G1-G7. Agents do and propose; they never approve.
   Why: an agent approving its own work removes the one human check this process relies on.
2. **No action before the Owner approves it.** Before starting a task, state what you plan to do (goal, files to write, commands to run) and wait for the Owner's approval. Before approval you may only read files. Do not write or edit files, create branches or worktrees, commit, push, run Terraform or AWS commands, or start other agents.
   Why: the Owner sees every change before it happens, not after.
   How: a subagent cannot pause mid-run to ask, so the coordinator gets the Owner's approval of the plan before it starts each agent, and the agent then does only what was approved.
3. **No commit without the Owner's review.** Before any `git commit`, show the Owner the staged diff (`git diff --staged --stat` plus the diff) and the full commit message. Commit only after the Owner approves. Every commit message follows `.gitmessage` at the repo root.
   Why: git history is the audit trail; each commit records what the Owner saw and approved.

### Story runs (Owner decision, 2026-11-01)

A story run (`/story <story>`, `.claude/skills/story/SKILL.md`) is the one exception to rules 1 to 3:

- **Rule 1:** the `approver` agent may approve the story's merge into `develop` (gate G5) when nothing on its escalation list applies. Everything it escalates comes to the Owner, and the Owner still approves every other gate, including G6 for every merged story.
- **Rule 2:** the Owner typing `/story <story>` approves the whole run as the skill describes it: worktree, Dev rounds, reviews, tests, commits, pushing the story branch, the PR and its merge. Nothing outside the skill is approved by it. Deployment is never part of a run; the Owner runs CD by hand.
- **Rule 3:** inside a run, the coordinator commits the Dev's proposed commits on the story branch without a separate Owner review; the review lenses and the approver review them instead. Messages still follow `.gitmessage`. All other commits need the Owner's review.

## Branches

4. **One branch per feature, created before implementation.** Before any implementation work for a story (tests or code), the Dev Lead creates `feature/<story>_<summary>` from `develop`, for example `feature/US01_user_list`. QA's tests and the Dev's code both go on that branch. Process, design and fix work uses the same form with its own ID (`feature/PROC06_kickoff`). Never implement on `develop` or `main`. Branching details: `docs/kickoff.md`.
   Why: each feature stays isolated, reviewable as one PR, and easy to drop.

## Coordination

5. **Summaries before implementation.** Before the coordinator (PM/Scrum Master) lets the Dev Lead start a Dev, every agent that worked on the story (Product Owner, Dev Lead, QA) writes `reports/handoff/<story>-<role>-summary.md`: what was done, files produced, decisions made, open questions. The PM/Scrum Master collects them, gives the Owner one summary, and starts implementation only after the Owner approves.
   Why: the Owner and the Dev start from the same, complete picture of the story.
6. **Hand off only through files** (`docs/`, `reports/handoff/`), never by message.
   Why: content passed from agent to agent in messages degrades at every hop; a committed file does not.

## Scope and safety

7. **Use only mock data** in `testdata/mock/`. Never read `.env` or secrets.
8. **Work only inside the approved baseline.** A request outside it becomes a Change Request.
9. **When something is ambiguous or irreversible, stop and write an open question.** Do not guess.
