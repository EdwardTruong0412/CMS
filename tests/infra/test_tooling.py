"""Repository tooling, read as text (QA, US01a T0).

Enabler tests, not criterion tests: `make bootstrap`, `make deps` and
`make check` (decision US01a-D2), tflint run with HOME inside the repository
(US01a-D3, PROC12-D2) and the Terraform pin (SP1-D5). Source:
docs/plans/US01a.plan.md T1. Only the behaviour the plan fixes is checked;
wording, comments and variable names other than the ones the plan names are free.

Standard library and pytest only; the repository root is parents[2] (plan 7.2).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = REPO_ROOT / "Makefile"
TERRAFORM_VERSION = REPO_ROOT / ".terraform-version"
TFLINT_HCL = REPO_ROOT / ".tflint.hcl"

RULE_RE = re.compile(
    r"^(?P<targets>[A-Za-z0-9_.-]+(?:[ \t]+[A-Za-z0-9_.-]+)*)[ \t]*:(?![=:])(?P<rest>.*)$"
)
INSTALL_RE = re.compile(
    r"(?:\bpip3?\s+install|-m\s+pip\b|\bnpm\s+(?:ci|install|i)\b|\bbrew\s|\btfenv\s+install|-m\s+venv\b)"
)


def makefile_text() -> str:
    assert MAKEFILE.is_file(), "Makefile is missing"
    text = MAKEFILE.read_text(encoding="utf-8")
    # Join backslash continuations so a recipe line is one logical line.
    return re.sub(r"\\\n[ \t]*", " ", text)


def rules() -> dict[str, tuple[str, list[str]]]:
    """Target -> (prerequisites, recipe lines). Special targets (.PHONY) skipped."""
    result: dict[str, tuple[str, list[str]]] = {}
    current: list[str] = []
    for line in makefile_text().splitlines():
        if line.startswith("\t"):
            for target in current:
                result[target][1].append(line.strip())
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = RULE_RE.match(line)
        if match is None:
            current = []
            continue
        targets = [t for t in match.group("targets").split() if not t.startswith(".")]
        prereqs = match.group("rest").split("#")[0].split(";")[0].strip()
        current = targets
        for target in targets:
            result[target] = (prereqs, [])
    return result


def rule(target: str) -> tuple[str, list[str]]:
    all_rules = rules()
    assert target in all_rules, f"Makefile has no `{target}` target"
    return all_rules[target]


def assert_in_order(text: str, items: list[str]) -> None:
    """Each item appears in text after the previous one."""
    position = 0
    for item in items:
        found = text.find(item, position)
        assert found >= 0, f"`{item}` missing, or out of order, in:\n{text}"
        position = found + len(item)


# ---------------------------------------------------------------------------
# US01a-D2: bootstrap, deps and check
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target", ["bootstrap", "deps", "check", "check-api", "check-web", "check-terraform"]
)
def test_us01a_d2_makefile_has_target(target: str) -> None:
    rule(target)


def test_us01a_d2_check_is_default_goal() -> None:
    assert re.search(r"^\.DEFAULT_GOAL\s*:?=\s*check\s*$", makefile_text(), re.MULTILINE)


def test_us01a_d2_no_parallel_and_stop_on_failure() -> None:
    """Steps run in order and the first failure stops the run (.NOTPARALLEL, pipefail)."""
    text = makefile_text()

    assert re.search(r"^\.NOTPARALLEL\s*:", text, re.MULTILINE), ".NOTPARALLEL: missing"
    assert re.search(r"^SHELL\s*:?=\s*/bin/bash\s*$", text, re.MULTILINE)
    flags = re.search(r"^\.SHELLFLAGS\s*:?=\s*(.+)$", text, re.MULTILINE)
    assert flags, ".SHELLFLAGS missing"
    for flag in ("-e", "-u", "pipefail", "-c"):
        assert flag in flags.group(1).replace("-eu", "-e -u"), f".SHELLFLAGS lacks {flag}"


def test_us01a_d2_check_runs_api_web_terraform_in_order() -> None:
    prereqs, recipe = rule("check")

    assert_in_order(prereqs + " " + " ".join(recipe), ["check-api", "check-web", "check-terraform"])


def test_us01a_d2_check_api_steps_in_order() -> None:
    _, recipe = rule("check-api")
    text = "\n".join(recipe)

    assert_in_order(text, ["ruff check .", "ruff format --check .", "mypy", "pytest"])
    assert "src/api/.venv is missing: run make deps" in text


def test_us01a_d2_check_web_steps_in_order() -> None:
    _, recipe = rule("check-web")
    text = "\n".join(recipe)

    assert_in_order(text, ["npm run lint", "npm run typecheck", "npm run build"])
    assert "src/web/node_modules is missing: run make deps" in text


def test_us01a_d2_check_terraform_steps_in_order() -> None:
    _, recipe = rule("check-terraform")
    text = "\n".join(recipe)

    assert_in_order(text, ["terraform fmt -check -recursive", "tflint --init", "tflint --recursive"])


@pytest.mark.parametrize("target", ["check", "check-api", "check-web", "check-terraform"])
def test_us01a_d2_check_never_installs(target: str) -> None:
    """`make check` installs nothing: no pip, npm ci or install, brew, tfenv or venv."""
    prereqs, recipe = rule(target)
    offenders = [line for line in recipe if INSTALL_RE.search(line)]

    assert offenders == [], f"`{target}` installs something: {offenders}"
    assert "deps" not in prereqs.split(), f"`{target}` depends on deps"
    assert "bootstrap" not in prereqs.split(), f"`{target}` depends on bootstrap"


def test_us01a_d2_deps_creates_venv_and_installs() -> None:
    _, recipe = rule("deps")
    text = "\n".join(recipe)

    assert_in_order(text, ["-m venv", "pip install", "npm ci"])
    assert re.search(r"pip install\b.*-e\s+\S*\[dev\]", text), "editable install with [dev] missing"
    assert re.search(r"^PYTHON\s*\?=\s*python3\.13\s*$", makefile_text(), re.MULTILINE)


def test_us01a_d2_bootstrap_installs_tools() -> None:
    _, recipe = rule("bootstrap")
    text = "\n".join(recipe)

    for tool in ("tfenv", "tflint", "trivy", "python@3.13"):
        assert re.search(rf"brew install\b[^\n]*\b{re.escape(tool)}", text), f"bootstrap lacks {tool}"
    assert re.search(r"brew install --cask\b[^\n]*\bdrawio", text), "bootstrap lacks drawio"
    assert "tfenv install" in text


# ---------------------------------------------------------------------------
# US01a-D3: tflint with HOME inside the repository, and its configuration
# ---------------------------------------------------------------------------


def test_us01a_d3_tflint_runs_with_home_in_repository() -> None:
    """HOME is changed only on the two tflint lines, to .cache/home (PROC12-D2)."""
    text = makefile_text()
    home = re.search(r"^TFLINT_HOME\s*:?=\s*(\S+)\s*$", text, re.MULTILINE)
    assert home, "TFLINT_HOME is not defined"
    assert home.group(1) == "$(CURDIR)/.cache/home"

    _, recipe = rule("check-terraform")
    tflint_lines = [line for line in recipe if re.search(r"\btflint\s+--", line)]
    assert len(tflint_lines) >= 2, f"expected tflint --init and --recursive lines: {recipe}"
    for line in tflint_lines:
        assert re.search(r"HOME=\"?\$\(TFLINT_HOME\)\"?", line), f"HOME not set: {line}"
        assert ".tflint.hcl" in line or "$(TFLINT_CONFIG)" in line, f"--config missing: {line}"
    for line in recipe:
        if "terraform fmt" in line:
            assert "HOME=" not in line, "HOME must be changed only on the tflint lines"


def test_us01a_d3_tflint_config() -> None:
    assert TFLINT_HCL.is_file(), ".tflint.hcl is missing"
    text = TFLINT_HCL.read_text(encoding="utf-8")

    assert re.search(r'preset\s*=\s*"recommended"', text)
    aws = re.search(r'plugin\s+"aws"\s*\{(?P<body>[^}]*)\}', text)
    assert aws, 'plugin "aws" block missing'
    assert re.search(r'version\s*=\s*"0\.50\.0"', aws.group("body"))
    assert re.search(r'enabled\s*=\s*true', aws.group("body"))
    for name in (
        "terraform_naming_convention",
        "terraform_documented_variables",
        "terraform_documented_outputs",
        "terraform_standard_module_structure",
    ):
        block = re.search(rf'rule\s+"{name}"\s*\{{(?P<body>[^}}]*)\}}', text)
        assert block, f'rule "{name}" missing'
        assert re.search(r"enabled\s*=\s*true", block.group("body")), f"{name} not enabled"
    for name in ("terraform_required_version", "terraform_required_providers"):
        block = re.search(rf'rule\s+"{name}"\s*\{{(?P<body>[^}}]*)\}}', text)
        assert block, f'rule "{name}" missing'
        assert re.search(r"enabled\s*=\s*false", block.group("body")), f"{name} not disabled"


# ---------------------------------------------------------------------------
# SP1-D5: Terraform version pin
# ---------------------------------------------------------------------------


def test_sp1_d5_terraform_version_pinned() -> None:
    assert TERRAFORM_VERSION.is_file(), ".terraform-version is missing"

    assert TERRAFORM_VERSION.read_text(encoding="utf-8") == "1.16.4\n"
