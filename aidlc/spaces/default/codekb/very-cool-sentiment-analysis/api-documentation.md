# API Documentation — `very-cool-sentiment-analysis`

> Derived from the developer scan
> (`inception/reverse-engineering/developer-scan.md`) and verified against the
> route handlers. The app is served on `127.0.0.1:8000` only
> (`app/main.py:35-36`); there is no remote caller, no versioning prefix and no
> authentication on the API itself.

## 1. Internal HTTP Surface (FastAPI)

`router = APIRouter()` is declared in `app/routes.py:79` and included by
`create_app()` (`app/main.py:90`); a `StaticFiles` mount covers `/static`
(`app/main.py:91`). Eight routes total.

| # | Method | Path | Handler | Request | Success response | Failure responses |
|---|---|---|---|---|---|---|
| 1 | `GET` | `/` | `index` (`app/routes.py:83`) | — | `200` `text/html`, `app/static/index.html` served verbatim | — |
| 2 | `POST` | `/analyze` | `post_analyze` (`app/routes.py:89`) | JSON body `AnalyzeRequest` `{"text": "<string>"}` | `200` with the stored `AnalysisRecord` as JSON | `422 VALIDATION_FAILED` (body rejected by the framework), `422 INVALID_TEXT` (empty or whitespace-only), `502 SENTIMENT_ENGINE_ERROR`, `502 AUTH_EXPIRED` |
| 3 | `GET` | `/analyses` | `get_analyses` (`app/routes.py:102`) | query `limit` (int, `>= 1`, default `50`) | `200` `{"analyses": [AnalysisRecord, ...]}` newest-first | `422 VALIDATION_FAILED` with detail `field = "query.limit"` |
| 4 | `GET` | `/health` | `health` (`app/routes.py:113`) | — | `200` `{"status": "ok", connected, source, mode, model, reason}` | — |
| 5 | `GET` | `/auth/status` | `auth_status` (`app/routes.py:129`) | — | `200` the same `effective_connection` payload as `/health` without `status` | — |
| 6 | `GET` | `/auth/openrouter/start` | `auth_start` (`app/routes.py:138`) | — | `302` to `https://openrouter.ai/auth?...` (`callback_url`, `code_challenge`, `code_challenge_method=S256`, `key_label`) | — (always redirects) |
| 7 | `GET` | `/auth/callback` | `auth_callback` (`app/routes.py:146`) | query `code` (optional) | `302` to `/?auth=connected` | `302` to `/?auth=failed` when the code is absent, no flow is pending, or the exchange fails |
| 8 | `POST` | `/auth/disconnect` | `auth_disconnect` (`app/routes.py:161`) | — | `200` the offline connection payload | — |
| — | `GET` | `/static/*` | `StaticFiles` mount (`app/main.py:91`) | — | the asset (`app.js`, `index.html`) | `404` from Starlette |

Notes on the two routes that matter most:

- **`POST /analyze`** validates only presence and type of `text`; emptiness
  (including whitespace-only) is a domain rule enforced in the service, so every
  rejection of the text travels through one code path (`app/models.py:34-44`,
  `app/service.py:95-103`). The response is the record **as read back from
  SQLite**, not the in-memory payload (`app/repository.py:38-70`).
- **`GET /analyses`** uses `Query(DEFAULT_LIST_LIMIT, ge=1)`; `limit=0`, `-1` or
  `abc` is a `422`, never a silent clamp (`app/routes.py:102-108`, `README.md`).

## 2. Error Envelope

Every non-2xx response produced by the application uses exactly one shape,
built by `error_response()` (`app/routes.py:41-57`):

```json
{ "error": { "code": "INVALID_TEXT", "message": "...", "details": [ { "field": "body.text", "reason": "..." } ] } }
```

| Code | HTTP | Raised when | Handler |
|---|---|---|---|
| `VALIDATION_FAILED` | 422 | The request body or a query parameter fails framework validation (missing/non-string `text`, `limit` below 1 or not a number) | `handle_validation_error` (`app/routes.py:173-190`); `details[].field` joins the error `loc`, e.g. `query.limit` |
| `INVALID_TEXT` | 422 | The text is empty or whitespace-only; **no row is written** | `handle_invalid_text` (`app/routes.py:192-199`); `details = [{"field": "body.text", ...}]` |
| `SENTIMENT_ENGINE_ERROR` | 502 | The live engine could not produce a typed decision (network failure, non-2xx, untyped or malformed body) | `handle_engine_error` (`app/routes.py:202-208`) |
| `AUTH_EXPIRED` | 502 | OpenRouter rejected the credential (HTTP 401/403); the handler also drops the session credential | `handle_auth_error` (`app/routes.py:211-221`) |

The four handlers are registered in `create_app()`
(`app/main.py:93-96`); the error envelope shape and its four codes are asserted
by the test suite (developer scan, "Handoff Summary").

## 3. Response Contracts

### 3.1 `AnalysisRecord` (returned by `POST /analyze` and inside `GET /analyses`)

Field set and order are pinned by `RECORD_FIELDS` (`app/models.py:20-30`) and
rendered by `AnalysisRecord.to_dict()` (`app/models.py:64-77`); the same nine
fields are the columns of the `analyses` table (`app/db.py:38-48`):

| Field | Type | Encoding |
|---|---|---|
| `id` | integer | SQLite `INTEGER PRIMARY KEY AUTOINCREMENT` |
| `text` | string | the **stripped** submitted text (`app/service.py:95-103`) |
| `label` | string | one of `positive`, `negative`, `neutral` (SQL `CHECK`, `app/db.py:20`) |
| `probabilities` | object | JSON object **keyed by label**, never an array; all three labels present |
| `confidence` | number | probability of the chosen label |
| `intensity` | number | signed, clamped to −1..1 |
| `model` | string | `dummy-keyword-v1` (`app/dummy_client.py:69`) or the configured model id, default `typesafe/jev-1.13` (`app/config.py:22`) |
| `provider` | string | `local-dummy` (`app/dummy_client.py:70`) or `openrouter` (`app/openrouter_client.py:40`) |
| `created_at` | string | ISO 8601 UTC ending in `Z`, e.g. `2026-09-30T12:00:00Z` (`app/repository.py:33-35`) |

`model` + `provider` are the documented way to tell a dummy-mode row from a
live-mode row (developer scan, "Technical Debt Signals" #10).

### 3.2 Connection payload (`GET /health`, `GET /auth/status`, `POST /auth/disconnect`)

Built by `effective_connection()` (`app/service.py:31-57`):

| Field | Type | Meaning |
|---|---|---|
| `connected` | boolean | `true` when a live credential exists |
| `source` | `"session"` \| `"config"` \| `null` | A session credential wins over a config key; `null` means the offline engine is in use |
| `mode` | `"dummy"` \| `"openrouter"` | The engine actually in use, not merely the mode named in the config |
| `model` | string | The configured model id |
| `reason` | string | Why the app is not connected (or the neutral message when it is) |
| `status` | `"ok"` | Present on `/health` only |

`GET /health` and `GET /auth/status` currently return the same payload apart
from `status` — a contract the next stages should either keep deliberately or
collapse (developer scan, "Risks / follow-up").

### 3.3 `GET /analyses` envelope

```json
{ "analyses": [ { "id": 12, "text": "...", "label": "positive", "probabilities": {"positive": 0.85, "negative": 0.05, "neutral": 0.10}, "confidence": 0.85, "intensity": 0.6, "model": "dummy-keyword-v1", "provider": "local-dummy", "created_at": "2026-09-30T12:00:00Z" } ] }
```

Newest-first (`ORDER BY id DESC LIMIT ?`, `app/repository.py:73-80`), at most
`limit` entries, default 50.

## 4. External APIs Consumed

Three outbound calls, all to OpenRouter, all over `urllib` with the stdlib (no
HTTP client dependency), all with a 30 s timeout
(`app/openrouter_client.py:32`, `app/session_auth.py:53`).

| # | Call | Where | Request | Response handling |
|---|---|---|---|---|
| E1 | `POST https://openrouter.ai/api/alpha/decisions` | `app/openrouter_client.py:30`, request built at `122-189` | `{model, state: {text}, questions: {sentiment: <choice question>, intensity: <score question>}}`, `Authorization: Bearer <key>` | Reads only typed fields: `_read_choice()` (`194-229`) requires `type == "choice"`, a `choice` in `LABELS` and probabilities for all three labels; `_read_score()` (`232-250`) requires `type == "score"` and a numeric `score`, mapped onto −1..1. `401`/`403` to `SentimentAuthError`; any other failure or untyped body to `SentimentEngineError` — **never** a guessed label |
| E2 | `POST https://openrouter.ai/api/v1/auth/keys` | `app/session_auth.py:41`, called only from `exchange_code_at_openrouter()` (`78-121`) | `{code, code_verifier, code_challenge_method: "S256"}` | Expects `{"key": "..."}`; a missing/non-string/blank key raises `AuthExchangeError`, as do an HTTP error, an unreachable host, an unusable body |
| E3 | `GET https://openrouter.ai/auth` | `app/session_auth.py:40`, URL built by `SessionAuth.start()` (`163-180`) | query `callback_url`, `code_challenge`, `code_challenge_method=S256`, `key_label` | Browser redirect target; never fetched server-side |

## 5. Internal Python API (module contracts other modules depend on)

| Module | Public contract | Consumers |
|---|---|---|
| `app.sentiment` | `LABELS` (`:16`), `SentimentResult` (`:20`), `SentimentEngineError` (`:36`), `SentimentAuthError` (`:45`), `SentimentClient` Protocol with `analyze(text) -> SentimentResult` (`:56-61`) | `service`, `dummy_client`, `openrouter_client`, `repository` (typing only), `routes`, `main` |
| `app.config` | `Settings` (`:38`), `ConfigError`, `load_settings()` (`:73`), `MODES` (`:19`), `DEFAULT_MODE`/`DEFAULT_MODEL`/`DEFAULT_CONFIG_PATH`/`DEFAULT_DB_PATH` (`:21-24`), `REDACTED` (`:27`) | `main`, `routes`, `service` |
| `app.db` | `connect()` (`:51`), `init_db()` (`:66`), `SCHEMA_VERSION` (`:14`), `ANALYSES_COLUMNS` (`:38`) | `main`, `routes` |
| `app.repository` | `insert_analysis()` (`:38`), `list_analyses()` (`:73`), `format_timestamp()` (`:33`), `DEFAULT_LIST_LIMIT` (`:24`) | `routes`, `service` |
| `app.models` | `RECORD_FIELDS` (`:20`), `AnalyzeRequest` (`:34`), `AnalysisRecord.to_dict()/from_row()` (`:64,79`) | `routes`, `service`, `repository` |
| `app.service` | `analyze_text()` (`:85`), `get_client()` (`:60`), `effective_connection()` (`:31`), `InvalidTextError` | `routes`, `main` |
| `app.session_auth` | `SessionAuth` (`:141`) with `start/complete/credential/reason/expire/disconnect`, `SessionCredential` (`:125`), `AuthExchangeError`, `create_code_verifier()`, `code_challenge_for()`, `exchange_code_at_openrouter()` (`:78`) | `main`, `routes`, `service` |
| `app.main` | `create_app()` (`:53`), module-level `app` (`:101`), `HOST`/`PORT` (`:35-36`) | `app/__init__.py`, `uvicorn`, tests |
| `app.__init__` | `app` re-export (`:8`) — the `uvicorn app:app` entry point | deployment command, tests |

## 6. Contract Invariants to Preserve

1. `uvicorn app:app` keeps resolving (`app/__init__.py:8`).
2. The error envelope shape and its four codes are unchanged or the tests and
   `app/static/app.js` (`readErrorMessage`, `:25-35`) both break.
3. `probabilities` is a JSON **object** keyed by label; `created_at` is ISO 8601
   UTC ending in `Z`.
4. `GET /health` and `GET /auth/status` report the **engine in use**, not the
   configured mode — the page's indicator depends on it
   (`app/static/app.js:147-157`).
5. Empty text is rejected before the engine is called and before any row is
   written (`app/service.py:95-103`).
6. `limit < 1` is an error, not a clamp.
7. The API key never appears in a response body, a log line or a `repr`
   (`app/config.py:47-52`, `app/session_auth.py:131-138`,
   `app/openrouter_client.py:93-95`).
