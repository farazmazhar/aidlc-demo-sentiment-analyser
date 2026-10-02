# Observability Requirements — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-requirements` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Source of truth.** The inception parent is `NFR8`. Targets carry sub-numbers
> and a **measuring instrument**. No monitoring stack is proposed: the repository
> has no metrics, tracing, exporter or dashboard infrastructure, and `C-5`/`C-6`
> forbid adding one — so this file states what exists (logging) and records the
> absences honestly rather than inventing a monitoring system.

## Logging (`NFR8`)

| ID | Requirement | Measuring instrument | Source |
|---|---|---|---|
| **NFR8.1** | An analytics failure is **visible through the module logger** — it is logged as a record via the module's logger, never swallowed and never printed. `print()` does not appear in `app/`. | The failure-logging test: provoke a storage failure (or the failure path under test) and assert a log record is emitted through the module logger. The repository's existing pattern (module loggers; `print()` never appears in `app/`) is the convention the new module must follow. `BR4.6` pins the behaviour. | `NFR8`; `BR4.6`; `C-12` |
| **NFR8.2** | A failure with a machine code travels through the error envelope with its code (`VALIDATION_FAILED`, `STORAGE_FAILURE`) **and** appears in the application log, so the wire surface and the log agree. | The same failure tests assert both: the response carries the envelope code (`NFR4.1`, `NFR4.2`) and a matching log record is emitted. The code stays in the server log; the view's render path never shows the machine code on screen (`contract-summary.md` C2). | `NFR8`; `BR4.5`; `BR4.6`; `contract-summary.md` C2 |
| **NFR8.3** | **No request parameter is interpolated into statement text, and no credential appears in any log record.** The logging rule and the parameter-binding rule are the same rule from two sides (`NFR2.3`): a value reaches a statement only as a bound parameter, and a log record carries no credential and no interpolated statement text. | The instruments that exist **in this unit today**: code inspection of the read module and failure handler (`BR2.9`, `BR4.6`) plus the existing redaction assertions (`reprs`, `record.__dict__`, response bodies) staying green. **Cross-unit dependency (not this unit's instrument):** the secret-scanning gate (`FR7.3`) does not exist yet and is a `u4-platform-packaging` obligation — named only as a dependency, not as a measuring instrument available to `u1` now. | `NFR8`; `BR4.6`; `BR2.9`; `NFR2.5`; `FR7.3` (scanner — owned by `u4-platform-packaging`) |

## SLI/SLO definitions

| Aspect | Statement |
|---|---|
| **SLI — correctness** | `correct_responses / total_responses`, measured by the `FR8.2` hand-pinned aggregate and refusal-shape tests. The hand-pinned expected values are the instrument, not the coverage floor. |
| **SLI — latency** | `requests_below_200ms / total_requests` over the 10,000-row / 365-day fixture, measured by the `FR8.9` test (`NFR1.1`, `NFR1.2`). |
| **SLI — failure distinguishability** | `failures_with_distinct_code / total_failures`, measured by the `NFR4.1`/`NFR4.2` tests. |
| **SLO** | **None is stated.** There is no hosted service, no multi-user load and no 30-day window to compute against; the deployment is a localhost checkout. Per the NFR design guide, an SLO is defined per critical user journey *for a service with an availability target* — this system has none (`NFR9`, `team.md` §Deployment). Recorded as a deliberate absence rather than a missing number. |

## Monitoring, alerting and dashboards

| Aspect | Statement |
|---|---|
| **Monitoring** | **None.** No metrics endpoint, no exporter, no collector. `C-5`/`C-6` forbid adding one, and `A5`/`FR7.3` treat the transitively pulled `opentelemetry-api` as a non-imported dependency. The absence is recorded so it is not mistaken for coverage. |
| **Alerting** | **None, and no thresholds.** A single-user local app has no pager and no alert channel. A failure is surfaced in-line to the one operator and in the local log (`NFR8.1`). No alert threshold is invented here. |
| **Dashboards** | **None.** The analytics view itself is the operator's picture; there is no separate operations dashboard. The view's own loading/empty/error/partial states (`NFR4.6`) are the closest thing to an operational surface, and they are a user-facing rendering, not monitoring. |
| **Distributed tracing** | **Not applicable.** One process, one local store, no network hop in the read path (`BR2.8`). There is no distributed boundary to trace, so no trace spans are required; adding OTel spans would be egress-adjacent tooling the constraints forbid. |
| **Instrument that exists** | The `sqlite3` trace hook (`FR8.9`) is a **test-only** instrument that counts statements; it is not a production metric and is not exposed by any endpoint. Recorded so its existence is not read as monitoring. |

## Cross-reference

The wire-side failure contract (the `{code, message}` envelope, `STORAGE_FAILURE`,
`VALIDATION_FAILED`) is owned by the **reliability** file (`NFR4.*`); this file owns
the **log-side** obligation and the record that no monitoring system exists. The
two files share the failure tests as instruments but make different claims, so
neither duplicates the other.
