# Requirements — CSV Bulk Import / Export

> Active intent: `csv-bulk-import` (`261001-csv-bulk-import`), scope `express`, depth Minimal.
> Grounded in the authoritative project description and the `sentiment-opencode`
> reverse-engineering knowledge base at HEAD `4eb9b74`.
> Requirement IDs (`FR{n}`/`FR{n}.{m}`, `NFR{n}`) are permanent traceability keys.

## Intent Analysis

The intent adds a bulk path to the existing single-text sentiment app: import a
CSV of texts in one request, analyze each row through the **existing**
`SentimentClient`, persist the successful results under one shared `import_id`,
and return a per-label/confidence breakdown; then export the rows belonging to a
given `import_id` as CSV. The work is an additive extension of three seams that
already exist in the code — the engine seam (`SentimentClient` / `analyze_text`
/ `insert_analysis`), the `/v1/analyses` route family, and the SQLite `analyses`
schema — and it must not change the single-analysis behaviour or the app's
offline, loopback-only trust model. The goal is convenience and data portability
for the single local user, not a new service.

## Functional Requirements

### FR1 — `POST /v1/analyses/import` (bulk import)

- **FR1.1** The system shall expose `POST /v1/analyses/import` on the existing `/v1` router and accept a CSV request body (`Content-Type: text/csv`).
- **FR1.2** The CSV shall carry one text per row in a single column. If the first row is exactly `text`, it shall be treated as a header row and skipped. CSV quoting (quoted commas and newlines) shall be handled by the standard-library `csv` module.
- **FR1.3** For each data row, the system shall analyze the text through the same engine seam as single analysis (`SentimentClient` resolved by the existing factory, using the existing dummy client offline) and persist each successful result under one server-generated `import_id` shared by every row of that request.
- **FR1.4** A row that cannot be analyzed shall be **skipped**, not fatal: blank/whitespace-only text is not analyzed, and an engine failure (e.g. a live-mode `502`) does not abort the request. Successfully persisted rows are kept and other rows are unaffected.
- **FR1.5** The response shall report, for the request: the `import_id`; the number of rows imported; the number of rows skipped; and a breakdown over the imported rows giving per-label counts (over the three allowed labels `positive`, `negative`, `neutral`, zero counts included) and the mean of the imported rows' confidence values.
- **FR1.6** A successful import shall return `200`, including when some rows were skipped and including when zero rows were imported (the breakdown reports zeros and the `import_id` is still returned).
- **FR1.7** Invalid input shall be refused with `422` through the standard error envelope (`{code, message}`, code `VALIDATION_FAILED`): a body that cannot be parsed as CSV, and a request whose content type is neither `text/csv` nor `text/plain`.

### FR2 — `GET /v1/analyses/export` (bulk export)

- **FR2.1** The system shall expose `GET /v1/analyses/export?import_id=<id>` on the `/v1` router.
- **FR2.2** The response shall be CSV, one row per analysis persisted under that `import_id`, ordered newest first (descending `id`), with columns `id,text,label,confidence,model,provider,created_at`.
- **FR2.3** The response shall set `Content-Type: text/csv` and `Content-Disposition: attachment; filename="analyses-<import_id>.csv"`. CSV quoting shall be produced by the standard-library `csv` module.
- **FR2.4** An `import_id` with no matching rows shall return `404` through the standard error envelope (new machine code `IMPORT_NOT_FOUND`), not an empty body.
- **FR2.5** A missing `import_id` query parameter shall return `422` through the standard error envelope (`VALIDATION_FAILED`); the parameter is required.
- **FR2.6** Export shall include only rows persisted under that `import_id`. Rows created by single analysis (no `import_id`) are never returned.

### FR3 — Record contract and persistence

- **FR3.1** The persisted `analyses` row shall gain a nullable `import_id` column; single-analysis rows store `NULL`.
- **FR3.2** `import_id` shall be part of the analysis record contract: it shall be added to every hand-written copy of the contract (`RECORD_FIELDS`, the `AnalysisRecord` field declarations, `to_dict()`, and the SQL column tuple plus `CREATE TABLE`/insert DDL) so the copies stay in sync, and it shall be returned by the existing per-analysis endpoints (`POST /v1/analyze`, `GET /v1/analyses`) as `"import_id": null` for single analyses.
- **FR3.3** The schema version shall bump, and the in-place migration shall add the nullable column and include `import_id` in the explicit rebuild copy list so existing rows survive the rebuild with `import_id = NULL`.
- **FR3.4** Deleting `data/sentiment.db` shall remain an acceptable recovery path; no separate migration tooling is introduced.

### FR4 — Tests

- **FR4.1** The change shall be covered by requirement-driven offline tests (Minimal strategy: at least one test per requirement, with a happy-path floor per changed component), and the existing suite shall remain green.
- **FR4.2** New tests shall remain fully offline (through the existing in-process ASGI harness and the session `offline_guard`) and shall read values back from real SQLite, matching the existing test pattern. No new test dependency (e.g. `httpx`) is added.

## Non-Functional Requirements

- **NFR1 — Dependency cap.** No new *runtime* dependency may be added; CSV parsing and serialisation use the Python standard library. The project's two-runtime-dependency cap (`fastapi` + `uvicorn`) is preserved and its existing test assertion stays green.
- **NFR2 — Trust model.** The new endpoints stay loopback-only and unauthenticated by design; no non-loopback bind and no change to the authentication posture (project rule).
- **NFR3 — Error envelope.** Every failure the application code raises travels through the single `{code, message}` error envelope; framework-generated routing errors keep FastAPI's `{"detail": ...}` shape (project rule). The unknown-`import_id` 404 uses the envelope.
- **NFR4 — Secret handling.** No real credential may appear in code, logs, responses, tests, or any `aidlc/` artifact (project rule).
- **NFR5 — Backward compatibility.** Existing endpoints keep their request and response shapes except for the additive `import_id` field; the 94-test suite stays green; single-analysis behaviour (including the `422` empty-text refusal) is unchanged.
- **NFR6 — Testability.** All new behaviour is verifiable offline and deterministically through the existing in-process ASGI harness, with no network access.
- **NFR7 — Concurrency.** No new concurrency target is defined. The import processes rows sequentially in request order; the existing accepted SQLite thread-affinity limitation (R-01) is not addressed by this change.

## Constraints

- **C1** Must reuse the existing `SentimentClient` seam and the existing dummy client; no new engine and no change to engine selection.
- **C2** Must keep the same SQLite schema, adding only the `import_id` column (plus the schema-version bump).
- **C3** Python, standard library `csv` and `sqlite3` only; no ORM, no HTTP client, no multipart parser.
- **C4** Localhost-only, unauthenticated, single-user; no cloud, no container, no new service.
- **C5** Tests must be offline; no addition to the runtime or test dependency sets that the project's dependency cap forbids.

## Assumptions

- **A1** `import_id` is generated server-side per import request (a unique opaque identifier), not supplied by the client. It is the grouping key returned to the caller and used by export.
- **A2** Rows are analyzed and persisted sequentially in request order; ordering within a request does not need to be preserved beyond the resulting `id` order.
- **A3** "Mean confidence" is the arithmetic mean of the `confidence` values of the imported rows; when zero rows are imported it is reported as `null` (no division by zero).
- **A4** The header row, when present, is exactly `text`; any other first row is data.
- **A5** The export columns use the record's existing serialised field values (e.g. `confidence` as a number), and `created_at` is the stored ISO-8601 UTC string.
- **A6** Adding `import_id` to the record contract is additive: existing clients tolerate the extra (nullable) field.

## Out of Scope

- Any change to the web page or `app/static/*` (no CSV UI).
- Streaming, chunked, or very large uploads; multi-column CSV; alternative delimiters.
- Retention, delete, or per-import management endpoints.
- New engines, cloud/hosted deployment, containers, or authentication changes.
- The CI Pipeline stage (not in this scope) and the existing lockfile/audit/supply-chain gaps.

## Open Questions

- **OQ1** The exact machine-readable code string for the unknown-`import_id` `404` envelope response — proposed `IMPORT_NOT_FOUND` — to be confirmed during Contract Design / Code Generation.
- **OQ2** Whether the export's numeric `confidence` formatting needs a fixed decimal precision for spreadsheet consumers, or the existing default float representation is acceptable.
- **OQ3** Whether a caller may supply its own `import_id` (assumed no, per A1) — revisit only if a use case appears.

## Sources

- **Initial description:** the authoritative project description for `csv-bulk-import` (source `project-description.json`).
- **Reverse-engineering knowledge base:** `aidlc/spaces/default/codekb/sentiment-opencode/business-overview.md`, `architecture.md`, `code-structure.md` (HEAD `4eb9b74`).
- **[Q1]** Import failure handling — answered **A** (skip unanalyzable rows, persist successes, report breakdown plus skipped count).
- **[Q2]** CSV request format and transport — answered **B** (raw `text/csv`, one text per row, optional exact-`text` header row skipped).
- **[Q3]** `import_id` contract — answered **B** (part of the record contract; returned by existing endpoints as `null` when absent).
- **[Q4]** Export shape and unknown `import_id` — answered **B** (404 via the standard error envelope).
- **Memory:** `aidlc/spaces/default/memory/project.md` mandates (localhost-only, single error envelope) and Forbidden (no credentials in artifacts).
