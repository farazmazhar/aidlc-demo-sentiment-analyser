# SLO / SLI Configuration — intent `261001-analytics-layer`

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
> (`infrastructure-specification`). Measured baselines are re-taken in this stage;
> the recorded ones are shown alongside for comparison.
>
> **This file deliberately extends `observability-design.md` §1, which recorded "SLO:
> none stated".** The extension is stated in §1 and §6 rather than smuggled in: a
> 30-day rolling SLO is meaningless for this system, but a *verification-window*
> target is exactly as enforceable and is what a release actually gates on.

---

## 1. What an SLO means when there is one operator, one machine and no traffic history

An SLO is a **promise about a measurement window**. The standard formulation —
"99.9 % of requests served under 200 ms, over a 30-day rolling window" — presumes a
stream of requests arriving from somewhere, continuously, for a month. Every one of
those preconditions is absent here:

| Precondition | This project | Evidence |
|---|---|---|
| A continuous stream of requests | **No.** The app runs when the operator starts it and receives requests when the operator makes them. | The largest real sample ever produced is **27 requests** (`smoke-test-results.md` §2); this stage's run was **13**. |
| A 30-day measurement window | **No.** Nothing runs between sessions; nothing accumulates history. | `monitoring-design.md` §1 — "no log aggregation, no retention tier". |
| Users whose experience is at stake | **One.** The operator, who is also the developer and the only person who could act on a breach. | `memory/team.md` §Deployment — "a localhost checkout is the entire deployment". |
| A continuously computed SLI to burn an error budget against | **No.** No metric is emitted at all. | `C-6`; `observability-design.md` §1. |
| Multiple instances, so "availability" means something | **No.** One process over one file. | `infrastructure-specification.md` §Deployment. |

**So a service-shaped SLO here would be theatre** — a number no one computes, over a
window that never elapses, guarding a user who is also the on-call engineer.

**What replaces it, and is genuinely enforceable:** an SLO over the **verification
window** — the span of a release verification run, which *is* measured, *is*
repeatable, *does* gate a release, and *has already run three times* in this project
(`build-and-test`, `environment-provisioning`, `deployment-execution`). Every SLI
below is computed over that window. The targets are stated as **release gates**, not
as uptime promises.

**The honest cost of this framing:** a verification-window SLI proves the system is
correct *at the moment it was checked* and says nothing about the hours in between.
That gap is real and is the direct consequence of having no alerting
(`alarms.md` §1). It is named here rather than papered over with a percentage.

## 2. The SLIs, each with the measurement that computes it

An SLI is only worth stating if the thing that measures it exists. Each row names
it.

### SLI-1 — Read-path latency

| | |
|---|---|
| **Definition** | Proportion of `/v2/analytics/*` requests answered within the **200 ms** budget (`tests/test_analytics_read.py:34`, `BUDGET_MS = 200`), over the pinned 10 000-row / 365-day fixture, measured **without coverage instrumentation**. |
| **Measured, this stage** | **50 / 50 requests within budget = 100 %** (25 runs × 2 endpoints). `summary` min 13.57 · p50 15.42 · mean 15.71 · **max 20.53 ms**. `terms` min 27.49 · p50 30.08 · mean 31.05 · **max 59.28 ms**. Both `200`. |
| **Recorded upstream** | `summary 15.24 ms / terms 25.04 ms`, single run, `test-results.md` §3.1. |
| **Instrument** | `pytest tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget` (asserts both endpoints under budget **and** `200`). |
| **Scope caveat** | This SLI holds **only** for the pinned 365-day span. It does **not** hold for arbitrary ranges: measured this stage, a 100-year window returns **235 ms** with a *single* stored row — over budget. See §5. |

### SLI-2 — Availability of the read surface

| | |
|---|---|
| **Definition** | Proportion of analytics reads that answer `200` rather than `5xx`. |
| **Measured, this stage** | Every well-formed read in every measurement taken answered `200`. Two deliberate `500`s appear only where this stage *provoked* a storage failure (`database is locked`) to capture the log format. `smoke-test-results.md` §2 records **27/27** for the release run. |
| **Instrument** | the release smoke suite; `health-check-report.md` H-10. |
| **Why no percentage is quoted** | Over 13 requests a percentage quantises to 7.7 % steps and over 27 to 3.7 % steps. Quoting "100 %" over that sample would be arithmetically true and statistically meaningless. The gate is the **count**: *zero unexpected 5xx in the verification window*. |

### SLI-3 — Correctness of the analytics answers

| | |
|---|---|
| **Definition** | Proportion of aggregate responses matching hand-written expected values. |
| **Measured, this stage** | **192 tests passed, 0 failed, 0 skipped, 0 errors, 0 warnings** (re-run by me: `pytest -v --no-header` → `192 passed in 2.30s`). Coverage **97.06 %** against the affirmed **80 %** floor (884 statements, 26 missed). |
| **Target coverage** | `test-results.md` §5 records **24 of 26** applicable NFR targets `Met`; the 2 `Unverified` (`NFR4.6`, `NFR4.7`) are owned by `u3-analytics-view`, which has not been built. |
| **Instrument** | the whole suite; the per-target matrix in `test-results.md` §5. |

### SLI-4 — Failure distinguishability

| | |
|---|---|
| **Definition** | Proportion of failures that carry a machine code distinct from every other outcome, and never render as a plausible empty result. |
| **Measured, this stage** | Three structurally distinct shapes observed over real HTTP: **empty success** (`200`, `total:0`, `series:[]`), **validation failure** (`422 VALIDATION_FAILED`, per-field message), **storage failure** (`500 STORAGE_FAILURE`). Never a `404` for emptiness; never a fabricated `0.0` where there is no denominator. |
| **Source** | `reliability-design.md` §2.2–§2.3; `smoke-test-results.md` §2.5 bodies S-14…S-21; reproduced live this stage for the storage shape. |
| **Why this is an SLI and not a nicety** | It is the property that lets an operator tell failure from emptiness *without any metric*. `NFR4.3`. |

### SLI-5 — Store write-neutrality of the read path

| | |
|---|---|
| **Definition** | Reading analytics never changes the store — same sha256, **same mtime**, same row count, same schema. |
| **Measured, this stage** | The operator's store, sampled before and after every command in this stage: `sha256 c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39`, `mtime 2026-10-03 03:33:42.920985500 +0500`, `size 32768`, `mode 644` — **identical on every field**. The unchanged **mtime** proves the file was never opened for writing, which is strictly stronger than "the contents matched". |
| **Instrument** | `sha256sum data/sentiment.db; stat -c '%y' data/sentiment.db` before and after; `tests/test_migration_indexes.py::test_reading_analytics_never_changes_the_store`. |

### SLI-6 — Loopback-only exposure

| | |
|---|---|
| **Definition** | Exactly one listening socket for the app, on a loopback address. |
| **Measured, this stage** | `LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:* users:(("python",pid=162172,fd=6))`; `resolve_bind_host` accepts `127.0.0.1`, `::1`, `localhost` and refuses `0.0.0.0`, `127.0.0.2`, `192.168.1.10`, `example.com` — the refusal is exact-set membership, so an "almost loopback" value does not slip through. |
| **Caveat — this SLI is verifiable only point-in-time.** | Measured this stage: the `uvicorn app:app --host …` CLI shape **bypasses the enforcement entirely** and binds whatever host it is given (`alarms.md` §3.1). The SLI is true of the socket as observed at check time and says nothing about how it was started. |

## 3. SLO targets, as release gates

Each is stated so that a run either satisfies it or blocks the release. None is a
percentage over an imaginary month.

| # | SLI | **SLO (release gate)** | Measured | Met? |
|---|---|---|---|---|
| **SLO-1** | SLI-1 latency | Every analytics read in the verification window answers **< 200 ms** on the pinned fixture | 50/50 | **yes** |
| **SLO-2** | SLI-2 availability | **Zero** unexpected `5xx` in the verification window | 0 | **yes** |
| **SLO-3** | SLI-3 correctness | **192 passed, 0 failed**; coverage **≥ 80 %** | 192 / 97.06 % | **yes** |
| **SLO-4** | SLI-4 distinguishability | Every observed failure carries a distinct machine code; emptiness is never an error | 3 distinct shapes | **yes** |
| **SLO-5** | SLI-5 store neutrality | Store `sha256` **and `mtime`** unchanged across the window | unchanged | **yes** |
| **SLO-6** | SLI-6 loopback | Exactly one listener, on `127.0.0.1` | confirmed | **yes** |

**All six are currently met, and all six were measured in this stage.** The
nearest miss is SLO-1, which is met with 140 ms of headroom on the *terms* endpoint's
measured maximum (59.28 ms) — and is the one that a wide request breaks; §5.

## 4. Error budget — what it honestly means here

The standard framing: an SLO of 99.9 % leaves 0.1 % of a 30-day window ≈ **43
minutes** of allowed unreliability. None of that transfers. What transfers is the
*shape*:

> **The verification run is the window. The budget is the count of failures it may
> contain.**

For SLO-1…SLO-6 the budget is expressed as a count, and every one of them is a gate
that a single failure exhausts:

| SLO | Budget | What exhausts it |
|---|---|---|
| SLO-1 latency | **0** requests over 200 ms | one slow read |
| SLO-2 availability | **0** unexpected 5xx | one storage failure |
| SLO-3 correctness | **0** test failures | one failing test |
| SLO-4 distinguishability | **0** ambiguous outcomes | one failure indistinguishable from emptiness |
| SLO-5 store neutrality | **0** writes | one byte, or one mtime tick |
| SLO-6 loopback | **0** non-loopback listeners | one socket |

**Two honest consequences.**

**First, the budget is trivially exhaustible, and that is correct.** For a
single-operator tool, "one failure blocks the release" is the right policy — there is
no competing work to protect and no second user to serve. The budget's usual job is
to arbitrate between shipping speed and reliability; there is no such tension here, so
the budget collapses to a boolean.

**Second, the budget is only ever consulted *before* a release.** After the release,
nothing computes any of these, because no alerting channel exists
(`alarms.md` §1). So the honest summary is: **this system has an error budget on the
way in and none on the way out.** Burn-rate alerting is not provisioned —
`slo-sli-patterns`' multi-window burn-rate scheme needs a continuously computed SLI
over a rolling window, and neither exists.

## 5. Where the SLIs do not reach — the honest boundary

Three limits, each measured, each named rather than averaged away.

1. **The latency SLI is fixture-shaped.** SLI-1 holds over a 365-day span by
   construction. The same endpoint over a 100-year window answers in **235 ms** — over
   budget — with a *single* stored row, because the series is zero-filled to the
   requested width (`BR4.4`) and the width is uncapped by design (`NFR9.3`,
   deliberately). Measured: 1 yr → 70 640 B / 13 ms · 21 yr → 2 803 760 B / 115 ms ·
   100 yr → 7 012 976 B / **235 ms**. **An SLI that holds only inside its fixture is
   a weaker promise than it looks, and this is the weakest of the six.**
2. **SLI-6 is point-in-time only** (`alarms.md` §3.1) — the CLI bypass means the bind
   is a property of *how the process was started*, which no in-process check records.
3. **No SLI covers the hours between verification runs.** Nothing accumulates, so
   there is no "over 30 days" claim available, and none is made.

## 6. Relationship to the upstream design, stated rather than quietly overridden

`observability-design.md` §1 records **"SLO: none stated"**, and
`monitoring-design.md` §4 records the SLI/SLO section as **"empty (operational)"**.
Both remain true of a *service-shaped* SLO, and this file does not contradict them.

What this file adds is a **verification-window** framing: targets over a span that is
actually measured and actually gates a release. It is an *extension*, and the reason
is that this stage is `CONDITIONAL` and executes specifically because monitoring
configuration is wanted; recording "none" and stopping would have been a faithful
restatement of an upstream design, but not a useful stage output. The extension adds
no mechanism, no dependency and no infrastructure — only a table of measured numbers
and the gates they support.

**What is *not* claimed:** no availability target over time, no uptime promise, no
multi-instance property, no capacity target (`NFR9`/`performance-design.md` §4 record
that no RPS target exists, and none is invented here).