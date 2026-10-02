# Monitoring Design — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `infrastructure-design`
> (construction) · unit `u1-analytics-slice` (kind `service`).
>
> **Upstream inputs.** The accepted infrastructure-design assessment
> (`infrastructure-design-questions.md` Q1 option A), the NFR design
> `observability-design.md` (the full observability strategy this file implements
> at the platform level — §1 what exists and what does not, §2 the module-logger
> logging design, §3 SLIs as test-level indicators only, §5 patterns declared
> inapplicable), `reliability-design.md` §2 the failure-visibility model (the
> module-logger failure records and the distinguishable error shapes),
> `nfr-requirements/observability-requirements.md` (`NFR8.1`–`NFR8.3` and the
> "no monitoring stack" framing), the functional design (`rules.md` `BR4.5`,
> `BR4.6`; `functional-spec.md` Workflows 1–2), and the affirmed constraints in
> `memory/project.md` (`C-5`, `C-6`; the localhost-only mandate) and
> `memory/team.md` §Deployment.
>
> **This is a design artifact.** It states plainly that no monitoring tier is
> designed, why, and what stands in its place. It invents no monitoring stack.

## 1. No monitoring tier is designed — the decision, stated plainly

**This unit designs no monitoring tier of any kind: no metrics, no tracing, no
exporter, no collector, no dashboard, no alerting, no SLO, no log aggregation.**
That is the correct and complete design decision for this system, not an omission,
and this file records the reasons and the stand-in so a later reader does not
mistake the absence for missing coverage.

| Monitoring surface | Designed? | Reason |
|---|---|---|
| **Metrics endpoint / exporter / collector** | **No.** | `C-5`/`C-6` forbid introducing a new external service, hosted dependency or network call, and the repository already carries no metrics infrastructure (`observability-design.md` §1). The transitively pulled `opentelemetry-api` is non-imported by anything in `app/` and has no SDK or exporter installed (`A5`), so it is not an egress path. |
| **Distributed tracing** | **No.** | One process, one local store, and no network hop in the read path (`BR2.8`); there is no distributed boundary to trace. `observability-design.md` §1/§5 records this. |
| **Dashboards** | **No.** | The analytics view itself is the operator's picture; its loading/empty/error/partial states are a user-facing rendering, not a monitoring surface (`observability-design.md` §1). There is no second operations surface to build. |
| **Alerting / thresholds / escalation** | **No.** | A single-user localhost app has no pager, no alert channel and no on-call escalation. A failure is surfaced in-line to the one operator and in the local log; no threshold is invented (`observability-design.md` §1, §5). |
| **SLIs / SLOs (operational)** | **No.** | There is no hosted service, no multi-user load and no 30-day measurement window; an SLO is defined per critical user journey *for a service with an availability target*, and this system has none (`NFR9`, `observability-design.md` §1). The three SLIs in `observability-design.md` §3 are deliberately **test-level** indicators, not production metrics. |
| **Log aggregation / shipping / retention** | **No.** | There is no log sink, no formatter and no remote store. Logging goes through the process's module loggers to the process output only (`observability-design.md` §2.1). `BR2.15` forbids a new configuration value and the no-junk-drawer convention forbids a logging helper module, so no aggregation tier is added. |

## 2. Why no monitoring tier — the two reasons

**Reason 1 — it is forbidden by constraint.** `C-5` (and the project mandate
"NEVER introduce a new external service, hosted dependency, cloud component or
network call") rules out any hosted monitoring tier; `C-6` caps declared runtime
dependencies at exactly two (`fastapi`, `uvicorn`), so no in-process metrics or
tracing library may be declared either. A monitoring stack would be both a new
external service and a new dependency — doubly forbidden. This is recorded in
`observability-design.md` §1 and is unchanged at this stage.

**Reason 2 — the system has no monitoring subject.** It is a single-user localhost
application with no multi-user load, no availability target, no network boundary in
the read path, and no alerting channel. There is nothing to page, no availability
window to track, and no second operations surface to build. Adding a monitoring
stack would create a mechanism with no threat to observe and no operator to notify —
the same "no mechanism to exist here" reading the NFR design applies to caches,
pools, circuit breakers and replicas.

## 3. What stands in its place

Monitoring is replaced by the **failure-visibility design already recorded in NFR
Design**. The unit's observability obligation is narrow and precise: a failure
reaches the application log through the module logger, the envelope code and the
log agree, and no credential and no interpolated statement text appears in any log
record (`NFR8.1`–`NFR8.3`). This is not a monitoring tier; it is application
logging, and it is the whole of what applies.

### 3.1 The module-logger failure records (the stand-in for metrics/alerts)

Every analytics failure is logged through the **module's logger** as a record:
never swallowed, never `print()`ed (`NFR8.1`, `BR4.6`). The two failure classes
produce **distinguishable, structurally distinct** records and wire shapes, so the
one operator can tell them apart without a metric:

| Failure class | Wire shape | Log record | Source |
|---|---|---|---|
| Validation failure | `422` `VALIDATION_FAILED`; message names the field(s); nothing computed | Module-logger record for the refused request | `BR4.1`–`BR4.3`, `BR4.6` |
| Storage failure | `500` `STORAGE_FAILURE`, distinct from every validation code | Module-logger `exception(...)` record carrying the code and stack, **no parameter interpolated into statement text and no credential** | `BR4.5`, `NFR8.3`, `observability-design.md` §2 |
| Empty success | `200` with the endpoint's frozen empty shape | No failure record — it is a success, not an error | `BR4.4` |

The envelope **code** travels on the wire **and** appears in the application log,
so the wire surface and the log agree (`NFR8.2`): given a `STORAGE_FAILURE` on the
wire, the matching log record is the one the module logger wrote for that failure.
This is the correlation and provenance mechanism in place of a trace — there is no
boundary to propagate a correlation ID across (`observability-design.md` §4).

### 3.2 The distinguishable error shapes (the stand-in for alert thresholds)

The failure-visibility model itself is the observability surface: three
structurally distinct outcomes — **empty success**, **validation failure**,
**storage failure** — kept separate on the wire, in the log and in the view, so a
failure is never rendered as a plausible-looking empty result (`NFR4.3`). The
separation is the guarantee that stands where a threshold would: a reader does not
need a metric to know whether the endpoint failed, because the shape says so
unambiguously.

### 3.3 What is *not* a monitoring surface

- The **`sqlite3` trace hook** that counts statements (`FR8.9`) is a **test-only**
  instrument. It is not a production metric, is not exposed by any endpoint, and
  is not monitored (`observability-design.md` §3).
- The **SLIs** in `observability-design.md` §3 (correctness, latency, failure
  distinguishability) are **test-level** statements about what a test pins, not
  live numbers.
- The **analytics view's** loading/empty/error/partial states are a user-facing
  rendering, not a dashboard.

## 4. Metrics & KPIs, Alerts, SLIs/SLOs — all empty by decision

The stage's tabular monitoring sections are recorded here as deliberately empty,
so an absent table is not mistaken for an unfinished one.

| Section | Content |
|---|---|
| **Metrics & KPIs** | **Empty.** No metrics are collected, exported or stored; there is no metrics endpoint (`C-5`/`C-6`). |
| **Alerts** | **Empty.** No alert is defined, no threshold is set, no severity is assigned, no route exists — there is no alerting channel for a single-user localhost app. |
| **SLIs / SLOs** | **Empty (operational).** No SLI is measured at runtime and no SLO is stated; the test-level SLIs in `observability-design.md` §3 are noted there as non-operational. |
| **Logs & Tracing** | **Logging: module logger only**, to process output (§3.1). **Tracing: none** — one process, no network hop. **Log aggregation: none** — no sink, no formatter, no retention tier. |

## 5. Traceability

| NFR (this unit) | What this file records |
|---|---|
| `NFR8.1` | §3.1 — failures reach the application log through the module logger; never swallowed, never `print()`. |
| `NFR8.2` | §3.1 — the envelope code and the log agree; the code is the provenance shared by wire and log. |
| `NFR8.3` | §3.1 — no credential and no interpolated statement text in any log record. |
| `NFR8.*` infrastructure dimension | §1/§2 — no monitoring tier is provisioned; the absence is a decision under `C-5`/`C-6`. |

Full id-level enumeration is in `traceability.json`.
