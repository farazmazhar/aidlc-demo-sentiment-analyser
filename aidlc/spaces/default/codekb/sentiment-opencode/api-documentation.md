# API Documentation — `sentiment-opencode`

> Synthesized from the developer scan at HEAD
> `4eb9b74c4197114181dab641c177c569f2058c24` and verified against
> `app/routes.py`, `app/main.py` and `app/models.py`.

## Overview

The app exposes one HTTP surface from a single FastAPI application
(`app.main:app`). Data routes are versioned under `/v1` (`V1_PREFIX =
"/v1"`, `app/routes.py:44`); the page, its static assets and the `/auth/*`
support routes are intentionally unversioned because they carry no data
contract (`app/routes.py:117-121`, `README.md:166-169`).

There is **no committed OpenAPI/Swagger spec**; FastAPI serves an app-generated
schema at `/openapi.json` at runtime only. That schema is not exercised or
asserted by any test.

## External HTTP API

### Versioned JSON API (`/v1`)

| Method | Path | Purpose | Success |
|---|---|---|---|
| POST | `/v1/analyze` | Analyse one text, persist, return the stored record | `200` stored record |
| GET | `/v1/analyses` | List stored analyses newest-first | `200` bare JSON array |
| GET | `/v1/health` | Active mode + connection state | `200` health object |

**`POST /v1/analyze`** (`app/routes.py:130-150`)

- Request body: `{"text": "<string>"}` (`AnalyzeRequest`, `app/models.py:44-54`).
  Only presence and type are enforced at the boundary.
- Validation order: undeclared body keys are refused by
  `require_declared_fields` (`X`-field → `422 VALIDATION_FAILED`); then
  `require_text` trims and rejects empty/whitespace-only text *before* engine
  resolution (`422 INVALID_TEXT`).
- Engine resolution: session credential → configured live key → offline dummy;
  a live request with no usable key raises `LiveKeyMissingError`
  (`503 LIVE_KEY_MISSING`) with nothing stored.
- Response `200`: the stored `AnalysisRecord` as JSON, field order pinned by
  `to_dict()`.
- Live failures: `503 SENTIMENT_ENGINE_ERROR` for an engine failure;
  `503 AUTH_EXPIRED` when OpenRouter rejects the credential (which is then
  dropped).

Response shape (example):

```json
{
  "id": 1,
  "text": "I love this",
  "label": "positive",
  "probabilities": {"positive": 0.85, "negative": 0.05, "neutral": 0.10},
  "confidence": 0.85,
  "model": "dummy-keyword-v1",
  "provider": "offline",
  "created_at": "2026-10-01T15:24:59Z"
}
```

**`GET /v1/analyses?limit=50`** (`app/routes.py:153-164`)

- Query `limit: int`, default `DEFAULT_LIST_LIMIT = 50`, constrained `ge=1`.
- Response `200`: a **bare JSON array** of record objects, newest first
  (`ORDER BY id DESC LIMIT ?`). Absent `limit` applies 50.
- `limit=0`, `-1`, or non-numeric → `422 VALIDATION_FAILED`; never a silent
  clamp.

**`GET /v1/health`** (`app/routes.py:167-183`)

- Response `200`:
  `{"mode": "offline"|"live", "connected": <bool>}`, plus `"reason": <string>`
  **only when not connected**. Never carries credential material.

### Unversioned page & support routes

| Method | Path | Purpose | Response |
|---|---|---|---|
| GET | `/` | Serve the page markup | `200` HTML |
| GET | `/auth/status` | Connection payload for the indicator (also `source`, `model`) | `200` JSON |
| GET | `/auth/openrouter/start` | Begin PKCE authorization | `302` to OpenRouter |
| GET | `/auth/callback` | Exchange `code` for a key, keep in memory | `302` to `/?auth=connected` or `/?auth=failed` |
| POST | `/auth/disconnect` | Forget the session credential | `200` connection payload |

- `GET /auth/status` (`app/routes.py:189-193`) returns the full
  `effective_connection` payload: `mode`, `connected`, `source`
  (`"session"`/`"config"`/`null`), `model`, and `reason` when disconnected.
- `GET /auth/callback` (`app/routes.py:204-221`) catches `AuthExchangeError`
  **inline** and answers with a `302` redirect to `/?auth=failed`, never the
  error envelope.
- `POST /auth/disconnect` (`app/routes.py:224-231`) is body-less and has no CSRF
  token or `Origin` check — an accepted low risk under loopback-only.

### Static assets

- `/static/*` is mounted with `StaticFiles` (`app/main.py:92`); `/static/app.js`
  is served as JavaScript.

## Error Contract

Every failure the **application code** raises uses one envelope:

```json
{ "code": "<MACHINE_CODE>", "message": "<human-readable message>" }
```

The envelope is exactly `{code, message}` (`app/routes.py:56-66`); it has no
field-level detail array, so the message names the offending field itself.

| Code | Status | Trigger |
|---|---|---|
| `VALIDATION_FAILED` | 422 | Rejected body/query (e.g. undeclared field, bad `limit`) |
| `INVALID_TEXT` | 422 | Empty or whitespace-only text |
| `LIVE_KEY_MISSING` | 503 | Live mode requested, no usable key |
| `SENTIMENT_ENGINE_ERROR` | 503 | Engine could not produce a decision |
| `AUTH_EXPIRED` | 503 | OpenRouter rejected the credential (credential dropped) |

**Framework-generated errors are outside the envelope**: an unknown path or a
missing static asset returns `404 {"detail": "Not Found"}`, and a wrong method
returns `405 {"detail": "Method Not Allowed"}`. This boundary is a project rule
(`project.md`, Mandated).

Handler wiring (`app/main.py:94-98`): `RequestValidationError`,
`InvalidTextError`, `LiveKeyMissingError`, `SentimentAuthError`,
`SentimentEngineError`. `AuthExchangeError` and `ConfigError` are deliberately
**not** handler-mapped — the former is caught inline in the callback route, the
latter surfaces as a startup failure through `load_settings()` in the lifespan.

## Internal APIs (Contracts to Reuse)

| API | Signature | Location |
|---|---|---|
| Engine interface | `SentimentClient.analyze(text: str) -> SentimentResult` | `app/sentiment.py:78-84` |
| Result type | `SentimentResult(label, probabilities: dict[str,float], confidence, model, provider)` | `app/sentiment.py:23-36` |
| Result validation | `validate_result(result) -> None` (raises `SentimentEngineError`) | `app/sentiment.py:58-75` |
| Input validation | `require_text(text: str \| None) -> str` (raises `InvalidTextError`) | `app/service.py:104-113` |
| Engine factory | `get_client(settings, credential=None) -> SentimentClient` | `app/service.py:72-90` |
| Connection state | `effective_connection(settings, credential, reason) -> dict` | `app/service.py:41-69` |
| Per-text orchestration | `analyze_text(client, connection, text, now=None) -> AnalysisRecord` | `app/service.py:116-132` |
| Insert | `insert_analysis(connection, text, result, now=None) -> AnalysisRecord` | `app/repository.py:40-69` |
| List | `list_analyses(connection, limit=DEFAULT_LIST_LIMIT) -> list[AnalysisRecord]` | `app/repository.py:72-79` |
| DB connect | `db.connect(db_path) -> sqlite3.Connection` | `app/db.py:121-133` |
| DB init/migrate | `db.init_db(db_path) -> None` | `app/db.py:136-159` |
| Request model | `AnalyzeRequest{text: str}`; `ANALYZE_FIELDS`, `undeclared_body_fields(body)` | `app/models.py:44-72` |
| Record model | `AnalysisRecord` with `to_dict()`, `from_row(row)` | `app/models.py:75-133` |
| Session auth | `SessionAuth.start/complete/credential/reason/expire/disconnect` | `app/session_auth.py:139-247` |
| FastAPI dependencies | `get_settings`, `get_session_auth`, `get_connection`, `require_declared_fields` | `app/routes.py:69-114` |

## Intent-Relevant Contract Notes (CSV Import/Export)

- `GET /v1/analyses` already exists, so `/v1/analyses/import` and
  `/v1/analyses/export` are **additive sub-paths**, not a rename.
- A CSV upload cannot use `multipart/form-data` without adding
  `python-multipart`, which would breach the two-runtime-dependency cap asserted
  by `tests/test_config.py:141-160`. The viable within-cap options are a raw
  request body (`text/csv`/`text/plain`) read with the stdlib `csv` module, or a
  JSON-wrapped CSV string.
- A CSV **export** response is new: `app/routes.py` currently builds only
  `JSONResponse`, `HTMLResponse` and `RedirectResponse`; a CSV response needs a
  `Response`/`PlainTextResponse` with `text/csv` and a `Content-Disposition`
  header.
- Adding `import_id` to the persisted record touches every copy of the record
  contract (see `code-quality-assessment.md`), and the architect/design must
  decide whether `import_id` is part of the *returned* record contract or
  **storage-only**.
