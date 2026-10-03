# Health Check Report — intent `261001-analytics-layer`

> **Stage:** `deployment-execution` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> support `aidlc-developer-agent` (migration step, §3) · **Date:** 2026-10-03 ·
> **Subject of the health check:** the release of commit `aa0b1e4` on
> `127.0.0.1:8000`
> · **Companion to:** `deployment-log.md`, `smoke-test-results.md`,
> `deployment-execution-questions.md`
> · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/deployment-execution`
>
> **Upstream inputs this validation was performed against:**
> `operation/environment-provisioning/validation-report.md` (V-06, V-07 the loopback
> checks; V-15 write-neutrality; V-16 the offline default; V-19 the store-safety
> method; V-20 the RB1 rehearsal; F-01 the conditional-mutation correction;
> F-02 the exit-code ambiguity) · `operation/environment-provisioning/environment-inventory.md`
> (`environment-inventory` §2.1–§2.6, §3 the live hazard) ·
> `operation/deployment-pipeline/cd-config.md` (`cd-config` §4 preconditions D1–D7,
> §5 the store hazard, R5, R6) · `operation/deployment-pipeline/deployment-strategy.md`
> (`deployment-strategy` §4 the failure signature) ·
> `operation/deployment-pipeline/rollback-runbook.md` (RB1, RB2, RB3) ·
> `construction/build-and-test/test-results.md` (`build-test-results` §2.1) ·
> `construction/build-and-test/build-instructions.md` §2.3, §6 ·
> `memory/team.md` § Deployment, § Code Style, § Testing Posture ·
> `memory/project.md` · `app/main.py`, `app/config.py`, `app/db.py`.

---

## 1. What was health-checked, and the standard the check is held to

Four things, each measured in this stage against the released commit rather than
read out of an upstream artifact:

1. **The enforced loopback bind** — that the process serving the release is bound to
   loopback and that a non-loopback host is refused loudly rather than served.
2. **The migration step's outcome** — the `v3 → v4` schema step: where it stands,
   whether it ran, and whether it was a no-op. **Full record in §3.**
3. **The live process's health** — that the released thing actually serves, and what
   its health endpoint reports.
4. **The operator's store** — that it is byte-identical to how this stage found it.

**There is no host, no supervisor, no load balancer and no monitoring stack to health
check.** `environment-inventory.md` §2.6 and `deployment-strategy.md` §6 both record
those absences, and they are recorded here too so a green result is not read as
coverage of a monitoring surface that does not exist. What exists is one process on
one machine over one file, and that is exactly what was checked.

---

## 2. The enforced loopback bind — confirmed

`app/main.py` pins `HOST = "127.0.0.1"`, `PORT = 8000`, defines
`LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}`, and refuses anything else in
`resolve_bind_host` by raising `NonLoopbackBindError`. That enforcement is the
project's own substitute for a network boundary, and it is the one process-exposure
control this release depends on, so it was checked at both the function level and the
socket level.

### 2.1 `resolve_bind_host` accepts loopback and refuses everything else

```
HOST/PORT = 127.0.0.1 8000
LOOPBACK_HOSTS = ['127.0.0.1', '::1', 'localhost']
 accept 127.0.0.1    -> 127.0.0.1
 accept ::1          -> ::1
 accept localhost    -> localhost
 refused 0.0.0.0     -> Refusing to bind '0.0.0.0': this app is unauthenticated and holds the operator's ...
 refused 127.0.0.2   -> Refusing to bind '127.0.0.2': this app is unauthenticated and holds the operator ...
 refused 192.168.1.10-> Refusing to bind '192.168.1.10': this app is unauthenticated and holds the opera ...
 refused example.com -> Refusing to bind 'example.com': this app is unauthenticated and holds the operator ...
exit = 0
```

**Result: PASS.** All three allowed hosts resolve; all four refused hosts raise with
the explanation, including `127.0.0.2` — a value that is *almost* loopback and that a
naive prefix or `startswith` check would have let through. The refusal is on an exact
set membership, which is the correct reading of `FR7.6`/`AC7.6.1`.

### 2.2 The live socket is on loopback and nothing else

While the release was serving (R7 in `deployment-log.md` §2):

```
$ ss -ltnp | grep 8000
State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN 0      2048          127.0.0.1:8000       0.0.0.0:*     users:(("python",pid=162172,fd=6))
```

**Result: PASS.** The local address is `127.0.0.1:8000` and the peer column is
`0.0.0.0:*`, which is how `ss` renders a wildcard *remote* endpoint on a listening
socket — the bind is the `Local Address` column, and it is loopback only. The process
holding it is the release's own PID. There is no second listener on a wildcard
address.

### 2.3 What this check does and does not cover

**Covered:** the bind is loopback in fact, and a non-loopback host is refused by
construction.

**Not covered, stated so absence is not read as coverage:**

- **The `uvicorn` CLI's `--host` flag bypasses `resolve_bind_host`.** The enforcement
  lives in `run()` (`app/main.py:83-94`), which resolves `HOST` through
  `resolve_bind_host()` before calling `uvicorn.run`. Launching uvicorn directly as
  `uvicorn app:app --host 0.0.0.0` does **not** pass through `resolve_bind_host`,
  because the application object is constructed at module scope with the default.
  This is precisely the gap `resolve_bind_host`'s own docstring records — *"uvicorn's
  own default is not our constant, so `uvicorn app:app --host 0.0.0.0` used to expose
  the app while every test still passed"* — and closing it for the direct-CLI
  invocation shape is beyond what this stage can do, since it is a code change, not a
  deployment action.
  **The operational consequence is concrete and stated: the enforced bind holds on
  the documented run path (`python -m app.main` / `app.main:run`) and on the
  `uvicorn app:app --host 127.0.0.1` form this stage used. An operator who types
  `--host 0.0.0.0` on the CLI overrides it.** The mitigation available to an operator
  today is the default: omit `--host`, or pass a loopback value.
- **No external reachability was tested from another host.** There is no second host
  in this environment, so `fr7.6`'s "never exposed" claim rests on the bind check
  above plus the absence of any other listening socket — not on an attempted
  connection from outside.
- **Firewall and host configuration were not inspected.** Nothing in this project
  manages them, and no artifact claims to.

---

## 3. Database migration log — the `v3 → v4` step

**This step is applicable, so it is logged in full. It is the first schema change this
project has shipped under a release, and it is the one object in this deployment that
is not reversible by a `git checkout`.**

`cd-config.md` §1 states the reason this stage has a migration log at all: at schema
version 3 the team could correctly write *"there is no rollback procedure to write,
because there is no deployment."* At version 4 that sentence is no longer true,
because the release is now the thing that mutates durable state.

### 3.1 Where the step stands

| Property | Value | Source |
|---|---|---|
| `SCHEMA_VERSION` at the release commit | **4** | `app/db.py:60`, measured at run time |
| What the step does | Adds **three named indexes** — `idx_analyses_created_at`, `idx_analyses_import_id`, `idx_analyses_label_created_at` — via `CREATE INDEX IF NOT EXISTS`, **after** the migrate-or-create branch | `app/db.py:249` `_ensure_indexes` |
| What it does **not** do | No column added, renamed, retyped or dropped; no row backfilled, rewritten or discarded | `deployment-strategy.md` §3; `infrastructure-specification.md` §2.2 |
| Atomicity | One `BEGIN … commit`; `except BaseException: connection.rollback(); raise` | `app/db.py:232-244` |
| When it runs | In the FastAPI lifespan, **before** the server accepts anything | `app/main.py:132` |
| Strategy | **expand-only**; contract phase deferred deliberately | `deployment-strategy.md` §3 |
| Idempotent | Yes — `IF NOT EXISTS` plus an upsert on the version key | `tests/test_migration_indexes.py:246` |

### 3.2 Whether it was required on the operator's store: **no — it was a no-op**

The operator's real `data/sentiment.db` was **already at `schema_meta.version = 4`
with all three indexes present**, sampled through SQLite's read-only URI before
anything ran:

```
schema_meta rows [('version', '4')]
indexes        ['idx_analyses_created_at', 'idx_analyses_import_id', 'idx_analyses_label_created_at']
analyses rows  0
```

So on this machine the `v3 → v4` step had **nothing to do**. This is not an
assumption — it is the measured basis of finding **F-01** in
`validation-report.md` §4, which corrected `cd-config.md` §5's over-general wording:
the startup migration writes the store **if and only if** the store is behind
`SCHEMA_VERSION`, and on a store already at v4 it is provably write-neutral down to
the mtime.

**R7 proved that independently on the real store, not on a copy.** Booting the real
`app:app` from the repository root — the actual release, against the actual
`sentiment.db` — left **both the sha256 and the mtime unchanged**:

```
PRE   sha=c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
PRE   mtime=2026-10-03 03:33:42.920985500 +0500
POST  sha=c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
POST  mtime=2026-10-03 03:33:42.920985500 +0500
STORE SHA256 UNCHANGED
STORE MTIME UNCHANGED
```

Both `sha256sum` and `stat` were sampled immediately before the server was started and
immediately after it was terminated, and the verdict lines above are the script's own
comparison of those two sampled values. §4.1 carries the independent final re-read.

An unchanged mtime means the file was **not opened for writing at all** — a stronger
statement than "the contents came out the same".

### 3.3 Whether it was **tested**: yes — executed deliberately, in isolation, against seeded data

Running the step against the operator's v4 store proves nothing: a no-op is a no-op.
So the `v3 → v4` step was executed **on purpose**, on an isolated copy in a
`mktemp -d` scratch tree, against a copy that had been **seeded with four real rows
through the application's own write path** (`app.service.analyze_text` with
`DummySentimentClient`) so that row preservation would be a real measurement rather
than a vacuous one over an empty table.

The copy was first driven to v3 by the **`express` release's own `init_db`**,
recovered with `git show beeb587:app/db.py` — the same technique `rollback-runbook.md`
§3 uses, and the reason a rollback target is testable without a second working tree.

```
express release SCHEMA_VERSION = 3

STEP 0  seeded v4 copy           version=4   indexes=3  rows=4  data_sha=045b2bec1c4bc28e
STEP 1  express init_db -> v3    version=3   indexes=3  rows=4  data_sha=045b2bec1c4bc28e
release commit SCHEMA_VERSION = 4
STEP 2  v3->v4 step              version=4   indexes=3  rows=4  data_sha=045b2bec1c4bc28e
STEP 3  re-run (idempotency)     version=4   indexes=3  rows=4  data_sha=045b2bec1c4bc28e

version 3 -> 4 advanced          : True
rows preserved across the step   : True
row data byte-identical          : True
3 indexes present at v4           : True
idempotent                       : True
exit = 0
```

**Result: PASS.** Read left to right:

| Step | What it shows |
|---|---|
| STEP 0 | A v4 store with **4 real rows**, written through the app's own write path, digest `045b2bec1c4bc28e`. |
| STEP 1 | The `express` release's `init_db` (v3) ran over it and **recorded version 3 without touching a row or an index** — the measured basis of RB2's "old code is safe against a v4 store". |
| STEP 2 | **The `v3 → v4` step under test ran.** Version advanced `3 → 4`. All **4 rows survived**, and the **content digest is byte-identical** to STEP 0's — the step added indexes and nothing else, exactly as `expand-only` promises. All three named indexes present. |
| STEP 3 | Re-running the step changed **nothing at all** — version, index count, row count and digest all identical. **Idempotent**, which is what makes re-releasing after a rollback safe. |

**The digest comparison is what makes this a real test.** A migration that rewrote a
row, coerced a `confidence` value, or dropped a row would have moved
`045b2bec1c4bc28e`. It did not. And because the step ran against a store that was
genuinely at v3 — produced by the previous release's own code, not by hand-editing a
version string — the `3 → 4` transition is the real one.

### 3.4 Migration outcome, stated in one place

| Question | Answer |
|---|---|
| **Where does the step stand?** | Defined at `app/db.py:219-247` and `_ensure_indexes` at `:249`; expand-only, additive, atomic, idempotent. Contract phase deliberately deferred. |
| **Was it required?** | **No.** The operator's store was already at v4 with all three indexes. |
| **Did it run?** | **Yes — twice, deliberately, and once incidentally.** Incidentally on the real store during R7 (as a verified no-op); deliberately on an isolated seeded copy at §3.3 (as a real `3 → 4` transition, with idempotency re-confirmed). |
| **Was it a no-op?** | **On the operator's real store: yes, provably** — sha256 and mtime unchanged, so the file was not written at all. **On the isolated seeded copy: no** — it advanced the version and preserved every row, which is the step doing its job. |
| **Who executed it?** | The stage lead, on the isolated copy, with `aidlc-developer-agent` on hand as the stage's declared migration support. The code under test is `app/db.py` from the release commit; the downgrade to v3 came from `beeb587`'s own `app/db.py`. The scratch tree was removed after measurement. **The operator's store was never a migration target.** |

### 3.5 What this migration log does not establish

- **It does not establish the failure path.** The one store shape the step cannot
  preserve — a row whose `label` the v1 `CHECK` domain refuses — was **not**
  reconstructed here. That is `rollback-runbook.md` §5 and `validation-report.md`
  V-20's measurement (exit 1, port never opened, store byte-identical afterwards),
  inherited rather than re-measured. Stated as inherited so a reader knows which
  claims in this log were produced in this stage and which were carried.
- **It does not establish behaviour at scale.** Four rows is enough to prove nothing
  is dropped and nothing is rewritten. It says nothing about migration time on a
  large store, and no artifact in this project claims to.
- **It does not cover a store at a version below 3.** Only the `3 → 4` edge was
  exercised. Versions 1 and 2 are reachable only by a pre-project store, which
  `memory/team.md` records as no longer the operator's situation.
- **It does not establish that a v4 store is safe against a *future* v5.** The
  expand-only discipline that makes rollback cheap holds only while no destructive
  change ships. `deployment-strategy.md` §3 states the constraint on the next scope
  that wants one, and repeating it here would not extend it: **a scope that drops or
  retypes a column must not do it in the same release as the change that stops using
  it.**

---

## 4. Live process health, and the store's final state

### 4.1 The operator's store, re-read at the end

Every check in this section was performed through SQLite's **read-only URI**
(`file:data/sentiment.db?mode=ro`), which opens the database without any write
intent.

| | Before this stage | After this stage | |
|---|---|---|---|
| sha256 | `c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39` | `c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39` | **identical** |
| mtime | `2026-10-03 03:33:42.920985500 +0500` | `2026-10-03 03:33:42.920985500 +0500` | **identical** |
| size | `32768` | `32768` | **identical** |
| `schema_meta.version` | `4` | `4` | **identical** |
| indexes | 3 | 3 | **identical** |
| rows | 0 | 0 | **identical** |

**The store is byte-identical and untouched in time.** The unchanged mtime is the
strongest of these: the file was not opened for writing at any point in this stage.

The only file added under `data/` is `data/sentiment.db.bak-aa0b1e4` — R5's recorded
backup, byte-identical to the store, inside the gitignored `/data/`. Every throwaway
store built during this stage (R6's smoke, the 27-check smoke suite, the seeded
migration copy) lived under a `mktemp -d` scratch directory, and none was inside the
repository.

### 4.2 The live process

```
$ curl -sS -w "\nHTTP=%{http_code}\n" http://127.0.0.1:8000/v1/health
{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
HTTP=200

$ curl -sS -w "\nHTTP=%{http_code}\n" http://127.0.0.1:8000/v2/analytics/summary
{"total":0,"counts":{"positive":0,"negative":0,"neutral":0},"shares":{"positive":null,"negative":null,"neutral":null},"mean_confidence":null,"mean_confidence_row_count":0,"series":[]}
HTTP=200
```

**Healthy, with one dependency not connected.** `mode: offline` is the measured
default of this checkout — there is no `config.local.toml`
(`validation-report.md` V-16) — so the app serves its full read surface on the dummy
engine with no credential and no egress. The empty aggregate is correct: the real
store genuinely holds 0 rows. This is a healthy offline checkout, not a degraded one.

Startup and shutdown were clean on every invocation:

```
INFO:     Started server process [162172]
INFO:     Sentiment analysis app ready in offline mode (OpenRouter not connected)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
...
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
```

**No process was left running.** Both cutover cycles exited `143` (SIGTERM) with the
port closed in between (`deployment-log.md` §2 R7b).

### 4.3 Preconditions D1–D7, re-checked against the live release

`cd-config.md` §4 lists the preconditions that gate a release. Each is either
re-measured here or explicitly inherited.

| # | Precondition | Status |
|---|---|---|
| D1 | The source is a git working tree | **PASS** — `.git` and `.gitignore` present; `git status` and `git log` both ran. |
| D2 | `git` is on `PATH` | **PASS** — every `git` command in R1 and §3 of the deployment log ran without a not-found. |
| D3 | `env -u APPIMAGE` on every interpreter invocation | **PASS** — applied to every command in this stage. Had it been omitted, the suite's one spawned interpreter would have exited `130`. |
| D4 | CPython ≥ 3.11; measured 3.14.7 | **PASS** — `.venv/bin/python -V` → `Python 3.14.7`; `pyproject.toml` requires `>=3.11`. |
| D5 | Install is a venv | **PASS** — R2's bare form exits 1 under PEP 668; the venv form exits 0. |
| D6 | The bind stays loopback | **PASS** — §2.1 and §2.2, with the CLI-bypass caveat in §2.3 stated rather than omitted. |
| D7 | No release step reaches the network except R2 | **PASS** — R2 is the only step that resolves from an index. R3, R4, R6, R7, the smoke suite and the migration experiment are all local; the app ran `offline` and no request left the machine. |

---

## 5. The rollback path is reachable from the state this stage left behind

Re-stated here because it is a health property, not only a deployment one: a release
that leaves no reachable recovery is not healthy, it is merely finished.

| Runbook | Reachable? | Evidence |
|---|---|---|
| **RB1** — migration failed at startup | **Reachable, not triggered.** The handler is `app/db.py:241` (`rollback()` then `raise`), inside the lifespan. The signature — *the port never opens, connection refused* — is `deployment-strategy.md` §4's teaching point and was measured by Environment Provisioning (V-20). **Inherited, not re-executed here** (see §3.5). | code read + inherited measurement |
| **RB2** — roll back the release commit | **Reachable.** `git describe --tags` → `express`; `git rev-parse express` → `d3a7703f…cc6f` → commit `beeb587`; `git merge-base --is-ancestor beeb587 HEAD` → **YES**. `git checkout express` works, with no remote to fetch from. | measured this stage |
| **RB3** — the store is damaged or gone | **The recovery entry that was empty now exists.** `data/sentiment.db.bak-aa0b1e4`, sha256 `c8be1361…c39`. `mv` it back and the restored store migrates forward idempotently — idempotency measured at §3.3 STEP 3. | created and verified this stage (R5) |

**R5 is the load-bearing part of this table.** `rollback-runbook.md` §3 is explicit
that there is no backup path, no replication and no migration tool, so RB3 without
that file is total data loss. **That file now exists, and it is byte-identical to the
store it protects.**

---

## 6. Health verdict

| # | Check | Result |
|---|---|---|
| H-1 | `resolve_bind_host` accepts the 3 loopback hosts, refuses 4 non-loopback hosts including `127.0.0.2` | **PASS** |
| H-2 | The live listening socket is `127.0.0.1:8000` only | **PASS** |
| H-3 | The CLI `--host` bypass of the enforcement is recorded, not hidden | **RECORDED** (§2.3) |
| H-4 | `SCHEMA_VERSION` at the release commit is `4`; the step is additive, atomic, idempotent | **PASS** |
| H-5 | The migration was **not required** on the operator's store (already v4, 3 indexes) | **PASS** |
| H-6 | The migration on the real store was a **verified no-op** — sha256 *and* mtime unchanged | **PASS** |
| H-7 | The `v3 → v4` step was **executed deliberately** on an isolated seeded copy: version advanced, 4 rows preserved with an identical content digest, 3 indexes present | **PASS** |
| H-8 | The migration is **idempotent** on re-run | **PASS** |
| H-9 | `/v1/health` returns `200` with `mode: offline`, `connected: false`, no credential material | **PASS** |
| H-10 | `/v2/analytics/summary` returns `200` over live HTTP from the release commit | **PASS** |
| H-11 | Startup and shutdown complete cleanly on every invocation; no process left running | **PASS** |
| H-12 | The operator's store is byte-identical in content **and** mtime, with nothing written | **PASS** |
| H-13 | Preconditions D1–D7 re-checked against the live release | **PASS** (D6 with the §2.3 caveat) |
| H-14 | RB1 reachable; RB2's rollback target present and an ancestor of HEAD; RB3's recovery file exists | **PASS** |

**The release is healthy.** The process serves on loopback, the health endpoint
reports the truth, the migration step is proven both inert-where-it-should-be and
correct-where-it-should-act, the operator's store is byte-identical down to the
mtime, and all three rollback procedures are reachable from the state left behind.

**Three things this health check does not cover, so that nothing above is read as
more than it is:** there is **no monitoring or alerting** on this host, so nothing
would have reported a regression had one occurred after the checks ran
(`deployment-strategy.md` §6, `environment-inventory.md` §2.6); the **RB1 failure
signature** is inherited from Environment Provisioning rather than re-measured here;
and the **`uvicorn --host` bypass** in §2.3 is a live gap in the enforced bind that
the documented run path closes and a hand-typed flag can still open.
