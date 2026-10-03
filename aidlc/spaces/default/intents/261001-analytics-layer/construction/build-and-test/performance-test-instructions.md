# Performance Test Instructions — intent `261001-analytics-layer`, Unit `u1-analytics-slice`

> **Stage:** `build-and-test` (construction) · **Test strategy:** `standard`
> (this file exists because measurable performance NFRs exist —
> `nfr-requirements/performance-requirements.md` and
> `nfr-requirements/scalability-requirements.md` define `NFR1.1`–`NFR1.4` and
> `NFR9.1`–`NFR9.4`) · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer`
>
> **Inputs this file was derived from** (the stage's declared `consumes`):
> `construction/u1-analytics-slice/code-generation/code-generation-plan.md` ·
> `construction/u1-analytics-slice/code-generation/unit-test-instructions.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md`, plus
> `construction/u1-analytics-slice/nfr-requirements/performance-requirements.md`,
> `…/scalability-requirements.md` and `construction/u1-analytics-slice/nfr-design/performance-design.md`,
> `…/scalability-design.md`.

## 1. Framework and configuration

`pytest`, as everywhere in this repository (`pyproject.toml`
`[tool.pytest.ini_options]`). **There is no `pytest-benchmark`, no `locustfile`, no
k6 script and no load generator** — and none is added here, for a reason stated in
§6 rather than assumed.

**The one non-default rule: the budget is never measured inside an instrumented
run.** `addopts` applies `--cov` on *every* invocation, and coverage instrumentation
inflates wall time, so a budget measured inside the suite would describe the harness
rather than the application (`BR3.6`, `AC8.1.4`). `tests/test_analytics_read.py`
therefore spawns `[sys.executable, "-c", scenario, tmp_path]` — a **separate
interpreter with no pytest and therefore no coverage plugin** — seeds the fixture
there, drives both endpoints end to end through the real ASGI application, and prints
the measurements as JSON.

> **`env -u APPIMAGE` is mandatory.** That subprocess is spawned with
> `sys.executable`. On this host the shell exports
> `APPIMAGE=…opencode-desktop-linux-x86_64.AppImage`, which makes CPython report the
> AppImage as `sys.executable`; the spawn then fails with exit code 130 and the test
> fails for an environmental reason. Proof and remedy: `build-instructions.md` §6.

## 2. The target being measured

| Property | Value | Source |
|---|---|---|
| Budget | **200 ms per request** — the single stated latency target | `NFR1` / `NFR1.1`, `NFR1.2` |
| Workload | **10,000 stored analyses pinned to span exactly 365 distinct UTC days** | `NFR1.1` |
| Endpoints | `GET /v2/analytics/summary`, `GET /v2/analytics/terms` | `NFR1.1`, `NFR1.2` |
| Statement count | **Independent of how many days the resolved range covers** | `NFR1.3`, `NFR9.4` |
| Series length | **Bounded by the resolved range, not the store** — exactly 365 entries for the unbounded request over 10,000 rows | `NFR1.4`, `NFR9.1` |
| Terms payload | At most `limit` (default 10) entries **per list** | `NFR9.2` |
| There is **no RPS target** | The store is a single-user local SQLite file (`NFR9`); "throughput" here means bounded work per request | `scalability-requirements.md` § Load profile |
| There is **no SLO** | No hosted service, no multi-user load, no 30-day window | `observability-requirements.md` § SLI/SLO |

**The 365-day span is part of the target, not a construction detail.** Because the
series length equals the days in the resolved range (`NFR9.1`) and the unbounded
series is deliberately uncapped (`NFR9.3`), the in-process fill work the budget
measures is a direct function of that span. Pinning it makes the measured work a
fixed, stated quantity, so a fixture concentrated in one week and one spread over
years cannot silently produce different numbers.

## 3. How to run the performance tests

All commands run from the repository root.

### 3.1 The latency budget — `NFR1.1`, `NFR1.2`

```bash
env -u APPIMAGE python -m pytest --no-cov -p no:cacheprovider -v \
  "tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget"
```

One test asserts three things at once: both endpoints answer `200`, both answer
inside the budget, and the unbounded summary's series length equals the fixture's
span.

### 3.2 The statement-count invariant — `NFR1.3`, `NFR9.4`

```bash
env -u APPIMAGE python -m pytest --no-cov -p no:cacheprovider -v \
  "tests/test_analytics_read.py::test_the_statement_count_does_not_grow_with_the_number_of_days"
```

A `sqlite3` trace hook counts statements for the same endpoint over a 7-day range and
a 365-day range against the same 10,000-row store and asserts the count is **constant**
in the number of days, and that the statement carries `GROUP BY`. This is the
observable form of "no query per day".

### 3.3 The series-extent invariant — `NFR1.4`, `NFR9.1`

```bash
env -u APPIMAGE python -m pytest --no-cov -p no:cacheprovider -v \
  "tests/test_analytics_read.py::test_the_unbounded_series_length_is_the_fixture_span_not_the_row_count"
```

Asserts 365 entries over 10,000 rows, the first and last dates, and that the series
totals sum to the row count — so the length follows the **range** and the work does
not follow the **store**.

### 3.4 The terms payload bound — `NFR9.2`

```bash
env -u APPIMAGE python -m pytest --no-cov -p no:cacheprovider -v \
  "tests/test_analytics_read.py::test_the_default_limit_is_ten_per_list_and_an_oversized_one_is_honoured" \
  "tests/test_analytics_read.py::test_a_label_with_no_rows_yields_an_empty_list_and_not_none"
```

### 3.5 All four in one go, and the recorded per-unit command

```bash
env -u APPIMAGE python -m pytest --no-cov -q tests/test_analytics_read.py

env -u APPIMAGE python -m pytest -q \
  tests/test_analytics_read.py tests/test_analytics_routes.py \
  tests/test_terms.py tests/test_migration_indexes.py --cov-fail-under=0
```

### 3.6 Print the raw measurements yourself

The test prints nothing on success. To read the actual milliseconds, run the same
scenario the test runs:

```bash
env -u APPIMAGE python - <<'PY'
import json, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, ".")
from tests.test_analytics_read import _TIMING_SCENARIO, FIXTURE_ROWS, FIXTURE_DAYS, BUDGET_MS
scenario = _TIMING_SCENARIO.format(root=str(Path.cwd()), rows=FIXTURE_ROWS, days=FIXTURE_DAYS)
out = subprocess.run([sys.executable, "-c", scenario, tempfile.mkdtemp()],
                     capture_output=True, text=True, timeout=280)
print("returncode", out.returncode)
print(out.stdout.strip().splitlines()[-1])
print("budget_ms", BUDGET_MS, "rows", FIXTURE_ROWS, "days", FIXTURE_DAYS)
PY
```

## 4. Measured results on this host

CPython 3.14.7, Linux x86_64, `127.0.0.1`, store on the local filesystem, **no
coverage instrumentation**, 10,000 rows over 365 distinct UTC days:

| Target | Expected | Measured | Verdict |
|---|---|---|---|
| `NFR1.1` summary latency | `< 200 ms` | **15.24 ms** (HTTP `200`) | headroom 92 % |
| `NFR1.2` terms latency | `< 200 ms` | **25.04 ms** (HTTP `200`) | headroom 87 % |
| `NFR1.3` statement count | constant in days | **1** over 7 days and **1** over 365 days, and the statement carries `GROUP BY` | constant |
| `NFR1.4` series length | 365 over 10,000 rows | **365** entries; `total` 10,000; series sums to 10,000 | exact |
| `NFR9.2` terms payload | ≤ `limit` per list | default **10** per list; an oversized `limit` is honoured, never clamped | holds |

Raw JSON from §3.6, verbatim:

```json
{"summary": [15.241942000102426, 200], "terms": [25.04308499965191, 200], "series_length": [0.0, 365]}
```

**How to read this number, honestly.** It is a **single cold measurement on one
machine with no concurrency**, not a percentile over a sustained load. The targets
that exist (`NFR1.1`–`NFR1.4`) are exactly that shape — a single stated budget over
a pinned fixture — so this measurement satisfies them as written. It does **not**
establish p95/p99 behaviour, and nothing in the source inventory asks it to. If a
later stage wants percentiles, that is a new target with a new instrument, not
something this file may read into an existing one.

## 5. Expected coverage for this strategy level

The performance tests contribute to the **whole-application 80 % line floor** and are
counted in it; they do not carry a separate coverage target. Measured on the whole
suite: `app/analytics.py` **100 %** (112 stmts, 0 missed), `app/terms.py` **100 %**
(11 stmts, 0 missed), whole application **97.06 %**.

Two consequences to keep in view:

* `--no-cov` in §3.1–§3.5 is a **speed** choice for a targeted rerun, not a coverage
  exemption. The gate run is the whole suite, which carries the floor.
* Coverage says **nothing** about whether the aggregates are *correct*. `team.md`
  records why this feature's tests were written the way they were: there is no `AVG(`,
  no `GROUP BY`, no `strftime(` and no `json_extract` anywhere in the codebase before
  this Unit, so the pre-existing 96 % figure could not have detected a `strftime`
  bucket boundary off by one day at the UTC edge. The defence is the hand-written
  expected values — `test_the_summary_aggregates_are_the_hand_computed_values` and
  its API-level siblings — **not** the coverage number. The coverage floor is not a
  substitute for either.

## 6. Test data and environment setup

| Concern | Arrangement |
|---|---|
| Fixture | `tests/test_analytics_read.py::_performance_store` — 10,000 rows, `created_at` pinned to `index % 365` days back from today at `12:00:00Z`, labels rotating over all three, confidence cycling `0.00`–`0.99`, `import_id` `NULL` |
| Location | `tmp_path` — the same store is never reused, and nothing is left behind |
| Determinism | The unbounded case resolves against a `today` seam that tests pin, so the result does not depend on the wall clock |
| Coverage instrumentation | **Excluded from the measurement** — the timing runs in a subprocess with no pytest and no `pytest-cov` |
| Network | None. The offline guard is armed; the read path is in-process by design (`BR2.8`) |
| Concurrency | Not part of the latency measurement. Overlapping requests are a *correctness* instrument (`NFR4.6` is not among them; see §7) and live in `tests/test_analytics_routes.py` |
| Load generator | **None installed and none needed** — see §7 |

## 7. What is deliberately absent, and why

Recording the absences is the point; a load-testing paragraph that quietly implied
coverage would be worse than none.

| Standard practice | Applies? | Why not |
|---|---|---|
| `locust` / `k6` / `artillery` load test | **No** | There is no RPS target to hit. The store is a single-user local SQLite file (`NFR9`); a virtual-user model would measure the load generator. |
| Ramp-up / steady-state / spike / soak | **No** | All four presuppose a multi-user service. `NFR9`'s framing is *bounded work*, not throughput. |
| p50/p95/p99 percentiles | **No** | The requirement states a single 200 ms budget over a pinned fixture. Introducing percentiles would be inventing a target. |
| Auto-scaling validation | **No** | No hosted tier, no autoscaler, no queue (`scalability-design.md` §3). |
| Cache / pool / prepared-statement reuse | **No** | A local file read once per request (`A2`). Each would add an invalidation surface for no measured gain — the accepted NFR-design assessment reached this conclusion and this file records it rather than re-opening it. |

The concurrency posture is a **failure-behaviour** constraint, not a performance
target: two genuinely overlapping requests must raise no cross-thread connection error
and must not serialise behind a per-request schema re-initialisation. It has no
inception NFR parent (it traces to `FR1.6`, `BR6.3`, `FR8.4`) and is pinned by
`tests/test_analytics_routes.py::test_two_overlapping_analytics_requests_never_raise_a_cross_thread_error`
plus `::test_the_driver_opens_connections_that_may_be_used_and_closed_on_another_thread`.
Measured: both `200`, and the driver instrument goes red with
`ProgrammingError('SQLite objects created in a thread can only be used in that same
thread…')` when `check_same_thread` is reverted.

## 8. What is deferred to a later stage, and what is not

**Nothing in the performance inventory is deferred.** All of `NFR1.1`–`NFR1.4` and
`NFR9.1`–`NFR9.4` are executable on a developer machine and were executed here (§4).
The deferral clause in the stage definition requires a deployed or production-like
environment, and no performance target in this Unit has that requirement.

The later stage `performance-validation` in the Operation phase (`4.7`) is the right
home for a **production-like** exercise — real data volume, a sustained window, an
auto-scaling check — but **no target in this inventory is assigned to it**, so no
target's verdict depends on it and nothing is deferred on its account. If a future
scope adds a percentile or throughput target, that target should name
`performance-validation` as its owning stage at the moment it is written.