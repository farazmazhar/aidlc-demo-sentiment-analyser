# Alarms — intent `261004-analytics-view-packaging`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent` ·
> **Date:** 2026-10-04 · **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/observability-setup`

## 1. No alarm can fire, and that is the honest starting point

An alarm needs three things: a metric to evaluate, a schedule that evaluates it, and a
notification channel. This project has **none of the three**. There is no metric
emission (`C-4`/`C-5`; the runtime cap), no scheduler (the app runs only when started),
and no channel (no SNS, no second recipient — one operator). So the stage's "CloudWatch
alarm definitions" output is **inapplicable per element**, and what this file records is
the set of **thresholds an operator can check by hand**, each derived from a measurement,
with its severity.

## 2. The thresholds that matter, and where each number comes from

### 2.1 Read-path latency — **200 ms**
The budget pinned in `tests/test_analytics_read.py` (`BUDGET_MS = 200`). The measured
distribution over the pinned fixture (inherited: `summary` max 20.53 ms, `terms` max
59.28 ms) sits well inside it. A manual check is `pytest tests/test_analytics_read.py`.

### 2.2 Availability — **zero unexpected 5xx**
The app's `500` is `STORAGE_FAILURE` (a genuine store read failure). The gate is the
**count**: zero unexpected `5xx` in a verification window. A manual check is the smoke
suite (`smoke-test-results.md`).

### 2.3 Startup failure — **the port never opens**
The distinctive signature. `init_db` runs in the lifespan before the server accepts
anything; a failed migration exits non-zero and the port never binds. An operator sees
"connection refused", not a `500`. See `rollback-runbook.md` RB1.

### 2.4 Slow request — **the requested range width**
Measured (inherited): a 100-year `from`/`to` range returns ~7 MB / 36,525 zero-filled
series entries in ~235 ms — over the 200 ms budget — with a *single* stored row. The
cost is the range width, not the data volume. Recorded as an operator-relevant property
(`anomaly-config.md` §2-A6).

### 2.5 Loopback bind — **exactly one listener on `127.0.0.1`**
Check with `ss -ltnp | grep 8000`. The `uvicorn --host` CLI shape bypasses the
enforcement (§3).

### 2.6 Store write-neutrality — **sha256 and mtime unchanged**
A read session must not open the store for writing. Check `sha256sum`/`stat` before and
after.

## 3. The one live gap in the enforced bind

**Measured:** `resolve_bind_host` refuses four non-loopback hosts including the near-miss
`127.0.0.2`, but the `uvicorn app:app --host 127.0.0.2` CLI shape **binds and serves
`200`** with no refusal logged, because the application object is constructed at module
scope with the default. The enforced bind holds on the documented run path
(`app.main:run`) and on `--host 127.0.0.1`; a hand-typed non-loopback flag overrides it.

**Interim mitigation:** omit `--host`, or pass a loopback value. Closing the gap is a
code change and a scope decision (`observability-setup-questions.md` OQ-3).

## 4. Thresholds deliberately absent, with reasons

| Absent threshold | Why |
|---|---|
| Error-**rate** alarm | Not computable: a rate over a handful of requests quantises to large steps. The **count** is used. |
| CPU / memory / disk alarm | No host agent; one local process. |
| Canary / synthetic alarm | No Synthetics; the operator's smoke run is the substitute. |
| SLO burn-rate alarm | Needs a continuously computed SLI over a rolling window; neither exists. |
| Availability-uptime alarm | No continuous measurement window; the app runs on demand. |

## 5. Severity as a mapping, not a rotation

`incident-response-guide.md`'s severity matrix presupposes an on-call team this project
does not have. Restated for one operator:

| Severity | Here it means | Response |
|---|---|---|
| **SEV1** | The app cannot start (port never opens) or the store is unreadable | follow `rollback-runbook.md` RB1/RB3 |
| **SEV2** | A read path returns `500 STORAGE_FAILURE` or a wrong aggregate | stop, diagnose, roll back the code (RB2) |
| **SEV3** | A slow/oversized response (wide range) | narrow the range; the contract is uncapped by design |
| **SEV4** | Cosmetic page issue | next session |

There is no notification channel and no second responder; the "escalation path" is the
operator's own runbook. Recorded rather than implied.
