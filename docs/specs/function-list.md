# Function list: CMS (spec-001)

| | |
| --- | --- |
| Source | `docs/specs/spec-001.md`, section "Basic Design" (BD-6 API overview, BD-7 functional specification) |
| Author | Dev Lead, Step 4b, 2026-11-01 |
| Status | Draft for Owner approval at G2 |
| Use | The Product Owner builds the backlog (Step 5) from this list; each story names the function IDs it delivers. QA traces tests to the acceptance criteria named here. |

Roles: "Anyone" means no session is needed. "Both" means admin and HR member. "Owner" means the Owner acting with AWS or GitHub access, outside the application. "Scheduler" and "CI" are AWS or GitHub automation.

## Application functions

| Function ID | Name | Screen | API | Role | Acceptance criteria |
| --- | --- | --- | --- | --- | --- |
| F-SYS-01 | System status | All (on load and after a 503) | `GET /api/v1/status` | Anyone | SCH-AC02, SCH-AC03, SCH-AC07, SETUP-AC01, SETUP-AC05 |
| F-SYS-02 | Health check | - | `GET /healthz`, `GET /api/healthz` | Anyone (ALB, smoke test) | CNT-AC03, CICD-AC10, CICD-AC12 |
| F-SET-01 | Create first admin | SCR-01 | `POST /api/v1/setup` | Anyone with the setup token | SETUP-AC01 to SETUP-AC06, LGN-AC09, LGN-AC10, ACC-AC03, SEC-AC13, SEC-AC14 |
| F-AUTH-01 | Log in | SCR-02 | `POST /api/v1/auth/login` | Both | LGN-AC01, LGN-AC02, LGN-AC11 to LGN-AC18, LGN-AC20, ROLE-AC05, SEC-AC13, SEC-AC14 |
| F-AUTH-02 | Log out | Header of every screen | `POST /api/v1/auth/logout` | Both | LGN-AC08 |
| F-AUTH-03 | Current user | Every screen on open | `GET /api/v1/auth/me` | Both | LGN-AC04, ROLE-AC04 |
| F-AUTH-04 | Change own password (also forced change) | SCR-03 | `POST /api/v1/auth/password` | Both | LGN-AC09, LGN-AC10, LGN-AC19, LGN-AC21 |
| F-AUTH-05 | Session and permission check | Every screen | Every session API | Both | LGN-AC03 to LGN-AC07, LGN-AC19, ROLE-AC02 to ROLE-AC04, ACC-AC06, ACC-AC14 |
| F-ACC-01 | List accounts | SCR-30 | `GET /api/v1/accounts` | Admin | ACC-AC01, ROLE-AC04 |
| F-ACC-02 | View account | SCR-31 | `GET /api/v1/accounts/{id}` | Admin | ROLE-AC04, ACC-AC12 |
| F-ACC-03 | Create account | SCR-31, SCR-32 | `POST /api/v1/accounts` | Admin | ACC-AC02 to ACC-AC05, ROLE-AC01, ROLE-AC04, LGN-AC19, LGN-AC20 |
| F-ACC-04 | Edit account (full name, role) | SCR-31 | `PATCH /api/v1/accounts/{id}` | Admin | ACC-AC10, ACC-AC12 to ACC-AC14, ROLE-AC01, ROLE-AC04 |
| F-ACC-05 | Disable account | SCR-30 | `POST /api/v1/accounts/{id}/disable` | Admin | ACC-AC06, ACC-AC07, ROLE-AC04 |
| F-ACC-06 | Re-enable account | SCR-30 | `POST /api/v1/accounts/{id}/enable` | Admin | ACC-AC10, ROLE-AC04 |
| F-ACC-07 | Reset password | SCR-30, SCR-32 | `POST /api/v1/accounts/{id}/reset-password` | Admin | ACC-AC08, ACC-AC09, LGN-AC13, LGN-AC19, LGN-AC20, ROLE-AC04 |
| F-ACC-08 | Unlock account | SCR-30 | `POST /api/v1/accounts/{id}/unlock` | Admin | ACC-AC11, LGN-AC13, ROLE-AC04 |
| F-EMP-01 | List and search employees | SCR-10 | `GET /api/v1/employees` | Both | EMP-AC15 to EMP-AC18, EMP-AC20 |
| F-EMP-02 | View employee | SCR-12 | `GET /api/v1/employees/{id}` | Both | EMP-AC19, EMP-AC21 |
| F-EMP-03 | Add employee | SCR-11 | `POST /api/v1/employees` | Both | EMP-AC01 to EMP-AC07, EMP-AC19, EMP-AC21, ROLE-AC05 |
| F-EMP-04 | Edit employee | SCR-11 | `PUT /api/v1/employees/{id}` | Both | EMP-AC08, EMP-AC09, EMP-AC19, ROLE-AC05 |
| F-EMP-05 | Deactivate employee | SCR-12 | `POST /api/v1/employees/{id}/deactivate` | Both | EMP-AC10 |
| F-EMP-06 | Reactivate employee | SCR-12 | `POST /api/v1/employees/{id}/reactivate` | Both | EMP-AC11 |
| F-EMP-07 | Delete employee permanently | SCR-12, SCR-13 | `DELETE /api/v1/employees/{id}` | Both | EMP-AC06, EMP-AC12 to EMP-AC14, ROLE-AC03, ROLE-AC05 |
| F-ORG-01 | List departments or positions | SCR-20, SCR-21, SCR-11 (selects) | `GET /api/v1/departments`, `GET /api/v1/positions` | Both | ORG-AC01, ORG-AC09 |
| F-ORG-02 | Add department or position | SCR-20, SCR-21 | `POST /api/v1/departments`, `POST /api/v1/positions` | Both | ORG-AC02 to ORG-AC04, ORG-AC09 |
| F-ORG-03 | Rename department or position | SCR-20, SCR-21 | `PATCH /api/v1/departments/{id}`, `PATCH /api/v1/positions/{id}` | Both | ORG-AC04, ORG-AC05 |
| F-ORG-04 | Remove department or position | SCR-20, SCR-21 | `DELETE /api/v1/departments/{id}`, `DELETE /api/v1/positions/{id}` | Both | ORG-AC06 to ORG-AC08, ROLE-AC03 |
| F-LNG-01 | Switch language | Every screen except SCR-00 | None (UI only) | Anyone | LNG-AC01 to LNG-AC06 |
| F-UI-01 | Show closed page | SCR-00 | Uses F-SYS-01 | Anyone | SCH-AC02 to SCH-AC05, SCH-AC09, SCH-AC10 |

## Operations and delivery functions

| Function ID | Name | Where | Role | Acceptance criteria |
| --- | --- | --- | --- | --- |
| F-OPS-01 | Scheduled stop (18:00 ICT Mon-Fri) | App Auto Scaling scheduled action, EventBridge Scheduler (`office_hours_schedule`) | Scheduler | SCH-AC01, SCH-AC05, SCH-AC08, SCH-AC10, SCH-AC11, SCALE-AC07, OBS-AC05 |
| F-OPS-02 | Scheduled start (08:45 ICT Mon-Fri; alarm actions 09:15) | Same as F-OPS-01 | Scheduler | SCH-AC06, SCH-AC07, SCH-AC08, SCH-AC11, SCALE-AC07, LGN-AC13 |
| F-OPS-03 | Delivery run (CD), with pre-flight | GitHub Actions (`image_build_push_dev`, `deploy_ecs_dev`, `deploy_web_dev`, `terraform_apply_dev_*`) | Owner starts it (Q-O54); CI deploy role | CICD-AC06 to CICD-AC14, CICD-AC16, CNT-AC04, CNT-AC05, CNT-AC07 |
| F-OPS-04 | Database migration task | One-off ECS task | CI deploy role | CICD-AC08, CICD-AC09 |
| F-OPS-05 | Pull-request checks | GitHub Actions on pull requests | CI plan role | CICD-AC01 to CICD-AC05, IAC-AC10, IAC-AC11, CNT-AC01, CNT-AC02, CNT-AC05 |
| F-OPS-06 | Alerting | `modules/monitoring` (alarms, EventBridge rules), SNS alert topic | Automation | OBS-AC01 to OBS-AC10, COST-AC01 |
| F-OPS-07 | Admin recovery (break-glass) | Manual workflow, one-off ECS task, secret `cms-dev01/admin-recovery` | Owner | ACC-AC07, SETUP-AC05, SEC-AC10, SEC-AC13 (Q-D15) |
| F-OPS-08 | Bootstrap and rebuild | Runbook, bootstrap script, Terraform layers | Owner | IAC-AC01 to IAC-AC09, IAC-AC12 to IAC-AC14, NET-AC01 to NET-AC11, SEC-AC01 to SEC-AC12 (Q-D11) |
| F-OPS-09 | Profile switch (lean, full) | tfvars of group and env (Q-O55) | Owner | SCALE-AC01 to SCALE-AC06, SCALE-AC08, SCALE-AC09, COST-AC02, COST-AC03 |
| F-OPS-10 | Teardown and clean-up | Destroy workflows, clean-up checklist | Owner | TDN-AC01 to TDN-AC05, COST-AC04, CICD-AC15 |
| F-OPS-11 | Local run | `docker compose up` | Developer | CNT-AC06 |

## Coverage check

All 183 acceptance criteria of spec-001 are named by at least one function above (checked on 2026-11-01 by expanding every "to" range). Criteria about the system as a whole (for example EMP-AC21 data minimisation, ROLE-AC01, and the infrastructure criteria under F-OPS-08) are also tested against the system as a whole, not only through the named function.
