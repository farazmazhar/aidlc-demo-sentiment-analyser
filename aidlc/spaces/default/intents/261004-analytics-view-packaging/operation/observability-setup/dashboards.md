# Dashboards — intent `261004-analytics-view-packaging`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent` ·
> **Date:** 2026-10-04 · **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/observability-setup`

## 1. No dashboard is possible — and why

A dashboard is a hosted, continuously refreshing view over emitted metrics. This project
has **no metric backend, no host and no account**: `C-4`/`C-5` forbid a cloud component,
the runtime cap holds dependencies at `fastapi` + `uvicorn`, and there is no `aws` CLI,
no `~/.aws`, no `AWS_*`/`CDK_*` variable and no IaC file. So the stage's
"CloudWatch dashboard configuration" output is recorded as **inapplicable per element**,
with the rule that rules it out — and **substituted** by the four command-panels below,
each of which prints a measured value on demand.

## 2. The four panels (commands, not charts)

### Panel A — The four golden signals (read over a session)

| Signal | Command | What it shows |
|---|---|---|
| Traffic | `wc -l access.log` | requests served this session |
| Errors | `grep -cE '" (4|5)[0-9][0-9]' access.log` | 4xx/5xx count |
| Latency | `grep -E '" [0-9]{3} ' access.log` (no duration field) | **not measurable from the log** — measured only by a stopwatch or the fixture test (`slo-config.md` SLI-1) |
| Saturation | store census (Panel C) + the requested range width | store size and the cost driver |

### Panel B — Engine / connection state (the health signal)

```bash
curl -sS http://127.0.0.1:8000/v1/health
# {"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
```

The single authoritative "is it serving, and how" line. `mode` and `connected` are
intent vs reality; `reason` appears only when not connected.

### Panel C — Store census

```bash
python -c "import sqlite3; c=sqlite3.connect('file:data/sentiment.db?mode=ro',uri=True); \
 print('version', list(c.execute('select * from schema_meta'))); \
 print('rows', list(c.execute('select count(*) from analyses'))[0][0]); \
 print('indexes', [r[0] for r in c.execute(\"select name from sqlite_master where type='index' and name not like 'sqlite_%'\")])"
```

Read-only. Expected: `version 4`, `rows ≥ 0`, three indexes. Measured at the cutover:
`version 4`, `rows 7`, three indexes.

### Panel D — The analytics view's served surface

```bash
curl -sS http://127.0.0.1:8000/ | grep -oE 'data-testid="(range-from|range-to|range-status|terms-positive|terms-negative|summary-partial|terms-partial)"' | sort -u
```

Prints the seven hooks this release adds. Their presence is the only server-visible
evidence of the view change, because the browser script is never executed by any test
(`tracing-config.md` §3).

## 3. What a dashboard would have shown, and does not

| Would-be panel | Reality |
|---|---|
| Latency percentile chart | No duration in the access line; latency is a stopwatch value or the fixture test. |
| Error-rate time series | No metric emission; the count is greppable, the rate is not computable. |
| Saturation/CPU/memory | No host agent; the app is one local process. |
| SLO burn-down | No continuously computed SLI over a rolling window. |
| Synthetic canary result | No Synthetics; the substitute is the operator's own smoke run. |

Each absence is a decision (or a consequence of the two-package cap), not an oversight,
and each is recorded so a green verification is not read as coverage of a monitoring
surface that does not exist.
