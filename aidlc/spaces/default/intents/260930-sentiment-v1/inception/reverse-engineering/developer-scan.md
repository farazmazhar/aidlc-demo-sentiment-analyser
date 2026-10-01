# Reverse Engineering — Developer Code Scan (repo `very-cool-sentiment-analysis`)

- Workspace root / repo root: `/mnt/hdd/Compiler/work/aws-aidlc-eval-project/very-cool-sentiment-analysis` (`./` IS the codebase; the application lives in `./app`).
- Scan date: 2026-09-30. Mode: FULL rescan (NO_STORE — no prior CodeKB store exists; `aidlc/spaces/default/codekb/` is empty).
- Repo HEAD at scan time: `5b328fc96766679e98f3fc4effc39198a2811744` ("v1-classic: FastAPI + SQLite sentiment analysis app with AI-DLC record"). Read-only scan: no file outside this handoff was written, and no build, linter, or test suite was executed.
- Every fact below was read out of the files listed under *Analyzed deeply*; the traceability of each claim is the file path next to it.

## Developer Code Scan Results

### Scan Coverage

- **Analyzed deeply** (read in full and understood, repo-relative, all within `./`):
  - `app/` (whole package): `app/__init__.py`, `app/main.py`, `app/config.py`, `app/models.py`, `app/db.py`, `app/repository.py`, `app/sentiment.py`, `app/dummy_client.py`, `app/openrouter_client.py`, `app/service.py`, `app/session_auth.py`, `app/routes.py`
  - `app/static/` : `app/static/index.html`, `app/static/app.js`
  - `tests/` (whole suite): `tests/conftest.py`, `tests/test_config.py`, `tests/test_db.py`, `tests/test_repository.py`, `tests/test_dummy_client.py`, `tests/test_service.py`, `tests/test_routes.py`, `tests/test_page.py`, `tests/test_session_auth.py`, `tests/test_auth_routes.py`
  - Build/config/docs: `pyproject.toml`, `config.example.toml`, `.gitignore`, `README.md`, `AGENTS.md`
  - Generated metadata: `very_cool_sentiment_analysis.egg-info/{PKG-INFO,requires.txt,SOURCES.txt,top_level.txt}`
  - Runtime artifact: `data/sentiment.db` (opened read-only with `sqlite3`: tables `analyses`, `sqlite_sequence`, `schema_meta`; 12 rows in `analyses`; the file is untracked — `/data/` is gitignored)
  - Test-run state: `.pytest_cache/v/cache/lastfailed` (`{}` — no recorded failing test from the last run) and `.pytest_cache/v/cache/nodeids` (present; not used as behaviour evidence)
  - Intent/record context read for framing only: `aidlc/spaces/default/intents/260930-sentiment-v1/project-description.json`, `aidlc/spaces/default/intents/260929-sentiment-analysis/inception/requirements-analysis/requirements.md` (the FR/NFR ids the code cites in its docstrings), `aidlc/spaces/default/intents/260930-sentiment-v1/inception/reverse-engineering/memory.md` (template only, no entries)
- **Skimmed only** (noted at directory granularity, not read in depth):
  - `.venv/` — only the installed distribution metadata was listed to pin versions (`fastapi`, `uvicorn`, `pytest`, `pydantic`, `starlette`, `anyio`, `click`, `h11`, `idna`, `typing_extensions`); no site-packages source was read
  - `.omp/` — harness scaffolding (35 `skills/*/SKILL.md`, 14 `agents/*.md`, `extensions/aidlc-omp-adapter.ts`); this is the AI-DLC harness, not application code
  - `aidlc/` — AI-DLC workspace (memory rules, prior intent record `260929-sentiment-analysis/`, this intent's `260930-sentiment-v1/`, empty `codekb/`, `.aidlc-sessions/`, `intents.json`); read only for the rule bundle and the prior intent's requirements, otherwise skimmed
  - `.pytest_cache/` (beyond the two cache files above), `.git/`, `aidlc/spaces/default/intents/*/.aidlc-engine/` (framework runtime state)

### Packages Found

| Package | Type | Language | Purpose |
|---|---|---|---|
| `app` | Application package (declared in `pyproject.toml` → `[tool.setuptools] packages = ["app"]`) | Python 3.11+ (dev venv is CPython 3.14.7) | The entire application: settings/mode resolution, SQLite schema + access, sentiment-engine interface and its two implementations, orchestration, HTTP routes, static page |
| `tests` | Test suite (not a declared distributable package; imported as `tests.conftest`) | Python | 9 test modules + 1 `conftest.py`, 52 test functions, hand-rolled in-process ASGI harness |
| `very_cool_sentiment_analysis.egg-info` | Generated setuptools metadata for the editable install | — | `PKG-INFO`, `SOURCES.txt`, `requires.txt`, `top_level.txt`; **stale** (see Technical Debt) |
| `data` | Runtime data directory (gitignored) | — | Holds the single SQLite DB `data/sentiment.db` |
| `.omp`, `aidlc` | Not application code | — | Harness scaffolding and the AI-DLC workspace/record tree |

Module-by-module purpose (from module docstrings and code, `app/`):

- `app/__init__.py` (10 lines) — re-exports the ASGI app so `uvicorn app:app` resolves from the repo root.
- `app/main.py` (101) — `create_app(settings=None, session_auth=None)` factory, lifespan (loads settings, calls `db.init_db`, logs the active mode once), route + static mounting, exception-handler wiring; module-level `app = create_app()`; `HOST = "127.0.0.1"`, `PORT = 8000` (lines 35-36).
- `app/config.py` (125) — frozen `Settings` dataclass with key-redacting `__repr__`, `ConfigError`, `load_settings(config_path, db_path)` implementing 6 ordered resolution rules (lines 73-125); `DEFAULT_MODE="dummy"`, `DEFAULT_MODEL="typesafe/jev-1.13"`, `DEFAULT_CONFIG_PATH=Path("config.local.toml")`, `DEFAULT_DB_PATH=Path("data/sentiment.db")`.
- `app/models.py` (94) — `AnalyzeRequest` (request body, plain dataclass), `AnalysisRecord` with `to_dict()` / `from_row()`, `RECORD_FIELDS` (9 pinned fields).
- `app/db.py` (83) — `connect()` (mkdir parent, `sqlite3.Row`, `PRAGMA foreign_keys = ON`), `init_db()` (idempotent `CREATE TABLE IF NOT EXISTS` for `analyses` + `schema_meta`, version row), `SCHEMA_VERSION = 1`, `ANALYSES_COLUMNS`, `CREATE_ANALYSES_TABLE` (label CHECK constraint).
- `app/repository.py` (80) — `insert_analysis()` (parameterised INSERT + read-back of the stored row), `list_analyses(limit=50)` (`ORDER BY id DESC LIMIT ?`), `format_timestamp()` (ISO 8601 UTC ending in `Z`), `DEFAULT_LIST_LIMIT = 50`.
- `app/sentiment.py` (61) — `LABELS = ("positive","negative","neutral")`, frozen `SentimentResult`, `SentimentEngineError`, `SentimentAuthError`, `@runtime_checkable` `SentimentClient` Protocol with a single `analyze(text) -> SentimentResult`.
- `app/dummy_client.py` (106) — `DummyClient`: keyword counting over 15 positive / 14 negative words, fixed per-label probability triples (`LABEL_PROBABILITIES`), fixed signed intensity (`INTENSITY_BY_LABEL`), `MODEL="dummy-keyword-v1"`, `PROVIDER="local-dummy"`; no network, no key, deterministic.
- `app/openrouter_client.py` (250) — `OpenRouterClient`: POSTs the OpenRouter **Decisions** API with a `choice` question (`sentiment`) plus a `score` question (`intensity`), reads only the typed fields, raises `SentimentEngineError` / `SentimentAuthError` (401/403) instead of guessing; stdlib `urllib` only; key redacted in `__repr__`.
- `app/session_auth.py` (263) — in-app OpenRouter **PKCE (S256) authorization** flow; `SessionAuth` store (thread-locked) holding a `SessionCredential` in process memory only, `start()`, `complete()`, `expire()`, `disconnect()`, 600 s pending-verifier TTL; the only outbound call is `exchange_code_at_openrouter()` to `https://openrouter.ai/api/v1/auth/keys`.
- `app/service.py` (104) — `InvalidTextError`, `effective_connection()` (credential-vs-config precedence, returns `connected/source/mode/model/reason`), `get_client()` (the only place a concrete client is chosen), `analyze_text()` (strip → reject empty → engine → persist).
- `app/routes.py` (221) — the HTTP surface and the single error envelope `{"error": {code, message, details}}`; 8 routes; `get_connection()` per-request SQLite dependency.
- `app/static/index.html` (185) / `app/static/app.js` (175) — one page: submit form, result panel, error panel, history list, and a fixed-position OpenRouter connection indicator (red = dummy engine, green = connected); `fetch()` calls to `/analyze`, `/analyses?limit=50`, `/auth/status`, `/auth/openrouter/start`, `/auth/disconnect`.

### Build System

- **Type**: PEP 517/518 build via **setuptools** (`[build-system] requires = ["setuptools>=68"]`, `build-backend = "setuptools.build_meta"`), configured entirely in `pyproject.toml`. No `setup.py`, no lockfile, no `requirements.txt`, no Makefile, no task runner.
- **Config Files**: `pyproject.toml` (project metadata, dependency cap, setuptools package + package-data, `[tool.pytest.ini_options]`); `config.example.toml` (committed placeholder app config); `.gitignore`.
  - `[project]`: name `very-cool-sentiment-analysis`, version `0.1.0`, `requires-python = ">=3.11"`, `dependencies = ["fastapi>=0.110", "uvicorn>=0.27"]`, optional extra `dev = ["pytest>=8"]`.
  - `[tool.setuptools] packages = ["app"]`; `[tool.setuptools.package-data] app = ["static/*"]` (the page ships with the package).
  - `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `addopts = "-q"`, `filterwarnings = ["error"]`.
- **Build Dependencies** (installed in the local venv, read from `*.dist-info` directory names): `fastapi 0.141.1` → `starlette 1.7.0`, `pydantic 2.13.5`, `pydantic_core 2.46.5`, `anyio 4.15.1`, `annotated_types 0.8.0`, `annotated_doc 0.0.5`, `typing_extensions 4.16.0`, `typing_inspection`; `uvicorn 0.54.0` → `click 8.5.0`, `h11 0.16.0`, `idna 3.20`; `pytest 9.1.1` → `pluggy 1.6.0`, `iniconfig`, `packaging`, `pygments`. `httpx` is deliberately absent (see Test Coverage). Runtime size of the declared set: **2 runtime + 1 dev** direct packages — the "dependency-light" constraint holds at the manifest level.
- **Build Dependencies (package → package)**: `app` depends on `fastapi` (routing, ASGI, `StaticFiles`, exception handler types), `uvicorn` (dev server only — not imported by any module), `pytest` (tests only), and the stdlib (`tomllib`, `sqlite3`, `urllib`, `json`, `hashlib`, `secrets`, `threading`, `logging`, `dataclasses`, `pathlib`). No module imports `pydantic` directly — `app/models.py` uses a plain dataclass on purpose (NFR3 comment at `app/models.py:8-11`).
- **Run/test commands found** (`README.md`): `python -m venv .venv && source .venv/bin/activate && python -m pip install -e ".[dev]"`; dev `uvicorn app:app --reload`; tests `pytest` (bare) or `python -m pytest tests -q`.

### APIs Discovered

**A. Internal HTTP surface — FastAPI, `app/routes.py` (`router = APIRouter()`, mounted in `app/main.py:90`), plus one static mount** — 8 routes total:

| Method | Path | Handler (line) | Contract |
|---|---|---|---|
| GET | `/` | `index` (82) | Serves `app/static/index.html` as `text/html` (FR4.1/FR4.2) |
| POST | `/analyze` | `post_analyze` (88) | Body `AnalyzeRequest{text}` → `200` with the stored `AnalysisRecord`; empty/whitespace-only text → `422 INVALID_TEXT` with nothing written |
| GET | `/analyses` | `get_analyses` (101) | `?limit=` (`ge=1`, default 50) → `{"analyses": [...]}` newest-first; `limit=0/-1/abc` → `422 VALIDATION_FAILED` (`query.limit`) |
| GET | `/health` | `health` (112) | `{"status":"ok", connected, source, mode, model, reason}` — `mode` is the engine actually in use |
| GET | `/auth/status` | `auth_status` (128) | The indicator's data source: `effective_connection(...)` |
| GET | `/auth/openrouter/start` | `auth_start` (137) | `302` to OpenRouter's authorize URL with an S256 PKCE challenge |
| GET | `/auth/callback` | `auth_callback` (145) | `?code=` → exchanges the code, stores the key in memory, `302` to `/?auth=connected` or `/?auth=failed` |
| POST | `/auth/disconnect` | `auth_disconnect` (160) | Drops the session credential, returns the offline connection state |
| — | `/static/*` | `StaticFiles` mount (`app/main.py:91`) | Serves `app.js` (and any future asset) |

Error envelope (one shape for every non-2xx; `error_response()` at `app/routes.py:41-57`): `{"error": {"code", "message", "details": [{"field", "reason"}]}}` with codes `VALIDATION_FAILED` (422), `INVALID_TEXT` (422), `SENTIMENT_ENGINE_ERROR` (502), `AUTH_EXPIRED` (502). Handlers are registered in `app/main.py:93-96`.

**B. External service calls** — 3, all to OpenRouter, all stdlib `urllib`, all bearing the API key as `Authorization: Bearer <key>`:

1. `POST https://openrouter.ai/api/alpha/decisions` — `app/openrouter_client.py:30` (`ENDPOINT`), request built at `_post_decisions()` (122-189); payload `{model, state:{text}, questions:{sentiment: choice, intensity: score}}`; typed answers read by `_read_choice()` (193-229) and `_read_score()` (231-250); HTTP 401/403 → `SentimentAuthError`, other failures → `SentimentEngineError`; 30 s timeout.
2. `POST https://openrouter.ai/api/v1/auth/keys` — `app/session_auth.py:41` (`EXCHANGE_ENDPOINT`), called only from `exchange_code_at_openrouter()` (78-121); body `{code, code_verifier, code_challenge_method}`; expects `{"key": "..."}`; 30 s timeout.
3. `GET https://openrouter.ai/auth` — `app/session_auth.py:40` (`AUTHORIZE_ENDPOINT`), the browser redirect target built by `SessionAuth.start()` (163-180) with `callback_url`, `code_challenge`, `code_challenge_method=S256`, `key_label`.

**C. Internal Python API (module contracts other modules depend on)**:

- `app.sentiment` — `SentimentClient` Protocol (`analyze(text) -> SentimentResult`), `SentimentResult(label, probabilities, confidence, intensity, model, provider)`, `LABELS`, `SentimentEngineError`, `SentimentAuthError`. This is the single seam every engine sits behind (swapped only in `app/service.py:60-82`).
- `app.config` — `Settings`, `load_settings()`, `ConfigError`, `MODES`, `REDACTED`, defaults.
- `app.db` — `connect()`, `init_db()`, `SCHEMA_VERSION`, `ANALYSES_COLUMNS`.
- `app.repository` — `insert_analysis()`, `list_analyses()`, `format_timestamp()`, `DEFAULT_LIST_LIMIT`.
- `app.service` — `analyze_text()`, `get_client()`, `effective_connection()`, `InvalidTextError`.
- `app.models` — `AnalyzeRequest`, `AnalysisRecord.to_dict()/from_row()`, `RECORD_FIELDS`.
- `app.session_auth` — `SessionAuth` (`start/complete/credential/reason/expire/disconnect`), `SessionCredential`, `AuthExchangeError`, `create_code_verifier()`, `code_challenge_for()`, `exchange_code_at_openrouter()`.
- `app.main` — `create_app()`, `app`, `HOST`, `PORT`.
- Cross-module call graph (no cycles, one direction): `main` → {`config`, `db`, `routes`, `service`, `sentiment`, `session_auth`}; `routes` → {`db`, `config`, `models`, `repository`, `service`, `sentiment`, `session_auth`}; `service` → {`config`, `dummy_client`, `models`, `repository`, `sentiment`, `session_auth`, lazily `openrouter_client`}; `repository` → {`models`} (+ `sentiment` under `TYPE_CHECKING` only); `{dummy_client, openrouter_client}` → {`sentiment`}; `db` and `models` depend on nothing internal.

**D. Data contract (one row, one JSON record)** — identical field set and order in `RECORD_FIELDS` (`app/models.py:20-30`), `ANALYSES_COLUMNS` (`app/db.py:38-48`) and `AnalysisRecord.to_dict()`: `id, text, label, probabilities, confidence, intensity, model, provider, created_at`. `probabilities` is a JSON object keyed by label; `label ∈ {positive, negative, neutral}` enforced by a SQL `CHECK`; `created_at` is ISO 8601 UTC ending in `Z`.

### Frameworks & Libraries

Versions are the ones actually installed in `./.venv` (`*.dist-info`) plus the declared floors in `pyproject.toml`; none are guessed.

| Name | Version (installed / declared) | Purpose |
|---|---|---|
| Python | 3.14.7 (venv) / `requires-python >=3.11` | Language runtime |
| FastAPI | 0.141.1 / `>=0.110` | ASGI app, routing, `StaticFiles`, exception handlers; plain dataclass accepted as request body |
| Starlette | 1.7.0 (transitive) | Underlying ASGI toolkit (responses, `JSONResponse`, lifespan) |
| pydantic | 2.13.5 (transitive) | Used **only** by FastAPI internally for request validation — never imported by `app/` |
| pydantic_core | 2.46.5 (transitive) | Pydantic's Rust core |
| anyio | 4.15.1 (transitive) | Async/threadpool plumbing used by Starlette |
| uvicorn | 0.54.0 / `>=0.27` | Dev ASGI server (`uvicorn app:app --reload`); not imported by app code |
| click | 8.5.0 (transitive) | uvicorn CLI |
| h11 | 0.16.0 (transitive) | HTTP/1.1 parsing for uvicorn |
| idna | 3.20 (transitive) | IDNA for h11/urllib |
| pytest | 9.1.1 / `>=8` (extra `dev`) | Test framework and runner config |
| sqlite3 | stdlib (Python 3.14.7) | Storage engine — no ORM, no SQLAlchemy, no Alembic |
| tomllib / urllib.request / hashlib / secrets / json / threading / base64 | stdlib | Config parsing, HTTP transport, PKCE (S256), credential generation, JSON encoding, thread-safe session store |

Not present anywhere: no HTTP client library (`requests`/`httpx`), no ORM/migration tool, no template engine (the page is served verbatim), no JS framework or bundler (vanilla `app.js`), no Docker/k8s artifact, no cloud SDK.

### Test Coverage

- **Test Directories**: `tests/` — sole test root (`testpaths = ["tests"]`), 10 files: `conftest.py` + `test_config.py` (7), `test_db.py` (2), `test_repository.py` (2), `test_dummy_client.py` (6), `test_service.py` (3), `test_routes.py` (6), `test_page.py` (2), `test_session_auth.py` (12), `test_auth_routes.py` (12) = **52 test functions**; 5 fixtures (`offline_guard` session/autouse, `tmp_settings`, `tmp_db_path` in `conftest.py`; per-file `app` fixtures in `test_routes.py` and `test_page.py`).
- **Test Frameworks**: `pytest` 9.1.1 only. No `pytest-cov`, no `pytest-asyncio`, no `unittest` suites, no `fastapi.testclient`.
  - `tests/conftest.py` (168 lines) supplies a **hand-rolled in-process ASGI caller** (`asgi_request()` builds a raw ASGI scope, enters the app's `lifespan_context`, collects messages) explicitly because `TestClient` would require `httpx`, which the dependency cap forbids (`conftest.py:5-9`).
  - A session-scoped autouse **`offline_guard`** monkeypatches `socket.socket.connect` to raise, so any accidental network use fails the run loudly (`conftest.py:129-146`).
  - `tmp_settings` / `tmp_db_path` point every test at a `tmp_path` DB, so no test reads the real `config.local.toml` or `data/sentiment.db` (`conftest.py:149-168`).
  - Assertions are made against values read back out of real SQLite (`test_repository.py`, `test_db.py`, `test_routes.py`, `test_service.py`) and against the served markup (`test_page.py`).
  - `test_config.py::test_local_config_is_gitignored` shells out to `git check-ignore`; `filterwarnings = ["error"]` turns any warning into a failure.
- **Coverage Config**: **absent** — no `[tool.coverage]`, no `--cov` in `addopts`, no coverage floor, no coverage dependency, no coverage badge. The only automated gate is `filterwarnings = ["error"]`.
- **What is not covered**: `app/openrouter_client.py` (250 lines) is never imported, constructed, or called by any test — the offline guard makes that structural, and the module docstring states it explicitly (`openrouter_client.py:10-12`; `README.md` "Notes"). The live insertion path through `repository.insert_analysis()` is exercised only with `SentimentResult` fakes injected by tests, and the browser-side execution of `app/static/app.js` is not executed at all — `test_page.py` asserts served markup and `data-testid` hooks only (page/assets contract level).
- Local run state at scan time: `.pytest_cache/v/cache/lastfailed` contains `{}` (no failing test recorded by the last run). No test was executed during this scan, so this is not a statement about today's suite health.

### Code Quality Indicators

- **Linting**: **absent**. No `ruff`, `flake8`, `pylint`, `mypy`, `black`, `isort`, or `pre-commit` configuration exists anywhere (`pyproject.toml` has no `[tool.ruff]`/`[tool.mypy]`/`[tool.black]` section; no `.ruff.toml`, `ruff.toml`, `setup.cfg`, `tox.ini`, or `.pre-commit-config.yaml` in the repo root). Style is enforced by convention and review only.
- **CI/CD**: **absent**. No `.github/` directory, no workflow file, no `.gitlab-ci.yml`, no Jenkinsfile, no pipeline or deployment config; nothing automates install/lint/test on a change.
- **Documentation**: strong. `README.md` (≈180 lines) covers prerequisites, setup, run, test, the auth flow, both modes, the 6 config-resolution rules, storage, the full HTTP surface table (including the auth routes), the file layout, and explicit "Notes" on what is *not* tested. `AGENTS.md` documents the AI-DLC harness layout. Every `app/` module carries a long docstring naming its single responsibility and the requirement ids it satisfies (FR1.1–FR5.5 from the prior intent's `requirements.md`), and every non-obvious function/constant is commented (e.g. `app/service.py:78-79` explains the lazy import of the live client; `app/repository.py:46-49` explains the `now` seam). Type annotations are used throughout with `from __future__ import annotations`. There is no `py.typed` marker, no CHANGELOG, no LICENSE file, and no contributor guide.
- **Consistency positives**: one error envelope for all failures; one `RECORD_FIELDS` contract used by both storage and wire; parameterised SQL only (no string interpolation in `app/repository.py` or `app/db.py`); secrets redacted in `Settings.__repr__`, `SessionCredential.__repr__`, and `OpenRouterClient.__repr__`, with a test asserting the key never appears in a rendered setting, a log record, or any endpoint body.

### Technical Debt Signals

1. **In-app OAuth flow exists and contradicts the v1 intent's "no auth" + manual-config key.** `app/session_auth.py` (263 lines), the four `/auth/*` routes (`app/routes.py:125-167`), 24 of the 52 tests (`tests/test_session_auth.py`, `tests/test_auth_routes.py`), the indicator in `app/static/index.html:104-116` + `app/static/app.js:130-175`, and the config comment in `config.example.toml` all implement/serve an OpenRouter PKCE authorization whose credential lives in process memory. The v1 description instead says the key is supplied manually in the gitignored `config.local.toml` and asks for "no auth". This is the largest single divergence between the code as it stands and the intent.
2. **Config rule 5 supersedes the fail-fast rule the intent still asks for.** `app/config.py:111-123` (and the amendment noted in `tests/test_config.py:70-85`) make `mode = "openrouter"` with no key start *unconnected* on the dummy engine, whereas the v1 description says live mode with a missing key shall "fail with a clear error naming the file to fill in". `README.md` documents the new behaviour; the intent text does not.
3. **Naming drift on both clients.** The code ships `DummyClient` (`app/dummy_client.py:75`) and `OpenRouterClient` (`app/openrouter_client.py:76`); the intent names them `DummySentimentClient` and `OpenRouterJevSentimentClient`.
4. **Stale comment that directly contradicts the code.** `app/main.py:33-34` says "No authentication, session or CORS middleware exists anywhere in this app" while `SessionAuth`, session-scoped credentials and four `/auth/*` routes exist — the comment is left over from before the auth flow landed.
5. **Stale generated metadata.** `very_cool_sentiment_analysis.egg-info/PKG-INFO` embeds an *older* README: its config rules still show rule 5 as "app **fails at startup**", its HTTP table lists 6 routes (`/health` returning only `mode`), its file layout omits `session_auth.py` and the two auth test modules, and `SOURCES.txt` lists neither `tests/test_session_auth.py` nor `tests/test_auth_routes.py`. `SOURCES.txt` also omits `app/__init__.py`'s sibling artifacts ordering vs. the tracked tree, and the package-data entry for `static/*` is not reflected in what a fresh `sdist` would ship. The repo's own README, app and tests are newer than this artifact.
6. **Unmeasured test coverage.** No coverage tooling or floor, despite the active `classic` scope's 80 % line-coverage expectation and the ~250 LOC `app/openrouter_client.py` that no test touches; there is no measurement that would detect a regression in it.
7. **No linting, formatting, or CI to enforce the conventions the code already follows.** Everything (import order, annotation style, docstring content) rests on review; `filterwarnings = ["error"]` is the sole mechanical gate, and `test_config.py` shells out to `git` (skips silently if `git` is absent, `test_config.py:128-129`).
8. **Per-request SQLite connection with default thread affinity.** `app/routes.py:70-76` opens and closes one `sqlite3.Connection` per request through a sync-generator dependency with `sqlite3.connect()` defaults (`check_same_thread=True`, no `timeout`/WAL, `app/db.py:51-63`). The prior intent's record already caught this as a thread-affinity risk (`sqlite3.ProgrammingError` under overlapping requests) and accepted it as a known limitation (`aidlc/spaces/default/memory/project.md`, Corrections). It remains unresolved in the code.
9. **Import-time application construction.** `app/__init__.py:8` re-exports `app.main.app`, and `app/main.py:101` builds the app at module import. Importing any submodule (e.g. `from app.config import Settings` in a test) therefore constructs a full FastAPI app and `SessionAuth` as a side effect, coupling pure modules to the ASGI assembly.
10. **Dummy engine quality is fixed by design and invisible to users of the live path.** `DummyClient` returns constant per-label probability triples (0.85/0.05/0.10 and variants, `app/dummy_client.py:56-60`) and a constant intensity per label, so stored dummy-mode rows carry no real signal; the two engines therefore produce records that are not comparable (`model`/`provider` differ, which is the documented way to tell them apart).
11. **`data/sentiment.db` carries live local state (12 rows) and `schema_meta.version = 1` with no migration mechanism.** `app/db.py` only creates tables when absent; there is no version-aware migration step and no downgrade/upgrade path, so any future schema change is a hand-written delta (the `SCHEMA_VERSION` constant is only written, never read back for comparison).

## Handoff Summary

- **Intent-relevant finding**: The POC in `./app` already implements the v1 core — one `SentimentClient` seam (`app/sentiment.py:55-61`) with an offline deterministic `DummyClient` (`app/dummy_client.py`, no key/no network) and a live Jev/OpenRouter Decisions client that reads only typed Choice/Score answers (`app/openrouter_client.py:99-250`), SQLite persistence with an idempotent init step (`app/db.py:66-83`), a one-page UI with history (`app/static/index.html`, `app/static/app.js`), and JSON `POST /analyze` + `GET /analyses` (`app/routes.py:88-109`). The gap against the v1 intent is drift, not absence: the code additionally carries an in-app OpenRouter PKCE authorization flow (`app/session_auth.py`, four `/auth/*` routes, 24 of 52 tests) where the intent says "no auth" and a manually supplied key in `config.local.toml`; live mode without a key no longer fails fast (`app/config.py:111-123`); and the two client classes are named `DummyClient`/`OpenRouterClient` rather than `DummySentimentClient`/`OpenRouterJevSentimentClient`. Everything v1 asks for on the engine, storage, page and JSON-API axes is already present and tested offline by 52 tests behind a socket-blocking guard (`tests/conftest.py:129-146`).
- **Risks / follow-up** (facts the architect or the next stage must preserve):
  - Read-only scan; no build, lint, or test command was run, so no claim here about the suite's current pass/fail state — the only run evidence is `.pytest_cache/v/cache/lastfailed = {}`.
  - The repo also contains non-application trees that must not be mistaken for the codebase: `aidlc/` (AI-DLC workspace and record), `.omp/` (harness skills/agents), `.venv/`, `.pytest_cache/`, `data/`, and the stale `very_cool_sentiment_analysis.egg-info/`.
  - The pre-scan snapshot bounds verified coverage to `./`; every deeply analyzed path listed above lies inside it.
  - Test-harness constraints any v1 change must keep intact: no `httpx` (hand-rolled ASGI caller), the session-wide socket-blocking `offline_guard`, `tmp_path`-scoped settings, and `filterwarnings = ["error"]`.
  - Behavioural contracts in force today: `uvicorn app:app` must keep resolving (`app/__init__.py:8`); `GET /health` and `GET /auth/status` currently return the same `effective_connection` payload; the error envelope shape and its four codes are asserted by tests; `Probabilities` are JSON objects keyed by label, never arrays; `created_at` is ISO 8601 UTC ending in `Z`.
  - The prior intent's requirement ids (FR1.1–FR5.5, NFR1–NFR6 in `260929-sentiment-analysis/inception/requirements-analysis/requirements.md`) are cited throughout the code's docstrings — the v1 requirements will need the same ids carried forward, or the docstring references will dangle.
  - Known accepted limitation to re-decide if the connection lifecycle is touched: per-request `sqlite3` connections rely on default thread affinity (`app/routes.py:70-76`, `app/db.py:51-63`), recorded in `aidlc/spaces/default/memory/project.md` under Corrections.
  - `data/sentiment.db` exists locally with 12 rows at schema version 1 (gitignored, untracked); no migration mechanism exists beyond `CREATE TABLE IF NOT EXISTS`.
