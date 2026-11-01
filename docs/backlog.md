# Product Backlog: intent-001 (CMS)

| | |
| --- | --- |
| Source | `docs/intent/intent-001.md`; criteria and NFR in `docs/specs/spec-001.md`; functions in `docs/specs/function-list.md` |
| Author | Product Owner, workflow Step 5, 2026-11-01 |
| Status | Proposal for the Owner, input to G3. The priority order below is the Product Owner's proposal; the final order is the Owner's call. |
| PRD | None for intent-001 (decided in the intent), so each story line links to its detail section in this file |

Coverage: 183 of 183 criteria assigned, each to exactly one story (checked on 2026-11-01 by counting the criterion IDs in the "Delivers" lines, see Decisions log BL-D1).

## Stories in priority order

- US01 Walking skeleton on dev01 → docs/backlog.md#us01
- US02 Budget and alert email reach the Owner → docs/backlog.md#us02
- US03 Owner ends a session by destroying env and group → docs/backlog.md#us03
- US04 Developer runs the whole stack locally → docs/backlog.md#us04
- US05 Pull-request checks guard develop → docs/backlog.md#us05
- US06 Owner deploys develop to dev01 with one CD run → docs/backlog.md#us06
- US07 Secrets and stored data protected with project keys → docs/backlog.md#us07
- US08 First admin setup → docs/backlog.md#us08
- US09 Log in and log out → docs/backlog.md#us09
- US10 Session time limits → docs/backlog.md#us10
- US11 Only CloudFront reaches the API, encrypted on every hop → docs/backlog.md#us11
- US12 WAF blocks attacks and floods → docs/backlog.md#us12
- US13 Admin login protected against password guessing → docs/backlog.md#us13
- US14 Audit trail and threat alerts → docs/backlog.md#us14
- US15 Application and access logs kept 14 days → docs/backlog.md#us15
- US16 View and add departments and positions → docs/backlog.md#us16
- US17 Employee list and details → docs/backlog.md#us17
- US18 Add an employee → docs/backlog.md#us18
- US19 English and Vietnamese UI → docs/backlog.md#us19
- US20 Admin lists and creates user accounts → docs/backlog.md#us20
- US21 Users set their own password → docs/backlog.md#us21
- US22 HR member accounts lock after repeated failures → docs/backlog.md#us22
- US23 Admin disables and re-enables accounts → docs/backlog.md#us23
- US24 Admin resets passwords and unlocks accounts → docs/backlog.md#us24
- US25 Admin edits account name and role → docs/backlog.md#us25
- US26 Edit, deactivate and reactivate employees → docs/backlog.md#us26
- US27 Search and filter employees → docs/backlog.md#us27
- US28 Permanently delete an employee → docs/backlog.md#us28
- US29 Rename and remove departments and positions → docs/backlog.md#us29
- US30 Office-hours stop and start → docs/backlog.md#us30
- US31 Closed page out of hours → docs/backlog.md#us31
- US32 Alarms and dashboard → docs/backlog.md#us32
- US33 Failed or out-of-hours deliveries stop safely → docs/backlog.md#us33
- US34 Owner switches between lean and full profiles → docs/backlog.md#us34
- US35 Load check and auto scaling on the full profile → docs/backlog.md#us35
- US36 Database failover on the full profile → docs/backlog.md#us36
- US37 Every alert path tested → docs/backlog.md#us37
- US38 Stop and start cycle observed with a test schedule → docs/backlog.md#us38
- US39 Rebuild from an empty account → docs/backlog.md#us39
- US40 Final teardown leaves nothing behind → docs/backlog.md#us40
- US41 Owner recovers admin access (break-glass) → docs/backlog.md#us41

Releases (detail in `docs/release-plan.md`): Release 1 is US01 to US18, Release 2 is US19 to US33, Release 3 is US34 to US41.

## How to read the story sections

- **Delivers** lists the acceptance criteria the story owns, by ID only; the text is in `docs/specs/spec-001.md`. Each criterion is owned by exactly one story. Criterion IDs appear in backticks only on "Delivers" lines, so that the coverage count can be checked mechanically.
- **Also checked in** names later stories that must keep a criterion of this story passing, and why (BL-D2).
- **Functions** are the IDs of `docs/specs/function-list.md`.
- **Size** is relative, for one Dev in one `/story` run: S about 1 day, M 1 to 2 days, L 2 to 3 days (BL-D4).
- **Priority** is MoSCoW (BL-D3). Release is the release of `docs/release-plan.md`.
- Stories describe what the user or the Owner can do. They are not split into technical tasks; that happens at Sprint Planning (workflow section 6.2).

<a id="us01"></a>
## US01 Walking skeleton on dev01

As the Owner, I want to bootstrap the Terraform state bucket and build the singleton, group and env layers in the lean profile from the repository, so that the app hostname serves the UI over HTTPS and the API answers its health and status checks from the database, and every later story has a running system to build on.

Delivers: `IAC-AC03`, `IAC-AC04`, `IAC-AC05`, `IAC-AC06`, `IAC-AC07`, `IAC-AC08`, `IAC-AC12`, `IAC-AC14`, `NET-AC01`, `NET-AC02`, `NET-AC03`, `NET-AC04`, `NET-AC07`, `NET-AC08`, `NET-AC09`, `NET-AC10`, `NET-AC11`, `CNT-AC01`, `CNT-AC02`, `CNT-AC03`, `SEC-AC01`, `SEC-AC02`, `SCALE-AC01`

Also checked in:
- IAC-AC04, IAC-AC12, IAC-AC14: every later story that adds or changes Terraform (US02, US03, US05 to US07, US11, US12, US14, US15, US30, US32 to US34, US41); IAC-AC12 for the full profile in US34; IAC-AC14 also in US40 (tag search).
- IAC-AC05: US02 (budget reaches the alert topic without reading group state), US39.
- NET-AC07: US14 (CloudTrail bucket), US15 (access-log bucket).
- NET-AC08: US09 (test point: an unauthenticated data request under `/api/` gets the API's refusal).
- CNT-AC03: US06 and US33 (rollout uses the health check).
- SCALE-AC01: US34 (return from full to lean).

Functions: F-SYS-01, F-SYS-02, F-OPS-08
Depends on: none
Priority: Must   Size: L   Release: 1   Source: docs/intent/intent-001.md

Notes: thin on purpose. No CI/CD, WAF, customer managed keys, monitoring or schedule yet; each comes in its own story. Until US05 and US06 exist the Owner applies the layers and pushes the first image with documented local commands. This is the largest story; if Sprint Planning finds it over 3 days, the Product Owner splits it at refinement.

<a id="us02"></a>
## US02 Budget and alert email reach the Owner

As the Owner, I want the $2 monthly AWS Budget and the SNS alert topic with my confirmed email subscription in place, so that I hear about cost and alerts from the first check session on.

Delivers: `OBS-AC04`, `COST-AC01`

Also checked in:
- COST-AC01: US37 (the budget path stays wired), US40 (teardown report says whether a notification fired).

Functions: F-OPS-06
Depends on: US01
Priority: Must   Size: S   Release: 1   Source: docs/intent/intent-001.md

<a id="us03"></a>
## US03 Owner ends a session by destroying env and group

As the Owner, I want manual-only workflows to destroy the env and group layers, force-unlock state and create the `dev01` workspace, so that I can end every check session with only singleton left, as the $2 budget rule requires (Q-O57).

Delivers: `CICD-AC15`

Functions: F-OPS-10
Depends on: US01
Priority: Must   Size: S   Release: 1   Source: docs/intent/intent-001.md

Notes: the complete teardown with singleton, the state bucket and the clean-up checklist is US40.

<a id="us04"></a>
## US04 Developer runs the whole stack locally

As a developer, I want `docker compose up` to start the API, PostgreSQL and the UI with mock data only, so that every application story can be built and tested without AWS.

Delivers: `CNT-AC06`

Functions: F-OPS-11
Depends on: US01
Priority: Must   Size: S   Release: 1   Source: docs/intent/intent-001.md

<a id="us05"></a>
## US05 Pull-request checks guard develop

As the Owner, I want every pull request to `develop` to run the lint, test, build, Terraform and Trivy checks through OIDC without changing anything in AWS, and to be blocked from merging when a check fails, so that only checked code reaches `develop`.

Delivers: `CICD-AC01`, `CICD-AC02`, `CICD-AC03`, `CICD-AC04`, `CICD-AC05`, `IAC-AC01`, `IAC-AC10`, `IAC-AC11`

Also checked in:
- CICD-AC01, CICD-AC02, IAC-AC10, IAC-AC11: every later pull request.

Functions: F-OPS-05
Depends on: US01
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us06"></a>
## US06 Owner deploys develop to dev01 with one CD run

As the Owner, I want to start one CD run on `develop` that builds, scans and pushes the image, applies Terraform, migrates the database, rolls out the service, publishes the UI and smoke-tests the result within 30 minutes, so that dev01 runs exactly the merged commit with no manual step.

Delivers: `CICD-AC06`, `CICD-AC07`, `CICD-AC08`, `CICD-AC12`, `CICD-AC13`, `CICD-AC16`, `CNT-AC04`, `CNT-AC05`, `CNT-AC07`

Also checked in:
- CNT-AC07: US07, US08 (secrets exist and must stay out of the image).
- CICD-AC16: US33, US39 (the first run of a session, see "Notes for Sprint Planning").

Functions: F-OPS-03, F-OPS-04
Depends on: US05
Priority: Must   Size: L   Release: 1   Source: docs/intent/intent-001.md

<a id="us07"></a>
## US07 Secrets and stored data protected with project keys

As the Owner, I want the database password, JWT key and setup token generated into Secrets Manager without ever entering Terraform state, logs or the image, every data store encrypted at rest (with the project's customer managed keys where required), the app's roles limited to their own secrets, and 7-day database backups, so that the mock personal data and the credentials stay protected.

Delivers: `SEC-AC06`, `SEC-AC07`, `SEC-AC08`, `SEC-AC09`, `SEC-AC10`, `SETUP-AC02`, `SCALE-AC09`

Also checked in:
- SEC-AC07: US14 (CloudTrail destination), US15 (access-log bucket).
- SEC-AC08, SEC-AC09: US08 (setup token in use), US09 (JWT key in use).
- SEC-AC10: US41 (the recovery role is separate).
- SETUP-AC02: US08, US39 (token created at each deployment).

Functions: F-OPS-08
Depends on: US01
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us08"></a>
## US08 First admin setup

As the Owner, I want a one-time setup screen that, given the setup token, creates the first admin with a strong password and then never appears again, so that the system gets its first administrator without any default account.

Delivers: `SETUP-AC01`, `SETUP-AC03`, `SETUP-AC04`, `SETUP-AC05`, `SETUP-AC06`, `LGN-AC09`, `LGN-AC10`, `LGN-AC18`

Also checked in:
- LGN-AC09, LGN-AC10: US21 (own and forced password change).
- LGN-AC18: US20, US21, US24 (every stored password).
- SETUP-AC05: US30 (after a stop/start cycle), US39 (after a redeployment on a rebuilt system).

Functions: F-SET-01, F-SYS-01
Depends on: US07
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us09"></a>
## US09 Log in and log out

As an admin or HR member, I want to log in with my email and password, see one generic message when a login fails, and log out from any screen, so that only authenticated users reach any data.

Delivers: `LGN-AC01`, `LGN-AC02`, `LGN-AC03`, `LGN-AC04`, `LGN-AC08`, `LGN-AC15`, `SEC-AC13`

Also checked in:
- LGN-AC02: US18 (test point: the work email of an employee with no account is refused).
- LGN-AC03: every later story that adds a data operation (US16 to US18, US20, US23 to US29).
- LGN-AC04, LGN-AC08: every later story that adds a screen.
- LGN-AC15: US13 (throttled), US21 (expired temporary password), US22 (locked HR member), US23 (disabled account).
- SEC-AC13: US15 (access-log bucket), US20 and US24 (temporary passwords).

Functions: F-AUTH-01, F-AUTH-02, F-AUTH-03, F-AUTH-05
Depends on: US08
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us10"></a>
## US10 Session time limits

As an admin or HR member, I want my session to end after 10 minutes without activity and 8 hours after login at most, so that an unattended browser does not stay open to the data.

Delivers: `LGN-AC05`, `LGN-AC06`, `LGN-AC07`

Functions: F-AUTH-05
Depends on: US09
Priority: Must   Size: S   Release: 1   Source: docs/intent/intent-001.md

Notes: the 8-hour test points are proven by automated tests with a controlled clock (D-PM3 in the spec, after OQ-1).

<a id="us11"></a>
## US11 Only CloudFront reaches the API, encrypted on every hop

As the Owner, I want the ALB to accept traffic only from the project's CloudFront distribution over HTTPS, the database to accept only TLS connections, and nothing but CloudFront and the ALB to accept connections from the internet, so that the WAF and TLS cannot be bypassed.

Delivers: `NET-AC05`, `NET-AC06`, `SEC-AC03`

Also checked in:
- NET-AC05: US39 (inventory of the rebuilt account).

Functions: F-OPS-08
Depends on: US01
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us12"></a>
## US12 WAF blocks attacks and floods

As the Owner, I want the WAF on CloudFront to block common attack patterns and any IP address that sends more than 1000 requests in 5 minutes, so that the public hostname is protected without blocking normal use.

Delivers: `SEC-AC04`, `SEC-AC05`

Also checked in:
- SEC-AC04: US13 (an ordinary login is not blocked), US17 (an ordinary employee-list request is not blocked).

Functions: F-OPS-08
Depends on: US01
Priority: Must   Size: S   Release: 1   Source: docs/intent/intent-001.md

<a id="us13"></a>
## US13 Admin login protected against password guessing

As an admin, I want repeated failed logins on my account to be slowed by a growing delay and by the WAF login rate limit instead of a lockout, so that guessing my password is impractical while I can never be locked out.

Delivers: `LGN-AC11`, `LGN-AC16`, `LGN-AC17`, `SEC-AC14`

Also checked in:
- LGN-AC11: US22 (the same reset of the count on an HR member account).

Functions: F-AUTH-01
Depends on: US09, US12
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us14"></a>
## US14 Audit trail and threat alerts

As the Owner, I want CloudTrail to record management API calls and GuardDuty findings of medium or higher to reach me by email, so that I can see who changed what and hear about threats.

Delivers: `SEC-AC11`, `SEC-AC12`, `OBS-AC07`, `OBS-AC10`

Also checked in:
- OBS-AC07: US37.
- OBS-AC10: US32 and US33 (every later alarm, metric filter and EventBridge rule).

Functions: F-OPS-06, F-OPS-08
Depends on: US02
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us15"></a>
## US15 Application and access logs kept 14 days

As the Owner, I want the API container logs in CloudWatch and the CloudFront and ALB access logs in S3, each kept for 14 days, so that I can investigate problems without paying to keep old logs.

Delivers: `OBS-AC01`, `OBS-AC02`, `OBS-AC03`

Functions: F-OPS-06
Depends on: US01
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us16"></a>
## US16 View and add departments and positions

As an admin or HR member, I want to view the department and position lists and add entries with unique names that keep their Vietnamese diacritics, so that employees can be assigned to them.

Delivers: `ORG-AC01`, `ORG-AC02`, `ORG-AC03`, `ORG-AC04`, `ORG-AC09`, `ROLE-AC02`

Also checked in:
- ORG-AC02: US18 and US26 (selectable in the employee add and edit forms).
- ORG-AC04: US29 (rename).
- ORG-AC09: US17, US18 (shown in the employee list, details and forms).
- ROLE-AC02: every later story that adds an employee, organisation or account action (US17, US18, US20, US23 to US29).

Functions: F-ORG-01, F-ORG-02
Depends on: US09
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us17"></a>
## US17 Employee list and details

As an admin or HR member, I want to page through all employees sorted by code and open one employee's details, with the 50 mock employees loadable into dev01, so that I can find any record.

Delivers: `EMP-AC15`, `EMP-AC16`, `EMP-AC21`

Also checked in:
- EMP-AC21: US18, US26 (no forbidden field in any form or response).

Functions: F-EMP-01, F-EMP-02
Depends on: US16
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

Notes: loading the 50 mock employees (with their departments and positions) from `testdata/mock/` into a freshly built dev01 is part of this story's capability, because every check session starts with an empty database (Q-O57). `testdata/mock/` is created at workflow Step 7.

<a id="us18"></a>
## US18 Add an employee

As an admin or HR member, I want to add an employee with validated fields, a unique code and work email, and a department and position chosen from the lists, so that new staff are recorded correctly.

Delivers: `EMP-AC01`, `EMP-AC02`, `EMP-AC03`, `EMP-AC04`, `EMP-AC05`, `EMP-AC06`, `EMP-AC07`, `EMP-AC19`

Also checked in:
- EMP-AC06: US26 (edit), US28 (test point: code and email reused after a permanent delete).
- EMP-AC07, EMP-AC19: US26 (edit form).

Functions: F-EMP-03
Depends on: US17
Priority: Must   Size: M   Release: 1   Source: docs/intent/intent-001.md

<a id="us19"></a>
## US19 English and Vietnamese UI

As an admin or HR member, I want to switch every screen between English and Vietnamese, with my choice remembered in my browser, so that each user works in their own language.

Delivers: `LNG-AC01`, `LNG-AC02`, `LNG-AC03`, `LNG-AC04`, `LNG-AC05`, `LNG-AC06`

Also checked in:
- LNG-AC01, LNG-AC02, LNG-AC03, LNG-AC06: every later story that adds a screen or a message (US20 to US31).

Functions: F-LNG-01
Depends on: US08, US09
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

<a id="us20"></a>
## US20 Admin lists and creates user accounts

As an admin, I want to list every user account and create an account for an admin or an HR member with a one-time temporary password, so that colleagues can get access, while HR members cannot reach account management at all.

Delivers: `ACC-AC01`, `ACC-AC02`, `ACC-AC03`, `ACC-AC04`, `ACC-AC05`, `ROLE-AC01`, `ROLE-AC03`, `ROLE-AC04`

Also checked in:
- ACC-AC01: US22 (locked shown), US23 (disabled shown).
- ACC-AC03: US25 (full-name rule on edit).
- ACC-AC05: US24 (temporary password after a reset).
- ROLE-AC01: US25 (role changed only by an admin, never their own).
- ROLE-AC03: US26, US28, US29 (HR member edits, deletes and removes).
- ROLE-AC04: US23, US24, US25 (each further account operation refused to an HR member).

Functions: F-ACC-01, F-ACC-03, F-AUTH-05
Depends on: US09
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

<a id="us21"></a>
## US21 Users set their own password

As a user with a temporary password, I want to be made to choose my own password at first login, with the temporary one expiring after 24 hours; and as any logged-in user I want to change my password later, so that only I know my password.

Delivers: `LGN-AC19`, `LGN-AC20`, `LGN-AC21`

Also checked in:
- LGN-AC19, LGN-AC20: US24 (after a reset).

Functions: F-AUTH-04
Depends on: US20
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

Notes: the 24-hour expiry test points are proven by automated tests with a controlled clock (D-PM3 in the spec, after OQ-1).

<a id="us22"></a>
## US22 HR member accounts lock after repeated failures

As the Owner, I want an HR member account to lock after 5 consecutive failed logins until an admin acts, without affecting any other account, so that guessing an HR member's password is stopped.

Delivers: `LGN-AC12`, `LGN-AC13`, `LGN-AC14`

Also checked in:
- LGN-AC13: US24 (only unlock or reset ends the lock), US30 (still locked after a stop/start cycle).

Functions: F-AUTH-01
Depends on: US13, US20
Priority: Must   Size: S   Release: 2   Source: docs/intent/intent-001.md

<a id="us23"></a>
## US23 Admin disables and re-enables accounts

As an admin, I want to disable another user's account (never my own) and re-enable it later, so that people who should not have access lose it at once and the system always keeps an active admin.

Delivers: `ACC-AC06`, `ACC-AC07`, `ACC-AC10`

Also checked in:
- ACC-AC07: US25 (together with the own-role rule).
- ACC-AC10: US25 (test point: an edit that changes the email is refused).

Functions: F-ACC-05, F-ACC-06
Depends on: US20
Priority: Must   Size: S   Release: 2   Source: docs/intent/intent-001.md

<a id="us24"></a>
## US24 Admin resets passwords and unlocks accounts

As an admin, I want to reset another user's password to a new temporary password and to unlock a locked HR member, so that users who forgot their password or are locked out can get back in.

Delivers: `ACC-AC08`, `ACC-AC09`, `ACC-AC11`

Also checked in:
- ACC-AC08: US41 (the recovery task resets an admin the same way).

Functions: F-ACC-07, F-ACC-08
Depends on: US21, US22
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

<a id="us25"></a>
## US25 Admin edits account name and role

As an admin, I want to view an account and change its full name and role (never my own role), with a role change taking effect at the user's next request, so that mistakes and role changes are fixed without creating new accounts.

Delivers: `ACC-AC12`, `ACC-AC13`, `ACC-AC14`

Functions: F-ACC-02, F-ACC-04
Depends on: US20, US22
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

<a id="us26"></a>
## US26 Edit, deactivate and reactivate employees

As an admin or HR member, I want to edit an employee's details and to deactivate and reactivate the employee, so that records stay correct when people change role or leave.

Delivers: `EMP-AC08`, `EMP-AC09`, `EMP-AC10`, `EMP-AC11`

Functions: F-EMP-04, F-EMP-05, F-EMP-06
Depends on: US18
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

<a id="us27"></a>
## US27 Search and filter employees

As an admin or HR member, I want one search box that matches name, code or email while ignoring Vietnamese diacritics and case, plus department, position and status filters, so that I find an employee quickly.

Delivers: `EMP-AC17`, `EMP-AC18`, `EMP-AC20`

Functions: F-EMP-01
Depends on: US17
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

<a id="us28"></a>
## US28 Permanently delete an employee

As an admin or HR member, I want to delete an employee permanently after a confirmation dialog, so that records created by mistake can be removed without touching any user account.

Delivers: `EMP-AC12`, `EMP-AC13`, `EMP-AC14`, `ROLE-AC05`

Functions: F-EMP-07
Depends on: US18
Priority: Must   Size: S   Release: 2   Source: docs/intent/intent-001.md

<a id="us29"></a>
## US29 Rename and remove departments and positions

As an admin or HR member, I want to rename a department or position, and to remove one only when no employee is assigned, with the number still assigned shown otherwise, so that the lists stay tidy without leaving employees unassigned.

Delivers: `ORG-AC05`, `ORG-AC06`, `ORG-AC07`, `ORG-AC08`

Functions: F-ORG-03, F-ORG-04
Depends on: US18
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

<a id="us30"></a>
## US30 Office-hours stop and start

As the Owner, I want dev01 to stop at 18:00 and start at 08:45 ICT every Monday to Friday by itself, with no data lost and no start or stop control in the UI, so that the system runs only in office hours.

Delivers: `SCH-AC01`, `SCH-AC05`, `SCH-AC06`, `SCH-AC07`, `SCH-AC08`, `SCH-AC10`

Also checked in:
- SCH-AC08: US38 (the observed cycle).
- SCH-AC10: US31 (no control on any screen).

Functions: F-OPS-01, F-OPS-02
Depends on: US17, US20
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

Notes: the start is observed with the test schedule of US38 (OQ-1), not after a real overnight stop.

<a id="us31"></a>
## US31 Closed page out of hours

As an admin or HR member, I want a closed page in English and Vietnamese with the office hours whenever the system is stopped or still starting, so that I know why it is unavailable and no data is ever shown.

Delivers: `SCH-AC02`, `SCH-AC03`, `SCH-AC04`, `SCH-AC09`

Functions: F-UI-01, F-SYS-01
Depends on: US30, US18
Priority: Must   Size: S   Release: 2   Source: docs/intent/intent-001.md

<a id="us32"></a>
## US32 Alarms and dashboard

As the Owner, I want the ten alarms and the dev01 dashboard, with the WAF alarm in us-east-1 forwarded to the same alert topic and alarm emails paused out of hours, so that I hear about real problems and only about them.

Delivers: `OBS-AC05`, `OBS-AC06`, `IAC-AC09`

Functions: F-OPS-06
Depends on: US02, US12, US15, US30
Priority: Must   Size: L   Release: 2   Source: docs/intent/intent-001.md

<a id="us33"></a>
## US33 Failed or out-of-hours deliveries stop safely

As the Owner, I want a CD run to stop before any change when the system is outside office hours, to stop when the migration fails, and to roll back automatically with an alert when new tasks are unhealthy, so that a bad or badly timed deployment never leaves dev01 broken.

Delivers: `CICD-AC09`, `CICD-AC10`, `CICD-AC11`, `CICD-AC14`, `OBS-AC08`

Also checked in:
- CICD-AC10, CICD-AC11: US34 (the full-profile part: no failed request during a deployment, rollback in the full profile).
- OBS-AC08: US37.

Functions: F-OPS-03, F-OPS-04, F-OPS-06
Depends on: US06, US30
Priority: Must   Size: M   Release: 2   Source: docs/intent/intent-001.md

<a id="us34"></a>
## US34 Owner switches between lean and full profiles

As the Owner, I want to switch dev01 between lean and full sizing with only the tfvars files of the group and env layers, and to keep the full profile only for the full verification, so that I pay for full sizing only when I need it.

Delivers: `SCALE-AC02`, `SCALE-AC03`, `SCALE-AC04`, `COST-AC02`, `COST-AC03`

Also checked in:
- COST-AC02: every later check session.
- COST-AC03: the full-verification session of US35 to US38.

Functions: F-OPS-09
Depends on: US30
Priority: Must   Size: M   Release: 3   Source: docs/intent/intent-001.md

<a id="us35"></a>
## US35 Load check and auto scaling on the full profile

As the Owner, I want a repeatable load check with the 50 mock employees and 5 virtual users that measures the 95th percentile and shows auto scaling out and back in, so that done-criterion 3 has a measured result.

Delivers: `SCALE-AC05`, `SCALE-AC08`

Functions: F-OPS-09
Depends on: US34, US26, US27
Priority: Must   Size: M   Release: 3   Source: docs/intent/intent-001.md

<a id="us36"></a>
## US36 Database failover on the full profile

As the Owner, I want one database reboot with failover on the full profile to recover with no manual action and no data change, so that I know the Multi-AZ standby works.

Delivers: `SCALE-AC06`

Functions: F-OPS-09
Depends on: US34, US17
Priority: Must   Size: S   Release: 3   Source: docs/intent/intent-001.md

<a id="us37"></a>
## US37 Every alert path tested

As the Owner, I want every alarm, the GuardDuty rule and the rollback rule triggered once during the full verification, with each email arriving within 10 minutes, so that I can trust the alerts.

Delivers: `OBS-AC09`

Functions: F-OPS-06
Depends on: US14, US32, US33, US34
Priority: Must   Size: M   Release: 3   Source: docs/intent/intent-001.md

<a id="us38"></a>
## US38 Stop and start cycle observed with a test schedule

As the Owner, I want one stop and start cycle observed and timed on dev01 with a test schedule set a few minutes ahead, also with the full profile, so that done-criterion 2 is proven within one short session (OQ-1).

Delivers: `SCH-AC11`, `SCALE-AC07`

Functions: F-OPS-01, F-OPS-02
Depends on: US30, US31, US34
Priority: Must   Size: S   Release: 3   Source: docs/intent/intent-001.md

Notes: (OQ-1 answered 2026-11-01) runs in the short full-profile session of Release 3 with the test schedule; no overnight run. Earlier note: needed the env and group layers to exist overnight, and the full profile through the stop and the start, which the current one-weekday limit on the full profile does not allow; see OQ-1.

<a id="us39"></a>
## US39 Rebuild from an empty account

As the Owner, I want to rebuild the whole system from an account that holds only the state bucket, following the documented runbook with only the listed manual steps, so that I know the repository alone describes the system.

Delivers: `IAC-AC02`, `IAC-AC13`

Functions: F-OPS-08
Depends on: every infrastructure story (US01 to US03, US05 to US07, US11, US12, US14, US15, US30, US32, US33)
Priority: Must   Size: M   Release: 3   Source: docs/intent/intent-001.md

Notes: needs a singleton destroy first, which is destructive and needs the Owner's explicit approval. A new hosted zone gets new name servers, so the Namecheap NS records change and DNS propagation can delay the env build; the release plan schedules for this.

<a id="us40"></a>
## US40 Final teardown leaves nothing behind

As the Owner, I want to destroy env, group and singleton, delete the state bucket last and tick a clean-up checklist with proof, so that the project ends with nothing left that bills.

Delivers: `TDN-AC01`, `TDN-AC02`, `TDN-AC03`, `TDN-AC04`, `TDN-AC05`, `COST-AC04`

Functions: F-OPS-10
Depends on: US39, US35, US36, US37, US38
Priority: Must   Size: M   Release: 3   Source: docs/intent/intent-001.md

<a id="us41"></a>
## US41 Owner recovers admin access (break-glass)

As the Owner, I want a manual recovery workflow that resets a chosen admin's password to a temporary one I read from Secrets Manager, so that I can regain admin access without rebuilding the database.

Delivers: no criterion of its own (BL-D6). Pass condition: the reset behaves as US24 describes for a user reset, and the "Also checked in" items of US07 and US09 hold for the recovery task (least privilege, no secret in logs), following Dev Lead decision Q-D15.

Functions: F-OPS-07
Depends on: US24, US06
Priority: Could   Size: S   Release: 3   Source: docs/intent/intent-001.md

## Notes for Sprint Planning

These are not tasks; they are points the story plans must settle (owner in brackets).

1. **First CD run of a session** (Dev Lead, plans of US06 and US33). Under Q-O57 every check session starts with no env layer. The pre-flight check of US33 stops a run when the ECS service has no running tasks or the database is not available, and the 30-minute limit of US06 applies to every successful run. The plans must say how a session's first deployment works (for example, the env apply workflow first, then the CD run) so that both criteria hold.
2. **Order of the UI publish and the smoke test** (Dev Lead, plan of US06). Basic Design BD-2 shows the UI sync after the smoke test, while the smoke test checks that `/` serves the UI of the deployed commit. The plan sets the order.
3. **Per-session setup and mock data** (Dev Lead and QA). Every session needs the first admin created again (US08) and the mock data loaded (US17); both belong in the session runbook.
4. **Time-based test points** (QA). The 8-hour session, the 24-hour temporary password expiry, the 60-minute lock and the overnight cycle: answered by OQ-1 (test schedule) and D-PM3 (controlled-clock tests).

## Decisions log

Backlog-only choices made by the Product Owner under workflow section 8 "Decision tiers". The Owner can override any row.

| ID | Decision | Reason | Affects |
| --- | --- | --- | --- |
| BL-D1 | Coverage is checked by counting the criterion IDs written in backticks on the "Delivers" lines: 183 IDs, 183 distinct, matching the 17 group totals of the spec summary. Criterion IDs are written in backticks nowhere else in this file. | Makes "each criterion in exactly one story" checkable mechanically | All stories |
| BL-D2 | Assignment rule. A criterion belongs to the story that first delivers its behaviour. A cross-cutting criterion (a rule for every screen, operation or resource) belongs to the first story where it can be proven for what exists then, and later stories keep it ("Also checked in"). When one test point of a criterion needs a later capability, that test point runs in the later story named under "Also checked in". | Follows the coordinator's rule; keeps each criterion's owner clear while every story keeps earlier rules passing | All stories |
| BL-D3 | Every story that owns a criterion is Must, because done-criterion 1 requires every acceptance test to pass and intent-001 places its whole scope in its Release 1. US41 owns none and is Could. The order of the list, not MoSCoW, carries the priority. | MoSCoW would otherwise suggest that approved scope is optional | All stories |
| BL-D4 | Sizes: S about 1 day, M 1 to 2 days, L 2 to 3 days for one Dev in one `/story` run. No story is larger than L. US01, US06 and US32 are L. | Matches the one-to-three-day limit | All stories |
| BL-D5 | US01 is the thinnest working slice on dev01 (UI and API through the app hostname, database reached). The budget and alert email (US02) and the session destroy workflows (US03) come straight after it, because under Q-O57 every session must end with env and group destroyed and cost alerts must exist before spending grows. | Owner's budget rule of 2026-11-01; infrastructure is first-class (Owner, 2026-10-14) | US01 to US03 |
| BL-D6 | US41 (break-glass recovery, Q-D15) is kept as a story with no criterion of its own and priority Could. Under Q-O57 the database is rebuilt every session and the first admin is created again by setup, so the recovery path matters only if a session's admin password is lost mid-session. No new criterion is added, because criteria live in the spec and were approved at G1. | Keeps the approved design traceable without changing the approved criteria | US41 |
| BL-D7 | The release numbers 1 to 3 of `docs/release-plan.md` are delivery increments of the scope that intent-001 and the spec call "Release 1". Where a criterion says "In Release 1" it means the whole intent-001 scope. | Avoids reading the spec's "Release 1" as this plan's first increment | Release plan |
| BL-D8 | The language story (US19) opens Release 2 rather than Release 1. Release 1 screens are already built on the English and Vietnamese message catalogues decided in D-DL8, so adding the switch later needs little rework. | Keeps Release 1 the smallest working, secure system | US19 |
| BL-D9 | Loading the 50 mock employees into dev01 is part of US17, not a separate story. | Every session starts with an empty database (Q-O57); the list story is the first that needs the data | US17 |

## Open questions for the Owner

Only Owner-tier items (workflow section 8). Neither blocks Release 1 or Release 2 development.

### OQ-1 One long verification session for the overnight checks

**Answered by the Owner on 2026-11-01:** no long session. The cycle is checked with a test schedule set a few minutes ahead (SCH-AC11, SCALE-AC07 reworded), and the long timers by controlled-clock tests (D-PM3). Spec Decisions log row OQ-1.

- **Question.** May the final verification run as one long session of about 30 hours (start on a Monday to Thursday morning, end the next afternoon) that keeps the env and group layers up overnight, with the full profile from the afternoon of day 1 through the 18:00 stop and the 08:45 start until the end of day 2?
- **Why it matters.** Three things need real elapsed time and cannot happen in a 1 to 2 hour session: the observed cycle (done-criterion 2, SCH-AC11), the schedule holding with the full profile (SCALE-AC07, which needs the full profile through a stop and the next start), and the long test points (the 8-hour session of LGN-AC07, the 24-hour temporary password expiry of LGN-AC20, the lock that still holds after 60 minutes and after a stop/start cycle of LGN-AC13). Also, COST-AC03 limits the full profile to one weekday within office hours, which contradicts SCALE-AC07; both were approved at G1, so only the Owner can choose which gives way.
- **Cost.** Rough estimate, to verify with the AWS Pricing Calculator: about $5 to $7 for the session (lean office hours about $0.15 per hour, full office hours about $0.27 per hour, full overnight while stopped about $0.17 per hour). The $2 budget alert will fire at 80% and 100%. Doing the overnight cycle in lean and SCALE-AC07 in a second full-profile night would cost more.
- **Blocks.** US38 and the exit of Release 3 (and the dev01 run of the long test points of US10, US21, US22 and US30).
- **Recommended answer.** Yes. Run one long session that combines the cycle, the full-profile schedule check, the long test points and the full verification of US35 to US37, then destroy env and group the same afternoon. The Product Owner then rewords COST-AC03 (same ID) to "the full profile is applied on a weekday within office hours and is returned to lean or destroyed by 18:00 on the next weekday, spanning at most one scheduled stop and start".

### OQ-2 Monthly cost above the $2 alert

**Answered by the Owner on 2026-11-01:** keep the $2 alert and accept that it fires in most months; batching rule RP-D1 stands. Spec Decisions log row OQ-2.

- **Question.** Do you accept that the $2 budget alert will fire in most months of active work, while the Product Owner batches dev01 checks so that each release needs only a few sessions?
- **Why it matters.** Singleton alone costs roughly $1.50 to $1.70 per month (the customer managed KMS key for CloudTrail about $1, the Route 53 zone $0.50, small amounts for ECR, CloudTrail storage and GuardDuty), which is close to the 80% threshold of $1.60 before any session. Each lean check session of 1 to 2 hours adds about $0.20 to $0.30. If KMS keys pending deletion are billed during their 7-day window (the Dev Lead marked this "verify at plan time"), each session's two env keys add roughly $0.45 more. All figures are estimates to verify.
- **Blocks.** Nothing directly; it sets how often check sessions can run.
- **Recommended answer.** Yes, accept it. Keep the $2 alert as your early signal (it is not a cap), keep the architecture as approved (moving CloudTrail off its customer managed key would go below the CIS recommendation), and approve the batching rule of the release plan: one check session per 3 to 5 merged stories that change dev01, plus one exit session per release.
