# Scalability Requirements — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-requirements` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Source of truth.** The sole inception parent is `NFR9`; targets below carry
> sub-numbers and a **measuring instrument**. No cap is invented: `NFR9` states
> the real bound and *deliberately imposes none*, and that omission is recorded
> rather than papered over.

## Load profile and scaling model

The store is a **single-user local SQLite file**. There is no multi-user,
multi-tenant or network load, so "scalability" here means **bounded work**, not
throughput, and there is no horizontal-scaling target to state. This framing is
`NFR9`'s, restated so the sub-requirements below are read in the right key.

| ID | Requirement | Measuring instrument | Source |
|---|---|---|---|
| **NFR9.1** | **The series length equals the number of UTC days in the resolved range.** One entry per day of the resolved range (ascending, continuous, zero-filled within a matched range); an empty range returns an empty series. The series work is therefore a function of the range, never of the store's row count. | The series-extent tests pinned by `BR3.1`/`BR3.2`/`BR3.3` (hand-written expected series over known fixtures), plus the `FR8.9` statement-count hook proving the *read* work does not grow with the day count; together they separate series *length* from read *cost*. | `NFR9`; `BR3.1`–`BR3.3`; `BR3.4` |
| **NFR9.2** | **No response grows with the size of the store.** For a bounded range the caller bounds the series; for the terms payload, at most `limit` (default 10) entries are materialised **per list**, whatever the store holds. The only quantity that can grow without a caller-imposed bound is the *unbounded* series length (the span of stored data); the terms response never does. | The `limit`-application tests of `BR2.4`/`BR2.6` (hand-written expected top-N, oversized `limit` honoured, empty label empty-not-null) and the series-extent test; a test over a large fixture asserting the response never carries more than `limit` entries per list. | `NFR9`; `BR2.4`; `BR2.6` |
| **NFR9.3** | **The unbounded series is capped by nothing, deliberately.** When `from`/`to` are absent and no `import_id` is supplied, the resolved range is the earliest stored analysis UTC day through today inclusive, and its length is the span of the stored data. **No cap is imposed**, and the omission is deliberate — it is a policy decision for a future scope, not an oversight. | Instrument: the honest bound is stated (the series length equals the resolved day count, `NFR9.1`), and the omission is recorded in the requirements' Open Questions ("Whether the unbounded series needs a cap"). No test asserts a cap, because none is required. | `NFR9`; `requirements.md` Open Questions; `BR1.3` |
| **NFR9.4** | **Statement count does not grow with the range span.** One grouped read over the range plus an in-process fill produces the per-day buckets, so neither the range length nor the store size adds statements. This is `NFR1.3` from the scalability side — the mechanism that keeps the series bounded-work rather than proportional-work. | The `FR8.9` `sqlite3` trace hook asserting a statement count constant across two ranges of different span (shared instrument with `NFR1.3`). | `NFR9`; `NFR1`; `BR3.4`; `FR8.9` |

## Growth projections and data growth

| Aspect | Reality (derived, not invented here) | Source |
|---|---|---|
| Store growth | Slow and operator-driven: one row per analysed text or per imported CSV line. The store is on the local filesystem and gitignored. | `technology-stack.md` §Database; `team.md` §Deployment |
| Read path under growth | Aggregate reads are bounded per request (`NFR9.1`, `NFR9.4`) and the terms payload is bounded by `limit` (`NFR9.2`); the unbounded series is the one quantity that tracks history length (`NFR9.3`). | `NFR9` |
| Schema growth | Additive only, one index set (`BR5.1`–`BR5.3`); no data migration of existing rows. Growth in schema surface is a bounded, fixed set. | `BR5`; `contract-summary.md` §2.2 |
| Concurrency | Single-user; the concurrency constraint (functionally-sourced — `FR1.6`, `BR6.3`, `FR8.4`; see `performance-requirements.md` § "Concurrency posture") is about not *failing* when two requests overlap, not about scaling to load. | `NFR9`; `BR6.3` |

## Capacity planning

There is no capacity target to plan against: no hosted tier, no pool, no
autoscaling, no queue. The deployment is a localhost checkout (`team.md`
§Deployment). The only capacity-shaped statement this unit carries is the
**performance fixture size** (10,000 rows pinned to a 365-day span, `NFR1.1`–`NFR1.2`) used as the
representative working set, and the bounded-work guarantees above. Stating that
no capacity plan exists is the accurate record, not a gap this stage should fill
with invented numbers.
