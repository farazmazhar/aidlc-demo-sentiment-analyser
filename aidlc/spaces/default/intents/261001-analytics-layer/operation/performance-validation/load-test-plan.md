# Load Test Plan — intent `261001-analytics-layer`, stage `performance-validation`

> **Stage:** `performance-validation` (operation) · lead `aidlc-quality-agent`
> support `aidlc-operations-agent` · **Date:** 2026-10-03
> **Release under test:** commit `aa0b1e4` · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/performance-validation`
>
> **This plan was executed, not proposed.** Every scenario in §5 was run; §6 gives
> the measured outcome of each. The measured outcome lives in `test-results.md`;
> this file is the design that produced it, so a second run is reproducible from
> it alone.

## Upstream inputs consumed

| Declared `consumes` artifact | Where in this plan it is used |
|---|---|
| `performance-requirements.md` | §3 targets `NFR1.1`–`NFR1.4`; §4 the latency budget; §5 `S1`, `S2`, `S4` |
| `scalability-requirements.md` | §3 targets `NFR9.1`–`NFR9.4`; §4 the load profile (single-user, bounded work, no RPS target); §5 `S4`, `S5`, `P1` |
| `performance-design.md` | §2 the bounded-work model and budget decomposition; §5 `S2`, `S9`; §7 the design claim under test |
| `scalability-design.md` | §7 the pattern families declared inapplicable, and §8 the per-element ruling for each |
| `dashboards.md` | §5 `S5` (Panel D's width ladder) and §6 the comparison against Panel D's recorded table |

Also consulted, because they carry the measured baselines and the recorded
threshold this stage compares against: `nfr-design/reliability-design.md` (§3
the connection model), `operation/observability-setup/alarms.md` (§2.3 latency
thresholds, §2.4 range width), `operation/observability-setup/slo-config.md`
(SLI-1, SLO-1), `operation/incident-response/runbooks.md` (IR-7), and
`construction/build-and-test/{performance-test-instructions,test-results}.md`.

---

## 1. What this stage is for, and what it cannot do

`performance-requirements.md` and `scalability-requirements.md` state the load
profile plainly: **the store is a single-user local SQLite file, there is no
multi-user or network load, and "scalability" here means bounded work, not
throughput.** `performance-requirements.md` § "Concurrency posture" is equally
explicit that **there is no requests-per-second target** and that the concurrency
constraint has **no inception NFR parent** — it traces to `FR1.6`, `BR6.3`,
`FR8.4` and is a failure-behaviour instrument.

So this plan deliberately does **not** build a virtual-user model aimed at an RPS
number. It does four things that the delivered code can actually be wrong about:

1. **Re-measure the one stated budget** (`NFR1.1`/`NFR1.2`, 200 ms) as a
   distribution rather than the single cold figure Build and Test recorded.
2. **Test the bounded-work claim the way it is actually claimed** — one statement
   regardless of range — across four range widths and over real HTTP.
3. **Measure the concurrency behaviour** of the R-01 connection model
   (`reliability-design.md` §3) against a real `uvicorn` process, which is where
   the untested assumption in "bounded work" lives: bounded *logical* work is not
   bounded *wall-clock* work when requests overlap.
4. **Measure local capacity** — file descriptors, threads, resident memory,
   behaviour under a competing writer — because "there is no capacity plan" is a
   true statement about hosted tiers and a false one about a process.

## 2. Test environment

One real `uvicorn` process over real HTTP. **No in-process ASGI call is used for
any latency figure** (`BR3.6` / `AC8.1.4`: coverage instrumentation and an
in-process harness both inflate wall time and would make a budget a measurement
artefact). In-process calls appear once, in probe `P1`, and only to count
**statements**, never milliseconds.

| Element | Value |
|---|---|
| Host | Linux x86_64, AMD Ryzen 5 5600X (6 cores / 12 threads), 32 030 MiB RAM |
| Interpreter | CPython 3.14.7 |
| Driver | `sqlite3` 3.53.4 |
| Server | `uvicorn` 0.54.0, single process, **no `--workers`**; `fastapi` 0.142.2, `starlette` 1.7.0, `anyio` 4.15.1 |
| Invocation | `python -m uvicorn app:app --host 127.0.0.1 --port <p> --log-level info` |
| Bind | loopback only, the documented value. `alarms.md` §3.1 records that the CLI bypasses `resolve_bind_host`; that caveat is inherited and not re-litigated here — the value used **is** loopback, so the bypass has no exposure to create. |
| Ports | 8971 (run 1), 8973 (run 2), 8975 (probe 3) |
| Offline mode | no `config.local.toml` in the server's working directory, so `load_settings()` resolves the default offline engine and no credential exists in the process |

**Store isolation.** Every database lives under a fresh `tempfile.mkdtemp()`. The
`uvicorn` process is started with `cwd=<tempdir>` and `PYTHONPATH=<repo>`, so
`load_settings()` resolves `data/sentiment.db` relative to that directory. The
repository's own `data/sentiment.db` is **never opened**, read or written by any
scenario. Its `sha256`, `mtime`, `size`, `mode` and `inode` were sampled before
and after all three runs and are recorded in `test-results.md` §7.

**The fixture** is the one the targets are stated over: 10 000 analyses pinned to
span **exactly 365 distinct UTC days** (`2025-10-04` … `2026-10-03`), labels
rotating over all three, confidence cycling `0.00`–`0.99`, `import_id` `NULL`
(`NFR1.1`, `BR3.6`). Each row's text is realistic enough for the term path
(`"a stored analysis number N about wonderful dreadful ordinary things"`), so
`/terms` exercises tokenisation and ranking over 10 000 rows, not over one.

## 3. Targets under test

| ID | Target | Instrument this stage |
|---|---|---|
| `NFR1.1` | `/summary` answers **under 200 ms** over the pinned fixture | `S1`, `S2` |
| `NFR1.2` | `/terms` answers **under 200 ms** over the same fixture, without coverage instrumentation | `S1`, `S2` |
| `NFR1.3` | statement count **independent of the range's day count** | `P1` |
| `NFR1.4` | unbounded summary returns **exactly 365 entries** over 10 000 rows | `P1` |
| `NFR9.1` | series length **equals** the UTC days in the resolved range | `P1`, `S4` |
| `NFR9.2` | terms payload bounded by `limit` per list, never by the store | `P1` |
| `NFR9.3` | the unbounded series is **capped by nothing, deliberately** | `S5`, `P1` |
| `NFR9.4` | statement count does not grow with the range span | `P1` (shared with `NFR1.3`) |
| `NFR3.1` | reading analytics never changes the store | §7 store neutrality |
| `NFR3.2` | the read path issues **no mutating statement** | `P1` |
| `NFR4.1` | a validation failure is `422`, names its field, and **computes nothing** | `S9`, `P1` |
| `NFR4.2` | a storage failure is `500 STORAGE_FAILURE`, distinct from validation | `S10`, `P3` |
| `NFR4.3` | a failure never renders as a plausible empty result | `S9`, `P1`, `P3` |
| `NFR4.5` | additive migration idempotent, row-preserving, loud rollback | `M1` |
| `NFR8.1` | every application failure reaches the module logger | `P3` |
| `NFR8.2` | the machine code travels on the envelope **and** in the log | `P3` |
| `NFR8.3` | no parameter interpolated into statement text | `P1` |

`NFR2.1`–`NFR2.6` and `NFR4.4`'s tie-rounding are **not** this stage's
instruments (they are security and aggregate-correctness targets with no latency
or concurrency dimension); they are carried into the matrix with their evidence
named rather than claimed. `NFR4.6` and `NFR4.7` are **not executable in this
Bolt** — see §9.

## 4. Measurement method

- **Percentiles only.** Every distribution is reported as
  `min / p50 / p95 / p99 / max`, nearest-rank (`ceil(q·N)`), over the raw
  per-request samples. **No average is reported anywhere**, because an average of
  50 ms hides a p99 of 5 s (`nfr-validation-methods` § "Latency percentiles").
- **Timer:** `time.perf_counter()` around request-send → response-body-read, so
  the measurement includes serialisation and transfer, not just handler time.
- **Client:** stdlib `http.client.HTTPConnection`, one keep-alive connection per
  worker thread, re-established transparently on a transport error. **Standard
  library only** — `http.client`, `threading`, `concurrent.futures`,
  `statistics`, `sqlite3`, `subprocess`, `os`, `json`. No k6, no Locust, no
  Artillery, no `pytest-benchmark`, and no new entry in `pyproject.toml`: `C-6`
  caps declared runtime dependencies at two (`fastapi`, `uvicorn`).
- **No outbound network call.** The only sockets opened are loopback
  `HTTPConnection`s to the server this harness starts, plus one `uvicorn`
  process. The repository's offline guard (`tests/conftest.py::offline_guard`)
  stays armed and untouched; the harness lives outside the test tree, so it
  neither satisfies nor weakens that guard.
- **Warm-up** requests precede every timed scenario so connection setup and the
  first-request import path are not counted as steady state.
- **Attribution control.** The client and server CPU costs are read from
  `/proc/<pid>/stat` (`utime + stime`) around each scenario, and a control
  scenario drives a request that **never touches the store** (`/v1/health`) at the
  same concurrencies. Without those two, "the server is slow" and "my load
  generator is slow" are indistinguishable, and this plan would be reporting an
  uninterpretable number.
- **`env -u APPIMAGE` on every spawn.** The shell exports
  `APPIMAGE=…opencode-desktop-linux-x86_64.AppImage`, which makes CPython report
  the AppImage as `sys.executable`; a subprocess spawn then fails with exit 130.
  `build-and-test/test-results.md` §3.1 records this as the cause of the one
  failing test in that stage; every command here carries the prefix.

## 5. Scenarios

`c` = concurrent client threads. `n` = requests in the scenario. Requests are
split evenly across clients so every level issues the *same total work*, which is
what makes the throughput column comparable.

| # | Scenario | `c` | `n` | Question it answers |
|---|---|---|---|---|
| **S1** | Sequential baseline, unbounded range, `/summary` then `/terms` | 1 | 200 each | What is the budget's real distribution, not its single cold figure? |
| **S2** | Concurrency ramp on `/summary`: `c` = 1, 2, 4, 8, 16, 32, 64 | as shown | 240 each | Does concurrent reading behave, and where is the first budget breach? |
| **S3** | Mixed `/summary` + `/terms` interleaved at `c` = 8 | 8 | 240 | What does one page load actually cost when several overlap? |
| **S4** | Range-width ladder on `/summary`: 7, 365, 3 650, 36 500 days | 1 | 15 each | Is the payload linear in range width, and is the cost on `/summary` or `/terms`? |
| **S4′** | The same ladder on `/terms` | 1 | 15 each | Localises the width cost to one endpoint or neither. |
| **S5** | Unbounded 100-year `/summary`, repeated (IR-7's breach mode) | 1 | 25 | Is the crossover reproducible, and is it a breach or a near miss on this host? |
| **S5′** | The same 100-year range on `/terms` | 1 | 25 | Confirms the localisation from the other side. |
| **S6** | Memory growth: 10 × 7 MB payloads, RSS sampled before / after / after settle | 1 | 10 | Does resident memory grow with series length? |
| **S7** | Analytics at `c` = 8 with a parallel `/v1/health` probe thread | 8 | 240 | Does the process stay responsive while the read path is saturated, and does health see the store at all? |
| **S8** | Refusal cost: valid unbounded vs `422` inverted range vs `422` unreadable bound | 1 | 120 each | Does a refused request really pay no read cost? (`performance-design.md` §2.3) |
| **S9** | Writer contention: a second process holds `BEGIN EXCLUSIVE`; 6 readers race it, then repeat after release | 6 | 6, then 12 | What does a competing writer do to the read surface, and how fast is recovery? |
| **S10** | Soak: mixed load at `c` = 8 | 8 | 2 000 | Does anything drift over a sustained window, and do descriptors or threads leak? |
| **C1** | **Control:** `/v1/health` (never touches the store) at `c` = 1, 8, 32 | as shown | 400 each | How much throughput does this host and harness have when the read path is not involved? |
| **C2** | Ramp repeat, independent run | 1…32 | 240 each | Are the ramp numbers reproducible? |
| **C3** | Mixed at `c` = 8, repeated twice | 8 | 240 each | Run-to-run stability of the mixed collapse. |
| **C4** | `/terms` alone at `c` = 8 | 8 | 240 | Attributes the mixed collapse to one endpoint. |
| **C5** | `/summary` alone at `c` = 8, second run | 8 | 240 | The pair to `C4`. |
| **C6** | Soak at `c` = 8, mixed, with fd/thread accounting | 8 | 3 000 | Longest sustained run; descriptor and thread leak check. |
| **P1** | Statement-count probe, in-process, traced on the connection the app itself opens | — | 4 widths × 2 endpoints, plus unbounded and three refusals | `NFR1.3`, `NFR9.4`, `NFR1.4`, `NFR9.1`, `NFR9.2`, `NFR9.3`, `NFR3.2`, `NFR8.3`, `NFR4.1` |
| **P3** | Storage-failure probe over real HTTP with an `EXCLUSIVE` holder | 1 | 2 endpoints | `NFR4.2`, `NFR4.3`, `NFR8.1`, `NFR8.2` |
| **M1** | Migration lifecycle: fresh store, v3 store, re-run | — | 3 paths | `NFR4.5` — statement counts, row preservation, index set, byte and mtime identity |

`P1` is the only in-process probe and it measures **counts, never milliseconds** —
which is exactly the split `BR3.6` draws. Every latency figure in this stage came
over HTTP from a real `uvicorn`.

## 6. Scenario coverage map

| Requirement family | Covered by |
|---|---|
| `performance-requirements` `NFR1.1`–`NFR1.2` (200 ms) | `S1` (c=1 distribution), `S2` (ramp), `C1`/`C2`/`C5` (attribution) |
| `performance-requirements` `NFR1.3` / `scalability-requirements` `NFR9.4` (one statement) | `P1` |
| `performance-requirements` `NFR1.4` / `NFR9.1` (series length = range) | `P1`, `S4` |
| `scalability-requirements` `NFR9.2` (payload bounded by `limit`) | `P1`, `S4′` |
| `scalability-requirements` `NFR9.3` (uncapped unbounded series) | `S5`, `S5′`, `P1` |
| `reliability-design.md` §3 (connection model, `check_same_thread=False`) | `S2`, `S3`, `S9`, `C6` |
| `performance-design.md` §2.1 (one grouped read) and §2.3 (validation before computation) | `P1`, `S8` |
| `performance-design.md` § "What is deliberately absent" (no cache, no pool) | §6 capacity results — RSS, fds, threads |
| `dashboards.md` Panel D (range width as the saturation signal) | `S4`, `S5`, compared against its recorded table |
| `alarms.md` §2.3 / `slo-config.md` SLI-1 (latency thresholds) | `S1`, `S2`, `S7` |
| `runbooks.md` IR-7 (wide-range budget breach) | `S5`, `S5′` |
| `runbooks.md` IR-1 (`database is locked`) | `S9`, `P3` |

## 7. The design claim this plan is built to test

`scalability-design.md` §2 states the unit's scaling story as four invariants, of
which two are performance claims this plan can falsify:

> "**Statement count does not grow with the range span.** One grouped read over
> the range plus an in-process fill … `NFR9.4`, `NFR1.3`."
>
> "The one quantity that can grow without a caller-imposed bound is the unbounded
> series length — and the design binds its *cost* … even though it does not bind
> its *length*. … **cost is bounded, length is not**."

**The claim under test is "cost is bounded".** The plan tests it in the two forms
it could be true or false:

- **Is the cost bounded as a function of the range?** `P1` counts statements at
  7 / 365 / 3 650 / 36 500 days; `S4`/`S5` measure latency and bytes over the same
  ladder.
- **Is the cost bounded as a function of concurrency?** Nothing upstream claims
  it is — the concurrency posture is explicitly not a performance target — but
  "cost is bounded" is the phrase a reader would carry away, so `S2`, `C2`–`C6`
  measure it. **This is where the plan's central finding lives**, and it is a
  finding about a *stated design phrase*, not about a failed requirement.

## 8. Declared inapplicable, per element, with the rule that rules each out

`scalability-design.md` §3 and `reliability-design.md` §5 already rule out most of
this stage's standard repertoire with stated reasons. Those rulings are inherited
and re-measured where measurement was possible, so each element is recorded here
against the rule that excludes it.

| Standard practice | Applies? | The rule that rules it out | Measured anyway? |
|---|---|---|---|
| CloudWatch / X-Ray latency and trace analysis | **No** | `infrastructure-specification.md` §5 and `environment-provisioning` V-* : no `aws` CLI, no `~/.aws`, no `AWS_*`/`CDK_*`, no `cdk.json`, no `*.tf`/`*.bicep`/`Pulumi.yaml` anywhere in the tree; and `C-6` caps runtime deps at two, so no metrics/tracing agent can be added. `dashboards.md` §4 records CloudWatch as not provisioned. | **Partly.** There is no CloudWatch, but there *are* two real text streams: `uvicorn`'s access log and the module logger. `P3` reads the module logger's `ERROR` record verbatim and compares it with the envelope and the access line. That is the same three-surface agreement a trace would evidence, at the fidelity this host permits. |
| Auto-scaling validation (scale-out/in triggers, min/max capacity) | **No** | `scalability-design.md` §3: one loopback process over one local file — no hosted tier, no autoscaler, no queue, no threshold to tune. There is no scaling group to trigger and no second instance to drain. | **No, and none should be.** Manufacturing a replica would contradict the localhost-only mandate (`BR6.5`). |
| Multi-tier / horizontally-scaled capacity planning | **No** | Same rule. `scalability-requirements.md` § "Capacity planning" states there is no capacity target to plan against and that saying so is the accurate record. | **Replaced by local capacity**, §9 — which is real and was measured. |
| Load-balancer / queue / cache-tier benchmarks | **No** | `scalability-design.md` §3, each with its own reason: no second instance to balance to; nothing to decouple (the read path is synchronous with no outbound call, `BR2.8`); the data is a local file read once per request, so a cache adds an invalidation surface for no measured gain. | **No.** |
| Virtual-user model against an RPS target | **No** | `performance-requirements.md` § "Concurrency posture": "There is no stated requests-per-second target: the store is a single-user local SQLite file (`NFR9`), so 'throughput' here means bounded work per request, not RPS." | **Yes, deliberately, and labelled as such.** Concurrency levels were driven anyway — because the concurrency *constraint* is real (`FR8.4`, `BR6.3`) — but every throughput number in `test-results.md` is reported as **measured capacity of this host**, never against a target. |
| Percentile SLOs / burn-rate alerting | **No** | `slo-config.md` §1: no continuous request stream, no 30-day window, one user, no continuously computed SLI. §4: the verification run *is* the window. | **Partly.** This stage publishes the **distribution** the 200 ms budget was missing (`S1`, `S2`); it does not convert it into an SLO, because nothing computes one continuously. |

## 9. What this plan will not do, and why

**It will not manufacture an instrument for `NFR4.6` or `NFR4.7`.**
`reliability-design.md` §2.5 hangs both partly on this unit ("the rule
participates in this unit's summary region") while naming instruments that only
`u3-analytics-view` can satisfy: `AC6.5.3` / `AC6.5.5` need a **second analytics
section**, and `AC6.5.2` needs a **date-range control** to supersede. Neither
markup exists in this Bolt. Writing the markup here would duplicate
`u3-analytics-view`'s deliverable and repeat the `app/terms.py` unit-boundary
violation that three review passes already disclose. Both are therefore reported
`Unverified` with their owning Unit named, and no test is written against markup
that does not exist.

**It will not modify application source, tests, configuration or the store.**
Verified after all three runs: `git status --porcelain -- app tests pyproject.toml
data` is empty, and `git diff --stat HEAD -- app tests pyproject.toml` is empty.
The repository's `data/sentiment.db` is byte-identical including mtime.

**It will not add a runtime dependency or a load-testing framework.** The
generator is ~330 lines of standard library; §11 reproduces it.

## 10. Re-running this plan

```bash
cd <repo-root>
env -u APPIMAGE python /tmp/opencode/perfval/loadgen.py  "$(pwd)" /tmp/opencode/perfval/out
env -u APPIMAGE python /tmp/opencode/perfval/loadgen2.py "$(pwd)" /tmp/opencode/perfval/out
env -u APPIMAGE python /tmp/opencode/perfval/loadgen3.py "$(pwd)" /tmp/opencode/perfval/out
```

Each writes `load-results.json`, `load-results-2.json` and `load-results-3.json`
into the output directory and prints its own summary table. Wall time is about
**9 minutes** for all three (`S10`/`C6` soaks dominate). Ports 8971/8973/8975 must
be free. Nothing outside the output directory and the harness's own temp
directories is written.

## 11. The harness

Three files, standard library only, no project file touched.

### `loadgen.py` — the load, concurrency and capacity run

```python
#!/usr/bin/env python3
"""Load / concurrency harness for intent 261001-analytics-layer, stage performance-validation.

Standard library only (http.client, threading, concurrent.futures, statistics,
sqlite3, subprocess, os, json). No load-testing framework, no new runtime
dependency, no outbound network call: the only socket this file ever opens is a
loopback HTTPConnection to the uvicorn process it starts.

Isolation: every database lives under a temporary directory; the uvicorn process
is started with cwd=<tmp> so `load_settings()` resolves `data/sentiment.db`
relative to that directory. The repository's own `data/sentiment.db` is never
opened for writing and never opened at all.

Usage:  python loadgen.py <repo-root> <out-dir>
"""

from __future__ import annotations

import http.client
import json
import math
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))

FIXTURE_ROWS = 10_000
FIXTURE_DAYS = 365
BUDGET_MS = 200
LABELS = ("positive", "negative", "neutral")
PROBS = '{"positive": 0.9, "negative": 0.05, "neutral": 0.05}'
INSERT = (
    "INSERT INTO analyses (text, label, probabilities, confidence, model, provider,"
    " created_at, import_id) VALUES (?,?,?,?,?,?,?,?)"
)
HOST = "127.0.0.1"


def pct(sorted_values: list[float], q: float) -> float:
    """Nearest-rank percentile: the smallest value at or above rank ceil(q*N)."""
    if not sorted_values:
        return float("nan")
    rank = max(1, math.ceil(q * len(sorted_values)))
    return sorted_values[min(rank, len(sorted_values)) - 1]


def dist(values: list[float]) -> dict:
    """The distribution actually reported: percentiles, never an average."""
    s = sorted(values)
    return {
        "n": len(s),
        "min_ms": round(s[0], 3),
        "p50_ms": round(pct(s, 0.50), 3),
        "p95_ms": round(pct(s, 0.95), 3),
        "p99_ms": round(pct(s, 0.99), 3),
        "max_ms": round(s[-1], 3),
    }


def seed_pinned_store(db_path: Path) -> dict:
    """The NFR1.1 fixture: 10,000 analyses pinned to exactly 365 distinct UTC days."""
    from app.db import init_db

    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_db(db_path)
    today = datetime.now(UTC).date()
    start = today - timedelta(days=FIXTURE_DAYS - 1)
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany(
            INSERT,
            [
                (
                    f"a stored analysis number {index} about wonderful dreadful ordinary things",
                    LABELS[index % 3],
                    PROBS,
                    (index % 100) / 100.0,
                    "dummy-keyword-v1",
                    "offline",
                    f"{(start + timedelta(days=index % FIXTURE_DAYS)).isoformat()}T12:00:00Z",
                    None,
                )
                for index in range(FIXTURE_ROWS)
            ],
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "path": str(db_path),
        "rows": FIXTURE_ROWS,
        "days": FIXTURE_DAYS,
        "first_day": start.isoformat(),
        "last_day": today.isoformat(),
        "bytes": db_path.stat().st_size,
    }


def hit(conn: http.client.HTTPConnection, path: str, timeout: float = 30.0) -> Sample:
    t0 = time.perf_counter()
    try:
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read()
        return Sample((time.perf_counter() - t0) * 1000.0, resp.status, len(body), None)
    except Exception as exc:  # noqa: BLE001 - the harness reports, never hides
        try:
            conn.close()
        except Exception:
            pass
        return Sample((time.perf_counter() - t0) * 1000.0, None, 0, f"{type(exc).__name__}: {exc}")


def run_scenario(base_port, name, concurrency, total, path_fn, note="", warmup=0,
                 timeout=30.0, background=None) -> dict:
    """Drive `total` requests at `concurrency` against one path each, over real HTTP.

    `path_fn(worker_index, request_index)` returns the request path, so a scenario
    can mix endpoints or walk a width ladder. Each worker keeps one keep-alive
    HTTPConnection for the whole scenario.
    """
    samples, lock = [], threading.Lock()
    per_worker = [total // concurrency] * concurrency
    for i in range(total % concurrency):
        per_worker[i] += 1

    def worker(w: int) -> None:
        conn = http.client.HTTPConnection(HOST, base_port, timeout=timeout)
        local: list[Sample] = []
        try:
            for r in range(per_worker[w]):
                s = hit(conn, path_fn(w, r), timeout=timeout)
                local.append(s)
                if s.error:  # a dropped keep-alive needs a fresh connection
                    conn = http.client.HTTPConnection(HOST, base_port, timeout=timeout)
        finally:
            try:
                conn.close()
            except Exception:
                pass
        with lock:
            samples.extend(local)

    if warmup:  # the first request pays connection setup; it is not steady state
        wc = http.client.HTTPConnection(HOST, base_port, timeout=timeout)
        for _ in range(warmup):
            hit(wc, path_fn(0, 0), timeout=timeout)
        wc.close()

    if background is not None:
        background[1].start()

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(worker, range(concurrency)))
    wall = time.perf_counter() - t0
    if background is not None:
        background[1].join()

    ok = [s for s in samples if s.status == 200]
    out = {
        "scenario": name, "note": note, "concurrency": concurrency,
        "requested": total, "completed": len(samples), "wall_s": round(wall, 4),
        "throughput_rps": round(len(samples) / wall, 2) if wall > 0 else None,
        "status_counts": dict(Counter(str(s.status) for s in samples)),
        "error_count": sum(1 for s in samples if s.error),
        "error_kinds": dict(Counter(s.error for s in samples if s.error)),
        "http_2xx": len(ok),
        "non_2xx": sum(1 for s in samples if s.status and s.status >= 300),
        "response_bytes_median": None,
    }
    if ok:
        out["response_bytes_median"] = sorted(s.nbytes for s in ok)[len(ok) // 2]
        out["latency_200_only"] = dist([s.ms for s in ok])
    out["latency_all"] = dist([s.ms for s in samples])
    return out


class Server:
    """A real uvicorn process, started in a temp cwd, with /proc accounting."""

    def __init__(self, tmp: Path, port: int):
        self.tmp, self.port, self.proc = tmp, port, None
        self.log = tmp / "uvicorn.log"

    def start(self) -> dict:
        env = dict(os.environ)
        env.pop("APPIMAGE", None)          # otherwise sys.executable is the AppImage
        env["PYTHONPATH"] = str(REPO)
        env["PYTHONUNBUFFERED"] = "1"
        self.handle = self.log.open("wb")
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", "--host", HOST,
             "--port", str(self.port), "--log-level", "info"],
            cwd=str(self.tmp), env=env, stdout=self.handle, stderr=subprocess.STDOUT,
        )
        deadline = time.time() + 40
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("uvicorn exited: "
                                   + self.log.read_text(errors="replace")[-2000:])
            try:
                c = http.client.HTTPConnection(HOST, self.port, timeout=1.0)
                c.request("GET", "/v1/health")
                if c.getresponse().status == 200:
                    c.close()
                    return {"pid": self.proc.pid, "port": self.port, "cwd": str(self.tmp)}
                c.close()
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("uvicorn did not open the port within 40s")

    def rss_kb(self) -> int:
        for line in Path(f"/proc/{self.proc.pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
        return -1

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.handle.close()


def day_bounds(days: int) -> str:
    """A from/to query string covering `days` UTC days ending today."""
    today = datetime.now(UTC).date()
    return f"from={(today - timedelta(days=days - 1)).isoformat()}&to={today.isoformat()}"


def fingerprint(path: Path) -> dict:
    import hashlib

    st = path.stat()
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "mtime_ns": st.st_mtime_ns, "size": st.st_size}


def hold_exclusive_lock(db_path: Path, seconds: float) -> subprocess.Popen:
    """A second process holding BEGIN EXCLUSIVE on the store (IR-1's condition)."""
    script = ("import sqlite3,sys,time\n"
              "c=sqlite3.connect(sys.argv[1])\n"
              "c.execute('BEGIN EXCLUSIVE')\n"
              "print('held', flush=True)\n"
              "time.sleep(float(sys.argv[2]))\n"
              "c.rollback(); c.close()\n")
    env = dict(os.environ)
    env.pop("APPIMAGE", None)
    return subprocess.Popen([sys.executable, "-c", script, str(db_path), str(seconds)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)


def migration_lifecycle(tmp: Path) -> dict:
    """Statement counts per init_db path, traced on the connection init_db opens."""
    import app.db as db
    from tests.test_migration_indexes import (EXPECTED_INDEXES, V3_DDL, _INSERT,
                                              _PROBABILITIES, _V3_ROWS)

    captured: list[str] = []
    original = db.connect

    def traced_connect(p):
        conn = original(p)
        conn.set_trace_callback(captured.append)
        return conn

    db.connect = traced_connect
    try:
        fresh = tmp / "create.db"
        captured.clear(); db.init_db(fresh)
        create = [s.strip() for s in captured if s.strip()]
        v3 = tmp / "v3.db"
        c = sqlite3.connect(v3)
        c.execute(V3_DDL)
        c.executemany(_INSERT, [(r[0], r[1], _PROBABILITIES, *r[2:]) for r in _V3_ROWS])
        c.commit(); c.close()
        captured.clear(); db.init_db(v3)
        migrate = [s.strip() for s in captured if s.strip()]
        captured.clear(); db.init_db(v3)
        rerun = [s.strip() for s in captured if s.strip()]
        c = sqlite3.connect(v3)
        c.row_factory = sqlite3.Row
        rows = [dict(r) for r in c.execute("SELECT * FROM analyses ORDER BY id")]
        cols = [r[1] for r in c.execute("PRAGMA table_info(analyses)")]
        version = c.execute("SELECT value FROM schema_meta WHERE key='version'").fetchone()[0]
        names = sorted(r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"))
        c.close()
    finally:
        db.connect = original

    return {"create_statements": len(create), "migrate_statements": len(migrate),
            "rerun_statements": len(rerun), "rows_preserved": len(rows),
            "columns_after": cols, "schema_version_after": version,
            "named_indexes_exact": sorted(EXPECTED_INDEXES) == names}


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="perfval-"))
    port = 8971
    results = {"generated_at": datetime.now(UTC).isoformat(), "repo": str(REPO),
               "python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version,
               "uvicorn_port": port, "budget_ms": BUDGET_MS, "scenarios": []}

    results["migration_lifecycle"] = migration_lifecycle(tmp / "mig")
    db_path = tmp / "data" / "sentiment.db"
    results["fixture"] = seed_pinned_store(db_path)
    store_before = fingerprint(db_path)

    server = Server(tmp, port)
    results["server"] = server.start()
    try:
        # S1 -- baseline sequential
        for ep, label in (("/v2/analytics/summary", "summary"),
                          ("/v2/analytics/terms", "terms")):
            results["scenarios"].append(run_scenario(
                port, f"S1-sequential-baseline-{label}", 1, 200,
                lambda w, r, e=ep: e,
                note="NFR1.1/NFR1.2 budget shape: 200 consecutive requests, no concurrency",
                warmup=5))

        # S2 -- concurrency ramp on /summary
        for c in (1, 2, 4, 8, 16, 32, 64):
            results["scenarios"].append(run_scenario(
                port, f"S2-ramp-summary-c{c}", c, 240,
                lambda w, r: "/v2/analytics/summary",
                note=f"concurrency ramp, {c} concurrent clients, 240 requests total", warmup=3))

        # S3 -- mixed, what one page load actually issues
        paths = ("/v2/analytics/summary", "/v2/analytics/terms")
        results["scenarios"].append(run_scenario(
            port, "S3-mixed-summary-and-terms-c8", 8, 240,
            lambda w, r: paths[(w + r) % 2], note="interleaved summary+terms", warmup=4))

        # S4/S5 -- range-width ladder on both endpoints
        for ep, label in (("/v2/analytics/summary", "summary"),
                          ("/v2/analytics/terms", "terms")):
            for days in (7, 365, 3650, 36500):
                q = day_bounds(days)
                results["scenarios"].append(run_scenario(
                    port, f"S4-width-{label}-{days}d", 1, 15,
                    lambda w, r, p=ep, qq=q: f"{p}?{qq}",
                    note=f"range width ladder, {days} UTC days", warmup=2))

        # S6 -- the unbounded payload, repeated (IR-7)
        for name, ep in (("S6-unbounded-100y-summary", "/v2/analytics/summary"),
                         ("S6b-unbounded-100y-terms", "/v2/analytics/terms")):
            results["scenarios"].append(run_scenario(
                port, name, 1, 25, lambda w, r, p=ep: f"{p}?" + day_bounds(36500),
                note="100-year range on the 10k/365-day store", warmup=2))

        # S7 -- memory growth with series length
        rss_before = server.rss_kb()
        for _ in range(10):
            c = http.client.HTTPConnection(HOST, port, timeout=30)
            hit(c, "/v2/analytics/summary?" + day_bounds(36500))
            c.close()
        results["memory_growth"] = {"rss_kb_before_wide_payloads": rss_before,
                                    "rss_kb_after_10_wide_payloads": server.rss_kb()}
        time.sleep(2)
        results["memory_growth"]["rss_kb_after_gc_settle"] = server.rss_kb()

        # S8 -- health during analytics load
        bg: list = []

        def bg_worker() -> None:
            bc = http.client.HTTPConnection(HOST, port, timeout=30)
            for _ in range(60):
                s = hit(bc, "/v1/health", timeout=30)
                bg.append(s)
                if s.error:
                    bc = http.client.HTTPConnection(HOST, port, timeout=30)
            bc.close()

        bg_thread = threading.Thread(target=bg_worker, daemon=True)
        results["scenarios"].append(run_scenario(
            port, "S8-analytics-c8-with-health-probe", 8, 240,
            lambda w, r: "/v2/analytics/summary",
            note="240 concurrent reads with a parallel /v1/health probe", warmup=2,
            background=("/v1/health", bg_thread)))
        results["health_during_load"] = dist([s.ms for s in bg])

        # S9 -- refusal pays no read cost
        for label, fn in (("valid-unbounded", lambda w, r: "/v2/analytics/summary"),
                          ("refused-422-inverted-range",
                           lambda w, r: "/v2/analytics/summary?from=2026-10-03&to=2026-01-01"),
                          ("refused-422-unreadable-bound",
                           lambda w, r: "/v2/analytics/summary?from=not-a-date")):
            results["scenarios"].append(run_scenario(
                port, f"S9-{label}", 1, 120, fn,
                note="refused request must cost no read (BR1.4)", warmup=3))

        # S10 -- writer contention, then recovery
        holder = hold_exclusive_lock(db_path, 16)
        holder.stdout.readline()
        results["writer_lock_held"] = "held"
        results["scenarios"].append(run_scenario(
            port, "S10-writer-lock-contention-c6", 6, 6,
            lambda w, r: "/v2/analytics/summary",
            note="a second process holds BEGIN EXCLUSIVE; 6 readers race it",
            warmup=0, timeout=25.0))
        holder.wait(timeout=30)
        results["scenarios"].append(run_scenario(
            port, "S10b-writer-lock-released-c6", 6, 12,
            lambda w, r: "/v2/analytics/summary",
            note="same workload immediately after the lock is released",
            warmup=0, timeout=25.0))

        # S11 -- soak at the knee
        results["scenarios"].append(run_scenario(
            port, "S11-soak-c8-2000-requests", 8, 2000,
            lambda w, r: paths[(w + r) % 2], note="sustained mixed load", warmup=2))
    finally:
        after = fingerprint(db_path)
        results["store_fingerprint_after_load"] = after
        results["store_byte_identical_across_load"] = after["sha256"] == store_before["sha256"]
        results["store_mtime_identical_across_load"] = after["mtime_ns"] == store_before["mtime_ns"]
        server.stop()

    (OUT / "load-results.json").write_text(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
```

### `loadgen2.py` — attribution, control and reproducibility

The second harness differs from the first in one decisive way: it reads
**`/proc/<pid>/stat` `utime + stime`** for both the server and the client around
every scenario, and it drives `/v1/health` — a request that never touches the
store — at the same concurrencies. Its core:

```python
def cpu_ticks(pid: int) -> int:
    """utime + stime for `pid`, in clock ticks."""
    f = Path(f"/proc/{pid}/stat").read_text()
    parts = f[f.rindex(")") + 2 :].split()
    return int(parts[11]) + int(parts[12])          # fields 14 and 15


def proc_state(pid: int) -> dict:
    txt = Path(f"/proc/{pid}/status").read_text()
    out = {"threads": 0, "rss_kb": -1}
    for line in txt.splitlines():
        if line.startswith("Threads:"):
            out["threads"] = int(line.split()[1])
        elif line.startswith("VmRSS:"):
            out["rss_kb"] = int(line.split()[1])
    out["fds"] = len(os.listdir(f"/proc/{pid}/fd"))   # BR6.1's connection lifecycle
    return out


def drive(port, pid, name, concurrency, total, path_fn, note="", warmup=3):
    """Drive `total` requests at `concurrency`, attributing CPU to server and client."""
    samples, lock = [], threading.Lock()
    per = [total // concurrency] * concurrency
    for i in range(total % concurrency):
        per[i] += 1

    def worker(w):
        conn = http.client.HTTPConnection(HOST, port, timeout=60)
        loc = []
        try:
            for r in range(per[w]):
                t0 = time.perf_counter()
                try:
                    conn.request("GET", path_fn(w, r))
                    resp = conn.getresponse()
                    body = resp.read()
                    loc.append(((time.perf_counter() - t0) * 1000.0, resp.status,
                                len(body), None))
                except Exception as exc:  # noqa: BLE001
                    try:
                        conn.close()
                    except Exception:
                        pass
                    conn = http.client.HTTPConnection(HOST, port, timeout=60)
                    loc.append(((time.perf_counter() - t0) * 1000.0, None, 0,
                                f"{type(exc).__name__}: {exc}"))
        finally:
            try:
                conn.close()
            except Exception:
                pass
        with lock:
            samples.extend(loc)

    if warmup:
        wc = http.client.HTTPConnection(HOST, port, timeout=60)
        for _ in range(warmup):
            wc.request("GET", path_fn(0, 0)); wc.getresponse().read()
        wc.close()

    s_cpu0, c_cpu0, st0 = cpu_ticks(pid), cpu_ticks(os.getpid()), proc_state(pid)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(worker, range(concurrency)))
    wall = time.perf_counter() - t0
    s_cpu = (cpu_ticks(pid) - s_cpu0) / CLK          # CLK = os.sysconf("SC_CLK_TCK")
    c_cpu = (cpu_ticks(os.getpid()) - c_cpu0) / CLK
    st1 = proc_state(pid)
    ok = [s for s in samples if s[1] == 200]
    return {
        "scenario": name, "note": note, "concurrency": concurrency,
        "requested": total, "completed": len(samples), "wall_s": round(wall, 4),
        "rps": round(len(samples) / wall, 2),
        "status_counts": dict(Counter(str(s[1]) for s in samples)),
        "transport_errors": sum(1 for s in samples if s[3]),
        "server_cpu_s": round(s_cpu, 3),
        "server_cpu_utilisation": round(s_cpu / wall, 3),
        "client_cpu_s": round(c_cpu, 3),
        "client_cpu_utilisation": round(c_cpu / wall, 3),
        "server_fds_before": st0["fds"], "server_fds_after": st1["fds"],
        "server_rss_kb_after": st1["rss_kb"],
        "latency_all": dist([s[0] for s in samples]),
        "latency_200_only": dist([s[0] for s in ok]) if ok else None,
        "bytes_median": sorted(s[2] for s in ok)[len(ok) // 2] if ok else None,
    }
```

Its `main()` runs `C1` (the `/v1/health` control at `c` = 1, 8, 32), `C2` (an
independent ramp), `C3` (the mixed load twice), `C4` (`/terms` alone at `c` = 8),
`C5` (`/summary` alone at `c` = 8), `C6` (a 3 000-request mixed soak), plus the
migration statement counts and the server's `/proc` state at boot and after load.
The full file is 300 lines of the same primitives shown above.

### `loadgen3.py` — statement counts and the failure shapes

```python
def shape(s: str) -> str:
    """The traced statement with every bound value masked, so two widths compare equal."""
    import re as _re
    return _re.sub(r"'(?:[^']|'')*'", "?", " ".join(s.split()))


# P1: trace the connection the *application* opens, at four range widths.
real_connect = dbmod.connect

def traced(p):
    conn = real_connect(p)
    conn.set_trace_callback(captured.append)
    return conn

with application_started(app):
    dbmod.connect = traced
    try:
        for ep, tag in (("/v2/analytics/summary", "summary"),
                        ("/v2/analytics/terms", "terms")):
            for d in (7, 365, 3650, 36500):
                q = day_bounds(d)
                r = asyncio.run(_serve(app, "GET", ep, q, b"", None))
                stmts = [s.strip() for s in captured if s.strip()]
                # -> statement_count == 1 at every width, and shape() identical
                captured.clear()
    finally:
        dbmod.connect = real_connect
```

`P3` then starts a real `uvicorn` on the seeded store, holds `BEGIN EXCLUSIVE`
from a second process for 9 s, and captures the wire status, the envelope body and
the server's own log lines for both endpoints — plus `/v1/health` during the
failure and the response after release.
