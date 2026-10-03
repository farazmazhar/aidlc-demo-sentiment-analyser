# SLO Compliance Report — intent `261001-analytics-layer`

> **Stage:** `feedback-optimization` (operation, final stage) · lead `aidlc-operations-agent`
> support `aidlc-aws-platform-agent` · **Date:** 2026-10-03
> **Release under report on:** commit `aa0b1e4`
> **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/feedback-optimization`
>
> **Upstream inputs consumed by this stage:** `observability-setup/slo-config.md`
> (`slo-config`) · `observability-setup/dashboards.md` (`dashboards`) ·
> `observability-setup/alarms.md` (`alarms`) ·
> `observability-setup/log-queries.md` · `observability-setup/anomaly-config.md` ·
> `deployment-execution/deployment-log.md` (`deployment-log`) ·
> `deployment-execution/smoke-test-results.md` ·
> `deployment-execution/health-check-report.md` ·
> `performance-validation/load-test-plan.md` and
> `performance-validation/test-results.md` — the latter is the file this stage's
> declared upstream slug `load-test-results` resolves to, and it is cited under
> that name throughout so the reference resolves ·
> `performance-validation/nfr-validation-matrix.md` ·
> `incident-response/incident-plan.md` (`incident-plan`) ·
> `incident-response/runbooks.md` · `incident-response/escalation-matrix.md` ·
> `environment-provisioning/validation-report.md` (F-01…F-04) ·
> `construction/ci-pipeline/quality-gates.md` · `memory/team.md` § Deployment.

---

## 1. The verdict, in one line

**There is no SLO compliance figure to report, because nothing continuously
computes an SLI and no window ever elapses; what *does* exist is a six-gate
verification-window target set from `slo-config` §3, all six currently met on their
stated single-client fixture, and one of the six is broken the moment a second
client appears — a breach no percentage in this report could have expressed.**

Everything below is the support for that sentence and for its two halves.

## 2. Why a conventional SLO report cannot be written, preconditions first

A conventional SLO report has three moving parts: a continuously computed SLI, a
rolling measurement window, and an error budget to spend or overrun. Each is
absent, and each absence is measured rather than assumed.

| Part | Status here | The measurement that establishes it |
|---|---|---|
| **A continuously computed SLI** | **Absent.** No metric is ever emitted, so there is nothing to compute a proportion from. | `dashboards.md` §1: no metrics endpoint, no exporter, no collector, no time-series store. `alarms.md` §1 names the four missing ingredients — metric, rule engine, notification channel, schedule. |
| **A rolling measurement window** | **Absent.** Nothing runs between sessions; nothing accumulates. The largest real sample the project has ever produced is **27 requests** (`deployment-log`'s smoke run, `smoke-test-results.md` §2); `dashboards.md` Panel B's own capture is **13**. | `slo-config.md` §1's precondition table; `alarms.md` §4 — over 13 requests a percentage quantises to 7.7 % steps. |
| **An error budget with a window to burn it against** | **Absent as a time quantity.** `slo-config.md` §4 already reduced it to a *count per verification run*, and §4's own words are that this system "has an error budget on the way in and none on the way out". | `slo-config.md` §4; `alarms.md` §4 records the burn-rate alert as deliberately not set, with the reason. |
| **A user population whose experience is at stake** | **One**, and that person is also the developer, the deployer and the only responder. | `incident-plan.md` §1; `escalation-matrix.md` §3.1 — "the responder is the operator, and the operator is the last resort". |

`slo-config.md` §1 already made this argument and then *supplied a substitute*: a
verification-window framing whose targets are release gates rather than uptime
promises. **This report does not re-derive that; it audits it**, because the
substitute is the only SLO-shaped thing in this project and its limits have to be
stated by whoever closes the workflow.

## 3. Declared not-applicable, per element, with the rule that rules each out

Recorded per element so absence is not read as a gap in the analysis. Nothing here
is a deferral of an assigned target.

| Element of an SLO report | Verdict | The rule that rules it out | What was done instead |
|---|---|---|---|
| **30-day rolling SLO compliance** | **N/A — no window elapses** | No continuous request stream and no history accumulate between sessions; `slo-config.md` §1's precondition table. | §5 records the one measured distribution per endpoint that does exist, with its percentile. |
| **Error budget remaining, in absolute and percentage terms** | **N/A — no computed SLI to subtract from** | A budget is `1 − SLO` measured over a window; there is no measurement and no window. `slo-config.md` §4. | §5 records the budget as a **count per verification run** — six zero-tolerance counts. |
| **Burn rate (fast / medium / slow)** | **N/A, and deliberately not estimated** | The multi-window multi-burn-rate scheme needs a continuously computed SLI over a rolling window; neither exists. `alarms.md` §4 names the burn-rate alert as a threshold deliberately not set. | **Nothing.** See §6 — this is the one figure that could have been fabricated from the `load-test-results` run and must not be. |
| **Availability SLO / uptime percentage** | **N/A — no history, and one process** | `slo-config.md` §2 SLI-2 declines a percentage for exactly this reason: over 27 requests it quantises to 3.7 % steps. | The gate form: **zero unexpected 5xx in the verification window**. |
| **RTO / RPO tier compliance** | **N/A — no tier** | `incident-response-guide.md`'s tier table presupposes multi-AZ, replication and PITR; `escalation-matrix.md` §3.3 records that the measured RTO's dominant term is *notice*, which is unbounded and not a system property. | §7 records the two components separately, and says which one is the real RTO. |
| **Toil as a percentage of an operations engineer's time** | **N/A — there is no operations engineer** | The Google SRE 50 % standard measures toil against a staffed rotation. `escalation-matrix.md` §3.2: no rotation exists, "a rotation of one is not a rotation". | §7 names the toil that exists, as a count of manual steps, not as a percentage. |
| **SLO dashboard / error-budget trend chart** | **N/A — no metrics store** | `C-5` forbids a cloud component and `C-6` caps declared runtime dependencies at exactly two, so no exporter may be declared; measured absence of any AWS account to host one. `dashboards.md` §4. | `dashboards.md`'s four shell panels, each with its real captured output. |
| **Per-SLI historical trend (7/30-day burn-rate view)** | **N/A — nothing accumulates** | `log-queries.md` §4.1: no retention, no aggregation, no shipping; a session's log lives or dies with its terminal. | Nothing, and §8 records what that costs. |

**The one-line reason common to all eight:** `slo-config.md` §1 and `dashboards.md`
§1 both established it — there is no request stream, no metrics store, and one
operator.

## 4. What `slo-config` claims, read back against what `load-test-results` measured

`slo-config.md` §3 publishes six release gates. This is the audit of each against
the larger and later measurement set in `load-test-results` (scenarios `S1`, `S2`/
`C2`, `S3`, `S4`/`S5`, `S9`, `P1`, `M1`). **No row is scored from the stage that
wrote it.**

| # | SLI / gate (`slo-config` §3) | `slo-config`'s own measurement | `load-test-results`' independent measurement | Verdict on re-read |
|---|---|---|---|---|
| **SLO-1** | Every analytics read answers **< 200 ms** on the pinned fixture | 50/50 within budget; `summary` max 20.53 ms, `terms` max 59.28 ms | `S1`, 200 requests per endpoint over real HTTP: `summary` p99 **14.297** / max **27.167 ms**; `terms` p99 **35.899** / max **41.394 ms**. All 400 `200`. | **Met as written** — and this stage's own measurement lands in the same place: an unbounded `summary` over a 10 000-row fixture answered in **12.3 ms** at **123 515 B**. **But see §4.1, which is where the gate actually breaks.** |
| **SLO-2** | **Zero** unexpected `5xx` in the verification window | 0 across 13 requests | **1 920 ramp requests across two runs, all `200`** (`S2`/`C2`); **5 000** soak requests, all `200` (`S10`/`C6`); and the **6 of 6 `500`** in `S9`, every one of them deliberately provoked by a competing `BEGIN EXCLUSIVE` holder. | **Met**, on the definition `slo-config` itself uses — "unexpected". The provoked ones are the instrument, not a breach. This is the strongest result in the record: nothing failed at 64-way concurrency. |
| **SLO-3** | **192 passed, 0 failed**; coverage **≥ 80 %** | 192 / 97.06 % | `load-test-results` did not re-run the suite; `nfr-validation-matrix` carries the verdict forward unchanged at **24 `Met` / 0 `Not Met` / 2 `Unverified`**. | **Met.** The two `Unverified` targets are `NFR4.6` and `NFR4.7`, both owned by the unbuilt `u3-analytics-view` — carried, not improved. |
| **SLO-4** | Every observed failure carries a distinct machine code; emptiness is never an error | 3 distinct shapes | `S9`/`P1`/`P3`: empty success (`200`, `total: 0`), validation failure (`422 VALIDATION_FAILED`), storage failure (`500 STORAGE_FAILURE`); **no `404`** for emptiness in any run. | **Met.** `nfr-validation-matrix` §4 records the standing trap this report repeats: the partial outcome in `P3` is *not* the `NFR4.6` instrument. |
| **SLO-5** | Store `sha256` **and `mtime`** unchanged across the window | unchanged | `load-test-results` §13: the load store's `sha256`, `mtime_ns` and `size` identical after 3 000+ concurrent reads, a 100-year range and an `EXCLUSIVE` lock holder. | **Met, and the strongest form of the claim in the record.** An unchanged mtime proves the file was never opened for writing, which is strictly stronger than matching contents. |
| **SLO-6** | Exactly one listener, on `127.0.0.1` | confirmed | `alarms.md` §3.1 measured the **bypass**: `resolve_bind_host("127.0.0.2")` refuses, yet `uvicorn app:app --host 127.0.0.2` bound and served `200` with **no refusal logged**. | **Met only point-in-time**, and `slo-config` §5 limit 2 says so itself. An operator-typed flag changes the property while the check still reads green. |

### 4.1 The one gate that breaks, and what kind of failure it is

**SLO-1 does not hold under concurrency, and the record measures that three ways.**

| Evidence | Figure | Scenario |
|---|---|---|
| Throughput **peaks and then falls** | `summary` **157.8 rps at `c` = 2**, falling to **44.1 at `c` = 32** and **41.2 at `c` = 64** — 240 identical requests at every level | `S2`/`C2`, two independent runs |
| Per-request CPU **inflates superlinearly** for identical logical work | **11.75 ms → 62.21 ms** (`summary`), **22 → 305.88 ms** (`terms`); the same 240 requests cost **2.8 CPU-s at `c` = 1** and **14.9 CPU-s at `c` = 32** | `S2`/`C2`, `C4` |
| The **mixed page load breaches the budget on essentially every request** | **p95 952.7 ms**, p99 977.3 ms, max 1004.9 ms at `c` = 8 | `S3`, reproduced three times to within 1 % (14.58 / 14.58 / 14.43 rps) |
| `/terms` is the cause, and the attribution is clean | alone at `c` = 8: **8.60 rps**, p50 **921.9 ms**; `summary` alone: **46.98 rps**, p50 **169.5 ms**. `/terms` is **5.1× slower than its own single-client rate** | `C4`/`C5` |
| **It is not the harness** | the control `/v1/health`, which never touches the store, reached **2 323.53 rps at `c` = 32** with per-request CPU **flat at 0.43–0.50 ms** | `S2`/`C2` §3.1 |

**Why no SLO percentage can express this.** `slo-config` §4's honest substitution —
the budget as a *count* — works for SLO-2 through SLO-6 and fails for SLO-1,
because SLO-1's failure is not "one request over budget" but "a *shape* of the
system inverts": the same work is served faster with one client than with six
dozen. A count would read 1 920 of 1 920 as success, which is arithmetically true
and operationally the opposite of the truth.

**And the honest counterweight, which belongs in the same breath:** `NFR1.1`
states the budget over a single client and the pinned fixture, `performance-requirements.md`
declines to sub-number the concurrency constraint because it has **no inception NFR
parent**, and `FR8.4` asserts only that requests do not fail — which they do not.
**The system meets every requirement that exists.** The concurrency behaviour is
recorded as findings `F-1` and `F-2` in `load-test-results` §15 precisely because
no requirement claims it. Carried to `feedback-loop.md` as **BL-06**, ranked by
consequence rather than by effort.

## 5. The measured latency and error figures that do exist

Everything in this table comes from `load-test-results`, over real HTTP against a
real `uvicorn`, on the pinned 10 000-row / 365-UTC-day fixture. Budget is
**200 ms** (`tests/test_analytics_read.py:34`).

| What | p50 | p95 | p99 | max | Status | Scenario |
|---|---|---|---|---|---|---|
| `/v2/analytics/summary`, `c` = 1, n = 200 | 11.567 | 12.645 | 14.297 | 27.167 | 200 × 200, 0 errors | `S1` |
| `/v2/analytics/terms`, `c` = 1, n = 200 | 22.128 | 24.583 | 35.899 | 41.394 | 200 × 200, 0 errors | `S1` |
| `/summary`, `c` = 8, n = 240 (run 1 / run 2) | 166.953 / 166.358 | 178.257 / 178.496 | 184.520 / 187.969 | 190.513 / **206.004** | 200 × 480, 0 errors | `S2`/`C2` |
| `/summary`, `c` = 32 | 712.512 / 715.670 | 761.583 / 798.106 | 789.685 / 822.136 | 804.446 / 834.200 | 200 × 480, 0 errors | `S2`/`C2` |
| Mixed load, `c` = 8 | 227.621 / 292.565 / 260.651 | 952.683 / 941.671 / 996.735 | 977.333 / 985.877 / 1039.555 | 1004.909 / 1015.326 / 1065.160 | 200 × 720, 0 errors | `S3`, `C3`×2 |
| **100-year range**, `/summary`, n = 25 | 186.541 | 196.141 | **199.700** | **199.700** | 200 × 25, **0 of 25 over budget** | `S5`/`S6` |
| Refused request (`422`), n = 120 | 0.746 | 0.997 | 1.232 | 1.275 | 422 × 120, **0 statements issued** | `S9` |
| Valid read, same server, n = 120 | 10.846 | 12.299 | 13.268 | 25.169 | 200 × 120, 1 statement | `S9` |

**The three error figures, and their honest denominator.**

| Class | Count | Denominator | What it does and does not license |
|---|---|---|---|
| Unexpected 5xx | **0** | 1 920 ramp + 5 000 soak + 400 baseline requests | The strongest availability evidence in the record. It says nothing about frequency over time, because no time passes between runs. |
| Provoked `500 STORAGE_FAILURE` | **6 of 6** at p50 **5007.942 ms** | 6 concurrent readers against one `EXCLUSIVE` holder | A **total** read-surface outage for the full 5.0 s `busy_timeout`, not a fraction of it. `app/db.py:213` sets none; this stage confirmed the driver default independently: `PRAGMA busy_timeout` → **5000 ms** on this interpreter. |
| `422` refusals | **0** unexpected | 120 + 120 + the smoke suite's malformed requests | Each issues **zero** statements against the store, at **14.5× less wall time** than a valid read. Validation precedes computation, measured. |

**One correction this report carries forward rather than smoothing over.** The
single figure Build and Test recorded (`summary` 15.24 ms / `terms` 25.04 ms) sits
**inside** both later distributions, and `alarms.md` §2.3 notes it sits *below* the
observability stage's p50 for `terms`. It was one draw from a distribution, not an
outlier and not a baseline. Quoting it alone would have understated the tail — which
is why `slo-config.md` §2 SLI-1 published a distribution instead.

## 6. Why no burn rate appears anywhere in this report

This is the omission that most needs defending, because the material to fake one
was available and would have been easy.

**What a burn rate is:** the rate at which an error budget is consumed, relative to
the window, measured over a rolling window against a continuously computed SLI.
A burn rate of 1.0 means the budget is exhausted exactly at the window's end.

**What this project has instead:** one load-test run of **30 requests per
concurrency level** (`load-test-results` `S2`/`C2`), over **340 seconds** of wall
clock on one host, on a fixture this stage built in a scratch directory. From that
one could be computed a perfectly-shaped number — and it would be meaningless,
because:

1. **A rate needs a denominator in time, and 340 seconds is not the 30 days the
   target is defined over.** Dividing a 30-request sample by a 30-day window
   produces a quantity whose units describe nothing.
2. **The "budget" has no history to be drawn down against.** `slo-config.md` §4
   reduced it to a count of failures permitted *per verification run*. There is no
   prior run's spend to subtract from.
3. **Zero failures across the entire run is not a low burn rate; it is an absence
   of exposure.** Nothing failed because nothing contended, nothing was deployed
   mid-window, and nothing aged. `load-test-results` §11's six `500`s came from a
   lock this stage held on purpose — a condition that, in ordinary use, arises from
   the operator's own second process and lasts as long as they leave it open.
4. **`alarms.md` §4 already ruled the threshold out**, with the same reason, before
   this stage ran. Repeating the number here would contradict the artifact that
   owns the decision.

> **A burn rate derived from a load test is the single worst figure this report
> could contain.** It would be arithmetically computable, superficially
> authoritative, quoted by the next scope as an SLO baseline, and wrong in a way
> nobody could detect from the number itself. It is therefore absent, and its
> absence is the finding.

**What replaces it, and it is enough for this system:** the six counts in
`slo-config` §4, each of which a single failure exhausts. For a single-operator
tool that is the correct policy — `slo-config.md` §4 says so, and the reasoning
survives re-reading: there is no competing work to protect and no second user to
serve, so the budget's usual job of arbitrating between shipping speed and
reliability has no referent, and the budget collapses to a boolean.

## 7. Toil, counted rather than percentageed

The Google SRE standard measures toil as a share of an operations engineer's time.
There is no operations engineer, so this section counts the manual steps instead —
which is the same information without a fictitious denominator.

| Repeated manual step | Cost, measured | Automatable under the project's rules? |
|---|---|---|
| Install, test, boot, exercise the changed path before every squash-merge | **1.67 s** for the suite (`load-test-results`, `deployment-log` R3), plus the boot | **Yes** — `FR7.2`'s platform-neutral script, unbuilt (`u4-platform-packaging`) |
| Copy the store before anything starts the app | **under a second** | **Yes** — one `cp -p`, and `incident-plan.md` §5.3 already prescribes the exact command |
| Take a fresh copy after an incident and verify it | **under a second** | **Yes** — same command plus `sha256sum` |
| Run four grep-shaped checks to triage a failure | **under 10 s** once looking (`escalation-matrix.md` §3.3) | **No** — no rule engine exists, and `alarms.md` §1 names its absence |
| Notice that something is wrong at all | **unbounded** | **No** — four missing ingredients, all named in `alarms.md` §1 |

**The last row is the only one that matters, and `escalation-matrix.md` §3.3 says
so without hedging:** a restart takes 0.45–0.52 s (three runs, `runbooks.md` §7) and
detection time is unbounded. **The effective RTO is the notice time, not the
restart time**, and no SLO framework has a cell for it. Quoting an RTO that omits
that row — which `incident-response-guide.md`'s tier table invites, since it offers
< 5 minutes / < 30 minutes / < 4 hours — would be a fiction.

## 8. What this report does not establish, and what would change it

| Not established | Why | What would change it |
|---|---|---|
| Any property of the hours *between* verification runs | Nothing accumulates. `log-queries.md` §4.1: no retention, no aggregation, no shipping. | The cheapest single fix is `… > access.log 2> app.log` at startup (`incident-plan.md` §6's closing note, parked as **OQ-5**). Files still do not aggregate, but they survive the terminal — which is what makes any future trend possible. |
| Whether a latency regression would be *detected* | The access line carries **no duration field**; every latency figure in this project is stopwatch-measured by a human. `dashboards.md` §5. | A `log_config` access-log format carrying the duration. One configuration value, no new dependency — the same shape of change as the `TID251` entries already ruled on. Carried as **BL-08**. |
| Whether a `422` would be diagnosable from logs | Measured: **6 refusals, 0 application records** (`log-queries.md` §4(a)); `runbooks.md` §4 confirms it live. | A `logger` call on the validation branch, plus a decision about whether a mistyped date deserves a line (**OQ-2**, genuinely open). Carried as **BL-09**. |
| Whether the bind is safe | Point-in-time only. `alarms.md` §3.1 measured the CLI bypass on `127.0.0.2`; this stage re-confirmed the code shape: `app/main.py:93` resolves through `resolve_bind_host()`, `:120` refuses inside `create_app`, and the `uvicorn app:app` path reaches neither. | Moving enforcement somewhere the CLI cannot bypass (**OQ-3**, a scope decision, not a monitoring one). Carried as **BL-05**. |
| That any of this recurs at a knowable rate | No traffic history exists. `alarms.md` §4: the largest real sample is 27 requests. Severity is therefore classified by **consequence**, never by expected volume (`escalation-matrix.md` §5). | Nothing available on this machine. `incident-plan.md` §9 is right that quarterly game days would be theatre with one operator — and the real drill is the `rollback-runbook.md` rehearsal, which has now run twice. |

## 9. Summary

- **Six gates, all six met on their stated single-client, pinned-fixture shape** —
  audited against `load-test-results` rather than against `slo-config`'s own numbers.
- **Zero unexpected 5xx in 1 920 ramp + 5 000 soak requests**; 6 of 6 provoked `500`s
  from a competing writer, at the 5.0 s `busy_timeout` this stage independently
  confirmed as the driver default.
- **SLO-1 does not survive concurrency**: throughput peaks at two clients and falls
  3.8× by `c` = 32; the mixed load at `c` = 8 runs at p95 952.7 ms. A count-based
  budget cannot express that, and no requirement currently claims it.
- **No burn rate is quoted, and §6 gives the four reasons why computing one from
  this material would be worse than useless.**
- **Eight report elements recorded not-applicable**, each with the rule that rules
  it out and the substitute that was produced instead.
- **The honest summary is `slo-config.md` §4's own sentence, confirmed:** this
  system has an error budget on the way in and none on the way out.