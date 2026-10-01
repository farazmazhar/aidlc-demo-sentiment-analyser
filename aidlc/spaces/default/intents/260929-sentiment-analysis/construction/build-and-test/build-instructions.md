# Build Instructions — very-cool-sentiment-analysis

Applies to the whole application produced by Code Generation
(`construction/code-generation/code-generation-plan.md`,
`construction/code-generation/unit-test-instructions.md`,
`construction/code-generation/code-summary.md`). This intent is zero-Unit, so
there is one build target: the repository root.

## 1. Prerequisites

- Python 3.11 or newer (`pyproject.toml` sets `requires-python = ">=3.11"`;
  `tomllib` is standard-library only from 3.11).
- No network access is required to build, run in dummy mode, or run the tests.
- No database server, container runtime, or cloud account is required.

## 2. Dependency installation

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

This installs exactly three third-party packages beyond the standard library:
`fastapi` and `uvicorn` (runtime) and `pytest` (dev). There is no separate
build, bundle, or transpile step — the project is plain Python.

## 3. Environment setup

Nothing is required for the default (`dummy`) mode: with no config file present
the app starts offline with no credentials.

For live mode, copy the committed example and fill in the key:

```bash
cp config.example.toml config.local.toml   # then edit config.local.toml
```

`config.local.toml` is gitignored and must never be committed. In live mode,
if the key is missing or empty the app fails at startup with a message naming
that file.

## 4. Build commands

```bash
.venv/bin/python -m compileall -q app
```

## 5. Build verification

| Step | Command | Expected |
|------|---------|----------|
| Dependencies resolve | `.venv/bin/python -m pip install -e ".[dev]"` | exits 0; installs `fastapi`, `uvicorn`, `pytest` |
| Modules compile | `.venv/bin/python -m compileall -q app` | exits 0, no output |
| App imports | `.venv/bin/python -c "import app"` | exits 0 |
| Dev entry point | `.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000` | startup log line `Sentiment analysis app ready in dummy mode`; binds `127.0.0.1` only |
| Health | `curl -s http://127.0.0.1:8000/health` | `{"status":"ok","mode":"dummy"}` |

## 6. Running the app

```bash
.venv/bin/python -m uvicorn app:app --reload
```

Binds `127.0.0.1:8000` by default (uvicorn's default host/port); the app is
localhost-only by design. `data/sentiment.db` is created automatically on first
startup.

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `error: externally-managed-environment` on install | system Python is PEP 668 managed | create and use `.venv` as shown above |
| `Address already in use` | another process holds port 8000 | pass `--port <free-port>` |
| Startup error naming `config.local.toml` | live mode selected with no key | put a real key in `config.local.toml`, or remove the file to run in dummy mode |
| `unable to open database file` | `data/` not writable | check directory permissions; `init_db()` creates the directory and file itself |
| `ModuleNotFoundError: app` | run from a different directory | always run from the repository root |
