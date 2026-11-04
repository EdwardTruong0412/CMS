# Handoff: 2026-11-02 US01a - Product Owner summary (repo tooling and app skeleton, before the story run)

| | |
| --- | --- |
| Task | Product Owner summary for US01a, required by global rule 5 and the `/story` preflight. Approved by the Owner on 2026-11-02 |
| Branch / worktree | `feature/US01a_repo_tooling_app_skeleton`, `/Users/truongquy/Documents/wt-US01a` |
| Read | `docs/backlog.md` (US01a, BL-D10), `docs/specs/spec-001.md` (CNT-AC01, CNT-AC02, CNT-AC07, IAC-AC01), `docs/project-plan.md` (section 3, Definition of Done), `docs/plans/US01a.plan.md` (sections 1, 4, 14, 15), `docs/gates/G4.md` (US01a, approved), `reports/sprints/sprint-1-planning.md` |
| Changed | This file only. Nothing committed |

## 1. What was done (PO side)

1. **Scope.** US01a is the first of the three parts of the former US01, recorded in `docs/backlog.md` in PROC10 (BL-D10, refinement inside `baseline-1`, no CR). It delivers CNT-AC01 and CNT-AC02, functions F-SYS-01 and F-SYS-02, Must, size M, Release 1, depends on nothing.
2. **G4 review (DES03, read-only).** Result CHANGES, notes only: `react-i18next` from the start is not scope creep (KO-14, no LNG criterion delivered); the US09 plan must write the `X-CMS-Request` header name into spec BD-6 and D-DL2; the US05 and US06 plans keep CNT-AC01 and CNT-AC02 checked for every image they build. The Dev Lead applied all three (plan section 15, row 4). The Owner approved the US01a section of `docs/gates/G4.md`.
3. **Sprint 1.** Lane Dev 2 ("App and small infrastructure"), target merge Wed 11 Nov 2026 (`reports/sprints/sprint-1-planning.md`).

## 2. The story in one paragraph

A developer gets `make bootstrap`, `make deps` and `make check` in the repository, an API skeleton that answers its health and status paths, a web UI skeleton, `.terraform-version` (`1.16.4`), and a multi-stage `src/api/Dockerfile` whose final stage is `python:3.13-slim` and which runs as a non-root user. Everything works from a clean clone without AWS access. No AWS resource is created and no dev01 session is needed.

## 3. Criteria delivered and what "done" means

Criterion text lives in `docs/specs/spec-001.md`; it is not repeated here.

| Criterion | Done at G5 (merge) | Done at G6 (Sprint Review) |
| --- | --- | --- |
| CNT-AC01 | QA's `tests/infra` check of the Dockerfile text passes in `make check`, and QA's `tests/image` check (the built image's base layers are those of `python:3.13-slim`) passes in QA's test round with Docker running, not skipped | Both tests trace to CNT-AC01 and pass on the merged `develop`; the DoD items below hold |
| CNT-AC02 | QA's `tests/infra` check (last `USER` after the last `FROM` is not `root` or `0`) passes in `make check`, and QA's `tests/image` check (configured user set and not root, `id -u` in the container is not `0`) passes in the test round | Same as G5 for the image part. The third check point, "the ECS task definition does not override the user to root", is not part of US01a; it is checked in US01c (backlog "Also checked in") and does not hold back US01a at G6 (US01a-PO-D1) |

Definition of Done (`docs/project-plan.md`, section 3) as it applies to US01a at G6:

- Item 1: both criteria have passing QA tests written before the code. Enabler tests (health and status contracts, settings, clock) are named by function or decision ID and do not count as criterion tests.
- Item 2: `make check` passes. No CI workflow exists until US05, so the "pull-request checks in CI" part has nothing to run for this story (US01a-PO-D2).
- Items 3 and 4: lenses pass and the approver says APPROVE, or the Owner approves the escalation (new pins, `AGENTS.md` and `CLAUDE.md` edits, plan section 9); `tests/` changed only by QA's `test(US01a): ...` commits.
- Item 5: not applicable; US01a does not change dev01.
- Item 6: `AGENTS.md` and `CLAUDE.md` updated where the story changes them (plan T5, including the `tests/image/` folder and the `make` targets).

## 4. Out of scope

- Any AWS resource or Terraform code (US01b onward).
- IAC-AC01: `.terraform-version` is written here because local tooling needs it, but the criterion (every workflow uses that version) stays with US05 (S1-PO-D4, SP1-D5).
- CNT-AC07 (no secret in the image): owned by US06. US01a keeps the Dockerfile free of secret `ARG` or `ENV` values (plan T3 boundary) but does not claim the criterion.
- CNT-AC03 (ALB health check) and the SCH criteria: owned by US01c and US30, US31; US01a only provides the paths as enablers.
- `compose.yaml` and the Vite proxy (US04), CI workflows (US05), Alembic and tables (US08), sessions (US09), language switch (US19), final start screen (US31).

## 5. Also checked in

- CNT-AC01, CNT-AC02 in **US01c**: the first image pushed to ECR and run on dev01, and the ECS task definition check point of CNT-AC02.
- CNT-AC01, CNT-AC02 in **US06** (and the image build of US05): every image the CD run builds keeps both checks, reusing the `tests/image` checks or equivalent workflow steps (plan section 4).

## 6. Decisions (PO tier)

| ID | Decision | Reason |
| --- | --- | --- |
| US01a-PO-D1 | CNT-AC02 is accepted at US01a's G6 on the Dockerfile and built-image check points; the ECS task definition check point is accepted at US01c's G6 | The task definition does not exist until US01c; BL-D2 places a test point that needs a later capability in the later story (PROC10-PO-D2) |
| US01a-PO-D2 | DoD item 2 for US01a means `make check` passes; the CI part applies from US05 on, when the pull-request workflows exist | No workflow exists in the repository yet; requiring one would pull US05 scope into US01a |
| US01a-PO-D3 | The plan's layer comparison (the base image's root layers are a prefix of the built image's layers) is accepted as the check that "the built image's history shows that base" in CNT-AC01 | It proves the same fact as the image history and is more reliable than parsing history text; the criterion text is unchanged |

## 7. Open questions (Owner tier)

None. The Owner actions before the run (install `python@3.13`, keep Docker Desktop running) are in `docs/gates/G4.md` and are actions, not questions.
