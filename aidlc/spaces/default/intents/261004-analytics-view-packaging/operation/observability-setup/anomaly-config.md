# Anomaly Configuration — intent `261004-analytics-view-packaging`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent` ·
> **Date:** 2026-10-04 · **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/observability-setup`

## 1. No ML anomaly detection — and what replaces it

CloudWatch Anomaly Detection needs a metric with a stable baseline over time. There is
no metric backend, no history and no scheduler, so it is **inapplicable per element**
(`C-4`/`C-5`; no AWS account). What replaces it is a short list of **expected-value
checks**: each names a value the system should hold, the command that reads it, and what
a deviation would mean. An operator runs them by hand; there is no automatic detector.

## 2. The expected-value checks

| # | Check | Expected | Command | A deviation means |
|---|---|---|---|---|
| A1 | Store schema version | `4` | read-only `select * from schema_meta` | a schema change shipped unexpectedly, or a rollback downgraded it |
| A2 | Store indexes | the three named analytics indexes present | read-only `sqlite_master where type='index'` | a migration dropped them (the historical TD-1 defect) |
| A3 | Store row count | non-decreasing across a read session | `select count(*) from analyses` before/after | a read wrote (violates SLI-5) |
| A4 | Store sha256 + mtime | unchanged across a read session | `sha256sum` / `stat -c %y` | the read path opened the file for writing |
| A5 | Loopback bind | exactly one listener on `127.0.0.1` | `ss -ltnp \| grep 8000` | a non-loopback bind (the CLI-bypass gap, `alarms.md` §3) |
| A6 | Summary payload width | proportional to the requested range; small for a small range | `curl … summary?from&to \| wc -c` | a request for a wide range returns a multi-MB body — the documented, uncapped behaviour, not a defect |
| A7 | View hooks present | the seven new `data-testid`s in `/` | the Panel D command | the view markup regressed |
| A8 | `/v1/health` mode | `offline` on a checkout with no `config.local.toml` | `curl /v1/health` | a credential appeared, or the mode changed unexpectedly |
| A9 | `/v1/health` body | no key/token material | `curl /v1/health` | a credential leaked into a response |
| A10 | Failure shapes | `422`/`500` distinct from empty `200` | the smoke suite | a failure rendered as a plausible empty result |
| A11 | `make verify` result | all gates green | `make verify` | a gate regressed (tests, coverage, lint, secret scan, audit) |

## 3. The checks that are *most* likely to catch a real regression

- **A11** — the packaging gates are the broadest single check; a red `make verify` is the
  first thing to look at.
- **A4/A3** — store write-neutrality is the property most easily broken by a careless
  read-path change, and the mtime check is strictly stronger than comparing contents.
- **A7** — the only server-visible evidence of the view change, since the browser script
  is never executed.

## 4. What is deliberately not configured

| Not configured | Why |
|---|---|
| CloudWatch Anomaly Detection bands | No metric, no baseline, no backend. |
| Static metric thresholds with evaluation periods | No evaluator. |
| Dynamic baselines / seasonal models | No traffic history (the largest real sample is a handful of requests). |
| Automated remediation | No orchestrator, no supervisor, no second process to act. |

## 5. The view's un-instrumented behaviours (restated)

NFR4.6 (partial-failure marker) and NFR4.7 (supersede / no silent retry) have **no
automated execution instrument** — they are pinned statically and exercised manually
(`tracing-config.md` §4). A green `make verify` must not be read as coverage of them;
A7 only proves the hooks are *present*, not that the browser logic behaves.
