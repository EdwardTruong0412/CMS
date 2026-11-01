# RADIO matrix: CMS

| | |
| --- | --- |
| Step | Workflow Step 6 (`docs/process/ai-native-sdlc-workflow.md` section 3) |
| Author | PM/SM, 2026-11-01 |
| Status | Baseline 1 (G3 approved 2026-11-01), frozen by tag `baseline-1`; changes only through a Change Request (`docs/project-plan.md` section 5) |

Legend: **R** = Review, **A** = Approve (exactly one per row), **D** = Do, **I** = Inform, **O** = Observe. Blank means not involved.

Roles:
- **Owner**: you, the only approver at gates G1 to G7.
- **PM/SM**: the main session (coordinator).
- **PO**: Product Owner.
- **DL**: Dev Lead.
- **Dev**: Codex Dev 1 and Dev 2.
- **QA**.
- **Lens**: the story-run review lenses, `reviewer-security`, `reviewer-infra` and `reviewer-ui`.
- **Appr**: the story-run `approver` agent.

## Phase A: initiation

| Activity | Owner | PM/SM | PO | DL | Dev | QA | Lens | Appr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Intent, acceptance criteria, NFR (G1) | A | R | D | R | I | R | | |
| High-level architecture (input) | D, A | I | I | R | I | I | | |
| Basic Design, function list (G2) | A | I | R | D | R | R | | |
| Backlog and Release Plan | A | R | D | R | I | I | | |
| RADIO matrix, project plan, CR process, risk plan | A | D | R | R | I | R | | |
| Mock data (`testdata/mock/`) | A | D | R | I | I | R | | |
| Kick-off: conventions, `CLAUDE.md` / `AGENTS.md` | A | D | I | D | I | I | | |
| Baseline freeze, tag `baseline-1` (G3) | A | D | R | R | I | I | | |

## Phase B: sprint loop

| Activity | Owner | PM/SM | PO | DL | Dev | QA | Lens | Appr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sprint Planning, Sprint Goal | A | D | D | D | I | I | | |
| Story plan `docs/plans/<story>.plan.md` (G4) | A | O | R | D | R | R | | |
| Feature branch and worktree | I | D | | D | I | I | | |
| Test cases, test first | O | O | R | R | I | D | | |
| Code | O | O | I | R | D | R | | |
| Code review: code lens | O | I | I | D | I | R | | |
| Code review: security, infra, UI lenses | O | I | | R | I | | D | |
| Full test suite and test report | O | I | I | R | I | D | | |
| Merge into `develop` in a story run (G5) | R (on ESCALATE: A) | D | I | R | I | R | R | A |
| Merge into `develop` outside a story run | A | D | I | R | I | R | | |
| Sprint Review against the Definition of Done (G6) | A | D | D | R | I | R | | |
| Retrospective: rule, hook and eval changes | A | D | R | R | I | R | | |
| Daily summary and dashboard | O | D | I | I | | I | | |

The approver decides G5 only when nothing on its escalation list applies. Anything it escalates comes to the Owner, who then approves (Owner decision 2026-11-01, `.claude/rules/global.md`).

## Infrastructure and delivery

| Activity | Owner | PM/SM | PO | DL | Dev | QA | Lens | Appr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Terraform code and workflows (in a story) | O | O | I | R | D | R | R | |
| `terraform apply` / `destroy` on singleton, group, env | A, D | I | | R | | I | | |
| CD run to dev01 (image, migrate, deploy, smoke test) | A, D | I | | R | | I | | |
| Check session on dev01 (build, check, destroy; RP-D1) | A | D | I | R | | D | | |
| Session cost record | A | D | I | I | | | | |
| Final teardown and clean-up checklist (G7, TDN) | A, D | D | I | R | | R | | |
| Break-glass admin recovery (Q-D15) | A, D | I | | R | | | | |

Agents never run Terraform or AWS commands against dev01, and never start CD (global rule 2, workflow section 9). "D" for the PM/SM and QA in a check session means preparing the runbook and running QA's checks while the Owner drives the session.

## Change and release

| Activity | Owner | PM/SM | PO | DL | Dev | QA | Lens | Appr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Change Request (`docs/change-requests/CR-xxx.md`) | A | D | R | R | I | I | | |
| CR impact analysis | I | D | R | D | | I | | |
| New intent and backlog items from an approved CR | A | R | D | R | I | I | | |
| Release tag on `develop` (G7) | A | R | R | R | I | R | | |

## Decisions log

| ID | Decision | Reason | Decided by |
| --- | --- | --- | --- |
| RD-1 | The story-run roles (review lenses, approver) and the infrastructure activities are added to the section 3 proposal. | The `/story` loop and the Owner-only AWS actions are not covered by the generic matrix. | PM/SM |
| RD-2 | In a story run, the approver holds A for G5 and the Owner R, with A on escalation. | Owner decision of 2026-11-01 (story runs). One A per row is kept by marking the escalation case. | PM/SM, from the Owner decision |
| RD-3 | Every AWS action on dev01 (apply, destroy, CD, recovery) is "A, D" for the Owner. Agents prepare and review only. | Global rule 2 and the Owner's manual-CD decision (Q-O54). | PM/SM |
