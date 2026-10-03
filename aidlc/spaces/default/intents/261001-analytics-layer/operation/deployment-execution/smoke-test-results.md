# Smoke Test Results — intent `261001-analytics-layer`

> **Stage:** `deployment-execution` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Date:** 2026-10-03 · **Release commit under test:** `aa0b1e4`
> · **Companion to:** `deployment-log.md`, `health-check-report.md`,
> `deployment-execution-questions.md`
> · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/deployment-execution`
>
> **Upstream inputs this suite was designed against:** `cd-config.md` §5 (the
> throwaway-store isolation this suite extends) · `deployment-strategy.md` §4 (the
> failure signature and the read-path-writes-nothing property) ·
> `operation/environment-provisioning/validation-report.md` V-06/V-07, V-15, V-16,
> V-19 (loopback enforcement, write-neutrality, the offline default, store safety) ·
> `construction/build-and-test/build-instructions.md` §2.3 (the venv remedy) and
> §6 (the `APPIMAGE` gotcha) · `operation/deployment-pipeline/rollback-runbook.md`
> RB1/RB6 (the data-safe smoke precedent) · `memory/team.md` § Deployment, §
> Code Style · `app/routes.py`, `app/analytics.py`, `app/db.py`, `app/main.py`.

---

## 1. Method — real HTTP against a real `uvicorn` process

**Every request in this report went over a real TCP socket to a real `uvicorn`
subprocess.** No check here is an in-process ASGI call, a `TestClient` call, or a
call into a handler function. That distinction is the whole reason this file
exists rather than a line in `test-results.md`: the 192-test suite exercises the
application through the ASGI interface, and a release has to be proven through the
interface it is actually served on — process start, lifespan, socket bind, HTTP
parse, response serialise, real shutdown.

Concretely, per run:

| Property | How it was arranged |
|---|---|
| **Real server process** | `.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8212` spawned as a `subprocess` — its own PID, its own interpreter, its own lifespan. Readiness proved by a TCP `connect_ex` poll, not by a sleep. |
| **Real client** | `urllib.request` against `http://127.0.0.1:<port>`. `HTTPError` is caught and its status and body are treated as the result, so a `422` or a `404` is data rather than an exception. |
| **Real store isolation** | The subprocess's `cwd` is a fresh `mktemp -d` scratch tree, with `PYTHONPATH` set to the repository so the import still resolves. The CWD-relative `DEFAULT_DB_PATH` (`app/config.py:39`) therefore resolves **inside the scratch tree** — this is `cd-config.md` §5's mechanism, applied to a subprocess instead of a thread. |
| **`APPIMAGE` stripped** | `env` is copied and `APPIMAGE` is popped before the spawn, so `sys.executable` is the venv's interpreter. |
| **Clean shutdown** | `SIGTERM`, then `communicate(timeout=15)` to capture the server's own log lines, which are quoted below as independent confirmation of every status code. |

The scratch store was created by the server itself on startup:
`/tmp/smoke-jw5qxtle/data/sentiment.db`, 32768 bytes. **The operator's real store
was never opened by any process in this suite** — verified in `deployment-log.md`
§5.1 and `health-check-report.md` §4.

### 1.1 Data was seeded through the real write path, not injected

An analytics endpoint answering over an empty store proves very little — a `200`
with `total: 0` is what a broken aggregate also returns. So the suite seeds rows
through `POST /v1/analyze`, the application's own write path, and only then queries
the read surface. Three rows with known labels were submitted, and the labels the
server chose are quoted in §2 — which also demonstrates that the offline dummy
engine, the text validation, the store write and the response contract all work
end to end over HTTP.

### 1.2 One correction made during the run, recorded rather than hidden

The first execution reported **8 failures out of 25**. All eight were defects in
the **test harness's expected-substring strings**, not in the application: the suite
matched on `"label": "positive"` (with a space) while the API correctly emits
compact JSON (`"label":"positive"`), and matched `"total": 0` against `"total":0`.
One expectation was also simply wrong: an empty submitted text is refused with code
`INVALID_TEXT`, not `VALIDATION_FAILED`, which is the correct contract behaviour.

**In every one of those eight cases the HTTP status code the application returned
was already the expected one.** The assertions were corrected and the suite re-run
end to end; the results below are from the corrected run, and no application
behaviour was changed to make anything pass.

---

## 2. Results — 27 checks, 27 passed, 0 failed

### 2.1 Reachability and seeding

| # | Check | Request | Status | Result |
|---|---|---|---|---|
| **S-00** | `uvicorn` binds `127.0.0.1` and accepts TCP | TCP connect `127.0.0.1:8212` | up | **PASS** — pid alive, socket accepting before any request was issued |
| **S-01** | `POST /v1/analyze` seeds a **positive** row | `{"text":"I absolutely love this wonderful product"}` | `200` | **PASS** |
| **S-02** | `POST /v1/analyze` seeds a **negative** row | `{"text":"This is dreadful and terrible, a waste"}` | `200` | **PASS** |
| **S-03** | `POST /v1/analyze` seeds a **neutral** row | `{"text":"It arrived on Tuesday in a box"}` | `200` | **PASS** |
| **S-04** | `GET /v1/analyses` lists the seeded rows | — | `200` | **PASS** |

Server responses, verbatim and compact:

```
S-01 {"id":1,"text":"I absolutely love this wonderful product","label":"positive","probabilities":{"positive":0.85,"negative":0.05,"neutral":0.1},"confidence":0.85,"model":"dummy-keyword-v1","provider":"offline","created_at":"2026-10-03T14:53:49Z","import_id":null}
S-02 {"id":2,"text":"This is dreadful and terrible, a waste","label":"negative","probabilities":{"positive":0.05,"negative":0.85,"neutral":0.1},"confidence":0.85,"model":"dummy-keyword-v1","provider":"offline","created_at":"2026-10-03T14:53:49Z","import_id":null}
S-03 {"id":3,"text":"It arrived on Tuesday in a box","label":"neutral","probabilities":{"positive":0.15,"negative":0.15,"neutral":0.7},"confidence":0.7,"model":"dummy-keyword-v1","provider":"offline","created_at":"2026-10-03T14:53:49Z","import_id":null}
S-04 [{"id":3,...},{"id":2,...},{"id":1,...}]   (newest first, FR1.2)
```

The labels came back correct for each text, the `probabilities`/`confidence` agree
with the label, `model` is `dummy-keyword-v1` and `provider` is `offline` — which is
the offline default measured by `validation-report.md` V-16, observed here as live
HTTP traffic rather than as a config reading. `import_id` is `null` on all three,
matching the classification that `import_id` is server-generated and only set by a
bulk import.

### 2.2 `/v1/health`

| # | Check | Request | Status | Result |
|---|---|---|---|---|
| **S-05** | `/v1/health` reports the active engine and connection state | `GET /v1/health` | `200` | **PASS** |
| **S-06** | `/v1/health` carries no credential material | `GET /v1/health` | `200` | **PASS** |

```
{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
```

Exactly the three-key contract: `mode`, `connected`, and `reason` present **only**
because the app is not connected. No key, no token, no header value appears in the
body — the `AC5.3.1` property that the `/v1` health response can never leak the
operator's key, confirmed over the wire rather than by reading the handler.

### 2.3 `/v2/analytics/*` with **no** parameters

| # | Check | Request | Status | Result |
|---|---|---|---|---|
| **S-07** | `/v2/analytics/summary`, no parameters | `GET /v2/analytics/summary` | `200` | **PASS** |
| **S-08** | `/v2/analytics/terms`, no parameters | `GET /v2/analytics/terms` | `200` | **PASS** |

```
S-07 {"total":3,"counts":{"positive":1,"negative":1,"neutral":1},"shares":{"positive":0.3333,"negative":0.3333,"neutral":0.3333},"mean_confidence":0.8,"mean_confidence_row_count":3,"series":[{"date":"2026-10-03","total":3,"counts":{"positive":1,"negative":1,"neutral":1},"shares":{"positive":0.3333,"negative":0.3333,"neutral":0.3333},"mean_confidence":0.8,"mean_confidence_row_count":3}]}

S-08 {"positive":[{"term":"absolutely","count":1},{"term":"love","count":1},{"term":"product","count":1},{"term":"wonderful","count":1}],"negative":[{"term":"dreadful","count":1},{"term":"terrible","count":1},{"term":"waste","count":1}]}
```

These are the load-bearing results of the whole release. Both `/v2` endpoints
answer over real HTTP with real aggregates derived from rows written moments earlier
through the real write path: the counts and shares match the three seeded rows
exactly (1/1/1 of 3), `mean_confidence` 0.8 is the arithmetic mean of 0.85, 0.85
and 0.7 rounded half-up, and the terms are the real tokens of the positive and
negative texts — stop words correctly absent, `neutral` correctly absent from a
payload that is exactly `{positive, negative}`.

### 2.4 `/v2/analytics/*` **with** parameters

| # | Check | Request | Status | Result |
|---|---|---|---|---|
| **S-09** | `summary?from&to` over a populated window | `?from=2000-01-01&to=2099-12-31` | `200` | **PASS** |
| **S-09b** | same request: status and payload size | `?from=2000-01-01&to=2099-12-31` | `200` | **PASS** — `7,012,992` bytes, `36,525` series entries. See §4 for the observation. |
| **S-09c** | `summary?from&to` over a 7-day window | `?from=2026-09-27&to=2026-10-03` | `200` | **PASS** |
| **S-10** | `summary?import_id` with no matching group | `?import_id=deadbeef` | `200` | **PASS** |
| **S-11** | `terms?limit=1` | `?limit=1` | `200` | **PASS** |
| **S-12** | `terms?from&to&limit=5` over a populated window | `?from=2000-01-01&to=2099-12-31&limit=5` | `200` | **PASS** |
| **S-13** | `summary` over a window matching **no row** — `200`, never `404` | `?from=1990-01-01&to=1990-01-02` | `200` | **PASS** |

```
S-10 {"total":0,"counts":{"positive":0,"negative":0,"neutral":0},"shares":{"positive":null,"negative":null,"neutral":null},"mean_confidence":null,"mean_confidence_row_count":0,"series":[]}

S-11 {"positive":[{"term":"absolutely","count":1}],"negative":[{"term":"dreadful","count":1}]}

S-13 {"total":0,"counts":{"positive":0,"negative":0,"neutral":0},"shares":{"positive":null,"negative":null,"neutral":null},"mean_confidence":null,"mean_confidence_row_count":0,"series":[]}
```

Four properties confirmed by these bodies, each of them a stated contract rule:

- **`import_id` really filters.** `?import_id=deadbeef` returns `total: 0` with an
  empty series while the unfiltered call returns `total: 3` — the grouping filter is
  applied, not ignored.
- **`limit` really truncates.** `?limit=1` returns exactly one term per label; the
  unfiltered call returns four and three. `limit` is applied, not defaulted away.
- **A no-match range is `200`, not `404`.** `BR4.4` says a range matching no row is
  a `200` with `total` 0 and an empty series. Measured: `200` with `"series":[]`.
- **Empty aggregates are `null`, not `0`.** `shares` and `mean_confidence` are
  `null` where there is nothing to divide, so a consumer can distinguish "no rows"
  from "an average of zero" — which `0.3333` in S-07 and `null` in S-13 together
  demonstrate.

### 2.5 Refusal paths

Every one of these returns the single `{code, message}` envelope and a `422`. The
point of the block is that **no aggregate is computed on a refused request** — the
refusal happens in the handler before any read.

| # | Check | Request | Status | Code |
|---|---|---|---|---|
| **S-14** | `summary` with an **inverted** range | `?from=2026-01-02&to=2026-01-01` | `422` | `VALIDATION_FAILED` |
| **S-15** | `summary` with an **unparseable** `from` | `?from=not-a-date` | `422` | `VALIDATION_FAILED` |
| **S-16** | `terms` with an **inverted** range | `?from=2026-01-02&to=2026-01-01` | `422` | `VALIDATION_FAILED` |
| **S-17** | `terms?limit=0` — refused, **never clamped** | `?limit=0` | `422` | `VALIDATION_FAILED` |
| **S-18** | `terms?limit=abc` — refused | `?limit=abc` | `422` | `VALIDATION_FAILED` |
| **S-19** | `POST /v1/analyze` with empty text | `{"text":""}` | `422` | `INVALID_TEXT` |
| **S-20** | `POST /v1/analyze` with an **undeclared** field | `{"text":"hello there","mode":"live"}` | `422` | `VALIDATION_FAILED` |
| **S-21** | `GET /v1/analyses?limit=0` — refused | `?limit=0` | `422` | `VALIDATION_FAILED` |

Bodies, verbatim:

```
S-14 {"code":"VALIDATION_FAILED","message":"query.from and query.to: 'from' must not be a later UTC day than 'to'."}
S-15 {"code":"VALIDATION_FAILED","message":"query.from: expected a UTC calendar date written YYYY-MM-DD."}
S-16 {"code":"VALIDATION_FAILED","message":"query.from and query.to: 'from' must not be a later UTC day than 'to'."}
S-17 {"code":"VALIDATION_FAILED","message":"query.limit: Input should be greater than or equal to 1"}
S-18 {"code":"VALIDATION_FAILED","message":"query.limit: Input should be a valid integer, unable to parse string as an integer"}
S-19 {"code":"INVALID_TEXT","message":"Text to analyse must not be empty or whitespace-only."}
S-20 {"code":"VALIDATION_FAILED","message":"body.mode: Extra inputs are not permitted"}
S-21 {"code":"VALIDATION_FAILED","message":"query.limit: Input should be greater than or equal to 1"}
```

Four things this block establishes, and they are the ones most easily asserted and
never checked:

- **`limit` is refused, not clamped.** `?limit=0` returning `422` rather than
  silently becoming the default is `BR3.5`/`BR3.6` on `/v1` and `BR2.6` on `/v2`.
  The two endpoints produce the **same envelope and the same message text** for the
  same bad `limit` (S-17 and S-21 are byte-identical), which is the shared-validation-
  handler property S-17's description records.
- **The inverted range is named in the message.** `S-14`'s message names *both*
  offending fields (`query.from and query.to`), and `S-15` names only the one that is
  actually wrong (`query.from`) — a per-field message, not a blanket one.
- **An undeclared body field is refused by name.** `S-20`'s message is
  `body.mode: Extra inputs are not permitted`. `AnalyzeRequest` is a plain dataclass,
  so without `require_declared_fields` the key would have been dropped silently and
  the request would have returned `200`. Over HTTP it returns `422`.
- **Empty text is refused even though the engine is unconfigured.** `S-19` returns
  `INVALID_TEXT` on an offline checkout — the text is validated before the engine is
  resolved, so the refusal is about the input, not about the missing key.

### 2.6 The served page and the surrounding surface

| # | Check | Request | Status | Result |
|---|---|---|---|---|
| **S-22** | `GET /` serves the single page as HTML | `GET /` | `200` | **PASS** — `content-type: text/html; charset=utf-8`, `10,767` bytes, contains `<html` and a `<form` |
| **S-23** | An unknown path is `404`, not a served page | `GET /does-not-exist` | `404` | **PASS** — `content-type: application/json`, 22 bytes |
| **S-24** | `/auth/status` reports the unauthenticated session state | `GET /auth/status` | `200` | **PASS** |

```
S-24 {"mode":"offline","connected":false,"source":null,"model":"typesafe/jev-1.13","reason":"Not connected to OpenRouter."}
```

`/auth/status` returns `source: null` — no session credential has been established —
and still names the configured model, so a support route is answering correctly
without any credential in play. `/auth/callback` was not exercised: establishing a
session requires an OpenRouter authorisation round trip, and this checkout is
`offline` with no `config.local.toml` (`validation-report.md` V-16). Recording the
absence rather than implying coverage.

### 2.7 Independent confirmation from the server's own log

The server's access log is captured independently of the client. Every status code
in §2 is corroborated by a line the **server** wrote:

```
INFO:     127.0.0.1:38802 - "GET /v2/analytics/summary?from=not-a-date HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:38806 - "GET /v2/analytics/terms?from=2026-01-02&to=2026-01-01 HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:38810 - "GET /v2/analytics/terms?limit=0 HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:38818 - "GET /v2/analytics/terms?limit=abc HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:38822 - "POST /v1/analyze HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:38838 - "POST /v1/analyze HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:38842 - "GET /v1/analyses?limit=0 HTTP/1.1" 422 Unprocessable Content
INFO:     127.0.0.1:38850 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:38864 - "GET /does-not-exist HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:38868 - "GET /auth/status HTTP/1.1" 200 OK
```

and the shutdown:

```
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [162001]
```

The shutdown sequence completes all four lines, so the lifespan's `finally` ran and
the startup connection was closed cleanly. This is the graceful-shutdown property
`deployment-strategy.md` §6 records as real and already owned by the code,
demonstrated rather than re-asserted.

---

## 3. Coverage map — what was tested and what was not

| Surface | Covered | How |
|---|---|---|
| `/v1/health` | yes | S-05, S-06, plus R7 over a live server on port 8000 |
| `/v1/analyze` (happy + refusals) | yes | S-01…S-03, S-19, S-20 |
| `/v1/analyses` | yes | S-04, S-21 |
| `/v2/analytics/summary` (no params) | yes | S-07 |
| `/v2/analytics/summary` (params) | yes | S-09, S-09b, S-09c, S-10, S-13 |
| `/v2/analytics/terms` (no params) | yes | S-08 |
| `/v2/analytics/terms` (params) | yes | S-11, S-12 |
| refusal paths on both `/v2` endpoints | yes | S-14…S-18 |
| served page `/` | yes | S-22 |
| 404 behaviour | yes | S-23 |
| `/auth/status` | yes | S-24 |
| **`/v1/analyses/import`** | **no** | Needs a multipart upload and drives the `import_id` grouping path. It is covered by the suite (R3, 192 passed) and is untouched by this release; it is not in the `/v2` surface this release ships. Recorded as not-smoked rather than counted as covered. |
| **`/v1/analyses/export`** | **no** | Returns a CSV attachment. Suite-covered; not part of this release's surface. |
| **`/v1/auth/*`, `/auth/callback`, `/auth/disconnect`** | **no** | Require an OpenRouter round trip; this checkout is `offline` with no `config.local.toml`. |
| **`/v1/analyze` in live mode** | **no** | No credential exists on this machine, by design (`memory/project.md` `## Forbidden`). The offline path is what this release is actually verified against. |

None of the uncovered rows is a gap in **this release's** surface. Every one of them
is a pre-existing `/v1` endpoint that this release does not touch, and every one is
covered by the 192-test suite that R3 ran green.

---

## 4. Observation — the summary series is zero-filled to the width of the range

**This is recorded as an observation, not a failure, and not a defect claim.**

`GET /v2/analytics/summary?from=2000-01-01&to=2099-12-31` returns `200` correctly, but
the response is **7,012,992 bytes** carrying **36,525** series entries — one entry
per calendar day in the requested window, including the ~36,522 days that match no
row. The same call over a 7-day window (S-09c) is small and immediate.

The behaviour is the documented one: `BR4.4` calls for a series, and
`app/analytics.py`'s `_zero_entry` exists precisely to zero-fill gaps so a chart has
no holes. **So the contract is being honoured.** What is worth an operator's
attention is the arithmetic: payload size is **linear in the width of the requested
range**, with no upper bound on that width in the request contract, and this is
served synchronously on a single loopback process with a single SQLite connection.

Concretely: the default call (S-07, no parameters) is ~470 bytes. The widest window
this suite happened to try produced 7 MB — roughly **15,000×** the default, from a
parameter change alone, on a request that took noticeably longer than any other in
the suite.

**What this stage does not do with it.** It does not call it a defect: no upstream
artifact bounds the series width, `NFR` documents were not re-read for a stated
latency budget on this endpoint, and the full suite (`test-results.md`) records no
failing performance test. Deciding whether a maximum range width belongs in the
`/v2` contract is a design decision for the unit that owns the analytics surface
(`u3-analytics-view`), not a deployment observation this stage can settle.

**Why it is written down anyway.** This is a release execution, and the release's
own procedure is what an operator will follow. A person who reads
`deployment-strategy.md` §2 and sees "no traffic to serve" could reasonably type a
wide `from`/`to` pair into the analytics view and receive a multi-megabyte response
from a single-threaded local server. That is a property of the deployed release
that the operator now knows, and it is better known than discovered.

**A second, smaller observation:** S-09c's 7-day window and S-09's 100-year window
return the *same* `total` (3), which is correct — the seed data is all dated today —
but it means the wide-window call's cost is entirely in the series, not in the
aggregate.

---

## 5. What this suite does not establish

Stated so that a green result here is not read as more than it is.

- **It does not establish that the analytics read path writes nothing.** That
  property is real and is asserted by `test-results.md`'s suite
  (`tests/test_migration_indexes.py:442, 469`: row count, content hash and schema
  digest unchanged across many requests). This suite ran 27 requests against a
  *throwaway* store whose post-run state was never compared row-for-row, because the
  store's real content was not the subject. The write-free property is inherited from
  the suite, and **labelled inherited** rather than re-measured.
- **It does not establish anything about live mode.** No request in this suite
  reached OpenRouter; the app is `offline` and no egress occurred.
- **It does not exercise the failure paths RB1 depends on.** RB1's signature — the
  migration failing so the port never opens — needs a deliberately unpreservable
  store, which is `rollback-runbook.md` §5 and `validation-report.md` V-20's
  measurement, not this suite's. See `health-check-report.md` §5.
- **It says nothing about performance under concurrency.** 27 sequential requests
  from one client is a correctness surface, not a load surface.
- **One client, one process, one machine.** There is no second process and no second
  environment in this project, so this suite cannot and does not test promotion,
  canary behaviour, or any multi-instance property.

---

## 6. Verdict

**27 checks. 27 passed. 0 failed.**

The released commit `aa0b1e4`, served by a real `uvicorn` process over real HTTP on
the enforced loopback bind, answers correctly on `/v1/health`, on both `/v2/analytics/*`
endpoints with and without every documented parameter, refuses every malformed
request with the right code and a per-field message, and serves the page. Its
aggregates are computed from rows written moments earlier through the real write
path, and the numbers in the response match those rows.

**No application source file was changed during this stage**, and the operator's
real store was not opened by any process in this suite.
