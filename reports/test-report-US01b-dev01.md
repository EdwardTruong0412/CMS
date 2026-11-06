RESULT: PARTIAL

# Test report: US01b dev01, singleton layer (2026-11-06, branch develop, commit b7c66f6)

## Current state (after the re-run and the Owner's answers, 2026-11-06)

No test has failed a check, and no defect is open. The Owner's script run at
04:56Z configured the state bucket fully. Every setting reads back as
expected, and QA's second bootstrap run changed nothing. The result is
PARTIAL because these items are still open:

- `test_iac_ac08_bootstrap_second_run_changes_nothing` and
  `test_us01b_d11_state_bucket_tags`: they timed out twice each in the QA
  sandbox on the read-only `aws s3api get-bucket-location` call in
  `bucket_settings()` (120 s subprocess timeout). They did not fail on an
  assertion. In re-run 2, the bootstrap test's exit, "already exists" and
  ready-line checks passed. Direct AWS CLI reads show the expected values
  (evidence below). These two tests are waiting for the Owner's run from their
  own shell (open question 5).
- IAC-AC07 phases 1 and 2 on singleton: not run, because the first apply was
  not paused. The Owner decided to run the lock test (phases 1 to 3) on the
  group's first apply in Session 1 (2026-11-18) and on the next singleton
  apply with pending changes (US02's re-apply). Open question 1 is closed.
- NS delegation: the configuration is verified from the Owner's Namecheap
  screenshot (below). The public resolution check is a follow-up that must be
  done before US01c's ACM DNS validation.

### NS delegation: configuration verified from the Namecheap screenshot (2026-11-06)

The Owner showed the Namecheap Advanced DNS page for `imaprof.ink`. It has four
NS records for host `cms`, TTL Automatic, with the values
`ns-1498.awsdns-59.org.`, `ns-1781.awsdns-30.co.uk.`, `ns-215.awsdns-26.com.`
and `ns-623.awsdns-13.net.`. These are the same four name servers as the
zone's delegation set and the `hosted_zone_name_servers` output
(`test_us01b_d10_hosted_zone_is_public_with_four_name_servers`, PASS). Result:
configuration verified from the screenshot. Public resolution is not proven:
`dig @1.1.1.1` timed out from the QA sandbox and from the Owner's network.
Follow-up, before US01c's ACM validation:
`dig +short NS cms.imaprof.ink @1.1.1.1` and `@8.8.8.8` from a network with
outbound DNS. Both must return the four name servers above.

### Re-run 1: 2026-11-06 05:09:20Z to 05:14:42Z

Approved by the Owner ("approve QA re-run") after the Owner's rerun of the
script ("rerun done"). Same shell, environment and limits as the first run.
Selection: `-k "versioning_enabled or bootstrap_second_run or d11_state_bucket or after_apply_lock_released"`
(6 selected, 4 passed, 2 failed, 321.7 s).

| Acceptance criterion | Test | Result | Evidence |
| --- | --- | --- | --- |
| IAC-AC07 (phase 3) | `test_iac_ac07_singleton_after_apply_lock_released_plan_succeeds` | PASS | No `singleton/terraform.tfstate.tflock`; `terraform plan -detailed-exitcode` exit 0 (no changes); no lock left; no force-unlock |
| IAC-AC08 (versioning) | `test_iac_ac08_state_bucket_versioning_enabled` | PASS | `Status: Enabled` |
| IAC-AC08 (bootstrap re-run) | `test_iac_ac08_bootstrap_second_run_changes_nothing` | FAIL (timeout) | `TimeoutExpired` (120 s) on `get-bucket-location` while reading the "before" settings. The script was not run in this attempt |
| US01b-D11 (SSE, public access, ownership, region) | `test_us01b_d11_state_bucket_settings` | PASS | `AES256`; all four public access blocks `true`; `BucketOwnerEnforced`; `ap-southeast-1` |
| US01b-D11 (TLS-only policy) | `test_us01b_d11_state_bucket_tls_only_policy` | PASS | One statement `DenyInsecureTransport`, Deny, `*`, `s3:*`, bucket and `/*`, `aws:SecureTransport = false` |
| US01b-D11 (tags) | `test_us01b_d11_state_bucket_tags` | FAIL (timeout) | `TimeoutExpired` (120 s) on `get-bucket-location` inside `bucket_settings()`, before the tag assertion |

### Re-run 2 (one retry of the two timed-out tests): 05:15:08Z to 05:19:28Z

A direct `get-bucket-location` at 05:14:57Z answered in 3.7 s, so QA retried
the two tests once (`-k "bootstrap_second_run or d11_state_bucket_tags"`).
Both failed again, and QA did not retry them a third time.

| Acceptance criterion | Test | Result | Evidence |
| --- | --- | --- | --- |
| IAC-AC08 (bootstrap re-run) | `test_iac_ac08_bootstrap_second_run_changes_nothing` | FAIL (timeout) | The "before" read passed and the script ran (CloudTrail `Put*` at 05:15:15Z to 05:15:18Z, below). The exit-0, "already exists" line and ready-line assertions passed: the failure is at line 148, after them. It then timed out (120 s) on `get-bucket-location` in the "after" read at `assert bucket_settings(dev01) == before` |
| US01b-D11 (tags) | `test_us01b_d11_state_bucket_tags` | FAIL (timeout) | Same `get-bucket-location` timeout, before the tag assertion |

### Manual evidence for the two timed-out tests: 05:19:50Z to 05:23:33Z

Because the harness could not finish its "after" read, QA did the second
bootstrap run once by hand. It read all seven settings with the AWS CLI
(`--cli-read-timeout 30`), ran `./scripts/bootstrap_state_bucket.sh`, then read
the seven settings again:

- The script exited 0. Output: `Bucket cms-terraform-state-store already exists in account <account>; re-applying its settings.`,
  `Enabled`, `AES256`, the four public access blocks `true`, and last line
  `State bucket cms-terraform-state-store is ready (versioning Enabled).`
- Before and after snapshots are byte-identical (`diff` empty, no error in
  either): versioning `Enabled`; SSE `AES256`; four public access blocks `true`;
  `BucketOwnerEnforced`; policy `DenyInsecureTransport` as above; tags
  `Project = cms`, `ManagedBy = bootstrap-script`; location `ap-southeast-1`.
- The "after" snapshot took about 3.5 minutes (05:20:00Z to 05:23:33Z) but
  completed. The sandbox's S3 reads are slow at times, which matches the timeouts.
- Lock objects: `list-objects-v2 --prefix singleton/` shows only
  `singleton/terraform.tfstate`, with no `.tflock`.

Disclosure: the second bootstrap run was approved once, and QA's script ran
twice. The first time was inside re-run 2 (05:15:15Z), which QA learned only
from CloudTrail and the traceback. The second time was the manual run
(05:19:55Z). Both re-applied the same values, and neither changed any setting.
QA made no other AWS write.

### CloudTrail evidence (read-only `lookup-events`)

| Time (UTC) | Calls (all by `SA-Edward`, no error code) | Source |
| --- | --- | --- |
| 03:56:28Z | `CreateBucket`, `PutBucketEncryption` only | First creation (open question 2) |
| 04:56:23Z to 04:56:28Z | `PutBucketPublicAccessBlock`, `PutBucketOwnershipControls`, `PutBucketEncryption`, `PutBucketVersioning`, `PutBucketPolicy`, `PutBucketTagging` | Owner's rerun ("rerun done") |
| 05:15:15Z to 05:15:18Z | the same six `Put*` calls | QA, script run inside re-run 2 |
| 05:19:55Z to 05:19:58Z | the same six `Put*` calls | QA, manual second bootstrap run |

The Owner's 04:56 calls are the six writes the script makes after
`create-bucket`, in the script's order. That matches a complete script run.

## First run (history): 2026-11-06 04:38:18Z to 04:38:44Z

QA live check of the state bucket and the singleton layer on dev01, approved by
the Owner on 2026-11-06 ("approve QA for the singleton checks").

- Shell: main checkout `/Users/truongquy/Documents/CMS`, branch `develop` at
  `b7c66f6` (US01b merged), `AWS_PROFILE=3tier`, `AWS_REGION=ap-southeast-1`,
  `TF_WORKSPACE` unset, singleton workspace `default`, Terraform v1.16.4.
  Caller: IAM user `SA-Edward` in the project account.
- Runner: `src/api/.venv` does not exist in this checkout, so pytest 9.2.0 ran
  from a throwaway venv in the QA scratchpad (stdlib + pytest only; these tests
  need nothing else). No file in the repository was changed apart from this report.
- Command (phase 3 selection of the test module header), from `src/api`:
  `pytest ../../tests/dev01/test_us01b_singleton.py -k "not before_apply and not during_apply" -v`
- Phase 3 run: 2026-11-06 04:38:18Z to 04:38:44Z (11:38 to 11:38 ICT).
  Result: 14 selected, 9 passed, 5 failed, 3 deselected (the IAC-AC07 phase 1 and 2 tests).

### Results (first run)

| Acceptance criterion | Test | Result | Evidence |
| --- | --- | --- | --- |
| IAC-AC07 (phase 1) | `test_iac_ac07_singleton_before_apply_record_state_version` | NOT RUN | First apply was not paused; see "Deviation: IAC-AC07" |
| IAC-AC07 (phase 2) | `test_iac_ac07_singleton_during_apply_lock_object_exists` | NOT RUN | First apply was not paused |
| IAC-AC07 (phase 2) | `test_iac_ac07_singleton_during_apply_second_plan_stops_with_lock_error` | NOT RUN | First apply was not paused |
| IAC-AC07 (phase 3) | `test_iac_ac07_singleton_after_apply_lock_released_plan_succeeds` | PASS | No `singleton/terraform.tfstate.tflock`; state object present; `terraform plan -input=false -detailed-exitcode` exit 0 (no changes); no lock left after the plan; no force-unlock run |
| IAC-AC08 (versioning) | `test_iac_ac08_state_bucket_versioning_enabled` | **FAIL** | `get-bucket-versioning` returns an empty body: versioning was never enabled |
| IAC-AC08 (not in any layer) | `test_iac_ac08_state_bucket_not_in_singleton_state` | PASS | Singleton state not empty; no `aws_s3_bucket*` address in it names `cms-terraform-state-store` |
| IAC-AC08 (bootstrap re-run) | `test_iac_ac08_bootstrap_second_run_changes_nothing` | **FAIL** (script not run) | Failed while reading the "before" settings (`get-bucket-policy`: `NoSuchBucketPolicy`), before the script line. The script was not executed; no write was made |
| US01b-D11 (SSE, public access, ownership, region) | `test_us01b_d11_state_bucket_settings` | **FAIL** | Fails on the shared read of the bucket policy (`NoSuchBucketPolicy`). Read alone, the four settings it asserts match: SSE `AES256`, all four public access blocks `true`, `BucketOwnerEnforced`, `ap-southeast-1` (these are the AWS defaults for a new bucket) |
| US01b-D11 (TLS-only policy) | `test_us01b_d11_state_bucket_tls_only_policy` | **FAIL** | `NoSuchBucketPolicy`: the bucket has no policy, so no `DenyInsecureTransport` statement |
| US01b-D11 (tags) | `test_us01b_d11_state_bucket_tags` | **FAIL** | Fails on the policy read; a direct `get-bucket-tagging` returns `NoSuchTagSet`: no `Project`/`ManagedBy` tags on the bucket |
| IAC-AC14 (singleton, state) | `test_iac_ac14_singleton_every_taggable_resource_has_project_tag` | PASS | Every resource with `tags_all` in `terraform show -json` (incl. ECR repository and Route 53 zone) has `Project = cms`, `ManagedBy = terraform` |
| IAC-AC14 (singleton, AWS CLI) | `test_iac_ac14_singleton_tags_spot_check_with_aws_cli` | PASS | ECR `cms-api` and zone `cms.imaprof.ink` tags read with the AWS CLI: `Project = cms`, `ManagedBy = terraform` |
| US01b-T2 outputs | `test_us01b_t2_singleton_outputs` | PASS | All six outputs present; `cms-api`; URL ends `.dkr.ecr.ap-southeast-1.amazonaws.com/cms-api`; zone `cms.imaprof.ink`; 4 name servers |
| US01b-D9 ECR | `test_us01b_d9_ecr_repository_settings` | PASS | `IMMUTABLE`, scan on push, `AES256`, lifecycle policy with 2 rules |
| US01b-D10 hosted zone | `test_us01b_d10_hosted_zone_is_public_with_four_name_servers` | PASS | Public zone `cms.imaprof.ink.`; delegation set equals the output: `ns-1498.awsdns-59.org`, `ns-1781.awsdns-30.co.uk`, `ns-215.awsdns-26.com`, `ns-623.awsdns-13.net` |
| US01b-T2 region | `test_us01b_t2_singleton_resources_in_ap_southeast_1[ecr_repository_arn]` | PASS | ARN contains `ap-southeast-1` |
| US01b-T2 region | `test_us01b_t2_singleton_resources_in_ap_southeast_1[ecr_repository_url]` | PASS | URL contains `ap-southeast-1` |
| Delegation (Q-D11 step 4) | `dig +short NS cms.imaprof.ink @1.1.1.1` and `@8.8.8.8` | NOT RUN (sandbox) | Both: `connection timed out; no servers could be reached`. The QA sandbox has no outbound DNS; left to the Owner (not a failure) |

### Failures (first run; fixed by the Owner's rerun at 04:56Z)

All five failures have one cause: the state bucket `cms-terraform-state-store`
does not carry the settings the bootstrap script applies after `create-bucket`.

Read back on 2026-11-06 ~04:40Z (read-only calls):

| Setting | Expected (script, US01b-D11, IAC-AC08) | Actual |
| --- | --- | --- |
| Versioning | `Enabled` | not set (empty response) |
| Bucket policy | `DenyInsecureTransport` | `NoSuchBucketPolicy` |
| Tags | `Project = cms`, `ManagedBy = bootstrap-script` | `NoSuchTagSet` |
| Encryption | `AES256` | `AES256` (plus AWS default `BucketKeyEnabled: true`, SSE-C blocked) |
| Public access block | all four `true` | all four `true` |
| Object ownership | `BucketOwnerEnforced` | `BucketOwnerEnforced` |
| Region | `ap-southeast-1` | `ap-southeast-1` |

Further evidence:

- `list-object-versions --prefix singleton/`: one object,
  `singleton/terraform.tfstate`, `VersionId: null`, written 04:04:11Z. The
  singleton state was written into an unversioned bucket, so it has no
  version history.
- CloudTrail event history (read-only `lookup-events`), S3 management events
  2026-11-06 03:50Z to 04:30Z: `GetAccountPublicAccessBlock` (03:56:12Z),
  `CreateBucket` and `PutBucketEncryption` (03:56:28Z), then only `Get*` calls
  (versioning, ownership, public access block, encryption, tags, logging). There
  is no `PutBucketVersioning`, `PutBucketPolicy`, `PutBucketTagging`,
  `PutPublicAccessBlock` or `PutBucketOwnershipControls` call, successful or
  failed, and no `PutBucketVersioning` at all on 2026-11-06. The script's
  `put-*` calls never reached AWS. The pattern (account public access block read
  first, then a burst of reads after create) looks like bucket creation in the
  S3 console rather than the script, or a script run that stopped right after
  `create-bucket`/`wait`. QA cannot tell which; the Owner can.

Per failing test:

1. `test_iac_ac08_state_bucket_versioning_enabled` (IAC-AC08). Expected
   `Status = Enabled`; actual: no status (versioning never enabled), the test
   errors with `AttributeError: 'NoneType' object has no attribute 'get'` on the
   empty response.
2. `test_iac_ac08_bootstrap_second_run_changes_nothing` (IAC-AC08). Expected:
   script prints the "already exists" line, ends with the ready line, exit 0,
   settings unchanged. Actual: the test stopped at the "before" read
   (`NoSuchBucketPolicy`); the script was not run. QA did not run it by hand
   either: it was approved as a no-change call, and on this bucket it would
   enable versioning and write the policy and tags, which is a change the Owner
   has not approved.
3. `test_us01b_d11_state_bucket_settings` (US01b-D11). Fails on the policy read
   inside `bucket_settings()`; its own four assertions match when read directly.
4. `test_us01b_d11_state_bucket_tls_only_policy` (US01b-D11). Expected one
   `DenyInsecureTransport` statement; actual: no policy.
5. `test_us01b_d11_state_bucket_tags` (US01b-D11). Expected `Project = cms`,
   `ManagedBy = bootstrap-script`; actual: no tags.

Steps to reproduce (read-only):

```bash
export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1
aws s3api get-bucket-versioning --bucket cms-terraform-state-store
aws s3api get-bucket-policy     --bucket cms-terraform-state-store
aws s3api get-bucket-tagging    --bucket cms-terraform-state-store
```

Suggested remedy (Owner decision, not done by QA): run
`./scripts/bootstrap_state_bucket.sh` again with `AWS_PROFILE=3tier`, check it
ends with `State bucket cms-terraform-state-store is ready (versioning Enabled).`,
then QA re-runs the five failing tests (the bootstrap test is then the real
"second run changes nothing" check). The script itself is not shown to be wrong
by this run: none of its write calls reached AWS. If the Owner's run printed an
error, that output is what tells whether the script needs a fix (Dev) or the run
was incomplete.

## Deviation: IAC-AC07 on singleton

The Owner did not pause at the apply's `Enter a value:` prompt, so phases 1
(record the state version and check no lock exists before the apply) and 2
(lock object held during the apply; a second `plan -lock-timeout=0s` stops
with `Error acquiring the state lock` and changes no state) were not run:
**not run: first apply was not paused**. They were not simulated.

Phase 3 ran and passed twice, at 04:38Z and 05:09Z: the lock was released,
the plan exited 0 with no changes, and no force-unlock was used. Phase 3 alone
does not prove IAC-AC07, because the core of the criterion is that a second
run stops on the lock. Owner decision, 2026-11-06: the lock test (phases 1 to
3) moves to the group layer's first apply in Session 1 on 2026-11-18 (already
in `tests/dev01/test_us01b_group.py`) and to the next singleton apply with
pending changes (US02's re-apply).

## What remains for the group layer (Session 1, 2026-11-18)

From `tests/dev01/test_us01b_group.py`, with the group lean profile:

- IAC-AC07 on group, all three phases: before apply (record version, no lock),
  during apply (lock object exists; second plan stops on the lock; state
  unchanged), after apply (lock released, plan exit 0, no force-unlock). The
  Owner must stop at `Enter a value:` and wait for QA's "go".
- IAC-AC08: state bucket not in group state; env state does not hold the state
  bucket.
- IAC-AC14 on group: every taggable resource has `Project = cms`,
  `ManagedBy = terraform`, plus AWS CLI spot check.
- NET-AC01: six subnets, three tiers, two AZs; outputs match the subnets.
- NET-AC02: isolated route tables have only the local route; isolated subnets
  use `cms-isolated-rt`.
- US01b-D6 to D8: VPC and subnet CIDRs; routes follow the profile; no public IP
  on launch; default security group has no rules.
- The state bucket is fixed: versioning has been enabled since 04:56Z, so the
  group state will be versioned. Before Session 1, the two tests that timed
  out (open question 5) still need one clean run.

## Not tested, and why

- IAC-AC07 phases 1 and 2 on singleton: the first apply was not paused. They
  move to Session 1 and to US02's singleton re-apply (Owner decision).
- NS delegation through public resolvers: `dig` at 1.1.1.1 timed out from the
  QA sandbox and from the Owner's network. The Namecheap configuration is
  verified from the screenshot. Public resolution is a follow-up before US01c's
  ACM validation.
- First run only: the second bootstrap run was not executed, because the bucket
  was not in the state the script leaves (first-run failure 2). It was run in
  re-run 2 and by hand afterwards (above).

## Open questions

Status on 2026-11-06, after the Owner's answers: questions 1, 2 and 3 are
closed. Questions 4 and 5 are open.

1. (Owner/PM) Move the IAC-AC07 lock test: singleton phases 1 and 2 were not
   run. Proposal: prove IAC-AC07 on the group's first apply in Session 1
   (planned) and on the next singleton apply with pending changes (US02's
   re-apply). Not decided by QA.
   **Closed, decided by the Owner (2026-11-06):** phases 1 to 3 run on the
   group's first apply in Session 1 (2026-11-18) and on the next singleton
   apply with pending changes (US02's re-apply).
2. (Owner) How was `cms-terraform-state-store` created? CloudTrail shows no
   `put-*` call from the script. Did the Owner's script run end with the ready
   line, or with an error? The answer decides whether this is a rerun (Owner)
   or a script defect (Dev).
   **Closed (Owner, 2026-11-06):** the bucket was first created in the S3
   console, not by the script. The first-run failures came from that console
   creation, not from a script defect. The Owner's script run at 04:56Z
   configured the bucket fully (CloudTrail: all six `Put*` calls in the
   script's order).
3. (Owner) Approve a rerun of `./scripts/bootstrap_state_bucket.sh` to apply
   versioning, the TLS-only policy and the tags, followed by QA's re-run of the
   five failing tests, before Session 1. The current `singleton/terraform.tfstate`
   has `VersionId: null` and stays without earlier versions; versioning only
   protects writes after it is enabled.
   **Closed:** the Owner reran the script (04:56Z) and QA re-ran the tests
   (05:09Z and 05:15Z).
4. (QA, test note, no change made) `bucket_settings()` reads all settings in
   one call, so a missing policy also fails `test_us01b_d11_state_bucket_settings`
   and `test_us01b_d11_state_bucket_tags`, which do not assert on the policy.
   The tests are not wrong (they fail for a real defect), but each failure is
   less specific than it could be. QA proposes, in a later `test(US01b)` commit
   with Owner review, to read only the settings each test asserts on.
5. (Owner/QA) The QA sandbox's `aws s3api get-bucket-location` hung past 120 s
   four times in the two re-runs. Each time it was the last read of
   `bucket_settings()`, and the call answered in 3.7 s on its own. Proposal:
   the Owner runs, from their own shell (from `src/api`, with
   `AWS_PROFILE=3tier AWS_REGION=ap-southeast-1`),
   `pytest ../../tests/dev01/test_us01b_singleton.py -k "bootstrap_second_run or d11_state_bucket_tags"`,
   or QA re-runs these two tests in a later session. The bootstrap test
   runs the script again. It changes nothing, as shown above, but the Owner
   approves that run with the command. Still open: waiting for the Owner's
   run. QA also proposes
   adding `--cli-read-timeout`/`--cli-connect-timeout` and a single retry to
   `Dev01.aws()` in a later reviewed `test(US01b)` commit, so that a network
   stall reports as an environment error and not a test failure.
