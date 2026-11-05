"""Terraform layout of the layers and modules, read as text (QA, US01b T0).

Criterion tests, static part, for IAC-AC03, IAC-AC04, IAC-AC07, IAC-AC14,
NET-AC01 and NET-AC02 (docs/specs/spec-001.md "IAC" and "NET";
docs/plans/US01b.plan.md section 4, "At merge" column, and section 7 items 6
and 7). The dev01 parts are in tests/dev01/test_us01b_singleton.py and
tests/dev01/test_us01b_group.py. The static part of IAC-AC08 is in
test_bootstrap.py.

Also enabler checks of the designs the plan fixes for later stories (section
6): version pins and lock files (US01b-D4), state keys (US01b-D3), module calls
and their arguments, outputs, the network design (US01b-D6 to US01b-D8), ECR
(US01b-D9) and the hosted zone (US01b-D10). They are named by decision or task
ID, never by a criterion ID.

The criterion checks are written for every root under awsenv/dev/ and every
module under modules/, so they keep holding when US01c and later stories add
the env root and new modules (backlog, "Also checked in").

Standard library and pytest only; the repository root is parents[2] (plan 7.7).
Files are read as text with regular expressions, no HCL parser. `.terraform/`
directories (created by `terraform init`) are skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AWSENV = REPO_ROOT / "awsenv"
LAYERS_DIR = AWSENV / "dev"
MODULES = REPO_ROOT / "modules"
TEMPLATE = MODULES / "README_TEMPLATE.md"

STATE_BUCKET = "cms-terraform-state-store"
REGION = "ap-southeast-1"

# US01b-D2, plan T1 and section 7 item 6: the nine headings, in this order.
TEMPLATE_HEADINGS = [
    "## Purpose",
    "## Layer and callers",
    "## Resources",
    "## Inputs",
    "## Outputs",
    "## Example",
    "## Security",
    "## Cost",
    "## Teardown",
]

# Plan section 5 and section 6 "Module names": the modules this story creates.
US01B_MODULES = ["container_registry", "dns_zone", "network"]
# Plan section 6: the roots this story creates. Env is US01c's.
US01B_LAYERS = ["singleton", "group"]
ROOT_FILES = [
    "versions.tf",
    "providers.tf",
    "backend.tf",
    "main.tf",
    "variables.tf",
    "outputs.tf",
    ".terraform.lock.hcl",
]
MODULE_FILES = ["main.tf", "variables.tf", "outputs.tf", "README.md"]

# IAC-AC03: a resource block, with a quoted or a bare first label.
RESOURCE_LINE_RE = re.compile(r"^\s*resource\s+[\"A-Za-z_]")


# ---------------------------------------------------------------------------
# Text helpers: HCL read with comments and string contents masked
# ---------------------------------------------------------------------------


def _blank(chars: list[str], start: int, end: int) -> None:
    for k in range(start, min(end, len(chars))):
        if chars[k] != "\n":
            chars[k] = " "


def mask_hcl(text: str) -> tuple[str, str]:
    """Two copies of text, same length and same line breaks.

    `clean` has comments blanked. `mask` also has the content of every string
    and heredoc blanked (the quotes of a string stay), so braces and keywords
    found in `mask` are real HCL structure. Values are read from `clean` at
    the same positions.
    """
    clean = list(text)
    mask = list(text)
    n = len(text)
    i = 0
    # Stack of open string (0) and template expression (1, with brace depth).
    stack: list[list[int]] = []
    heredoc_re = re.compile(r"<<-?([A-Za-z_][A-Za-z0-9_]*)[ \t]*\n")
    while i < n:
        c = text[i]
        if stack and stack[-1][0] == 0:  # inside a string
            if c == "\\":
                _blank(mask, i, i + 2)
                i += 2
                continue
            if c == '"':
                stack.pop()
                if stack:
                    _blank(mask, i, i + 1)
                i += 1
                continue
            if text.startswith("${", i) or text.startswith("%{", i):
                stack.append([1, 0])
                _blank(mask, i, i + 2)
                i += 2
                continue
            _blank(mask, i, i + 1)
            i += 1
            continue
        if stack:  # inside a template expression of a string
            _blank(mask, i, i + 1)
            if c == '"':
                stack.append([0, 0])
            elif c == "{":
                stack[-1][1] += 1
            elif c == "}":
                if stack[-1][1] == 0:
                    stack.pop()
                else:
                    stack[-1][1] -= 1
            i += 1
            continue
        if c == "#" or text.startswith("//", i):
            end = text.find("\n", i)
            end = n if end < 0 else end
            _blank(clean, i, end)
            _blank(mask, i, end)
            i = end
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = n if end < 0 else end + 2
            _blank(clean, i, end)
            _blank(mask, i, end)
            i = end
            continue
        if c == '"':
            stack.append([0, 0])
            i += 1
            continue
        heredoc = heredoc_re.match(text, i)
        if heredoc:
            marker = heredoc.group(1)
            end_re = re.compile(rf"^[ \t]*{re.escape(marker)}[ \t]*$", re.MULTILINE)
            found = end_re.search(text, heredoc.end())
            end = n if found is None else found.end()
            _blank(mask, heredoc.end(), found.start() if found else n)
            i = end
            continue
        i += 1
    return "".join(clean), "".join(mask)


@dataclass(frozen=True)
class Body:
    """A piece of HCL (a file or a block body): its clean and masked text."""

    clean: str
    mask: str

    @classmethod
    def parse(cls, text: str) -> Body:
        clean, mask = mask_hcl(text)
        return cls(clean, mask)

    def _depths(self) -> list[int]:
        depths: list[int] = []
        depth = 0
        for ch in self.mask:
            depths.append(depth)
            if ch in "{[(":
                depth += 1
            elif ch in "}])":
                depth -= 1
        return depths

    def _close(self, open_index: int) -> int:
        depth = 0
        for k in range(open_index, len(self.mask)):
            ch = self.mask[k]
            if ch in "{[(":
                depth += 1
            elif ch in "}])":
                depth -= 1
                if depth == 0:
                    return k
        raise AssertionError("unbalanced braces in HCL text")

    def blocks(self, keyword: str) -> list[tuple[list[str], Body]]:
        """Direct child blocks `keyword "label" ... {`: (labels, body)."""
        pattern = re.compile(
            rf"^[ \t]*{re.escape(keyword)}((?:[ \t]+(?:\"[^\"\n]*\"|[A-Za-z_][\w-]*))*)[ \t]*\{{",
            re.MULTILINE,
        )
        depths = self._depths()
        result: list[tuple[list[str], Body]] = []
        for match in pattern.finditer(self.mask):
            start = match.start() + len(match.group(0)) - len(match.group(0).lstrip())
            if depths[start] != 0:
                continue
            label_text = self.clean[match.start(1) : match.end(1)]
            labels = [
                quoted if quoted else bare
                for quoted, bare in re.findall(r"\"([^\"\n]*)\"|([A-Za-z_][\w-]*)", label_text)
            ]
            open_index = match.end() - 1
            close_index = self._close(open_index)
            result.append(
                (
                    labels,
                    Body(
                        self.clean[open_index + 1 : close_index],
                        self.mask[open_index + 1 : close_index],
                    ),
                )
            )
        return result

    def attribute(self, name: str) -> str | None:
        """Raw expression of a direct attribute `name = ...`, or None."""
        pattern = re.compile(rf"^[ \t]*{re.escape(name)}[ \t]*=(?!=)", re.MULTILINE)
        depths = self._depths()
        for match in pattern.finditer(self.mask):
            if depths[match.end() - 1] != 0:
                continue
            depth = 0
            k = match.end()
            while k < len(self.mask):
                ch = self.mask[k]
                if ch in "{[(":
                    depth += 1
                elif ch in "}])":
                    depth -= 1
                elif ch == "\n" and depth <= 0:
                    break
                k += 1
            return self.clean[match.end() : k].strip()
        return None

    def assignments(self) -> list[str]:
        """Names of the direct attributes, in order."""
        depths = self._depths()
        names: list[str] = []
        for match in re.finditer(r"^[ \t]*([A-Za-z_][\w-]*)[ \t]*=(?!=)", self.mask, re.MULTILINE):
            if depths[match.start(1)] == 0:
                names.append(match.group(1))
        return names

    def nested(self, name: str) -> list[Body]:
        """Direct child blocks `name {` and `dynamic "name" {`."""
        found = [block for _, block in self.blocks(name)]
        found += [block for labels, block in self.blocks("dynamic") if labels == [name]]
        return found

    def without(self, keyword: str) -> Body:
        """A copy with every `keyword ... { }` block blanked (any depth)."""
        clean = list(self.clean)
        mask = list(self.mask)
        pattern = re.compile(rf"(?<![\w-]){re.escape(keyword)}[ \t]*\{{")
        for match in pattern.finditer(self.mask):
            close_index = self._close(match.end() - 1)
            _blank(clean, match.start(), close_index + 1)
            _blank(mask, match.start(), close_index + 1)
        return Body("".join(clean), "".join(mask))


def string_value(expression: str | None) -> str | None:
    """The literal of a plain quoted string expression, else None."""
    if expression is None:
        return None
    match = re.fullmatch(r"\"([^\"\\$%]*)\"", expression.strip())
    return match.group(1) if match else None


def map_keys(expression: str) -> list[str] | None:
    """Keys of a literal map expression `{ k = v, ... }`, or None if not a literal map."""
    expression = expression.strip()
    if not expression.startswith("{") or not expression.endswith("}"):
        return None
    inner = Body.parse(expression[1:-1])
    keys: list[str] = []
    depths = inner._depths()
    for match in re.finditer(
        r"(?:^|,)[ \t]*(\"[^\"\n]*\"|[A-Za-z_][\w-]*)[ \t]*[=:](?!=)", inner.mask, re.MULTILINE
    ):
        if depths[match.start(1)] != 0:
            continue
        raw = inner.clean[match.start(1) : match.end(1)]
        keys.append(raw.strip('"'))
    return keys


def tf_files(base: Path) -> list[Path]:
    if not base.is_dir():
        return []
    return sorted(
        path for path in base.rglob("*.tf") if ".terraform" not in path.relative_to(base).parts
    )


def read_body(path: Path) -> Body:
    return Body.parse(path.read_text(encoding="utf-8"))


def dir_body(directory: Path) -> Body:
    """All `*.tf` files directly in a directory, as one body."""
    assert directory.is_dir(), f"{directory.relative_to(REPO_ROOT)} is missing"
    files = sorted(directory.glob("*.tf"))
    assert files, f"{directory.relative_to(REPO_ROOT)} has no .tf file"
    return Body.parse("\n".join(path.read_text(encoding="utf-8") for path in files))


def resources(body: Body, resource_type: str | None = None) -> dict[str, Body]:
    """`type.name` -> body of each resource block."""
    found: dict[str, Body] = {}
    for labels, block in body.blocks("resource"):
        assert len(labels) == 2, f"resource block with labels {labels}"
        if resource_type is None or labels[0] == resource_type:
            found[f"{labels[0]}.{labels[1]}"] = block
    return found


def resource(body: Body, address: str) -> Body:
    found = resources(body)
    assert address in found, f"resource {address} is missing; found {sorted(found)}"
    return found[address]


def module_dirs() -> list[str]:
    """Every child module directory, plus the ones this story must create."""
    names = set(US01B_MODULES)
    if MODULES.is_dir():
        names.update(
            path.name
            for path in MODULES.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        )
    return sorted(names)


def layer_dirs() -> list[str]:
    """Every root under awsenv/dev/, plus the ones this story must create."""
    names = set(US01B_LAYERS)
    if LAYERS_DIR.is_dir():
        names.update(
            path.name
            for path in LAYERS_DIR.iterdir()
            if path.is_dir() and not path.name.startswith(".") and any(path.glob("*.tf"))
        )
    return sorted(names)


def headings_missing(readme_text: str, headings: list[str]) -> list[str]:
    """Template headings that are not a whole line of the README (IAC-AC04)."""
    lines = {line.rstrip() for line in readme_text.splitlines()}
    return [heading for heading in headings if heading not in lines]


def resource_lines(text: str) -> list[str]:
    """Lines that open a resource block (IAC-AC03)."""
    return [line for line in text.splitlines() if RESOURCE_LINE_RE.match(line)]


def tags_violations(body: Body, where: str) -> list[str]:
    """Every `tags` argument that is not a literal map holding only `Name` (US01b-D5)."""
    problems: list[str] = []
    depths = body._depths()
    for match in re.finditer(r"^[ \t]*tags[ \t]*=(?!=)", body.mask, re.MULTILINE):
        line_start = match.start() + len(match.group(0)) - len(match.group(0).lstrip())
        sub = Body(body.clean[line_start:], body.mask[line_start:])
        value = sub.attribute("tags")
        assert value is not None
        keys = map_keys(value)
        if keys is None or keys != ["Name"]:
            line = body.clean.count("\n", 0, match.start()) + 1
            problems.append(f"{where}: tags at line {line} (depth {depths[line_start]}): {value}")
    return problems


# ---------------------------------------------------------------------------
# Self-checks of the helpers (they pass without the Terraform code)
# ---------------------------------------------------------------------------


def test_iac_ac03_detector_finds_resource_blocks() -> None:
    text = (
        'module "a" {}\nresource "aws_vpc" "this" {}\n'
        '  resource aws_eip nat {}\n# resource "x" "y"\n'
    )

    assert resource_lines(text) == ['resource "aws_vpc" "this" {}', "  resource aws_eip nat {}"]


def test_iac_ac04_detector_flags_missing_heading() -> None:
    readme = "# network\n\n## Purpose\n## Resources\n### Inputs\n## Cost extra\n"

    missing = headings_missing(readme, TEMPLATE_HEADINGS)

    assert "## Purpose" not in missing
    assert "## Inputs" in missing, "a ### heading is not the template's ## heading"
    assert "## Cost" in missing, "a heading must be a whole line"


def test_iac_ac14_detector_flags_tags_other_than_name() -> None:
    text = (
        'resource "aws_vpc" "this" {\n  tags = { Name = "cms-vpc" }\n}\n'
        'resource "aws_subnet" "a" {\n  tags = {\n    Name    = "cms-${var.x}"\n'
        '    Project = "cms"\n  }\n}\n'
        'resource "aws_eip" "b" {\n  tags = merge(var.tags, { Name = "x" })\n}\n'
        '# tags = { Project = "cms" }\n'
    )

    problems = tags_violations(Body.parse(text), "sample")

    assert len(problems) == 2, problems
    assert "Project" in problems[0]
    assert "merge" in problems[1]


def test_net_ac02_parser_reads_nested_route_block() -> None:
    text = (
        'resource "aws_route_table" "isolated" {\n  vpc_id = aws_vpc.this.id\n'
        '  route {\n    cidr_block = "0.0.0.0/0"\n  }\n'
        '  tags = { Name = "cms-isolated-rt" }\n}\n'
    )

    table = resource(Body.parse(text), "aws_route_table.isolated")

    assert len(table.nested("route")) == 1
    assert table.attribute("vpc_id") == "aws_vpc.this.id"
    dynamic = Body.parse('resource "aws_route_table" "t" {\n  dynamic "route" {\n  }\n}\n')
    assert len(resource(dynamic, "aws_route_table.t").nested("route")) == 1


# ---------------------------------------------------------------------------
# IAC-AC03: no resource block in awsenv/, resources only through child modules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("layer", US01B_LAYERS)
@pytest.mark.parametrize("name", ROOT_FILES)
def test_us01b_t2_t3_root_file_exists(layer: str, name: str) -> None:
    """Root file layout of plan section 6 (versions, providers, backend, ..., lock file)."""
    path = LAYERS_DIR / layer / name
    assert path.is_file(), f"{path.relative_to(REPO_ROOT)} is missing"


def test_iac_ac03_no_resource_block_in_awsenv() -> None:
    files = tf_files(AWSENV)
    for layer in US01B_LAYERS:
        assert any(path.parent == LAYERS_DIR / layer for path in files), (
            f"awsenv/dev/{layer} has no .tf file"
        )

    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {line.strip()}"
        for path in files
        for line in resource_lines(path.read_text(encoding="utf-8"))
    ]

    assert offenders == [], f"resource blocks in awsenv/: {offenders}"


@pytest.mark.parametrize("layer", layer_dirs())
def test_iac_ac03_root_module_calls_point_to_child_modules(layer: str) -> None:
    body = dir_body(LAYERS_DIR / layer)
    calls = body.blocks("module")
    assert calls, f"awsenv/dev/{layer} calls no module"

    for labels, call in calls:
        source = string_value(call.attribute("source"))
        assert source is not None, f"module {labels} has no literal source"
        target = (LAYERS_DIR / layer / source).resolve()
        assert target.parent == MODULES.resolve(), f"module {labels}: {source} not in modules/"
        assert target.is_dir(), f"module {labels} source {source} does not exist"


@pytest.mark.parametrize(
    ("layer", "expected"),
    [("singleton", ["container_registry", "dns_zone"]), ("group", ["network"])],
)
def test_us01b_t2_t3_layer_calls_its_modules(layer: str, expected: list[str]) -> None:
    """Plan section 6 "Module names"; later stories may add more calls."""
    body = dir_body(LAYERS_DIR / layer)
    names = {labels[0] for labels, _ in body.blocks("module")}

    assert set(expected) <= names, f"awsenv/dev/{layer} lacks module calls {set(expected) - names}"


@pytest.mark.parametrize("layer", US01B_LAYERS)
def test_us01b_t2_t3_module_call_named_after_directory(layer: str) -> None:
    """AGENTS.md "Terraform" and plan section 6: a module call is named after its directory."""
    body = dir_body(LAYERS_DIR / layer)
    for labels, call in body.blocks("module"):
        source = string_value(call.attribute("source")) or ""

        assert labels == [Path(source).name], f"module call {labels} has source {source}"


# ---------------------------------------------------------------------------
# IAC-AC04: every module has a README with every template heading
# ---------------------------------------------------------------------------


def test_us01b_d2_template_has_exactly_the_nine_headings() -> None:
    assert TEMPLATE.is_file(), "modules/README_TEMPLATE.md is missing"
    lines = TEMPLATE.read_text(encoding="utf-8").splitlines()
    headings = [line.rstrip() for line in lines if line.startswith("## ")]

    assert headings == TEMPLATE_HEADINGS
    assert any(line.startswith("# ") for line in lines), "template has no H1 line"


@pytest.mark.parametrize("module", module_dirs())
def test_iac_ac04_module_has_readme(module: str) -> None:
    readme = MODULES / module / "README.md"

    assert readme.is_file(), f"modules/{module}/README.md is missing"


@pytest.mark.parametrize("module", module_dirs())
def test_iac_ac04_readme_has_every_template_heading(module: str) -> None:
    assert TEMPLATE.is_file(), "modules/README_TEMPLATE.md is missing"
    template_headings = [
        line.rstrip()
        for line in TEMPLATE.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    ]
    assert template_headings, "the template has no ## heading to compare"
    readme = MODULES / module / "README.md"
    assert readme.is_file(), f"modules/{module}/README.md is missing"

    missing = headings_missing(readme.read_text(encoding="utf-8"), template_headings)

    assert missing == [], f"modules/{module}/README.md lacks {missing}"


@pytest.mark.parametrize("module", US01B_MODULES)
@pytest.mark.parametrize("name", MODULE_FILES)
def test_us01b_t2_t3_module_file_exists(module: str, name: str) -> None:
    path = MODULES / module / name
    assert path.is_file(), f"{path.relative_to(REPO_ROOT)} is missing"


# ---------------------------------------------------------------------------
# IAC-AC07: S3 native lock file, no DynamoDB table (static part)
# ---------------------------------------------------------------------------


def backend_block(layer: str) -> Body:
    body = dir_body(LAYERS_DIR / layer)
    backends = [
        block
        for _, terraform in body.blocks("terraform")
        for labels, block in terraform.blocks("backend")
        if labels == ["s3"]
    ]
    assert len(backends) == 1, f"awsenv/dev/{layer}: expected one backend \"s3\" block"
    return backends[0]


@pytest.mark.parametrize("layer", layer_dirs())
def test_iac_ac07_backend_uses_s3_lock_file(layer: str) -> None:
    backend = backend_block(layer)

    assert backend.attribute("use_lockfile") == "true", f"{layer}: use_lockfile = true missing"


@pytest.mark.parametrize("layer", layer_dirs())
def test_iac_ac07_no_dynamodb_lock_table(layer: str) -> None:
    backend_block(layer)
    offenders = [
        str(path.relative_to(REPO_ROOT))
        for path in tf_files(LAYERS_DIR / layer)
        if re.search(r"\bdynamodb_table\b|\bdynamodb_endpoint\b", read_body(path).clean)
    ]

    assert offenders == [], f"DynamoDB locking configured in {offenders}"


@pytest.mark.parametrize("layer", layer_dirs())
def test_us01b_d3_backend_bucket_key_region(layer: str) -> None:
    """Plan section 6 "State bucket and keys" and T2 step 3 (no profile in the backend)."""
    backend = backend_block(layer)

    assert string_value(backend.attribute("bucket")) == STATE_BUCKET
    assert string_value(backend.attribute("key")) == f"{layer}/terraform.tfstate"
    assert string_value(backend.attribute("region")) == REGION
    assert backend.attribute("profile") is None, "the backend must name no profile"
    assert backend.attribute("workspace_key_prefix") is None, "the default workspace prefix is kept"


@pytest.mark.parametrize("layer", US01B_LAYERS)
def test_us01b_t2_backend_encrypts_state(layer: str) -> None:
    """Plan T2 step 3: encrypt = true."""
    assert backend_block(layer).attribute("encrypt") == "true"


# ---------------------------------------------------------------------------
# IAC-AC14: one common project tag through provider default_tags
# ---------------------------------------------------------------------------


def aws_providers(layer: str) -> list[Body]:
    body = dir_body(LAYERS_DIR / layer)
    providers = [block for labels, block in body.blocks("provider") if labels == ["aws"]]
    assert providers, f"awsenv/dev/{layer} declares no provider \"aws\""
    return providers


def default_tags(provider: Body) -> dict[str, str | None]:
    blocks = provider.blocks("default_tags")
    assert len(blocks) == 1, "provider \"aws\" has no default_tags block"
    tags = blocks[0][1].attribute("tags")
    assert tags is not None, "default_tags has no tags map"
    inner = Body.parse(tags.strip()[1:-1])
    return {key: string_value(inner.attribute(key)) for key in map_keys(tags) or []}


@pytest.mark.parametrize("layer", layer_dirs())
def test_iac_ac14_every_aws_provider_has_project_default_tag(layer: str) -> None:
    """Every provider "aws" block of the root, including any alias, carries the tag (D-DL9)."""
    for provider in aws_providers(layer):
        tags = default_tags(provider)

        assert tags.get("Project") == "cms", f"{layer}: Project = \"cms\" missing in {tags}"
        assert tags.get("ManagedBy") == "terraform", f"{layer}: ManagedBy = \"terraform\" missing"


@pytest.mark.parametrize("module", module_dirs())
def test_iac_ac14_module_tags_hold_only_name(module: str) -> None:
    """Common tags only from default_tags; resource tags only for Name (US01b-D5)."""
    files = tf_files(MODULES / module)
    assert files, f"modules/{module} has no .tf file"

    problems = [
        problem
        for path in files
        for problem in tags_violations(read_body(path), str(path.relative_to(REPO_ROOT)))
    ]

    assert problems == [], problems


@pytest.mark.parametrize("layer", layer_dirs())
def test_iac_ac14_roots_set_tags_only_in_default_tags(layer: str) -> None:
    """No module call or other block in a root passes a tags map (D-DL9)."""
    problems: list[str] = []
    files = tf_files(LAYERS_DIR / layer)
    assert files, f"awsenv/dev/{layer} has no .tf file"
    for path in files:
        body = read_body(path).without("default_tags")
        for match in re.finditer(r"^[ \t]*tags[ \t]*=(?!=)", body.mask, re.MULTILINE):
            end = body.clean.find("\n", match.start())
            line = body.clean[match.start() : end if end >= 0 else None]
            problems.append(f"{path.relative_to(REPO_ROOT)}: {line.strip()}")

    assert problems == [], f"tags set outside default_tags: {problems}"


@pytest.mark.parametrize("layer", US01B_LAYERS)
def test_us01b_t2_provider_region_without_profile_or_alias(layer: str) -> None:
    """Plan T2 step 2: one provider, region ap-southeast-1, no profile, no alias (US01c adds it)."""
    providers = aws_providers(layer)

    assert len(providers) == 1, f"{layer}: exactly one provider \"aws\" expected"
    assert string_value(providers[0].attribute("region")) == REGION
    assert providers[0].attribute("profile") is None, "the provider must name no profile"
    assert providers[0].attribute("alias") is None


# ---------------------------------------------------------------------------
# US01b-D4: version pins and committed lock files
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("layer", US01B_LAYERS)
def test_us01b_d4_version_pins(layer: str) -> None:
    path = LAYERS_DIR / layer / "versions.tf"
    assert path.is_file(), f"{path.relative_to(REPO_ROOT)} is missing"
    body = read_body(path)
    blocks = body.blocks("terraform")
    assert len(blocks) == 1, "versions.tf: one terraform block expected"
    terraform = blocks[0][1]

    assert string_value(terraform.attribute("required_version")) == "~> 1.16.4"
    providers = terraform.blocks("required_providers")
    assert len(providers) == 1, "required_providers block missing"
    aws = providers[0][1].attribute("aws")
    assert aws is not None, "required_providers has no aws entry"
    aws_body = Body.parse(aws.strip()[1:-1])
    assert string_value(aws_body.attribute("source")) == "hashicorp/aws"
    assert string_value(aws_body.attribute("version")) == "~> 6.71"


@pytest.mark.parametrize("layer", US01B_LAYERS)
def test_us01b_d4_lock_file_has_aws_provider_for_two_platforms(layer: str) -> None:
    """Lock file for darwin_arm64 and linux_amd64: at least two h1: hashes (plan T2 step 9)."""
    path = LAYERS_DIR / layer / ".terraform.lock.hcl"
    assert path.is_file(), f"{path.relative_to(REPO_ROOT)} is missing"
    body = read_body(path)
    entries = [
        block
        for labels, block in body.blocks("provider")
        if labels == ["registry.terraform.io/hashicorp/aws"]
    ]
    assert len(entries) == 1, "lock file has no registry.terraform.io/hashicorp/aws entry"
    version = string_value(entries[0].attribute("version")) or ""
    match = re.fullmatch(r"6\.(\d+)\.\d+", version)

    assert match and int(match.group(1)) >= 71, f"locked aws provider {version} not ~> 6.71"
    assert len(re.findall(r"\"h1:", entries[0].clean)) >= 2, "fewer than two h1: hashes"


# ---------------------------------------------------------------------------
# Singleton: module calls and outputs (plan T2, section 6)
# ---------------------------------------------------------------------------


def module_call(layer: str, name: str) -> Body:
    body = dir_body(LAYERS_DIR / layer)
    calls = [block for labels, block in body.blocks("module") if labels == [name]]
    assert len(calls) == 1, f"awsenv/dev/{layer}: module \"{name}\" call missing"
    return calls[0]


def outputs(directory: Path) -> dict[str, Body]:
    body = dir_body(directory)
    return {labels[0]: block for labels, block in body.blocks("output")}


def test_us01b_t2_singleton_module_arguments() -> None:
    registry = module_call("singleton", "container_registry")
    zone = module_call("singleton", "dns_zone")

    assert string_value(registry.attribute("repository_name")) == "cms-api"
    assert string_value(zone.attribute("zone_name")) == "cms.imaprof.ink"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("ecr_repository_name", "module.container_registry.repository_name"),
        ("ecr_repository_arn", "module.container_registry.repository_arn"),
        ("ecr_repository_url", "module.container_registry.repository_url"),
        ("hosted_zone_id", "module.dns_zone.zone_id"),
        ("hosted_zone_name", "module.dns_zone.zone_name"),
        ("hosted_zone_name_servers", "module.dns_zone.name_servers"),
    ],
)
def test_us01b_t2_singleton_output(name: str, value: str) -> None:
    found = outputs(LAYERS_DIR / "singleton")
    assert name in found, f"singleton output {name} is missing"

    assert found[name].attribute("value") == value
    assert string_value(found[name].attribute("description")), f"{name} has no description"


@pytest.mark.parametrize(
    ("module", "names"),
    [
        ("container_registry", ["repository_name", "repository_arn", "repository_url"]),
        ("dns_zone", ["zone_id", "zone_name", "name_servers"]),
        (
            "network",
            [
                "vpc_id",
                "vpc_cidr_block",
                "availability_zones",
                "public_subnet_ids",
                "private_subnet_ids",
                "isolated_subnet_ids",
                "nat_gateway_ids",
                "nat_public_ips",
            ],
        ),
    ],
)
def test_us01b_t2_t3_module_outputs(module: str, names: list[str]) -> None:
    found = outputs(MODULES / module)

    assert set(names) <= set(found), f"modules/{module} lacks outputs {set(names) - set(found)}"


# ---------------------------------------------------------------------------
# US01b-D9 and US01b-D10: ECR repository and hosted zone
# ---------------------------------------------------------------------------


def test_us01b_d9_ecr_repository_settings() -> None:
    repo = resource(dir_body(MODULES / "container_registry"), "aws_ecr_repository.this")

    assert repo.attribute("name") == "var.repository_name"
    assert string_value(repo.attribute("image_tag_mutability")) == "IMMUTABLE"
    assert repo.attribute("force_delete") == "true"
    scanning = repo.blocks("image_scanning_configuration")
    assert len(scanning) == 1 and scanning[0][1].attribute("scan_on_push") == "true"
    encryption = repo.blocks("encryption_configuration")
    assert len(encryption) == 1
    assert string_value(encryption[0][1].attribute("encryption_type")) == "AES256"


def test_us01b_d9_ecr_lifecycle_policy() -> None:
    body = dir_body(MODULES / "container_registry")
    policy = resource(body, "aws_ecr_lifecycle_policy.this")
    variables = {labels[0]: block for labels, block in body.blocks("variable")}

    assert "aws_ecr_repository.this" in (policy.attribute("repository") or "")
    assert "images_to_keep" in variables, "variable images_to_keep is missing"
    assert variables["images_to_keep"].attribute("type") == "number"
    assert variables["images_to_keep"].attribute("default") == "5"
    assert "var.images_to_keep" in body.clean, "the lifecycle policy must use var.images_to_keep"


def test_us01b_d10_hosted_zone_settings() -> None:
    zone = resource(dir_body(MODULES / "dns_zone"), "aws_route53_zone.this")

    assert zone.attribute("name") == "var.zone_name"
    assert zone.attribute("force_destroy") == "false"


# ---------------------------------------------------------------------------
# NET-AC01: two zones, three tiers in each (static part)
# ---------------------------------------------------------------------------

SUBNET_COUNT_VALUES = {"2", "length(var.availability_zones)"}


def network_body() -> Body:
    return dir_body(MODULES / "network")


def test_net_ac01_three_subnet_tiers() -> None:
    subnets = resources(network_body(), "aws_subnet")

    assert sorted(subnets) == [
        "aws_subnet.isolated",
        "aws_subnet.private",
        "aws_subnet.public",
    ]


@pytest.mark.parametrize("tier", ["public", "private", "isolated"])
def test_net_ac01_each_tier_has_one_subnet_per_zone(tier: str) -> None:
    subnet = resource(network_body(), f"aws_subnet.{tier}")

    assert subnet.attribute("count") in SUBNET_COUNT_VALUES, f"{tier}: count must be 2"
    zone = subnet.attribute("availability_zone") or ""
    assert "var.availability_zones" in zone and "count.index" in zone, (
        f"{tier}: availability_zone must come from var.availability_zones by count.index, "
        f"got {zone!r}"
    )


def test_net_ac01_group_calls_network_with_two_zones() -> None:
    network = module_call("group", "network")

    assert network.attribute("availability_zones") is not None
    zones = re.findall(r"\"([^\"]+)\"", network.attribute("availability_zones") or "")
    assert zones == ["ap-southeast-1a", "ap-southeast-1b"]


def test_net_ac01_network_requires_exactly_two_zones() -> None:
    body = network_body()
    variables = {labels[0]: block for labels, block in body.blocks("variable")}
    assert "availability_zones" in variables, "variable availability_zones is missing"

    validations = variables["availability_zones"].blocks("validation")
    validation = " ".join(block.clean for _, block in validations)
    assert re.search(r"length\(\s*var\.availability_zones\s*\)\s*==\s*2", validation), (
        "availability_zones must be validated to length exactly 2"
    )


def test_us01b_t3_group_module_arguments() -> None:
    network = module_call("group", "network")

    assert string_value(network.attribute("name_prefix")) == "cms"
    assert string_value(network.attribute("vpc_cidr")) == "10.20.0.0/16"
    assert network.attribute("nat_gateway_count") == "var.nat_gateway_count"


@pytest.mark.parametrize(
    "name",
    [
        "vpc_id",
        "vpc_cidr_block",
        "availability_zones",
        "public_subnet_ids",
        "private_subnet_ids",
        "isolated_subnet_ids",
        "nat_gateway_ids",
        "nat_public_ips",
    ],
)
def test_us01b_t3_group_output(name: str) -> None:
    found = outputs(LAYERS_DIR / "group")
    assert name in found, f"group output {name} is missing"

    assert found[name].attribute("value") == f"module.network.{name}"
    assert string_value(found[name].attribute("description")), f"{name} has no description"


# ---------------------------------------------------------------------------
# US01b-D7: NAT count from the profile file, routes as separate resources
# ---------------------------------------------------------------------------


def test_us01b_d7_group_nat_gateway_count_variable() -> None:
    body = dir_body(LAYERS_DIR / "group")
    variables = {labels[0]: block for labels, block in body.blocks("variable")}
    assert "nat_gateway_count" in variables, "variable nat_gateway_count is missing"
    variable = variables["nat_gateway_count"]

    assert variable.attribute("type") == "number"
    assert variable.attribute("default") is None, "nat_gateway_count must have no default"
    assert string_value(variable.attribute("description")), "description missing"
    assert variable.blocks("validation"), "nat_gateway_count needs a validation (1 or 2)"


@pytest.mark.parametrize(("profile", "count"), [("lean", "1"), ("full", "2")])
def test_us01b_d7_profile_file_sets_only_nat_count(profile: str, count: str) -> None:
    path = LAYERS_DIR / "group" / "tfvars" / f"{profile}.tfvars"
    assert path.is_file(), f"{path.relative_to(REPO_ROOT)} is missing"
    body = read_body(path)

    assert body.assignments() == ["nat_gateway_count"], "only nat_gateway_count in the file"
    assert body.attribute("nat_gateway_count") == count


def test_us01b_d7_nat_gateways_and_eips_follow_the_count() -> None:
    body = network_body()
    nat = resource(body, "aws_nat_gateway.this")
    eip = resource(body, "aws_eip.nat")

    assert nat.attribute("count") == "var.nat_gateway_count"
    assert eip.attribute("count") == "var.nat_gateway_count"
    assert "aws_subnet.public" in (nat.attribute("subnet_id") or "")
    assert string_value(eip.attribute("domain")) == "vpc"


def test_us01b_d7_no_inline_route_in_any_route_table() -> None:
    tables = resources(network_body(), "aws_route_table")
    assert tables, "modules/network has no aws_route_table"

    inline = [
        address
        for address, table in tables.items()
        if table.nested("route") or table.attribute("route") is not None
    ]
    assert inline == [], f"inline routes in {inline}"


def test_us01b_d7_public_and_private_default_routes() -> None:
    body = network_body()
    public = resource(body, "aws_route.public_internet")
    private = resource(body, "aws_route.private_nat")

    assert string_value(public.attribute("destination_cidr_block")) == "0.0.0.0/0"
    assert "aws_route_table.public" in (public.attribute("route_table_id") or "")
    assert "aws_internet_gateway.this" in (public.attribute("gateway_id") or "")
    assert string_value(private.attribute("destination_cidr_block")) == "0.0.0.0/0"
    assert "aws_route_table.private" in (private.attribute("route_table_id") or "")
    assert "aws_nat_gateway.this" in (private.attribute("nat_gateway_id") or "")


# ---------------------------------------------------------------------------
# NET-AC02: the isolated route table has no route (static part)
# ---------------------------------------------------------------------------


def test_net_ac02_isolated_route_table_has_no_route_block() -> None:
    table = resource(network_body(), "aws_route_table.isolated")

    assert table.nested("route") == [], "aws_route_table.isolated has a route block"
    assert table.attribute("route") is None, "aws_route_table.isolated sets route ="


def test_net_ac02_no_aws_route_refers_to_isolated_table() -> None:
    body = network_body()
    resource(body, "aws_route_table.isolated")

    offenders = [
        address
        for address, block in resources(body).items()
        if re.search(r"\baws_route_table\.isolated\b", block.clean)
        and not address.startswith("aws_route_table_association.")
    ]
    assert offenders == [], f"only the associations may refer to the isolated table: {offenders}"


def test_net_ac02_isolated_subnets_associated_with_isolated_table() -> None:
    association = resource(network_body(), "aws_route_table_association.isolated")

    assert association.attribute("count") in SUBNET_COUNT_VALUES
    assert "aws_subnet.isolated" in (association.attribute("subnet_id") or "")
    assert "aws_route_table.isolated" in (association.attribute("route_table_id") or "")


# ---------------------------------------------------------------------------
# US01b-D8: network hardening
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tier", ["public", "private", "isolated"])
def test_us01b_d8_no_public_ip_on_launch(tier: str) -> None:
    subnet = resource(network_body(), f"aws_subnet.{tier}")

    assert subnet.attribute("map_public_ip_on_launch") == "false", f"{tier}: must be false"


def test_us01b_d8_default_security_group_closed() -> None:
    group = resource(network_body(), "aws_default_security_group.this")

    assert group.nested("ingress") == [], "the default security group has an ingress rule"
    assert group.attribute("ingress") in (None, "[]")
    assert group.nested("egress") == [], "the default security group has an egress rule"
    assert group.attribute("egress") in (None, "[]")


def test_us01b_d8_vpc_dns_settings() -> None:
    vpc = resource(network_body(), "aws_vpc.this")

    assert vpc.attribute("cidr_block") == "var.vpc_cidr"
    assert vpc.attribute("enable_dns_support") == "true"
    assert vpc.attribute("enable_dns_hostnames") == "true"
