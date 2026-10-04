# Contract Summary — sentiment-opencode v2 analytics layer

> **Intent:** `261001-analytics-layer` · stage `contract-design` (inception) ·
> brownfield extension of a working local app.
>
> **Upstream this contract pins:** `inception/units-generation/unit-of-work.md` and
> `unit-of-work-dependency.md` (the four units and the DAG, including the declared
> `U1 → U2` edge), `inception/domain-design/components.md` and `decisions.md` (the
> twelve-row component catalogue and ADR-001…ADR-009), `inception/requirements-analysis/requirements.md`
> (**including its Revision 2 corrections**), `inception/user-stories/stories.md`,
> `inception/refined-mockups/mockups.md`, the CodeKB's
> `aidlc/spaces/default/codekb/sentiment-opencode/api-documentation.md`, and the
> **running code** (`app/routes.py`, `app/models.py`, `app/repository.py`,
> `app/db.py`, `app/static/app.js`, `tests/test_page.py`).
>
> **This artifact pins boundaries once; it does not restate `/v1`.** The `/v1`
> surface is frozen and remains recorded by the README's `## HTTP surface` table
> (19 rows today), with `api-documentation.md` as its exhaustive verified twin.
> This contract describes the new `/v2` surface plus the two inter-unit edges, and
> it requires the README (updated under `FR7.9`) and this artifact to agree after
> the change.
>
> **Ground truth rule.** Every *existing* shape restated here was read out of the
> running code, not copied from prose. Where the requirements prose and the code
> disagree, the disagreement is stated in **§5 Ground-truth reconciliation** rather
> than silently resolved. A prior intent's contract review caught three critical
> mismatches by skipping this comparison; that comparison is done here.

---

## 1. Contracts table

| # | Provider Unit | Consumer | Mechanism | Owner |
|---|---|---|---|---|
| **C1** | `U1` (`u1-analytics-slice`) | **External: the page's script** (`app/static/app.js`, part of `Web UI`/`U3`) and any future loopback consumer | HTTP/JSON, `/v2` prefix | **U1** |
| **C2** | `U1` (`u1-analytics-slice`) | `U3` (`u3-analytics-view`) | HTTP/JSON on the same `/v2` wire — the consumer-supplier agreement over C1 | **U1** |
| **C3** | `U2` (`u2-term-extraction`) | `U1` (`AnalyticsRead` term ranking and the `/v2/analytics/terms` handler) | Plain Python call (import) | **U2** |

**Why C1 and C2 overlap on one wire.** Accepted decision 2 pairs the public surface
with HTTP/JSON and the two inter-unit boundaries with shared-schema pins rather than
OpenAPI. In this system the two inter-unit edges are **not the same kind of seam**:
`U3 → U1` is the browser/server seam and *is* a wire protocol (the analytics view is
one script fetching the endpoints), while `U1 → U2` is the only plain-Python import.
C1 is the provider-side public spec (OpenAPI); C2 is the internal consumer-side
agreement pinned as a shared schema; C3 is the plain-Python edge pinned as a shared
schema. Reading decision 2's phrase "plain Python calls at the two inter-unit
boundaries" literally would misdescribe `U3 → U1`, which both the component graph
(`Web UI -> HTTP API Surface`) and `unit-of-work-dependency.md` fix as HTTP. Recorded
explicitly so no reader assumes a second import edge that does not exist.

---

## 2. Contract C1 — the public `/v2` HTTP surface

**Provider:** `U1` · **Consumer:** External: the page's script (`app.js`) and any
future loopback consumer · **Mechanism:** HTTP/JSON, loopback only (no new egress).

**Endpoints.** Exactly two, both `GET`, both on `v2_router` under the `/v2` prefix:

| Endpoint | Query parameters | Defaults | Statuses |
|---|---|---|---|
| `GET /v2/analytics/summary` | `from`, `to`, `import_id` — **all optional** | neither bound and no `import_id`: earliest stored analysis UTC day through today, inclusive | `200`, `422`, `500` |
| `GET /v2/analytics/terms` | `from`, `to`, `import_id`, `limit` — all optional | `limit` = **10, applied per list**; bounds as above | `200`, `422`, `500` |

There is **no `limit` parameter on the summary endpoint** (`FR2.2`); `limit` belongs
to `/v2/analytics/terms` only (`FR3.2`). A `limit` sent to the summary endpoint is an
unknown query parameter and is ignored by FastAPI's binding — see §5.

**Range resolution (shared by both endpoints, `FR3.8`).**

- `from` / `to` are UTC calendar dates written `YYYY-MM-DD` (`FR2.4`). Both ends are
  **inclusive**; `to` bounds the whole day `T00:00:00Z`–`T23:59:59.999999Z`.
- A single bound is never dropped (`FR2.5`): `from` alone → that day through now;
  `to` alone → beginning of history through that day.
- Neither bound and no `import_id` → earliest stored analysis UTC day through today,
  inclusive (`FR2.6`).
- `import_id` is an **opaque string** (server-minted `uuid4().hex`). It has no parse
  step. An id that matches no rows behaves exactly like an empty range: `200`, empty
  series, **no store-wide zero-fill** (`FR2.6`, `FR2.10`, `R-03`/`Q10` rulings).
  With a matched `import_id` and no bounds, the range is the span of the matching
  rows (pinned here; see §8.1).
- **Inverted range** (`from` later than `to`) is **refused**: `422 VALIDATION_FAILED`,
  nothing computed, and the message text names **both** `query.from` and `query.to`
  (`FR2.11`, `R-04`/`Q11`). The envelope carries **no `field` member** (`FR2.11`
  Revision 2).
- No parameter is ever silently defaulted or clamped (`FR2.11`).

**Series / zero-fill rule (the reconciled reading).**

- A range that matches **at least one row** yields a series with **one entry per UTC
  calendar day in the resolved range**, ascending, continuous, **zero-filled for
  internal gaps**.
- A range that matches **no rows** yields an **empty series** (`[]`) — never a
  zero-filled span, never a `404` (`FR2.9` qualified by `FR2.10`, reconciled by the
  `user-stories` `Q10` ruling). Zero-filling applies **only to the gaps inside a
  matched range**.

**Error envelope (`FR2.12`, `NFR5`).** Exactly two top-level keys, at the top level —
never nested under `error`, never carrying a `field` member or an `errors`/`details`
array (verified against `app/routes.py:69-79`, `api-documentation.md:227-238`):

```json
{ "code": "VALIDATION_FAILED", "message": "query.limit: Input should be greater than or equal to 1" }
```

- `422 VALIDATION_FAILED` — malformed `from`/`to`; `limit` below 1 or non-numeric
  (terms only); an inverted range (message names both fields). The message text names
  the offending parameter itself, because the envelope has no `field` member.
- `500 STORAGE_FAILURE` — a `sqlite3` error raised while reading. This code is
  **distinct from every validation code** and is the **only permitted addition to the
  envelope's code set** (`FR2.12`, `NFR5`, `US8.5.2`). `FR2.12` fixes the literal at
  **Contract Design**; this contract therefore fixes it here as `STORAGE_FAILURE`.
- Framework-generated routing errors keep FastAPI's own shape (`404 {"detail": …}`
  for an unknown path, `405 {"detail": …}` for a wrong method) and are **outside** the
  envelope — a binding project rule, not an accident.

**Timeout and retry.** **No retry.** The page surfaces a failure rather than
auto-retrying, because a silent retry would make a stale range look current. The
**request timeout is explicitly unspecified** — it is the client's own choice and no
timeout value is part of this contract.

### 2.1 C1 spec — OpenAPI (the public surface)

```yaml
openapi: 3.1.0
info:
  title: sentiment-opencode analytics API (/v2)
  version: "2.0.0"
  description: >
    The public /v2 read surface. Provider U1; consumer the page's script (and any
    future loopback consumer). Loopback only; no new egress path. Additive-only
    within /v2; a breaking change requires a new prefix. /v1 is frozen.
servers:
  - url: http://127.0.0.1:8000
paths:
  /v2/analytics/summary:
    get:
      operationId: getAnalyticsSummary
      summary: Aggregates over the resolved range and optional import_id filter.
      parameters:
        - $ref: '#/components/parameters/From'
        - $ref: '#/components/parameters/To'
        - $ref: '#/components/parameters/ImportId'
      responses:
        '200':
          description: >
            The computed summary. A range matching no rows is still 200 with
            total 0 and series [] (never 404).
          content:
            application/json:
              schema: { $ref: '#/components/schemas/AnalyticsSummary' }
        '422': { $ref: '#/components/responses/ValidationFailed' }
        '500': { $ref: '#/components/responses/StorageFailure' }
  /v2/analytics/terms:
    get:
      operationId: getAnalyticsTerms
      summary: Ranked positive/negative term lists over the resolved range.
      parameters:
        - $ref: '#/components/parameters/From'
        - $ref: '#/components/parameters/To'
        - $ref: '#/components/parameters/ImportId'
        - $ref: '#/components/parameters/Limit'
      responses:
        '200':
          description: >
            Up to `limit` (default 10) entries per list. A label with no rows in
            range yields an empty array, never null.
          content:
            application/json:
              schema: { $ref: '#/components/schemas/AnalyticsTerms' }
        '422': { $ref: '#/components/responses/ValidationFailed' }
        '500': { $ref: '#/components/responses/StorageFailure' }
components:
  parameters:
    From:
      name: from
      in: query
      required: false
      description: >
        Inclusive lower bound: a UTC calendar date YYYY-MM-DD. With `to` absent it
        means the beginning of history; absent with `to` absent too, the default
        span applies.
      schema:
        type: string
        format: date
        pattern: '^\d{4}-\d{2}-\d{2}$'
    To:
      name: to
      in: query
      required: false
      description: >
        Inclusive upper bound: a UTC calendar date YYYY-MM-DD; it bounds the whole
        day T00:00:00Z..T23:59:59.999999Z.
      schema:
        type: string
        format: date
        pattern: '^\d{4}-\d{2}-\d{2}$'
    ImportId:
      name: import_id
      in: query
      required: false
      description: >
        Opaque grouping key (server-minted uuid4().hex). Optional, no parse step.
        An id matching no rows is an empty population: 200 + empty series, not 404
        and not 422.
      schema: { type: string }
    Limit:
      name: limit
      in: query
      required: false
      description: >
        Applies per list. Default 10. Below 1 or non-numeric is refused 422, never
        clamped. An oversized value is honoured (every available term returned); no
        upper bound is imposed.
      schema:
        type: integer
        minimum: 1
        default: 10
  schemas:
    AnalyticsSummary:
      type: object
      additionalProperties: true
      required: [total, counts, shares, mean_confidence, mean_confidence_row_count, series]
      properties:
        total:
          type: integer
          minimum: 0
          description: Rows in the resolved range after the import_id filter.
        counts: { $ref: '#/components/schemas/LabelCounts' }
        shares: { $ref: '#/components/schemas/LabelShares' }
        mean_confidence:
          type: [number, 'null']
          description: >
            Arithmetic mean of `confidence` over EVERY row in range (Revision 2;
            confidence is NOT NULL in the shipped schema), rounded to 4 decimals.
            null iff total is 0.
        mean_confidence_row_count:
          type: integer
          minimum: 0
          description: >
            How many rows contributed. Always equals `total` (Revision 2), so 0
            when total is 0. This is the response stating its own denominator.
        series:
          type: array
          description: >
            Ascending; one entry per UTC calendar day in the resolved range,
            zero-filled for internal gaps; [] when the range matched no rows.
          items: { $ref: '#/components/schemas/AnalyticsSeriesEntry' }
    AnalyticsSeriesEntry:
      type: object
      additionalProperties: true
      required: [date, total, counts, shares, mean_confidence, mean_confidence_row_count]
      properties:
        date:
          type: string
          format: date
          pattern: '^\d{4}-\d{2}-\d{2}$'
          description: The UTC calendar day this entry aggregates.
        total: { type: integer, minimum: 0 }
        counts: { $ref: '#/components/schemas/LabelCounts' }
        shares: { $ref: '#/components/schemas/LabelShares' }
        mean_confidence:
          type: [number, 'null']
          description: 4-decimal mean over the day's rows; null iff the day's total is 0.
        mean_confidence_row_count:
          type: integer
          minimum: 0
          description: Equals the day's `total` (0 on a zero-filled day).
    LabelCounts:
      type: object
      additionalProperties: true
      required: [positive, negative, neutral]
      description: >
        Keyed by the closed label set LABELS = (positive, negative, neutral); every
        label is present, zero-valued labels included.
      properties:
        positive: { type: integer, minimum: 0 }
        negative: { type: integer, minimum: 0 }
        neutral:  { type: integer, minimum: 0 }
    LabelShares:
      type: object
      additionalProperties: true
      required: [positive, negative, neutral]
      properties:
        positive: { $ref: '#/components/schemas/Share' }
        negative: { $ref: '#/components/schemas/Share' }
        neutral:  { $ref: '#/components/schemas/Share' }
    Share:
      type: [number, 'null']
      minimum: 0
      maximum: 1
      description: >
        The label's count / total, a FRACTION in [0,1] rounded to 4 decimals (not
        a percentage). null iff total is 0: a zero denominator has no answer and
        the project refuses to substitute a fabricated 0.0.
    AnalyticsTerms:
      type: object
      additionalProperties: true
      required: [positive, negative]
      description: >
        Exactly two lists. There is no `neutral` list: rows labelled neutral
        contribute to neither (FR3.6). Lists are keyed by label to mirror the
        summary's counts/shares keying.
      properties:
        positive:
          type: array
          description: Up to `limit` entries, count desc, ties broken alphabetically.
          items: { $ref: '#/components/schemas/TermFrequencyEntry' }
        negative:
          type: array
          description: Up to `limit` entries, count desc, ties broken alphabetically.
          items: { $ref: '#/components/schemas/TermFrequencyEntry' }
    TermFrequencyEntry:
      type: object
      additionalProperties: true
      required: [term, count]
      description: >
        A term and its occurrence count only: no share, no score, no weighting.
      properties:
        term:
          type: string
          description: A significant term (>= 3 chars, not in the stopword list).
        count: { type: integer, minimum: 1 }
    ErrorEnvelope:
      type: object
      additionalProperties: false
      required: [code, message]
      properties:
        code:
          type: string
          enum: [VALIDATION_FAILED, STORAGE_FAILURE]
        message:
          type: string
          description: >
            Names the offending parameter(s) itself. No `field` member and no
            `errors`/`details` array exist on this envelope.
  responses:
    ValidationFailed:
      description: >
        422 VALIDATION_FAILED. message names query.from, query.to, query.import_id
        or query.limit; an inverted range names BOTH query.from and query.to.
        Nothing is computed.
      content:
        application/json:
          schema: { $ref: '#/components/schemas/ErrorEnvelope' }
    StorageFailure:
      description: >
        500 STORAGE_FAILURE, distinct from every validation code: a sqlite3 error
        raised while reading.
      content:
        application/json:
          schema: { $ref: '#/components/schemas/ErrorEnvelope' }
```

**Field-by-field notes not fully expressible in OpenAPI.**

- **Object member order is not part of the contract** — a consumer must not depend
  on JSON key order. **Array order is part of the contract**: `series` ascending by
  `date`; each term list by `count` descending, ties broken alphabetically
  (`FR3.5`), a total and stable order a test can pin.
- **Rounding**: `shares` and both `mean_confidence` fields are **4 decimal places**
  (`FR2.7`, `FR2.8`). The **rounding tie rule is unspecified** (open point O1).
- **Nullability**: `shares.*` and `mean_confidence` are `null` exactly when their
  denominator (`total`, or the day's `total`) is 0. `counts.*`,
  `mean_confidence_row_count` and `total` are always integers.
- **Empty-result shape** (both endpoints, `FR2.10`): summary = `total: 0`,
  `counts: {positive: 0, negative: 0, neutral: 0}`, `shares: {positive: null,
  negative: null, neutral: null}`, `mean_confidence: null`,
  `mean_confidence_row_count: 0`, `series: []`; terms = `{positive: [], negative: []}`.
- **`resolved_range` is deliberately absent from the wire.** `components.md` records
  `resolved_range` as the `AnalyticsSummary` computed-shape identifier, but `FR2.3`
  fixes the response to exactly six fields, none of them a resolved-bounds field.
  This contract pins the wire to `FR2.3`'s six fields (see upstream correction UC3, §8.2).
- **Money/no credentials**: no response body carries credential material (`NFR2`).
- **Forward-compatible success payloads vs the frozen envelope.** The success
  schemas (`AnalyticsSummary`, `AnalyticsSeriesEntry`, `LabelCounts`, `LabelShares`,
  `AnalyticsTerms`, `TermFrequencyEntry`) are `additionalProperties: true`: `required`
  pins the fields the provider emits, while open additional properties let a consumer
  tolerate an additive field (accepted decision 5, §6). The `ErrorEnvelope` alone
  stays `additionalProperties: false`, because its shape is frozen at exactly
  `{code, message}` (G3, `AC8.5.2`); additive openness there would contradict the
  verified envelope.

### 2.2 C1 spec — the `U1` schema surface (shared-schema)

The migration is part of `U1`'s provider surface: it runs at startup and every read
in C1 stands on it. Pinned here as a shared schema because it is a storage surface,
not a wire.

```yaml
shared-schema: u1-storage-surface
provider: U1  # Persistence and Schema, changed inside the existing component (ADR-004)
schema_version:
  from: 3
  to: 4
  recorded_in: schema_meta  # key 'version', written in the SAME transaction as the migration (FR5.7)
indexes:
  - name: idx_analyses_created_at
    columns: [created_at]
  - name: idx_analyses_import_id
    columns: [import_id]
  - name: idx_analyses_label_created_at
    columns: [label, created_at]
rules:
  - >
    The v3 -> v4 step is additive and idempotent: no column dropped, renamed or
    retyped; no row discarded or rewritten; a store already at v4 changes nothing
    (FR5.1, FR5.4).
  - >
    The three indexes are created BY NAME, and re-created explicitly as statements
    in `_rebuild_analyses` after RENAME -> CREATE TABLE -> COPY -> DROP TABLE,
    because SQLite's CREATE TABLE declares no index (FR5.2, FR5.3 Revision 2; ADR-004).
  - >
    A test asserts the three indexes by NAME via sqlite_master; do NOT assert
    "exactly three indexes", because `schema_meta` (TEXT PRIMARY KEY) carries an
    implicit autoindex (`sqlite_autoindex_schema_meta_1`), so a raw count is never
    exactly three. `analyses`'s `INTEGER PRIMARY KEY AUTOINCREMENT` is a rowid alias
    and creates no autoindex — SQLite creates none for that form, and only
    `sqlite_autoindex_schema_meta_1` exists (FR8.3, R-19).
  - >
    A migration that cannot preserve every row fails loudly and rolls back in one
    transaction; never a partial migration (FR5.6).
  - >
    Existing stored timestamps are second-precision UTC ISO 8601 ending in `Z`
    (`%Y-%m-%dT%H:%M:%SZ`, `app/repository.py:39-41`); the series buckets on the UTC
    calendar date of `created_at`, so `to`'s `.999999` upper bound is equivalent to
    `<= T23:59:59Z` for every row this app writes.
```

---

## 3. Contract C2 — the `U3 → U1` inter-unit boundary

**Provider:** `U1` · **Consumer:** `U3` (`app/static/app.js` inside `Web UI`) ·
**Mechanism:** HTTP/JSON on the same `/v2` wire as C1. Pinned as a shared schema
(the consumer-supplier agreement), not as a second OpenAPI document.

**What the view sends.** Exactly two `GET` requests per populated render, one per
section, both with the **same resolved bounds**:

- `GET /v2/analytics/summary?from=<date>&to=<date>` — feeds the summary figures, the
  per-day series and the label breakdown.
- `GET /v2/analytics/terms?from=<date>&to=<date>` — feeds the two term lists at the
  affirmed **top 10 per list**.

The page sends **no `import_id`** (no page control; the filter is API-only, `FR6.3`,
`AC6.3.3`) and **no `limit`** (`limit` is API-only; the server default of 10 applies,
`AC6.3.5`). The default first load sends no bounds (`AC6.3.1`). An explicit
`Show all time` reset returns to the unbounded request (`AC6.3.4`).

**What the view expects.** Exactly the C1 response shapes
(`AnalyticsSummary`, `AnalyticsTerms`). It uses only values an endpoint returned,
and each of the three readouts has exactly one fetch to its own endpoint
(`AC6.2.2`).

```yaml
shared-schema: u3-consumes-u1-v2
provider: U1
consumer: U3
mechanism: HTTP/JSON
requests:
  summary:
    method: GET
    path: /v2/analytics/summary
    query: [from, to]           # no import_id, no limit from the page
    response: C1.AnalyticsSummary
  terms:
    method: GET
    path: /v2/analytics/terms
    query: [from, to]           # no import_id, no limit from the page; server limit default 10
    response: C1.AnalyticsTerms
rules:
  - >
    Exactly one fetch per section, and never a value the endpoint did not return
    (AC6.2.2).
  - >
    Changing the range issues BOTH fetches with the same bounds, so all three
    readouts describe one population; never two populations at once (FR6.4, AC6.3.2).
  - >
    NO RETRY. A failed fetch renders an inline error naming the failure through the
    one app-wide error panel, rather than auto-retrying (FR6.7; accepted decision 6).
  - >
    Out-of-order discard: when two requests are in flight for one range change and
    they complete out of order, only the NEWEST range's responses render; a late
    response from a superseded range is discarded, never allowed to overwrite current
    data (AC6.5.2).
  - >
    Partial success: one section succeeds while another fails -> render the succeeded
    section plus a distinct partial-failure status; the failed section keeps its
    heading and reads an in-place marker. Loading, empty and error stay distinct
    regions (AC6.5.3, AC6.5.5, FR6.7).
  - >
    A `null` share renders an explicit no-share marker, never a fabricated `0%`; a
    genuine `0.0` share still renders as `0.00%` (AC6.2.5, FR2.7).
  - >
    The analytics render path never shows the machine code on screen: it shows a
    status-derived lead-in plus `message`, and keeps the code in the server log.
    This deliberately diverges from the shipped Analyze path's `${code}: ${message}`
    rendering (mockups.md §1 C7, §6; U3's remit).
  - >
    Rendering is native HTML with `textContent` everywhere; no chart library and no
    new front-end dependency (FR6.6, ADR-007).
  - >
    The analytics prefix constant in `app.js` must equal the backend `V2_PREFIX`
    constant; a static assertion pins the two (AC6.2.3). See §5.
```

---

## 4. Contract C3 — the `U1 → U2` inter-unit boundary (the declared edge)

**Provider:** `U2` (`u2-term-extraction`) · **Consumer:** `U1`
(`AnalyticsRead`'s term ranking and the `/v2/analytics/terms` handler) ·
**Mechanism:** plain Python call (import). `U2` is a fan-out-0 leaf module beside
`app/sentiment.py` (ADR-002).

This edge is **real** but **suppressed from the machine-readable DAG block** so that
`U1` stays the `skeleton: on` integrated slice (`unit-of-work-dependency.md`,
"The suppressed U1 → U2 edge"). Delivery Planning must not sequence `U1`'s terms work
ahead of `U2`. Pinning it here is what stops the suppression becoming a surprise.

```yaml
shared-schema: u1-consumes-u2-term-extraction
provider: U2
consumer: U1
mechanism: plain Python call (import)
module: app/terms.py        # indicative; the module filename is pinned at Functional Design
constants:
  TOKEN_PATTERN: "maximal runs of ASCII lowercase letters and apostrophes"  # replaces app/dummy_client.py:68 `_WORD = re.compile(r\"[a-z']+\")`
  MIN_TERM_LENGTH: 3
  STOPWORDS: "single versioned in-repo English stopword constant, applied case-insensitively after lowercasing"
operations:
  tokenize:
    signature: "tokenize(text: str) -> list[str]"
    input: any str
    output: >
      Lowercased word tokens. Runs containing digits, whitespace or non-ASCII
      characters are token boundaries. NO length filter and NO stopword filter.
    consumers: [U2 offline-engine refactor of app/dummy_client.py, U1 AnalyticsRead]
  significant_terms:
    signature: "significant_terms(tokens: Sequence[str]) -> list[str]"
    aliases: [filter to significant terms]
    input: an already-tokenized token sequence (tokenize is NOT called again here)
    output: >
      The tokens that are >= MIN_TERM_LENGTH and absent from STOPWORDS, in the same
      order as the input. No counts and no ranking: ranking stays in U1.
    consumers: [U1 AnalyticsRead]
rules:
  - >
    The offline engine (app/dummy_client.py) consumes ONLY `tokenize`. It must NOT
    call `significant_terms` and must NOT apply the 3-char minimum or the stopword
    filter. Its scoring behaviour is IDENTICAL before and after; a parity test pins
    it (FR4.5, A4, AC4.2.2, AC4.2.3).
  - >
    The private `_WORD` regex (app/dummy_client.py:68, used at :83) is DELETED. No
    module imports another module's private name and no module duplicates the pattern
    (AC4.2.1; memory/team.md "The tokeniser").
  - >
    U1's analytics path calls `tokenize` then `significant_terms` on the text of rows
    in range; the terms handler returns ranked entries but all ranking and counting
    stays in AnalyticsRead, never in U2 (FR3.5, FR2.13).
  - >
    `U2` imports nothing from `app` (fan-out-0, ADR-002). No stemming, lemmatisation,
    POS tagging, weighting, learned model, downloaded corpus or external service
    (FR4.3).
  - >
    Additive-only: new operations or constants may be added; once U1 consumes an
    operation, its name, signature and semantics are frozen. Any change to `tokenize`
    must preserve offline-engine scoring parity.
  - >
    A term written entirely in a non-Latin script contributes nothing - a recorded,
    accepted limitation (FR4.6).
```

---

## 5. Version prefix — a named constant on both sides

Accepted decision 4: the version prefix is a named contract constant on both sides,
and the contract names both locations and requires them to agree. Verified against
the running code (not the prose):

| Side | Location | Current value (verified) | This change |
|---|---|---|---|
| Backend `/v1` | `app/routes.py:49` `V1_PREFIX`; consumed at `:134` `v1_router = APIRouter(prefix=V1_PREFIX)` | `"/v1"` | **Unchanged and frozen** |
| Frontend `/v1` | `app/static/app.js:10` `const API = "/v1";` | `"/v1"` | **Unchanged**; fetch sites `:87` (`/analyses`), `:97` (`/analyze`), `:157` (`/health`) stay `/v1`; `:185` `/auth/disconnect` stays unversioned |
| Backend `/v2` | `app/routes.py` — new `V2_PREFIX` constant, consumed by a new `v2_router = APIRouter(prefix=V2_PREFIX)` | **does not exist yet** (`grep v2 app/` → none) | New: `V2_PREFIX = "/v2"` |
| Frontend `/v2` | `app/static/app.js` — a new named analytics-prefix constant | **does not exist yet** | New; must equal the backend's `/v2` value |

**Rule.** The backend `V2_PREFIX` and the frontend analytics-prefix constant must be
equal, and a static assertion pins the two (`AC6.2.3`). This is the cheapest available
check for the likeliest silent break in the feature. The existing `/v1` pair
(`V1_PREFIX` ↔ `const API`) remains **two independent, unasserted copies**; this
feature adds the assertion for `/v2` only and leaves the `/v1` pair as-is, because
`/v1` is frozen.

---

## 6. Contract ownership rules

- **`U1` owns C1 and C2**: the `/v2` public surface and the `U3 → U1` boundary. It
  owns `v2_router`, both handlers, the one error envelope and the new storage-failure
  code, and the `V2_PREFIX` constant.
- **`U2` owns C3**: it owns the module being called, so it owns the operation names,
  signatures, constants and the scoring-parity guarantee the offline engine relies on.
- **Additive-only within `/v2`.** Adding a field, an endpoint or a query parameter is
  allowed and needs no new prefix. **A breaking change — removing, renaming or
  retyping a field, changing a status or machine code, or changing range/filter
  semantics — requires a new prefix (`/v3`).** A `/v2` contract is never mutated in
  place.
- **Consumers ignore unknown fields.** A consumer must tolerate a field it does not
  recognise; `U1` may add fields additively and `U3` must not break on them. Response
  objects are open to additive fields even though the provider emits the pinned set.
  This is what §2.1's success schemas encode as `additionalProperties: true` (with
  `required` pinning the emitted set); the `ErrorEnvelope` is the deliberate
  exception and stays `additionalProperties: false`, because its two-key shape is
  frozen and verified against the running code (G3).
- **`/v1` is frozen outright.** No `/v1` route, response shape, envelope shape or test
  changes. The **single** permitted change to the envelope code set is the addition of
  `STORAGE_FAILURE` (`FR2.12`, `NFR5`, `US8.5.2`).
- **How a change is agreed.** With one developer, the *owning unit* edits this artifact
  and the README, and the test suite pins what a test can pin (the prefix assertion,
  the aggregate values, the index names). A change to C1 or C2 must keep `U3` working;
  a change to C3 must keep `U1`'s calls working and scoring parity holding. A
  cross-boundary change is not agreed until both this contract and the README's
  `## HTTP surface` table state the same thing.
- **Record of truth.** The README's `## HTTP surface` table (19 rows today) is the
  `/v1` record of truth, with `api-documentation.md` as its exhaustive verified twin.
  Under `FR7.9`, `U4` updates that table for the new router and endpoints; **after the
  change, this contract, the README and `api-documentation.md` must agree.** A
  disagreement between them is a contract defect, not a documentation nit.

---

## 7. Ground-truth reconciliation against the running code

Every existing shape below was read out of the code. The prior intent's contract
review caught three critical mismatches by *not* doing this; the same three checks
are called out first.

| # | Check | What the code actually is | Consequence for this contract |
|---|---|---|---|
| G1 | **Are the paths versioned in code?** | Yes: `V1_PREFIX = "/v1"` (`app/routes.py:49`) and `v1_router = APIRouter(prefix=V1_PREFIX)` (`:134`). **There is no `/v2` anywhere in `app/` today** — the `/v2` surface is wholly new. | The contract states the new `V2_PREFIX`/`v2_router`; it does not restate `/v1`. |
| G2 | **Is the history response wrapped?** | No. `GET /v1/analyses` returns a **bare JSON array**, newest-first, unwrapped (`app/routes.py:166-177`; `api-documentation.md:92-93`). | The `/v2` payloads are likewise **bare**: the summary is a bare object and the terms payload a bare object, with no `data`/`items` wrapper. |
| G3 | **Is the error envelope nested, with a details array?** | No. `error_response` builds exactly `{"code": …, "message": …}` at the top level (`app/routes.py:69-79`); the contract sets `additionalProperties: false`; the message names the field itself (`api-documentation.md:227-238`). | The `/v2` envelope is the same two-key top-level shape. **No `error` nesting, no `field` member, no `errors`/`details` array.** |
| G4 | **How is a bad `limit` reported today?** | `422 VALIDATION_FAILED` through `handle_validation_error` (`app/routes.py:342-355`), with message `"query.limit: Input should be greater than or equal to 1"` for `limit=0`; `limit` uses `Query(..., ge=1)` and is never clamped (`app/routes.py:168`; `api-documentation.md:98`). | `/v2/analytics/terms`'s `limit` matches this convention exactly (`FR3.4`): `422 VALIDATION_FAILED`, message text begins `"query.limit: …"`. |
| G5 | **Label vocabulary** | `LABELS = ("positive", "negative", "neutral")` (`app/sentiment.py:20`); the DB `label` CHECK enforces the same closed set (`app/db.py:44`). | `counts`/`shares` always carry all three labels; the terms payload carries exactly `positive` and `negative` (no `neutral` list, `FR3.6`). |
| G6 | **Stored timestamp precision** | `format_timestamp` renders `%Y-%m-%dT%H:%M:%SZ` (`app/repository.py:39-41`) — second precision, always `Z`. | The series day is the UTC calendar date of `created_at`; `FR2.4`'s `.999999` upper bound is equivalent to `<= T23:59:59Z` for app-written rows. |

**Requirements prose vs the running code / later rulings.**

| # | Prose says | The code / later ruling says | Stated resolution in this contract |
|---|---|---|---|
| P1 | `FR2.11` (as written): 422 carries `field == "query.from"` etc. | The envelope has no `field` member; `handle_validation_error` puts the field name in the **message text** (`app/routes.py:351-352`). Requirements Revision 2 corrects this at the `user-stories` `Q11` ruling. | The message text names the offending parameter; an inverted range names **both** `query.from` and `query.to`. |
| P2 | `FR2.8`: the mean averages "only the rows that carry a confidence value", null for an empty contributor set. | `confidence REAL NOT NULL` (`app/db.py:46`); `_is_v1_shape` rebuilds a store that disagrees and aborts on a NULL. Requirements Revision 2 / `Q7` corrects it. | `mean_confidence` averages **every** row in range, 4 dp; `mean_confidence_row_count` **always equals `total`**. |
| P3 | `FR2.9` (unconditional zero-fill) vs `FR2.10` (empty series). | Reconciled by the `user-stories` `Q10` ruling. | A range matching **no rows** returns `series: []`; zero-filling applies only to internal gaps of a range that matched at least one row. |
| P4 | `FR2.9` / `AC2.3.3`: a day with no analyses reports "both mean fields null". | Revision 2: `mean_confidence_row_count` **always equals `total`**; `AC2.1.3` and `AC2.3.3`'s own first clause agree. `AC2.3.3` is self-contradictory as written. | On a zero day/range: `mean_confidence` = `null`, `mean_confidence_row_count` = `total` = **0**. Required upstream correction **UC2** (§8.2). |
| P5 | `FR5.2`: "exactly these indexes, and no others". | `schema_meta` (`TEXT PRIMARY KEY`) adds an implicit autoindex (`sqlite_autoindex_schema_meta_1`), so a raw count cannot pass; `analyses`'s `INTEGER PRIMARY KEY AUTOINCREMENT` is a rowid alias and adds none (`app/db.py:42,57`). | The three indexes are named and matched **by name**; never assert "exactly three". |
| P6 | `FR5.3`: index declarations live "in `CREATE_ANALYSES_TABLE`". | SQLite's `CREATE TABLE` has no index declaration; `CREATE_ANALYSES_TABLE` declares no index (`app/db.py:40-53`) and `_rebuild_analyses` drops/rebuilds the table (`app/db.py:233-243`). | The rebuild re-creates the three indexes as explicit statements after the copy. |
| P7 | `FR2.11`: "an unparseable `import_id` answers 422 naming `query.import_id`". | `import_id` is an opaque string (server-minted `uuid4().hex`); the export route takes any string. There is no parse step, so there is no reachable 422 trigger. An unmatched id is a `200` empty result (`FR2.6`, `FR2.10`, `AC2.4.2`). | `import_id` is pinned as an opaque optional string with **no parse failure**; unmatched → 200 + empty series. Required upstream correction **UC1** (§8.2). |
| P8 | `FR2.11`'s `limit` clause sits in the **summary** section. | The summary has no `limit` parameter (`FR2.2`: `from`, `to`, `import_id` only); `limit` is a terms parameter (`FR3.2`). FastAPI ignores an unknown query parameter. | `limit` is pinned on `/v2/analytics/terms` only. Pinned here; no upstream change (§8.1). |
| P9 | `FR2.12` says the storage-failure literal is fixed at **Contract Design**; a downstream note places it at Functional Design. | `FR2.12` and accepted decision 6 ("every status and machine code stated") both require the literal now. | This contract fixes it as **`STORAGE_FAILURE` / `500`**. Functional Design inherits it rather than inventing one. Pinned here; no upstream change (§8.1). |
| P10 | `components.md`: `AnalyticsSummary` records `resolved_range` as its identifier/attribute. | `FR2.3` fixes the response to exactly six fields, none a resolved-bounds field. | The wire payload is `FR2.3`'s six fields; `resolved_range` stays in-process. Required upstream correction **UC3** (§8.2). |
| P11 | `FR3` does not literally enumerate the terms payload's top-level keys. | `counts`/`shares` are objects keyed by label; the two entity names are `PositiveTermList`/`NegativeTermList`. | The terms payload is pinned to exactly `{positive, negative}`. Pinned here; no upstream change (§8.1). |
| P12 | `FR2.6` defines the default span for the "no `import_id`" case only. | No criterion pins the matched-`import_id`-with-no-bounds range. | Pinned as the span of the matching rows (empty if none). Pinned here; no upstream change (§8.1). |

---

## 8. Open points and upstream corrections

The former single "Open questions" table mixed two different things: points this
contract leaves genuinely unresolved, and defects in the **upstream** artifacts that
this contract has already resolved and that must be corrected where they live. They
are separated below.

### 8.1 Open contract points

| Contract | Question | Blocks |
|---|---|---|
| C1 | **O1 — 4-decimal rounding tie rule.** `FR2.7`/`FR2.8` fix 4-dp rounding but state no tie rule (half-up vs half-even disagree on e.g. `36/128 = 0.28125`). `mockups.md §9` point 10 registers this for `requirements.md` Revision 3; the mockups' fixture avoids a tie, so this contract takes no side. | U1 (implementation and the `FR8.2` hand-pinned share/mean values) |
| C3 | **O9 — stopword membership and module filename.** `FR4.4` bounds the stopword list and leaves its entries to Design; the module filename (`app/terms.py`?) is indicative here and pinned at Functional Design. Both remain decisions for a later stage, not pins this contract can invent. | U2 (the stopword constant), and U1's terms ranking that consumes it |
| C2 | **O10 — `analytics-partial` as a second surface.** `role="status"` partial region vs the one app-wide error panel (`mockups.md §9` point 2). Genuinely undecided. | U3 (markup and its page tests) |
| C1 / C2 | **O11 — request timeout.** The one value this contract deliberately leaves unspecified: it is the client's own choice, no timeout value is part of the contract, and it must not be resolved by inventing one. Recorded so it is neither silently defaulted nor mistaken for a settled number. | none (recorded non-specification) |

Former O3, O5, O7 and O8 are **not** open points and require **no** upstream change:
this contract already pins each in its body, and §7 records the reconciliation
(O3 — the terms payload's two top-level keys, §2.1; O5 — `limit` on `/v2/analytics/terms`
only, §2; O7 — the matched-`import_id` span, §2; O8 — the `STORAGE_FAILURE` literal,
§6). They are not re-opened here.

### 8.2 Upstream corrections required

These are defects in the upstream artifacts — a contradiction or a false record, not a
question this stage may leave open — and each must be fixed where it lives. None of
them blocks a unit on its own; each blocks the *upstream artifact* from being
internally consistent with this contract.

| # | Owning artifact | Defect | Change required |
|---|---|---|---|
| **UC1** (R-01) | `requirements.md` `FR2.11`; `stories.md` `AC2.4.3` | `import_id` is pinned as an **opaque** string (server-minted `uuid4().hex`, no parse step), so the criterion's required `422` naming `query.import_id` has no reachable trigger — an opaque string has no parse failure to fail. | Narrow the criterion: drop `import_id` from the `422` trigger set in `FR2.11`/`AC2.4.3`, **or** give `import_id` a validating shape whose parse can fail. Until one is chosen, this contract's opaque reading stands and no test is written for a `422` that cannot occur. |
| **UC2** (R-02) | `requirements.md` `FR2.9`; `stories.md` `AC2.3.3` (second clause) | `AC2.3.3`'s second clause says a zero-filled sibling day carries `null` for **both** mean fields; that is self-contradictory with `FR2.9`'s zero-filled entries and with `AC2.1.3`/Revision 2's "`mean_confidence_row_count` always equals `total`". | Correct the clause to the contract's reading: on a zero-filled day `mean_confidence` = `null` and `mean_confidence_row_count` = `0` (= that day's `total`). The contract's `0` is the correct value. |
| **UC3** (O2) | `components.md` `AnalyticsSummary` | `AnalyticsSummary` records `resolved_range` as the computed shape's identifier/attribute, but `FR2.3` fixes the response to exactly six fields, none a resolved-bounds field. | Remove `resolved_range` from the `AnalyticsSummary` wire attribute list — keep it only as an in-process value if it is used at all — so `components.md` agrees with `FR2.3` and §2.1. |
