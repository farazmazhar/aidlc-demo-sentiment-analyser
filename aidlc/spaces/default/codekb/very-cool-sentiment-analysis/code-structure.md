# Code Structure — `very-cool-sentiment-analysis`

> Derived from the developer scan
> (`inception/reverse-engineering/developer-scan.md`) and verified by reading the
> modules. All paths are repo-relative; line counts are the current working-tree
> counts.

## Repository Layout

```
.
+-- pyproject.toml                     # PEP 621 metadata, dependency cap, pytest config
+-- config.example.toml                # committed placeholder config (never a secret)
+-- README.md                          # setup, run, test, modes, full HTTP surface
+-- AGENTS.md                          # AI-DLC harness onboarding for this repo
+-- .gitignore                         # ignores /data/, .venv/, *.egg-info/, .pytest_cache/
+-- app/                               # THE APPLICATION PACKAGE
|   +-- __init__.py                    # re-exports `app` so `uvicorn app:app` resolves
|   +-- main.py                        # create_app() factory, lifespan, static mount
|   +-- config.py                      # Settings + load_settings() (mode resolution)
|   +-- models.py                      # AnalyzeRequest, AnalysisRecord, RECORD_FIELDS
|   +-- db.py                          # sqlite3 connect + idempotent schema init
|   +-- repository.py                  # insert_analysis(), list_analyses()
|   +-- sentiment.py                   # LABELS, SentimentResult, SentimentClient protocol
|   +-- dummy_client.py                # offline keyword engine (default)
|   +-- openrouter_client.py           # live Jev engine (never exercised by tests)
|   +-- session_auth.py                # in-app OpenRouter PKCE flow (memory only)
|   +-- service.py                     # analyze_text(), get_client(), effective_connection()
|   +-- routes.py                      # page + API + auth routes + error envelope
|   +-- static/
|       +-- index.html                 # the single page and the connection indicator
|       +-- app.js                     # fetch(), rendering, history, indicator polling
+-- tests/                             # TEST SUITE (10 files, 52 test functions)
|   +-- conftest.py                    # in-process ASGI caller, offline guard, tmp fixtures
|   +-- test_config.py  test_db.py  test_repository.py  test_dummy_client.py
|   +-- test_service.py  test_routes.py  test_page.py
|   +-- test_session_auth.py  test_auth_routes.py
+-- very_cool_sentiment_analysis.egg-info/   # GENERATED, stale (see below)
+-- data/sentiment.db                  # RUNTIME, gitignored, untracked, 12 rows
+-- .venv/ .pytest_cache/              # local tooling state (not application code)
+-- .omp/ aidlc/                       # AI-DLC harness and workspace record (not application code)
```

## File Classification

| Class | Files | Tracked | Notes |
|---|---|---|---|
| Application modules | `app/*.py` (12 files, 1 498 lines) | yes | `[tool.setuptools] packages = ["app"]` (`pyproject.toml`) |
| Static assets | `app/static/index.html` (185), `app/static/app.js` (175) | yes | shipped as package data: `[tool.setuptools.package-data] app = ["static/*"]` |
| Tests | `tests/*.py` (10 files, 1 407 lines) | yes | not a declared distributable package |
| Build/manifest | `pyproject.toml`, `config.example.toml`, `.gitignore` | yes | no `setup.py`, no lockfile, no `requirements.txt`, no Makefile |
| Documentation | `README.md` (189), `AGENTS.md` (59) | yes | README is also the packaging long-description (`PKG-INFO`) |
| Generated metadata | `very_cool_sentiment_analysis.egg-info/*` | no (`*.egg-info/` ignored) | **stale**: `PKG-INFO` embeds an older README, `SOURCES.txt` omits `session_auth.py` and the two auth test modules |
| Runtime state | `data/sentiment.db` (12 rows, schema version 1) | no (`/data/` ignored) | created by the app; no migration mechanism |
| Tooling state | `.pytest_cache/`, `app/__pycache__/`, `tests/__pycache__/` | no | `.pytest_cache/v/cache/lastfailed` held `{}` at scan time |
| Harness / workspace | `.omp/`, `aidlc/`, `.aidlc/` | mixed | AI-DLC scaffolding and record tree — **not** application code |

## Module Organisation and Sizes

| Module | Lines | Single responsibility (from its own docstring) | Cited requirement ids |
|---|---|---|---|
| `app/__init__.py` | 10 | Re-export the ASGI app so `uvicorn app:app` resolves | `FR5.1`, `A2` |
| `app/main.py` | 101 | Assemble the application: settings, schema init, log once, mount routes and static | `FR1.4`, `FR1.5`, `FR3.2`, `FR4.7`, `FR5.1`, `NFR4` |
| `app/config.py` | 125 | Decide which engine runs and where the database lives; hold the key; redact it | `FR1.1`–`FR1.6`, `NFR1`, `NFR2` |
| `app/models.py` | 94 | Pin the wire and storage shape of one analysis in one place | `FR4.5`, `FR3.3`, `NFR3` |
| `app/db.py` | 83 | Own the shape and lifecycle of the local database file | `FR3.1`, `FR3.2`, `NFR6` |
| `app/repository.py` | 80 | Translate between the sentiment result and `analyses` rows, read back | `FR3.3`, `FR3.4`, `NFR5` |
| `app/sentiment.py` | 61 | Define what a sentiment engine is (the one seam) | `FR2.1`, `FR2.5`, `FR2.7`, `NFR5` |
| `app/dummy_client.py` | 106 | Produce a deterministic decision with no network, no key, no state | `FR2.2`, `FR2.5`, `FR2.7`, `NFR1` |
| `app/openrouter_client.py` | 250 | Turn text into a typed result via the OpenRouter Decisions API; never guess | `FR2.3`–`FR2.7`, `NFR3`, `FR5.5` |
| `app/session_auth.py` | 263 | In-app OpenRouter PKCE authorization, session-scoped, memory only | (no FR id in the docstring; introduced after the prior intent) |
| `app/service.py` | 104 | Turn submitted text into a persisted analysis; choose the engine | `FR4.3`, `FR3.3`, `FR2.1`, `NFR5` |
| `app/routes.py` | 221 | The HTTP surface: one page, one analysis API, one health endpoint, the auth routes, one error envelope | `FR4.1`–`FR4.6` (plus the auth routes) |

Total application code: **1 498 lines** across `app/*.py`; **360 lines** of static
assets; **1 407 lines** of tests.

## Internal Dependency Graph (no cycles)

```
app/__init__ ----> app/main
app/main -------> app/config, app/db, app/routes, app/service, app/sentiment, app/session_auth
app/routes -----> app/db, app/config, app/models, app/repository, app/service,
                  app/sentiment, app/session_auth
app/service ----> app/config, app/dummy_client, app/models, app/repository,
                  app/sentiment, app/session_auth, (lazily) app/openrouter_client
app/repository -> app/models   (+ app/sentiment under TYPE_CHECKING only)
app/dummy_client, app/openrouter_client ----> app/sentiment
app/db, app/models, app/config, app/sentiment ----> nothing internal (leaves)
```

One direction only: nothing that a module imports imports it back, and the two
engines depend on the interface rather than the reverse (`app/service.py:60-82`).

## Code Patterns in Use

| Pattern | Where | Why it matters for a change |
|---|---|---|
| **Port + adapter (strategy)** | `SentimentClient` Protocol (`app/sentiment.py:56-61`); the two clients implement it | A new engine is added by implementing one method and widening the mode list — routes, repository and page stay untouched |
| **Factory** | `create_app(settings=None, session_auth=None)` (`app/main.py:53-101`) | Tests inject temp settings and a session-store double; production builds `app` at import time |
| **Lifespan initialisation** | `@asynccontextmanager lifespan` calls `db.init_db()` and logs the mode once (`app/main.py:65-77`) | First-run readiness lives here; nothing else creates the schema |
| **Dependency injection (framework-level)** | `Depends(get_settings)`, `Depends(get_connection)` (`app/routes.py:60-76`) | One short-lived SQLite connection per request; the settings object is shared read-only state |
| **Repository** | `insert_analysis()` / `list_analyses()` (`app/repository.py:38-80`) | Callers never write SQL; the stored row is read back before returning |
| **Parameterised SQL only** | `_INSERT_SQL` and the `SELECT` statements (`app/repository.py:26-31,51-68`) | No string interpolation anywhere in `app/db.py` or `app/repository.py` |
| **DTO / record mapping** | `AnalyzeRequest`, `AnalysisRecord.to_dict()/from_row()` (`app/models.py:34-93`) | One field list feeds both the wire and the row; the encodings (JSON object, `Z` timestamp) are pinned here |
| **Single error envelope + exception handlers** | `error_response()` and four handlers wired in `create_app` (`app/routes.py:41-57`, `app/main.py:93-96`) | New failure modes must reuse the envelope or the tests and page break |
| **Lazy import as a test seam** | `from app.openrouter_client import OpenRouterClient` inside `get_client()` (`app/service.py:80-82`) | The offline path and the whole test suite never load the live client |
| **Injected seams for determinism** | a `now` parameter in `insert_analysis` (`app/repository.py:38-49`); `exchanger`/`clock` in `SessionAuth.__init__` (`app/session_auth.py:148-160`) | Timestamps and the PKCE exchange are deterministic in tests |
| **Redaction by construction** | `Settings.__repr__`, `SessionCredential.__repr__`, `OpenRouterClient.__repr__` (`app/config.py:47-52`, `app/session_auth.py:131-138`, `app/openrouter_client.py:93-95`) | Any new object holding a secret must redact it the same way |
| **Lock-protected mutable state** | `threading.Lock` around the pending-verifier map and the credential (`app/session_auth.py:141-263`) | FastAPI runs sync endpoints in a thread pool; the store is the only shared mutable state |
| **Typed answer reading, never free-text parsing** | `_read_choice()` / `_read_score()` (`app/openrouter_client.py:194-250`) | The live engine raises rather than inventing a label |
| **Class-less module functions for pure helpers** | `format_timestamp()`, `create_code_verifier()`, `code_challenge_for()` | Pure helpers stay testable without a fixture |

## Conventions Observed

- **Every module** starts with a `"""…"""` docstring naming its single
  responsibility and the requirement ids it satisfies.
- `from __future__ import annotations` and type annotations on every public and
  private function (`app/*.py`).
- Module-level constants in `UPPER_CASE` and documented with `#:` comments
  (e.g. `app/db.py:37-48`, `app/session_auth.py:40-56`).
- Private helpers and state are underscore-prefixed (`_read_choice`,
  `_pending`, `_drop_expired_pending`).
- Errors are domain exceptions (`ConfigError`, `InvalidTextError`,
  `SentimentEngineError`, `SentimentAuthError`, `AuthExchangeError`), mapped to
  HTTP only in `app/routes.py`.
- Tests are named `test_<module>.py` per production module, with a shared
  `conftest.py`; there is no test for `app/openrouter_client.py`.

## Non-Application Trees (do not mistake for the codebase)

The workspace also holds `.venv/` (installed distribution metadata only was
read to pin versions), `.omp/` (35 harness skills, 14 agent definitions, one
adapter extension), `aidlc/` (workspace memory, the prior intent record, this
intent's record, an empty `codekb/`, audit and engine state), `.git/` and
`.pytest_cache/`. The developer scan classified all of these as harness or
runtime state, not application code.
