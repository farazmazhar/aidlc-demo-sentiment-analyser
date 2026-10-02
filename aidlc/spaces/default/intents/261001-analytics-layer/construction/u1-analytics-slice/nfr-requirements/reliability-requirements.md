# Reliability Requirements — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-requirements` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Source of truth.** Derives from inception `NFR3` (read-only) and `NFR4`
> (distinguishable failures, refuse-never-substitute). Each requirement carries its
> parent id plus a sub-number and a **measuring instrument**. The file also carries
> one **functionally-sourced constraint** (the cross-thread concurrency posture),
> recorded separately with its real source ids (`FR1.6`, `BR6.3`, `FR8.4`) and **no
> inception NFR parent** — it is not sub-numbered onto `NFR4`.

## Read-only guarantee (`NFR3`)

| ID | Requirement | Measuring instrument | Source |
|---|---|---|---|
| **NFR3.1** | Both endpoints are `GET` and perform **no write, no schema change and no access bookkeeping**. Reading analytics never mutates the store it reads; no timestamp or last-read state is recorded. | The read-only test paired with the store's before/after comparison: row count, schema and content hash are asserted unchanged across any number of analytics requests, and no bookkeeping table/row is written. `BR2.7` pins exactly this observable. | `NFR3`; `BR2.7`; `FR2.13` |
| **NFR3.2** | The read path issues **no mutating operation of any kind**: no `INSERT`/`UPDATE`/`DELETE`, no DDL, no `PRAGMA` that changes state. | Code inspection of the read module (`BR2.10` places every aggregate there) plus the `sqlite3` trace hook used by `FR8.9`, which can assert the statement set contains no mutating form; the read-only before/after test of `NFR3.1` is the end-to-end instrument. | `NFR3`; `BR2.7`; `BR2.10` |

## Distinguishable failures (`NFR4`)

| ID | Requirement | Measuring instrument | Source |
|---|---|---|---|
| **NFR4.1** | A malformed parameter produces a **`422` naming its own field** in the message text (`query.from`, `query.to` or `query.limit`), and **computes nothing**. An inverted range is refused rather than silently emptied; its one refusal names **both** `query.from` and `query.to`. No parameter is silently defaulted or clamped. | The `FR8.2` refusal-shape tests: one per `422` in `FR2.11`/`FR3.4`, asserting status, the `{code, message}` envelope, the field name **inside the message**, and that nothing was computed. `BR4.1`/`BR4.2`/`BR4.3` pin the shapes. | `NFR4`; `BR4.1`–`BR4.3`; `FR8.2` |
| **NFR4.2** | A **storage failure is a `500` carrying a machine code distinct from every validation code** — fixed as `STORAGE_FAILURE` at Contract Design. An unavailable query is never mistaken for a malformed parameter. | The `FR8.2`/`US8.5.2` test: a storage read is made to raise, and the response is asserted to be `500` with code `STORAGE_FAILURE`, and asserted distinct from every validation code. `BR4.5` pins the mechanism. | `NFR4`; `BR4.5`; `contract-summary.md` §2 |
| **NFR4.3** | A **failed request never renders as a plausible-looking empty result.** A `422` and a `500` are visibly different from an empty result, on the wire and in the view. | The `FR6.7` view test plus the endpoint response tests: an empty range is `200` with each endpoint's frozen empty shape; a failure is the envelope with its code. The three cases (empty success, validation failure, storage failure) are asserted to render distinctly. | `NFR4`; `BR4.4`; `FR6.7`; `contract-summary.md` C2 |
| **NFR4.4** | The **refuse-never-substitute convention governs every null**: a share is `null` when its denominator is `0`, never a fabricated `0.0`; a mean with no inputs is `null`, never `0.0`; a label with no rows yields an empty list, never `null` and never a padded list. | The `FR8.2` hand-pinned aggregate tests, including the zero-denominator `shares: null` case (Revision 2's added criterion) and the empty-label empty-array case; `BR2.2`, `BR2.3`, `BR2.4`, `BR4.4` pin each null. | `NFR4`; `BR2.2`–`BR2.4`; `BR4.4`; `FR8.2` (Revision 2) |

## Data integrity and graceful degradation

| ID | Requirement | Measuring instrument | Source |
|---|---|---|---|
| **NFR4.5** | The additive migration that this unit's reads stand on is **idempotent and preserves every row**: it never completes partially, and a store it cannot read fails loudly and rolls back rather than serving on a half-migrated file. | The migration tests of `BR5.2`/`BR5.5`: running `init_db` against an already-`v4` store changes nothing (the harness re-enters the lifespan on every in-process request, so idempotency is exercised on every request); the three named indexes are asserted by name (`BR5.3`), and a failing step is asserted to roll back and re-raise. | `FR5.1`–`FR5.7` (migration integrity — functional source); `BR5.1`–`BR5.6`; `FR5.6`, `FR8.3` |
| **NFR4.6** | **Graceful degradation is per-section, not all-or-nothing.** A failed analytics section renders an in-place failure; a section that succeeds while another fails shows the successful section plus a partial-failure marker, so the two never silently disagree about the range. | The `FR6.7` / `AC6.5.3`/`AC6.5.5` view tests: one section made to fail while the other succeeds, asserting the succeeded section plus a distinct partial-failure status; the failed section keeps its heading and an in-place marker. Loading, empty and error stay distinct regions. | `NFR4`; `FR6.7`; `contract-summary.md` C2 |
| **NFR4.7** | **No silent retry.** The client surfaces a failure rather than auto-retrying, because a silent retry would make a stale range look current; an out-of-order late response from a superseded range is discarded rather than allowed to overwrite current data. | The `AC6.5.2` out-of-order test: two in-flight requests for one range change completing out of order, asserting only the newest range's responses render. No retry is issued by the render path. (The markup behaviour is `u3-analytics-view`'s; the rule participates in this unit's summary region.) | `NFR4`; `contract-summary.md` C2; `FR6.4` |

## Availability

The availability target is **the process being up**, and recovery is local: there
is no SLA, no replica, no failover and no HA — deleting the local file is the
accepted recovery (`team.md` §Deployment; `technology-stack.md` §Database records
backup/replication/HA as "None"). This unit adds no availability mechanism and
must not invent one. Its reliability contribution is the pair above: a read that
cannot mutate its store, and failures that are distinguishable rather than
substituted.

## Concurrency — a functionally-sourced constraint carried for traceability

**Not an `NFRx` target; no inception NFR parent.** The cross-thread connection
constraint is a *failure-behaviour* concern, but the inception set has no NFR that
owns it: it originates in **functional** requirements — `FR1.6` (the cross-thread
connection defect R-01 is fixed by this feature), `BR6.3` (its governing rule) and
`FR8.4` (the reproducing test). It is recorded here rather than as an `NFR4.y` row
so that it is not falsely hung off `NFR4` (which owns failure *shapes* and
refuse-never-substitute). It is carried for traceability only, with its real source
ids named; the owning file for the target-level statement is
`performance-requirements.md` § "Concurrency posture", where a reader looks for it.

| Aspect | Statement | Measuring instrument | Sources (functional — no NFR parent) |
|---|---|---|---|
| **Cross-thread concurrency** | Two genuinely overlapping requests against either endpoint raise **no cross-thread connection error** and do not serialise behind a per-request schema re-initialisation — a failure mode, which is why it is recorded beside the reliability pair. | The `FR8.4` concurrency test on the replaced harness (`FR7.7`): two requests on genuinely different threads, both asserted to overlap and both to succeed; `BR6.3` requires the test to go red if the thread-affinity decision is reverted. | `FR1.6`; `BR6.3`; `FR8.4`; `BR6.4`; `FR7.7` |
