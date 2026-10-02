# Component Inventory — `very-cool-sentiment-analysis` (repo `sentiment-opencode`)

Twelve components, one per logical building block. Each entry states what the
component owns, the surface it exposes, what it depends on, and a health rating
against the boundary rules in **architecture.md**.

**Health ratings.** *Healthy* — single nameable responsibility, no back-channel
coupling, no shared mutable state. *Watch* — responsibility is single but a
concrete property is worth naming before extending. *At-risk* — a boundary or a
consequence an extension would inherit.

---

## Application Assembly

| | |
|---|---|
| **Files** | `app/__init__.py` (10), `app/main.py` (103) |
| **Responsibility** | Build the application and own startup. Resolve settings, bring the database schema to its current version, log the active mode exactly once, mount both routers and the static assets, register the five exception handlers, expose `app:app`. |
| **Exposes** | `create_app(settings=None, session_auth=None) -> FastAPI`; module-level `app`; `_configure_logging()`. |
| **Depends on** | `app.db`, `app.config`, `app.routes`, `app.sentiment`, `app.service`, `app.session_auth` (6) |
| **Health** | **Healthy.** The composition root, with no peers to import from and nothing importing into it except the re-export shim. It is the only component allowed to know every other component exists. |

Notes:
- `HOST = "127.0.0.1"`, `PORT = 8000` (`app/main.py:33-35`) — the only bind
  address this app is ever served on, and an affirmed project rule.
- `create_app`'s two injectable parameters exist so **no test ever reaches
  OpenRouter** and no test touches the real database.
- The lifespan does exactly four things, in order: resolve settings, build the
  session store, `db.init_db`, log. Any failure stops startup loudly rather than
  serving a half-configured app.
- `app/__init__.py` exists solely so `uvicorn app:app` resolves without naming
  `app.main`.

---

## Configuration and Settings

| | |
|---|---|
| **Files** | `app/config.py` (151) |
| **Responsibility** | Decide which sentiment engine the app runs and where its database lives, from one local TOML file, with an offline default. Hold the key, and redact it everywhere it could be rendered. |
| **Exposes** | `load_settings(config_path, db_path) -> Settings`; `Settings` (frozen dataclass, `repr=False`); `ConfigError`; `Mode` type alias; `DEFAULT_MODE`, `DEFAULT_MODEL`, `DEFAULT_CONFIG_PATH`, `DEFAULT_DB_PATH`, `FILE_MODES`, `REDACTED`. |
| **Depends on** | nothing inside `app` — a leaf. Stdlib `tomllib`, `dataclasses`, `pathlib`, `logging`. |
| **Health** | **Healthy.** A leaf with high fan-in (3 importers), which is the correct shape for a shared value object. |

Notes:
- Resolution has six documented outcomes (absent file, absent `mode`, `dummy`,
  `openrouter` + key, `openrouter` without key, unrecognised `mode`), each cited
  by rule id in the docstring.
- `mode` records the **intent**, so a file requesting live without a key yields
  `Settings(mode="live", api_key=None)` — the app still starts on the offline
  engine and refuses a submission. Intent and reality are separate fields by
  design (D1 in **architecture.md**).
- Redaction is by `__repr__`, and `__str__` is aliased to it. **Redacted means
  "not rendered", not "not obtainable"** — `api_key` is a public dataclass field,
  so `dataclasses.asdict` or a locals dump would still expose it.
- Any unrecognised `mode` value raises `ConfigError` naming the accepted values.
  That error is never mapped to an HTTP status; it is a startup failure.

---

## Record and Request Contracts

| | |
|---|---|
| **Files** | `app/models.py` (144) |
| **Responsibility** | Define the wire and storage shape of one analysis in one place, so the API contract and the stored-row contract cannot drift apart. |
| **Exposes** | `AnalyzeRequest` (dataclass); `AnalysisRecord` (frozen dataclass) with `to_dict()` and `from_row()`; `RECORD_FIELDS`; `ANALYZE_FIELDS`; `undeclared_body_fields(body)`; `UNKNOWN_PROVIDER = "unknown"`. |
| **Depends on** | nothing inside `app` — a leaf. Stdlib `json`, `dataclasses`, `collections.abc`. |
| **Health** | **Watch.** A shared contract depended on by four modules, and the contract itself exists in **four** hand-maintained copies (`RECORD_FIELDS`, the field declarations, `to_dict()`'s literal, and `ANALYSES_COLUMNS` + the DDL in `app/db.py`) — plus a fifth positional copy in the export route. They are held in sync by tests, not mechanically. TD-8 in **code-quality-assessment.md**. |

Notes:
- `ANALYZE_FIELDS` is **derived** from the dataclass via `dataclasses.fields`, so
  the declared-body set cannot drift. `RECORD_FIELDS` is hand-maintained and,
  as written, nothing in the code reads it.
- `AnalysisRecord.from_row` deliberately **does not read `intensity`**: a pre-v1
  row keeps the value in the file and it is neither surfaced nor back-filled.
- A row migrated from a store that predates `provider` reads back as the explicit
  sentinel `"unknown"` — never the string `"None"`, never a fabricated engine
  name.
- No pydantic: the codebase has **no direct pydantic import**, deliberately, to
  hold the runtime cap at two packages (A1 in **architecture.md**). The cost is
  that no response model exists, so `/openapi.json` cannot describe real shapes.

---

## Sentiment Engine Interface

| | |
|---|---|
| **Files** | `app/sentiment.py` (84) |
| **Responsibility** | Define what a sentiment engine *is*, so everything above depends on one small abstraction instead of a concrete implementation. |
| **Exposes** | `LABELS = ("positive", "negative", "neutral")`; `SentimentResult` (frozen dataclass: `label`, `probabilities`, `confidence`, `model`, `provider`); `SentimentClient` (`@runtime_checkable` `Protocol`, one method); `validate_result(result)`; `SentimentEngineError`; `SentimentAuthError`. |
| **Depends on** | nothing inside `app` — a leaf. Stdlib `dataclasses`, `typing`. |
| **Health** | **Healthy.** The highest fan-in leaf (4 importers) with zero dependencies of its own — the correct shape, and the reason both adapters are swappable. |

Notes:
- The typed result **is** the whole contract. A result that cannot be read as
  "one label from `LABELS` plus a probability for every label" is a failure,
  never a guess.
- `SentimentAuthError` subclasses `SentimentEngineError`, deliberately: the app
  drops the credential on the auth signal *alone*, and nothing else must drop it.
- `LABELS` here is the canonical closed label set, independently re-asserted as a
  `CHECK` constraint in the DDL. The two are held in sync by test, not generated.

---

## Offline Dummy Engine

| | |
|---|---|
| **Files** | `app/dummy_client.py` (101) |
| **Responsibility** | Produce a deterministic sentiment decision with no network, no credentials and no external state, so development and the whole test suite run offline by default. |
| **Exposes** | `DummySentimentClient` with `analyze(text)`; `POSITIVE_WORDS` (15 terms); `NEGATIVE_WORDS` (14 terms); `LABEL_PROBABILITIES`; `MODEL = "dummy-keyword-v1"`; `PROVIDER = "offline"`. |
| **Depends on** | `app.sentiment` only. Stdlib `re`. |
| **Health** | **Watch.** The engine itself is clean and exactly as narrow as it should be — but it is also the accidental home of `_WORD = re.compile(r"[a-z']+")` (`app/dummy_client.py:68`), the **only** tokenizer in the repository, which is underscore-private and lives in an engine rather than a shared place. TD-6 in **code-quality-assessment.md**. |

Notes:
- Classification is a keyword count: more positive than negative → `positive`,
  the reverse → `negative`, **including a tie** → `neutral`.
- Probabilities are fixed per-label triples, so the same text always yields the
  same answer. The module docstring says the engine exists to be *predictable,
  not accurate*, and that is the correct expectation to carry forward.
- Nothing in this module can fail: it has no I/O and no branch that raises.

---

## Live OpenRouter Engine

| | |
|---|---|
| **Files** | `app/openrouter_client.py` (232) |
| **Responsibility** | Call OpenRouter's Decisions API for a live typed decision, with a bounded timeout, and read the answer strictly as a typed result or fail. |
| **Exposes** | `OpenRouterJevSentimentClient(api_key, model, transport=…)`; `HttpTransport` (`Protocol`, one method); `DECISIONS_ENDPOINT`; `LIVE_TIMEOUT_SECONDS = 10.0`. |
| **Depends on** | `app.sentiment`. Stdlib `urllib.request`, `json`, `dataclasses`, `logging`. |
| **Health** | **At-risk, by design and by constraint.** It is the only component that performs real HTTP, and the two-package runtime cap forbids a client library, so it uses stdlib `urllib` and is **not importable-by-test**: every test injects a transport, leaving lines 89-96 — the actual request construction and call — uncovered. TD-9 in **code-quality-assessment.md**. |

Notes:
- Imported **only** from inside `_live_client` (`app/service.py:103`), so the
  offline path never even loads the module. This is a deliberate static/dynamic
  split of the import graph.
- The answer-reading side (`_read_choice`, `_read_score` and the label/probability
  extraction) is pure and *is* tested; only the transport body is not.
- Raises `SentimentAuthError` on HTTP 401/403 so the credential is dropped on
  that signal alone, and `SentimentEngineError` for everything else — including a
  response that carries no usable typed result.
- The endpoint is a hardcoded `https` constant, which is why the four
  `# noqa: S310` suppressions in the codebase are justified rather than blanket.
- The API key is redacted in its `__repr__` (`app/openrouter_client.py:118`).

---

## Session Authorization

| | |
|---|---|
| **Files** | `app/session_auth.py` (259) |
| **Responsibility** | Run OpenRouter's PKCE flow and hold the resulting credential in this process's memory, so the app can reach OpenRouter without the key ever touching disk. |
| **Exposes** | `SessionAuth` (`start`, `complete`, `credential`, `reason`, `disconnect`, `expire`); `SessionCredential` (frozen, `repr=False`, key redacted); `AuthExchangeError`; `create_code_verifier()`, `code_challenge_for()`, `exchange_code_at_openrouter()`; `AUTHORIZE_ENDPOINT`, `EXCHANGE_ENDPOINT`, `PKCE_METHOD = "S256"`, `PENDING_TTL_SECONDS = 600.0`, `EXCHANGE_TIMEOUT_SECONDS = 30.0`, `NOT_CONNECTED`. |
| **Depends on** | nothing inside `app` — a leaf. Stdlib `secrets`, `hashlib`, `base64`, `json`, `threading`, `time`, `urllib.*`. |
| **Health** | **Watch.** Correctly isolated — it reads and writes no file, no database, no config — but it carries its **own** `urllib` request rather than sharing `openrouter_client`'s transport, which is why lines 84-120 are also uncovered. The duplication is cohesion chosen over DRY; the cost is a second untested HTTP body. TD-9. |

Notes:
- Thread-safe by construction: `threading.Lock` guards the pending-verifier map
  and the credential, because a browser round trip can overlap any request.
- Pending verifiers are dropped on the same 600 s schedule as the authorization
  codes, so a stale browser tab cannot pin memory.
- The exchanged key is an ordinary OpenRouter key used exactly like the
  config-file key.
- Every failure path records a reason in the store, which is how the page
  reports a failure **after** a `302` — the redirect cannot carry a JSON
  envelope.

---

## Analysis Orchestration

| | |
|---|---|
| **Files** | `app/service.py` (214) |
| **Responsibility** | Turn submitted text into a persisted analysis: reject input the engine must not see, resolve and call the engine through the interface, validate the typed result, store it. |
| **Exposes** | `analyze_text`, `import_texts`, `get_client`, `effective_connection`, `require_text`, `new_import_id`, `ImportSummary` (with `to_dict()`); `InvalidTextError`; `LiveKeyMissingError`. |
| **Depends on** | `app.config`, `app.dummy_client`, `app.models`, `app.repository`, `app.sentiment`, `app.session_auth`; plus `app.openrouter_client` by **function-local** import. |
| **Health** | **Healthy.** Imports nothing from `fastapi`, so the whole of the business flow is callable without a request object. `get_client` being the sole construction site is what makes the engine swappable. |

Notes:
- The validation order W1 is enforced **twice** — in the route
  (`app/routes.py:161-162`) and in `analyze_text` (`app/service.py:211-213`) —
  so the boundary holds for the route and the bulk importer alike.
- `import_texts` reuses the exact same per-text seam, one row at a time, and
  aggregates into `ImportSummary`. This is the **existing aggregate precedent**
  in the codebase: pre-seeded `label_counts` from `LABELS`, and a
  `mean_confidence` that is `None` when nothing was imported rather than a
  fabricated `0.0`.
- `effective_connection` is the single connection-state payload — health, the
  page indicator and the startup log all read it, so they cannot disagree.
- The dispatcher never constructs a client it was not handed; the route resolves
  the client and passes it in.

---

## Persistence and Schema

| | |
|---|---|
| **Files** | `app/repository.py` (102), `app/db.py` (243) |
| **Responsibility** | Own the local database file's shape and lifecycle. `db.py` owns the connection, all DDL and the in-place migration; `repository.py` owns all DML and the row↔record mapping. |
| **Exposes (repository)** | `insert_analysis(connection, text, result, now=None, import_id=None)`, `list_analyses(connection, limit)`, `list_analyses_by_import_id(connection, import_id)`, `format_timestamp(moment)`, `DEFAULT_LIST_LIMIT = 50`. |
| **Exposes (db)** | `connect(db_path)`, `init_db(db_path)`, `SCHEMA_VERSION = 3`, `CREATE_ANALYSES_TABLE`, `CREATE_SCHEMA_META_TABLE`, `ANALYSES_COLUMNS`, plus the private migration helpers. |
| **Depends on** | `app.models` (both). `repository` reaches `SentimentResult` only under `TYPE_CHECKING` (`app/repository.py:22-23`), so it has **no runtime engine dependency**. |
| **Health** | **At-risk.** `repository.py` is the natural and uncontested home for aggregate SQL and is currently clean. `db.py` carries two verified migration defects: the rebuild **silently drops every index on `analyses`** (TD-1) and a new column on `analyses` is a five-place edit (TD-2). Both are load-bearing for the active intent's additive-schema constraint. |

Notes:
- **DDL shape (version 3):** `analyses(id INTEGER PK AUTOINCREMENT, text TEXT
  NOT NULL, label TEXT NOT NULL CHECK(label IN ('positive','negative','neutral')),
  probabilities TEXT NOT NULL, confidence REAL NOT NULL, intensity REAL,
  model TEXT NOT NULL, provider TEXT NOT NULL, created_at TEXT NOT NULL,
  import_id TEXT)` plus `schema_meta(key TEXT PK, value TEXT NOT NULL)`.
  `intensity` and `import_id` are the only nullable columns besides the key.
- **Migration strategy** (`_migrate_analyses`): add any missing column nullable in
  place, then — unless the table is *already exactly* the current shape — rebuild
  it from the current DDL and copy every row across, backfilling a missing
  `provider` with the `unknown` sentinel. The order composes so a pre-v1 store
  that both lacks `provider` and carries `intensity NOT NULL` migrates without
  either trigger aborting the other.
- `_is_v1_shape` checks **column order**, **every NOT NULL flag**, and that the
  label `CHECK` is present in the stored DDL text. A table that is merely
  *readable* as the current shape is rebuilt, so the recorded schema version
  stays truthful.
- The whole migration runs in **one transaction** and rolls back on any
  `BaseException`: a migration that cannot preserve every row fails loudly
  rather than discarding data.
- `init_db` runs on **every** startup and is idempotent — verified by running it
  twice against a migrated store.
- **Verified empirically:** a migrating store carrying
  `CREATE INDEX idx_analyses_created ON analyses(created_at)` came out of
  `init_db` with the columns correct, the row preserved (including its
  `intensity` value), the side table untouched and the version bumped to 3 — and
  `sqlite_master` reporting **zero** indexes on `analyses`. A *separate* table is
  unaffected by the rebuild.
- **Observed scope boundary:** `_COPY_ROWS_INTO_V1_TABLE` backfills only
  `provider`. A store missing a value in any *other* added column aborts the copy
  with an `IntegrityError` — which, inside the transaction, becomes a loud
  startup failure. That is the safe outcome, but it is not the same as a
  successful migration.
- The committed `data/sentiment.db` reports `schema_meta.version = 2` with no
  `import_id` column and 0 rows, so the v2 → v3 path has never run against that
  file. `/data/` is gitignored, so it is local state only.
- **No index exists on `analyses` today**, and `created_at` — the column any
  date-range aggregate would filter on — is unindexed. Its ISO-8601-Z encoding
  makes it lexicographically sortable and directly range-comparable as a string.

---

## HTTP API Surface

| | |
|---|---|
| **Files** | `app/routes.py` (387) |
| **Responsibility** | Translate HTTP requests into service calls and service failures into one consistent error envelope. Nothing else — no sentiment logic, no SQL. |
| **Exposes** | `router`, `v1_router`, `V1_PREFIX`; 11 route handlers; `error_response`; `require_declared_fields`; the four dependency providers; the five handler functions; the six machine-code constants. |
| **Depends on** | `app.db` (for `connect` only), `app.config`, `app.models`, `app.repository`, `app.sentiment`, `app.service`, `app.session_auth` (7). |
| **Health** | **Healthy, with a size caveat.** The layering holds exactly: no SQL, no engine construction, no sentiment logic. It is the largest file and the highest fan-out in the system, and it is where every new endpoint lands by default — so it is the file whose growth an extension should watch. |

Notes:
- Two routers, deliberately split: `v1_router` carries the data contract,
  `router` carries the page and `/auth/*` which carry none.
- `get_connection` is the **only** place the `sqlite3` driver and the connection
  lifecycle are touched anywhere in the codebase — and therefore also the only
  place the accepted cross-thread defect lives (TD-5). A polling page is the
  access pattern most likely to expose it.
- `get_analyses_export` writes the seven export columns by unpacking each
  `AnalysisRecord` field **by hand** rather than from `to_dict()` or
  `dataclasses.fields`, so the record shape and the export shape can silently
  drift. TD-8.
- The three `/auth/*` handlers answer with `302` redirects, never the envelope.
  That is deliberate: a browser redirect cannot carry JSON.
- `EXPORT_COLUMNS` is seven of the record's nine fields — `probabilities` and
  `import_id` are deliberately excluded.

---

## Web UI

| | |
|---|---|
| **Files** | `app/static/index.html` (193), `app/static/app.js` (201) |
| **Responsibility** | Present the submit form, the result panel, the error panel, the history list and the connection indicator, and translate user actions into the four `fetch` calls that drive them. |
| **Exposes** | Served markup and one script. Nothing else — there is no build, no bundler, no `package.json`, and no framework. |
| **Depends on** | the HTTP surface over HTTP only. No build-time or import-time dependency on anything. |
| **Health** | **At-risk, and honestly so.** The markup and the served asset are pinned by `tests/test_page.py`, but **browser-side execution of `app.js` is not driven by the suite at all**, because the two-package runtime cap forbids any browser-automation dependency. The page's own docstring says so. Any new view inherits this gap. |

Notes:
- One HTML file with inline `<style>`, one vanilla script. `const API = "/v1";`
  is the only place the version prefix appears on the client.
- 14 `data-testid` attributes across 12 test ids plus a `<template>`. Every
  interactive element carries a stable automation hook, and
  `REQUIRED_TEST_IDS` pins them.
- Accessibility affordances present: `role="alert"` on the error panel,
  `role="status"` + `aria-live="polite"` on the connection indicator and the
  result panel.
- All rendering goes through `textContent`, so there is no HTML injection sink —
  which is why the absence of a CSP is recorded as a low accepted risk rather
  than a finding.
- `GET /` re-reads `index.html` from disk on **every** request, so a markup edit
  is live without a restart.
- **There is currently no navigation link anywhere on the page.** Adding a second
  view therefore means adding a link to this markup — and `tests/test_page.py`
  asserts this markup must not contain the word `intensity`.
- `intensity` is rendered nowhere. The page shows label, confidence, the engine
  name and the per-label probabilities only.

---

## Test Harness and Suite

| | |
|---|---|
| **Files** | `tests/conftest.py` (176), `tests/test_db.py` (436), `tests/test_routes.py` (363), `tests/test_bulk_import.py` (315), `tests/test_service.py` (304), `tests/test_auth_routes.py` (259), `tests/test_repository.py` (237), `tests/test_live_client.py` (220), `tests/test_session_auth.py` (196), `tests/test_config.py` (180), `tests/test_dummy_client.py` (84), `tests/test_page.py` (77) |
| **Responsibility** | Pin the observable contract of every component above, offline, with no mock objects. |
| **Exposes** | `asgi_request`, `offline_guard`, `tmp_settings`, `tmp_db_path`; 118 test functions. |
| **Depends on** | `app.*` (as the subject under test) and `tests.conftest`. `pytest` only. |
| **Health** | **Healthy.** 118 passing, 96.02% line coverage against an 80% floor, `ruff check` and `ruff format --check` both clean, and a session-wide socket blocker that makes an accidental network call fail the run. Measured detail is in **code-quality-assessment.md**. |

Notes:
- `asgi_request` builds a raw ASGI scope, enters the lifespan and collects the
  response messages in-process. `fastapi.testclient` is **unavailable** because
  the two-package runtime cap forbids `httpx` — so this harness is the only way
  any test reaches the app, and any new endpoint test must reuse it.
- **Zero mock objects.** Every double is a hand-written class or function at a
  real seam (`FakeExchanger`, `StubTransport`, `DuckTypedClient`,
  `FailingOnBoomClient`, `IncompleteClient`, `UnsupportedLabelClient`,
  `RejectingClient`, `FailingClient`) or a `monkeypatch.setattr` on
  `app.routes.get_client`.
- No `unittest`, no `hypothesis`, no `asyncio` marker — `asgi_request` calls
  `asyncio.run` per request.
- Assertions read values back out of **real SQLite and real served markup**,
  never out of doubles.
- `tmp_path`-scoped settings and DB paths mean no test reads `config.local.toml`
  or `data/sentiment.db`, and `tests/test_config.py` shells out to
  `git check-ignore` as an executable assertion that the key file cannot be
  committed.

---

## Ownership Rules

The rules that keep these boundaries intact, each with the enforcement that
keeps it true.

| Rule | Owner | Enforcement |
|---|---|---|
| Only the HTTP layer touches `sqlite3` and the connection lifecycle | HTTP API Surface | `get_connection` is the sole call site of `db.connect` outside `db.py` |
| Only `db.py` issues DDL; only `repository.py` issues DML | Persistence and Schema | No SQL token appears in `routes.py`, `service.py`, `models.py` or `sentiment.py` |
| The engine is reached only through `SentimentClient` | Analysis Orchestration | `get_client` is the sole `SentimentClient(...)` construction site |
| Nothing below `routes.py` imports `fastapi` | every component below the edge | No `fastapi` import outside `routes.py` and `main.py` |
| One envelope construction site | HTTP API Surface | `error_response` is called by all five handlers and by the two inline `4xx` returns |
| One connection-state payload | Analysis Orchestration | health, `/auth/status` and the startup log all call `effective_connection` |
| Settings and the session store are resolved once, at startup | Application Assembly | Both are read through `app.state`, never re-resolved per request |
| The key never reaches disk or a response body | Configuration and Settings, Session Authorization | `__repr__` redaction on all three key-bearing types; `git check-ignore` asserted by test |

## Boundary Assessment

**Observed strengths.** The layering is genuinely respected rather than merely
documented — every module's docstring names what it does *not* contain, and the
code agrees. The internal import graph is acyclic and descending. No module is a
pass-through proxy. No table is written by more than one component. Shared
contracts are small, immutable value objects rather than shared mutable state.

**The four boundaries an extension should look at first**, in the order they are
likely to be touched:

1. **`app/routes.py` size** — 387 lines and growing by endpoint. The natural
   pressure point for a future split (page routes vs. data routes vs. support
   routes) is visible but not yet urgent.
2. **`app/db.py` migration correctness** — the index drop (TD-1) and the
   five-place column edit (TD-2) are the only places where an extension can
   corrupt a user's local store rather than merely fail to compile.
3. **`app.js` execution coverage** — zero. Any new page's behaviour is
   unverifiable by the suite as it stands.
4. **The contract's five copies** — TD-8. Adding a field means editing five
   places, and the export route's positional copy can drift without any test
   noticing.

Measured coverage, lint status, CI status and the full debt register are in
**code-quality-assessment.md**. Endpoint and payload reference is in
**api-documentation.md**. Module adjacency is in **dependencies.md**. Versions
are in **technology-stack.md**.