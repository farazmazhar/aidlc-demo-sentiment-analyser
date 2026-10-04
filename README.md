# very-cool-sentiment-analysis

A small, self-contained local web app that turns a short piece of text into a
typed sentiment label (`positive`, `negative`, `neutral`) with a confidence and
the per-label probabilities. It runs on localhost only, stores its history in a
single SQLite file, and is **fully offline by default**.

It also answers two read-only **analytics** questions over the same history: how
the stored sentiment breaks down over a date range, and which terms dominate it.
Both are served from `/v2`; the original surface at `/v1` is unchanged and
additive changes only.

The HTTP data surface is versioned: `/v1` for the original routes, `/v2` for the
analytics routes added later.

## Documentation

Project write-ups live in [`docs/`](docs/):

- [`docs/SCOPES.md`](docs/SCOPES.md) — every AI-DLC intent that has run here and
  what each one left behind
- [`docs/OUTCOMES.md`](docs/OUTCOMES.md) — the handover pack for the analytics
  layer: what was built, how it was verified, and what is still open

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
the tooling: `pytest` (the test runner), `pytest-cov` (the coverage plugin that
applies the 80% line floor over `app/`), `ruff` (formatting and linting,
configured in `pyproject.toml` with an explicit rule set that includes the `S`
security rules and the `TID251` layer-boundary rules), `detect-secrets` (the
secret scan, FR2.2), `pip-audit` (the dependency audit, FR2.3) and `uv` (the
generator of the hashed lockfile, FR2.4).

A hashed lockfile, `requirements.lock`, is committed so an install resolves the
same set on every host. To install exactly what it pins:

```bash
python -m pip install --require-hashes -r requirements.lock
python -m pip install -e . --no-deps
```

Regenerate it with `make lock` (needs network).

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

The page shows an OpenRouter connection indicator in its header:
**red** means the app is running the offline engine, **green** means it is
talking to OpenRouter. The state is also written in words and announced through a
live region, so colour is never the only signal. Clicking it connects or
disconnects.

The header also carries a three-link nav — **Analyse**, **Summary**, **Terms** —
with `aria-current` on the active section. A shared **date-range control** (two
labelled, native date inputs) drives the analytics view; both bounds default to
empty, which means all history with no bounds, and changing either bound
refetches both `/v2` endpoints with the same bounds so the two sections always
describe one population. The page sends no `import_id` filter — that stays
API-only.

**Summary** and **Terms** read the `/v2` analytics endpoints and render the
result: totals, mean confidence, a per-day series drawn as an SVG polyline with
the values also present as text, a per-label breakdown with shares, and the top
10 positive and negative terms with their counts. Empty, failed and
partial-failure states are distinct regions: if one section fails, the other
still renders its data and the failed section shows a partial-failure marker.
A range change supersedes any in-flight request (an `AbortController` plus a
request token), so a late response from an earlier range can never overwrite a
newer one, and the view never re-sends a failed request on its own. Every value
reaches the DOM through `textContent`, so no stored text is ever parsed as
markup.

## Test it, lint it

`make verify` runs every standing gate, in order — install, lint, format check,
the whole suite with its coverage floor, the secret scan and the dependency
audit:

```bash
make verify                               # the whole gate, end to end
```

Or run the individual gates:

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

Two security instruments run as part of `make verify`. The **secret scan** uses
`detect-secrets` against the committed `.secrets.baseline`; the baseline records
the repository's fake-key fixtures (the six test files that hold `sk-or-v1-*`
placeholders and the `README`'s example) as reviewed findings, so a genuinely new
secret still fails the target. The **dependency audit** uses `pip-audit` against
`requirements.lock`. Neither is a pre-commit hook or a CI job: there is no
remote, so the `Makefile` is the gate.

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

The schema is versioned in `schema_meta` and is currently **v4**. On startup an
existing store is brought to the current shape **in place**: a missing column is
added first, then the table is rebuilt with the v1 DDL and every row is copied
across, so the physical constraints (`provider` NOT NULL, `intensity` nullable,
`import_id` nullable, the label domain) always match the recorded version. The
retired `intensity` attribute is the one such change: rows written before it was
dropped keep the value they already hold, and new rows simply leave it unset — it
is never back-filled with an invented number. A migration that cannot preserve
every row fails loudly and rolls back rather than discarding data.

Rebuilding a table drops its indexes, and SQLite's `CREATE TABLE` cannot declare
one, so v4 re-creates all three as explicit statements after the copy:
`idx_analyses_created_at`, `idx_analyses_import_id` and
`idx_analyses_label_created_at`. The step is additive and idempotent: running it
again on a current store changes nothing, not even the file's modification time.

A fresh store is around 32 KB and grows by roughly 266 bytes per row.

## HTTP surface

Data routes are versioned: `/v1` carries the original surface and `/v2` the
analytics routes. The page, its static assets and the `/auth/*` support routes
are unversioned because they carry no data contract.

### `/v1` — the original surface

| Route | Behaviour |
|---|---|
| `GET /` | the page: submit form, result panel, history, connection indicator, and the analytics view (date-range control, summary, term lists) |
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

### `/v2` — analytics

Both routes are read-only. They never write to the store, and a read is proved
not to mutate anything by comparing the row count, the schema text and a content
hash before and after.

| Route | Behaviour |
|---|---|
| `GET /v2/analytics/summary` | totals, per-label counts and shares, mean confidence with its row count, and a per-day series |
| `GET /v2/analytics/terms` | the top terms per label; `limit` defaults to 10, ties break alphabetically |
| `GET /v2/analytics/*` with `from` later than `to` | `422 VALIDATION_FAILED`, naming both `query.from` and `query.to` |
| `GET /v2/analytics/*` with a date that is not `YYYY-MM-DD`, or not a real calendar date | `422 VALIDATION_FAILED`, naming the parameter |
| `GET /v2/analytics/terms?limit=0` / `abc` / a negative value | `422 VALIDATION_FAILED`, never a silent clamp |
| `GET /v2/analytics/*` with an `import_id` that matches nothing | `200` with an empty result, not a `404` — an unknown id is a valid question with no answer |
| any `/v2` route when the store cannot be read | `500 STORAGE_FAILURE`, logged with its code and distinct from every validation code |

Query parameters on both routes: `from`, `to`, `import_id`, and `limit` (terms
only). Dates are **inclusive UTC calendar days** and are written `YYYY-MM-DD`. A
single bound is never dropped, so `from` alone means "from that day onward". With
neither bound the span runs from the earliest stored analysis through today.

Three range behaviours worth knowing, because they differ:

- **An empty range returns an empty series** — not a series of zeros. If nothing
  matched, there is nothing to plot.
- **Zero-fill covers only the interior.** When a range *does* match rows, days
  inside it with no rows are emitted as zero entries, so the series has one entry
  per day and a gap in the line means a real gap.
- **A `shares` value is `null` when its denominator is zero**, never `0` — no rows
  is a different fact from zero rows.

Each analytics read issues exactly **one** `SELECT`, whatever the range width: the
per-day and per-label figures come from one grouped statement and the series is
grown in memory from it.

Every non-2xx response the application itself raises uses one envelope:

```json
{ "code": "INVALID_TEXT", "message": "Text to analyse must not be empty or whitespace-only." }
```

Framework-generated errors (an unknown path, a wrong method) keep FastAPI's own
`{"detail": ...}` shape.

## File layout

```
.
├── Makefile                  # `make verify`: install, lint, format, test, secret scan, audit
├── pyproject.toml            # metadata, dependencies, pytest/coverage/ruff configuration
├── requirements.lock         # hashed lockfile; the reproducible install set
├── .secrets.baseline         # detect-secrets allowlist (the fake-key fixtures)
├── LICENSE                   # MIT
├── config.example.toml       # committed placeholder configuration
├── config.local.toml         # gitignored; your key and mode
├── app/
│   ├── __init__.py           # re-exports `app` so `uvicorn app:app` resolves
│   ├── main.py               # create_app() factory, lifespan, enforced loopback bind
│   ├── config.py             # Settings + load_settings(), mode resolution, warning
│   ├── models.py             # AnalyzeRequest, AnalysisRecord, the four analytics dataclasses
│   ├── db.py                 # sqlite3 connection, schema v4, in-place migration, indexes
│   ├── repository.py         # insert_analysis(), list_analyses(), list_analyses_by_import_id()
│   ├── analytics.py          # AnalyticsRead: range resolution, aggregates, series, ranking
│   ├── terms.py              # tokenize() + significant_terms(); shared by engine and analytics
│   ├── sentiment.py          # LABELS, SentimentResult, SentimentClient, validate_result
│   ├── dummy_client.py       # offline keyword client, DummySentimentClient (default)
│   ├── openrouter_client.py  # live Jev client, injected transport, 10 s timeout
│   ├── session_auth.py       # in-app OpenRouter PKCE flow, in memory only
│   ├── service.py            # analyze_text(), import_texts(), get_client(), effective_connection()
│   ├── routes.py             # the page, the `/v1` API, the `/v2` analytics API, the auth routes
│   └── static/
│       ├── index.html        # header, nav, range control, analyse / summary / terms sections
│       └── app.js            # `/v1` + `/v2` fetch calls, rendering, range, supersede guard
└── tests/
    ├── conftest.py           # ASGI harness, concurrency helper, offline guard, tmp settings
    ├── test_db.py            ├── test_repository.py
    ├── test_config.py        ├── test_dummy_client.py
    ├── test_live_client.py   ├── test_service.py
    ├── test_routes.py        ├── test_page.py   # served markup + the analytics view contract
    ├── test_bulk_import.py   ├── test_session_auth.py
    ├── test_auth_routes.py
    ├── test_analytics_read.py    # range resolution, aggregates, ranking, latency budget
    ├── test_analytics_routes.py  # the /v2 acceptance and API tests
    ├── test_migration_indexes.py  # the additive migration and its three indexes
    └── test_terms.py             # tokeniser parity
```

## Notes and known limitations

- A credential obtained through the in-app authorization lives in the server
  process's memory only. It is never written to disk, never committed, and it is
  gone when the process restarts.
- The live client is covered by tests that never touch the network: its
  transport is injected, so the request it builds and the typed answer it reads
  are asserted directly, including the unreadable-answer and
  provider-rejected-credential failures.
- **Overlapping requests are supported.** A per-request SQLite connection is
  opened with same-thread checking off and closed in that same request, so a
  connection may legitimately be used and closed on a different worker thread.
  This was a known v1 limitation that raised `sqlite3.ProgrammingError` and
  answered `500` whenever two requests overlapped; it is fixed, and the test that
  proves it goes red when the flag is restored.
- **Concurrency is correct but not cheap.** Per-request CPU grows faster than
  linearly with the number of simultaneous clients: the same 240 requests cost
  2.8 CPU-seconds at one client and about 14.9 at thirty-two, and throughput
  peaks at two clients and then falls. Measured against a control route that
  stayed flat, so it is the analytics read path and not the test harness. A
  single-user localhost app has no reason to care today; a concurrent consumer
  would.
- **The analytics payload grows with the range you ask for.** A century-wide
  `from`/`to` returns roughly 7 MB and 36 500 series entries. Nothing bounds it,
  because the contract sets no bound. `/v2/analytics/terms` is unaffected.
- **`/v1/analyses/export` is a view of one import, not a backup.** It requires an
  `import_id`, excludes every row whose `import_id` is `NULL` — which is every row
  created by a single analysis — and omits the `probabilities` and `intensity`
  columns. It cannot serve as a copy of the store.
- **`data/sentiment.db` is not backed up.** The directory is gitignored and no
  commit has ever contained it, so the file on disk is the only copy. Copy it
  yourself if the history matters.
- **The loopback bind is enforced on the documented run path, not on the
  process.** `resolve_bind_host` refuses a non-loopback host at startup, but
  `uvicorn --host` on the command line bypasses that check.

## Verify it end to end

```bash
make verify
```

That runs the whole standing gate in order — install, `ruff check`, `ruff format
--check`, `pytest` with the 80% coverage floor, the `detect-secrets` scan and the
`pip-audit` dependency audit. To also boot the app and exercise the changed path
over real HTTP (the manual end-to-end step), run the one-liner below: it installs,
runs the suite, then boots the app on loopback and reads its health payload.

```bash
python -m pip install -e ".[dev]" && python -m pytest -q && python -c "import threading,time,urllib.request,uvicorn; from app.main import app as a; threading.Thread(target=uvicorn.run, args=(a,), kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'}, daemon=True).start(); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"
```

It prints, for a fresh checkout:

```json
{"mode": "offline", "connected": false, "reason": "Not connected to OpenRouter."}
```

**On an externally-managed interpreter** — Arch, Debian's `python3`, any PEP 668
environment — the first step exits 1 with `error: externally-managed-environment`
and the rest never runs. Use the venv form from [Setup](#setup) instead, or pass
`--break-system-packages` if you accept the risk to your interpreter. The test
and boot steps pass unchanged either way.
