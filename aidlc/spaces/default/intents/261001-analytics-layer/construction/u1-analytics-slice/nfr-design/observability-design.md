# Observability Design — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-design` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Upstream inputs.** `nfr-requirements/observability-requirements.md` (`NFR8.1`–`NFR8.3`
> and the SLI table; the "no monitoring stack" framing), the functional design
> (`rules.md` `BR4.5`, `BR4.6`, `BR2.9`; `functional-spec.md` Workflows 1–2),
> the contracts (`contract-summary.md` §2 C1 — the envelope carries the code, the
> view keeps the code off-screen), the component catalogue (`components.md`
> `HTTP API Surface`; `decisions.md` ADR-003), the CodeKB
> (`architecture.md` §Layering — one envelope builder, module loggers;
> `code-quality-assessment.md` §Documentation — all 12 modules carry a
> `Single responsibility:` line), and the affirmed rules in
> `memory/team.md` §Code Style and §Deployment. Accepted assessment:
> `nfr-design-questions.md` Q1 option A.
>
> **This is a design artifact.**

## Observability posture in one paragraph

The repository has **no metrics, tracing, exporter or dashboard infrastructure**,
and `C-5`/`C-6` forbid adding one. So this design states what exists (structured
logging through module loggers) and records the **absences honestly** rather than
inventing a monitoring system. The unit's observability obligation is narrow and
precise: **a failure reaches the application log through the module logger, the
envelope code and the log agree, and no credential and no interpolated statement
text appears in any log record.**

## 1. What exists and what does not

| Surface | Design | Why |
|---|---|---|
| **Logging** | Module logger only; a failure is logged as a record, never swallowed and never `print()`ed. | `NFR8.1`, `BR4.6`; `print()` does not appear in `app/` (affirmed convention). |
| **Metrics endpoint / exporter / collector** | **None.** | `C-5`/`C-6` forbid adding one; the transitively pulled `opentelemetry-api` is non-imported (`A5`). Recorded so its absence is not mistaken for coverage. |
| **Distributed tracing** | **Not applicable.** | One process, one local store, no network hop in the read path (`BR2.8`); there is no distributed boundary to trace. |
| **Alerting / thresholds** | **None.** | A single-user local app has no pager and no alert channel; a failure is surfaced in-line to the one operator and in the local log. No threshold is invented. |
| **Dashboards** | **None.** | The analytics view itself is the operator's picture; the view's loading/empty/error/partial states are a user-facing rendering, not monitoring. |
| **SLO** | **None stated.** | No hosted service, no multi-user load, no 30-day window; an SLO is defined per critical user journey *for a service with an availability target* and this system has none (`NFR9`). Recorded as a deliberate absence. |

## 2. Structured logging design

**Design decision: one logging obligation, shared with security.**

- Every analytics failure is logged through the **module's logger** as a record
  (`NFR8.1`, `BR4.6`). No analytics failure is swallowed, and none is `print()`ed.
- The envelope **code** (`VALIDATION_FAILED`, `STORAGE_FAILURE`) appears in the
  response **and** in the application log, so the wire surface and the log agree
  (`NFR8.2`). The view's render path never shows the machine code on screen
  (contract C2); the code stays in the server log.
- **No request parameter is interpolated into statement text, and no credential
  appears in any log record** (`NFR8.3`). This is the same rule as `BR2.9`
  (parameter binding) seen from the log side: a value reaches a statement only as
  a bound parameter, and a log record carries no credential and no interpolated
  statement text.

```text
except StorageError as exc:
    logger.exception("analytics summary read failed")   # code + stack, no params
    return error_response(500, "STORAGE_FAILURE", "analytics read failed")
```

The design keeps the **classification** of failures in `reliability-design.md`
§2 and the **logging** of them here, so neither duplicates the other.

### 2.1 Why the module logger and not a handler

The codebase already uses module loggers and has a single startup logging
convention (`architecture.md` §Startup logs exactly one line naming the mode).
The analytics modules inherit that convention; the design adds no second logging
mechanism, no log sink, no formatter and no log-level configuration, because
`BR2.15` requires the analytics layer to add **no new configuration value** and
the no-junk-drawer convention forbids a logging helper module.

## 3. SLIs (informative, not operational)

These are **test-level** service indicators, not production metrics: the system
has no metrics endpoint, so an SLI here is a statement about what a test pins,
not a live number.

| SLI | Definition | Instrument |
|---|---|---|
| Correctness | `correct_responses / total_responses` | The `FR8.2` hand-pinned aggregate and refusal-shape tests (the hand-pinned expected values are the instrument, not the coverage floor). |
| Latency | `requests_below_200ms / total_requests` over the 10,000-row / 365-day fixture | The `FR8.9` test (`NFR1.1`, `NFR1.2`). |
| Failure distinguishability | `failures_with_distinct_code / total_failures` | The `NFR4.1`/`NFR4.2` tests. |

**An SLI is not a metric.** These are recorded so a later reader sees the
correctness/latency/failure axes were considered; they are **not** exposed by any
endpoint and are **not** monitored. The one instrument that *does* observe the
read path at test time — the `sqlite3` trace hook counting statements (`FR8.9`) —
is **test-only**, is not a production metric, and is not exposed by any endpoint.

## 4. Correlation and provenance

**Design decision: no correlation-ID propagation, because there is no boundary to
propagate across.**

- There is one process and no network hop in the read path (`BR2.8`); a request
  never crosses a process or host boundary, so there is no distributed trace to
  correlate and no correlation header to thread.
- The error envelope's machine code is the provenance a client and a log reader
  share: given a `STORAGE_FAILURE` on the wire, the matching log record is the
  one written by the module logger for that failure (`NFR8.2`).
- Adding a correlation ID would require either a header contract (widening C1) or
  a logging-context mechanism (a new configuration/tooling surface, forbidden by
  `C-5`/`C-6`) — for no boundary that exists.

## 5. Patterns declared inapplicable, with stated reasons

| Pattern family | Applies? | Why not |
|---|---|---|
| **Metrics collection architecture** | **No.** | No metrics endpoint, exporter or collector permitted (`C-5`/`C-6`); absence recorded. |
| **Distributed tracing architecture** | **No.** | One process, no network hop; no distributed boundary to span. |
| **Alerting rules and escalation** | **No.** | No pager, no alert channel; the one operator sees the in-line failure and the local log. |
| **Dashboard specifications** | **No.** | The analytics view is the operator's picture; no separate operations surface. |
| **SLI/SLO tracking infrastructure** | **No.** | SLIs exist only as test assertions; the SLO is deliberately unstated (no availability target). |
| **Correlation-ID propagation** | **No.** | No boundary to propagate across (§4). |

## 6. Traceability

| NFR (this unit) | Design solution (this file) |
|---|---|
| `NFR8.1` | §2 — failure logged through the module logger; never swallowed; never `print()`. |
| `NFR8.2` | §2, §4 — envelope code and log agree; code stays in the log, off-screen. |
| `NFR8.3` | §2 — no credential and no interpolated statement text in any log record. |

Full id-level enumeration is in `traceability.json`.
