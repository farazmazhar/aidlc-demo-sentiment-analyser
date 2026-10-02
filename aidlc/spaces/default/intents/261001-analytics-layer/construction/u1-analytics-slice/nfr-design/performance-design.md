# Performance Design — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-design` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Upstream inputs.** `nfr-requirements/performance-requirements.md` (`NFR1.1`–`NFR1.4`
> plus the functionality-sourced concurrency posture), `nfr-requirements/scalability-requirements.md`
> (`NFR9.1`, `NFR9.4` — the range-bounded series and the range-independent
> statement count), the functional design (`functional-spec.md` Workflows 1–2;
> `rules.md` `BR2.2`, `BR2.3`, `BR3.4`, `BR3.6`, `BR6.1`, `BR6.2`; `entities.md`
> `AnalyticsSummary`/`AnalyticsSeriesEntry`), the contracts
> (`contract-summary.md` §2 C1: no retry, timeout deliberately unspecified), the
> component catalogue and ADRs (`components.md` `AnalyticsRead`/`HTTP API Surface`;
> `decisions.md` ADR-003, ADR-006, ADR-008), and the CodeKB
> (`architecture.md` §Data Flow "Read path", D2, A2, A3; `code-quality-assessment.md`
> TD-5). The accepted NFR-design assessment is `nfr-design-questions.md` (Q1 option A).
>
> **This is a design artifact.** It states architectural patterns, strategies and
> decisions, not implementation. Code is limited to short interface-level
> pseudocode that clarifies a decision.

## Performance posture in one paragraph

The whole latency budget for both endpoints is a single in-process read path: one
local SQLite file, two endpoints, no network hop, no engine invocation, no
outbound call (`BR2.8`). There is therefore **no per-hop budget to allocate** —
the 200 ms is entirely parameter-bound aggregate statements (`BR2.9`) plus
in-process aggregation, zero-fill and term ranking. The design that holds that
budget is the **bounded-work model**: the range is resolved once, read once, and
grown to its final series shape **in memory**, so neither the store's row count
nor the length of the resolved range adds an SQL statement. This is the
performance-side statement of `NFR1.3`/`NFR1.4` and the mechanism behind
`NFR9.4`.

## 1. The performance budget and how it is decomposed

| Budget component | Design allocation | Source |
|---|---|---|
| Request validation and range resolution | In-process, O(1); a `from`/`to` parse and a bounds comparison before any read (`BR1.1`–`BR1.4`, `BR4.2`, `BR4.3`). | `NFR1.1`, `NFR1.2` |
| Range-bounded aggregate read (summary) | **One** parameter-bound grouped statement over the resolved range; returns range totals and per-day buckets together. | `NFR1.3`, `BR3.4` |
| Series assembly and zero-fill | Pure in-process loop over the resolved day span; no statement per day. | `NFR1.3`, `NFR1.4`, `BR3.1`, `BR3.2` |
| Term extraction and ranking (terms) | Reads the text of rows in range once; tokenises and counts in process; ranking is a sort. | `NFR1.2`, `BR2.4`, `BR2.5` |
| Serialisation | Stdlib dict construction; the payload is bounded by the range (series) and by `limit` (term lists). | `NFR9.1`, `NFR9.2` |

**There is no component to cache, pool or queue.** A cache tier would add
invalidation risk to a file already read once per request for no measured gain
(accepted assessment). No async offload is designed: the unit's contract fixes
**no retry and no timeout** (`contract-summary.md` §2 C1, O11) because there is no
outbound call to bound; inventing a timeout would be inventing a mechanism the
system has no place for.

### The one measured variable — the fixture span

`NFR1.1`/`NFR1.2` are measured over a fixture of 10,000 stored analyses pinned to
span **exactly 365 distinct UTC days** (`NFR1.1`, `BR3.6`). The design does not
bend to that number; it states it because the in-process fill work is the one
quantity the budget measures, and `NFR9.1` makes the series length equal the days
in the resolved range. Pinning the span makes the measured work a fixed quantity,
so the budget is reproducibly checkable rather than a fixture-construction
artefact. The design's contribution to that target is simply: the fill is O(days
in range) **in memory**, never O(days) in statements (`BR3.4`).

## 2. The bounded-work model (the central performance decision)

The unit's performance identity is "the work is bounded", never "add replicas"
(`scalability-requirements.md` §Load profile). Three decisions hold that bound.

### 2.1 One grouped read, not one read per day

The read module issues **one** grouped statement to produce the per-day buckets
for the resolved range, and **one** aggregate statement (or an aggregate carried
by the same pass) for the range totals. The statement-count assertion of
`FR8.9`/`NFR1.3` traces executed statements and asserts the count is **constant**
in the number of days; this is exactly the observable form of "no query per day".

Design shape (interface-level only — not the statement text, which belongs to
Code Generation):

```text
read_summary(conn, resolved_range):
    rows = one_grouped_by_utc_day(conn, resolved_range)      # 1 statement
    totals = aggregate_over(rows)                             # in process
    series = fill_days(rows, resolved_range)                 # in process, O(days)
    return AnalyticsSummary(totals, shares, mean, series)
```

The invariant the design guarantees is **statement count is a function of the
query shape, not of the range**: neither `from`/`to` widening nor store growth
adds a statement (`NFR1.3`, `NFR9.4`). A read-per-day implementation would violate
both the budget and `BR3.4`.

### 2.2 In-process zero-fill of gaps

The grouped read returns only the days that have rows. The series must carry
**one entry per UTC day in the resolved range**, ascending and continuous
(`BR3.1`), with gaps and edge days zero-filled (`BR3.2`). The fill is a pure
in-memory walk from the resolved range's first day to its last: a day present in
the grouped result takes its real values; a day absent gets `total` 0, all counts
0, all shares `null`, `mean_confidence` `null`, `mean_confidence_row_count` 0
(`BR3.2`). No second query, no `generate_series` equivalent, no per-day round
trip. The fill's cost is proportional to the resolved range's length — the one
quantity `NFR1.4`/`NFR9.1` deliberately binds the series length to.

```text
fill_days(grouped_by_day, first_day, last_day):
    for day in days_inclusive(first_day, last_day):   # O(days), in memory
        yield grouped_by_day.get(day) or zero_entry(day)
```

The **unbounded** case (no bounds, no `import_id`) resolves to the earliest
stored analysis UTC day through today inclusive (`BR1.3`), so the fill walks that
span; its length is deliberately uncapped (`NFR9.3`) and the design does not add
a cap — that is a policy question for a future scope, and adding one here would
contradict the requirement.

### 2.3 The refusal shapes that keep "unavailable" distinguishable from "empty"

Performance and correctness meet at the failure boundary: a **failed request must
never render as a plausible-looking empty result** (`NFR4.3`). The bounded-work
model therefore produces three distinct, non-overlapping outcomes, and the design
keeps them structurally separate rather than collapsing them:

| Outcome | Shape | Where produced | Not to be confused with |
|---|---|---|---|
| Empty success | `200` with each endpoint's frozen empty shape (summary: `total` 0, empty series; terms: `{positive: [], negative: []}`) | The read module, when the range matched no rows (`BR3.3`, `BR4.4`) | Never a failure; never a `404` |
| Validation failure | `422` `VALIDATION_FAILED`, nothing computed (`BR4.1`–`BR4.3`) | The route, **before** the read module is called | Never an empty result |
| Storage failure | `500` `STORAGE_FAILURE`, distinct from every validation code (`BR4.5`) | The route, when the read raises | Never mistaken for a malformed parameter |

The performance consequence is deliberate: **validation is ordered before
computation** (Workflow 1 step 2–3), so a refused request pays no read cost at
all, and a storage error is surfaced as an error rather than degraded into a
zero-filled series. A design that swallowed a storage failure into an empty
series would be faster and wrong — it would hide an unavailable query behind an
empty answer.

## 3. Holding the budget — the mechanisms and why each is sufficient

| Mechanism | Design decision | Bound it holds |
|---|---|---|
| Parameter-bound aggregates | Every value reaches a statement only as a bound parameter (`BR2.9`); no interpolation. | Correctness and injection safety (shared with security design); the pattern is not a performance mechanism but it is the shape the read is written in. |
| Range-bounded series | The series is assembled from the resolved range, not the store (`NFR1.4`, `NFR9.1`). | Series work ∝ range length, not row count. |
| `limit`-bounded term payload | At most `limit` (default 10) entries materialised per list (`BR2.4`, `BR2.6`); an oversized value is honoured, never clamped. | Term payload ∝ `limit`, not store size (`NFR9.2`). |
| Zero-fill in process | Gaps grown in memory (`BR3.2`). | No statement per gap day. |
| No cache, no pool | The data is a local file read once per request (`A2`); the connection is short-lived and owned at the HTTP edge (`BR6.1`). | No invalidation risk, no stale state, no pool resource. |
| Measurement isolation | The timing is taken **without coverage instrumentation** (`BR3.6`), because `--cov` inflates wall time. | The budget measures the read path, not the harness. |

**What is deliberately absent, and why.** No query cache, no prepared-statement
pool, no background warm-up, no materialised view. Each would add a lifecycle and
an invalidation surface to a path whose measured cost is already a single local
read; the accepted assessment concluded these have no mechanism to exist here,
and the design agrees rather than inventing them.

## 4. The concurrency posture is not a performance target

The cross-thread connection fix (R-01) is **functionally sourced** (`FR1.6`,
`BR6.3`, `FR8.4`) and has **no inception NFR parent**; the NFR-requirements review
corrected exactly that mis-parenting (review-01 R-01). It is designed in
`reliability-design.md` §3, because it is a failure-behaviour concern, and its
performance-visible requirement — that two overlapping requests do not serialise
behind a per-request schema re-initialisation — is a **consequence** of the
harness hoisting schema initialisation out of the request path (`BR6.4`), not a
throughput target. There is **no RPS target**; the store is a single-user local
file (`NFR9`).

## 5. Traceability

| NFR (this unit) | Design solution (this file) |
|---|---|
| `NFR1.1` | §1 budget decomposition; §3 parameter-bound single read; 365-day pinned fixture (§1). |
| `NFR1.2` | §2.1 single text read + in-process counting/ranking; §3 `limit`-bounded payload. |
| `NFR1.3` | §2.1 one grouped read; statement count constant in day count (`BR3.4`, `NFR9.4`). |
| `NFR1.4` | §2.2 series length equals resolved-range day count; fill bounded by range. |
| Concurrency posture (functional, no NFR parent) | §4 + `reliability-design.md` §3 (thread-affinity decision). |

Full id-level enumeration is in `traceability.json`.
