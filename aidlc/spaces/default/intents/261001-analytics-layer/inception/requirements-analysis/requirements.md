# Requirements — sentiment-opencode v2 analytics layer

> **Intent:** `261001-analytics-layer` · scope `feature` · depth Standard ·
> brownfield extension of a working local app.
>
> **Revision 1**, addressing the advisory review recorded at
> `.aidlc-engine/reviews/requirements-analysis/stage/37ce79e569a3a7cd/1.review.md`
> (`NOT-READY`, 1 Critical / 11 Major / 9 Minor). Every finding is dispositioned
> in *Review Follow-up Rulings* below.
>
> **Tag legend.** `[desc]` the authoritative initial description ·
> `[Q<n>]` an answer in `requirements-analysis-questions.md` ·
> `[Cn]` the Feasibility constraint register (`ideation/feasibility/constraint-register.md`) ·
> `[RM-n]` a Rough Mockups finding (`ideation/rough-mockups/wireframes.md` and its review) ·
> `[RE]` a Reverse Engineering finding (`aidlc/spaces/default/codekb/sentiment-opencode/`) ·
> `[team]` / `[Qn-practices]` an affirmed practice in `memory/team.md` /
> `memory/project.md` and the answer that produced it ·
> `[R-nn]` a review finding, with the human's ruling on it.

## Review Follow-up Rulings

Five review findings needed a human decision and were put to the human rather than
closed by the author. Each is recorded in the audit ledger as a `QUESTION_ANSWERED`
event on this stage.

| Review finding | Ruling | Where it lands |
|---|---|---|
| **R-01** (Critical) — FR8.4 and FR8.5 could not both hold, because nothing fixed R-01 | **This feature fixes R-01.** Connection thread affinity and lifecycle are decided explicitly rather than inherited from `sqlite3`'s default. The reproducing test passes because the defect is gone. | FR1.6, FR8.4 |
| **R-08** — the share unit was the author's invention | **A fraction in `[0,1]`, rounded to 4 decimal places.** Not a percentage. | FR2.7, NFR9 |
| **R-04** — an inverted range had no stated behaviour | **422** through the envelope, naming `query.from` and `query.to` as the offending pair. | FR2.11 |
| **R-03** — `import_id` matching no rows was defined two ways | **Behaves exactly like an empty range:** 200, empty series, no store-wide zero-fill. | FR2.6, FR2.10 |
| **R-10** — the `import_id` UI disposition and term top-N were left open | **No `import_id` control on the page**; the filter stays API-only. The term lists show the affirmed **top 10 per list**. | FR6.2, FR6.3 |

The remaining fifteen findings were drafting defects and are corrected in place:
R-02 (A5 vs FR4.5), R-05 and R-20 (NFR1's bounds were false and scalability was
absent), R-06 (no measurement method or fixture), R-07 (FR8.2 named no aggregates),
R-09 (`mean_confidence_row_count` missing from the series entry), R-11 (no machine
code for a storage failure), R-12 (FR3.9's deferral list), R-13 (`mean_confidence`
had no precision rule), R-14 (token character class unstated), R-15 (broken
citations), R-16 (untagged requirements), R-17 (six constraints silently dropped),
R-18 (`target-version` obligation missing), R-19 (no fixed index set).

## Intent Analysis

The app stores every analysis it has ever performed and has never summarised any
of it. The developer — the only user, operator and decision-maker in this project
— cannot answer "how much have I analysed, what mix of labels is it, how
confident are those calls, and how is sentiment moving over time" without reading
rows by hand. [desc]

The goal is not a dashboard product. It is **a picture at a glance over rows that
already exist**: one call that answers the volume question, one call that shows
what the positive and negative text actually says, and one place in the existing
page where both can be read and narrowed by date. The engine, the persistence
contracts, the `SentimentClient` interface and the single-page shell are reused as
they are, not rewritten. [desc][C-2][C-3]

Two earlier rulings shape this document materially. **`mean intensity` is removed**
— the `intensity` column was retired in v1, is never written, and would aggregate
to a permanent `null`. [Q8] And **the analytics endpoints are `/v2`, on a new
versioned router, with the `/v1` contract untouched.** [Q7] That second ruling
**amends constraint `C-4`**, which reads "the new endpoints follow the existing
`/v1` JSON API conventions": the JSON conventions, the error envelope and the
versioned-router shape are all followed, while the prefix itself becomes `/v2`. The
amendment is the human's and is recorded here so no later stage reads `C-4` as
uncontradicted.

The work also carries eight obligations affirmed at Practices Discovery that were
not among the four stated capabilities, all of which ship in this feature by
explicit choice. [Q1-practices] That roughly doubles the effort beyond the
analytics layer itself, and it was chosen knowingly rather than by default.

## Functional Requirements

### FR1 — Analytics read layer and connection handling

- **FR1.1** Aggregate read queries live in a dedicated read module beside
  `app/repository.py` and are called from the route. The service layer is not
  inserted into the read path. [Q9-practices][C-5]
- **FR1.2** Every aggregate is computed in-process from stored rows. No external
  service, no network call, no model inference. [desc][C-5]
- **FR1.3** The read module receives the connection the HTTP layer already owns and
  never opens, closes or owns a connection itself. [team — connection ownership
  sits at the HTTP edge]
- **FR1.4** Every statement is parameter-bound. No SQL string interpolation. [team —
  parameter-bound SQL only]
- **FR1.5** The read module declares a single responsibility in its module docstring,
  in the same `Single responsibility:` form the eleven existing modules use.
  [team]
- **FR1.6** **The cross-thread connection defect (R-01) is fixed by this feature.**
  Concurrent, overlapping requests against the analytics endpoints must not raise
  `sqlite3.ProgrammingError`. The connection's thread affinity and its lifecycle are
  **decided explicitly in code** rather than inherited from `sqlite3`'s default, and
  the decision is stated in the owning module's docstring so a later reader sees
  what was chosen and why. [R-01 ruling][Q5-practices]

### FR2 — `GET /v2/analytics/summary`

- **FR2.1** The endpoint is served by a new `/v2` router. The `/v1` contract, its
  routes, its response shapes and its tests are unchanged. [Q7]
- **FR2.2** Query parameters, all optional: `from`, `to`, `import_id`.
- **FR2.3** The response carries exactly these fields: `total`; `counts`, an object
  keyed by label; `shares`, an object keyed by label; `mean_confidence`;
  `mean_confidence_row_count`; and `series`, an array of per-day entries. [R-09]
- **FR2.4** `from` and `to` are UTC calendar dates written `YYYY-MM-DD`. Both ends
  are inclusive, so `to` bounds that entire calendar day from `T00:00:00Z` to
  `T23:59:59.999999Z`. [Q3]
- **FR2.5** A single bound is never dropped. `from` alone resolves to that day
  through now; `to` alone resolves to the beginning of history through that day.
  [Q4]
- **FR2.6** With **neither** bound **and no `import_id`**, the series spans the
  earliest stored analysis date through today inclusive. This default span applies
  to the unfiltered case only; an `import_id` that matches nothing does not inherit
  it. [Q12][R-03 ruling]
- **FR2.7** A share is that label's count divided by `total`, expressed as a
  **fraction in `[0,1]` rounded to four decimal places** — not a percentage. A share
  is `null` whenever `total` is 0, because a zero denominator has no answer and the
  project's convention is to refuse rather than substitute a fabricated number.
  [Q5][R-08 ruling]
- **FR2.8** `mean_confidence` averages only the rows that carry a confidence value,
  rounded to four decimal places like every other computed number here. [R-13]
  `mean_confidence_row_count` reports how many rows contributed, so a subset mean
  can never be read as a whole-range mean. An empty contributor set yields `null`
  for both. [Q13]
- **FR2.9** The series holds exactly one entry per UTC calendar day in the resolved
  range, zero-filled and continuous, in ascending date order. **Each entry carries
  `date`, `total`, `counts`, `shares`, `mean_confidence` and
  `mean_confidence_row_count`** — the row count is present per day for the same
  reason it is present overall, so a per-day subset mean is distinguishable from a
  whole-day mean. A day with no analyses reports `total` 0, all label counts 0, all
  shares `null`, and both mean fields `null`. [Q6][R-09]
- **FR2.10** An empty range is a **200 with an empty series**, never a 404. An
  `import_id` that matches no rows behaves identically — 200, empty series, no
  store-wide zero-fill — because an empty population and a non-existent population
  are the same answer. [Q5][R-03 ruling]
- **FR2.11** Validation, all through the existing error envelope, computing nothing:
  a malformed `from` or `to`, or an unparseable `import_id`, answers **422** naming
  `field == "query.from"`, `"query.to"` or `"query.import_id"`; a `limit` below 1 or
  non-numeric answers **422** naming `field == "query.limit"`. **An inverted range —
  `from` later than `to` — answers 422 naming both `query.from` and `query.to` as
  the offending pair**, because a range that cannot exist is refused rather than
  silently emptied. No parameter is ever silently defaulted or clamped.
  [Q11][R-04 ruling]
- **FR2.12** Every failure this endpoint raises travels through the single existing
  error envelope in a machine-code field. Validation failures reuse the envelope's
  existing field-naming code. A **storage failure** — a `sqlite3` error raised while
  reading — answers **500** carrying a machine code **distinct from every validation
  code**, so an unavailable query is never mistaken for a malformed parameter. That
  addition is the only permitted change to the envelope's code set; the literal code
  is fixed at Contract Design and its only testable property here is that it differs
  from every validation code. [R-11]
- **FR2.13** The analytics endpoints perform **no write and no access bookkeeping**.
  Reading analytics never mutates the store it reads.

### FR3 — `GET /v2/analytics/terms`

- **FR3.1** The endpoint is served by the same new `/v2` router. [Q7]
- **FR3.2** Query parameters: `from`, `to`, `import_id`, and `limit`. The
  `import_id` parameter is a deliberate extension of the description's
  `?from=&to=&limit=`, so that both analytics endpoints filter identically and the
  page can never present two different populations at once. It is recorded as an
  amendment to the intent's success metric, which still reads without it. [Q9]
- **FR3.3** `limit` defaults to **10** and applies **per list**, so the response
  carries up to 10 positive and 10 negative terms. Each entry carries `term` and
  `count`, and nothing else — no share, no score, no weighting. [Q7][Q2]
- **FR3.4** `limit` below 1 or non-numeric answers **422** naming
  `field == "query.limit"`, matching the existing history `limit` discipline
  exactly. [Q7]
- **FR3.5** Terms are ordered by count descending, with ties broken alphabetically.
  The order is total and stable, so a test can pin it with a hand-written expected
  value. [Q8]
- **FR3.6** Only rows labelled `positive` and rows labelled `negative` contribute. A
  row labelled `neutral` contributes to neither list.
- **FR3.7** A label with no rows in range yields an **empty array** for that list,
  never `null` and never a fabricated top-N.
- **FR3.8** Range resolution, bounds, `import_id` semantics, inversion refusal and
  the empty-result shape are **identical to FR2.4, FR2.5, FR2.6, FR2.9, FR2.10 and
  FR2.11**. The two endpoints must never disagree about which rows are in range, and
  must never disagree about what an empty answer looks like. [R-12]

### FR4 — Term extraction

- **FR4.1** Text is lowercased, then split into word tokens. A token is a maximal
  run of **ASCII lowercase letters and apostrophes**, and a token is kept only when
  it is **3 or more characters** long. Runs containing digits, whitespace or any
  non-ASCII character are token boundaries, not token characters. [Q2][R-14]
- **FR4.2** A token present in the fixed, in-repo English stopword list is excluded.
  [Q2]
- **FR4.3** No stemming, no lemmatisation, no part-of-speech tagging, no term
  weighting, no learned model, no downloaded corpus, no external service. [desc][C-5]
- **FR4.4** The stopword list is a single constant held in the repository, versioned
  with the code, and applied case-insensitively after lowercasing. Its specific
  contents are a design choice inside the bounds of FR4.1 and FR4.2. [Q2]
- **FR4.5** The tokenizer is promoted to a public, documented module beside
  `app/sentiment.py` and exposes **two distinct operations**: tokenizing text into
  word tokens, and filtering a token sequence down to significant terms. **The
  offline engine consumes only the tokenizer, and its scoring behaviour is unchanged
  by the analytics filter** — the 3-character minimum and the stopword list apply to
  analytics term extraction and not to sentiment scoring. The existing private
  `_WORD` regex is neither imported across a module boundary nor duplicated; the
  offline engine is refactored to call the promoted tokenizer. [Q2][R-02]
- **FR4.6** **Recorded limitation:** because FR4.1 admits only ASCII letters, a term
  written in a non-Latin script contributes nothing to either list. This is a known
  and accepted consequence of reusing the repository's simple tokenizer rather than
  introducing Unicode segmentation, which the two-runtime-dependency cap forbids.

### FR5 — Additive, idempotent migration

- **FR5.1** A schema-version step from v3 to v4 that is **additive only**. No column
  is dropped, renamed or retyped; no row is discarded or rewritten. [desc][C-1]
- **FR5.2** The migration creates **exactly** these indexes, and no others:
  `idx_analyses_created_at` on `created_at`; `idx_analyses_import_id` on
  `import_id`; `idx_analyses_label_created_at` on `(label, created_at)`. A fixed set
  is required so FR8.3 has a fixed expected value. [RE][R-19]
- **FR5.3** Those three index declarations live in `CREATE_ANALYSES_TABLE` as well
  as in the migration, because `_rebuild_analyses` performs `RENAME` → `CREATE
  TABLE` → `COPY` → `DROP TABLE` and would otherwise silently destroy every index on
  any migrating store. [RE][Q14-practices]
- **FR5.4** The migration is **idempotent**. Running it against an already-v4 store
  changes nothing and loses nothing.
- **FR5.5** A new table's DDL is placed after the migrate-or-create branch in
  `init_db`, following the placement `schema_meta` already uses, so it is created on
  every path. [RE]
- **FR5.6** A migration that cannot preserve every row **fails loudly and rolls
  back**, never completing partially. This also covers a store whose shape the
  migration cannot read. [C-1]
- **FR5.7** The stored schema version is incremented to 4 and written to
  `schema_meta` in the same transaction as the migration.

### FR6 — Analytics view in the existing page

- **FR6.1** The analytics view is a **third top-level entry inside the existing
  single-page shell**, added to the existing static-asset serving — not a second
  site, not a separate URL tree. [RM-1][C-3]
- **FR6.2** The view renders the per-day time series, the label breakdown with counts
  and shares, and both the positive and negative term lists at the affirmed
  **top 10 per list**. [desc][RM-6][R-10 ruling]
- **FR6.3** A date-range control narrows the view. **The default is all history with
  no bounds**, so the first view shows everything stored. **There is no `import_id`
  control on the page**; that filter is API-only, so the page always presents the
  unfiltered population and can never show a filtered subset it cannot label.
  [Q10][RM-4][R-10 ruling]
- **FR6.4** Changing the range refetches both endpoints with the same bounds, so the
  series, the breakdown and the term lists always describe the same population.
- **FR6.5** The view works **fully offline** against the dummy client. It issues no
  request other than to its own analytics endpoints. [desc]
- **FR6.6** Rendering uses native HTML elements and the page's existing class names.
  No new front-end dependency and no chart library — the runtime dependency cap
  admits none. [C-6]
- **FR6.7** A failed analytics request renders an inline error state that names the
  failure, rather than an empty chart or a silent blank. The endpoint's error
  envelope is the source of that state, so a 422 and a 500 are visibly different
  from an empty result. [RM-3]
- **FR6.8** The view meets the accessibility basics already recorded for the page:
  the range control is labelled, the series is exposed to assistive technology rather
  than drawn only visually, and status changes are announced. [RM-5]
- **FR6.9** The view's markup hooks are added to the page module's existing pinned
  test-id constant, following the convention the current page tests already assert
  rather than inventing a new pinning style. [team]

### FR7 — Practices obligations shipping with this feature

All eight were affirmed at Practices Discovery and ruled in-scope by explicit
choice. [Q1-practices]

- **FR7.1** A dependency lockfile with hashes ships, so every install resolves to
  the same set rather than to whatever is newest that day. [Q6-practices]
- **FR7.2** A platform-neutral verification script ships, and it is what runs the
  standing gates — the 80 % whole-application line-coverage floor, the
  warnings-as-errors filter and the pinned `ruff` rule set. It is neither a
  pre-commit hook nor a provider CI job. [Q3-practices]
- **FR7.3** Secret scanning and a dependency audit run as part of verification, with
  the four known fake-key fixtures in the test tree allowlisted so the first run
  produces signal rather than noise. [Q12-practices]
- **FR7.4** A `LICENSE` file ships and the installed distribution declares it.
  [Q13-practices]
- **FR7.5** The layer boundaries are expressed as `ruff` `TID251` `banned-api`
  entries, so a boundary breach is a lint failure rather than something only a
  reviewer can notice. [Q10-practices]
- **FR7.6** The loopback bind is enforced at startup. A non-loopback host fails
  loudly at startup; a documented `uvicorn` default is not enforcement, and the
  `HOST` constant becomes the value the run path actually consumes. [Q11-practices]
- **FR7.7** The in-process ASGI test harness is replaced with a shape that can host
  a genuinely concurrent request, so FR1.6 and FR8.4 can be demonstrated. [Q5-
  practices]
- **FR7.8** The linter's `target-version` is kept matched to `requires-python`, so
  the project's static analysis targets the interpreter the application actually
  runs on. [Q13-practices]
- **FR7.9** The README's `## HTTP surface` table, its `## File layout` tree and its
  `## Storage` section are updated for the new router, module and test module. The
  README's table is this project's contract of record. [RE]

### FR8 — Tests

- **FR8.1** Offline, requirement-driven tests cover both new endpoints across an
  empty range, a populated range, an `import_id` filter and term extraction. [desc]
- **FR8.2** **Every computed aggregate named in FR2 and FR3 is pinned by at least one
  test asserting a hand-written expected value.** That set is: `total`; every
  per-label `count`; every `shares` value including the zero-denominator `null`;
  `mean_confidence` and `mean_confidence_row_count`; every series entry's `date`,
  `total`, `counts`, `shares` and both mean fields; the zero-fill of a day with no
  rows; the resolved bounds of an unbounded and a single-bound range; the
  alphabetical tie-break; the per-list application of `limit`; and the refusal
  shapes for every 422 in FR2.11. The coverage floor is not a substitute. No test
  in the repository currently exercises `AVG`, `GROUP BY`, `strftime` or any
  aggregate, so a wrong date-bucket boundary would otherwise stay green.
  [Q14-practices][R-07]
- **FR8.3** A test asserts that **exactly** the three indexes named in FR5.2 exist
  after migration, by inspecting `sqlite_master`. [Q14-practices][RE][R-19]
- **FR8.4** A test reproduces R-01 against the harness from FR7.7 — issuing
  genuinely concurrent overlapping requests — and **passes because FR1.6 fixed the
  defect**. It fails if the defect returns. [R-01 ruling][Q5-practices]
- **FR8.5** The existing suite stays green with no network and no API key. The
  session-scoped offline guard stays armed, and a test continues to prove the guard
  itself is armed. [desc]
- **FR8.6** Page contract tests pin the analytics view's markup hooks, per FR6.9.
- **FR8.7** Acceptance- and API-level tests are written against the requirement or
  acceptance criterion **before** the implementation; lower-level unit tests follow
  the implementation. [team — Ordering]
- **FR8.8** The 80 % whole-application line-coverage floor still holds after this
  change, counting the new modules. [team]
- **FR8.9** **The NFR1 performance target is verified, not asserted.** A test seeds
  **10,000 stored analyses**, exercises both endpoints, and asserts each answers
  within the stated budget. The same test counts the SQL statements executed via a
  `sqlite3` trace hook and asserts the count is **constant in the number of days in
  the resolved range** — which is the observable form of "no query per day". Without
  this, neither the budget nor the query-count claim is checkable. [R-06]

## Non-Functional Requirements

- **NFR1 — Performance.** Over a local store of **10,000 stored analyses**, each
  endpoint answers in **under 200 ms**, measured by FR8.9. The number of SQL
  statements executed must be **independent of how many days the resolved range
  covers**: the series is produced by one grouped query over the range, never by a
  query per day. Neither figure is carried over from the description, which states
  none — they are engineering judgement recorded so the target is testable, and
  measurement overrides them. [R-05][R-06][A3]
- **NFR2 — Security.** No new egress path of any kind; analytics reads local rows
  only. All SQL is parameter-bound. The loopback bind is enforced at startup
  (FR7.6). No credential is added to any code path, response body, log record or
  artifact. [C-5][C-10][C-11]
- **NFR3 — Read-only guarantee.** Both endpoints are `GET` and perform no write, no
  schema change and no access bookkeeping, so a read of analytics never mutates the
  store it reads. [FR2.13]
- **NFR4 — Reliability.** A malformed parameter produces a 422 naming its own field
  and computes nothing; an inverted range is refused rather than silently emptied; a
  storage failure is a 500 distinguishable from a validation failure. A failed
  request never renders as a plausible-looking empty result. The
  refuse-never-substitute convention governs every null.
- **NFR5 — Compatibility.** The `/v1` contract, the `SentimentClient` interface and
  its adapters' behaviour, the existing error envelope **shape** and the
  `config.example.toml` / gitignored `config.local.toml` convention are all
  unchanged. The envelope's *shape* is frozen; its machine-code set gains exactly one
  member under FR2.12. [desc][C-4 as amended by Q7]
- **NFR6 — Maintainability.** New modules follow the conventions the codebase
  already holds 100 % on: a module docstring carrying a `Single responsibility:`
  line, full annotations, `from __future__ import annotations`, `UPPER_CASE`
  constants with `#:` prose comments, underscore-private helpers, and no
  junk-drawer module. Stdlib dataclasses, never `pydantic`, in `app/`. [team]
- **NFR7 — Testability.** Tests reach real SQLite and real served markup, never a mock
  of the thing under test. No browser execution is introduced, because the runtime
  dependency cap admits no browser-automation library. [team][C-6]
- **NFR8 — Observability.** An analytics failure is visible: it travels through the
  error envelope with its machine code and appears in the application log, with no
  request parameter interpolated into a SQL string. [C-12]
- **NFR9 — Scalability.** The store is a single-user local SQLite file, so
  "scalability" here means bounded work rather than throughput. **The series length
  equals the number of UTC days in the resolved range.** When the range is bounded
  by `from`/`to`, the caller bounds it. When it is unbounded (FR2.6), its length is
  the span of the stored data — the only quantity in this feature that can grow
  without a caller-imposed bound, and therefore the one a future scope may need to
  cap. `limit` has a floor of 1; its effective upper end is the number of distinct
  significant terms in range, of which the response materialises at most `limit` per
  list, so **no response grows with the size of the store**. No cap is imposed here,
  and the omission is deliberate rather than an oversight. [R-05][R-20]

## Constraints

The Feasibility constraint register, restored in full so every id resolves
upstream. [register]

| ID | Type | Constraint | Carried into |
|----|------|------------|-------------|
| C-1 | Technical | Reuse the existing SQLite database and access code; analytics adds tables/indexes only, via an additive, idempotent migration, never a destructive change | FR5.1, FR5.6 |
| C-2 | Technical | Reuse the `SentimentClient` interface and service layer; analytics reads stored rows and does not call the engine | FR1.1, A5 |
| C-3 | Technical | The analytics view is added to the existing single-page UI and static asset serving | FR6.1 |
| C-4 | Technical | The new endpoints follow the existing `/v1` JSON API conventions and the single error envelope | FR2.1, FR2.12, NFR5 — **prefix amended to `/v2` by [Q7]; the conventions and the envelope are followed unchanged** |
| C-5 | Technical | No new external service; analytics is computed in-process from stored rows | FR1.2, FR4.3, NFR2 |
| C-6 | Technical | Prefer the Python standard library; the project caps runtime dependencies at two | FR6.6, NFR7 |
| C-7 | Organizational | One developer; no second human reviewer, so stage reviews are advisory and review-before-land is self-review plus agent review | — (process, not product) |
| C-8 | Organizational | No change freeze, no competing priorities, and no external budget | — (no schedule pressure on scope) |
| C-9 | Regulatory | Privacy obligations apply: submitted/imported text may be personal data, stored locally, and sent to OpenRouter in live mode | NFR2; no new egress is added |
| C-10 | Regulatory | Keep the app localhost-only; any non-loopback bind, hosted deploy, or change to the authentication posture needs a fresh threat model | FR7.6, NFR2 |
| C-11 | Regulatory | Never commit, log, print, or paste a real credential | FR7.3, NFR2 |
| C-12 | Schedule | Soft target to land the work in one short work session; no fixed deadline | NFR8 (the verification surface a release must satisfy); note that [Q1-practices] materially widened the work, so this soft target is at risk |

## Assumptions

- **A1 — "Significant term" is now pinned**, closing the assumption carried from
  intent capture: 3+ character ASCII word tokens minus a fixed in-repo English
  stopword list, no stemming. [Q2]
- **A2 — Page placement is settled**: a view inside the existing page shell, not a
  second site. [RM-1][C-3]
- **A3 — The 200 ms budget and the constant statement count in NFR1 are engineering
  judgement**, not stated requirements. The description contains no latency figure.
  They are stated so the target is testable, and FR8.9 measures them so they can be
  revised on evidence rather than defended. [R-06]
- **A4 — `SentimentClient` satisfies C-2 vacuously here.** The description says to
  reuse `SentimentClient`, but both analytics endpoints read persisted rows and
  invoke no sentiment engine at all. The interface and both adapters' behaviour are
  therefore untouched, which satisfies C-2. **The one file that does change is the
  offline engine's, because FR4.5 promotes its private `_WORD` regex into a public
  tokenizer** — the adapter's scoring behaviour is explicitly unchanged by the
  analytics filter, and the promoted module exposes tokenization and term-filtering
  as separate operations so the two concerns cannot entangle. Stated explicitly so
  no later stage reads FR4.5 as contradicting NFR5. [C-2][R-02]
- **A5 — The transitively pulled `opentelemetry-api` does not breach C-5.**
  `fastapi` hard-depends on it, but nothing in `app/` imports `otel`, and with no
  SDK or exporter installed there is no egress. Practices Discovery recorded this
  tension without ruling on it; this requirement adopts the reading that C-5
  constrains egress and what we introduce, not what a dependency pulls in.

## Out of Scope

- Rewriting the sentiment engine, the persistence contracts, the `SentimentClient`
  interface or the single-page UI. [desc][C-2][C-3]
- Any new external service or new data egress path. [desc][C-5]
- Any destructive schema change. [desc][C-1]
- **Resurrecting the retired `intensity` column or reporting any mean intensity.**
  The column is never written, never read, and null on every row the application has
  produced; the field is removed from the requirement. [Q8]
- **A retention or delete endpoint** for stored raw text. A pre-existing gap, not
  part of this change. [feasibility R-3][C-9]
- **Term extraction for `neutral`-labelled rows.** The description asks for positive
  versus negative only.
- **An `import_id` control on the page.** The filter is API-only. [R-10 ruling]

---

## Revision 2 — corrections found by the User Stories mob

Recorded after this artifact was approved, because the User Stories mob verified
three defects against the shipped code. The story set has already been corrected;
these are the requirement-side corrections that must be carried forward.

- **`FR2.8` — the null-tolerant mean is unreachable.** The clause "averages only
  the rows that carry a confidence value", with a null result for an empty
  contributor set, describes a case that cannot occur: `confidence` is `NOT NULL`
  in the shipped schema, `_is_v1_shape` rebuilds any store that disagrees, and the
  rebuild aborts on a NULL. **Corrected reading, ruled by the human at
  `user-stories` Q7:** `mean_confidence` averages **every** row in range, and
  `mean_confidence_row_count` always equals `total`. The field is retained so the
  response states its own denominator rather than asserting one nobody can vary.
  This is the second instance in this intent of a requirement written against a
  retired or unreachable column, after `mean intensity` — and like that one, it was
  only caught by asking what the schema actually permits.
- **`FR5.3` — the named mechanism does not exist.** The requirement says the index
  declarations live "in `CREATE_ANALYSES_TABLE`". SQLite's `CREATE TABLE` has no
  index declaration; two mob participants verified this independently against a
  live interpreter. **Corrected reading:** `_rebuild_analyses` re-creates the three
  indexes explicitly as statements after the copy, and a test asserts by index
  **name** rather than by counting every `type='index'` row — the same `init_db`
  also creates an autoindex, so "exactly three" was false as written.
- **`FR6.8` — the `RM-n` citation family is unsourceable.** The requirement cites
  `[RM-5]`, and elsewhere this artifact cited `[RM-2]`. **No `RM-n` ids exist in
  the Rough Mockups artifacts at all** — verified by the User Stories review. Cite
  the wireframes finding by its actual heading or section instead. The substance of
  the accessibility requirement is unaffected; only the tags are wrong.
- **`FR8.2` — one enumerated aggregate had no criterion.** The zero-denominator
  `shares: null` at summary level was named by `FR8.2` and pinned by nothing, so an
  empty range could have answered `0.0` and passed the entire story set. A
  criterion now pins it.

> **Reading note for the first Correction bullet above:** its "corrected reading"
> omits the four-decimal rounding rule that `FR2.8` states. The rounding survives;
> see Revision 2's final bullet.

### Revision 2 — corrections found by the User Stories mob and its review

Graded **2 Critical** and 13 Major by the stage review. Both Criticals were
inherited from this artifact rather than introduced downstream, and both were
resolved by human ruling.

- **`FR2.9` versus `FR2.10` — never reconciled.** `FR2.9` requires one zero-filled
  entry per calendar day in the resolved range; `FR2.10` requires an empty series
  for an empty range. Both cannot hold for a bounded range that matches no rows.
  **Corrected reading, ruled by the human at `user-stories` Q10:** a range matching
  **no rows** returns an empty series; zero-filling applies only to the internal
  gaps of a range that matched at least one row. `FR2.9` must be qualified
  accordingly, and any criterion asserting unconditional zero-fill narrowed to
  match.
- **`FR2.11` — the envelope has no `field` member.** This requirement asks the 422
  to carry `field == "query.from"`. The envelope is exactly `{code, message}` with
  `additionalProperties: false`, and the message itself names the field — as with
  `"query.limit: Input should be greater than or equal to 1"`. An inverted range
  also needs to name *two* fields, which `errors[0]` cannot do. **Corrected
  reading, ruled at `user-stories` Q11:** one `VALIDATION_FAILED` whose **message
  text** names the offending parameter, and both `query.from` and `query.to` for an
  inverted range.
- **`FR5.2` — "exactly these indexes, and no others" is false.** `sqlite_master`
  also holds an autoindex the same `init_db` creates, so "exactly three indexes"
  cannot pass. Name the three indexes and match by name.
- **`FR7.3` — the fake-key fixture count is wrong.** This requirement says "the
  **four** known fake-key fixtures", matching `team.md`. The developer participant
  counted **six** literals matching the real key shape. Reconcile before writing any
  scanner's allowlist; until then, state no number.
- **`FR2.8`'s four-decimal rounding must survive its correction.** The first
  story-side rewrite of the `mean_confidence` simplification dropped the rounding
  rule, and `FR8.2` requires a hand-pinned value that rounding makes deterministic.
  Carry it into the correction.
- **Unicode-aware tokenization or stemming.** Reusing the repository's simple
  tokenizer is the stated approach, and FR4.6 records what that costs.
- Any change to the `/v1` contract, including the health endpoint, the auth
  endpoints, the analyze path and the CSV import/export endpoints.
- Real-time, streaming or incremental analytics. Everything is computed on request
  from stored rows.
- Market validation. The Ideation brief approved as a conditional go with
  "Market validation: pending", and that remains true.

## Open Questions

- **Which secret scanner and which dependency audit tool.** FR7.3 requires both; the
  choice is unresolved, and any scanner adopted needs the four known fake-key
  fixtures allowlisted before its first run.
- **Lockfile format and the install command that consumes it.** FR7.1 requires a
  lockfile with hashes, so "every install resolves to the same set" has no
  determinable pass/fail until the format and the command are fixed.
- **Which licence.** FR7.4 requires a `LICENSE`; the licence itself is a project
  decision and is not settled. Every installed dependency is permissive, so there is
  no compatibility constraint forcing the choice.
- **The specific stopword list.** FR4.4 bounds it and leaves the entries to Design.
- **The literal machine code for a storage failure.** FR2.12 fixes the status and
  the code's distinctness; the literal is fixed at Contract Design.
- **The analytics view's error and empty presentations in detail.** FR6.7 states the
  requirement; the specific markup belongs to Refined Mockups and Design.
- **Whether the unbounded series needs a cap.** NFR9 states the real bound and
  deliberately imposes none. A cap is a policy decision, not an oversight.
- **Whether `C-5` should reach a transitively pulled telemetry API.** A5 adopts the
  narrower reading. Practices Discovery recorded the tension without ruling on it, so
  a future scope may reverse it.
- **Whether `C-12`'s soft one-session target survives [Q1-practices].** Eight extra
  obligations plus an R-01 fix landed in the same feature. Recorded so the schedule
  expectation is not silently missed.