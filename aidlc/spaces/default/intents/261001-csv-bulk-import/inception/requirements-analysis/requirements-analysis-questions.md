# Requirements Analysis Questions — CSV Bulk Import / Export

> Active intent: `csv-bulk-import` (`261001-csv-bulk-import`), scope `express`, depth Minimal.
> This file is the source of truth for this stage. For each question, the letter of
> the chosen option is recorded after `[Answer]:`; `X` would mean a custom answer.
>
> Source reviewed: the authoritative project description and the reverse-engineering
> knowledge base for `sentiment-opencode` (business overview, architecture, code
> structure) at HEAD `4eb9b74`. Nothing in the new CSV surface exists in the code today.

## Q1. Import failure handling

**Context:** The intent says the import "analyzes each row through the existing
SentimentClient, persists the results under a shared import_id, and returns a
breakdown", but does not say what happens when a row cannot be analyzed. Today
`analyze_text` raises on the first bad row and there is no transaction boundary
across rows, so the failure path has to be defined explicitly. A "bad row" means
either a blank/empty text or an engine failure (e.g. a live-mode `502`).

**Question:** When a row cannot be analyzed, what should `POST /v1/analyses/import` do?

- **A.** Skip every unanalyzable row (blank and engine-failed alike), persist the rows that succeeded under the shared `import_id`, and report the breakdown of imported rows plus a count of skipped rows. Other rows are never affected by one bad row.
- **B.** Skip blank rows, but abort the entire import on an engine failure and persist nothing (all-or-nothing per request). Blank rows are treated as "nothing to analyze", not as an error.
- **C.** Abort the entire import on the first unanalyzable row of any kind and persist nothing (all-or-nothing).
- **D.** Abort on the first bad row, but keep the rows already written before the failure (partial import persists under the `import_id`).
- **X.** Other (please specify)

[Answer]: A

## Q2. CSV request format and transport

**Context:** The project caps runtime dependencies at two (`fastapi` + `uvicorn`)
and `python-multipart` is not installed, so a `multipart/form-data` file upload
would add a runtime dependency and fail the existing dependency-cap test. The
intent only says "takes a CSV with one text per row".

**Question:** What request format should `POST /v1/analyses/import` accept?

- **A.** Raw request body with `Content-Type: text/csv` (or `text/plain`), one text per line, single column, **no header row**; parsed with the standard-library `csv` module. No new runtime dependency.
- **B.** Raw request body with `Content-Type: text/csv`, one text per line, and if the first line is exactly `text` treat it as a header row and skip it.
- **C.** JSON body `{"csv": "<csv text>"}` with `Content-Type: application/json`, parsed with the standard-library `csv` module.
- **D.** `multipart/form-data` file upload, which requires adding `python-multipart` and changing the two-runtime-dependency cap.
- **X.** Other (please specify)

[Answer]: B

## Q3. Is `import_id` part of the record contract?

**Context:** `import_id` must be stored to group and export bulk-imported rows. The
stored/returned analysis record is defined in four hand-written places
(`RECORD_FIELDS`, the `AnalysisRecord` fields, `to_dict()`, and the SQL column
tuple plus DDL), so whether `import_id` joins the public record changes how much
has to be threaded and what the existing endpoints return.

**Question:** Should `import_id` be part of the per-analysis record contract, or storage-only?

- **A.** **Storage-only.** `import_id` groups rows for export but is not added to the per-analysis JSON returned by the existing endpoints (`POST /v1/analyze`, `GET /v1/analyses`); the import response exposes it at the top level. Individual rows analyzed one at a time have no `import_id`.
- **B.** **Part of the record contract.** Add `import_id` to `AnalysisRecord` and every copy of the contract, and return it (usually `null`) from the existing endpoints too.
- **X.** Other (please specify)

[Answer]: B

## Q4. Export CSV shape, ordering, and unknown `import_id`

**Context:** `GET /v1/analyses/export?import_id=...` returns CSV. The app today
only builds JSON/HTML/redirect responses, so a CSV response type and its exact
columns and headers need to be defined, including what to return for an
`import_id` with no matching rows.

**Question:** What should the export return?

- **A.** One row per analysis for that `import_id`, newest first, with columns `id,text,label,confidence,model,provider,created_at`; response `Content-Type: text/csv` with `Content-Disposition: attachment; filename="analyses-<import_id>.csv"`. An unknown `import_id` returns an empty CSV body with `200`.
- **B.** Same columns and ordering, but an unknown `import_id` returns `404` with the standard error envelope.
- **C.** Same as A, but also include the `import_id` as a column in each row.
- **X.** Other (please specify)

[Answer]: B
