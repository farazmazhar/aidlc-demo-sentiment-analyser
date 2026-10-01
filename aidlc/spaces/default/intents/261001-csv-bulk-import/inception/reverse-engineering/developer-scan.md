# Developer Code Scan — `very-cool-sentiment-analysis`

Link 1 of 2 (developer → architect). Read-only code scan of the whole
repository, taken over `./` at `git:b212a85db8c21470c36acc527d511d630bd042a3`.
Commit examined: `4eb9b74c4197114181dab641c177c569f2058c24` ("v1-classic: harden
sentiment-analysis app to v1 (classic scope)", branch `main`).

## Developer Code Scan Results

### Scan Coverage

- **Analyzed deeply** (read in full and understood; repo-relative):
  - `app/__init__.py`, `app/main.py`, `app/config.py`, `app/models.py`,
    `app/sentiment.py`, `app/dummy_client.py`, `app/openrouter_client.py`,
    `app/repository.py`, `app/service.py`, `app/routes.py`, `app/session_auth.py`
  - `app/static/index.html`, `app/static/app.js`
  - `tests/conftest.py`, `tests/test_db.py`, `tests/test_repository.py`,
    `tests/test_service.py`, `tests/test_routes.py`, `tests/test_page.py`,
    `tests/test_dummy_client.py`, `tests/test_live_client.py`,
    `tests/test_config.py`, `tests/test_session_auth.py`, `tests/test_auth_routes.py`
  - `pyproject.toml`, `config.example.toml`, `README.md`, `AGENTS.md`, `.gitignore`
  - `data/sentiment.db` — opened read-only to read the live schema and row count;
    no write.
  - `aidlc/spaces/default/codekb/very-cool-sentiment-analysis/reverse-engineering-timestamp.md`
    and `component-inventory.md` headings — read only to carry forward the prior
    run's component names and scope basis.

- **Skimmed only** (noted at directory granularity, not deep-read):
  - `.venv/` — only installed distribution metadata was listed to pin versions.
  - `.opencode/` — harness agents/command/plugin, no application code.
  - `.aidlc/` — framework engine, agents, protocols, skills.
  - `aidlc/` (except the two codekb files above) — workspace memory, prior intent
    record, this intent's record, audit and engine state.
  - `.ruff_cache/`, `.git/`.

- **Note for the architect**: `aidlc/spaces/default/memory/team.md` is **stale
  against HEAD**. It describes `main` at `0268a5d`, the app on the unmerged
  `v1-classic` branch at `5b328fc`, "52 passed" tests, and `ruff`/coverage as
  still-to-be-adopted. That pre-merge commit is **not reachable in this clone**
  (`git cat-file` fails). The code, `pyproject.toml` and a live run (evidence
  below) are authoritative: the v1 work is merged to `main` at `4eb9b74`, the
  suite is 94 tests, coverage and `ruff` are configured and green. The prior
  CodeKB store also predates this merge, so it must not be trusted verbatim.

### Packages Found

Single installable package `app` (`pyproject.toml:36`, `packages = ["app"]`);
flat by-layer FastAPI package, not feature-sliced. Import graph is acyclic and
one-directional: leaves → data/engine adapters → service → routes → main.

- `app` — application package (FastAPI) — Python — localhost-only sentiment app.
  - `app/__init__.py` — re-export shim (`from app.main import app`) so
    `uvicorn app:app` resolves (`app/__init__.py:8-10`).
  - `app/main.py` — `create_app()` factory, lifespan (`init_db`, one startup
    log), router mounts, exception handlers, `HOST = "127.0.0.1"`
    (`app/main.py:36,52-100`).
  - `app/config.py` — `Settings` dataclass + `load_settings()` mode resolution
    (`app/config.py:54-151`).
  - `app/models.py` — `AnalyzeRequest`, `AnalysisRecord`, `RECORD_FIELDS`,
    `undeclared_body_fields` (`app/models.py:25-133`).
  - `app/sentiment.py` — engine interface: `LABELS`, `SentimentResult`,
    `SentimentClient` Protocol, `validate_result`, exception types.
  - `app/dummy_client.py` — offline keyword adapter `DummySentimentClient`.
  - `app/openrouter_client.py` — live Jev adapter `OpenRouterJevSentimentClient`.
  - `app/repository.py` — `insert_analysis`, `list_analyses`, `DEFAULT_LIST_LIMIT`.
  - `app/service.py` — `analyze_text`, `get_client`, `effective_connection`,
    `require_text`.
  - `app/routes.py` — page router, `/v1` router, auth routes, error envelope.
  - `app/session_auth.py` — in-app OpenRouter PKCE flow, process memory only.
  - `app/static/` — `index.html` (page) and `app.js` (fetch/render/indicator).
- `tests` — pytest suite — Python — 10 `test_*.py` modules + `conftest.py`
  harness (not a shipped package).

Source volume: ~2,194 lines across 12 `app/*.py` + 2 static files; ~2,303 lines
across 11 test files (per `wc -l`).

### Build System

- **Type**: PEP 517/518 Python package built with setuptools; no compiled or
  container build.
- **Config Files**: `pyproject.toml` (`[build-system]` requires
  `setuptools>=68`, backend `setuptools.build_meta`; `[project]`;
  `[project.optional-dependencies].dev`; `[tool.setuptools]`;
  `[tool.pytest.ini_options]`; `[tool.coverage.run]`; `[tool.coverage.report]`;
  `[tool.ruff]`; `[tool.ruff.lint]`; `[tool.ruff.format]`).
- **Build Dependencies**: single package `app` → imports only stdlib +
  `fastapi` (runtime). `app/__init__` → `app.main` → `app.routes`/`app.config`/
  `app.service`/`app.db` → `app.models`/`app.repository`/`app.sentiment`; engine
  adapters `app.dummy_client` (always importable) and `app.openrouter_client`
  (imported lazily inside `app/service._live_client`, `app/service.py:93-101`,
  so the offline path never loads the live module).
- **Runtime dependencies**: exactly two (`fastapi>=0.110`, `uvicorn>=0.27`),
  NFR3 cap asserted by `tests/test_config.py:141-160`.
- **Dev dependencies**: `pytest>=8`, `pytest-cov>=5`, `ruff>=0.6`.
- **No** `requirements.txt`, lockfile, `Makefile`, `Dockerfile`, tox/ini, or
  `.pre-commit` config.

### APIs Discovered

- **Versioned JSON HTTP API** — `app/routes.py` `v1_router` (`prefix="/v1"`,
  `app/routes.py:44,121`), included in `app/main.py:90` — **3 endpoints**:
  - `POST /v1/analyze` — body `AnalyzeRequest{text}`; validates text, resolves
    engine, persists, returns the stored record as JSON; `200`
    (`app/routes.py:130-150`).
  - `GET /v1/analyses?limit=50` — bare JSON array newest-first; bad `limit`
    (`ge=1`) → `422 VALIDATION_FAILED` (`app/routes.py:153-164`).
  - `GET /v1/health` — `{mode, connected[, reason]}` (`app/routes.py:167-183`).
- **Unversioned page/support HTTP routes** — `router` (`app/routes.py:118`),
  included in `app/main.py:91` — **5 endpoints**: `GET /` (`:124`),
  `GET /auth/status` (`:189`), `GET /auth/openrouter/start` (`:196`),
  `GET /auth/callback` (`:204`), `POST /auth/disconnect` (`:224`).
- **Static mount** — `/static` via `StaticFiles` (`app/main.py:92`).
- **Error envelope** — `{code, message}` only; codes `VALIDATION_FAILED`,
  `INVALID_TEXT`, `LIVE_KEY_MISSING`, `SENTIMENT_ENGINE_ERROR`, `AUTH_EXPIRED`
  (`app/routes.py:46-51,56-66,237-282`); framework routing errors keep FastAPI's
  `{"detail": ...}`.
- **Internal APIs (contracts to reuse)**:
  - `SentimentClient.analyze(text) -> SentimentResult`
    (`app/sentiment.py:78-84`); `SentimentResult` fields
    `label, probabilities, confidence, model, provider` (`app/sentiment.py:23-36`).
  - `service.get_client(settings, credential=None) -> SentimentClient` — the one
    adapter-selection point (`app/service.py:72-90`).
  - `service.analyze_text(client, connection, text, now=None) -> AnalysisRecord`
    — the per-text orchestration seam (`app/service.py:116-132`).
  - `repository.insert_analysis(connection, text, result, now=None)` and
    `list_analyses(connection, limit)` (`app/repository.py:40-79`).
  - `db.connect(db_path)` / `db.init_db(db_path)` (`app/db.py:121-159`).
- **No OpenAPI/Swagger spec file** is committed; FastAPI serves the app-generated
  schema only at runtime (`/openapi.json`, not exercised or asserted anywhere).

### Frameworks & Libraries

Versions from the repo-local `.venv` (`pip list`), Python `3.14.7`;
`requires-python = ">=3.11"`. Declared floors in `pyproject.toml`.

- `fastapi` — declared `>=0.110`, installed `0.142.2` — HTTP framework/routing.
- `uvicorn` — declared `>=0.27`, installed `0.54.0` — ASGI server (only run path).
- `starlette` — installed `1.7.0` — FastAPI's ASGI layer (transitive).
- `pydantic` / `pydantic_core` — installed `2.13.5` / `2.46.5` — FastAPI request
  validation (transitive; **not used directly in `app/`**, which uses stdlib
  dataclasses — `app/models.py:7-10`).
- `anyio` — installed `4.15.1` — thread-pool workers FastAPI uses for sync
  endpoints (relevant to the accepted R-01 thread-affinity debt).
- `pytest` — declared `>=8`, installed `9.1.1` — test runner.
- `pytest-cov` / `coverage` — declared `>=5`, installed `7.1.0` / `7.16.2` —
  coverage floor.
- `ruff` — declared `>=0.6`, installed `0.16.9` — lint + format.
- Standard library only for everything else: `sqlite3`, `csv`, `json`, `re`,
  `urllib`, `tomllib`, `hashlib`/`secrets`/`base64`, `threading`, `asyncio`.
- **Notably absent**: `python-multipart`, `httpx`, `requests`, `aiofiles`
  (verified by `pip list`). This matters for CSV upload (see Handoff).

### Test Coverage

- **Test Directories**: `tests/` only (`testpaths = ["tests"]`,
  `pyproject.toml`).
- **Test Frameworks**: `pytest` + `pytest-cov`.
- **Coverage Config**: **present** — `addopts = "-q --cov=app
  --cov-report=term-missing --cov-fail-under=80"`, `[tool.coverage.run]
  source=["app"]`, `[tool.coverage.report] fail_under=80`
  (`pyproject.toml`); asserted as configured input by
  `tests/test_config.py:141-160`.
- **Measured at scan time** (`.venv/bin/python -m pytest -q -p no:cacheprovider`,
  coverage data written to `/tmp/opencode`): **94 tests collected, 94 passed**
  (86 `def test_*` functions, expanded by parametrization), **96.03% line
  coverage** over `app/` (605 statements, 24 missed). Per-module weak spots:
  `app/session_auth.py` 85% (`84-120`, the network exchange body),
  `app/openrouter_client.py` 92% (`89-96`, `urllib_transport`),
  `app/main.py` 98% (`49`, logging fallback). All other modules 100%.
- **Offline harness**: `tests/conftest.py` — hand-rolled in-process ASGI caller
  `asgi_request()` (`:44-125`, no `httpx`/`TestClient`, deliberate under the
  dependency cap), session-scoped autouse `offline_guard` replacing
  `socket.socket.connect` with a raiser (`:128-146`), and `tmp_settings` /
  `tmp_db_path` fixtures (`:148-165`). Assertions read values back from real
  SQLite and served markup, not from mocks.
- **Test shape**: API-level via `tests/test_routes.py` (15 functions) and
  `tests/test_auth_routes.py` (12); behavioural units for db (6), repository (6),
  service (6), dummy_client (6), live_client (9), config (10), session_auth (12);
  markup contract `tests/test_page.py` (4). `app/static/app.js` is **not
  executed** by the suite (markup/route contract only — README:69-71).

### Code Quality Indicators

- **Linting**: `ruff`, configured in `pyproject.toml` (`[tool.ruff]`
  `line-length = 100`, `target-version = "py311"`; `[tool.ruff.lint] select =
  ["E","F","W","I","N","UP","S","B","C4","SIM"]` including the `S`
  security set; `extend-immutable-calls` for `fastapi.Depends`/`Query`;
  `per-file-ignores` for tests). At scan time `.venv/.../ruff check app tests`
  → **All checks passed**, and `ruff format --check app tests` → **23 files
  already formatted**. `.ruff_cache/` exists (self-ignoring).
- **CI/CD**: **none**. No workflow YAML, no `Dockerfile`, no `Makefile`, no
  `.pre-commit-config.yaml`. The only mechanical gates run locally: pytest's
  `filterwarnings = ["error"]`, the coverage floor in `addopts`, and ruff.
- **Documentation**: `README.md` (256 lines) is thorough — setup, run, modes,
  config resolution, storage/migration, full HTTP surface table, file layout,
  known limitations, and an end-to-end verify command. `AGENTS.md` is the
  AI-DLC harness onboarding. Every one of the 12 `app/*.py` modules opens with a
  docstring naming a single responsibility and citing prior-intent requirement
  ids. No `docs/` directory and no committed OpenAPI spec.
- **Runtime state**: `data/sentiment.db` is gitignored, currently schema
  `version = 2`, **0 rows**, columns
  `id, text, label, probabilities, confidence, intensity, model, provider,
  created_at`.

### Technical Debt Signals

- **R-01 — SQLite connection thread affinity (accepted, documented).**
  `get_connection` opens one connection per request inside a FastAPI
  sync-generator dependency (`app/routes.py:79-85`) and `db.connect` uses
  `sqlite3.connect(path)` with the default `check_same_thread=True`
  (`app/db.py:130`). Overlapping requests can open in one anyio worker and use
  in another → `sqlite3.ProgrammingError`. Recorded as accepted in
  `README.md:237-243` and `project.md`; no concurrency test exists.
- **Record contract has four hand-written copies.** `RECORD_FIELDS`
  (`app/models.py:25-34` — **untouched by any code**, not even imported by a
  test), the `AnalysisRecord` field declarations (`app/models.py:88-95`),
  `to_dict()`'s literal (`app/models.py:97-108`), and `ANALYSES_COLUMNS` +
  `CREATE_ANALYSES_TABLE` (`app/db.py:36-48,58-68`). Kept in sync only by tests
  (`tests/test_routes.py:27-36` declares its own private `RECORD_FIELDS`). Any
  new column must be threaded through all copies.
- **`schema_meta.version` is written but never compared.** `init_db` writes
  `SCHEMA_VERSION` (`app/db.py:115-118,153`) yet migration is driven by physical
  shape (`_is_v1_shape`, `app/db.py:186-200`), not by the recorded value.
- **Legacy `intensity` column retained** as nullable for pre-v1 rows
  (`app/db.py:43`, `app/models.py:12-14`); values are preserved, never surfaced
  (`AnalysisRecord` has no such field).
- **Browser script untested** — `app/static/app.js` (201 lines) is only asserted
  at served-markup level.
- **No secret scanner / dependency audit / lockfile.** Fake key fixtures match
  OpenRouter's real shape (`tests/test_config.py:23`,
  `tests/test_live_client.py:27`, `tests/test_auth_routes.py:25-26`,
  `tests/test_session_auth.py:26`).
- **Suppressions, all deliberate and few**: 5 × `# noqa: S310` on hardcoded-https
  stdlib URL calls (`app/openrouter_client.py:89,93`; `app/session_auth.py:88,96`),
  2 × `# type: ignore[method-assign]` (`tests/conftest.py:141,145`), 4 ×
  `# pragma: no cover` (`app/db.py:181`, `app/repository.py:20`,
  `app/routes.py:248`, `tests/test_config.py:165`). **Zero TODO/FIXME/HACK/XXX**
  anywhere in `app/` or `tests/` (grep clean).

## Handoff Summary

- **Intent-relevant finding**: The intent's whole surface already exists as
  three clean seams, and **none of the new CSV surface exists yet** (grep for
  `csv|import_id|bulk|multipart|upload` over `app/`, `tests/`, `README.md`,
  `pyproject.toml` returns nothing). (1) The engine seam is exactly where the
  intent says to plug in: `SentimentClient` Protocol
  (`app/sentiment.py:78-84`) with the offline adapter
  `DummySentimentClient.analyze` (`app/dummy_client.py:77-101`) selected in the
  single factory `service.get_client` (`app/service.py:72-90`); the per-text
  orchestration to loop over is `service.analyze_text(client, connection, text,
  now=None)` (`app/service.py:116-132`), which calls
  `repository.insert_analysis(connection, text, result, now=None)`
  (`app/repository.py:40-69`). (2) Routes are mounted from `v1_router` with
  `prefix="/v1"` (`app/routes.py:44,121`) — `POST /v1/analyses/import` and
  `GET /v1/analyses/export` slot in there; note `GET /v1/analyses` already
  exists (`app/routes.py:153`) so `/analyses/import` and `/analyses/export` are
  additive sub-paths, not a rename. (3) The schema to extend is
  `CREATE_ANALYSES_TABLE` (`app/db.py:36-48`), the pinned ordered
  `ANALYSES_COLUMNS` (`app/db.py:58-68`), the `_V1_NOT_NULL_COLUMNS` set
  (`app/db.py:72-74`), `_ADD_COLUMN_SQL` (`app/db.py:87-97`) and the explicit
  rebuild copy list `_COPY_ROWS_INTO_V1_TABLE` (`app/db.py:106-111`);
  `SCHEMA_VERSION = 2` (`app/db.py:32`) must bump. The live store is already v2
  with 0 rows, so an added `import_id` column is a normal forward migration.

- **Risks / follow-up** (facts the architect must preserve):
  1. **Four record-contract copies** (`app/models.py:25,88-95,97-108`;
     `app/db.py:36-48,58-68`) plus independent test-local field sets
     (`tests/test_routes.py:27-36`) mean adding `import_id` to the persisted
     record touches models, DDL, column tuple, insert SQL, migration copy SQL,
     `to_dict()`, `from_row()`, and several exact-field-set assertions. Decide
     explicitly whether `import_id` is part of the returned record contract or
     storage-only.
  2. **Dependency cap NFR3** (two runtime deps; asserted by
     `tests/test_config.py:141-160`) and **`python-multipart` is not installed**.
     A `multipart/form-data` file upload via `fastapi.UploadFile`/`Form` would
     add a runtime dependency and fail that test. Use the stdlib `csv` module on
     a raw request body (`text/csv`/`text/plain`) or a JSON-wrapped CSV string to
     stay within the cap.
  3. **Migration rebuild drops unincluded columns**: `_COPY_ROWS_INTO_V1_TABLE`
     lists columns explicitly (`app/db.py:106-111`); a new column not added
     there and to `ANALYSES_COLUMNS`/`_ADD_COLUMN_SQL` would be lost or abort
     the rebuild. `_is_v1_shape` compares `tuple(info) != ANALYSES_COLUMNS`, so
     bumping the tuple makes every existing v2 store rebuild — intended, but it
     means the migration must copy `import_id` too.
  4. **Tests must stay offline**: the session autouse `offline_guard`
     (`tests/conftest.py:128-146`) makes any socket connect fail; new
     import/export tests must drive `create_app(tmp_settings)` through
     `asgi_request` and read values back from real SQLite, matching the existing
     pattern (`tests/test_routes.py:42-45`). No `httpx`.
  5. **Batch failure semantics are undefined in code**: `analyze_text` writes
     nothing when a row's engine result is invalid, and raises on the first bad
     row. The intent says "analyzes each row … returns a breakdown"; the
     architect/design must decide per-row error handling (skip vs abort) and
     whether a partially-imported `import_id` is persisted, since no transaction
     boundary across rows exists today.
  6. **Export response type is new**: `app/routes.py` only builds
     `JSONResponse`/`HTMLResponse`/`RedirectResponse` (`app/routes.py:22`); a CSV
     export needs a `Response`/`PlainTextResponse` with
     `text/csv` and a `Content-Disposition`.
  7. **Stale steering**: `aidlc/spaces/default/memory/team.md` and the prior
     CodeKB store predate the merge to `main`; base the synthesis on the code at
     `4eb9b74` and re-verify counts. Prior CodeKB component names available for
     reuse (from `component-inventory.md` headings): Application Assembly,
     Configuration and Settings, Record and Request Contracts, Sentiment Engine
     Interface, Offline Dummy Engine, Live OpenRouter Engine, Session
     Authorization, Analysis Orchestration, Persistence and Schema, HTTP API
     Surface, Web UI, Test Harness and Suite.
  8. **Scan bound**: every deep path above is inside `./`; no deep read outside
     the pre-scan snapshot set.
