# Technology Stack — `sentiment-opencode`

> Versions are the repo-local `.venv` (`pip list`) at HEAD
> `4eb9b74c4197114181dab641c177c569f2058c24`; declared floors come from
> `pyproject.toml`. Python interpreter: `3.14.7`, `requires-python = ">=3.11"`.

## Summary

| Area | Choice | Version |
|---|---|---|
| Language | Python | 3.11+ (developed on 3.14.7) |
| Web framework | FastAPI | declared `>=0.110`, installed `0.142.2` |
| ASGI server | Uvicorn | declared `>=0.27`, installed `0.54.0` |
| ASGI toolkit (transitive) | Starlette | installed `1.7.0` |
| Validation (transitive) | Pydantic / pydantic_core | installed `2.13.5` / `2.46.5` |
| Async worker pool (transitive) | anyio | installed `4.15.1` |
| Storage | Python stdlib `sqlite3` | stdlib (no server) |
| HTTP client (outbound) | Python stdlib `urllib` | stdlib |
| CSV (intended) | Python stdlib `csv` | stdlib (not yet used) |
| Config format | TOML via stdlib `tomllib` | stdlib |
| Test runner | pytest | declared `>=8`, installed `9.1.1` |
| Coverage | pytest-cov / coverage | declared `>=5`, installed `7.1.0` / `7.16.2` |
| Lint + format | Ruff | declared `>=0.6`, installed `0.16.9` |
| Build backend | setuptools | `>=68`, PEP 517/518 (`setuptools.build_meta`) |
| Front end | Hand-written HTML + vanilla JS | none (no framework, no bundler) |
| CI/CD | **none** | — |
| Containers | **none** | — |

## Runtime Dependencies (exactly two)

`pyproject.toml` declares the runtime list and a comment tying the cap to
NFR3.1/C1:

```toml
dependencies = [
    "fastapi>=0.110",
    "uvicorn>=0.27",
]
```

The cap is asserted by `tests/test_config.py:141-160` (two runtime deps; dev
tools must not appear in the runtime list). `python-multipart` is deliberately
**not** installed.

## Development Dependencies (the `dev` extra)

```toml
dev = ["pytest>=8", "pytest-cov>=5", "ruff>=0.6"]
```

Adding development tools does not change the two-runtime-dependency count, but
the NFR3 comment and the README's "exactly three packages" line must be kept
truthful when they change.

## Not Used / Notably Absent

Verified by `pip list` and repository inspection:

- **No** `python-multipart` (relevant to CSV upload design).
- **No** `httpx`, `requests`, `aiofiles`.
- **No** ORM (SQLAlchemy, etc.) or migration framework (Alembic, etc.).
- **No** `requirements.txt`, lockfile, constraints file, `Makefile`,
  `Dockerfile`, tox/ini, `.pre-commit-config.yaml`.
- **No** front-end framework, bundler, package.json or npm dependency.
- **No** `pydantic` used directly in `app/` (it is a FastAPI transitive; request
  and record shapes are stdlib dataclasses).
- **No** CI workflow files of any kind.

## Standard Library Used

`sqlite3`, `csv` (not yet used), `json`, `re`, `urllib` (`request`/`error`/
`parse`), `tomllib`, `hashlib`, `secrets`, `base64`, `threading`, `asyncio`
(tests), `logging`, `dataclasses`, `datetime`, `pathlib`, `time`.

## Build and Tooling Configuration

| Tool | Config location | Key settings |
|---|---|---|
| setuptools | `pyproject.toml` `[build-system]`, `[tool.setuptools]` | `packages = ["app"]`, `package-data app = ["static/*"]` |
| pytest | `[tool.pytest.ini_options]` | `testpaths = ["tests"]`, `addopts = "-q --cov=app --cov-report=term-missing --cov-fail-under=80"`, `filterwarnings = ["error"]` |
| coverage | `[tool.coverage.run]`, `[tool.coverage.report]` | `source = ["app"]`, `fail_under = 80`, `show_missing = true` |
| ruff lint | `[tool.ruff]`, `[tool.ruff.lint]` | `line-length = 100`, `target-version = "py311"`, `select = ["E","F","W","I","N","UP","S","B","C4","SIM"]`, `extend-immutable-calls = ["fastapi.Depends","fastapi.Query"]`, per-file ignores for tests |
| ruff format | `[tool.ruff.format]` | `quote-style = "double"`, `line-ending = "lf"` |

## Platform and Runtime Notes

- Python **3.14** is the development interpreter; the `filterwarnings = ["error"]`
  setting doubles as an upgrade canary for FastAPI/pydantic deprecations.
- FastAPI runs synchronous endpoints in anyio worker threads; this is directly
  relevant to the accepted SQLite thread-affinity risk (R-01).
- Storage is the standard-library `sqlite3` with `row_factory = sqlite3.Row` and
  `PRAGMA foreign_keys = ON`; no WAL, no connection pool, one connection per
  request.
- The only output path is a single Uvicorn process on `127.0.0.1:8000`
  (`HOST`/`PORT` in `app/main.py:36-37`).

## Intent-Relevant Stack Constraint (CSV Import/Export)

The two-runtime-dependency cap means a CSV upload must **not** introduce
`python-multipart`. Within the current stack the workable options are the stdlib
`csv` module over a raw request body (`text/csv` / `text/plain`) or a
JSON-wrapped CSV string. A CSV export can be produced with stdlib `csv` and a
`text/csv` response — no new dependency either way.
