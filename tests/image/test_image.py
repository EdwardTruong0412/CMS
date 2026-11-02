"""Checks of the built API image (QA, US01a T0; folder tests/image, US01a-D4).

Criterion tests for CNT-AC01 (the image is based on python:3.13-slim) and
CNT-AC02 (the image runs as a non-root user), built-image part
(docs/specs/spec-001.md "CNT: Container image"; docs/plans/US01a.plan.md
section 7.7). The Dockerfile text is checked in tests/infra/.

Not part of `make check`. Run by QA in the test round, after `make check`:

    cd <worktree>/src/api && .venv/bin/pytest ../../tests/image

Order: `docker pull python:3.13-slim`, then `docker build` from the repository
root, then the checks, then `docker image rm` of the test tag in the fixture
teardown. When Docker is not running, these tests fail; they never skip.
"""

from __future__ import annotations

import json
import subprocess
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_IMAGE = "python:3.13-slim"
EXPECTED_USER = "10001:10001"
EXPECTED_UID = "10001"


@dataclass
class BuiltImage:
    tag: str | None
    error: str | None

    def require(self) -> str:
        """The tag, or fail the test (never skip) with the reason the build failed."""
        if self.tag is None:
            pytest.fail(f"API image not available: {self.error}")
        return self.tag


def docker(*args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603  # fixed docker arguments, no shell
        ["docker", *args],  # noqa: S607  # docker is resolved from PATH on purpose
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _describe(result: subprocess.CompletedProcess[str]) -> str:
    return f"exit {result.returncode}: {(result.stderr or result.stdout).strip()[-2000:]}"


@pytest.fixture(scope="module")
def built_image() -> Iterator[BuiltImage]:
    tag = f"cms-api-qa-us01a:{uuid.uuid4().hex[:12]}"
    build_started = False
    try:
        try:
            pulled = docker("pull", BASE_IMAGE, timeout=900)
        except FileNotFoundError:
            yield BuiltImage(None, "the docker command is not installed (Docker down?)")
            return
        except subprocess.TimeoutExpired:
            yield BuiltImage(None, f"docker pull {BASE_IMAGE} timed out")
            return
        if pulled.returncode != 0:
            yield BuiltImage(None, f"docker pull {BASE_IMAGE} failed, {_describe(pulled)}")
            return

        build_started = True
        try:
            result = docker(
                "build", "-t", tag, "-f", "src/api/Dockerfile", "src/api", timeout=1800
            )
        except subprocess.TimeoutExpired:
            yield BuiltImage(None, "docker build timed out")
            return
        if result.returncode != 0:
            yield BuiltImage(None, f"docker build failed, {_describe(result)}")
            return
        yield BuiltImage(tag, None)
    finally:
        if build_started:
            # No test image is left behind (plan 7.7).
            docker("image", "rm", "--force", tag)


def inspect(image: str, template: str) -> str:
    result = docker("image", "inspect", "--format", template, image)
    assert result.returncode == 0, f"docker image inspect {image} failed, {_describe(result)}"
    return result.stdout.strip()


# ---------------------------------------------------------------------------
# CNT-AC01: the built image is based on python:3.13-slim
# ---------------------------------------------------------------------------


def test_cnt_ac01_image_layers_start_with_python_313_slim(built_image: BuiltImage) -> None:
    """The base image's root layers are a prefix of the built image's layers."""
    tag = built_image.require()
    base_layers = json.loads(inspect(BASE_IMAGE, "{{json .RootFS.Layers}}"))
    image_layers = json.loads(inspect(tag, "{{json .RootFS.Layers}}"))

    assert base_layers, f"{BASE_IMAGE} reports no layers"
    assert len(image_layers) > len(base_layers), "the image adds no layer on top of its base"
    assert image_layers[: len(base_layers)] == base_layers, (
        f"the image's layers do not start with the layers of {BASE_IMAGE}"
    )


# ---------------------------------------------------------------------------
# CNT-AC02: the built image runs as a non-root user
# ---------------------------------------------------------------------------


def test_cnt_ac02_image_config_user_is_10001(built_image: BuiltImage) -> None:
    tag = built_image.require()
    user = inspect(tag, "{{.Config.User}}")

    assert user, "the image has no configured user, so it runs as root"
    assert user.split(":")[0] not in {"root", "0"}, f"the image user is root: {user!r}"
    assert user == EXPECTED_USER


def test_cnt_ac02_container_runs_as_uid_10001(built_image: BuiltImage) -> None:
    tag = built_image.require()
    result = docker("run", "--rm", "--entrypoint", "id", tag, "-u", timeout=300)

    assert result.returncode == 0, f"docker run failed, {_describe(result)}"
    uid = result.stdout.strip()
    assert uid != "0", "the container runs as UID 0"
    assert uid == EXPECTED_UID
