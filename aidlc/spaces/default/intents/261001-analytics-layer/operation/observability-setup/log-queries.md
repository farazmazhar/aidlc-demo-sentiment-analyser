# Log Queries — intent `261001-analytics-layer`

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
> **Every format and every output below was produced by running this project's code
> in this stage.** Nothing here is a plausible-looking template. Where a query was
> run, its real output is quoted.

---

## 1. There are exactly two log streams, and here is who writes each

Measured this stage by running a real `uvicorn` process with a logging configuration
that names the originating logger on every line. That is the only way to attribute a
line to a logger rather than guess from its text, and it settled two things a
code-read would have left open.

```
WHO[uvicorn.error|INFO]  Started server process [178553]
WHO[uvicorn.error|INFO]  Waiting for application startup.
WHO[app.main|INFO]       Sentiment analysis app ready in offline mode (OpenRouter not connected)
WHO[uvicorn.error|INFO]  Application startup complete.
WHO[uvicorn.error|INFO]  Uvicorn running on http://127.0.0.1:8309 (Press CTRL+C to quit)
WHO[uvicorn.access|INFO] 127.0.0.1:40954 - "GET /v1/health HTTP/1.1" 200
WHO[uvicorn.access|INFO] 127.0.0.1:40966 - "GET /v2/analytics/summary?from=not-a-date HTTP/1.1" 422
WHO[app.routes|ERROR]    analytics summary read failed (STORAGE_FAILURE): database is locked
WHO[uvicorn.access|INFO] 127.0.0.1:51092 - "GET /v2/analytics/summary HTTP/1.1" 500
WHO[uvicorn.error|INFO]  Shutting down
```

| Stream | Logger(s) | Carries | Default destination |
|---|---|---|---|
| **Access log** | `uvicorn.access` | one line per request: client, method, path, query string, status | **stdout** |
| **Application log** | `app.config`, `app.main`, `app.routes` | the startup mode line, the credential warning, the analytics storage-failure record, the OAuth-failure warning | **stderr** |
| **Server lifecycle** | `uvicorn.error` | process start, lifespan enter/exit, shutdown, **and the whole startup-failure traceback** | **stderr** |

**The application log is configured by the app itself, once.** `app/main.py:96-103`,
`_configure_logging()`, sets `format="%(levelname)s:     %(message)s"` — five spaces
after the colon — *only* if the root logger has no handlers. `app/main.py:103` is the
one uncovered line in the whole application (98 % coverage on `app/main.py`).

### 1.1 The complete census of application log call sites — 5, in 3 modules

```
$ grep -rn "logger\.\(error\|warning\|info\|exception\)" app/ --include='*.py' | wc -l
5
$ grep -rn "getLogger" app/ --include='*.py'
app/config.py:44:logger = logging.getLogger("app.config")
app/main.py:53:logger = logging.getLogger("app.main")
app/routes.py:88:logger = logging.getLogger("app.routes")
```

| # | Site | Level | Message template |
|---|---|---|---|
| 1 | `app/config.py:140` | `WARNING` | `mode = 'openrouter' was requested but no API key is available; running the offline engine. Put your key in %s or connect from the page.` |
| 2 | `app/main.py:136` | `INFO` | `Sentiment analysis app ready in %s mode%s` |
| 3 | `app/routes.py:364` | `ERROR` | `analytics summary read failed (%s): %s` |
| 4 | `app/routes.py:398` | `ERROR` | `analytics terms read failed (%s): %s` |
| 5 | `app/routes.py:439` | `WARNING` | `OpenRouter authorization failed: %s` |

### 1.2 Two corrections to the record, both measured

**(a) `app/analytics.py` logs nothing at all.** Some upstream prose attributes the
analytics failure logging to both `app/routes.py` **and** `app/analytics.py`.
Measured: `grep -c logging app/analytics.py` → **0**. There is no logger in the read
module and no `import logging` in it. The analytics failure is logged one layer out,
in the route handler that catches `sqlite3.Error` and builds the envelope. The
*requirement* (`NFR8.1`) is satisfied; the *location* differs from what the prose
implies. Stated so a later reader does not go looking for a logger that is not there.

**(b) The record carries no stack trace.** The shipped calls are
`logger.error(...)`, not `logger.exception(...)`. `observability-design.md` §2 and
`monitoring-design.md` §3.1 both describe the record as an "`exception(...)` record
carrying the code **and stack**". Measured: the failure is a **single line** holding
only `str(exc)`. The code (which is what makes `NFR8.2` work) is present; the stack
is not. A defect report loses the frames — which is why §2's queries below lean on the
access log's status line rather than on the application record for diagnosis.

## 2. The exact formats, as produced

### 2.1 Application log (stderr) — verbatim capture of a live storage failure

Produced by holding a `BEGIN EXCLUSIVE` lock from a second process against a running
server, so the read path raised a **genuine** `sqlite3.Error`:

```
INFO:     Started server process [177766]
INFO:     Waiting for application startup.
INFO:     Sentiment analysis app ready in offline mode (OpenRouter not connected)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8305 (Press CTRL+C to quit)
ERROR:     analytics summary read failed (STORAGE_FAILURE): database is locked
ERROR:     analytics terms read failed (STORAGE_FAILURE): database is locked
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [177766]
```

**The analytics failure record, in full, is:**

```
ERROR:     analytics <summary|terms> read failed (STORAGE_FAILURE): <str(exc)>
```

Note the five spaces — that is `_configure_logging`'s `format`, not uvicorn's.

### 2.2 Access log (stdout) — verbatim capture of the same 13 requests

```
INFO:     127.0.0.1:43422 - "GET /v1/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:43426 - "POST /v1/analyze HTTP/1.1" 200 OK
INFO:     127.0.0.1:43442 - "POST /v1/analyze HTTP/1.1" 200 OK
INFO:     127.0.0.1:43452 - "GET /v2/analytics/summary HTTP/1.1" 200 OK
INFO:     127.0.0.1:43460 - "GET /v2/analytics/terms?limit=5 HTTP/1.1" 200 OK
INFO:     127.0.0.1:43476 - "GET /v2/analytics/summary?from=not-a-date HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:43480 - "GET /v2/analytics/terms?from=2026-01-02&to=2026-01-01 HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:43492 - "GET /v2/analytics/terms?limit=0 HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:43502 - "POST /v1/analyze HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:43506 - "GET /does-not-exist HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:43510 - "GET /v2/analytics/summary?from=2000-01-01&to=2099-12-31 HTTP/1.1" 200 OK
INFO:     127.0.0.1:43512 - "GET /v2/analytics/summary HTTP/1.1" 500 Internal Server Error
INFO:     127.0.0.1:35322 - "GET /v2/analytics/terms HTTP/1.1" 500 Internal Server Error
```

Format: `INFO:     <client_ip>:<port> - "<METHOD> <path[?query]> HTTP/1.1" <status> <reason>`.
**No duration field is emitted** in this configuration — load-bearing for every
latency claim in this stage (`slo-config.md` §1).

### 2.3 The startup-failure record (stderr) — the loudest signal in the system

```
INFO:     Started server process [176838]
INFO:     Waiting for application startup.
ERROR:    Traceback (most recent call last):
  ... 20 frames ...
  File ".../app/db.py", line 336, in _rebuild_analyses
    connection.execute(_COPY_ROWS_INTO_V1_TABLE, (UNKNOWN_PROVIDER,))
sqlite3.IntegrityError: CHECK constraint failed: label IN ('positive','negative','neutral')

ERROR:    Application startup failed. Exiting.
```

Produced by booting against a store holding a row the v1 rebuild cannot preserve.
Process **exit status 3**; **the port never opened** (`connection refused`). The
store was read back afterwards and still held `version=3` with the offending row —
the rollback held (`BR5.5`).

**Note the attribution:** with the named-logger configuration this traceback comes
from **`uvicorn.error`**, not from any `app.*` logger — measured: **0** `app.*`
records during a failed startup. `init_db` re-raises, and nothing in `app/` catches
it to log it in its own voice. **An operator grepping the application loggers for
`app.` finds nothing about a failed startup.** The signal is loud and unmistakable,
but it is a framework record. This is a real gap, named in §4.

## 3. The queries — each one run, each with its real output

All run against the 13-request capture in §2.2 and the stderr capture in §2.1.

**Q1 — did the process start cleanly, and exactly once?** (The `FR1.4` one-line rule.)

```bash
$ grep -c 'Sentiment analysis app ready' app.log
1
```

**Q2 — server-side analytics failures. This is the `NFR8.1`/`NFR8.2` signal.**

```bash
$ grep -n 'analytics .* read failed' app.log
6:ERROR:     analytics summary read failed (STORAGE_FAILURE): database is locked
7:ERROR:     analytics terms read failed (STORAGE_FAILURE): database is locked
```

**Q3 — status-code distribution.**

```bash
$ grep -oE '" [0-9]{3} ' access.log | tr -d '" ' | sort | uniq -c | sort -rn
      6 200
      4 422
      2 500
      1 404
```

**Q4 — user-impacting failures only (5xx on the analytics surface).**

```bash
$ grep -E '" 5[0-9]{2} ' access.log | grep '/v2/analytics' \
    | sed -E 's/.*"([A-Z]+ [^"]+)" ([0-9]{3}).*/\1 -> \2/'
GET /v2/analytics/summary HTTP/1.1 -> 500
GET /v2/analytics/terms HTTP/1.1 -> 500
```

**Q5 — request mix by endpoint, query string stripped.**

```bash
$ grep -oE '"[A-Z]+ [^"]+" [0-9]{3}' access.log | sed -E 's/\?[^"]*"/"/' | sort | uniq -c | sort -rn
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

**Q6 — a refused request, recovered from the query string alone.** The message is not
logged, but the offending parameter is in the URL:

```bash
$ grep -oE 'from=[0-9]{4}-[0-9]{2}-[0-9]{2}&to=[0-9]{4}-[0-9]{2}-[0-9]{2}' access.log \
  | while read -r q; do
      f=${q#from=}; f=${f%%&to=*}; t=${q##*to=}
      echo "  $q -> $(( ( $(date -d "$t" +%s) - $(date -d "$f" +%s) ) / 86400 + 1 )) days of series"
    done
  from=2026-01-02&to=2026-01-01 -> 0 days of series
  from=2000-01-01&to=2099-12-31 -> 36525 days of series
```

The second line is the saturation signal from `alarms.md` §2.4, recoverable from the
log alone.

**Q7 — store census, through the read-only URI so the check cannot mutate anything.**

```bash
$ sqlite3 'file:data/sentiment.db?mode=ro' \
    "SELECT value FROM schema_meta WHERE key='version';
     SELECT count(*) FROM analyses;
     SELECT min(created_at), max(created_at) FROM analyses;"
$ stat -c '%s %a' data/sentiment.db
```
```
4
2
2026-10-03T15:45:19Z|2026-10-03T15:45:19Z
32768 644
```

**Q8 — did the read path write anything?** The strongest single check available, and
free:

```bash
$ sha256sum data/sentiment.db; stat -c '%y' data/sentiment.db
c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39  data/sentiment.db
2026-10-03 03:33:42.920985500 +0500
```

An unchanged **mtime** is stronger than an unchanged hash: it means the file was
never opened for writing at all.

**Q9 — is the bind loopback?** (`alarms.md` §2.5.)

```bash
$ ss -ltnp | grep ':8000'
LISTEN 0  2048  127.0.0.1:8000  0.0.0.0:*  users:(("python",pid=162172,fd=6))
```

**Q10 — did startup succeed?** The inverse of §2.3.

```bash
$ grep -cE 'IntegrityError|Application startup failed' app.log     # want: 0
$ ss -ltn | grep ':8000'                                           # want: a listener
```

## 4. What the logs cannot tell you — the four real limits

These are properties of the logging design, not omissions from the query set.

**(a) A validation failure produces no application record at all.** Measured on the
capture above: **4 requests returned `422`; `grep -c VALIDATION_FAILED app.log` → 0.**
`app/routes.py` logs only the storage failure; the `RangeError` branch returns the
envelope silently. So of the two codes `NFR8.2` names — `VALIDATION_FAILED` **and**
`STORAGE_FAILURE` — only `STORAGE_FAILURE` appears in the application log.
`VALIDATION_FAILED` is observable *only* as a `422` on the access log and in the
response body. The stored verdict for `NFR8.2` (`test-results.md` §5) rests on
`::test_a_storage_failure_is_logged_through_the_module_logger_with_its_code`, which
exercises the storage path only — so the verdict is sound for what it tested and the
requirement's wording is broader than the coverage. **Named, not papered over.**

**(b) There is no request id, so a client-visible failure cannot be correlated to a
log line.** No `X-Request-ID` is generated, propagated, or logged; the client IP and
ephemeral port are the only correlator, and with one operator those are not unique
per logical action. The machine code is the intended correlator (`NFR8.2`) and it
works for the storage case only.

**(c) The failure record carries no stack.** §1.2(b). `logger.error`, not
`logger.exception`.

**(d) A failed startup is not in the application log.** §2.3 — it comes from
`uvicorn.error`, and **0** `app.*` records are emitted.

### 4.1 What is deliberately *not* claimed

- **No retention, no aggregation, no shipping.** There is no log file unless the
  operator redirects one; no log group, no rotation, no archive. `monitoring-design.md`
  §1 records this as empty by decision, and `BR2.15` forbids adding a configuration
  value for it. A session's log lives or dies with its terminal.
- **No redaction layer is needed, and this is a measured property rather than a
  hope.** No log record contains a credential: the log templates above interpolate
  only a mode string, a code, an exception's `str()`, a path, and an OAuth exception —
  and `NFR8.3` is enforced by asserting `sk-or-v1` and `SELECT` never appear.
  Measured independently this stage: `grep -c "print(" app/ --include='*.py'` → **0**,
  and the credential-redaction assertion `tests/test_config.py::test_the_key_is_never_rendered_or_logged`
  passes.
- **The instrument has teeth.** Verified on a scratch **copy** (the repository was
  not modified): deleting the two `logger.error` calls and re-running
  `test_a_storage_failure_is_logged_through_the_module_logger_with_its_code` fails
  with `AssertionError: the storage failure was swallowed rather than logged`. Note
  the response assertions *passed* in that run — the `500 STORAGE_FAILURE` was still
  returned — so **the log is the only thing that distinguishes "logged" from
  "swallowed"**. That is the value of this single log call, stated concretely.