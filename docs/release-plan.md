# Release plan: intent-001 (CMS)

| | |
| --- | --- |
| Source | `docs/backlog.md` (stories US01 to US41), `docs/intent/intent-001.md` section 8 (done-criteria DC1 to DC4), `docs/specs/spec-001.md` |
| Author | Product Owner, workflow Step 5, 2026-11-01 |
| Status | Proposal for the Owner, input to G3. The grouping and order are the Product Owner's proposal; the Owner decides. |

Releases 1 to 3 here are delivery increments of the scope that intent-001 calls "Release 1" (backlog BL-D7). The project is done only when all three are done.

## Done-criteria referenced (intent section 8)

- **DC1** All acceptance tests pass on `dev01`.
- **DC2** One timed cycle observed with a test schedule (OQ-1): stop, closed page, start, then an admin logs in and lists employees.
- **DC3** Full verification: full profile, load check with 50 employees (p95 under 2 seconds), alarm tests.
- **DC4** Teardown of env, group and singleton, with the clean-up checklist completed.

## Budget rule for every release (Owner, Q-O57)

- AWS Budget alert $2 per month (80% at $1.60, 100% at $2). It is an early signal, not a cap.
- Only singleton stays between sessions. Every check session builds group and env, runs its checks and destroys env and group before it ends (US03 workflows).
- Sessions run on weekdays during office hours and finish deployments before 17:30 ICT, because CD runs outside office hours stop at the pre-flight (US33) and the schedule stops the system at 18:00 (US30).
- **Batching (PO default, RP-D1).** One check session verifies every merged story that changes dev01 since the last session: about one session per 3 to 5 such stories, plus one exit session per release. A story whose checks run only in CI or locally (for example US04) needs no session.
- Each session: build group and env, deploy with one CD run, create the first admin (US08), load the mock data (US17), run QA's dev01 checks, destroy env and group, record the session cost.

## Release 1: working, secure system on dev01

**Goal.** The Owner can build dev01 from the repository, deliver a commit through checked pull requests and one CD run, and an admin can log in securely and keep employee, department and position records, behind TLS, WAF, CloudFront-only access, encrypted data and secrets, audit logging, threat alerts and cost alerts. Each session ends with env and group destroyed.

**Stories (in order).** US01 Walking skeleton on dev01; US02 Budget and alert email; US03 Session destroy workflows; US04 Local run; US05 Pull-request checks; US06 CD run; US07 Secrets and encryption; US08 First admin setup; US09 Log in and log out; US10 Session time limits; US11 CloudFront-only access and TLS on every hop; US12 WAF; US13 Admin login protection; US14 Audit trail and threat alerts; US15 Logs; US16 View and add departments and positions; US17 Employee list and details; US18 Add an employee.

Parallel work is possible after US01: infrastructure stories (US02, US03, US05, US07, US11, US12, US14, US15) and the application chain (US04, then US08, US09, US16 to US18) touch different parts, within the limits of workflow section 6.4.

**Exit check.**
- In one exit session on the lean profile, the acceptance tests of the 102 criteria owned by US01 to US18 pass on dev01, except the time-based test points listed under "Long verification session" below. This is the Release 1 part of DC1.
- The session starts from singleton only and ends with env and group destroyed, and its cost is recorded.
- No done-criterion is complete yet.

**Sizing for verification.** Lean (`awsenv/dev/group/tfvars/lean.tfvars` and `awsenv/dev/env/tfvars/dev01.tfvars`).

## Release 2: complete product and operations on lean

**Goal.** Both roles can do everything in scope: user accounts with temporary passwords, lockout, disable, reset, unlock and role changes; full employee lifecycle with search; department and position rename and removal; English and Vietnamese UI. The system stops and starts on the office-hours schedule with a closed page, alerts on real problems, and failed or badly timed deliveries stop safely.

**Stories (in order).** US19 English and Vietnamese UI; US20 Create user accounts; US21 Set own password; US22 HR member lockout; US23 Disable and re-enable; US24 Reset and unlock; US25 Edit name and role; US26 Edit, deactivate and reactivate employees; US27 Search and filter; US28 Permanent delete; US29 Rename and remove departments and positions; US30 Office-hours stop and start; US31 Closed page; US32 Alarms and dashboard; US33 Safe deliveries.

**Exit check.**
- In the exit sessions on the lean profile, the acceptance tests of the 62 criteria owned by US19 to US33 pass on dev01, and the Release 1 tests still pass. Together with Release 1 this covers DC1 for 164 of the 183 criteria, except the time-based test points below.
- The evening part of the schedule is checked in one session that runs from about 16:30 to 18:30 on a weekday: the 18:00 stop, the closed page by 18:15, no data and no login while stopped, an unsaved form lost, and a CD run after 17:30 stopped at the pre-flight. The start, the closed page until usable and data surviving the cycle are checked with the test schedule in the Release 3 verification session (OQ-1, RP-D2).
- No done-criterion is complete yet.

**Sizing for verification.** Lean.

## Release 3: proven on the full profile, then closed

**Goal.** The Owner proves the system at full sizing (scaling, failover, load, every alert path), observes one stop and start cycle with a test schedule, proves a rebuild from an empty account, and tears everything down with nothing left.

**Stories (in order).** US34 Lean and full profile switch; US35 Load check and auto scaling; US36 Database failover; US37 Alert path tests; US38 Stop and start cycle with a test schedule; US39 Rebuild from an empty account; US40 Final teardown; US41 Break-glass admin recovery (Could; if kept, merged before the final teardown).

**Sequence (OQ-1 answered 2026-11-01: short session with a test schedule).**
1. Develop and merge US34 to US38 and US41; their scripts and procedures are tested in short lean sessions where possible.
2. **Rebuild proof (US39).** With the Owner's explicit approval, destroy singleton, then rebuild singleton from the repository and update the Namecheap NS records. Wait for DNS propagation (allow up to a day) before the verification session, which then applies group and env on this account, so the rebuild runs in the required order from an account holding only the state bucket.
3. **Full verification session, about 2 to 3 hours, on a weekday within office hours.**
   - Lean: build, deploy, setup, mock data.
   - Switch to the full profile (US34) and check a rolling deployment and a rollback on full.
   - Load check with scale-out and scale-in (US35), database failover (US36), alert path tests (US37).
   - Stop and start cycle with the test schedule on the full profile (US38, also the start part of US30 and US31), then reset the schedule to 18:00 and 08:45 ICT.
   - Destroy env and group at the end. Record the session cost.
4. **Final teardown (US40).** Destroy env (if rebuilt), group and singleton, delete the state bucket last by hand, remove the NS records, tick the clean-up checklist, and record the total cost from Cost Explorer the day after.

**Exit check.**
- DC1 complete: all 183 criteria have passing acceptance tests; the hours-long timers by controlled-clock tests (D-PM3).
- DC2: the timed cycle with the test schedule, with timestamps (US38).
- DC3: the full profile with the load check result, scaling, failover and alarm tests (US34 to US37).
- DC4: the teardown with the ticked checklist and the cost record (US40).

**Sizing for verification.** Full for US34 to US38 (only within the verification session), lean for US39, none for US40 after the destroys.

**Expected cost.** About $1 for the verification session (estimate, to verify with the AWS Pricing Calculator). With singleton running all month, the $2 alert is expected to fire; the Owner accepted this (OQ-2).

## Time-based test points

Decided after OQ-1 (D-PM3 in the spec): the hours-long timers are proven by automated tests with a controlled clock in CI and locally, which QA plans per story; the schedule cycle uses the test schedule.

| Story | Test point | How |
| --- | --- | --- |
| US10 | Action at 7 hours 55 minutes succeeds; first action after 8 hours 5 minutes refused | Controlled clock |
| US21 | Temporary password works at 23 hours 55 minutes and is refused at 24 hours 5 minutes | Controlled clock |
| US22 | Lock still holds after 60 minutes and after a stop/start cycle | Controlled clock; stop/start part in the US38 cycle |
| US30 | Start, admin can log in and list employees, data unchanged after the cycle | Test schedule (US38) |
| US31 | Closed page while stopped until the system is usable | Test schedule (US38) |
| US38 | Timed cycle and the full-profile schedule check | Test schedule |

## Decisions log

| ID | Decision | Reason | Affects |
| --- | --- | --- | --- |
| RP-D1 | Batch dev01 checks: one session per 3 to 5 merged stories that change dev01, plus one exit session per release. | Each session costs about $0.20 to $0.30 lean, and singleton already uses most of the $2 alert each month (OQ-2) | All releases |
| RP-D2 | The start half of the schedule (start, closed page until usable, data after the cycle) is checked in the Release 3 verification session with the test schedule (OQ-1), not in Release 2. The weekend rule (no start on Saturday or Sunday) is checked from the schedule definition; no weekend is observed. | A test schedule avoids keeping the layers up overnight (OQ-1); observing a weekend would cost about three days of running layers | US30, US31, US38 |
| RP-D3 | The rebuild proof (US39) destroys and rebuilds singleton before the verification session, with a pause for DNS propagation after the new NS records are set. | A new hosted zone gets new name servers; certificate validation waits for propagation | US39 |
| RP-D4 | Release 1 is the 18 stories US01 to US18. Account management, the language switch, the schedule and alarms move to Release 2. | Smallest set where an admin can work securely end to end on dev01 and the Owner can deliver and destroy safely | Release 1, Release 2 |
