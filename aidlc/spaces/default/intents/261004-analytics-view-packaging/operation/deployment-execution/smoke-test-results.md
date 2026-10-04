# Smoke Test Results — intent `261004-analytics-view-packaging`

> **Stage:** `deployment-execution` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Date:** 2026-10-04 · **Release under test:** the working tree at HEAD `4b67c03`
> · **Companion to:** `deployment-log.md`, `health-check-report.md`,
> `deployment-execution-questions.md`
> · **Record:**
> `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/deployment-execution`

---

## 1. Method — real HTTP against a real `uvicorn` process

Every request went over a real TCP socket to a real `uvicorn` subprocess. The suite
spawns `.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8213` with a fresh
`mktemp -d` as its CWD and `PYTHONPATH` set to the repository, so the CWD-relative
`DEFAULT_DB_PATH` resolves **inside the scratch tree** and the operator's real store is
never opened. Readiness is proved by a TCP connect poll; the server is stopped with
`SIGTERM`.

Rows are seeded through `POST /v1/analyze` — the application's own write path — so the
`/v2` aggregates are computed from real stored rows, not injected fixtures.

---

## 2. Results — 14 checks, 14 passed, 0 failed

| # | Check | Request | Status | Result |
|---|---|---|---|---|
| S-01 | seed a **positive** row | `POST /v1/analyze {"text":"I absolutely love this wonderful product"}` | 200 | PASS |
| S-02 | seed a **negative** row | `POST /v1/analyze {"text":"This is dreadful and terrible, a waste"}` | 200 | PASS |
| S-03 | seed a **neutral** row | `POST /v1/analyze {"text":"It arrived on Tuesday in a box"}` | 200 | PASS |
| S-04 | health reports the engine/connection state | `GET /v1/health` | 200 | PASS |
| S-05 | history lists the three seeded rows | `GET /v1/analyses` | 200 | PASS |
| S-06 | summary, no parameters | `GET /v2/analytics/summary` | 200 | PASS |
| S-07 | terms, no parameters | `GET /v2/analytics/terms` | 200 | PASS |
| S-08 | summary over a populated range | `GET /v2/analytics/summary?from=2000-01-01&to=2099-12-31` | 200 | PASS |
| S-09 | a range matching **no row** is `200`, empty — never `404` | `GET /v2/analytics/summary?from=1990-01-01&to=1990-01-02` | 200 | PASS |
| S-10 | `limit` truncates | `GET /v2/analytics/terms?limit=1` | 200 | PASS |
| S-11 | an **inverted** range is refused | `GET /v2/analytics/summary?from=2026-01-02&to=2026-01-01` | 422 | PASS |
| S-12 | `limit=0` is **refused, never clamped** | `GET /v2/analytics/terms?limit=0` | 422 | PASS |
| S-13 | the served page carries the **new view hooks** | `GET /` | 200 | PASS |
| S-14 | an unknown path is `404` | `GET /does-not-exist` | 404 | PASS |

Selected bodies, verbatim:

```
S-04 {"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
S-06 {"total":3,"counts":{"positive":1,"negative":1,"neutral":1},"shares":{"positive":0.3333,"negative":0.3333,"neutral":0.3333},"mean_confidence":0.8,"mean_confidence_row_count":3,"series":[…]}
S-07 {"positive":[{"term":"absolutely","count":1},{"term":"love","count":1},{"term":"product","count":1},{"term":"wonderful","count":1}],"negative":[{"term":"dreadful","count":1},{"term":"terrible","count":1},{"term":"waste","count":1}]}
S-09 {"total":0,"counts":{"positive":0,"negative":0,"neutral":0},"shares":{"positive":null,"negative":null,"neutral":null},"mean_confidence":null,"mean_confidence_row_count":0,"series":[]}
S-10 {"positive":[{"term":"absolutely","count":1}],"negative":[{"term":"dreadful","count":1}]}
S-11 {"code":"VALIDATION_FAILED","message":"query.from and query.to: 'from' must not be a later UTC day than 'to'."}
S-12 {"code":"VALIDATION_FAILED","message":"query.limit: Input should be greater than or equal to 1"}
```

**S-13** confirms the page this release changes carries all seven new hooks:
`range-from`, `range-to`, `range-status`, `terms-positive`, `terms-negative`,
`summary-partial`, `terms-partial`.

### 2.1 The cutover check (real store, port 8000)

Separately from the throwaway suite, the real release was booted against the operator's
real store (`deployment-log.md` §2 R6). It answered `200` on `/v1/health`,
`/v2/analytics/summary` (7 real rows: `total:7`, shares `0.4286/0.4286/0.1429`,
`mean_confidence: 0.9786`) and `/v2/analytics/terms`, served the page with the new
hooks, bound `127.0.0.1:8000` only, and left the store's sha256 **and** mtime unchanged.

### 2.2 What the smoke suite does not establish

- **It does not execute the browser script.** `app/static/app.js` is served and its hooks
  are pinned (S-13, and `tests/test_page.py`), but nothing here runs it — no
  browser-automation library is admitted under the two-package cap. NFR4.6/NFR4.7 rest on
  the static assertions plus this manual end-to-end evidence, per the recorded Q2
  decision.
- **It does not establish the read path writes nothing** beyond the store sha256/mtime
  check on the cutover; the stronger write-neutrality assertions live in the test suite.
- **It says nothing about live mode** — no request reached OpenRouter; the app is offline.
- **It says nothing about concurrency** — sequential requests from one client.
- **One client, one process, one machine** — no promotion, canary or multi-instance
  property is tested, because none exists.

---

## 3. Verdict

**14 checks. 14 passed. 0 failed.** The release serves the changed analytics view and both
`/v2` endpoints correctly over real HTTP on the enforced loopback bind, refuses malformed
requests with the right code and a per-field message, and leaves the operator's store
byte-identical. No application source file was changed during this stage.
