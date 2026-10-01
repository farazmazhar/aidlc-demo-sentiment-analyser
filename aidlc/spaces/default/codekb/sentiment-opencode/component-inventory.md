# Component Inventory — `sentiment-opencode`

> Derived from the developer scan (`inception/reverse-engineering/developer-scan.md`)
> and verified against the source at HEAD
> `4eb9b74c4197114181dab641c177c569f2058c24`. Component names are the headings
> below; the Scope of Analysis block in `reverse-engineering-timestamp.md` uses
> them **verbatim**.

Each component is a logical building block of the code in `app/` (or, for the
last two headings, of the shipped page and the test suite). Ownership is
exclusive: every scanned file belongs to exactly one component.

**Component summary.**

| Component | Owned paths | Internal deps (out) | Health |
|---|---|---|---|
| Application Assembly | `app/__init__.py`, `app/main.py` | config, db, routes, service, sentiment, session_auth | healthy |
| Configuration and Settings | `app/config.py` | none | healthy |
| Record and Request Contracts | `app/models.py` | none | healthy (contract duplicated 4×) |
| Sentiment Engine Interface | `app/sentiment.py` | none | healthy |
| Offline Dummy Engine | `app/dummy_client.py` | sentiment | healthy |
| Live OpenRouter Engine | `app/openrouter_client.py` | sentiment | healthy (never network-run in suite) |
| Session Authorization | `app/session_auth.py` | none | at-risk (largest module, holds secrets) |
| Analysis Orchestration | `app/service.py` | config, dummy_client, models, repository, sentiment, session_auth, openrouter_client (lazy) | healthy |
| Persistence and Schema | `app/db.py`, `app/repository.py` | models | at-risk (connection lifecycle) |
| HTTP API Surface | `app/routes.py` | db, config, models, repository, service, sentiment, session_auth | at-risk (widest fan-out) |
| Web UI | `app/static/index.html`, `app/static/app.js` | HTTP API Surface (over HTTP only) | healthy (browser script untested) |
| Test Harness and Suite | `tests/` | all application components (imports + in-process ASGI) | healthy (with named gaps) |

```
+---------------------------------------------------------------------+
| Application Assembly --> HTTP API Surface --> Analysis Orchestration|
|        |                        |                    |              |
|        |                        |                    +--> Sentiment  |
|        |                        |                    |    Engine    |
|        |                        |                    |    Interface |
|        |                        |                    |      ^    ^  |
|        |                        |                    |      |    |  |
|        |                        |                    |  Dummy  Live |
|        |                        |                    |         |    |
|        |                        +--> Session Authorization     |    |
|        |                        +--> Persistence and Schema    |    |
|        +--> Configuration and Settings                       |    |
+---------------------------------------------------------------------+
   Web UI (browser) --HTTP--> HTTP API Surface   OpenRouter <---+
```

## Application Assembly

- **Responsibility**: assemble the running application — resolve settings at
  startup, create/migrate the database, log the active mode exactly once, mount
  the versioned API, the page and the static assets, wire the five exception
  handlers, and re-export the ASGI object so `uvicorn app:app` resolves.
- **Owned paths**: `app/__init__.py` (10 lines), `app/main.py` (103 lines).
- **Provided contract**: `create_app(settings=None, session_auth=None)`
  (`app/main.py:52-100`), the module-level `app = create_app()`
  (`app/main.py:103`), `HOST = "127.0.0.1"` and `PORT = 8000`
  (`app/main.py:36-37`); `app` re-export (`app/__init__.py:8-10`).
- **Depends on**: Configuration and Settings, Persistence and Schema, HTTP API
  Surface, Analysis Orchestration, Sentiment Engine Interface, Session
  Authorization.
- **Consumed by**: `uvicorn`, the test harness, `app/__init__.py`.
- **Health**: healthy. Two documented wrinkles: the app is constructed at import
  time (`app/main.py:103`), so importing any submodule builds a FastAPI app as a
  side effect; and the comment at `app/main.py:33-34` still claims no auth flow
  exists, which the `/auth/*` routes contradict.
- **Evidence**: `app/main.py:33-103`, `app/__init__.py:1-10`.

## Configuration and Settings

- **Responsibility**: decide which engine the app runs and where its database
  lives, from one optional local TOML file, with an offline default; hold the API
  key and never expose it in a `repr` or a log line.
- **Owned paths**: `app/config.py` (151 lines).
- **Provided contract**: `Settings` (frozen dataclass, key-redacting `__repr__`),
  `ConfigError`, `load_settings(config_path, db_path)` implementing six ordered
  rules, `Mode`, `FILE_MODES`, `DEFAULT_MODE`/`DEFAULT_MODEL`/
  `DEFAULT_CONFIG_PATH`/`DEFAULT_DB_PATH`, `REDACTED`.
- **Depends on**: nothing internal (stdlib `tomllib`, `dataclasses`, `pathlib`,
  `logging`).
- **Consumed by**: Application Assembly, HTTP API Surface, Analysis
  Orchestration.
- **Health**: healthy. Rule 5 (live mode without a key starts unconnected and
  refuses a submission) is a deliberate amendment over an earlier fail-fast rule
  and is the largest semantic nuance in mode resolution.
- **Evidence**: `app/config.py:19-151`, `tests/test_config.py`.

## Record and Request Contracts

- **Responsibility**: define the wire and storage shape of one analysis in a
  single place so the API contract and the stored-row contract cannot drift.
- **Owned paths**: `app/models.py` (133 lines).
- **Provided contract**: `AnalyzeRequest{text}`, `ANALYZE_FIELDS`,
  `undeclared_body_fields(body)`, `AnalysisRecord` with `to_dict()` and
  `from_row()`, `RECORD_FIELDS`, `UNKNOWN_PROVIDER = "unknown"`.
- **Depends on**: nothing internal (stdlib `json`, `dataclasses`, `typing`
  only — deliberately, so `app/` gains no direct pydantic dependency).
- **Consumed by**: Persistence and Schema, Analysis Orchestration, HTTP API
  Surface.
- **Health**: healthy, with a maintenance risk: the same field set is written
  out four times (`RECORD_FIELDS`, the `AnalysisRecord` declarations,
  `to_dict()`, and `ANALYSES_COLUMNS` + DDL), kept aligned only by tests.
  `RECORD_FIELDS` itself is not referenced by any code or test.
- **Evidence**: `app/models.py:19-133`, `app/db.py:36-68`, `tests/test_routes.py:27-36`.

## Sentiment Engine Interface

- **Responsibility**: define what a sentiment engine *is*, so everything above
  it depends on one small abstraction instead of a concrete implementation.
- **Owned paths**: `app/sentiment.py` (84 lines).
- **Provided contract**: `LABELS`, frozen `SentimentResult`, `SentimentEngineError`,
  `SentimentAuthError`, `validate_result(result)`, `@runtime_checkable
  SentimentClient` Protocol with `analyze(text) -> SentimentResult`.
- **Depends on**: nothing internal.
- **Consumed by**: both engines (they implement it), Analysis Orchestration,
  HTTP API Surface, Persistence (typing only, under `TYPE_CHECKING`), Application
  Assembly.
- **Health**: healthy. This is the seam the whole design rests on: swapping the
  engine touches no other component (NFR5).
- **Evidence**: `app/sentiment.py:1-84`, `app/service.py:72-90`.

## Offline Dummy Engine

- **Responsibility**: produce a deterministic sentiment decision with no
  network, no credentials and no external state, so development and the whole
  test suite run offline by default.
- **Owned paths**: `app/dummy_client.py` (101 lines).
- **Provided contract**: `DummySentimentClient.analyze(text)`; constants
  `POSITIVE_WORDS` (15 entries), `NEGATIVE_WORDS` (14), `LABEL_PROBABILITIES`
  (fixed triples), `MODEL = "dummy-keyword-v1"`, `PROVIDER = "offline"`.
- **Depends on**: Sentiment Engine Interface.
- **Consumed by**: Analysis Orchestration (default engine).
- **Health**: healthy. Intentionally low fidelity: keyword counting over a tiny
  word list with fixed probabilities, so dummy-mode rows carry no real signal
  and are not comparable with live-mode rows.
- **Evidence**: `app/dummy_client.py:16-101`, `tests/test_dummy_client.py`.

## Live OpenRouter Engine

- **Responsibility**: turn one piece of text into a typed `SentimentResult` by
  asking the Jev model a Choice question through the OpenRouter Decisions API,
  reading only typed answer fields, and raising instead of guessing when a typed
  result is unavailable.
- **Owned paths**: `app/openrouter_client.py` (232 lines).
- **Provided contract**: `OpenRouterJevSentimentClient(api_key, model, transport,
  timeout).analyze(text)`, `HttpTransport` Protocol, `urllib_transport`,
  `ENDPOINT`, `DEFAULT_MODEL`, `LIVE_TIMEOUT_SECONDS = 10.0`,
  `AUTH_REJECTED_STATUSES = {401, 403}`, `PROVIDER = "openrouter"`, typed-reading
  helper `_read_choice`.
- **Depends on**: Sentiment Engine Interface (stdlib `urllib` for transport).
- **Consumed by**: Analysis Orchestration, by lazy import inside `get_client()`.
- **Health**: healthy in code terms; the production transport is never executed
  by the suite (the `offline_guard` makes that structural). The typed reading and
  the request builder are covered through the injected transport.
- **Evidence**: `app/openrouter_client.py:1-232`, `tests/test_live_client.py`,
  `tests/conftest.py:128-146`.

## Session Authorization

- **Responsibility**: hold the session's OpenRouter connection — an in-app PKCE
  (S256) authorization flow whose credential lives in process memory only — and
  expose the credential, its absence reason and the pending-verifier state under
  one lock.
- **Owned paths**: `app/session_auth.py` (259 lines — the largest module).
- **Provided contract**: `SessionAuth` with `start()`, `complete()`,
  `credential()`, `reason()`, `expire()`, `disconnect()`; `SessionCredential`
  (key-redacting `__repr__`); `AuthExchangeError`; `create_code_verifier()`,
  `code_challenge_for()`, `exchange_code_at_openrouter()`,
  `AUTHORIZE_ENDPOINT`, `EXCHANGE_ENDPOINT`, `PENDING_TTL_SECONDS = 600`,
  `EXCHANGE_TIMEOUT_SECONDS = 30`.
- **Depends on**: nothing internal (stdlib `hashlib`, `base64`, `secrets`,
  `threading`, `time`, `urllib`, `json`).
- **Consumed by**: Application Assembly (constructs the store), HTTP API Surface
  (auth routes, health), Analysis Orchestration (credential precedence).
- **Health**: at-risk. It is the largest module and it holds live secrets in
  memory. Its exchange call and clock are injectable, which is why the flow can
  be covered without network access.
- **Evidence**: `app/session_auth.py:1-259`, `app/routes.py:189-231`,
  `tests/test_session_auth.py`, `tests/test_auth_routes.py`.

## Analysis Orchestration

- **Responsibility**: turn submitted text into a persisted analysis — reject
  input the engine must not see, choose and build the engine, call it through the
  interface, validate the result, and store it.
- **Owned paths**: `app/service.py` (132 lines).
- **Provided contract**: `analyze_text(client, connection, text, now=None)`,
  `get_client(settings, credential=None)` (the only place a concrete engine is
  built), `effective_connection(settings, credential, reason)`, `require_text`,
  `InvalidTextError`, `LiveKeyMissingError`.
- **Depends on**: Configuration and Settings, Offline Dummy Engine, Record and
  Request Contracts, Persistence and Schema, Sentiment Engine Interface, Session
  Authorization, and the Live OpenRouter Engine by lazy import.
- **Consumed by**: HTTP API Surface, Application Assembly.
- **Health**: healthy. It is the component that decides credential precedence
  (`session` beats `config`) and therefore the one place where the page's
  indicator and the engine in use cannot disagree.
- **Evidence**: `app/service.py:31-132`, `tests/test_service.py`.

## Persistence and Schema

- **Responsibility**: own the shape and lifecycle of the local database file,
  bring an older store to the current contract without losing a row, and
  translate between a sentiment result and `analyses` rows, handing back records
  read out of the database rather than echoed payloads.
- **Owned paths**: `app/db.py` (234 lines), `app/repository.py` (79 lines).
- **Provided contract**: `db.connect(db_path)`, `db.init_db(db_path)`,
  `db.SCHEMA_VERSION = 2`, `db.CREATE_ANALYSES_TABLE`, `db.ANALYSES_COLUMNS`,
  the migration internals (`_is_v1_shape`, `_migrate_analyses`,
  `_rebuild_analyses`, `_ADD_COLUMN_SQL`, `_COPY_ROWS_INTO_V1_TABLE`);
  `repository.insert_analysis()`, `repository.list_analyses(limit=50)`,
  `repository.format_timestamp()`, `DEFAULT_LIST_LIMIT`.
- **Depends on**: Record and Request Contracts (and Sentiment only under
  `TYPE_CHECKING`).
- **Consumed by**: HTTP API Surface, Analysis Orchestration, Application
  Assembly.
- **Health**: at-risk. One short-lived connection per request with default
  thread affinity (`check_same_thread=True`, no `timeout`, no WAL) — a recorded,
  accepted risk (R-01). The migration rebuild copies an explicit column list, so
  a new column not threaded through `ANALYSES_COLUMNS` / `_ADD_COLUMN_SQL` /
  `_COPY_ROWS_INTO_V1_TABLE` would be lost or abort the rebuild.
- **Evidence**: `app/db.py:14-234`, `app/repository.py:24-79`,
  `app/routes.py:79-85`, `README.md:237-243`.

## HTTP API Surface

- **Responsibility**: provide the whole HTTP surface — the page, the versioned
  analysis API, the health/status endpoints, the four auth routes — and map every
  failure onto the single error envelope.
- **Owned paths**: `app/routes.py` (282 lines).
- **Provided contract**: `router` (unversioned page/support routes), `v1_router`
  (`prefix="/v1"`, three data routes), `error_response()`, the five machine codes
  (`VALIDATION_FAILED`, `INVALID_TEXT`, `LIVE_KEY_MISSING`,
  `SENTIMENT_ENGINE_ERROR`, `AUTH_EXPIRED`), the `get_settings` /
  `get_session_auth` / `get_connection` dependencies, `require_declared_fields`,
  and the five handler functions registered in `create_app()`.
- **Depends on**: Persistence and Schema, Configuration and Settings, Record and
  Request Contracts, Analysis Orchestration, Sentiment Engine Interface, Session
  Authorization.
- **Consumed by**: Application Assembly; the Web UI over HTTP.
- **Health**: at-risk mainly by breadth: page serving, the analysis API, the auth
  endpoints and exception mapping share one file, and it is the widest fan-out in
  the system. See `api-documentation.md` for the full contract.
- **Evidence**: `app/routes.py:29-282`, `tests/test_routes.py`,
  `tests/test_auth_routes.py`, `tests/test_page.py`.

## Web UI

- **Responsibility**: the single page — submit form, result panel, error panel,
  history list and the connection indicator — and its behaviour: `fetch()` calls,
  rendering and indicator polling. The script only displays what the API returns;
  it never decides a label, probability or confidence itself.
- **Owned paths**: `app/static/index.html` (193 lines), `app/static/app.js`
  (201 lines); shipped as package data (`[tool.setuptools.package-data]
  app = ["static/*"]`).
- **Provided contract**: stable `data-testid` hooks used by the tests
  (`analyze-form`, `analyze-input`, `analyze-submit-button`, `result-panel`,
  `result-label`, `result-confidence`, `result-engine`, `result-probabilities`,
  `error-panel`, `history-list`, `history-empty`, `history-item`,
  `connection-status`, `connection-status-text`) and the endpoints it calls:
  `/v1/analyze`, `/v1/analyses?limit=50`, `/v1/health`, `/auth/openrouter/start`,
  `/auth/disconnect`.
- **Depends on**: HTTP API Surface, over HTTP only (no bundler, no framework).
- **Consumed by**: the local user's browser.
- **Health**: healthy, with one measurement gap: the page is verified at the
  served-markup level only; browser-side execution of `app.js` is not driven by
  any test, because no browser-automation dependency is permitted.
- **Evidence**: `app/static/index.html`, `app/static/app.js:1-201`,
  `tests/test_page.py`, `README.md:69-71`.

## Test Harness and Suite

- **Responsibility**: verify the application offline — one `conftest.py`
  providing a hand-rolled in-process ASGI caller, a session-wide socket-blocking
  offline guard, and temp-path fixtures, plus ten per-module test files.
- **Owned paths**: `tests/` (11 files, 2,303 lines, 86 `def test_*` functions
  expanding to 94 tests, 5 fixtures).
- **Provided contract**: `asgi_request()`, `AsgiResponse`, the session-scoped
  autouse `offline_guard`, `tmp_settings`, `tmp_db_path`, and the per-file `app`
  fixtures in `test_routes.py` / `test_page.py`.
- **Depends on**: every application component it imports or drives in-process.
- **Consumed by**: `pytest` (`testpaths = ["tests"]`, coverage addopts,
  `filterwarnings = ["error"]` in `pyproject.toml`).
- **Health**: healthy, with named gaps: the production HTTP transport of the live
  engine is never executed, `app/static/app.js` is not executed, and there is no
  concurrency test (mapping to the accepted R-01). Details in
  `code-quality-assessment.md`.
- **Evidence**: `tests/conftest.py:1-165`, `tests/test_*.py`,
  `pyproject.toml` (`[tool.pytest.ini_options]`).

## Ownership Rules

1. `SentimentClient` implementations own nothing but the decision; they must not
   persist, log the key, or know about HTTP (`app/sentiment.py:1-8`).
2. Only Analysis Orchestration may choose an engine (`app/service.py:72-90`);
   only Persistence and Schema may write SQL (`app/db.py`, `app/repository.py`).
3. Only the HTTP API Surface may translate a domain error into a status code and
   the error envelope (`app/routes.py:56-66,237-282`).
4. Secrets live in exactly two objects, both redacting (`Settings`,
   `SessionCredential`), and nowhere else.
