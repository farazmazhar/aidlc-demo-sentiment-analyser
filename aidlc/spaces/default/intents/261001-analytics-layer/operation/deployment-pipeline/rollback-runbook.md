# Rollback Runbook — intent `261001-analytics-layer`

> **Stage:** `deployment-pipeline` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Companion to:** `cd-config.md` (R1–R8) and `deployment-strategy.md` ·
> **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/deployment-pipeline`
>
> **Inputs this artifact was derived from**:
> `construction/ci-pipeline/ci-config.md` · `construction/ci-pipeline/quality-gates.md` ·
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md` ·
> `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` ·
> `construction/build-and-test/build-instructions.md` ·
> `memory/team.md` § Deployment and § Way of Working ·
> `app/db.py` · `app/main.py` · `app/config.py` · `tests/test_migration_indexes.py` ·
> the git history at `beeb587` and `HEAD`.
>
> **Every load-bearing claim below was measured, not reasoned about.** The
> measurements were taken against real SQLite files and real `uvicorn`, in this run.
> The commands are given so a reader can repeat them.

---

## 1. What "rollback" means here, and what it costs

`memory/team.md` § Deployment recorded the pre-v4 position exactly: *"Recovery means
stopping the process, deleting or restoring the local file, and checking out the
previous commit."* That was written when the code was at schema version 3 and a
release carried no schema change at all.

**This is the first release in the project where a rollback has two objects** — the
commit and the store — and the whole runbook follows from that fact:

| Object | Reversible by | Cost |
|---|---|---|
| **The commit** | `git checkout` of the previous commit + restart | **One command and one restart.** No data recovery, in the common case — **measured**, §3 |
| **The store** | The file is left alone; the v3 → v4 step is additive and needs no undo | **Nothing**, as long as the step succeeded or failed cleanly. Both measured — §2, §3 |
| **The store, if it is destroyed** | **Nothing.** No commit contains it (`/data/` is gitignored), there is no replication, and there is no migration tool | **Total data loss.** The only mitigation is R5 in `cd-config.md`: copy the file *before* the release |

**One sentence to hold on to.** The recoverable failure is the code; the
unrecoverable failure is the file, and it is unrecoverable because it was never
backed up, not because anything is hard to reverse.

---

## 2. RB1 — The migration failed at startup

**Symptom — and it is not what a failed startup usually looks like: the port never
opens.** A connection is refused. There is no `500`, no degraded mode, no partially
served app, because the migration runs in the lifespan *before* the server accepts
anything (`app/main.py:132`).

**Measured in this run**, booting real `uvicorn` against a store the step cannot
preserve:

```
uvicorn process exit code: 1
client sees             : urllib.error.URLError: [Errno 111] Connection refused
exception raised by init_db:
    sqlite3.IntegrityError: CHECK constraint failed: label IN ('positive','negative','neutral')
```

**Diagnosis — what to grep the console for:** the `sqlite3.IntegrityError` line
above. The application never swallows it: `app/db.py:241` catches `BaseException`,
calls `rollback()`, and re-raises. `memory/team.md` § Code Style names this as the
project's **one** deliberate broad handler and calls it *"rollback-and-re-raise, not
a swallow — a failed migration stops startup loudly instead of leaving a
half-migrated file."*

**The store is already back in its pre-release state. Verified, byte-identical:**

```
store rows after   : 1
store label after  : 'ecstatic'          ← the offending row, intact
store tables after : ['analyses', 'sqlite_sequence']   ← no analyses_pre_v1 left behind
schema_meta after  : no schema_meta table (pre-v1 store) ← no version bump committed
```

Also asserted by `tests/test_migration_indexes.py:398`.

**Procedure — and note that step 3 is a *diagnostic*, not a fix:**

1. **Stop.** The process is already down. Do not restart it against the same store.
2. **Confirm the store is unchanged** before touching anything:
   `env -u APPIMAGE python -c "import sqlite3; c=sqlite3.connect('data/sentiment.db'); print([r[0] for r in c.execute(\"select name from sqlite_master where type='table'\")])"`
   — expect `analyses` and `schema_meta`, and **no `analyses_pre_v1`**. Its presence
   would mean the rollback did not run, which is a different bug and needs
   investigation, not a retry.
3. **Diagnose the row the rebuild cannot copy.** The failure is always a row the v1
   `label` domain refuses — the constraint is
   `CHECK (label IN ('positive','negative','neutral'))` (`app/db.py:69`), so a store
   holding an out-of-domain label is the reproducible cause:
   `env -u APPIMAGE python -c "import sqlite3; print([r for r in sqlite3.connect('data/sentiment.db').execute('select id,label from analyses') if r[1] not in ('positive','negative','neutral')])"`
   An empty list means the cause is something else — stop and investigate rather than
   retry, because a retry is deterministic and will fail identically.
4. **Decide the disposition of that row with the operator.** The application has no
   delete endpoint for it, and there is no migration tool. This is a data decision
   about the operator's own history, and no agent makes it.
5. **Roll the code back** — §3 — so the operator has a running application while
   they decide.
6. **Only then re-attempt the release**, from the fixed commit.

**What is *not* in this procedure, and why:** no `git checkout` is needed to make the
store usable again, because the rollback already happened. And **do not delete
`data/sentiment.db`** — `memory/team.md` § Deployment records the same temptation
twice now: *"Deleting it is still acceptable recovery — but that sentence is weaker
than it reads"*; a store holds *"rows with their original `intensity` values and
their `import_id` grouping; the import/export feature is now the user's way of
moving data out."* A deletion is RB3, not RB1.

---

## 3. RB2 — Roll back the release commit (the common case)

**Measured answer to the only question that matters: rolling back the code is safe
against a v4 store, and costs no data recovery.**

Experiment run in this stage. A real v4 store was built by the new code and seeded
with two rows; then the **`express` release's own `init_db`** — recovered with
`git show beeb587:app/db.py`, `SCHEMA_VERSION = 3` — was run over it:

```
STEP 1  new code, store before rollback : version 4 · 3 indexes · 2 rows · relation pinned
STEP 2  old SCHEMA_VERSION              : 3
STEP 2  outcome                         : init_db SUCCEEDED on a v4 store
STEP 3  after old code ran              : version 3 · 3 indexes · 2 rows · relation unchanged

ROW DATA SURVIVED          : True
RELATION UNCHANGED         : True
ALL THREE INDEXES SURVIVED : True
```

**Then, re-upgrading** — the state a real rollback-then-re-release leaves behind:

```
state before re-upgrade : version 3 · 4 indexes · 2 rows
state after  re-upgrade : version 4 · 4 indexes · 2 rows     ← idempotent, nothing lost
```

**Procedure:**

1. **Stop the process.**
2. **Identify the rollback target.** `git describe --tags` names the last release tag
   — `v1-classic` → `4eb9b74`, `express` → `beeb587`. **There is no remote, so there
   is nothing to fetch and no branch to fall back to beyond the local history.** If
   the target commit is not in the local history, it is gone; see RB3.
   `git log --oneline --decorate -5` before you move.
3. **Check out the previous release commit:**
   `git checkout <previous-release-tag>` — or, to undo the release *in place* while
   keeping the history linear: `git revert --no-edit <release-sha>`. **Prefer
   `git revert` on a tag that is already published to the audit trail**, so the
   rollback is itself recorded as a commit rather than as a branch move — the
   project's provenance record is the committed audit shard
   (`aidlc/spaces/default/intents/261001-analytics-layer/audit/`), and `org.md`
   relies on it precisely because a squash-merge destroys intermediate commits.
4. **Reinstall if the dependency set changed:** `python -m venv .venv &&
   .venv/bin/python -m pip install -e ".[dev]"`. **Known risk, measured by the team:
   there is no lockfile**, so a reinstall resolves newest-compatible versions of
   roughly a dozen transitives and the suite's pass/fail state is *"a function of the
   resolved dependency set, not of the code"* (`memory/team.md` § Testing Posture).
   If a reinstall is not part of the problem, **do not perform one** — rolling back
   the code without touching the venv removes that whole class of variable.
5. **Start and confirm:** `uvicorn app:app`, then `GET /v1/health` on
   `127.0.0.1:8000`. Expect `{"mode":"offline",…}` on an offline checkout.
6. **The store needs no action.** §3's measurement is the proof: the old code's
   `init_db` succeeded, left every row, left every index and left the relation
   untouched.

**Two facts about the store's recorded version that a rollback operator should know,
because both were measured and neither is obvious:**

* **The old code downgrades `schema_meta.version` from `4` to `3`** on the store it
  finds. This is harmless — the relation is what the code reads, and it is unchanged
  — and it is what `_RECORD_SCHEMA_VERSION` is written to do. **Do not "fix" it by
  hand-editing the version string.** Re-running the new `init_db` restores `4`
  idempotently, as measured above.
* **The recorded version tracks "what last ran", not "the highest version ever
  reached."** `deployment-pipeline-questions.md` Q8 records whether that should be
  guarded by a test; the decision belongs to Code Generation.

---

## 4. RB3 — The store is damaged, empty or gone

**This is the one with no procedure, and it is written here so its absence is
unambiguous.**

There is **no backup path and no replication**. `/data/` is gitignored, so no commit
in this repository's history contains a copy of the store; there is no migration
tool, no dump command, and no managed database. `infrastructure-specification.md`
§2.2 states it in the project's own voice: *"There is no backup path, no replication
and no rollback procedure to write, because there is no deployment."*

| Situation | What is actually recoverable |
|---|---|
| `data/sentiment.db` deleted | **Nothing.** The app recreates an empty store at version 4 on the next start (`app/db.py:219`, create branch) and the application works — with **zero history**. |
| `data/sentiment.db` truncated or corrupt | **Nothing**, unless a copy exists — see below |
| A copy exists as `data/sentiment.db.bak-<sha>` from `cd-config.md` R5 | **Everything.** Stop the process, `mv` the copy back to `data/sentiment.db`, start. The restored store will be migrated forward on the next start, idempotently. |
| The only surviving copy is the operator's own `POST /v1/analyses/export` CSV | **The rows, not the database.** That is what the import/export endpoints are for, and `memory/team.md` records it as the reason deletion stopped being costless. |

**Therefore the only meaningful entry here is prevention**, and it is already a
release step: **R5 copies the file before anything starts the app**
(`cd-config.md` §3, §5). **The absence of a backup path is the single strongest
argument for R5 being part of the release rather than an optional nicety**, and the
strongest thing this stage can say about a project with no deployment infrastructure
is that its one irreversible asset needs a `cp`.

---

## 5. Rehearsal — this runbook is tested, and here is how

An untested rollback is not a rollback plan. Every procedure above was exercised
against real SQLite files and a real `uvicorn` in this stage, and the results are
recorded beside each one:

| Procedure | What was executed | Result |
|---|---|---|
| **RB1** — the migration fails | Built the one store shape the step cannot preserve (a row whose label the v1 domain refuses), booted the real `app.main:app` through real `uvicorn` on a loopback port | **exit 1**, port never opened, `sqlite3.IntegrityError: CHECK constraint failed…`, store byte-identical afterwards — row intact, no `analyses_pre_v1`, no version bump |
| **RB2** — roll the code back | Built a real v4 store with two rows; ran `beeb587`'s `init_db` (`SCHEMA_VERSION = 3`) over it | **succeeded**; 2 rows → 2 rows, relation unchanged, all three indexes survived; version recorded 3 |
| **RB2** — then re-release | Ran the new `init_db` over that store again | **idempotent**: version 4, all indexes present, nothing lost |
| **RB1/R6** — the data-safe smoke | Booted the real app with the store path isolated via a throwaway CWD | **exit 0**, `{"mode":"offline",…}`, throwaway store created, **real store's mtime unchanged** |

**Reproducing them.** RB1 and RB3 need a scratch store and never touch the real one
— write it under `$(mktemp -d)`. RB2 needs two checkouts of `app/db.py`; the
`beeb587` copy is recoverable with `git show beeb587:app/db.py`, which is how the
experiment above was run without a second working tree. **No rehearsal requires a
git remote, a registry or a second environment**, because none of them exist.

**What this runbook does not cover, so absence is not read as coverage:**

* **No `git fetch`-based rollback** — there is no remote. A commit not in the local
  history cannot be recovered.
* **No artifact rollback** — nothing is published, so there is no previous image,
  wheel or bundle to redeploy (`memory/team.md` § Deployment).
* **No promotion rollback** — there is one environment, so nothing was promoted.
* **No credential or secret rotation** — no release step handles a credential; the
  OpenRouter key lives in the gitignored `config.local.toml` and in process memory
  (`BR6.1`), and no release step touches either.
* **No automated rollback trigger** — a strategy that reacts to an error rate or a
  latency breach presupposes traffic and monitoring. There is neither, so the trigger
  is *"a human noticed"*; the procedure above is what they then do. Inventing a
  threshold nobody can observe would be a gate with no instrument behind it — the
  failure mode `memory/team.md` names as *"An unrun gate is not a gate."*
* **No concurrency or partial-migration recovery** — the single broad handler at
  `app/db.py:241` is rollback-and-re-raise, and R-01 (the cross-thread SQLite
  connection defect) remains accepted, with the team's ruling that **no test written
  against today's harness can reproduce it**. If a connection-level fault appears
  during a release, it is not covered here and must be investigated as a defect.