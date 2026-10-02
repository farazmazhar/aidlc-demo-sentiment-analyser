## Developer Code Scan Results

### Scan Coverage

- **Analyzed deeply**:
  - `app/__init__.py` — ASGI re-export (10 lines, full read)
  - `app/main.py` — application factory, lifespan, router/static/exception wiring (103 lines, full read)
  - `app/routes.py` — the entire HTTP surface: page, `/v1` API, `/auth/*`, error handlers (387 lines, full read)
  - `app/models.py` — `AnalyzeRequest`, `AnalysisRecord`, `RECORD_FIELDS`, `UNKNOWN_PROVIDER` (144 lines, full read)
  - `app/repository.py` — `insert_analysis`, `list_analyses`, `list_analyses_by_import_id`, `DEFAULT_LIST_LIMIT` (102 lines, full read)
  - `app/db.py` — `connect`, `init_db`, migration/rebuild, all DDL constants (243 lines, full read)
  - `app/service.py` — `analyze_text`, `import_texts`, `get_client`, `effective_connection`, `ImportSummary` (214 lines, full read)
  - `app/sentiment.py` — `LABELS`, `SentimentResult`, `SentimentClient` protocol, `validate_result` (84 lines, full read)
  - `app/config.py` — `Settings`, `load_settings`, mode resolution, redaction (151 lines, full read)
  - `app/session_auth.py` — PKCE flow, `SessionAuth`, `SessionCredential` (259 lines, full read)
  - `app/dummy_client.py` — offline keyword engine and the only tokenizer in the repo (101 lines, full read)
  - `app/openrouter_client.py` — live Jev client, injected transport, typed answer reading (232 lines, full read)
  - `app/static/index.html` — the single page: markup, inline CSS, `data-testid` inventory (193 lines, full read)
  - `app/static/app.js` — page behaviour, all `fetch` call sites (201 lines, full read)
  - `tests/conftest.py` — `asgi_request` harness, `offline_guard`, `tmp_settings`, `tmp_db_path` (176 lines, full read)
  - `tests/test_db.py`, `tests/test_repository.py`, `tests/test_service.py`, `tests/test_routes.py`, `tests/test_bulk_import.py`, `tests/test_page.py`, `tests/test_config.py`, `tests/test_dummy_client.py`, `tests/test_live_client.py`, `tests/test_session_auth.py`, `tests/test_auth_routes.py` — all 11 test modules (2140 lines total, full read)
  - `pyproject.toml` — build, dependencies, pytest/coverage/ruff config (72 lines, full read)
  - `README.md` — HTTP surface table, storage/migration contract, file layout, known limitations (266 lines, full read)
  - `config.example.toml` (24 lines, full read), `opencode.json` (16 lines, full read)
  - `.gitignore` — read the ignore rules relevant to `config.local.toml`, `/data/`, `.venv/`, `.coverage`
  - `data/sentiment.db` — probed live with `sqlite3` (schema, `schema_meta` version, row count); not read as text
  - `git` history — 2 commits on `main` (`beeb587` express bulk import, `4eb9b74` v1-classic hardening)
  - `.aidlc/knowledge/aidlc-developer-agent/re-artifacts.md` — the artifact template (methodology, not application code)
- **Skimmed only**:
  - `.aidlc/knowledge/aidlc-shared/` and `.aidlc/knowledge/aidlc-developer-agent/` — read for the mandated knowledge preflight and the artifact template; not analysed as application code
  - `aidlc/spaces/default/codekb/sentiment-opencode/` — read only to align component names and the prior Scope of Analysis block with the existing store
  - `aidlc/spaces/default/intents/261001-analytics-layer/` — read the intent statement and `aidlc-state.md` to understand the target; the ideation artifacts were not analysed
  - `.aidlc/tools/`, `.aidlc/skills/`, `.aidlc/hooks/`, `.aidlc/agents/`, `.aidlc/sensors/`, `.aidlc/scopes/`, `.aidlc/onboarding.md` — listed only; harness engine, not application code
  - `.opencode/agents/*.md`, `.opencode/command/aidlc.md`, `.opencode/plugin/*.ts` — listed only; harness adapter
  - `aidlc/spaces/default/memory/{org,team,project}.md` — not read; practice rules, not code
  - `.venv/` — `importlib.metadata` version probe only; site-packages not read
  - `.git/`, `.pytest_cache/`, `.ruff_cache/`, `app/__pycache__/`, `tests/__pycache__/`, `.coverage` — build/bytecode artefacts, not analysed
  - `.commandcode/taste/taste.md` — present but empty (0 bytes)

### Packages Found

- `very-cool-sentiment-analysis` — application package (declared in `pyproject.toml` `[project]`, shipped as `packages = ["app"]`) — Python 3.11+ — a localhost-only sentiment analysis web app: typed positive/negative/neutral classification, local SQLite history, single-page UI plus a versioned JSON API
- `app` — the single importable package under `[tool.setuptools]` — Python — all 12 modules plus the `static/` asset directory (`package-data` = `static/*`)
- `tests` — test package (`tests/conftest.py` is imported as `tests.conftest` by every route test) — Python — in-process ASGI acceptance/unit suite

There is exactly one distributable package and one test package. No sub-packages, no `src/` layout, no namespace package, no vendored third-party code inside `app/`.

### Build System

- **Type**: PEP 517 / setuptools with a `pyproject.toml` manifest; no Makefile, no Dockerfile, no `noxfile.py`, no `tox.ini`, no CI workflow
- **Config Files**: `pyproject.toml` (the only manifest), `.gitignore`, `config.example.toml` (runtime configuration template, gitignored sibling `config.local.toml`)
- **Build Dependencies**:
  - `very-cool-sentiment-analysis` (root project) → no internal package dependency; the only declared package is itself
  - `app` (package) → no dependency on any other local module at *packaging* level; internal coupling is by import only
  - **Internal import graph (one direction per layer, no cycles detected):**
    - `app/__init__.py` → `app/main.py`
    - `app/main.py` → `app.db`, `app.config`, `app.routes`, `app.sentiment`, `app.service`, `app.session_auth`
    - `app/routes.py` → `app.db`, `app.config`, `app.models`, `app.repository`, `app.sentiment`, `app.service`, `app.session_auth`
    - `app/service.py` → `app.config`, `app.dummy_client`, `app.models`, `app.repository`, `app.sentiment`, `app.session_auth`; **function-local** import of `app.openrouter_client` at `app/service.py:103` so the offline path never loads the live client
    - `app/repository.py` → `app.models`; `TYPE_CHECKING`-only import of `app.sentiment` (`app/repository.py:22-23`)
    - `app/dummy_client.py` → `app.sentiment`; `app/openrouter_client.py` → `app.sentiment`
    - `app/db.py` → `app.models` (for `UNKNOWN_PROVIDER` only)
    - `app/config.py`, `app/session_auth.py` → no `app.*` imports (leaves of the graph)
- **Build/runtime commands** (from `README.md:51-57`): `python -m pytest -q`, `python -m ruff check app tests`, `python -m ruff format --check app tests`; serve with `uvicorn app:app --reload`
- **Executable verification command** (`README.md:258`): install `.[dev]`, run `pytest -q`, then boot uvicorn on `127.0.0.1:8141` and read `/v1/health`

### APIs Discovered

- **External JSON API (versioned)** — `app/routes.py` — 6 endpoints under `V1_PREFIX = "/v1"` (`app/routes.py:49`), mounted on `v1_router = APIRouter(prefix=V1_PREFIX)` (`app/routes.py:134`), included at `app/main.py:90`
  - `POST /v1/analyze` — `app/routes.py:143` — body `{"text": str}` (plain dataclass `AnalyzeRequest`, `additionalProperties: false` enforced by `require_declared_fields`, `app/routes.py:101`); `200` with the stored record, `422 VALIDATION_FAILED`, `422 INVALID_TEXT`, `503 LIVE_KEY_MISSING`, `503 SENTIMENT_ENGINE_ERROR`, `503 AUTH_EXPIRED`
  - `GET /v1/analyses` — `app/routes.py:166` — query `limit: int = 50` (`ge=1`, `DEFAULT_LIST_LIMIT` at `app/repository.py:26`); `200` with a bare JSON array newest-first, `422` on a bad limit (never clamped)
  - `POST /v1/analyses/import` — `app/routes.py:180` — raw `bytes` body, `Content-Type` must be `text/csv` or `text/plain` (`IMPORT_CONTENT_TYPES`, `app/routes.py:61`); `200` with `ImportSummary.to_dict()`, `422 VALIDATION_FAILED`
  - `GET /v1/analyses/export` — `app/routes.py:229` — required query `import_id: str`; `200` `text/csv` attachment, `404 IMPORT_NOT_FOUND`, `422 VALIDATION_FAILED`
  - `GET /v1/health` — `app/routes.py:272` — `200` with `{mode, connected}` plus `reason` only when not connected
  - No `/v2` router exists. The only version prefix in the codebase is `V1_PREFIX`.
- **External HTML + asset surface (unversioned)** — `app/routes.py`, `app/main.py` — 5 routes on the unprefixed `router` (`app/routes.py:131`)
  - `GET /` — `app/routes.py:137` — `HTMLResponse(INDEX_HTML.read_text(encoding="utf-8"))`; the file is re-read from disk on every request
  - `GET /static/*` — `app/static` mounted via `StaticFiles` at `app/main.py:92` (serves `app.js`, `index.html`)
  - `GET /auth/status` — `app/routes.py:294`
  - `GET /auth/openrouter/start` — `app/routes.py:301` — `302` to `https://openrouter.ai/auth` with an S256 PKCE challenge
  - `GET /auth/callback?code=` — `app/routes.py:309` — `302` back to `/?auth=connected` or `/?auth=failed`
  - `POST /auth/disconnect` — `app/routes.py:329`
- **Outbound external API (client)** — `app/openrouter_client.py:34` — 1 endpoint, `POST https://openrouter.ai/api/alpha/decisions` through the `HttpTransport` protocol (`app/openrouter_client.py:69`), stdlib `urllib` in production, 10 s bound timeout (`LIVE_TIMEOUT_SECONDS = 10.0`, `app/openrouter_client.py:38`)
- **Outbound external API (auth)** — `app/session_auth.py:40-41` — 1 endpoint, `POST https://openrouter.ai/api/v1/auth/keys` for the PKCE code exchange (`exchange_code_at_openrouter`, `app/session_auth.py:78`), 30 s timeout
- **Internal seams that are genuine extension points**
  - `SentimentClient` protocol (`app/sentiment.py:78`) — the one engine interface; `get_client` (`app/service.py:76`) is the only place a concrete client is chosen
  - `get_connection` dependency (`app/routes.py:92`) — yields one short-lived `sqlite3.Connection` per request from `app.state.settings.db_path`
  - `error_response(status_code, code, message)` (`app/routes.py:69`) — the single error-envelope builder; the envelope is exactly `{code, message}` because the contract sets `additionalProperties: false`
  - `get_settings` / `get_session_auth` dependencies (`app/routes.py:82`, `app/routes.py:87`)
  - `app.service.effective_connection` (`app/service.py:45`) — the one connection-state payload read by the health endpoint, the page indicator and the startup log
- **Exception-handler registrations** — `app/main.py:94-98` — five handlers: `RequestValidationError`, `InvalidTextError`, `LiveKeyMissingError`, `SentimentAuthError`, `SentimentEngineError`

### Frameworks & Libraries

- **fastapi** — `>=0.110` declared (`pyproject.toml:13`), `0.142.2` installed — HTTP surface, routing, dependency injection, exception handlers, `StaticFiles`
- **uvicorn** — `>=0.27` declared (`pyproject.toml:14`), `0.54.0` installed — ASGI server, `uvicorn app:app --reload`
- **starlette** — `1.7.0` installed (transitive via FastAPI) — `StaticFiles`, `HTMLResponse`, `JSONResponse`, `RedirectResponse`
- **pydantic** — `2.13.5` installed (transitive) — reached only through FastAPI request-body validation; `app/models.py` deliberately uses stdlib `dataclass` so the codebase has no direct pydantic import (stated at `app/models.py:9-10`)
- **anyio** — `4.15.1` installed (transitive) — the thread pool FastAPI uses for the synchronous `def` handlers
- **pytest** — `>=8` declared under `[project.optional-dependencies].dev`, `9.1.1` installed — the whole test runner
- **pytest-cov** — `>=5` declared, `7.1.0` installed — enforces the coverage floor
- **ruff** — `>=0.6` declared, `0.16.9` installed — linter and formatter
- **Standard library only** for everything else: `sqlite3` (`app/db.py`, `app/repository.py`), `urllib.request` (both outbound clients), `tomllib` (`app/config.py:24`), `csv` + `io` (`app/routes.py:17-18`), `uuid` (`app/service.py:15`), `threading` (`app/session_auth.py:30`), `secrets`/`hashlib`/`base64` for PKCE, `re` for tokenising (`app/dummy_client.py:68`), `logging`, `dataclasses`, `datetime`/`zoneinfo`-free UTC via `datetime.UTC`
- **Not installed, deliberately**: `httpx` (so `fastapi.testclient` is unusable; `tests/conftest.py:6-9` explains this) and any browser-automation package (`tests/test_page.py:1-6`). The runtime dependency cap is **exactly two packages** and is asserted by `tests/test_config.py:141-160`.
- **No frontend framework**: the UI is one hand-written HTML file with inline CSS plus one vanilla ES module-free script. No npm, no bundler, no `package.json` in the repo (`opencode.json` is the opencode harness config, not a build manifest).
- **SQLite**: bundled `sqlite3` module, library version `3.53.4` — JSON1 (`json_extract`) and `strftime`/`date` functions verified available for any aggregate work.

### Test Coverage

- **Test Directories**: `tests/` (single directory, no sub-directories, no fixtures directory — fixtures are pytest fixtures in `conftest.py`)
  - `tests/conftest.py` (176 lines) — the harness
  - `tests/test_db.py` (436), `tests/test_routes.py` (363), `tests/test_bulk_import.py` (315), `tests/test_service.py` (304), `tests/test_auth_routes.py` (259), `tests/test_repository.py` (237), `tests/test_live_client.py` (220), `tests/test_session_auth.py` (196), `tests/test_config.py` (180), `tests/test_dummy_client.py` (84), `tests/test_page.py` (77)
- **Test Frameworks**: `pytest` only. No `unittest`, no `hypothesis`, no `mock`/`unittest.mock` — every double is a hand-written class or function (`FakeExchanger`, `StubTransport`, `DuckTypedClient`, `FailingOnBoomClient`, `IncompleteClient`, `UnsupportedLabelClient`, `RejectingClient`, `FailingClient`) or a `monkeypatch.setattr("app.routes.get_client", ...)` seam. No `pytest.mark.asyncio`; `asgi_request` uses `asyncio.run` per call (`tests/conftest.py:136`).
- **Coverage Config**: **present and enforced twice over** — `pyproject.toml:37` puts `--cov=app --cov-report=term-missing --cov-fail-under=80` in `addopts` so every run applies it, and `pyproject.toml:41-47` repeats it under `[tool.coverage.run]` / `[tool.coverage.report]` (`source = ["app"]`, `fail_under = 80`, `show_missing = true`). `testpaths = ["tests"]` (`pyproject.toml:33`) and `filterwarnings = ["error"]` (`pyproject.toml:39`) are also configured, so a FastAPI/pydantic deprecation is a hard failure.
- **Measured baseline (this scan, `python -m pytest -q`)**: **118 passed, 0 failed, 0 skipped**, in 0.66 s. Line coverage over `app/`: **96.02%** against the 80% floor — 679 statements, 27 missed.
  - 100%: `app/__init__.py`, `app/config.py`, `app/dummy_client.py`, `app/models.py`, `app/repository.py`, `app/sentiment.py`, `app/service.py`
  - Partial: `app/db.py` 98% (line 208), `app/main.py` 98% (line 49), `app/routes.py` 99% (lines 217-218, the `csv.Error` branch), `app/openrouter_client.py` 92% (lines 89-96, the production `urllib_transport` body), `app/session_auth.py` 85% (lines 84-120, the production `exchange_code_at_openrouter` body)
  - The five uncovered blocks are the two production `urllib` transports plus one branch each in `db.py`/`main.py`/`routes.py` — all deliberately bypassed in favour of injected seams.
- **Offline enforcement**: the session-scoped autouse fixture `offline_guard` (`tests/conftest.py:139-156`) monkeypatches `socket.socket.connect` to raise, so an accidental network call fails the run. `tests/test_dummy_client.py:70-84` actively proves the guard is armed.
- **Isolation**: `tmp_settings` and `tmp_db_path` (`tests/conftest.py:159-176`) point every test at `tmp_path`; no test reads or writes the real `config.local.toml` or `data/sentiment.db`.
- **Frontend coverage limit, stated in the suite itself**: `tests/test_page.py` asserts the served **markup and asset** contract only (test-id presence, `role="status"`, `aria-live`, absence of `intensity`, asset content-type). Browser-side execution of `app.js` is not driven by the suite because no browser-automation dependency is permitted under the cap (`tests/test_page.py:1-6`).
- **Linter status (this scan)**: `ruff check app tests` → *All checks passed!*; `ruff format --check app tests` → *24 files already formatted*.

### Code Quality Indicators

- **Linting**: `ruff`, configured entirely in `pyproject.toml`
  - `[tool.ruff]` — `line-length = 100`, `target-version = "py311"` (`pyproject.toml:49-51`)
  - `[tool.ruff.lint] select = ["E","F","W","I","N","UP","S","B","C4","SIM"]` (`pyproject.toml:57`) — an explicit, reviewed selection rather than a drifting default; `S` is the security set (secrets in code, unsafe calls, weak hashing)
  - `extend-immutable-calls = ["fastapi.Depends", "fastapi.Query"]` (`pyproject.toml:62`) so B008 does not fire on FastAPI's argument-default markers
  - `per-file-ignores` for `tests/*`: `["S101","S105","S106","S603","S607"]` — asserted inside `app/` in full (`pyproject.toml:64-68`)
  - `[tool.ruff.format] quote-style = "double"`, `line-ending = "lf"` (`pyproject.toml:70-72`)
- **Type checking**: **absent**. No `mypy`, no `pyright`, no `py.typed` marker. Typing is present but unenforced — `from __future__ import annotations` in all 12 modules, full annotations on every public function, two `TYPE_CHECKING`/`type: ignore` sites only.
- **CI/CD**: **none**. No `.github/`, no `.gitlab-ci.yml`, no Jenkinsfile, no pre-commit config, no GitHub Actions, no Docker. Verification is a documented manual command sequence (`README.md:51-57` and the end-to-end one-liner at `README.md:258`).
- **Documentation**: strong and unusually traceable for a project of this size
  - `README.md` (266 lines) is genuinely maintained: it carries a full HTTP surface table (`README.md:174-194`) that already documents all 11 routes, the six-step config resolution, the storage/migration contract, an accurate file-layout tree, and an explicit "Notes and known limitations" section. Every route and code constant in the table matches the code I read.
  - Every one of the 12 `app/*.py` modules opens with a "Single responsibility:" docstring naming its own boundary (e.g. `app/routes.py:1-13` "No sentiment logic and no SQL live here").
  - Traceability is embedded in the source itself: requirements IDs (`FR4.1`, `NFR3.1`), business rules (`BR4.3`), acceptance criteria (`AC7.1.2`), risk IDs (`R-01`, `R-04`) and decisions (`D1`–`D4`, `W1`) appear in docstrings and inline comments throughout `app/` and `tests/`, and the same IDs are used in the README.
  - No `docs/` directory, no ADRs, no OpenAPI spec file — the README table *is* the API contract of record.
- **File sizes**: no file exceeds 500 lines; the largest are `app/routes.py` (387) and `app/session_auth.py` (259). Longest functions are `import_texts` (41 lines) and `complete` (41 lines) — both are linear loops/sequences rather than deep control flow. No class exceeds 100 lines.
- **Layering discipline**: the routes → service → repository → db split is respected — no SQL in `app/routes.py`, no sentiment logic in the routes, and the engine is reached only through the `SentimentClient` protocol. **No circular imports** were found in the internal graph.
- **Error handling**: five named exception types mapped to a single envelope; validation before engine resolution (`analyze_text` order at `app/service.py:211-214`); secrets redacted in every `__repr__` (`app/config.py:69`, `app/session_auth.py:130`, `app/openrouter_client.py:118`); SQL is parameter-bound throughout, with only literal DDL statements.

### Technical Debt Signals

- **`_rebuild_analyses` silently drops any index on `analyses`** — `app/db.py:233-243` renames the table to `analyses_pre_v1`, creates a fresh `analyses`, copies rows, and drops the old table. The new table is created from `CREATE_ANALYSES_TABLE` (`app/db.py:40-53`), which declares **no indexes at all**. I verified this empirically: a store carrying `CREATE INDEX idx_analyses_created ON analyses(created_at)` plus a v2 relation came out of `init_db` with the columns correct and the row preserved but `sqlite_master` reporting **zero** indexes on `analyses`. The index therefore has to be re-created by `init_db` after the rebuild, or a migrating store loses it without warning. This matters directly for the intent's "add tables/indexes only via migration" constraint.
- **Adding a column to `analyses` is a five-place edit** — `ANALYSES_COLUMNS` (`app/db.py:63-74`), `CREATE_ANALYSES_TABLE` (`app/db.py:40-53`), `_ADD_COLUMN_SQL` (`app/db.py:94-105`), `_V1_NOT_NULL_COLUMNS` (`app/db.py:79-81`), and the explicit column list in `_COPY_ROWS_INTO_V1_TABLE` (`app/db.py:114-120`). Miss any one and `_is_v1_shape` (`app/db.py:195-209`) either reports a false v1 shape or the row copy aborts. A separate table, or an index created idempotently in `init_db`, is far cheaper — and an unrelated table *does* survive both paths (I verified a side table survives the idempotent re-init).
- **The committed dev database is one schema version behind the code** — `data/sentiment.db` reports `schema_meta.version = 2` with columns lacking `import_id`, while `SCHEMA_VERSION = 3` (`app/db.py:35`). It holds 0 rows, and `/data/` is gitignored (`.gitignore:94`), so this is a local artefact only. The v2 → v3 path (`app/db.py:226-230`) has never actually run against this file.
- **Known cross-thread SQLite defect, accepted for v1** — `README.md:247-253` records that a per-request `sqlite3.Connection` created in one anyio worker thread and closed in another raises `sqlite3.ProgrammingError` and answers `500` when requests overlap. Sequential use is unaffected. `get_connection` (`app/routes.py:92-98`) is the single place this happens, so **any new read-heavy endpoint inherits the defect**, and a polling analytics page is exactly the access pattern that would trip it. The fix is explicitly recorded as out of scope for v1.
- **`_WORD` is a private, unexported tokenizer living in the wrong module** — `app/dummy_client.py:68` declares `_WORD = re.compile(r"[a-z']+")` and `.findall(text.lower())` at line 83. This is the only tokeniser in the codebase, it is underscore-private, and it sits in the *offline engine* rather than a utility module. Any term-frequency work would either reach into a private of an unrelated module or duplicate the regex — a clean extraction candidate that this intent makes urgent.
- **No pagination beyond a bare `LIMIT`** — `list_analyses` (`app/repository.py:80-87`) is `ORDER BY id DESC LIMIT ?` with no offset, cursor, or `totalCount`. The API surface has no pagination metadata at all.
- **No response-model / OpenAPI contract enforcement** — handlers return bare `list[dict[str, object]]`, `dict[str, object]` or hand-built `JSONResponse`, so FastAPI's generated `/openapi.json` cannot describe the real shapes. Contracts are pinned only by hand-written constants in `tests/test_routes.py:28-41` and `tests/test_bulk_import.py:27-33`.
- **The export route duplicates the record shape positionally** — `get_analyses_export` (`app/routes.py:229-269`) writes seven columns out of `EXPORT_COLUMNS` by unpacking each `AnalysisRecord` field by hand, rather than from `AnalysisRecord.to_dict()` or `dataclasses.fields`. Any change to the record shape, or a new export column, must be edited in two places (`app/routes.py:63-64` and `app/models.py:103-115`) and the two can silently drift.
- **Coverage gaps concentrated in the production HTTP transports** — `app/openrouter_client.py:89-96` and `app/session_auth.py:84-120` are uncovered because every test injects a transport instead. Acceptable by design (the cap forbids a real client library), but it means the two places that build and parse real HTTP are unexercised.
- **Zero `TODO`/`FIXME`/`HACK`/`XXX` markers** anywhere in `app/` or `tests/`.
- **Nine suppression comments, all narrow and justified** — 3 `# pragma: no cover` (`app/db.py:190`, `app/repository.py:22`, `app/routes.py:353`, plus `tests/test_config.py:165`), 4 `# noqa: S310` on `urllib.request` calls with a hardcoded-https-constant comment (`app/openrouter_client.py:89,93`; `app/session_auth.py:88,96`), 2 `# type: ignore[method-assign]` in the offline guard (`tests/conftest.py:152,156`). No blanket suppressions.
- **No CI, so the 80% floor and the ruff rule set are enforced only by whoever remembers to run them locally** — this is the single largest process-level debt signal.
- **`.coverage`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/` are present in the working tree** — all gitignored (`.gitignore:99-103`), so harmless, but the tree is not pristine.

## Handoff Summary

- **Intent-relevant finding**: the four extension seams an analytics layer can reuse are all present, explicit, and already in the shape the intent needs — but the requested `/v2` prefix does not exist yet, and one requested metric conflicts with a deliberate v1 decision.
  1. **A `/v2` prefix must be created, not extended.** The only version prefix in the codebase is `V1_PREFIX = "/v1"` (`app/routes.py:49`) on `v1_router` (`app/routes.py:134`), included at `app/main.py:90` alongside the unprefixed page/auth `router` (`app/main.py:91`). The two-router split is the established convention and the exact insertion point for a third `v2_router`; the README's own rule is that *data* routes are versioned and *page* routes are not (`README.md:169-172`), so the second UI page belongs on the unprefixed `router` beside `index()` (`app/routes.py:137`), served the same way — a file in `app/static/` read via `HTMLResponse(INDEX_HTML.read_text(...))`.
  2. **`mean intensity` is a contract conflict that must be resolved before design.** The intent asks for "mean intensity", but `intensity` is a **retired** column: it is deliberately nullable and never written by new rows (`app/db.py:47`), absent from `RECORD_FIELDS` (`app/models.py:25-35`), never read by `AnalysisRecord.from_row` (`app/models.py:117-144`), and its removal is asserted in three test files (`tests/test_page.py:64-68` asserts the string `intensity` is absent from the page markup; `tests/test_db.py:132-189`; `tests/test_repository.py:163-209`). It exists only on pre-v1 rows. `AVG(intensity)` over the current `analyses` table would return `NULL` for every row written since v1. **This is the one requirement that cannot be implemented as written without a decision.**
  3. **The aggregate SQL has a natural home and a verified query surface.** `app/repository.py` is the only module that talks SQL, all three of its functions take a `sqlite3.Connection` as their first argument, and no aggregate query exists yet. `get_connection` (`app/routes.py:92`) is the per-request connection dependency. Aggregating over `label` (TEXT with a CHECK domain, `app/db.py:44`), `confidence` (REAL) and `created_at` (TEXT ISO-8601 ending in `Z`, therefore lexicographically sortable and directly range-comparable) is straightforward; I confirmed the bundled SQLite is `3.53.4` with `json_extract` and `strftime('%Y-%m-%d', …)` available if the `probabilities` JSON column or per-day bucketing needs them. `LABELS` (`app/sentiment.py:20`) is the canonical closed label set, and `import_id` is a plain TEXT grouping key already indexed by nothing but queryable (`app/repository.py:99-101`).
  4. **The term-extraction requirement already has a tokenizer, in the wrong place.** `app/dummy_client.py:68` holds `_WORD = re.compile(r"[a-z']+")` and the positive/negative word sets (`app/dummy_client.py:16-53`), used at line 83. The intent's "reuse a simple tokenizer" is satisfiable, but only by extracting that private into a shared utility or duplicating it — it should be a deliberate, named decision, not an import of another module's underscore name.
- **Risks / follow-up**:
  - **Unresolved requirement, not a scan limitation**: the `mean intensity` conflict in (2) above needs a human decision — return it as `null`, omit it, or reintroduce a written intensity column. Per the intent's own instruction ("If any requirement is ambiguous, ask me before building rather than guessing"), this must be raised, not resolved by assumption. Flagging it now, at scan time, is cheaper than discovering it in code generation.
  - **The index-drop defect in `_rebuild_analyses`** (`app/db.py:233-243`, verified empirically) means any new index on `analyses` must be created idempotently inside `init_db` *after* the rebuild branch, or it disappears on any migrating store. `init_db` runs on every startup from the lifespan (`app/main.py:73`), so this is a cheap place to add it — but only if the designer knows the rebuild drops it.
  - **The accepted cross-thread SQLite defect** (`README.md:247-253`) is inherited by any new endpoint using `get_connection`, and a date-range-filtered analytics page is a polling client — the access pattern most likely to expose it. Treat it as a known, already-documented constraint rather than a new discovery; do not silently widen scope to fix it.
  - **A new page needs its own test-id contract.** `tests/test_page.py:17-32` pins `REQUIRED_TEST_IDS` for the existing page, and `tests/conftest.py:119-136` (`asgi_request`) is the only way tests reach the app — `fastapi.testclient` is unavailable because the two-package cap forbids `httpx`. Any new page test must reuse that harness and add its own required-id list. There is also currently **no navigation link between pages** in `index.html`, so a route to the new page must be added to the existing markup — which touches the file `tests/test_page.py:64-68` asserts must not contain the word `intensity`.
  - **Coverage floor interaction**: the floor is 80% and the suite is at 96%, with `--cov=app` measuring the whole package. New untested code in `app/` pulls the *package* average down, so a partially-tested new module is affordable but a wholly untested one is not. `filterwarnings = ["error"]` (`pyproject.toml:39`) also means any new FastAPI/pydantic deprecation is a hard suite failure.
  - **No CI exists**, so the 80% floor, the pinned ruff `select` list and the existing 118 green tests are the *only* safety net. The brownfield safeguard applies: establish this baseline (118 passed / 96.02%) before changes and re-run after, treating any new failure as a regression.
  - **Scope honesty for the next stage**: I read all 12 `app/` modules, both static assets, all 11 test modules plus `conftest.py`, and the four root config files in full. I did **not** analyse the `.aidlc/` harness engine, the `.opencode/` adapter, the `aidlc/` workflow record tree, the `aidlc/spaces/default/codekb/` store's prose, or `.venv/` contents — those are workflow machinery and vendored dependencies, not application code. `data/sentiment.db` was probed live rather than read as text, and `.commandcode/taste/taste.md` is empty. `aidlc/spaces/default/memory/{org,team,project}.md` was not read; the architect should read the Code Style and Testing Posture sections before any design decision, since they carry the team/project practices this scan cannot see.
  - **Store alignment**: the existing `aidlc/spaces/default/codekb/sentiment-opencode/` Scope of Analysis block is `kind: full` with `./` in `analyzed.paths` and 12 named components. My scan is consistent with that claim and with the component names, so a rerun should be able to keep `kind: full` — but the architect owns that block, and must decide whether the newly-verified coverage (root config files, the live `data/sentiment.db` probe, the empirical index-drop and JSON1/strftime findings) widens `analyzed.paths`.
