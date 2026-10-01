# Performance Design — `u1-application`

## Design solutions

| Requirement | Design solution |
|---|---|
| NFR-P1 | The offline path performs its scoring in memory and writes exactly one row. No pooling, caching or batching layer is introduced: at one user, a pool costs more than it saves. |
| NFR-P2 | The live call is made through an injected transport that carries the timeout, so the wait is bounded in one place and the caller's busy state is driven by the request's own lifecycle rather than a timer. |
| NFR-P3 | No design element exists for throughput: the unit runs one request at a time within one process, and the store's access is serialised by that process. |

## Shape of the design

Two code paths, one bounded: the offline result is synchronous and immediate; the live result is a
single outbound call whose duration is the provider's, bounded by the transport's timeout. Nothing in
the design scales horizontally, and nothing needs to.

## What would change at a higher load

Recorded to keep the design honest rather than as a plan: a shared deployment would need connection
handling for the store and a bounded worker count around the live call. Neither is v1.
