# Build Instructions — Analytics View & Packaging

> Stage: **build-and-test** (Construction, scope `express`, depth Minimal, test strategy Minimal).
> Intent: `analytics-view-packaging` (`261004-analytics-view-packaging`).
> This is a pure-Python, localhost-only project with no compile/bundle step.

## Prerequisites

- **Python 3.14** (the project targets 3.11+; developed and verified on 3.14.7).
- **pip** and an editable install of the package.
- **GNU make** (the verification entry point is `make verify`).
- No external services, no database server. `make verify`'s dependency audit reaches
  PyPI; the test suite itself never touches the network.

## Dependency installation

```bash
python -m pip install -e ".[dev]"
```

- **Runtime dependencies** (cap of two, preserved): `fastapi`, `uvicorn`.
- **Dev dependencies**: `pytest`, `pytest-cov`, `ruff`, and this intent's additions
  `detect-secrets`, `pip-audit`, and `uv` (the lockfile generator).
- **Reproducible install from the lockfile**: `requirements.lock` (hashes) is
  committed; `make lock` documents how it is regenerated with `uv`.

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
make verify
```

`make verify` runs, in order:

1. `python -m pip install -e ".[dev]"`
2. `python -m ruff check app tests`
3. `python -m ruff format --check app tests`
4. `python -m pytest` (the 80 % whole-application coverage floor is applied by `addopts`)
5. `python -m detect_secrets.pre_commit_hook --baseline .secrets.baseline …`
6. `python -m pip_audit -r requirements.lock`

Exit code 0 means the build and all gates are green.

## Troubleshooting common build issues

- **A deprecation warning fails the run.** `filterwarnings = ["error"]` is the
  mechanical gate; fix the warning rather than relaxing the filter.
- **A subset run fails the coverage floor.** `addopts` enforces whole-application
  coverage, so any partial run cannot satisfy 80 %. The Code Generation inner loop
  runs with `--cov-fail-under=0`; the **full** run applies the floor unchanged.
  Never lower the floor to make a subset pass.
- **`detect-secrets` exits 3.** Committed line numbers drifted from the baseline;
  regenerate with `detect-secrets scan … > .secrets.baseline` after confirming the
  findings are the known fake-key fixtures.
- **`pip-audit` flags a CVE.** Treat it as a real finding; never relax the gate.
- **SQLite:** the app creates/migrates `data/sentiment.db` on first startup;
  deleting the file is the accepted recovery path.
