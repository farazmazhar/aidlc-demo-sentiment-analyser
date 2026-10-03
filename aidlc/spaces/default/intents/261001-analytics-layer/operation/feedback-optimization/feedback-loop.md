# Feedback Loop — intent `261001-analytics-layer`

> **Stage:** `feedback-optimization` (operation, final stage) · lead `aidlc-operations-agent`
> support `aidlc-aws-platform-agent` · **Date:** 2026-10-03
> **Release the findings come from:** commit `aa0b1e4`
> **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/feedback-optimization`
>
> **This is the input to the next Ideation cycle.** It is not a wish list. Every
> item below exists because a measurement in this record produced it, and every
> item names that measurement, the requirement it relates to *or the absence of
> one*, a concrete change, a rough size, and an owner.
>
> **Upstream inputs consumed:** `observability-setup/slo-config.md` (`slo-config`) ·
> `observability-setup/dashboards.md` (`dashboards`) ·
> `observability-setup/alarms.md` (`alarms`) ·
> `observability-setup/log-queries.md` · `observability-setup/anomaly-config.md` ·
> `deployment-execution/deployment-log.md` (`deployment-log`) ·
> `deployment-execution/health-check-report.md` ·
> `deployment-execution/smoke-test-results.md` ·
> `performance-validation/test-results.md` — cited under this stage's declared slug
> `load-test-results` · `performance-validation/nfr-validation-matrix.md` ·
> `performance-validation/load-test-plan.md` ·
> `incident-response/incident-plan.md` (`incident-plan`) ·
> `incident-response/runbooks.md` · `incident-response/escalation-matrix.md` ·
> `environment-provisioning/validation-report.md` (F-01…F-04, V-05…V-44) ·
> `environment-provisioning/environment-inventory.md` (M1–M5) ·
> `deployment-pipeline/rollback-runbook.md` (RB1/RB2/RB3) ·
> `deployment-pipeline/cd-config.md` (R1–R8) ·
> `construction/ci-pipeline/ci-config.md` · `construction/ci-pipeline/quality-gates.md` ·
> `construction/build-and-test/test-results.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md` (§R-02, §R-09) ·
> `verification/phase-check-construction.md` (the **FAIL** verdict) ·
> `inception/requirements-analysis/requirements.md` (FRs, NFRs, Revisions 1–2) ·
> `inception/units-generation/unit-of-work.md` ·
> `inception/contract-design/contract-summary.md` (open point O9) ·
> `memory/project.md` `## Forbidden` / `## Mandated`;
> `memory/team.md` § Deployment, § Testing Posture, § Way of Working.

---

## 1. The ranking rule, stated before the ranking

**Ranked by consequence, not by ease.** Consequence is defined as: *how badly does
this hurt if nobody ever fixes it, weighted by how likely it is to occur given how
this system is actually used?* Three consequences weigh more than everything else
in this project, and they set the top of the list:

1. **Unrecoverable loss of the only durable state.** The project holds one
   gitignored SQLite file. There is no replication, no backup mechanism, no
   migration tool and no second copy (`runbooks.md` §9, `validation-report.md` V-25).
2. **The feature is one quarter delivered**, and its own boundary verdict says so.
3. **A single stray process takes the whole read surface down.**

The ordering deliberately does **not** track effort. **BL-03 is a one-line change
and it ranks third**; the lockfile (**BL-14**) is larger and ranks fourteenth. That
is the rule working, and §5 states the traps a size-first ranking would have
created.

**Size** is rough and in this project's own terms — the team's cadence is
"coarse and milestone-shaped", one squashed commit per scope — so:

| Size | Meaning here |
|---|---|
| **XS** | under an hour; a habit, a doc correction, or a one-line source change |
| **S** | under half a working session; a small isolated code change or a new repository file |
| **M** | about one session; a new module, a new gate, or a contract change |
| **L** | more than one session; a new Unit or a re-run of an Inception/Construction stage |
| **—** | not a change; recorded so it is not re-investigated |

**Owner** is the stage or role that *owns the decision*, which is not always the
role that writes the code. Where the record already names an owner, that name is
used verbatim.

## 2. The ranked backlog

Twenty items. The consequence band each sits in is stated, so a reader who
disagrees with one ranking can see exactly what argument to have.

| # | Item | Consequence band | Requirement | Size | Owner |
|---|---|---|---|---|---|
| **BL-01** | **Finish the three unbuilt Units.** 1 of 4 built; boundary verdict **FAIL**; 11 findings, 9 blocking; `NFR4.6` and `NFR4.7` ship **unverified**; `AC6.2.1` satisfied by neither owning Unit | **The feature does not work as specified** | 46 `AC` ids and 22 `FR` ids with no coverage; `NFR4.6`, `NFR4.7` | **L** | `u2-term-extraction`, `u3-analytics-view`, `u4-platform-packaging`; **Delivery Planning** for the Bolt-order re-run |
| **BL-02** | **Create a backup mechanism.** Zero commits contain `data/`; exactly **one** manual copy exists (`data/sentiment.db.bak-aa0b1e4`, created by luck during release step R5); no scheduler, no `VACUUM INTO`, no `iterdump`, no `.backup()`, no off-machine copy | **Total, unrecoverable loss of every row written since that instant** | **none** — `infrastructure-specification.md` §5 records backup as *not provisioned*, which is a decision, not a requirement | **S** | the human (a `cp -p` habit) + `u4-platform-packaging` for anything durable |
| **BL-03** | **Set a `busy_timeout` on the analytics connection.** One competing writer takes **100 %** of the read surface down for the full **5.0 s** | **Total read-surface outage from one stray `sqlite3` shell** | **none** — `NFR9` records single-user operation; `runbooks.md` IR-1 documents the mode and sets no target | **XS** | `u1-analytics-slice` (a follow-on code-generation pass at `app/db.py:213`) |
| **BL-04** | **Decide what the export surface is for.** `import_id` is required, `import_id IS NULL` rows are excluded, and `EXPORT_COLUMNS` omits `probabilities` and `intensity` — so **single-analysis rows are structurally unreachable**, which is the normal way this app is used | **The only copy surface cannot copy the normal data**; measured 1 of 3 rows returned, and `404 IMPORT_NOT_FOUND` on a store where `/v2/analytics/summary` returned `total: 2` | `FR2.5`, `FR2.6` — **working as written**; there is simply no requirement anywhere that anything be recoverable | **M** | **Requirements Analysis** (a new FR) + `u1-analytics-slice` |
| **BL-05** | **Close the `uvicorn --host` bypass.** `resolve_bind_host("127.0.0.2")` refuses, `create_app(host="127.0.0.2")` refuses — yet `uvicorn app:app --host 127.0.0.2` **bound and served `200` with no refusal logged** | **An unauthenticated app holding the operator's OpenRouter key, reachable off-machine, with no record of how the process was started** | `FR7.6` / `NFR2.4` / `BR6.5` are **Met as written** — the enforcement is correct *where it is reached*; `project.md` mandates it "so a non-loopback host fails loudly" | **S** | `u1-analytics-slice` + a **scope decision** (**OQ-3**) |
| **BL-06** | **Give the concurrency behaviour a requirement.** Six measured findings, no NFR parent, no gate, no target, no owner | **The project's most consequential measured behaviours are unguarded** | **none** — `performance-requirements.md` § "Concurrency posture" *declines* to sub-number it because that would invent a parent the inception set does not contain | **L** | **Requirements Analysis** in the next Inception phase |
| **BL-07** | **Cap, paginate or bound the unbounded series.** `7 011 966 B` / `36 500` entries at p99 **199.700 ms** — **0.3 ms inside** budget; `IR-7` recorded 4 of 5 repeats **over** at a median of 240.7 ms | **A single query parameter can request 7 MB and sit on the 200 ms boundary**; ~192 B per series entry, linear in the requested range | `NFR9.3` **deliberately imposes no cap** — so this is a contract change, not a fix | **M** | `u3-analytics-view` (**OQ-1**) |
| **BL-08** | **Close the four observability gaps** (OG-1…OG-4): a `422` emits **no** application record (6 → 0); a failed startup emits **no `app.*` record** (only `uvicorn.error`); the access line carries **no duration field**; `/v1/health` answered `200` in **1.4 ms** while every analytics read was `500` | **Every incident is harder to diagnose than it needs to be**; latency is never recorded by the system at all | `NFR8.1`/`NFR8.2` are `Met` — for the codes and paths the tests exercise. `NFR8.2` **names both** `VALIDATION_FAILED` and `STORAGE_FAILURE`; only the second reaches the log | **S** (four one-to-three-line changes) | `u1-analytics-slice`; **OG-1 also needs a policy decision** (**OQ-2**) |
| **BL-09** | **Make `/terms` stop being the hot spot.** Alone at `c` = 8 it manages **8.60 rps** at p50 **921.9 ms** and **305.88 ms** of CPU per request, versus `summary`'s **46.98 rps** at 56.58 ms | **The mixed page load breaches the 200 ms budget 5×** (p95 952.7 ms), reproducibly | **none** beyond BL-06's parent | **M** | `u2-term-extraction` (owns `TermExtraction`) — the cost is per-row pure Python under one GIL |
| **BL-10** | **Tighten the store's file mode** from measured **644** to **600**. It holds submitted text, unencrypted, world-readable on this host | **Local confidentiality of the only durable state** | **none** — `anomaly-config.md` A12 records the expected value; `team.md` records the unencrypted posture as deliberate | **XS** | the human (**OQ-4**) — it changes a file on the operator's machine |
| **BL-11** | **Log to files at startup**: `… > access.log 2> app.log` | **Right now every grep in `runbooks.md` §13 cannot work**, because the two streams interleave in one terminal | **none** | **XS** | the human (**OQ-5**) / `u4-platform-packaging` for the script |
| **BL-12** | **Correct three artifacts measurement disproved**: `health-check-report.md` §2.3 names `python -m app.main` as a documented run path and it **does not serve** (no `__main__` guard; exits 0, no listener — re-verified twice this stage); `rollback-runbook.md` **RB1**'s stated trigger never fires, because a v3 store boots clean since the current relation already *is* v1-shaped; `cd-config.md` §5 over-generalises the store hazard (**F-01**) | **A 1am operator loses an incident to a command that silently exits 0; a runbook's own rehearsal cannot reproduce its trigger** | **none** — these are record defects, not requirement defects | **XS** | **Deployment Execution** (`health-check-report.md`), **Incident Response** (`rollback-runbook.md`), **Deployment Pipeline** (`cd-config.md`) |
| **BL-13** | **Decide repository hosting.** `git remote -v` is empty; no `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`, `.circleci/`, `azure-pipelines.yml` | **The `feature` scope's "CI execution before merge" is unsatisfiable**; every gate runs by hand and blocks nothing; a commit not in local history is **unrecoverable** | `memory/org.md` § Testing Posture, for `feature`; `FR7.2`'s script is the thing any job would call | **S** (the human) + **M** (`u4`) | the human (**Q1**) → `u4-platform-packaging` |
| **BL-14** | **Ship the lockfile with hashes.** No lockfile, no constraints file, no `requirements.txt`; system `ruff` **0.16.9** vs fresh-venv **0.16.10**; `setuptools` is **not an installed distribution at all**, so PEP 517 downloads it unpinned and unhashed on every install and **executes `setuptools.build_meta` as code** | **The suite's pass/fail state is a function of the resolved dependency set, not of the code** | `FR7.1` | **S** | `u4-platform-packaging` |
| **BL-15** | **Land `tools/security_static_checks.py` and `tools/security_dast_probe.py` as repository files**, and give `pyproject.toml` a machine-readable report so the coverage-delta gate becomes buildable | **Two blocking security gates that no one can run, ever** — they exist only as heredocs inside an artifact — and the first gate of the standard quality set is **unbuildable** (no `--junit-xml`, no coverage XML, no `-ra`) | `quality-gates.md` G9, G10; `FR7.2`; the delta gate is *"the first gate of the standard quality-gate set"* per `team.md` | **S** | `u4-platform-packaging` |
| **BL-16** | **Make the record's declarations checkable between stages.** Every drift item in `drift-report.md` §3–§5 was found by a stage *reading a declaration and running one check* — not by any mechanism | **The next scope will re-derive all of it, or inherit it as fact** | **none** — `memory/team.md` § Enforcement Summary: *"An unrun gate is not a gate; a documented default is not enforcement."* | **M** | **Delivery Planning** (decide what is checked when) + `u4-platform-packaging` (a script to check it) |
| **BL-17** | **Reconcile `verification-command.txt`.** Step 1 is `python -m pip install -e ".[dev]"`, which **exits 1** under PEP 668 on this host's externally-managed `/usr/bin/python3.14`; proven pre-existing on a pristine clone of `HEAD`. Steps 2 and 3 pass verbatim | **A human-approved artifact fails its first step on every externally-managed host**; the remedy exists (a venv, exit 0) and was deliberately not applied | the artifact is human-approved, so Build and Test could not edit it | **XS** | the human, via **Delivery Planning** (`Q6`) |
| **BL-18** | **Correct `FR7.3`'s fixture count.** The requirement says "the **four** known fake-key fixtures"; `team.md` said four; a review counted six; **F-03 measured seven** distinct `sk-or-v1-*` literals — all placeholders, zero real credentials | **An allowlist built from "four" leaves three fixture literals as false positives on the first run** — i.e. the first secret scan produces noise | `FR7.3` (open in `requirements.md` § Open Questions: *"until then, state no number"*) | **XS** | **Requirements Analysis**, then `u4-platform-packaging` |
| **BL-19** | **Establish whether 147–186 MB RSS is a plateau or a slow leak.** Measured this stage: 55 940 kB at boot → 67 728 kB after 71 requests and five 7 MB responses; descriptors **7 → 7**, threads **1 → 2**, no leak. Recorded steady state after thousands of requests: **147–186 MB** | **Unknown memory behaviour under real sustained use** — and `load-test-results` §14 says so itself: *"a 342-second soak cannot detect a slow leak"* | **none** | **S** | the next scope's **Performance Validation** |
| **BL-20** | **Decide the store's retention story.** No retention policy, no delete endpoint; rows live until the operator deletes the file or round-trips a CSV. Measured **266.2 B/row** on a 32 768 B fixed base | **The only cost surface that grows with no caller-imposed bound, and nothing tells the operator** | **none** — `NFR9` names the unbounded series but not row growth | **M** | **Product / Requirements** in the next Ideation cycle |

### 2.1 The top of the list, restated as sentences

1. **The feature is a quarter built and its own boundary check says so.**
   `verification/phase-check-construction.md` records **❌ FAIL**, 11 unresolved
   findings with a named owning stage each, **9 of them blocking** — and 46 `AC` ids
   and 22 `FR` ids with no coverage at all.
2. **The only durable state has no backup mechanism** — one manual copy, taken by
   luck during a release, byte-identical to a file that now has **0 rows**.
3. **One stray process can take the whole read surface down** for five seconds,
   with a **100 %** failure rate, because `app/db.py:213` sets no `busy_timeout`
   and CPython's **5 000 ms** default applies (re-verified this stage).
4. **The only copy surface cannot copy the normal data** — `import_id` is required,
   `import_id IS NULL` rows are excluded, and `probabilities` and `intensity` are
   not exported.
5. **An unauthenticated app holding the operator's API key can be bound off
   loopback**, and nothing records how the process was started.

## 3. Items 1–5: the consequence band that outranks effort

**These five are not a "critical" priority list chosen for impact. Each one is a
place where the project's own records say something that measurement contradicts,
or where the project's own metrics show a total failure.**

### BL-01 — Finish the three unbuilt Units

**Measured:** 1 of 4 Units built. `u2-term-extraction` (9 absent `AC` ids),
`u3-analytics-view` (19), `u4-platform-packaging` (18). The cross-Unit FR/NFR/AC
gate's own recorded verdict is `❌ FAIL — as written`: **215 ids enumerated, 83
covered, 131 uncovered.**

**Two halves, and the honest one is the second.** Cause 1 is that **no `FR` id is
ever a row in a code-generation traceability**, so the gate's literal condition
*cannot be satisfied for any `FR`, in this repository, for any Unit* — a
reporting-shape defect in `code-generation`'s traceability contract. Cause 2 is
that the enumerated set is intent-wide and only Bolt 1 of 4 exists. **Cause 2 is
"the honest one."** Within U1's own scope the coverage is sound: **83 of 84** `AC`
ids `OK`, and **all 152 `OK` targets resolve to files that exist on disk, 0
missing.**

**Two targets ship unverified and the record says so twice rather than closing
them with an invented instrument.** `NFR4.6` (per-section graceful degradation) and
`NFR4.7` (no silent retry; a superseded range's out-of-order response discarded)
both need markup that `u3-analytics-view` ships. Build and Test walked its full
failure ladder and the human chose **A — Accept: carry both into `u3`**, which
supplies the missing *ownership* rung without reclassifying either as `Met`.
`performance-validation` then reported `Unverified` **a second time** rather than
building an instrument against another Unit's markup — and in doing so walked past
a genuine partial outcome in `P3` (`/terms` answered `200` while `/summary` had
already answered `500`) and correctly declined to call it the `NFR4.6` instrument.
**That judgement is worth carrying into the next scope: two open targets cost less
than a second disclosed boundary violation.**

**One boundary violation is live and disclosed.** `app/terms.py` was authored by
U1 against three inception artifacts; a `U1 → U2` import edge is live at
`app/analytics.py:41`; and the **stopword set is U2's decision** (contract open
point **O9**) which U1 has already chosen and test-pinned. The correct order — U2
before U1's terms path — is *"not reachable from inside the current engine
state"*, so it needs a **Delivery Planning re-run** to move the Bolt sequence.

### BL-02 — Create a backup mechanism

**Measured, and the measured state is more precise than "no backup":**

| Claim | Measured |
|---|---|
| Any commit contains the store | **0** — `.gitignore:94:/data/` |
| Copies of the store on this machine | **exactly 2**, both under `data/`, both sha256 `c8be1361…`, both **32 768 B** |
| Where the second came from | release step **R5**, a manual `cp` taken at 19:53 on 2026-10-03 |
| Any schedule, retention or second copy | **none** |
| Any off-machine or second-host copy | **none** |
| Any backup tool | **none** — no `scripts/`, no `VACUUM INTO`, no `iterdump`, no `.backup()`, no `shutil.copy2` (re-verified this stage) |

**The accurate sentence is `runbooks.md` §9's:** *there is no backup **mechanism**;
there is exactly one manual copy, taken once, at a known instant, and it is
byte-identical to the store it protects.* **And the copy is of an empty store** —
`validation-report.md` V-11 and `health-check-report.md` §4.1 both read
**`rows = 0`**. So today it protects nothing, and it will protect exactly the
snapshot it holds, forever.

**Why this ranks second despite being a one-line habit.** The asymmetry is
measured and it is stark: **RB2** (roll back the code) costs one `checkout` and one
restart and needs no data recovery, because the `v3 → v4` step is expand-only.
**RB3** (recover the file) costs **everything**, because nothing else holds a copy.
A 30-second precaution converts a potential catastrophe into a non-event — which is,
in `runbooks.md` §10's words, *"the strongest argument in this project for treating
`cp` as part of starting the app rather than as an optional nicety."*

**What is genuinely unrecoverable, per `runbooks.md` §9, and stated in full because
the honest answer is the useful one:** (1) any row written since the last manual
copy; (2) **every row written by single analysis, unconditionally** — see BL-04;
(3) `probabilities` and `intensity`, even from a successful export; (4) the
incident history, since there is no log retention, no aggregation and no shipping.

### BL-03 — Set a `busy_timeout` on the analytics connection

**Measured, three independent times by three stages:** `runbooks.md` IR-1
(5005.26 ms), `load-test-results` `S9` (p50 **5007.942 ms**, **6 of 6** reads `500`),
and this stage's confirmation that `PRAGMA busy_timeout` on this interpreter
returns **5000 ms** while `app/db.py:213` — the **only** `sqlite3.connect` site in
the application, per its own module docstring — sets none.

**The consequence is total, not partial.** One process holding `BEGIN EXCLUSIVE`
makes **100 %** of reads fail, every one of them, for the full timeout.
`load-test-results` §11 adds the dimension IR-1 lacks: **a single writer takes the
whole read surface down, not a fraction of it.**

**Three things this project already knows that make it cheap to fix and expensive
to leave:** the recovery is automatic (a retry succeeded **2.63 s** after a failure
while the holder was still exiting), so `runbooks.md` IR-1's instruction is *"do
not restart — waiting fixes it and a restart does not"*; the application raises a
clean, distinguishable `500 STORAGE_FAILURE` with its machine code on the envelope,
in the module log **and** on the access line, so the failure is never mistaken for
emptiness; and `runbooks.md` §3 already carries the exact diagnosis procedure.

**What the fix is not.** It is not a retry loop, not a circuit breaker, and not a
queue. The change is one keyword on one connection. The *decision* of what value is
a design choice — and the honest constraint is that a `busy_timeout` makes a read
*wait* rather than fail fast, so the right value trades a longer worst-case wait
against a lower failure rate. **That is a requirement decision, which is why this
item is paired with BL-06.**

### BL-04 — Decide what the export surface is for

**Measured, on real stores, by the incident-response stage, and confirmed by code
read this stage:** `GET /v1/analyses/export` takes `import_id: str = Query(...)` —
**required**; `app/repository.py:100` filters `WHERE import_id = ?`, so rows with
`import_id IS NULL` are **structurally unreachable**; and `EXPORT_COLUMNS`
(`app/routes.py:86`) is `("id","text","label","confidence","model","provider",
"created_at")` — **`probabilities` and `intensity` are not exported.**

**The consequence, measured:** on a 3-row store the export returned **1** of 3 rows.
On a 2-row store with no import at all it returned **`404 IMPORT_NOT_FOUND`** —
**while `/v2/analytics/summary` on the same store returned `total: 2`.** The data
is readable and simultaneously unreachable by the only copy surface.

**This is the sharpest item in the backlog, because the export's *own* behaviour is
correct.** `FR2.5` requires the parameter; `FR2.6` states that rows written by
single analysis are never included; both are `Met`. **The gap is that no
requirement anywhere says the operator's history must be recoverable** — and
`import_id IS NULL` is *precisely* the normal way this app is used, since
`POST /v1/analyze` is the everyday path and `POST /v1/analyses/import` is the
occasional one. **A backup surface that excludes the common case is a view, not a
backup, and the requirement set never asked for a backup.**

**The change is therefore a requirements change, not a code fix:** either a new FR
that mandates an exportable whole-store surface with an explicit column list, or an
explicit decision that the export is an *import-group* feature and the operator
accepts BL-02's consequence. **What must not happen is a unilateral code change** —
that would break `FR2.5` and `FR2.6`, which are `Met`.

### BL-05 — Close the `uvicorn --host` bypass

**Measured, and upgraded from code-reading to measurement by two stages.**
`alarms.md` §3.1, on `127.0.0.2` — a host inside `127.0.0.0/8`, which Linux routes
to `lo`, so nothing is exposed off-machine in that specific test:

```
resolve_bind_host("127.0.0.2")   -> REFUSED (NonLoopbackBindError)
create_app(host="127.0.0.2")     -> REFUSED, before any lifespan ran
--- but the uvicorn CLI ignores both ---
LISTEN 0  2048  127.0.0.2  0.0.0.0:*  users:(("python",pid=176689,fd=6))
GET http://127.0.0.2:8299/v1/health -> 200
server stderr: (no refusal logged — the enforcement was never consulted)
```

**Why the enforcement is bypassable, confirmed at the source this stage:**
`resolve_bind_host` is called at `app/main.py:93` inside `run()` and at `:120`
inside `create_app()`. The `uvicorn app:app` construction path reaches **neither**,
because the application object is built at module scope with the default.

**The gap that matters is the detection, not the bind.** `ss -ltnp` shows the socket
**as it is now** and has no memory; nothing records how the process was started. So
an operator who once typed `--host 0.0.0.0` leaves no trace, and `alarms.md` §2.5's
own row records that this is *"the most important row in the file precisely because
its automation status is worst."*

**The honest limit on the consequence.** There is **one machine and no second host**
from which to attempt a connection, so "was it actually reached?" **cannot be
answered after the fact** — `runbooks.md` §6 says so, and this stage repeats it:
treat the exposure window as unknown, rotate the credential, accept that the window
is unrecoverable by design. **That unrecoverability is precisely what makes the
prevention worth an S.**

## 4. Items 6–10: the unguarded behaviours

**BL-06** is the most structurally important item on this list and the smallest to
state. The project's most consequential measured behaviours have **no requirement,
no gate, no target and no owner** — not because anyone decided that, but because
`performance-requirements.md` § "Concurrency posture" **declined to sub-number the
concurrency constraint**, on the reasoning that hanging a `NFRx.y` id on it would
invent a parent the inception set does not contain.

**That call was correct.** Inventing a parent would have been worse. But the
consequence is that the next scope may change any of the six behaviours in
`load-test-results` §15 without knowing they were measured, and that no gate would
notice. **The fix is a requirements act, not a code act**, and it is the single
highest-value thing the next Inception phase can do for this system.

**BL-07** is the one item where **the measurement and the requirement disagree and
the requirement is right.** `NFR9.3` states the real bound and says no cap is
imposed, *"and the omission is deliberate rather than an oversight."* `load-test-results`
recorded it `Met` **because** no cap exists — a cap imposed here would contradict
it. So BL-07 is a **contract change owned by the Unit that owns the analytics
surface**, exactly as `smoke-test-results.md` §4 and `observability-setup`'s **OQ-1**
both ruled, and this report does not overturn that.

**BL-08** is four small changes that between them make the difference between
diagnosing an incident from evidence and diagnosing it from a terminal scroll. The
measured facts: **6 refusals produced 0 application records**; a failed startup
produced **0 `app.*` records** and only `uvicorn.error`; the access line carries
**no duration field**, so every latency figure in this project is stopwatch-measured;
and `/v1/health` answered `200` in **1.4 ms** while every analytics read was `500`.
**The first of the four needs a decision as well as a code change** — whether a
mistyped date deserves a log line — and that decision is genuinely open (**OQ-2**),
because with one operator a typo would then write a line on every attempt.

**BL-09** localises BL-06's most expensive symptom. `/terms` reads all 10 000 rows'
text in one statement and then does `tokenize` → `significant_terms` →
`Counter.update` **in pure Python for every row** — CPython bytecode under one GIL.
**The SQL is bounded; the Python is proportional to the store, not the range.** That
is why `/terms` alone at `c` = 8 manages **8.60 rps** at **305.88 ms** of CPU per
request while `/summary` alone manages **46.98 rps** at 56.58 ms. **The fix belongs
to `u2-term-extraction`, which already owns `TermExtraction`** — the same Unit that
must adopt `app/terms.py` under BL-01's boundary fix.

**BL-10** is XS and belongs to the human, because it changes a file on the
operator's own machine. Recorded so the decision is not silently dropped: measured
**644** where the check expects **600**, on a store that holds submitted text
unencrypted. `team.md` § Deployment records the unencrypted posture as deliberate
and the single-user localhost trust model as the reason; **nothing in the record
argues for changing the mode**, which is why this is XS and last in its band rather
than treated as a defect.

## 5. Four traps this ranking deliberately avoids

A backlog derived from a rich measurement record has a predictable failure mode:
**the measured, interesting, easy thing outranks the unmeasured, boring,
load-bearing thing.** Four specific traps, each with the item that would have won:

| Trap | What a size-first or novelty-first ranking would put at the top | Why that is wrong |
|---|---|---|
| **Fix the performance findings — they are the most interesting measurements here** | BL-06 / BL-09 (concurrency, `/terms`) | They are real, but **no requirement is broken and nothing fails.** `FR8.4`'s assertion — that requests do not fail — **holds**: 1 920 ramp requests and 5 000 soak requests, zero errors, descriptors 7 → 7, threads 1 → 2. **The system is slow under a load profile `NFR9` says will not occur.** Meanwhile BL-02's consequence is that every row written since one instant on one afternoon is gone forever. |
| **Add a cap on the series — it is an obvious defect at the budget boundary** | BL-07 | `NFR9.3` **deliberately** imposes no cap and records the omission as policy. Imposing one **contradicts a requirement the project is currently meeting**, and it changes the `/v2` contract. It ranks seventh because it is a *decision*, not a fix — and the decision belongs to `u3-analytics-view`. |
| **Close the observability gaps first — they are cheap** | BL-08 | They are cheap **and** they rank eighth, because their consequence is *diagnostic difficulty*, not data loss or outage. **BL-03 is the same size class and outranks it by an order of consequence**: one failing request versus 100 % of the read surface failing for five seconds. |
| **Finish the scope and close the workflow — the boundary check already failed** | BL-01 | This is the one trap the record itself sets, and it deserves stating carefully. **`verification/phase-check-construction.md` recommends *against* approving the Construction → Operation transition on the current record, and that recommendation stands.** This workflow ran `feedback-optimization` anyway, because the stage is `CONDITIONAL` and there was real operational evidence to synthesise — and doing so produced BL-03, BL-06, BL-08 and BL-09, none of which existed as backlog items before. **That is a real gain and it is not a pass.** The correct reading is: the FAIL verdict is unresolved, BL-01 is the first item, and this report does not soften it. |

## 6. What feeds the next Ideation cycle

Five seed questions, each derived from a measurement rather than from a preference.
**They are the questions this stage could not answer from the record, and each names
what is already known so the next cycle does not re-derive it.**

| # | Question | What is already known | What an answer would change |
|---|---|---|---|
| **Q-A** | **What must be recoverable, and from which surface?** | The export returns **1 of 3** rows on a 3-row store and `404`s on a 2-row store where `summary` reports `total: 2`; `probabilities` and `intensity` are never exported; one byte-identical manual copy exists of a store holding **0 rows**. | Whether BL-02 stays a habit and BL-04 needs a new FR, or whether a real backup surface is a requirement. **This is the single highest-consequence product question in the backlog.** |
| **Q-B** | **What behaviour under overlap is *wanted*, given that none is required?** | Throughput peaks at **157.78 rps at `c` = 2** and falls to **41.20 at `c` = 64**; per-request CPU inflates **11.75 → 62.21 ms**; the mixed load at `c` = 8 runs at p95 **952.683 ms**; `/v1/health` reached **2 323.53 rps** at the same concurrency, so the harness is not the cause. | Whether the next Inception phase creates the missing NFR parent, and whether a *fix* (BL-09) or a *documented acceptance* is the right output. **A fix without a target would be BL-06 repeated.** |
| **Q-C** | **Who reads `/v2/analytics/summary`, and with what range?** | The largest real sample the project has ever produced is **27 requests**; the summary's payload is linear in the *requested* range at **~192 B per entry**; a 100-year range returns **7 011 966 B**. No RPS target exists because `NFR9` records a single-user store. | Whether BL-07 becomes a cap, a default range, a pagination contract, or an accepted risk. **It also decides whether any of the concurrency findings matter to the user at all.** |
| **Q-D** | **What is this application's "incident", given that one person is the user, the developer and the only responder?** | Detection time is **unbounded**; restart is **0.45–0.52 s**; there is no pager, no metric, no rule engine, no notification channel and no schedule; the effective RTO is the *notice* time. | Whether any of BL-08's four gaps is worth closing for a system with no alerting at all — which is a real question, not a rhetorical one, and this stage does not presume the answer. |
| **Q-E** | **Is a local gitignored SQLite file the right durable store for text that may be personal?** | `validation-report.md` §G records the falsifiers precisely: the schema **does not stop** third-party personal data in `text` (`TEXT NOT NULL`, no length or content constraint, and the import endpoint takes a whole CSV), and turning on `mode = "openrouter"` creates a **transfer** and a processor relationship. `FR7.4`'s `LICENSE` does not exist; no retention policy exists. | Whether Q-E is a next-scope concern at all. **Recorded because `validation-report.md` states the falsifiers alongside the "none apply" finding, and that pairing is the whole point.** |

## 7. The measurement discipline this backlog inherits

Four properties of how this record was produced, carried forward so the next cycle
reproduces them rather than merely inheriting the numbers.

1. **Controls, not just measurements.** The concurrency attribution holds because a
   control that never touches the store (`/v1/health`, **2 323.53 rps** at `c` = 32,
   flat CPU) ran at every level. A superlinear result without a control is a
   hypothesis.
2. **Reproduce across runs before publishing.** The concurrency ramp was run twice on
   separate servers and agreed to ~1 %; the range ladder was repeated 25 times. A
   single draw is a number, not a distribution — which is why `alarms.md` §2.3 notes
   the one recorded latency figure sits *below* a later p50.
3. **A reproduction that first fails to fail is the most valuable kind.** A **v3**
   store boots clean, because the current relation already *is* v1-shaped, so the
   rebuild never runs and no `CHECK` is ever exercised. **RB1's stated trigger was
   wrong because of it** (BL-12). Note the correction was found by an *organism* —
   the incident-response stage re-read its own reproduction and said so.
4. **Do not build an instrument against another Unit's deliverable.** Twice now — at
   Build and Test and again at Performance Validation — a genuine partial outcome
   appeared in the data (one section succeeding while another failed) and was
   correctly **declined** as the `NFR4.6` instrument, because `NFR4.6` requires a
   *view-level marker* and a storage-lock timing accident produces no marker, is
   invisible to the user, and is not reproducible on demand. **Reporting it as
   progress would have been exactly the claim that leaving the target `Unverified`
   prevents.**

## 8. What this stage did not do, and the store it left behind

**No application source, test, configuration or the data store was modified by this
stage.** Every measurement that touched SQLite ran in a `mktemp -d` scratch tree
under `/tmp/opencode/`; the read-only queries used `file:…?mode=ro`; `git status
--porcelain -- app tests pyproject.toml data README.md` is empty; and both scratch
trees were removed.

The operator's store, sampled before the first command of this stage and after the
last:

```
sha256  c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39  data/sentiment.db
        mtime  2026-10-03 03:33:42.920985500 +0500   size 32768   mode 644   inode 854420
        (identical on every field, including the inode — a file that was replaced
         would almost certainly carry a different one)
```

and its only backup, which **this stage did not create, verify or alter**:
`data/sentiment.db.bak-aa0b1e4`, **32 768 B**, sha256 `c8be1361…`, byte-identical,
inode 857387.

**Four things this stage deliberately did not do**, each with the reason, because
each looks like an omission from the outside:

- **Did not edit another stage's artifact.** `health-check-report.md` §2.3,
  `rollback-runbook.md` RB1 and `cd-config.md` §5 are all demonstrably wrong and all
  belong to other stages. They are recorded here and in `drift-report.md` §5
  instead. **Correcting another stage's record is not this stage's to do**, and the
  record already demonstrates the discipline: `observability-setup` upgraded
  `health-check-report.md` §2.3's CLI bypass from code-reading to measurement
  *without* editing it, and `incident-response` recorded `python -m app.main` as
  **OQ-IR-5** rather than adding a `__main__` guard.
- **Did not tag, commit, merge or push.** `deployment-log.md` §5.2 records that R8 —
  the release tag — is a human decision, and nothing since has changed that.
- **Did not manufacture a burn rate.** See `slo-report.md` §6 for the four reasons,
  stated there in full.
- **Did not present the Construction → Operation boundary as anything but a FAIL.**
  It is the first item in this backlog.

**What this closes.** `feedback-optimization` is the final stage of the workflow.
Its output is this backlog plus three honest accounting artifacts — `slo-report.md`,
`cost-analysis.md` and `drift-report.md` — and one questions file. **The single
sentence worth carrying into the next Ideation cycle is BL-02's:** the project's one
irreversible asset has exactly one byte-identical copy of a store holding **zero
rows**, and it was created by luck during a release. Everything else on this list
can be rebuilt; that cannot.