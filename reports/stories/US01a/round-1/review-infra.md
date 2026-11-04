VERDICT: CHANGES

## Checks
Scope: the branch adds no Terraform layer or module (no `awsenv/`, `modules/`, no change under `.github/`). Infra-relevant files: `.terraform-version`, `.tflint.hcl`, `Makefile` (check-terraform), `src/api/Dockerfile`, `src/api/.dockerignore`.

- `terraform version`: pass (v1.16.4, matches `.terraform-version`)
- `terraform fmt -check -recursive` (repo root): pass (no .tf files)
- `terraform init` / `validate`: not applicable (no Terraform layer or module exists)
- `tflint --init` and `tflint --recursive --config .tflint.hcl` with `HOME=.cache/home`: pass (plugin tflint-ruleset-aws 0.50.0 installs; empty tree exit 0)
- `trivy config` (repo, HIGH/CRITICAL): pass, `src/api/Dockerfile` 0 findings. All severities: 1 LOW, DS-0026 (no HEALTHCHECK), intended by plan US01a-D15
- `terraform plan` (env, dev01): not applicable (no env layer)
- `docker build -t us01a-review src/api`: pass
- Image config: `Config.User` = `10001:10001`; `docker run --entrypoint id ... -u` prints `10001`; `Env` holds no secret (CNT-AC01, CNT-AC02, CNT-AC07 hold)
- Runtime smoke (`CMS_DB_PASSWORD=dummy`, no DB): `GET /healthz` 200 `{"status":"ok"}`; `GET /api/v1/status` 503 `SYSTEM_NOT_READY`. Without `CMS_DB_PASSWORD` the container exits at startup, as intended (required setting)
- `trivy image --scanners secret`: pass, no secrets
- `trivy image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1`: FAIL, 5 HIGH with a fixed version available (0 CRITICAL), see Finding 1

## Findings
1. src/api/Dockerfile:7-14 (runtime stage) The final image ships `pip` 26.2.2 from the base image, and Trivy reports 5 HIGH vulnerabilities with fixes, all in pip's vendored packages under `/usr/local/lib/python3.13/site-packages/pip/_vendor/`: msgpack 1.1.2 (CVE-2026-114613, GHSA-6v7p-g79w-8964), urllib3 2.7.0 (CVE-2026-97687, CVE-2026-97689), setuptools 70.3.0 recorded in pip's vendor bill of materials (CVE-2025-47273). Impact: the same scan gate CNT-AC05 sets for US05 and US06 (HIGH/CRITICAL with a fix fails the job) fails on this image today, and pip is not needed at runtime (the migration task runs Alembic, not pip). Fix: in the runtime stage, before `USER 10001:10001`, uninstall pip, for example by extending the existing `RUN groupadd ...` line with `&& python -m pip uninstall -y pip`. I checked this in the scratchpad: the same image with pip uninstalled passes the gate (`--ignore-unfixed --severity HIGH,CRITICAL --exit-code 1` gives exit 0), `/healthz` still returns 200, and the existing `tests/infra` and `tests/image` checks stay valid, because the RUN line comes before the last `USER`. Add a `tests/image` or `tests/infra` check for it only if QA wants one; that is QA's decision.

## Notes
- No `HEALTHCHECK` in the image (Trivy DS-0026 LOW) is a deliberate plan decision (US01a-D15, the ALB checks `/healthz`, CNT-AC03). Not a finding. When US05 adds the Trivy config gate, either keep it at HIGH/CRITICAL or add DS-0026 to the reviewed ignore file of IAC-AC11 with this reason.
- The base image is pinned by tag, not digest (KO-11); the Python deps are pinned exactly in `pyproject.toml`, and the build backend `setuptools==84.2.1` is used only in the builder stage. Fine.
- `.tflint.hcl` pins `tflint-ruleset-aws` 0.50.0 and enables the recommended preset plus `terraform_standard_module_structure` (US01a-D3). Since there is no .tf yet, the AWS ruleset is not exercised here; the first Terraform story (US05 or the first layer story) will be the real test.
- `make check-terraform` runs `tflint --init`, which needs network; this matches plan section 7. Trivy is installed by `bootstrap` but is not part of `make check`; that matches the plan (the scans come in the US05 workflows).
- No AWS resources, no cost impact, no teardown impact, no em dashes in resource names (none created).
- Local Trivy is 0.75.0 (0.76.1 available). Not blocking.
