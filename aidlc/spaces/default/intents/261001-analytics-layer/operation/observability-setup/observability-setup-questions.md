# Observability Setup — Questions — intent `261001-analytics-layer`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent`
> · **Date:** 2026-10-03 · **Release under observation:** commit `aa0b1e4`
> · **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/observability-setup`
>
> **Upstream inputs consumed by this stage:** `nfr-design/performance-design.md`
> (`performance-design`), `nfr-design/security-design.md` (`security-design`),
> `nfr-design/reliability-design.md` (`reliability-design`),
> `nfr-design/observability-design.md` and
> `infrastructure-design/monitoring-design.md` (`monitoring-design`),
> `infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`); `memory/team.md` § Deployment, § Testing
> Posture, § Way of Working; `memory/project.md` `## Forbidden` (`C-5`), `##
> Mandated` (`C-6`, `C-1`, `C-10`).
>
> **This file contains no manufactured open questions.** The stage's Step 2 asks for
> clarifying questions, and this project's principles say *"questions before
> assumptions"*. Where the answer is already fixed by an affirmed practice, a
> recorded measurement, or a constraint, inventing a question would be asking the
> human to decide something the record has already decided. Those are recorded in §2
> as **answered from evidence**, with the source. §3 holds only what the evidence
> genuinely does not settle.

---

## 1. The organising rule, stated once

| § | Contains | Standard applied |
|---|---|---|
| **§2** | Questions the record already answers | **Answered from evidence**, with the source named per row. |
| **§3** | Questions the record genuinely does not settle | Left open, with what is already known and what a decision would change. |
| **§4** | Questions deliberately **not** asked | Named, with the reason — so their absence is not read as an oversight. |

## 2. Questions answered from evidence

### 2.1 The stage's own Step 2 questions

**Q — "What are the golden signals to track (latency, traffic, errors, saturation)?"**

**Answered from evidence: all four are visible; none from a metric.** Latency is
visible only as a stopwatch measurement because the access line carries **no duration
field** in this configuration (measured: `… 200 OK`). Traffic is the access log.
Errors are the `app.routes` module logger plus the access-log status. Saturation is
the store census plus the requested range width. Sources: measured in this stage;
`dashboards.md` §2 and §5; `observability-design.md` §1; `monitoring-design.md` §4
("Metrics & KPIs: **empty**", "Alerts: **empty**").

**Q — "What SLOs/SLIs are defined?"**

**Answered from evidence: six SLIs, expressed as release gates over a verification
window, not as 30-day service targets.** `slo-config.md` §2–§3. The framing is forced
by `team.md` § Deployment ("a localhost checkout is the entire deployment") and
`performance-design.md` §4 ("there is **no RPS target**; the store is a single-user
local file"). The extension over `observability-design.md` §1 ("SLO: none stated") is
declared, not smuggled in — `slo-config.md` §6.

**Q — "What dashboard layouts does the team need?"**

**Answered from evidence: no dashboard is possible; a documented query set is what
exists.** `C-5` forbids a cloud component and `C-6` forbids a third runtime
dependency; measured this stage: no `aws` CLI, no `~/.aws`, no `CDK_*`/`AWS_*`
variable, no IaC file. Four panels specified as commands with measured output —
`dashboards.md` §2. `monitoring-design.md` §1 ("Dashboards: **No**") already ruled
this out; this stage supplies the substitute rather than the prohibition.

**Q — "What log retention and aggregation rules apply?"**

**Answered from evidence: none, by decision, and none is invented here.** There is no
log sink, no formatter and no retention tier; a session's log exists only if the
operator redirects one. Sources: `monitoring-design.md` §1 ("Log aggregation: **none**
— no sink, no formatter, no retention tier"), `BR2.15` (no new configuration value),
and the no-junk-drawer convention (no logging helper module). The two log streams and
the five application call sites are enumerated in `log-queries.md` §1–§2.

**Q — "What distributed tracing instrumentation is needed?"**

**Answered from evidence: none — there is no boundary to span.** Measured: the read
path imports nothing network-capable (`app/analytics.py`'s complete import list is
`re`, `sqlite3`, `collections`, `dataclasses`, `datetime`, `decimal` + three in-repo
modules); only `openrouter_client.py` and `session_auth.py` import a network client
and neither is reachable from a read. Sources: `observability-design.md` §1/§4/§5,
`reliability-design.md` §5, `security-design.md` §2, and the measurement in
`tracing-config.md` §1. What substitutes is in `tracing-config.md` §2.

### 2.2 Further questions this stage had to resolve, answered from evidence

**Q — What latency threshold should be used, and on what basis?**

**Answered from evidence: a measured distribution, not a remembered number.** 25
consecutive runs per endpoint over the pinned 10 000-row / 365-day fixture with no
coverage instrumentation: `summary` min 13.57 · p50 15.42 · mean 15.71 · **max 20.53
ms**; `terms` min 27.49 · p50 30.08 · mean 31.05 · **max 59.28 ms**. Thresholds set
at ≈5× and ≈2× those maxima (100 ms / 120 ms), inside the **200 ms** budget
(`tests/test_analytics_read.py:34`, `BUDGET_MS = 200`). The recorded single-run figure
(`summary 15.24 / terms 25.04 ms`, `test-results.md` §3.1) is quoted alongside — and
noted as *below* this run's p50 for `terms`, which is exactly why the distribution is
published rather than the single number. Sources: `alarms.md` §2.3;
`slo-config.md` §2 SLI-1.

**Q — Should an error-rate threshold be set?**

**Answered from evidence: no — a rate is not computable.** The largest real sample is
27 requests; over 13 a percentage quantises to 7.7 % steps. `performance-design.md` §4
records that no RPS target exists. `alarms.md` §4 lists this and four other absent
thresholds with reasons. **The count is used instead of the rate**, and
`slo-config.md` §4 states the resulting error budget honestly.

**Q — Does `app/analytics.py` emit the analytics failure record?**

**Answered from evidence: no — the read module has no logger at all.**
`grep -c logging app/analytics.py` → **0**. The record is emitted one layer out, in
`app/routes.py:364` and `:398`, by the handler that catches `sqlite3.Error`.
`observability-design.md` §2's pseudocode places the `except StorageError` in the
read module; the shipped code places it in the route. `NFR8.1` is satisfied either way;
the location differs from what the design implies. Source: measured and
`log-queries.md` §1.2(a).

**Q — Does the storage-failure record carry a stack trace?**

**Answered from evidence: no.** The shipped calls are `logger.error(...)`, not
`logger.exception(...)`, so the record is a single line holding `str(exc)` only.
`observability-design.md` §2 and `monitoring-design.md` §3.1 both describe an
"`exception(...)` record carrying the code **and stack**". The code — which is what
makes `NFR8.2` hold — is present; the stack is not. Source: `app/routes.py:364,398`
and the captured line in `log-queries.md` §2.1.

**Q — Does a `422` produce an application log record?**

**Answered from evidence: no.** Measured on a live 13-request capture: **4 requests
returned `422`; `grep -c VALIDATION_FAILED app.log` → 0.** Only the storage branch
logs. `NFR8.2` names both `VALIDATION_FAILED` and `STORAGE_FAILURE`; the stored verdict
(`test-results.md` §5) rests on a test that exercises the storage path only. Recorded
as a gap in `log-queries.md` §4(a), not resolved here — resolving it is a code change
plus a requirement decision, and both are §3 questions.

**Q — Is the logging test real, or would it pass either way?**

**Answered from evidence: it has teeth.** Verified on a scratch **copy** (the
repository was not modified): deleting the two `logger.error` calls and re-running
`test_a_storage_failure_is_logged_through_the_module_logger_with_its_code` fails with
`AssertionError: the storage failure was swallowed rather than logged`. Notably the
response assertions *passed* in that run — the `500 STORAGE_FAILURE` was still
returned — so **the log call is the only thing separating "logged" from
"swallowed"**. Source: measured this stage; `log-queries.md` §4.1.

**Q — Is the loopback bind actually enforced?**

**Answered from evidence: enforced where it is reached, and bypassable on the CLI.**
`resolve_bind_host` and `create_app` refuse four non-loopback hosts, including the
near-miss `127.0.0.2`. But measured this stage: `uvicorn app:app --host 127.0.0.2`
**bound and served `200` with no refusal logged**, and was simultaneously unreachable
on `127.0.0.1`. This upgrades `health-check-report.md` §2.3 from a code-reading
observation to a measurement. Sources: `security-design.md` §4, `team.md` §Deployment
("ALWAYS enforce that loopback bind at startup"), `alarms.md` §3.1.

**Q — Where does the startup-failure signal come from?**

**Answered from evidence: `uvicorn.error`, not an application logger.** With a
named-logger configuration, a failing migration produced **0** `app.*` records and two
`uvicorn.error` records (`Traceback…` and `Application startup failed. Exiting.`),
exit status **3**, port never opened. `init_db` re-raises and nothing in `app/` catches
it to log it in its own voice. Sources: measured; `reliability-design.md` §2.1/§4,
`rollback-runbook.md` RB1, `log-queries.md` §2.3.

**Q — Does the startup migration write the store?**

**Answered from evidence: not on a v4 store, and the mechanism is now visible at the
statement level.** On a v4 store `init_db` runs **11** statements (including
`CREATE INDEX IF NOT EXISTS` no-ops and an `ON CONFLICT … DO UPDATE` upsert of the
version it already holds) and leaves the file byte-identical with **mtime unchanged**
— no page is dirtied, so no journal is written. Confirms finding **F-01**
(`validation-report.md` §4) with a mechanism rather than only a file-level result. On
the operator's own store the version is `4` and all three indexes are present
(`validation-report.md` V-11; `health-check-report.md` §3.2). Sources: measured;
`alarms.md` §2.6, `anomaly-config.md` §2-A9.

**Q — What can make this app slow?**

**Answered from evidence: the requested range width, not the data volume.** Measured
over real HTTP against a store holding **one** row: 1 yr → 70 640 B / 13 ms · 21 yr →
2 803 760 B / 115 ms · 100 yr → **7 012 976 B / 235 ms**, at 36 525 entries. The last
exceeds the 200 ms budget. Independently, `sqlite3` tracing shows every read is
exactly **one `SELECT`** at all four widths — the cost is entirely in-process series
assembly and serialisation. Sources: measured; `anomaly-config.md` §2-A6/§2-A7,
`tracing-config.md` §2.2/§2.3, `alarms.md` §2.4.

## 3. What the evidence does not settle — genuinely open

Each is a real decision, not a rhetorical question. **None was taken by this stage**,
and no artifact under this record's directory depends on one being taken.

**OQ-1 — Should the summary series width be bounded?**

Measured and published: payload size is linear in the requested range, uncapped by
design (`NFR9.3` says so deliberately), and a 100-year window breaches the latency
budget with a single stored row. `smoke-test-results.md` §4 explicitly declined to
decide this, recording it as *"a design decision for the unit that owns the analytics
surface (`u3-analytics-view`), not a deployment observation this stage can settle."*
**This is still that decision, and it still belongs to `u3-analytics-view`** — capping
it changes the `/v2` contract. A cap would also directly weaken `NFR9.3`, so it is not
a change this stage may propose unilaterally. **Decide in the unit that owns the
surface.**

**OQ-2 — Should a validation failure emit an application log record?**

The requirement text (`NFR8.2`) names both codes; the implementation logs only the
storage one; the test covers only the storage one. Closing it means a code change
**and** a decision about whether a 422 is worth a line — which is a real trade (a
single operator mistyping a date would then write a line on every attempt). No
affirmed practice in `team.md` or `project.md` settles it. **This stage changed no
source**, so it cannot and did not close it.

**OQ-3 — Should the `uvicorn --host` bypass be closed, and how?**

The gap is measured (§2.2). Closing it is a code change — moving enforcement somewhere
the CLI cannot bypass — and `team.md` § Deployment's rule (*"the `HOST` constant must
be the thing the run path actually consumes"*) is satisfied for `run()` but not for the
`uvicorn app:app` invocation the same document records as documented. **A scope
decision, not a monitoring decision.** The interim operator mitigation is recorded
everywhere it matters: omit `--host`, or pass a loopback value.

**OQ-4 — Should the store's file mode be tightened from 644 to 600?**

Measured `644`; the store holds submitted text unencrypted and is world-readable on
this host (`validation-report.md` V-12). Tightening it changes a file on the
operator's machine, which is **not this stage's to do** and is arguably not this
project's to decide unilaterally. Recorded as an anomaly with its expected value
(`anomaly-config.md` §2-A12) so it is visible rather than normalised away.

**OQ-5 — Should logs be redirected to a file, and retained?**

Nothing in the project's affirmed practices fixes a log destination or retention
period, and `monitoring-design.md` §1 rules aggregation out by decision. The evidence
therefore cannot answer it — but the *answer is cheap*: `… uvicorn app:app > app.log
2> error.log`. Whether the operator wants files at all is a preference about their own
machine, not a project fact.

**OQ-6 — Is a verification-window SLO the right target, or should there be no SLO?**

`observability-design.md` §1 recorded "SLO: none stated", and this stage extended it
to a verification-window framing (`slo-config.md` §6) on the reasoning that a 30-day
rolling target is uncomputable here while a verification gate is enforceable. **That
reasoning is a judgement, and this stage flags it as one** rather than presenting an
extension as a correction.

## 4. Questions deliberately not asked

| Not asked | Why |
|---|---|
| "Which CloudWatch dashboard do you want?" | Unanswerable and unaskable: no AWS account, no CLI, no credential, no IaC — **measured this stage**. Asking would imply the choice is open. |
| "What SNS topic should alarms route to?" | There is no channel and no second recipient. `incident-response-guide.md`'s escalation matrix presupposes a team this project does not have; `alarms.md` §5 restates severity as a mapping, not a rotation. |
| "What X-Ray sampling rate do you want?" | No trace exists to sample (`tracing-config.md` §1). |
| "What is the RTO / RPO?" | `reliability-design.md` §5 records backup/PITR as **absent by decision**, and `deployment-log.md` §3 measures the actual asymmetry: RB2 (roll back code) costs one checkout; RB3 (recover the file) costs everything, and R5's byte-identical `data/sentiment.db.bak-aa0b1e4` is the only thing that changes that. |
| "Should we track business KPIs (sentiment volume, conversion)?" | `NFR9` / `performance-design.md` §4 — single-user local file, no load profile, no capacity plan. A KPI here is a row count an operator can already read with one query (`log-queries.md` §Q7). |
| "Should branch coverage be enabled to raise observability confidence?" | Off by affirmed decision (`team.md`, 2026-10-02), with its measured cost already recorded: 98 branches, 3 partial. Re-litigating an affirmed practice is not this stage's business. |
| "Do the two `Unverified` targets (`NFR4.6`, `NFR4.7`) need observability work?" | They are owned by `u3-analytics-view` and were accepted as carried-forward by the human at Build and Test (`test-results.md` §6). Nothing in this stage's remit changes that ownership. |

## 5. Summary of the stage's posture

**Answered from evidence and closed:** 6 golden-signal mappings · 6 SLIs with 6
release-gate targets · 4 dashboard panels · 0 retention rules (by decision) · 0 tracing
instruments (by measurement) · every threshold derived from a measurement taken in
this stage or a named recorded one.

**Left open for the human:** 6 questions, of which **1** changes a contract
(`OQ-1`, series width, owned by `u3-analytics-view`), **2** require a code change
(`OQ-2`, `OQ-3`), **1** touches the operator's own file permissions (`OQ-4`), **1** is
an operator preference (`OQ-5`), and **1** is a judgement this stage is flagging as
its own (`OQ-6`).

**Not provisioned, per element, with the ruling rule in each file:** CloudWatch
dashboards, CloudWatch alarms, CloudWatch Logs Insights, SLO dashboards, burn-rate
alerting, CloudWatch Synthetics canaries, X-Ray, OpenTelemetry SDK/exporter, CloudWatch
EMF, log shipping and retention. **The one-line reason, common to all ten:**
`C-5` forbids a new external service or cloud component and `C-6` caps declared
runtime dependencies at exactly `fastapi` and `uvicorn` — and there is no AWS account,
no CLI, no credential and no IaC on this machine to host them anyway.