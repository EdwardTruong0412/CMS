# Handoff: 2026-11-02 PROC10 - Product Owner summary (US01 split recorded in the backlog)

| | |
| --- | --- |
| Task | PROC10, approved by the Owner on 2026-11-02. Records the Sprint 1 Planning decision OQ-S1-1 (Dev Lead's 3-part split of US01) as refinement inside `baseline-1`, no CR, no new tag |
| Branch / worktree | `feature/PROC10_us01_split`, `/Users/truongquy/Documents/wt-PROC10` |
| Read | `reports/sprints/sprint-1-planning.md` (sections 3 and 10), `reports/handoff/PROC08-dev-lead-summary.md` (section 1), `reports/handoff/PROC08-product-owner-summary.md`, `.claude/skills/story/SKILL.md` ("/story next"), `docs/specs/spec-001.md` (the 23 criteria), `docs/specs/function-list.md`, `docs/release-plan.md` |
| Changed | `docs/backlog.md` only, plus this file. Nothing committed |

## 1. What changed in `docs/backlog.md`

1. **Story lines.** The US01 line is replaced by three lines in the same format, `- <story> <title> → <link>`, at the top of the order (`/story next` reads `- <story> <title> → <link>`; there are no claim markers in the backlog, claims are folders under `factory/stories/`):
   - `- US01a Repo tooling and app skeleton → docs/backlog.md#us01a`
   - `- US01b State bucket, singleton and group → docs/backlog.md#us01b`
   - `- US01c Env layer serves the app over HTTPS → docs/backlog.md#us01c`
2. **Story sections.** The US01 section is replaced by three sections (anchors `us01a`, `us01b`, `us01c`) with user-story sentence, Delivers, Also checked in, Functions, Depends on, Priority/Size/Release/Source and Notes.

   | Part | Delivers | Functions | Depends on | Size |
   | --- | --- | --- | --- | --- |
   | US01a | CNT-AC01, CNT-AC02 | F-SYS-01, F-SYS-02 | none | M |
   | US01b | IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01, NET-AC02 | F-OPS-08 | US01a | M |
   | US01c | IAC-AC05, IAC-AC06, IAC-AC12, NET-AC03, NET-AC04, NET-AC07 to NET-AC11, CNT-AC03, SEC-AC01, SEC-AC02, SCALE-AC01 | F-SYS-01, F-SYS-02, F-OPS-08 | US01a, US01b | L |

   All three are Must, Release 1, source intent-001. The 23 IDs were checked against the former US01 Delivers line: the same 23, each in exactly one part.
3. **Also checked in.** The former US01 items moved with their criterion: IAC-AC04 and IAC-AC14 (later Terraform stories, US40 tag search) to US01b; IAC-AC12 (later Terraform stories, full profile in US34), IAC-AC05, NET-AC07, NET-AC08, CNT-AC03 and SCALE-AC01 to US01c. Added where a criterion's own text reaches into a later part (BL-D2): CNT-AC01 and CNT-AC02 in US01c and US06 (the CNT-AC02 test point "the ECS task definition does not override the user to root" can only run in US01c); IAC-AC03 in US01c and later Terraform stories; IAC-AC07 in US01c (env layer, workspace `dev01`).
4. **Depends on, other stories.** US02 and US03 to US01b; US04 to US01a; US05 to US01a, US01b, US01c; US07, US11, US12 and US15 to US01c; US39's list to "US01a to US01c, US02, US03, ...". US08 changed from "US07" to "US01a, US04 (build and local tests); US07 (dev01 check, SP1-D4 and SP1-D13)", as the coordinator asked and the Dev Lead summary states; the US07 link is kept for the dev01 check. US06 (US05) and US09 (US08) are unchanged: their US01 parts are reached through US05 and US08.
5. **Other references in the file.** Status row (split noted), coverage line (recount date 2026-11-02), releases line ("Release 1 is US01a to US18"), BL-D4 (US01c is the L part), BL-D5 (the slice is US01a to US01c; "Affects" now US01a to US03). The words "former US01" stay only in the three Notes and in BL-D4, BL-D5 and BL-D10 as history.
6. **Decisions log.** New row BL-D10 records the split, the reason (refinement per the US01 note approved at G3, Sprint 1 Planning OQ-S1-1, decided by the PM/SM under the Owner's delegation of 2026-11-02, no CR, no new tag), the moved and added "Also checked in" items, the new Depends on lines and the recount.

No other story's scope, criteria, priority order or release changed. No criterion ID is written in backticks outside a Delivers line.

## 2. Recount

Method: the criterion IDs in backticks on the "Delivers" lines, as BL-D1 defines. Run with the Grep tool (ripgrep) on `docs/backlog.md`, pattern `` `[A-Z]+-AC[0-9]+` ``, once in only-matching mode (every match) and once in line mode (to confirm every match is on a `Delivers:` line). Shell equivalent:

```bash
grep '^Delivers:' docs/backlog.md | grep -oE '`[A-Z]+-AC[0-9]+`' | wc -l            # 183
grep '^Delivers:' docs/backlog.md | grep -oE '`[A-Z]+-AC[0-9]+`' | sort -u | wc -l  # 183
grep -c '`[A-Z]+-AC[0-9]+`' docs/backlog.md   # 43 lines, all of them Delivers lines
```

Result on 2026-11-02: **183 IDs, 183 distinct**, on 43 Delivers lines (US41 has none). Release 1 (US01a to US18) still owns 102 criteria (2 + 7 + 14 + 79), matching the release plan's exit check.

## 3. Decisions (PO tier)

| ID | Decision | Reason |
| --- | --- | --- |
| PROC10-PO-D1 | Story IDs `US01a`, `US01b`, `US01c` with the Dev Lead's titles; US02 to US41 keep their numbers | S1-PO-D5; renumbering would touch every cross-reference in the baseline |
| PROC10-PO-D2 | Added "Also checked in" items for CNT-AC01, CNT-AC02, IAC-AC03 and IAC-AC07 where the criterion's text spans two parts | BL-D2: a test point that needs a later capability runs in the later story; no criterion text changes |
| PROC10-PO-D3 | US08's Depends on names US01a and US04 for the build and keeps US07 for the dev01 check | Matches the Sprint 1 lanes (US08 built before US07 merges, SP1-D4, SP1-D13) without losing the dev01 dependency |
| PROC10-PO-D4 | US06 and US09 Depends on lines are left as they are | They never named US01; the parts are reached through US05 and US08 |

## 4. Open points (not Owner questions)

1. **`docs/release-plan.md` (not edited, out of scope).** Lines that now name US01 where the parts are meant: line 5 (Source "stories US01 to US41"), line 30 (Release 1 story list starts "US01 Walking skeleton on dev01"), line 32 ("Parallel work is possible after US01"), line 35 ("criteria owned by US01 to US18"), line 101 (RP-D4 "the 18 stories US01 to US18"; Release 1 now has 20 stories). Suggested follow-up: a release-plan refinement edit by the PO in a later approved task.
2. **Other files naming US01 as the first story** (PM/SM or Dev Lead governance edits): `CLAUDE.md` line 32 ("added by the first story (US01)", now US01a); `docs/kickoff.md` lines 104, 187, 194, 195, 200 (KO-9, KO-16, KO-17, KO-22: "US01" and "the US01 plan" now mean US01a for `make check`, `.terraform-version`, `.tflint.hcl` and `testpaths`); `docs/project-plan.md` lines 8 ("US01 to US41"), 16 (pin "delivered by US01"), 18 (Sprint 1 "US01 to US09"). `docs/gates/G3.md` is a gate record of 2026-11-01 and should stay as it was.
3. **Generic examples, no change needed:** `docs/process/ai-native-sdlc-workflow.md`, `.claude/skills/story/SKILL.md`, `.claude/agents/dev-lead.md`, `qa.md`, `product-owner.md`, `AGENTS.md` line 122 and `docs/kickoff.md` line 56 use "US01" only as an example ID.
4. **Before `/story next` picks US01a,** this branch must be merged to `develop`, because the skill reads the backlog from `origin/develop`.

No Owner question arises from this task.
