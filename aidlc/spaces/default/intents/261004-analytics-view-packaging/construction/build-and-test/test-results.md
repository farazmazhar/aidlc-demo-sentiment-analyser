# Build and Test Results — Analytics View & Packaging

> Stage: **build-and-test** (Construction, scope `express`, depth Minimal, test strategy Minimal).
> Intent: `analytics-view-packaging` (`261004-analytics-view-packaging`), lead: quality engineer with the security engineer on hand.
> Every command below was executed in this environment against the workspace after Code Generation was approved.

## Build status

**Success.** The editable install is present, `import app` resolves, and the full
suite executes. No compile/bundle step exists (pure Python).

## Executed commands and results

| # | Command | Result |
|---|---------|--------|
| 1 | `make verify` | **Green end to end** — all six steps exited 0 (install, `ruff check`, `ruff format --check`, `pytest`, `detect-secrets`, `pip-audit`) |
| 2 | `python -m pytest` | **198 passed, 0 failed, 0 skipped** in 1.91 s; total coverage **97.06 %** (`--cov-fail-under=80` reached); `filterwarnings = ["error"]` clean |
| 3 | `python -m ruff check app tests` | **All checks passed!** |
| 4 | `python -m ruff format --check app tests` | **30 files already formatted** |
| 5 | `python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline app tests config.example.toml pyproject.toml README.md Makefile docs` | No findings (allowlisted fixtures only) |
| 6 | `python -m pip_audit -r requirements.lock` | **No known vulnerabilities found** |

The developer's scoped inner-loop command
(`python -m pytest -q tests/test_page.py --cov-fail-under=0`) was also run during
Code Generation; it is a subset and is not the authoritative signal. The full run
above is authoritative and applies the coverage floor unchanged.

## Test results

- **Total: 198, Passed: 198, Failed: 0, Skipped: 0.**
- **Coverage: 97.06 %** (884 statements, 26 missed). Per module: `app/analytics.py`,
  `app/config.py`, `app/db.py`, `app/dummy_client.py`, `app/models.py`,
  `app/repository.py`, `app/sentiment.py`, `app/service.py`, `app/terms.py`,
  `app/__init__.py` all 100 %; `app/routes.py` 99 %; `app/main.py` 98 %;
  `app/openrouter_client.py` 92 % (live engine, not exercised by design);
  `app/session_auth.py` 85 %.
- **New tests added by this change:** 6 served-markup / served-script contract
  tests in `tests/test_page.py` (+6 over the 192-test baseline), plus 10 new
  `REQUIRED_TEST_IDS` hooks.

## Failure details

None. No command failed, so the failure-escalation ladder was not entered.

## Target Verification Matrix

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|-----------|--------|----------|--------|----------|--------------|---------|
| TV-1 | `requirements.md` FR3.1 | Full suite green | 198 passed, 0 failed | `make verify` / `python -m pytest` | build-and-test | Met |
| TV-2 | `requirements.md` C2 / `pyproject.toml` | No new runtime dependency; dependency-cap test green | 2 runtime deps (`fastapi`, `uvicorn`); `tests/test_config.py` passes | `python -m pytest` | build-and-test | Met |
| TV-3 | `requirements.md` FR1.10 (NFR4.6) | Partial-failure marker present and pinned | `summary-partial` / `terms-partial` hooks asserted | `tests/test_page.py` | build-and-test | Met |
| TV-4 | `requirements.md` FR1.11 (NFR4.7) | Supersede / no-silent-retry hooks present and pinned | `AbortController` + request-token hooks asserted; no resend | `tests/test_page.py` | build-and-test | Met |
| TV-5 | `requirements.md` FR2.1 | `make verify` runs install → lint → pytest → scan → audit | 6-step recipe verified | `make verify`, `make -n verify` | build-and-test | Met |
| TV-6 | `requirements.md` FR2.2 | Secret scan with the fixture allowlist | `detect-secrets` clean against `.secrets.baseline` | `make verify` | build-and-test | Met |
| TV-7 | `requirements.md` FR2.3 | Dependency audit wired into verify | `pip-audit` — no known vulnerabilities | `make verify` | build-and-test | Met |
| TV-8 | `requirements.md` FR2.4 | Hashed lockfile committed | `requirements.lock` present and consumed by `pip-audit` | `requirements.lock` | build-and-test | Met |
| TV-9 | `requirements.md` FR2.5 | `LICENSE` present and declared | MIT `LICENSE`; declared in `pyproject.toml` | `LICENSE`, `pyproject.toml` | build-and-test | Met |
| TV-10 | `requirements.md` FR2.6 | `ruff TID251` boundary rules active | `TID` selected; three `banned-api` boundaries; probe proved non-vacuous | `pyproject.toml`, `ruff check` | build-and-test | Met |
| TV-11 | `pyproject.toml` (`--cov-fail-under=80`) | Line coverage ≥ 80 % | 97.06 % | pytest coverage report | build-and-test | Met |
| TV-12 | `memory/team.md` Code Style | `ruff check` clean | All checks passed | `python -m ruff check app tests` | build-and-test | Met |
| TV-13 | `memory/team.md` Code Style | `ruff format --check` clean | 30 files already formatted | `python -m ruff format --check app tests` | build-and-test | Met |
| TV-14 | Testing Contract (Minimal strategy, stage-protocol §8) | One test per requirement + happy-path floor | 29/29 IDs `OK`; +6 page-contract tests | `traceability.json`, `tests/test_page.py` | build-and-test | Met |
| TV-15 | `requirements.md` NFR1 / FR3.3 | NFR4.6/NFR4.7 verified by static assertions + manual end-to-end | assertions in `tests/test_page.py`; manual boot documented in README | `tests/test_page.py`, README | build-and-test | Met |

No applicable target is `Not Met` or `Unverified`; the inventory found applicable
measurable targets, so no `N/A` row is used.

## Loop-Back Log

Not present — the failure ladder (rungs 1–4) was never entered.

## Known limitations / outstanding items

- The browser script is served and its hooks are pinned, but it is never executed
  by the suite; NFR4.6/NFR4.7 rest on the static assertions plus the documented
  manual boot, per the recorded Q2 decision.
- The secret scan covers the project's authored paths; the `aidlc/` harness tree
  is not scanned.
- R-01 (SQLite per-request connection thread affinity) is unchanged and remains
  the accepted, recorded limitation; no concurrency target is in scope.
- The two deferred prior-FR7 items (startup loopback enforcement, ASGI harness
  replacement) are out of scope for this intent.
