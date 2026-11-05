# Handoff: 2026-11-05 US01b - Dev Lead summary (state bucket, singleton and group, before the story run)

| | |
| --- | --- |
| Task | Dev Lead summary for US01b, required by global rule 5 and the `/story` preflight. Approved by the Owner on 2026-11-05 |
| Branch / worktree | `feature/US01b_state_singleton_group`, `/Users/truongquy/Documents/wt-US01b`, from `371d12a` (`develop` with US01a merged); QA tests `cfa91ec` |
| Read | `docs/plans/US01b.plan.md`, `docs/gates/G4.md` (US01b), `reports/handoff/US01b-qa-summary.md`, `reports/handoff/US01b-po-summary.md`, `tests/infra/test_bootstrap.py`, `tests/infra/test_terraform_layout.py`, `tests/dev01/test_us01b_singleton.py`, `reports/handoff/US01a-dev-lead-summary.md`, `reports/stories/US01a/` (decision, rounds 1 and 2), `.claude/skills/story/SKILL.md`, `.claude/agents/reviewer-infra.md`, `REVIEW.md`, `AGENTS.md`, `Makefile`, `.tflint.hcl`, `.gitignore` |
| Changed | This file only. Nothing committed; no Dev started; no AWS or Terraform command run |

## 1. What was done

1. **Plan.** Wrote `docs/plans/US01b.plan.md` in DES03: tasks T0 to T5, detailed design, traceability per test moment, complete file list, fixed interfaces, pins, 15 Dev Lead decisions (US01b-D1 to D15), no Owner-tier question. Revised after the PO and QA read-only G4 review; the six changes are in plan section 15.
2. **G4.** The Owner approved the US01b section of `docs/gates/G4.md` (`Owner approval: [x]`, already on `develop`). The branch was then created from `develop` after the US01a merge.
3. **Tests first.** QA committed T0 as `cfa91ec` (only `tests/`). The Owner closed US01b-QA-Q4 on 2026-11-05: the "singleton has no variables and no tfvars" test was dropped before the commit, because US02 adds a singleton variable. No criterion depended on it. I answer QA-Q1 to Q3 in section 7.

## 2. Design in brief (pointers, not a restatement)

| Topic | Plan section |
| --- | --- |
| Goal and out of scope | 1 |
| T1 module README template (nine `##` headings) | 2, T1; US01b-D2 |
| T2 singleton: `container_registry`, `dns_zone`, root files, lock file | 2, T2; US01b-D3, D4, D9, D10 |
| T3 group: `network` module, root, `lean`/`full` tfvars, address plan | 2, T3; US01b-D5 to D8 |
| T4 bootstrap script (fixed strings, `aws` from `PATH`) and runbook | 2, T4; US01b-D11, D14, D15 |
| T5 one `CLAUDE.md` line | 2, T5 |
| Traceability and when each test file runs | 4, 7 (item 10) |
| Complete file list | 5 |
| Interfaces later stories rely on | 6 |

## 3. Dev assignment for the run

- **Dev 1**, lane "Terraform and pipeline" (SP1-D1). One Dev for the whole story.
- **Worktree** `../wt-US01b-dev1`, created by `/story` (`.claude/skills/story/SKILL.md`), not by me. The skill starts Codex with network access and the pip, npm and tflint caches under the worktree's git-ignored `.cache/`, because the sandbox cannot write to the home directory (learned in US01a, OQ-S1-2). The plan is the whole assignment.
- **First step in the fresh worktree:** `make deps` (no `src/api/.venv` or `node_modules` yet), then `make check`.
- **Order** (plan section 3): T1, T2, T3, T4, T5, all `[Infra]`. After T2 and T3: `make check`, `init -backend=false` plus `validate` in each root, and Trivy if it can run. Outputs pasted in the handoff. One proposed commit per task, messages as in section 3.

## 4. What the Dev must not do

- No `terraform init` against the S3 backend (always `-backend=false -input=false`), no `plan`, `apply`, `destroy`, `import`, `state` or `force-unlock`.
- No AWS CLI command against the account and no run of `scripts/bootstrap_state_bucket.sh` against AWS. Its only runs are QA's tests in `make check`, with a fake `aws` on `PATH`.
- No file outside plan section 5. In particular, no second copy of the handoff such as `reports/handoff/US01b-dev1.md`: the round handoff is `factory/stories/US01b/round-<N>/handoff-dev.md`, written by `codex exec -o` (US01a round 1, code finding 2). Also no `awsenv/dev/env/`, no Trivy ignore file, and no change to `.gitignore`, `.tflint.hcl`, the `Makefile` or `AGENTS.md`. Changing `.tflint.hcl` or the `check` target is a blocker under RV-03.
- No edit under `tests/`. If a test conflicts with the plan, report it in the handoff with `STATUS: BLOCKED` (section 7).
- No `.terraform/` directory or state file in a proposed commit (both are git-ignored). No commit at all.

## 5. Can `make check` and the Terraform steps run in the Codex sandbox without AWS

| Step | Needs AWS | Needs network | Note |
| --- | --- | --- | --- |
| `tests/infra` (pytest) | No | No | Reads files as text. `test_bootstrap.py` writes a fake `aws` to pytest's `tmp_path` (under `TMPDIR`, which the workspace-write sandbox allows) and runs the script with `bash` from `PATH`. It strips `AWS_*` and points the config and credentials files at missing paths |
| `terraform fmt -check -recursive` | No | No | No provider needed |
| `tflint --init` | No | Yes | Downloads `tflint-ruleset-aws` 0.50.0 into `.cache/home` (US01a's design) |
| `tflint --recursive` | No | No | `call_module_type = "local"` reads the local module calls without `terraform init`, so tflint needs no provider download. The AWS ruleset's deep check is off, so it needs no credentials. Not yet run on real Terraform in this repo (see risks) |
| `terraform init -backend=false` | No | Yes | Not part of `make check`. Needed for `validate` and for the lock file. It downloads `hashicorp/aws` into `<root>/.terraform/`, which is git-ignored and skipped by the tests. `CHECKPOINT_DISABLE=1` stops writes to `~/.terraform.d` |
| `terraform providers lock -platform=darwin_arm64 -platform=linux_amd64` | No | Yes | Downloads the package for both platforms from the registry to compute their `h1:` hashes, and writes only `.terraform.lock.hcl`. Run it from inside the sandbox, after `init` and before `validate`, in each root (plan T2 step 9, T3 step 7). The lock file then holds two `h1:` hashes plus the registry's `zh:` hashes, which is what `test_us01b_d4_lock_file_has_aws_provider_for_two_platforms` checks (6.x with x of 71 or more, at least two `h1:`). If the download fails in the sandbox, the Dev reports BLOCKED with the error (plan section 12). The lock file is never written by hand |
| `terraform validate` | No | No (after init) | Runs the provider plugin locally, with no credentials |
| `trivy config` | No | Yes, for its checks bundle | Optional in the plan. In the sandbox it needs `--cache-dir "$PWD/.cache/trivy"`, because its default cache is under the home directory. If it cannot run, the Dev says so. The infra lens runs it in any case, as in US01a |

Conclusion: `make check` with the new `tests/infra` and tflint on the new Terraform runs in the sandbox without AWS. The only network it needs is the tflint plugin. The lock file needs `init -backend=false` and `providers lock` with network, but no AWS.

## 6. Dependency pins and escalation

- **Pins** (plan section 8): new provider `hashicorp/aws ~> 6.71`, locked in both `.terraform.lock.hcl` files with `darwin_arm64` and `linux_amd64` hashes; `required_version = "~> 1.16.4"`, matching `.terraform-version`. No Python or npm change.
- **Approver escalation** (plan section 9): the run is expected to end in `needs-human`, so you decide G5. Triggers:
  - account and network layers (`awsenv/dev/singleton/`, `awsenv/dev/group/` and their three modules);
  - dependencies (the AWS provider);
  - governance (`CLAUDE.md`, T5);
  - cost: the always-on hosted zone at $0.50 a month plus a few cents of ECR storage; group lean at about $0.064 an hour, only in sessions. These are estimates.

  It will also note exposure (an internet gateway and NAT addresses, as the architecture expects), and that the dev01 parts are proven only after the merge (G6).
- **At G5 you check:** the provider version in both lock files, the one `CLAUDE.md` line against plan T5, and the cost and exposure above.

## 7. Answers to QA's questions (Dev Lead tier)

| ID | Question | Decision | Reason | Test change |
| --- | --- | --- | --- | --- |
| US01b-DL-D1 | US01b-QA-Q1: runbook sections as headings | **Confirmed.** Each of the eight T4 section names is a Markdown heading. The form for the Dev is `## <n>. <name>`, for example `## 3. Step 1: state bucket`, with the names exactly as plan T4 writes them in bold | The bold labels in T4 are the section titles; headings make the runbook navigable and testable. The test accepts any level and numbering, so this form passes and nothing is over-specified | None |
| US01b-DL-D2 | US01b-QA-Q2: output streams | **Confirmed: stdout** for the fixed lines and the read-back step. The ready line is the last non-empty stdout line. The `head-bucket` error on a non-404 is written to stderr, then the script exits 1. The script captures the CLI output of `head-bucket` (it needs the stderr text to tell 404 from the rest), so stdout carries only the script's own lines. Stdout is deterministic: no timestamps or other run-dependent text | Results to stdout and errors to stderr is the normal convention, and it matches the tests. `test_iac_ac08_two_runs_make_the_same_calls` compares the stdout of two runs byte for byte, so anything that varies would fail it | None |
| US01b-DL-D3 | US01b-QA-Q3: `-k` inside a dev01 file | **Accepted.** Plan section 15 item 8 says each criterion's dev01 checks are selected by file name instead of `-k` across `tests/dev01/`. Using `-k` inside one file to pick the phases (`before_apply`, `during_apply`, `env_state`) is consistent with it. The phases have to run at fixed moments of the Owner's apply | The file stays the unit of evidence for `reports/test-report-US01b-dev01.md`. The phase substrings are fixed in the test names, so the selection is stable | None |

**No test change is needed.** If the first real `make check` in the run shows that a test is wrong (QA ran it only with a pytest stub), the Dev reports it in the handoff. Any change to `tests/` then goes back to QA and needs your approval (global rule 2).

## 8. Owner actions after the merge (plan section 10)

Same day if possible (target Thu 12 or Fri 13 Nov), per `docs/runbooks/bootstrap.md`:
1. Run `./scripts/bootstrap_state_bucket.sh` with `AWS_PROFILE=3tier`.
2. Run `terraform init` and `terraform apply` in `awsenv/dev/singleton`. Wait at `Enter a value:` until QA says "go" (IAC-AC07 lock test), then type `yes`. This starts the always-on cost.
3. Add the four NS records for host `cms` at Namecheap, then run the two `dig` checks.
4. Tell QA that singleton is applied. QA's phase 3 runs the bootstrap script a second time on the real bucket (a no-change call), which needs your approval with QA's command list.

In Session 1 (Wed 2026-11-18, lean):
- apply group with `tfvars/lean.tfvars` and wait at the prompt for QA;
- QA runs `tests/dev01/test_us01b_group.py`, and its env-state check after US01c's env apply;
- at the end, destroy env, then group, with the same files.

## 9. Risks

| Risk | Response |
| --- | --- |
| The bash on `PATH` is macOS `/bin/bash` 3.2, both for your run of the script and for `test_bootstrap.py` (`bash` from `PATH`). Under `set -u`, bash before 4.4 fails on an empty array expansion, and it has no `mapfile`, `${var,,}` or associative arrays | The script avoids those constructs. The Dev checks it with `bash -n` and `shellcheck` (installed), and `make check` runs it under 3.2 against the fake `aws`. Reviewers check this under RV-01 and RV-12 |
| `tflint-ruleset-aws` is exercised on real Terraform for the first time (US01a review note) and may report something the plan did not foresee | The Dev fixes the Terraform, never `.tflint.hcl` (RV-03). If a fix would leave the plan, the Dev reports BLOCKED |
| `init -backend=false` and `providers lock` download the AWS provider: several hundred MB per root, and two platforms for the lock | Network is enabled for the run. If the download fails or times out, the Dev reports BLOCKED (plan section 12) |
| `tests/infra` for US01b has not yet run under real pytest (QA used a stub) | The Dev's first `make check` is the first real run. A wrong test goes back to QA with your approval (section 7) |
| The state bucket name is taken by another account before step 1 | The script stops at `(403)` and changes nothing. A new name becomes an Owner question then (plan section 12) |
| NS delegation not propagated before US01c's env apply | Add the records right after the singleton apply. The runbook gives the `dig` check |

## 10. Open questions (Owner tier)

None.
