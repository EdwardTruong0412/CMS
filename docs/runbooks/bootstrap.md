# Bootstrap the CMS account

## 1. Purpose

Use this procedure for the first build and for a rebuild after final teardown
(US39). It creates the Terraform state bucket outside all layers, applies
singleton, delegates DNS, and prepares group for a check session. The Owner runs
these commands after reviewing the changes; the story build does not run them.

## 2. Prerequisites

- AWS CLI v2 and a working local profile `3tier` for the intended account.
- Run `make bootstrap` to install Terraform 1.16.4 through `tfenv` and the project
  tools. Run the commands from the repository root unless stated otherwise.
- `dig`, access to Namecheap for `imaprof.ink`, and QA available for the first
  apply's state-lock checks.
- Keep singleton and group in the `default` workspace (`TF_WORKSPACE` unset).
  Only the later env layer uses workspace `dev01`.

## 3. Step 1: state bucket

From the repository root:

```bash
export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1
./scripts/bootstrap_state_bucket.sh
```

The script creates `cms-terraform-state-store` in ap-southeast-1 or re-applies its
settings. It enables versioning, SSE-S3 (AES256), all four public access blocks,
`BucketOwnerEnforced` ownership, a TLS-only bucket policy and bootstrap tags.
It prints the versioning status, encryption algorithm and public access settings,
ending with:

```text
State bucket cms-terraform-state-store is ready (versioning Enabled).
```

It is safe to re-run in the same account. An existing bucket produces this line
before the settings are re-applied:

```text
Bucket cms-terraform-state-store already exists in account <id>; re-applying its settings.
```

Any `head-bucket` error other than `(404)`, including `(403)`, stops the script
with exit 1 before any changes. Check the profile/account and permissions; if
another account owns the name, raise it to the Owner rather than changing the
bucket name locally. The script never reads secret values.

## 4. Step 2: singleton apply

From the repository root:

```bash
cd awsenv/dev/singleton
export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1
terraform init
terraform apply
```

Review the plan before typing `yes`; do not save an `-out` plan file. On the first
apply, **wait at `Enter a value:` until QA says "go"**. QA records the prior state
version, verifies that the S3 `.tflock` object exists and that a second plan fails
with a lock error without changing state. After QA says "go", type `yes`. QA then
verifies the lock is released and a no-change plan succeeds without force-unlock
(IAC-AC07; plan section 7, item 5).

Singleton creates ECR `cms-api` and public hosted zone `cms.imaprof.ink`. It stays
between sessions and starts the always-on storage/hosted-zone costs accepted in
the plan. Tell QA when it is applied so the remaining singleton checks and the
approved second bootstrap run can finish. QA records evidence from
`tests/dev01/test_us01b_singleton.py` in `reports/test-report-US01b-dev01.md`.

## 5. Step 3: NS delegation at Namecheap

In the singleton directory, read the four name servers:

```bash
terraform output hosted_zone_name_servers
```

In Namecheap, open Domain List, `imaprof.ink`, Advanced DNS. Add four NS records
with host `cms`, one value per name server and TTL automatic. This delegates only
`cms.imaprof.ink`; the root domain and other subdomains remain at Namecheap.
Verify from outside AWS:

```bash
dig +short NS cms.imaprof.ink @1.1.1.1
dig +short NS cms.imaprof.ink @8.8.8.8
```

Both must list the four Route 53 servers. Add the records right after singleton
apply to allow propagation before US01c's env apply and ACM DNS validation
(R-06). If results differ, wait for DNS propagation and check the four records
before proceeding to env.

## 6. Group layer in a check session

From the repository root, apply group before env:

```bash
cd awsenv/dev/group
export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1
terraform init
terraform apply -var-file=tfvars/lean.tfvars
```

Review the plan. On Session 1's first group apply, wait at `Enter a value:` until
QA says "go" for the same lock test, then type `yes`. QA checks
`tests/dev01/test_us01b_group.py`; the env-state check runs after US01c's env apply.
Results go to `reports/test-report-US01b-dev01.md`.

At the end of every session, destroy env first, then run in the group directory:

```bash
terraform destroy -var-file=tfvars/lean.tfvars
```

Use the same profile file for apply and destroy. Full verification uses
`tfvars/full.tfvars` for both commands, with no `.tf` changes. Group bills only
during sessions; do not leave its NAT gateways running between sessions.
The session procedure will continue in `docs/runbooks/session.md` (US01c).

## 7. Steps added by later stories

The remaining Q-D11 steps are documented by their owning stories:

- US05: GitHub repository variables, secret and environment `dev01` limited to
  `develop`.
- US02: confirm the SNS email subscription after group apply.
- US03: create workspace `dev01` through its workflow.
- US01c and US06: first image build/push, env apply and delivery. ECR tags are
  immutable; US06 checks for an existing commit SHA and treats it as a successful
  push, skipping that build/push.
- US08: the Owner reads the setup token and creates the first admin.

## 8. What this procedure never does

It never deletes the state bucket or its versions. The bucket is outside every
layer's Terraform state and is deleted last, by hand, only with the Owner's
approval during final teardown (US40, TDN-AC05). Singleton is also kept between
sessions. At final teardown, empty the zone except NS/SOA before destroying it;
the Owner removes the Namecheap NS records.
