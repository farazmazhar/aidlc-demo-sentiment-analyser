# SLO / SLI Configuration — intent `261004-analytics-view-packaging`

> **Stage:** `observability-setup` (operation) · lead `aidlc-operations-agent` ·
> **Date:** 2026-10-04 · **Release under observation:** the working tree at HEAD `4b67c03`
> · **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/observability-setup`
>
> **Upstream inputs:** the prior intent's `observability-setup/*` (measured baselines
> re-used where this release did not change the server side) · this intent's
> `deployment-execution/*` and `construction/build-and-test/*`.

## 1. What an SLO means here

An SLO is a promise about a measurement window. The standard 30-day rolling
formulation presumes a continuous request stream, a running service and multiple
users. None exists: one operator, one machine, one file, and the app runs only when
started. **A service-shaped SLO here would be theatre.**

What replaces it is an SLO over the **verification window** — the span of a release
verification run, which is measured, repeatable and gates a release. Every SLI below is
computed over that window; the targets are **release gates**, not uptime promises.

**Honest cost:** a verification-window SLI proves correctness at the moment it was
checked and says nothing about the hours between. That gap is the direct consequence of
having no alerting (`alarms.md` §1), and it is named rather than papered over.

## 2. The SLIs, each with the measurement that computes it

### SLI-1 — Read-path latency
Proportion of `/v2/analytics/*` requests answered within the **200 ms** budget
(`tests/test_analytics_read.py` `BUDGET_MS = 200`) over the pinned 10,000-row / 365-day
fixture. **Measured (inherited):** `summary` max 20.53 ms, `terms` max 59.28 ms, 50/50
inside budget. This release adds no server work, so the distribution is inherited.
**Instrument:** `pytest tests/test_analytics_read.py`.
**Caveat:** holds only for the pinned 365-day span; a 100-year window returns ~235 ms
with a single stored row (uncapped by design — `anomaly-config.md` §2).

### SLI-2 — Availability of the read surface
Proportion of analytics reads answering `200` rather than `5xx`. **Measured, this
release:** the smoke suite's well-formed reads answered `200`; the cutover answered
`200` on `/v1/health`, both `/v2` endpoints and `/` (`smoke-test-results.md`).
**Instrument:** the release smoke suite. **No percentage is quoted** — over a handful of
requests a percentage quantises to large steps; the gate is the **count** (zero
unexpected 5xx).

### SLI-3 — Correctness of the analytics answers
Proportion of aggregate responses matching hand-written expected values. **Measured,
this release:** `make verify` → **198 passed, 0 failed**; coverage **97.06 %** against
the affirmed **80 %** floor. **Instrument:** the whole suite via `make verify`.

### SLI-4 — Failure distinguishability
Proportion of failures carrying a machine code distinct from every other outcome, never
rendering as a plausible empty result. **Measured, this release:** empty success
(`200`, `total:0`, `series:[]`), validation failure (`422 VALIDATION_FAILED`, per-field
message) and storage failure (`500 STORAGE_FAILURE`) are structurally distinct.
**Instrument:** the smoke suite's refusal checks.

### SLI-5 — Store write-neutrality
Reading analytics never changes the store. **Measured, this release:** the operator's
store `sha256 2a4574cf…d42e7` and mtime `2026-10-03 23:59:14.115475300 +0500` were
**identical** before and after the cutover; the unchanged mtime proves the file was not
opened for writing. **Instrument:** `sha256sum`/`stat` before and after; the suite's
write-neutrality tests.

### SLI-6 — Loopback-only exposure
Exactly one listening socket for the app, on a loopback address. **Measured, this
release:** `LISTEN … 127.0.0.1:8000 0.0.0.0:*`; the loopback bind is enforced by
`resolve_bind_host`. **Caveat:** point-in-time only — the `uvicorn --host` CLI shape
bypasses the enforcement (`alarms.md` §3).

## 3. SLO targets, as release gates

| # | SLI | **SLO (release gate)** | Measured | Met? |
|---|---|---|---|---|
| **SLO-1** | SLI-1 latency | Every analytics read in the window answers **< 200 ms** on the pinned fixture | inherited 50/50 | yes |
| **SLO-2** | SLI-2 availability | **Zero** unexpected `5xx` in the window | 0 | yes |
| **SLO-3** | SLI-3 correctness | **All tests pass**; coverage **≥ 80 %** | 198 / 97.06 % | yes |
| **SLO-4** | SLI-4 distinguishability | Every observed failure carries a distinct machine code; emptiness is never an error | 3 distinct shapes | yes |
| **SLO-5** | SLI-5 store neutrality | Store `sha256` **and `mtime`** unchanged across the window | unchanged | yes |
| **SLO-6** | SLI-6 loopback | Exactly one listener, on `127.0.0.1` | confirmed | yes |

All six are met. The nearest miss is SLO-1, which a wide request breaks (§5).

## 4. Error budget

> **The verification run is the window. The budget is the count of failures it may contain.**

Each SLO is a gate a single failure exhausts: SLO-1 = 0 reads over budget; SLO-2 = 0
unexpected 5xx; SLO-3 = 0 test failures; SLO-4 = 0 ambiguous outcomes; SLO-5 = 0 writes;
SLO-6 = 0 non-loopback listeners.

**Two honest consequences.** (1) The budget is trivially exhaustible, and that is
correct for a single-operator tool with no competing work to protect — it collapses to a
boolean. (2) The budget is only ever consulted **before** a release; nothing computes it
afterwards, because no alerting channel exists. This system has an error budget on the
way in and none on the way out. Burn-rate alerting is not provisioned — it needs a
continuously computed SLI over a rolling window, and neither exists.

## 5. Where the SLIs do not reach

1. **SLI-1 is fixture-shaped.** It holds over a 365-day span by construction; a
   100-year window breaches the budget with a single stored row because the series is
   zero-filled to the requested width and the width is uncapped by design.
2. **SLI-6 is point-in-time only** — the CLI bypass means the bind is a property of how
   the process was started.
3. **No SLI covers the hours between verification runs** — nothing accumulates.

## 6. Relationship to the upstream design

`express` ships no `observability-design`; this file adds a verification-window framing
where the prior intent recorded "SLO: none stated" for a service-shaped SLO. The
extension adds no mechanism, dependency or infrastructure — only a table of measured
numbers and the gates they support. **Not claimed:** no availability target over time, no
uptime promise, no multi-instance property, no capacity target.
