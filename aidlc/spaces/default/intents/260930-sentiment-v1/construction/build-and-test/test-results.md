# Test Results — `u1-application`

## Build status

**Success.** `python -m pip install -e ".[dev]"` in `.venv` completes; `ruff check app tests` reports
"All checks passed!"; `ruff format --check app tests` reports "23 files already formatted".

## Test results

| Suite | Command | Total | Passed | Failed | Skipped |
|---|---|---|---|---|---|
| Unit + coverage | `pytest -q <10 unit-scoped test files> --cov=app --cov-report=term-missing --cov-fail-under=80` | 94 | 94 | 0 | 0 |

No failures, no skips. The run was executed with `PYTHONDONTWRITEBYTECODE=1`, a `/tmp` coverage file
and `-p no:cacheprovider` so no build artifacts land in the workspace.

## Coverage report

```
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
app/__init__.py                2      0   100%
app/config.py                 54      0   100%
app/db.py                     66      0   100%
app/dummy_client.py           23      0   100%
app/main.py                   42      1    98%   49
app/models.py                 31      0   100%
app/openrouter_client.py      80      6    92%   89-96
app/repository.py             20      0   100%
app/routes.py                109      0   100%
app/sentiment.py              22      0   100%
app/service.py                39      0   100%
app/session_auth.py          117     17    85%   84-120
--------------------------------------------------------
TOTAL                        605     24    96%
Required test coverage of 80% reached. Total coverage: 96.03%
```

## End-to-end smoke

The recorded verification command installs, runs the suite, starts the app on loopback and probes
`/v1/health`. Observed:

```
info:     Sentiment analysis app ready in offline mode (OpenRouter not connected)
{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
```

Exit code 0. The health payload reports the offline mode, is not connected, and carries a reason.

## Target Verification Matrix (final)

The per-target matrix with actual values, evidence, owning stage and one final verdict per applicable
target is in `build-and-test-summary.md` § "Target Verification Matrix". Every applicable target is
`Met`; the two deliberate absences (`NFR-P3`, `NFR-SC1`) are `N/A` with their justification. No
`Pending` verdict remains.

## Failure details

None. The failure-escalation ladder was not entered, so there is no `## Loop-Back Log` for this run.
