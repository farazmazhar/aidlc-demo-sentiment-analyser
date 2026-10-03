# Feedback & Optimization — Questions — intent `261001-analytics-layer`

> **Stage:** `feedback-optimization` (operation, final stage) · lead `aidlc-operations-agent`
> support `aidlc-aws-platform-agent` · **Date:** 2026-10-03
> **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/feedback-optimization`
>
> **This file contains no manufactured open questions.** The stage's Step 2 asks for
> clarifying questions, and this project's principles say *"questions before
> assumptions"*. Where the record already settles the matter — by a measurement, a
> requirement, an affirmed practice, or a constraint — asking the human to decide it
> would be asking them to rule on something the evidence has already ruled. Those
> are in §2, **answered from evidence**, with the source named per row. §3 holds
> only what the evidence genuinely does not settle. §4 names the questions
> deliberately **not** asked, with the reason.
>
> **Companions:** `slo-report.md` · `cost-analysis.md` · `drift-report.md` ·
> `feedback-loop.md`.

---

## 1. The organising rule

| § | Contains | Standard applied |
|---|---|---|
| **§2** | Questions the record already answers (14) | **Answered from evidence**, with the artifact and the measurement per row |
| **§3** | Questions the evidence genuinely does not settle (9) | Left open, with what is known, what a decision would change, and who owns it |
| **§4** | Questions deliberately not asked (8) | Named with the reason, so their absence is not read as an oversight |

**No question in §3 is rhetorical.** Each one changes an artifact, and each names
which one.

## 2. Answered from evidence

### 2.1 The stage's own Step-2 questions

**Q — "Are SLOs being met? What is the error budget burn rate?"**

**Answered from evidence: the six verification-window gates are met on their stated
shape; no burn rate is computable, and one is not estimated.** All six of
`slo-config`'s gates are `Met` as audited against `load-test-results` rather than
against `slo-config`'s own numbers: **zero unexpected 5xx in 1 920 ramp + 5 000 soak
requests**; the 200 ms budget met at `c` = 1 (p99 **14.297 ms** `summary`, **35.899 ms**
`terms`); store `sha256` **and mtime** unchanged after 3 000+ concurrent reads, a
100-year range and a competing writer; six of 6 provoked `500`s carrying a
distinct machine code. **The burn rate is not quoted**, because a burn rate needs a
continuously computed SLI over a rolling window and there is neither: no metric is
emitted, the largest real sample in the project is **27 requests**, and 30 requests
per level over 340 seconds is not a denominator in time. `slo-report.md` §6 gives
the four reasons in full — the shortest being that **zero failures across the run is
an absence of exposure, not a low burn rate.** Sources: `slo-config.md` §§1–4;
`load-test-results` §§2–3, 5, 11; `alarms.md` §4; `slo-report.md`.

**Q — "Are there cost optimization opportunities?"**

**Answered from evidence: ten AWS cost elements are not-applicable — no account, no
CLI, no IaC, `C-5` forbids a cloud component — and five local cost surfaces exist and
were measured.** Dependency cost: **2 declared → 24 installed → 68 995 649 B**, with
**no lockfile** and `setuptools` downloaded-and-executed unpinned per install. Store:
**32 768 B** fixed base plus **266.2 B/row** measured, **no retention policy and no
delete endpoint**. Memory: **55 940 kB at boot**, ~150–186 MB steady state, no
descriptor or thread leak, and **no multi-hour soak** to say whether that high-water
mark is a plateau. CPU: the same 240 requests cost **2.8 CPU-s at `c` = 1** and
**14.9 CPU-s at `c` = 32**. Payload: the unbounded series is **linear in the
requested range at ~192 B per entry**, reaching **7 011 966 B / 36 500 entries**.
Four ranked opportunities (`CO-1`…`CO-4`) and one accepted cost (`CO-5`) are in
`cost-analysis.md` §5. Sources: measured this stage; `load-test-results` §§3.2, 6, 12;
`quality-gates.md` §5; `runbooks.md` §9.

**Q — "Is there configuration or infrastructure drift?"**

**Answered from evidence: AWS Config and Trusted Advisor drift detection are
not-applicable per element — but there is real drift, in four classes, and 13
substantiated items.** Requirement drift: **4** requirements corrected after code
existed (`FR2.8`'s unreachable nullable mean, `FR5.3`'s non-existent SQL mechanism,
`FR7.3`'s fixture count, and the unreconciled `FR2.9`/`FR2.10`), all after being
written against a schema that was *described* rather than *read*. Structure drift:
**`app/terms.py` authored by U1 against three inception artifacts**, with a live
`U1 → U2` import edge and U1 having already chosen U2's stopword set (contract
open point O9). Artifact drift: **7** records stating something measurement
disproved — `python -m app.main` does not serve, `RB1`'s stated trigger never fires,
`cd-config.md` §5 over-generalises the store hazard, the fake-key count is **7** not
4, the suppression census is **15** not 9, RB1's exit code is 1 *or* 3, and the
analytics logger lives in `routes.py` not `analytics.py`. Behaviour with no
requirement: the six `F-1`…`F-6` findings plus OG-1…OG-5. Sources:
`drift-report.md` §§3–7; `validation-report.md` F-01…F-04; `runbooks.md` §5;
`phase-check-construction.md` §§3–9.

**Q — "What user behaviour patterns suggest new features or issues?"**

**Answered from evidence: there are no user behaviour patterns, and that is a finding
rather than a gap in the analysis.** The largest real sample the project has ever
produced from a live process is **27 requests** (`smoke-test-results.md` §2);
`dashboards.md` Panel B's capture is **13**. There is one operator, whose usage
generates no traffic pattern distinguishable from a smoke test, and **no metric is
emitted** from which a pattern could be read even if there were. What the record
*does* hold is the **store's shape**, which is the closest thing to a usage signal
that exists: the operator's real store holds **0 rows**, so **every** observation of
"how the app is used" in this record is from a fixture. **`alarms.md` §4's reason for
setting no error-rate threshold is this same fact**, and it is why
`performance-requirements.md` § "Concurrency posture" states there is **no RPS
target**: a rate over 27 requests cannot be distinguished from noise. Sources:
`alarms.md` §§1, 4; `dashboards.md` §2 Panel B; `validation-report.md` V-11;
`health-check-report.md` §4.1.

**Q — "What operational toil can be automated?"**

**Answered from evidence: five recurring manual steps exist; **three** are automatable
under the project's rules and **two are not.** Automatable: the standing
verification command (**1.67 s** for the suite, plus the boot) — `FR7.2`'s
platform-neutral script is specified but **unbuilt**; taking the store copy
(**under a second**) — one `cp -p`, and `incident-plan.md` §5.3 already prescribes
the exact command; and redirecting the logs, which costs nothing and without which
**every grep in `runbooks.md` §13 cannot work** because the access log is on
**stdout** and the application log on **stderr**. Not automatable: the four triage
greps, because **no rule engine exists** (`alarms.md` §1 names all four missing
ingredients); and **noticing that something is wrong at all**, because detection time
is **unbounded**. **`escalation-matrix.md` §3.3 puts the consequence exactly: a
restart takes 0.45–0.52 s and detection is unbounded, so the effective RTO is the
notice time** — and no SLO framework has a cell for that. The Google SRE "toil ≤ 50 %
of an operations engineer's time" standard is not usable here because **there is no
operations engineer**; `slo-report.md` §7 counts the steps instead of inventing a
denominator. Sources: `slo-report.md` §7; `escalation-matrix.md` §3.3;
`incident-plan.md` §§5.3, 6; `runbooks.md` §13; `ci-config.md` §4.

### 2.2 Further questions this stage had to answer, with the evidence

**Q — Does `load-test-results` exist as a file, or is the slug unresolvable?**

**Answered from evidence: the slug resolves to a file, under a different name.** The
stage frontmatter's `produces` list for `performance-validation` names
`load-test-results`, and its `outputs` line names the file
`load-test-plan.md, test-results.md, …`. **The framework resolved the output name to
`test-results.md`.** So this stage cites `performance-validation/test-results.md`
and uses the declared slug `load-test-results` wherever the upstream reference needs
to resolve. Same pattern for `incident-plan` → `incident-response/incident-plan.md`,
which does match. Recorded because a reader resolving the slug mechanically will
find two names, and the discrepancy is a framework resolution, not an error in either
artifact.

**Q — Is the store still byte-identical after this stage?**

**Answered from evidence: yes, on every field including the inode.** `sha256`
`c8be1361…c39`, `mtime` `2026-10-03 03:33:42.920985500 +0500`, `size` **32 768**,
`mode` **644**, `inode` **854420** — identical before the first command of this
stage and after the last. Every measurement that touched SQLite ran in a `mktemp -d`
scratch tree under `/tmp/opencode/`, both of which were removed; every read-only
query used `file:…?mode=ro`; `git status --porcelain -- app tests pyproject.toml
data README.md` is empty. **The inode is the strongest field in the set** — a
write-and-restore would produce matching content and a different inode, so an
unchanged inode plus an unchanged mtime is stronger than either alone. This stage
created, verified and altered **no** backup; `data/sentiment.db.bak-aa0b1e4` remains
**32 768 B**, sha256 `c8be1361…`, inode 857387, created by release step **R5** on
2026-10-03 at 19:53.

**Q — Should this stage have fixed anything it found?**

**Answered from evidence: no, and the record demonstrates why.** `feedback-loop.md`
is a *feedback* artifact; the stages that own the fixes are named per item. Three
precedents in this record show the discipline working: `observability-setup`
**upgraded** `health-check-report.md` §2.3's CLI bypass from a code-reading
observation to a measurement **without editing it**; `incident-response` recorded
`python -m app.main` as **OQ-IR-5** rather than adding a `__main__` guard, because
adding one is a code change and correcting the other stage's artifact is not its
call; and `performance-validation` reported `Unverified` for `NFR4.6` and `NFR4.7`
**a second time** rather than closing them with an instrument built against another
Unit's markup. **The same rule applies here**, which is why BL-01…BL-20 are backlog
items with owners rather than edits.

**Q — Is the Construction → Operation boundary a pass?**

**Answered from evidence: no. `verification/phase-check-construction.md` records
`❌ FAIL`.** Two of its three confirmations fail: **1 of 4 Units is built**, and the
cross-Unit FR/NFR/AC gate's own verdict is `❌ FAIL — as written` (215 ids
enumerated, 83 covered). **Eleven unresolved findings with a named owning stage each;
nine are blocking.** `NFR4.6` and `NFR4.7` ship **unverified**; `AC6.2.1` is
satisfied by neither owning Unit; and the `app/terms.py` boundary violation is live.
The one passing item is `ci-pipeline`'s own — *"confirm the CI quality gates enforce
the build and test commands"*. **`feedback-loop.md` §5's fourth trap addresses this
directly: running this `CONDITIONAL` stage anyway produced four backlog items that
did not exist before, which is a real gain and is not a pass.** BL-01 is the first
item in the backlog.

## 3. Genuinely open — the evidence does not settle these

Each names what is already known, what a decision would change, and who owns it.
**None was taken by this stage, and no artifact under this record's directory
depends on one being taken.**

### 3.1 The product question with the highest consequence

**OQ-FO-1 — What must be recoverable, and from which surface?**

**Known:** `GET /v1/analyses/export` **requires** `import_id` (`app/routes.py:270`,
`Query(...)`); `app/repository.py:100` filters `WHERE import_id = ?`, so
`import_id IS NULL` rows are **structurally unreachable**; `EXPORT_COLUMNS`
(`app/routes.py:86`) omits `probabilities` and `intensity`. Measured by the
incident-response stage: **1 of 3 rows** returned on a 3-row store, and `404
IMPORT_NOT_FOUND` on a 2-row store where `/v2/analytics/summary` reported
`total: 2`. Exactly **one** byte-identical manual copy exists, of a store holding
**0 rows**; **0** commits contain `data/`; no scheduler, no backup tool.
**Unsettled because:** `FR2.5` and `FR2.6` both *require* the current behaviour and
are `Met` — so this is not a defect but a **gap in the requirement set**, and no
requirement anywhere states that the operator's history must be recoverable. `import_id
IS NULL` is *precisely* the normal usage path (`POST /v1/analyze` is everyday;
`POST /v1/analyses/import` is occasional).
**A decision would change:** whether `BL-02` stays a one-line habit or becomes a
real backup surface, and whether `BL-04` needs a new FR, a default range, or an
explicit accepted-risk record.
**Owner:** the human, via **Product / Requirements Analysis** in the next Ideation
cycle. **`feedback-loop.md` Q-A.**

### 3.2 The requirement gap with the widest blast radius

**OQ-FO-2 — What behaviour under concurrent overlap is *wanted*?**

**Known, all measured in `load-test-results`:** throughput **peaks at 157.78 rps at
`c` = 2** and falls to **41.20 at `c` = 64**; per-request server CPU inflates
**11.75 → 62.21 ms** (`summary`) and **22 → 305.88 ms** (`terms`); the mixed load at
`c` = 8 runs at **p95 952.683 ms**; the same 240 requests cost **2.8 CPU-s at
`c` = 1** and **14.9 CPU-s at `c` = 32`; the `/v1/health` control reached **2 323.53
rps** at `c` = 32 with CPU flat at 0.43–0.50 ms, so the harness is not the cause.
**Nothing fails** — 1 920 ramp requests and 5 000 soak requests, zero errors,
descriptors 7 → 7, threads 1 → 2.
**Unsettled because:** `performance-requirements.md` § "Concurrency posture" **declines
to sub-number the concurrency constraint**, because hanging a `NFRx.y` id on it would
invent a parent the inception set does not contain. **That call was correct**, and its
consequence is that the six most consequential measured behaviours have no
requirement, no gate and no owner.
**A decision would change:** whether the next Inception phase creates the missing NFR
parent, and therefore whether `BL-09` is a fix or an accepted-and-documented property.
**A fix without a target would reproduce the gap it was meant to close.**
**Owner:** **Requirements Analysis**, next Inception phase. `feedback-loop.md` Q-B
and **BL-06**.

### 3.3 The contract decision three artifacts have already deferred

**OQ-FO-3 — Should the unbounded series be bounded?**

**Known:** the payload is **linear in the requested range** at **~192 B per series
entry** — 1 610 B at 7 days, 74 046 at 365, 704 766 at 3 650, **7 011 966 at
36 500** — and `/terms` over the same range is **479 B**, flat. A 100-year range
returned **36 500 entries at p99 199.700 ms, 0.3 ms inside** the 200 ms budget on
this host; `runbooks.md` IR-7 recorded **4 of 5 repeats over** at a median of
**240.7 ms**; `dashboards.md` Panel D recorded **235 ms** with **7 012 976 B**; this
stage re-measured **7 013 243 B in 189.271 ms**.
**Unsettled because:** `NFR9.3` **deliberately** imposes no cap and records the
omission as policy — `load-test-results` marked it `Met` *because* no cap exists, so
imposing one would contradict a requirement the project is currently meeting.
**Three artifacts already ruled it belongs elsewhere:** `smoke-test-results.md` §4
("a design decision for the unit that owns the analytics surface, not a deployment
observation this stage can settle"), `runbooks.md` IR-7 step 3, and
`observability-setup`'s **OQ-1**.
**A decision would change:** whether `BL-07` is a cap, a default range, a pagination
contract, or a recorded accepted risk — and it changes the `/v2` contract either way.
**Owner:** `u3-analytics-view` (Bolt 3), via a contract change. **This stage does not
overturn three prior rulings and will not.**

### 3.4 The two observability decisions that are policy, not code

**OQ-FO-4 — Should a validation failure emit an application log record?**

**Known:** measured **6 refusals → 0 application records**.
`app/routes.py:364`/`:398` log the storage branch; the `RangeError` branches at
`:359`/`:393` and the shared handler at `:470`/`:475` return the envelope silently.
So of the two codes **`NFR8.2` names** — `VALIDATION_FAILED` **and**
`STORAGE_FAILURE` — only the second reaches the log, and the stored verdict rests on
a test that exercises the storage path only. **The requirement's wording is broader
than the coverage.** The diagnosis today is the access line plus the query string,
which does carry the offending parameters.
**Unsettled because:** it is a real trade, not an oversight. With **one operator**,
a mistyped date would then write a log line on every attempt; with many operators it
would be free signal. **No affirmed practice in `team.md` or `project.md` settles
it**, and `memory/project.md` forbids adding a logging helper module by the
no-junk-drawer convention, so any fix must live in the module that owns the concept.
**A decision would change:** whether `BL-08`'s first item is a one-line call or a
requirement change — and whether `NFR8.2`'s verdict should be re-read as `Met` or
narrowed.
**Owner:** the human, via **Requirements Analysis**. Prior ruling: **OQ-2** in
`observability-setup`, open and unchanged.

**OQ-FO-5 — Should a `busy_timeout` be set, and at what value?**

**Known:** `app/db.py:213` — the **only** `sqlite3.connect` site in the application,
per its own module docstring — sets none, so CPython's default applies. This stage
confirmed the default independently: **`PRAGMA busy_timeout` → 5000 ms** on this
interpreter. Measured three times by three stages: `runbooks.md` IR-1 (5005.26 ms),
`load-test-results` `S9` (**6 of 6** reads `500` at p50 **5007.942 ms**),
`incident-response` (health `200` in **1.4 ms** throughout). Recovery is automatic: a
retry succeeded **2.63 s** after a failure while the holder was still exiting.
**Unsettled because:** the change trades a longer worst-case wait against a lower
failure rate, and **which side of that trade is right depends on whether overlap is
wanted at all** — `OQ-FO-2`. A `busy_timeout` also cannot exceed the request
pathway's own patience, so the value is coupled to whatever the next scope decides
about the view.
**A decision would change:** `BL-03`'s implementation, and whether the failure stays
"100 % of reads fail for N seconds" or becomes "some reads wait and succeed".
**Owner:** `u1-analytics-slice` (a follow-on code-generation pass), coupled to
`OQ-FO-2`.

### 3.5 The posture question the project's own mandates force

**OQ-FO-6 — Should the loopback enforcement be moved where the CLI cannot bypass
it?**

**Known and measured:** `resolve_bind_host("127.0.0.2")` refuses,
`create_app(host="127.0.0.2")` refuses before any lifespan — yet `uvicorn app:app
--host 127.0.0.2` **bound and served `200` with no refusal logged**. Confirmed at
the source this stage: `resolve_bind_host` is called at `app/main.py:93` inside
`run()` and `:120` inside `create_app()`; the CLI path reaches neither. The refusal
is exact-set membership, so the near-miss `127.0.0.2` is correctly rejected by the
resolver. **The operator mitigation available today: omit `--host`, or pass a
loopback value** — and `runbooks.md` §7's measured serving command
(`python -c 'from app.main import run; run()'`, boot to first `200` in **0.522 s**)
is the only one measured to both serve *and* enforce.
**Unsettled because:** `project.md` mandates the bind be enforced "so a non-loopback
host fails loudly", and `FR7.6` / `NFR2.4` / `BR6.5` are **`Met`** — the enforcement
is correct *where it is reached*. Closing the CLI path is a code change that moves
enforcement somewhere the CLI cannot bypass, and `memory/project.md` requires **a
fresh threat model** for any change to the exposure posture. That is a scope
decision, not a monitoring one.
**A decision would change:** whether `BL-05` is an S or a larger change, and whether
`alarms.md` §2.5's most important row gains an instrument or keeps its "manual, and
only partial" status.
**Owner:** the human, via a scope decision. Prior ruling: **OQ-3** in
`observability-setup`, open and unchanged.

### 3.6 Two decisions that are the operator's, about the operator's own machine

**OQ-FO-7 — Should the store's file mode move from 644 to 600?**

**Known:** measured **644** on a file that holds submitted text **unencrypted**
(plain SQLite format 3, **zero** SQLCipher markers in the first 4 KiB), owner
`faraz:faraz`, `umask` **022**. `anomaly-config.md` A12 records the expected value
as **600**; `validation-report.md` V-12 records the measurement; `team.md` §
Deployment records the unencrypted, world-readable posture as **deliberate** under a
single-user localhost trust model. **Nothing in the record argues for changing it.**
**Unsettled because:** it changes a file on the operator's machine, which is not the
project's to decide unilaterally — and there is no other user and no network reach.
**A decision would change:** `BL-10`, which is XS either way.
**Owner:** the human. Prior ruling: **OQ-4** in `observability-setup`, open and
unchanged.

**OQ-FO-8 — Should logs be redirected to files, and retained?**

**Known:** the access log is on **stdout** and the application log on **stderr**
(`log-queries.md` §1, established by running the server with a logger-naming format
rather than inferring it from configuration). **The cheapest fix is
`… > access.log 2> app.log`**, and `incident-plan.md` §6 names it *"the one
observability answer that is cheap but not yet taken"* — without it, a failure on one
stream is invisible to a grep on the other. **No retention, aggregation or shipping
exists**, by decision: `monitoring-design.md` §1 records it as empty, `BR2.15`
forbids adding a configuration value for it, and a session's log lives or dies with
its terminal.
**Unsettled because:** nothing in the affirmed practices fixes a log destination or
retention period, and **whether the operator wants files at all is a preference about
their own machine, not a project fact** — even though the evidence says the answer is
cheap and improves every row of `incident-plan.md` §6's detection table.
**A decision would change:** `BL-11` (XS) and, indirectly, whether any future SLI
could be computed at all — which is the precondition for every SLO question in
`slo-report.md`.
**Owner:** the human. Prior ruling: **OQ-5** in `observability-setup`, open and
unchanged.

### 3.7 One question about the record itself

**OQ-FO-9 — Should this workflow's boundary FAIL gate the closing approval?**

**Known:** `verification/phase-check-construction.md` records **`❌ FAIL`**, 11
unresolved findings, **9 blocking**, and states in §11 that *"Approval is not
recommended on the current record"* and that *"the correct next actions, in order"*
are: continue the Bolt sequence, a Delivery Planning re-run for the boundary fix, and
two human decisions. `aidlc-state.md` nevertheless shows Operation Active and this
stage running, because `feedback-optimization` is `CONDITIONAL` and there was real
operational evidence to synthesise.
**What that produced:** four backlog items that did not exist before this stage —
**BL-03** (the `busy_timeout`), **BL-06** (the missing NFR parent), **BL-08** (the
four observability gaps), **BL-09** (`/terms` as the hot spot) — none of which any
requirement or artifact had surfaced.
**Unsettled because:** this is a process judgement about what a `CONDITIONAL` final
stage means when the boundary above it failed. **The honest position is that the
stage's own execution was valuable and the boundary verdict is unresolved, and this
file does not resolve it by asserting one over the other.**
**A decision would change:** whether this workflow closes with BL-01 open, or stays
open until the three remaining Units are built.
**Owner:** the human. Carried as **BL-01** and as `feedback-loop.md` §5's fourth
trap.

## 4. Questions deliberately not asked

| Not asked | Why |
|---|---|
| "What is your monthly AWS spend?" | **There is none.** No account, no CLI, no credential, no IaC — measured by `environment-inventory.md` (M1–M5) and re-confirmed this stage. Asking would imply a figure exists. |
| "Should I set an error-rate alarm at N %?" | **No rate is computable.** The largest real sample is 27 requests; over 13 a percentage quantises to 7.7 % steps. `alarms.md` §4 lists this among four thresholds deliberately not set, each with its reason. |
| "What is your RTO and RPO?" | **There is no tier and no backup.** `escalation-matrix.md` §3.3 records that the measured RTO's dominant term — noticing — is unbounded and not a system property, and that the guide's tier table has no cell for "whenever the operator notices". **That is the honest answer, and it is already written.** |
| "Who is the on-call engineer for SEV1?" | **There is nobody to name.** `escalation-matrix.md` §3.2 records that inventing a name would put a verifiable-sounding fiction into the one artifact class whose value is that every line is checkable. The escalation path is the operator, at every severity, and that is the finding rather than a shortfall. |
| "Which cloud provider should the next scope use?" | **`C-5` forbids any external service or cloud component, and `team.md` § Deployment affirms a localhost checkout as the whole deployment.** This project's constraints make the question unaskable, not merely undecided. |
| "Should we add X-Ray / distributed tracing?" | **There is nothing to trace.** One process, no network hop on the read path — `validation-report.md` V-28 found **no network-capable import at all** in the read path's closure. A trace would have a single span. `tracing-config.md` §1 established this before this stage ran. |
| "Do `NFR4.6` and `NFR4.7` need observability work?" | **They are owned by `u3-analytics-view`** and were accepted as carried-forward debt by the human at Build and Test. Nothing in this stage's remit changes that ownership, and reporting them a second time as `Unverified` is the correct output, not a request for a decision. |
| "Should the series cap be applied now, since it breaches the budget?" | **It did not breach it on this host** — p99 **199.700 ms**, 0.3 ms inside — while `runbooks.md` IR-7 recorded 4 of 5 repeats over on the same host. **The finding is real and host-dependent**, and the decision belongs to `OQ-FO-3`'s owner. This stage costs the payload in `cost-analysis.md` §3.5 and does not re-litigate it. |

## 5. Summary of this stage's posture

**Answered from evidence and closed (14):** SLO compliance and the refusal to
manufacture a burn rate · cost optimisation, per element and then locally ·
configuration and requirements drift, in four classes · user-behaviour patterns,
answered as *none exist and that is the finding* · operational toil, three
automatable and two not · the `load-test-results` slug resolution · store integrity
including inode · whether this stage should fix anything (no) · and whether the
boundary is a pass (**no**).

**Left open for the human (9):** `OQ-FO-1` what must be recoverable · `OQ-FO-2` what
overlap behaviour is wanted · `OQ-FO-3` whether the series is bounded · `OQ-FO-4`
whether a `422` deserves a log line · `OQ-FO-5` whether and at what value a
`busy_timeout` · `OQ-FO-6` whether the bind moves where the CLI cannot bypass it ·
`OQ-FO-7` whether the store's mode tightens · `OQ-FO-8` whether logs are redirected
and retained · `OQ-FO-9` whether this workflow closes with BL-01 open.

**Of the nine: two are decisions only Requirements Analysis can take** (`OQ-FO-1`,
`OQ-FO-2`), **one belongs to an unbuilt Unit** (`OQ-FO-3`), **two need a code change
before they can be measured** (`OQ-FO-4`, `OQ-FO-6`), **two are one-line source or
habit changes coupled to another decision** (`OQ-FO-5`, `OQ-FO-8`), **one touches a
file on the operator's machine** (`OQ-FO-7`), and **one is a process judgement about
this workflow** (`OQ-FO-9`). **Five of the nine inherit an existing open ruling** —
OQ-1, OQ-2, OQ-3, OQ-4, OQ-5 from `observability-setup` — and **this stage does not
reopen any of them**; it carries them forward with the measurement that has landed
since.

**Not provisioned, per element, with the ruling rule in each file:** CloudWatch
dashboards, metrics, Logs Insights, Synthetics and anomaly detection · AWS Config
rules, conformance packs and drift correction · AWS Cost Explorer, cost allocation,
rightsizing and commitment coverage · Trusted Advisor · CloudTrail · resource
tagging · CloudWatch burn-rate alerting · distributed tracing · log shipping and
retention. **The one-line reason, common to all:** no AWS account, no CLI, no
credential and no IaC on this machine — and `C-5` forbids a cloud component while
`C-6` caps declared runtime dependencies at exactly `fastapi` and `uvicorn`, so no
exporter or collector could be added even if there were.