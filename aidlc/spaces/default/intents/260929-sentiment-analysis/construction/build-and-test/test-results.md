# Test Results — very-cool-sentiment-analysis

Execution record for Build and Test (`construction/build-and-test/`), zero-Unit
stage-level scope. Inputs: `construction/code-generation/unit-test-instructions.md`
and `construction/code-generation/code-summary.md`.

## Build status

| Command | Exit | Output |
|---------|------|--------|
| `.venv/bin/python -m pip install -e ".[dev]"` | 0 | `Successfully installed very-cool-sentiment-analysis-0.1.0` |
| `.venv/bin/python -m compileall -q app` | 0 | no output |

## Test results

| Command | Total | Passed | Failed | Skipped |
|---------|-------|--------|--------|---------|
| `.venv/bin/python -m pytest tests` | 27 | 27 | 0 | 0 |

Final line: `27 passed in 0.25s`.

Both commands from the instruction files were run once each: the suite is
stage-scoped (`testpaths = ["tests"]`), and there are no per-unit duplicates in
this zero-Unit intent.

## Failure details

None. No test failed, no command returned non-zero, and no target ended
`Not Met` or `Unverified`, so the failure-escalation ladder never entered and no
loop-back was recorded.

## Coverage report

No line-coverage gate applies: the active strategy is Minimal and `poc` adds no
extra new-test floor. Requirement coverage is 42/42 IDs mapped in
`construction/code-generation/traceability.json` (39 `OK`, 3 `N/A` justified by
FR5.5), confirmed against existing target files in `cross-unit-traceability.md`.

## Target Verification Matrix (final)

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|-----------|--------|----------|--------|----------|--------------|---------|
| BUILD-1 | build-instructions.md §5 | install exits 0 | exit 0 | pip output above | build-and-test | Met |
| BUILD-2 | build-instructions.md §5 | modules byte-compile | exit 0 | compileall above | build-and-test | Met |
| FR5.2 | requirements.md FR5.2 | one command, suite green | 27 passed / 0 failed | pytest output above | build-and-test | Met |
| TC-1 | code-generation-plan.md ## Testing Contract | one verifiable test per requirement, happy-path floor per component | 27 tests across all five layers; 42/42 IDs mapped | `tests/`; `traceability.json` | build-and-test | Met |
| TC-2 | code-generation-plan.md ## Testing Contract | `poc` floor: suite green, no extra floor | 27 passed | pytest output above | build-and-test | Met |
| FR5.3 | requirements.md FR5.3 | tests fully offline | suite green with no config file and no key | pytest run; `socket.connect` guard in `tests/conftest.py` | build-and-test | Met |
| FR5.4 | requirements.md FR5.4 | dummy, DB and handler paths covered | dummy, db, repository, config, service, routes, page covered | `tests/` | build-and-test | Met |
| FR5.5 | requirements.md FR5.5 | live client never exercised | no test touches it | `tests/`; `N/A` rows in `traceability.json` | build-and-test | Met |
| FR1.4 / FR4.6 | requirements.md FR1.4, FR4.6 | mode visible in startup and health | startup log line + `{"status":"ok","mode":"dummy"}` | live run `127.0.0.1:8141` | build-and-test | Met |
| FR4.3 | requirements.md FR4.3 | stored record returned; invalid input rejected and not persisted | 200 with record; `422` for empty text | live run | build-and-test | Met |
| FR4.4 | requirements.md FR4.4 | newest-first with limit | newest-first; `limit=0` → `422` | live run | build-and-test | Met |
| FR4.7 / NFR4 | requirements.md FR4.7, NFR4 | localhost only, no auth/cloud/Docker | `LISTEN 127.0.0.1:8141` only; no auth; no deployment artifacts | `ss -ltn`; repository listing | build-and-test | Met |
| NFR1 | requirements.md NFR1 | offline dev and tests | completed with no config and no key | pytest run; live run | build-and-test | Met |
| NFR2 | requirements.md NFR2 | key only in gitignored config; example has no secret | `config.local.toml` absent and gitignored; example `api_key = ""` | `git check-ignore -v`; file contents | build-and-test | Met |
| NFR3 | requirements.md NFR3 | three direct dependencies beyond the stdlib | `fastapi`, `uvicorn`, `pytest` | `pyproject.toml`; distribution audit | build-and-test | Met |
| NFR5 | requirements.md NFR5 | engine replaceable behind the interface | substitutability test passes through SQLite | `tests/test_service.py::test_client_is_substitutable_behind_the_interface` | build-and-test | Met |
| NFR6 / FR3.1 / FR3.2 | requirements.md NFR6, FR3.1, FR3.2 | database created on first run | `data/sentiment.db` created automatically | live run; `ls -la data/` | build-and-test | Met |
| FR2.2 / FR2.5 | requirements.md FR2.2, FR2.5 | deterministic dummy label, probabilities, intensity | deterministic across runs | `tests/test_dummy_client.py`; live run | build-and-test | Met |

No `Pending` verdict remains; every applicable target is `Met`.

## Known limitations carried into the record

The accepted Code Generation review risk (R-01, connection thread-affinity),
the untested live OpenRouter path (FR5.5 by design), and the untested
browser-side JavaScript are recorded in the Build and Test Summary under
"Known limitations and outstanding items". None of them is a defined target of
this scope.
