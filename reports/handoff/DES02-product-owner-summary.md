# Handoff: 2026-11-01 DES02 - Product Owner summary (Step 5, Product Backlog and Release Plan)

## What was done

- Read the PO agent file, workflow sections 4, 6 and 8, intent-001, all of spec-001, the function list, G2, the `/story next` and preflight sections of the story skill, and `CLAUDE.md`.
- Worked out the criteria rewording for Q-O54 to Q-O57 (same IDs). **Not written into spec-001:** this agent has only Read, Write, Grep and Glob, with no Edit tool. Applying the change would mean rewriting the whole 894-line spec (about 59k tokens) through Write. That risks the output limit and accidental changes to G1/G2-approved text. The exact find-and-replace pack is below; the coordinator can apply it with Edit (12 replacements plus 1 new row).
- Wrote `docs/backlog.md`: 41 end-to-end stories in proposed priority order, each with its detail section, functions, dependencies, MoSCoW, size and release. It also has notes for Sprint Planning, a decisions log (BL-D1 to BL-D9) and 2 Owner questions.
- Wrote `docs/release-plan.md`: 3 releases with goal, stories, exit check against DC1 to DC4, sizing, a long-session plan, and a decisions log (RP-D1 to RP-D4).
- Coverage: 183 of 183 criteria assigned, each to exactly one story. I checked it with Grep, since this agent cannot run scripts. There are 183 backticked IDs on "Delivers" lines, 183 distinct, and every group total matches the spec summary. Exactly 41 lines start with `- US`, all in the required form. To re-check with a script, run `python3 -I /private/tmp/claude-501/-Users-truongquy-Documents-CMS/04c33295-ffda-402f-825f-17161cfc9e16/scratchpad/check_backlog_coverage.py /Users/truongquy/Documents/CMS`.

## Files produced

| File | State |
| --- | --- |
| `docs/backlog.md` | New |
| `docs/release-plan.md` | New |
| `reports/handoff/DES02-product-owner-summary.md` | This file |
| `docs/specs/spec-001.md` | Unchanged; edit pack below |

## Spec-001 edit pack (apply with Edit; find text is exact)

Applied by the PM/SM on 2026-11-01: all 13 edits (each find string matched once) and the four stale lines listed at the end of this section (CICD row, profile term, cost NFR $1.60/$2, portability NFR 4 resources).

1. Term (How to read, infrastructure terms)
   - Find: `  - "Delivery run": the GitHub Actions run triggered by a merge to `develop`.`
   - Replace: `  - "Delivery run": a run of the CD workflows (F-OPS-03) started by hand by the Owner on `develop` (Q-O54). A merge to `develop` starts no delivery run.`
2. IAC trace line
   - Find: `Q-O36, Q-O39, Q-O52.`
   - Replace: `Q-O36, Q-O39, Q-O52; Q-O56 (IAC-AC09 reworded on 2026-11-01, same ID).`
3. IAC-AC09
   - Find: `The only resources in us-east-1 are the ACM certificate used by CloudFront and the WAF web ACL attached to CloudFront. Check: a resource inventory of us-east-1 tagged or named for the project lists only those two;`
   - Replace: `The only resources in us-east-1 are: the ACM certificate used by CloudFront; the WAF web ACL attached to CloudFront; the CloudWatch alarm on that web ACL's blocked requests (OBS-AC05 item 9); and one EventBridge rule that forwards that alarm's state changes to the default event bus in ap-southeast-1, from where they reach the SNS alert topic. The alarm and the rule are created by `modules/monitoring` with the `us_east_1` provider alias (OBS-AC10). Check: a resource inventory of us-east-1 tagged or named for the project lists only those four;`
4. CNT trace line
   - Find: `Pipeline flow); Q-O39. Image size`
   - Replace: `Pipeline flow); Q-O39; Q-O54 (CNT-AC04 reworded on 2026-11-01, same ID). Image size`
5. CNT-AC04
   - Find: `the image of every running ECS task is the one tagged with the SHA at the head of `develop` (Check: `aws ecs describe-tasks` image field compared with `git rev-parse develop`).`
   - Replace: `the image of every running ECS task is the one tagged with the SHA of the commit the Owner started the run on, which is the head of `develop` at that time (Check: `aws ecs describe-tasks` image field compared with the commit SHA of the run; with no later merge, this equals `git rev-parse develop`).`
6. CICD trace line
   - Find: `(GitHub Actions Workflows, Pipeline flow); Q-O40, Q-O41.`
   - Replace: `(GitHub Actions Workflows, Pipeline flow); Q-O40, Q-O41; Q-O54 (CD started by hand by the Owner: CICD-AC06, CICD-AC09, CICD-AC11 and CICD-AC16 reworded on 2026-11-01, same IDs; CICD-AC14 checked, unchanged).`
7. CICD-AC06
   - Find: `- CICD-AC06: A merge to `develop` starts a delivery run with no manual action, which performs in this order:`
   - Replace: `- CICD-AC06: A delivery run, started by hand by the Owner on `develop`, starts with the pre-flight check of CICD-AC14 and then, with no further manual action, performs in this order:`
   - And find, in the same line: `(Check: step timestamps in the run log).` (first occurrence, CICD-AC06)
   - Replace: `(Check: step timestamps in the run log). A merge to `develop` on its own starts no delivery run.`
8. CICD-AC09
   - Find: `Negative test: a branch with a migration that raises an error, merged to `develop`, leaves the running image unchanged.`
   - Replace: `Negative test: a branch with a migration that raises an error is merged to `develop` and the Owner starts a delivery run on it; the run fails at the migration and the running image is unchanged.`
9. CICD-AC11
   - Find: `Negative test: a deliberately broken image, merged to `develop`, is rolled back in each profile.`
   - Replace: `Negative test: a commit with a deliberately broken image is merged to `develop` and the Owner starts a delivery run on it; the deployment is rolled back, in each profile.`
10. CICD-AC16
    - Find: `takes at most 30 minutes from the merge to the smoke test passing.`
    - Replace: `takes at most 30 minutes from the start of the run to the smoke test passing.`
11. SCALE trace line and SCALE-AC03
    - Find: `Q-O28, Q-O29, Q-O45, Q-O46; ARCH`
    - Replace: `Q-O28, Q-O29, Q-O45, Q-O46; Q-O55 (SCALE-AC03 reworded on 2026-11-01, same ID); ARCH`
    - Find: `- SCALE-AC03: Switching between the lean and full profiles needs only a different tfvars file: applying the env layer with the other file changes the sizing of SCALE-AC01 or SCALE-AC02 with no change to any `.tf` file, and a following plan with the same file reports no changes.`
    - Replace: `- SCALE-AC03: Switching between the lean and full profiles needs only different tfvars files. In this spec "lean profile" and "full profile" mean the group layer applied with `awsenv/dev/group/tfvars/lean.tfvars` or `full.tfvars` and the env layer applied with `awsenv/dev/env/tfvars/dev01.tfvars` or `dev01_full.tfvars` (Q-O55). Applying the group layer and then the env layer, each with the file of the chosen profile, changes the sizing of SCALE-AC01 or SCALE-AC02 with no change to any `.tf` file, and a following plan of each layer with the same file reports no changes.`
12. COST trace line, COST-AC02, COST-AC03 (COST-AC04 unchanged: no contradiction with Q-O57)
    - Find: `(Cost); Q-O47, Q-O48.`
    - Replace: `(Cost); Q-O47, Q-O48; Q-O55 and Q-O57 (COST-AC02 and COST-AC03 reworded on 2026-11-01, same IDs; COST-AC04 checked, unchanged).`
    - Find: `- COST-AC02: Outside the full verification, the env layer is in the lean profile: `terraform plan -var-file=tfvars/dev01.tfvars` on the env layer reports no changes at any check made outside the full-verification window.`
    - Replace: `- COST-AC02: Outside the full verification, the group and env layers, whenever they exist, are in the lean profile: `terraform plan -var-file=tfvars/lean.tfvars` on the group layer and `terraform plan -var-file=tfvars/dev01.tfvars` on the env layer each report no changes at any check made outside the full-verification window. These checks are made during office hours (Q-D1).`
    - Find: `it is applied and then returned to the lean profile or destroyed on the same weekday, both within office hours. Check: the timestamps of the two applies (or the apply and the destroy) are on the same weekday between 09:00 and 18:00 ICT. How the run fits the budget is Q-D4.`
    - Replace: `it is applied (group, then env, SCALE-AC03) and then returned to the lean profile or destroyed on the same weekday, both within office hours. Check: the timestamps of the full apply and of the return to lean (or of the destroy) are on the same weekday between 09:00 and 18:00 ICT. The budget for the run is the alert of COST-AC01, and the env and group layers are destroyed at the end of the session (Q-O57, which answered Q-D4).`
13. Decisions log: add a sentence at the end of each Decision cell, before ` | `
    - Q-O54, after `is read as "CD (manual): image ..."`: ` Applied on 2026-11-01 by the Product Owner at Step 5: the term "Delivery run", CICD-AC06, CICD-AC09, CICD-AC11, CICD-AC16 and CNT-AC04 reworded, same IDs; CICD-AC14 checked and unchanged (it applies to every run, whoever starts it).`
    - Q-O55, after `and SCALE-AC01 fails).`: ` Applied on 2026-11-01 by the Product Owner at Step 5: SCALE-AC03 and COST-AC02 reworded, same IDs; COST-AC03 also names the group apply (D-PO6).`
    - Q-O56, after `and the WAF metric dimensions.`: ` Applied on 2026-11-01 by the Product Owner at Step 5: IAC-AC09 reworded, same ID.`
    - Q-O57, after `only singleton stays between sessions. ARCH unchanged.`: ` Checked on 2026-11-01 by the Product Owner at Step 5: COST-AC01 already updated; COST-AC03 reworded to point to Q-O57 instead of the answered Q-D4 (D-PO6); COST-AC04 and the done-criteria of intent section 8 do not contradict Q-O57 and are unchanged. The overnight and long-duration checks are raised as OQ-1 in `docs/backlog.md`.`
    - New row after the D-PO5 row:
      `| D-PO6 | Step 5 rewording choices: (1) SCALE-AC03 states that "lean profile" and "full profile" cover both the group and the env layer files (Q-O55); (2) COST-AC02 checks run during office hours, as Q-D1 requires for every no-change plan, and only while group and env exist (Q-O57); (3) COST-AC03 counts the group apply in the switch and points to Q-O57 instead of the answered Q-D4; (4) CNT-AC04 compares the running image with the commit the run was started on, because with manual CD `develop` can move after the run starts; (5) CICD-AC06 names the pre-flight of CICD-AC14 as the first step. | Keeps the reworded criteria consistent with Q-D1, Q-D3, Q-O54, Q-O55 and Q-O57 without changing what they require | PO default | SCALE-AC03, COST-AC02, COST-AC03, CNT-AC04, CICD-AC06 |`

Left stale outside the approved edit scope (recommend a follow-up edit with the Owner's approval):
- "How to read" group table, CICD row: "delivery on merge to `develop`".
- "How to read" term "Lean profile" / "full profile": env tfvars only (SCALE-AC03 now defines it, under item 11).
- NFR "Related constraint: cost": "80% ($8) and 100% ($10)" should be $1.60 and $2.
- NFR Portability: "Exactly 2 regional resources in us-east-1 (IAC-AC09)" should be 4.
- Basic Design BD-2 puts the UI sync after the smoke test, while CICD-AC12 checks the deployed UI (Dev Lead, US06 plan).

## Stories (priority order, size)

Release 1: US01 Walking skeleton on dev01 (L); US02 Budget and alert email reach the Owner (S); US03 Owner ends a session by destroying env and group (S); US04 Developer runs the whole stack locally (S); US05 Pull-request checks guard develop (M); US06 Owner deploys develop to dev01 with one CD run (L); US07 Secrets and stored data protected with project keys (M); US08 First admin setup (M); US09 Log in and log out (M); US10 Session time limits (S); US11 Only CloudFront reaches the API, encrypted on every hop (M); US12 WAF blocks attacks and floods (S); US13 Admin login protected against password guessing (M); US14 Audit trail and threat alerts (M); US15 Application and access logs kept 14 days (M); US16 View and add departments and positions (M); US17 Employee list and details (M); US18 Add an employee (M). 102 criteria.

Release 2: US19 English and Vietnamese UI (M); US20 Admin lists and creates user accounts (M); US21 Users set their own password (M); US22 HR member accounts lock after repeated failures (S); US23 Admin disables and re-enables accounts (S); US24 Admin resets passwords and unlocks accounts (M); US25 Admin edits account name and role (M); US26 Edit, deactivate and reactivate employees (M); US27 Search and filter employees (M); US28 Permanently delete an employee (S); US29 Rename and remove departments and positions (M); US30 Office-hours stop and start (M); US31 Closed page out of hours (S); US32 Alarms and dashboard (L); US33 Failed or out-of-hours deliveries stop safely (M). 62 criteria.

Release 3: US34 Owner switches between lean and full profiles (M); US35 Load check and auto scaling on the full profile (M); US36 Database failover on the full profile (S); US37 Every alert path tested (M); US38 One real office-hours cycle observed (S); US39 Rebuild from an empty account (M); US40 Final teardown leaves nothing behind (M); US41 Owner recovers admin access, break-glass (S, Could, no own criterion). 19 criteria.

## Decisions made (PO defaults)

- Spec: D-PO6 (in the edit pack).
- Backlog: BL-D1 coverage method; BL-D2 assignment rule (first delivered; cross-cutting criteria owned by the first story that can prove them; later test points listed under "Also checked in"); BL-D3 every criterion-owning story is Must, US41 Could; BL-D4 sizes; BL-D5 budget, alerts and session destroy right after US01; BL-D6 US41 has no own criterion; BL-D7 releases 1 to 3 are increments of the intent's "Release 1"; BL-D8 language switch opens Release 2; BL-D9 mock data loading belongs to US17.
- Release plan: RP-D1 batch dev01 checks (one session per 3 to 5 stories plus one exit session per release); RP-D2 morning schedule checks in the Release 3 long session, weekend checked from the schedule definition; RP-D3 singleton rebuild before the long session, with a pause for NS propagation; RP-D4 the Release 1 scope.

## Questions for the Owner (in `docs/backlog.md`)

- **OQ-1 One long verification session (about 30 hours, Mon-Thu start).** This one session would hold the overnight cycle (DC2), the full profile through a stop and the next start (SCALE-AC07, which contradicts COST-AC03's one-weekday limit), and the real-time test points (8 h, 24 h, 60 min). Estimated cost is about $5 to $7, so the alert fires. Recommended: yes, and the PO then rewords COST-AC03 to "until 18:00 on the next weekday, spanning at most one stop and start".
- **OQ-2 Monthly cost above the $2 alert.** Singleton alone costs about $1.50 to $1.70 per month, and each lean session adds about $0.20 to $0.30. It may add about $0.45 more if KMS keys pending deletion are billed. Recommended: accept the alert firing, keep the architecture, and approve the batching in RP-D1.

## What I was unsure of

- Cost figures are rough estimates from on-demand prices; verify with the AWS Pricing Calculator.
- US01, US06 and US32 are L and could exceed 3 days. US01 in particular carries 23 criteria; if Sprint Planning finds it too large, the PO splits it at refinement.
- Session start-up under Q-O57: the first CD run of a session meets an env that does not exist yet. This affects the pre-flight (CICD-AC14) and the 30-minute limit (CICD-AC16). It is a Dev Lead item for the US06 and US33 plans (backlog "Notes for Sprint Planning" item 1). If no design satisfies both criteria, it comes back as an Owner question.
- File naming: `.claude/rules/global.md` says `<story>-<role>-summary.md`, while the story skill preflight checks `<story>-po-summary.md`. Per-story PO summaries need one agreed name (PM/SM).
- The "Release 1" wording in the intent and in ACC-AC10 differs from this plan's Release 1 (BL-D7).
- No commit, git, Terraform or AWS command was run. Only the three files above and one scratchpad script were written.
