# Build Instructions — `u1-application`

Unit `u1-application`, intent `260930-sentiment-v1`, scope `classic`, test strategy **Standard**.
This unit is the whole application, so these build steps cover the single repository.

## Prerequisites

- Python 3.11 or newer (the workspace runs on Python 3.14).
- No network access is required to build or to run the offline suite; the only outbound call is the
  user-initiated live engine call.
- No cloud component, container runtime, or account is required (project rule C3 / NFR5.2).

## Dependency installation

From the repository root:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

- Runtime dependencies stay exactly two: `fastapi`, `uvicorn` (NFR3 / NFR3.1).
- The `dev` extra carries the test runner (`pytest`), the coverage plugin (`pytest-cov`) and the
  linter/formatter (`ruff`) only (NFR3.2).

## Environment setup

- No key or config file is needed for development or tests; the app defaults to the offline engine
  (NFR1.1). To exercise live mode, place a key in the gitignored `config.local.toml` — never in a
  tracked file (NFR2 / C2).
- The SQLite store (`data/sentiment.db`) is created on first run by the startup initialisation step;
  `data/` is gitignored.

## Build commands

There is no compile/transpile step. "Build" is the editable install plus the tool checks:

```bash
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m ruff check app tests
.venv/bin/python -m ruff format --check app tests
```

## Build verification

```bash
.venv/bin/python -m pytest -q tests/test_config.py tests/test_dummy_client.py tests/test_live_client.py \
  tests/test_db.py tests/test_repository.py tests/test_service.py tests/test_routes.py \
  tests/test_page.py tests/test_session_auth.py tests/test_auth_routes.py \
  --cov=app --cov-report=term-missing --cov-fail-under=80
```

A successful build is: editable install succeeds, `ruff check` and `ruff format --check` are clean,
and the unit suite passes at or above the 80% line-coverage floor.

## Troubleshooting

- **`pip install` needs the network**: the development install pulls tooling from an index; a
  pre-built wheelhouse or an already-populated environment avoids this. Runtime use never needs it.
- **`.venv` cannot be created** (some sandboxes resolve `venv` to a non-Python base executable): run
  the same commands with the available interpreter, for example
  `/usr/bin/python3.14 -m pip install -e ".[dev]"`, without weakening any flag.
- **Coverage floor fails**: a module fell below the floor; add or extend tests rather than lowering
  `--cov-fail-under`.
- **Import error for `app.*`**: re-run the editable install from the repository root.
