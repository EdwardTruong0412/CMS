# Handoff: 2026-11-05 US01b - QA summary (tests first, plan task T0)

| | |
| --- | --- |
| Task | US01b T0, tests first. The Owner approved the task on 2026-11-04 and the test commit on 2026-11-05 |
| Branch | `feature/US01b_state_singleton_group`, worktree `wt-US01b`, from `371d12a` (`develop` with US01a merged) |
| Commit | `cfa91ec` `test(US01b): add tests-first checks for state bucket, singleton and group` (only `tests/`) |
| Criteria | IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01, NET-AC02 |
| Inputs read | `docs/plans/US01b.plan.md` (T0 to T5, sections 4 to 7, 10, 13 and 15), `docs/gates/G4.md` (US01b), `docs/specs/spec-001.md` (IAC-AC03, AC04, AC07, AC08, AC14, NET-AC01, NET-AC02, D-DL9, Q-D11), `docs/backlog.md` (US01b), `AGENTS.md` ("Coding convention", test layout KO-9), `src/api/pyproject.toml`, `Makefile`, the existing `tests/infra` files, `reports/handoff/US01a-qa-summary.md`, `docs/process/ai-native-sdlc-workflow.md` |

## What was done

- Wrote tests for all seven criteria in two parts, as plan section 4 asks:
  - `tests/infra/`: the static part, run by `make check`, with no AWS and no network.
  - `tests/dev01/`: the dev01 part, run by QA against the real account after the merge. Not part of `make check`.
- `tests/infra` reads the Terraform files as text. It masks comments, strings and heredocs, and matches braces; there is no HCL parser (plan 7.7). `.terraform/` directories are skipped.
  - The criterion checks run over every root under `awsenv/dev/` and every directory under `modules/`, and always include this story's two roots and three modules. They keep holding when US01c and later stories add the env root and new modules (backlog, "Also checked in").
  - The checks for IAC-AC03, IAC-AC04, IAC-AC08, IAC-AC14 and NET-AC02 each have a small self-check that proves the detector finds a violation (their failure paths).
- The bootstrap script is tested with a fake `aws` that the test writes to `tmp_path` and puts first on PATH (US01b-D15).
  - The fake logs every call (arguments, `AWS_PROFILE`, `AWS_REGION`) and answers like AWS CLI v2. It uses mock account ID `123456789012`, the AWS documentation example.
  - It covers the 404 branch (create, wait, settings), the second run, the 403 stop and the six settings.
  - It also checks `--expected-bucket-owner`, the profile default `3tier`, the fixed region, and that nothing is ever deleted or suspended.
  - Safety:
    - AWS_* variables are removed and the AWS config and credentials files point to missing files.
    - The script is not run at all if it calls `aws` by absolute path.
- `tests/dev01` calls the AWS CLI and `terraform` through `subprocess` (US01b-D13).
  - The shared helpers and the IAC-AC07 three-phase lock procedure are in `tests/dev01/conftest.py`, behind the `dev01` fixture.
  - The fixture fails (never skips) unless `AWS_PROFILE=3tier` and `AWS_REGION=ap-southeast-1` are set and `aws` and `terraform` are on PATH.
  - A Terraform call fails if `awsenv/dev/<layer>/.terraform` is missing (no `terraform init`).
- Enabler checks of designs the plan fixes are named by decision ID (US01b-D2 to D4, D6 to D11, D14, D15) or task ID (`t2`, `t3`, `t2_t3`), never by a criterion ID. This is the same convention as US01a.
- No mock data file was needed.

## Files produced

| File | Content |
| --- | --- |
| `tests/infra/test_terraform_layout.py` | IAC-AC03, IAC-AC04, IAC-AC07 (backend), IAC-AC14, NET-AC01, NET-AC02 (static); enablers D2, D3, D4, D7, D8, D9, D10, T2, T3 |
| `tests/infra/test_bootstrap.py` | IAC-AC08 (script, no `.tf` declares the bucket, runbook); enablers D11, D14, D15 |
| `tests/dev01/conftest.py` | `dev01` fixture: AWS CLI and Terraform helpers, state-object version, `show -json` walk, state-bucket search in a layer's state, lock phases |
| `tests/dev01/test_us01b_singleton.py` | IAC-AC07, IAC-AC08, IAC-AC14 on singleton and the state bucket; enablers D9, D10, D11, T2 |
| `tests/dev01/test_us01b_group.py` | IAC-AC07, IAC-AC08 (group and env), IAC-AC14, NET-AC01, NET-AC02 on group; enablers D6, D7, D8 |

## Tests mapped to IDs

### `tests/infra/` (in `make check`, at merge)

| ID | Tests |
| --- | --- |
| IAC-AC03 | `test_iac_ac03_no_resource_block_in_awsenv`, `test_iac_ac03_root_module_calls_point_to_child_modules` [per layer], `test_iac_ac03_detector_finds_resource_blocks` (self-check) |
| IAC-AC04 | `test_iac_ac04_module_has_readme` [per module], `test_iac_ac04_readme_has_every_template_heading` [per module], `test_iac_ac04_detector_flags_missing_heading` (self-check) |
| IAC-AC07 | `test_iac_ac07_backend_uses_s3_lock_file` [per layer], `test_iac_ac07_no_dynamodb_lock_table` [per layer] |
| IAC-AC08 | `test_iac_ac08_script_exists_and_is_executable`, `_first_run_creates_versioned_bucket`, `_second_run_reapplies_settings_without_create`, `_two_runs_make_the_same_calls`, `_403_stops_without_any_change`, `_versioning_enabled_on_every_run`, `_script_reads_back_settings`, `_no_tf_declares_the_state_bucket`, `_detector_finds_state_bucket_resource` (self-check), `_runbook_documents_the_state_bucket_step` |
| IAC-AC14 | `test_iac_ac14_every_aws_provider_has_project_default_tag` [per layer], `_module_tags_hold_only_name` [per module], `_roots_set_tags_only_in_default_tags` [per layer], `_detector_flags_tags_other_than_name` (self-check) |
| NET-AC01 | `test_net_ac01_three_subnet_tiers`, `_each_tier_has_one_subnet_per_zone` [3 tiers], `_group_calls_network_with_two_zones`, `_network_requires_exactly_two_zones` |
| NET-AC02 | `test_net_ac02_isolated_route_table_has_no_route_block` (also catches `dynamic "route"`), `_no_aws_route_refers_to_isolated_table`, `_isolated_subnets_associated_with_isolated_table`, `_parser_reads_nested_route_block` (self-check) |

Enabler tests (the test report lists them as enablers, not criteria):

| ID | Tests |
| --- | --- |
| US01b-D2 | `test_us01b_d2_template_has_exactly_the_nine_headings` |
| US01b-D3 | `test_us01b_d3_backend_bucket_key_region` [per layer] |
| US01b-D4 | `test_us01b_d4_version_pins`, `_lock_file_has_aws_provider_for_two_platforms` (at least two `h1:` hashes; provider 6.x with x of 71 or more) |
| US01b-D7 | `test_us01b_d7_group_nat_gateway_count_variable`, `_profile_file_sets_only_nat_count`, `_nat_gateways_and_eips_follow_the_count`, `_no_inline_route_in_any_route_table`, `_public_and_private_default_routes` |
| US01b-D8 | `test_us01b_d8_no_public_ip_on_launch` [3 tiers], `_default_security_group_closed`, `_vpc_dns_settings` |
| US01b-D9 | `test_us01b_d9_ecr_repository_settings`, `_ecr_lifecycle_policy` |
| US01b-D10 | `test_us01b_d10_hosted_zone_settings` |
| US01b-D11 | `test_us01b_d11_script_header`, `_every_call_names_the_expected_owner`, `_account_from_caller_identity`, `_public_access_block_all_true`, `_ownership_enforced`, `_encryption_sse_s3`, `_tls_only_bucket_policy`, `_bucket_tags`, `_profile_defaults_to_3tier_region_fixed`, `_profile_from_environment_is_honoured`, `_script_never_deletes_or_suspends`, `_script_has_no_em_dash` |
| US01b-D14 | `test_us01b_d14_runbook_has_section` [8 sections], `_runbook_singleton_and_ns_steps`, `_runbook_group_session_and_later_steps` |
| US01b-D15 | `test_us01b_d15_script_calls_aws_from_path` |
| Plan T2, T3 | `test_us01b_t2_t3_root_file_exists`, `_t2_t3_layer_calls_its_modules`, `_t2_t3_module_call_named_after_directory`, `_t2_t3_module_file_exists`, `_t2_t3_module_outputs`, `_t2_backend_encrypts_state`, `_t2_provider_region_without_profile_or_alias`, `_t2_singleton_module_arguments`, `_t2_singleton_output` [6 outputs], `_t3_group_module_arguments`, `_t3_group_output` [8 outputs] |

### `tests/dev01/test_us01b_singleton.py` (after the Owner's bootstrap and singleton apply)

| ID | Tests |
| --- | --- |
| IAC-AC07 | `test_iac_ac07_singleton_before_apply_record_state_version`, `_singleton_during_apply_lock_object_exists`, `_singleton_during_apply_second_plan_stops_with_lock_error`, `_singleton_after_apply_lock_released_plan_succeeds` |
| IAC-AC08 | `test_iac_ac08_state_bucket_versioning_enabled`, `_state_bucket_not_in_singleton_state`, `_bootstrap_second_run_changes_nothing` |
| IAC-AC14 | `test_iac_ac14_singleton_every_taggable_resource_has_project_tag` (`tags_all` in `terraform show -json`), `_singleton_tags_spot_check_with_aws_cli` |
| Enablers | `test_us01b_d11_state_bucket_settings`, `_d11_state_bucket_tls_only_policy`, `_d11_state_bucket_tags`, `_t2_singleton_outputs`, `_d9_ecr_repository_settings`, `_d10_hosted_zone_is_public_with_four_name_servers`, `_t2_singleton_resources_in_ap_southeast_1` |

### `tests/dev01/test_us01b_group.py` (Session 1)

| ID | Tests |
| --- | --- |
| IAC-AC07 | `test_iac_ac07_group_before_apply_record_state_version`, `_group_during_apply_lock_object_exists`, `_group_during_apply_second_plan_stops_with_lock_error`, `_group_after_apply_lock_released_plan_succeeds` (with `-var-file=tfvars/lean.tfvars`) |
| IAC-AC08 | `test_iac_ac08_state_bucket_not_in_group_state`, `_env_state_does_not_hold_state_bucket` (workspace `dev01`; reads only `state list` and `state show` of `aws_s3_bucket*` addresses) |
| IAC-AC14 | `test_iac_ac14_group_every_taggable_resource_has_project_tag`, `_group_tags_spot_check_with_aws_cli` |
| NET-AC01 | `test_net_ac01_vpc_has_six_subnets_three_tiers_two_zones`, `_group_outputs_match_the_subnets` |
| NET-AC02 | `test_net_ac02_isolated_subnet_route_tables_have_only_local_route` [zones a, b; uses the main table if a subnet has no explicit association], `_isolated_subnets_use_cms_isolated_rt` |
| Enablers | `test_us01b_d6_vpc_and_subnet_cidrs`, `_d7_routes_follow_the_profile`, `_d8_no_public_ip_on_launch`, `_d8_default_security_group_has_no_rules` |

## How and when the tests run

### At merge (story run test round)

`make check` runs `tests/infra` through `testpaths`. `tests/dev01` is not run in the story run, which has no AWS access. The test report lists it under "Not tested, and why", with the dates below.

### dev01

Every dev01 run uses the same shell, from `src/api` of a checkout that contains the US01b merge:

```bash
cd src/api
export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1
```

Each layer must be initialised with `terraform init` before its tests run. Results go to `reports/test-report-US01b-dev01.md`, with the time of each phase. They are the evidence for DoD item 5 at G6.

**Singleton** (after the merge, target Thu 12 or Fri 13 Nov 2026). The Owner first runs the bootstrap script (runbook step 1). Then:

1. Before the Owner starts the first singleton apply:
   `.venv/bin/pytest ../../tests/dev01/test_us01b_singleton.py -k before_apply`
2. While the Owner waits at `Enter a value:`, from a second shell:
   `.venv/bin/pytest ../../tests/dev01/test_us01b_singleton.py -k during_apply`
   QA says "go" only after this run ends.
3. After the apply has ended and the Owner has said singleton is applied:
   `.venv/bin/pytest ../../tests/dev01/test_us01b_singleton.py -k "not before_apply and not during_apply"`

Phase 3 includes `test_iac_ac08_bootstrap_second_run_changes_nothing`. It runs the real `scripts/bootstrap_state_bucket.sh` a second time. That is a no-change call, but it does call the `put-*` APIs on the real bucket, so it **needs the Owner's approval** with the check's command list (plan 7.4).

**Group** (Session 1, Wed 2026-11-18, lean profile, office hours, before the destroy):

1. Before the Owner's first group apply (`terraform apply -var-file=tfvars/lean.tfvars`):
   `-k before_apply`
2. While the Owner waits at the prompt, from a second shell:
   `-k during_apply`
3. After the group apply has ended:
   `-k "not before_apply and not during_apply and not env_state"`
4. After US01c's env apply (`awsenv/dev/env` initialised; the test sets workspace `dev01`):
   `-k env_state`

The no-change plan of phase 3 runs in office hours, as every no-change plan does (`CLAUDE.md`).

The "before" state version is kept between phase runs in `$CMS_QA_EVIDENCE_DIR`, default `$TMPDIR/cms-qa-us01b`. The "after" test waits up to 10 minutes for the `.tflock` object to disappear.

## What was run and what was not

**The tests have not been run with real pytest, and have not been run against AWS.** pytest is not installed outside a venv, the worktree has no `src/api/.venv`, and no install or AWS access was approved for T0. Everything below used a small pytest stub I wrote in the session scratchpad, as in US01a.

| Check | Result |
| --- | --- |
| `python3 -m py_compile` on all 5 files | pass |
| `tests/infra` against the worktree | 5 pass (the detector self-checks), 135 fail, all for the right reason: the plan's files do not exist yet |
| `tests/infra` against a fake repository built to the plan in the scratchpad (T1 to T4) | 140 of 140 pass |
| Mutations on that fake repository | The intended tests fail. Mutations: a state-bucket resource in `awsenv`; a `Project` tag in a module; an inline, `dynamic` or `aws_route` route on the isolated table; `dynamodb_table`; a README heading missing; the script continuing after a 403; versioning `Suspended`; a missing `--expected-bucket-owner`; an absolute `aws` path; subnet `count = 3`; a public IP on launch |
| `tests/dev01` against a fake `aws` and `terraform` in the scratchpad | Every phase passes for both files. They fail correctly when the second plan ignores the lock, the isolated table has a NAT route, or the profile is wrong |
| `make check`, real pytest, AWS | not run |

## Decisions (QA, routine)

| ID | Decision | Reason |
| --- | --- | --- |
| US01b-QA-D1 | `tests/dev01` helpers live in `conftest.py` and reach the tests through the `dev01` fixture | With `--import-mode=importlib`, test modules cannot import each other or `conftest` |
| US01b-QA-D2 | `tests/infra` allows equivalent forms for some plan literals. `count` may be `2` or `length(var.availability_zones)`. The zone may come from indexing or from `element()`. CLI arguments may be shorthand, JSON or `file://`. The default security group may have no `ingress`/`egress`, or `ingress = []` / `egress = []` | Do not over-specify beyond the plan |
| US01b-QA-D3 | IAC-AC03 also catches unquoted labels (`resource aws_vpc this {`) | HCL allows them; the criterion is "no resource block" |
| US01b-QA-D4 | `test_iac_ac14_roots_set_tags_only_in_default_tags` checks that roots pass no `tags` outside `default_tags` | AGENTS.md and D-DL9: tags come only from provider `default_tags` |
| US01b-QA-D5 | The IAC-AC08 static check looks only at `aws_s3_bucket*` resource blocks and `import` blocks. It does not search for every mention of the bucket name | US01c's remote state and US05's IAM policies will name the bucket legitimately |

## Closed items

- **US01b-QA-Q4 (closed, Owner decision 2026-11-05).** `test_us01b_t2_singleton_has_no_variables_and_no_tfvars` was dropped before the commit. US02 adds a singleton variable and a git-ignored tfvars file, so the check would break `make check` from US02 on. `test_us01b_t2_provider_region_without_profile_or_alias` is kept as it is.

## Open questions (for the Dev Lead)

- **US01b-QA-Q1, runbook section headings.** Plan T4 lists the eight sections of `docs/runbooks/bootstrap.md` as bold items, not headings. `test_us01b_d14_runbook_has_section` requires each section name in a Markdown heading line: any level, case-insensitive, numbering allowed (for example `## 3. Step 1: state bucket`). Please confirm, or name the heading form you want.
- **US01b-QA-Q2, which stream the fixed strings go to.** T4 says the script "prints" its fixed strings. The tests expect:
  - the "already exists" line and the ready line on stdout, with the ready line as the last non-empty stdout line;
  - the 403 error on stdout or stderr;
  - "Enabled" and "AES256" in the stdout of the read-back step.

  Please confirm stdout is right for the fixed lines.
- **US01b-QA-Q3, `-k` inside a dev01 file.** Plan section 15 item 8 says dev01 tests are selected by file, not by `-k`. I select the file by name, but the IAC-AC07 phases need `-k` inside the file (`before_apply`, `during_apply`, `env_state`), because they run at different moments of the Owner's apply. Please confirm this fits item 8.
