# Technology Stack — `very-cool-sentiment-analysis`

> Versions are the ones actually installed in `./.venv` (read from
> `*.dist-info` directory metadata by the developer scan) plus the declared
> floors in `pyproject.toml`. Nothing here is guessed; where only a declaration
> exists it is labelled "declared".

## Languages and Runtimes

| Layer | Technology | Version | Evidence |
|---|---|---|---|
| Application language | Python | `requires-python = ">=3.11"` (declared) | `pyproject.toml` |
| Development/runtime interpreter in this checkout | CPython | 3.14.7 | `.venv/bin/python -V`, `.venv/lib/python3.14/` |
| Front-end language | Vanilla JavaScript (ES2020-era, no transpile step) | n/a | `app/static/app.js` |
| Markup/styling | HTML5 + inline CSS in one document | n/a | `app/static/index.html` (styles in a `<style>` block in the head) |
| Persistence language | SQL (SQLite dialect, stdlib `sqlite3`) | SQLite as shipped with CPython 3.14.7 | `app/db.py`, `data/sentiment.db` |
| Shell/build glue | none (no Makefile, no scripts directory) | n/a | repo root listing |

## Frameworks and Libraries — Runtime

| Package | Declared | Installed (venv) | Role in this codebase |
|---|---|---|---|
| `fastapi` | `>=0.110` | 0.141.1 | ASGI app, `APIRouter`, `Depends`, `Query`, `RequestValidationError`, `StaticFiles`, `JSONResponse`/`RedirectResponse`/`HTMLResponse`; accepts a plain dataclass as the request body |
| `uvicorn` | `>=0.27` | 0.54.0 | Development ASGI server (`uvicorn app:app --reload`); **not imported** by any module |
| `starlette` (transitive) | — | 1.7.0 | Underlying ASGI toolkit: responses, lifespan, static files |
| `pydantic` (transitive) | — | 2.13.5 | Used **only inside FastAPI** for request validation; `app/` never imports it (NFR3) |
| `pydantic_core` (transitive) | — | 2.46.5 | Pydantic's native core |
| `anyio` (transitive) | — | 4.15.1 | Async/threadpool plumbing behind Starlette — the thread pool that runs the sync endpoints |
| `annotated_types`, `annotated_doc`, `typing_extensions`, `typing_inspection` (transitive) | — | 0.8.0, 0.0.5, 4.16.0, 0.4.4 | FastAPI/pydantic typing support |
| `click` (transitive) | — | 8.5.0 | uvicorn's CLI |
| `h11` (transitive) | — | 0.16.0 | HTTP/1.1 parsing for uvicorn |
| `idna` (transitive) | — | 3.20 | IDNA encoding for h11/`urllib` |

Runtime dependency count beyond the standard library: **2 direct**
(`fastapi`, `uvicorn`). This is the "dependency light" constraint (NFR3) and it
holds at the manifest level.

## Frameworks and Libraries — Development

| Package | Declared | Installed | Role |
|---|---|---|---|
| `pytest` | `>=8` (extra `dev`) | 9.1.1 | Test framework and runner; configured in `pyproject.toml` |
| `pluggy` (transitive) | — | 1.6.0 | pytest plugin core |
| `iniconfig` (transitive) | — | 2.3.0 | INI parsing for pytest |
| `packaging` (transitive) | — | 26.3 | Version handling |
| `pygments` (transitive) | — | 2.21.0 | Terminal colouring in pytest output |
| `pip` | — | 26.2.1 | Toolchain only (editable install of the project) |

## Standard-Library Modules the Application Relies On

From the import graph of `app/*.py`:

| Area | Modules |
|---|---|
| Configuration | `tomllib` (parses `config.local.toml`) |
| Persistence | `sqlite3` (no ORM, no SQLAlchemy, no Alembic) |
| HTTP transport (outbound) | `urllib.request`, `urllib.error`, `urllib.parse` |
| PKCE / credentials | `hashlib` (SHA-256), `base64` (urlsafe, unpadded), `secrets` (`token_urlsafe(64)`) |
| Concurrency | `threading` (one lock in the session store) |
| Serialisation | `json` |
| Structure | `dataclasses`, `pathlib`, `typing` (`Protocol`, `runtime_checkable`, `TYPE_CHECKING`), `__future__.annotations` |
| Runtime plumbing | `logging`, `contextlib.asynccontextmanager`, `collections.abc`, `datetime`, `time`, `re` |
| Tests | `socket` (monkeypatched by the offline guard), `asyncio` (drives the in-process ASGI call), `json` |

## Build and Packaging

| Aspect | Choice | Evidence |
|---|---|---|
| Build backend | `setuptools>=68` via PEP 517 (`build-backend = "setuptools.build_meta"`) | `pyproject.toml` |
| Manifest | PEP 621 metadata in `pyproject.toml` | `pyproject.toml` |
| Package layout | Flat: `packages = ["app"]`; static assets shipped as package data | `pyproject.toml` |
| Install command | `python -m pip install -e ".[dev]"` | `README.md` |
| Lockfile | none (floors only) | repo root listing |
| Task runner | none (bare `pytest`, bare `uvicorn`) | `README.md`, `pyproject.toml` |
| Generated metadata present | `very_cool_sentiment_analysis.egg-info/` — **stale**, embeds an older README and omits `session_auth.py` and the two auth test modules | `very_cool_sentiment_analysis.egg-info/PKG-INFO`, `SOURCES.txt` |

## Front End

- One static document plus one script, served verbatim:
  `GET /` returns `app/static/index.html` from disk on every request
  (`app/routes.py:83-87`), and `/static/*` is a `StaticFiles` mount
  (`app/main.py:91`).
- No framework, no bundler, no npm dependency, no build artifact.
- Browser APIs used: `fetch` (paths `/analyze`, `/analyses?limit=50`,
  `/auth/status`, `/auth/openrouter/start`, `/auth/disconnect`),
  `document.querySelector`, `<template>` cloning and `setInterval` (20 s
  indicator poll); no other browser API and no client-side state store.
- The script never computes a label, probability or intensity — it renders only
  values the API returned (`app/static/app.js:1-6,48-78`).

## Data Storage

| Aspect | Value | Evidence |
|---|---|---|
| Engine | SQLite via stdlib `sqlite3` | `app/db.py:3,51-63` |
| File | `data/sentiment.db` (gitignored, untracked, 12 rows at scan time) | `.gitignore` (`/data/`), `data/sentiment.db` |
| Tables | `analyses` (8 columns + autoincrement `id`), `schema_meta` (`key`,`value`), plus SQLite's `sqlite_sequence` | `app/db.py:18-36,66-83`; inspected read-only |
| Schema version | `SCHEMA_VERSION = 1`, written to `schema_meta.version` once (`ON CONFLICT DO NOTHING`) and never read back | `app/db.py:14,74-83` |
| Migration tooling | none — only `CREATE TABLE IF NOT EXISTS` | `app/db.py:66-83` |

## External Services

| Service | Endpoint | Used by | Protocol |
|---|---|---|---|
| OpenRouter Decisions API | `https://openrouter.ai/api/alpha/decisions` | Live OpenRouter Engine | HTTPS + JSON, `Authorization: Bearer <key>`, 30 s timeout |
| OpenRouter key exchange | `https://openrouter.ai/api/v1/auth/keys` | Session Authorization | HTTPS + JSON, 30 s timeout |
| OpenRouter authorization page | `https://openrouter.ai/auth` | Session Authorization (browser redirect only) | HTTPS |

No cloud SDK, no AWS service, no message broker, no cache server, no reverse
proxy and no container runtime is used anywhere in the repository.

## Tooling Deliberately Absent

Verified absent from the repository root and `pyproject.toml`:

- linters/formatters/type checkers: no `ruff`, `flake8`, `pylint`, `mypy`,
  `black`, `isort`, no `.pre-commit-config.yaml`, no `setup.cfg`/`tox.ini`
- CI/CD: no `.github/`, no `.gitlab-ci.yml`, no Jenkinsfile, no pipeline config
- coverage: no `pytest-cov`, no `[tool.coverage]`, no coverage floor
- containers/infra: no Dockerfile, no compose file, no Kubernetes manifests
- HTTP client library: no `requests`, no `httpx` — deliberately excluded, which
  is why the test harness hand-rolls its ASGI caller
  (`tests/conftest.py:5-9`)

The only mechanical quality gate in the project is
`filterwarnings = ["error"]` in `[tool.pytest.ini_options]`.
