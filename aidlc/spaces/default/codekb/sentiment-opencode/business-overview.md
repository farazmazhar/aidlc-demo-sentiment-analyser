# Business Overview — `very-cool-sentiment-analysis` (repo `sentiment-opencode`)

## Business Domain

Single-label **text sentiment analysis** with a local, durable history. The
product turns a short piece of text into one typed decision — `positive`,
`negative` or `neutral` — with a per-label probability triple and a confidence
score, records every decision locally, and shows the result and the recent
history in a single page.

The domain has no user accounts, no multi-tenancy, no billing and no hosting.
It is a **single-operator, localhost-only tool**: one process bound to
`127.0.0.1`, one unauthenticated page, one SQLite file on the operator's own
machine. The "business" is the operator's own workflow — try text, see the
verdict, keep the history, occasionally load a batch from CSV, and (since
`261001-analytics-layer`) read aggregates over that history.

A second, read-only face has grown beside classification: an **analytics read
layer** answering "what happened in this date range" (a per-range summary:
totals, per-label counts, shares, a zero-filled per-day series) and "which terms
led" (ranked significant terms per polarity). It computes entirely in-process
from the stored rows, never calls a sentiment engine, and opens no outbound
socket. The server half is complete and heavily tested; the **view half is a
scaffold** — the page carries the nav and the summary region, but the terms
section is a static placeholder and there is no date-range control yet (this is
the gap the active intent `261004-analytics-view-packaging` fills).

## Purpose

Three purposes, in priority order, each traceable to code that already exists:

1. **Decide fast, offline by default.** The app must answer with a real,
   deterministic decision on a machine with no credentials and no network. That
   is the whole reason the offline keyword engine is the default and why the
   entire test suite runs with the network hard-blocked.
2. **Escalate to a real model when the operator asks for it.** An opt-in live
   path through OpenRouter's Jev model upgrades quality without changing any
   contract above the engine seam, and degrades to the offline engine rather
   than failing the operator's flow.
3. **Keep the decisions.** Every analysis is persisted, listable, bulk-loadable
   from CSV and exportable back to CSV, so the operator can inspect or move
   their own data at any time. No retention or deletion policy exists because
   deleting the SQLite file is the accepted recovery.
4. **Report over the kept decisions.** A read-only `/v2` analytics surface
   aggregates the stored rows over a resolved date range (and optionally one
   `import_id`), so the operator can see volume, polarity and leading terms
   without exporting and counting by hand. It is additive: `/v1` is frozen and
   the analytics paths perform no write.

## Operating Context

| Aspect | Reality | Evidence |
|---|---|---|
| Deployment | A localhost checkout. `python -m pip install -e ".[dev]"` then `uvicorn app:app --reload`; a commit is the release. | `README.md` §Setup/Run it; `app/main.py:33-35` (`HOST = "127.0.0.1"`) |
| Users | One person, who is also the sole operator and decision-maker. Unauthenticated by design. | project rule: localhost-only and unauthenticated is affirmed |
| Scale | Local single-user volume. One SQLite file, per-request connections, no pooling, no cache layer. | `app/routes.py:92-98`, `app/db.py:130-142` |
| Data sensitivity | Submitted text is stored unencrypted and, in live mode, sent to OpenRouter. The API key lives only in the gitignored `config.local.toml` or process memory. | `app/repository.py:30-38`; project rule on credentials |
| Availability target | None stated. No SLO, no monitoring, no alerting, no incident process. | absence across `app/`; no `docs/`, no CI |
| Failure posture | Fail loudly at startup on a bad config or an unpreservable migration; fail with a typed envelope at request time; never store a fabricated label. A store read error on `/v2` is answered `500 STORAGE_FAILURE`, never a fabricated empty aggregate. | `app/config.py:52-58`, `app/db.py:145-168`, `app/sentiment.py:57-70`, `app/routes.py:339-403` |

## Key Functionality

| # | Capability | Entry point | Notes that matter to a reader |
|---|---|---|---|
| F1 | Analyse one piece of text | `POST /v1/analyze` | Validates input, resolves the engine, validates the typed answer, stores, then returns the row **as read back from the database** rather than echoing the in-memory payload. |
| F2 | Show recent history | `GET /v1/analyses?limit=` | Bare `LIMIT`, newest-first, no offset, cursor, total count or pagination metadata. The documented default is 50. |
| F3 | Bulk-load a CSV | `POST /v1/analyses/import` | One text per row; an exact `text` first row is a header. Blank and unanalyzable rows are skipped, never aborting the request. Returns counts, a per-label breakdown and mean confidence. |
| F4 | Export one import back to CSV | `GET /v1/analyses/export?import_id=` | Strictly scoped to the grouping key, so single-analysis rows are never included. An unknown id is a `404`, not an empty file. |
| F5 | Report engine and connection state | `GET /v1/health`, `GET /auth/status` | Both read one function, so they cannot disagree. `reason` appears only when not connected, so the payload can never name a live engine and a disconnection at once. |
| F6 | Serve the single page | `GET /` + `GET /static/*` | One hand-written HTML file with inline CSS plus one vanilla script. The page now carries a three-link nav (`nav-summary`, `nav-terms`) and an analytics summary region; the terms section is a **static placeholder** and there is no date-range control. `fetch` call sites reach `/v1`, `/v2` and `/auth/*`. |
| F7 | Connect to OpenRouter in-app | `/auth/openrouter/start`, `/auth/callback`, `POST /auth/disconnect` | PKCE (S256). The exchanged key is held in process memory for the session only and is never written to any file. |
| F8 | Read aggregates over history | `GET /v2/analytics/summary`, `GET /v2/analytics/terms` | Read-only and additive (`BR4.7`). Both accept `from`/`to` (inclusive ISO dates) and `import_id`; the terms endpoint also takes `limit`. Both share one `resolve_range`, so they describe one population. The **server half is complete; only the page wiring (terms fetch, range control, partial-failure marker, superseded-response guard) is missing.** |

Full endpoint reference, request/response shapes and the status-code matrix are
in **api-documentation.md**. Component-by-component responsibility is in
**component-inventory.md**.

## Domain Vocabulary

These names are the ubiquitous language; they appear identically in the code,
the README, the table DDL and the tests.

| Term | Meaning in this system |
|---|---|
| **Label** | One of the closed set `positive` / `negative` / `neutral`. Enforced three times: as `LABELS` in `app/sentiment.py:20`, as a `CHECK` constraint on the column (`app/db.py:44`), and by `validate_result` before anything is stored. |
| **Probabilities** | A JSON **object keyed by label** (never an array), every label present, values summing to the engine's belief. Serialised on write, decoded on read. |
| **Confidence** | The engine's confidence in the *chosen* label — not a separate score. |
| **Provider** | Which engine produced the row: `offline` for the dummy engine, the model id for the live engine, or the sentinel `unknown` for a row migrated from a store that predates the column. |
| **Model** | The specific engine build, e.g. `dummy-keyword-v1` or `typesafe/jev-1.13`. |
| **Analysis / record** | One persisted decision. The wire shape and the row shape are the same nine fields in a pinned order. |
| **Import** | One bulk-import request. Its server-minted `import_id` (a `uuid4` hex) is written on every row it persists, and is `NULL` on every single-analysis row. |
| **Effective connection** | The single payload describing which engine is actually in use right now, plus why not, when not. |
| **Mode** | What the config *intends*: `offline`, or `live` even when no usable key exists. Intent and reality are deliberately separate fields. |
| **Resolved range** | The inclusive UTC day window (`from`/`to`) plus optional `import_id` that the two `/v2` queries run against, produced by one shared `resolve_range` so the summary and the terms populations cannot disagree. An absent bound is unbounded; a range with no rows is a normal empty result, never an error. |
| **Significant term** | A token that survives `app.terms.significant_terms`: length ≥ `MIN_TERM_LENGTH` (3) and not in `STOPWORDS`, matched case-insensitively. Counting, ranking and trimming to `limit` belong to `app.analytics`, not to `app.terms`. |

## Business Rules of Record

The rules are cited in the code by identifier (`BR1.1`…`BR6.2`), so the rule set
is recoverable from the source. They are listed here as the business layer's
own statement, not as a code index.

**Engine selection**
- BR1.1 Absent config file, absent `mode`, or `mode = "dummy"` → the offline engine; any key in the file is ignored.
- BR1.2 A usable in-session credential wins over the config file.
- BR1.3 `mode = "openrouter"` with a non-empty key → live with that key.
- BR1.4 `mode = "openrouter"` with a missing or empty key → **live is recorded as intended, the app still starts on the offline engine, and a submission is refused** with an instruction naming the config file. Silent fallback on submission is forbidden.
- BR1.5 The key never appears in a repr, a log line or a response body.

**Typed decision**
- BR2.2 A result that is not exactly "one supported label plus a probability for every label" is an engine failure, never a guess.
- BR2.3 Nothing is persisted when the engine fails or the answer is incomplete.

**Storage and history**
- BR3.2 `probabilities` is a JSON object keyed by label; `created_at` is ISO 8601 UTC ending in `Z`; the field order is pinned.
- BR3.4 `intensity` is retired. Pre-v1 rows keep the value they hold; new rows leave it unset; it is never back-filled with an invented number.
- BR3.5 History is newest-first, bounded by an explicit `limit`, whose documented default is 50.
- BR3.6 An out-of-range or non-numeric `limit` is **refused with a `422`, never silently clamped**.

**HTTP boundary**
- BR4.1 Empty or whitespace-only text is invalid input and is rejected before the engine is resolved; no row is written.
- BR4.2 Data routes are versioned. `/v1` is the frozen classification contract; the additive analytics read contract lives under `/v2` (`BR4.7`). Page, asset and `/auth/*` routes are unversioned because they carry no data contract.
- BR4.3 Every failure the application code raises uses **one envelope, exactly `{code, message}`** — no field array, because the contract sets `additionalProperties: false`. Framework-generated routing errors keep FastAPI's own `{"detail": …}` shape.
- BR4.4 The health payload carries mode and connected, plus a reason only when not connected.
- BR4.7 The `/v2` analytics endpoints are **read-only and additive**: they never write, never call a sentiment engine, and never change a `/v1` response. A store read error is `500 STORAGE_FAILURE`; a bad or inverted range is `422 VALIDATION_FAILED`.

**Session authorization**
- BR6.1 The in-app key lives in process memory only. A restart starts disconnected.
- BR6.2 When OpenRouter rejects the credential, the credential is dropped on that signal alone, the next request runs offline, and the page indicator goes red again.

## Explicitly Retired and Absent Capabilities

Absence is as much a part of the domain here as presence, because several of
these look available and are not.

| Thing | Status | Why it matters |
|---|---|---|
| **`intensity`** | **Retired.** The column is still physically present and nullable, but it is absent from the record contract, never written by new rows, and never read back. It survives only on pre-v1 rows. | `AVG(intensity)` over the current table returns `NULL` for every row written since v1. Any aggregate requirement naming mean intensity is asking for a value this system does not produce. See **code-quality-assessment.md** TD-4. |
| Pagination beyond `LIMIT` | Absent. No offset, no cursor, no total count, no pagination metadata in any response. | A growing history cannot be walked; only the newest `limit` rows are reachable. |
| Retention / deletion | Absent. | There is no delete path at all — not a route, not a retention job. |
| Multi-user auth, accounts, roles | Absent by design and affirmed as a project rule (localhost-only, unauthenticated). | Any reachable process can spend the operator's key. |
| Caching, rate limiting, circuit breakers | Absent. | Nothing to protect: no shared bottleneck exists at local scale. |
| Pagination-independent reporting / analytics | **Server half present since `261001-analytics-layer`; view half a scaffold.** `app/analytics.py` owns the aggregate reads behind `GET /v2/analytics/summary` and `GET /v2/analytics/terms`; `/v1` itself is still row-fetch only. The page's terms section is a static placeholder and no date-range control exists. | The server answers both questions over one shared resolved range; the remaining gap is the page wiring — the active intent `261004-analytics-view-packaging` — see **code-quality-assessment.md** TD-12. |

## Domain Invariants Worth Protecting

1. **Nothing fabricated is ever stored.** A refused attempt leaves the store untouched; a stored row always carries a real engine's real typed answer.
2. **The returned record is the persisted record.** Handlers return `AnalysisRecord.to_dict()` built from a row read back out of SQLite, not the in-memory payload.
3. **Migration never loses a row.** A migration that cannot preserve every row raises and rolls back rather than discarding data.
4. **One envelope for application errors.** No second error shape exists inside the application.
5. **The key never leaves process memory or the gitignored config file.**
6. **Analytics reads never write and never call an engine.** `app/analytics.py` and `app/terms.py` contain no write, no DDL, no socket and no credential, and `resolve_range`/`read_summary`/`read_terms` take the request's connection rather than opening one.