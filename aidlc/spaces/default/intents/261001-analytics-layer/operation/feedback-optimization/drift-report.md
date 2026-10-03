# Configuration & Requirements Drift Report — intent `261001-analytics-layer`

> **Stage:** `feedback-optimization` (operation, final stage) · lead `aidlc-operations-agent`
> support `aidlc-aws-platform-agent` · **Date:** 2026-10-03
> **Release under report on:** commit `aa0b1e4`
> **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/feedback-optimization`
>
> **Upstream inputs consumed by this stage:**
> `observability-setup/dashboards.md` (`dashboards`) ·
> `observability-setup/alarms.md` (`alarms`) ·
> `observability-setup/slo-config.md` (`slo-config`) ·
> `observability-setup/log-queries.md` ·
> `deployment-execution/deployment-log.md` (`deployment-log`) ·
> `deployment-execution/health-check-report.md` ·
> `deployment-execution/smoke-test-results.md` ·
> `performance-validation/test-results.md` — cited under this stage's declared slug
> `load-test-results` ·
> `performance-validation/nfr-validation-matrix.md` ·
> `incident-response/incident-plan.md` (`incident-plan`) ·
> `incident-response/runbooks.md` · `incident-response/escalation-matrix.md` ·
> `environment-provisioning/validation-report.md` (F-01…F-04) ·
> `environment-provisioning/environment-inventory.md` (M1–M5) ·
> `construction/ci-pipeline/ci-config.md` · `construction/ci-pipeline/quality-gates.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md` (§R-02, §R-09) ·
> `verification/phase-check-construction.md` (the FAIL verdict) ·
> `inception/requirements-analysis/requirements.md` (FRs, NFRs, Revisions 1–2) ·
> `inception/contract-design/contract-summary.md` ·
> `inception/units-generation/unit-of-work.md` ·
> `memory/project.md` `## Forbidden` / `## Mandated`;
> `memory/team.md` § Deployment, § Code Style.

---

## 1. What "drift" means here — said first, because the usual meaning is absent

**There is no AWS Config, no conformance pack, no drift-correction automation and
no Trusted Advisor.** Configuration drift in its usual sense — *the live
configuration has diverged from the declared configuration* — is therefore **not
observable in this project at all**, and no amount of analysis would make it so.
§2 records that per element, with the rule that rules each out.

**But drift is not absent. It is merely located somewhere other than a cloud
resource.** Three of the artifacts this project produces are *declarations of fact
about itself*: a requirement set, a unit-boundary decomposition, and a set of
runbooks and reports that tell an operator what will happen. Each is a claim about
code and behaviour. Each can be checked against the code and against a measurement.
**When one of those claims is false, that is configuration drift in the only sense
available here, and there is a great deal of it.**

The five classes found, each measured:

| Class | Count | The mechanism |
|---|---|---|
| **D-1 — Requirement drift**: a requirement changed after code was written against it | **4 items** | Revision 1 and Revision 2 of `requirements.md` correct defects found by asking what the schema and the shipped code actually permit. |
| **D-2 — Structure drift**: the code violates a boundary the design declared | **2 items** | `app/terms.py` authored by U1 against three inception artifacts, with a live import edge; and `AC6.2.1` satisfied by neither of its two owning Units. |
| **D-3 — Artifact drift**: a record names a run path, a trigger, a count or a default that measurement disproved | **7 items** | `python -m app.main` does not serve; `RB1`'s stated trigger never fires; `cd-config.md` §5 over-generalises the store hazard; the fake-key count; the suppression census; the exit code; the design-vs-code logging location. |
| **D-4 — Undrifted-by-decision**: absence that looks like drift and is not | **4 items** | The uncapped series (`NFR9.3`), the absent CI (no remote), the absent metrics (`C-6`), the absent escalation matrix (one operator). Recorded so absence is not re-investigated every cycle. |
| **D-5 — Unclaimed-behaviour drift**: measured behaviour no requirement covers | **9 items** | The six `F-1`…`F-6` findings, plus OG-1…OG-5. |

**Nothing in this report required AWS to find, and nothing in it required a
continuous collector. Every item was found by reading one declaration and running
one check against the code.** That is the honest version of a drift report for this
system, and the reason it is worth writing is that the next scope will otherwise
re-derive all of it.

## 2. Declared not-applicable, per element, with the rule that rules it out

| Drift element | Verdict | The rule that rules it out |
|---|---|---|
| **AWS Config rule evaluation** | **N/A — no Config, no account** | No `aws` CLI, no `~/.aws`, no `AWS_*`/`CDK_*`, no `cdk.json`, no `*.tf`/`*.bicep`/`Pulumi.yaml` in the tree. Measured by `environment-inventory.md` (M1–M5) and re-confirmed this stage. |
| **Config conformance pack / desired-state file** | **N/A — nothing declares desired state** | No IaC of any kind. `team.md` § Deployment: no tiers, no container, no hosted service, no IaC. There is no file to compare against. |
| **CloudTrail / API-call audit trail** | **N/A — no API calls to audit** | No AWS call is made. The analytics read path's import closure contains **no** network-capable import (V-28; corroborated by `load-test-results` `NFR2.2`). |
| **Trusted Advisor review** | **N/A — no service to review** | Trusted Advisor is an AWS service. There is no account. |
| **Manual-configuration drift (hand-edited console settings)** | **N/A — no console, no settings** | There is nothing to hand-edit. The nearest analogue is the operator's own `config.local.toml`, which **does not exist** on this checkout — measured `mode: offline`. |
| **Certificate / credential expiry drift** | **N/A for the stored state; a live risk for the operator's key** | No certificate, no stored credential, no secret manager. The operator's OpenRouter key lives in the gitignored `config.local.toml` and in process memory only; with `mode: offline` there is no key on this machine at all. Rotation cadence is not a project's decision. |
| **Resource-tagging drift** | **N/A** | No resources. `C-5`. |
| **Environment-to-environment drift (dev/staging/prod)** | **N/A — one environment** | `cd-config.md` §2: there is one environment, and `deployment-log.md` §4 measured the consequence — the deployment window is a sub-second gap on a port that closed and reopened cleanly, with no freeze calendar because nothing competes. |

**The one-line reason common to all eight:** no AWS account, no CLI, no credential,
no IaC file, and no hosted resource of any kind — which `team.md` § Deployment
affirms rather than suffers.

**And the honest admission about what that costs:** the absence of a drift
detector means **drift of class D-1…D-3 below was found by people reading
artifacts, not by a mechanism.** Every item in §3–§5 was found by some stage
happening to check. Nothing will check for the next one unless a human reads the
record. That is a real gap and it belongs in `feedback-loop.md` (**BL-16**), not
here, where the job is to report the drift that exists.

## 3. D-1 — Requirement drift: four requirements changed after code existed

Every item here was caught *after* the code or schema was fixed, by asking what
the schema actually permits. **None is a defect in the implementation** — each is a
defect in a declaration that had been treated as settled. All four corrections are
already recorded in `requirements.md`'s Revisions; this report records that the
correction happened **late**, names what the pre-correction text would have
caused, and says who owns closing it.

| # | Requirement | The drift | Caught by | Consequence had it not been caught | Owner of the residual |
|---|---|---|---|---|---|
| **R-1** | **`FR2.8`** — "`mean_confidence` averages only the rows that carry a confidence value, with `null` for an empty contributor set" | **The clause is unreachable.** `confidence` is `NOT NULL` in the shipped schema; `_is_v1_shape` rebuilds any store that disagrees, and the rebuild aborts on a `NULL`. **Corrected reading, ruled by the human at `user-stories` Q7:** it averages every row in range and `mean_confidence_row_count` always equals `total`. **The field is retained only so the response states its own denominator.** | `user-stories` Revision 2 | A field and an entire null-path would have been built and tested against a case that cannot occur — and the 4-decimal rounding rule `FR2.7` depends on would have had nothing to round. This is the **second** requirement in one intent written against a retired or unreachable column, after `mean intensity`. | closed by the ruling; `FR8.2` pins the corrected behaviour |
| **R-2** | **`FR5.3`** — index declarations "in `CREATE_ANALYSES_TABLE`" | **The named mechanism does not exist.** SQLite's `CREATE TABLE` has no index declaration; two mob participants verified this independently against a live interpreter. **Corrected reading:** `_rebuild_analyses` re-creates the three indexes explicitly after the copy, and the test matches by index **name**. | `user-stories` Revision 2 | The test would have counted `type='index'` rows and failed on `sqlite_autoindex_schema_meta_1` — which the same `init_db` creates. `BR5.3` and the R-08 review already recorded that "exactly three indexes" is false against a real store. | closed; `load-test-results` `M1` measured all three indexes present at v4 |
| **R-3** | **`FR7.3`** — "the **four** known fake-key fixtures" | **Wrong, and wrong three times over.** `team.md` said four; an advisory review over `user-stories` counted six; `validation-report.md` **F-03 measured seven** distinct `sk-or-v1-*` literals. **All are placeholders; zero real credentials** (V-33). | `user-stories` Revision 2 → `environment-provisioning` F-03 | An allowlist built from "four" leaves **three** real fixture literals as false positives on the first run — i.e. the first secret scan produces noise, which is how scanners get switched off. **This one is still open**: `requirements.md` Revision 2 says "reconcile before writing any scanner's allowlist; until then, state no number". | **open** — `u4-platform-packaging` owns `FR7.3`; the number is now known (7) and the requirement text is not yet corrected |
| **R-4** | **`FR2.9` vs `FR2.10`** — one requires a zero-filled entry per calendar day in the resolved range, the other an empty series for an empty range | **Never reconciled, and both cannot hold** for a bounded range matching no rows. **Corrected reading, ruled at `user-stories` Q10:** a range matching **no rows** returns an empty series; zero-filling applies only to the internal gaps of a range that matched at least one row. | `user-stories` Revision 2, graded **Critical** | An analytics view could render a 3 650-entry zero-filled series for a range that matched nothing, or return an empty series for a range with internal gaps. **Both readings shipped as a defect.** | closed by the ruling; `BR4.4` and `NFR4.3` carry it |

**Two more corrections from the same revision, recorded because they are the same
class of drift and a future reader will meet them in the file:**

- **`FR2.11`** asked the `422` to carry a `field == "query.from"` member. The
  envelope is exactly `{code, message}` with `additionalProperties: false`, and an
  inverted range needs to name **two** fields, which `errors[0]` cannot do.
  **Corrected reading, ruled at Q11:** one `VALIDATION_FAILED` whose **message
  text** names the offending parameter, and both bounds for an inverted range.
  *This is what shipped* — `load-test-results` `S9` measured the exact strings
  `"query.from: expected a UTC calendar date written YYYY-MM-DD."` and
  `"query.from and query.to: 'from' must not be a later UTC day than 'to'."`
- **`FR6.8`** cited `[RM-5]` and `[RM-2]`; **no `RM-n` ids exist in the Rough
  Mockups artifacts at all**, verified by the User Stories review. The tags are
  wrong; the accessibility requirement's substance is unaffected.

**The pattern, stated once because it is the transferable lesson:** four of these
five defects share one cause — **a requirement written against a schema or an
artifact that was described rather than read.** `FR2.8` assumed a nullable column
that is `NOT NULL`; `FR2.8`'s sibling `mean intensity` assumed a column the app
never writes; `FR5.3` assumed a SQL clause that does not exist; `FR2.11` assumed a
response member the envelope forbids; `FR7.3` assumed a count nobody counted. The
project's own `## Corrections` rule already says the lesson for requirements
drafting — *"Write the precedence rule and the invalid-input behaviour explicitly
while drafting requirements, before the summary checkpoint"* — and this is the
same discipline applied to **the schema the requirement is about**.

## 4. D-2 — Structure drift: the code does not match the declared decomposition

| # | Drift | Evidence | Owner |
|---|---|---|---|
| **S-1** | **`app/terms.py` was authored by U1, which three inception artifacts forbid.** *"Term tokenisation is delegated to `u2-term-extraction` … this unit consumes it, does not re-implement it"* (`tech-stack-decisions.md:49`); *"U1 **does not own** the `TermExtraction` module (U2)"* (`unit-of-work.md:96`); `contract-summary.md` §4 repeats it. **A live `U1 → U2` import edge remains at `app/analytics.py:41`**, and `source-manifest.json` still claims the module and its tests. Worse, the **stopword set is U2's decision** (contract open point **O9**) and **U1 has already chosen and test-pinned it** (`code-summary.md` §R-09). | `phase-check-construction.md` §5; `code-summary.md` §R-02, §R-09 | **Delivery Planning** (re-run to move the Bolt order — *"not reachable from inside the current engine state"*), then **`code-generation` for `u2-term-extraction`** to adopt the module and own the set. **Blocking.** |
| **S-2** | **`AC6.2.1` is satisfied by neither owning Unit alone.** `unit-of-work-story-map.md`'s cross-cutting table says so outright: *"Neither unit alone satisfies `AC6.2.1`; both rows ship the story."* U1 delivers the series and label-breakdown summary region; U3 delivers the two term-list containers. | `phase-check-construction.md` §3 | **`u3-analytics-view`** — the two term-list containers. **Blocking.** |

**Why this is drift and not merely unfinished work.** S-1 is the difference. An
unbuilt Unit is a plan not yet executed; a Unit that wrote another Unit's module is
a **declaration that no longer matches the code**. `code-summary.md` §R-02 puts it
without hedging: *"It did not permit U1 to write U2's module, and U1 did. Until U2
runs, the binding recorded in `unit-of-work.md:96` is violated, and this note is
the disclosure rather than a claim of compliance."* Carried as **BL-02**.

**And the boundary class is not enforced by a mechanism.** The team already ruled
that boundaries become machine-checked via `ruff` `TID251` (`## Mandated`, Q10), and
`quality-gates.md` §5 records that the rule set is **not configured** — so a
boundary breach is currently visible only to a reviewer. That is why S-1 survived
three review passes. `FR7.5` is unbuilt; `u4-platform-packaging` owns it.

## 5. D-3 — Artifact drift: seven records that state something measurement disproved

Each row is a declaration in an artifact this project relies on, and the
measurement that falsifies it. **None was corrected in place**, because each
belongs to another stage's artifact and this stage may not edit them; each is
carried in `feedback-loop.md` instead.

| # | The declaration | What measurement shows | Status in the record |
|---|---|---|---|
| **A-1** | **`health-check-report.md` §2.3** — *"the enforced bind holds on the documented run path (`python -m app.main` / `app.main:run`)"* | **`python -m app.main` does not serve.** `app/main.py` has **no `__main__` guard** (re-verified this stage: `grep -n '__main__' app/main.py` → no match). Run in a scratch CWD, it prints `<frozen runpy>:130: RuntimeWarning: 'app.main' found in sys.modules after import of package 'app'…`, **exits 0**, and **no listener ever opens** (verified twice on two ports). The only invocation measured to both serve *and* enforce the bind is `python -c 'from app.main import run; run()'` — boot to first HTTP `200` in **0.522 s**. | Correctly **not** edited by the incident-response stage; parked as **OQ-IR-5**. `runbooks.md` §7 / IR-6 carries the true command. Carried as **BL-11**. |
| **A-2** | **`rollback-runbook.md` RB1** — the migration-failure trigger, and its stated **`uvicorn process exit code: 1`** | **Two drifts in one row.** (i) The trigger is wrong: a **v3 store boots clean**, because `_is_v1_shape` (`app/db.py:284`) compares the physical table against the v1 relation and **the current relation already is v1-shaped** — so a v3 store takes no rebuild path and **no `CHECK` is ever exercised**. The failure needs a shape that is *not* v1-shaped (e.g. a pre-project store missing `import_id`) **plus** a row whose `label` is outside the domain. (ii) The exit code is **1 or 3 depending on the invocation**: uvicorn's own is **3** (both foreground forms); `1` is the *script's* exit from an uncaught `URLError` in the daemon-thread shape. | `runbooks.md` §5 states the corrected trigger explicitly and says *"I got this wrong first"*; **F-02** in `validation-report.md` names the exit-code ambiguity. **`rollback-runbook.md` itself is uncorrected.** Carried as **BL-12**. |
| **A-3** | **`cd-config.md` §5** — *"any `uvicorn app:app` from the repository root migrates `data/sentiment.db`"* | **Over-generalised.** The startup migration writes **if and only if** the store is behind `SCHEMA_VERSION`. Measured: booting against a v4 store leaves **sha256 and mtime unchanged** (V-15); a forced v3 downgrade **does** rewrite the file (V-14). `deployment-log.md` R7 proved it independently on the real store. | **F-01** in `validation-report.md` corrects it, and **both halves of the mitigation stand** — R5 and R6 are unaffected. A reader taking the original wording at face value would either treat R5 as an every-boot habit or assume the hazard is gone. Neither reading is right. |
| **A-4** | **`team.md` § Code Style** — *"nine suppressions in total… 4 × `# pragma: no cover`"* and *"the four `S310` suppressions are the entire security-suppression budget"* | **15 suppressions, and the security budget in `app/` is 5, not 4** — 7 `pragma: no cover`, 4 `S310`, **1 `S105`** (`app/terms.py:27`, a regex misreading as a credential), 1 `S104`, 2 `type: ignore`, 0 file-level. **The fifth is this intent's own module.** | **F-04** in `validation-report.md`; measured at V-37. The characterisation ("narrow and justified") still holds; only the census is stale. |
| **A-5** | **`team.md` § Deployment** and **`FR7.3`** — *"the four known fake-key fixtures"* | **Seven.** Same finding as **R-3** above; recorded here because `team.md` is a *practice* file, so a stale count propagates into every future scope's allowlist. | **F-03**. Requirement side still open. |
| **A-6** | **`observability-design.md` §2 / `monitoring-design.md` §3.1** — the storage-failure record is an "`exception(...)` record carrying the code **and stack**", emitted from the read module | **Two errors.** (i) The shipped calls are `logger.error(...)`, not `logger.exception(...)`, so the record is **a single line holding `str(exc)`** — no stack. (ii) **`app/analytics.py` has no logger at all** (`grep -c logging app/analytics.py` → **0**); the record is emitted one layer out, in `app/routes.py:364` and `:398`. | Corrected in `log-queries.md` §1.2(a) and (b). `NFR8.1` is satisfied either way; the *location* differs from what the prose implies, which is worth knowing so a future reader does not go looking for a logger that is not there. |
| **A-7** | **`slo-config.md` §1** — SLI-6 "exactly one listening socket … on a loopback address" | **True point-in-time, and bypassable.** Measured on `127.0.0.2`: `resolve_bind_host("127.0.0.2")` refuses, `create_app(host="127.0.0.2")` refuses before any lifespan — yet `uvicorn app:app --host 127.0.0.2` **bound and served `200` with no refusal logged**. `resolve_bind_host` is called at `app/main.py:93` inside `run()` and at `:120` inside `create_app()`; the CLI path reaches neither. | Corrected in `alarms.md` §3.1 and `incident-plan.md` **OG-5**. The gap is real and open (**OQ-3**). Carried as **BL-05**. |

**One more that is not drift but is adjacent, recorded so it is not mistaken for
it.** `team.md` § Code Style names `architecture.md:502`'s `ensure_page_state` as
the connection-ownership improvement; **that function does not exist anywhere in
this repository** — the owner is `get_connection` (`app/routes.py:92`). That is a
**stale CodeKB row**, not drift between a declaration and this project's code. It is
listed in `team.md` itself as a trap, and it is named here only because the same
CodeKB also records `from __future__ import annotations` as applying to "all 12
modules" when it applies to **11**, and `opentelemetry-api` as **1.45.1** when
**1.45.0** is installed. **The CodeKB's "Installed" columns are a one-time snapshot
nothing keeps honest** — which is a maintenance observation, not drift.

## 6. D-4 — Undrifted by decision: four absences that look like gaps and are not

Recorded so the next cycle does not re-investigate them. **Each is a requirement or
an affirmed practice doing its job.**

| Absence | Why it is not drift |
|---|---|
| **The series is uncapped.** | `NFR9` states the real bound and says *"No cap is imposed here, and the omission is deliberate rather than an oversight."* It also names the quantity as *"the only quantity in this feature that can grow without a caller-imposed bound, and therefore the one a future scope may need to cap."* `load-test-results` `NFR9.3` is `Met` **because** no cap exists. **The risk is real and measured** — 7 011 966 B at the budget boundary — and the *decision* belongs to `u3-analytics-view` (**OQ-1**). A cap imposed here would contradict the requirement as written. Carried as **BL-07**. |
| **No CI runs automatically.** | `git remote -v` is empty; no `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`, `.circleci/`, `azure-pipelines.yml`. The `feature` scope's "CI execution before merge" is therefore **unsatisfiable, not waived**. `ci-config.md` §2 is explicit that Tier 0 is executable and Tier 1 *"has never executed"*; §5 marks every trigger *currently inoperative*. **This is drift between a scope requirement and a reachable reality, and it closes the day a remote exists.** Carried as **BL-13**. |
| **No metrics, no exporter, no agent.** | `C-6` caps declared runtime dependencies at exactly `fastapi` and `uvicorn`, so no exporter may be declared; `C-5` forbids a cloud component. `dashboards.md` §4 records CloudWatch as not provisioned. The *absence* is the requirement working. |
| **No escalation matrix with named humans.** | `escalation-matrix.md` §3.2 fills each absent column with **the reason it is empty**: no rotation exists, no incident commander can be staffed with one responder, there are no stakeholders to communicate to. *"Inventing a name would put an unverifiable fiction into the one artifact class whose value is that every line is checkable."* Correct, and a model of how to record an absence. |

## 7. D-5 — Behaviour that drifted away from the requirement set entirely

Nine measured items that no requirement claims. These are drift in the strongest
available sense: **the system does things nobody asked it to do, or fails in ways
nobody wrote down.**

### 7.1 Six concurrency findings with no NFR parent

| # | Finding | Measurement | Why it has no target |
|---|---|---|---|
| **F-1** | Concurrency degrades **superlinearly**; throughput peaks at 2 clients and falls | `summary` **157.78 rps at `c` = 2** → **44.08 at `c` = 32** → **41.20 at `c` = 64`**; per-request server CPU **11.75 → 62.21 ms**; the same 240 requests cost **2.8 CPU-s at `c` = 1** and **14.9 CPU-s at `c` = 32** | The concurrency constraint is a *failure-behaviour* requirement (`FR8.4`, `BR6.3`): it asserts requests do not fail. **They do not** — 1 920 ramp requests, zero errors. |
| **F-2** | The **mixed page load breaches the 200 ms budget on essentially every request** at `c` = 8 | p95 **952.683 ms**, p99 977.333, max 1004.909; reproduced three times to within 1 % | As `F-1`. `/terms` is the cause: alone it manages **8.60 rps** at p50 921.9 ms while `/summary` alone manages **46.98 rps** at p50 169.5 ms. |
| **F-3** | **One competing writer takes the whole read surface down** | **6 of 6** reads `500 STORAGE_FAILURE` at p50 **5007.942 ms**; recovery immediate on release | `NFR9` records single-user operation; nothing states behaviour under a second writer. `runbooks.md` IR-1 documents the mode but sets no target. `app/db.py:213` sets no `busy_timeout` — re-verified this stage: `PRAGMA busy_timeout` → **5000 ms** on this interpreter. |
| **F-4** | The unbounded series is **linear in the requested range** and lands at the budget boundary | **7 011 966 B / 36 500 entries**, p99 **199.700 ms** — **0.3 ms inside**; `IR-7` recorded 4 of 5 repeats *over* at a median of 240.7 ms | `NFR9.3` **deliberately** imposes no cap. |
| **F-5** | The server saturates at **~2.8 of 12 threads**, whatever the load | utilisation 2.63–2.79 cores at `c` ≥ 4 | No requirement states a CPU ceiling; there is no autoscaler to trigger on one. |
| **F-6** | Steady-state RSS is **147–186 MB** against 58 MB at boot, and does not grow with series length | ten 7 MB responses → **+3 356 kB**, unreleased after a 2 s settle | `C-6` forbids the metrics agent that would record it; no requirement states a memory budget. |

**The reason all six exist is a single structural gap**, and it is the most
useful thing in this section: `performance-requirements.md` § "Concurrency posture"
**declines to sub-number the concurrency constraint because hanging a `NFRx.y` id on
it would invent a parent the inception set does not contain.** That was the correct
call at the time. The consequence is that the six most consequential measured
behaviours in this project have **no requirement, no gate, no target and no owner**.
`nfr-validation-matrix.md` §8 records the absence explicitly, and §9 carries the six
findings forward. **Closing this gap is a requirements decision for the next
Inception phase** — carried as **BL-06**.

### 7.2 Four operational gaps, plus the fifth that behaves like one

From `incident-plan.md` §10, each measured:

| # | Gap | Measurement |
|---|---|---|
| **OG-1** | A `422` emits **no** application record | 6 refusals → **0** records. `app/routes.py` logs only the storage branch; the `RangeError` branches at `:359`/`:393` and the shared handler at `:470`/`:475` return the envelope silently. So of the two codes `NFR8.2` names, only `STORAGE_FAILURE` reaches the log. |
| **OG-2** | A failed startup emits **no `app.*` record** — only `uvicorn.error` | **0 `app.*` records** during a failing migration; the traceback comes from `uvicorn.error`, exit status **3**, and the port never opens. `init_db` re-raises and nothing in `app/` catches it to log it in its own voice. |
| **OG-3** | The access line carries **no duration field** | Measured line: `INFO:     127.0.0.1:43452 - "GET /v2/analytics/summary HTTP/1.1" 200 OK`. **Every latency figure in this project is stopwatch-measured by a human.** |
| **OG-4** | `/v1/health` does not touch the store, so it cannot see the read path | **`200` in 1.4 ms while every analytics read was `500`**; and during a 240-request `c` = 8 saturation, health p99 was **4.444 ms** while analytics p95 was 183.5 ms. |
| **OG-5** | The `uvicorn --host` flag bypasses `resolve_bind_host`, and **nothing records how the process was started** | See **A-7** above. This one is not a gap but behaves like one. |

**Four of these five are code changes this stage may not make**, and one (OG-1)
additionally needs a policy decision that is genuinely open — whether a mistyped
date deserves a log line (**OQ-2**). Carried as **BL-08** (OG-1…OG-4) and **BL-05**
(OG-5).

## 8. The declaration-to-code drift nobody measured, stated because it is the largest

**`verification/phase-check-construction.md` records the verdict `❌ FAIL` on the
Construction → Operation boundary**, on **two** of its three confirmations: only
**1 of 4** Units is built, and the cross-Unit FR/NFR/AC gate's own recorded verdict
is `❌ FAIL — as written` (**215 ids enumerated, 83 covered**). It itemises
**eleven unresolved findings with a named owning stage each**, nine of them
blocking.

**This is drift in the most consequential sense available here: the workflow's own
boundary artifact says the work is not finished, and the Operation phase ran
anyway** — because `feedback-optimization` is `CONDITIONAL` and its condition
("ongoing operational monitoring and optimization are needed") was met by having
something to measure. That is a defensible reading and it produced the six
concurrency findings and the whole of this report. **It is not a pass, and this
report does not present it as one.**

Two of the eleven deserve restating here because they are declaration drift:

- **U2 — the cross-Unit gate FAILED, and its own spec cannot pass as written.** No
  `FR` id is ever a row in a code-generation traceability, so the literal gate
  ("covered with status `OK` in at least one entry") **cannot be satisfied for any
  `FR`, in this repository, for any Unit**. The honest decomposition is already in
  the record: **Cause 1 is a reporting-shape defect in `code-generation`'s
  traceability contract; Cause 2 is real unfinished work.** Cause 2 is "the honest
  one". Within U1's own scope, coverage is sound: **83 of 84** `AC` ids `OK` and
  **all 152 `OK` targets resolve to files that exist on disk, 0 missing**.
- **U7/U8 — two requirements are recorded as satisfied-by-remedy and unsatisfiable
  respectively.** `verification-command.txt` step 1 **exits 1** under PEP 668 on an
  externally-managed interpreter (proven pre-existing on a pristine clone of
  `HEAD`); the human declined the rewrite, so it is *not* treated as a pass. And
  the `feature` scope's "CI execution before merge" is unsatisfiable with no
  remote. Both are recorded rather than absorbed, which is why they appear here.

## 9. Summary of the drift inventory

| Class | Count | Carried to `feedback-loop.md` as |
|---|---|---|
| **D-1** Requirement drift, corrected after the fact | **4** (plus 2 same-revision corrections) | closed; R-3 (`FR7.3`'s count) still open → **BL-14** |
| **D-2** Structure drift: code vs the unit decomposition | **2**, both blocking | **BL-02** |
| **D-3** Artifact drift: a record states something measurement disproved | **7** | **BL-05, BL-11, BL-12** |
| **D-4** Undrifted by decision | **4** | **BL-07, BL-13** recorded as decisions, not defects |
| **D-5** Behaviour no requirement claims | **9** (F-1…F-6, OG-1…OG-5, two of which overlap D-3) | **BL-06, BL-08, BL-05** |
| **Boundary** — the Construction → Operation verdict is **FAIL** | **11 findings, 9 blocking** | **BL-01**, **BL-13**, **BL-17** |
| **Not-applicable** — AWS drift detection | **8 elements** | none; there is nothing to detect |

**The transferable finding, in one sentence:** every item in D-1, D-2 and D-3 was
found by **a stage reading a declaration and running one check against the code** —
not by a mechanism, not by a collector, and not by AWS Config, which does not exist
here. **The declarations in this project's record are load-bearing and unverified
between stages, and that is the drift-detection gap worth closing next**
(**BL-16**).