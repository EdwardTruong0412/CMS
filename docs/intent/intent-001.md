# Intent 001: CMS employee records system

| | |
| --- | --- |
| Intent ID | intent-001 |
| Project | CMS |
| Date | 2026-10-13 |
| Author | Product Owner (agent) |
| Source | Owner's request and requirements conversation of 2026-10-13 |
| Status | Approved by Owner on 2026-10-13 (input to gate G1) |
| Process | `docs/process/ai-native-sdlc-workflow.md` v3, Phase A, Step 1 |

This document records only what the Owner decided. Anything not decided is listed in section 9 as an open question. Acceptance criteria, NFR numbers, the backlog and the release plan are written in later steps (3, 3b, 5) and are not part of this file.

## 1. Owner's request

> "I want a CMS system to manage about 50 employees, work in office-hour and shutdown for the rest of the day. I have already provide high-architecture."

## 2. Problem

- HR/admin staff need one place to keep the records of about 50 employees, with each employee assigned to a department and a position.
- The system is needed only during office hours. Running it outside office hours costs money for no benefit, so it must shut down by schedule for the rest of the day and the whole weekend.
- The project is a practice project for the AI-native SDLC workflow. Following the workflow's steps and gates is itself a goal of the project.

## 3. Desired outcome

- A working employee records system named CMS, deployed on the single environment `dev01`, built on the Owner's existing high-level architecture.
- HR/admin staff can log in and maintain employee profiles, departments and positions.
- The system stops and starts automatically on the office-hours schedule, and shows a "closed" page out of hours.
- The system is verified end to end, then all AWS resources are destroyed. There is no production environment.

## 4. Users

| Who | Uses the system? | Notes |
| --- | --- | --- |
| HR/admin staff | Yes | The only users. One role. They log in. |
| Employees (about 50) | No | They are the data, not users. They never log in. |

There is no manager role and no employee self-service.

## 5. Scope

### 5.1 In scope (Release 1)

1. **Admin login.**
2. **Employee profiles:** add, edit, deactivate, search, list.
3. **Departments and positions:** maintain both lists. Each employee has exactly one department and one position.
4. **Scheduled stop/start** of the system around office hours, with a "closed" page out of hours (section 6.2).

Employee record fields (complete list):

| Field | Notes |
| --- | --- |
| Employee code | |
| Full name | |
| Work email | |
| Phone | |
| Department | One per employee |
| Position | One per employee |
| Start date | |
| Status | active / inactive |

### 5.2 Out of scope

- Employee self-service
- Manager role
- Document or contract upload
- Reports and CSV export
- Audit log
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

Naming: the project is CMS. The architecture diagram and `CLAUDE.md` still carry the name of the project they were copied from. Renaming them is pending (see Q-D6).

### 6.2 Office hours and scheduled shutdown

| Item | Decision |
| --- | --- |
| Office hours | Monday to Friday, 09:00-18:00 ICT (UTC+7) |
| Stop | 18:00: ECS scaled to 0 and RDS stopped |
| Start | Around 08:30: both started, so the system is ready by 09:00 |
| Weekend | Off all weekend |
| Stays up out of hours | Network, ALB and CloudFront |
| Out-of-hours user experience | Users see a "closed" page |

### 6.3 Environment

- A single environment, `dev01`. No production environment.
- Built, verified, then destroyed.

### 6.4 Cost

- AWS Budget alert at $10.
- Lean sizing while iterating; full sizing only for the final verification.

### 6.5 Process

- The Owner is the only approver at every gate (G1-G7). Agents do and propose.
- Work happens only inside the approved baseline.

## 7. Personal-data security requirements

Employee records are personal data (name, work email, phone). The Owner's decisions, together with workflow section 8:

1. **Mock data only.** All data used in the project comes from `testdata/mock/`. No real personal data in prompts, fixtures or logs.
2. **Data minimisation.** The record holds only the eight fields in section 5.1. No sensitive identifiers (national ID, salary, bank account) and no personal details (date of birth, home address, emergency contact) are stored.
3. **Encryption at rest and in transit.**
4. **Access for authenticated admins only.** No employee data is reachable without an admin login.
5. **Secrets.** Agents do not read or write secrets (`.env`, keys).

Measurable security criteria (for example password rules and session length) are not yet decided; see Q-O3.

## 8. Definition of done for the project

The project is done when all four are true:

1. **Acceptance tests:** all acceptance tests pass on `dev01`.
2. **One real timed cycle is observed:** automatic stop at 18:00, "closed" page out of hours, automatic start and a working login by 09:00 the next weekday.
3. **Full verification:** the full-sizing profile (2-6 ECS tasks, Multi-AZ RDS), a load check with 50 employees' worth of data, and alarm tests.
4. **Teardown:** all AWS resources are destroyed (env, then group, then singleton) and the clean-up checklist is completed.

## 9. Open questions

None of these are answered. No requirement is to be derived from them until the Owner decides.

### 9.1 For the Owner (Steps 3 and 3b, before gate G1)

| ID | Question | Why it matters | Blocks |
| --- | --- | --- | --- |
| Q-O1 | What is the target response time? | Without a number, performance cannot be tested and the load check in done-criterion 3 has no pass/fail threshold. | Performance NFR; load check |
| Q-O2 | What is the exact deadline for the system being usable each morning? ("Ready by 09:00" and "started around 08:30" are stated; is 09:00 a hard deadline, and what counts as usable?) | Sets the start time of the schedule and the pass/fail condition of done-criterion 2. | Availability NFR; schedule acceptance criteria |
| Q-O3 | What are the session length and the password rules? | Security criteria for login must be measurable. | Admin login acceptance criteria; security NFR |
| Q-O4 | How many admin accounts are there, and how is the first admin created? | No scope item covers managing admin accounts, so there is currently no defined way for any admin to exist. | Admin login acceptance criteria; capacity NFR |
| Q-O5 | Can a deactivated employee be reactivated? Can an employee be deleted? | Defines the status lifecycle and whether delete exists at all. | Employee profile acceptance criteria |
| Q-O6 | Which fields must be unique (employee code, work email)? | Defines validation rules and error cases for add and edit. | Employee profile acceptance criteria |
| Q-O7 | What happens to employees when their department or position is removed? (Removal blocked, employees reassigned, or something else.) | Each employee must have one department and one position, so removal can break that rule. | Departments and positions acceptance criteria |

### 9.2 For the Dev Lead (Basic Design, before gate G2)

These are gaps or contradictions between the Owner's decisions and the existing architecture. The Dev Lead proposes; the Owner decides.

| ID | Question | Why it matters | Blocks |
| --- | --- | --- | --- |
| Q-D1 | The ECS auto scaling minimum of 2 (full sizing) conflicts with a scale-to-zero schedule. How do the two coexist? | Auto scaling could restart tasks after the scheduled stop, or the schedule could fail. | Scheduled stop/start design |
| Q-D2 | Alarms will fire every evening when ECS and RDS stop, unless suppressed out of hours. How are they handled? | Daily false alerts hide real ones, and the alarm tests in done-criterion 3 need a defined expected behaviour. | Monitoring design; alarm tests |
| Q-D3 | A merge to `develop` out of hours would fail its migration and smoke test because the database is stopped. What should the pipeline do? | Deploys would fail for a reason unrelated to the change. | CI/CD design |
| Q-D4 | NAT gateway, ALB and RDS storage keep billing while the system is stopped. How short must the full-sizing run be to respect the $10 budget alert? | The cost constraint may be breached during final verification. | Full verification plan |
| Q-D5 | Where is the "closed" page served from, given that ECS is at 0 and the ALB and CloudFront stay up? | Decides how out-of-hours requests (UI and API) are answered. | Scheduled stop/start design; closed-page acceptance criteria |
| Q-D6 | The architecture diagram (`20261003_02_high_level_architecture.png`) and `CLAUDE.md` still carry the old project name. Who does the rename, and when? | The diagram is the input to Basic Design (workflow section 5.1) and should name the right project. | Basic Design start |
