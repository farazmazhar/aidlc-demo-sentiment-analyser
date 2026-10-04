# Technology Stack — `very-cool-sentiment-analysis` (repo `sentiment-opencode`)

## Languages

| Language | Version | Where | Notes |
|---|---|---|---|
| **Python** | `>=3.11` declared; **3.14.7** installed and used to measure the suite | All 14 `app/` modules, all 15 `tests/` modules, build and tool config | `target-version = "py311"` for `ruff`, so the code stays 3.11-compatible. Uses `from __future__ import annotations` in 13 of 14 `app/` modules (the exception is the 10-line `app/__init__.py`) |
| **JavaScript** | ES2020-era, no transpile | `app/static/app.js` (322 lines) | Vanilla, no module syntax, no bundler, no `package.json`. Runs as the browser loads it |
| **CSS** | — | Inline `<style>` in `app/static/index.html` | One `:root` custom-property block plus class rules. No preprocessor, no external stylesheet |
| **HTML** | — | `app/static/index.html` | One document, no partials, no client-side templating beyond one `<template>` element |
| **TOML** | — | `pyproject.toml`, `config.example.toml` (read at runtime via stdlib `tomllib`) | The configuration format for both the build and the app |

There are **no** other languages in the repository. `opencode.json` is the AI-DLC
harness configuration, not a build manifest — there is no npm ecosystem here at
all.

## Build System

| Aspect | Reality |
|---|---|
| **Type** | PEP 517 / setuptools, driven entirely by `pyproject.toml` |
| **Backend** | `setuptools.build_meta` (`requires = ["setuptools>=68"]`) |
| **Manifest** | `pyproject.toml` is the **only** manifest. No `setup.py`, no `setup.cfg`, no `requirements.txt`, no lockfile, no constraints file |
| **Packaging** | `packages = ["app"]`; `package-data` ships `static/*` |
| **Distribution** | `very-cool-sentiment-analysis` version `0.1.0`, description "A small localhost-only sentiment-analysis web app (FastAPI + sqlite3)…" |
| **Install** | `python -m pip install -e ".[dev]"` — editable, local only, never published |
| **Run** | `uvicorn app:app --reload` |
| **Absent** | No Makefile, Dockerfile, `compose.yaml`, `noxfile.py`, `tox.ini`, CI workflow, pre-commit config, or ADR directory |

## Runtime Framework

| Package | Declared floor | Installed | Role |
|---|---|---|---|
| **fastapi** | `>=0.110` | **0.142.2** | The whole HTTP surface: routing, dependency injection, request-body validation, exception handlers, `StaticFiles` |
| **uvicorn** | `>=0.27` | **0.54.0** | The ASGI server. `uvicorn app:app --reload` resolves through the `app/__init__.py` re-export |

These are the **only two runtime dependencies**, and that is an enforced
requirement, not a preference (NFR3.1, cited at `pyproject.toml:11`). The whole
rest of the runtime is the standard library.

## Transitive Runtime Dependencies

All resolved transitively by FastAPI / uvicorn. None is imported by application
code.

| Package | Installed | Reached through | Where it is used |
|---|---|---|---|
| starlette | 1.7.0 | fastapi | `StaticFiles`, `HTMLResponse`, `JSONResponse`, `RedirectResponse`, `Request`, routing |
| pydantic | 2.13.5 | fastapi | Request-body validation only. **No direct import in `app/`** — deliberate |
| pydantic_core | 2.46.5 | pydantic | native validation core |
| annotated-types | 0.8.0 | pydantic | typing support |
| anyio | 4.15.1 | starlette | The thread pool FastAPI uses to run the synchronous `def` handlers and the sync-generator dependency |
| click | 8.5.0 | uvicorn | uvicorn's CLI |
| h11 | 0.16.0 | uvicorn | HTTP/1.1 protocol implementation |
| idna | 3.20 | anyio | IDNA host encoding |
| annotated-doc | 0.0.5 | fastapi | documentation typing |
| opentelemetry-api | 1.45.0 | fastapi (a hard, non-extra dependency) | tracing hooks; nothing in `app/` imports it and no SDK/exporter is installed, so it is an unused transitive |
| typing_extensions | 4.16.0 | pydantic / fastapi | typing backports |
| typing-inspection | 0.4.4 | pydantic | typing introspection |

## Development Dependencies

Declared under `[project.optional-dependencies].dev`, so installing for use
stays at two packages.

| Package | Declared floor | Installed | Role |
|---|---|---|---|
| **pytest** | `>=8` | **9.1.1** | The entire test runner |
| **pytest-cov** | `>=5` | **7.1.0** | Enforces the coverage floor via `addopts` |
| **ruff** | `>=0.6` | **0.16.9** | Linter **and** formatter — one dependency buys both style and a static-analysis floor |
| coverage | *(via pytest-cov)* | 7.16.2 | The measurement engine |

**Deliberately not installed:**
- **`httpx`** — without it `fastapi.testclient` cannot work, which is why the
  suite carries its own hand-rolled in-process ASGI caller (`tests/conftest.py`).
  The dependency cap is asserted by a test (`tests/test_config.py:141-160`).
- **Any browser-automation package** — so `app.js` is never executed by the suite.
  `tests/test_page.py:1-6` states the limit explicitly.
- **Any type checker** — no `mypy`, no `pyright`, and no `py.typed` marker.

## Standard Library in Use

Everything else is stdlib. This is the substance of the two-package cap.

| Module | Used for | Location |
|---|---|---|
| `sqlite3` | The only storage driver; DDL, DML and the migration | `app/db.py`, `app/repository.py` |
| `urllib.request` / `urllib.error` / `urllib.parse` | Both outbound HTTP calls — the live sentiment call and the PKCE exchange | `app/openrouter_client.py`, `app/session_auth.py` |
| `tomllib` | Parsing `config.local.toml` | `app/config.py:24` |
| `csv` + `io` | Bulk import parsing and export writing | `app/routes.py:17-18` |
| `uuid` | Minting `import_id` | `app/service.py:15` |
| `datetime` + `timezone` (`datetime.UTC`) | UTC timestamps and the resolved per-day range; no `zoneinfo` and no local-time dependency | `app/repository.py`, `app/session_auth.py`, `app/analytics.py` |
| `decimal` (`Decimal`, `ROUND_HALF_UP`) | Rounding analytics shares and means deterministically | `app/analytics.py` |
| `collections.Counter` | Term-frequency counting for the `/v2` terms endpoint | `app/analytics.py` |
| `secrets`, `hashlib`, `base64` | PKCE verifier and S256 challenge | `app/session_auth.py` |
| `threading` | Locking the session credential and pending-verifier map | `app/session_auth.py:30` |
| `re` | The one tokeniser's word pattern, and the analytics date-bound pattern | `app/terms.py`, `app/analytics.py` |
| `json` | Serialising `probabilities` on write, decoding on read | `app/models.py`, `app/repository.py` |
| `logging` | Module loggers; `print()` never appears in `app/` | `app/main.py`, `app/routes.py`, `app/config.py` |
| `dataclasses` | All request/record/config types | throughout |
| `contextlib.asynccontextmanager`, `collections.abc` | Lifespan, type annotations | `app/main.py`, throughout |

## Database

| Aspect | Reality |
|---|---|
| Engine | SQLite, bundled with CPython |
| Library version | **3.53.4** (verified at runtime) |
| Driver | `sqlite3` stdlib module — no third-party driver |
| File | `data/sentiment.db`, created on demand (parent directory created automatically) |
| Row factory | `sqlite3.Row`, mapped to `AnalysisRecord` by `AnalysisRecord.from_row` |
| Pragma | `PRAGMA foreign_keys = ON` on every connection |
| Schema version | 4, recorded in `schema_meta(key, value)` and written on every `init_db`; three named indexes on `analyses` |
| Concurrency | One short-lived connection per request, opened `check_same_thread=False`; no pooling. The request-scoped invariant is documented in `app/db.py` and the suite carries `concurrent_requests` |
| Backup / replication / HA | **None.** Deleting the file is the accepted recovery |

### Verified SQLite capabilities relevant to analytics work

Confirmed available in the bundled 3.53.4 library, so no new dependency is
needed for aggregate work:

| Capability | Verified |
|---|---|
| `json_extract(...)` (JSON1) | yes — `select json_extract('{"a":1}','$.a')` → `1` |
| `strftime('%Y-%m-%d', <ts>)` | yes — works directly on the stored ISO-8601-Z string |
| `CHECK` constraint enforcement | yes — the `label` domain is enforced by the DDL |
| `ALTER TABLE … ADD COLUMN` | yes — used by the migration |
| Window functions / `GROUP BY` aggregate | available in 3.53.4; `GROUP BY` is now exercised by the `/v2` summary |

The stored `created_at` encoding (ISO 8601 UTC ending in `Z`) means a date range
filter is a plain string comparison — lexicographic order equals chronological
order, so no date parsing is required.

## Tooling Configuration

All four tool config blocks live in `pyproject.toml`. There is no separate
config file for any of them.

### `pytest`

| Setting | Value | Effect |
|---|---|---|
| `testpaths` | `["tests"]` | The suite is the whole test surface |
| `addopts` | `-q --cov=app --cov-report=term-missing --cov-fail-under=80` | **Coverage is applied to every run**, not only to a run that remembers to ask for it |
| `filterwarnings` | `["error"]` | A FastAPI or pydantic deprecation is a **hard suite failure** — the project's only mechanical deprecation canary |

### `coverage`

| Setting | Value | Effect |
|---|---|---|
| `source` | `["app"]` | Measures the **whole application**, including the never-imported live client — the expensive, affirmed reading |
| `fail_under` | `80` | The floor is an input, never lowered to make a step pass |
| `show_missing` | `true` | Uncovered lines are visible, which is how the two transport gaps were located |

### `ruff`

| Setting | Value | Effect |
|---|---|---|
| `line-length` | `100` | |
| `target-version` | `"py311"` | Matches `requires-python` |
| `lint.select` | `["E","F","W","I","N","UP","S","B","C4","SIM"]` | An **explicit, reviewed selection** rather than a tool default that drifts between releases. `S` is the security set (secrets in code, unsafe calls, weak hashing) |
| `lint.flake8-bugbear.extend-immutable-calls` | `["fastapi.Depends", "fastapi.Query"]` | FastAPI's argument-default markers are documented escape hatches, not bugs — B008 is silenced by configuration, not by a `# noqa` |
| `lint.per-file-ignores` for `tests/*` | `["S101","S105","S106","S603","S607"]` | Tests assert by construction, hold obviously-fake fixture credentials, and shell out to `git`. The security rules apply **in full to `app/`** |
| `format.quote-style` / `format.line-ending` | `"double"` / `"lf"` | |

## Measured Baseline at This Commit

Independently re-measured during this synthesis, not carried over from the scan.

| Measure | Value |
|---|---|
| Tests | **192 passed**, 0 failed, 0 skipped |
| Line coverage over `app/` | **97.06%** — 884 statements, 26 missed — against the 80% floor |
| `ruff check app tests` | *All checks passed!* |
| `ruff format --check app tests` | *30 files already formatted* |
| Interpreter used | CPython 3.14.7 on linux |

Per-module coverage detail and the full debt register are in
**code-quality-assessment.md**.

## Supply Chain Posture

Dependencies are declared as **floors, not pins**. There is no lockfile, no
hash pinning, no constraints file, no `requirements.txt`, and no remote. Each
install resolves the newest compatible version of roughly a dozen transitive
packages, so the exact versions in the tables above are what *this* environment
holds, not what any other install would get.

There is no audit command, no update bot, and no automatic patch path. The
mitigating property is the small surface: two direct runtime dependencies, one of
which (`uvicorn`) is the only one that parses untrusted input, and the
dependency cap keeps that surface from growing without an explicit requirement
change. There is also **no secret scanner and no dependency audit** today, and no
lockfile; adding the scanners (with the fake-key test fixtures allowlisted) and a
hashed lockfile is the active intent's packaging half.

The full dependency adjacency — including the internal module-level import graph
and its acyclicity — is in **dependencies.md**.