STATUS: READY

Handoff: 2026-11-02 US01a - Dev 2, build round 2, fix round 1

Read all five round-1 files. Addressed every finding:

- Code #1: malformed non-2xx bodies now produce `ApiError(status, [])`. Valid error items are checked before use. Existing 503 and rejected-fetch behavior is preserved.
- Code #2: deleted `reports/handoff/US01a-dev2.md`. This handoff contains the complete commit proposals and no duplicate-report link.
- Infra #1: removed pip from the runtime image before switching to UID 10001.

Validation:

- `make check`: PASS, including 91 QA tests.
- Built-image tests: 3 passed.
- API-client smoke checks: passed for ten error payloads, 503, rejected fetch, 204 and 200.
- Trivy HIGH/CRITICAL scan with `--ignore-unfixed --exit-code 1`: PASS.
- Runtime smoke: pip absent, UID 10001, `/healthz` returns 200.
- `git diff --check`: PASS. `tests/` unchanged.

Proposed commits, one per affected task, covering all three changed files:

**T3** — `src/api/Dockerfile`

```text
infra(US01a): remove pip from the runtime image

Why:
- Resolve the runtime image vulnerability finding.

What:
- src/api/Dockerfile: uninstall pip before switching to UID 10001.

Refs: US01a, round-1 review-infra finding 1
```

**T4** — `src/web/src/api/client.ts`

```text
fix(US01a): handle malformed API error responses

Why:
- Preserve the ApiError contract for proxy and malformed responses.

What:
- src/web/src/api/client.ts: catch JSON parsing failures and validate
  error items, falling back to an empty errors array.

Refs: US01a, round-1 review-code finding 1
```

**T5 cleanup** — delete `reports/handoff/US01a-dev2.md`

```text
docs(US01a): remove the duplicate story handoff

Why:
- Keep the handoff in the story round record.

What:
- reports/handoff/US01a-dev2.md: delete the out-of-plan duplicate.

Refs: US01a, round-1 review-code finding 2
```

No commits made. No dependency pins changed. The successful-response JSON parsing note remains unchanged; the finding concerned non-2xx responses. The existing Starlette/httpx deprecation warning remains nonblocking.

No open questions. Ready for review and QA.