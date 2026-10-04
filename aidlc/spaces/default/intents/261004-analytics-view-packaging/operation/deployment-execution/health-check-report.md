# Health Check Report — intent `261004-analytics-view-packaging`

> **Stage:** `deployment-execution` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> support `aidlc-developer-agent` · **Date:** 2026-10-04 ·
> **Subject:** the release of the working tree at HEAD `4b67c03` on `127.0.0.1:8000`
> · **Companion to:** `deployment-log.md`, `smoke-test-results.md`,
> `deployment-execution-questions.md`
> · **Record:**
> `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/deployment-execution`

---

## 1. What was health-checked

Four things, each measured against the released working tree rather than read out of an
upstream artifact: the enforced loopback bind; the store's write-neutrality; the live
process's health; and the reachability of the rollback path. There is **no host, no
supervisor, no load balancer and no monitoring stack** to health-check; that absence is
recorded so a green result is not read as coverage of a surface that does not exist.

---

## 2. The enforced loopback bind — confirmed

`app/main.py` pins `HOST = "127.0.0.1"`, `PORT = 8000` and refuses a non-loopback host.
While the release was serving, the listening socket was:

```
$ ss -ltnp | grep 8000
LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:* users:(("python",pid=…,fd=6))
```

The `Local Address` column is `127.0.0.1:8000`; the peer column is `ss`'s rendering of a
wildcard *remote* endpoint on a listening socket. The bind is loopback only, and the
process holding it is the release's own PID.

**Recorded gap (inherited):** the `uvicorn app:app --host 0.0.0.0` CLI form bypasses the
`resolve_bind_host` enforcement, because the application object is built at module scope
with the default. The enforced bind holds on the documented run path and on the
`--host 127.0.0.1` form this stage used; a hand-typed non-loopback flag would override it.
This is a code-level gap, not a deployment action, and is stated rather than hidden.

---

## 3. Store write-neutrality — confirmed

This release ships **no schema step** (`SCHEMA_VERSION` stays `4`; no column, table or
index is added). `init_db` therefore runs its idempotent no-op on startup. The operator's
store was sampled immediately before and after the cutover:

| | Before | After |
|---|---|---|
| sha256 | `2a4574cf05238ff031afd0c0e022ee4cd1c14cab949110027f176350436d42e7` | same |
| mtime | `2026-10-03 23:59:14.115475300 +0500` | same |
| `schema_meta.version` | `4` | `4` |
| indexes | 3 | 3 |
| rows | 7 | 7 |

**An unchanged mtime means the file was not opened for writing at all** — a stronger
statement than "the contents came out the same".

---

## 4. Live process health

```
GET /v1/health            -> 200 {"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
GET /v2/analytics/summary -> 200 {"total":7,…}
GET /v2/analytics/terms   -> 200 {"positive":[…],"negative":[…]}
GET /                     -> 200 (page carries the new view hooks)
```

**Healthy, with one dependency not connected.** `mode: offline` is the measured default of
this checkout (no `config.local.toml`), so the app serves its full read surface on the
dummy engine with no credential and no egress. Startup and shutdown completed cleanly on
every invocation; **no process was left running.**

---

## 5. Preconditions re-checked against the live release

| # | Precondition | Status |
|---|---|---|
| D1 | The source is a git working tree | PASS — `.git` and `.gitignore` present |
| D2 | `git` is on `PATH` | PASS |
| D3 | Install is a venv (PEP 668 blocks the bare form) | PASS |
| D4 | CPython ≥ 3.11 (3.14.7) | PASS |
| D5 | The bind stays loopback | PASS (§2, with the CLI-bypass caveat) |
| D6 | No release step reaches the network except install/audit | PASS — the app ran offline; `pip-audit` is the only networked gate |

**Correction to `cd-config.md`:** a git remote now exists (`origin` →
`https://github.com/farazmazhar/aidlc-demo-sentiment-analyser.git`), contrary to
`memory/team.md`'s "no remote". It carries no CI workflow. The deployment-pipeline
artifacts were corrected for this; it changes where a release tag can be pushed, not
whether a pipeline runs.

---

## 6. The rollback path is reachable

| Runbook | Reachable? | Evidence |
|---|---|---|
| **RB1** — migration fails at startup | Reachable, not triggered | rollback-and-re-raise in `app/db.py`; failure signature is the port never opening. Inherited from the prior intent's rehearsal. |
| **RB2** — roll back the release commit | Reachable | the prior release tag is an ancestor of HEAD; `git checkout` works (a `git fetch` is now also possible). No data recovery, because no schema step ships. |
| **RB3** — the store is damaged or gone | Recovery entry exists | `data/sentiment.db.bak-4b67c03`, sha256 `2a4574cf…d42e7`, byte-identical. |

---

## 7. Health verdict

| # | Check | Result |
|---|---|---|
| H-1 | The live listening socket is `127.0.0.1:8000` only | PASS |
| H-2 | The `--host` CLI bypass is recorded, not hidden | RECORDED (§2) |
| H-3 | `SCHEMA_VERSION` is `4`; no schema step ships this release | PASS |
| H-4 | The startup migration was a **verified no-op** — store sha256 *and* mtime unchanged | PASS |
| H-5 | `/v1/health` returns `200`, `mode: offline`, no credential material | PASS |
| H-6 | Both `/v2/analytics/*` endpoints and `/` return `200` over live HTTP | PASS |
| H-7 | Startup and shutdown clean on every invocation; no process left running | PASS |
| H-8 | The operator's store is byte-identical in content **and** mtime | PASS |
| H-9 | Preconditions re-checked (with the remote-drift correction) | PASS |
| H-10 | RB1 reachable; RB2's target present; RB3's recovery file exists | PASS |

**The release is healthy.** The process serves on loopback, the health endpoint reports the
truth, the startup step is proven write-neutral, the operator's store is byte-identical
down to the mtime, and all three rollback procedures are reachable from the state left
behind.

**Two things this health check does not cover:** there is **no monitoring or alerting** on
this host, so nothing would report a regression after these checks ran; and the
**`uvicorn --host` bypass** (§2) remains a live gap in the enforced bind that the
documented run path closes and a hand-typed flag can open.
