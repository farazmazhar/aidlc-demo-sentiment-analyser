# Performance Requirements — `u1-analytics-slice`
> **Upstream inputs.** These requirements derive from this unit's `functional-spec.md`
> (the workflows and the state the targets apply to), its `rules.md` (the `BRx.y`
> decision logic each target constrains), `requirements.md` (`NFR1`–`NFR9`), and
> `contract-summary.md` (the pinned boundary behaviour). The technology baseline is
> the brownfield `technology-stack.md`.

> **Intent:** `261001-analytics-layer` · stage `nfr-requirements` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Source of truth.** Every target below is derived from an inception NFR
> (`NFR1`) or the contract; no target is invented here. Each detailed requirement
> inherits its inception parent id and appends a sub-number (`NFR1.1`, `NFR1.2`, …)
> and names the **measuring instrument** that proves it — a target with no
> instrument is an assertion, not a requirement.
>
> **No new SLA.** The contract (`contract-summary.md` §2) adds no performance SLA of
> its own: `NFR1`'s 200 ms budget and the range-independent statement count are the
> whole of it.

## Performance targets

| ID | Target | Measuring instrument | Source |
|---|---|---|---|
| **NFR1.1** | `GET /v2/analytics/summary` answers in **under 200 ms** over a local store of 10,000 stored analyses spread across a **pinned span of 365 distinct UTC days** (one year, one row per ~27.4 days on average). | The `FR8.9` performance test: a fixture seeded with 10,000 stored analyses whose created-at values are pinned to span exactly **365 distinct UTC days**, the endpoint exercised end to end through the served ASGI app, the response time asserted below the budget. | `NFR1`; `BR3.6` |
| **NFR1.2** | `GET /v2/analytics/terms` answers in **under 200 ms** over the same 10,000-row / 365-day store, including the in-process term extraction and ranking. | The same `FR8.9` test, exercising the terms endpoint on the same fixture; the measurement is taken **without coverage instrumentation** (`BR3.6`), because `--cov` inflates wall time and would make the budget a measurement artefact. | `NFR1`; `BR3.6` |
| **NFR1.3** | The number of SQL statements executed is **independent of how many days the resolved range covers**: for a fixed store, the count does not grow as `from`/`to` widen the range, because the per-day series comes from one grouped read plus an in-process fill, not one query per day. | The `FR8.9` test's `sqlite3` trace hook: it counts statements for the same endpoint over two ranges of different span and asserts the count is **constant** in the number of days. This is the observable form of "no query per day". | `NFR1`; `BR3.4`; `FR8.9` |
| **NFR1.4** | The series length is bounded by the resolved range, not by the store: over the 10,000-row / 365-day fixture, an unbounded summary request returns exactly **365 entries** — one per UTC day in the pinned span — so the response's series work is proportional to the range and not to 10,000. | The `FR8.9` fixture combined with the series-extent assertions of `BR3.1`; the fixture's span is pinned to 365 distinct UTC days (see `NFR1.1`), so the unbounded series length is a fixed, stated quantity and the fill work is reproducible. The statement-count hook of `NFR1.3` proves the *work* is range-independent, and the series-shape test proves the *length* follows the resolved range. | `NFR1`; `NFR9`; `BR3.1` |

## Latency budget

- **Budget: 200 ms per request**, the single stated latency target, fixed by
  `NFR1` over a 10,000-row / 365-day store. It is an engineering-judgement figure
  (`requirements.md` A3), stated so it is testable, and measurement overrides it.
- **Components of the budget.** There is no per-hop latency budget to allocate:
  both endpoints are one process, one local SQLite read, no network call and no
  engine invocation (`BR2.8`). The whole 200 ms is the in-process read path —
  parameter-bound aggregate statements (`BR2.9`) plus in-process aggregation and
  term ranking.
- **No timeout to set.** The contract's request-timeout point (O11) was explicitly
  unspecified. This unit makes **no outbound call**, so there is no timeout value
  to set; recording that is the correct closure, not inventing a number. The
  only timeouts in the repository (`LIVE_TIMEOUT_SECONDS`, `EXCHANGE_TIMEOUT_SECONDS`)
  belong to the live sentiment and PKCE paths, which the analytics read path never
  touches.

## Concurrency posture (functionally-sourced constraint, carried for traceability)

**No inception NFR parent.** The concurrency constraint is **not** an `NFRx` target
and has no inception NFR parent. It originates in **functional** concerns —
`FR1.6` (the cross-thread connection defect is fixed by this feature), `BR6.3` (its
governing rule) and `FR8.4` (the reproducing concurrency test). It is recorded here
only because the *performance* file is where a reader looks for a concurrency
figure, and because it touches the same read path the latency budget measures. It is
carried for traceability, not sub-numbered onto `NFR1`; hanging a `NFRx.y` id on it
would invent a parent the inception set does not contain.

| Aspect | Statement | Measuring instrument | Sources (functional — no NFR parent) |
|---|---|---|---|
| **Concurrency constraint** | Two genuinely overlapping analytics requests against either endpoint complete without a cross-thread connection error and without serialising behind a per-request schema re-initialisation. There is no stated requests-per-second target: the store is a single-user local SQLite file (`NFR9`), so "throughput" here means bounded work per request, not RPS. | The `FR8.4` concurrency test on the replaced harness (`FR7.7`): two requests issued on genuinely different threads, both asserted to overlap, both to succeed; `BR6.3` requires the test to go red if the thread-affinity decision is reverted. | `FR1.6`; `BR6.3`; `FR8.4`; `BR6.4`; `FR7.7` |

## Resource constraints

- **No new resource dependency.** The read path runs on stdlib `sqlite3` and
  in-process Python only; no pool, no cache, no background worker, no external
  service (`BR2.8`, `C-5`, `C-6`).
- **Connection lifecycle is bounded.** One short-lived connection per request,
  owned at the HTTP edge (`BR6.1`); the read module never opens or closes one, so
  the analytics layer adds no connection-pool resource (`A2`, TD-5).
- **Coverage instrumentation is excluded from the measurement**, not from the
  suite: `BR3.6`/`FR8.9` require the timing taken without `--cov`, because the
  repository applies coverage on every run via `pyproject.toml` `addopts`.

## Benchmarks

The benchmark is the `FR8.9` fixture itself: **10,000 stored analyses pinned to span
exactly 365 distinct UTC days**, both endpoints exercised, each asserted under
200 ms, plus the statement-count trace hook proving the count is constant across
range spans. **The span is part of the target, not a construction detail**: because
the series length equals the days in the resolved range (`NFR9.1`/`NFR1.4`) and the
unbounded series is deliberately uncapped (`NFR9.3`), the in-process fill work the
budget measures is a direct function of that span. Pinning it to 365 days makes the
measured work a fixed, stated quantity, so a fixture concentrated in one week and a
fixture spread over years cannot silently yield different measurements. There is no
separate benchmark suite and none is required; the performance target and its
instrument are one test, assigned to this unit by `US8.1`.

## Derivation note

`NFR1` is the sole inception parent for this file's *targets*. It fixes two figures
(200 ms; range-independent statement count). This file sub-numbers them without
adding a third: `NFR1.4` restates the range-bounded series as a *performance*
consequence (it is the mechanism by which `NFR1.3` holds for the series). The
**concurrency posture** is recorded separately below the targets and is explicitly
**not** an `NFR1.y` target: it has no inception NFR parent and traces to functional
sources (`FR1.6`, `BR6.3`, `FR8.4`) — see "Concurrency posture" above. `NFR9`
(growth) is the parent of the scalability file; `NFR1.4` is its performance-side
mirror and is labelled as such rather than double-counted as a new scalability
claim.
