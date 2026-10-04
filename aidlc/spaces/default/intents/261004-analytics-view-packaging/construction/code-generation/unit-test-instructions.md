# Unit Test Instructions — `analytics-view-packaging` (stage-level)

## Framework and configuration

`pytest` only, already configured in `pyproject.toml` under
`[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `addopts = "-q --cov=app
--cov-report=term-missing --cov-fail-under=80"`, and `filterwarnings = ["error"]`.
No new test tooling is added by this iteration. The active test strategy is
**Minimal** (express): one verifiable test per requirement at the narrowest
effective level, plus at least one happy-path unit test per component.

## How to run this iteration's tests

The scoped command for the view work is the page contract module, run from the
project root:

```bash
python -m pytest -q tests/test_page.py --cov-fail-under=0
```

> `--cov-fail-under=0` disables the **whole-application** 80 % floor for this
> subset run only: a single test module cannot cover the whole application, so the
> floor would exit 1 for a reason unrelated to any failure. The floor stays fully
> enforced on the whole-suite run, which is where it means anything.

Before the new assertions exist, the runnable scoped command is the existing page
suite, used only to verify the runner (plan step 1):

```bash
python -m pytest -q tests/test_page.py
```

The whole-suite gate is the recorded verification: `make verify` (plan step 9)
runs the full `pytest` with the floor applied, plus `ruff check`,
`ruff format --check`, the secret scan and the dependency audit.

## Expected coverage

The whole-application line floor is **80 %**, enforced twice in configuration
(`addopts` and `[tool.coverage.report] fail_under`). This iteration's changes are
counted in it, not excluded from it. The browser script is not executed by any
test, so it contributes no coverage; that is unchanged and expected.

## Mocking and stubbing

The suite's standing policy holds: assertions read values back out of real SQLite
and real served markup, never out of a mock of the thing under test. Substitution
happens only at process seams, and the session-scoped offline guard must stay
armed. No browser execution is introduced, because the runtime dependency cap
admits no browser-automation library.

## Test data management

`tmp_path`-scoped settings and database paths, so no test reads the real
configuration file or the real database. The view tests assert on the served
markup returned by `GET /` and on the served script bytes, not on a live browser.

## Ordering

Acceptance- and markup-level tests are written against the requirement **before**
the implementation (plan step 2); lower-level unit tests are written **after** it
(plan step 8). The packaging steps (9–16) are configuration and tooling and carry
no new unit test beyond the whole-suite gate that `make verify` runs.
