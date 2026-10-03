# Escalation Matrix — intent `261001-analytics-layer`

> **Stage:** `incident-response` (operation) · lead `aidlc-operations-agent`
> · **Date:** 2026-10-03 · **Release under observation:** commit `aa0b1e4`
> · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/incident-response`
> · **Companion to:** `runbooks.md`, `incident-plan.md`.
>
> **Upstream inputs consumed by this stage:**
> `operation/observability-setup/alarms.md` (`alarms`) — §5 is this file's
> starting point and is extended and corrected here;
> `operation/observability-setup/dashboards.md` (`dashboards`) — Panels A–D are
> the instruments every row below depends on;
> `operation/observability-setup/anomaly-config.md` A1–A12, `slo-config.md`;
> `construction/u1-analytics-slice/nfr-design/reliability-design.md`
> (`reliability-design`) §2 and §5;
> `construction/u1-analytics-slice/nfr-design/security-design.md`
> (`security-design`) §3.4 and §4;
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md`
> (`infrastructure-specification`) §5;
> `operation/deployment-pipeline/rollback-runbook.md` (RB1/RB2/RB3);
> `memory/team.md` § Deployment; `memory/project.md` `## Forbidden` (`C-5`);
> `memory/phases/operation.md` § Incident Response;
> `.aidlc/knowledge/aidlc-operations-agent/incident-response-guide.md` §
> Severity Levels, § Escalation Matrix, § On-Call Rotation, § Incident
> Commander.
>
> **This is a severity classification, not a roster.** `alarms.md` §5 already
> says so of its own table — *"It is a **mapping**, not a rotation: there is no
> on-call to rotate, and `incident-response-guide.md`'s escalation matrix
> presupposes a team this project does not have."* This file carries that
> through to its conclusion, which is that **the escalation column has one
> value on every row.**

---

## 1. The one fact that decides this file

**There is one person, and that person is the operator, the developer, the
deployer and the only possible responder.** `memory/team.md` § Deployment: *"a
localhost checkout is the entire deployment."* Measured across the previous
stages: no pager, no SNS topic, no webhook, no chat integration, no monitoring
agent, no scheduled job (`alarms.md` §1).

So the standard matrix from `incident-response-guide.md` —

| Severity | Primary Responder | Escalation (30 min) | Escalation (1 hour) |
|---|---|---|---|
| SEV1 | On-call engineer | Engineering manager + Incident commander | VP Engineering + Stakeholder communication |
| SEV2 | On-call engineer | Team lead | Engineering manager |
| SEV3 | On-call engineer | Team lead (if unresolved in 4 hours) | — |
| SEV4 | Any team member | — | — |

— has **no counterpart on any of its four columns except the first**, and the
first column contains a role ("on-call engineer") that does not exist here. Every
other cell presupposes a person, a management layer, and an organisation. There
is no honest way to fill them, so this file does not fill them.

---

## 2. Severity classification, against this project's measured failure modes

`alarms.md` §5 defines four levels and this file **keeps them** and re-derives
the criteria from what was reproduced in `runbooks.md` §2–§12 rather than from
the generic criteria in the guide ("error rate > 10 %", "payment processing
failure"). The four-level shape transfers; the criteria do not, because there is
no error rate, no user population, and no payment path.

### SEV1 — the app does not serve, or is exposed

**Criterion:** the process does not start, **or** it answers on a non-loopback
address.

| | |
|---|---|
| **Failure modes** | **IR-4** (migration `IntegrityError`, exit 3, port never opens) · **IR-5** (non-loopback listener) · **IR-8** (store gone: the app starts and serves, but with zero history) · **IR-10** (credential in a log) |
| **Why SEV1** | Each of these either stops the app or removes the project's only security boundary. `security-design.md` §4 calls the loopback bind *"the central hardening"* and threat **T5** *"the principal risk this unit could introduce"*; `alarms.md` §2.5 rates a non-loopback listener **SEV1 equivalent** — *"an unauthenticated app holding the operator's OpenRouter key, reachable off-machine."* |
| **Detect with** | `ss -ltnp \| grep ':8000'` (IR-5, IR-8) · `grep -E 'IntegrityError\|Application startup failed'` **plus** the socket check (IR-4) · `grep -cE 'sk-or-v1\|AKIA\|password' app.log access.log` (IR-10) |
| **Response time** | **Immediately, in the same sitting.** Not a 15-minute target — there is no queue, no handoff and no second person, so "response time" is only "how long until the operator stops doing something else". |
| **Mitigation** | `runbooks.md` §5 (IR-4), §6 (IR-5), §9 (IR-8), §11 (IR-10) |
| **Recovery time (measured)** | restart **0.45–0.52 s**; store restore **under a second**; code rollback **one restart** |
| **Escalation path** | **No escalation path exists. The operator is the last resort.** |

### SEV2 — the read surface fails while the process is up

**Criterion:** a request that should have succeeded returns `5xx`, or the process
exits while serving.

| | |
|---|---|
| **Failure modes** | **IR-1** (`STORAGE_FAILURE`) · **OG-5** as it would appear if a bind escape were discovered late · a boot against a store behind `SCHEMA_VERSION` when a copy has not been taken (IR-9 at its SEV2 reading) |
| **Why SEV2** | `reliability-design.md` §2.2 makes the storage failure a *structurally distinct* class from validation and from empty success, precisely so it can be triaged without a metric. It degrades the surface the operator depends on while everything else keeps working. |
| **Detect with** | `grep -n 'analytics .* read failed' app.log` · `grep -cE '" 5[0-9]{2}' access.log` — `dashboards.md` Panel C, `alarms.md` §2.1–§2.2 |
| **Response time** | **Same sitting.** Same reason as SEV1. |
| **Mitigation** | `runbooks.md` §3. Measured: **transient** — a retry succeeded 2.63 s after a failure while the lock-holder was still exiting, and instant thereafter. **Do not restart**; a restart fixes nothing that waiting does not. |
| **Recovery time (measured)** | **≤ 5 s** — the failing request itself blocks for the driver's default 5.0 s `busy_timeout` (`app/db.py:213` sets none), then succeeds or fails; the next request is milliseconds. |
| **Escalation path** | **No escalation path exists. The operator is the last resort.** |

### SEV3 — degraded, with a workaround

**Criterion:** something is measurably wrong and the operator can work around it.

| | |
|---|---|
| **Failure modes** | **IR-7** (a wide range: ~7 MB, 36 525 entries, ~240 ms, over the 200 ms budget) · **IR-6** (the documented run command does not serve) · a stale schema version with no boot pending (IR-9) · a **seconds-long** read, which means lock contention and is IR-1 wearing a different hat |
| **Why SEV3** | There is a workaround in every case and no data is at risk. `alarms.md` §2.3 rates latency *"SEV3 equivalent — degraded, with a workaround (narrow the range)."* |
| **Detect with** | `curl -sS -o /dev/null -w '%{size_download} %{time_total}\n' '…/v2/analytics/summary?from=2000-01-01&to=2099-12-31'` · `grep -oE 'from=[0-9-]+&to=[0-9-]+' access.log` — `dashboards.md` Panel D, `alarms.md` §2.4 |
| **Response time** | **Same day**, or never — the workload is the operator's own, so they will notice or they will not. |
| **Mitigation** | `runbooks.md` §8 (narrow the range), §7 (use a command that serves) |
| **Escalation path** | **No escalation path exists. The operator is the last resort.** |

### SEV4 — the system is working correctly and said so

**Criterion:** the refusal or the anomaly is the contracted behaviour.

| | |
|---|---|
| **Failure modes** | **IR-2** (`422 VALIDATION_FAILED`) · **IR-3** (`422 INVALID_TEXT`) · **IR-11** (a refusal that looks like an empty result and is not) · store file mode `644` where the check expects `600` |
| **Why SEV4** | `reliability-design.md` §2.2: a validation failure is a *distinct, designed* outcome with nothing computed and no row written (`BR4.1`, `BR4.2`). Treating it as an incident would train the operator to ignore the log, which `alarms.md` §4 names as the failure mode of a non-discriminating alarm. |
| **Detect with** | `grep -cE '" 422' access.log` — and note the measured gap: **no application record exists** for a `422`, so this is the *only* place it is visible (`log-queries.md` §4(a)) |
| **Response time** | **Next release, or never.** |
| **Escalation path** | **None, and none is wanted.** |

### 2.1 The classification, as one table

| | **Criterion here** | **Response** | **Failure modes** | **Escalation** |
|---|---|---|---|---|
| **SEV1** | Does not start, or answers off loopback | immediate | IR-4, IR-5, IR-8, IR-10 | none — operator is the last resort |
| **SEV2** | Read surface fails, process up | same sitting | IR-1, IR-9 (pending boot) | none — operator is the last resort |
| **SEV3** | Degraded, workaround exists | same day | IR-6, IR-7, slow read | none — operator is the last resort |
| **SEV4** | Contracted refusal or minor anomaly | next release | IR-2, IR-3, IR-11, store mode | none — and none wanted |

---

## 3. The escalation path, which is a path of length one

### 3.1 Stated plainly

> **For every severity, in every failure mode, in this project:
> the responder is the operator, and the operator is the last resort.
> There is no secondary responder, no incident commander, no engineering
> manager, no vendor support, and no escalation beyond stopping work.**

This is not a gap in the table; it is the table. Four rows of SEV1–SEV4 and four
identical escalation entries is the accurate rendering of a one-person system.

### 3.2 What each absent column would have contained, and why it is empty

| Column the guide defines | What it would hold | Why it is empty — the rule that rules it out |
|---|---|---|
| **Primary responder** | On-call engineer | **No rotation exists.** `incident-response-guide.md` §On-Call requires *"at least 2 people trained for on-call at all times"* and *"no more than 1 week in 4"*. There is one person, so the rotation is a rotation of one, which is a rename, not a rotation. `alarms.md` §1 measured that no notification channel exists to rotate into. |
| **Escalation at 30 minutes (SEV1/SEV2)** | Incident commander, engineering manager | **No incident commander role can be staffed.** Its whole function is *"coordinates response; does not debug directly"* and *"delegates workstreams"* — with one responder there is nothing to coordinate and nothing to delegate. `incident-plan.md` §3.1 states this as the answer, not as a shortfall. |
| **Escalation at 1 hour (SEV1)** | VP Engineering, stakeholder communication | **No such people and no such stakeholders.** There are no users but the operator, so there is nothing to communicate *to*; a status page for a system with one user is a document read by its own author. `incident-plan.md` §3.2. |
| **Team lead (SEV2, SEV3)** | Team lead | **No team.** `memory/team.md` records the project's practices; it records no membership, and inventing a name would put an unverifiable fiction into the one artifact class whose value is that every line is checkable. |
| **Compensation, handoff checklist, on-call stipend** | — | **Not applicable, and not listed as missing.** They presuppose a rota. `incident-plan.md` §9 records the omission and its reason rather than leaving the reader to infer an oversight. |
| **Vendor / upstream escalation** (OpenRouter outage in live mode) | — | **Cannot exist.** `C-5` forbids any new external service or cloud component, and the measured mode on this checkout is `offline` (`validation-report.md` V-16). The consequence is real and worth stating: **an upstream outage becomes this project's outage**, because the only available response is to wait. |

### 3.3 What actually happens when the operator is unavailable

This is the row the standard matrix has no cell for, and the one that matters at
1am. Measured and reasoned:

| Situation | What happens | Measured basis |
|---|---|---|
| The operator is asleep and something breaks | **It stays broken until they wake.** No page, no alert, no heartbeat. | `alarms.md` §1 — four missing ingredients: metric, rule engine, notification channel, schedule. |
| The operator is away for a week | **The app is unavailable to them for a week**, and that is the correct outcome — nothing else can use it either. | one operator, loopback bind, no users |
| The machine loses power | **The app is down until it is restarted.** There is no supervisor, no unit file, no restart policy. | `infrastructure-specification.md` §5 — no hosting, no IaC, no process supervision |
| The operator cannot reach the previous commit | **That release is gone.** There is no remote, nothing to fetch. | `rollback-runbook.md` §4 — *"A commit not in the local history cannot be recovered."* |

**The honest maximum acceptable downtime (RTO) therefore has two components**,
and only one of them is under the system's control:

| Component | Measured | Under whose control |
|---|---|---|
| **Restore the process** | **0.45–0.52 s** (three runs, `runbooks.md` §7) | the system |
| **Notice that it is broken** | **unbounded** — from "the moment it happens" to "the moment the operator next looks", which is not a number this project can set | nobody |
| **Diagnose it** | **under 10 s**, using the four checks in `runbooks.md` §13, once looking | the operator |
| **Recover the store** | **under a second**, if a copy exists | the operator — but *whether* one exists is luck (`runbooks.md` §9) |

**The RTO that matters is therefore the second row, not the first.** A system
whose restart takes half a second and whose detection time is unbounded has an
effective RTO equal to its detection time. Any number quoted for RTO that omits
that row is a fiction, and `incident-response-guide.md` §RTO's tier table
(< 5 minutes, < 30 minutes, < 4 hours) has no cell for "whenever the operator
notices" — which is the honest answer for this project.

### 3.4 The single-responder concentration risk, stated as a risk

`incident-response-guide.md` §On-Call says: *"If the team is too small, address
staffing."* **This project has addressed it by declining to need staffing**, and
the residual risk is not abstract:

| Concentration | Consequence | Measured basis |
|---|---|---|
| One person holds all knowledge | A problem only they can solve is a problem with no resolution time | one operator; the codebase is small but it is theirs |
| One person is the only responder | **Any absence is a total absence of response** | §3.3 |
| One machine holds the only durable state | Machine loss is data loss unless a copy exists | §3.3, `runbooks.md` §9 |
| The credential is the operator's own | Rotating it affects their own machine | `memory/project.md` `## Forbidden` — the key lives only in the gitignored `config.local.toml` and process memory |

**The one mitigation available without a second person is the one this file
keeps pointing at: take the copy.** It converts the largest of these four rows
from unrecoverable to recoverable, and it costs under a second
(`incident-plan.md` §5.3).

---

## 4. Not-provisioned: the escalation and alerting machinery, element by element

Recorded here rather than left implicit, each with the rule that rules it out.
The full table is `incident-plan.md` §2; this is the subset that belongs in an
escalation document.

| Element | Status | Ruling |
|---|---|---|
| PagerDuty / Opsgenie / any paging service | **Not provisioned** | `C-5` — no new external service, hosted dependency or cloud component. Measured: no notification channel of any kind (`alarms.md` §1). |
| SNS topic / alert email / chat webhook | **Not provisioned** | Same rule. There is also **nothing to send**: no metric is emitted, so a threshold has no instrument behind it — `rollback-runbook.md` §5's *"an unrun gate is not a gate."* |
| On-call rotation, primary/secondary pair, handoff checklist | **Not provisioned** | One person. `incident-response-guide.md` §On-Call requires ≥2 trained responders; there is 1. |
| Incident commander role | **Not provisioned** | Coordination and delegation have no referent with one responder. `incident-plan.md` §3.1. |
| Escalation to management or stakeholders | **Not provisioned** | No management layer, no stakeholders, no users but the operator. `incident-plan.md` §3.2. |
| Status page / external communication | **Not applicable** | No customer-visible surface: loopback-only, unauthenticated by design, no second user. |
| Burn-rate alerting on an error budget | **Not provisioned** | Needs a continuously computed SLI over a rolling window. `slo-config.md` §4: *"this system has an error budget on the way in and none on the way out."* |
| CloudWatch composite alarms / anomaly detection | **Not provisioned** | No account, no CLI, no IaC; `C-6` caps runtime dependencies at two so no exporter may be declared. `dashboards.md` §4, `anomaly-config.md` §1. |
| SSO / identity for "who is responding" | **Not applicable** | `security-design.md` §1 — unauthenticated by design, single user, loopback only. |

---

## 5. What this matrix does not establish

| Not established | Why |
|---|---|
| That any failure mode is **unlikely** | No traffic history exists: the largest real sample in the project is 27 requests (`alarms.md` §4). Frequency is unknowable, so severity is classified by **consequence**, never by expected volume. |
| That a severity will ever be *reached* | Nothing detects anything. Every row in §2 describes a state the operator must choose to look for. |
| That a rollback will be needed | `rollback-runbook.md` §4 records that RB1's trigger is *"a human noticed"* — the same posture this matrix inherits. |
| Any **cross-machine** or **multi-region** property | There is one machine. `validation-report.md` §5 records that cross-machine reproducibility is precisely the claim the lockfile (`FR7.1`) is meant to close, and that it cannot be closed today. |
| That a credential incident can be assessed | Nothing logs access from another host and there is no second host to check from (`runbooks.md` §6). The exposure window is unknowable after the fact. |

---

## 6. Standing constraint honoured by this stage

No application source, test, configuration or data-store file was modified. Every
store inspection used `file:…?mode=ro`; every process booted ran with its CWD
inside `/tmp/opencode/ir/`. `data/sentiment.db` is byte-identical before and
after, down to the mtime. Evidence in `runbooks.md` §14.
