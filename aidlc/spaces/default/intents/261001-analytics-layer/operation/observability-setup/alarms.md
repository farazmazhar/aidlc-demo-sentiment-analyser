# Alarms — intent `261001-analytics-layer`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent`
> · **Date:** 2026-10-03 · **Release under observation:** commit `aa0b1e4`
> · **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/observability-setup`
>
> **Upstream inputs consumed by this stage:** `nfr-design/performance-design.md`
> (`performance-design`), `nfr-design/security-design.md` (`security-design`),
> `nfr-design/reliability-design.md` (`reliability-design`),
> `nfr-design/observability-design.md` and
> `infrastructure-design/monitoring-design.md` (`monitoring-design`),
> `infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`). Plus the deployed evidence in
> `operation/deployment-execution/` and `operation/environment-provisioning/`.
>
> **Every threshold below was measured in this stage.** Where a threshold is
> inherited from a recorded measurement rather than re-measured, the source is named
> as such and both are shown.

---

## 1. There is no alerting channel — stated first, because it is the whole headline

**This project has zero alarms. Not "alarms that are hard to reach" — zero.**

There is no pager, no SNS topic, no webhook, no email, no chat integration, no
monitoring agent and no scheduled job. Measured this stage: no `aws` CLI, no
`~/.aws`, no `CDK_*`/`AWS_*` environment variable, no `terraform`/`ansible`; the only
scheduler-shaped thing on the machine is a `docker` binary that this project does not
use. `monitoring-design.md` §1 already recorded this as a design decision ("no alert
is defined, no threshold is set, no severity is assigned, no route exists") and
`observability-design.md` §1 repeats it.

**Therefore every row in §2 is a check a human runs, not an alarm that fires.** The
column that matters is *Automation status*, and for all of them it reads
**manual**. Saying otherwise would be the single most misleading thing this stage
could do — a reader who believed an alarm existed would wait for a page that cannot
come, and would learn about a `STORAGE_FAILURE` from a broken view instead.

**What would be required to change that**, and why it is not done here:

| Ingredient an alarm needs | Exists? | Ruling |
|---|---|---|
| A metric to threshold on | **No** | no metric is emitted; `C-6` caps runtime deps at `fastapi`+`uvicorn` |
| A rule engine to evaluate the threshold | **No** | no CloudWatch alarm, no local equivalent |
| A notification channel to route the result | **No** | nothing to send to — one operator, one terminal |
| A schedule to evaluate it without a human | **No** | no cron, no timer, no daemon beyond `uvicorn` itself |

Four absences. Naming them is more useful than a dashboard-shaped fiction.

## 2. Real signals, with real thresholds

Each row is checkable *right now*, against something that exists. **Normal-state
value** is what a healthy run looks like; **threshold** is what makes it worth a
look. Sources are measured measurements, labelled.

### 2.1 Storage failure on the analytics read path

| | |
|---|---|
| **Signal** | An `ERROR` record from the `app.routes` logger naming `STORAGE_FAILURE`. |
| **Normal** | **0** records. Measured: a clean 13-request run produced none. |
| **Threshold** | **≥ 1 occurrence.** No rate, no ratio, no percentage — see §4 for why a rate is not defensible here. |
| **Check** | `grep -n 'analytics .* read failed' app.log` |
| **Severity** | **SEV2 equivalent** — the read surface the operator depends on is failing. |
| **Source** | measured this stage: `ERROR:     analytics summary read failed (STORAGE_FAILURE): database is locked` (produced by holding an `EXCLUSIVE` lock from a second process against a live server). Wire status `500`, envelope `{"code":"STORAGE_FAILURE",…}` — three surfaces agree, per `NFR8.2`. |

### 2.2 Any 5xx in the access log

| | |
|---|---|
| **Signal** | A request line ending in a 5xx status. |
| **Normal** | **0**. Measured distribution across 13 real requests: `6 × 200`, `4 × 422`, `2 × 500`, `1 × 404` — where the two `500` were deliberately provoked for §2.1. |
| **Threshold** | **≥ 1**. |
| **Check** | `grep -cE '" 5[0-9]{2} ' access.log` |
| **Severity** | **SEV2 equivalent** for `/v2/analytics/*`; **SEV3** for anything else. |
| **Source** | measured this stage, live `uvicorn` on `127.0.0.1:8305`. |

### 2.3 Analytics read latency

| | |
|---|---|
| **Signal** | Wall-clock time of a `/v2/analytics/*` request. |
| **Normal** | over the pinned 10 000-row / 365-day fixture, **without coverage instrumentation**, 25 consecutive runs each: |
| | `summary` min **13.57** · p50 **15.42** · mean **15.71** · **max 20.53 ms** |
| | `terms`   min **27.49** · p50 **30.08** · mean **31.05** · **max 59.28 ms** |
| **Threshold** | `summary > 100 ms` · `terms > 120 ms` — ≈5× and ≈2× the measured maxima. These are *early-warning* thresholds, placed inside the 200 ms budget so there is room to react. |
| **Hard budget** | **200 ms** (`tests/test_analytics_read.py:34`, `BUDGET_MS = 200`). A request over this breaches `NFR1.1`/`NFR1.2` regardless of any warning threshold. |
| **Check** | `curl -sS -o /dev/null -w '%{time_total}\n' 'http://127.0.0.1:8000/v2/analytics/summary'`, or the in-suite measurement (`pytest tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget`). |
| **Severity** | **SEV3 equivalent** — degraded, with a workaround (narrow the range). |
| **Source** | measured this stage (the 25-run distribution). The single recorded figure in `test-results.md` §3.1 is `summary 15.24 ms / terms 25.04 ms` — a **single run**, which is why this file also publishes the distribution: the recorded `terms` figure sits *below* this run's p50 of 30.08 ms, so quoting it alone would understate the tail. |

### 2.4 Requested range width — the one saturation signal that bites

| | |
|---|---|
| **Signal** | The `from`/`to` span in the query string; equivalently the response byte count. |
| **Normal** | the unbounded default call: **368 bytes**, **1 ms** with one stored row. |
| **Threshold** | **> 1.5 MB response, or > 1 s wall time.** Measured crossover: **≈36 500 series entries ≈ a 100-year window**, which took **197 ms** at 36 502 entries and **235 ms** at 36 525 — i.e. it crosses the 200 ms budget. |
| **Check** | `curl -sS -o /dev/null -w '%{size_download} %{time_total}\n' '…/v2/analytics/summary?from=2000-01-01&to=2099-12-31'`, or read the width straight out of the access log: `grep -oE 'from=[0-9-]+&to=[0-9-]+' access.log`. |
| **Severity** | **SEV3 equivalent**. |
| **Source** | measured this stage over real HTTP against a store holding **one** row: 1 yr → 70 640 B / 13 ms · 21 yr → 2 803 760 B / 115 ms · 100 yr → **7 012 976 B / 235 ms**. This independently reproduces the `7,012,992` byte / `36,525` entry observation in `smoke-test-results.md` §4 (a 16-byte difference is response framing). |

### 2.5 Bind exposure — the only security-relevant signal

| | |
|---|---|
| **Signal** | The listening socket for the app's port. |
| **Normal** | **exactly one listener, on `127.0.0.1`**. Measured: `LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:* users:(("python",pid=162172,fd=6))`. |
| **Threshold** | **any** listener whose local address is not `127.0.0.1`, `::1` or `localhost`. |
| **Check** | `ss -ltnp \| grep ':8000'` |
| **Severity** | **SEV1 equivalent** — an unauthenticated app holding the operator's OpenRouter key, reachable off-machine. |
| **Automation status** | **manual, and only partial** — see §3.1. This is the most important row in the file precisely because its automation status is worst. |

### 2.6 Store schema integrity

| | |
|---|---|
| **Signal** | `schema_meta.version` and the count of named indexes. |
| **Normal** | **version `4`** and **exactly three** named indexes: `idx_analyses_created_at`, `idx_analyses_import_id`, `idx_analyses_label_created_at`. |
| **Threshold** | version ≠ 4, **or** any of the three indexes missing. A *version below 4* means the next boot will write the store (the migration runs iff the store is behind `SCHEMA_VERSION` — finding `F-01`). |
| **Check** | `sqlite3 'file:data/sentiment.db?mode=ro' "SELECT value FROM schema_meta WHERE key='version';"` plus `SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';` — the read-only URI means the check itself cannot mutate the store. |
| **Severity** | **SEV3 equivalent**; SEV2 if a boot is pending against a stale store. |
| **Source** | measured this stage; corroborated by `validation-report.md` V-11 and `health-check-report.md` §3.2 (the operator's store is at v4 with all three indexes, and a boot against it is write-neutral down to the mtime). |

### 2.7 Startup integrity — the migration's loud failure

| | |
|---|---|
| **Signal** | The process exiting at startup, or a `sqlite3.IntegrityError` in the output. |
| **Normal** | the one-line startup record, exactly once: `INFO:     Sentiment analysis app ready in offline mode (OpenRouter not connected)`, followed by the port opening. |
| **Threshold** | **any** `Application startup failed. Exiting.`, **or** any `IntegrityError`, **or** exit status ≠ 0. |
| **Check** | `grep -E 'IntegrityError\|Application startup failed' app.log`; `ss -ltn \| grep ':8000'` (a silent startup failure means **the port never opens**). |
| **Severity** | **SEV1 equivalent for the app** — it does not start. The store, however, is *not* damaged (see below). |
| **Source** | measured this stage by building a v3 store holding a row whose `label` the v1 rebuild cannot preserve: `sqlite3.IntegrityError: CHECK constraint failed: label IN ('positive','negative','neutral')`, **exit status 3**, and the port **never opened** (`connection refused`). The rollback held — the store still read `version=3` with the offending row intact, which is `BR5.5`/`NFR4.5` working. |

### 2.8 File permissions on the store

| | |
|---|---|
| **Signal** | The mode of `data/sentiment.db`. |
| **Normal** | measured `644`. |
| **Threshold** | **wider than `600`** — i.e. any group- or world-readable bit. |
| **Check** | `stat -c '%a' data/sentiment.db` |
| **Severity** | **SEV3 equivalent** on a single-user host. |
| **Note** | "Unauthenticated by design" extends to the file: it holds submitted text, unencrypted, world-readable on this host. Measured and recorded by `validation-report.md` V-12; repeated here because an operator reading only the *wire* posture would miss it. |

## 3. Automation status per signal — the honest column

| § | Signal | Automation | Why |
|---|---|---|---|
| 2.1 | `STORAGE_FAILURE` | **manual** — one `grep` | no rule engine, no channel |
| 2.2 | any 5xx | **manual** — one `grep` | as above |
| 2.3 | latency | **manual, and structural** | the app emits **no duration field**; measured access line is `… 200 OK` with no ms. Every latency figure here was stopwatch-measured by this stage, not continuously recorded by the system. |
| 2.4 | range width | **manual** | visible in the query string, but nothing evaluates it |
| 2.5 | bind exposure | **manual, partial** | see below |
| 2.6 | schema integrity | **manual** — one read-only query | safe to run at any time; not run at any time |
| 2.7 | startup integrity | **manual** | only observable at boot |
| 2.8 | file mode | **manual** | as above |

### 3.1 Why §2.5 is only partially checkable — a real gap, not a caveat

`ss` shows the socket **as it is now**. It has no memory, and the enforcement it
would be checking against is **bypassable by the documented invocation style**.
Measured this stage, on `127.0.0.2` — a host inside `127.0.0.0/8`, which Linux routes
to `lo` and which is therefore unreachable off-machine:

```
resolve_bind_host("127.0.0.2")   -> REFUSED (NonLoopbackBindError)
create_app(host="127.0.0.2")     -> REFUSED, before any lifespan ran
--- but the uvicorn CLI ignores both ---
$ python -m uvicorn app:app --host 127.0.0.2 --port 8299
LISTEN 0  2048  127.0.0.2:8299  0.0.0.0:*  users:(("python",pid=176689,fd=6))
GET http://127.0.0.2:8299/v1/health -> 200
GET http://127.0.0.1:8299/v1/health -> failed to connect
server stderr: (no refusal logged — the enforcement was never consulted)
```

**This upgrades `health-check-report.md` §2.3 from a code-reading observation to a
measurement.** The enforcement is real and correct where it is reached; the
`uvicorn app:app` CLI shape simply never reaches it, because `resolve_bind_host` is
called inside `run()`, not inside the application object. The operator mitigation
available today is the default: **omit `--host`, or pass a loopback value.**

## 4. Thresholds deliberately NOT set — and why

An alarm that cannot discriminate is worse than no alarm, because it trains the
operator to ignore it. Four standard thresholds are deliberately absent.

| Standard threshold | Why not set |
|---|---|
| **Error-rate percentage** (e.g. "alert above 1 %") | **No traffic history exists.** The largest real sample in this project is 27 requests (`smoke-test-results.md` §2) and the run in this file is 13. A percentage over 13 requests quantises to 7.7 % steps; over 3 requests, to 33 %. It cannot be distinguished from noise, and it would fire on a single user typo. `NFR9`/`performance-design.md` §4 record that there is **no RPS target** because the store is a single-user local file. |
| **Request-rate / throughput alarm** | Same reason: one operator, no traffic, no baseline. Any rate threshold would be invented. |
| **CPU / memory / disk-I/O saturation** | Nothing records them. A threshold on a number that is never measured is a fiction, and `monitoring-design.md` §1 already records "metrics: empty by decision". |
| **Log-volume growth** | The log has no retention and no baseline; a run of 3 requests and a run of 30 000 produce the same order of magnitude of lines. |
| **Burn-rate alert** | Requires a continuously computed SLI over a rolling window. Nothing computes one. See `slo-config.md` §4. |

## 5. Severity mapping for this project

The standard four-level scheme is retained, with each level restated in terms of
what this app actually is — one operator, one machine, one file. It is a **mapping,
not a rotation**: there is no on-call to rotate, and `incident-response-guide.md`'s
escalation matrix presupposes a team this project does not have.

| Level | Criterion **here** | Response time | Example |
|---|---|---|---|
| **SEV1** | The app does not start, or is reachable off loopback. | immediate | migration rollback (§2.7); non-loopback listener (§2.5) |
| **SEV2** | The read surface fails while the process is up. | same sitting | `STORAGE_FAILURE` records (§2.1); any 5xx (§2.2) |
| **SEV3** | Degraded but usable, with a workaround. | same day | latency above the early-warning threshold (§2.3); a very wide range (§2.4) |
| **SEV4** | No user impact; recorded, not acted on. | next release | a stale schema version with no boot pending (§2.6); store mode `644` (§2.8) |

**Two honest notes on this table.** First, the SEV1 criterion "reachable off
loopback" is the one alarm whose *absence* is most valuable and whose detection is
weakest (§3.1). Second, the recovery paths are the ones already proven reachable by
`deployment-log.md` §3 — RB1 (startup failure), RB2 (`git checkout express`), RB3
(the byte-identical `data/sentiment.db.bak-aa0b1e4` created by release step R5).