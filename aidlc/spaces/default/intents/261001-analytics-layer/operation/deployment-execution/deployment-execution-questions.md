# Deployment Execution Questions — intent `261001-analytics-layer`

> **Stage:** `deployment-execution` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Date:** 2026-10-03 · **Release commit:** `aa0b1e4`
> · **Companion to:** `deployment-log.md`, `smoke-test-results.md`,
> `health-check-report.md`
> · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/deployment-execution`
>
> **Upstream inputs consulted:** `operation/deployment-pipeline/cd-config.md` ·
> `operation/deployment-pipeline/deployment-strategy.md` ·
> `operation/deployment-pipeline/rollback-runbook.md` ·
> `operation/environment-provisioning/environment-inventory.md` ·
> `operation/environment-provisioning/validation-report.md` ·
> `construction/build-and-test/test-results.md` · `memory/team.md` ·
> `memory/project.md`.

---

## How this file is written

The stage's Step 2 asks four questions. **Most of the questions a deployment-execution
stage normally asks were already answered before this stage started** — by an affirmed
practice in `memory/team.md`, by a recorded upstream artifact, or by a measurement an
upstream stage made and recorded. Manufacturing open questions to fill a file would
misrepresent the state of the project, so this file does not do it.

Each question below carries one of two dispositions:

- **Answered from evidence** — the answer is fixed by an affirmed practice, a recorded
  artifact, or a measurement, and the **source is named**. These are not "agent
  opinion" and do not need the human's judgement.
- **Genuinely open** — the answer is not fixed by any of those, and the stage's own
  measurement produced something a human has to decide. There are **two** of these,
  and they are the only two things in this file that need the operator.

---

## 1. The four Step-2 questions

### Q1 — Are all pre-deployment checks passing? → **Answered from evidence: yes**

**Source:** this stage's own execution of `cd-config.md` R1–R7, recorded step by step
with exit statuses in `deployment-log.md` §2, plus R3/R4 against
`construction/quality-gates.md` §2.

| Check | Exit | Result |
|---|---|---|
| R2 install (venv form) | 0 | `very-cool-sentiment-analysis-0.1.0` installed editable |
| R3 gate set | 0 | **192 passed**, 0 failed, coverage 97.06 % |
| R4 lint + format | 0 / 0 | `All checks passed!` · `30 files already formatted` |
| R5 store backup | 0 | backup byte-identical to the store |
| R6 throwaway-store smoke | 0 | `{"mode":"offline",…}`, real store's mtime unchanged |
| R7 cutover | 0 | `/v1/health` 200, `/v2/analytics/summary` 200 on `127.0.0.1:8000` |

**One recorded divergence, already anticipated.** The *bare* install command
`python -m pip install -e ".[dev]"` **exits 1** here with
`error: externally-managed-environment` (PEP 668). This is not a code defect and not
a new finding: `cd-config.md` §3 R2 already carries it as a deliberate divergence
from the approved artifact, sourced to `build-instructions.md` §2.3 and
`ci-config.md` §4.1. It was re-confirmed here by running it, and the venv remedy
exits 0. The approved `verification-command.txt` step 1 does not pass on this host,
which Environment Provisioning recorded as V-02.

**Nothing needs the human's decision on this question.** The one thing that is
genuinely a human action — writing the release tag, R8 — is not a check result but a
release decision, and it is Q7 below.

### Q2 — Are database migrations required and tested? → **Answered from evidence: a migration step exists and is tested; it was NOT required here, and it was a no-op on the real store**

**Source:** `app/db.py:60,219-247,249`; `deployment-strategy.md` §3; and this
stage's own migration execution, logged in full in `health-check-report.md` §3.

**Required?** **No.** The operator's `data/sentiment.db` was sampled read-only before
anything ran: `schema_meta.version = 4`, all three named indexes present, 0 rows. There
was nothing for the `v3 → v4` step to do.

**Was it a no-op where it ran against the real store?** **Yes, and provably.** R7 booted
the real `app:app` from the repository root — the actual release, against the actual
store — and both the **sha256 and the mtime** were unchanged afterwards. An unchanged
mtime means the file was not opened for writing at all. This independently reproduces
`validation-report.md` V-15 and confirms **F-01**, which corrected `cd-config.md` §5's
over-general wording to: the startup migration writes **iff** the store is behind
`SCHEMA_VERSION`.

**Tested?** **Yes, and this is the part that mattered.** A no-op proves nothing, so the
step was executed **deliberately** on an isolated copy in a `mktemp -d` scratch tree,
against a copy seeded with **four real rows** through the app's own write path, and
driven to a genuine v3 by the `express` release's own `init_db` (`git show
beeb587:app/db.py`):

```
STEP 0  seeded v4 copy        version=4  indexes=3  rows=4  data_sha=045b2bec1c4bc28e
STEP 1  express init_db -> v3 version=3  indexes=3  rows=4  data_sha=045b2bec1c4bc28e
STEP 2  v3->v4 step           version=4  indexes=3  rows=4  data_sha=045b2bec1c4bc28e
STEP 3  re-run (idempotency)  version=4  indexes=3  rows=4  data_sha=045b2bec1c4bc28e
version 3 -> 4 advanced : True    rows preserved : True
row data byte-identical : True    idempotent     : True
```

The content digest `045b2bec1c4bc28e` is identical across every step. That is what
makes this a test rather than a tautology: a step that rewrote a row, coerced a
`confidence`, or dropped a record would have moved it.

**Nothing here needs the human's decision.** The strategy — expand-only, no contract
phase in this release — is already fixed by `deployment-strategy.md` §3, and the
constraint on the *next* scope that wants a destructive change is stated there too.

### Q3 — Are dependent services available and healthy? → **Answered from evidence: there are none, and the one external dependency is not connected but the app is healthy without it**

**Source:** `environment-inventory.md` §1.1 (M1, M2, M3, M5), §2.6, §3;
`validation-report.md` V-16; and this stage's own live `/v1/health` response.

**There is no infrastructure to be unhealthy.** Measured by Environment Provisioning
and re-confirmed here: `aws` is not on `PATH`; no `AWS_*`/`CDK_*` variable is set; no
`~/.aws`, `~/.cdk.json`, `cdk.json` or `~/.pulumi` exists; and a tree-wide find for
`*.tf`, `*.tfvars`, `cdk.json`, `*.template`, `Pulumi.yaml`, `serverless.yml`,
`*.bicep`, `Dockerfile*` and `docker-compose*` returns **zero hits**. `git remote -v`
is empty, so there is no VCS service, no registry and no CI runner either.

**The one external dependency is OpenRouter, and it is not connected:**

```
GET http://127.0.0.1:8000/v1/health  ->  200
{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
```

There is no `config.local.toml` on this machine (`validation-report.md` V-16), so
`offline` is the **measured** default, not an untaken branch. **This is a healthy
checkout, not a degraded one:** the app served its complete read surface — health,
both `/v2/analytics/*` endpoints, the page — on the dummy engine with no credential
and no network egress.

**The dependency that does matter for a release, the store, is healthy:** present,
readable, at schema version 4, all three indexes intact, and now backed up
(`data/sentiment.db.bak-aa0b1e4`, byte-identical).

**Nothing here needs the human's decision**, unless the operator wants live mode —
which is a runtime mode choice about their own credential, not a release question.

### Q4 — What is the deployment window? → **Answered from evidence: there is none, and none is invented**

**Source:** `memory/team.md` § Way of Working; `deployment-strategy.md` §6;
`cd-config.md` §6.

`memory/team.md` § Way of Working records that *"No maximum branch age has ever been
affirmed and we are not inventing one."* `cd-config.md` §6 lists "a branch-age gate,
deployment window or freeze calendar" among the things a CD configuration
deliberately does not contain, and `deployment-strategy.md` §6 records the freeze
period as **not designed**. A freeze calendar for a one-operator localhost release
would invent a constraint nobody has affirmed.

**What the recreate strategy actually costs, measured rather than estimated.** R7b ran
two full cycles:

```
cycle 1 pid=162427 health={"mode":"offline",...}   exited 143   port closed after stop
cycle 2 pid=162663 health={"mode":"offline",...}   exited 143   port closed after stop
```

The port was genuinely closed between the old and the new process, and reopened on
the new one. The outage is the interval between two hand-typed commands on a machine
with one user and no traffic — **not a window anyone has to book.**

**Nothing here needs the human's decision.**

---

## 2. Questions this stage raised while executing

### Q5 — Should the release tag be written? → **GENUINELY OPEN — a human decision, deliberately not taken**

`memory/team.md` § Way of Working makes the tag the release: *"tag that commit with
the scope name."* `cd-config.md` §3 R8 is the step that writes it, and this stage did
**not** execute R8 — the stage boundary in force was explicit that nothing be
committed, tagged, merged or pushed.

**What is now known:** the release is verified. R1–R7 all passed, the commit
`aa0b1e4` installs, passes its full 192-test gate set, boots on the enforced loopback
bind, serves both `/v2/analytics/*` endpoints over real HTTP, refuses every malformed
request correctly, and left the operator's store byte-identical. **R8 is the only
remaining step of the release**, and it is a single command:

```
git tag -a analytics-layer -m "analytics-layer scope release" aa0b1e4
```

**The two things the human is actually deciding, neither of which the stage can:**

1. **Whether this scope is released at all.** The scope has **8 commits and no tag**
   (`git describe --tags` → `express-6-gaa0b1e4`, so `aa0b1e4` is 6 commits past the
   last release). That is consistent with the one-commit-per-scope rule and with a
   scope that is not finished — but whether *this* Bolt's verified state warrants a
   release tag, or whether the tag waits for the scope's completion, is a judgement
   about the release, not about the code.
2. **What the tag is named.** `cd-config.md` writes it as `<scope-name>`, which here
   resolves to `analytics-layer`; the two existing tags are `express` and `v1-classic`,
   which are *scope* names. Confirming the name before writing it is cheap; renaming a
   published tag afterwards is not.

**One fact recorded so the decision is informed:** tagging `aa0b1e4` does **not**
capture this stage's artifacts. R3–R7 and the `operation/deployment-execution/`
files are currently **uncommitted** (`git status --short` shows them as untracked), so
a tag on `aa0b1e4` points at a commit that does not contain the deployment record. The
audit shard — the project's stated provenance record — likewise has uncommitted
modifications. `memory/team.md` § Way of Working leans on the audit log rather than on
git history precisely for this reason, but if the tag is meant to be the release
provenance, the record should be committed first. **This stage did not commit
anything**, so the ordering is the human's.

### Q6 — Should the analytics summary's series width be bounded? → **GENUINELY OPEN — a design question this stage cannot settle, raised by its own measurement**

This is the one genuine surprise the execution produced, and it is reported rather
than filed as a defect.

`GET /v2/analytics/summary?from=2000-01-01&to=2099-12-31` returns `200` **correctly**
— but the response is **7,012,992 bytes** carrying **36,525** series entries, one per
calendar day in the requested window, nearly all of them zero-filled. The default
call with no parameters is ~470 bytes. The same request over a 7-day window is small
and immediate. Recorded in `smoke-test-results.md` §4.

**Why it is not this stage's call.** The behaviour is the *documented* one:
`BR4.4` calls for a series and `app/analytics.py`'s `_zero_entry` exists to zero-fill
gaps so a chart has no holes — so the contract is being honoured. Whether a maximum
range width belongs in the `/v2` request contract is a decision for the unit that owns
the analytics surface (`u3-analytics-view`), with its own design and tests. No upstream
artifact bounds the width, and no NFR latency budget was found for this endpoint; this
stage did not re-read the NFR documents to manufacture one.

**Why it is raised anyway.** The release procedure is what an operator will follow,
and `deployment-strategy.md` §2's "no traffic to shape" is easy to read as "no cost to
be aware of". A person who types a wide `from`/`to` pair into the analytics view gets
a multi-megabyte response from a single-threaded loopback server with one SQLite
connection. That is a property of the deployed release, and an operator is better
knowing it than discovering it. **No code was changed**; this is a question, not a
finding against the release.

### Q7 — Questions this stage did *not* need to ask

Recorded so their absence is not read as an oversight.

| A question that might be expected | Why it does not apply | Source |
|---|---|---|
| *Which environment tier is this deploying to?* | There is exactly one. No tiers, no promotion matrix, no staging. | `memory/team.md` § Deployment; `deployment-strategy.md` §6 |
| *Which artifact registry receives the build?* | Nothing is published. The artifact is the git commit; there is no wheel, image or bundle. | `memory/team.md` § Deployment; `cd-config.md` §2 |
| *What is the canary metric threshold?* | There is no traffic and no monitoring to shape. The rollback trigger is *"a human noticed"*. | `deployment-strategy.md` §2, §7; `rollback-runbook.md` §5 |
| *Which feature flag gates the new endpoints?* | There is no flag mechanism in the code and nothing to gate — the `/v2` prefix is a compatibility boundary, and the schema step cannot be flagged off because it runs at startup regardless. | `deployment-strategy.md` §7 |
| *Who approves the production promotion?* | One author, no co-authors, no second human reviewer, no remote. There is no second reviewer to ask. | `memory/team.md` § Way of Working |
| *What is the rollback plan?* | Already written and **rehearsed**: RB1/RB2/RB3 in `rollback-runbook.md` §5, and re-confirmed reachable from the state left behind in `health-check-report.md` §5 — including the RB3 recovery file R5 created. | `rollback-runbook.md`; this stage's R5 and §5 measurements |
| *Does the release need a backup before it runs?* | Yes, and it ran — R5. `rollback-runbook.md` §3 records that no commit contains a copy of the store, so without R5 the loss of the file is unrecoverable. | `cd-config.md` R5; `health-check-report.md` §5 |

---

## 3. Disposition summary

| # | Question | Disposition | One-line answer |
|---|---|---|---|
| Q1 | All pre-deployment checks passing? | **Answered from evidence** | Yes — R2/R3/R4/R5/R6/R7 all exit 0; 192 tests pass; coverage 97.06 %. The bare `pip install` fails under PEP 668, already recorded in `cd-config.md` R2. |
| Q2 | Migrations required and tested? | **Answered from evidence** | A `v3 → v4` step exists and was **tested** (real `3 → 4` transition on a seeded isolated copy, 4 rows and a content digest preserved, idempotent). It was **not required** here and was a **verified no-op** on the real store (sha256 and mtime unchanged). |
| Q3 | Dependent services available and healthy? | **Answered from evidence** | There are none — no AWS, no IaC, no remote. OpenRouter is **not connected** (`mode: offline`) and the app is healthy without it. The store is healthy and now backed up. |
| Q4 | Deployment window? | **Answered from evidence** | None exists and none is invented; the recreate outage is the interval between two hand-typed commands, measured as a clean stop-then-start. |
| **Q5** | **Should the release tag be written?** | **GENUINELY OPEN — human** | R8 is the only remaining step and the commit is verified. Two human choices: whether this Bolt's state warrants a release tag now, and the tag's name. Note the deployment record is still uncommitted. |
| **Q6** | **Should the summary series width be bounded?** | **GENUINELY OPEN — design, belongs to `u3-analytics-view`** | A 100-year range returns 7 MB / 36,525 zero-filled entries against a ~470-byte default. The behaviour is the documented one, so this is a question about the contract, not a defect. |

**Two open questions. Four answered from evidence with a named source.** No question in
this file was invented to fill the file, and none of the four Step-2 questions required
the human to make a judgement call — which is the expected shape for a release this
small, not a sign that the questions went unasked.
