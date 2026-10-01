# very-cool-sentiment-analysis

A small, self-contained local web app that turns a short piece of text into a
typed sentiment label (`positive`, `negative`, `neutral`) with a confidence and
the per-label probabilities. It runs on localhost only, stores its history in a
single SQLite file, and is **fully offline by default**.

The HTTP data surface is versioned at `/v1`.

## Prerequisites

- Python 3.11 or newer (developed and verified on 3.14)
- No other system dependencies: storage is the standard-library `sqlite3`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Runtime dependencies are exactly two: `fastapi` and `uvicorn`. Everything else
is the standard library — storage is the standard library's `sqlite3` and the
one outbound HTTP call uses the standard library too. The development extra adds
three packages: `pytest` (the test runner), `pytest-cov` (the coverage plugin
that applies the 80% line floor over `app/`) and `ruff` (formatting and linting,
configured in `pyproject.toml` with an explicit rule set that includes the `S`
security rules).

## Run it

```bash
uvicorn app:app --reload
```

Then open <http://127.0.0.1:8000/>. The server binds `127.0.0.1` only.

The app has no authentication of its own: it is loopback-only and single-user by
design. The one credential anywhere in the system is *your* OpenRouter key, used
outbound only when live mode is active; it lives either in the gitignored
`config.local.toml` or in the server process's memory after the in-app sign-in,
and it is never written to disk, logged or returned in a response body.

The page shows an OpenRouter connection indicator in its top-left corner:
**red** means the app is running the offline engine, **green** means it is
talking to OpenRouter. The state is also written in words and announced through a
live region, so colour is never the only signal. Clicking it connects or
disconnects.

## Test it, lint it

```bash
python -m pytest -q                       # the whole suite, with the coverage floor
python -m ruff check app tests            # lint
python -m ruff format --check app tests   # formatting
```

`testpaths = ["tests"]` is configured in `pyproject.toml`, so a bare `pytest`
runs this project's suite and nothing else. The coverage settings live in
`addopts`, so every run measures line coverage over `app/` and fails below 80%.

Every test runs offline: no network, no API key, and no `config.local.toml` is
required or read. A session-wide guard in `tests/conftest.py` makes any socket
connection raise, so an accidental network call fails the run rather than
silently reaching OpenRouter. The live client is exercised through an injected
transport instead.

`tests/test_page.py` verifies the page at the served-markup level; browser-side
execution of `app.js` is not driven by the suite, because no browser-automation
dependency is permitted under the dependency cap.

## Connecting to OpenRouter from the app

You do not need a config file or a key on disk to use the live model. Click the
red indicator and the app walks OpenRouter's PKCE authorization flow:

1. The browser is sent to `https://openrouter.ai/auth` with a localhost
   `callback_url` and an S256 `code_challenge`.
2. You authorize on OpenRouter, which redirects back with a one-time `code`.
3. The app exchanges that code at `/api/v1/auth/keys` for an API key and keeps
   it **in the server process's memory only** — nothing is written to disk, to
   `config.local.toml`, to the database, or to git.
4. The indicator turns green and `POST /v1/analyze` uses the live model.

A credential obtained this way lasts for the life of the process: restart the
server and you are back to red and offline. If OpenRouter later rejects it (an
expired or revoked key answers HTTP 401/403), the app drops it on that response,
falls back to the offline engine, and the indicator turns red again with the
reason shown on the page. Clicking a green indicator disconnects.

Each failure path of the flow — a stray callback, a blank code, a refused
exchange, an expired verifier — records its reason server-side, and the page
reports it while staying usable on the offline engine.

## The two modes

The app has one `SentimentClient` interface and two implementations, selected by
the config file.

| Mode | Engine | `provider` recorded | Needs a key | Network |
|---|---|---|---|---|
| `dummy` (default) | keyword-based `DummySentimentClient` | `offline` | no | none |
| `openrouter` | live Jev model (`typesafe/jev-1.13`) via the OpenRouter Decisions API, `OpenRouterJevSentimentClient` | `openrouter` | yes | yes |

With no config file at all the app runs in `dummy` mode — that is the default
for a fresh checkout, for development and for the whole test suite.

## Configuration

```bash
cp config.example.toml config.local.toml
```

`config.local.toml` is gitignored and is the only place on disk the API key
belongs; `config.example.toml` is committed and contains a placeholder, never a
secret.

```toml
mode = "openrouter"          # "dummy" (default) or "openrouter"
api_key = "sk-or-v1-..."     # required only for mode = "openrouter"
model = "typesafe/jev-1.13"  # optional; this is the default
```

Resolution rules:

1. No config file → the offline engine, no key.
2. Config file with no `mode` → the offline engine.
3. `mode = "dummy"` → the offline engine; any `api_key` in the file is ignored.
4. `mode = "openrouter"` with a non-empty key → the live engine.
5. `mode = "openrouter"` with a missing or blank key → live mode is *requested*
   but no key is usable. The app starts on the offline engine, logs a warning
   naming `config.local.toml`, and the indicator is red until you connect in the
   app or put a key in the file. A submission in that state is refused with
   `503 LIVE_KEY_MISSING`, whose message names the file to fill in; nothing is
   stored.
6. Any other `mode` value → startup fails, naming the accepted values.

The key is never logged, never rendered (it shows as `<redacted>`), and never
stored in the database.

## Storage

History lives in one SQLite file, `data/sentiment.db`. The `data/` directory and
the schema are created automatically on first start, so there is no manual setup
step. The directory is gitignored.

Each row holds the input text, the label, the per-label probabilities as a JSON
object keyed by label, the confidence, the model id, the provider and an ISO 8601
UTC `created_at`. A row written by bulk import also carries the shared
`import_id` that groups every row of that request; a single analysis stores
`NULL`. A row migrated from a store written before the `provider`
column existed has no engine to name: it carries the recorded sentinel
`"unknown"` (never JSON `null` and never the literal string `"None"`), which keeps
the record a schema-conformant string so an unknown provider is not confused with
a real one.

The schema is versioned in `schema_meta`. On startup an existing store is brought
to the current shape **in place**: a missing column is added first, then the table
is rebuilt with the v1 DDL and every row is copied across, so the physical
constraints (`provider` NOT NULL, `intensity` nullable, `import_id` nullable, the
label domain) always
match the recorded version. The retired `intensity` attribute is the one such
change: rows written before it was dropped keep the value they already hold, and
new rows simply leave it unset — it is never back-filled with an invented number.
A migration that cannot preserve every row fails loudly and rolls back rather than
discarding data.

## HTTP surface

Data routes are versioned under `/v1`; the page, its static assets and the
`/auth/*` support routes are unversioned because they carry no data contract.

| Route | Behaviour |
|---|---|
| `GET /` | the page: submit form, result panel, history, connection indicator |
| `POST /v1/analyze` | `{"text": "..."}` → `200` with the stored record |
| `POST /v1/analyze` with a field the body does not declare | `422 VALIDATION_FAILED`, nothing stored |
| `POST /v1/analyze` with empty or whitespace-only text | `422 INVALID_TEXT`, nothing stored |
| `POST /v1/analyze` while live mode was requested with no usable key | `503 LIVE_KEY_MISSING`, nothing stored |
| `POST /v1/analyze` when the live engine fails or rejects the key | `503 SENTIMENT_ENGINE_ERROR` / `503 AUTH_EXPIRED` |
| `GET /v1/analyses?limit=50` | a JSON array of records, newest first (an absent limit means 50) |
| `GET /v1/analyses?limit=0` / `-1` / `abc` | `422 VALIDATION_FAILED`, never a silent clamp |
| `POST /v1/analyses/import` | a `text/csv` (or `text/plain`) CSV body, one text per row; an exact `text` first row is a header. `200` with `import_id`, imported/skipped counts, per-label counts and mean confidence; blank or unanalyzable rows are skipped |
| `POST /v1/analyses/import` with another content type | `422 VALIDATION_FAILED`, nothing stored |
| `POST /v1/analyses/import` with a body that is not valid UTF-8 CSV | `422 VALIDATION_FAILED`, nothing stored |
| `GET /v1/analyses/export?import_id=...` | the rows for that import as a `text/csv` attachment, newest first |
| `GET /v1/analyses/export` with no `import_id` | `422 VALIDATION_FAILED` (the parameter is required) |
| `GET /v1/analyses/export?import_id=...` for an unknown id | `404 IMPORT_NOT_FOUND` |
| `GET /v1/health` | `{"mode": "offline"\|"live", "connected": ...}`, plus `"reason"` only when not connected |
| `GET /auth/status` | the page's connection payload: also `source` (`session`/`config`/`null`) and `model` |
| `GET /auth/openrouter/start` | `302` to OpenRouter's authorization page with a PKCE challenge |
| `GET /auth/callback?code=...` | exchanges the code, keeps the key in memory, redirects back to `/` |
| `POST /auth/disconnect` | forgets the session credential and returns the offline engine |

Every non-2xx response the application itself raises uses one envelope:

```json
{ "code": "INVALID_TEXT", "message": "Text to analyse must not be empty or whitespace-only." }
```

Framework-generated errors (an unknown path, a wrong method) keep FastAPI's own
`{"detail": ...}` shape.

## File layout

```
.
├── pyproject.toml            # metadata, dependencies, pytest/coverage/ruff configuration
├── config.example.toml       # committed placeholder configuration
├── config.local.toml         # gitignored; your key and mode
├── app/
│   ├── __init__.py           # re-exports `app` so `uvicorn app:app` resolves
│   ├── main.py               # create_app() factory, lifespan, HOST bind
│   ├── config.py             # Settings + load_settings(), mode resolution, warning
│   ├── models.py             # AnalyzeRequest + AnalysisRecord (to_dict/from_row)
│   ├── db.py                 # sqlite3 connection, schema creation, in-place migration
│   ├── repository.py         # insert_analysis(), list_analyses(), list_analyses_by_import_id()
│   ├── sentiment.py          # LABELS, SentimentResult, SentimentClient, validate_result
│   ├── dummy_client.py       # offline keyword client, DummySentimentClient (default)
│   ├── openrouter_client.py  # live Jev client, injected transport, 10 s timeout
│   ├── session_auth.py       # in-app OpenRouter PKCE flow, in memory only
│   ├── service.py            # analyze_text(), import_texts(), get_client(), effective_connection()
│   ├── routes.py             # the page, the `/v1` API, the auth routes, the error envelope
│   └── static/
│       ├── index.html        # the page + the connection indicator
│       └── app.js            # `/v1` fetch calls, rendering, history, indicator
└── tests/
    ├── conftest.py           # in-process ASGI harness, offline guard, tmp settings
    ├── test_db.py            ├── test_repository.py
    ├── test_config.py        ├── test_dummy_client.py
    ├── test_live_client.py   ├── test_service.py
    ├── test_routes.py        ├── test_page.py
    ├── test_bulk_import.py   ├── test_session_auth.py
    └── test_auth_routes.py
```

## Notes and known limitations

- A credential obtained through the in-app authorization lives in the server
  process's memory only. It is never written to disk, never committed, and it is
  gone when the process restarts.
- The live client is covered by tests that never touch the network: its
  transport is injected, so the request it builds and the typed answer it reads
  are asserted directly, including the unreadable-answer and
  provider-rejected-credential failures.
- **Known limitation (accepted for v1).** A per-request SQLite connection is
  created in one anyio worker thread and closed in another when requests
  overlap, which raises `sqlite3.ProgrammingError` and answers `500`. Sequential
  use — one request at a time, which is what the tests and the verification
  command exercise — is unaffected. No concurrency target is defined for v1 and
  the fix is deliberately out of scope; it is recorded here rather than left to
  be rediscovered.

## Verify it end to end

```bash
python -m pip install -e ".[dev]" && python -m pytest -q && python -c "import threading,time,urllib.request,uvicorn; from app.main import app as a; threading.Thread(target=uvicorn.run, args=(a,), kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'}, daemon=True).start(); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"
```

That installs, runs the suite with the coverage floor applied, then boots the
app on loopback and reads its health payload. It prints, for a fresh checkout:

```json
{"mode": "offline", "connected": false, "reason": "Not connected to OpenRouter."}
```
