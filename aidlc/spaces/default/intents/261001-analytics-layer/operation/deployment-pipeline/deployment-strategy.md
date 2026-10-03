# Deployment Strategy — intent `261001-analytics-layer`

> **Stage:** `deployment-pipeline` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Companion to:** `cd-config.md` (the procedure) and `rollback-runbook.md` (the
> recovery) · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/deployment-pipeline`
>
> **Inputs this artifact was derived from**:
> `construction/ci-pipeline/ci-config.md` · `construction/ci-pipeline/quality-gates.md` ·
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md` ·
> `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` ·
> `memory/team.md` § Deployment and § Way of Working · `memory/project.md` ·
> `app/db.py` · `app/main.py` · `app/config.py` ·
> `tests/test_migration_indexes.py`.
>
> **This is a design artifact.** It adds no file to the repository root.

---

## 1. What the strategy question means against this repository

A deployment strategy answers one question: **how is the running thing replaced, and
how is the replacement reversed?** That question has a real answer here, and it is
not a variation on a hosted-service answer — it is the strategy for **one process on
one machine over one file**, which is a genuinely distinct case, not a degraded one.

The stage definition's menu is blue/green, canary, rolling, A/B and feature flags.
Four of those five are *traffic-shaping* strategies: they presuppose that requests
can be divided between two versions. **This app has no traffic to shape.** It binds
one address, for one operator, with no second version running:

| Fact | Where it is |
|---|---|
| One bind address, `127.0.0.1:8000`, enforced at startup on every path | `app/main.py:45-46, 65, 83, 106` |
| A non-loopback bind **raises** `NonLoopbackBindError` rather than serving | `app/main.py:65-81`; instrumented by gate **G12** |
| No container, no image, no hosted service, no IaC, no orchestrator | `memory/team.md` § Deployment |
| No second human, no remote, no PR, no reviewer | `memory/team.md` § Way of Working |
| One durable file, gitignored, created on first run | `app/config.py:39`; `.gitignore` `/data/` |

**The honest strategy statement is therefore two strategies, not one** — one for the
process and one for the schema, because in this repository they are different objects
with different failure modes, and conflating them is how a rollback procedure goes
wrong.

---

## 2. Process strategy: **recreate**

**The running process is stopped and a new one is started on the new commit.** There
is no overlap, no draining, no warm standby, because there is nothing to drain *to*
and nothing to keep warm.

| Property | Value here |
|---|---|
| **Strategy** | recreate |
| **Trigger** | a human, at a terminal, after R1–R6 have passed (`cd-config.md` §3) |
| **Unit of replacement** | the commit, identified by the annotated scope tag |
| **Overlap** | none — the old process is gone before the new one starts |
| **Rollback cost** | one `git checkout` plus one restart, and no data recovery in the common case — **measured**, `rollback-runbook.md` §3 |
| **Downtime** | the interval between the two processes, on a single-developer local app with no traffic to serve |

**Why not the alternatives.** Each is rejected for a reason that is checkable, not
for lack of imagination:

* **Blue/green** needs two complete environments to swap between. There is one, and
  its cost is not double infrastructure but *double the local store*, which is the
  one thing in this repository that cannot be recreated for free — `memory/team.md` §
  Deployment: *"Real stores are no longer disposable… the import/export feature is
  now the user's way of moving data out."* A blue/green cutover would require
  replicating `data/sentiment.db`, and there is no replication.
* **Canary** needs to route a percentage of requests to a new version. There is one
  requester and one process; a canary of 1 % of one user is the whole user.
* **Rolling** needs several instances behind a balancer. There is exactly one
  process, started by hand, with no supervisor and no load balancer.
* **A/B** is an experiment framework, not a safety mechanism — and an experiment
  needs two variants to compare, which requires the same missing second environment.

---

## 3. Schema strategy: **expand-only** — and the contract half is correctly deferred

`app/db.py:60` sets `SCHEMA_VERSION = 4`. The v3 → v4 step is the first schema change
this project has shipped under a release, and its strategy is the discipline the
standard expand-contract pattern requires:

| Phase | What this release does | Evidence |
|---|---|---|
| **Expand** | Adds **no column at all** — only three named indexes, created with `CREATE INDEX IF NOT EXISTS` after the migrate-or-create branch | `app/db.py:249` `_ensure_indexes`; `tests/test_migration_indexes.py:283, 302` |
| **Migrate** | No backfill: there is no new column to populate, so no row is rewritten | `tests/test_migration_indexes.py:219` asserts every row's value survives, `intensity` included |
| **Contract** | **Deferred, deliberately.** No `DROP COLUMN`, no rename, no retyping ships in this release — which is what makes it deferrable at all | `infrastructure-specification.md` §2.2: *"No column dropped, renamed or retyped; no row discarded or rewritten"* |

**The single most important property of this strategy is measured, not asserted: the
v3 → v4 step is forward- *and* backward-compatible with the previous release's code.**
`rollback-runbook.md` §3 records the experiment — the `express` release's `init_db`
(`SCHEMA_VERSION = 3`, recovered from `git show beeb587:app/db.py`) run against a
real v4 store:

```
old init_db on a v4 store → SUCCEEDED
rows 2 → 2, relation byte-identical, all three indexes still present
schema_meta.version 4 → 3
```

That is the whole reason a code rollback here is cheap. **It is a consequence of
expand-only**, and it is exactly what a contract-phase release would destroy: once a
column is dropped, the previous release cannot read the new store, and rollback stops
being a `git checkout`. **The next scope that wants a destructive change must not do
it in the same release as the application change that stops using the column** — that
is the constraint this strategy buys, stated so it is not lost.

**One property is not a one-way ratchet, and it is worth knowing before it surprises
someone.** The old code *downgraded* `schema_meta.version` from `4` to `3` on the
store it found. Nothing broke — the relation and the indexes were untouched — and
re-running the new `init_db` restored `4` idempotently with all three indexes intact,
also measured (`rollback-runbook.md` §3, step A). So the recorded version tracks
*"what last ran"*, not *"the highest version ever reached"*. `deployment-pipeline-
questions.md` Q8 records whether that deserves a guard test; the decision belongs to
Code Generation, not to this stage.

---

## 4. What is atomic, and what is not

| Boundary | Atomic? | Measured behaviour |
|---|---|---|
| The schema step itself | **Yes.** One `BEGIN` … `commit`; any `BaseException` → `rollback()` → `raise` | `app/db.py:219-247`. Reproduced in this run: a store the step cannot preserve raised `sqlite3.IntegrityError: CHECK constraint failed: label IN ('positive','negative','neutral')`, and the store was left byte-identical — the row intact, no `analyses_pre_v1` table, no `schema_meta` created. Also `tests/test_migration_indexes.py:398` |
| Application startup | **Yes, in the sense that matters.** The migration runs in the lifespan *before* the server accepts anything | Measured: booting real `uvicorn` against the unpreservable store exited **1** and the port **never opened** — the operator sees "connection refused", not a half-served app |
| The process cutover | **No.** Two processes cannot be swapped atomically; there is a gap | The recreate strategy's one accepted cost |
| The commit/tag pair | **No.** A tag can be written against the wrong commit | `memory/team.md` § Way of Working's own reliance: *"the audit log preserves the full event sequence anyway"* — the provenance record is the committed audit shard, not the git history |
| The analytics read path | **Not applicable — and it is proven to write nothing.** | `tests/test_migration_indexes.py:442, 469`: row count, content hash and schema digest are unchanged across many requests, and the trace taken on the request's own connection contains no mutating statement |

**The failure signature to teach the operator**, because it is not what a failed
start-up usually looks like: **the port never opens.** Not a `500`, not a degraded
mode. A refused connection during a release is the migration failing, and the store
behind it is already back in its pre-release state.

---

## 5. Blast radius, stated precisely

| Question | Answer |
|---|---|
| Who can be affected? | **One person: the operator, on the machine the store lives on.** `memory/team.md` § Deployment; the app is unauthenticated by design and binds loopback only. |
| What is at risk? | **`data/sentiment.db` and nothing else.** No user data leaves the machine, no credential is written anywhere (`BR6.1`: the session store is process memory), and `config.local.toml` is gitignored and untouched by any release step. |
| What is the worst outcome? | A migration that cannot preserve a row **fails loudly and changes nothing** — measured above. The genuinely unrecoverable outcome is the one no code can prevent: **deleting the file**, because no commit contains a copy and there is no backup path. `cd-config.md` R5 exists for exactly that. |
| Is data egress part of this? | Only if the operator runs in live mode, and that is a runtime mode choice, not a release one: `POST /v1/analyze` sends the submitted text to OpenRouter. Unchanged by this release. |

---

## 6. The standard zero-downtime checklist, answered honestly

Every line is answered against this repository rather than ticked. A checklist whose
items are all N/A is still the correct instrument; a checklist with invented answers
is not.

| Item | Status |
|---|---|
| Load-balancer health checks with thresholds | **N/A — no load balancer.** The equivalent is the process exiting non-zero, which it does. |
| Connection draining / deregistration delay | **N/A — nothing registers anywhere.** |
| Graceful shutdown: finish in-flight requests, close DB connections | **Real, and already owned by the code.** `app/main.py`'s lifespan closes through `init_db`'s `finally: connection.close()`; each request closes its own connection in its own `finally` (`app/db.py` module docstring's invariant). **Not extended by this release and not claimed as a release property.** |
| Schema changes backward-compatible | **Yes, and measured** — §3. This is the release's central safety property. |
| Rollback plan tested and documented | **Yes** — `rollback-runbook.md`, with every load-bearing claim measured in this run rather than asserted. |
| Monitoring and alarms in place before deployment | **N/A — no process supervisor and no host to alert on.** Absence recorded so it is not read as coverage. |
| Pre-deployment smoke tests in a staging environment | **Replaced, not skipped.** There is no staging environment; the equivalent is R6's throwaway-store smoke (`cd-config.md` §5), which is the `express`-intent precedent reduced to its cheapest form. |
| **Deployment window / freeze period** | **Not designed.** `memory/team.md` § Way of Working: *"No maximum branch age has ever been affirmed and we are not inventing one."* A freeze calendar for a one-operator localhost release would invent a constraint nobody has. |

---

## 7. Feature flags: none, and the reason is structural

The stage definition asks for a feature-flag strategy. There is none, and this is not
an omission:

* **There is no flag mechanism in the code** — no flag module, no config key, no
  runtime toggle. Adding one would be a new feature with its own design and tests,
  not a deployment-strategy artifact.
* **There is nothing to gate.** The whole surface of this release is two read-only
  `GET` endpoints on a `/v2` router, and the pre-existing `/v1` contract is
  untouched — which is the actual risk-control mechanism here, and it is a
  **compatibility boundary, not a flag**. `memory/team.md` records the deciding
  interview answer: the `/v2` router is a *new versioned prefix*, leaving `/v1`
  exactly as it was.
* **The cost that makes flags wrong here is the store, not the code.** A flag protects
  a *code* path. The only thing this release changes that cannot be flagged off is
  the schema step, and a flag cannot help there — the migration runs at startup
  regardless of any toggle. It is made safe by being **additive and idempotent**
  (§3), which is a stronger guarantee than a flag would give.
* `C-5` forbids a new external service, which rules out AppConfig, CloudWatch
  Evidently and every other hosted flag system, and a self-rolled flag store would be
  new persistent state competing with the one file this project already treats as
  precious.

**Recorded as a reasoned absence with a named alternative** (the versioned-prefix
boundary plus expand-only schema change), not as "not needed".

---

## 8. What this strategy deliberately does not do

| Not done | Why |
|---|---|
| No traffic-shifting strategy of any kind | Nothing to shift — one process, one address, one operator. §1 |
| No canary analysis, no metric thresholds, no error-rate rollback trigger | There is no traffic and no monitoring. A rollback *trigger* would have to be "a human noticed", which is the recreate strategy's actual trigger. |
| No contract-phase schema change | §3. Shipping one would end code-level rollback compatibility, and nothing in this release needs it. |
| No second environment, therefore no "test the migration on staging first" | The throwaway-store smoke (R6) is the substitute, and it runs the *real* `app.main:app` through real `uvicorn` — measured. |
| No feature-flag system | §7 |
| No change to `app/main.py`'s bind, port or `run()` entry point | The release adds no interface. `G12` stays green because the bind is untouched. |
| No duplication of the CI gate set | `cd-config.md` §6 names the convergence with `u4-platform-packaging`'s `FR7.2` script as the intended destination rather than writing a second copy that could drift. |