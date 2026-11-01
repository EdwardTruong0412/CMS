# Mock data

The only data any agent, test or dev01 session uses (`.claude/rules/global.md` rule 7, workflow section 8). Every value is invented. Emails use the reserved `example.test` domain, and phone numbers are made up.

| File | Content |
| --- | --- |
| `departments.json` | 6 departments, `[{"name": ...}]` |
| `positions.json` | 8 positions, `[{"name": ...}]` |
| `employees.json` | 50 employees with exactly the eight fields of intent 5.1 (EMP-AC21) |

Employee fields: `employee_code`, `full_name`, `work_email`, `phone` (`null` when not given), `department` and `position` (by name, from the two lists), `start_date` (ISO `YYYY-MM-DD` in the file; the UI shows DD/MM/YYYY), and `status` (`active` or `inactive`).

## Rules the data follows

Checked by script before the data was committed (PM/SM, 2026-11-01):

- **Format rules of EMP-AC03.** Codes `EMP001` to `EMP050`. Names are at most 100 characters. Phones are optional: an optional `+`, then 8 to 15 digits; 7 employees have none. Every date is a valid calendar date.
- **Uniqueness of EMP-AC04 to EMP-AC06.** Codes and emails are unique, ignoring case. Department and position names are unique within their list (ORG-AC04).
- **Capacity.** 50 employees, 6 departments and 8 positions, within the NFR limits of 20 departments and 20 positions.
- **Status.** 5 employees are inactive: EMP012, EMP019, EMP028, EMP036 and EMP045.

## Data built in for the spec's test points

| Criterion | What the data guarantees |
| --- | --- |
| EMP-AC16 | 50 rows give 3 pages of 20, 20 and 10, and `EMP001` is first |
| EMP-AC17 | A search for `001` matches only EMP001 |
| EMP-AC19 | "Nguyễn Thị Hồng Ánh" (EMP001), "Đỗ Đức Dũng" (EMP002) and "Trần Quốc Vượng" (EMP003) exist |
| EMP-AC20 | "do" and "duc" match only "Đỗ Đức Dũng", and "vuong" matches only "Trần Quốc Vượng". "nguyen" and "NGUYỄN" match the same 10 "Nguyễn" employees. Matching covers name, code and email, with diacritics folded and `đ` as `d` |
| ORG-AC04, ORG-AC09 | "Phòng Kế toán" and "Phòng Nhân sự" exist as departments; "Kế toán trưởng" exists as a position |
| ORG-AC07 | The position "Trợ lý" has exactly 3 employees, 1 of them inactive (EMP012) |

`a.nguyen@example.test` (EMP-AC06) is deliberately not in the data, so tests can create it.

## How it is used

- **Locally (US04):** `docker compose up` loads these files into PostgreSQL.
- **On dev01 (US17, backlog BL-D9):** every check session starts with an empty database (Q-O57), so the session runbook loads these files after the first admin is created (US08).
- **Tests:** QA's tests read these files or build their own records from the same rules. A test that needs another record creates it and never edits these files.
- **Not included:** user accounts and passwords. Tests create accounts through the API with mock passwords at run time, so no credential-like value is committed.

Changes to this folder go through a reviewed commit like any other change. Keep the rules above true, and re-run the check after every change: `python3 -I testdata/mock/check_mock.py testdata/mock` (prints PASS or the failing rules).
