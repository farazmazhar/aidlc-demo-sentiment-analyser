# Log Queries — intent `261004-analytics-view-packaging`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent` ·
> **Date:** 2026-10-04 · **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/observability-setup`

## 1. The two log streams

There is no log sink, no formatter and no retention tier — a session's log exists only
if the operator redirects one (`… uvicorn app:app > access.log 2> error.log`). The two
streams are:

| Stream | Source | Carries |
|---|---|---|
| **stdout** | `uvicorn`'s access logger | one line per request: client, method, path+query, status |
| **stderr** | `uvicorn.error` + the application's module loggers | startup/shutdown, the one startup mode line, and any application `logger.error(...)` |

Application loggers exist in three modules: `app.routes`, `app.main`, `app.config`.
The read layer (`app/analytics.py`) has **no logger** — a storage failure is logged one
layer out, in `app.routes`, by the handler that catches `sqlite3.Error`.

## 2. Application log call sites

| Where | Level | Emits |
|---|---|---|
| `app/main.py` lifespan | INFO | one startup line naming the resolved mode |
| `app/routes.py` (storage branch) | ERROR | the `STORAGE_FAILURE` record (`logger.error`, `str(exc)` only — no stack trace) |
| `app/config.py` | WARNING | the "live intended, no key" warning naming the config file, never the key |

## 3. Query patterns (shell `grep`, since there is no Logs Insights)

```bash
# requests that failed
grep -E '" (4|5)[0-9][0-9]' access.log

# storage failures (the only application error the read path emits)
grep -F 'STORAGE_FAILURE' error.log

# startup mode
grep -F 'offline mode' error.log

# the config warning (never contains the key)
grep -F 'config.local.toml' error.log
```

These are the four operational questions worth asking of the logs: what failed, why did
a read fail, what mode am I in, and is a key misconfigured.

## 4. What the logs do **not** carry — recorded, not normalised away

1. **A `422` produces no application log record.** Measured in the prior intent on a
   live capture: four requests returned `422` and `grep -c VALIDATION_FAILED error.log`
   was `0`. Only the storage branch logs. The access log still shows the `422`, so the
   failure is not invisible — it is just not in the application stream. Closing it is a
   code change and a decision (`observability-setup-questions.md` OQ-2).
2. **The storage record carries no stack trace** — the shipped calls are
   `logger.error(...)`, not `logger.exception(...)`. The machine code is present (which
   is what makes the failure distinguishable); the stack is not.
3. **No duration field** in the access line, so latency is not derivable from logs
   (`alarms.md` §2.1).
4. **No correlation/request id.** There is no multi-service boundary to correlate
   across, so none is introduced (`tracing-config.md` §1).

## 5. This release's own log evidence

The cutover and smoke run produced the expected lines: the startup mode line
(`Sentiment analysis app ready in offline mode …`), `200` access lines for `/`,
`/v1/health`, `/v2/analytics/summary`, `/v2/analytics/terms`, `422` access lines for the
malformed analytics requests, and a clean shutdown sequence. No unexpected application
`ERROR` line appeared. The view change itself adds **no** log line — it is client-side.
