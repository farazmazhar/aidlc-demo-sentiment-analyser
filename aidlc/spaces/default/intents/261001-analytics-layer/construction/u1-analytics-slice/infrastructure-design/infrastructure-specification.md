# Infrastructure Specification — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `infrastructure-design`
> (construction) · unit `u1-analytics-slice` (kind `service`).
>
> **Upstream inputs.** The accepted infrastructure-design assessment
> (`infrastructure-design-questions.md` Q1 option A — "no new questions; this unit
> adds no infrastructure"), the NFR design set beside this stage
> (`logical-components.md` §3 shared resources, §5 patterns declared inapplicable;
> `reliability-design.md` §4 the migration lifecycle; `security-design.md` §2 zero
> egress, §4 loopback enforcement at startup, §6 the dependency cap;
> `observability-design.md` §1 what exists and what does not), the functional
> design (`functional-spec.md` Workflow 3 the startup migration; `rules.md`
> `BR5.1`–`BR5.6`, `BR6.5`), the component catalogue and ADRs
> (`components.md` `Application Assembly`, `Persistence and Schema`; `decisions.md`
> ADR-006), and the affirmed practices in `memory/team.md` §Deployment,
> §Way of Working and `memory/project.md` (localhost-only; `C-5`/`C-6`).
>
> **This is a design artifact.** It records the deployment surface as it exists and
> the two startup behaviours this unit changes. It provisions nothing and invents
> no cloud resource, container, IaC tool or environment tier.

## What this file records

This unit adds **no infrastructure**. The deployment is one loopback `uvicorn`
process over one gitignored SQLite file: no container, no cloud resource, no IaC,
no hosted tier, no network boundary (`memory/team.md` §Deployment). The stage's own
skip condition — *"no infrastructure changes and infrastructure already defined"* —
largely applies, but the stage still owes its declared artifacts, so this file records the
deployment surface **as it exists**, the two startup behaviours this unit *does*
change, and what is deliberately **not** provisioned, rather than inventing
infrastructure to fill the tables.

| Aspect | This unit |
|---|---|
| Deployment surface | Unchanged: one loopback `uvicorn` process, one gitignored SQLite file. |
| What this unit changes | (1) the loopback bind becomes **enforced at startup**; (2) the additive v3 → v4 migration runs in one transaction that rolls back on failure. |
| What this unit provisions | **Nothing.** No new process, file, service, network boundary, hosted tier or dependency. |

## 1. Deployment

The deployment facets are unchanged by this unit; the table records them so a
later stage reads the surface rather than inferring it. The "change this unit
makes" column is the only column that moves.

| Facet | Choice | Rationale | Change this unit makes |
|---|---|---|---|
| **Compute model** | One local `uvicorn` process, run from a checkout (`uvicorn app:app --reload`). No container, no serverless, no VM, no second process. | `memory/team.md` §Deployment: "a commit is the release"; a localhost checkout is the entire deployment. | **None.** The run path stays one process; §2 makes the loopback bind it consumes enforced. |
| **Networking topology** | Bound to loopback `127.0.0.1` only. No VPC, no subnet, no ingress, no egress, no load balancer, no TLS termination. | `NFR2.1`, `C-10`, the affirmed "ALWAYS keep the app localhost-only"; no network hop exists in the read path (`BR2.8`). | **Hardened, not changed in shape.** The loopback bind is now enforced at startup so a non-loopback host fails loudly (§2.1, `NFR2.4`). |
| **Storage strategy** | One gitignored SQLite file (`data/sentiment.db`), created on first run, owned by `Persistence and Schema`. No managed database, no replica, no volume, no object store. | `memory/team.md` §Deployment "Local data and recovery"; `entities.md` — `StoredAnalysis` is the only persisted shape. | **Schema migrated additively** v3 → v4 with three named indexes, in one rollback-on-failure transaction (§2.2, `NFR4.5`). No new file, no new store. |
| **Environments** | **None.** There is no dev/staging/prod tier. The only runtime distinction is the engine *mode* (offline dummy vs live OpenRouter) resolved from settings, which is application configuration, not an environment tier. | `memory/team.md` §Deployment: the framework default (deploy on merge to staging behind a production gate) "has no counterpart here, because the environments it assumes do not exist". | **None.** |
| **IaC approach** | **None.** No CDK, Terraform, CloudFormation or Pulumi. A commit is the release; the "infrastructure" is the checkout and the file it creates. | `C-5` forbids a new external service or cloud component; `memory/team.md` §Deployment names no IaC. Authoring IaC for one loopback process over one local file would provision the very tiers the practices forbid. | **None.** |
| **Resource sizing** | The process runs at the developer's host size; the only sizing-shaped quantity in the design is the **performance fixture** (10,000 rows / 365-day span), which is a test working set, not a provisioned tier. | `scalability-design.md` §1 ("Capacity plan: none exists and none is invented"); `performance-design.md` §1. | **None.** The fixture is a `u1` test instrument, not capacity to provision. |
| **Runtime dependencies** | Exactly two declared: `fastapi`, `uvicorn`; every dev tool in the `dev` extra. Resolution pulls transitives, but the declared list is capped at two. | `C-6`, `memory/project.md` mandate "declare runtime dependencies as exactly two"; enforced by `tests/test_config.py`. | **None.** This unit declares no new runtime dependency (`NFR2.6`); the dependency-cap assertion stays green. |

**The only documented run path.** `python -m pip install -e ".[dev]"` then
`uvicorn app:app --reload` (`memory/team.md` §Deployment). The released artifact is
the squashed commit tagged with the scope name (`memory/team.md` §Way of Working).
This unit changes neither.

## 2. Startup contract this unit changes

This unit provisions nothing, but it **does** change two behaviours that run at
startup. Recording them here is the honest content of this stage: they are the only
infrastructure-relevant surfaces the unit touches.

### 2.1 Loopback bind enforced at startup (`NFR2.4`)

**Change: the run path consumes the `HOST` constant and refuses to serve a
non-loopback host, failing with an explanation at startup.**

| Aspect | Recorded behaviour | Source |
|---|---|---|
| What is enforced | A loopback host (`127.0.0.1`) is the only bind the run path accepts; a non-loopback host fails loudly rather than serving an unauthenticated app. | `NFR2.4`, `BR6.5`, `FR7.6` |
| Why it is an infrastructure concern | It is the process-exposure boundary — the one place the app's network surface is decided. Enforcing it at startup is a deployment-surface decision, not request-time code. | `security-design.md` §4; `logical-components.md` LC-4 |
| Why the current state is insufficient | `HOST = "127.0.0.1"` (`app/main.py:36`) is asserted by a test but has **no call site in the run path**; the documented invocation uses uvicorn's own default, so `uvicorn app:app --host 0.0.0.0` would expose the app while every test passes. A documented default is documentation, not enforcement. | `memory/team.md` §Deployment "Loopback is now enforced rather than documented" |
| Normal path unchanged | A loopback run is the normal local run, unchanged. | `BR6.5` |
| Instrument | The startup-enforcement test (`FR7.6`): supplying a non-loopback host must make startup fail with an explanation; a constant-only assertion is insufficient (`BR6.5`). | `NFR2.4` |

No new port, no new interface, no new network boundary is created — one existing
constant (`HOST`) is promoted from a tested value to a consumed, enforced value.

### 2.2 Additive v3 → v4 migration, atomic (`NFR4.5`)

**Change: `init_db` performs an additive, idempotent v3 → v4 step and creates three
named indexes, all inside one transaction that rolls back and re-raises on
failure.**

| Aspect | Recorded behaviour | Source |
|---|---|---|
| Subject | The existing gitignored SQLite file — its schema only. No new file, directory, engine or store is introduced. | `components.md` `Persistence and Schema`; `logical-components.md` §3 |
| Additive / idempotent | No column dropped, renamed or retyped; no row discarded or rewritten. A store already at v4 changes nothing. Because the test harness re-enters the lifespan on every in-process request, idempotency is exercised on every request. | `BR5.1`, `BR5.2` |
| The three indexes | Created by name — `idx_analyses_created_at`, `idx_analyses_import_id`, `idx_analyses_label_created_at` — and explicitly re-created after the table-rebuild path (the TD-1 index-survival fix). | `BR5.3`, `BR5.4` |
| Atomicity | The version bump to 4 lands in the **same transaction** as the step; any step that cannot preserve every row rolls back and re-raises, so startup halts loudly rather than serving on a half-migrated store. | `BR5.5`, `reliability-design.md` §4 |
| Instrument | The migration tests (`BR5`) and the `sqlite_master` index-survival assertion (affirmed practice: always assert indexes survive a migration). | `NFR4.5`, `memory/project.md` mandate Q14 |

This is a schema change to an existing local file, not a provisioned data tier.
There is no backup path, no replication and no rollback procedure to write, because
there is no deployment (`reliability-design.md` §5).

## 3. Infrastructure Services

**None.** The stage's Infrastructure Services section is keyed by service (role =
database / cache / queue / search / cdn / dns / load-balancer). This unit adds none
of them. The table below names each service family the stage anticipates and records
the absence with its reason, so an absent row is not mistaken for an oversight.

| Service family | Provisioned? | Why not |
|---|---|---|
| **Database (managed)** | **No.** | The store is one local SQLite file owned by `Persistence and Schema`, created on first run. No managed engine, no replica, no failover. The v3 → v4 migration (§2.2) changes the existing file's schema; it does not introduce a database service. |
| **Cache** | **No.** | `performance-design.md` §3: the data is a local file read once per request; a cache would add an invalidation lifecycle for no measured gain. `A2` records no cache exists. |
| **Message queue / broker** | **No.** | `scalability-design.md` §3: the read path is synchronous request → read → respond with no outbound call and no background work (`BR2.8`); `C-5` forbids a broker. |
| **Search service** | **No.** | Term extraction is in-process tokenising and counting over the stored text (`TermExtraction`); no search index or engine is added. |
| **CDN / static asset distribution** | **No.** | The view and its one script are served by the same loopback process via FastAPI `StaticFiles` (`app/main.py` `mount("/static", …)`); there is no public edge and no network boundary. |
| **DNS** | **No.** | The app is reached at `127.0.0.1`; there is no name to resolve and no hosted endpoint. |
| **Load balancer** | **No.** | `scalability-design.md` §3: there is no second instance to balance to; the run path is a single documented `uvicorn app:app` invocation. |
| **Object store** | **No.** | `C-5` forbids a new external service; durable state is the single gitignored SQLite file. |

**External dependencies the unit *reads through* (not provisioned here).** SQLite
(the local file), FastAPI and uvicorn are the runtime dependencies named in
`components.md`; this stage provisions none of them — they are installed from the
manifest and started by the run path.

## 4. Shared Infrastructure

**No shared infrastructure is introduced.** The stage's Shared Infrastructure
section is CONDITIONAL — only for resources shared across multiple units. The
`feature` scope resolves to four units; this unit provisions no resource another
unit consumes.

The two resources shared **inside** this unit's boundaries are already designed in
`logical-components.md` §3 and are not infrastructure to provision:

| Shared resource | Owner | Consumers | Access boundary | Provisioned here? |
|---|---|---|---|---|
| The SQLite file (one per deployment) | `Persistence and Schema` (not this unit) | LC-1 read module (reads), LC-2 connection owner (opens/closes), LC-4 startup (migrates) | One short-lived connection per request; single-writer-at-startup; no pool, no cache, no second writer | **No** — the file already exists and is created by the existing `init_db`; this unit only migrates its schema. |
| The per-request `sqlite3.Connection` | `HTTP API Surface` (`get_connection`, LC-2) | LC-1 (borrows via parameter), LC-3 (hands over) | One connection per request, closed at the request boundary; never shared between concurrent requests | **No** — an in-process object, not an infrastructure resource. |

## 5. What is NOT provisioned, and why

Each line below is a deliberate absence with a named reason. An absent design with
a stated reason is a decision; an absent design with no reason is an oversight.

| Not provisioned | Reason |
|---|---|
| **Container image / Dockerfile** | `memory/team.md` §Deployment: no container, no published image. A commit is the release; the process runs from a checkout. `C-5` forbids a new hosted/cloud component. |
| **Cloud provider resource** (compute, managed DB, bucket, queue, CDN, etc.) | `C-5` and the project mandate "NEVER introduce a new external service, hosted dependency, cloud component or network call"; `memory/team.md` §Deployment names no cloud. |
| **IaC tool** (CDK / Terraform / CloudFormation / Pulumi) | There is nothing to define as code: one loopback process over one local file. Authoring IaC would provision the tiers the practices forbid, and `C-5` rules out the cloud surface it would target. |
| **Environment tiers** (dev / staging / prod) | `memory/team.md` §Deployment: the framework default assumes environments that do not exist here. The only runtime distinction is the engine mode, which is application config, not a tier. |
| **Network boundary** (VPC, subnet, security group, NACL, load balancer, TLS terminator, ingress) | The process binds loopback only; there is no public surface, no east-west traffic and no TLS hop. `NFR2.1`/`C-10` keep it that way; §2.1 enforces it. |
| **Monitoring / metrics / tracing / alerting stack** | **No monitoring tier exists and `C-5`/`C-6` forbid adding one.** See `monitoring-design.md` for the full record and the stand-in (module-logger failure records). |
| **CI runner / pipeline infrastructure** | There is no CI and no git remote (`memory/team.md` §Way of Working, §Deployment). The pipeline work belongs to the `u4-platform-packaging` verification script and the CI Pipeline stage. See `cicd-pipeline.md`. |
| **Secrets manager / vault** | `NFR2.5`: the analytics path carries no credential. Live-mode credentials already live only in the gitignored `config.local.toml` and process memory (affirmed NEVER rule); this unit adds no secret and no secret store. |
| **Backup / replication / failover / HA mechanism** | `reliability-design.md` §5: no SLA, no replica, no failover; deleting or restoring the local file is the accepted recovery (`memory/team.md` §Deployment). |
| **New runtime dependency** | `C-6` caps declared runtime dependencies at exactly two (`fastapi`, `uvicorn`); this unit is stdlib- and existing-dependency-only (`NFR2.6`). |
| **New configuration value** | `BR2.15`: the analytics layer adds no new configuration value; all behaviour is computed or a request parameter. |

## 6. Traceability

This file records the deployment surface and the two startup behaviours; the NFR
IDs it touches are enumerated in `traceability.json`. The index is:

| NFR (this unit) | What this file records |
|---|---|
| `NFR2.4` | §2.1 — loopback bind enforced at startup; non-loopback host fails loudly. |
| `NFR4.5` | §2.2 — additive, idempotent, atomic v3 → v4 migration; three named indexes; loud rollback. |
| `NFR2.2`, `NFR2.6` | §1 (runtime dependencies, no new egress) and §5 (nothing cloud/hosted provisioned). |
| `NFR3.1`, `NFR3.2` | §3/§4 — the read path provisions no service and mutates no store beyond the startup schema step. |
| `NFR1.*`, `NFR9.*`, `NFR8.*`, `NFR4.1`–`NFR4.4`, `NFR4.6`, `NFR4.7` | **No infrastructure dimension** — request-time behaviour, not a provisioned resource. Recorded `N/A` with justification in `traceability.json`. |

Full id-level enumeration is in `traceability.json`.
