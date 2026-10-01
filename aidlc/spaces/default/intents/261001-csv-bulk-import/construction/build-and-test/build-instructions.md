# Build Instructions — CSV Bulk Import / Export

> Stage: **build-and-test** (Construction, scope `express`, depth Minimal).
> Intent: `csv-bulk-import` (`261001-csv-bulk-import`).
> This is a pure-Python, localhost-only project with no compile/bundle step.

## Prerequisites

- **Python 3.14** (the project targets 3.11+; developed and verified on 3.14.7).
- **pip** and an editable install of the package.
- No external services, no network, no database server.

## Dependency installation

```bash
python -m pip install -e ".[dev]"
```

- **Runtime dependencies** (cap of two, preserved): `fastapi`, `uvicorn`.
- **Dev dependencies**: `pytest`; the project already configures coverage
  (`pytest-cov`) and `ruff` in `pyproject.toml`. The bulk CSV feature adds
  **no** runtime or test dependency (it uses the standard-library `csv` module).

## Environment setup

- **Build and tests need no environment variables.**
- **Live (OpenRouter) mode only:** copy `config.example.toml` to
  `config.local.toml` and set the key there. That file is gitignored and must
  never be committed (project rule). It is not needed for the build or the
  offline suite.

## Build commands

There is no compile, bundle, or transpile step. The editable install is the
build. A quick structural check:

```bash
python -c "import app; print('app imported OK')"
```

The application entry point is `app:app` (`create_app()` built at import time);
`uvicorn app:app` is the runtime command used by the team's verification command.

## Build verification steps

```bash
python -m pytest
```

This runs the full suite with the project's configured coverage floor
(`addopts` includes `--cov=app --cov-fail-under=80`) and
`filterwarnings = ["error"]`. Exit code 0 means the build is green.

## Troubleshooting common build issues

- **A deprecation warning fails the run.** `filterwarnings = ["error"]` is the
  mechanical gate; fix the warning rather than relaxing the filter.
- **A subset run fails the coverage floor.** `addopts` enforces whole-application
  coverage, so any partial run (e.g. one test module) cannot satisfy 80%. The
  Code Generation inner loop runs with `--no-cov`; the **full** run applies the
  floor unchanged. Never lower the floor to make a subset pass.
- **Lint/format:** `python -m ruff check app tests` and
  `python -m ruff format --check app tests` must both be clean.
- **SQLite:** the app creates/migrates `data/sentiment.db` on first startup;
  deleting the file is the accepted recovery path.
