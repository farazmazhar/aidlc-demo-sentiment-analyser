# Anomaly Detection Configuration — intent `261001-analytics-layer`

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
> (`infrastructure-specification`).
>
> **Every expected value below is a measurement taken in this stage**; every check
> is a command that was run and whose real output is quoted.

---

## 1. No anomaly-detection model is fitted — and a statistical one could not be

CloudWatch Anomaly Detection establishes a statistical baseline per metric and alerts
on deviation. Every precondition it needs is absent:

| Precondition | This system | Evidence |
|---|---|---|
| A continuous metric time series | **None.** No metric is emitted by anything. | `C-6`; `observability-design.md` §1. **Measured**: no metrics library, no exporter, no agent in `app/`. |
| Enough history to fit a baseline on | **None.** 2–4 weeks is the minimum; this project has produced **27** real requests (`smoke-test-results.md` §2) and **13** in the run this file re-measured. | `slo-sli-patterns.md` §"Process", step 1. |
| A steady baseline shape (daily/weekly cycle) to model | **None.** One operator's usage is episodic: nothing runs between sessions. | `alarms.md` §1. |
| A component to evaluate the band | **None.** No rule engine exists locally. | `alarms.md` §1. |

**Fitting a model to that would be the worst of both worlds**: an alert whose band is
estimated from a handful of points, firing on noise. So this file specifies
**deterministic, threshold-based checks a human runs** — the same distinction
`observability-patterns.md` draws when it recommends static thresholds alongside
anomaly detection, applied in the only direction available here.

**What is lost by not fitting one, stated honestly:** drift and gradual
degradation. A statistical detector would eventually notice that latencies are
creeping up or the store is quietly growing; nothing in this file will, because
nothing accumulates. §3 names what that costs.

## 2. The anomalies that *can* be detected by hand

Each row is a check that was run in this stage. **Expected** is the healthy value;
**anomalous** is what the check returns instead.

### A1 — Analytics storage failure

| | |
|---|---|
| **Check** | `grep -n 'analytics .* read failed' app.log` |
| **Expected** | no output (measured: 0 on a clean 13-request run) |
| **Anomalous** | `ERROR:     analytics summary read failed (STORAGE_FAILURE): database is locked` |
| **Why this is an anomaly, not a value** | The *whole* `app.routes` logger should be silent during healthy operation. Any line from it is an anomaly by construction — the module emits nothing on the success path. |
| **Severity** | SEV2 — `alarms.md` §5 |

### A2 — The R-01 cross-thread signature (a distinct sub-case of A1)

| | |
|---|---|
| **Check** | `grep -c 'SQLite objects created in a thread' app.log` |
| **Expected** | **0** |
| **Anomalous** | ≥ 1 |
| **Verified** | `sqlite3.ProgrammingError` **is** a subclass of `sqlite3.Error` (MRO measured: `ProgrammingError → DatabaseError → Error`), so the route's `except sqlite3.Error` catches it and the message lands in the A1 record verbatim: `SQLite objects created in a thread can only be used in that same thread. The object was created in thread id … and this is thread id ….` |
| **Why it earns its own row** | It is the **signature of accepted defect R-01** (`reliability-design.md` §3, `team.md` "NEVER ship a defect without a test that reproduces it"). Today the fix holds the thread-affinity decision with `check_same_thread=False`, so this string should never appear. If it does, the invariant recorded in `app/db.py`'s connection docstring — *request-scoped, never pooled, never shared* — has been violated, and the failure will present to the operator as an indistinguishable `STORAGE_FAILURE`. This one grep is the cheapest available regression check for that invariant. |
| **Severity** | SEV2 |

### A3 — Any 5xx in the access log

| | |
|---|---|
| **Check** | `grep -cE '" 5[0-9]{2} ' access.log` |
| **Expected** | **0** (measured mix: `6 × 200`, `4 × 422`, `2 × 500` — the two `500` were deliberately provoked for A1) |
| **Anomalous** | ≥ 1 |
| **Severity** | SEV2 for `/v2/analytics/*`, SEV3 elsewhere |

### A4 — Startup failure

| | |
|---|---|
| **Check** | `grep -E 'IntegrityError\|Application startup failed' app.log` **and** `ss -ltn \| grep ':8000'` |
| **Expected** | no match, **and** a listener present |
| **Anomalous** | the `IntegrityError` line, or **no listener at all** |
| **Verified this stage** | built a v3 store holding a row the v1 rebuild cannot preserve: `sqlite3.IntegrityError: CHECK constraint failed: label IN ('positive','negative','neutral')`, **exit status 3**, port **never opened** (`connection refused`), store afterwards still `version=3` with the row intact — rollback held. |
| **The two-shape detail** | the check must look at **both** the text *and* the socket. A silent startup failure shows no friendly message — the port simply is not there. This is `deployment-strategy.md` §4's teaching point, confirmed. |
| **Severity** | SEV1 |

### A5 — Bind escape to a non-loopback address

| | |
|---|---|
| **Check** | `ss -ltnp \| grep ':8000'` |
| **Expected** | exactly one listener, `127.0.0.1:8000` |
| **Anomalous** | any local address outside `127.0.0.1` / `::1` / `localhost` |
| **Severity** | **SEV1** — unauthenticated app holding the operator's key, off-machine |
| **Caveat — this check has a blind spot, measured** | it shows the socket *now*, and it cannot tell you how the process was started. Measured: `resolve_bind_host("127.0.0.2")` refuses and `create_app(host="127.0.0.2")` refuses, yet `uvicorn app:app --host 127.0.0.2` **bound and served `200` with no refusal logged**. So a check that passes is genuine evidence about the present, and **no** evidence about the past. Full measurement in `alarms.md` §3.1. |

### A6 — Latency outside the measured band

| | |
|---|---|
| **Check** | `curl -sS -o /dev/null -w '%{time_total}\n' 'http://127.0.0.1:8000/v2/analytics/summary'` |
| **Expected** | `summary` under **~21 ms**, `terms` under **~59 ms** — the maxima of a 25-run distribution this stage took (p50 15.42 / 30.08 ms) |
| **Anomalous** | `summary` > 100 ms · `terms` > 120 ms (early warning) · anything > **200 ms** (budget breach, `NFR1.1`/`NFR1.2`) |
| **Validity condition** | **only over a bounded range.** On the pinned 365-day fixture. A wide request legitimately exceeds the budget (§A7), so a latency check run over an unbounded range will read as an anomaly when the input is the cause. |
| **Severity** | SEV3 |

### A7 — Unbounded series width

| | |
|---|---|
| **Check** | `grep -oE 'from=[0-9-]+&to=[0-9-]+' access.log \| while …` (width in days — the working form is in `log-queries.md` §Q6), or `curl -w '%{size_download}'` |
| **Expected** | the unbounded default call: **368 bytes**, **1 ms**, with one stored row |
| **Anomalous** | > **1.5 MB** or > **1 s**; the crossover is ≈ **36 500 entries** (≈ a 100-year window) |
| **Verified this stage** | over real HTTP on a store holding **one** row: 7 days → 1 520 B / 7 ms · 1 yr → 70 640 B / 13 ms · 21 yr → 2 803 760 B / 115 ms · 100 yr → **7 012 976 B / 235 ms** (36 525 entries). |
| **Why it is an anomaly and not a defect** | the behaviour is the contracted one (`BR4.4` zero-fills the chart; `NFR9.3` caps the series width **deliberately, by nothing**). The anomaly is a *person about to ask for it*, not a bug. `smoke-test-results.md` §4 recorded the same arithmetic as an observation and declined to call it a defect — that judgement still stands. |
| **Severity** | SEV3 |

### A8 — The store written when it should not have been

| | |
|---|---|
| **Check** | `stat -c '%y' data/sentiment.db`, before and after any command that reads analytics |
| **Expected** | **mtime unchanged** — measured, before and after every command in this stage: `2026-10-03 03:33:42.920985500 +0500`, `sha256 c8be1361…c39`, `size 32768`, `mode 644` |
| **Anomalous** | mtime moved after a read-only operation |
| **Why mtime and not the hash** | an unchanged mtime means the file was **never opened for writing**; a matching hash would also be consistent with a write-then-restore. `NFR3.1`/`NFR3.2`. |
| **Severity** | SEV2 — the read-only guarantee is load-bearing for this whole layer |

### A9 — Schema drift

| | |
|---|---|
| **Check** | `sqlite3 'file:data/sentiment.db?mode=ro' "SELECT value FROM schema_meta WHERE key='version';"` plus the `idx_%` index listing — the read-only URI means the check cannot itself cause A8 |
| **Expected** | **4**, with exactly `idx_analyses_created_at`, `idx_analyses_import_id`, `idx_analyses_label_created_at` |
| **Anomalous** | version ≠ 4, or any index missing |
| **Direction matters** | a version **below** 4 means the next boot *will* write the store. Verified: on a v4 store `init_db` runs 11 statements and leaves the file byte-identical, mtime unchanged — the `CREATE INDEX IF NOT EXISTS` no-ops and the `ON CONFLICT … DO UPDATE` upsert write the values already held, so no page is dirtied and no journal is created. That is the mechanism behind finding **F-01**. |
| **Severity** | SEV3; SEV2 if a boot is pending |

### A10 — Credential material in a log

| | |
|---|---|
| **Check** | `grep -cE 'sk-or-v1\|sk-\|AKIA\|BEGIN .* PRIVATE KEY\|api_key\|password' app.log access.log` |
| **Expected** | **0** for every pattern |
| **Anomalous** | ≥ 1 |
| **Verified this stage** | against a real 13-request capture containing a deliberate storage failure: `sk-or-v1` 0/0 · `sk-` 0/0 · `AKIA` 0/0 · `BEGIN.*PRIVATE KEY` 0/0 · `api_key` 0/0 · `password` 0/0 (app.log / access.log). |
| **Why this check is the security-relevant one** | `NFR8.3` requires no credential and no interpolated statement text in any record. The five log templates interpolate only a mode string, a code, `str(exc)`, a file path and an OAuth exception — but "no credential is *designed in*" is not the same as "no credential *appears*", and this grep is the difference. It is a **manual** stand-in for the secret scanner that `FR7.3` mandates and `u4-platform-packaging` does not yet provide. |
| **Severity** | **SEV1** — a leaked credential in a log is the one finding that becomes unrecoverable |

### A11 — Unexpected engine mode

| | |
|---|---|
| **Check** | `grep 'Sentiment analysis app ready' app.log` |
| **Expected** | exactly **one** line, reading `… in offline mode (OpenRouter not connected)` — measured: `grep -c` → `1` |
| **Anomalous** | **0** lines (the app did not finish startup); **≥ 2** (a restart in one captured stream); or the word **`live`** where offline was expected |
| **Why it matters** | the line names the engine in use and **never the key** (`NFR6.2`, `BR5.1`). It is the only place the active mode is recorded, and mode is the difference between "no egress" and "egress to a third party". Measured default on this checkout: `offline`, no `config.local.toml` (`validation-report.md` V-16). |
| **Severity** | SEV2 if unexpected `live` (egress the project did not intend); SEV1 if the line is absent |

### A12 — File permissions on the store

| | |
|---|---|
| **Check** | `stat -c '%a' data/sentiment.db` |
| **Expected** | `600` |
| **Measured** | **`644`** |
| **Anomalous** | any group- or world-readable bit |
| **Honest note** | **the measured value is already anomalous against the expectation.** The store holds submitted text unencrypted, and `644` makes it world-readable on this host. `validation-report.md` V-12 records the same and `team.md` §Deployment states "stores submitted text unencrypted". On a single-user machine with no second account and no network reach the practical exposure is nil — but the check is included because "unauthenticated by design" extends to the file, and an operator reading only the *wire* posture would not know that. |
| **Severity** | SEV3 |

## 3. Anomalies that exist and are **not** detectable here

Named, because "absence must not read as coverage" is this project's own standing rule.

| Anomaly | Why it is not detectable | What it would take |
|---|---|---|
| **Gradual latency regression** | Nothing accumulates; each run starts from zero history. A 1 %/week drift is invisible because week 2 is compared to nothing. | A metrics stream and a stored series. |
| **Store growth / disk pressure** | One sample, no trend. `anomaly-config.md` §2-A8 catches *unexpected writes*, never *slow growth*. | A history of `stat` samples. |
| **Slow memory growth / leak** | Never measured. A single process, restarted when the operator restarts it. | An in-process metrics surface — forbidden by `C-6`. |
| **Anything after the operator stops looking** | The whole posture is inspect-on-demand. A regression introduced at 18:00 and discovered at 09:00 has no record at all. | An alerting channel that does not exist (`alarms.md` §1). |
| **Cross-request ordering / concurrency faults** | 27 sequential requests from one client is a correctness surface, not a load surface — `smoke-test-results.md` §5 says so explicitly. A2's grep would catch R-01's *signature*, but nothing generates the concurrency that would trigger it. | A concurrent client. |
| **A bind escape that happened and stopped** | A5 is point-in-time (§2, A5 caveat). | Enforcement that the CLI cannot bypass. |

## 4. The honest posture in one paragraph

Twelve deterministic checks exist, all runnable today, all with measured expected
values, all requiring no dependency and no infrastructure. Together they cover
startup, the request path, the store's integrity and the two security properties
that matter here (credential leakage, bind exposure). **What none of them does is
run on its own** — each is a command a person types, and until that person types it,
this system is unobserved. That is the single sentence that describes this project's
observability posture, and it is a direct consequence of `C-5`/`C-6` plus a
single-operator deployment: the constraint removes the machinery, and nothing else
substitutes for it. `alarms.md` §1, `slo-config.md` §4 and `tracing-config.md` §4
each arrive at the same conclusion from their own direction.