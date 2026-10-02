# Logical Components — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-design` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Upstream inputs.** The NFR design set beside this file
> (`performance-design.md`, `security-design.md`, `scalability-design.md`,
> `reliability-design.md`, `observability-design.md`), the functional design
> (`entities.md`, `rules.md` `BR6.x`/`BR4.x`/`BR2.x`, `functional-spec.md`), the
> contracts (`contract-summary.md` §2 C1, §2.2 storage surface), the component
> catalogue and ADRs (`components.md` `AnalyticsRead`, `HTTP API Surface`,
> `Persistence and Schema`, `Application Assembly`, `TermExtraction`;
> `decisions.md` ADR-003, ADR-004, ADR-006, ADR-008), the NFR requirements
> (`reliability-requirements.md` §Availability; `scalability-requirements.md`),
> and the CodeKB (`architecture.md` A2, D3, §Extension Seams, §Boundary
> Discipline; `code-quality-assessment.md` TD-1, TD-5).
>
> **This is a design artifact.** It draws the unit's *internal* logical
> boundaries, its failure domains and the shared resources they contend on. It is
> not a deployment diagram and does not choose topology (a deployment decision
> made in Units Generation: one loopback process, one SQLite file).

## What this file is, and what it is not

`components.md` (inception) catalogues the building blocks the feature adds and
touches across the whole system. This file narrows the lens to **this unit's own
internal seams** — the sub-boundaries inside `u1-analytics-slice`'s remit — so
Infra Design and Code Generation see where the NFR patterns above actually apply.
Because the unit is a single loopback process over one file, the honest framing
is: **one failure domain, a handful of internal logical boundaries, and exactly
two shared resources.**

## 1. The unit's internal logical boundaries

The unit's remit spans four code-level concerns. Three already exist in the
codebase; one is the new read module. Each boundary is a *responsibility* seam,
not a deployable or an independent failure domain.

| # | Logical boundary | Kind | Owns | Does **not** own | NFR pattern applied |
|---|---|---|---|---|---|
| **LC-1** | **The read module** (`AnalyticsRead`) | New, in-unit | All aggregate SQL; range resolution; zero-fill; share/mean computation; term ranking; terminal refusal shapes. | Its own connection (it receives one); any write; any entity persistence. | Bounded-work model (`performance-design.md` §2; `scalability-design.md` §2); read-only guarantee (`reliability-design.md` §1). |
| **LC-2** | **The connection owner** (at the HTTP edge) | Existing boundary, changed | Creation, configuration, hand-over and close of the per-request connection; the explicit thread-affinity decision; its own documentation. | Any aggregate SQL; any read logic. | The connection model (`reliability-design.md` §3); loopback enforcement lives in a sibling startup boundary (§1 LC-4). |
| **LC-3** | **The route / HTTP edge** | Existing boundary, grows | The `/v2` router, the two handlers, request validation, the range-check ordering, the error envelope, the `STORAGE_FAILURE` mapping. | Statement text; query helpers (`BR2.10` — the route holds no statement); the service layer is not inserted into the read path (ADR-008). | Failure-visibility model (`reliability-design.md` §2); the frozen envelope (`security-design.md` §3.3). |
| **LC-4** | **Startup / migration boundary** | Existing boundary, changed | The v3 → v4 additive migration, the three named indexes and the TD-1 index-survival fix, the same-transaction version bump, loud rollback; the loopback bind enforcement at startup. | Any request-time work. | Migration atomicity (`reliability-design.md` §4); loopback hardening (`security-design.md` §4). |
| **LC-5** | **The summary region of the view** | In-unit slice (detailed spec owned by `u3-analytics-view`) | The series and label-breakdown containers, one fetch per endpoint, `null`-share rendering as a no-share marker. | The full view's component specification (carried by `u3`); browser-execution testing (structurally absent, TD-11). | Per-section degradation (`reliability-design.md` §2.5); the view renders only returned values. |

**Ownership is singular at every seam.** LC-1 never opens a connection (LC-2
owns it); LC-3 never holds SQL (LC-1 owns it); LC-4 runs only at startup (LC-3
serves requests). This is the "least coupling, highest cohesion" principle made
concrete: the boundaries are drawn so that the R-01 fix lives entirely in LC-2
and the bounded-work guarantee lives entirely in LC-1.

## 2. Failure domains and blast radius

**There is exactly one failure domain.** The unit is a single loopback process
over one local file; there is no independent failure domain to isolate and no
partial-failure surface to contain (accepted assessment). The blast-radius
mapping is therefore at the **request** level, not the service level.

| Failure | Reaches | Blast radius | Recovery |
|---|---|---|---|
| A malformed parameter | LC-3, before computation | **This request only**; nothing is read, nothing is written. | Caller fixes the request; no state to unwind. |
| A storage read raises | LC-3 catches, maps to `500 STORAGE_FAILURE` | **This request only**; the envelope carries the code, the module logger records it. | Retry is the caller's choice (no silent retry, `NFR4.7`). |
| A cross-thread connection error (the pre-fix defect) | LC-2 | **This request only**, but it was *not* distinguishable from other 500s before the fix; the fix removes it. | Fixed by the thread-affinity decision (`reliability-design.md` §3). |
| The migration cannot preserve every row | LC-4, at startup | **The whole process** — startup halts loudly rather than serving on a half-migrated store. | Operator restores/recreates the local file; the loud failure is the correct outcome. |
| A non-loopback host is supplied | LC-4, at startup | **The whole process** — fails loudly rather than exposing an unauthenticated app. | Operator supplies a loopback host. |

The design **does not** draw bulkheads around LC-1…LC-5: they are responsibilities
in one process, and a "bulkhead" between functions in one process would be a
mechanism with no independent failure to contain. The one place the design does
contain blast radius is the startup boundary (LC-4), where failure is correctly
fatal rather than partial.

## 3. Shared resources

Exactly **two** resources are shared across the unit's boundaries. Naming them is
what keeps the coupling honest.

| Shared resource | Shared by | Contention model | Design decision |
|---|---|---|---|
| **The SQLite file** (one per deployment) | LC-1 (reads), LC-2 (opens/closes), LC-4 (migrates at startup) | Single-user, single-writer-at-startup; request-time reads are concurrent | The file is owned by `Persistence and Schema` (not this unit); this unit reads it and the migration writes it once at startup. Access goes through one short-lived connection per request (`reliability-design.md` §3). No pool, no cache, no second writer. |
| **The per-request `sqlite3.Connection`** | LC-2 (owns), LC-1 (borrows via parameter), LC-3 (hands over) | One connection per request; not shared between concurrent requests | Ownership is single (LC-2); the read module receives it (`BR6.1`) and never closes it. This is the R-01 seam. |

**No other resource is shared.** There is no cache to invalidate, no queue to
drain, no pool to exhaust, no in-memory mutable state added by this unit (the only
process-wide mutable state remains `app.state.session_auth`, untouched). The
design does not add a semaphore, a lock or a connection guard, because the
contention model — one connection per request, one read each — has none to
manage.

## 4. Component isolation strategy

The design's isolation strategy is **boundary discipline**, not runtime
isolation, because runtime isolation has no mechanism to exist here.

| Isolation | Mechanism | Effect |
|---|---|---|
| Layering | The read path is a strictly descending chain: route (LC-3) → read module (LC-1); the service layer is not inserted (ADR-008). | The read path cannot accidentally acquire write concerns. |
| Connection ownership | Single-site ownership at LC-2 (`BR6.1`, ADR-006). | Connection lifecycle cannot spread; the R-01 fix is local to one function. |
| Statement placement | All aggregates in LC-1; the route holds no statement (`BR2.10`). | SQL cannot leak into the HTTP edge. |
| Module conventions | One responsibility per module, typed, no junk-drawer, no new config (`BR2.15`). | Each boundary stays independently readable and testable. |
| Machine-checked boundaries | `ruff TID251` banned-api entries turn a boundary breach into a lint failure (affirmed practice). | The boundaries above are enforced by a gate, not only by review. |

## 5. Patterns declared inapplicable, with stated reasons

| Pattern family | Applies? | Why not |
|---|---|---|
| **Independent failure domains / bulkheads between components** | **No.** | One process, one file; the logical boundaries are responsibilities, not independently-failing services. |
| **Service isolation / process isolation** | **No.** | Single process by design (`NFR9`, `team.md` §Deployment). |
| **Shared-resource pooling** | **No.** | Two shared resources, one connection per request, no pool (A2). |
| **Circuit-breaker / retry isolation** | **No.** | No outbound call; nothing to isolate. |

## 6. Traceability

This file is the component-level view of where the NFR patterns apply. Each
`NFRx.y` mapping is enumerated in `traceability.json`; the boundary-to-NFR index
is:

| Boundary | NFRs it carries |
|---|---|
| LC-1 read module | `NFR1.1`–`NFR1.4`, `NFR3.1`, `NFR3.2`, `NFR4.4`, `NFR9.1`–`NFR9.4`, part of `NFR4.3` |
| LC-2 connection owner | Concurrency posture (functional), part of `NFR4.2` |
| LC-3 route / HTTP edge | `NFR2.1`, `NFR2.3`, `NFR4.1`–`NFR4.3`, `NFR4.7`, `NFR8.1`–`NFR8.3`, part of `NFR2.2` |
| LC-4 startup / migration | `NFR2.4`, `NFR2.5`, `NFR4.5` |
| LC-5 view region | `NFR4.6`, part of `NFR4.3` |
| Whole unit | `NFR2.2`, `NFR2.5`, `NFR2.6` (unit-wide invariants) |
