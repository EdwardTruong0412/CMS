---
name: story
description: Run one user story through the automated build → review → test → approve → merge loop. Use when the Owner types /story <story>, /story approve <story> or /story rework <story> <note>. The session that runs it becomes the coordinator of the story run.
---

# Story run

You are the coordinator for one story run. You run the loop below, start every
agent, and are the only writer of the story's `story.json`. You never write
code, tests, reviews or decisions yourself. Agents do the work and each writes
one file; you move the story along, make the commits the Dev proposes, and keep
`story.json` current.

Adapted from the `software-factory-claude-code` template for this project's
process (`docs/process/ai-native-sdlc-workflow.md`, section 6.3).

## Where a run sits in the process

A run covers workflow section 6.3, steps 2 to 8: build, review, fix rounds,
full test suite, PR and merge. Everything before it stays as it is: G4
approval, the feature branch, QA's tests and the three summaries.

The Owner typing `/story <story>` is the Owner's approval to start
implementation (global rule 5) and approves the whole run as this file
describes it, including the commits, the push of the feature branch, the PR and
the merge into `develop` on `APPROVE` (global rules 1 to 3, "Story runs").
Nothing outside this file is approved by it. Deployment is not part of a run:
the Owner runs the CD pipeline by hand.

## The loop

```
preflight → Dev (Codex) → commit → [code, security, infra, ui?] → WAIT FOR ALL
                ▲                                                     │
                └──── any CHANGES or tests FAIL: next fix round ◄─────┤
                                                                      ▼ all PASS
                                          QA full suite ── FAIL ──────┘
                                                 │ PASS
                                                 ▼
               PR → checks → merge ◄─ APPROVE ─ approver ─ ESCALATE → needs-human
```

| Step    | Who                                        | Writes                                       |
| ------- | ------------------------------------------ | -------------------------------------------- |
| build   | Dev k (Codex, `codex exec`)                | `round-<N>/handoff-dev.md`, uncommitted code |
| commit  | you                                        | commits on the feature branch                |
| review  | `dev-lead` (code lens)                     | `round-<N>/review-code.md`                   |
|         | `reviewer-security`                        | `round-<N>/review-security.md`               |
|         | `reviewer-infra`                           | `round-<N>/review-infra.md`                  |
|         | `reviewer-ui` (only if `src/web/` changed) | `round-<N>/review-ui.md`                     |
| test    | `qa`                                       | `round-<N>/test-report.md`                   |
| approve | `approver`                                 | `decision.md`                                |
| merge   | you                                        | `pr-body.md`, the PR, the merge              |

`MAX_FIX_ROUNDS = 3`: after round 1 the Dev gets at most three fix rounds, so a
run has at most 4 rounds. A round fails when any review says
`VERDICT: CHANGES` or the test report says `RESULT: FAIL`.

## Files

`<repo>` is the main checkout (`git rev-parse --show-toplevel`). `<base>` is
`origin/develop`. `factory/stories/` is gitignored runtime state; the record is
committed with the story (see **Merge**).

```
<repo>/factory/dashboard.html                             the board (tracked)
<repo>/factory/stories/<story>/story.json                 the run's state (you write it)
<repo>/factory/stories/<story>/rework-<k>.md              written by you, from /story rework
<repo>/factory/stories/<story>/round-<N>/handoff-dev.md   the Dev's handoff (codex exec -o)
<repo>/factory/stories/<story>/round-<N>/review-{code,security,infra,ui}.md
<repo>/factory/stories/<story>/round-<N>/test-report.md
<repo>/factory/stories/<story>/decision.md
<repo>/factory/stories/<story>/pr-body.md
<parent of repo>/wt-<story>-dev<k>/                       the story's worktree
```

The worktree must be named `wt-<story>-dev<k>` next to the repo: the
`protect-tests.py` hook only protects `tests/` in worktrees with that prefix.

Your session stays in the main checkout and never changes its branch or files
outside `factory/stories/<story>/`. All git work for the story happens in the
worktree (`git -C <worktree> ...`).

### story.json

```json
{ "id": "US01", "title": "User list",
  "branch": "feature/US01_user_list", "base": "origin/develop",
  "worktree": "/Users/you/Documents/wt-US01-dev1", "dev": 1,
  "stage": "review", "round": 2, "fixes": 1,
  "reviews": { "code": "PASS", "security": "CHANGES", "infra": "pending", "ui": "skip" },
  "tests": "pending", "pr": null }
```

- `stage` is one of `build`, `review`, `test`, `approve`, `merging`, `merged`,
  `needs-human`. Preflight counts as `build`.
- `round` is the current round (0 until the first build starts). `fixes` is the
  number of fix rounds used since the run (or the last rework) started.
- `reviews` and `tests` hold the current round only: `pending`, `PASS`,
  `CHANGES` (`FAIL` for tests), or `skip` for `ui` when the story does not touch
  `src/web/`. Earlier rounds live in their `round-<N>/` folders, which the
  dashboard reads directly.
- `pr` is the PR number once it exists.
- Rewrite the whole file on every change. `worktree` is always an absolute path.

### Prompts

Every agent prompt starts with:
`Story: <story>. Story folder: <repo>/factory/stories/<story>/. Worktree: <worktree>. Branch: <branch>. Base: origin/develop.`
Below, `<paths>` stands for that sentence.

## /story <story>

1. **Preflight.** Run `git fetch origin` and check every item below. If any
   fails, stop and tell the Owner exactly which one; do not create anything.
   - `docs/plans/<story>.plan.md` exists, and `docs/gates/G4.md` shows
     `Owner approval: [x]` for this story.
   - Exactly one branch matches `feature/<story>_*` (local or on origin).
   - QA's tests are on it: `git log --oneline <base>..<branch> -- tests/` is
     not empty.
   - `reports/handoff/<story>-po-summary.md`, `<story>-dev-lead-summary.md` and
     `<story>-qa-summary.md` exist, in the main checkout or on the branch.
   - `AGENTS.md` has a real check command, not the "blank until" placeholder.
   - `factory/stories/<story>/` does not exist yet. If it does, the story
     already has a run: use `/story rework`, or ask the Owner.
2. **Create the run.** Read the Dev number `k` from the plan ("which Dev takes
   the story"; default 1). The worktree is `$(dirname <repo>)/wt-<story>-dev<k>`.
   `mkdir -p factory/stories/<story>` and write `story.json` with
   `stage: "build"`, `round: 0`, `fixes: 0`, all reviews `pending` and
   `tests: "pending"`.
3. **Worktree.** If the worktree does not exist, run
   `git worktree add <worktree> <branch>`. Check that
   `git -C <worktree> branch --show-current` prints the branch and
   `git -C <worktree> status --porcelain` prints nothing.
4. Go to **Build round 1**.

### Build round N

1. Set `stage: "build"`, `round: N`. `mkdir -p factory/stories/<story>/round-<N>`.
2. Start the Dev from the worktree with `run_in_background`, and wait for its
   completion notice (a build can outlast a foreground command):
   ```bash
   cd <worktree> && codex exec --sandbox workspace-write \
     -o <repo>/factory/stories/<story>/round-<N>/handoff-dev.md "<dev prompt>"
   ```
   The `<dev prompt>` for round 1:
   `You are Dev <k>. Read AGENTS.md and docs/process/agents/dev-<k>.md. Story <story>, build round 1. Your tasks are in docs/plans/<story>.plan.md. Do not edit anything in tests/. Run the check command from AGENTS.md until it passes. Do not commit: propose one commit per task, and together the proposed commits must cover every file you changed. Your final message is the handoff report; its first line must be exactly STATUS: READY or STATUS: BLOCKED.`
   For a fix round, append:
   `This is fix round <fixes>. Read every file in <repo>/factory/stories/<story>/round-<N-1>/. Address every finding in the files whose first line is VERDICT: CHANGES or RESULT: FAIL, and in the handoff list each finding and what you did about it.`
   For a rework, append instead:
   `This is a rework. Read <repo>/factory/stories/<story>/rework-<k>.md and address it. Earlier rounds are in <repo>/factory/stories/<story>/round-*/.`
   Each round is a fresh `codex exec`: the Dev's context comes from the files
   named in the prompt, not from an earlier session.
3. Read the first line of `round-<N>/handoff-dev.md`.
   - `STATUS: READY`: go to **Commit**.
   - `STATUS: BLOCKED`: go to **Needs human**.
   - Missing file or any other first line: go to **Needs human** and say so.

### Commit

1. In the worktree, list what changed: `git -C <worktree> status --porcelain`.
2. If anything under `tests/` changed, commit nothing and go to **Needs human**:
   the Dev may not edit QA's tests.
3. For each proposed commit in the handoff, in order, stage exactly its files
   (`git add -- <paths>`, never `git add -A`) and commit with its message.
   Messages follow `.gitmessage`; use `Approved-by: Owner (/story run, <date the run started>)`.
4. `git status --porcelain` must now print nothing. If files are left over, or
   a proposed commit names a file that did not change, go to **Needs human**
   and list them. Never commit a file the handoff does not name.
5. Go to **Review round N**.

### Review round N

1. Set `stage: "review"`, all reviews `pending`, `tests: "pending"`. Set `ui` to
   `skip` when `git -C <worktree> diff --name-only <base>...<branch> -- src/web/`
   prints nothing.
2. Start the active reviewers **in one message**, so they run in parallel. Each
   gets `<paths> Review round N.`; tell `dev-lead` also
   `You are the code lens of a story run: write only round-<N>/review-code.md in the story folder.`
3. **WAIT FOR ALL.** Each time a reviewer finishes, read the first line of its
   file and write the verdict to `story.json` straight away, so the dashboard
   fills in as verdicts land. The step is done only when every active
   reviewer's file exists in `round-<N>/`. Never start the next build
   mid-round. If a reviewer finishes without writing its file, or its first
   line is not `VERDICT: PASS` or `VERDICT: CHANGES`, stop and tell the Owner.
4. Any `CHANGES`: go to **Round failed**. All `PASS`: go to **Test round N**.

### Test round N

1. Set `stage: "test"`. Start `qa` with
   `<paths> Story run, round N: run the full suite in the worktree and write round-<N>/test-report.md in the story folder. Edit nothing else.`
2. Read the first line of `round-<N>/test-report.md` and set `tests`.
   - `RESULT: PASS`: go to **Approve**.
   - `RESULT: FAIL`: go to **Round failed**.
   - Missing file or any other first line: stop and tell the Owner.

### Round failed

- **Fix rounds left** (`fixes < 3`): increase `fixes`, then go to **Build
  round N+1**.
- **None left**: write `decision.md` yourself, reading `ESCALATE`, a blank
  line, then
  `Fix rounds exhausted. Outstanding findings in round-<N>/ from: <reviewers and/or tests>.`
  Go to **Needs human**.

### Approve

Set `stage: "approve"`. Start `approver` with `<paths> Final round: N.` When it
finishes, read the first line of `decision.md`:

- `APPROVE`: go to **Merge**.
- `ESCALATE`: go to **Needs human**.
- Anything else: stop and tell the Owner.

### Merge

The PR checks are the last automated gate before `develop`. Never force-push,
never pass `--admin`, never skip or re-run a check to get past it. Never push
`develop` or any branch other than this story's, and never start a deploy
workflow: the Owner runs CD by hand.

1. Set `stage: "merging"`.
2. **Record.** Copy every file in the story folder except `story.json` and
   `pr-body.md` to `<worktree>/reports/stories/<story>/`, keeping the round
   folders, and commit it on the branch as
   `docs(<story>): add story run record`, following `.gitmessage`.
3. **PR.** Write `pr-body.md`: the story and its intent, the acceptance criteria
   from `decision.md`, one line per round (verdicts and test result), the
   approver's "Why", and a link to `reports/stories/<story>/`. End it with
   `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Then:
   ```bash
   git -C <worktree> push -u origin <branch>
   gh pr create --base develop --head <branch> \
     --title "<type>(<story>): <story title>" --body-file <story folder>/pr-body.md
   ```
   Set `pr` to the PR number. If a PR for the branch already exists, update its
   body with `gh pr edit` instead.
4. **Checks.** Wait 30 seconds, then `gh pr checks <pr> --watch`. If it reports
   no checks, wait 30 seconds and try once more. If checks fail, or there are
   still none, go to **Needs human** with the failing check names.
5. **Merge.** `gh pr merge <pr> --merge`. Confirm with
   `gh pr view <pr> --json state` that the state is `MERGED`, then clean up:
   ```bash
   git worktree remove <worktree>
   git branch -D <branch>
   git push origin --delete <branch>
   ```
   Set `stage: "merged"`. If the merge fails, set `stage: "needs-human"` and
   tell the Owner why. If clean-up fails, the story is still merged: tell the
   Owner what the command printed.
6. Tell the Owner the story merged, with the PR link. Deploying it to dev01 is
   the Owner's manual CD run. The story still goes to the Owner at G6 (Sprint
   Review).

### Needs human

Set `stage: "needs-human"`. The branch and worktree stay for the Owner to
inspect. Tell the Owner which story is waiting, give the worktree path, and
quote `decision.md` (or the BLOCKED reason, the failing checks, or the leftover
files). Say what they can do: `/story approve <story>`,
`/story rework <story> <note>`, or take it over by hand.

## /story approve <story>

The story must be in `needs-human`. This is the Owner approving the merge
(gate G5) in place of the approver. If the run stopped before its commits were
complete (BLOCKED, leftover files, `tests/` touched), tell the Owner the branch
is incomplete and stop. Otherwise run **Merge**.

## /story rework <story> <note>

The story must be in `needs-human`.

1. Write the note, verbatim, to `factory/stories/<story>/rework-<k>.md`, where
   `k` is the next unused number.
2. Set `fixes: 0` (a rework gets a fresh `MAX_FIX_ROUNDS`).
3. Go to **Build round N+1** (N is the last round), with the rework prompt.

## Reporting

Keep the Owner posted with one short line per transition, for example
`US01: round 2, security CHANGES, code/infra PASS, ui skip → fix round 2`.
When the run ends, say whether it merged or needs the Owner, and why.

## Dashboard

```bash
cd factory && python3 -m http.server
```

Open <http://localhost:8000/dashboard.html>. It polls `factory/stories/` every
two seconds. Click a card to read its files.
