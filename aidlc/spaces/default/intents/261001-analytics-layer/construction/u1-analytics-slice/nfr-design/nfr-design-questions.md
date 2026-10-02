# NFR Design — `u1-analytics-slice`

> **No new questions.** This unit is a single-process localhost app with one SQLite
> file, no network boundary, no external service and exactly two declared runtime
> dependencies. Most of the resilience and scaling pattern catalogue the stage lists
> does not apply, and saying so is the honest design. This file records that
> assessment so the artifacts can be written without inventing mechanisms the
> system has no place for.

## Q1 — Which pattern families genuinely apply, and which do not?

| Stage's focus area | Applies here? | Why |
|---|---|---|
| Circuit breakers, retries with backoff | **No** | No outbound call exists in this unit; there is nothing to break a circuit to. The contract records the request timeout as deliberately unspecified for the same reason. |
| Bulkheads, failure domains, blast radius | **No** | One process, one file. There is no independent failure domain to isolate and no partial-failure surface to contain. |
| Horizontal scaling, load balancing, sharding, queues | **No** | `NFR9` bounds growth and the deployment is a single loopback process; the scaling story is "the work is bounded", not "add replicas". |
| Caching tiers, CDNs, lazy loading | **No** | The data is a local file read once per request; a cache would add invalidation risk for no measured gain. |
| Connection pooling | **Yes, and it is the R-01 fix** | The connection lifecycle and its thread affinity are the unit's one real reliability decision. |
| Health checks, graceful degradation | **Partially** | Startup already fails loudly on a bad configuration; the migration's rollback is the degradation story. |
| Input validation, parameter binding, secrets handling | **Yes** | `NFR2` and `C-11`; the rules already pin the behaviour. |
| Structured logging, SLI/SLO, alerting | **Partially** | One developer, one machine, no alerting channel. The logging rule applies; an alerting philosophy has nothing to route to. |
| Logical component boundaries | **Yes** | The unit's own internal boundaries: the read module, the migration, the route, and the connection owner. |

**The three real designs this stage produces:**

1. **The connection model** — how a connection is created, owned, closed, and made safe across the thread pool. This is the unit's central NFR design and the R-01 fix.
2. **The bounded-work model** — one grouped query rather than per-day work, in-process zero-fill, and the refusal shapes that keep an unavailable query distinguishable from an empty answer.
3. **The failure-visibility model** — what fails loudly (startup config, a migration that cannot preserve rows), what returns a distinguishable error, and what is logged.

A. Accept this assessment
B. Name a pattern family you want designed anyway
C. Other (please specify)

[Answer]: A. Accept.
