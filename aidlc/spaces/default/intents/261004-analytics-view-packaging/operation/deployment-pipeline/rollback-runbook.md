# Rollback Runbook — intent `261004-analytics-view-packaging`

> **Stage:** `deployment-pipeline` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Companion to:** `cd-config.md` (R1–R8) and `deployment-strategy.md`
> **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/deployment-pipeline`
>
> **Inputs derived from:** the prior intent's `deployment-pipeline/rollback-runbook.md`
> and its measured rehearsals · this intent's `construction/build-and-test/*` ·
> `memory/team.md` § Deployment and § Way of Working · `app/db.py` · `app/main.py` ·
> `app/config.py` · the git history.

---

## 1. What "rollback" means here, and what it costs

**This release adds no schema step.** `SCHEMA_VERSION` stays `4`, and the change is
static page assets plus repository-level tooling, so a rollback has **one object**, not
two:

| Object | Reversible by | Cost |
|---|---|---|
| **The commit** | `git checkout` of the previous release + restart | **One command and one restart.** No data recovery. |
| **The store** | **Nothing to do** — no schema change ran, so the store is untouched by this release | **Nothing** |
| **The store, if destroyed** | **Nothing.** No commit contains it (`/data/` is gitignored), there is no replication and no migration tool | **Total data loss.** The only mitigation is R4: copy the file before the release |

**One sentence to hold on to.** Because this release carries no schema step, the
recoverable failure is the code and the unrecoverable failure is the file — and the file
is only at risk from the *manual boot* step, which still runs `init_db` on the real store.

---

## 2. RB1 — The migration failed at startup

Even though this release changes no schema, `init_db` still runs on every startup, and
the prior intent measured its failure mode against the real app. **The symptom is not
what a failed start-up usually looks like: the port never opens.** A connection is
refused — no `500`, no degraded mode — because the migration runs in the lifespan before
the server accepts anything.

**Diagnosis — grep the console for the `sqlite3.IntegrityError` line.** The application
never swallows it: the one deliberate broad handler calls `rollback()` and re-raises, so
the store is left byte-identical.

**Procedure:**
1. **Stop.** The process is already down; do not restart it against the same store.
2. **Confirm the store is unchanged** before touching anything — expect `analyses` and
   `schema_meta`, and **no `analyses_pre_v1`**.
3. **Diagnose the offending row** (the failure is always a row the v1 `label` domain
   refuses).
4. **Decide that row's disposition with the operator.** No agent makes a data decision.
5. **Roll the code back** — §3.
6. **Only then re-attempt the release**, from the fixed commit.

**Do not delete `data/sentiment.db`** as a reflex; a store holds the operator's history
and the import/export feature is their way of moving it out.

---

## 3. RB2 — Roll back the release commit (the common case)

**Because this release adds no schema step, rolling the code back needs no data
recovery at all: the previous release's code and this release's code read the same v4
relation.** The prior intent's rehearsal remains valid for the relation itself (its
`beeb587` `init_db` ran cleanly on a v4 store, preserving every row and all indexes).

**Procedure:**
1. **Stop the process.**
2. **Identify the rollback target.** `git describe --tags` names the last release tag.
   There is no remote, so a commit not in the local history is gone.
3. **Check out the previous release commit** — `git checkout <previous-release-tag>` — or,
   to undo the release in place while keeping history linear, `git revert --no-edit
   <release-sha>`. Prefer `git revert` on a published tag so the rollback is itself
   recorded as a commit.
4. **Reinstall only if the dependency set changed.** With `requirements.lock` now
   committed, a reinstall from the lockfile is reproducible; if a reinstall is not part
   of the problem, **do not perform one**.
5. **Start and confirm:** `uvicorn app:app`, then `GET /v1/health` on `127.0.0.1:8000`.
6. **The store needs no action** — no schema step ran.

**One measured fact worth knowing:** the prior intent showed that older code can
*downgrade* `schema_meta.version` on a store it finds, harmlessly, because the field
tracks "what last ran", not "the highest version ever reached". **Do not "fix" it by
hand-editing the version string.** (This release ships no schema change, so it does not
trigger that behaviour.)

---

## 4. RB3 — The store is damaged, empty or gone

**This is the one with no procedure, written here so its absence is unambiguous.**
There is no backup path and no replication: `/data/` is gitignored, so no commit contains
a copy of the store, and there is no migration tool or managed database.

| Situation | What is recoverable |
|---|---|
| `data/sentiment.db` deleted | **Nothing.** The app recreates an empty store at version 4 on the next start — with zero history. |
| Truncated or corrupt | **Nothing**, unless a copy exists. |
| A copy exists as `data/sentiment.db.bak-<sha>` from R4 | **Everything.** Stop, `mv` the copy back, start. It migrates forward idempotently on the next start. |
| Only the operator's `POST /v1/analyses/export` CSV survives | **The rows, not the database.** |

**Therefore the only meaningful entry here is prevention**, and it is release step R4:
copy the file before anything starts the app. The absence of a backup path is the
strongest argument for R4 being part of the release rather than an optional nicety.

**The remaining live hazard.** The README's documented manual end-to-end step boots the
real `app.main:app` from the repository root and therefore migrates the real store.
`make verify` does **not** (the suite never starts a server), so the automated gate is
safe; the manual step is the one to run from a throwaway CWD (R5). Whether the README
step should be rewritten is the human's call — recorded as Q7 in
`deployment-pipeline-questions.md`.

---

## 5. Rehearsal

An untested rollback is not a rollback plan. The load-bearing rehearsals were run in the
prior intent against real SQLite files and a real `uvicorn`, and they remain valid for
the relation this release leaves untouched:

| Procedure | What was executed | Result |
|---|---|---|
| RB1 — the migration fails | Built the one store shape the step cannot preserve, booted the real app through real `uvicorn` | **exit 1**, port never opened, store byte-identical afterwards |
| RB2 — roll the code back | Ran `beeb587`'s `init_db` (`SCHEMA_VERSION = 3`) over a real v4 store | **succeeded**; rows unchanged, relation unchanged, all three indexes survived |
| RB2 — then re-release | Ran the new `init_db` over that store again | **idempotent**: version 4, nothing lost |
| R5 — the data-safe smoke | Booted the real app with the store path isolated by a throwaway CWD | **exit 0**, throwaway store created, **real store's mtime unchanged** |

**This release's own verification** is `make verify` (198 passed, 97.06 % coverage; secret
scan and dependency audit clean), recorded in `construction/build-and-test/test-results.md`.

**What this runbook does not cover, so absence is not read as coverage:**
- **No `git fetch`-based rollback** — there is no remote.
- **No artifact rollback** — nothing is published.
- **No promotion rollback** — there is one environment.
- **No credential or secret rotation** — no release step handles a credential.
- **No automated rollback trigger** — a threshold presupposes traffic and monitoring;
  the trigger is "a human noticed".
- **No concurrency or partial-migration recovery** — R-01 (the cross-thread SQLite
  connection defect) remains accepted, with the team's ruling that no test written
  against today's harness can reproduce it.
