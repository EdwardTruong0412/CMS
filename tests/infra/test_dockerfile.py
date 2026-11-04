"""API Dockerfile, read as text (QA, US01a T0).

Criterion tests for CNT-AC01 (multi-stage, final stage python:3.13-slim) and
CNT-AC02 (non-root user), static part (docs/specs/spec-001.md "CNT: Container
image"; docs/plans/US01a.plan.md T3 and section 4). The built-image part of both
criteria is in tests/image/. The ECS test point of CNT-AC02 belongs to US01c.

Also enabler checks for the plan's T3 boundaries (no secret ARG or ENV, no
HEALTHCHECK, the .dockerignore entries). They are not criterion tests: CNT-AC07
is delivered by US06.

Standard library and pytest only; the repository root is parents[2] (plan 7.2).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO_ROOT / "src" / "api" / "Dockerfile"
DOCKERIGNORE = REPO_ROOT / "src" / "api" / ".dockerignore"

FINAL_BASE_RE = re.compile(r"^python:3\.13-slim(?:\s+as\s+[A-Za-z0-9_.-]+)?$", re.IGNORECASE)
SECRET_NAME_RE = re.compile(
    r"PASSWORD|PASSWD|SECRET|TOKEN|PRIVATE_KEY|CREDENTIAL|API_?KEY|JWT|AWS_ACCESS|AWS_SESSION",
    re.IGNORECASE,
)


def parse_instructions(text: str) -> list[tuple[str, str]]:
    """Dockerfile instructions as (KEYWORD, arguments), continuations joined.

    Comment lines and blank lines are dropped, also inside a continued
    instruction, as Docker does.
    """
    instructions: list[tuple[str, str]] = []
    pending = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith("\\"):
            pending += stripped[:-1].strip() + " "
            continue
        logical = (pending + stripped).strip()
        pending = ""
        keyword, _, args = logical.partition(" ")
        instructions.append((keyword.upper(), args.strip()))
    if pending.strip():
        keyword, _, args = pending.strip().partition(" ")
        instructions.append((keyword.upper(), args.strip()))
    return instructions


@pytest.fixture(scope="module")
def instructions() -> list[tuple[str, str]]:
    assert DOCKERFILE.is_file(), f"{DOCKERFILE.relative_to(REPO_ROOT)} is missing"
    return parse_instructions(DOCKERFILE.read_text(encoding="utf-8"))


def final_stage(instructions: list[tuple[str, str]]) -> list[tuple[str, str]]:
    from_indexes = [i for i, (keyword, _) in enumerate(instructions) if keyword == "FROM"]
    assert from_indexes, "the Dockerfile has no FROM line"
    return instructions[from_indexes[-1] :]


def _strip_platform(from_args: str) -> str:
    return re.sub(r"^--platform=\S+\s+", "", from_args)


# ---------------------------------------------------------------------------
# CNT-AC01: multi-stage, final stage python:3.13-slim
# ---------------------------------------------------------------------------


def test_cnt_ac01_dockerfile_exists() -> None:
    assert DOCKERFILE.is_file(), "src/api/Dockerfile is missing"


def test_cnt_ac01_dockerfile_has_two_or_more_stages(
    instructions: list[tuple[str, str]],
) -> None:
    from_lines = [args for keyword, args in instructions if keyword == "FROM"]

    assert len(from_lines) >= 2, f"expected two or more FROM lines, found {from_lines}"


def test_cnt_ac01_final_stage_is_python_313_slim(instructions: list[tuple[str, str]]) -> None:
    last_from = _strip_platform(final_stage(instructions)[0][1])

    assert FINAL_BASE_RE.match(last_from), (
        f"the last FROM must name python:3.13-slim (tag, no digest), found {last_from!r}"
    )


# ---------------------------------------------------------------------------
# CNT-AC02: non-root user (static part)
# ---------------------------------------------------------------------------


def test_cnt_ac02_final_stage_sets_user(instructions: list[tuple[str, str]]) -> None:
    """Without a USER in the final stage the container runs as root."""
    users = [args for keyword, args in final_stage(instructions) if keyword == "USER"]

    assert users, "the final stage has no USER line, so it runs as root"


def test_cnt_ac02_last_user_is_10001_not_root(instructions: list[tuple[str, str]]) -> None:
    users = [args for keyword, args in final_stage(instructions) if keyword == "USER"]
    assert users, "the final stage has no USER line"
    last_user = users[-1]

    user_part = last_user.split(":")[0]
    assert user_part not in {"root", "0"}, f"the last USER is root: {last_user!r}"
    assert last_user == "10001:10001", f"the last USER must be 10001:10001, found {last_user!r}"


def test_cnt_ac02_no_user_change_after_last_user(instructions: list[tuple[str, str]]) -> None:
    """The last USER line of the whole file is 10001:10001 and sits in the final stage."""
    all_users = [
        (i, args) for i, (keyword, args) in enumerate(instructions) if keyword == "USER"
    ]
    assert all_users, "the Dockerfile has no USER line"
    from_indexes = [i for i, (keyword, _) in enumerate(instructions) if keyword == "FROM"]
    last_index, last_user = all_users[-1]

    assert last_index > from_indexes[-1], "the last USER line is not in the final stage"
    assert last_user == "10001:10001"


# ---------------------------------------------------------------------------
# Enablers: plan T3 boundaries (not criterion tests)
# ---------------------------------------------------------------------------


def test_us01a_t3_no_secret_in_arg_or_env(instructions: list[tuple[str, str]]) -> None:
    """No ARG or ENV names a password, key, token or AWS credential (plan T3)."""
    offenders = [
        f"{keyword} {args}"
        for keyword, args in instructions
        if keyword in {"ARG", "ENV"} and SECRET_NAME_RE.search(args)
    ]

    assert offenders == [], f"ARG or ENV holding a secret: {offenders}"


def test_us01a_t3_no_healthcheck(instructions: list[tuple[str, str]]) -> None:
    """The ALB checks /healthz, so the image has no HEALTHCHECK (plan T3, US01a-D15)."""
    assert all(keyword != "HEALTHCHECK" for keyword, _ in instructions)


def test_us01a_t3_final_stage_runtime_settings(instructions: list[tuple[str, str]]) -> None:
    """PYTHONDONTWRITEBYTECODE, PYTHONUNBUFFERED, port 8000 and an exec-form CMD."""
    stage = final_stage(instructions)
    env_text = " ".join(args for keyword, args in stage if keyword == "ENV")
    exposes = [args for keyword, args in stage if keyword == "EXPOSE"]
    cmds = [args for keyword, args in stage if keyword == "CMD"]

    assert re.search(r"PYTHONDONTWRITEBYTECODE=1\b", env_text)
    assert re.search(r"PYTHONUNBUFFERED=1\b", env_text)
    assert any("8000" in args.split() for args in exposes), f"EXPOSE 8000 missing: {exposes}"
    assert cmds, "the final stage has no CMD"
    assert cmds[-1].startswith("["), "CMD must be in exec form"
    for part in ('"uvicorn"', '"app.main:create_app"', '"--factory"', '"8000"'):
        assert part in cmds[-1], f"CMD lacks {part}: {cmds[-1]}"


@pytest.mark.parametrize(
    "entry",
    [
        ".env*",
        ".git",
        ".venv/",
        "__pycache__/",
        "*.pyc",
        ".mypy_cache/",
        ".ruff_cache/",
        ".pytest_cache/",
        "*.egg-info/",
        "build/",
        "tests/",
    ],
)
def test_us01a_t3_dockerignore_excludes(entry: str) -> None:
    """src/api/.dockerignore holds each entry the plan lists (plan T3)."""
    assert DOCKERIGNORE.is_file(), "src/api/.dockerignore is missing"
    lines = {
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    # A trailing slash is optional in .dockerignore patterns.
    accepted = {entry, entry.rstrip("/")}

    assert lines & accepted, f".dockerignore lacks {entry!r}"
