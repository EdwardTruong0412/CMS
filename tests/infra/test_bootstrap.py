"""State bucket bootstrap script and runbook (QA, US01b T0).

Criterion tests for IAC-AC08, static part (docs/specs/spec-001.md "IAC";
docs/plans/US01b.plan.md T4, section 4 "At merge" column, section 7 item 4,
US01b-D11 and US01b-D15): the script and the runbook exist with the settings
of T4, the bucket is versioned, the 403 stop and the second-run branch work,
and no `.tf` file declares the state bucket. The dev01 part (the real bucket,
the layers' state) is in tests/dev01/.

The script is run with `bash`, from the repository root, with a fake `aws`
first on PATH (US01b-D15). The fake is written to a temporary directory, logs
every call (arguments and the AWS_PROFILE and AWS_REGION it sees) and answers
as the AWS CLI v2 would. No AWS access: AWS credentials and configuration are
removed from the environment and pointed at missing files, so even a script
that bypassed PATH could not reach an account.

Enabler checks of the T4 boundaries are named by decision ID (US01b-D11,
US01b-D14, US01b-D15).

Standard library and pytest only; the repository root is parents[2] (plan 7.7).
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "bootstrap_state_bucket.sh"
RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "bootstrap.md"

BUCKET = "cms-terraform-state-store"
REGION = "ap-southeast-1"
BUCKET_ARN = f"arn:aws:s3:::{BUCKET}"
# Mock account ID (the AWS documentation example), never a real account.
ACCOUNT_ID = "123456789012"

ALREADY_EXISTS_LINE = (
    f"Bucket {BUCKET} already exists in account {ACCOUNT_ID}; re-applying its settings."
)
READY_LINE = f"State bucket {BUCKET} is ready (versioning Enabled)."

# Plan T4 step 3: the six settings applied on every run.
SETTING_CALLS = [
    "put-public-access-block",
    "put-bucket-ownership-controls",
    "put-bucket-encryption",
    "put-bucket-versioning",
    "put-bucket-policy",
    "put-bucket-tagging",
]

FAKE_AWS = r'''#!{python}
"""Fake AWS CLI for tests/infra/test_bootstrap.py. Never contacts AWS."""
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
logged = []
for arg in args:
    if arg.startswith("file://"):
        path = Path(arg[len("file://"):])
        logged.append(path.read_text() if path.is_file() else arg)
    else:
        logged.append(arg)
with open(os.environ["FAKE_AWS_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({{
        "args": logged,
        "profile": os.environ.get("AWS_PROFILE"),
        "region": os.environ.get("AWS_REGION"),
    }}) + "\n")

services = {{"s3api", "sts", "s3"}}
service = next((a for a in args if a in services), "")
rest = args[args.index(service) + 1:] if service else []
operation = rest[0] if rest else ""
if operation == "wait" and len(rest) > 1:
    operation = "wait " + rest[1]

ACCOUNT = "{account}"
responses = {{
    "get-caller-identity": {{"UserId": "AIDAMOCKUSER", "Account": ACCOUNT,
                            "Arn": "arn:aws:iam::" + ACCOUNT + ":user/qa-mock"}},
    "create-bucket": {{"Location": "http://{bucket}.s3.amazonaws.com/"}},
    "get-bucket-versioning": {{"Status": "Enabled"}},
    "get-bucket-encryption": {{"ServerSideEncryptionConfiguration": {{"Rules": [
        {{"ApplyServerSideEncryptionByDefault": {{"SSEAlgorithm": "AES256"}},
         "BucketKeyEnabled": False}}]}}}},
    "get-public-access-block": {{"PublicAccessBlockConfiguration": {{
        "BlockPublicAcls": True, "IgnorePublicAcls": True,
        "BlockPublicPolicy": True, "RestrictPublicBuckets": True}}}},
    "get-bucket-ownership-controls": {{"OwnershipControls": {{"Rules": [
        {{"ObjectOwnership": "BucketOwnerEnforced"}}]}}}},
    "get-bucket-tagging": {{"TagSet": [{{"Key": "Project", "Value": "cms"}},
                                      {{"Key": "ManagedBy", "Value": "bootstrap-script"}}]}},
    "head-bucket": {{"BucketRegion": "{region}", "AccessPointAlias": False}},
}}

if operation == "head-bucket":
    mode = os.environ.get("FAKE_HEAD_BUCKET", "ok")
    if mode == "403":
        sys.stderr.write(
            "\nAn error occurred (403) when calling the HeadBucket operation: Forbidden\n"
        )
        sys.exit(254)
    if mode == "404":
        sys.stderr.write(
            "\nAn error occurred (404) when calling the HeadBucket operation: Not Found\n"
        )
        sys.exit(254)

response = responses.get(operation)
if response is None:
    sys.exit(0)


def option(name):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else None


def query(value, expression):
    for part in expression.strip("'\"").split("."):
        name, _, index = part.partition("[")
        if name:
            if not isinstance(value, dict) or name not in value:
                return None
            value = value[name]
        while index:
            number, _, index = index.partition("]")
            if not isinstance(value, list):
                return None
            value = value[int(number)]
            index = index.lstrip("[")
    return value


def text(value):
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, dict):
        return "\t".join(text(v) for v in value.values())
    if isinstance(value, list):
        return "\t".join(text(v) for v in value)
    return "None" if value is None else str(value)


expression = option("--query")
if expression:
    response = query(response, expression)
if option("--output") == "text":
    print(text(response))
else:
    print(json.dumps(response, indent=4))
'''


@dataclass
class Run:
    returncode: int
    stdout: str
    stderr: str
    calls: list[dict[str, object]]

    def operations(self) -> list[str]:
        return [operation(call) for call in self.calls]

    def calls_to(self, name: str) -> list[list[str]]:
        return [args(call) for call in self.calls if operation(call) == name]

    def output(self) -> str:
        return f"exit {self.returncode}\nstdout:\n{self.stdout}\nstderr:\n{self.stderr}"


def args(call: dict[str, object]) -> list[str]:
    value = call["args"]
    assert isinstance(value, list)
    return [str(item) for item in value]


def operation(call: dict[str, object]) -> str:
    items = args(call)
    service = next((a for a in items if a in {"s3api", "sts", "s3"}), "")
    rest = items[items.index(service) + 1 :] if service else []
    name = rest[0] if rest else ""
    if name == "wait" and len(rest) > 1:
        name = f"wait {rest[1]}"
    return name


def option_value(items: list[str], name: str) -> str | None:
    """Value of `--name value` or `--name=value`."""
    for index, item in enumerate(items):
        if item == name and index + 1 < len(items):
            return items[index + 1]
        if item.startswith(name + "="):
            return item[len(name) + 1 :]
    return None


def require_script() -> None:
    assert SCRIPT.is_file(), "scripts/bootstrap_state_bucket.sh is missing"
    text = SCRIPT.read_text(encoding="utf-8")
    # Safety before running: the script must reach `aws` only through PATH.
    assert not absolute_aws_calls(text), "the script calls aws by absolute path; not run"


def absolute_aws_calls(text: str) -> list[str]:
    return re.findall(r"(?:^|[\s;|&(`$\"'])(/[^\s\"']*/aws)(?=[\s\"';)]|$)", text, re.MULTILINE)


def run_script(
    tmp_path: Path,
    head_bucket: str = "ok",
    profile: str | None = None,
    region: str | None = None,
) -> Run:
    require_script()
    tmp_path.mkdir(parents=True, exist_ok=True)
    fake_bin = tmp_path / "fakebin"
    fake_bin.mkdir(exist_ok=True)
    fake = fake_bin / "aws"
    fake.write_text(
        FAKE_AWS.format(python=sys.executable, account=ACCOUNT_ID, bucket=BUCKET, region=REGION),
        encoding="utf-8",
    )
    fake.chmod(0o755)
    log = tmp_path / "aws-calls.jsonl"
    log.write_text("", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)

    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("AWS_") and key != "HOME"
    }
    env.update(
        {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
            "HOME": str(home),
            "FAKE_AWS_LOG": str(log),
            "FAKE_HEAD_BUCKET": head_bucket,
            "AWS_CONFIG_FILE": str(home / "missing-config"),
            "AWS_SHARED_CREDENTIALS_FILE": str(home / "missing-credentials"),
            "AWS_EC2_METADATA_DISABLED": "true",
        }
    )
    if profile is not None:
        env["AWS_PROFILE"] = profile
    if region is not None:
        env["AWS_REGION"] = region

    result = subprocess.run(  # noqa: S603  # fixed arguments, no shell
        ["bash", str(SCRIPT)],  # noqa: S607  # bash from PATH, as the shebang does
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
    return Run(result.returncode, result.stdout, result.stderr, calls)


def stdout_lines(run: Run) -> list[str]:
    return [line.rstrip() for line in run.stdout.splitlines() if line.strip()]


def joined(items: list[str]) -> str:
    return " ".join(items)


def flag_true(text: str, key: str) -> bool:
    return re.search(rf"{key}\"?\s*[=:]\s*\"?true\b", text, re.IGNORECASE) is not None


def parse_tags(text: str) -> dict[str, str]:
    """Tags from `--tagging` in JSON or in CLI shorthand."""
    try:
        data = json.loads(text)
    except ValueError:
        return dict(re.findall(r"Key=([^,}\]]+),Value=([^,}\]]+)", text))
    tag_set = data.get("TagSet", []) if isinstance(data, dict) else []
    return {str(tag.get("Key")): str(tag.get("Value")) for tag in tag_set}


def only_call(run: Run, name: str) -> list[str]:
    calls = run.calls_to(name)
    assert len(calls) == 1, f"expected one `{name}` call, got {len(calls)}\n{run.output()}"
    return calls[0]


# ---------------------------------------------------------------------------
# IAC-AC08: the script exists and runs as the plan fixes it
# ---------------------------------------------------------------------------


def test_iac_ac08_script_exists_and_is_executable() -> None:
    assert SCRIPT.is_file(), "scripts/bootstrap_state_bucket.sh is missing"
    mode = SCRIPT.stat().st_mode

    assert mode & stat.S_IXUSR, "the script is not executable (mode 755)"


def test_us01b_d11_script_header() -> None:
    """Plan T4 step 1: shebang, strict mode, fixed bucket and region, profile default 3tier."""
    assert SCRIPT.is_file(), "scripts/bootstrap_state_bucket.sh is missing"
    text = SCRIPT.read_text(encoding="utf-8")

    assert text.splitlines()[0] == "#!/usr/bin/env bash"
    assert re.search(r"^\s*set -euo pipefail\s*$", text, re.MULTILINE)
    assert re.search(rf"^\s*BUCKET=\"{BUCKET}\"\s*$", text, re.MULTILINE)
    assert re.search(rf"^\s*REGION=\"{REGION}\"\s*$", text, re.MULTILINE)


def test_us01b_d15_script_calls_aws_from_path() -> None:
    """The fake on PATH can only stand in for `aws` when the script never uses an absolute path."""
    assert SCRIPT.is_file(), "scripts/bootstrap_state_bucket.sh is missing"
    text = SCRIPT.read_text(encoding="utf-8")

    assert absolute_aws_calls(text) == [], "aws must be called from PATH, not by path"
    assert not re.search(r"^\s*alias\s+aws\b", text, re.MULTILINE), "aws must not be an alias"
    assert re.search(r"(?:^|[\s;|&(`$])aws\s+s3api\b", text, re.MULTILINE), "no `aws s3api` call"


def test_iac_ac08_first_run_creates_versioned_bucket(tmp_path: Path) -> None:
    """head-bucket answers (404): create, wait, then apply the settings, exit 0."""
    run = run_script(tmp_path, head_bucket="404")

    assert run.returncode == 0, run.output()
    create = only_call(run, "create-bucket")
    assert option_value(create, "--bucket") == BUCKET
    assert option_value(create, "--region") == REGION
    assert option_value(create, "--create-bucket-configuration") == f"LocationConstraint={REGION}"
    assert option_value(create, "--object-ownership") == "BucketOwnerEnforced"
    ops = run.operations()
    assert "wait bucket-exists" in ops, f"no `s3api wait bucket-exists`\n{run.output()}"
    assert ops.index("create-bucket") < ops.index("wait bucket-exists")
    for name in SETTING_CALLS:
        assert name in ops, f"`{name}` not called\n{run.output()}"
        assert ops.index("wait bucket-exists") < ops.index(name), f"`{name}` before the wait"
    versioning = joined(only_call(run, "put-bucket-versioning"))
    assert re.search(r"Status\"?\s*[=:]\s*\"?Enabled", versioning), versioning
    assert stdout_lines(run)[-1] == READY_LINE, run.output()


def test_iac_ac08_second_run_reapplies_settings_without_create(tmp_path: Path) -> None:
    """head-bucket succeeds: the "already exists" line, no create-bucket, six settings, exit 0."""
    run = run_script(tmp_path, head_bucket="ok")

    assert run.returncode == 0, run.output()
    assert ALREADY_EXISTS_LINE in stdout_lines(run), run.output()
    assert stdout_lines(run)[-1] == READY_LINE, run.output()
    assert run.calls_to("create-bucket") == [], "create-bucket called for an existing bucket"
    for name in SETTING_CALLS:
        only_call(run, name)


def test_iac_ac08_two_runs_make_the_same_calls(tmp_path: Path) -> None:
    """Idempotence: a run on an existing bucket repeats exactly the same calls."""
    first = run_script(tmp_path / "first", head_bucket="ok")
    second = run_script(tmp_path / "second", head_bucket="ok")

    assert first.returncode == 0 and second.returncode == 0, first.output() + second.output()
    assert [args(c) for c in first.calls] == [args(c) for c in second.calls]
    assert first.stdout == second.stdout


def test_iac_ac08_403_stops_without_any_change(tmp_path: Path) -> None:
    """head-bucket answers (403): print the error, exit 1, no create-bucket and no put-* call."""
    run = run_script(tmp_path, head_bucket="403")

    assert run.returncode == 1, run.output()
    changing = [op for op in run.operations() if op == "create-bucket" or op.startswith("put-")]
    assert changing == [], f"changes made after a 403: {changing}"
    assert "(403)" in run.stdout + run.stderr, "the head-bucket error is not printed"
    assert READY_LINE not in run.stdout


def test_us01b_d11_every_call_names_the_expected_owner(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok")
    assert run.returncode == 0, run.output()

    for name in ["head-bucket", *SETTING_CALLS]:
        call = only_call(run, name)
        assert option_value(call, "--bucket") == BUCKET, f"`{name}` on another bucket: {call}"
        assert option_value(call, "--expected-bucket-owner") == ACCOUNT_ID, (
            f"`{name}` lacks --expected-bucket-owner {ACCOUNT_ID}: {call}"
        )


def test_us01b_d11_account_from_caller_identity(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok")
    assert run.returncode == 0, run.output()

    identity = only_call(run, "get-caller-identity")
    assert option_value(identity, "--query") == "Account"
    assert option_value(identity, "--output") == "text"
    assert run.operations()[0] == "get-caller-identity"


def test_us01b_d11_public_access_block_all_true(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok")
    text = joined(only_call(run, "put-public-access-block"))

    keys = ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")
    for key in keys:
        assert flag_true(text, key), f"{key} is not true: {text}"


def test_us01b_d11_ownership_enforced(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok")
    text = joined(only_call(run, "put-bucket-ownership-controls"))

    assert "BucketOwnerEnforced" in text, text


def test_us01b_d11_encryption_sse_s3(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok")
    text = joined(only_call(run, "put-bucket-encryption"))

    assert "AES256" in text, text
    assert "aws:kms" not in text, text


def test_iac_ac08_versioning_enabled_on_every_run(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok")
    text = joined(only_call(run, "put-bucket-versioning"))

    assert re.search(r"Status\"?\s*[=:]\s*\"?Enabled", text), text
    assert "Suspended" not in text


def test_us01b_d11_tls_only_bucket_policy(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok")
    policy_text = option_value(only_call(run, "put-bucket-policy"), "--policy")
    assert policy_text is not None, "put-bucket-policy has no --policy"
    policy = json.loads(policy_text)
    statements = policy["Statement"]
    statements = statements if isinstance(statements, list) else [statements]

    assert len(statements) == 1, statements
    statement = statements[0]
    assert statement["Sid"] == "DenyInsecureTransport"
    assert statement["Effect"] == "Deny"
    assert statement["Principal"] in ("*", {"AWS": "*"})
    action = statement["Action"]
    actions = action if isinstance(action, list) else [action]
    assert actions == ["s3:*"]
    assert set(statement["Resource"]) == {BUCKET_ARN, f"{BUCKET_ARN}/*"}
    secure = statement["Condition"]["Bool"]["aws:SecureTransport"]
    assert str(secure).lower() == "false"


def test_us01b_d11_bucket_tags(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok")
    tagging = option_value(only_call(run, "put-bucket-tagging"), "--tagging")
    assert tagging is not None, "put-bucket-tagging has no --tagging"
    tags = parse_tags(tagging)

    assert tags.get("Project") == "cms", tags
    assert tags.get("ManagedBy") == "bootstrap-script", tags


def test_iac_ac08_script_reads_back_settings(tmp_path: Path) -> None:
    """Plan T4 step 4: versioning, encryption and public access block read back and printed."""
    run = run_script(tmp_path, head_bucket="ok")
    assert run.returncode == 0, run.output()
    ops = run.operations()

    for name in ("get-bucket-versioning", "get-bucket-encryption", "get-public-access-block"):
        assert name in ops, f"`{name}` not called"
        last_put = max(ops.index(put) for put in SETTING_CALLS)
        assert ops.index(name) > last_put, f"`{name}` before the settings"
    assert "Enabled" in run.stdout and "AES256" in run.stdout, run.output()


def test_us01b_d11_profile_defaults_to_3tier_region_fixed(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok", region="us-east-1")
    assert run.returncode == 0, run.output()

    assert {call["profile"] for call in run.calls} == {"3tier"}
    assert {call["region"] for call in run.calls} == {REGION}


def test_us01b_d11_profile_from_environment_is_honoured(tmp_path: Path) -> None:
    run = run_script(tmp_path, head_bucket="ok", profile="qa-mock-profile")
    assert run.returncode == 0, run.output()

    assert {call["profile"] for call in run.calls} == {"qa-mock-profile"}


def test_us01b_d11_script_never_deletes_or_suspends(tmp_path: Path) -> None:
    assert SCRIPT.is_file(), "scripts/bootstrap_state_bucket.sh is missing"
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = re.findall(r"\bdelete-[a-z-]+|\bs3\s+(?:rb|rm)\b|\bSuspended\b", text)
    assert forbidden == [], f"the script may delete or disable: {forbidden}"

    for mode in ("ok", "404", "403"):
        run = run_script(tmp_path / mode, head_bucket=mode)
        deleting = [op for op in run.operations() if op.startswith("delete-")]
        assert deleting == [], f"{mode}: delete calls {deleting}"


def test_us01b_d11_script_has_no_em_dash() -> None:
    assert SCRIPT.is_file(), "scripts/bootstrap_state_bucket.sh is missing"

    assert "—" not in SCRIPT.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# IAC-AC08: no layer declares the state bucket (static part)
# ---------------------------------------------------------------------------


def _close_brace(text: str, open_index: int) -> int:
    """Index of the brace closing text[open_index], skipping strings and comments."""
    depth = 0
    k = open_index
    in_string = False
    while k < len(text):
        ch = text[k]
        if in_string:
            if ch == "\\":
                k += 2
                continue
            if ch == '"':
                in_string = False
        elif ch == '"':
            in_string = True
        elif ch == "#" or text.startswith("//", k):
            newline = text.find("\n", k)
            k = len(text) if newline < 0 else newline
            continue
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return k
        k += 1
    raise AssertionError("unbalanced braces")


def bucket_declarations(text: str) -> list[str]:
    """aws_s3_bucket* resource blocks and import blocks that name the state bucket."""
    found: list[str] = []
    pattern = re.compile(
        r"^[ \t]*(resource[ \t]+\"?(aws_s3_bucket[a-z0-9_]*)\"?[ \t]+\"?[\w-]+\"?|import)[ \t]*\{",
        re.MULTILINE,
    )
    for match in pattern.finditer(text):
        body = text[match.end() - 1 : _close_brace(text, match.end() - 1) + 1]
        if BUCKET in body:
            found.append(match.group(1))
    return found


def test_iac_ac08_detector_finds_state_bucket_resource() -> None:
    text = (
        'resource "aws_s3_bucket" "state" {\n  bucket = "cms-terraform-state-store"\n}\n'
        'resource "aws_s3_bucket" "ui" {\n  bucket = "cms-dev01-ui"\n}\n'
        'import {\n  to = aws_s3_bucket_versioning.x\n  id = "cms-terraform-state-store"\n}\n'
    )

    assert bucket_declarations(text) == ['resource "aws_s3_bucket" "state"', "import"]


def test_iac_ac08_no_tf_declares_the_state_bucket() -> None:
    files = sorted(
        path
        for base in (REPO_ROOT / "awsenv", REPO_ROOT / "modules")
        if base.is_dir()
        for path in base.rglob("*.tf")
        if ".terraform" not in path.parts
    )
    backends = [path for path in files if path.name == "backend.tf"]
    assert len(backends) >= 2, "the singleton and group backend.tf files are missing"

    offenders = [
        f"{path.relative_to(REPO_ROOT)}: {declaration}"
        for path in files
        for declaration in bucket_declarations(path.read_text(encoding="utf-8"))
    ]
    assert offenders == [], f"the state bucket is declared in Terraform: {offenders}"


# ---------------------------------------------------------------------------
# IAC-AC08: the bootstrap procedure is documented (docs/runbooks/bootstrap.md)
# ---------------------------------------------------------------------------

RUNBOOK_SECTIONS = [
    "Purpose",
    "Prerequisites",
    "Step 1: state bucket",
    "Step 2: singleton apply",
    "Step 3: NS delegation at Namecheap",
    "Group layer in a check session",
    "Steps added by later stories",
    "What this procedure never does",
]


def runbook_text() -> str:
    assert RUNBOOK.is_file(), "docs/runbooks/bootstrap.md is missing"
    return RUNBOOK.read_text(encoding="utf-8")


def test_iac_ac08_runbook_documents_the_state_bucket_step() -> None:
    text = runbook_text()

    assert "./scripts/bootstrap_state_bucket.sh" in text
    assert BUCKET in text
    assert "3tier" in text
    assert READY_LINE in text, "the runbook shows the expected output"
    assert re.search(r"re-run", text, re.IGNORECASE), "the runbook says re-running is safe"


@pytest.mark.parametrize("section", RUNBOOK_SECTIONS)
def test_us01b_d14_runbook_has_section(section: str) -> None:
    headings = [line for line in runbook_text().splitlines() if line.startswith("#")]

    assert any(section.lower() in heading.lower() for heading in headings), (
        f"no heading for `{section}` in {headings}"
    )


def test_us01b_d14_runbook_singleton_and_ns_steps() -> None:
    text = runbook_text()

    for snippet in (
        "cd awsenv/dev/singleton",
        "terraform init",
        "terraform apply",
        "terraform output hosted_zone_name_servers",
        "dig +short NS cms.imaprof.ink @1.1.1.1",
        "@8.8.8.8",
        "imaprof.ink",
    ):
        assert snippet in text, f"runbook lacks `{snippet}`"


def test_us01b_d14_runbook_group_session_and_later_steps() -> None:
    text = runbook_text()

    assert "terraform apply -var-file=tfvars/lean.tfvars" in text
    assert "terraform destroy -var-file=tfvars/lean.tfvars" in text
    assert "docs/runbooks/session.md" in text
    for story in ("US05", "US02", "US03", "US01c", "US06", "US08", "US40"):
        assert story in text, f"runbook does not name {story}"
