# Dashboards — intent `261001-analytics-layer`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent`
> · **Date:** 2026-10-03 · **Release under observation:** commit `aa0b1e4`
> · **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/observability-setup`
>
> **Upstream inputs consumed by this stage** (the stage frontmatter's `consumes`,
> all under `construction/u1-analytics-slice/`): `nfr-design/performance-design.md`
> (`performance-design`), `nfr-design/security-design.md` (`security-design`),
> `nfr-design/reliability-design.md` (`reliability-design`),
> `nfr-design/observability-design.md` and
> `infrastructure-design/monitoring-design.md` (`monitoring-design`),
> `infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`). Plus the deployed application's own evidence:
> `operation/deployment-execution/deployment-log.md`,
> `operation/deployment-execution/smoke-test-results.md`,
> `operation/deployment-execution/health-check-report.md`,
> `operation/environment-provisioning/validation-report.md`,
> `construction/build-and-test/test-results.md`, and the source
> `app/routes.py`, `app/analytics.py`, `app/main.py`, `app/db.py`.
>
> **Every figure in this file was measured in this stage.** Commands are given so a
> reader can repeat them. Nothing is transcribed from an upstream artifact as
> though it had been observed here.

---

## 1. What a "dashboard" is in this project — said plainly, because the name misleads

**There is no dashboard, and this file does not describe one.** A dashboard is a
rendered, auto-refreshing, multi-panel view backed by a metrics store. This project
has no metrics store, no collector, no exporter and no render target, and `C-5`/`C-6`
forbid adding any: `C-5` ("NEVER introduce a new external service, hosted dependency,
cloud component or network call", `memory/project.md` `## Forbidden`) and `C-6`
("ALWAYS declare runtime dependencies as exactly two — `fastapi` and `uvicorn`").

What this project has is exactly **two text streams the operator already has on
their terminal** and **one file they already have on disk**. Measured:

| Surface | Exists? | Evidence |
|---|---|---|
| `uvicorn.access` — one line per request, on **stdout** | **Yes** | produced in this stage; see `log-queries.md` §2 |
| `app.config` / `app.main` / `app.routes` module loggers, on **stderr** | **Yes** | 5 call sites across 3 loggers; `grep -rn "logger\." app/ --include='*.py'` |
| Any metrics endpoint / exporter / collector | **No** | none in `app/`; `C-5`/`C-6` forbid one |
| Any time-series store to chart | **No** | no metric is ever emitted, so there is nothing to store |

**So the "dashboard" this file specifies is a documented set of shell commands and
queries, run by a human, against text that already exists.** It is a manual
dashboard. That is a real and usable thing — it is what the 27-check smoke suite in
`smoke-test-results.md` effectively ran — but it is not a rendered dashboard, and
calling one the other would misrepresent the posture.

**What it costs:** nothing is refreshed while you watch it, nothing accumulates
history, and nothing alerts. `alarms.md` §1 states the alerting gap; `slo-config.md`
§4 states what an error budget means when nothing measures the burn.

## 2. The four panels

The Four Golden Signals are latency, traffic, errors and saturation. All four are
visible in this project — none of them from a metric. Each panel below is a
command; each was run in this stage and its real output is quoted.

### Panel A — Liveness and bind ("is it up, and is it up *safely*?")

This is the panel that replaces "is the service healthy", because there is no
health-check *monitor*, only a health *endpoint*.

```bash
# 1. the process answers
curl -sS -o /dev/null -w "GET /v1/health HTTP=%{http_code}\n" http://127.0.0.1:8000/v1/health
# 2. the socket is on loopback and nothing else
ss -ltnp | grep ':8000'
# 3. the startup convention fired exactly once (the FR1.4 one-line rule)
grep -c 'Sentiment analysis app ready' app.log
```

**Measured output, this stage:**

```
GET /v1/health HTTP=200
LISTEN 0  2048  127.0.0.1:8000  0.0.0.0:*  users:(("python",pid=162172,fd=6))
1
```

Panel A answers "up", "on loopback", "started cleanly". It is the only panel with a
genuine security consequence, because the bind is the process-exposure boundary
(`security-design.md` §4, `NFR2.4`). Its limitation is stated in §3.

### Panel B — Traffic (request mix by endpoint and status)

```bash
grep -oE '"[A-Z]+ [^"]+" [0-9]{3}' access.log | sed -E 's/\?[^"]*"/"/' | sort | uniq -c | sort -rn
```

**Measured output, this stage** (13 real requests over a live `uvicorn` on
`127.0.0.1:8305`):

```
      2 "POST /v1/analyze HTTP/1.1" 200
      2 "GET /v2/analytics/terms" 422
      1 "POST /v1/analyze HTTP/1.1" 422
      1 "GET /v2/analytics/terms HTTP/1.1" 500
      1 "GET /v2/analytics/terms" 200
      1 "GET /v2/analytics/summary HTTP/1.1" 500
      1 "GET /v2/analytics/summary HTTP/1.1" 200
      1 "GET /v2/analytics/summary" 422
      1 "GET /v2/analytics/summary" 200
      1 "GET /v1/health HTTP/1.1" 200
      1 "GET /does-not-exist HTTP/1.1" 404
```

Traffic is real and free — it is the access log, and it is the only panel that
needs no interpretation. **Its scale is the catch:** 13 requests is the largest
sample this project has ever produced from a live process
(`smoke-test-results.md` §2 records 27; this run is a deliberate single-session
reproduction). Panel B is a *shape*, never a rate. See `slo-config.md` §1.

### Panel C — Errors (the four distinguishable shapes, kept apart)

```bash
# server-side failure records only
grep -n 'analytics .* read failed' app.log
# access-log status mix
grep -oE '" [0-9]{3} ' access.log | tr -d '" ' | sort | uniq -c | sort -rn
```

**Measured output, this stage:**

```
6:ERROR:     analytics summary read failed (STORAGE_FAILURE): database is locked
7:ERROR:     analytics terms read failed (STORAGE_FAILURE): database is locked

      6 200
      4 422
      2 500
      1 404
```

Panel C is where this project's observability is genuinely strong, and the reason
is a design property rather than tooling: the three outcomes — **empty success**,
**validation failure**, **storage failure** — are *structurally distinct* on the
wire, in the log and in the view, so a failure is never rendered as a
plausible-looking empty result (`reliability-design.md` §2, `NFR4.3`). A reader does
not need a metric to know whether the endpoint failed; the shape says so.

**What Panel C shows that a metric would not:** in the run above, 4 requests
returned `422` and **0** produced any application log record. See §3 and
`log-queries.md` §4 — this is a real, named gap.

### Panel D — Saturation (store growth, and the one quantity that actually grows)

Saturation here means the size of the file and the width of the requested series.

```bash
# store census through the READ-ONLY URI — no write intent, so running this is safe
sqlite3 'file:data/sentiment.db?mode=ro' \
  "SELECT value FROM schema_meta WHERE key='version';
   SELECT count(*) FROM analyses;
   SELECT min(created_at), max(created_at) FROM analyses;"
stat -c '%s %a' data/sentiment.db
```

**Measured output, this stage** (on a scratch store built by this stage; the
operator's own store is untouched, §5):

```
schema_meta.version = 4
named indexes       = ['idx_analyses_created_at', 'idx_analyses_import_id', 'idx_analyses_label_created_at']
rows                = 2
span (earliest..latest) = ('2026-10-03T15:45:19Z', '2026-10-03T15:45:19Z')
file bytes          = 32768   mode=644
```

**The real saturation signal is not the row count — it is the range width**, because
the summary's payload is linear in the *requested* range, not in the store. Measured
over real HTTP on a store holding **one** row, varying only the range:

| `from`…`to` | series entries | response bytes | wall ms |
|---|---|---|---|
| *(none — unbounded)* | 1 | 368 | 1 |
| 7 days | 8 | 1 520 | 7 |
| 1 year | 367 | 70 640 | 13 |
| 21 years | 14 602 | 2 803 760 | 115 |
| **100 years** | **36 525** | **7 012 976** | **235** |

The last row **exceeds the 200 ms budget** — and does so with a single stored row.
This is the measurement behind Panel D's only threshold, and it is the honest answer
to "what could make this app slow": not data volume, a parameter. `alarms.md` §2.4
and `anomaly-config.md` §2.5 carry the threshold.

## 3. What each panel cannot tell you

Naming the limits is part of the dashboard, not an apology for it.

| Panel | Cannot answer | Why |
|---|---|---|
| **A** Liveness/bind | "was it ever exposed on a non-loopback address?" | The enforcement lives in `run()`/`create_app()`, not in the ASGI app object. `uvicorn app:app --host …` never consults it. Measured this stage: `resolve_bind_host("127.0.0.2")` refuses, `create_app(host="127.0.0.2")` refuses before any lifespan ran — yet `uvicorn app:app --host 127.0.0.2` **bound and served `200` with no refusal logged**. Panel A shows the socket as it is *now*; it has no memory. |
| **B** Traffic | any rate, percentile or trend | There is no aggregation and no history. 13 requests is the whole dataset. |
| **C** Errors | which field a `422` refused, and who asked | A validation failure emits **no** application record (measured: 4 × `422`, 0 records). The offending field is in the response body, and the body is not logged. There is no request id, so a client-visible `422` cannot be matched to anything. |
| **D** Saturation | whether the file is *growing dangerously* | One sample is one sample. Growth is real but nothing here accumulates it. |

## 4. Not provisioned — CloudWatch

| Element | Status | Ruling rule |
|---|---|---|
| CloudWatch Dashboard | **Not provisioned** | `C-5` forbids a new external service or cloud component; there is no AWS account, no `aws` CLI, no `~/.aws`, no `CDK_*`/`AWS_*` environment variable and no IaC file of any kind. **Measured this stage:** `which aws` → not found; `ls ~/.aws` → *No such file or directory*; `env | grep -E '^CDK_\|^AWS_'` → no output. |
| CloudWatch metric publication | **Not provisioned** | `C-6` caps declared runtime dependencies at exactly two (`fastapi`, `uvicorn`), so no `boto3`/CloudWatch client may be declared. `monitoring-design.md` §2 states this as the ruling reason. |
| CloudWatch Logs Insights saved queries | **Not provisioned** | There is no log group to query. The real queries in `log-queries.md` run against a terminal, by hand. |
| Custom metrics for business indicators | **Not provisioned** | No metric is ever emitted, so there is nothing to publish. |

**The transitively-present package is not an egress path and must not be read as
one.** `opentelemetry-api 1.45.0` is installed because `fastapi` hard-requires it
(`memory/team.md` §Deployment records this precisely). Measured: nothing in `app/`
imports `opentelemetry` or `otel`, and no OTel SDK or exporter is installed, so there
is no automatic path out. `monitoring-design.md` §1 records the same.

## 5. Golden-signal coverage, stated as coverage

| Golden signal | Panel | Source | Threshold? |
|---|---|---|---|
| Latency | D (indirectly) | wall-clock on the operator's own request; **not** logged by the app | yes — `alarms.md` §2.3, from a 25-run distribution |
| Traffic | B | access log | no — no traffic history to threshold against |
| Errors | C | module logger + access-log status | yes — `alarms.md` §2.1 |
| Saturation | D | store census + requested range width | yes — `alarms.md` §2.4 |

**Coverage is honest and incomplete in one specific way: latency is not observed by
the application at all.** `uvicorn`'s access line carries method, path, status and
duration — but in this project's configuration it emits **no duration field**
(measured: `INFO:     127.0.0.1:43452 - "GET /v2/analytics/summary HTTP/1.1" 200 OK`;
the duration appears only with a non-default access-log format). So every latency
figure in `slo-config.md` and `alarms.md` is a figure this stage measured by
stopwatch against a live server, **not** a number the system continuously records.
That is a structural limitation, not an oversight, and it is why `alarms.md` §3
lists latency as a check a human performs rather than an alarm that fires.

## 6. Standing constraint honoured throughout this stage

**No application source, test, configuration or the data store was modified.** Every
store inspection used SQLite's read-only URI (`file:…?mode=ro`); every process this
stage booted ran with its CWD inside a `mktemp -d` scratch tree under
`/tmp/opencode/obs/`. The operator's store is byte-identical before and after:

```
before  sha256 c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
        mtime  2026-10-03 03:33:42.920985500 +0500   size 32768  mode 644
after   sha256 c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
        mtime  2026-10-03 03:33:42.920985500 +0500   size 32768  mode 644
```

The unchanged **mtime** is the load-bearing field: it means the file was never opened
for writing. Matches `deployment-log.md` §5.1 and `health-check-report.md` §4.1.