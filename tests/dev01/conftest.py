"""Shared helpers for the dev01 checks (QA, US01b T0; folder tests/dev01, KO-9).

These checks need the real AWS account and network. They are not part of
`make check` (`testpaths` in src/api/pyproject.toml names only tests/api and
tests/infra). QA runs them by file from src/api, in a shell with the Owner's
profile, as docs/plans/US01b.plan.md section 7 item 8 says:

    cd src/api
    export AWS_PROFILE=3tier AWS_REGION=ap-southeast-1
    .venv/bin/pytest ../../tests/dev01/test_us01b_singleton.py

The AWS CLI and Terraform are called through `subprocess` (US01b-D13); no boto3.
Every command here only reads, except the ones a test docstring names (the
second bootstrap run, and `terraform plan`, which takes and releases the state
lock). No command prints or reads a secret.

Terraform runs in the root of this checkout (`awsenv/dev/<layer>`), which must
already be initialised with the S3 backend (`terraform init`, an Owner-approved
step of the session). A test fails, never skips, when that is missing.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYERS_DIR = REPO_ROOT / "awsenv" / "dev"
STATE_BUCKET = "cms-terraform-state-store"
REGION = "ap-southeast-1"
PROFILE = "3tier"
# The "before" state version of the IAC-AC07 lock test is kept between the
# phase runs here (one small text file per layer).
EVIDENCE_DIR = Path(
    os.environ.get("CMS_QA_EVIDENCE_DIR", str(Path(tempfile.gettempdir()) / "cms-qa-us01b"))
)
LOCK_RELEASE_TIMEOUT_SECONDS = 600


def state_key(layer: str) -> str:
    """State object key of a layer (plan section 6, US01b-D3)."""
    return f"{layer}/terraform.tfstate"


class Dev01:
    """AWS CLI and Terraform calls for the dev01 checks."""

    def __init__(self) -> None:
        self._account: str | None = None

    # -- AWS CLI ----------------------------------------------------------

    def aws(self, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603  # fixed arguments, no shell
            ["aws", *args, "--no-cli-pager"],  # noqa: S607  # aws from PATH on purpose
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def aws_json(self, *args: str) -> Any:
        result = self.aws(*args, "--output", "json")
        if result.returncode != 0:
            pytest.fail(f"aws {' '.join(args)} failed, exit {result.returncode}: {result.stderr}")
        return json.loads(result.stdout) if result.stdout.strip() else None

    def account_id(self) -> str:
        if self._account is None:
            result = self.aws(
                "sts", "get-caller-identity", "--query", "Account", "--output", "text"
            )
            if result.returncode != 0:
                pytest.fail(f"aws sts get-caller-identity failed: {result.stderr}")
            self._account = result.stdout.strip()
        return self._account

    def object_version(self, key: str) -> str:
        """VersionId of a state bucket object, or "absent"."""
        result = self.aws(
            "s3api", "head-object", "--bucket", STATE_BUCKET, "--key", key,
            "--expected-bucket-owner", self.account_id(),
            "--query", "VersionId", "--output", "text",
        )  # fmt: skip
        if result.returncode == 0:
            return result.stdout.strip()
        if "(404)" in result.stderr or "Not Found" in result.stderr:
            return "absent"
        pytest.fail(f"head-object {key} failed, exit {result.returncode}: {result.stderr}")

    def object_exists(self, key: str) -> bool:
        return self.object_version(key) != "absent"

    def vpc_id(self) -> str:
        data = self.aws_json("ec2", "describe-vpcs", "--filters", "Name=tag:Name,Values=cms-vpc")
        vpcs = data["Vpcs"]
        assert len(vpcs) == 1, f"expected one VPC named cms-vpc, found {len(vpcs)}"
        return str(vpcs[0]["VpcId"])

    # -- Terraform --------------------------------------------------------

    def terraform(
        self, layer: str, *args: str, workspace: str | None = None, timeout: int = 900
    ) -> subprocess.CompletedProcess[str]:
        root = LAYERS_DIR / layer
        if not (root / ".terraform").is_dir():
            pytest.fail(f"awsenv/dev/{layer} is not initialised: run `terraform init` there first")
        env = dict(os.environ)
        env.update({"CHECKPOINT_DISABLE": "1", "TF_IN_AUTOMATION": "1", "TF_INPUT": "0"})
        env.pop("TF_WORKSPACE", None)
        if workspace is not None:
            env["TF_WORKSPACE"] = workspace
        return subprocess.run(  # noqa: S603  # fixed arguments, no shell
            ["terraform", f"-chdir={root}", *args],  # noqa: S607  # terraform from PATH
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def terraform_ok(self, layer: str, *args: str, workspace: str | None = None) -> str:
        result = self.terraform(layer, *args, workspace=workspace)
        if result.returncode != 0:
            pytest.fail(
                f"terraform {' '.join(args)} in {layer} failed, exit {result.returncode}: "
                f"{result.stderr[-3000:]}"
            )
        return result.stdout

    def outputs(self, layer: str) -> dict[str, Any]:
        data = json.loads(self.terraform_ok(layer, "output", "-json"))
        return {name: item["value"] for name, item in data.items()}

    def show(self, layer: str) -> dict[str, Any]:
        data: dict[str, Any] = json.loads(self.terraform_ok(layer, "show", "-json", "-no-color"))
        return data

    def state_list(self, layer: str, workspace: str | None = None) -> list[str]:
        out = self.terraform_ok(layer, "state", "list", workspace=workspace)
        return [line.strip() for line in out.splitlines() if line.strip()]

    def state_bucket_in_state(self, layer: str, workspace: str | None = None) -> list[str]:
        """Managed aws_s3_bucket* addresses of a layer whose attributes name the state bucket."""
        found: list[str] = []
        for address in self.state_list(layer, workspace=workspace):
            resource_type = Dev01.managed_type(address)
            if resource_type is None or not resource_type.startswith("aws_s3_bucket"):
                continue
            shown = self.terraform_ok(
                layer, "state", "show", "-no-color", address, workspace=workspace
            )
            if f'"{STATE_BUCKET}"' in shown:
                found.append(address)
        return found

    @staticmethod
    def managed_type(address: str) -> str | None:
        """Resource type of a state address, or None for a data source."""
        rest = address
        while rest.startswith("module."):
            match = re.match(r"module\.[^.\[]+(?:\[[^\]]*\])?\.", rest)
            if match is None:
                return None
            rest = rest[match.end() :]
        if rest.startswith("data."):
            return None
        return rest.split(".", 1)[0]

    @staticmethod
    def managed_resources(show: dict[str, Any]) -> Iterator[dict[str, Any]]:
        """Every managed resource in `terraform show -json`, root and child modules."""

        def walk(module: dict[str, Any]) -> Iterator[dict[str, Any]]:
            for item in module.get("resources", []):
                if item.get("mode") == "managed":
                    yield item
            for child in module.get("child_modules", []):
                yield from walk(child)

        root = show.get("values", {}).get("root_module", {})
        yield from walk(root)

    @staticmethod
    def tag_list(tags: list[dict[str, str]] | None) -> dict[str, str]:
        return {item["Key"]: item["Value"] for item in tags or []}

    # -- IAC-AC07: the lock test, in three phases (plan section 7 item 5) --

    @staticmethod
    def evidence_file(layer: str) -> Path:
        return EVIDENCE_DIR / f"{layer}-state-version-before-apply.txt"

    def lock_before_apply(self, layer: str) -> str:
        """Step 1: record the state object's version (or "absent") before the Owner's apply."""
        assert not self.object_exists(f"{state_key(layer)}.tflock"), (
            f"{layer}: a lock object exists before the apply; another run holds the lock"
        )
        version = self.object_version(state_key(layer))
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        Dev01.evidence_file(layer).write_text(version + "\n", encoding="utf-8")
        return version

    @staticmethod
    def recorded_version(layer: str) -> str:
        path = Dev01.evidence_file(layer)
        if not path.is_file():
            pytest.fail(f"{layer}: run the before_apply test first; {path} is missing")
        return path.read_text(encoding="utf-8").strip()

    def lock_held_during_apply(self, layer: str) -> None:
        """Step 3, first check: the lock object exists while the Owner waits at the prompt."""
        assert self.object_exists(f"{state_key(layer)}.tflock"), (
            f"{layer}: no {state_key(layer)}.tflock while the apply waits at its prompt"
        )

    def second_plan_stops_during_apply(self, layer: str, var_file: str | None) -> str:
        """Step 3: a second plan stops with a lock error and changes no state."""
        before = self.recorded_version(layer)
        version_now = self.object_version(state_key(layer))
        assert version_now == before, (
            f"{layer}: state changed before the second run ({before} -> {version_now})"
        )
        args = ["plan", "-input=false", "-lock-timeout=0s", "-no-color"]
        if var_file:
            args.append(f"-var-file={var_file}")

        result = self.terraform(layer, *args)
        output = result.stdout + result.stderr

        assert result.returncode != 0, (
            f"{layer}: the second plan ran while the lock was held:\n{output}"
        )
        assert "Error acquiring the state lock" in output, output
        assert "Plan:" not in result.stdout and "No changes." not in result.stdout, (
            f"{layer}: the second plan got past the lock:\n{output}"
        )
        assert self.object_version(state_key(layer)) == before, f"{layer}: the state object changed"
        assert self.object_exists(f"{state_key(layer)}.tflock"), (
            f"{layer}: the first run lost its lock"
        )
        return output

    def lock_released_after_apply(self, layer: str, var_file: str | None) -> None:
        """Step 5: the lock object is gone; a new plan succeeds, no change, no force-unlock."""
        lock_key = f"{state_key(layer)}.tflock"
        deadline = time.monotonic() + LOCK_RELEASE_TIMEOUT_SECONDS
        while self.object_exists(lock_key):
            if time.monotonic() > deadline:
                pytest.fail(
                    f"{layer}: {lock_key} still exists {LOCK_RELEASE_TIMEOUT_SECONDS}s later"
                )
            time.sleep(10)
        assert self.object_version(state_key(layer)) != "absent", (
            f"{layer}: no state after the apply"
        )
        args = ["plan", "-input=false", "-detailed-exitcode", "-no-color"]
        if var_file:
            args.append(f"-var-file={var_file}")

        result = self.terraform(layer, *args)

        assert result.returncode == 0, (
            f"{layer}: plan after the apply exit {result.returncode} (0 = no changes):\n"
            f"{result.stdout[-3000:]}{result.stderr[-3000:]}"
        )
        assert not self.object_exists(lock_key), f"{layer}: the new plan left its lock behind"


@pytest.fixture(scope="session")
def dev01() -> Dev01:
    """Fails (never skips) when the shell is not the Owner's dev01 shell."""
    if os.environ.get("AWS_PROFILE") != PROFILE:
        pytest.fail(f"set AWS_PROFILE={PROFILE} (got {os.environ.get('AWS_PROFILE')!r})")
    if os.environ.get("AWS_REGION") != REGION:
        pytest.fail(f"set AWS_REGION={REGION} (got {os.environ.get('AWS_REGION')!r})")
    for tool in ("aws", "terraform"):
        if shutil.which(tool) is None:
            pytest.fail(f"`{tool}` is not on PATH")
    return Dev01()
