# Intent 001: CMS employee records system

| | |
| --- | --- |
| Intent ID | intent-001 |
| Project | CMS |
| Date | 2026-10-13 |
| Author | Product Owner (agent) |
| Source | Owner's request and requirements conversation of 2026-10-13; Owner's answers to Q-O1 to Q-O7 of 2026-10-13; Owner's decisions of 2026-10-31 on roles, session, lockout, password and first admin (Q-O8 to Q-O12) |
| Status | Approved by Owner on 2026-10-13 (input to gate G1). Revised on 2026-10-13 and on 2026-10-31 to record the Owner's answers and decisions (see Change history); the revisions are confirmed by the Owner at gate G1. |
| Process | `docs/process/ai-native-sdlc-workflow.md` v3, Phase A, Step 1 |
| PRD | Not needed (decided by PO on 2026-10-31): the acceptance criteria, NFR and decisions log in `docs/specs/spec-001.md` were written before Step 1b existed and already cover the product view. A PRD would only duplicate them. |

This document records what the Owner decided. Routine values decided by agents are not repeated here; they are in the "Decisions log" of `docs/specs/spec-001.md`. Acceptance criteria and NFR numbers are in `docs/specs/spec-001.md` (Steps 3 and 3b). The backlog and the release plan are written at Step 5 and are not part of this file.

## 1. Owner's request

> "I want a CMS system to manage about 50 employees, work in office-hour and shutdown for the rest of the day. I have already provide high-architecture."

## 2. Problem

- HR staff and administrators need one place to keep the records of about 50 employees, with each employee assigned to a department and a position.
- The system is needed only during office hours. Running it outside office hours costs money for no benefit, so it must shut down by schedule for the rest of the day and the whole weekend.
- The project is a practice project for the AI-native SDLC workflow. Following the workflow's steps and gates is itself a goal of the project.

## 3. Desired outcome

- A working employee records system named CMS, deployed on the single environment `dev01`, built on the Owner's existing high-level architecture.
- Admins and HR members can log in and maintain employee profiles, departments and positions.
- Admins can manage the user accounts of both roles in the UI (create, edit name and role, disable, re-enable, reset, unlock).
- The UI is available in English and Vietnamese, switchable by the user.
- The system stops and starts automatically on the office-hours schedule, and shows a "closed" page out of hours.
- The system is verified end to end, then all AWS resources are destroyed. There is no production environment.

## 4. Users

| Who | Uses the system? | Notes |
| --- | --- | --- |
| Admin | Yes | Logs in. Can do everything, including managing user accounts (create, edit name and role, disable, re-enable, reset, unlock) and everything an HR member can do. Admin accounts are never locked. |
| HR member | Yes | Logs in the same way as an admin. Manages employees, departments and positions. Has no access to user account management. |
| Employees (about 50) | No | They are the data, not users. They never log in. |

Access is role-based (RBAC) with exactly these two roles. Login works the same way for both roles; the role decides the permissions. There is no manager role and no employee self-service.

## 5. Scope

### 5.1 In scope (Release 1)

1. **Login for both roles.** Session ends after 10 minutes without user activity and after 8 hours at most regardless of activity; a log-out action exists (Q-O8). Password of at least 12 characters containing at least one upper-case letter, one lower-case letter, one digit and one special character (Q-O10). HR member accounts are locked after 5 consecutive failed logins (a successful login resets the count) and stay locked until an admin unlocks them; admin accounts are never locked (Q-O9). Admin logins are protected against brute force without locking the account (PM/SM safeguard, see spec Decisions log D-PM1).
2. **User account management** (admin only): admins create, edit (name and role), disable, re-enable, reset and unlock user accounts of both roles in the UI (Q-O4, Q-O9, Q-O12). The very first admin is created on a one-time setup screen that appears only while no admin account exists (Q-O11), protected by a one-time setup token (PM/SM safeguard, D-PM2). The admin management screen was added by the Owner on 2026-10-13 and widened to both roles on 2026-10-31, before the baseline is frozen; both are scope decisions, not Change Requests.
3. **Employee profiles:** add, edit, deactivate, reactivate, permanently delete (with a confirmation step), search, list (Q-O5).
   - Employee code and work email are each unique across all employees, active or inactive. A duplicate is rejected with a clear error on that field (Q-O6).
4. **Departments and positions:** maintain both lists. Each employee has exactly one department and one position.
   - Removing a department or position that still has employees is blocked, with a message showing how many employees are still assigned. The user reassigns them first (Q-O7).
5. **Scheduled stop/start** of the system around office hours, with a "closed" page out of hours (section 6.2).
6. **Bilingual UI:** English and Vietnamese, switchable. Names and search must handle Vietnamese diacritics.

Employee record fields (complete list):

| Field | Notes |
| --- | --- |
| Employee code | Unique across all employees, active or inactive |
| Full name | Must handle Vietnamese diacritics |
| Work email | Unique across all employees, active or inactive |
| Phone | |
| Department | One per employee |
| Position | One per employee |
| Start date | |
| Status | active / inactive |

User account fields: email (the login identifier), full name, role (admin or HR member), status (active or disabled); HR member accounts can also be locked (Q-O12). Email is fixed after creation; an admin can edit the name and role of another account, not their own role (PM/SM decision, 2026-10-31).

### 5.2 Out of scope

- Employee self-service
- Manager role, and any role other than admin and HR member
- Document or contract upload
- Reports and CSV export
- Audit log (confirmed by the Owner on 2026-10-31, Q-O35)
- Sending email from the application (no welcome or password-reset emails, Q-O13)
- Sensitive fields: national ID, salary, bank account
- Personal details: date of birth, home address, emergency contact

A request for any of these after the baseline is frozen is a Change Request (workflow section 7).

## 6. Constraints

### 6.1 Architecture

The Owner's existing high-level architecture (`20261003_02_high_level_architecture.png` at the repo root) is used as-is, renamed to CMS:

- React UI on S3 behind CloudFront + WAF
- FastAPI (Python 3.13) on ECS Fargate behind an ALB, in private subnets
- RDS PostgreSQL in isolated subnets
- Secrets Manager, KMS, CloudWatch, SNS, CloudTrail, GuardDuty, AWS Budgets
- Region ap-southeast-1
- Terraform in singleton / group / env layers
- GitHub Actions with OIDC

One addition to that architecture: a scheduled stop/start (section 6.2).

Naming: the project is CMS. The hosted zone is `cms.imaprof.ink` and the `dev01` hostname is `dev01.cms.imaprof.ink` (Q-O37, Owner 2026-10-31: only the subdomain is delegated to Route 53; the root domain stays at Namecheap). The architecture diagram and `CLAUDE.md` still carry the name of the project they were copied from. Renaming them is pending (see Q-D6).

### 6.2 Office hours and scheduled shutdown

| Item | Decision |
| --- | --- |
| Office hours | Monday to Friday, 09:00-18:00 ICT (UTC+7) |
| Stop | 18:00: ECS scaled to 0 and RDS stopped |
| Start | The schedule starts both at 08:45 ICT. The system being usable around 09:00 is best effort; there is no hard pass/fail deadline (Q-O2) |
| "Usable" means | An admin can log in and list employees (Q-O2) |
| Weekend | Off all weekend |
| Stays up out of hours | Network, ALB and CloudFront |
| Out-of-hours user experience | Users see a "closed" page |

### 6.3 Environment

- A single environment, `dev01`. No production environment.
- Built, verified, then destroyed.

### 6.4 Cost

- AWS Budget alert at $2 (Owner, 2026-11-01, Q-O57 in the spec; was $10). The env and group layers are destroyed at the end of every check session.
- Lean sizing while iterating; full sizing only for the final verification.

### 6.5 Process

- The Owner is the only approver at every gate (G1-G7). Agents do and propose.
- Work happens only inside the approved baseline.

## 7. Personal-data security requirements

Employee records are personal data (name, work email, phone). The Owner's decisions, together with workflow section 8:

1. **Mock data only.** All data used in the project comes from `testdata/mock/`. No real personal data in prompts, fixtures or logs.
2. **Data minimisation.** The record holds only the eight fields in section 5.1. No sensitive identifiers (national ID, salary, bank account) and no personal details (date of birth, home address, emergency contact) are stored.
3. **Encryption at rest and in transit.**
4. **Access for authenticated users only, by role.** No employee data is reachable without a login as an admin or an HR member. Only admins can reach user account management.
5. **Secrets.** Agents do not read or write secrets (`.env`, keys).
6. **Login rules (Q-O8 to Q-O11, 2026-10-31; replace the values of Q-O3).** Session ends after 10 minutes without user activity and after 8 hours at most; log out exists. Password of at least 12 characters with at least one upper-case letter, one lower-case letter, one digit and one special character. HR member accounts lock after 5 consecutive failed logins and stay locked until an admin unlocks them; admin accounts are never locked.
7. **Safeguards decided by the PM/SM (2026-10-31)** to keep the Owner's choices at common practice: admin logins get brute-force protection that does not lock the account (a progressive delay per account and a WAF rate limit on the login endpoint); the one-time setup screen requires a setup token created at deployment and stored in Secrets Manager, and is refused for good once the first admin exists.

The measurable rules (delays, limits, temporary passwords, message wording) are in the LGN, ROLE, ACC, SETUP and SEC groups of `docs/specs/spec-001.md`.

## 8. Definition of done for the project

The project is done when all four are true:

1. **Acceptance tests:** all acceptance tests pass on `dev01`.
2. **One real timed cycle is observed:** automatic stop at 18:00, "closed" page out of hours, automatic start at 08:45 ICT the next weekday, after which an admin can log in and list employees. Being usable around 09:00 is best effort: the time is recorded, and there is no hard pass/fail deadline.
3. **Full verification:** the full-sizing profile (2-6 ECS tasks, Multi-AZ RDS), a load check with 50 employees' worth of data, and alarm tests. The load check threshold is a 95th percentile response time under 2 seconds (Q-O1).
4. **Teardown:** all AWS resources are destroyed (env, then group, then singleton) and the clean-up checklist is completed.

## 9. Open questions

### 9.1 For the Owner (Steps 3 and 3b, before gate G1)

Q-O1 to Q-O7 were answered by the Owner on 2026-10-13. The answers are the source of truth for the requirements in this file and in `docs/specs/spec-001.md`. Where a later Owner decision (2026-10-31) changes an answer, the later decision applies; this is noted in the table.

| ID | Question | Why it matters | Blocks | Status | Owner's answer (2026-10-13) |
| --- | --- | --- | --- | --- | --- |
| Q-O1 | What is the target response time? | Without a number, performance cannot be tested and the load check in done-criterion 3 has no pass/fail threshold. | Performance NFR; load check | Answered | 95th percentile response time under 2 seconds during office hours. |
| Q-O2 | What is the exact deadline for the system being usable each morning? ("Ready by 09:00" and "started around 08:30" are stated; is 09:00 a hard deadline, and what counts as usable?) | Sets the start time of the schedule and the pass/fail condition of done-criterion 2. | Availability NFR; schedule acceptance criteria | Answered | Best effort around 09:00. The schedule starts the system at 08:45 ICT. There is no hard pass/fail deadline. "Usable" means an admin can log in and list employees. This supersedes "started around 08:30 / ready by 09:00". |
| Q-O3 | What are the session length and the password rules? | Security criteria for login must be measurable. | Admin login acceptance criteria; security NFR | Answered; values replaced on 2026-10-31 | Session ends after 15 minutes idle. Password at least 14 characters with complexity (mixed character classes). Account lockout after 5 failed attempts. Replaced on 2026-10-31 by Q-O8 to Q-O10: 10 minutes idle and 8 hours maximum; at least 12 characters with upper-case, lower-case, digit and special character; lockout of HR members only, ended by an admin. |
| Q-O4 | How many admin accounts are there, and how is the first admin created? | No scope item covers managing admin accounts, so there is currently no defined way for any admin to exist. | Admin login acceptance criteria; capacity NFR | Answered; widened on 2026-10-31 | An admin management screen is in scope for Release 1: admins can create, disable and reset other admins in the UI. Scope addition made before the baseline is frozen, not a Change Request. Widened on 2026-10-31 to user account management for two roles (admin, HR member) with re-enable and unlock; first admin through a one-time setup screen (Q-O11); account numbers decided as a PO default (Q-O28 in the spec). |
| Q-O5 | Can a deactivated employee be reactivated? Can an employee be deleted? | Defines the status lifecycle and whether delete exists at all. | Employee profile acceptance criteria | Answered | A deactivated employee can be reactivated. An employee can also be permanently deleted, with a confirmation step. |
| Q-O6 | Which fields must be unique (employee code, work email)? | Defines validation rules and error cases for add and edit. | Employee profile acceptance criteria | Answered | Employee code and work email are each unique across all employees, active or inactive. A duplicate is rejected with a clear error on that field. |
| Q-O7 | What happens to employees when their department or position is removed? (Removal blocked, employees reassigned, or something else.) | Each employee must have one department and one position, so removal can break that rule. | Departments and positions acceptance criteria | Answered | Removal is blocked, with a message showing how many employees are still assigned. The admin reassigns them first. |

Extra decision given with the answers (no question ID): the UI language is English and Vietnamese, switchable; names and search must handle Vietnamese diacritics.

### 9.2 For the Dev Lead (Basic Design, before gate G2)

These are gaps or contradictions between the Owner's decisions and the existing architecture. The Dev Lead proposes; the Owner decides.

| ID | Question | Why it matters | Blocks | Status |
| --- | --- | --- | --- | --- |
| Q-D1 | The ECS auto scaling minimum of 2 (full sizing) conflicts with a scale-to-zero schedule. How do the two coexist? | Auto scaling could restart tasks after the scheduled stop, or the schedule could fail. | Scheduled stop/start design | Resolved by the Dev Lead, 2026-11-01 (spec Decisions log, Q-D1) |
| Q-D2 | Alarms will fire every evening when ECS and RDS stop, unless suppressed out of hours. How are they handled? | Daily false alerts hide real ones, and the alarm tests in done-criterion 3 need a defined expected behaviour. | Monitoring design; alarm tests | Resolved by the Dev Lead, 2026-11-01 (Q-D2) |
| Q-D3 | A merge to `develop` out of hours would fail its migration and smoke test because the database is stopped. What should the pipeline do? | Deploys would fail for a reason unrelated to the change. | CI/CD design | Resolved by the Dev Lead, 2026-11-01 (Q-D3; CICD-AC14 written). Related wording question escalated as Q-O54 |
| Q-D4 | NAT gateway, ALB and RDS storage keep billing while the system is stopped. How short must the full-sizing run be to respect the $10 budget alert? | The cost constraint may be breached during final verification. | Full verification plan | Answered by the Owner as Q-O57 (2026-11-01): $2 budget alert, env and group destroyed after every session |
| Q-D5 | Where is the "closed" page served from, given that ECS is at 0 and the ALB and CloudFront stay up? | Decides how out-of-hours requests (UI and API) are answered. | Scheduled stop/start design; closed-page acceptance criteria | Resolved by the Dev Lead, 2026-11-01 (Q-D5) |
| Q-D6 | The architecture diagram (`20261003_02_high_level_architecture.png`) and `CLAUDE.md` still carry the old project name. Who does the rename, and when? | The diagram is the input to Basic Design (workflow section 5.1) and should name the right project. | Basic Design start | Resolved by the Dev Lead, 2026-11-01 (Q-D6) |
| Q-D7 | What is the request-count target per task for the second ECS scaling policy (ARCH says "CPU 60% / requests" without a request value)? | The policy cannot be configured or tested without a value. | SCALE-AC04 | Resolved by the Dev Lead, 2026-11-01 (Q-D7; SCALE-AC04 written) |
| Q-D8 | Where are CloudTrail logs delivered, and how are they encrypted? ARCH shows CloudTrail but no log destination. | A trail needs a destination; retention (14 days, OBS-AC02) and encryption (SEC-AC07) apply to it, and teardown must remove it. | SEC-AC07, SEC-AC11, OBS-AC02, TDN-AC02 | Resolved by the Dev Lead, 2026-11-01 (Q-D8) |
| Q-D9 | How is the access-log bucket encrypted? To verify: ALB access logs may not support delivery to a bucket encrypted with a customer managed KMS key, which would conflict with "KMS keys for S3" if read as every bucket. | Decides whether SEC-AC06 or SEC-AC07 applies to that bucket. | SEC-AC07 | Resolved by the Dev Lead, 2026-11-01 (Q-D9) |
| Q-D10 | Which WAF managed rule groups are enabled, and how is the ALB restricted to traffic from CloudFront only? | QA needs the rule groups to craft the blocked requests, and the mechanism to know what a direct request to the ALB returns. | SEC-AC04, NET-AC06 | Resolved by the Dev Lead, 2026-11-01 (Q-D10) |
| Q-D11 | What is the bootstrap sequence on an empty account (state bucket, first singleton apply before the CI role exists, repository variables), and which manual steps does it need beyond NS delegation, SNS confirmation and reading the setup token? | IAC-AC13 allows only documented manual steps. | IAC-AC08, IAC-AC13 | Resolved by the Dev Lead, 2026-11-01 (Q-D11) |
| Q-D12 | KMS keys and Secrets Manager secrets enter a waiting period when deleted. How does a rebuild after a teardown avoid name or alias conflicts with items still pending deletion? | A rebuild soon after teardown could fail on the same names. | IAC-AC13, TDN-AC02 | Resolved by the Dev Lead, 2026-11-01 (Q-D12) |
| Q-D13 | How is the setup token created at deployment and stored in Secrets Manager so that its value never enters the Terraform state, plan output or logs, and how does the Owner read it? (Added 2026-10-31.) | SEC-AC09 forbids secret values in state; a token generated by Terraform in the usual way would be stored there. | SETUP-AC02, SEC-AC09 | Resolved by the Dev Lead, 2026-11-01 (Q-D13) |
| Q-D14 | How does the WAF login rate rule match the login and setup endpoints, and does WAF support a limit of 20 requests per 5 minutes? (Added 2026-10-31; if the limit is not supported, the lowest supported limit is proposed.) | The rule cannot be configured or tested without the match and a supported limit. | SEC-AC14 | Resolved by the Dev Lead, 2026-11-01 (Q-D14) |
| Q-D15 | If no admin can log in (for example the only admin forgets the password), how is admin access recovered? Setup is refused for good once an admin exists, there is no email service, and admins cannot reset themselves. (Added 2026-10-31.) | Without a documented recovery path the only way back is rebuilding the database, which loses all data. | ACC-AC07, SETUP-AC05 | Resolved by the Dev Lead, 2026-11-01 (Q-D15) |

### 9.3 Follow-up questions for the Owner

The follow-up questions Q-O8 to Q-O53 of `docs/specs/spec-001.md` were resolved on 2026-10-31: the Owner decided Q-O8 to Q-O11, the two-role model and Q-O35; the PM/SM decided two security safeguards; the Product Owner decided the remaining routine questions as defaults under workflow section 8 "Decision tiers". Every decision is in the spec's "Decisions log" and can be overridden by the Owner at G1.

Still open for the Owner, because only the Owner holds the value (details in the spec's "Open questions for the Owner"):


## 10. Change history

| Date | Change | Reason |
| --- | --- | --- |
| 2026-10-13 | First version, approved by the Owner. | Step 1 |
| 2026-10-13 | Revised after the Owner answered Q-O1 to Q-O7 and gave one extra decision. (1) Scope: added the admin management screen (create, disable, reset other admins); added reactivate and permanent delete with confirmation to employee profiles; added the uniqueness rule for employee code and work email; added the blocked-removal rule for departments and positions; added the bilingual UI (English and Vietnamese, switchable, Vietnamese diacritics in names and search). (2) Section 6.2: start changed from "around 08:30, ready by 09:00" to "schedule starts at 08:45 ICT, usable around 09:00 best effort, no hard deadline"; "usable" defined. (3) Section 7: login rules recorded (15 minutes idle, 14 characters with complexity, lockout after 5 failed attempts). (4) Section 8: done-criterion 2 reworded to match Q-O2; done-criterion 3 now names the Q-O1 threshold. (5) Section 9.1: Q-O1 to Q-O7 marked as answered with the Owner's answer; section 9.3 added, pointing to the follow-up questions in the spec. Sections 3 and 4 updated to match. Section 9.2 unchanged. | Owner's answers of 2026-10-13 (Steps 3 and 3b) |
| 2026-10-14 | Owner's direction recorded: focus also on the infrastructure and container parts of the approved architecture. The Owner was offered a smaller application scope and chose to keep it exactly as it is, so the application scope in this file is unchanged. Infrastructure, container and delivery acceptance criteria (groups IAC, NET, CNT, CICD, SEC, OBS, SCALE, COST, TDN), the NFR additions, Owner questions Q-O36 to Q-O53 and Dev Lead questions Q-D7 to Q-D12 were added to `docs/specs/spec-001.md`. No other section of this file changed. | Owner's direction of 2026-10-14 (Steps 3 and 3b) |
| 2026-10-31 | Revised after the Owner's decisions of 2026-10-31. (1) Scope change: two roles with RBAC, admin and HR member; "admin management" became user account management for both roles (create, disable, re-enable, reset, unlock); sections 2, 3, 4 and 5.1 items 1, 2 and 4 updated, user account fields added to 5.1. (2) Login rules replaced (Q-O8 to Q-O10): 10 minutes idle and 8 hours maximum, log out; at least 12 characters with four character classes; HR member lockout after 5 consecutive failures until an admin unlocks; admins never locked. (3) First admin through a one-time setup screen (Q-O11). (4) PM/SM safeguards recorded in section 7 item 7: admin brute-force protection without lockout, setup token in Secrets Manager. (5) Section 5.2: audit log confirmed out of scope (Q-O35); application email sending added as out of scope (Q-O13); roles other than admin and HR member excluded. (6) Section 6.1: hostname pattern `cms.imaprof.ink` / `dev01.cms.imaprof.ink` recorded. (7) Section 9: Q-O3 and Q-O4 annotated with the later decisions; Dev Lead questions Q-D13 to Q-D15 added; section 9.3 now lists only Q-O37 and Q-O38 as open. Q-O13 to Q-O53 (other than Q-O35, Q-O37, Q-O38) decided as Product Owner defaults in the spec's Decisions log. | Owner's decisions of 2026-10-31 and the decision tiers of workflow section 8 (Steps 3 and 3b) |
| 2026-10-31 | PM/SM decision on Q-O12: an admin can edit the full name and role of another user account; email stays fixed; an admin cannot change their own role; a role change ends that user's sessions. Sections 3, 4 and 5.1 updated. |
| 2026-10-31 | Q-O37 answered by the Owner: domain `imaprof.ink`; only `cms.imaprof.ink` is delegated to Route 53. |
| 2026-10-31 | Q-O38 answered by the Owner: alert address provided, kept outside the repository (never committed). |
| 2026-11-01 | Constraint in section 6.4 changed by the Owner (Q-O57): AWS Budget alert $2 instead of $10; env and group destroyed at the end of every check session. Section 9.2 gained a Status column (Dev Lead, Step 4b). | Owner's answer at G2 |
