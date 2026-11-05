"""US01b on dev01: the group layer in Session 1 (QA, US01b T0).

Criterion tests, dev01 part, for IAC-AC07, IAC-AC08 (group, and env after
US01c's env apply), IAC-AC14 on group, NET-AC01 and NET-AC02
(docs/specs/spec-001.md "IAC" and "NET"; docs/plans/US01b.plan.md section 4,
column "Session 1", section 7 items 1, 3, 5, 8 and 10, US01b-D12). The static
parts are in tests/infra/. Enabler checks of the network design (addresses,
NAT routes, hardening) are named by decision ID.

When: Session 1, Wed 2026-11-18, lean profile, during office hours and before
the destroy (plan section 7 item 10). Not part of `make check`. Results go to
reports/test-report-US01b-dev01.md.

Shell: from src/api of the session checkout, with
`export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1`, singleton applied, and
`awsenv/dev/group` initialised (`terraform init`). Group uses the default
workspace. Run in phases, in this order, selecting tests by `-k` inside this
one file:

1. Before the Owner starts the first group apply of the session
   (`terraform apply -var-file=tfvars/lean.tfvars`):
       .venv/bin/pytest ../../tests/dev01/test_us01b_group.py -k before_apply
2. While the Owner waits at that apply's `Enter a value:` prompt, from a
   second shell (QA says "go" only after this run has passed or failed):
       .venv/bin/pytest ../../tests/dev01/test_us01b_group.py -k during_apply
3. After the group apply has ended:
       .venv/bin/pytest ../../tests/dev01/test_us01b_group.py \
           -k "not before_apply and not during_apply and not env_state"
4. After US01c's env apply (workspace `dev01`, `awsenv/dev/env` initialised):
       .venv/bin/pytest ../../tests/dev01/test_us01b_group.py -k env_state

The no-change plan of phase 3 runs during office hours, as every no-change
plan does (CLAUDE.md, "Common Terraform Commands"). The report records the
time of each phase.
"""

from __future__ import annotations

from typing import Any

import pytest

LAYER = "group"
LEAN = "tfvars/lean.tfvars"
TIERS = ("public", "private", "isolated")
ZONES = {"a": "ap-southeast-1a", "b": "ap-southeast-1b"}
# US01b-D6: the address plan.
CIDRS = {
    "cms-public-a": "10.20.0.0/24",
    "cms-public-b": "10.20.1.0/24",
    "cms-private-a": "10.20.10.0/24",
    "cms-private-b": "10.20.11.0/24",
    "cms-isolated-a": "10.20.20.0/24",
    "cms-isolated-b": "10.20.21.0/24",
}
# Plan section 7 item 3: the group resources that have tags_all (NAT and EIP counted apart).
GROUP_TAGGABLE = {
    "aws_vpc": 1,
    "aws_default_security_group": 1,
    "aws_internet_gateway": 1,
    "aws_subnet": 6,
    "aws_route_table": 4,
}


def name_of(item: dict[str, Any]) -> str | None:
    return dev01_tags(item.get("Tags")).get("Name")


def dev01_tags(tags: list[dict[str, str]] | None) -> dict[str, str]:
    return {tag["Key"]: tag["Value"] for tag in tags or []}


def subnets(dev01: Any) -> list[dict[str, Any]]:
    data = dev01.aws_json(
        "ec2", "describe-subnets", "--filters", f"Name=vpc-id,Values={dev01.vpc_id()}"
    )
    return list(data["Subnets"])


def subnets_by_name(dev01: Any) -> dict[str, dict[str, Any]]:
    return {str(name_of(subnet)): subnet for subnet in subnets(dev01)}


def route_tables_for_subnet(dev01: Any, subnet_id: str) -> list[dict[str, Any]]:
    """The route table that applies to a subnet: its explicit one, or the VPC's main table."""
    explicit = dev01.aws_json(
        "ec2", "describe-route-tables",
        "--filters", f"Name=association.subnet-id,Values={subnet_id}",
    )["RouteTables"]  # fmt: skip
    if explicit:
        return list(explicit)
    main = dev01.aws_json(
        "ec2", "describe-route-tables",
        "--filters", f"Name=vpc-id,Values={dev01.vpc_id()}", "Name=association.main,Values=true",
    )["RouteTables"]  # fmt: skip
    return list(main)


def route_table_by_name(dev01: Any, name: str) -> dict[str, Any]:
    tables = dev01.aws_json(
        "ec2", "describe-route-tables",
        "--filters", f"Name=vpc-id,Values={dev01.vpc_id()}", f"Name=tag:Name,Values={name}",
    )["RouteTables"]  # fmt: skip
    assert len(tables) == 1, f"expected one route table named {name}, found {len(tables)}"
    return dict(tables[0])


def default_route(table: dict[str, Any]) -> dict[str, Any]:
    routes = [r for r in table["Routes"] if r.get("DestinationCidrBlock") == "0.0.0.0/0"]
    assert len(routes) == 1, f"{name_of(table)}: expected one 0.0.0.0/0 route: {table['Routes']}"
    return dict(routes[0])


# ---------------------------------------------------------------------------
# IAC-AC07: the lock, on the first group apply of Session 1 (US01b-D12)
# ---------------------------------------------------------------------------


def test_iac_ac07_group_before_apply_record_state_version(dev01: Any) -> None:
    """Phase 1, before the Owner runs `terraform apply -var-file=tfvars/lean.tfvars`.

    Records the version of group/terraform.tfstate ("absent" on the first
    apply ever; after an earlier session's destroy the object exists) and
    checks that no lock object exists yet.
    """
    version = dev01.lock_before_apply(LAYER)

    assert version, "no version recorded"


def test_iac_ac07_group_during_apply_lock_object_exists(dev01: Any) -> None:
    """Phase 2: the Owner's group apply waits at `Enter a value:`; its lock object exists."""
    dev01.lock_held_during_apply(LAYER)


def test_iac_ac07_group_during_apply_second_plan_stops_with_lock_error(dev01: Any) -> None:
    """Phase 2: `terraform plan -input=false -lock-timeout=0s -var-file=tfvars/lean.tfvars`
    exits non-zero with `Error acquiring the state lock`; the state version is unchanged."""
    dev01.second_plan_stops_during_apply(LAYER, var_file=LEAN)


def test_iac_ac07_group_after_apply_lock_released_plan_succeeds(dev01: Any) -> None:
    """Phase 3: the lock object is gone and `terraform plan -detailed-exitcode
    -var-file=tfvars/lean.tfvars` exits 0 (no changes), with no force-unlock."""
    dev01.lock_released_after_apply(LAYER, var_file=LEAN)


# ---------------------------------------------------------------------------
# IAC-AC08: the state bucket is in no layer's state
# ---------------------------------------------------------------------------


def test_iac_ac08_state_bucket_not_in_group_state(dev01: Any) -> None:
    """Phase 3."""
    assert dev01.state_list(LAYER), "group state is empty; is group applied?"

    assert dev01.state_bucket_in_state(LAYER) == []


def test_iac_ac08_env_state_does_not_hold_state_bucket(dev01: Any) -> None:
    """Phase 4, after US01c's env apply: env, workspace `dev01` (kept by US01c in Session 1).

    Reads only `terraform state list` and `state show` of the aws_s3_bucket*
    addresses, never the whole env state.
    """
    assert dev01.state_list("env", workspace="dev01"), "env (dev01) state is empty; is env applied?"

    assert dev01.state_bucket_in_state("env", workspace="dev01") == []


# ---------------------------------------------------------------------------
# IAC-AC14: the project tag on every taggable group resource
# ---------------------------------------------------------------------------


def test_iac_ac14_group_every_taggable_resource_has_project_tag(dev01: Any) -> None:
    """A resource supports tags when it has `tags_all` in `terraform show -json` (plan 7.3)."""
    taggable = [
        item
        for item in dev01.managed_resources(dev01.show(LAYER))
        if isinstance(item.get("values", {}).get("tags_all"), dict)
    ]
    types: dict[str, int] = {}
    for item in taggable:
        types[item["type"]] = types.get(item["type"], 0) + 1
    for resource_type, count in GROUP_TAGGABLE.items():
        assert types.get(resource_type, 0) >= count, f"{resource_type} x{count} missing: {types}"
    assert types.get("aws_nat_gateway", 0) >= 1, types
    assert types.get("aws_eip", 0) == types.get("aws_nat_gateway", 0), types

    missing = [
        item["address"]
        for item in taggable
        if item["values"]["tags_all"].get("Project") != "cms"
        or item["values"]["tags_all"].get("ManagedBy") != "terraform"
    ]
    assert missing == [], f"resources without Project = cms, ManagedBy = terraform: {missing}"


def test_iac_ac14_group_tags_spot_check_with_aws_cli(dev01: Any) -> None:
    vpc = dev01.aws_json("ec2", "describe-vpcs", "--vpc-ids", dev01.vpc_id())["Vpcs"][0]
    checked = [("cms-vpc", dev01_tags(vpc.get("Tags")))]
    for name, subnet in subnets_by_name(dev01).items():
        checked.append((name, dev01_tags(subnet.get("Tags"))))
    nats = dev01.aws_json(
        "ec2", "describe-nat-gateways",
        "--filter", f"Name=vpc-id,Values={dev01.vpc_id()}", "Name=state,Values=available",
    )["NatGateways"]  # fmt: skip
    checked += [(str(name_of(nat)), dev01_tags(nat.get("Tags"))) for nat in nats]

    for name, tags in checked:
        assert tags.get("Project") == "cms", f"{name}: {tags}"
        assert tags.get("ManagedBy") == "terraform", f"{name}: {tags}"


# ---------------------------------------------------------------------------
# NET-AC01: two zones, three tiers in each
# ---------------------------------------------------------------------------


def test_net_ac01_vpc_has_six_subnets_three_tiers_two_zones(dev01: Any) -> None:
    found = subnets(dev01)

    assert len(found) == 6, f"expected 6 subnets in cms-vpc, found {len(found)}"
    by_name = {str(name_of(subnet)): subnet for subnet in found}
    expected = {f"cms-{tier}-{zone}" for tier in TIERS for zone in ZONES}
    assert set(by_name) == expected, sorted(by_name)
    for name, subnet in by_name.items():
        zone = subnet["AvailabilityZone"]
        assert zone == ZONES[name[-1]], f"{name} is in {zone}"
    assert {subnet["AvailabilityZone"] for subnet in found} == set(ZONES.values())


def test_net_ac01_group_outputs_match_the_subnets(dev01: Any) -> None:
    outputs = dev01.outputs(LAYER)
    by_name = subnets_by_name(dev01)

    assert outputs["vpc_id"] == dev01.vpc_id()
    assert outputs["availability_zones"] == ["ap-southeast-1a", "ap-southeast-1b"]
    for tier in TIERS:
        expected = [by_name[f"cms-{tier}-a"]["SubnetId"], by_name[f"cms-{tier}-b"]["SubnetId"]]
        assert outputs[f"{tier}_subnet_ids"] == expected, f"{tier}_subnet_ids not ordered a, b"


# ---------------------------------------------------------------------------
# NET-AC02: the isolated subnets have only the local route
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("zone", sorted(ZONES))
def test_net_ac02_isolated_subnet_route_tables_have_only_local_route(
    dev01: Any, zone: str
) -> None:
    subnet = subnets_by_name(dev01)[f"cms-isolated-{zone}"]
    tables = route_tables_for_subnet(dev01, subnet["SubnetId"])
    assert tables, f"no route table applies to cms-isolated-{zone}"

    for table in tables:
        routes = table["Routes"]
        others = [
            route
            for route in routes
            if route.get("GatewayId") != "local"
            and not str(route.get("GatewayId", "")).startswith("vpce-")
        ]
        assert others == [], f"{name_of(table)}: routes other than local: {others}"
        assert any(route.get("GatewayId") == "local" for route in routes), routes


def test_net_ac02_isolated_subnets_use_cms_isolated_rt(dev01: Any) -> None:
    by_name = subnets_by_name(dev01)
    table = route_table_by_name(dev01, "cms-isolated-rt")
    associated = {a.get("SubnetId") for a in table["Associations"] if not a.get("Main")}

    expected = {by_name["cms-isolated-a"]["SubnetId"], by_name["cms-isolated-b"]["SubnetId"]}
    assert associated == expected


# ---------------------------------------------------------------------------
# US01b-D6 to US01b-D8: addresses, NAT routes, hardening
# ---------------------------------------------------------------------------


def test_us01b_d6_vpc_and_subnet_cidrs(dev01: Any) -> None:
    vpc = dev01.aws_json("ec2", "describe-vpcs", "--vpc-ids", dev01.vpc_id())["Vpcs"][0]

    assert vpc["CidrBlock"] == "10.20.0.0/16"
    assert {name: s["CidrBlock"] for name, s in subnets_by_name(dev01).items()} == CIDRS


def test_us01b_d7_routes_follow_the_profile(dev01: Any) -> None:
    """Lean: one NAT gateway, cms-nat-a in cms-public-a, used by both private tables.
    Full: each private table uses the NAT gateway of its own zone."""
    by_name = subnets_by_name(dev01)
    nats = dev01.aws_json(
        "ec2", "describe-nat-gateways",
        "--filter", f"Name=vpc-id,Values={dev01.vpc_id()}", "Name=state,Values=available",
    )["NatGateways"]  # fmt: skip
    nat_by_name = {str(name_of(nat)): nat for nat in nats}
    assert len(nats) == len(dev01.outputs(LAYER)["nat_gateway_ids"]), nat_by_name
    assert "cms-nat-a" in nat_by_name, sorted(nat_by_name)
    assert nat_by_name["cms-nat-a"]["SubnetId"] == by_name["cms-public-a"]["SubnetId"]
    igws = dev01.aws_json(
        "ec2", "describe-internet-gateways",
        "--filters", f"Name=attachment.vpc-id,Values={dev01.vpc_id()}",
    )["InternetGateways"]  # fmt: skip
    assert [name_of(igw) for igw in igws] == ["cms-igw"]

    public = route_table_by_name(dev01, "cms-public-rt")
    assert default_route(public).get("GatewayId") == igws[0]["InternetGatewayId"]
    for zone in sorted(ZONES):
        private = route_table_by_name(dev01, f"cms-private-rt-{zone}")
        nat = nat_by_name.get(f"cms-nat-{zone}", nat_by_name["cms-nat-a"])
        assert default_route(private).get("NatGatewayId") == nat["NatGatewayId"], zone


def test_us01b_d8_no_public_ip_on_launch(dev01: Any) -> None:
    flags = {name: s["MapPublicIpOnLaunch"] for name, s in subnets_by_name(dev01).items()}

    assert flags == dict.fromkeys(CIDRS, False)


def test_us01b_d8_default_security_group_has_no_rules(dev01: Any) -> None:
    groups = dev01.aws_json(
        "ec2", "describe-security-groups",
        "--filters", f"Name=vpc-id,Values={dev01.vpc_id()}", "Name=group-name,Values=default",
    )["SecurityGroups"]  # fmt: skip

    assert len(groups) == 1
    assert groups[0]["IpPermissions"] == []
    assert groups[0]["IpPermissionsEgress"] == []
    assert dev01_tags(groups[0].get("Tags")).get("Name") == "cms-default-sg"
