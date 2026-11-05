RESULT: PASS

# Test report: US01b (2026-11-05, branch feature/US01b_state_singleton_group, commit 3c5f88b598481c350c5efa5e5996e8b1deb293cb)

Scope of this round: the at-merge checks of `docs/plans/US01b.plan.md` section 7 item 8, that is `make check` (which runs `tests/api/` and `tests/infra/`, including `tests/infra/test_terraform_layout.py` and `tests/infra/test_bootstrap.py`). The dev01 checks in `tests/dev01/` need the Owner's bootstrap and applies and are run later (see "Not tested, and why").

Commands, run in `/Users/truongquy/Documents/wt-US01b-dev1`:

- `make check`: exit 0. ruff, ruff format, mypy strict, pytest **231 passed, 0 failed, 0 skipped** (1 Starlette deprecation warning, not a failure), web lint, typecheck and build, `terraform fmt -check -recursive`, tflint.
- US01b static tests alone (`pytest tests/infra/test_bootstrap.py tests/infra/test_terraform_layout.py -v`): **140 passed**, 0 failed.
- Extra, PR-check equivalents (not part of `make check`): `terraform init -backend=false` + `terraform validate` in `awsenv/dev/singleton` and `awsenv/dev/group`: both "Success! The configuration is valid."; `trivy config --severity HIGH,CRITICAL --exit-code 1` on `modules`, `awsenv/dev/singleton`, `awsenv/dev/group`: exit 0 on each (0 HIGH/CRITICAL).
- `tests/` and `testdata/` unchanged since QA's commit `cfa91ec` (`git diff --stat cfa91ec HEAD -- tests/ testdata/` is empty).
- `pytest tests/dev01 --collect-only`: 34 tests collect without error.

| Acceptance criterion | Tests | Result |
| --- | --- | --- |
| IAC-AC03 no `resource` in `awsenv/` | `test_iac_ac03_detector_finds_resource_blocks`, `test_iac_ac03_no_resource_block_in_awsenv`, `test_iac_ac03_root_module_calls_point_to_child_modules[group,singleton]`, plus layout tests `test_us01b_t2_t3_*` (root files, module calls, module files, outputs) | PASS (static) |
| IAC-AC04 README with every template heading | `test_us01b_d2_template_has_exactly_the_nine_headings`, `test_iac_ac04_detector_flags_missing_heading`, `test_iac_ac04_module_has_readme[container_registry,dns_zone,network]`, `test_iac_ac04_readme_has_every_template_heading[container_registry,dns_zone,network]` | PASS |
| IAC-AC07 state lock blocks a second run, released after | Static: `test_iac_ac07_backend_uses_s3_lock_file[group,singleton]`, `test_iac_ac07_no_dynamodb_lock_table[group,singleton]`, `test_us01b_d3_backend_bucket_key_region[*]`, `test_us01b_t2_backend_encrypts_state[*]`. dev01: `test_iac_ac07_singleton_*` (4), `test_iac_ac07_group_*` | Static PASS; dev01 not yet run |
| IAC-AC08 versioned state bucket outside every layer, documented | Static: `test_iac_ac08_*` in `test_bootstrap.py` (script exists, first run, second run, same calls, 403 stops without change, versioning, read-back, detector, no `.tf` declares the bucket, runbook step) and `test_us01b_d11_*`, `test_us01b_d14_*`, `test_us01b_d15_*`. dev01: `test_iac_ac08_state_bucket_*`, `test_iac_ac08_bootstrap_second_run_changes_nothing`, group and env state checks | Static PASS; dev01 not yet run |
| IAC-AC14 common project tag | Static: `test_iac_ac14_detector_flags_tags_other_than_name`, `test_iac_ac14_every_aws_provider_has_project_default_tag[*]`, `test_iac_ac14_module_tags_hold_only_name[*]`, `test_iac_ac14_roots_set_tags_only_in_default_tags[*]`. dev01: `test_iac_ac14_singleton_*`, `test_iac_ac14_group_*` | Static PASS; dev01 not yet run |
| NET-AC01 two zones, three tiers each | Static: `test_net_ac01_three_subnet_tiers`, `test_net_ac01_each_tier_has_one_subnet_per_zone[public,private,isolated]`, `test_net_ac01_group_calls_network_with_two_zones`, `test_net_ac01_network_requires_exactly_two_zones`, `test_us01b_t3_*`, `test_us01b_d7_*`, `test_us01b_d8_*`. dev01: `test_net_ac01_vpc_has_six_subnets_three_tiers_two_zones`, `test_net_ac01_group_outputs_match_the_subnets` | Static PASS; dev01 not yet run |
| NET-AC02 isolated subnets without an internet route | Static: `test_net_ac02_parser_reads_nested_route_block`, `test_net_ac02_isolated_route_table_has_no_route_block`, `test_net_ac02_no_aws_route_refers_to_isolated_table`, `test_net_ac02_isolated_subnets_associated_with_isolated_table`. dev01: `test_net_ac02_isolated_subnet_route_tables_have_only_local_route[a,b]`, `test_net_ac02_isolated_subnets_use_cms_isolated_rt` | Static PASS; dev01 not yet run |

## Failures

None.

## Not tested, and why

- `tests/dev01/test_us01b_singleton.py` (IAC-AC07, IAC-AC08, IAC-AC14 on singleton; D9, D10, D11, T2 outputs): needs the Owner's state bucket bootstrap and the first singleton apply, with the IAC-AC07 lock test run while that apply waits at its prompt (plan section 7 item 5, section 10). Planned after the merge (target Thu 12 or Fri 13 Nov). No AWS operation was performed in this round.
- `tests/dev01/test_us01b_group.py` (IAC-AC07, IAC-AC08 including env state, IAC-AC14, NET-AC01, NET-AC02 on group): needs the first group apply of Session 1 (Wed 2026-11-18); its env state check for IAC-AC08 runs after US01c's env apply.
- These dev01 parts are checked at G6 (DoD item 5), as plan section 9 states. Until then, the dev01 halves of IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01 and NET-AC02 are unproven.

## Open questions

None. Note: `terraform init -backend=false` for the validate step created `awsenv/dev/singleton/.terraform/` and `awsenv/dev/group/.terraform/` in the worktree; both are git-ignored and change no tracked file.
