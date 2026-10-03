# Cost Analysis — intent `261001-analytics-layer`

> **Stage:** `feedback-optimization` (operation, final stage) · lead `aidlc-operations-agent`
> support `aidlc-aws-platform-agent` · **Date:** 2026-10-03
> **Release analysed:** commit `aa0b1e4`
> **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/feedback-optimization`
>
> **Upstream inputs consumed by this stage:**
> `observability-setup/dashboards.md` (`dashboards`) ·
> `observability-setup/alarms.md` (`alarms`) ·
> `observability-setup/slo-config.md` (`slo-config`) ·
> `observability-setup/anomaly-config.md` ·
> `deployment-execution/deployment-log.md` (`deployment-log`) ·
> `deployment-execution/health-check-report.md` ·
> `performance-validation/test-results.md` — cited under this stage's declared slug
> `load-test-results` (§7 of the stage frontmatter) ·
> `performance-validation/nfr-validation-matrix.md` ·
> `incident-response/incident-plan.md` (`incident-plan`) ·
> `incident-response/runbooks.md` §9 ·
> `environment-provisioning/validation-report.md` (V-05, V-12, V-25, F-01…F-04) ·
> `construction/ci-pipeline/ci-config.md` §7 (caching) and `quality-gates.md` §5 ·
> `inception/requirements-analysis/requirements.md` (`FR7.1`, `FR7.3`, `C-5`, `C-6`) ·
> `memory/team.md` § Deployment ("Deployment is a localhost checkout, and a commit
> is the release").
>
> **Every byte, count and duration in §3–§5 was measured by this stage** unless the
> row names the artifact it is inherited from. Commands are given so a reader can
> repeat them.

---

## 1. What this file is, stated before anything else

**There is no AWS cost to analyse.** There is no account, no bill, no Cost Explorer
and no spend. This file therefore does two things, in this order:

1. **§2 records every cost element the stage declares as not-applicable, per
   element, with the rule that rules it out** — so the absence reads as a finding
   rather than as an oversight, which is the standard `memory/team.md` §
   Deployment sets: *"absence must not read as coverage."*
2. **§3–§5 measure the costs that genuinely exist** — a local, single-user Python
   application's real cost surfaces: dependency set and install footprint, store
   growth, process memory, CPU, and the bytes an unbounded response costs.

**Nothing in this file estimates a dollar figure.** Not because dollars are
uninteresting, but because inventing one for a system with no hosted component
would be arithmetic on nothing, and `memory/team.md` § Deployment records the
project's own version of that judgement: *"with no git remote, a hosted workflow
file is a file that has never run."* The measured quantities below are the honest
substitute, and they are the ones an operator can act on.

## 2. Declared not-applicable, per element, with the rule that rules it out

The stage declares "AWS Cost Explorer analysis & optimization recommendations".
Every element of that is absent, and each absence has an independent measured or
affirmed cause.

| Cost element | Verdict | The rule that rules it out | What was done instead |
|---|---|---|---|
| **Cost Explorer: actual vs forecast** | **N/A — no account** | No `aws` CLI on `PATH`, no `~/.aws`, no `AWS_*`/`CDK_*` environment variable, no `cdk.json`, no `*.tf`/`*.bicep`/`Pulumi.yaml` anywhere in the tree. Measured by `environment-provisioning` (inventory M1–M5) and re-confirmed by this stage. | Nothing to forecast. §5 instead reports **whether a growth projection is even constructible**, and concludes it is not. |
| **Cost allocation tags / showback / chargeback** | **N/A — nothing to allocate** | `C-5`: never introduce a new external service, hosted dependency or cloud component. There is no resource to tag. | §3.4 measures CPU seconds, the only resource quantity this system actually consumes in quantity. |
| **Rightsizing recommendations (over/under-provisioned)** | **N/A — no provisioned resource** | No instance, no volume type, no managed service. One process over one file on the operator's own machine. `incident-plan.md` §2 records no hosting, no supervisor, no IaC. | §3.3 measures the process's actual resident set, and §3.2 the store's actual growth per row. |
| **Idle-resource detection / unused instance or EBS cost** | **N/A — no resource to be idle** | Same absence. A local process consumes what the operator's machine already has. | §5 names what *would* be idle if this were hosted: nothing is provisioned, which is the cheapest possible rightsizing outcome. |
| **Reserved-instance / Savings Plans / commitment coverage** | **N/A — no commitment to make** | A commitment discount requires a baseline utilisation curve. `slo-config.md` §1 records that no request stream and no history exist; `load-test-results` adds that the largest real sample is 27 requests. | §3.4 publishes the one thing a capacity plan would start from: the measured throughput and CPU ceiling. |
| **Data-transfer / egress cost** | **N/A for the analytics path — structurally zero** | `environment-provisioning` V-28: the analytics read path's complete import closure contains **no network-capable import** at all. Measured again in `load-test-results` (`NFR2.2`, 0 forbidden imports). | §3.5 measures the *wire* bytes instead — the transfer that does happen is loopback, and its volume is the payload size. |
| **Storage cost (EBS/S3) growth projection** | **N/A as a cloud cost; measured as a local file** | No volume, no bucket. | §3.2 measures store growth per row, which is the quantity any storage projection would be built from. |
| **Trusted Advisor cost-optimization recommendations** | **N/A — Trusted Advisor does not exist here** | It is an AWS service. There is no account to be advised about. | §5 substitutes a four-item list of the project's own cost findings, each with a measured basis and a named owner. |
| **Log-retention / ingestion cost** | **N/A — nothing is shipped** | `dashboards.md` §1 and `log-queries.md` §4.1: no log group, no sink, no formatter, no retention tier; a session's log lives or dies with its terminal. `BR2.15` forbids adding a configuration value for one. | §5 records the cost of *not* having one, which is the real cost and it is not a dollar figure. |
| **Support-plan / licence / professional-services cost** | **N/A** | No licence is bought, no support contract exists, no external service is engaged. `FR7.4` requires a `LICENSE` **file** for the distribution's licence *expression*; that is a compliance artifact, not a purchase. | Noted so the absence is not read as a pending decision. |

**The one-line reason common to all ten:** there is no AWS account, no CLI, no
credential and no IaC file on this machine — and `C-5` forbids a cloud component
outright, `C-6` caps declared runtime dependencies at exactly two, so no exporter,
agent or collector could be added even if there were.

## 3. The five cost surfaces that genuinely exist

### 3.1 Dependency cost — 2 declared, 24 installed, 72 MB, no lockfile

| Quantity | Measured | How |
|---|---|---|
| Declared runtime dependencies | **`['fastapi>=0.110', 'uvicorn>=0.27']`** | `tomllib` read of `pyproject.toml` |
| Declared dev dependencies | **`['pytest>=8', 'pytest-cov>=5', 'ruff>=0.6']`** | same |
| Resolved distributions installed | **24** | `.venv/bin/python -m pip list`, rows after the two header lines |
| Install footprint on disk | **68 995 649 B (72 MB)** | `du -sb .venv` |
| Lockfile / constraints file | **none** | no `*lock*`, `constraints*` or `requirements*.txt` outside `.venv/` and the harness tree |

**Three costs inside that one row, in ascending order of how little they are
noticed.**

1. **The two-package rationale does not describe the install.** 24 distributions
   install from 2 declarations. `memory/team.md` § Deployment already names the
   awkward one: **`opentelemetry-api 1.45.0`** is a hard, non-extra dependency
   declared by `fastapi` itself and reached directly rather than through `anyio`.
   Nothing in `app/` imports `opentelemetry`, and no SDK or exporter is installed,
   so there is no egress path — but a reader counting two packages would be
   counting declarations, not distributions.
2. **`setuptools` is not an installed distribution at all.** PEP 517 build
   isolation means every `pip install -e ".[dev]"` downloads `setuptools>=68`
   fresh, unpinned and unhashed, into a temporary isolated environment and
   **executes `setuptools.build_meta` as code**. That is a real supply-chain cost
   with no artifact in the repository describing it.
3. **There is no lockfile, so the resolution is not reproducible.**
   `quality-gates.md` §5 measures the consequence directly: the system `ruff` is
   **0.16.9** and a fresh venv's is **0.16.10** — two different resolutions of the
   same manifest. The suite passes under both, so the cost today is *latent*, and
   the team's own wording (`memory/team.md` § Testing Posture) is exact: the
   suite's pass/fail state is "a function of **the resolved dependency set, not of
   the code**". `FR7.1` requires a lockfile with hashes; it is unbuilt, and
   `u4-platform-packaging` owns it.

**The store's own cost is separate and smaller:** the operator's
`data/sentiment.db` is **32 768 B** and `deployment-log.md` §5 records exactly one
file added under `data/` in this release — `data/sentiment.db.bak-aa0b1e4`, also
32 768 B, byte-identical. Two files, 64 KiB total, inside the gitignored
`/data/`. That is the whole durable footprint of the system.

### 3.2 Store growth — measured at **266 B per row**, on a **32 KiB** fixed base

Measured this stage, in a `mktemp -d` scratch tree, writing through the schema the
application's own `init_db` produces:

| Quantity | Measured |
|---|---|
| Page size | **4 096 B** |
| Store size after `init_db` on an empty database | **32 768 B** — exactly **8 pages**, and precisely the size of the operator's real store |
| Growth over **1 000** inserted rows (55-character text) | **266 240 B** → **266.2 B/row** |
| Store after 1 003 rows | **299 008 B** |
| Corroboration from `load-test-results`' own 10 000-row fixture | **2 887 680 B / 10 000 = 288.8 B/row** |

**Two honest consequences, and the second is the one that matters operationally.**

- **The cost is linear and small, and it is dominated by the text, not the
  analytics.** At 266 B/row, 10 000 rows is 2.7 MB; 1 000 000 rows would be
  266 MB. There is no index bloat surprise: the three named indexes are on
  `created_at`, `import_id` and `(label, created_at)`, and `load-test-results` `M1`
  measured the `v3 → v4` step as **index-additive only** — a content digest
  byte-identical across the step.
- **But there is no retention policy and no delete endpoint.** `validation-report.md`
  §G records this: rows live until the operator deletes the file or round-trips a
  CSV. So this is the one cost surface in the project that grows **without a
  caller-imposed bound and without the operator being told** — and `NFR9` names
  the same quantity as "the only quantity in this feature that can grow without a
  caller-imposed bound, and therefore the one a future scope may need to cap".

### 3.3 Process memory — **~55 MB at boot, ~65 MB after 71 requests, flat in payload volume

Measured this stage against a real `uvicorn` process over a 10 000-row fixture,
reading `/proc/<pid>/status` **on the python process** (an earlier attempt matched
the wrong pid and is not reported):

| Point in the sequence | `VmRSS` |
|---|---|
| At boot, before any request | **55 940 kB** |
| After 1 `/summary` read | **60 752 kB** |
| After 51 reads | **59 576 kB** |
| After 20 further `/terms` reads (each scanning all 10 000 rows) | **63 436 kB** |
| After 5 × ~7 MB responses | **67 728 kB** — i.e. **+4 292 kB for ~35 MB of payload served** |
| OS threads across the whole sequence | **1 → 2** (the `anyio` pool grows once) |
| Open file descriptors | **7 → 7** — **no descriptor leak** |

**Inherited and consistent:** `load-test-results` §12 records the boot floor at
**57 668 kB** and a steady-state working set of **147–186 MB** after the full
scenario sequence (including a 3 000-request soak), with **+3 356 kB for 71 MB of
payload** and no accumulation after a 2 s settle. My 71-request sample reaches
67.7 MB; theirs reaches 147–186 MB over thousands of requests. The two agree on
the shape — boot near 55–58 MB, descriptor count flat, payload growth small and
non-accumulating — and differ on the high-water mark, which is expected from a
77-request sample against a 5 000-request one.

**What cannot be concluded, and is not concluded:** whether 147–186 MB is a
**plateau** or a **slow leak**. `load-test-results` §14 says so in its own words —
*"a 342-second soak cannot detect a slow leak; that limit is real and is not
papered over."* Nothing in this project can settle it without a multi-hour soak,
and no requirement asks for one.

**The practical figure an operator should know** is the steady-state working set,
not the boot floor: **~150–190 MB** of the operator's 32 GB.

### 3.4 CPU cost — the same work costs **5.3× more** at eight clients

The clearest cost signal in the whole record, and it is a *cost* signal rather than
a latency one. `load-test-results` §3.2, on 240 identical requests per level:

| `c` | Throughput | Server CPU per request | Server CPU total for the same 240 requests |
|---|---|---|---|
| 1 | 84.43 rps | 11.75 ms | **2.8 CPU-s** |
| 2 | **157.78 rps** (peak) | 11.67 ms | — |
| 4 | 106.01 rps | 18.75 ms | — |
| 8 | 48.53 rps | **55.46 ms** | — |
| 32 | 44.08 rps | **62.21 ms** | **14.9 CPU-s** |

**5.3× the CPU for byte-identical logical work.** The mechanism is measured, not
guessed: `/terms` reads all 10 000 rows' text in one statement and then runs
`tokenize` → `significant_terms` → `Counter.update` **in pure Python per row**
(`app/analytics.py::read_terms`, `app/terms.py`) — CPython bytecode under one GIL.
The SQL is bounded; the Python is proportional to the **store**, not the range.

**The attribution is controlled.** The control `/v1/health`, which never touches the
store, reached **2 323.53 rps at `c` = 32** with per-request CPU **flat at
0.43–0.50 ms**, and the client spent 0.21–0.29 ms per analytics request — about 2 %
of what the server spent. So neither the load generator nor the transport explains
the curve. **The control is what makes this a cost finding about the analytics
path rather than a harness artefact.**

**The ceiling, which is the number a capacity plan would start from:** server
utilisation saturates at **2.63–2.79 cores** on a 12-thread host, whatever the
load beyond `c` = 4, and stays there. Twelve threads are available; the server uses
under three. That is the machine's real limit for this application, and it is why
throughput *falls* past `c` = 2 rather than rising.

### 3.5 What the unbounded payload costs in bytes

**This is the cost surface a caller can drive, and it is the only one under
external control.** Measured over real HTTP:

| Requested range | Series entries | `/summary` wire bytes | **Bytes per series entry** | Wall |
|---|---|---|---|---|
| 7 days | 7 | 1 610 | 230.0 | p50 1.067 ms |
| 365 days | 365 | 74 046 | 202.9 | p50 10.975 ms |
| 3 650 days | 3 650 | 704 766 | 193.1 | p50 25.253 ms |
| **36 500 days (100 years)** | **36 500** | **7 011 966** | **192.1** | p50 186.541 ms, **p99 199.700 ms** |

Source: `load-test-results` §6.1 and §6.2.

**The shape is the finding: the per-entry cost converges to ~192 B and stays
there.** Fixed framing (headers, envelope, the `total`/`counts`/`shares`/`mean_*`
preamble) is amortised as the series grows, so the response is **linear in the
*requested* range** — 1 610 → 74 046 → 704 766 → 7 011 966 B, a **4 355× rise for
a 5 214× rise in width**. `/terms` over the same 36 500 days returns **479 B**,
flat against its 365-day 479 B: the cost is entirely in `/summary`'s series
assembly.

**Confirmed independently by this stage**, over the same 10 000-row fixture:
`?from=2000-01-01&to=2099-12-31` returned **7 013 243 B in 189.271 ms** — within
1 277 B and 10 ms of the recorded figure, which is response framing and host
variance. The unbounded summary over the same store returned **123 515 B in
12.3 ms**.

**The memory cost of serving it is small and does not accumulate:** five
consecutive 7 MB responses cost **4 292 kB** resident (§3.3), and
`load-test-results` §12 measured ten of them at **3 356 kB with no release after a
2 s settle**. The cost of the unbounded payload is therefore **bytes on the wire and
milliseconds of serialisation, not resident memory.**

**And it is uncapped by decision, which is the honest framing.** `NFR9` states that
no cap is imposed and that *"the omission is deliberate rather than an oversight"*;
`alarms.md` §2.4 anticipates the crossover at "> 1.5 MB or > 1 s" without claiming a
breach; `runbooks.md` IR-7 declines to call it a defect and names the owner of the
decision (`u3-analytics-view`, **OQ-1**). This file therefore costs it and does not
re-litigate it. Carried to `feedback-loop.md` as **BL-07**, where the consequence
ranking — not the effort — decides it.

## 4. What these costs are not, stated so the numbers are not over-read

| Figure | What it does **not** establish |
|---|---|
| 266 B/row | Anything about a store of a different size. It is a linear extrapolation from one 55-character text and one schema. A different corpus changes it. |
| 24 distributions / 72 MB | A maintenance burden estimate. The cost is the **unpinned** resolution, not the count. |
| ~55 MB boot → ~150–186 MB steady state | Whether the high-water mark is a plateau or a leak. Untestable in 342 s. |
| 2.8 → 14.9 CPU-s for the same 240 requests | A regression against an earlier release. **There is no earlier release to regress against** — `git log --all -- data/` returns **0 commits**, and the previous code path had no analytics surface at all. This is a first measurement, not a trend. |
| 7 011 966 B for a 100-year range | A breach of the 200 ms budget. On this host it landed at **p99 199.700 ms — 0.3 ms inside** — while `runbooks.md` IR-7 recorded **4 of 5 repeats over** at a median of 240.7 ms and `dashboards.md` Panel D recorded 235 ms. **The finding is real and host-dependent; this run lands on the boundary rather than past it.** |
| Zero AWS cost | Zero cost. §3 lists five surfaces that all consume real local resources. |

## 5. Cost findings and optimization opportunities, ranked by size

Four opportunities that are **real cost reductions**, and one that is a cost this
project has chosen to carry. Each carries its measured basis and its owner. None is
proposed as an AWS action, because there is nothing to act on in AWS.

| # | Opportunity | Measured basis | Size | Owner |
|---|---|---|---|---|
| **CO-1** | **Ship the lockfile (`FR7.1`).** Removes the unpinned resolution, the per-install `setuptools` download-and-execute, and the two-`ruff`-versions drift in one change. No new dependency. | `quality-gates.md` §5; system ruff **0.16.9** vs venv **0.16.10**; `pyproject.toml` declares 5 floors and **no pins**. | S | `u4-platform-packaging` |
| **CO-2** | **Make the R5 store copy a standing step rather than a release step.** It costs **under a second** and it is the entire difference between a recoverable and an unrecoverable store loss. | `runbooks.md` §9: **0** commits contain `data/`; no scheduler, no `VACUUM INTO`, no `iterdump`, no `.backup()`; exactly **one** manual copy exists. | S | the human (a one-line habit) |
| **CO-3** | **Cap or paginate the unbounded series.** Removes a **7 MB / 36 500-entry / ~192 B-per-entry** response class that a single query parameter drives. Changes the `/v2` contract, so it is a contract decision, not an optimisation. | §3.5; `NFR9.3` deliberately imposes no cap; **OQ-1** names `u3-analytics-view` as the owner. | M | `u3-analytics-view` |
| **CO-4** | **Log to files at startup** (`… > access.log 2> app.log`). Costs nothing and makes every existing `grep` in `runbooks.md` §13 work — today the two streams interleave in one terminal where neither can be searched. | `log-queries.md` §1 (access on stdout, application on stderr); `incident-plan.md` §6 names it the one cheap observability answer not yet taken (**OQ-5**). | S | the human / `u4-platform-packaging` |
| **CO-5** | **Accept, with eyes open:** no log retention, no aggregation, no shipping, and no metrics. The saved cost is real and the price is named. | `log-queries.md` §4.1; `alarms.md` §1's four missing ingredients. | — | recorded, not proposed |

**One cost this project does not have, which is worth stating as the headline
finding of this section:** with no provisioned infrastructure, no registry, no
hosted service, no image and no CI runner, the recurring infrastructure cost of
this system is **zero dollars and zero provisioned resources**. That is not an
estimate — it is the direct consequence of `memory/team.md` § Deployment (*"no
environment tiers, no container, no hosted service, no IaC"*) and `C-5`. **The cost
this project actually pays is in attention, dependency reproducibility, and
unmeasured resource growth** — the four items above, none of which a Cost Explorer
would ever have shown.

## 6. Summary

- **Ten AWS cost elements recorded not-applicable**, each with the rule that rules
  it out and the local substitute produced instead. **No dollar figure is
  estimated anywhere in this file.**
- **Dependencies:** **2 declared → 24 installed → 68 995 649 B on disk**, with
  **no lockfile** and `setuptools` downloaded-and-executed unpinned on every install.
- **Store:** a **32 768 B** fixed base (8 × 4 096 B pages) plus **266.2 B/row**
  measured; the only cost surface that grows with no caller-imposed bound, and it
  has **no retention policy and no delete endpoint**.
- **Memory:** **55 940 kB at boot** → **67 728 kB after 71 requests and five 7 MB
  responses** (this stage), against an inherited **147–186 MB** steady state after
  thousands; descriptors **7 → 7**, threads **1 → 2**, **no leak** — and no
  multi-hour soak to say whether the high-water mark is a plateau.
- **CPU:** the same 240 requests cost **2.8 CPU-s at `c` = 1** and **14.9 CPU-s at
  `c` = 32**; the server saturates at **~2.8 of 12 threads**, and the
  `/v1/health` control at **2 323.53 rps** is what proves the cost is the analytics
  path rather than the harness.
- **Payload:** the unbounded series is **linear in the requested range** at
  **~192 B per entry**, reaching **7 011 966 B / 36 500 entries** at p99
  **199.700 ms** — re-measured this stage at **7 013 243 B / 189.271 ms** — and its
  resident-memory cost is small and non-accumulating.
- **Four ranked opportunities** (`CO-1`…`CO-4`), each with a measured basis and a
  named owner, and one accepted cost (`CO-5`).
- **The headline:** the recurring cloud cost of this system is **zero, because
  nothing is provisioned** — and that zero is the direct result of a deliberate
  constraint, not an accident of budget.