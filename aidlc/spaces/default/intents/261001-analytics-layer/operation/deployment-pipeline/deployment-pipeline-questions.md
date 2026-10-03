# Deployment Pipeline Questions — intent `261001-analytics-layer`

> **Stage:** `deployment-pipeline` (operation), Step 2 · lead
> `aidlc-pipeline-deploy-agent` · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/deployment-pipeline`
>
> **Inputs this artifact was derived from**:
> `construction/ci-pipeline/ci-config.md` · `construction/ci-pipeline/quality-gates.md` ·
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md` ·
> `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` ·
> `construction/build-and-test/build-instructions.md` ·
> `memory/team.md` § Deployment and § Way of Working · `memory/project.md` ·
> `app/db.py` · `app/main.py` · `app/config.py` · `tests/test_migration_indexes.py`.

---

## 0. Summary — five of the seven required questions are answered from evidence

| # | Question | Status | Answered by |
|---|---|---|---|
| **Q1** | What deployment strategy — blue/green, canary, rolling? | **ANSWERED** | `memory/team.md` § Deployment + the measured shape of the system; `deployment-strategy.md` §2 |
| **Q2** | What environment promotion gates (dev → staging → prod)? | **ANSWERED — none exist** | `memory/team.md` § Deployment; one bind address, `app/main.py:45-46` |
| **Q3** | What approval workflow for production? | **ANSWERED — there is no production and no second person** | `memory/team.md` § Way of Working; `ci-pipeline-questions.md` Q7 already recorded this |
| **Q4** | What is the rollback procedure? | **ANSWERED — and now measured** | `rollback-runbook.md` §2–§5 |
| **Q5** | What feature-flag strategy (AppConfig, CloudWatch Evidently)? | **ANSWERED — none, with a named alternative** | `deployment-strategy.md` §7; `C-5`; the `/v2`-prefix compatibility boundary |
| **Q6** | Should the standing verification command's step 3 stop migrating the real store? | **OPEN — the human's** | *nothing*; see §2 |
| **Q7** | Should copying `data/sentiment.db` before a release be a documented step? | **OPEN** | *nothing*; see §3 |
| **Q8** | Should the recorded schema version be guarded against moving backwards? | **OPEN — Code Generation's** | *nothing*; see §4 |

**What is deliberately not asked.** No question about coverage thresholds, branch age,
merge cadence, retention periods or artifact repositories: all are already recorded —
the floor is affirmed and stated twice, `memory/team.md` § Way of Working refuses to
invent a branch-age limit, `ci-pipeline-questions.md` Q4 answers the artifact-repository
question by negation, and there is no publishing to retain. Re-asking a settled question
is re-litigating a recorded decision, which `memory/org.md` § Forbidden names as a
thing agents must never do.

**And the honest note on Q1–Q5.** Five answered questions is *not* five decisions this
stage made. Each is an answer the repository had already given — by an affirmed
practice, or by an absence the team measured. The stage's own contribution is
narrower and is stated plainly in `cd-config.md` §1: the release procedure, the
throwaway-store hazard, and the measured rollback properties.

---

## 1. Q1–Q5 — answered from evidence, with sources

### Q1 — Deployment strategy

**Answer: recreate for the process; expand-only for the schema.** No traffic-shifting
strategy is possible or meaningful.

| Source | What it settles |
|---|---|
| `memory/team.md` § Deployment | *"Deployment is a localhost checkout, and a commit is the release. No environment tiers, no container, no hosted service, no IaC. The only documented run path is `python -m pip install -e ".[dev]"` then `uvicorn app:app --reload`, one process bound to `127.0.0.1:8000`."* |
| `app/main.py:45-46, 65` | One bind address; a non-loopback bind **raises** `NonLoopbackBindError` rather than serving (instrumented by gate **G12**) |
| `memory/team.md` § Deployment | *"Real stores are no longer disposable… the import/export feature is now the user's way of moving data out"* — which is why blue/green, the one strategy that needs a second environment, is specifically wrong here rather than merely unavailable |
| `app/db.py:60, 219-247` | The schema strategy: additive, idempotent, one transaction, `rollback()`-and-re-`raise` on any failure |
| **measured, this stage** | The previous release's code runs correctly on a v4 store — so the expand-only choice is what keeps rollback to a `git checkout` |

### Q2 — Environment promotion gates

**Answer: none, and none can be defined.** There is one environment, so there is
nothing to promote between and no gate to place on a promotion.

`memory/team.md` § Deployment settles it by name: *"The framework default — deploy-on-merge to staging behind a manual production gate — has no counterpart here, because the environments it assumes do not exist."* `u1`'s
`cicd-pipeline.md` §1 records the same disposition per-concern, and `ci-config.md` §9
records why no promotion matrix appears in the CI half. **The substitute is the
throwaway-store smoke** (R6), which runs the *real* application through real `uvicorn`
against a disposable store — measured in this run, §2 of `cd-config.md`.

### Q3 — Production approval workflow

**Answer: there is no production, and there is nobody to press approve.**
`memory/team.md` § Way of Working: *"one author, no co-authors, no merges, and therefore
**no second human reviewer**."* Already adjudicated upstream in
`ci-pipeline-questions.md` Q7, whose answer stands and is not reopened: with one
participant a required reviewer is either unsatisfiable or waived every time, and *"a
gate that is always bypassed is worse than no gate."*

### Q4 — Rollback procedure

**Answer: `rollback-runbook.md`, in full, and measured.** The three load-bearing
results: a failed migration leaves the store byte-identical and the port closed; the
previous release's code runs on a v4 store with every row and every index intact;
re-running the new code over that store is idempotent. Sources and method are in
`rollback-runbook.md` §5.

### Q5 — Feature-flag strategy

**Answer: none, and none is warranted.** No flag mechanism exists in the code; the
release's surface is two read-only endpoints on a new `/v2` router with `/v1` untouched,
which is the control that actually governs compatibility; and a flag **cannot** govern
the one thing this release changes that matters — the startup migration, which runs
regardless of any toggle. `memory/project.md` `## Forbidden` (`C-5`) additionally rules
out every hosted flag service. Detail in `deployment-strategy.md` §7.

---

## 2. Q6 — Should the standing verification command stop migrating the real store?

**Status: OPEN. It edits a human-approved Delivery Planning artifact, and the human
already declined a similar edit.**

### 2.1 What was measured

`verification-command.txt`'s step 3 boots the real `app.main:app`. Module scope builds
that app (`app/main.py:163`), the lifespan calls `db.init_db(resolved.db_path)`
(`app/main.py:132`), and with no injected settings that path is the relative
`Path("data/sentiment.db")` (`app/config.py:39`). So **running the approved verification
command migrates the operator's real store.**

The store moved: `memory/team.md` records this checkout at `schema_meta.version = 2`;
reading it now returns `4` with all three indexes and 0 rows.

`ci-config.md` §4.9 adopted that command verbatim as job **J9** and did not flag this.
This is the CD half's finding, and it is a genuine one — the smoke that proves a
release works is the same action that changes the release's durable state.

### 2.2 Why it is not simply fixed here

`build-instructions.md`'s halt-and-ask already put a rewrite of that file to the human
and the human chose not to take it (`test-results.md` §6: *"Option D remains open and
undone… it is **not** treated as a pass"*). That answer was about step 1's venv; this is
about step 3's store. **Same artifact, same owner, same reason not to edit it from a
design stage.** `cd-config.md` R6 therefore uses the working form and records the
divergence rather than quietly normalising it.

### 2.3 Options

| Option | Impact |
|---|---|
| **A. Leave the recorded command; `cd-config.md` R5+R6 handle release safety** | **Effort:** zero. **Cost:** the approved artifact still mutates the real store whenever anyone runs it for verification, outside a release. **Risk:** low — the step is additive and idempotent, and the harm is confined to a *premature* migration, which RB2 shows the older code tolerates. **Reversibility:** total. **Status quo.** |
| **B. Rewrite step 3 to run from a throwaway CWD** — the command in `cd-config.md` §5, verbatim | **Effort:** minutes. **Cost:** £0. **Risk:** low; it edits an approved artifact, which is the whole reason it needs the human. **Benefit:** the approved command stops touching the real store, permanently, and every future host inherits the fix. |
| **C. Add a one-line note to the README beside the verification command** | **Effort:** minutes. **Cost:** documents a defect where a fix is available — and `phases/construction.md`'s error-handling rule prefers failing fast to a note beside a footgun. |

**This stage takes no position and does not re-ask Build and Test's halt-and-ask.**
Recorded because the artifact is load-bearing for every future release.

---

## 3. Q7 — Should copying the store before a release be a documented step?

**Status: OPEN, and it is the cheapest open question in this stage.**

The store is the project's only irreversible asset: `/data/` is gitignored, no commit
contains a copy, there is no replication and no migration tool. A release now runs a
schema step against that file (`app/db.py:219`, via `app/main.py:132`).
`cd-config.md` R5 answers it with one `cp`, and `rollback-runbook.md` §4 states the
consequence of *not* doing it: total loss.

| Option | Impact |
|---|---|
| **A. Adopt R5 as written** — `cp data/sentiment.db data/sentiment.db.bak-$(git rev-parse --short HEAD)` before anything starts the app | **Effort:** one line. **Cost:** one file copy, ~32 KB on an empty store. **Risk:** it can be forgotten, because nothing enforces it; a forgotten copy is indistinguishable from a made one. **Reversibility:** total. |
| **B. Add it to `README.md`'s `## Storage` section**, so the recovery path is discoverable without this record | **Effort:** minutes. **Cost:** £0. **Risk:** `memory/team.md` records the README as *"part of the change"* for a new router, endpoint, module or test module — recovery procedure is not in that list, so this widens a convention deliberately. **Benefit:** the operator finds it at the moment they need it, which is the only moment it matters. |
| **C. Add it to `FR7`'s packaging obligations** so it becomes a `u4-platform-packaging` deliverable alongside the verification script | **Effort:** a requirements change. **Cost:** £0. **Risk:** widens an unbuilt unit's scope. **Benefit:** it becomes something with an owner rather than advice in an operation-phase record. |

**This stage's own position, stated but not enforced:** R5 is in `cd-config.md` because
a `cp` with a cost of one file copy and no downside is obviously right for a
single-operator local release. **Whether it is worth writing into the README or into
`FR7` is a call about where the project keeps its recovery instructions**, and that is
the human's.

---

## 4. Q8 — Should the recorded schema version be guarded against moving backwards?

**Status: OPEN, and it belongs to Code Generation or a future scope, not to this stage.**

Measured behaviour: the `express` release's `init_db` (`SCHEMA_VERSION = 3`) running
against a v4 store **downgraded `schema_meta.version` from `4` to `3`**, harmlessly —
rows, relation and all three indexes untouched — and the new `init_db` then restored
`4` idempotently. So the field tracks *"what last ran"*, not *"the highest version ever
reached"*.

Nothing is broken by this today, and RB2 §3 documents it so nobody "fixes" it by hand.
The question is whether the invariant should be **asserted**, i.e. whether a test should
require the recorded version never to decrease.

| Option | Impact |
|---|---|
| **A. Assert it** — a test that a store's recorded version never decreases | **Cost:** this would **fail today**, because the measured rollback behaviour is exactly a decrease. It would require deciding first whether a code rollback *should* rewrite the recorded version at all, which is a `app/db.py` behaviour change, not a test. |
| **B. Assert only the forward guarantee that matters** — re-running `init_db` never loses rows, columns or indexes | **Already covered.** `tests/test_migration_indexes.py:246` proves the at-v4 no-op and `:219` proves the additive v3 → v4 step. **No new test is needed**, and this is the reading this stage recommends. |
| **C. Change the behaviour** so the recorded version is monotonic, then assert it | **Cost:** a real change to `app/db.py`'s `_RECORD_SCHEMA_VERSION` semantics, plus a migration of the recorded value on existing stores. **Risk:** it removes the field's ability to say "this store is exactly what code X wrote", which is the property that makes `_is_v1_shape` and RB2's reasoning coherent. **Not proposed.** |

**No test is proposed by this stage**, and the reason is stated rather than hedged:
the property that actually protects the release is already proved, and the property
that is unguarded is a cosmetic monotonicity that the code does not claim. The
decision belongs to whoever next changes `SCHEMA_VERSION`.

---

## 5. Cross-Unit obligations this stage references rather than duplicates

| Obligation | Owner | How this stage relates to it |
|---|---|---|
| Verification script running the three standing gates (`FR7.2`) | **`u4-platform-packaging`** | `cd-config.md` R3/R4 are the command form of the same gates. When the script lands they become an argument to it, not a parallel copy — the convergence `ci-config.md` §9 names as the intended destination. Not duplicated. |
| Lockfile with hashes (`FR7.1`) | **`u4-platform-packaging`** | Bears directly on RB2 step 4: a reinstall with no lockfile re-resolves the dependency set, which is why the runbook says *"if a reinstall is not part of the problem, do not perform one."* |
| Secret scan and dependency audit (`FR7.3`) | **`u4-platform-packaging`** | Not release concerns — no release step handles a credential. |
| The two security scripts (gates G9, G10) | **`u4-platform-packaging`** | Their instruments are not in the repository, so they are **not** part of a release gate today. Recorded in `quality-gates.md` §4; not duplicated or re-specified. |
| `TID251` layer boundaries (`FR7.5`) | **`u4-platform-packaging`** | Not a release concern. |
| Cross-Unit FR/NFR/AC gate **FAILED**; 2 `Unverified` targets (`NFR4.6`, `NFR4.7`) | **`u3-analytics-view`** | Carried as accepted debt upstream. **Not re-adjudicated here** — a release concern neither satisfies nor worsens. |

---

## 6. Position of this stage

**The stage executed, narrowly and on evidence.** Its configuration is a release
procedure, not a pipeline, because the pipeline it would configure does not exist and
the repository's own memory forbids inventing one. Its one substantive contribution is
the pair of measured facts no upstream artifact recorded — that the approved
verification command migrates the operator's real store, and that the previous
release's code runs correctly on a v4 store — because the v3 → v4 step is the first
release-shaped change this project has shipped and neither upstream stage could have
measured it before the code existed.

**Three questions are left genuinely open (Q6, Q7, Q8) and all three are the human's
or another unit's, not this stage's.** Each is stated with the option set and an
impact estimate, and **no answer was inferred from habit.**