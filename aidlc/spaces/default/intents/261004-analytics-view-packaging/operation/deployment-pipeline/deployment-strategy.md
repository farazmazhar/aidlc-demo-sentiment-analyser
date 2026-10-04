# Deployment Strategy — intent `261004-analytics-view-packaging`

> **Stage:** `deployment-pipeline` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Companion to:** `cd-config.md` (the procedure) and `rollback-runbook.md` (the recovery)
> **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/deployment-pipeline`
>
> **Inputs derived from:** the prior intent's `deployment-pipeline/*` · this intent's
> `construction/build-and-test/*` · `memory/team.md` § Deployment and § Way of Working ·
> `memory/project.md` · `app/db.py` · `app/main.py` · `app/config.py` · `Makefile`.
>
> **This is a design artifact.** It adds no file to the repository root.

---

## 1. What the strategy question means here

A deployment strategy answers: **how is the running thing replaced, and how is the
replacement reversed?** Here that is the strategy for **one process on one machine over
one file** — a distinct case, not a degraded one. Four of the five menu strategies
(blue/green, canary, rolling, A/B) are traffic-shaping strategies that presuppose two
versions serving requests. This app binds one address for one operator with no second
version running, so none applies.

| Fact | Where |
|---|---|
| One bind address, `127.0.0.1:8000`, enforced at startup | `app/main.py:45-46, 65` |
| A non-loopback bind **raises** rather than serving | `app/main.py:65` |
| No container, image, hosted service, IaC or orchestrator | `memory/team.md` § Deployment |
| No second human, no PR, no reviewer (a git remote exists but carries no CI workflow) | `memory/team.md` § Way of Working; measured at Deployment Execution |
| One durable file, gitignored, created on first run | `app/config.py`; `.gitignore` `/data/` |

---

## 2. Process strategy: **recreate**

The running process is stopped and a new one started on the new commit. No overlap, no
draining, no warm standby — there is nothing to drain to.

| Property | Value |
|---|---|
| Strategy | recreate |
| Trigger | a human, after R1–R4 pass (`cd-config.md` §3) |
| Unit of replacement | the commit, identified by the annotated scope tag |
| Overlap | none |
| Rollback cost | one `git checkout` plus one restart, **no data recovery** — this release carries no schema step (`rollback-runbook.md` §3) |
| Downtime | the interval between the two processes, on a single-developer local app with no traffic |

**Why not the alternatives.** Blue/green needs two environments — and here its cost is
double the local store, the one asset that cannot be recreated for free. Canary needs to
route a percentage of requests to a new version; there is one requester. Rolling needs
several instances behind a balancer; there is one process. A/B needs two variants.

---

## 3. Schema strategy: **unchanged this release**

`app/db.py:60` still sets `SCHEMA_VERSION = 4`. **This release adds no column, no table
and no index** — it changes static page assets (`app/static/index.html`,
`app/static/app.js`), adds repository-level tooling (`Makefile`, `requirements.lock`,
`.secrets.baseline`, `LICENSE`) and tightens `pyproject.toml`. `init_db` therefore runs
its idempotent no-op against a v4 store on startup, exactly as the prior intent measured.

**What that buys.** Rollback is a pure code rollback: the previous release's code and
this release's code read the same v4 relation, so a `git checkout` needs no data
migration in either direction. The expand-only discipline the prior intent established
still holds and is not disturbed here.

**The standing constraint, restated so it is not lost:** the next scope that wants a
destructive schema change must not ship it in the same release as the application change
that stops using the column — that would end code-level rollback compatibility.

---

## 4. What is atomic, and what is not

| Boundary | Atomic? | Behaviour |
|---|---|---|
| The schema step | Yes | One `BEGIN` … `commit`; any `BaseException` → `rollback()` → `raise` (`app/db.py`). Unchanged, and a no-op at v4. |
| Application startup | Yes, in the sense that matters | `init_db` runs in the lifespan before the server accepts anything. |
| The process cutover | No | Two processes cannot be swapped atomically; there is a gap. Accepted. |
| The commit/tag pair | No | A tag can be written against the wrong commit; the committed audit shard is the provenance record. |
| The analytics read path | Not applicable — proven to write nothing | The prior intent's tests assert row count, content hash and schema digest are unchanged across reads. |

**The failure signature to teach the operator:** a failed start-up here means **the port
never opens** — not a `500`, not a degraded mode. A refused connection during a release
is the migration failing, and the store behind it is already back in its pre-release
state.

---

## 5. Blast radius

| Question | Answer |
|---|---|
| Who can be affected? | **One person: the operator, on the machine the store lives on.** |
| What is at risk? | **`data/sentiment.db` and nothing else.** No user data leaves the machine; no credential is written anywhere; `config.local.toml` is gitignored. |
| Worst outcome? | A migration that cannot preserve a row fails loudly and changes nothing. The genuinely unrecoverable outcome is **deleting the file** — no commit contains a copy — which is why R4 copies it first. |
| Data egress? | Only if the operator runs in live mode; unchanged by this release. |

---

## 6. The standard zero-downtime checklist, answered honestly

| Item | Status |
|---|---|
| Load-balancer health checks | N/A — no load balancer. The equivalent is the process exiting non-zero. |
| Connection draining | N/A — nothing registers anywhere. |
| Graceful shutdown | Real, and already owned by the code; not extended by this release. |
| Schema changes backward-compatible | Yes — trivially, because there is no schema change. |
| Rollback plan tested and documented | Yes — `rollback-runbook.md`. |
| Monitoring and alarms before deployment | N/A — no process supervisor. Absence recorded so it is not read as coverage. |
| Pre-deployment smoke in staging | Replaced, not skipped — the throwaway-store smoke (`cd-config.md` §5). |
| Deployment window / freeze period | Not designed — a freeze calendar for a one-operator localhost release would invent a constraint nobody has. |

---

## 7. Feature flags: none, and the reason is structural

- There is no flag mechanism in the code; adding one would be a new feature.
- There is nothing to gate. The release's surface is a page change plus tooling; the
  frozen `/v1` contract is untouched, which is the actual risk-control mechanism — a
  compatibility boundary, not a flag.
- The one thing a flag could not protect — a schema step — is absent from this release.
- `C-4`/`C-5` forbid a new external service, ruling out AppConfig, CloudWatch Evidently
  and every hosted flag system.

Recorded as a reasoned absence with a named alternative (the versioned-prefix boundary
plus expand-only schema discipline), not as "not needed".

---

## 8. What this strategy deliberately does not do

| Not done | Why |
|---|---|
| No traffic-shifting strategy | Nothing to shift — one process, one address, one operator. |
| No canary analysis, metric thresholds or error-rate rollback trigger | There is no traffic and no monitoring; the trigger is "a human noticed". |
| No schema change of any kind | §3. |
| No second environment | The throwaway-store smoke is the substitute. |
| No feature-flag system | §7. |
| No change to `app/main.py`'s bind, port or run entry point | The release adds no interface. |
| No duplication of the gate set | `make verify` is the single source (`cd-config.md` §3). |
