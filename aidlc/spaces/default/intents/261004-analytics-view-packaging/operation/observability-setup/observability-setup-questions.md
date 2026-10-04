# Observability Setup — Questions — intent `261004-analytics-view-packaging`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent` ·
> **Date:** 2026-10-04 · **Release under observation:** the working tree at HEAD `4b67c03`
> · **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/observability-setup`
>
> **Upstream inputs:** the prior intent's `261001-analytics-layer/operation/observability-setup/*`
> (the same project reality, re-measured where this release changed it) · this intent's
> `operation/deployment-execution/*` · `construction/build-and-test/*` · `memory/team.md`
> § Deployment, § Testing Posture, § Way of Working · `memory/project.md` § Forbidden
> (`C-4`, `C-5`).

`express` skips NFR Design and Infrastructure Design, so there is no `monitoring-design`
or `observability-design` to read; the minimum observable surface is derived from the
requirements, the deployed application, Build and Test, and Deployment Execution. Each
question below is either **answered from evidence** (with its source) or left genuinely
**open**.

---

## 1. The stage's five Step-2 questions, answered from evidence

**Q — Golden signals (latency, traffic, errors, saturation)?**
**Answered from evidence: all four are visible; none from a metric backend.** Latency is
a stopwatch measurement (the access line carries no duration field). Traffic is the
access log. Errors are the `app.routes` module logger plus access-log status. Saturation
is the store census plus the requested range width. Sources: `dashboards.md` §2,
`slo-config.md` §2, and this stage's measurements.

**Q — SLOs/SLIs defined?**
**Answered from evidence: six SLIs expressed as release gates over a verification
window, not 30-day service targets.** A 30-day rolling SLO is uncomputable here (no
continuous traffic, no metric emission, one operator). `slo-config.md` §1–§3.

**Q — Dashboard layouts needed?**
**Answered from evidence: no dashboard is possible; a documented query/command set is
what exists.** `C-4`/`C-5` forbid a cloud component, and there is no AWS account, CLI,
credential or IaC. Four panels are specified as commands with measured output —
`dashboards.md` §2.

**Q — Log retention and aggregation rules?**
**Answered from evidence: none, by decision.** There is no log sink, no formatter and no
retention tier; a session's log exists only if the operator redirects one. The two log
streams and the application call sites are enumerated in `log-queries.md` §1–§2.

**Q — Distributed tracing instrumentation?**
**Answered from evidence: none — there is no boundary to span.** One process, one
machine, one file; the read path imports nothing network-capable. `tracing-config.md` §1.

## 2. Further questions resolved from evidence

- **Latency threshold basis.** The prior intent's measured distribution over the pinned
  10,000-row/365-day fixture (`summary` max 20.53 ms; `terms` max 59.28 ms) and the
  **200 ms** budget (`tests/test_analytics_read.py` `BUDGET_MS = 200`). This release adds
  no server work, so the distribution is inherited, not re-measured (`alarms.md` §2).
- **Error-rate threshold.** None — a rate is not computable over a handful of requests;
  the **count** is used instead (`alarms.md` §4).
- **Does a `422` emit an application log record?** No (measured in the prior intent;
  `log-queries.md` §4). Unchanged by this release — the view change is client-side.
- **The view's own failure signals.** The partial-failure marker (`summary-partial`,
  `terms-partial`) and the supersede guard live in `app/static/app.js`, which the suite
  never executes; they are observable only as served markup hooks (`tracing-config.md`
  §3, `anomaly-config.md` §2).

## 3. Genuinely open — the human's or a later scope's

- **OQ-1 — Bound the analytics summary series width?** Still open; belongs to the
  analytics surface's owner. A 100-year range returns ~7 MB / 36,525 zero-filled entries.
  Inherited from the prior intent; this release does not change the series contract.
- **OQ-2 — Should a validation failure emit an application log record?** Open; a code
  change plus a decision about whether a mistyped date is worth a line.
- **OQ-3 — Close the `uvicorn --host` bypass?** Open; a code change, and `deployment-execution`
  §2 records the interim mitigation (omit `--host` or pass a loopback value).
- **OQ-4 — Should logs be redirected to a file and retained?** An operator preference
  about their own machine; nothing in the record fixes a destination.
- **OQ-5 — Commit and tag the release?** Still open from Deployment Execution Q5: the
  change is uncommitted.

## 4. Deliberately not asked

| Not asked | Why |
|---|---|
| Which CloudWatch dashboard / SNS topic / X-Ray sampling rate? | Unanswerable: no AWS account, CLI, credential or IaC (measured); no channel and no second recipient. |
| RTO / RPO? | Backup/PITR absent by decision; the actual asymmetry is measured (RB2 costs one checkout; RB3 costs everything, mitigated only by the R4 backup). |
| Business KPIs? | Single-user local file; a KPI is a row count one query already returns. |
| Raise coverage / enable branch coverage? | Off by affirmed decision with its measured cost recorded. |

## 5. Posture

**Answered from evidence:** 4 golden-signal mappings · 6 SLIs with release-gate targets ·
4 dashboard panels · 0 retention rules (by decision) · 0 tracing instruments (by
measurement). **Left open for the human:** 5 questions, none of which blocks this
stage's artifacts.

**Not provisioned, per element, with the ruling rule in each file:** CloudWatch
dashboards, alarms, Logs Insights, SLO dashboards, burn-rate alerting, Synthetics
canaries, X-Ray, OpenTelemetry SDK/exporter, CloudWatch EMF, log shipping and retention.
**The common one-line reason:** `C-4`/`C-5` forbid a new external service or cloud
component and the runtime cap holds dependencies at exactly `fastapi` and `uvicorn`, and
there is no AWS account, CLI, credential or IaC on this machine to host them.
