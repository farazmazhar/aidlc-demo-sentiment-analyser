# Tracing Configuration — intent `261004-analytics-view-packaging`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent` ·
> **Date:** 2026-10-04 · **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/observability-setup`

## 1. No distributed tracing — there is no boundary to span

Distributed tracing exists to follow one request across process/service boundaries.
This system has **one process, one machine, one file**. Measured: the read path imports
nothing network-capable (`app/analytics.py`'s import list is `re`, `sqlite3`,
`collections`, `dataclasses`, `datetime`, `decimal` plus in-repo modules); only
`openrouter_client.py` and `session_auth.py` import a network client, and neither is
reachable from a read. There is no second service to trace into.

So the stage's "X-Ray tracing configuration" output is **inapplicable per element**: no
AWS account, no X-Ray daemon, no SDK/exporter, and `C-4`/`C-5` forbid adding one. No
sampling rate is chosen because there is no trace to sample.

## 2. What substitutes for a trace

Three in-process instruments reconstruct what a trace would show:

### 2.1 The request lifecycle (access log + lifespan)
A request's path is fully described by the access line (method, path+query, status) plus
the lifespan's startup/shutdown lines. For a failure, the status plus the storage
`ERROR` record is the whole story.

### 2.2 The SQL statement trace (for the read path)
`sqlite3`'s `set_trace_callback` counts the statements a read executes. Measured
(inherited): every `/v2` read is exactly **one `SELECT`** at every range width — the
cost of a wide request is entirely in-process series assembly and serialisation, not in
per-day queries. This is the instrument that makes the "no query per day" claim
checkable.

### 2.3 The served-markup hooks (for the view change)
The view's new behaviour is client-side and is never executed by the suite. The
server-visible substitute is the served markup: `curl -sS http://127.0.0.1:8000/ | grep
-oE 'data-testid="(range-from|range-to|range-status|terms-positive|terms-negative|summary-partial|terms-partial)"'`.
Their presence proves the markup shipped; their behaviour (partial-failure marker,
supersede guard) is exercised only by the operator's manual end-to-end step, per the
recorded Q2 decision at Requirements Analysis.

## 3. What is deliberately not instrumented

| Not instrumented | Why |
|---|---|
| X-Ray segments / OpenTelemetry spans | No boundary; no SDK admitted by the cap. |
| Trace context propagation (W3C headers) | Nothing to propagate across. |
| Business annotations (`customerId`, `orderStatus`) | Single-user local tool; a row count is the only "business" metric. |
| Correlation ids in logs | No multi-service correlation to serve. |

## 4. The one gap worth naming

The view's two load-bearing behaviours — **NFR4.6** (per-section partial-failure marker)
and **NFR4.7** (no silent retry; superseded response discarded) — have **no automated
execution instrument**. They are pinned as static served-asset assertions
(`tests/test_page.py`) plus the operator's manual boot, because the runtime cap admits no
browser-automation library. This is recorded here and in `anomaly-config.md` so a green
`make verify` is not read as coverage of the browser behaviour.
