# Code Summary — CSV Bulk Import / Export

> Stage: **code-generation** (Construction, stage-level / zero-Unit; scope `express`, depth Minimal).
> Active intent: `csv-bulk-import` (`261001-csv-bulk-import`).
> Testing Contract: `sha256:90d67be610688942f0a22a56218142a24e8b33b08ee1afb10fca070ce56fce02`
> Methodology: **custom** — acceptance/API tests first, then implementation, then lower-level unit tests.

## What was built

An additive bulk CSV surface on the existing localhost-only sentiment app:

- `POST /v1/analyses/import` — accepts a `text/csv` (or `text/plain`) body, one
  text per row, with an optional exact-`text` first row treated as a header;
  analyses each row through the existing `SentimentClient` seam, skips blank and
  unanalyzable rows, persists each success under one server-generated
  `import_id`, and returns the `import_id`, the imported/skipped counts, the
  per-label breakdown and the mean confidence (null when nothing imported).
- `GET /v1/analyses/export?import_id=...` — returns the rows for that
  `import_id` as `text/csv` (columns `id,text,label,confidence,model,provider,created_at`),
  newest first, with an attachment disposition; an unknown id is a `404`
  `IMPORT_NOT_FOUND` envelope; a missing parameter is `422 VALIDATION_FAILED`.
- A nullable `import_id` column and record field, returned as `null` by the
  existing single-analysis endpoints, with an in-place schema migration to v3.

## Files created / modified

**Application (`app/`)**

| File | Change |
|---|---|
| `app/models.py` | added `import_id` to `RECORD_FIELDS`, `AnalysisRecord`, `to_dict()` and `from_row()` (nullable, additive) |
| `app/db.py` | `SCHEMA_VERSION = 3`; added nullable `import_id` to `ANALYSES_COLUMNS`, `CREATE_ANALYSES_TABLE`, `_ADD_COLUMN_SQL` and the rebuild copy list |
| `app/repository.py` | `insert_analysis(..., import_id=None)`; new `list_analyses_by_import_id(connection, import_id)` (descending id) |
| `app/service.py` | `analyze_text(..., import_id=None)`; new `ImportSummary`, `new_import_id()` and `import_texts()` |
| `app/routes.py` | `IMPORT_NOT_FOUND`, `IMPORT_CONTENT_TYPES`, `EXPORT_COLUMNS`; `POST /v1/analyses/import` and `GET /v1/analyses/export` |

**Tests (`tests/`)**

| File | Change |
|---|---|
| `tests/test_bulk_import.py` | **new** — 17 API-level acceptance tests for import/export (written before the implementation) |
| `tests/conftest.py` | additive harness support for a raw body + content type (`body`/`content_type`); the existing `json_body` path is unchanged |
| `tests/test_db.py` | v3 schema + v2→v3 migration tests |
| `tests/test_repository.py` | `import_id` round-trip + `list_analyses_by_import_id` scoping/order tests |
| `tests/test_service.py` | `import_texts` aggregation, per-row skip and zero-row tests |
| `tests/test_routes.py` | `RECORD_FIELDS` gains the additive `import_id`; asserted null for a single analysis |

**Documentation**

| File | Change |
|---|---|
| `README.md` | storage/`import_id` note, HTTP surface rows for both endpoints, file-layout comments |

## Key decisions

1. **Reuse the existing seams.** The bulk path resolves the engine once through
   the existing `get_client` factory and reuses `analyze_text` per row, so no
   engine-resolution or adapter code changed (C1). Each row is committed by the
   existing per-insert transaction, so a later failure never discards earlier
   successes (FR1.4).
2. **`import_id` is threaded, not invented.** It is generated server-side
   (`uuid.uuid4().hex`, A1) and passed `analyze_text → insert_analysis`, added to
   every hand-written copy of the record contract (FR3.2) and made nullable
   everywhere so single analysis stores `NULL`.
3. **Migration composes with the existing rebuild.** The column is added
   nullable by `_ADD_COLUMN_SQL` and copied by `_COPY_ROWS_INTO_V1_TABLE`, so an
   existing store reaches v3 with every row intact and `import_id = NULL`
   (FR3.3, FR3.4). `_is_v1_shape` now requires the column, which triggers the
   rebuild for any pre-v3 store.
4. **CSV via the standard library only.** `csv` + `io` for both directions; no
   multipart parser and no new runtime dependency (NFR1).
5. **One error envelope.** `IMPORT_NOT_FOUND` (404) and `VALIDATION_FAILED`
   (422) travel through the existing `error_response`; framework routing errors
   are untouched (NFR3).

## Test coverage summary

- **Baseline (before change):** the existing suite was green at HEAD `4eb9b74`
  (94 tests; coverage 96.03% — the coverage floor is already part of `addopts`).
- **Scoped command (inner loop):**
  `python -m pytest tests/test_bulk_import.py tests/test_db.py tests/test_repository.py tests/test_service.py tests/test_routes.py -q --no-cov`
  → **58 passed**.
- **Full suite (authoritative gate):** `python -m pytest`
  → **118 passed**, total coverage **96.02%** (`--cov-fail-under=80` satisfied; the floor was not changed).
- **Lint/format:** `python -m ruff check app tests` and
  `python -m ruff format --check app tests` → clean.
- Added tests: 17 acceptance/API + 7 lower-level unit tests (+24 over baseline).
  Every FR has at least one test at the narrowest effective level; every changed
  component (models, db, repository, service, routes) has a happy-path test.

## Deviations from the plan

1. **Step 1 scoped command runs with `--no-cov`.** The plan and its Testing
   Contract assumed `addopts = "-q"`. The workspace's actual `pyproject.toml`
   enforces whole-application coverage in `addopts`
   (`--cov=app --cov-fail-under=80`). No subset run can satisfy that floor
   (measured: `tests/test_routes.py` alone = 65%), so the inner-loop command is
   scoped with `--no-cov`. The floor itself was **not** lowered or disabled for
   the authoritative full run in Step 8, which still applies it.
2. **The import route is a sync `def`, with the raw body as a `bytes` parameter**
   (`payload: bytes = Body(default=b"")`) instead of `async def` + `await
   request.body()`. The per-request connection dependency (`get_connection`) runs
   on an anyio worker thread; an `async def` endpoint runs on the event loop, so
   using that connection there fails with `sqlite3.ProgrammingError` (the
   documented R-01 thread-affinity seam). A sync handler keeps the bulk route on
   the same worker-thread path the existing `POST /v1/analyze` already uses; no
   requirement was relaxed.
3. **"Unparseable body" is a non-UTF-8 body.** The stdlib `csv.reader` accepts
   NUL bytes and nearly any text, so the deterministic unparseable case is a body
   that is not valid UTF-8; a defensive `csv.Error` guard is still present.
4. **Import response key names were chosen here.** No Contract Design artifact
   exists for this scope, so the summary uses
   `import_id`, `imported`, `skipped`, `label_counts`, `mean_confidence`; tests
   pin that exact key set.
5. **`tests/conftest.py` was extended additively** to carry a raw body +
   content type, because the existing `asgi_request` harness only carried JSON
   and `text/csv` bodies are required by FR1.1/FR1.7. The existing JSON path and
   all prior tests are unaffected (no `httpx`/`TestClient` added).

## Unresolved / open points (carried forward)

- **OQ2 (from requirements):** export numeric `confidence` uses the default
  float representation (`0.85`, `0.7`); no fixed decimal precision was chosen.
- The `csv.Error` guard in `app/routes.py` (lines ~219-220) is defensive and not
  covered by a test because the stdlib parser does not raise on the inputs the
  endpoint accepts; overall coverage remains above the floor.
- R-01 (SQLite thread-affinity on overlapping requests) is unchanged and remains
  the accepted, recorded limitation; NFR7 defines no concurrency target.
