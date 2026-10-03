# Incident Response — Questions — intent `261001-analytics-layer`

> **Stage:** `incident-response` (operation) · lead `aidlc-operations-agent`
> · **Date:** 2026-10-03 · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/incident-response`
>
> **Upstream inputs consumed by this stage:** `operation/observability-setup/`
> — `alarms` (`alarms.md`), `dashboards` (`dashboards.md`), `anomaly-config.md`,
> `log-queries.md`, `slo-config.md`, `observability-setup-questions.md`;
> `construction/u1-analytics-slice/nfr-design/reliability-design.md`
> (`reliability-design`), `security-design.md` (`security-design`);
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`);
> `operation/deployment-pipeline/rollback-runbook.md`;
> `operation/environment-provisioning/validation-report.md`;
> `operation/deployment-execution/health-check-report.md`;
> `memory/team.md` § Deployment, § Code Style; `memory/project.md`
> `## Forbidden` (`C-5`), `## Mandated` (`C-6`, `C-10`);
> `memory/phases/operation.md` § Incident Response.
>
> **This file contains no manufactured open questions.** The stage's Step 2 asks
> for clarifying questions, and this project's principles say *"questions before
> assumptions"*. Where the answer is already fixed by an affirmed practice, a
> recorded measurement, or a constraint, inventing a question would be asking the
> human to decide something the record has already decided. Those are recorded in
> §2 as **answered from evidence**, with the source named per row. §3 holds only
> what the evidence genuinely does not settle, and every one of them is a
> decision this stage is not authorised to take. §4 names what was deliberately
> not asked, so the absence is not read as an oversight.

---

## 1. The organising rule, stated once

| § | Contains | Standard applied |
|---|---|---|
| **§2** | The stage's own Step 2 questions, and the further questions this stage had to resolve | **Answered from evidence**, with the source named per row |
| **§3** | What the evidence genuinely does not settle | Left open, with what is already known and what a decision would change |
| **§4** | Questions deliberately **not** asked | Named, with the reason |

---

## 2. Questions answered from evidence

### 2.1 The stage's own Step 2 questions

The stage defines five. All five are answered, none deferred.

---

**Q — "What are the most likely failure modes?"**

**Answered from evidence: eleven, all reproduced in this stage, and "most
likely" is not a ranking this project can compute.** There is no traffic history
— the largest real sample the project has ever produced is 27 requests
(`alarms.md` §4) — so frequency is unknowable and the eleven are classified by
**consequence** instead. Enumerated with their measured symptoms in `runbooks.md`
§2 and each with its own procedure:

| ID | Failure mode | Measured symptom |
|---|---|---|
| IR-1 | Analytics read fails, another process holds the store | `500 STORAGE_FAILURE`, **each failing request costs 5.0 s** |
| IR-2 | Refused request (bad date, inverted range, `limit` < 1, wrong body shape) | `422 VALIDATION_FAILED`, **0 application records** |
| IR-3 | Empty/whitespace text submitted | `422 INVALID_TEXT`, **0 application records** |
| IR-4 | Startup migration cannot preserve a row | `sqlite3.IntegrityError`, **exit 3, port never opens**, store byte-identical |
| IR-5 | App reachable off loopback | `200` on `127.0.0.2`, **no refusal logged** |
| IR-6 | The documented run command does not serve | **no listener**, instant exit |
| IR-7 | A very wide range | `200`, **~7 MB / 36 525 entries / ~240 ms** |
| IR-8 | Store damaged or gone | app starts with **zero history** |
| IR-9 | Store behind `SCHEMA_VERSION` | boots and **writes** the store |
| IR-10 | Credential material in a log | **SEV1** — external and permanent damage |
| IR-11 | A refusal mistaken for an empty result | `422` vs `200 total:0` |

Sources: measured this stage against real `uvicorn` and real SQLite files on
scratch stores; classification criteria in `escalation-matrix.md` §2, derived
from the failure classes in `reliability-design` §2.2.

---

**Q — "What are the escalation paths and on-call rotations?"**

**Answered from evidence: there are none, and the absence is the finding.**
Measured: no pager, no SNS topic, no webhook, no chat integration, no monitoring
agent, no scheduled job (`alarms` §1). One person operates, develops and deploys
this system (`memory/team.md` § Deployment). The standard rotation in
`incident-response-guide.md` §On-Call requires *"at least 2 people trained for
on-call at all times"*; there is 1, so a rotation of one is a rename rather than
a rotation.

**Every row of the escalation matrix therefore reads: no escalation path exists;
the operator is the last resort** — `escalation-matrix.md` §3.1, with each
absent column's reason in §3.2 and the four concentration risks in §3.4.

The one non-empty answer is about what happens when the operator is *not*
available: the incident stays broken until they look, and nothing bounds how
long that is (`escalation-matrix.md` §3.3).

---

**Q — "What automated remediation is possible?"**

**Answered from evidence: none, and nothing in this project could make it
possible.** An automated remediation needs a trigger, and `alarms` §1 names the
four ingredients that are all absent: a metric to threshold on, a rule engine to
evaluate it, a notification channel to route the result, and a schedule to
evaluate it without a human.

The recorded consequence is this project's own phrase, from
`rollback-runbook.md` §5: the automated rollback trigger is *"a human noticed"*,
because *"inventing a threshold nobody can observe would be a gate with no
instrument behind it."* What replaces automation is a documented, ordered set of
checks a person runs: `runbooks.md` §13, four commands, each under a second,
whose thresholds all come from `alarms` §2 and whose instruments are
`dashboards` Panels A–D.

**One partial exception, and it is not automation:** the mitigation ladder in
`incident-plan.md` §4 is ordered by measured cost — narrow the range (instant),
stop the other process (instant), retry (up to 5 s), restart (**0.45–0.52 s**),
restore the copy (under a second), roll back the commit (one restart) — so the
operator's default action at 1am is the cheapest one that works.

---

**Q — "What are the communication procedures during incidents?"**

**Answered from evidence: there are none, because there is nobody to communicate
to.** No stakeholder, no user but the operator, no team channel, no status page.
`incident-response-guide.md` §Communication assumes *"a dedicated
Slack/Teams channel"* and a status page for *"SEV1: within 20 minutes"*; neither
surface exists and neither has an audience.

What replaces it, and it is not nothing: **a durable incident record**, one file
per incident, written once at the end rather than streamed during
(`incident-plan.md` §5). The rationale is worth stating because it is the one
place this system is *better* than the standard: with no audience to orient, the
timeline does not need 15-minute updates, and a file that survives the terminal
is strictly more useful than a channel that scrolls away. The cost is that it is
written after the fact, and §5.2's template exists to stop that from becoming
vague.

The rules that do apply: never write an unmeasured cause into the record (with
one operator there is no second opinion to catch a guess, and a durable file
will be believed later); never put a credential in it
(`memory/project.md` `## Forbidden`).

---

**Q — "What are the RTO/RPO targets?"**

**Answered from evidence, with the reasoning, and the honest number is worse
than the tier table's best row.**

**RTO — two components, and only one is under the system's control:**

| Component | Measured | Reasoning |
|---|---|---|
| Restore the process | **0.45–0.52 s** | three runs, exec → first HTTP 200 on `/v1/health` |
| **Notice that it is broken** | **unbounded** | nothing detects anything; the detection time is "until the operator looks", which is not a number this project sets |
| Diagnose | **under 10 s** | four checks in `runbooks.md` §13, once looking |
| Recover the store | **under a second** | `mv` the copy and start; migrates forward idempotently |

**So the effective RTO equals the detection time**, and quoting the 0.45 s
restart alone would be a fiction. `incident-response-guide.md` §RTO's tier table
has no cell for "whenever the operator notices" — that absence is the honest
answer. There is no cell for the vendor case either: an upstream OpenRouter
outage becomes this project's outage, because the only available response is to
wait (`C-5` forbids depending on anything else).

**RPO — since the last manual copy, and the measured state of that copy is not
what "no backup" or "backup" would suggest:**

| Measured | Value |
|---|---|
| Commits containing the store | **0** (`.gitignore:94:/data/`) |
| Copies on this machine | **exactly 2**, both under `data/`, both sha256 `c8be1361…` |
| Where the second came from | release step **R5**, a manual `cp` taken at 19:53 today |
| Scheduled / off-machine / second-host copies | **none** |
| Backup tooling in the repo | **none** — no `scripts/`, no `VACUUM INTO`, no `iterdump`, no `.backup()`, no `shutil.copy2` |

So the store's RPO is **"since the last manual copy"**. Today that copy is
byte-identical to the store, so the current RPO is zero — **by luck, not by
design** — and it becomes nonzero the instant a row is written.

**And for most of this app's rows the RPO is not "unbounded", it is *worse than
unbounded*: the export surface cannot reach them at all.** Measured:

- `GET /v1/analyses/export` **requires** `import_id` (422 without it) and
  excludes every row written by single analysis (`import_id IS NULL`,
  `FR2.6`).
- On a 3-row store it returned **1 of 3** rows.
- On a 2-row store containing only single-analysis rows, it returned
  `{"code":"IMPORT_NOT_FOUND"}` **404** — while `/v2/analytics/summary` on the
  same store returned `total: 2`. **Readable and simultaneously unreachable by
  the only copy surface.**
- Even a successful export is **lossy**: `EXPORT_COLUMNS` is
  `(id, text, label, confidence, model, provider, created_at)`, so
  `probabilities` and `intensity` are dropped, and a re-import creates a new
  `import_id`. It is a view, not a backup.

**The only defensible statement of the data's real exposure:** rows written
since the last manual copy are lost; rows written by single analysis cannot be
exported at all; and `probabilities` and `intensity` are lost even from a
successful export. Sources: `infrastructure-specification` §5 (backup,
replication, failover and HA **not provisioned**), `reliability-design` §5 (the
same, for the design), `rollback-runbook.md` RB3 (no procedure, deliberately),
`runbooks.md` §9.

---

### 2.2 Further questions this stage had to resolve, answered from evidence

---

**Q — Is a failed startup visible in the application log?**

**Answered from evidence: no — and this is an incident-response hazard, not just
an observability one.** With a logger-naming format, a failing migration emitted
**0** `app.*` records and two `uvicorn.error` ones (`Traceback …` and
`Application startup failed. Exiting.`), exit status **3**, port never opened.
`init_db` re-raises and nothing in `app/` catches it to log it in its own voice.
Sources: measured; `log-queries.md` §2.3 and §4(d);
`reliability-design` §2.1 and §4 (the migration is deliberately loud — loudly,
but in the framework's voice).

**Operational consequence, and it is why `runbooks.md` §13 puts a socket check
before any grep:** an operator watching only the application loggers sees
nothing at all about a failed startup.

---

**Q — Does the storage-failure record carry a stack trace?**

**Answered from evidence: no.** `app/routes.py:364` and `:398` call
`logger.error(...)`, not `logger.exception(...)`, so the record is a single line
holding `str(exc)` — measured, verbatim:

```
ERROR:     analytics summary read failed (STORAGE_FAILURE): database is locked
```

`security-design` §3.4 is satisfied (nothing leaks to the *client*); the cost
lands on the responder, who loses the frames. The wire surface and the log still
agree on the machine code, which is what makes the failure classifiable.

---

**Q — Is a `STORAGE_FAILURE` persistent, and does it need a restart?**

**Answered from evidence: it is transient, and no restart is needed.** This
question is not answered anywhere upstream, and the answer changes the runbook.
Measured with a second process holding `BEGIN EXCLUSIVE` for 20 s:

```
  req1 summary -> HTTP=500 wall=5.018122s
  req2 summary -> HTTP=500 wall=5.005439s
  req3 summary -> HTTP=500 wall=5.005064s
  health -> HTTP=200 wall=0.001352s
```

and directly against the file: attempt 1 → `OperationalError: database is locked`
after **5005.26 ms**; attempt 2 → **OK in 2630.48 ms** (succeeded once the
holder released); attempts 3–5 → **OK in ~0.1 ms**.

Two facts follow. First, **each failing request costs 5.0 s**, because
`app/db.py:213` opens the connection with `sqlite3.connect(path,
check_same_thread=False)` and sets no `busy_timeout`, so CPython's 5.0 s default
applies — that is 25× the 200 ms budget (`tests/test_analytics_read.py:34`), and
the access log cannot show it because it carries no duration field
(`dashboards` §5). Second, **`/v1/health` answered `200` in 1.4 ms throughout** —
it does not touch the store, so **a green health line cannot detect this
failure.**

---

**Q — Does the `uvicorn --host` bypass reach a real exposure?**

**Answered from evidence: the bypass is real and the exposure is not.** Measured:
`resolve_bind_host('127.0.0.2')` → REFUSED; `create_app(host='127.0.0.2')` →
REFUSED before any lifespan ran; then `uvicorn app.main:app --host 127.0.0.2`
**bound `127.0.0.2:8314` and served `200`**, was unreachable on `127.0.0.1`, and
logged **no refusal** (`grep -ci refus` → 0). The enforcement is in `run()`, so
the CLI never consults it. Sources: `security-design` §4;
`health-check-report.md` §2.3; `alarms` §3.1, which records the detection's blind
spot — `ss` shows the socket as it is *now* and has no memory.

The enforced path itself was verified to hold, without touching source, by
rebinding the captured default: `RESULT: REFUSED before uvicorn started`. A
related measurement worth recording: `def resolve_bind_host(host: str = HOST)`
captures `HOST` **at definition time**, so `resolve_bind_host()` with no
argument ignores a later `m.HOST = '0.0.0.0'` (measured → `127.0.0.1`).

---

**Q — What recovery time can this system actually claim?**

**Answered from evidence: 0.45–0.52 s to serve, and that number is not the one
that matters.** Three `uvicorn` boots measured at **0.467 / 0.453 / 0.462 s**;
the `run()` path at **0.522 s**. The number that governs an incident is the
detection time, which is unbounded — see the RTO answer in §2.1.

A second measured recovery fact, and the reason IR-6 exists: **`python -m
app.main` does not serve.** `grep -n '__main__' app/main.py` → no match, so the
module executes, prints

```
<frozen runpy>:130: RuntimeWarning: 'app.main' found in sys.modules after import of
package 'app', but prior to execution of 'app.main'; this may result in unpredictable behaviour
```

and exits, with **no listener**. `health-check-report.md` §2.3 names
`python -m app.main` as a documented run path. The invocations measured to serve
are `python -c 'from app.main import run; run()'` (**0.522 s**, and it *enforces*
the bind) and `uvicorn app.main:app` (**0.45–0.47 s**, and it *bypasses* it).

---

**Q — Is RB2 still safe, i.e. is rolling the code back still free of data loss?**

**Answered from evidence: yes, re-verified rather than inherited**, because
`runbooks.md` §6.1 inlines it and an inlined runbook must not drift. A real v4
store with two rows, then the released `express` code's own `init_db`
(`SCHEMA_VERSION = 3`, recovered with `git show beeb587:app/db.py`):

```
STEP 1 (new code, before rollback): version=4 rows=2 indexes=3 rel=[(1,'negative',0.9),(2,'positive',0.9)]
STEP 2 (old init_db ran):             version=3 rows=2 indexes=3 rel=[(1,'negative',0.9),(2,'positive',0.9)]
ROW DATA SURVIVED : True
STEP 3 (re-upgrade):                  version=4 rows=2 indexes=3 rel=[(1,'negative',0.9),(2,'positive',0.9)]
```

**2 rows → 2 rows, all three indexes survived, the relation was unchanged, and
re-upgrading is idempotent.** That is what turns a rollback into a `git revert`
plus a restart instead of a data-recovery exercise. RB1 was re-rehearsed too: the
store was byte-identical after the failure, `schema_meta` was never created, and
both rows survived.

One precision worth carrying, because I got it wrong first: **the rebuild fires
only when the physical table is not exactly v1-shaped.** A *v3* store boots
cleanly — the current relation **is** v1-shaped, so no rebuild runs and no
`CHECK` is exercised. My first attempt at reproducing RB1 failed to fail for
exactly this reason. The trigger is an older physical shape (e.g. missing
`import_id`) **plus** a row whose `label` is outside the domain.

---

**Q — What is the real backup position?**

**Answered from evidence, and it is neither "backed up" nor "no backup".**
Measured: `git log --all --oneline -- data/ | wc -l` → **0**; `git check-ignore -v
data/sentiment.db` → `.gitignore:94:/data/`; a tree-wide find for
`*.db`/`*.sqlite*`/`*.bak*` returns **exactly two files**, both under `data/`,
both sha256 `c8be1361…`; `ls scripts/` → **no such directory**; and no
`VACUUM INTO`, `iterdump`, `.backup()` or `shutil.copy2` anywhere in `app/`,
`tests/` or the docs.

**There is no backup *mechanism*; there is exactly one manual copy**, taken once
by release step R5, byte-identical to the store it protects. `infrastructure-specification`
§5 and `reliability-design` §5 both record backup, replication, failover and HA
as not provisioned — and that remains accurate, because a manual release-step
copy is not a backup path. The difference between those two sentences is exactly
what §9 of `runbooks.md` costs.

---

**Q — Can a `422` and an empty result be told apart at 1am?**

**Answered from evidence: yes, from the body alone, and the three shapes are
deliberately distinct.** Measured in one run:

```
{"total":0,…,"series":[]}                                                        HTTP=200
{"code":"VALIDATION_FAILED","message":"query.from: expected a UTC calendar date…"}  HTTP=422
{"code":"STORAGE_FAILURE","message":"The analytics store could not answer…"}       HTTP=500
```

Framework-generated errors keep FastAPI's shape and are **not** this envelope —
measured `404 {"detail":"Not Found"}` and `405 {"detail":"Method Not Allowed"}` —
which is the affirmed rule in `memory/project.md` `## Mandated`, and is exactly
how to tell an app-raised failure from a routing mistake. `null` where there is
no denominator is deliberate, never a fabricated `0.0`
(`reliability-design` §2.3); a `404` for emptiness never occurs.

---

**Q — Is a very wide range really over budget?**

**Answered from evidence: yes, reproduced, and two details stop it being
misdiagnosed.** Ladder over real HTTP against a **one-row** store: 7 days →
1 518 B / 7 entries / 1.7 ms · 1 year → 70 254 B / 365 / 4.8 ms · 21 years →
1 542 894 B / 8 035 / 49.3 ms · **100 years → 7 012 974 B / 36 525 entries /
252.7, 248.5, 193.6, 221.0, 240.7 ms** — **four of five over the 200 ms budget**,
median 240.7 ms. `dashboards` Panel D and `alarms` §2.4 record the same crossover;
my byte count differs from theirs by two (response framing) and my wall time is
10–20 ms slower, so it is reproduced rather than inherited.

- **`/v2/analytics/terms` is width-insensitive**: 136 B, 2.2 ms at the same
  100-year range. The cost is series assembly on `/summary` alone.
- **An empty store yields an empty series at any width** — 183 bytes, 0 entries,
  for a 100-year request against a 0-row store. So "payload is linear in the
  requested range" is true **only once the range matches a row**
  (`BR3.3`/`BR4.4`), and the naive reading would send an operator looking for the
  wrong cause.

---

**Q — Is the store's file mode a finding, and does it belong in a runbook?**

**Answered from evidence: yes to the first, and it is inherited rather than
re-decided.** Measured **`644`** where `anomaly-config.md` A12 expects **`600`**,
recorded also by `validation-report.md` V-12. It appears in `runbooks.md` §11
because "unauthenticated by design" extends to the file: the store holds
submitted text unencrypted and is world-readable on this host. **The tightening
is not this stage's to do** — it changes a file on the operator's machine — and
it is `observability-setup-questions.md` **OQ-4**, still open, re-referenced here
rather than re-opened.

---

**Q — Does the export endpoint make the RPO acceptable?**

**Answered from evidence: no, and this is the sharpest correction in this
stage.** Measured, not reasoned: `export` **requires** `import_id` (422 without
it); it excludes every row with `import_id IS NULL` (`FR2.6`); on a 3-row store
it returned **1 of 3** rows; on a 2-row all-single-analysis store it returned
**404** while `/v2/analytics/summary` on the same store returned `total: 2`; and
`EXPORT_COLUMNS` omits `probabilities` and `intensity`, so even a successful
export is lossy and a re-import mints a new `import_id`.

**The export is a view, not a backup**, and for an operator whose history is all
`POST /v1/analyze` — the normal way to use this app — there is **no working copy
surface at all**. That is why `runbooks.md` §9 states the unrecoverable cases as
four separate items rather than as one sentence about backups.

---

### 2.3 Questions answered by an affirmed practice, with the practice named

---

**Q — Should the bind exposure be treated as an incident or a deployment
mishap?**

**Answered from evidence and from an affirmed rule: an incident.**
`memory/project.md` `## Mandated`: *"ALWAYS keep the app localhost-only: bound to
loopback (127.0.0.1) and unauthenticated by design; any non-loopback bind,
hosted deploy or change to the authentication posture requires a fresh threat
model."* `security-design` §4 calls it *"the central hardening"* and threat
**T5** *"the principal risk this unit could introduce"*, and
`memory/project.md` `## Forbidden` forbids a real credential in any artifact —
so a leak is the one failure mode whose damage is external and permanent
(`runbooks.md` §11). Hence SEV1 with an immediate response
(`escalation-matrix.md` §2).

---

**Q — Is RB3's absence a gap this stage should fill?**

**Answered from evidence and from a recorded decision: no — filling it would be
the failure mode.** `rollback-runbook.md` §4 states it in one line: *"This is
the one with no procedure, and it is written here so its absence is
unambiguous."* This stage re-measured the whole position and **restated** the
absence (`runbooks.md` §9) rather than inventing a path. The only entry that
exists is **prevention** — take and verify the copy — and the re-measurement
strengthened the argument for it: the export surface cannot reach most of the
data, so the `cp` is not a convenience.

---

**Q — Should runbooks carry contact information and escalation paths, as the
phase guardrail asks?**

**Answered from evidence and from the guardrail itself: the guardrail is
satisfied by recording the absence, not by filling it.**
`memory/phases/operation.md` § Incident Response: *"Runbooks must include
escalation paths and contact information."* The honest fulfilment is: the path
is stated (operator → nothing), the path's **terminal state** is stated as the
operator for every severity (`escalation-matrix.md` §3.1), and the
"contact information" that exists is **machine-local** — the port, the file path,
the check command — because there is no second person to contact. Naming an
absent responder would put a fiction into the one artifact class whose value is
that every line is checkable.

---

## 3. What the evidence does not settle — genuinely open

Five items. Each is a real decision, each is **outside this stage's authority**,
and no artifact under this record's directory depends on one being taken.

---

**OQ-IR-1 — How often should the store be copied, and is `cp` on every start
acceptable?**

This is the single highest-value open decision in the project, and the evidence
now makes it concrete. Measured: one manual copy exists, taken once by release
step R5; nothing schedules it; the store's mtime is `2026-10-03 03:33:42` while
the copy's is `19:53`, so **the copy is already stale the moment a row is
written.** Three defensible answers, and they cost different things:

| Option | Effect | Cost |
|---|---|---|
| **Release-step only** (today) | RPO = everything since the last release | the weakest option, and the only one currently in force |
| **Per-boot** | RPO ≈ one session | a copy on every start, which `validation-report.md` **F-01** warns is *not* the same thing as the migration hazard — and which would make a habitual `cp` out of a release discipline |
| **Per-incident + after any write** | RPO ≈ one incident | needs a trigger, and **there is no trigger** (no metric, no rule engine, no schedule — `alarms` §1) |

**Nothing in `memory/team.md` or `memory/project.md` settles it.** `R5` is a
release step; `incident-plan.md` §5.3 proposes a per-incident copy as a
*discipline*, not as a mechanism. **This is a decision about the operator's own
machine and their own data**, which is why it is put here rather than decided.

---

**OQ-IR-2 — Should `app/db.py` set an explicit `busy_timeout`?**

Measured: `sqlite3.connect(path, check_same_thread=False)` at `app/db.py:213`
sets none, so CPython's **5.0 s** default applies. Consequence, measured: a
contended read blocks for 5 s and then **fails** with
`OperationalError: database is locked` → `500 STORAGE_FAILURE`; the next attempt
succeeded **2.63 s** after the holder released. So today the app waits 5 s and
*still* loses the request.

Three shapes, and each changes IR-1's recovery differently: leave it (fail fast
at 5 s — current behaviour); raise it (wait longer, succeed more often, but a
held lock then stalls a worker thread for the full timeout); shorten it (fail
fast, surface the failure sooner). **No affirmed practice settles it**, and it is
a one-argument change with a real trade. `reliability-design` §5 rules out
retries *in the read path* as a design matter; a busy timeout is a
driver-level concern rather than a retry, so that ruling does not decide it.

---

**OQ-IR-3 — Should `EXPORT_COLUMNS` gain `probabilities` and `intensity`?**

Measured: the export is lossy today, and it is the **only** copy-bearing surface
in the project. Omitting two columns means a successful export is not a
restorable snapshot even for the rows it does carry.

The blocker is that this changes the frozen `/v1` response contract, so it
belongs to the unit that owns that surface, not to an operations stage.
**Decide there.** This is the sharpest form of the question
`observability-setup-questions.md` **OQ-1** poses for the read surface — a
capability the incident posture depends on and cannot supply.

---

**OQ-IR-4 — Should `/v1/health` report store reachability?**

Measured: health answered `200` in **1.4 ms** while every analytics read was
returning `500`, because it does not touch the store. So the one endpoint an
operator is most likely to trust as "the app is fine" **cannot detect the
failure that matters most** for the analytics layer.

This would add a store read to the health endpoint — changing its cost and its
contract, and making a *health* endpoint capable of failing for a reason
unrelated to process health. A real design trade, not a monitoring tweak, and the
same class of decision as OQ-IR-3. **Belongs to the unit that owns the HTTP
surface.**

---

**OQ-IR-5 — Which artifact gets corrected for `python -m app.main`, and is a
`__main__` guard wanted?**

Measured: `app/main.py` has **no `__main__` guard**, so `python -m app.main`
exits immediately with a `RuntimeWarning` and no listener. That invocation is
named as a documented run path in `health-check-report.md` §2.3 ("the enforced
bind holds on the documented run path (`python -m app.main` / `app.main:run`)")
and the phrase "documented run path" also implies it in `memory/team.md`
§ Deployment. **The artifact is wrong; this stage cannot correct another stage's
artifact, and adding the guard would be a code change.**

Two questions inside it: does the record get corrected (and where is that
recorded?), and should `app/main.py` gain a `__main__` guard so the documented
invocation actually serves? Until one is answered, `runbooks.md` §7 names the two
invocations measured to work, and this stage's measurements are the evidence that
the third does not.

---

### 3.1 Open items inherited, re-referenced rather than re-opened

Four upstream questions remain open and are load-bearing for this stage's
posture. None was decided here; each is listed so an incident record's "what to
change" section points at the right row.

| Upstream | Question | Why it matters to incident response |
|---|---|---|
| `observability-setup-questions.md` **OQ-1** | Should the summary series width be bounded? | the only reproducible latency breach (`runbooks.md` §8); the decision belongs to `u3-analytics-view` |
| **OQ-2** | Should a validation failure emit an application log record? | **OG-1** — 6 × `422`, 0 records; a `422` is diagnosable only from the access line |
| **OQ-3** | Should the `uvicorn --host` bypass be closed? | **OG-5** — the bind is a property of *how the process was started*, and nothing records how it was started |
| **OQ-4** | Should the store's file mode be tightened to `600`? | measured `644`; world-readable submitted text on this host (`runbooks.md` §11) |
| **OQ-5** | Should logs be redirected to a file? | **the cheapest available improvement to every row** of `incident-plan.md` §6, and still not taken |

---

## 4. Questions deliberately not asked

Named so their absence is not read as an oversight. Each would ask the human to
decide something the record has already decided, or would require a fact nobody
here possesses.

| Not asked | Why |
|---|---|
| **"Who is the primary and secondary on-call?"** | There is one person, and naming a second would be a fiction in an artifact whose value is that it is checkable. `escalation-matrix.md` §3.2 records the absence and the rule. |
| **"What is the escalation contact for SEV1?"** | No management layer, no stakeholder, no users but the operator. There is nobody to name. |
| **"How should incident status be communicated, and to whom?"** | No audience. The substitute is a durable incident record (`incident-plan.md` §5), which is strictly better here than a channel and needs no decision. |
| **"Should we schedule quarterly game days / DR drills, as the guide
suggests?"** | With one operator and one machine the rehearsal **is** the drill: `rollback-runbook.md` §5 rehearsed RB1/RB2/RB3 against real files and real `uvicorn`, and this stage re-rehearsed RB1 and RB2. Scheduling a calendar entry would add ceremony without adding coverage. |
| **"What backup retention and off-site policy do you want?"** | There is no off-site to retain anything on, and `C-5` forbids creating one. The real question is not retention but **frequency**, which is OQ-IR-1 and is genuinely open. |
| **"Which AWS service should replace the missing pieces?"** | `C-5` and `C-6` rule out every candidate: no new external service, hosted dependency or cloud component, and declared runtime dependencies are exactly two. This is not a question the project may ask. |
| **"What is the acceptable downtime for this app?"** | **Asked and answered** — in §2.1, from measurement: the restore is 0.45–0.52 s and the *detection* is unbounded, so the effective RTO is the detection time. There is nothing left to ask. |
| **"Should we cap the response size or add a request limit?"** | `NFR9.3` caps the series width **deliberately, by nothing**, and capping it changes the `/v2` contract. OQ-IR-3/OQ-1 already carry it to the unit that owns the surface. |

---

## 5. Standing constraint honoured by this stage

**No application source, test, configuration or data-store file was modified.**
Every store inspection used `file:…?mode=ro`; every process booted ran with its
CWD inside `/tmp/opencode/ir/`, so the store it opened was a throwaway.
`git diff --stat app tests pyproject.toml config.example.toml README.md` is
empty. The operator's `data/sentiment.db` is byte-identical before and after,
**down to the mtime**:

```
before  sha256 c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
        mtime  2026-10-03 03:33:42.920985500 +0500   size 32768   mode 644
after   sha256 c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
        mtime  2026-10-03 03:33:42.920985500 +0500   size 32768   mode 644
```

`data/sentiment.db.bak-aa0b1e4` — the one manual copy that exists — is
untouched and still byte-identical to the store it protects.
