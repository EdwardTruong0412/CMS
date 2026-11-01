# PRD-<NNN>: <Feature name>

<!--
How to use this template (Product Owner):
- Copy to docs/prd/prd-<NNN>-<short-slug>.md. <NNN> matches the source intent number.
- Write only when the PRD trigger in .claude/agents/product-owner.md says one is needed.
- Fill every section or write "Not applicable: <reason>". Do not delete sections.
- Sections marked [Dev Lead] are left as placeholders by the PO; the Dev Lead fills them at Step 4b.
  The PO may record business constraints there, never a technical design.
- Acceptance criteria and NFR numbers live in docs/specs/spec-<NNN>.md (single source).
  This PRD references them by ID and never copies their text.
- Delete these comments when the PRD is written.
-->

| | |
| --- | --- |
| PRD ID | prd-<NNN> |
| Version | 0.1 (Draft) |
| Date | YYYY-MM-DD |
| Author | Product Owner (agent) |
| Source intent | `docs/intent/intent-<NNN>.md` |
| Spec | `docs/specs/spec-<NNN>.md` (Acceptance Criteria, NFR, Basic Design) |
| Change Request | `docs/change-requests/CR-<xxx>.md`, or "None (in baseline)" |
| Status | Draft / Ready for G1 / Approved at G1 on YYYY-MM-DD |
| Process | `docs/process/ai-native-sdlc-workflow.md` v3 |

**Changelog:**
- `0.1` (YYYY-MM-DD) - First draft.

---

## 1. Executive summary

<!-- 3 to 6 lines: what the feature is, who it is for, which problem it solves, and how it fits CMS (user management on AWS, dev01 only). -->

## 2. Goals and non-goals

### 2.1 Goals

| # | Goal | Measured by (KPI) |
| --- | --- | --- |
| G1 | <outcome> | <number, threshold and how it is measured> |

### 2.2 Non-goals (out of scope for this PRD)

- <item>: <why it is out, and where it goes instead (later release, CR, never)>

## 3. Stakeholders and personas

| Role | Description | Main permissions in this feature |
| --- | --- | --- |
| Admin | | |
| HR member | | |
| Owner (approver) | Approves every gate G1-G7 | None in the app |

<!-- A new role or user group is a scope change: Owner question, not a PO default. -->

## 4. Functional scope

### 4.1 Capabilities

1. **<Capability>** - <one line>.

### 4.2 Priority (MoSCoW)

| Level | Capabilities |
| --- | --- |
| Must | |
| Should | |
| Could | |
| Won't (this release) | |

## 5. Data and business rules

### 5.1 Business entities

<!-- Business view only: entity, meaning, key attributes, owner role, personal data yes/no.
     Tables, columns, indexes and the Alembic migration belong to the Dev Lead (5.3). -->

| Entity | Meaning | Key attributes | Personal data? |
| --- | --- | --- | --- |

### 5.2 Business rules

| ID | Rule | Example | Related AC |
| --- | --- | --- | --- |
| BR-01 | | | `<GROUP>-ACnn` |

### 5.3 Data model and migration [Dev Lead]

<!-- Placeholder. Dev Lead: SQLAlchemy models, PostgreSQL tables, constraints, indexes, Alembic revision(s). -->

## 6. Business flows and user stories

### 6.1 Main flow

<!-- Numbered steps or a mermaid flowchart of the golden path, from the user's point of view. -->

### 6.2 User stories - golden path

> Conventions:
> - Story ID `US<NN>`, continuing the numbering in `docs/backlog.md`.
> - Stories are end-to-end (UI + API + DB + infra where needed). Do not split into technical tasks.
> - Acceptance criteria are defined in `docs/specs/spec-<NNN>.md`; list their IDs here.

#### US<NN> <title>  *(Priority: Must)*

As a <user>, I want <capability>, so that <outcome>.

Acceptance criteria: `<GROUP>-AC01`, `<GROUP>-AC02`
Release: <n>   Source: `docs/intent/intent-<NNN>.md`

### 6.3 User stories - negative and edge paths

<!-- Invalid input, permission denied, concurrent edits, lockout, the system being in scheduled shutdown,
     dependency failure. Every Must story has at least one negative path. -->

### 6.4 Story map

| Story | Capability (4.1) | Acceptance criteria | Test level (unit / API / E2E / infra) |
| --- | --- | --- | --- |

## 7. UI / UX

<!-- Screens added or changed, navigation, empty/error states, EN and VI labels, accessibility.
     Screen list and transitions in detail: Dev Lead at Step 4b. -->

## 8. Integrations and external dependencies

| System | Direction | Purpose | Failure behaviour |
| --- | --- | --- | --- |

## 9. Non-functional requirements (ISO 25010)

<!-- Summary only; numbers and NFR IDs live in the spec. Mark "No change" when the feature keeps the current target. -->

| Characteristic | Requirement summary | NFR / AC ID in spec |
| --- | --- | --- |
| Performance efficiency | | |
| Capacity | | |
| Availability (incl. office-hours schedule) | | |
| Security | | |
| Compatibility | | |
| Usability (incl. EN / VI) | | |
| Maintainability | | |
| Portability | | |

## 10. Infrastructure and delivery impact

<!-- Infrastructure and containers are first-class in this project. The PO states WHAT must be true
     (reachability, isolation, scaling, delivery behaviour) with AC IDs; the Dev Lead states HOW. -->

### 10.1 Impact checklist

| Area | Affected? | Requirement (what) | AC ID |
| --- | --- | --- | --- |
| Terraform layer: singleton / group / env | | | |
| Network (public / private / isolated tiers) | | | |
| Container image (build, scan, non-root, health) | | | |
| CI/CD workflows (PR checks, deploy, migration, smoke test) | | | |
| Secrets and KMS | | | |
| Monitoring (alarms, dashboard, SNS) | | | |
| Sizing: lean (`dev01.tfvars`) vs full (`dev01_full.tfvars`) | | | |
| Teardown / clean-up checklist | | | |

### 10.2 Technical architecture [Dev Lead]

<!-- Placeholder. Dev Lead: modules touched in modules/, API endpoints, new AWS resources, workflow changes. -->

## 11. Security and permissions

### 11.1 Permission matrix

| Action | Admin | HR member | Not logged in |
| --- | :---: | :---: | :---: |

### 11.2 Personal data

<!-- Which personal data is created, read, stored, logged or exported; masking in logs; retention; mock data only in testdata/mock/. -->

### 11.3 Audit

<!-- Which actions are recorded, by whom, and where (app log, CloudTrail). -->

## 12. Monitoring and operations

<!-- New or changed alarms, log metric filters, dashboard widgets (all in modules/monitoring), runbook notes. -->

## 13. Cost

| Item | Lean sizing | Full sizing | Within $10 budget? |
| --- | --- | --- | --- |

<!-- Cost beyond the approved budget is an Owner question. -->

## 14. Release plan

| Release | Stories | Business value | Dependencies |
| --- | --- | --- | --- |

<!-- Sprint scheduling and task split belong to the PM/SM and Dev Lead at Sprint Planning. -->

## 15. Acceptance summary (feature Definition of Done)

- [ ] Every Must story has all its AC IDs passing (QA test report).
- [ ] Golden path and negative paths verified on `dev01`.
- [ ] Infrastructure checks green: `terraform validate`, tflint, Trivy config and image scans.
- [ ] Monitoring for the feature in place and alarm tests run.
- [ ] EN and VI labels complete.
- [ ] Decisions log and open questions closed or carried forward with an owner.

## 16. Risks and mitigations

| Risk | Level | Mitigation | Owner role |
| --- | --- | --- | --- |

## 17. Glossary

| Term | Meaning |
| --- | --- |

## 18. References

- `docs/intent/intent-<NNN>.md`
- `docs/specs/spec-<NNN>.md`
- `20261003_02_high_level_architecture.png`
- <standards used for defaults, e.g. OWASP ASVS, AWS Well-Architected>

## 19. Data migration

<!-- Existing data affected, migration steps (always via Alembic), validation, rollback. "Not applicable" if no existing data changes. -->

## 20. Mock data

<!-- Fixtures in testdata/mock/ needed to demo and test the feature. Never real personal data. -->

## Decisions log

| ID | Decision | Reason | Criteria affected | Decided by |
| --- | --- | --- | --- | --- |
| D-01 | | | | PO default |

## Open questions

<!-- Owner questions only (scope, contradiction, cost/architecture, weaker security, irreversible, Owner-held values). -->

| # | Question | Why it matters | Blocks | Recommended answer |
| --- | --- | --- | --- | --- |
