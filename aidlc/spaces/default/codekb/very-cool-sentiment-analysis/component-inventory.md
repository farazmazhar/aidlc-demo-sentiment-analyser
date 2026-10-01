# Component Inventory — `very-cool-sentiment-analysis`

> Derived from the developer scan
> (`inception/reverse-engineering/developer-scan.md`) and verified against the
> scanned source. Component names are the headings below; the scope block in
> `reverse-engineering-timestamp.md` uses them verbatim.

Each component below is a logical building block of the code in `app/` (or, for
the last two entries, of the shipped page and the test suite). Ownership is
exclusive: every scanned file belongs to exactly one component.

**Component summary.**

| Component | Owned paths | Internal deps (out) | Health |
|---|---|---|---|
| Application Assembly | `app/__init__.py`, `app/main.py` | config, db, routes, service, sentiment, session_auth | healthy |
| Configuration and Settings | `app/config.py` | none | healthy |
| Record and Request Contracts | `app/models.py` | none | healthy |
| Sentiment Engine Interface | `app/sentiment.py` | none | healthy |
| Offline Dummy Engine | `app/dummy_client.py` | sentiment | healthy |
| Live OpenRouter Engine | `app/openrouter_client.py` | sentiment | degraded (unverified by tests) |
| Session Authorization | `app/session_auth.py` | none | at-risk (scope, size, secrets) |
| Analysis Orchestration | `app/service.py` | config, dummy_client, models, repository, sentiment, session_auth, openrouter_client (lazy) | healthy |
| Persistence and Schema | `app/db.py`, `app/repository.py` | models | at-risk (connection lifecycle) |
| HTTP API Surface | `app/routes.py` | db, config, models, repository, service, sentiment, session_auth | at-risk (widest fan-out) |
| Web UI | `app/static/index.html`, `app/static/app.js` | HTTP API Surface (over HTTP only) | healthy |
| Test Harness and Suite | `tests/` | all application components (imports and in-process ASGI) | healthy (with a named gap) |

```
+---------------------------------------------------------------------+
| Application Assembly  --> HTTP API Surface --> Analysis Orchestration|
|        |                        |                    |              |
|        |                        |                    +--> Sentiment |
|        |                        |                    |    Engine   |
|        |                        |                    |    Interface |
|        |                        |                    |      ^     ^ |
|        |                        |                    |      |     | |
|        |                        |                    |   Dummy  Live |
|        |                        |                    |         |    |
|        |                        +--> Session Authorization     |    |
|        |                        +--> Persistence and Schema     |    |
|        +--> Configuration and Settings                          |    |
+---------------------------------------------------------------------+
   Web UI (browser) --HTTP--> HTTP API Surface        OpenRouter <--+
```

## Application Assembly

- **Responsibility**: assemble the running application — resolve settings at
  startup, create the database schema, log the active mode exactly once, include
  the router, mount the static assets, wire the four exception handlers, and
  re-export the ASGI object so `uvicorn app:app` resolves.
- **Owned paths**: `app/__init__.py` (10 lines), `app/main.py` (101 lines).
- **Provided contract**: `create_app(settings=None, session_auth=None)`, the
  module-level `app = create_app()`, `HOST = "127.0.0.1"`, `PORT = 8000`
  (`app/main.py:35-36,53-101`); `app` re-export (`app/__init__.py:8`).
- **Depends on**: Configuration and Settings, Persistence and Schema, HTTP API
  Surface, Analysis Orchestration, Sentiment Engine Interface, Session
  Authorization.
- **Consumed by**: `uvicorn`, the test harness, `app/__init__.py`.
- **Health**: healthy. Two documented wrinkles: the app is constructed at import
  time (`app/main.py:101`), so importing any submodule builds a FastAPI app as a
  side effect; and the comment at `app/main.py:33-34` still claims no auth flow
  exists, which the auth routes contradict.
- **Evidence**: `app/main.py:33-36,53-101`, `app/__init__.py:1-10`.

## Configuration and Settings

- **Responsibility**: decide which sentiment engine the app runs and where its
  database lives, from one optional local TOML file, with an offline default;
  hold the API key and never expose it in a `repr` or a log line.
- **Owned paths**: `app/config.py` (125 lines).
- **Provided contract**: `Settings` (frozen dataclass, key-redacting `__repr__`),
  `ConfigError`, `load_settings(config_path, db_path)` implementing six ordered
  rules, `MODES`, `DEFAULT_MODE`/`DEFAULT_MODEL`/`DEFAULT_CONFIG_PATH`/
  `DEFAULT_DB_PATH`, `REDACTED`.
- **Depends on**: nothing internal (stdlib `tomllib`, `dataclasses`, `pathlib`).
- **Consumed by**: Application Assembly, HTTP API Surface, Analysis
  Orchestration.
- **Health**: healthy. Rule 5 (live mode without a key starts unconnected) is a
  deliberate amendment over the earlier fail-fast rule and the single largest
  semantic difference from the v1 intent (D-2 in `business-overview.md`).
- **Evidence**: `app/config.py:19-125`, `tests/test_config.py`.

## Record and Request Contracts

- **Responsibility**: define the wire and storage shape of one analysis in a
  single place so the API contract and the stored-row contract cannot drift.
- **Owned paths**: `app/models.py` (94 lines).
- **Provided contract**: `RECORD_FIELDS` (the pinned nine-field order),
  `AnalyzeRequest` (request body), `AnalysisRecord` with `to_dict()` and
  `from_row()`.
- **Depends on**: nothing internal (stdlib `json`, `dataclasses`, `typing` only —
  deliberately, so `app/` gains no direct pydantic dependency).
- **Consumed by**: Persistence and Schema, Analysis Orchestration, HTTP API
  Surface.
- **Health**: healthy, with a maintenance risk: the same nine fields are written
  out four times (`RECORD_FIELDS`, the `to_dict` mapping, `ANALYSES_COLUMNS`, the
  SQL DDL), kept aligned only by tests.
- **Evidence**: `app/models.py:19-93`, `app/db.py:18-48`, `tests/test_repository.py`.

## Sentiment Engine Interface

- **Responsibility**: define what a sentiment engine *is*, so everything above
  it depends on one small abstraction instead of a concrete implementation.
- **Owned paths**: `app/sentiment.py` (61 lines).
- **Provided contract**: `LABELS`, frozen `SentimentResult`, `SentimentEngineError`,
  `SentimentAuthError`, `@runtime_checkable SentimentClient` Protocol with
  `analyze(text) -> SentimentResult`.
- **Depends on**: nothing internal.
- **Consumed by**: both engines (they implement it), Analysis Orchestration,
  HTTP API Surface, Persistence (typing only, under `TYPE_CHECKING`), Application
  Assembly.
- **Health**: healthy. This is the seam the whole design rests on: swapping the
  engine touches no other component (NFR5).
- **Evidence**: `app/sentiment.py:1-61`, `app/service.py:60-82`.

## Offline Dummy Engine

- **Responsibility**: produce a deterministic sentiment decision with no
  network, no credentials and no external state, so development and the whole
  test suite run offline by default.
- **Owned paths**: `app/dummy_client.py` (106 lines).
- **Provided contract**: `DummyClient.analyze(text)`; constants
  `POSITIVE_WORDS` (15 entries), `NEGATIVE_WORDS` (14), `LABEL_PROBABILITIES`
  (fixed triples), `INTENSITY_BY_LABEL` (±0.6 / 0.0), `MODEL = "dummy-keyword-v1"`,
  `PROVIDER = "local-dummy"`.
- **Depends on**: Sentiment Engine Interface.
- **Consumed by**: Analysis Orchestration (default engine).
- **Health**: healthy. Intentionally low fidelity: keyword counting over a tiny
  word list, fixed probabilities and fixed intensity, so stored dummy-mode rows
  carry no real signal and are not comparable with live-mode rows.
- **Evidence**: `app/dummy_client.py:16-106`, `tests/test_dummy_client.py`.

## Live OpenRouter Engine

- **Responsibility**: turn one piece of text into a typed `SentimentResult` by
  asking the Jev model a Choice question and a Score question through the
  OpenRouter Decisions API, reading only the typed answer fields, and raising
  instead of guessing when the typed result is unavailable.
- **Owned paths**: `app/openrouter_client.py` (250 lines).
- **Provided contract**: `OpenRouterClient(api_key, model, timeout).analyze(text)`,
  `ENDPOINT`, `DEFAULT_MODEL`, `AUTH_REJECTED_STATUSES = {401, 403}`,
  `PROVIDER = "openrouter"`, typed-reading helpers `_read_choice` / `_read_score`.
- **Depends on**: Sentiment Engine Interface (stdlib `urllib` for transport).
- **Consumed by**: Analysis Orchestration, by lazy import inside `get_client()`.
- **Health**: degraded — the module is never imported, constructed or called by
  any test, by construction of the offline guard; there is no coverage
  measurement that would notice a regression in it.
- **Evidence**: `app/openrouter_client.py:1-250`, `README.md` ("Notes"),
  `tests/conftest.py:129-146` (the guard that makes the gap structural).

## Session Authorization

- **Responsibility**: hold the session's OpenRouter connection — an in-app
  PKCE (S256) authorization flow whose credential lives in process memory only —
  and expose the credential, its absence reason and the pending-verifier state
  under one lock.
- **Owned paths**: `app/session_auth.py` (263 lines — the largest module).
- **Provided contract**: `SessionAuth` with `start()`, `complete()`,
  `credential()`, `reason()`, `expire()`, `disconnect()`; `SessionCredential`
  (key-redacting `__repr__`); `AuthExchangeError`; `create_code_verifier()`,
  `code_challenge_for()`, `exchange_code_at_openrouter()`, `PENDING_TTL_SECONDS
  = 600`.
- **Depends on**: nothing internal (stdlib `hashlib`, `base64`, `secrets`,
  `threading`, `time`, `urllib`, `json`).
- **Consumed by**: Application Assembly (constructs the store), HTTP API Surface
  (auth routes, `/health`), Analysis Orchestration (credential precedence).
- **Health**: at-risk. It is the largest module, it is the code the v1 intent
  does not ask for (D-1 in `business-overview.md`), and it holds live secrets in
  memory. Its exchange call is injectable (`exchanger`, `clock`), which is why
  24 tests can cover it without network access.
- **Evidence**: `app/session_auth.py:40-263`, `app/routes.py:125-167`,
  `tests/test_session_auth.py`, `tests/test_auth_routes.py`.

## Analysis Orchestration

- **Responsibility**: turn submitted text into a persisted analysis — reject
  input the engine must not see, choose and build the engine, call it through
  the interface, and store the result.
- **Owned paths**: `app/service.py` (104 lines).
- **Provided contract**: `analyze_text(client, connection, text, now=None)`,
  `get_client(settings, credential=None)` (the only place a concrete engine is
  built), `effective_connection(settings, credential, reason)`,
  `InvalidTextError`.
- **Depends on**: Configuration and Settings, Offline Dummy Engine, Record and
  Request Contracts, Persistence and Schema, Sentiment Engine Interface, Session
  Authorization, and the Live OpenRouter Engine by lazy import.
- **Consumed by**: HTTP API Surface, Application Assembly.
- **Health**: healthy. It is the component that decides credential precedence
  (`session` beats `config`) and therefore the one place where the page's
  indicator and the engine in use cannot disagree.
- **Evidence**: `app/service.py:31-104`, `tests/test_service.py`.

## Persistence and Schema

- **Responsibility**: own the shape and lifecycle of the local database file and
  translate between a sentiment result and `analyses` rows, handing back records
  read out of the database rather than echoed payloads.
- **Owned paths**: `app/db.py` (83 lines), `app/repository.py` (80 lines).
- **Provided contract**: `db.connect()` (creates the parent directory, sets
  `sqlite3.Row`, enables foreign keys), `db.init_db()` (idempotent
  `CREATE TABLE IF NOT EXISTS` for `analyses` + `schema_meta`, writes
  `SCHEMA_VERSION = 1`), `db.ANALYSES_COLUMNS`; `repository.insert_analysis()`,
  `repository.list_analyses(limit=50)`, `repository.format_timestamp()`,
  `DEFAULT_LIST_LIMIT`.
- **Depends on**: Record and Request Contracts (and Sentiment only under
  `TYPE_CHECKING`).
- **Consumed by**: HTTP API Surface, Analysis Orchestration, Application
  Assembly.
- **Health**: at-risk. One short-lived connection per request with default
  thread affinity (`check_same_thread=True`, no `timeout`, no WAL) — the prior
  intent recorded the risk and accepted it; there is also no version-aware
  migration path, only `CREATE TABLE IF NOT EXISTS`, while `data/sentiment.db`
  already holds 12 rows at schema version 1.
- **Evidence**: `app/db.py:14-83`, `app/repository.py:24-80`,
  `app/routes.py:70-76`, `aidlc/spaces/default/memory/project.md` (Corrections).

## HTTP API Surface

- **Responsibility**: provide the whole HTTP surface — the page, the analysis
  API, the health/status endpoints, the four auth routes — and map every failure
  onto the single error envelope.
- **Owned paths**: `app/routes.py` (221 lines).
- **Provided contract**: `router` (8 routes), `error_response()`, the four error
  codes (`VALIDATION_FAILED`, `INVALID_TEXT`, `SENTIMENT_ENGINE_ERROR`,
  `AUTH_EXPIRED`), the `get_settings` / `get_session_auth` / `get_connection`
  dependencies, and the four handler functions registered in `create_app()`.
- **Depends on**: Persistence and Schema, Configuration and Settings, Record and
  Request Contracts, Analysis Orchestration, Sentiment Engine Interface, Session
  Authorization.
- **Consumed by**: Application Assembly; the Web UI over HTTP.
- **Health**: at-risk mainly by breadth: page serving, the analysis API, the auth
  endpoints and exception mapping share one file, and it is the widest fan-out
  in the system. See `api-documentation.md` for the full contract.
- **Evidence**: `app/routes.py:29-221`, `tests/test_routes.py`,
  `tests/test_auth_routes.py`, `tests/test_page.py`.

## Web UI

- **Responsibility**: the single page — submit form, result panel, error panel,
  history list and the fixed-position OpenRouter connection indicator — and its
  behaviour: `fetch()` calls, rendering and indicator polling. The script only
  displays what the API returns; it never decides a label, probability or
  intensity itself.
- **Owned paths**: `app/static/index.html` (185 lines), `app/static/app.js`
  (175 lines); shipped as package data (`[tool.setuptools.package-data]
  app = ["static/*"]`).
- **Provided contract**: stable `data-testid` hooks used by the tests
  (`analyze-form`, `analyze-input`, `analyze-submit-button`, `result-panel`,
  `result-label`, `result-confidence`, `result-intensity`, `result-probabilities`,
  `error-panel`, `history-list`, `history-empty`, `history-item`,
  `connection-status`, `connection-status-text`) and five endpoints it calls:
  `/analyze`, `/analyses?limit=50`, `/auth/status`, `/auth/openrouter/start`,
  `/auth/disconnect`.
- **Depends on**: HTTP API Surface, over HTTP only (no bundler, no framework).
- **Consumed by**: the local user's browser.
- **Health**: healthy, with one measurement gap: the page is verified at the
  served-markup level only — browser-side execution of `app.js` is not executed
  by any test, because no browser-automation dependency is permitted.
- **Evidence**: `app/static/index.html:104-185`, `app/static/app.js:25-175`,
  `tests/test_page.py`, `README.md` ("Notes").

## Test Harness and Suite

- **Responsibility**: verify the application offline — one `conftest.py`
  providing a hand-rolled in-process ASGI caller, a session-wide socket-blocking
  offline guard, and temp-path fixtures, plus nine per-module test files.
- **Owned paths**: `tests/` (10 files, 1 407 lines, 52 test functions, 5
  fixtures).
- **Provided contract**: `asgi_request()`, `AsgiResponse`, the session-scoped
  autouse `offline_guard`, `tmp_settings`, `tmp_db_path`, and the per-file `app`
  fixtures in `test_routes.py` / `test_page.py`.
- **Depends on**: every application component it imports or drives in-process.
- **Consumed by**: `pytest` (`testpaths = ["tests"]`, `addopts = "-q"`,
  `filterwarnings = ["error"]` in `pyproject.toml`).
- **Health**: healthy, with one named gap: `app/openrouter_client.py` has no
  coverage at all, and no coverage tooling or floor exists to detect that
  (`code-quality-assessment.md`).
- **Evidence**: `tests/conftest.py:1-168`, `tests/test_*.py`,
  `pyproject.toml` (`[tool.pytest.ini_options]`).

**Ownership rules that follow from these boundaries.**

1. `SentimentClient` implementations own nothing but the decision; they must not
   persist, log the key, or know about HTTP (`app/sentiment.py:1-8`).
2. Only Analysis Orchestration may choose an engine
   (`app/service.py:60-82`); only Persistence and Schema may write SQL
   (`app/repository.py`, `app/db.py`).
3. Only the HTTP API Surface may translate a domain error into a status code and
   the error envelope (`app/routes.py:173-221`).
4. Secrets live in exactly two objects, both redacting (`Settings`,
   `SessionCredential`), and nowhere else.
