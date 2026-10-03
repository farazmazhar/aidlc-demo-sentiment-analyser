# Incident Response Plan — intent `261001-analytics-layer`

> **Stage:** `incident-response` (operation) · lead `aidlc-operations-agent`
> · **Date:** 2026-10-03 · **Release under observation:** commit `aa0b1e4`
> · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/incident-response`
> · **Companion to:** `runbooks.md` (the failure modes), `escalation-matrix.md`
> (severity and the escalation path), `incident-response-questions.md`.
>
> **Upstream inputs consumed by this stage:**
> `operation/observability-setup/alarms.md` (`alarms`),
> `operation/observability-setup/dashboards.md` (`dashboards`),
> `operation/observability-setup/log-queries.md`,
> `operation/observability-setup/anomaly-config.md`, `slo-config.md`;
> `construction/u1-analytics-slice/nfr-design/reliability-design.md`
> (`reliability-design`) and `security-design.md` (`security-design`);
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`); `operation/deployment-pipeline/rollback-runbook.md`;
> `operation/deployment-execution/health-check-report.md`;
> `memory/team.md` § Deployment, § Code Style; `memory/project.md`
> `## Forbidden` (`C-5`), `## Mandated` (`C-6`, `C-10`);
> `memory/phases/operation.md` § Incident Response, § Observability.
>
> **The declared outputs of this stage assume an on-call rotation, an escalation
> matrix with named humans, SSM Automation runbooks, AWS Incident Manager, AWS
> Backup and disaster-recovery procedures. None of that exists here, and this
> plan does not pretend otherwise.** §2 states each absence and the rule that
> rules it out; §3 states what replaces each role, which in two cases is
> *nothing*.

---

## 1. The posture this plan describes, in one paragraph

This is one process, on one machine, over one gitignored SQLite file, used by
one person who is also its developer, deployer and only possible responder.
`memory/team.md` § Deployment: *"a localhost checkout is the entire
deployment."* Nothing monitors it, nothing pages, and nothing records what
happened after the terminal closes. **An incident here begins when one person
notices something and decides it is an incident** — that is the only detection
path that exists, and `alarms.md` §1 is the artifact that says so with its four
missing ingredients named. Everything below is built around that sentence.

---

## 2. Not provisioned, element by element

Each row is a deliberate absence with the rule that rules it out, so an absent
capability is not read as an oversight. This is the stage's Step-3 output list
answered against reality rather than against a template.

| Element the stage declares | Status | The rule that rules it out |
|---|---|---|
| **On-call rotation** | **Not provisioned** | There is no second person to rotate to. `memory/team.md` § Deployment fixes one operator; `C-5`/`C-6` forbid the infrastructure a rotation would need. Measured: no paging service, no notification channel of any kind (`alarms.md` §1). **A rotation of one is not a rotation.** |
| **Escalation to a named human** | **Not provisioned** | Same rule, plus: there is no second responder, no incident manager, no engineering manager, and no stakeholder to escalate to. The phase rule at `memory/phases/operation.md` § Incident Response asks runbooks to carry "escalation paths and contact information"; the honest fulfilment is §3.1, which records the path's **terminal state as the operator**, not a name that does not exist. |
| **SSM Automation runbooks** | **Not provisioned** | There is no Systems Manager, because there is no AWS account, no `aws` CLI, no `~/.aws`, no `AWS_*`/`CDK_*` variable and no IaC file of any kind — measured in `environment-provisioning` and recorded in `infrastructure-specification.md` §5. An SSM document is a document inside a service that does not exist; writing one would be a runbook for a system with no Systems Manager. **`runbooks.md` holds the procedures as shell.** |
| **AWS Incident Manager** | **Not provisioned** | Same AWS absence. Its function is incident *tracking* — a timeline, participants, a status, a postmortem — across responders. With one responder there is nothing to coordinate and no clock but the terminal's. §5 gives the substitute: one file, in this record, per incident. |
| **AWS Backup** | **Not provisioned** | No AWS account, and `C-5` forbids a cloud component outright. Measured this stage: **zero** backup tools in the repository — no `scripts/`, no `VACUUM INTO`, no `iterdump`, no `sqlite3.Connection.backup`, no `shutil.copy2` anywhere in `app/`, `tests/` or the docs. **The only copy mechanism that exists is a manual `cp`** (release step R5), and `runbooks.md` §9 measures exactly what that is worth. |
| **Disaster-recovery procedure** | **Partially applicable, and it is RB3** | DR means surviving the loss of a site or a system. There is one machine, one file and no replica, so the only DR event in scope is *the store is gone*, and `rollback-runbook.md` §4 already records it as having **no procedure**. This stage re-measured the whole picture and restated it in `runbooks.md` §9. Nothing was invented to fill the gap. |
| **PagerDuty / any incident-management SaaS** | **Not provisioned** | Same AWS/hosted-dependency rule as `C-5`. There is also nothing to page about: no metric is emitted, so a threshold has no instrument behind it. `rollback-runbook.md` §5 names this failure mode in the project's own words — *"An unrun gate is not a gate."* |
| **Status page / external communication** | **Not applicable, not merely unprovisioned** | There are **no users but the operator**, so there is no audience for a status update and nothing customer-visible to communicate. §3.2 states this rather than producing a template that would never be sent. |
| **Synthetic monitoring / heartbeat** | **Not provisioned** | A canary needs somewhere to run from and something to alert. `C-6` caps runtime dependencies at exactly two (`fastapi`, `uvicorn`), so no exporter or agent may be declared. The substitute is the three-command check in `runbooks.md` §13, run by a person. |
| **Error-budget-driven release policy** | **Partially applicable** | `slo-config.md` §4 is honest that this system has an error budget **on the way in and none on the way out**: the six SLIs gate a release verification run, and nothing computes them afterwards. So the budget can *block* a release and cannot *detect* a regression afterwards. |

---

## 3. What replaces each role the standard playbook assigns

This is the section the standard template would fill with names.

### 3.1 What replaces the incident commander: **nothing, and that is the answer**

An incident commander exists to coordinate people: delegate investigation,
mitigation, communication and documentation, and decide when to escalate, when
to roll back and when to declare resolution. **With one responder there is no
coordination to perform**, and the decision-maker and the doer are the same
person, so there is nothing to decide *between* roles.

The honest substitutes, which are smaller and worth more than a title:

- **Coordination** → the runbook. `runbooks.md` §13 fixes the check order so the
  operator does not have to decide where to look first; §3–§12 fix what to do
  next so the decision is pre-made.
- **Delegation** → nothing to delegate to. This is the real cost of one
  operator: a diagnosis that needs two hands cannot be parallelised.
- **The "when to roll back" decision** → the classification in
  `escalation-matrix.md` §3, written in advance so it is not made under
  pressure at 1am.
- **Escalation** → §3.1's answer again. There is no higher.

### 3.2 What replaces the status update: **nothing, because there is no stakeholder**

The standard cadence — status every 15–30 minutes to a channel, impact, next
step, ETA — exists to keep other people oriented so they can make decisions or
do work. **There is nobody to orient.** The one human in the loop is the one
doing the work, and the record that would carry the update does not exist
either: no log retention, no aggregation, no shipping
(`log-queries.md` §4.1), so a session's log lives or dies with its terminal.

What replaces it is **§5's incident record**, written once at the end rather
than streamed during: the timeline that a channel would have carried, in a file
that survives the terminal. That is a strictly better artefact for a system with
no audience — it is just later, and the lateness is the honest cost.

### 3.3 What replaces the post-incident review meeting: the blameless structure, kept, without the meeting

`memory/phases/operation.md` § Incident Response requires a post-incident review
for any P1/P2 incident. **The requirement is honoured; the meeting is not
possible.** A one-person review degenerates into the author grading their own
work, which is why §5's template is written as *evidence to fill in*, with the
blameless questions (`what` and `how`, never `who`) preserved from
`incident-response-guide.md` §"Blameless Principles":

1. **Timeline** — detection to recovery, to the minute. This is the part a
   channel would have streamed.
2. **Impact** — measured in requests, rows and seconds, not in users. With one
   user, "users affected" is either 1 or 0, so the meaningful units are
   different and are named here: **rows at risk** (the store), **requests that
   failed**, and **wall-clock time to recovery**.
3. **Root cause** — the technical cause, named to a line in the source where
   one exists (`app/routes.py:364`, `app/db.py:241`, `app/main.py:132`).
4. **Contributing factors** — observability gaps that made this harder than it
   needed to be. §4 collects them, and they are the most valuable output.
5. **What went well** — which check found it, and how fast.
6. **What could be improved** — a change to a *check*, a *runbook* or a
   *threshold*, never a change to a person, because there is only one.
7. **Action items** — specific, and each one either **done now** or written to
   `operation/incident-response/memory.md`'s open questions. Nothing waits for a
   ticket system that does not exist.

---

## 4. The five steps

The stages below are the process. They are short because the system is small,
and each one is anchored to something measured rather than to a template.

### Step 1 — Declare and classify

**Trigger: you noticed something.** There is no other trigger.

1. **Decide whether it is an incident at all.** In this system the test is
   narrow: does the app refuse to start, is it reachable off loopback, does the
   read surface fail, is the store damaged or gone, or has an answer become
   wrong? If none of those, it is a `422` (IR-2/IR-3) or a slow wide query
   (IR-7) — both are the system working correctly, and both are recorded as
   SEV4/SEV3 rather than escalated.
2. **Classify** with `escalation-matrix.md` §2, which is written against this
   project's *measured* failure modes rather than against generic ones.
3. **Take the first copy of the store, if the store is in question at all:**
   ```bash
   cp -p data/sentiment.db "data/sentiment.db.$(date +%Y%m%d-%H%M%S)"
   ```
   Measured in `runbooks.md` §9: this `cp` is the entire difference between a
   recoverable incident and an unrecoverable one, and it costs under a second.
   **Do it before diagnosis, not after** — diagnosis is the step most likely to
   involve running something.
4. **Write one line into the incident record** (its path, §5.1) with the
   timestamp and the severity. That line is the timeline's first entry, and
   writing it at the start rather than the end is what makes the timeline
   honest.

### Step 2 — Diagnose

Run `runbooks.md` §13 in order. Four checks, each under a second:

```bash
curl -sS -o /dev/null -w 'health HTTP=%{http_code}\n' http://127.0.0.1:8000/v1/health
ss -ltnp | grep ':8000'
grep -n 'analytics .* read failed' app.log ; grep -cE '" 5[0-9]{2}' access.log
sqlite3 'file:data/sentiment.db?mode=ro' \
  "SELECT 'version='||value FROM schema_meta WHERE key='version';
   SELECT 'rows='||count(*) FROM analyses;"
```

**Three diagnostic facts that are measured, not assumed, and each one saves time
at 1am:**

- **A green `/v1/health` does not mean the read surface works.** Measured during
  a live storage failure: health returned `200` in **1.4 ms** while every
  analytics read returned `500`. The health endpoint does not touch the store.
- **A failed startup produces no application record.** Measured: **0** `app.*`
  records during a failing migration — the traceback is `uvicorn.error`. So the
  socket check is not optional, and grepping the application loggers alone will
  find nothing.
- **A `422` produces no application record either.** Measured: six `422`s, zero
  records. The access line and the URL are the whole diagnosis.

If the checks do not name a failure mode, the honest next step is a **fresh
restart on a copied store** (`runbooks.md` §7), which costs 0.45–0.52 s and
rules out every process-level cause at once.

### Step 3 — Mitigate

**The mitigation ladder, cheapest first.** Mitigate before you fix: the goal is
to stop the bleeding, not to leave the system tidy.

| Order | Action | Measured cost | Applies to |
|---|---|---|---|
| 1 | **Narrow the range** | instant | IR-7 |
| 2 | **Stop the other process holding the store** | instant | IR-1 — measured: the failure is **transient**; a retry succeeded 2.63 s later while the holder was still exiting, then instantly |
| 3 | **Retry the request** | up to 5 s | IR-1 — the driver default `busy_timeout` is 5.0 s, so a blocked read costs 5 s and then succeeds or fails |
| 4 | **Restart the process** | **0.45–0.52 s** | IR-4, IR-6 — measured, three runs |
| 5 | **Restore the copy** | under a second | IR-8 — `mv` and start; migrates forward idempotently |
| 6 | **Roll back the commit** | 1 restart | RB2, §6.1 of `runbooks.md` |

**Do not restart for IR-1.** Measured: waiting fixes it and a restart does not.
**Do not delete the store for IR-4.** Measured: the store is already
byte-identical, so a deletion converts a no-data-loss failure into total loss.

### Step 4 — Recover

1. **Confirm the symptom is gone with the same command that found it.** Not with
   a different check, and not by assuming.
2. **Confirm the store is still the store:**
   ```bash
   sha256sum data/sentiment.db; stat -c '%y' data/sentiment.db
   ```
   An unchanged **mtime** is the strong form: it means the file was never opened
   for writing. This is the same instrument `dashboards.md` §5 and
   `alarms.md` §2.6 use for the read-only guarantee, and it is the cheapest
   possible confirmation that a read-only incident stayed read-only.
3. **Confirm the exposure is still only loopback** — `ss -ltnp | grep ':8000'`.
   After any restart, because the bind enforcement is bypassable by the CLI
   (`runbooks.md` §6).
4. **Only then** return to normal work, and take a fresh copy (§5.3).

### Step 5 — Record

Fill in the incident record. §5 gives the template; §3.3 gives the questions.
This step is not optional, and it is the only part of the process whose absence
is invisible at the time and expensive later.

**Minimum bar, and it is small: one file, six fields, written the same sitting.**

---

## 5. The incident record

### 5.1 Where it goes

One Markdown file per incident in
`aidlc/spaces/default/intents/261001-analytics-layer/operation/incident-response/incidents/`,
named `YYYYMMDD-HHMM-<one-word-summary>.md`, created on **declaration**. It is
committed with the rest of the `aidlc/` tree, which means it survives the
terminal — the single thing nothing else here does, since there is no log
retention at all (`log-queries.md` §4.1).

### 5.2 The template

```markdown
# Incident <n> — <one line>

- **Declared:** <ISO timestamp> · **Resolved:** <ISO timestamp>
- **Duration:** <minutes> — notice → recovery, measured
- **Severity:** <SEV1..SEV4> per escalation-matrix.md §2
- **Failure mode:** IR-<n> (runbooks.md §2)
- **Detected by:** <the exact check that found it — a person, a command, a
  keystroke; there was no alarm>

## Timeline
| when | what | evidence |
|---|---|---|
| | | the log line, the status, the hash — copied, not remembered |

## Impact
- **Requests that failed:** <count, from the access log>
- **Rows at risk:** <count, from the read-only census>
- **Rows actually lost:** <count — this is the number that matters>
- **Data still unbacked-up after this incident:** <rows written since the last copy>

## Cause
<the technical cause, named to a source line>

## What made this harder than it needed to be
<an observability gap, with its measured size: "0 application records", "no
duration field in the access line", "health stayed green">

## What to change
| change | where | done? |
|---|---|---|
```

### 5.3 The one action every record must end with

```bash
cp -p data/sentiment.db "data/sentiment.db.$(date +%Y%m%d-%H%M%S)"
sha256sum data/sentiment.db data/sentiment.db.* | sort
```

Take it **after** the incident, so the copy includes whatever the incident
touched, and **verify it**, because an unverified copy is a belief
(`runbooks.md` §9). Then update the copy inventory in that same record — this
is the only place the project's real recovery position is written down.

---

## 6. Detection: the honest summary of what would have told you

`alarms.md` §3 already records every signal as **manual**. Stated as a list of
detection paths, ordered by how quickly each one fires in reality:

| Detection path | Fires when | Measured gap |
|---|---|---|
| **A person noticing** | whenever they look | **This is the only automatic-ish path that exists.** `alarms.md` §1. |
| A `500` in the access log | someone reads the terminal | the record is on **stdout**; if it went to `app.log` it is not in `app.log` |
| A storage-failure record | same | on **stderr**; `log-queries.md` §1 |
| `/v1/health` returning non-200 | someone curls it | **does not detect IR-1 at all** — measured 200 in 1.4 ms during a storage failure |
| A `422` | someone reads the access log | **no application record exists** — measured 0 |
| A startup failure | someone looks for a listener | **no application record** — measured 0 `app.*` records |
| A latency regression | nothing | the access line carries **no duration field**; every latency figure in this project is stopwatch-measured |
| A wide range | nothing | visible only in the query string; nothing evaluates it |
| A bind escape | someone runs `ss` | **point-in-time only**; the check has no memory of how the process was started |

**One change would improve every row above, and it costs nothing:**
`… > access.log 2> app.log` at startup. Without it, a failure on one stream is
invisible to a grep on the other, and `observability-setup-questions.md`
**OQ-5** records this as the one observability answer that is cheap but not yet
taken.

---

## 7. Communication during an incident

**There is no communication procedure, because there is nobody to communicate
to.** No stakeholder, no team channel, no status page, no customer. The standard
"never speculate about root cause in external communications" rule has no
external surface to apply to, and inventing one would be padding.

What replaces it:

- **The incident record (§5.2) is the only communication artefact**, and its
  audience is a future version of the same person at 1am who has no memory of
  tonight.
- **Write the cause after you have measured it, never before.** In a system with
  one operator there is no second opinion to catch a guess, and an unmeasured
  cause written into a durable file is worse than no file: it will be believed
  later.
- **Do not put a credential in the record.** `memory/project.md` `## Forbidden`
  forbids a real key in any artifact under `aidlc/`. Quote the *pattern*, never
  the value (`sk-or-v1…`, never the suffix).

---

## 8. The blameless rule, and why it is easier here than it looks

`incident-response-guide.md` §"Blameless Principles" asks *what* and *how*, not
*who*. With one responder that discipline is unusually cheap: **there is no
second person to protect, and no one to blame but the reader** — who is the
author, on a bad day, with no memory.

The concrete form: "a `422` emits no application record" is a **property of
`app/routes.py`**, and it belongs in the *What made this harder* section with a
measurement and a named fix. It does not belong in a sentence about somebody's
judgement at 3am. `runbooks.md` §4 is written the same way, and that is why it
can be read without defensiveness by the person who needs it most.

---

## 9. What this plan deliberately does not do

| Not done | Why |
|---|---|
| A rotation, a primary/secondary pair, a handoff checklist | one person. `incident-response-guide.md` §On-Call assumes a team; a rotation of one is not a rotation. |
| Named responders, phone numbers, contact details | there is nobody to name. `memory/team.md` records no team, and inventing a name would put a fiction in an artifact whose whole value is that it is checkable. |
| An SSM Automation document per failure mode | no Systems Manager, no AWS account (`infrastructure-specification.md` §5). The procedures are shell in `runbooks.md`. |
| A status-page template, a Slack channel convention | no audience, no channel. |
| Quarterly game days, DR drills | `incident-response-guide.md` §RTO says to test RTO/RPO quarterly. **With one operator and one machine, the test *is* the rehearsal**: `rollback-runbook.md` §5 rehearsed RB1/RB2/RB3 against real SQLite files and real `uvicorn`, and this stage re-rehearsed RB1 and RB2 (`runbooks.md` §5, §6.1). That is the drill; scheduling it quarterly would be theatre. |
| A latency alarm, an error-rate alarm, a burn-rate alert | nothing computes a metric (`C-6`), there is no traffic history, and `alarms.md` §4 lists each absent threshold with its reason. |
| A post-incident review *meeting* | one person. §3.3 keeps the structure and drops the meeting. |

---

## 10. The four observability gaps, collected

They are listed here because they are, collectively, the largest incident-response
risk in this project after the absence of backups — each one is a measured hole
in what a responder can see, and each is a code change that is not this stage's
to make.

| # | Gap | Measured | Where it is recorded |
|---|---|---|---|
| **OG-1** | A `422` emits **no** application record | 6 × `422`, **0** records | `log-queries.md` §4(a); `observability-setup-questions.md` **OQ-2** |
| **OG-2** | A failed startup emits **no** `app.*` record — only `uvicorn.error` | **0** `app.*` records, exit 3, port never opened | `log-queries.md` §2.3, §4(d) |
| **OG-3** | The access line carries **no duration field** | `… 200 OK`, no ms — every latency figure in the project is stopwatch-measured | `dashboards.md` §5; `slo-config.md` §1 |
| **OG-4** | `/v1/health` does not touch the store | `200` in **1.4 ms** while every analytics read was `500` | measured this stage; `runbooks.md` §3 |

And one that is not an observability gap but behaves like one:

| # | Condition | Measured | Effect |
|---|---|---|---|
| **OG-5** | The `uvicorn --host` flag bypasses `resolve_bind_host` | `127.0.0.2` refused by the resolver, **bound and served `200`** by the CLI, **no refusal logged** | the bind is a property of *how the process was started*, and nothing records how it was started — `health-check-report.md` §2.3; `observability-setup-questions.md` **OQ-3** |

---

## 11. Standing constraint honoured by this stage

**No application source, test, configuration or data-store file was modified.**
Every store inspection used `file:…?mode=ro`; every process booted ran with its
CWD inside `/tmp/opencode/ir/`. `git diff --stat app tests pyproject.toml
config.example.toml README.md` is empty. `data/sentiment.db` is byte-identical
before and after, **down to the mtime** (`2026-10-03 03:33:42.920985500 +0500`,
sha256 `c8be1361…`, mode `644`), and `data/sentiment.db.bak-aa0b1e4` is
untouched. Full evidence in `runbooks.md` §14.
