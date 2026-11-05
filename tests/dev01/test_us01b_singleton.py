"""US01b on dev01: the state bucket and the singleton layer (QA, US01b T0).

Criterion tests, dev01 part, for IAC-AC07, IAC-AC08 and IAC-AC14 on
singleton (docs/specs/spec-001.md "IAC"; docs/plans/US01b.plan.md section 4,
column "After the Owner's singleton apply", section 7 items 3 to 5 and 8,
US01b-D12). The static parts are in tests/infra/. Enabler checks of the
singleton interface (outputs, ECR settings, hosted zone, bucket settings) are
named by decision or task ID.

When: after the merge, once the Owner has run the bootstrap script (runbook
step 1); target Thu 12 or Fri 13 Nov 2026 (plan section 7 item 10). Not part
of `make check`. Results go to reports/test-report-US01b-dev01.md.

Shell: from src/api of a checkout of `develop` with the US01b merge, with
`export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1`, and
`awsenv/dev/singleton` initialised (`terraform init`). Run in phases, in this
order, selecting tests by `-k` inside this one file:

1. Before the Owner starts the first singleton apply:
       .venv/bin/pytest ../../tests/dev01/test_us01b_singleton.py -k before_apply
2. While the Owner waits at the apply's `Enter a value:` prompt, from a second
   shell (QA says "go" only after this run has passed or failed):
       .venv/bin/pytest ../../tests/dev01/test_us01b_singleton.py -k during_apply
3. After the Owner has typed `yes`, the apply has ended, and the Owner has
   told QA that singleton is applied (plan section 10, after-merge step 4):
       .venv/bin/pytest ../../tests/dev01/test_us01b_singleton.py \
           -k "not before_apply and not during_apply"

Phase 3 includes the second run of the bootstrap script, a no-change call that
the Owner approves with the check's command list (plan section 7 item 4). The
report records the time of each phase.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "bootstrap_state_bucket.sh"
LAYER = "singleton"
STATE_BUCKET = "cms-terraform-state-store"
REGION = "ap-southeast-1"
ALREADY_EXISTS = "Bucket {bucket} already exists in account {account}; re-applying its settings."
READY_LINE = f"State bucket {STATE_BUCKET} is ready (versioning Enabled)."
# Plan section 7 item 3: the singleton resources that have tags_all.
SINGLETON_TAGGABLE = {"aws_ecr_repository": 1, "aws_route53_zone": 1}


def bucket_settings(dev01: Any) -> dict[str, Any]:
    """Every setting the bootstrap script applies, read back from the real bucket."""
    owner = ("--bucket", STATE_BUCKET, "--expected-bucket-owner", dev01.account_id())
    policy = dev01.aws_json("s3api", "get-bucket-policy", *owner)
    return {
        "versioning": dev01.aws_json("s3api", "get-bucket-versioning", *owner),
        "encryption": dev01.aws_json("s3api", "get-bucket-encryption", *owner),
        "public_access_block": dev01.aws_json("s3api", "get-public-access-block", *owner),
        "ownership": dev01.aws_json("s3api", "get-bucket-ownership-controls", *owner),
        "policy": json.loads(policy["Policy"]),
        "tags": dev01.tag_list(dev01.aws_json("s3api", "get-bucket-tagging", *owner)["TagSet"]),
        "location": dev01.aws_json("s3api", "get-bucket-location", *owner),
    }


# ---------------------------------------------------------------------------
# IAC-AC07: the lock, on the Owner's first singleton apply (US01b-D12)
# ---------------------------------------------------------------------------


def test_iac_ac07_singleton_before_apply_record_state_version(dev01: Any) -> None:
    """Phase 1, before the Owner runs `terraform apply` in awsenv/dev/singleton.

    Records the version of singleton/terraform.tfstate ("absent" on the first
    apply) and checks that no lock object exists yet.
    """
    version = dev01.lock_before_apply(LAYER)

    assert version, "no version recorded"


def test_iac_ac07_singleton_during_apply_lock_object_exists(dev01: Any) -> None:
    """Phase 2: the Owner's apply waits at `Enter a value:`; its lock object exists."""
    dev01.lock_held_during_apply(LAYER)


def test_iac_ac07_singleton_during_apply_second_plan_stops_with_lock_error(dev01: Any) -> None:
    """Phase 2: `terraform plan -input=false -lock-timeout=0s` exits non-zero with
    `Error acquiring the state lock`; the state object's version is unchanged."""
    dev01.second_plan_stops_during_apply(LAYER, var_file=None)


def test_iac_ac07_singleton_after_apply_lock_released_plan_succeeds(dev01: Any) -> None:
    """Phase 3: the lock object is gone and `terraform plan -detailed-exitcode`
    exits 0 (no changes), with no force-unlock."""
    dev01.lock_released_after_apply(LAYER, var_file=None)


# ---------------------------------------------------------------------------
# IAC-AC08: the state bucket is versioned and outside every layer
# ---------------------------------------------------------------------------


def test_iac_ac08_state_bucket_versioning_enabled(dev01: Any) -> None:
    versioning = dev01.aws_json(
        "s3api", "get-bucket-versioning",
        "--bucket", STATE_BUCKET, "--expected-bucket-owner", dev01.account_id(),
    )  # fmt: skip

    assert versioning.get("Status") == "Enabled", versioning


def test_iac_ac08_state_bucket_not_in_singleton_state(dev01: Any) -> None:
    addresses = dev01.state_list(LAYER)
    assert addresses, "singleton state is empty; is singleton applied?"

    assert dev01.state_bucket_in_state(LAYER) == []


def test_iac_ac08_bootstrap_second_run_changes_nothing(dev01: Any) -> None:
    """QA's second run of the bootstrap script (Owner-approved no-change call).

    It prints the "already exists" line, ends with the ready line, exits 0,
    and every setting read back is the same as before the run.
    """
    assert SCRIPT.is_file(), "scripts/bootstrap_state_bucket.sh is missing"
    before = bucket_settings(dev01)

    result = subprocess.run(  # noqa: S603  # fixed arguments, no shell
        [str(SCRIPT)],
        cwd=REPO_ROOT,
        env=dict(os.environ),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    lines = [line.rstrip() for line in result.stdout.splitlines() if line.strip()]

    assert result.returncode == 0, f"exit {result.returncode}\n{result.stdout}\n{result.stderr}"
    expected = ALREADY_EXISTS.format(bucket=STATE_BUCKET, account=dev01.account_id())
    assert expected in lines, result.stdout
    assert lines[-1] == READY_LINE, result.stdout
    assert bucket_settings(dev01) == before


# ---------------------------------------------------------------------------
# US01b-D11: the other settings of the state bucket (plan section 7 item 4)
# ---------------------------------------------------------------------------


def test_us01b_d11_state_bucket_settings(dev01: Any) -> None:
    settings = bucket_settings(dev01)

    rules = settings["encryption"]["ServerSideEncryptionConfiguration"]["Rules"]
    assert [r["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"] for r in rules] == ["AES256"]
    block = settings["public_access_block"]["PublicAccessBlockConfiguration"]
    assert block == {
        "BlockPublicAcls": True,
        "IgnorePublicAcls": True,
        "BlockPublicPolicy": True,
        "RestrictPublicBuckets": True,
    }
    ownership = settings["ownership"]["OwnershipControls"]["Rules"]
    assert [rule["ObjectOwnership"] for rule in ownership] == ["BucketOwnerEnforced"]
    assert settings["location"].get("LocationConstraint") == REGION


def test_us01b_d11_state_bucket_tls_only_policy(dev01: Any) -> None:
    statements = bucket_settings(dev01)["policy"]["Statement"]
    statements = statements if isinstance(statements, list) else [statements]
    arn = f"arn:aws:s3:::{STATE_BUCKET}"

    assert [s.get("Sid") for s in statements] == ["DenyInsecureTransport"]
    statement = statements[0]
    assert statement["Effect"] == "Deny"
    assert statement["Principal"] in ("*", {"AWS": "*"})
    assert statement["Action"] in ("s3:*", ["s3:*"])
    assert set(statement["Resource"]) == {arn, f"{arn}/*"}
    assert str(statement["Condition"]["Bool"]["aws:SecureTransport"]).lower() == "false"


def test_us01b_d11_state_bucket_tags(dev01: Any) -> None:
    tags = bucket_settings(dev01)["tags"]

    assert tags.get("Project") == "cms", tags
    assert tags.get("ManagedBy") == "bootstrap-script", tags


# ---------------------------------------------------------------------------
# IAC-AC14: the project tag on every taggable singleton resource
# ---------------------------------------------------------------------------


def test_iac_ac14_singleton_every_taggable_resource_has_project_tag(dev01: Any) -> None:
    """A resource supports tags when it has `tags_all` in `terraform show -json` (plan 7.3)."""
    taggable = [
        item
        for item in dev01.managed_resources(dev01.show(LAYER))
        if isinstance(item.get("values", {}).get("tags_all"), dict)
    ]
    types: dict[str, int] = {}
    for item in taggable:
        types[item["type"]] = types.get(item["type"], 0) + 1
    for resource_type, count in SINGLETON_TAGGABLE.items():
        assert types.get(resource_type, 0) >= count, f"{resource_type} missing from state: {types}"

    missing = [
        item["address"]
        for item in taggable
        if item["values"]["tags_all"].get("Project") != "cms"
        or item["values"]["tags_all"].get("ManagedBy") != "terraform"
    ]
    assert missing == [], f"resources without Project = cms, ManagedBy = terraform: {missing}"


def test_iac_ac14_singleton_tags_spot_check_with_aws_cli(dev01: Any) -> None:
    outputs = dev01.outputs(LAYER)
    ecr = dev01.aws_json(
        "ecr", "list-tags-for-resource", "--resource-arn", outputs["ecr_repository_arn"]
    )
    zone_id = str(outputs["hosted_zone_id"]).rsplit("/", 1)[-1]
    zone = dev01.aws_json(
        "route53", "list-tags-for-resource", "--resource-type", "hostedzone",
        "--resource-id", zone_id,
    )  # fmt: skip

    for name, tags in (
        ("ECR cms-api", dev01.tag_list(ecr["tags"])),
        ("zone cms.imaprof.ink", dev01.tag_list(zone["ResourceTagSet"]["Tags"])),
    ):
        assert tags.get("Project") == "cms", f"{name}: {tags}"
        assert tags.get("ManagedBy") == "terraform", f"{name}: {tags}"


# ---------------------------------------------------------------------------
# Plan section 6: singleton outputs and resource settings
# ---------------------------------------------------------------------------


def test_us01b_t2_singleton_outputs(dev01: Any) -> None:
    outputs = dev01.outputs(LAYER)

    assert set(outputs) >= {
        "ecr_repository_name",
        "ecr_repository_arn",
        "ecr_repository_url",
        "hosted_zone_id",
        "hosted_zone_name",
        "hosted_zone_name_servers",
    }, sorted(outputs)
    assert outputs["ecr_repository_name"] == "cms-api"
    assert str(outputs["ecr_repository_url"]).endswith(f".dkr.ecr.{REGION}.amazonaws.com/cms-api")
    assert str(outputs["hosted_zone_name"]).rstrip(".") == "cms.imaprof.ink"
    assert len(outputs["hosted_zone_name_servers"]) == 4


def test_us01b_d9_ecr_repository_settings(dev01: Any) -> None:
    data = dev01.aws_json("ecr", "describe-repositories", "--repository-names", "cms-api")
    repo = data["repositories"][0]

    assert repo["imageTagMutability"] == "IMMUTABLE"
    assert repo["imageScanningConfiguration"]["scanOnPush"] is True
    assert repo["encryptionConfiguration"]["encryptionType"] == "AES256"
    policy = dev01.aws_json("ecr", "get-lifecycle-policy", "--repository-name", "cms-api")
    assert len(json.loads(policy["lifecyclePolicyText"])["rules"]) == 2


def test_us01b_d10_hosted_zone_is_public_with_four_name_servers(dev01: Any) -> None:
    outputs = dev01.outputs(LAYER)
    zone_id = str(outputs["hosted_zone_id"]).rsplit("/", 1)[-1]
    zone = dev01.aws_json("route53", "get-hosted-zone", "--id", zone_id)

    assert zone["HostedZone"]["Name"] == "cms.imaprof.ink."
    assert zone["HostedZone"]["Config"]["PrivateZone"] is False
    assert sorted(zone["DelegationSet"]["NameServers"]) == sorted(
        outputs["hosted_zone_name_servers"]
    )


@pytest.mark.parametrize("output", ["ecr_repository_arn", "ecr_repository_url"])
def test_us01b_t2_singleton_resources_in_ap_southeast_1(dev01: Any, output: str) -> None:
    assert REGION in str(dev01.outputs(LAYER)[output])
