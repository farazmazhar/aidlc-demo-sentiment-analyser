# Unit Test Instructions — `u1-analytics-slice`

## Framework and configuration

`pytest` only, already configured in `pyproject.toml` under
`[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `addopts = "-q --cov=app
--cov-report=term-missing --cov-fail-under=80"`, and `filterwarnings = ["error"]`.
No new tooling is added by this unit.

## How to run this unit's tests

The command must be **scoped to this unit**, because Build and Test executes every
unit's command and an unscoped one would rerun the whole suite once per unit:

```bash
python -m pytest -q tests/test_analytics_read.py tests/test_analytics_routes.py tests/test_terms.py tests/test_migration_indexes.py --cov-fail-under=0
```

> **Amendment recorded at Code Generation.** `--cov-fail-under=0` was added to the
> command above as written, for a reason the original form did not account for.
> `addopts` applies the **whole-application** 80 % floor to *every* run, so the
> four-file subset scored 65.95 % and exited 1 — not because any test failed, but
> because a subset of the tests cannot cover the whole application: `app/service.py`
> and `app/session_auth.py` are not exercised by this unit's files at all. The flag
> disables the floor **for the scoped run only**, keeps the per-module coverage
> report visible to Build and Test, and leaves the floor fully enforced on the
> whole-suite run, which is where it means anything.
>
> **The residual, stated here because this is the artifact Build and Test reads.**
> The command above — the one Build and Test actually executes for this unit — has
> **no coverage gate of any kind**. It exits 0 at 66 %. Coverage is enforced on the
> full-suite run alone, so a regression confined to this unit's files would not be
> caught by the scoped command by itself. Read the number; do not rely on the exit
> code. The whole-suite floor is untouched: `addopts` still carries
> `--cov-fail-under=80` and `[tool.coverage.report] fail_under = 80` is unchanged,
> so the full run still exits non-zero below 80 %.

Before those files exist, the runnable scoped command is the existing suite, used
only to verify the runner (plan step 1):

```bash
python -m pytest -q tests/test_routes.py tests/test_db.py tests/test_repository.py
```

## Expected coverage

The whole-application line floor is 80 %, enforced twice in configuration. This
unit's new modules must be counted in it, not excluded from it.

## Mocking and stubbing

The suite's standing policy holds: assertions read values back out of real SQLite
and real served markup, never out of a mock of the thing under test. Substitution
happens only at process seams, and the session-scoped offline guard must stay
armed.

## Test data management

`tmp_path`-scoped settings and database paths, so no test reads the real
configuration file or the real database. The performance fixture seeds 10,000 rows
across **365 distinct UTC days**, which is what makes the series length — and
therefore the measured work — reproducible.

## Ordering

Acceptance- and API-level tests are written against the requirement **before** the
implementation; lower-level unit tests are written **after** it. Plan steps 2–4
are test-first; step 13 is test-after.
