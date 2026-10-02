# Reliability Design — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-design` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Upstream inputs.** `nfr-requirements/reliability-requirements.md` (`NFR3.1`,
> `NFR3.2` read-only; `NFR4.1`–`NFR4.7` distinguishable failures; the
> functionally-sourced concurrency constraint, no NFR parent),
> `nfr-requirements/performance-requirements.md` §Concurrency posture,
> `nfr-requirements/observability-requirements.md` (`NFR8.1`/`NFR8.2` — the
> log-side half), the functional design (`rules.md` `BR2.7`, `BR4.1`–`BR4.6`,
> `BR5.1`–`BR5.6`, `BR6.1`–`BR6.6`; `functional-spec.md` Workflows 1–4 and the
> migration state machine), the contracts (`contract-summary.md` §2 C1 the frozen
> envelope and `STORAGE_FAILURE`; §2.2 the storage surface), the component
> catalogue and ADRs (`components.md` `HTTP API Surface`,
> `Persistence and Schema`; `decisions.md` ADR-004, ADR-006), and the CodeKB
> (`architecture.md` A2, D2, §Data Flow; `code-quality-assessment.md` TD-1, TD-5).
> Accepted assessment: `nfr-design-questions.md` Q1 option A.
>
> **This is a design artifact.** No implementation code; short interface-level
> pseudocode only.

## Reliability posture in one paragraph

The unit's reliability contribution is a pair: **a read that cannot mutate its
store**, and **failures that are distinguishable rather than substituted**. Its
availability target is simply "the process is up"; there is no SLA, no replica,
no failover and no HA, and the design adds none (`team.md` §Deployment). The one
genuine lifecycle in the unit is the **startup migration** (a store moves between
schema versions, committing whole or rolling back), and the one genuine
concurrency decision is the **connection model** (§3) — the R-01 fix.

## 1. Read-only guarantee (`NFR3`)

**Design decision: the read path performs no write, no schema change and no
access bookkeeping.**

- Both endpoints are `GET` and mutate nothing; reading analytics never changes
  the store it reads, and no timestamp or last-read state is recorded
  (`BR2.7`).
- The read path issues **no mutating operation of any kind**: no
  `INSERT`/`UPDATE`/`DELETE`, no DDL, no state-changing `PRAGMA` (`BR2.10` places
  every aggregate in the read module).
- The connection the read module receives is used for `SELECT`s only; the module
  never opens, closes or owns a connection (`BR6.1`).

This is a design decision with a measurable instrument rather than a convention:
the before/after test asserts row count, schema and content hash unchanged across
any number of analytics requests, and the `sqlite3` trace hook can assert the
statement set contains no mutating form.

## 2. The failure-visibility model (distinguishable, never substituted)

**Design decision: three failure/outcome classes, structurally distinct on the
wire, in the log, and in the view.**

### 2.1 What fails loudly (at startup)

| Condition | Behaviour | Source |
|---|---|---|
| A non-loopback host is supplied | Startup fails loudly with an explanation; the loopback run path is unchanged. | `BR6.5`, `FR7.6` |
| The migration cannot preserve every row, or the store shape is unreadable | The transaction **rolls back and re-raises**; startup halts loudly rather than serving on a half-migrated store. | `BR5.5`, `FR5.6`/`FR5.7` |
| A bad configuration value is encountered during startup | Startup fails loudly (existing behaviour, unchanged). | `architecture.md` §Startup |

The design principle: **a startup that cannot guarantee the store's integrity must
not serve.** The migration's `BEGIN`/`try`/`rollback()`/`raise`/`commit()` block is
the one deliberate broad handler in the codebase, and it is rollback-and-re-raise
— not a swallow.

### 2.2 What returns a distinguishable error

| Class | Status + code | When | Not to be confused with |
|---|---|---|---|
| Validation failure | `422` `VALIDATION_FAILED` | Malformed `from`/`to`/`limit`, or an inverted range; **nothing computed**; message names the field(s). | An empty success |
| Storage failure | `500` `STORAGE_FAILURE` | A `sqlite3` error raised while reading; **distinct from every validation code**. | A malformed parameter |
| Empty success | `200` with the endpoint's frozen empty shape | The range matched no rows. | Neither of the above — it is a success |

The design keeps **empty ≠ failure** and **storage ≠ validation** as hard,
separate shapes (`BR4.4`, `BR4.5`). A `422` and a `500` are visibly different from
an empty result on the wire and in the view (`NFR4.3`). The refusal is discriminated
by **machine code**, not by message text, so a client can branch deterministically.

### 2.3 Refuse-never-substitute — every null is deliberate

| Situation | Correct answer | Never |
|---|---|---|
| Share with denominator 0 | `null` | A fabricated `0.0` |
| Mean with no inputs | `null` (with `row_count` 0 = the denominator) | A fabricated `0.0` |
| Label with no rows | Empty array `[]` | `null`, or a padded list |
| No-match range | Empty series `[]` + `total` 0 | A zero-filled span, or `404` |

This is the same precedent as the in-repo `ImportSummary.mean_confidence` (A3),
extended to every analytics aggregate (`BR2.2`–`BR2.4`, `BR4.4`). The design
states the rule once here; the "refuse, never substitute" idiom is an affirmed
convention, not a per-field choice.

### 2.4 What reaches the log

Every application-raised failure is logged through the **module logger** — never
swallowed, never `print()`ed (`NFR8.1`, `BR4.6`). A failure with a machine code
travels on the envelope **and** appears in the log, so the wire surface and the
log agree (`NFR8.2`). The log record carries no credential and no interpolated
statement text (`NFR8.3`). Full log-side design is in `observability-design.md`
§2; this file owns the *classification* of what fails, that file owns the
*logging* of it.

### 2.5 Graceful degradation is per-section

A failed analytics section renders an in-place failure; a section that succeeds
while another fails shows the successful section plus a distinct partial-failure
marker, so the two never silently disagree about the range (`NFR4.6`). There is
**no silent retry** (`NFR4.7`): the client surfaces a failure rather than
auto-retrying, because a silent retry would make a stale range look current, and
an out-of-order late response from a superseded range is discarded. (The markup
behaviour is `u3-analytics-view`'s; the rule participates in this unit's summary
region.)

## 3. The connection model (the unit's central design — the R-01 fix)

**This is the design the unit exists to get right.** `get_connection`
(`app/routes.py`) is the only place the `sqlite3` driver and the connection
lifecycle are touched anywhere in the codebase (ADR-006); every current and
future endpoint inherits whatever it does. Today it opens a connection in one
anyio worker thread and closes it in another, so genuinely overlapping requests
raise `sqlite3.ProgrammingError` and answer `500` — the accepted R-01 defect
(TD-5).

### 3.1 The thread-affinity decision (stated explicitly)

**Decision: open the connection with thread-affinity disabled — i.e. the
connection is created with `check_same_thread=False` — so a connection created in
one worker thread may be used and closed from another, and the design owns the
safety that `sqlite3`'s default would otherwise provide.**

The choice itself is a design decision, so its justification is explicit:

| Consideration | Reading | Consequence for the decision |
|---|---|---|
| What the default does | `sqlite3.connect` defaults to `check_same_thread=True`; using the connection from a thread other than its creator raises `ProgrammingError`. That default exists to catch genuinely unsafe cross-thread use of one connection. | The default is *safe* but not *sufficient* here, because FastAPI's synchronous dependency runs on a worker thread and the handler may run on another. |
| What the defect actually is | The connection is created per request but its creation and its use are not guaranteed to be on the same thread, so the default trips. | The fix is to make the affinity explicit, not to inherit either default. |
| Why `check_same_thread=False` is safe **here** | The connection is **short-lived and request-scoped**: it is opened at the HTTP edge for one request and closed at the end of that request. It is never shared concurrently between live requests — each request gets its own connection. | With one connection per request and no concurrent sharing of a single connection, disabling the same-thread guard removes a false positive without removing real protection. |
| Why not "pin the request to one thread" | Pinning would require restructuring how FastAPI dispatches the sync dependency and the handler, i.e. a broader change with no offsetting benefit; and it would still leave the lifecycle implicit. | Rejected in favour of the minimal, explicit, well-documented affinity decision. See Alternatives below. |

**The open/use/close model this decision implies**, stated so no later reader
infers a default:

```text
get_connection():                       # HTTP edge, per request
    conn = sqlite3.connect(path, check_same_thread=False)   # explicit affinity
    conn.row_factory = sqlite3.Row      # unchanged from today
    try:
        yield conn                       # handed to the route / read module
    finally:
        conn.close()                     # closed at the request boundary
```

The read module **receives** this connection and never opens, closes or owns one
(`BR6.1`); the lifecycle stays wholly at the HTTP edge (ADR-006 — no boundary
moves, connection lifecycle does not relocate to `Persistence and Schema`).

### 3.2 Where ownership sits

| Owner | Responsibility | Why |
|---|---|---|
| `HTTP API Surface` (the `get_connection` module) | Creates, configures, hands over and closes the connection; states the thread-affinity and lifecycle decision in its own docstring. | It is the only place the driver and lifecycle are touched (ADR-006); the fix lands with the defect. |
| `AnalyticsRead` (the read module) | Receives the connection as a parameter; issues parameter-bound `SELECT`s; owns no lifecycle. | Keeps connection ownership from spreading (`BR6.1`). |
| `Application Assembly` | Runs `init_db` once at startup; enforces loopback. | Startup concern, not a per-request concern. |

### 3.3 The module-documentation obligation

The chosen thread-affinity decision and the connection lifecycle must be stated
**explicitly in the connection-owning module's own documentation** (`BR6.2`),
rather than left for a later reader to infer. This is a design output of this
stage: the reason R-01 was accepted for so long is that the affinity was
implicit; the fix is only complete when the decision is written where the next
reader looks.

### 3.4 How the fix is proved

| Aspect | Instrument |
|---|---|
| Two genuinely overlapping requests raise no cross-thread error | The `FR8.4` concurrency test on the **replaced** harness (`FR7.7`): two requests on genuinely different threads, both asserted to overlap and both to succeed. |
| Reverting the decision makes the test fail | `BR6.3` requires the test to go **red** if the thread-affinity decision is reverted — the test must prove the decision, not merely pass. |
| Schema initialisation is not in the request path | The harness hoists `init_db` out of the per-request path (`BR6.4`), so a red test is red for the *connection* reason, not a "database is locked" reason. |

### 3.5 Alternatives rejected

- **Pin each request to a single thread** (restructure dispatch so the connection
  is created, used and closed on one thread). Rejected: it is a broader change
  than the defect requires, it still leaves the affinity implicit, and it would
  move FastAPI's dispatch shape for a fix that a one-argument, documented
  decision closes.
- **Move connection lifecycle to `Persistence and Schema`** (ADR-006 alternative
  rejected at Domain Design). Rejected: it would move an existing boundary for a
  fix that does not require the move, and put connection ownership in two places
  during the transition. The defect is in the caller, not the driver library.

## 4. The migration's atomicity (the one genuine lifecycle)

**Design decision: the v3 → v4 step commits whole or rolls back whole.**

- Additive only: no column dropped, renamed or retyped; no row discarded or
  rewritten (`BR5.1`).
- Idempotent: a store already at v4 changes nothing (`BR5.2`). Because the
  harness re-enters the lifespan on every in-process request, idempotency is
  exercised on every request — a free, continuous instrument.
- The three indexes are created by name and re-created explicitly after the
  rebuild path (`BR5.3`, `BR5.4`), fixing TD-1 (the rebuild silently dropped every
  index).
- The version bump to 4 lands in the **same transaction** as the step (`BR5.5`).
- Any step that cannot preserve every row rolls back and re-raises, so startup
  halts loudly (`BR5.5`).

This is the reliability design for the *schema*, and it is the unit's only real
state-machine (`functional-spec.md` §State machine — the migration). The request
workflows above are deliberately not lifecycles and are not drawn as state
machines.

## 5. Patterns declared inapplicable, with stated reasons

| Pattern family | Applies? | Why not |
|---|---|---|
| **Circuit breakers, retries with backoff** | **No.** | There is no outbound call in this unit; there is nothing to break a circuit to, and the contract records the request timeout as deliberately unspecified for the same reason (`contract-summary.md` O11). |
| **Bulkheads / independent failure domains / blast radius** | **No.** | One process, one file; there is no independent failure domain to isolate and no partial-failure surface to contain. |
| **Failover / replication / HA** | **No.** | No SLA, no replica, no failover; deleting or restoring the local file is the accepted recovery (`team.md` §Deployment). The design adds no availability mechanism. |
| **Backup strategy / point-in-time recovery** | **No (repository-level, absent by decision).** | There is no deployment and no migration tool; recovery is stop → delete/restore the local file → check out the previous commit. Recorded, not invented as a mechanism. |
| **Health checks** | **No new one.** | The existing `/v1/health` already reports the resolved mode; the analytics unit adds no health endpoint and no readiness probe. |
| **Graceful degradation of the *service*** | **Partially — per-section only.** | The degradation story that exists is per-section rendering (`NFR4.6`) and the migration's rollback (§4); there is no service-level degradation because there is no downstream dependency to degrade against. |

## 6. Traceability

| NFR (this unit) | Design solution (this file) |
|---|---|
| `NFR3.1` | §1 — read-only; no write, no schema change, no bookkeeping. |
| `NFR3.2` | §1 — no mutating statement; trace hook + before/after comparison. |
| `NFR4.1` | §2.2 — `422` naming its field; inverted range names both; nothing computed. |
| `NFR4.2` | §2.2 — `500 STORAGE_FAILURE`, distinct from every validation code. |
| `NFR4.3` | §2.1/§2.2 — a failure never renders as a plausible empty result. |
| `NFR4.4` | §2.3 — refuse-never-substitute for every null. |
| `NFR4.5` | §4 — idempotent, row-preserving additive migration; loud rollback. |
| `NFR4.6` | §2.5 — per-section graceful degradation. |
| `NFR4.7` | §2.5 — no silent retry; out-of-order discard. |
| Concurrency posture (functional, no NFR parent) | §3 — connection model; thread-affinity decision; `check_same_thread=False` with per-request ownership. |

Full id-level enumeration is in `traceability.json`.


## 9. Review follow-up — where the fix actually lands, and the invariant that makes it safe

**Review R-02, corrected.** The pseudocode above shows the flag at `get_connection`.
In the shipped code `get_connection` delegates to the module that owns the driver,
and that module is the **only** `sqlite3.connect` site. The design therefore names
the **driver-owning module** as the place the flag is set, and `get_connection` as
the place the connection is handed to a request. Two locations, one fix; naming only
the HTTP-edge function would have left Code Generation guessing which one to edit.

**Review R-01, recorded as a binding invariant.** Disabling the same-thread guard is
safe **only because** the connection is request-scoped. That invariant is now stated
as a constraint rather than left implicit:

- Exactly one connection is created per request and it is closed in that request's
  `finally`.
- No connection is ever cached, pooled, stored on a module global, or shared
  between two concurrent requests.
- If a future change introduces pooling or a shared connection, the same-thread
  guard must be re-enabled or the sharing must be made thread-safe — the flag is
  not a general licence to share a connection across threads.

The design closes R-01 **conditionally, on this invariant**. It is now written down
where a later reader will find it, which is what the review asked for.
