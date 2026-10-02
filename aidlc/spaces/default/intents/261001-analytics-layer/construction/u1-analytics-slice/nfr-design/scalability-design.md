# Scalability Design — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-design` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Upstream inputs.** `nfr-requirements/scalability-requirements.md` (`NFR9.1`–`NFR9.4`
> and the "scalability means bounded work, not throughput" framing),
> `nfr-requirements/performance-requirements.md` (`NFR1.3`, `NFR1.4` — the
> performance-side mirror), the functional design (`rules.md` `BR1.3`, `BR2.4`,
> `BR2.6`, `BR3.1`–`BR3.4`; `functional-spec.md` Workflows 1–2), the contracts
> (`contract-summary.md` §2 C1 `limit`; §2.2 storage surface), the component
> catalogue (`components.md` `AnalyticsRead`; ADR-008), and the CodeKB
> (`architecture.md` A2, §Aggregate-query surface; `code-quality-assessment.md`
> TD-7). Accepted assessment: `nfr-design-questions.md` Q1 option A.
>
> **This is a design artifact.**

## Scalability posture in one paragraph

The store is a **single-user local SQLite file**; there is no multi-user,
multi-tenant or network load (`scalability-requirements.md` §Load profile). So
"scalability" here means **bounded work**, not throughput, and **there is no
horizontal-scaling target to state**. The design that delivers bounded work is
the same model as `performance-design.md` §2: resolve the range once, read it
once, grow the series in memory, bound the term payload by `limit`. Every scaling
pattern the stage lists — horizontal scaling, load balancing, sharding, queues —
has **no mechanism to exist** in a single loopback process over one file, and the
design says so rather than inventing one.

## 1. Load profile and scaling model

| Aspect | Reality (derived, not invented) | Source |
|---|---|---|
| Load | Single user; the concurrency constraint is about *not failing* when two requests overlap, not about scaling to load. | `NFR9`, `BR6.3` |
| Growth | Slow and operator-driven: one row per analysed text or per imported CSV line; store on the local filesystem, gitignored. | `technology-stack.md` §Database |
| Read path under growth | Aggregate reads are bounded per request; the terms payload is bounded by `limit`; the **unbounded series** is the one quantity that tracks history length. | `NFR9.1`, `NFR9.2`, `NFR9.3` |
| Schema growth | Additive only, one fixed index set (`BR5.1`–`BR5.3`); no migration of existing rows. | `BR5`, `contract-summary.md` §2.2 |
| Capacity plan | None exists and none is invented: no hosted tier, no pool, no autoscaling, no queue. The only capacity-shaped statement is the performance fixture size (10,000 rows / 365-day span) used as the representative working set. | `scalability-requirements.md` §Capacity planning |

## 2. The bounded-work guarantee

The design's scaling story is four invariants, each already mechanised by the
read path; the design states *how* each holds, not a new mechanism.

| Invariant | Design | Source |
|---|---|---|
| **Series length = days in the resolved range.** One entry per UTC day of the resolved range (ascending, continuous, zero-filled); an empty range is an empty series. Work is a function of the range, never the store's row count. | Range resolved once (`BR1.1`–`BR1.3`); series assembled and zero-filled in process (`BR3.1`, `BR3.2`). | `NFR9.1`, `NFR1.4` |
| **No response grows with the store.** A bounded range bounds the series; the terms payload materialises at most `limit` entries per list whatever the store holds. | `limit` default 10, applied per list; oversized honoured, never clamped (`BR2.4`, `BR2.6`). | `NFR9.2` |
| **The unbounded series is deliberately uncapped.** Neither bound and no `import_id` → earliest stored analysis UTC day through today inclusive; its length is the stored-data span. **No cap is imposed**, and the omission is deliberate. | `BR1.3`; the design adds no cap. This is a policy question for a future scope. | `NFR9.3` |
| **Statement count does not grow with the range span.** One grouped read over the range plus an in-process fill; neither range length nor store size adds statements. | `BR3.4`; the `FR8.9` trace hook asserts a constant count across two ranges. | `NFR9.4`, `NFR1.3` |

The one quantity that can grow without a caller-imposed bound is the unbounded
series length — and the design binds its *cost* (one grouped read, one in-process
fill) even though it does not bind its *length*. That is the honest reading of
`NFR9.3`: **cost is bounded, length is not**, and the design records that
distinction rather than papering over the uncapped case.

## 3. Patterns declared inapplicable, with stated reasons

An absent design with a stated reason is a design decision; an absent design with
no reason is an oversight. Each line below is the reason.

| Pattern family | Applies? | Why not |
|---|---|---|
| **Horizontal scaling / replicas** | **No.** | The deployment is one loopback process over one local file (`NFR9`). There is no place to put a second replica and no load to distribute; adding one would contradict the localhost-only mandate. |
| **Load balancing** | **No.** | There is no second instance to balance to, and the run path is a single documented `uvicorn app:app` invocation. |
| **Data partitioning / sharding** | **No.** | The data is a single SQLite file owned by `Persistence and Schema`; sharding it would break the single-store ownership rule for no gain at single-user scale. |
| **Queue-based decoupling** | **No.** | The read path is synchronous request → read → respond with no outbound call and no background work (`BR2.8`); there is nothing to decouple and no broker permitted under `C-5`/`C-6`. |
| **Caching tiers / CDN / lazy loading** | **No.** | The data is a local file read once per request (`A2`); a cache would add an invalidation surface for no measured gain (accepted assessment). |
| **Auto-scaling rules / capacity thresholds** | **No.** | No hosted tier, no autoscaler, no threshold to tune. The single capacity-shaped statement is the performance fixture. |
| **Stateless-design-for-scaling** | **No (not a lever here).** | The process is already effectively stateless per request (short-lived connection, no shared mutable state beyond `session_auth`); this is a correctness property (`BR2.7`), not a scaling lever, because there is only one process. |

## 4. What growth the design *does* accept, and where it is noted

- **Schema surface** grows additively by a bounded, fixed set (three indexes,
  `BR5.1`–`BR5.3`); no data migration of existing rows. This is a fixed growth,
  not an open-ended one.
- **Store growth** is operator-driven and slow; the read path's bounded-work
  guarantee is what makes store growth a non-event for latency and payload size
  (`NFR9.2`), except for the deliberately uncapped unbounded series (`NFR9.3`).
- **History walking** is *not* in this unit's scope. `code-quality-assessment.md`
  TD-7 notes the existing history read has no pagination beyond a bare `LIMIT`;
  the design notes it as adjacent context and adds no pagination to the
  analytics endpoints, because `NFR9.2` already bounds every analytics response
  except the unbounded series.

## 5. Traceability

| NFR (this unit) | Design solution (this file) |
|---|---|
| `NFR9.1` | §2 row 1 — series length equals resolved-range day count; in-process fill. |
| `NFR9.2` | §2 row 2 — `limit`-bounded term payload; range-bounded series. |
| `NFR9.3` | §2 row 3 + §4 — unbounded series deliberately uncapped; cost bounded, length not. |
| `NFR9.4` | §2 row 4 — constant statement count; shared instrument with `NFR1.3`. |

Full id-level enumeration is in `traceability.json`.
