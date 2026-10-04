# API Documentation — `very-cool-sentiment-analysis` (repo `sentiment-opencode`)

> The contract of record for this project is the `README.md` HTTP surface table.
> This artifact is the exhaustive version of it, verified against the code at
> `4b67c03`. No response model exists, so the shapes below are pinned by
> hand-written constants in the tests (`tests/test_routes.py`,
> `tests/test_bulk_import.py`, and now `SUMMARY_FIELDS`/`TERMS_FIELDS` in
> `tests/test_analytics_routes.py`) rather than by a machine-readable schema —
> see TD-8 in **code-quality-assessment.md**.

## Surface Summary

| Surface | Prefix | Router | Mounted at | Count |
|---|---|---|---|---|
| Versioned JSON API (classification, **frozen**) | `/v1` | `v1_router` (`app/routes.py:171`) | `app/main.py:90` | 5 endpoints |
| Versioned JSON API (analytics, additive) | `/v2` | `v2_router` (`app/routes.py:174`) | `app/main.py:91` | 2 endpoints |
| Page + assets + auth support | *(none)* | `router` (`app/routes.py:168`) | `app/main.py:91-92` | 6 routes + 1 asset mount |
| Outbound, sentiment | — | — | `app/openrouter_client.py` | 1 endpoint |
| Outbound, authorization | — | — | `app/session_auth.py` | 1 endpoint |

`V1_PREFIX = "/v1"` (`app/routes.py:59`) and `V2_PREFIX = "/v2"`
(`app/routes.py:65`) are the only version prefixes in the codebase. The
versioning rule (BR4.2) is that routes carrying a data contract are versioned,
and routes that do not — the page, its assets, the `/auth/*` support routes — are
not. `/v1` is frozen; `/v2` was added additively (`BR4.7`) and never changes a
`/v1` response.

---

## Versioned JSON API (`/v1`) — classification, frozen

`/v1` is governed by `BR4.2` and frozen: the analytics work added no `/v1`
endpoint and changed no `/v1` response. The one new machine code (`STORAGE_FAILURE`)
is raised only on the `/v2` side.

### `POST /v1/analyze`

Analyse one text, store it, return the stored record.

**Request** — `Content-Type: application/json`

```json
{ "text": "this is great" }
```

`AnalyzeRequest` is a plain dataclass (`app/models.py`) declaring exactly
one field. `additionalProperties: false` is enforced by `require_declared_fields`
(`app/routes.py:138`), which reads the raw body **before** the body validator
and reports an undeclared key as the same `422 VALIDATION_FAILED` every other
rejected body produces. A body that is not valid JSON is left to the validator.

**Response `200`**

```json
{
  "id": 42,
  "text": "this is great",
  "label": "positive",
  "probabilities": { "positive": 0.85, "negative": 0.05, "neutral": 0.10 },
  "confidence": 0.85,
  "model": "dummy-keyword-v1",
  "provider": "offline",
  "created_at": "2026-10-02T09:41:00Z",
  "import_id": null
}
```

The nine fields are `RECORD_FIELDS` (`app/models.py:25-35`) in a pinned order.
`probabilities` is a JSON **object keyed by label**, never an array, and every
label is present. `created_at` is ISO 8601 UTC ending in `Z`. `import_id` is
`null` for single analysis. **The record is read back out of SQLite**
(`app/repository.py:67-69`), not echoed from the in-memory payload.

Note what is *absent*: `intensity`. The column still exists physically and is
nullable, but it is not part of the record contract and is never returned.

| Condition | Status | Code |
|---|---|---|
| Success | `200` | — |
| Undeclared body field | `422` | `VALIDATION_FAILED` |
| Empty or whitespace-only text | `422` | `INVALID_TEXT` |
| `mode = "openrouter"` with no usable key | `503` | `LIVE_KEY_MISSING` |
| Live engine failed or answered unusably | `503` | `SENTIMENT_ENGINE_ERROR` |
| OpenRouter rejected the credential | `503` | `AUTH_EXPIRED` |

Every refusal above writes **nothing**.

---

### `GET /v1/analyses`

Return stored analyses newest-first.

**Query**

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `limit` | integer | `50` (`DEFAULT_LIST_LIMIT`, `app/repository.py:26`) | `ge=1` |

**Response `200`** — a **bare JSON array** of record objects, newest-first, at
most `limit` of them. Not wrapped, no pagination metadata, no total count.

| Condition | Status | Code |
|---|---|---|
| Success | `200` | — |
| `limit` below 1, or not a number | `422` | `VALIDATION_FAILED` (message names `query.limit`) |

A bad `limit` is **refused, never silently clamped** (BR3.6, D2 in
**architecture.md**).

---

### `POST /v1/analyses/import`

Analyse a CSV body in bulk.

**Request** — raw body, `Content-Type` must be `text/csv` or `text/plain`
(`IMPORT_CONTENT_TYPES`, `app/routes.py:61`).

```csv
text
this is great
this is terrible
perfect and lovely
```

One text per row, first column. An exact `text` first row is a header and is
skipped. Blank or whitespace-only rows are skipped **without reaching the
engine**; a row whose engine call fails is skipped **without aborting the
request**. Rows are processed sequentially in request order.

**Response `200`**

```json
{
  "import_id": "3f1c…",
  "imported": 3,
  "skipped": 1,
  "label_counts": { "positive": 2, "negative": 1, "neutral": 0 },
  "mean_confidence": 0.7166666666666667
}
```

`import_id` is a server-minted `uuid4().hex`, generated once per request and
written on every row the request persists. `label_counts` is pre-seeded from
`LABELS`, so zero-valued labels are **present rather than absent**.
`mean_confidence` is `null` when `imported == 0` — the empty case has no
division by zero and reports no misleading `0.0` (precedent A3 in
**architecture.md**).

| Condition | Status | Code |
|---|---|---|
| Success, including zero rows imported | `200` | — |
| Content-Type not `text/csv`/`text/plain` | `422` | `VALIDATION_FAILED` |
| Body is not UTF-8 | `422` | `VALIDATION_FAILED` |
| Body is not parseable as CSV | `422` | `VALIDATION_FAILED` |

---

### `GET /v1/analyses/export`

Return the rows persisted under one `import_id` as a CSV attachment.

**Query**

| Parameter | Type | Required | Notes |
|---|---|---|---|
| `import_id` | string | **yes** (`Query(...)`) | Missing → `422` |

**Response `200`** — `text/csv` with
`Content-Disposition: attachment; filename="analyses-<import_id>.csv"`.

Columns are `EXPORT_COLUMNS` (`app/routes.py:64`) — **seven** of the record's
nine fields: `id, text, label, confidence, model, provider, created_at`. The
`probabilities` and `import_id` columns are deliberately not exported. Rows come
back newest-first.

Scoped strictly to the grouping key, so single-analysis rows
(`import_id IS NULL`) are never returned.

| Condition | Status | Code |
|---|---|---|
| Success | `200` `text/csv` | — |
| Unknown `import_id` (no matching rows) | `404` | `IMPORT_NOT_FOUND` |
| Parameter absent | `422` | `VALIDATION_FAILED` |

---

### `GET /v1/health`

Report the active engine and the live connection state.

**Response `200`**

```json
{ "mode": "offline", "connected": false, "reason": "Not connected to OpenRouter." }
```

```json
{ "mode": "live", "connected": true }
```

Exactly the contract's `Health`: `mode`, `connected`, and `reason` **present
only when not connected** — so the payload can never name a live engine and a
disconnection at the same time. Never carries credential material.

`mode` is what the app *intends*; `connected` is what is actually true. A
`mode: "live", connected: false` payload is a normal, expected state, not an
error. Both fields come from one function, `effective_connection`
(`app/service.py:45`), which is also what the page indicator and the startup log
read, so the three cannot disagree.

---

## Analytics JSON API (`/v2`)

Read-only and additive (`BR4.7`). Both endpoints accept the **same range query**
and share one `resolve_range` (`app/analytics.py:125`), so the two responses
always describe one population. Neither writes, and neither calls a sentiment
engine.

### Shared query parameters

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `from` | string (`YYYY-MM-DD`) | unbounded | inclusive lower bound; an absent bound is unbounded |
| `to` | string (`YYYY-MM-DD`) | unbounded | inclusive upper bound |
| `import_id` | string | absent | scope to one bulk import; absent means every row |

An unreadable date or `from` later than `to` is refused `422 VALIDATION_FAILED`
(never silently swapped or clamped). A `sqlite3.Error` while reading is logged
through the module logger and answered `500 STORAGE_FAILURE` — the one code added
to the envelope since v1-classic.

### `GET /v2/analytics/summary`

Return the analytics summary for the resolved range, optionally scoped to one
import. One grouped, parameter-bound `SELECT` carries the per-day and per-label
counts and confidence sums; the totals, label mix, shares, mean and the
**zero-filled per-day series** are then computed in process, so the statement
count does not grow with the number of days in the range (`app/routes.py:339`,
`app/analytics.py:141`).

**Response `200`** — six fields:

```json
{
  "total": 3,
  "counts": { "positive": 2, "negative": 1, "neutral": 0 },
  "shares": { "positive": 0.6667, "negative": 0.3333, "neutral": 0.0 },
  "mean_confidence": 0.7167,
  "mean_confidence_row_count": 3,
  "series": [
    { "date": "2026-10-01", "total": 3, "counts": { "..": ".." }, "shares": { "..": null }, "mean_confidence": 0.7167, "mean_confidence_row_count": 3 }
  ]
}
```

`counts` is pre-seeded from `LABELS`, so zero-valued labels are present rather
than absent. `mean_confidence` is `null` when `total == 0` — the empty case has
no division by zero and reports no misleading `0.0` (precedent A3 in
**architecture.md**). An empty range is a normal empty result, not an error.

| Condition | Status | Code |
|---|---|---|
| Success, including an empty range | `200` | — |
| Bad or inverted range bounds | `422` | `VALIDATION_FAILED` |
| Store read error | `500` | `STORAGE_FAILURE` |

### `GET /v2/analytics/terms`

Return ranked significant terms, split by polarity. The rows are read once;
tokenising (`app/terms.tokenize`), filtering (`significant_terms`: length ≥ 3,
not a stopword), counting and ranking all happen in process, and the payload is
bounded by `limit` rather than by the store size. Only rows carrying a label in
`TERM_LABELS` (`positive`, `negative`) contribute, so a neutral row reaches
neither list. (`app/routes.py:372`, `app/analytics.py:194`.)

**Query** — the shared parameters plus:

| Parameter | Type | Default | Constraint |
|---|---|---|---|
| `limit` | integer | `10` (`DEFAULT_TERM_LIMIT`, `app/analytics.py:48`) | `ge=1` |

**Response `200`** — `{ "positive": [...], "negative": [...] }`, each a ranked
list of `{ "term": "...", "count": N }`. `limit` is honoured, never clamped: an
oversized limit returns every available term.

| Condition | Status | Code |
|---|---|---|
| Success, including no terms | `200` | — |
| `limit` below 1, or bad/inverted bounds | `422` | `VALIDATION_FAILED` |
| Store read error | `500` | `STORAGE_FAILURE` |

---

## Page, Assets and Auth Support (unversioned)

These routes carry **no data contract**, which is why they are unversioned
(BR4.2).

| Route | Behaviour | Status codes |
|---|---|---|
| `GET /` | The single page. Serves `app/static/index.html`, **re-read from disk on every request**. | `200` `text/html` |
| `GET /static/*` | `StaticFiles` mount (`app/main.py:92`) serving `app.js` and `index.html`. | `200`; missing file → FastAPI's own `404 {"detail": …}` |
| `GET /auth/status` | The page's full connection payload: everything `effective_connection` returns — `mode`, `connected`, `source` (`session` / `config` / `null`), `model`, `reason`. | `200` |
| `GET /auth/openrouter/start` | `302` to `https://openrouter.ai/auth` with an S256 PKCE challenge. `callback_url` is derived from the request via `request.url_for("auth_callback")`. | `302` |
| `GET /auth/callback?code=…` | Exchanges the code for a key, holds it in process memory, then redirects to `/?auth=connected`. A missing code or a failed exchange is recorded in the session store and answered with `302 /?auth=failed` — **never the error envelope**. | `302` |
| `POST /auth/disconnect` | Forgets the session credential and returns the same connection payload as `/auth/status`. | `200` |

`/auth/*` failures are the deliberate exception to the envelope rule: a browser
redirect cannot carry a JSON envelope, so the failure is signalled through the
redirect target and the session store's recorded reason.

---

## Error Envelope

Every failure **the application code raises** uses exactly one shape
(`error_response`, `app/routes.py:69`):

```json
{ "code": "INVALID_TEXT", "message": "Text to analyse must not be empty or whitespace-only." }
```

Exactly two keys. No field-level array, because the contract sets
`additionalProperties: false` — the `message` names the offending field itself
(`"query.limit: Input should be greater than or equal to 1"`).

### Machine codes

| Code | Status | Raised by | Meaning |
|---|---|---|---|
| `VALIDATION_FAILED` | `422` | `handle_validation_error` (`app/routes.py:457`) | Rejected body or query parameter. Covers undeclared fields, bad `limit`, bad content type, non-UTF-8 body, unparseable CSV, a missing required query parameter, and a bad/inverted `/v2` range. |
| `INVALID_TEXT` | `422` | `handle_invalid_text` (`app/routes.py:473`) | Empty or whitespace-only text. |
| `LIVE_KEY_MISSING` | `503` | `handle_live_key_missing` (`app/routes.py:478`) | Live mode requested, no usable key. The message names the config file. |
| `SENTIMENT_ENGINE_ERROR` | `503` | `handle_engine_error` (`app/routes.py:483`) | The engine failed, or its answer was not a complete typed decision. The message is deliberately generic — the engine's own text is not echoed. |
| `AUTH_EXPIRED` | `503` | `handle_auth_error` (`app/routes.py:492`) | OpenRouter rejected the credential. **The credential is dropped as a side effect**, so the next request runs offline and the indicator goes red. |
| `IMPORT_NOT_FOUND` | `404` | returned inline (`app/routes.py:286`) | No rows under that `import_id`. |
| `STORAGE_FAILURE` | `500` | raised inline in the `/v2` handlers (`app/routes.py:339-403`) | A `sqlite3.Error` on an analytics read. Added with `/v2`; no `/v1` handler raises it. |

### Exception-handler registrations

Five handlers are registered in `create_app` (`app/main.py`):

| Exception | Handler |
|---|---|
| `RequestValidationError` | `handle_validation_error` |
| `InvalidTextError` | `handle_invalid_text` |
| `LiveKeyMissingError` | `handle_live_key_missing` |
| `SentimentAuthError` | `handle_auth_error` |
| `SentimentEngineError` | `handle_engine_error` |

### What the envelope does not cover

Framework-generated routing errors keep FastAPI's own shape: an unknown path and
a missing static asset return `404 {"detail": "Not Found"}`; a wrong method
returns `405 {"detail": "Method Not Allowed"}`. This split is a binding project
rule, not an accident.

`ConfigError` is never mapped to a status at all — it is raised in
`app/config.py` and surfaces as a **startup failure** through `load_settings()`
in the lifespan.

---

## Outbound API Contracts (client side)

### Sentiment decision — `POST https://openrouter.ai/api/v1/decisions`

Implemented in `app/openrouter_client.py` via the `HttpTransport` protocol
(`app/openrouter_client.py:69`); production transport is stdlib `urllib`, with
`LIVE_TIMEOUT_SECONDS = 10.0` as the single timeout. The path constant is at
`app/openrouter_client.py:34`.

The **read** contract is what matters architecturally: the answer must yield a
typed `SentimentResult` — one label from `LABELS`, a probability for every
label, a confidence, and the engine's model and provider. A response that cannot
be read this way raises `SentimentEngineError` and **nothing is persisted**
(`app/sentiment.py:57-70`). There is no free-text field to parse and no score
question — an unreadable answer is a failure, never a guess.

### Authorization code exchange — `POST https://openrouter.ai/api/v1/auth/keys`

Implemented in `exchange_code_at_openrouter` (`app/session_auth.py:78`),
`EXCHANGE_TIMEOUT_SECONDS = 30.0`. Sends `{code, code_verifier,
code_challenge_method: "S256"}` and reads `key` from the JSON response. Every
failure — HTTP error, network failure, non-JSON body, no `key` — becomes
`AuthExchangeError`.

`exchange_code_at_openrouter` is the **only** function in the authorization flow
that touches the network, and it is the one the test suite replaces with a
double.

---

## Internal API Surface (seams and extension points)

These are not HTTP, but they are the contracts other code is allowed to depend
on.

| Seam | Signature | Location | Contract |
|---|---|---|---|
| **Engine interface** | `SentimentClient.analyze(text) -> SentimentResult` | `app/sentiment.py:78` | The one engine interface. Structural (`runtime_checkable` `Protocol`); no registration. |
| **Engine selection** | `get_client(settings, credential=None) -> SentimentClient` | `app/service.py:76` | **The only place a concrete client is chosen.** Order: session credential → live config with a key → offline. Raises `LiveKeyMissingError` when live is intended and no key exists. |
| **Connection** | `get_connection(request) -> Iterator[sqlite3.Connection]` | `app/routes.py:114` | One short-lived connection per request, closed in a `finally`. The single place the `sqlite3` driver and the connection lifecycle are touched — including by the `/v2` reads, which receive it. |
| **Settings** | `get_settings(request) -> Settings` | `app/routes.py:104` | Reads `request.app.state.settings`, resolved once at startup. |
| **Session store** | `get_session_auth(request) -> SessionAuth` | `app/routes.py:109` | Reads `request.app.state.session_auth`; injectable at `create_app` for tests. |
| **Error builder** | `error_response(status_code, code, message) -> JSONResponse` | `app/routes.py:91` | The one envelope construction site. |
| **Connection state** | `effective_connection(settings, credential, reason) -> dict` | `app/service.py:45` | The one payload read by health, the page indicator and the startup log. |
| **Orchestration** | `analyze_text(client, connection, text, now=None, import_id=None) -> AnalysisRecord` | `app/service.py:200` | Order W1: validate → engine → validate answer → store. Returns the row read back. |
| **Bulk orchestration** | `import_texts(client, connection, texts, now=None) -> ImportSummary` | `app/service.py:129` | Reuses `analyze_text` per text under one `import_id`; skips rather than aborts. |
| **Range resolution** | `resolve_range(from_bound, to_bound) -> ResolvedRange` | `app/analytics.py:125` | Shared by both `/v2` endpoints, so their populations match. Raises `RangeError` on an unreadable or inverted range. |
| **Analytics read** | `read_summary(connection, resolved, import_id=None, today=None) -> AnalyticsSummary`; `read_terms(connection, resolved, import_id=None, limit=DEFAULT_TERM_LIMIT) -> AnalyticsTerms` | `app/analytics.py:141`, `:194` | Take the request's connection; open none; write nothing; call no engine. |
| **Term extraction** | `tokenize(text) -> list[str]`; `significant_terms(tokens) -> list[str]` | `app/terms.py:179`, `:189` | The one tokeniser (no filters) and the significance filter (length + stopwords). Counting/ranking stay in `app.analytics`. |
| **Persistence** | `insert_analysis`, `list_analyses`, `list_analyses_by_import_id` | `app/repository.py` | All three take a `sqlite3.Connection` as the first argument. **Row DML only — aggregate queries live in `app/analytics.py`.** |
| **Row decoding** | `AnalysisRecord.from_row(row)` | `app/models.py` | Decodes the JSON `probabilities`, maps a missing `provider` to the `unknown` sentinel, and deliberately does not read `intensity`. |
| **Validation** | `require_text(text) -> str`, `validate_result(result)` | `app/service.py:112`, `app/sentiment.py:57` | The two rejection gates. |
| **Field contract** | `RECORD_FIELDS`, `ANALYZE_FIELDS`, `undeclared_body_fields(body)` | `app/models.py` | `ANALYZE_FIELDS` is derived from the dataclass via `dataclasses.fields`, so it cannot drift. `RECORD_FIELDS` is a hand-maintained tuple. |

---

## Client Contract (`app/static/app.js`)

Five `fetch` call sites. Two client-side prefix constants: `const API = "/v1";`
(`app/static/app.js:14`) and `const API_V2 = "/v2";` (`:15`) — an independent
second copy of each prefix that nothing asserts matches the backend.

| Line | Call | Trigger |
|---|---|---|
| `:106` | `GET ${API}/analyses?limit=50` | page load |
| `:116` | `POST ${API}/analyze` | form submit |
| `:242` | `GET ${API_V2}/analytics/summary` | page load — **no query string** |
| `:277` | `GET ${API}/health` | connection poll |
| `:305` | `POST /auth/disconnect` | indicator click |

There is **no** terms fetch, **no** range parameter on the summary call, **no**
`AbortController` and no request-sequence guard. That wiring is the work the
active intent adds. Auth state after a redirect is read from the query string
(`new URLSearchParams(window.location.search).get("auth")`), and connecting is
`window.location.href = "/auth/openrouter/start"`.

## Generated OpenAPI Document

FastAPI will serve `/openapi.json` and `/docs`. **The generated document cannot
describe the real response shapes**, because no handler declares a response
model — they return bare `dict[str, object]`, `list[dict[str, object]]`,
`HTMLResponse` or hand-built `JSONResponse`. Treat the README table, this
artifact and the tests as the contract of record.

Component responsibility is in **component-inventory.md**; layering and the
transaction flows are in **architecture.md**; measured coverage and the debt
register are in **code-quality-assessment.md**.