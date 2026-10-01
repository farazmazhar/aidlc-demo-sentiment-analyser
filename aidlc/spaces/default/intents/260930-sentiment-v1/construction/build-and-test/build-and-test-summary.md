# Build and Test Summary — `u1-application`

## Overview

- Intent `260930-sentiment-v1`, scope `classic`, depth Standard, test strategy **Standard**.
- Single unit `u1-application` (the whole application); brownfield repository.
- Build status: **success**. Editable install succeeds; `ruff check` and `ruff format --check` are
  clean; the unit suite passes at 96.03% line coverage, above the 80% floor.

## Test type inventory

| Type | Artifact | Generated |
|---|---|---|
| Unit tests (per-unit) | `<record>/construction/u1-application/code-generation/unit-test-instructions.md` | yes (Code Generation) |
| Integration tests | `integration-test-instructions.md` | yes (Standard strategy) |
| Security checks | `security-test-instructions.md` | yes (security NFRs exist) |
| Performance checks | `performance-test-instructions.md` | yes (performance NFRs exist) |

## Coverage expectations per unit

- `u1-application`: whole-application line coverage ≥ 80% (affirmed floor, NFR4.1). Measured:
  **96.03%** (`605 stmts, 24 miss`).

## Target Verification Matrix

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|---|---|---|---|---|---|---|
| NFR-P1 | nfr-requirements/performance-requirements.md | offline analysis < 1s | offline analysis returns immediately (single in-memory score + one store write) | `.venv/bin/python -m pytest` + smoke run | build-and-test | Met |
| NFR-P2 | nfr-requirements/performance-requirements.md | live analysis bounded by the outbound timeout; caller sees a busy state | transport carries the 10s timeout constant; page shows a loading state | tests/test_live_client.py; app/static/app.js | build-and-test | Met |
| NFR-P3 | nfr-requirements/performance-requirements.md | no throughput/concurrency target applies | deliberate absence (assumption A4) | nfr-requirements/performance-requirements.md | build-and-test | N/A |
| NFR1.1 | nfr-requirements/reliability-requirements.md | offline serves every capability except live | suite runs offline with no key; smoke run starts offline | `.venv/bin/python -m pytest`; smoke run | build-and-test | Met |
| NFR1.2 | nfr-requirements/reliability-requirements.md | suite fails loudly on any network use | `offline_guard` raises on outbound connect | tests/conftest.py | build-and-test | Met |
| NFR-R1 | nfr-requirements/reliability-requirements.md | refused submission leaves the store untouched | row-count 0 asserted on refusal paths | tests/test_routes.py | build-and-test | Met |
| NFR-R2 | nfr-requirements/reliability-requirements.md | schema change keeps rows or fails visibly | migration test preserves rows; both-trigger case added in R-01 | tests/test_db.py | build-and-test | Met |
| NFR-R3 | nfr-requirements/reliability-requirements.md | rejected/missing credential degrades to offline | suite asserts fall-back | tests/test_auth_routes.py, tests/test_service.py | build-and-test | Met |
| NFR2.1 | nfr-requirements/security-requirements.md | credential never rendered/logged/in body | assertions over settings, logs and bodies | tests/test_config.py, tests/test_routes.py | build-and-test | Met |
| NFR2.2 | nfr-requirements/security-requirements.md | credential only in gitignored file or memory | `git check-ignore` assertion; placeholder example | tests/test_config.py | build-and-test | Met |
| NFR5.1 | nfr-requirements/security-requirements.md | server binds loopback only | single bind constant; smoke probe on 127.0.0.1 | app/main.py; smoke run | build-and-test | Met |
| NFR5.2 | nfr-requirements/security-requirements.md | no cloud/container/account introduced | one process and one file | app/main.py; nfr-design/security-design.md | build-and-test | Met |
| NFR-S1 | nfr-requirements/security-requirements.md | app failures carry code+message, never a stack trace/path | single two-field envelope asserted | tests/test_routes.py | build-and-test | Met |
| NFR6.1 | nfr-requirements/observability-requirements.md | health reports active engine and connection state | `/v1/health` payload asserted | tests/test_routes.py; smoke run | build-and-test | Met |
| NFR6.2 | nfr-requirements/observability-requirements.md | startup records mode; missing key warns naming the config file | captured log naming `config.local.toml` | tests/test_config.py | build-and-test | Met |
| NFR6.3 | nfr-requirements/observability-requirements.md | no log record contains credential material | assertions over captured records | tests/test_config.py | build-and-test | Met |
| NFR4.1 | nfr-requirements/observability-requirements.md | coverage reported over the whole app vs the floor | 96.03% ≥ 80% | coverage report in the verification command | build-and-test | Met |
| NFR4.2 | nfr-requirements/observability-requirements.md | suite result is the pre-ship visibility (no pipeline) | recorded gap; suite + coverage run at every checkpoint | nfr-requirements/observability-requirements.md | build-and-test | Met |
| NFR-SC1 | nfr-requirements/scalability-requirements.md | no scaling target applies | deliberate absence (assumption A4) | nfr-requirements/scalability-requirements.md | build-and-test | N/A |
| NFR-SC2 | nfr-requirements/scalability-requirements.md | history stays readable as it grows | history read bounded by a limit parameter | tests/test_routes.py | build-and-test | Met |
| NFR-SC3 | nfr-requirements/scalability-requirements.md | store remains a single local file | one SQLite file | app/db.py | build-and-test | Met |
| NFR3.1 | nfr-requirements/tech-stack-decisions.md | runtime dependencies exactly two | `fastapi`, `uvicorn` only | pyproject.toml | build-and-test | Met |
| NFR3.2 | nfr-requirements/tech-stack-decisions.md | dev tooling under the dev extra | pytest, pytest-cov, ruff | pyproject.toml | build-and-test | Met |
| NFR-TS1 | code-generation-plan.md (Testing Contract) | pinned ruff rule set including `S` | `[tool.ruff]` pinned; `ruff check` clean | pyproject.toml; `ruff check app tests` | build-and-test | Met |
| NFR-TS2 | code-generation-plan.md (Testing Contract) | coverage settings over `app/` with an 80% floor | `--cov=app --cov-fail-under=80` | pyproject.toml; coverage run | build-and-test | Met |

No `Pending` verdicts remain. Two deliberate absences (`NFR-P3`, `NFR-SC1`) are recorded as `N/A`
with their justification, per the requirements' assumption A4.

## Readiness assessment

- **Build-ready**: yes.
- **Test-ready**: yes — unit, integration, security and performance checks all pass.
- **Deployment-ready**: yes for the local model (localhost checkout; a commit is the release per the
  team's affirmed practices). No hosted/container deployment exists in scope.

## Known limitations or outstanding items

- **Coverage-vs-CI gap (NFR4.2)**: the affirmed posture expects the coverage floor in a CI job, but
  this scope skips the CI Pipeline stage; the floor runs only when the verification command runs.
  Recorded in `nfr-requirements/observability-requirements.md` and the phase's open questions.
- The SQLite concurrency limitation (assumption A4) remains accepted, not a v1 target.
