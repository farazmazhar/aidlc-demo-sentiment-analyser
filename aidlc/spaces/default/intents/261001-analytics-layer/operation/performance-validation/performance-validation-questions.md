# Performance Validation Questions — intent `261001-analytics-layer`, stage `performance-validation`

> **Stage:** `performance-validation` (operation) · lead `aidlc-quality-agent`
> support `aidlc-operations-agent` · **Date:** 2026-10-03
> **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/performance-validation`
>
> **This file exists because the stage's Step 2 asks for clarifying questions. Most
> of what it would ask is already fixed** — by an affirmed practice, by a recorded
> measurement, or by a constraint — **and manufacturing an open question for
> something already settled would waste a human's attention and make the record
> look less trustworthy, not more.** So the shape here is:
>
> - **Q1–Q8: answered from evidence**, each with its source named. Not questions
>   awaiting an answer — conclusions this stage reached and can defend, recorded so
>   a reader does not have to re-derive them.
> - **Q9–Q12: genuinely open**, each a policy choice this stage cannot make, with
>   the evidence that makes it a real question rather than a hypothetical.
>
> **Four questions the stage template would have asked are answered in §"Answers
> from evidence" as Q1–Q4**, so nothing settled is left looking open.

---

## Answers from evidence

### Q1 — What are the expected traffic patterns (steady state, peak, burst)?

**Answered from evidence: there are none to model, and the honest load profile is
one concurrent user with occasional overlap.**

`scalability-requirements.md` § "Load profile" states the store is a single-user
local SQLite file with no multi-user, multi-tenant or network load, and
`performance-requirements.md` § "Concurrency posture" states there is no stated
requests-per-second target and that "throughput" here means bounded work per
request. `team.md` §Deployment makes a localhost checkout the entire deployment.

This stage nonetheless drove concurrency 1 → 64, because the concurrency
*constraint* is real even though the concurrency *profile* is not. Measured
steady state is `c` = 1 (`S1`: 200 requests, p50 11.567 ms, 85.14 rps); measured
overlap is `c` = 8 as the first budget breach (`S2`: p50 166.4 ms, one request in
240 at 206.004 ms). **A peak profile worth writing down is therefore
"1 user, and at most about 2 genuinely overlapping requests before the 200 ms
budget is at risk"** — which is a capacity statement about a single operator, not
a traffic model.

*Measured: `test-results.md` §2, §3.*

### Q2 — What are the target latency percentiles (p50, p95, p99)?

**Answered from evidence: there is exactly one latency target and it is not a
percentile. 200 ms per request, measured at whatever percentile is worst, over the
pinned 10 000-row / 365-day fixture.**

`nfr-requirements/performance-requirements.md` § "Latency budget" fixes **200 ms**
as the single stated target, and `performance-test-instructions.md` §7 records
that introducing percentile targets "would be inventing a target". No `NFRx.y`
states a p95 or a p99.

This stage measured the percentiles anyway and published them — p50 / p95 / p99 /
max per scenario, never an average — because the **verification** of a budget
needs a distribution and the Build and Test figure was a single cold draw
(15.24 / 25.04 ms). Measured distributions now exist: `/summary`
p50 11.567 · p95 12.645 · **p99 14.297** · max 27.167 ms; `/terms`
p50 22.128 · p95 24.583 · **p99 35.899** · max 41.394 ms. The target is met at
every percentile.

**The one place a percentile would change the verdict:** a 100-year range puts the
p99 at **199.700 ms** against a 200 ms budget — the target is met on that
distribution by 0.3 ms. That is a reason to keep the 200 ms figure a *maximum*
rather than a p99, which is what it already is.

*Measured: `test-results.md` §2, §6.2.*

### Q3 — What throughput must the system sustain?

**Answered from evidence: there is no throughput target, and the measured ceiling
is recorded as capacity rather than as compliance.**

`performance-requirements.md` § "Concurrency posture": "There is no stated
requests-per-second target." So no figure is compared against a threshold here.

Measured capacity on this host, for whoever needs a number: **`/summary` peaks at
157.8 rps at `c` = 2** and falls to 44.1 rps at `c` = 32; **`/terms` sustains
44.2 rps at `c` = 1` and falls to 8.6 rps at `c` = 8`; mixed page load sustains
~14.5 rps at `c` = 8. The ceiling is ~2.8 CPU cores on a 12-thread host.

*Measured: `test-results.md` §3, §4, §12.*

### Q4 — Where are the likely bottlenecks?

**Answered from evidence, and the answer is not the SQL.** The bottleneck is
CPython bytecode under one GIL, and it is the **term extraction**, not the
aggregate read.

The measured attribution:

| Candidate | Evidence | Verdict |
|---|---|---|
| The harness, loopback or the ASGI HTTP layer | `/v1/health` — which never touches the store — reaches **2 323 rps** at `c` = 32 at a **flat 0.43–0.50 ms CPU/request**. Client CPU was 0.21–0.29 ms per analytics request, ~2 % of the server's. | **Exonerated.** |
| The SQL | **One `SELECT`** at 7, 365, 3 650 and 36 500 days; the masked statement text is byte-identical at all four. The grouped read returns 1 095 rows whatever the range. | **Exonerated as a per-request cost.** |
| `sqlite3` concurrency | Throughput **doubles** from `c` = 1 to `c` = 2 (84.4 → 157.8 rps) because the driver releases the GIL; server CPU reaches 1.84 cores at `c` = 2. | **Partial, and it helps rather than hurts.** |
| **Pure-Python work in the request path** | Per-request server CPU is flat at **11.7 ms** through `c` = 2, then inflates to **18.75 / 55.46 / 59.38 / 62.21 ms** at `c` = 4 / 8 / 16 / 32. `/terms` alone at `c` = 8 costs **305.88 ms CPU per request** at **8.6 rps** — 5.1× *below* its own single-client rate — because it tokenises and counts all 10 000 rows' text in Python. | **The bottleneck.** |

**So "cost is bounded" (`scalability-design.md` §2) is true of the work a request
does and false of what eight overlapping requests cost.** Measured CPU per request
inflates ~5.3× (`/summary`) and ~14× (`/terms`) at `c` = 8. Nothing fails — 1 920
ramp requests and 5 000 soak requests returned `200` with zero errors — the system
simply gets proportionally slower. See Q10.

*Measured: `test-results.md` §3, §3.1, §3.2, §4, §7.*

### Q5 — Does the bounded-work claim survive measurement at four range widths?

**Answered from evidence: yes, exactly, on both endpoints.**
`/summary` and `/terms` each issue **one** `SELECT` at 7, 365, 3 650 and 36 500
days — a 5 214× range increase with a constant statement count — and the traced
statement is byte-identical across all four once bound values are masked. The
series length equals the requested day count at every width (7 / 365 / 3 650 /
36 500) while `total` stays 10 000, so the *work* follows the range and never the
store. Every refusal issues **zero** statements.

*Measured: `test-results.md` §7, §10.*

### Q6 — Is the unbounded payload a defect, a risk, or a non-issue?

**Answered from evidence: a real, reproduced capacity risk sitting exactly at the
budget boundary — and a *requirement*, not a defect.**

`NFR9.3` deliberately imposes no cap, so the behaviour is correct as specified. The
measurement: a 100-year range returns **7 011 966 B in 36 500 series entries**,
p50 **186.541 ms**, p99 **199.700 ms**, max **199.700 ms** — **0 of 25 requests over
200 ms**, i.e. **0.3 ms inside** the budget. `/terms` over the same range: 479 B,
max 27.454 ms, so the cost is entirely in `/summary`'s series assembly.

Three prior measurements on this host, and they disagree about which side of the
line it falls: `dashboards.md` Panel D recorded **235 ms**, `runbooks.md` IR-7
recorded **4 of 5 over budget** (median 240.7 ms), `smoke-test-results.md` §4
recorded 7 012 992 B. My byte count is within 1 010 B of all three; my wall time is
17–22 % faster. **The magnitude reproduces; the breach is load- and
moment-dependent.** `alarms.md` §2.4's threshold — > 1.5 MB or > 1 s — anticipates
it correctly without claiming a breach, and that is the right posture given no
alarm can fire. See Q8.

*Measured: `test-results.md` §6, §6.2.*

### Q7 — Is the store genuinely read-only under load, and do connections or threads leak?

**Answered from evidence: yes to all three, and the leak check is non-vacuous
because the load was large enough to leak.**

- **Read-only:** the load store's `sha256`, `mtime_ns` and `size` were identical
  before and after the whole sequence — 3 000+ concurrent reads, a 100-year range
  and a competing `EXCLUSIVE` writer. The repository's own `data/sentiment.db` is
  byte-, mtime-, size- and inode-identical (`c8be1361…`, `2026-10-03
  03:33:42.920985500 +0500`). **An unchanged mtime proves the file was never opened
  for writing**, which is stronger than matching contents.
- **Descriptors:** **7 before, 7 after** every scenario, including the
  3 000-request soak. Direct evidence that `BR6.1`'s request-scoped connection is
  really closed.
- **Threads:** **2 at boot, 11 after all load** — the `anyio` pool grows once and is
  reused.
- **Memory:** 10 consecutive 7 MB responses — 71 MB of payload — cost
  **+3 356 kB** resident, unchanged after a settle window. **Memory does not grow
  with series length**, though the steady state is 147–186 MB against 58 MB at
  boot.

*Measured: `test-results.md` §12, §13.*

### Q8 — Does the migration lifecycle behave under this stage's hands?

**Answered from evidence: yes, and it independently reproduces the 10 / 11 figures
with the counting convention pinned.**

**10** statements on a fresh store, **11** on a v3 store, **11** on the re-run —
where all three totals include the single `PRAGMA foreign_keys = ON` that
`app.db.connect` issues while opening; excluding it, 9 and 10. 2 of 2 rows
preserved, all 10 columns including the retired `intensity`, `version 3 → 4`, the
three named indexes exactly. **The re-run leaves the store byte-identical *and*
mtime-identical.** The v3 store was built by reading the `V3_DDL` fixture from
`tests/test_migration_indexes.py` (read-only reuse — no test file was edited).

*Measured: `test-results.md` §8.*

### Q9 — Was the offline guard left armed, and did anything leave the machine?

**Answered from evidence: yes to both, and the guard was not relied upon.**

The repository's `tests/conftest.py::offline_guard` (which makes every socket
connect raise) is untouched — `git diff --stat HEAD -- tests` is empty. The harness
lives outside the test tree, so it neither satisfies nor weakens the guard; its own
only sockets are loopback `HTTPConnection`s to the `uvicorn` process it starts, plus
one `EXCLUSIVE` lock holder reading a local file. `C-6` was honoured: the generator
is standard-library only (`http.client`, `threading`, `concurrent.futures`,
`sqlite3`, `subprocess`, `os`, `json`, `hashlib`, `math`) and
`pyproject.toml` gained nothing.

*Verified: `git status --porcelain -- app tests pyproject.toml data` empty;
`load-test-plan.md` §11.*

---

## Genuinely open

Four, each a policy choice this stage cannot make for the team. They are ordered by
how much they would change.

### Q10 — Should the superlinear concurrency degradation become a requirement?

**Why it is a real question.** Measured: per-request server CPU inflates
**11.7 → 62.2 ms** (`/summary`) and **22 → 305.9 ms** (`/terms`) between `c` = 1
and `c` = 8; throughput peaks at 2 clients and *falls* as more are added; the mixed
page load at `c` = 8 runs at p95 **952.7 ms**, 4.8× the budget. This contradicts
the plain reading of `scalability-design.md` §2's "cost is bounded" — though not the
letter of it, since that claim is about work per request, and no requirement states
anything about concurrent execution.

**The options.** (a) Leave it as a recorded finding for a future scope — the current
scope's posture is single-user, so the honest default. (b) Add an `NFR` stating a
latency expectation under overlap, which would then need an instrument and a
threshold. (c) Amend `scalability-design.md`'s wording so "cost is bounded" cannot
be read as a concurrency claim — cheap, and it removes the misreading without
inventing a target.

**This stage's recommendation is (c) then (a)**, but the wording of a design
artifact is not this stage's to change, and (b) is a real scope decision.

### Q11 — Should the 5.0 s `busy_timeout` be bounded, and should `NFR4.2` say what a read costs when it fails?

**Why it is a real question.** With a competing `BEGIN EXCLUSIVE` holder, **6 of 6**
reads returned `500` after **5 007.9 ms** (max 5 009.2 ms) — the CPython default,
because `app/db.py:213` sets none. A single writer therefore takes the **entire**
read surface down for five seconds and then fails every request. IR-1 already tells
the operator "do not restart"; nothing tells them *how long to wait*, and nothing
states what a failed read should cost.

**The options.** (a) Record as-is — the single-user posture makes a second writer
out of scope, and `runbooks.md` IR-1 documents the mode. (b) Set an explicit
`busy_timeout` so the failure is fast rather than slow — a one-line change to
`app/db.py`, but it alters the behaviour `runbooks.md` §3 measured, so it needs its
own stage and its own review. (c) Add a latency expectation for the failure path.

**This stage's recommendation is (a) for this Bolt** — changing `app/db.py` here
would modify application source, which is out of scope for a validation stage.

### Q12 — Does the unbounded series get a cap, or does the risk stay recorded?

**Why it is a real question — and note this one is inherited, not new.**
`nfr-requirements/scalability-requirements.md` already records the omission as
deliberate and files "Whether the unbounded series needs a cap" under the inception
requirements' Open Questions. `NFR9.3` says so in its own text: *"No cap is imposed,
and the omission is deliberate — it is a policy decision for a future scope, not an
oversight."*

This stage's measurement gives that future scope its first real number: **7 011 966
B and ~187 ms at a 100-year range**, p99 **199.7 ms** against a 200 ms budget, and
growing linearly. So the question is no longer hypothetical, and this stage cannot
answer it: imposing a cap would **contradict `NFR9.3` as written**, which is the
same class of error as manufacturing an instrument for `NFR4.6`.

**The options.** (a) Keep it uncapped and rely on `alarms.md` §2.4's manual
threshold — the status quo, and defensible for a single operator. (b) Cap it in a
future scope, which means amending `NFR9.3` and its series-extent expectations
together. (c) Cap it now — **not recommended**: it contradicts an approved
requirement inside a validation stage.

### Q13 — Is a 342-second soak enough, and does it matter that it isn't?

**Why it is a real question.** The soak ran **5 000 sustained requests over
342 seconds** across two runs and found no drift: the 3 000-request soak's p50
(243.7 ms) was *lower* than the 240-request run's (260.7 ms), throughput was flat
at ~14.5 rps, and descriptors and threads did not move. A standard soak is 4–24
hours.

**What the limit means, stated plainly.** A 342-second soak **cannot** detect a
slow leak — one that manifests over hours. What it *can* do, and did, is rule out
the leaks a per-request resource bug would produce: a descriptor leak at 14.5 rps
would have added ~5 000 descriptors in six minutes, and the count stayed at 7.
**A longer soak would be needed to say anything more**, and nothing in this
project's requirements asks for one — `slo-config.md` §1 records that no window
long enough to be meaningful ever elapses here. Recorded as a limit on this stage's
own evidence rather than as a gap in the system.

---

## Summary

| | Count | IDs |
|---|---|---|
| **Answered from evidence** | **9** | Q1–Q9 |
| **Genuinely open** | **4** | Q10 concurrency target · Q11 `busy_timeout` and failure-path cost · Q12 a cap on the unbounded series · Q13 soak duration |

**Nothing in Q1–Q9 is awaiting an answer.** Each carries the measurement or the
affirmed practice that settles it, so a reader does not have to re-derive it and a
reviewer does not have to ask. **Nothing in Q10–Q13 could be settled by this stage**:
each needs a policy choice, an amendment to an approved artifact, or a change to
application source — all of which are outside a validation stage's remit.
