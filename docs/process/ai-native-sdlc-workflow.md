# AI-Native SDLC Workflow — v3 (English)

**Version:** v3.1 (2026-11-01). v3 (2026-10-11) is the English translation of the Vietnamese v3; v1 and v2 are kept unchanged.

**Changes in v3.1 (2026-11-01, Owner decisions):**
- Story runs: section 6.3 steps 2 to 8 can run as one automated loop, `/story <story>` (`.claude/skills/story/SKILL.md`), adapted from the `software-factory-claude-code` template. Review is split into parallel lenses (code by the Dev Lead, security, infra, and UI when `src/web/` changes). An `approver` agent merges the story's PR into `develop` or escalates to you (section 6.3a).
- CD is manual: merging into `develop` no longer deploys to DEV; you run the CD workflows yourself.

**Purpose:** a workflow for a personal project carried out by a team of agents, where you are the final approver at every gate. The team has five roles: PM/Scrum Master, Product Owner, Dev Lead, QA (run with Claude Code) and Devs (run with Codex).

**Changes from v2:**
- Only a DEV environment remains (STAGING and PROD removed).
- Role-based agent team: each role has its own definition file. Claude Code runs PM/SM, PO, Dev Lead and QA; Codex runs 2 to 3 Devs.
- You are the only approver at every gate. Agents never approve.
- Basic Design starts from a high-level architecture that you provide.
- All organization-specific content is removed; the 9-step process is kept and adapted for a personal project.

**How to read:** numbers in square brackets such as [2] refer to the sources at the end of the file. Sentences marked *(proposal)* are my own suggestions, not claims from a source. Section 12 lists assumptions and items to verify.

---

## 1. Overall model

### 1.1 The artifact chain

Each step ends with a committed file that the next step reads. Git history is the audit trail: who requested, who produced, who approved [2]. In a multi-agent team, handing off through files also avoids the "telephone game", where information degrades each time one agent passes it to another [7].

```
Your request → intent.md
  → prd.md (only when the PO decides the feature needs one)
  → spec.md (requirements + NFR + acceptance criteria + Basic Design, starting from your high-level architecture)
  → function list → Product Backlog (user stories) + Release Plan
  → plan.md (per story) → tests (QA) → code (Dev) → review (Dev Lead) → PR
  → you approve → merge → deploy to DEV → Sprint Review → new intent.md
```

### 1.2 Seven principles

1. **Humans supervise the system rather than doing the machines' work.** You set intent, resolve ambiguity and approve at gates; agents do the structured work in between [9].
2. **Machine-readable, structured artifacts.** Requirements, standards and diagrams live in standardized files so agents do not have to guess [9].
3. **No manual handoffs between steps.** If you are copying information from one document to another, that is a step to give to an agent [9].
4. **Standard environment.** Same framework and same repo layout so agent output is predictable [9].
5. **Governance as code.** Rules live in skills, hooks and versioned config files, reviewed like code [2].
6. **Controls built in.** Security and compliance checks run inside the pipeline, not at the end [9].
7. **Every failure improves the system.** Fix the instruction, skill, hook or eval that let the failure through, then add an eval so it cannot recur [2].

### 1.3 Agent authority

- Agents **do (D)** and **propose**. Only **you** approve (A).
- Agents do not approve their own PRs [2].
- Agents work only within the approved baseline. New requests go through a Change Request (section 7).
- Cost note: multi-agent systems use roughly 3 to 10 times more tokens than a single agent [7]. This is a deliberate choice for this project, but you should monitor consumption.

---

## 2. The agent team

### 2.1 Assignments

| Role | Runs on | Definition file | Main responsibilities |
| --- | --- | --- | --- |
| PM/Scrum Master | Claude Code | `.claude/agents/pm-scrum-master.md` | Coordinate the sprint, track gates, daily summary, manage risks, run the Retrospective |
| Product Owner | Claude Code | `.claude/agents/product-owner.md` | Turn requests into `intent.md`, acceptance criteria, Product Backlog and Release Plan; prioritize |
| Dev Lead | Claude Code | `.claude/agents/dev-lead.md` | Complete Basic Design from your architecture, write `plan.md`, assign work to Devs, review code, check security |
| QA | Claude Code | `.claude/agents/qa.md` | Write test cases from acceptance criteria before Devs code, run tests, report results |
| Dev 1 to 3 | Codex | `docs/process/agents/dev-N.md` + `AGENTS.md` | Implement a story from `plan.md` in a dedicated worktree |
| Review lenses (v3.1) | Claude Code | `.claude/agents/reviewer-{security,infra,ui}.md` | Review a story branch in parallel with the Dev Lead's code review, in a story run |
| Approver (v3.1) | Claude Code | `.claude/agents/approver.md` | Decide APPROVE (merge) or ESCALATE (to you) at the end of a story run |

### 2.2 How they work together

- **The main session is the PM/SM.** Run the whole session in this role with `claude --agent pm-scrum-master` [10]. The PM/SM delegates to PO, Dev Lead and QA as subagents; each subagent runs in its own context with its own tools and permissions [10]. By default a subagent can spawn subagents up to 3 layers deep [10].
- **The Dev Lead assigns work to Devs (Codex)** with `codex exec` run inside each worktree. `codex exec` runs Codex non-interactively with a read-only sandbox by default; add `--sandbox workspace-write` to allow edits, and `-o <file>` to write the final message to a file [12]. A previous session can be continued with `codex exec resume --last "<task>"` for fix rounds [12]. Codex requires a Git repository, which a worktree satisfies [12].
- **Codex reads its instructions from `AGENTS.md`** at the repo root, concatenated from the root down to the current directory; the combined size limit defaults to 32 KiB, so keep the file short and point to the process docs [11].
- **All handoffs go through files** in `reports/handoff/` and `docs/`. Agents do not pass important content to each other by message.

### 2.3 Example: Dev Lead assigns work to Dev 1

```bash
git worktree add ../wt-US01-dev1 feature/US01_user_list
cd ../wt-US01-dev1
codex exec --sandbox workspace-write \
  -o ../reports/handoff/US01-dev1.md \
  "You are Dev 1. Read AGENTS.md and docs/process/agents/dev-1.md. Do the tasks assigned in docs/plans/US01.plan.md. Do not edit files in tests/. Run the check command until it passes. Do not commit; propose one commit per task, then write the handoff report."
```

Fix round after review: `codex exec resume --last "Fix the issues in docs/reviews/US01-review.md"` [12].

---

## 3. Your role and the RADIO matrix

You are the **Owner**, the approver (A) at every gate. The matrix below is a *(proposal)*. Legend: **R** = Review, **A** = Approve (only one per row), **D** = Do, **I** = Inform, **O** = Observe.

| Activity | You | PM/SM | PO | Dev Lead | Dev (Codex) | QA |
| --- | --- | --- | --- | --- | --- | --- |
| `intent.md` and acceptance criteria | A | R | D | R | I | R |
| High-level architecture (input) | D, A | I | I | R | I | I |
| Basic Design (`spec.md`) | A | I | R | D | R | R |
| Backlog and Release Plan | A | R | D | R | I | I |
| `plan.md` per story | A | O | R | D | R | R |
| Write test cases | O | O | R | R | I | D |
| Write code | O | O | I | R | D | R |
| Review code | O | I | I | D | I | R |
| Merge PR | A (story run: on ESCALATE only; the approver agent decides otherwise) | I | I | R | I | R |
| Change Request | A | D | R | R | I | I |
| Release (tag) | A | R | R | R | I | R |

---

## 4. Phase A: Project initiation (9 steps)

The steps below are a 9-step initiation process adapted for a personal project (no customer, no multi-environment infrastructure). Rows marked **(added)** are my additions from other sources.

| Step | What to do | Who | Artifact | Gate |
| --- | --- | --- | --- | --- |
| 1 | Receive the request: you describe the simple requirement; the PO writes `intent.md` (problem, desired outcome, users, constraints, open questions). State personal-data security requirements explicitly (see section 8) | PO (D), you (A) | `docs/intent/intent-001.md` | |
| 1b *(added 2026-10-31)* | PRD: the PO decides whether the feature needs a PRD (criteria in `.claude/agents/product-owner.md`), records the decision in the intent, and if needed writes it from `docs/templates/prd-template.md`. Acceptance criteria and NFR numbers stay in `spec.md`; the PRD references their IDs | PO (D), Dev Lead (R), you (A) | `docs/prd/prd-<NNN>-<slug>.md` | G1 |
| 2 | Minimal infrastructure: Git repo, a single DEV environment, a CI pipeline (build, test, lint) and automatic deploy to DEV when merged to `develop`; set up the agent scaffolding (`CLAUDE.md`, `AGENTS.md`, `.claude/agents/`, hooks) | Dev Lead (D), you (A) | `.github/` or CI scripts, `.claude/`, `CLAUDE.md` v0, `AGENTS.md` v0 | |
| 3 | Settle acceptance criteria for each requirement: testable and measurable. Example: "Add employee" must allow uploading a PDF contract, automatically create an account, send a welcome email, and respond in under 1 second | PO (D), QA (R), you (A) | "Acceptance Criteria" section of `spec.md` | **G1** |
| 3b *(added)* | Clarify NFRs with the ISO 25010 checklist [3]: capacity, availability, security, performance, compatibility, usability, maintainability, portability. The PO asks you for the missing numbers | PO (D), you (A) | "NFR" section of `spec.md` | G1 |
| 4 | Reuse: search the `assets/` folder (old projects, components, schemas you want to reuse), propose what to reuse and record where it came from | Dev Lead (D) | `docs/reuse-assets.md` | |
| 4b *(added)* | Basic Design: you provide the **high-level architecture** (section 5); the Dev Lead completes the rest | Dev Lead (D), you (A) | `docs/specs/spec-001.md`, `function-list.md` | **G2** |
| 5 | Product Backlog and Release Plan from the business point of view. **Note:** the backlog contains only end-to-end user stories (covering FE, BE, DB) and is **not** split into technical tasks at this step. Example: US01 Employee profile management, US02 Permissions, US03 Reports. Release 1: US01 + US02. Release 2: US03 and further features | PO (D), you (A) | `docs/backlog.md`, `docs/release-plan.md` | |
| 6 | Assign responsibilities with RADIO: fill in the matrix (section 3) for the project | PM/SM (D), you (A) | `docs/radio.md` | |
| 7 | Project plan and sub-plans: Change Request process (section 7); risk plan (use mock data to start work if sample data is not yet available) | PM/SM (D), you (A) | `docs/project-plan.md`, `testdata/mock/` | |
| 8 | Kick-off: settle coding conventions and Git branching rules, set the Sprint Review schedule (every 2 weeks) | Dev Lead, PM/SM (D), you (A) | `CLAUDE.md` v1, `AGENTS.md` v1, `docs/kickoff.md` | |
| 9 | Freeze the Baseline Project Plan, then move to Sprint 1 | PM/SM (D), you (A) | Tag `baseline-1` | **G3** |

**Note on ordering:** step 2 comes before the technology stack is settled. So the first versions of `CLAUDE.md` and `AGENTS.md` contain only a skeleton and basic commands, are extended once Basic Design (step 4b) settles the stack, and are completed at step 8 *(proposal)*.

---

## 5. Basic Design from your high-level architecture

### 5.1 Division of work

- **You provide:** the high-level architecture, the diagram `20261003_02_high_level_architecture.png` at the repo root.
- **The Dev Lead does:** check that architecture against the NFRs and acceptance criteria, raise gaps or contradictions as questions to you, then write the rest of the Basic Design.
- **You approve** at gate G2.

### 5.2 What the high-level architecture should contain *(proposal)*

This list is a suggestion so the Dev Lead does not have to guess:
- System configuration diagram: main components and how they relate, including how it deploys to DEV [4]
- Technology stack (language, framework, database, external services)
- Where data is stored, and how authentication and authorization work
- Integrations with external systems
- Key constraints (cost, performance, security)

### 5.3 What the Dev Lead adds

Following the contents of a Basic Design [4][5]:
- Business flow
- Screen list (screen ID, title, function description) and screen transition diagram
- ER diagram (logical structure of the database)
- Functional specification: function ID, input, processing, output
- NFR overview (performance, security, availability)

More detailed design (sequence diagrams, full schema, API spec, exception handling) is detailed design and lives in the `plan.md` of each story [5].

---

## 6. Phase B: The Sprint loop

Default length *(proposal)*: **2 weeks**. Because you are the only approver, the sprint must be long enough for you to review. Scrum allows sprints of up to 1 month [1].

### 6.1 Scrum events and the responsible agent

| Event | Max timebox [1] | Responsible agent | What happens |
| --- | --- | --- | --- |
| Backlog refinement | within the sprint | PO | Split stories, check each story has acceptance criteria |
| Sprint Planning | 8 hours (1-month sprint) | PO, Dev Lead, PM/SM | Answer Scrum's 3 questions [1]: why is this sprint valuable, what can be done, how will the work get done. Set the Sprint Goal |
| Story execution | within the sprint | Dev Lead, QA, Dev | Section 6.3 |
| Daily Scrum | 15 minutes [1] | PM/SM | *(proposal)* Summarize from git: done, in progress, blocked |
| Sprint Review | 4 hours [1] | PM/SM, PO | Prepare the demo, compare each story against its acceptance criteria for your approval |
| Retrospective | 3 hours [1] | PM/SM | Collect recurring failures, propose updates to instructions, skills, hooks, evals |

The timeboxes are maximums for a 1-month sprint [1]. For a 2-week sprint, set your own specific timeboxes.

### 6.2 Sprint Planning: break stories into tasks by layer

At Sprint Planning, each user story is broken into technical tasks by layer. Example for US01:

- `[DB]` design the `Employees` and `Departments` tables
- `[BE]` write the RESTful API `POST /api/v1/employees`
- `[FE]` build the employee entry form
- `[Infra]` configure storage for the PDF contract files
- `[QA]` write test cases and integration tests

**How:**
1. The Dev Lead opens **plan mode** (read-only) and reads `spec.md` and the story [2].
2. The Dev Lead proposes the task list by layer, the order of work, and which Dev takes which story.
3. You ask questions, adjust, then approve (gate **G4**). The result is committed as `docs/plans/US01.plan.md` [2].

### 6.3 Executing a story

0. **Branch and summaries.** After G4, the Dev Lead creates `feature/<story>_<summary>` from `develop`. The PO, Dev Lead and QA each write `reports/handoff/<story>-<role>-summary.md`; the PM/SM gives you one combined summary, and implementation starts only after you approve. See `.claude/rules/global.md`.
1. **QA writes test cases first**, from the acceptance criteria, in `tests/`, on the feature branch. This is test-first: the Dev must make the tests pass without editing them [2].
2. **One story goes to one Dev (Codex)**, working in a dedicated worktree, in the order DB → BE → FE → Infra *(proposal)*. A story is not split across Devs because the layers of one story are tightly coupled, and splitting loses information between agents [7].
3. **Feedback loop.** The Dev runs a single check command (test, build, lint, type check) and iterates until it passes [2].
4. **The Dev Lead reviews** the diff against `REVIEW.md` and `spec.md`, including a security check. The Dev Lead only reports issues and does not fix code [2][7]. Results go in `docs/reviews/US01-review.md`.
5. **Fix rounds:** the Dev fixes issues from the review, at most 3 rounds *(proposal)*. After 3 rounds the PM/SM escalates to you.
6. **QA runs the full test suite** and writes a report to `reports/test-report-US01.md`.
7. **The PM/SM opens the PR** (one PR per story, one commit per task) with a summary for you. Every commit is made only after you review the diff and the message (`.gitmessage`); Devs do not commit themselves.
8. **You approve the PR (gate G5).** Merging into `develop` does not deploy; you run the CD workflows to deploy to DEV.

### 6.3a Story runs (v3.1)

Steps 2 to 8 can run as one loop: you type `/story <story>` once G4, the branch, QA's tests and the three summaries are in place, and that command approves the whole run (`.claude/rules/global.md`, "Story runs"). The loop is in `.claude/skills/story/SKILL.md`:

```
Dev (Codex) → coordinator commits → [code, security, infra, ui?] in parallel → WAIT FOR ALL
   ▲                                    any CHANGES or tests FAIL (max 3 fix rounds) ┘
   all PASS → QA full suite → approver → APPROVE: PR, checks, merge into develop
                                       → ESCALATE: waits for you (/story approve | /story rework)
```

- Every agent file starts with a machine-readable line (`STATUS:`, `VERDICT:`, `RESULT:`, `APPROVE`/`ESCALATE`), so the coordinator never interprets prose.
- Run state lives in `factory/stories/<story>/` (gitignored, shown by `factory/dashboard.html`); the record is committed with the story under `reports/stories/<story>/`.
- The approver escalates governance, pipeline, singleton/group layer, exposure and IAM, stateful destroy/replace, cost, destructive migrations, identity code, new dependencies and scope changes. You still review every merged story at G6.

### 6.4 Running stories in parallel

Run in parallel only when stories are independent and have clear interfaces. Each Dev uses its own worktree and branch [2]. Anthropic advises dividing work by the context it needs rather than by phase of work, and only splitting when there is a reason [7]. Anthropic also notes that coding has fewer parallelizable parts than research [8].

### 6.5 End of sprint

- **Sprint Review (gate G6):** you watch the demo and approve each story against the Definition of Done [1].
- **Retrospective:** each recurring failure becomes a concrete change to `CLAUDE.md`, `AGENTS.md`, a hook or an eval [2].

---

## 7. Change Request process

Applies when you want to add a feature or change scope after the baseline is frozen.

1. Agents **do not start** work outside the baseline. The PM/SM records it in `docs/change-requests/CR-xxx.md`.
2. The PM/SM and Dev Lead draft an impact analysis: affected stories and schedule impact (a draft only).
3. You decide to approve or reject.
4. If approved: the PO creates a new `intent.md` and adds it to the Product Backlog; the PM/SM updates the baseline.

---

## 8. Security rules and guardrails

- **Use mock data only** (`testdata/mock/`). Do not put real personal data into prompts, fixtures or logs.
- Do not read or write secrets (`.env`, keys). On the Claude Code side, enforce with hooks and permissions; on the Codex side, use the `workspace-write` sandbox inside a dedicated worktree [12].
- Devs must not edit files in `tests/`. On the Claude Code side, block with a hook; on the Codex side, use a CI step that rejects a PR if the Dev's branch changes anything in `tests/` *(proposal)*.
- No merge before tests and review pass.
- Agents do not approve or merge their own PRs [2].
- Destructive actions (deleting data, force push) need your explicit approval.
- Every change links to an `intent.md` and a decision-log entry.
- When something is ambiguous or irreversible: stop and write an open question in the handoff report; do not guess.
- Hooks must be fast [2].

### Decision tiers (added 2026-10-31)

The Owner asked not to be asked easy questions that have a standard answer in software design.

- **Agents decide:** routine defaults with a standard industry answer (validation rules, page sizes, timeouts, retention periods, alarm thresholds, naming, design patterns). The deciding agent records each one in the file's "Decisions log" (ID, decision, reason, criteria affected). The Owner sees them all at the next gate and can override any of them.
- **The Owner decides:** only
  - changes to scope (features, roles, user groups)
  - contradictions with an earlier Owner decision
  - cost beyond the approved budget, or changes to the approved architecture
  - weakening security below common practice
  - irreversible or destructive actions
  - values only the Owner holds (domains, email addresses, accounts)

  Each Owner question comes with a recommended answer. The PM/SM filters every question against this list before relaying it.

### Gates (you approve all of them)

Recording method *(proposal)*: each gate has a file `docs/gates/Gx.md` with a checklist and a line `Owner approval: [ ]`. Agents proceed only after you change it to `[x]` and commit.

| Gate | Question you answer | Blocks |
| --- | --- | --- |
| G1 Intent and AC | Are the scope, the PRD (if any) and the acceptance criteria correct? | Basic Design |
| G2 Basic Design | Does the design match your architecture, and are open decisions resolved? | Backlog |
| G3 Baseline | Are the plan, backlog and assignments settled? | Sprint 1 |
| G4 Plan | Is the story's plan correct before any code is written? | Writing code |
| G5 PR | Does the code meet requirements, with tests and traceability? In a story run, the approver decides unless it escalates (v3.1) | Merge |
| G6 Sprint Review | Does the story meet the Definition of Done? | Closing the story |
| G7 Release | Are all checks green on DEV, ready to place the release tag? | Release tag |

---

## 9. Phase C: Release and maintenance

- **Environment:** DEV only. CI runs on every PR; deploying to DEV is a CD workflow you run by hand after merging into `develop`.
- **A release** is a git tag on `develop` after you approve G7. There is no other environment for agents to deploy to.
- **Maintenance:** bugs or ideas that come up are written by the PO as a new `intent.md` and added to the Product Backlog. For a larger feature the PO also writes a PRD (Step 1b). The PO prioritizes them for later sprints [1][2]. Every bug fixed comes with a new eval or test so it does not recur [2].
- *(Optional, later)* If the project moves to a real environment, add threshold-based monitoring and gated environments, following Anthropic's playbook [2].

---

## 10. Sample agent configuration

### 10.1 Repo structure

```
.
├── CLAUDE.md                     # instructions for the Claude Code agents
├── AGENTS.md                     # instructions for the Codex Devs (keep short, < 32 KiB [11])
├── REVIEW.md                     # review criteria
├── .claude/
│   ├── settings.json             # hooks and permissions
│   └── agents/
│       ├── pm-scrum-master.md
│       ├── product-owner.md
│       ├── dev-lead.md
│       └── qa.md
├── docs/
│   ├── process/
│   │   ├── workflow.md           # this v3, the shared source for all agents
│   │   └── agents/dev-1.md  dev-2.md  dev-3.md
├── 20261003_02_high_level_architecture.png  # high-level architecture, provided by you
│   ├── intent/  prd/  templates/  specs/  plans/  reviews/  gates/  change-requests/  decisions/
│   ├── backlog.md  release-plan.md  radio.md  project-plan.md  kickoff.md  reuse-assets.md
├── assets/                       # old docs, components, schemas for reuse
├── src/   tests/   evals/   testdata/mock/
└── reports/handoff/              # handoff reports
```

Each Claude Code agent is a Markdown file with frontmatter; only `name` and `description` are required, `tools` is the allowlist of tools, and the body is the system prompt [10]. Project subagents go in `.claude/agents/` and should be committed to git [10].

### 10.2 `.claude/agents/dev-lead.md`

```markdown
---
name: dev-lead
description: Dev Lead. Completes Basic Design from 20261003_02_high_level_architecture.png, writes plan.md per story, assigns work to Devs (Codex) and reviews code. Use for design, planning or review.
tools: Read, Grep, Glob, Bash, Write
---
You are the Dev Lead. Follow docs/process/workflow.md.
- Do not edit code in src/. Write documents only (spec, plan, review).
- Write plan.md only in plan mode; assign work to Devs only after docs/gates/G4.md has Owner approval [x].
- Assign work to Devs with `codex exec` in a dedicated worktree, stating: goal, files to read, files to write, boundaries.
- Review the diff against REVIEW.md and the spec; report issues by severity, with file and line.
- Do not approve or merge; only the Owner approves.
```

### 10.3 `.claude/agents/qa.md`

```markdown
---
name: qa
description: QA. Writes test cases from acceptance criteria before Devs code, runs tests and reports results.
tools: Read, Grep, Glob, Bash, Write, Edit
---
You are QA. Follow docs/process/workflow.md.
- Write only to tests/ and reports/. Do not edit src/.
- Each test traces to one acceptance criterion (put the ID in the name or a comment).
- Use only data in testdata/mock/.
- Report: pass/fail, specific failures, steps to reproduce.
```

### 10.4 `.claude/agents/product-owner.md` and `pm-scrum-master.md` (abridged)

```markdown
---
name: product-owner
description: Product Owner. Writes intent.md, acceptance criteria, Product Backlog and Release Plan; splits and prioritizes stories.
tools: Read, Grep, Glob, Write
---
You are the Product Owner. Write only to docs/intent/, docs/backlog.md, docs/release-plan.md.
Stories must be end-to-end (FE, BE, DB) and have testable acceptance criteria. Do not split into technical tasks.
Requests outside the baseline: hand over to the PM/SM to open a Change Request.
```

```markdown
---
name: pm-scrum-master
description: PM/Scrum Master. Coordinates the sprint, tracks gates, writes the daily summary, manages risks and change requests, runs the Retrospective.
tools: Read, Grep, Glob, Bash, Write
---
You are the PM/Scrum Master and you coordinate the other agents. Do not make decisions in place of the Owner.
Stop and tell the Owner when a gate needs approval, when a story exceeds 3 fix rounds, or when there is a request outside the baseline.
Each day write a summary: done, in progress, blocked.
```

### 10.5 `docs/process/agents/dev-1.md` (for the Codex Dev)

```markdown
# Dev 1 (Codex)
- Do exactly the tasks in docs/plans/<story>.plan.md assigned to you.
- Work only in the assigned worktree; do not touch other branches.
- Do not edit files in tests/. Make QA's tests pass by changing the code.
- Run the single check command (see AGENTS.md) until it passes.
- Do not read .env or real data; use only testdata/mock/.
- When something is ambiguous: stop and write an open question in the handoff report.
- At the end: write the handoff report (what was done, check results, trade-offs, open questions).
```

### 10.6 `AGENTS.md` (abridged, for Codex)

```markdown
# Process
Follow docs/process/workflow.md and the role file in docs/process/agents/.
## The single check command
<cmd>   # test + build + lint + type check
## Conventions
- Branch: feature/<story>_<summary>; one commit per task, made only after Owner approval
- Coding convention: <fill in after step 8>
## Never do
- Edit tests/, read .env, use real data, merge on your own
```

### 10.7 Handoff report

```markdown
# Handoff: <date> <US ID> — <agent>
- Completed: commit links, acceptance criteria met
- Check results: pass/fail, specific failures
- Trade-offs chosen and why
- Open questions for the Owner
- Risks and next steps
```

For the `intent.md`, `plan.md`, `spec.md` and `REVIEW.md` templates, see sections 8 and 9 of v1 and v2.

---

## 11. Metrics (review at each Retrospective)

| Phase | Leading indicator | Lagging indicator |
| --- | --- | --- |
| Plan | Time from request to approved `intent.md` | Number of `intent.md` files that proceed to design |
| Design | Time from `intent.md` to `spec.md` | Number of `spec.md` edits after the first `plan.md` |
| Build | Share of stories passing review on the first try | Fix rounds per story |
| Test | First-pass CI success rate | Change failure rate |
| Deploy | Time you spend reviewing each PR | Defects caught before vs after merge |

The indicators come from Anthropic's playbook [2]. One more *(proposal)*: tokens consumed per story, since multi-agent systems use more tokens [7].

---

## 12. Assumptions and items to verify

1. **How the Dev Lead calls Codex** uses `codex exec` (section 2.3). The Codex MCP documentation I read says Codex is an MCP client and does not say Codex runs as an MCP server [14], so I did not use that approach.
2. **Codex custom agents** (`.codex/agents/*.toml` files) exist with the fields `name`, `description`, `developer_instructions` [13]. I did not find documentation on how to select a specific custom agent when running `codex exec`, so v3 uses role files `docs/process/agents/dev-N.md` instead. If you want to use Codex custom agents, more testing is needed.
3. **`claude --agent pm-scrum-master`**, to run the whole session in the PM/SM role, is described in the documentation [10]. I have not verified that such a session can in practice delegate to the other subagents by itself; try it on a small sprint first.
4. **The CI step blocking Devs from editing `tests/`** and **the 3-round fix limit** are my proposals and have no source.
5. **2-week sprint**, **one story per Dev**, **one PR per story** are my choices. You can change them.
6. **The high-level architecture** is provided by you. When do you plan to provide it, and does it already include the technology stack?
7. **How many Devs (2 or 3)?** Each Dev adds one `dev-N.md` file and increases token cost.

---

## Sources

1. [The Scrum Guide](https://scrumguides.org/scrum-guide.html): roles, 5 events, timeboxes, Definition of Done, Product Backlog.
2. [The AI-native SDLC playbook, Anthropic](https://claude.com/blog/the-ai-native-sdlc-playbook) and [Claude Academy course](https://academy.claude.com/courses/ai-native-sdlc-playbook): artifact chain, plan mode, feedback loop, test-first, PR review, parallel worktrees, metrics.
3. [ISO/IEC 25010, Wikipedia](https://en.wikipedia.org/wiki/ISO/IEC_25010): NFR checklist.
4. [How to create basic design doc](https://book.st-hakky.com/en/business/how-to-create-basic-design-doc): contents of a Basic Design.
5. [Difference between basic design and detailed design](https://book.st-hakky.com/en/business/difference-between-basic-design-and-detailed-design).
6. [Epics, stories, and initiatives, Atlassian](https://www.atlassian.com/agile/project-management/epics-stories-themes).
7. [Building multi-agent systems: when and how to use them, Claude](https://www.claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them): token cost, dividing by context, the "telephone game".
8. [How we built our multi-agent research system, Anthropic Engineering](https://www.anthropic.com/engineering/multi-agent-research-system).
9. McKinsey, "Rewiring software delivery for the agentic era", May 2026 (the PDF you attached).
10. [Subagents, Claude Code docs](https://code.claude.com/docs/en/sub-agents): agent file format, `--agent`, nesting limits.
11. [AGENTS.md, Codex docs](https://learn.chatgpt.com/docs/agent-configuration/agents-md): how Codex reads `AGENTS.md`, 32 KiB limit.
12. [Non-interactive mode (`codex exec`), Codex docs](https://learn.chatgpt.com/docs/non-interactive-mode): sandbox, `-o`, `resume`, Git repo requirement.
13. [Subagents, Codex docs](https://learn.chatgpt.com/docs/agent-configuration/subagents): custom agents as TOML files.
14. [MCP, Codex docs](https://learn.chatgpt.com/docs/extend/mcp?surface=cli): Codex uses other MCP servers.

The templates in section 10 are starting points I wrote, not copies of Anthropic or OpenAI documentation. Check the formats against current documentation before use.
