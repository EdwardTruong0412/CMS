ESCALATE

## Why
The change is clean: all three reviews PASS, the test report PASS, no conflicts, and only QA's commit touches `tests/`. It still has to go to the Owner, because it creates the account and network layers (`awsenv/dev/singleton/`, `awsenv/dev/group/`), edits `CLAUDE.md`, adds a new Terraform provider (hashicorp/aws 6.72.0), and adds always-on singleton resources (Route 53 hosted zone, ECR). Each of these is on the escalation list.

## Acceptance criteria
1. IAC-AC03 no `resource` in `awsenv/`: met (static). Test report shows the layout tests pass. I checked myself: `grep 'resource "' awsenv` returns nothing, and the roots contain only module calls.
2. IAC-AC04 README with every template heading: met. `modules/README_TEMPLATE.md` has the nine headings, all three module READMEs carry them, and the tests pass.
3. IAC-AC07 state lock: static part met. Both backends set `use_lockfile = true` and `encrypt = true` with no `dynamodb_table`; I checked `awsenv/dev/group/backend.tf` myself. The live lock test on the Owner's first apply is still to come (planned for G6, plan section 7).
4. IAC-AC08 versioned state bucket outside every layer, documented: static part met. The script and runbook pass, with a fake-CLI test of the first run, second run and 403 stop, and no `.tf` declares the bucket. The live dev01 checks are still to come.
5. IAC-AC14 common project tag: static part met. Provider `default_tags` sets `Project`/`ManagedBy`, and module tags hold only `Name`. The live check is still to come.
6. NET-AC01 two zones, three tiers each: static part met. There are three subnet resources with count 2 and the network module requires exactly two zones. The live `describe-subnets` check is still to come.
7. NET-AC02 isolated subnets without an internet route: static part met. I checked myself: `aws_route_table.isolated` (`modules/network/main.tf:96`) has no route block, and the only reference to it is the isolated association at line 116. Both `aws_route` resources target the public and private tables. The live check is still to come.

## Escalation checks
- Governance: triggered. `CLAUDE.md` gets one line in "State Management" pointing to `scripts/bootstrap_state_bucket.sh` and `docs/runbooks/bootstrap.md`. The line is harmless and was planned (T5).
- Pipeline: clear. Nothing under `.github/` changed.
- Account and network layers: triggered. The story creates `awsenv/dev/singleton/` (ECR, Route 53 zone) and `awsenv/dev/group/` (VPC, 6 subnets, IGW, NAT, route tables), plus the modules only they call (`container_registry`, `dns_zone`, `network`).
- Exposure and access: triggered, as expected. An internet gateway and NAT EIPs are added (NET-AC05). The default SG is closed, `map_public_ip_on_launch = false` on all subnets, and the isolated table has no default route. The bootstrap script creates a new state bucket policy: a TLS-only deny with all four public access blocks and BucketOwnerEnforced, so nothing is widened. No IAM, KMS or Secrets Manager changes.
- Stateful resources: clear. No plan was run (nothing is deployed yet) and the diff only adds resources. Note: ECR `force_delete = true` was the approved choice (Q-D12), and the zone has `force_destroy = false`.
- Cost: triggered. Singleton adds always-on spend between sessions, about $0.50/month for the hosted zone plus ECR storage (at most 5 images). The infra review puts that at roughly a quarter of the $2 alert (Q-O57). Group lean is about $0.064/hour per session, and full is about double. `dev01.tfvars` is untouched.
- Data: clear. No migration and no personal data.
- Identity: clear. No login, session, token or role code.
- Dependencies: triggered. New Terraform provider `hashicorp/aws ~> 6.71`, locked at 6.72.0 with darwin_arm64 and linux_amd64 hashes (both `.terraform.lock.hcl` files).
- Scope: clear, with one note. The commits match plan tasks T1 to T5. The plan itself names `aws_eip.nat` (the module's only EIP), which breaks the AGENTS.md rule that the only resource of its type is named `this`. QA's test depends on that name. The code review rated this a plan defect, not a Dev finding.

## For the Owner
Decisions needed before this merges:
1. Accept the new account and network layers as built: `awsenv/dev/singleton/*`, `awsenv/dev/group/*`, `modules/container_registry/main.tf`, `modules/dns_zone/main.tf`, `modules/network/main.tf`, `awsenv/dev/group/tfvars/{lean,full}.tfvars`.
2. Accept the new provider pin and lock: `awsenv/dev/singleton/.terraform.lock.hcl`, `awsenv/dev/group/.terraform.lock.hcl` (hashicorp/aws 6.72.0).
3. Accept the always-on singleton cost (hosted zone about $0.50/month plus ECR storage) against the $2 alert. See `factory/stories/US01b/round-1/review-infra.md`, note 5.
4. Accept the one-line `CLAUDE.md` change.
5. Decide on the `aws_eip.nat` naming exception (`modules/network/main.tf:52`): either log it as an accepted exception in the Decisions log, or rename it to `this` in a later story together with `tests/infra/test_terraform_layout.py:945`.
6. Review the bootstrap script you will run by hand: `scripts/bootstrap_state_bucket.sh`, `docs/runbooks/bootstrap.md`.
Also be aware that the dev01 halves of IAC-AC07, IAC-AC08, IAC-AC14, NET-AC01 and NET-AC02 are proven only after your bootstrap and applies (the `tests/dev01/test_us01b_*.py` tests), at G6.
