# Runbooks — intent `261001-analytics-layer`

> **Stage:** `incident-response` (operation) · lead `aidlc-operations-agent`
> · **Date:** 2026-10-03 · **Release under observation:** commit `aa0b1e4`
> · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/incident-response`
>
> **Upstream inputs consumed by this stage** (the stage frontmatter's `consumes`,
> plus the deployed evidence this stage depends on):
> `operation/observability-setup/dashboards.md` (`dashboards`),
> `operation/observability-setup/alarms.md` (`alarms`),
> `operation/observability-setup/anomaly-config.md`, `log-queries.md`,
> `slo-config.md`, `observability-setup-questions.md`;
> `construction/u1-analytics-slice/nfr-design/reliability-design.md`
> (`reliability-design`) and `security-design.md` (`security-design`);
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`);
> `operation/deployment-pipeline/rollback-runbook.md` (RB1/RB2/RB3);
> `operation/environment-provisioning/validation-report.md` (F-01…F-04);
> `operation/deployment-execution/health-check-report.md` (§2.3, §3.2, §4.1);
> `memory/team.md` § Deployment, § Code Style; `memory/project.md`
> `## Forbidden` (`C-5`), `## Mandated` (`C-6`, `C-1`, `C-10`), and
> `memory/phases/operation.md` § Incident Response.
>
> **Every log line, status code, exit code, hash and duration quoted below was
> produced in this stage**, against scratch stores under `/tmp/opencode/ir/`.
> Where a claim is *inherited* rather than re-measured it says so and names the
> artifact it came from. The operator's real store was never a target:
> `data/sentiment.db` is byte-identical before and after this stage, down to the
> mtime.

---

## 1. Read this before using any runbook below

Three facts govern everything in this file, and all three are measured.

1. **Nothing pages.** There is no pager, no SNS topic, no webhook, no chat
   integration, no monitor and no scheduler. `alarms.md` §1 records this and
   names the four missing ingredients (a metric, a rule engine, a notification
   channel, a schedule). **Every "detection" in this file is a command a person
   types.** An operator who is asleep is not an operator who has been paged.
2. **Two log streams, and they do not agree on coverage.** The access line is on
   **stdout**, the application log is on **stderr** (`log-queries.md` §1). A
   failure of the application is on stderr; a request is on stdout. Redirecting
   one into `app.log` and not the other is the single most likely way to read a
   healthy-looking run during a real incident.
3. **The store is the only thing here that can be lost.** One gitignored file,
   one process, one operator. `infrastructure-specification.md` §5 records that
   backup, replication, failover and HA are **not provisioned**, with the reason
   per line. §7 of this file is what that means when it goes wrong.

---

## 2. The failure-mode index

Each row is a symptom this project's code can actually produce, a check that
detects it, and the runbook that handles it. Every symptom below was reproduced
in this stage.

| ID | Failure mode | Wire | Detected by | Severity | Runbook |
|---|---|---|---|---|---|
| **IR-1** | Analytics read fails: another process holds the store | `500` `STORAGE_FAILURE`, after **5.0 s** | `grep 'analytics .* read failed'` | SEV2 | §3 |
| **IR-2** | A refused request: bad date, inverted range, `limit` < 1, wrong body shape | `422` `VALIDATION_FAILED` | access log only — **no application record exists** | SEV4 | §4 |
| **IR-3** | Empty or whitespace-only text submitted | `422` `INVALID_TEXT` | access log only — **no application record exists** | SEV4 | §4 |
| **IR-4** | The startup migration cannot preserve a row | process **exits 3**, **port never opens** | `grep 'IntegrityError'` + `ss -ltn` | SEV1 | §5 (RB1) |
| **IR-5** | The app is reachable off loopback | `200` on a non-loopback address | `ss -ltnp \| grep ':8000'` | SEV1 | §6 |
| **IR-6** | The run command the artifacts name does not serve | no listener, process exits at once | `ss -ltn \| grep ':8000'` | SEV3 | §7 |
| **IR-7** | A very wide requested range breaches the latency budget | `200`, **~7 MB / 36 525 entries / ~240 ms** | `curl -w '%{size_download} %{time_total}'` | SEV3 | §8 |
| **IR-8** | The store is damaged, truncated or gone | app starts, **history is empty** | `sqlite3 … '?mode=ro'` census | SEV1 | §9 (RB3) |
| **IR-9** | The store's schema is behind `SCHEMA_VERSION` | boots and writes the store | read-only version query | SEV3→SEV2 | §10 |
| **IR-10** | Credential material in a log | — | `grep -cE 'sk-or-v1\|AKIA\|…'` | SEV1 | §11 |
| **IR-11** | A `422` and an empty result are confused for one another | `422` vs `200`/`total:0` | response body shape | SEV3 | §12 |

---

## 3. IR-1 — the analytics read fails because another process holds the store

### Symptom, as it actually appears

Measured in this stage: real `uvicorn`, real store with one row, and a second
process holding `BEGIN EXCLUSIVE` on that store for 20 s.

```
$ curl -sS -m 30 -o /dev/null -w 'HTTP=%{http_code} wall=%{time_total}s\n' \
    'http://127.0.0.1:8344/v2/analytics/summary'
  req1 summary -> HTTP=500 wall=5.018122s
  req2 summary -> HTTP=500 wall=5.005439s
  req3 summary -> HTTP=500 wall=5.005064s
  health -> HTTP=200 wall=0.001352s
```

The response body, verbatim:

```
{"code":"STORAGE_FAILURE","message":"The analytics store could not answer the request."}
```

The **stderr** line, in uvicorn's own default format — this is byte-for-byte
what the operator sees, five spaces and all:

```
ERROR:     analytics summary read failed (STORAGE_FAILURE): database is locked
```

and the matching **stdout** access line:

```
INFO:     127.0.0.1:36326 - "GET /v2/analytics/summary HTTP/1.1" 500 Internal Server Error
```

Three details in that measurement that change what an operator should do:

- **Each failing request costs 5.0 s, not milliseconds.** `app/db.py:213` opens the
  connection with `sqlite3.connect(path, check_same_thread=False)` and sets no
  `busy_timeout`, so the CPython default of 5.0 s applies. Measured directly:
  attempt 1 → `OperationalError: database is locked` after **5005.26 ms**;
  attempt 2 → **OK in 2630.48 ms** (succeeded once the holder released);
  attempts 3–5 → **OK in ~0.1 ms**.
- **`/v1/health` is unaffected** — 200 in **1.4 ms** while every analytics read
  was failing. The health endpoint does not touch the store, so **a health check
  cannot detect this failure.** This is worth knowing before trusting a green
  health line during a read-path incident.
- **The record carries no stack.** `app/routes.py:364` and `:398` call
  `logger.error(...)`, not `logger.exception(...)`, so the single line holds
  `str(exc)` and nothing else. `security-design.md` §3.4 is satisfied (no stack
  leaks to the *client*); the cost is that the frames are gone from the
  operator's side too.

### The check that detects it

```bash
grep -n 'analytics .* read failed' app.log      # want: no output
grep -cE '" 5[0-9]{2}' access.log               # want: 0
```

This is `alarms.md` §2.1 and §2.2 verbatim, and `dashboards.md` Panel C. Both are
**manual** checks — `alarms.md` §3 records every signal in this file as
`manual`, and §1 explains why in one line: nothing evaluates them.

### Steps

1. **Confirm it is a lock, not a broken store.** A read failure and a corrupt
   store look the same on the wire. Open the store **read-only** — the URI means
   the check itself has no write intent:
   ```bash
   sqlite3 'file:data/sentiment.db?mode=ro' \
     "SELECT 'version='||value FROM schema_meta WHERE key='version';
      SELECT 'rows='||count(*) FROM analyses;
      SELECT 'integrity='||* FROM pragma_integrity_check;"
   ```
   A store under someone else's exclusive lock **also** answers `database is
   locked` here. If this query fails the same way, the store is not corrupt — it
   is contended, and step 2 is the fix.
2. **Find the other process.** In this project the contenders are narrow, and
   they are the operator's own:
   ```bash
   pgrep -af 'uvicorn|python'
   ls -la data/            # a second .db, a -journal or -wal file, an editor lock
   ```
   Measured contenders, all real: an `sqlite3` shell left open on the store; a
   second `uvicorn` (two processes on one file); a test run against
   `data/sentiment.db` instead of a temporary path.
3. **Release it.** Stop the other process. There is nothing to restart in *this*
   process.
4. **Confirm recovery without restarting.** Re-issue the request:
   ```bash
   curl -sS -o /dev/null -w '%{http_code} %{time_total}\n' \
     'http://127.0.0.1:8000/v2/analytics/summary'
   ```
   Expect `200` in a few milliseconds. **Measured: the failure is transient and
   self-clearing** — a retry succeeded 2.63 s later while the holder was still
   exiting, and instant thereafter. **Do not restart the app for this.** A
   restart costs the migration step and loses nothing else, but it fixes nothing
   that waiting does not.
5. **If it does not clear**, treat it as IR-8 (§9) and stop.

### What is not recoverable

**Nothing**, and that is the point: this failure mode costs **no data**. It is
also the only failure mode in this file whose cost is dominated by *latency*
rather than by correctness — 5 s per request against a 200 ms budget
(`tests/test_analytics_read.py:34`), a 25× breach, with nothing in the access
log to show it because **the access line carries no duration field**
(`dashboards.md` §5, `log-queries.md` §2.2).

---

## 4. IR-2 and IR-3 — the two `422`s, and why they are an observability gap

### Symptoms, as they actually appear

Measured, this stage, over real HTTP. All five are verbatim:

```
{"code":"VALIDATION_FAILED","message":"query.from: expected a UTC calendar date written YYYY-MM-DD."}
{"code":"VALIDATION_FAILED","message":"query.from and query.to: 'from' must not be a later UTC day than 'to'."}
{"code":"VALIDATION_FAILED","message":"query.limit: Input should be greater than or equal to 1"}
{"code":"VALIDATION_FAILED","message":"body: Input should be a dictionary or an instance of AnalyzeRequest"}
{"code":"INVALID_TEXT","message":"Text to analyse must not be empty or whitespace-only."}
```

The first three come from `/v2/analytics/*`; the fourth from `POST /v1/analyze`
sent as `text/plain`; the fifth from `POST /v1/analyze` with
`{"text":"   "}` or `{"text":""}`.

### The check that detects it — and the gap that makes it a runbook at all

```bash
grep -cE '" 422' access.log                  # want: 0 in normal use
grep -c 'VALIDATION_FAILED\|INVALID_TEXT' app.log   # measured: 0, always
```

**Measured: in a run that returned six `422`s, the application log contained zero
records for them.** The full application-record list from that run was three
lines — one startup line and two storage failures:

```
WHO[app.main|INFO]  Sentiment analysis app ready in offline mode (OpenRouter not connected)
WHO[app.routes|ERROR]  analytics summary read failed (STORAGE_FAILURE): database is locked
WHO[app.routes|ERROR]  analytics terms read failed (STORAGE_FAILURE): database is locked
```

`app/routes.py` logs the storage branch only; the `RangeError` branch at `:359`
and `:393` and the shared handler at `:470`/`:475` return the envelope silently.
`NFR8.2` names both codes; only `STORAGE_FAILURE` reaches the log. This is
recorded as a gap, not a defect fixed here: it needs a code change **and** a
decision about whether a mistyped date is worth a log line, which is
`observability-setup-questions.md` **OQ-2** and not an operations decision.

**Operational consequence:** a `422` is diagnosable **only** from the access
line and the URL. There is no application record, and there is no request id
(`log-queries.md` §4(b)), so a client-visible refusal cannot be correlated to
anything beyond the query string — which does carry the offending parameters:

```
INFO:     127.0.0.1:60646 - "GET /v2/analytics/summary?from=not-a-date HTTP/1.1" 422
```

### Steps

1. Read the message. It names the field (`query.from`, `body`) or both bounds.
2. Fix the request. **Nothing is wrong with the app or the store** — this is the
   contracted behaviour: `reliability-design.md` §2.2 keeps validation, storage
   failure and empty success as three structurally distinct shapes so a refusal
   can never be mistaken for a result.
3. If the message is `body: Input should be a dictionary or an instance of
   AnalyzeRequest`, the request was sent as raw text. Send JSON:
   `{"text": "…"}`.
4. If `INVALID_TEXT`, the text was empty or whitespace-only. Nothing was written.

### What is not recoverable

Nothing — and this is the good case: `BR4.1`/`BR4.2` guarantee **no row is
written** on a refusal. A `422` is the system working correctly.

---

## 5. IR-4 — the startup migration fails (rollback runbook **RB1**)

### Symptom, as it actually appears

**The port never opens.** There is no `500`, no degraded mode, no partially
served app, because the migration runs in the lifespan before the server accepts
anything (`app/main.py:132`).

Measured in this stage: a real `uvicorn` against a real store the step cannot
preserve.

```
$ curl -sS -m 3 http://127.0.0.1:8313/v1/health
curl: (7) Failed to connect to 127.0.0.1:8313 after 0 ms: Could not connect to server
$ ss -ltn | grep 8313
NO LISTENER on 8313
```

The process's own output, with every line attributed to its logger:

```
WHO[uvicorn.error|INFO]  Started server process [189781]
WHO[uvicorn.error|INFO]  Waiting for application startup.
WHO[uvicorn.error|ERROR]  Traceback (most recent call last):
  …
  File "…/app/main.py", line 132, in lifespan
    db.init_db(resolved.db_path)
  File "…/app/db.py", line 235, in init_db
    _migrate_analyses(connection)
  File "…/app/db.py", line 319, in _migrate_analyses
    _rebuild_analyses(connection)
  File "…/app/db.py", line 336, in _rebuild_analyses
    connection.execute(_COPY_ROWS_INTO_V1_TABLE, (UNKNOWN_PROVIDER,))
sqlite3.IntegrityError: CHECK constraint failed: label IN ('positive','negative','neutral')

WHO[uvicorn.error|ERROR]  Application startup failed. Exiting.
EXIT CODE = 3
WHO[app.* records during the failed startup]  0
```

Three of those lines are load-bearing:

- **Exit code 3.** `validation-report.md` **F-02** measured that `1` is the
  *script's* exit code in R6's shape and `3` is uvicorn's own. **Both processes
  print the same `IntegrityError` line, and that line is the reliable signal** —
  do not branch on the number.
- **Zero `app.*` records.** The traceback is `uvicorn.error`, not an application
  logger. **An operator watching only the application loggers sees nothing at
  all about a failed startup.** This is `log-queries.md` §4(d), and it is why
  this runbook's first check is a socket check and not a grep.
- **The store is untouched.** Measured before and after, byte-identical:
  ```
  before  sha256 dde70c5858aa57514d02b50a49dab726fc240d0ed64aa7cf32504219f113c02f
          mtime  2026-10-03 21:21:54.176939393 +0500
  after   sha256 dde70c5858aa57514d02b50a49dab726fc240d0ed64aa7cf32504219f113c02f
          mtime  2026-10-03 21:21:54.176939393 +0500
          tables=analyses,sqlite_sequence   labels=negative,ecstatic   schema_meta_exists=0
  ```
  No `schema_meta` was created, both rows survived, no `analyses_pre_v1` was
  left behind, and the unchanged **mtime** means the file was never opened for
  writing. That is `reliability-design.md` §4 — the step commits whole or rolls
  back whole (`BR5.5`) — working.

**What triggers it, stated precisely, because I got this wrong first.** My first
attempt built a *v3* store and it booted cleanly. The reason: `_is_v1_shape`
(`app/db.py:284`) compares the physical table against the v1 relation, and the
current relation **is** v1-shaped — so a v3 store takes no rebuild path and no
`CHECK` is ever exercised. The rebuild fires only when the physical table is
*not* exactly v1-shaped, e.g. a pre-project store missing `import_id`. The
failure needs that shape plus a row whose `label` is outside
`('positive','negative','neutral')`.

### Steps

1. **Stop. Do not retry.** The retry is deterministic and will fail identically.
2. **Confirm the rollback held** before touching anything:
   ```bash
   sqlite3 'file:data/sentiment.db?mode=ro' \
     "SELECT 'tables='||group_concat(name) FROM sqlite_master WHERE type='table';"
   ```
   Expect `analyses` and `sqlite_sequence`, **no `schema_meta`** and **no
   `analyses_pre_v1`**. A surviving `analyses_pre_v1` means the rollback did not
   run — a different bug, and a retry is the wrong move.
3. **Identify the row the rebuild cannot copy:**
   ```bash
   sqlite3 'file:data/sentiment.db?mode=ro' \
     "SELECT id, label FROM analyses
      WHERE label NOT IN ('positive','negative','neutral');"
   ```
   Empty means the cause is something else — investigate; do not retry.
4. **Do not delete the store.** `memory/team.md` § Deployment records this
   temptation twice and calls the sentence weaker than it reads. A deletion is
   **RB3** (§9 here), not RB1.
5. **Roll the code back** so the operator has a running app while they decide
   what to do about the row: `rollback-runbook.md` **RB2**, summarised in §6.1
   below.
6. **Re-attempt the release** only from a fixed commit, and only after the data
   decision is made. The application has no delete endpoint for the offending
   row and there is no migration tool, so **the disposition of that row is a
   decision about the operator's own history that no agent makes.**

### What is not recoverable

**The row is recoverable; nothing else is lost.** The store is byte-identical, so
every row survives — including the offending one. The one thing that is genuinely
lost is **time**: the app does not start until the row is dispositioned, and
there is no second environment to serve from.

---

## 6. IR-5 — the app is reachable off loopback

### Symptom

Measured, this stage, on `127.0.0.2` — a host inside `127.0.0.0/8`, which Linux
routes to `lo` and which is therefore unreachable off-machine:

```
  resolve_bind_host('127.0.0.1') -> '127.0.0.1'
  resolve_bind_host('::1')       -> '::1'
  resolve_bind_host('localhost') -> 'localhost'
  resolve_bind_host('0.0.0.0')   -> REFUSED (NonLoopbackBindError)
  resolve_bind_host('127.0.0.2') -> REFUSED (NonLoopbackBindError)
  resolve_bind_host('192.168.1.10') -> REFUSED (NonLoopbackBindError)
  create_app(host='127.0.0.2')   -> REFUSED before lifespan: NonLoopbackBindError
--- but the uvicorn CLI ignores both ---
LISTEN 0 2048 127.0.0.2:8314 0.0.0.0:* users:(("python",pid=189927,fd=6))
GET http://127.0.0.2:8314/v1/health -> 200
GET http://127.0.0.1:8314/v1/health -> curl: (7) Failed to connect … HTTP=000
server stderr: 0 lines matching 'refus'
```

**The enforcement is real, and the CLI bypasses it.** `resolve_bind_host` is
called inside `run()`, not inside the application object, so
`uvicorn app.main:app --host <anything>` never consults it and **logs no
refusal**. This is `security-design.md` §4's design working where it is reached
and `health-check-report.md` §2.3's caveat, now re-measured in this stage.
`alarms.md` §3.1 records the same measurement and names the detection's blind
spot: `ss` shows the socket **as it is now** and has no memory.

The enforced path itself does hold. Verified without touching source, by
rebinding the captured default argument:

```
  captured default HOST = ('127.0.0.1',)
  default rebound to    = ('0.0.0.0',)
  RESULT: REFUSED before uvicorn started -> Refusing to bind '0.0.0.0': this app is
  unauthenticated and holds the operator's API key, so it is served on loopback only…
```

A side observation worth recording, because it decides how to read a future
check: `def resolve_bind_host(host: str = HOST)` captures `HOST` **at
definition time**, so `resolve_bind_host()` with no argument ignores a later
reassignment of `m.HOST` (measured: `m.HOST='0.0.0.0'` then
`resolve_bind_host()` → `127.0.0.1`). Editing the constant in source and
restarting *is* enforced; overriding it at runtime is not.

### The check that detects it

```bash
ss -ltnp | grep ':8000'
```

**Healthy:** exactly one listener, `LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:*`.
**Anomalous:** any local address outside `127.0.0.1`, `::1`, `localhost`. This is
`alarms.md` §2.5 and `dashboards.md` Panel A — the only panel with a genuine
security consequence, and the one with the weakest instrument.

### Steps

1. Stop the process. An unauthenticated app holding the operator's API key is
   off-machine; this is the one failure mode where stopping first is right.
2. Restart **without** `--host`, or with a loopback value (§7).
3. Confirm with `ss -ltnp | grep ':8000'`.
4. Treat it as a security incident, not a deployment mishap: if a
   non-loopback listener existed, the key may have been reachable. §11's
   credential check is the follow-up.

### What is not recoverable

**Exposure is recoverable; a key that was read off-machine is not.** Nothing in
this system logs access from another host, and there is no second host to check
from, so "was it actually reached?" cannot be answered after the fact. Treat the
window as unknown, rotate the credential at the provider, and accept that the
exposure window is unrecoverable by design.

### 6.1 RB2 in one screen — rolling back a bad release

`rollback-runbook.md` §3 owns this. Re-verified in this stage, because a
runbook that inlines it must not drift from it:

```
STEP 1 new SCHEMA_VERSION = 4
STEP 1 (new code, before rollback): version=4 rows=2 indexes=3 rel=[(1,'negative',0.9),(2,'positive',0.9)]
STEP 2 old SCHEMA_VERSION = 3
STEP 2 (old init_db ran):             version=3 rows=2 indexes=3 rel=[(1,'negative',0.9),(2,'positive',0.9)]
ROW DATA SURVIVED : True
STEP 3 (re-upgrade):                  version=4 rows=2 indexes=3 rel=[(1,'negative',0.9),(2,'positive',0.9)]
```

The old code's `init_db` was recovered with `git show beeb587:app/db.py` and run
over a real v4 store: **2 rows → 2 rows, all three indexes survived, the
relation was unchanged, and re-upgrading is idempotent.** So:

1. Stop the process.
2. `git log --oneline --decorate -5` — identify the target. **There is no
   remote**, so a commit not in the local history is gone (§9).
3. `git revert --no-edit <release-sha>` — preferred over `git checkout`, so the
   rollback is itself a recorded commit rather than a branch move.
4. **Do not reinstall** unless the dependency set changed. There is no lockfile,
   so a reinstall resolves newest-compatible versions of roughly a dozen
   transitives and the suite's state becomes "a function of the resolved
   dependency set, not of the code" (`memory/team.md` § Testing Posture).
5. Start (§7) and confirm `/v1/health`.
6. **The store needs no action** — that is what the measurement above is for.
7. Note the recorded version drops to `3` and that this is harmless: the
   relation is what the code reads. **Do not hand-edit the version string.**

---

## 7. IR-6 — the run command the artifacts name does not serve

This runbook exists because two `1am`-relevant facts were measured in this
stage and neither is written down anywhere upstream.

### Symptom

`app/main.py` has **no `__main__` guard** (measured: `grep -n '__main__'
app/main.py` → no match), so the invocation `python -m app.main` — named as a
documented run path in `health-check-report.md` §2.3 and implied by
`memory/team.md` § Deployment — **executes the module, prints a warning, and
exits without serving**:

```
<frozen runpy>:130: RuntimeWarning: 'app.main' found in sys.modules after import of
package 'app', but prior to execution of 'app.main'; this may result in unpredictable behaviour
--- no listener ---
```

An operator who types that at 1am sees a process die instantly and no error
that names the cause.

### The commands that do serve, both measured

| Command | Boot → first HTTP 200 | Enforcement |
|---|---|---|
| `python -c 'from app.main import run; run()'` | **0.522 s**, `LISTEN 127.0.0.1:8000`, health `200` | **enforced** — `run()` consumes `HOST` through `resolve_bind_host()` |
| `uvicorn app.main:app` | **0.467 / 0.453 / 0.462 s** (3 runs) | **bypassed** — the CLI never reaches `resolve_bind_host` |

**Use the first.** It is the only invocation measured to both serve and enforce
the loopback bind, and §6 shows what the alternative costs.

### Steps

1. From the repository root, with the venv interpreter:
   ```bash
   .venv/bin/python -c 'from app.main import run; run()'
   ```
2. Confirm: `curl -sS -w ' HTTP=%{http_code}\n' http://127.0.0.1:8000/v1/health`
   → `{"mode":"offline",…} HTTP=200`, and `ss -ltnp | grep ':8000'` shows
   `127.0.0.1:8000`.
3. If you must use the `uvicorn` form, **omit `--host` entirely**.

### What is not recoverable

Nothing — but the cost of not knowing this is a wasted incident, which is why
it is a runbook and not a footnote. Capture the logs while you are here:
`… > access.log 2> app.log`, or the two streams land in one terminal where
neither can be grepped separately (`log-queries.md` §1).

---

## 8. IR-7 — a very wide range breaches the latency budget

### Symptom, as measured

A `200` — nothing is broken — that is far over budget. Ladder taken over real
HTTP against a store holding **one** row:

| `from`…`to` | series entries | response bytes | wall ms |
|---|---|---|---|
| *(none — unbounded)* | 1 | 366 | 1.8 |
| 7 days | 7 | 1 518 | 1.7 |
| 1 year | 365 | 70 254 | 4.8 |
| 21 years | 8 035 | 1 542 894 | 49.3 |
| **100 years** | **36 525** | **7 012 974** | **252.7 / 248.5 / 193.6 / 221.0 / 240.7** |

**Four of those five repeats are over the 200 ms budget**
(`tests/test_analytics_read.py:34`, `BUDGET_MS = 200`), median **240.7 ms**.
`dashboards.md` Panel D and `alarms.md` §2.4 record the same crossover
(≈36 500 entries ≈ a 100-year window); my byte count is 7 012 974 against their
7 012 976 — two bytes of response framing — and my wall time is 10–20 ms
slower, so the figure is reproduced, not merely inherited.

Two facts that stop this being misdiagnosed:

- **`/v2/analytics/terms` is width-insensitive.** Measured at the same
  100-year range: **136 bytes, 2.2 ms**. The cost is entirely in the *series
  assembly* on `/summary`, so "the analytics page is slow" localises to one
  endpoint.
- **An empty store yields an empty series at any width** — measured 183 bytes,
  0 entries, for a 100-year request against a 0-row store. `reliability-design.md`
  §2.3 and `BR3.3`/`BR4.4` refuse to zero-fill a range that matched nothing. So
  "payload is linear in the requested range" is true **only once the range
  matches at least one row**; the naive reading of it is wrong and would send an
  operator looking for the wrong cause.

### The check

```bash
curl -sS -o /dev/null -w '%{size_download} %{time_total}\n' \
  'http://127.0.0.1:8000/v2/analytics/summary?from=2000-01-01&to=2099-12-31'
# or, from the access log alone, without touching the running system:
grep -oE 'from=[0-9-]+&to=[0-9-]+' access.log | …   # log-queries.md Q6
```

Threshold: **> 1.5 MB or > 1 s** (`alarms.md` §2.4).

### Steps

1. Narrow the range. That is the whole fix, and it is available immediately from
   the UI.
2. If a narrow range is still slow, that is a *different* problem: check IR-1
   first, because a contended read costs **5 s**, not 240 ms. A request in the
   seconds rather than the hundreds of milliseconds means lock contention, not
   series width.
3. Do **not** treat this as a code defect here. `smoke-test-results.md` §4
   recorded the same arithmetic and declined to call it one; the width is
   uncapped **by design** (`NFR9.3`), and capping it changes the `/v2` contract
   and belongs to `u3-analytics-view`
   (`observability-setup-questions.md` **OQ-1**).

### What is not recoverable

Nothing. It is a slow answer, not a wrong one.

---

## 9. IR-8 / RB3 — the store is damaged, truncated or gone

### This runbook has no procedure, and that is deliberate

`rollback-runbook.md` §4 states it plainly and this stage re-measured every
number in it:

```
$ git log --all --oneline -- data/ | wc -l
0
$ git check-ignore -v data/sentiment.db
.gitignore:94:/data/   data/sentiment.db
$ find . -path ./.git -prune -o \( -name '*.db' -o -name '*.sqlite*' -o -name '*.bak*' \) -print
./data/sentiment.db
./data/sentiment.db.bak-aa0b1e4
$ ls scripts/
no scripts/ directory
$ grep -rln 'VACUUM INTO\|iterdump\|\.backup(\|shutil.copy2' app/ tests/ *.md
(no hits)
```

**The measured state of backups, precisely, because "no backup" and "one
`cp`" are both wrong:**

| Claim | Measured |
|---|---|
| Any commit contains the store | **0** — `.gitignore:94:/data/` |
| Copies of the store on this machine | **exactly 2**, both `data/`, both sha256 `c8be1361…` |
| Where the second came from | release step **R5** (`cd-config.md`), a manual `cp` taken at 19:53 today |
| Any schedule, retention or second copy | **none** |
| Any off-machine or second-host copy | **none** |
| Any backup tool | **none** — no `scripts/`, no `VACUUM INTO`, no `iterdump`, no `.backup()` |
| Where the store sits in git | nowhere; `git check-ignore` confirms |

So the accurate sentence is: **there is no backup *mechanism*; there is exactly
one manual copy, taken once, at a known instant, and it is byte-identical to the
store it protects.** `infrastructure-specification.md` §5 records backup,
replication, failover and HA as **not provisioned** with that reason;
`reliability-design.md` §5 records the same for the design. Both remain accurate
— a manual release-step copy is not a backup path, and the difference is exactly
what §10 below costs.

### The situations, and what is actually recoverable

| Situation | What is actually recoverable |
|---|---|
| `data/sentiment.db` **deleted** | **Nothing.** Measured behaviour: the app recreates an empty store at version 4 on the next start and works — with **zero history**. |
| **truncated or corrupt** | **Nothing**, unless a copy exists. |
| the R5 copy exists (today it does) | **Everything.** Stop the process, `mv data/sentiment.db.bak-aa0b1e4 data/sentiment.db`, start. The restored store migrates forward idempotently — idempotency measured (`rollback-runbook.md` §3; re-verified in §6.1 above). |
| the only surviving copy is an operator export | **The rows, and only the rows.** Measured, and worse than "the rows": `GET /v1/analyses/export` **requires** `import_id` (422 without it), returns only rows carrying that `import_id`, and **excludes every row written by single analysis** (`import_id IS NULL`). Measured on a 3-row store: the export returned **1** of 3 rows. Measured on a 2-row store with no import at all: `{"code":"IMPORT_NOT_FOUND",…}` `404` — **while `/v2/analytics/summary` on the same store returned `total: 2`.** The data is readable and simultaneously unreachable by the only copy surface. |

**And even a successful export is lossy.** `EXPORT_COLUMNS`
(`app/routes.py:86`) is `("id","text","label","confidence","model","provider","created_at")`
— verified against a real CSV header this stage:

```
id,text,label,confidence,model,provider,created_at
3,imported row,neutral,0.7,dummy,offline,2026-10-03T10:00:00Z
```

`probabilities` and `intensity` are **not** exported, and a re-import creates a
new `import_id`. So the export is a **view**, not a backup.

### The only meaningful entry is prevention

1. **Take the copy first**, before anything starts the app — R5 in
   `cd-config.md` §3. `cp data/sentiment.db data/sentiment.db.bak-$(git rev-parse --short HEAD)`.
2. **Verify it**, because an unverified copy is a belief:
   ```bash
   sha256sum data/sentiment.db data/sentiment.db.bak-*
   ```
3. Re-take it after any release. It does not advance on its own.

### What is not recoverable — stated plainly, because this is the honest answer

1. **Any row written since the last manual copy.** There is no second copy, so
   the copy is a snapshot and the gap after it is gone forever.
2. **Every row written by single analysis, unconditionally.** Measured: the
   export surface excludes `import_id IS NULL` rows, and a store containing
   nothing else returns `404` for every possible request. An operator whose
   history is all `POST /v1/analyze` — which is the normal way to use this app —
   has **no working copy surface at all**.
3. **`probabilities` and `intensity`,** even from a successful export.
4. **The incident history.** There is no log retention, no aggregation, no
   shipping (`log-queries.md` §4.1): a session's log lives or dies with its
   terminal. Nothing about this failure will be reconstructable tomorrow unless
   it is written down now.

---

## 10. IR-9 — the store is behind `SCHEMA_VERSION`

### Symptom and check

```bash
sqlite3 'file:data/sentiment.db?mode=ro' \
  "SELECT 'version='||value FROM schema_meta WHERE key='version';
   SELECT 'idx='||group_concat(name) FROM sqlite_master
     WHERE type='index' AND name LIKE 'idx_%';"
```

**Healthy:** `version=4` and `idx_analyses_created_at, idx_analyses_import_id,
idx_analyses_label_created_at`. **Direction matters:** a version **below 4**
means the next boot will **write** the store; `alarms.md` §2.6 and
`anomaly-config.md` A9 record that on a v4 store the step is provably
write-neutral down to the mtime, which is the correction `validation-report.md`
**F-01** makes to the upstream wording.

The operator's real store measured this stage, read-only:
`version=4`, `rows=0`, all three indexes present, sha256 `c8be1361…`, mtime
`2026-10-03 03:33:42.920985500 +0500`, mode `644`.

### Steps

1. A version **below 4** with no boot pending is SEV4 — record it.
2. A version **below 4** about to be booted against is **SEV2**: take the R5 copy
   *first* (§9), then boot. The step is additive and row-preserving when it
   works (`reliability-design.md` §4), and rolls back loudly when it cannot
   (IR-4), so the store is safe either way — but there is no second copy if that
   reassurance is ever wrong.
3. A missing index is SEV3; re-running the boot restores it
   (`CREATE INDEX IF NOT EXISTS`, `app/db.py:249`).

### What is not recoverable

Nothing, provided the copy was taken first. This is the one failure mode where
a 30-second precaution converts a potential catastrophe into a non-event — and
it is the strongest argument in this project for treating `cp` as part of
starting the app rather than as an optional nicety.

---

## 11. IR-10 — credential material in a log

### Symptom and check

```bash
grep -cE 'sk-or-v1|sk-|AKIA|BEGIN .* PRIVATE KEY|api_key|password' app.log access.log
```

**Expected: 0 for every pattern.** This is `anomaly-config.md` A10, verified
there against a real 13-request capture containing a deliberate storage failure
— `sk-or-v1` 0/0, `sk-` 0/0, `AKIA` 0/0, `api_key` 0/0, `password` 0/0.

The property is structural, not hopeful: the five log call sites
(`log-queries.md` §1.1) interpolate only a mode string, a machine code, an
exception's `str()`, a file path and an OAuth exception. `NFR8.3` is enforced by
asserting `sk-or-v1` and `SELECT` never appear. `memory/project.md`
`## Forbidden` forbids a real credential in any artifact, including under
`aidlc/`.

### Steps

1. Stop the process. Do not scroll the log further into a terminal that may be
   recording.
2. Rotate the credential at OpenRouter. **Do not paste the value anywhere** —
   not into an issue, not into a log, not into an artifact under `aidlc/`.
3. Delete any log file holding it, and confirm the file mode on the store
   (`stat -c '%a' data/sentiment.db`; measured **644**, where the check expects
   **600** — `anomaly-config.md` A12, `validation-report.md` V-12).

### What is not recoverable

**A leaked key, if it was actually used.** Rotation is the whole remedy; there
is no session to revoke and no audit trail to consult on the provider side from
here. This is the only failure mode in this file whose damage is external and
permanent.

---

## 12. IR-11 — a refusal mistaken for an empty result

Not a defect: the three outcomes are deliberately distinct, and this runbook
exists so a 1am reader does not mistake a design for a fault.

| Outcome | Status | Body shape | Meaning |
|---|---|---|---|
| Empty success | `200` | `{"total":0,…,"series":[]}` | the range matched no row |
| Validation failure | `422` | `{"code":"VALIDATION_FAILED","message":…}` | the request was refused; **nothing computed** |
| Storage failure | `500` | `{"code":"STORAGE_FAILURE","message":…}` | the store could not answer |

Measured, all three, this stage:

```
{"total":0,"counts":{"positive":0,…},"shares":{"positive":null,…},"mean_confidence":null,"mean_confidence_row_count":0,"series":[]}   HTTP=200
{"code":"VALIDATION_FAILED","message":"query.from: expected a UTC calendar date written YYYY-MM-DD."}                                     HTTP=422
{"code":"STORAGE_FAILURE","message":"The analytics store could not answer the request."}                                                   HTTP=500
```

`null` where there is no denominator is **deliberate**, never a fabricated `0.0`
(`reliability-design.md` §2.3). A `404` for emptiness never occurs. Two
framework-generated errors keep FastAPI's shape and are **not** this envelope —
measured: `404 {"detail":"Not Found"}` and `405 {"detail":"Method Not Allowed"}`
— which is the affirmed rule in `memory/project.md` `## Mandated` and is exactly
how to tell an app-raised failure from a routing mistake.

### What is not recoverable

Nothing. Nothing was computed.

---

## 13. The four checks to run first, in order

One block, for an operator who does not know which failure mode they are in.
Each line is drawn from `dashboards.md`'s four panels and `alarms.md`'s
thresholds, and each is **manual**.

```bash
# 0. capture the streams separately, or you cannot grep either one later
#    (access log = stdout, application log = stderr — log-queries.md §1)

# 1. is it up?                                    dashboards.md Panel A
curl -sS -o /dev/null -w 'health HTTP=%{http_code}\n' http://127.0.0.1:8000/v1/health
ss -ltnp | grep ':8000'                                  # IR-5, IR-6

# 2. did anything fail server-side?               dashboards.md Panel C
grep -n 'analytics .* read failed' app.log                # IR-1
grep -cE '" 5[0-9]{2}' access.log                         # IR-1
grep -cE '" 422' access.log                               # IR-2, IR-3

# 3. is the store intact and current?             dashboards.md Panel D
sqlite3 'file:data/sentiment.db?mode=ro' \
  "SELECT 'version='||value FROM schema_meta WHERE key='version';
   SELECT 'rows='||count(*) FROM analyses;"              # IR-8, IR-9

# 4. is the exposure the one that matters?
grep -cE 'sk-or-v1|AKIA|password' app.log access.log    # IR-10
stat -c 'store mode=%a' data/sentiment.db                # IR-10
```

**And one check that is stronger than any of them**, because an unchanged
**mtime** proves the file was never opened for writing at all — strictly more
than a matching hash, which would also be consistent with a write-then-restore:

```bash
sha256sum data/sentiment.db; stat -c '%y' data/sentiment.db
```

---

## 14. Standing constraint honoured by this stage

**No application source, test, configuration or data-store file was modified.**
Every store inspection used `file:…?mode=ro`. Every process booted ran with its
CWD inside `/tmp/opencode/ir/`, so the store it opened was a throwaway one.
`git diff --stat app tests pyproject.toml config.example.toml README.md` is
empty. The operator's store, sampled at the first command of this stage and at
the last, with absolute paths:

```
before  sha256 c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
        mtime  2026-10-03 03:33:42.920985500 +0500   size 32768   mode 644
after   sha256 c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
        mtime  2026-10-03 03:33:42.920985500 +0500   size 32768   mode 644
```

`data/sentiment.db.bak-aa0b1e4` is untouched and still byte-identical to the
store it protects.
