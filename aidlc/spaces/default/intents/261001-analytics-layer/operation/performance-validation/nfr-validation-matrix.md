# NFR Validation Matrix — intent `261001-analytics-layer`, stage `performance-validation`

> **Stage:** `performance-validation` (operation) · lead `aidlc-quality-agent`
> support `aidlc-operations-agent` · **Date:** 2026-10-03
> **Release under test:** commit `aa0b1e4`
> **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/operation/performance-validation`
>
> **Sources of the targets:** `performance-requirements.md` (`NFR1.1`–`NFR1.4`),
> `scalability-requirements.md` (`NFR9.1`–`NFR9.4`),
> `security-requirements.md` (`NFR2.1`–`NFR2.6`),
> `reliability-requirements.md` (`NFR3.1`–`NFR4.7`),
> `observability-requirements.md` (`NFR8.1`–`NFR8.3`), all under
> `construction/u1-analytics-slice/nfr-requirements/`, against the mechanisms
> declared in `performance-design.md`, `scalability-design.md` and
> `reliability-design.md` under `…/nfr-design/`. Measured results and the
> saturation baseline are in `test-results.md`; the plan is `load-test-plan.md`.
> `dashboards.md` Panel D and `alarms.md` §2.3/§2.4 carry the recorded thresholds
> these measurements are compared against.

## How to read this matrix

**No row is `Met` without a measurement, and every row states whose measurement
it is.** The `Evidence origin` column is not decoration:

| Origin | Meaning |
|---|---|
| **this stage** | Measured here, over real HTTP against a real `uvicorn`, or traced on the connection the application opens. The number is in `test-results.md` with its scenario id. |
| **carried** | Not this stage's instrument — a security or aggregate-correctness target with no latency or concurrency dimension. Build and Test measured it; the verdict is inherited with its evidence named, and **this stage neither claims nor disputes it**. |
| **n/a** | Not executable in this Bolt. The owning Unit is named. |

**Totals: 24 `Met` · 0 `Not Met` · 2 `Unverified` · 0 `N/A`.**
Of the 24 `Met`, **17 were measured by this stage** and 7 are carried.

## 1. Performance — `NFR1.1`–`NFR1.4`

| ID | Target | Measured actual | Scenario | Evidence origin | Verdict |
|---|---|---|---|---|---|
| **`NFR1.1`** | `/summary` answers **under 200 ms** over 10 000 rows / 365 distinct UTC days | **200/200 requests `200`.** min 10.883 · **p50 11.567** · **p95 12.645** · **p99 14.297** · **max 27.167 ms**. Throughput 85.14 rps. Headroom on the maximum: **86 %**. | `S1` | **this stage** | **Met** |
| **`NFR1.2`** | `/terms` answers **under 200 ms** over the same fixture, **without coverage instrumentation** | **200/200 requests `200`.** min 20.865 · **p50 22.128** · **p95 24.583** · **p99 35.899** · **max 41.394 ms**. Measured over HTTP from a separate `uvicorn` process with no pytest and no `--cov`. | `S1` | **this stage** | **Met** |
| **`NFR1.3`** | statement count **independent of the range's day count** | **`SELECT` count = 1 at 7, 365, 3 650 and 36 500 days.** The masked statement text is byte-identical at all four widths. | `P1` | **this stage** | **Met** |
| **`NFR1.4`** | unbounded summary returns **exactly 365 entries** over 10 000 rows | **365** entries; `total` **10 000**; the series sums to **10 000**; first `2025-10-04`, last `2026-10-03`; **1 statement**. | `P1` | **this stage** | **Met** |

> **Two caveats stated on the rows rather than hidden in a footnote.**
> **(a)** At `c` = 8 concurrency, one of 240 `/summary` requests in run 2 took
> **206.004 ms** — 0.4 % over the budget (`S2`, `C2`). `NFR1.1` states no
> concurrency condition, and `performance-requirements.md` § "Concurrency posture"
> states the load profile is a single client with **no RPS target**, so the target
> is met **as written**. The observation is recorded because a reader deciding
> what concurrency this system may see needs it.
> **(b)** The two figures Build and Test recorded (`summary` 15.24 ms / `terms`
> 25.04 ms) sit **inside** the distributions measured here, confirming they were
> single draws from these distributions rather than outliers.

## 2. Scalability — `NFR9.1`–`NFR9.4`

| ID | Target | Measured actual | Scenario | Evidence origin | Verdict |
|---|---|---|---|---|---|
| **`NFR9.1`** | series length **equals** the UTC days in the resolved range; an empty range returns an empty series | Series length **7 / 365 / 3 650 / 36 500** at the four requested widths — equal to the requested day count at every one. An unmatched range returns **`series: []`, `total: 0`**, every share `null`, `mean_confidence: null`, `mean_confidence_row_count: 0`. | `P1`, `S4` | **this stage** | **Met** |
| **`NFR9.2`** | no response grows with the store; at most `limit` entries **per list** | Over the **10 000-row** store: `limit=1` → **1 per list** (102 B); `limit=10`, `100` and `5000` → **7 per list** (536 B) each — the store holds 7 distinct significant terms, so an oversized limit is honoured, never clamped to 10 and never padded. At a **100-year** range the response is **479 B / p50 24.731 ms**, flat against its 365-day figure of 479 B / 24.686 ms. | `P1`, `S4′`, `S5′` | **this stage** | **Met** |
| **`NFR9.3`** | the unbounded series is **capped by nothing, deliberately** | No cap imposed, and the measurement proves the absence is real: a **100-year** range returns **36 500 series entries / 7 011 966 wire bytes / p50 186.541 ms / p99 199.700 ms**, `total` still 10 000. 36 500 days was requested and 36 500 entries were returned. | `S5`, `S6`, `P1` | **this stage** | **Met** |
| **`NFR9.4`** | statement count does not grow with the range span | **`SELECT` count = 1 at all four widths**, 7 → 36 500 days, on both endpoints. Same instrument as `NFR1.3`. | `P1` | **this stage** | **Met** |

> **`NFR9.3` carries a live capacity risk, and the matrix does not hide it inside a
> `Met`.** At 7 011 966 B and a p99 of 199.700 ms the unbounded payload lands
> **0.3 ms inside** the 200 ms budget on this host; `runbooks.md` IR-7 recorded 4
> of 5 repeats *over* budget on the same host and `dashboards.md` Panel D recorded
> 235 ms. The requirement is met because it asks for **no cap**, and imposing one
> would contradict it. The risk is recorded as finding `F-4` in `test-results.md`
> §15 and as an open question in `performance-validation-questions.md` Q8.

## 3. Read-only guarantee — `NFR3.1`–`NFR3.2`

| ID | Target | Measured actual | Scenario | Evidence origin | Verdict |
|---|---|---|---|---|---|
| **`NFR3.1`** | **no write, no schema change, no access bookkeeping** | The load store's `sha256`, `mtime_ns` and `size` are **identical** before and after the entire scenario sequence — including **3 000 concurrent reads, a 100-year range, and a competing `EXCLUSIVE` writer**. The repository's own `data/sentiment.db` is byte- **, mtime- **, inode- **and size-identical** (`c8be1361…`, `2026-10-03 03:33:42.920985500 +0500`, 32 768 B, inode 854420). An unchanged mtime proves the file was never opened for writing. | §7, §13 | **this stage** | **Met** |
| **`NFR3.2`** | **no mutating statement** of any kind in the read path | The traced read statement is a single `SELECT … GROUP BY` with two bound parameters, identical at every width. The store did not change under 3 000+ concurrent reads. | `P1`, §7 | **this stage** | **Met** |

## 4. Distinguishable failures — `NFR4.1`–`NFR4.7`

| ID | Target | Measured actual | Scenario | Evidence origin | Verdict |
|---|---|---|---|---|---|
| **`NFR4.1`** | `422` naming its own field; inverted range names **both**; **nothing computed** | **120 `422`** for the inverted range and **120 `422`** for the unreadable bound. Envelope exactly `{"code","message"}`; messages `"query.from: expected a UTC calendar date written YYYY-MM-DD."` and `"query.from and query.to: 'from' must not be a later UTC day than 'to'."`. **`limit=0` refused the same way.** **Zero statements issued** for every refusal, against 1 for a valid read — the design claim that validation precedes computation, measured. p50 **0.746** and **0.716 ms** versus **10.846 ms** valid. | `S9`, `P1` | **this stage** | **Met** |
| **`NFR4.2`** | storage failure is **`500 STORAGE_FAILURE`**, distinct from every validation code | Under a competing `BEGIN EXCLUSIVE` holder: `/summary` → **`500`**, body `{"code":"STORAGE_FAILURE","message":"The analytics store could not answer the request."}`, after **5 007.7 ms**. **6 of 6** concurrent reads returned `500` at p50 **5 007.942 ms** / max **5 009.235 ms** — the 5.0 s `busy_timeout`, since `app/db.py:213` sets none. Distinct from `VALIDATION_FAILED` in both code and status. | `S9`, `P3` | **this stage** | **Met** |
| **`NFR4.3`** | a failed request **never renders as a plausible-looking empty result** | Three structurally distinct shapes observed over real HTTP: **empty success** (`200`, `total: 0`, `series: []`, every share `null`, mean `null`), **validation failure** (`422`, per-field message), **storage failure** (`500`, `STORAGE_FAILURE`). **No `404`** was produced for emptiness in any run. | `S9`, `P1`, `P3` | **this stage** | **Met** |
| **`NFR4.4`** | refuse-never-substitute for **every** `null` | **Partially re-measured here:** the empty-success response carries `shares: {positive: null, negative: null, neutral: null}`, `mean_confidence: null`, `mean_confidence_row_count: 0` — the refuse-never-substitute shape observed on a real response rather than asserted. The exact half-up tie (`36/128 → 0.2813`) is an aggregate-correctness property with no latency or concurrency dimension and was **not** re-measured. | `P1` | **this stage** (null shape) / **carried** (tie rounding) | **Met** |
| **`NFR4.5`** | additive migration **idempotent, row-preserving**, loud rollback | **10** statements on create, **11** on migrate (including the one `PRAGMA foreign_keys = ON` `app.db.connect` issues; 9 and 10 excluding it), **11** on re-run. **2 of 2 rows preserved**, all **10** columns including the retired `intensity`; `version 3 → 4`; the three named indexes present exactly. **The re-run leaves the store byte-identical *and* mtime-identical** — an unchanged mtime proves it was never opened for writing. | `M1` | **this stage** | **Met** |
| **`NFR4.6`** | **per-section graceful degradation**: one section succeeding while another fails shows the successful section **plus a partial-failure marker** | **Not executable in this Bolt.** The named instruments `AC6.5.3` / `AC6.5.5` require a **second analytics section**, whose two term-list containers are `u3-analytics-view`'s deliverable. The markup does not exist here. **No instrument was manufactured against it.** The *participating* half remains delivered: summary / empty / error are three distinct regions, and a failed fetch renders in place (`app/static/index.html`, `tests/test_page.py`). **Owner: `u3-analytics-view`**, verified in that Unit's own code-generation and build-and-test pass. | — | **n/a** | **Unverified** |
| **`NFR4.7`** | **no silent retry**; an out-of-order late response from a superseded range is **discarded** | **Not executable in this Bolt.** The named instrument `AC6.5.2` requires a **date-range control** to supersede, which is `u3-analytics-view`'s deliverable. The *participating* half is delivered and asserted: exactly one summary fetch, no retry (`tests/test_page.py`). **Owner: `u3-analytics-view`**, same pass. | — | **n/a** | **Unverified** |

> **`NFR4.6` — the trap this stage walked past, named.** In `P3` a genuine partial
> outcome appeared: `/terms` waited out the same `EXCLUSIVE` lock inside its own
> 5 s budget and answered `200` while `/summary` had already answered `500`. **That
> is not the `NFR4.6` instrument.** `NFR4.6` requires a **view-level partial-failure
> marker** so an operator can see two sections disagreeing about the range. A
> storage-layer timing accident produces no marker, is invisible to the user, and
> is not reproducible on demand. Recording it as progress on `NFR4.6` would be
> precisely the claim that leaving the target `Unverified` prevents.
>
> **Both rows are unchanged from Build and Test and are not improved by this
> stage.** The same halt-and-ask was put to the human there and option **A**
> (carry both as `Unverified` into `u3-analytics-view`) was chosen. Building the
> markup here was re-examined and remains wrong: it duplicates `u3-analytics-view`
> and repeats the `app/terms.py` boundary violation three review passes disclosed.

## 5. Logging — `NFR8.1`–`NFR8.3`

| ID | Target | Measured actual | Scenario | Evidence origin | Verdict |
|---|---|---|---|---|---|
| **`NFR8.1`** | every application-raised failure reaches the **module logger** | Captured verbatim from a live `uvicorn` process: `ERROR:     analytics summary read failed (STORAGE_FAILURE): database is locked`. | `P3` | **this stage** | **Met** |
| **`NFR8.2`** | the machine code travels on the envelope **and** appears in the log | Three surfaces agreed on one failure: envelope `{"code":"STORAGE_FAILURE",…}`, module logger `… (STORAGE_FAILURE): database is locked`, access line `"GET /v2/analytics/summary HTTP/1.1" 500 Internal Server Error`. | `P3` | **this stage** | **Met** |
| **`NFR8.3`** | no parameter interpolated into statement text; no credential in any log record | The traced read statement is one module constant with two `?` placeholders, **byte-identical at 7, 365, 3 650 and 36 500 days** once bound values are masked — so no bound ever reaches statement text. The captured log lines carry no parameter, no path and no credential. | `P1`, `P3` | **this stage** | **Met** |

## 6. Security — `NFR2.1`–`NFR2.6`

| ID | Target | Verdict basis | Evidence origin | Verdict |
|---|---|---|---|---|
| **`NFR2.1`** | no authentication and no authorization added; posture unchanged | `tests/test_analytics_read.py::test_v1_routes_are_untouched_by_the_v2_surface`; `test_auth_routes.py` (12) + `test_session_auth.py` (12) — `build-and-test/test-results.md` §5. **Not a latency or concurrency dimension; not re-measured here.** | carried | **Met** |
| **`NFR2.2`** | no new egress path | 0 forbidden imports across the three read-path modules against a 12-module denylist; the offline guard proved to fire — `security-test-instructions.md` §3.1. **This stage's harness made no outbound network call** (loopback only), which corroborates but does not re-establish it. | carried | **Met** |
| **`NFR2.3`** | all SQL parameter-bound; nothing interpolated | Build and Test's 40 injection probes → `422`/`200`, never `500`. **Independently corroborated here:** the traced statement carries `?` placeholders at every range width (`P1`). | carried + **this stage** | **Met** |
| **`NFR2.4`** | loopback bind enforced at startup | `create_app(host="0.0.0.0")` → `NonLoopbackBindError` — `build-and-test` §5. **Noted, not re-measured:** this stage invoked `uvicorn --host 127.0.0.1`, a loopback value, so `alarms.md` §3.1's CLI bypass created no exposure. | carried | **Met** |
| **`NFR2.5`** | no credential added anywhere | 0 credential-shaped literals in `app/`; redaction assertions green — `build-and-test` §5. **Corroborated here:** this stage's `uvicorn` processes ran in offline mode with no credential present, and the captured log lines contain none. | carried + **this stage** | **Met** |
| **`NFR2.6`** | within the privacy and localhost-only rules; runtime dependency list unchanged | `pyproject.toml` byte-identical to the Bolt 1 commit; dependency-cap assertion passes. **Enforced by this stage:** the harness is standard-library only and added no entry to `pyproject.toml` — `git diff --stat HEAD -- pyproject.toml` is empty. | carried + **this stage** | **Met** |

## 7. Tally

| Verdict | Count | IDs |
|---|---|---|
| **Met** | **24** | `NFR1.1` `NFR1.2` `NFR1.3` `NFR1.4` · `NFR2.1` `NFR2.2` `NFR2.3` `NFR2.4` `NFR2.5` `NFR2.6` · `NFR3.1` `NFR3.2` · `NFR4.1` `NFR4.2` `NFR4.3` `NFR4.4` `NFR4.5` · `NFR8.1` `NFR8.2` `NFR8.3` · `NFR9.1` `NFR9.2` `NFR9.3` `NFR9.4` |
| **Not Met** | **0** | — |
| **Unverified** | **2** | **`NFR4.6`**, **`NFR4.7`** — both owned by `u3-analytics-view` |
| **N/A** | **0** | — an applicable target may never use it, and the inventory found applicable targets |

**Of the 24 `Met`: 17 were measured by this stage, 7 are carried** with Build and
Test's evidence named. **Same tally as Build and Test (24 / 0 / 2), reached
independently and from different instruments** — Build and Test from a
single-request in-process budget test, this stage from 5 000+ concurrent requests
over real HTTP plus a traced statement-count probe.

## 8. Requirements with no measurable target, and why

Recorded so the matrix's completeness is auditable rather than assumed.

| Item | Why it carries no row |
|---|---|
| `NFR5`, `NFR6`, `NFR7` | Declared `N/A` upstream as invariants with no sub-numberable value (`build-and-test/test-results.md` §5). Not applicable measurable targets. |
| The **concurrency constraint** | **No inception NFR parent.** It traces to `FR1.6`, `BR6.3`, `FR8.4` — functional, not performance. `performance-requirements.md` § "Concurrency posture" states this explicitly and declines to sub-number it, because hanging a `NFRx.y` id on it would invent a parent the inception set does not contain. Its behaviour **was** measured (`test-results.md` §3, §15 `F-1`) and **is** held by `FR8.4`, which Build and Test recorded `Met`. |
| **Percentile targets (p95, p99)** | None exist. `performance-test-instructions.md` §7: introducing them would be inventing a target. This stage **measures** percentiles and refuses to make them targets. |
| **Throughput / RPS target** | `NFR9` records a single-user store and no RPS target. Throughput is reported as this host's measured capacity (`test-results.md` §3, §12), never against a threshold. |

## 9. Findings that are not NFR targets

Six measured findings have **no requirement claiming them** and so carry no row.
They are the substance of what this stage learned and belong to the next scope;
`test-results.md` §15 carries each with its evidence and its reason for having no
target.

`F-1` superlinear concurrency degradation, throughput peaking at 2 clients ·
`F-2` the mixed page load breaching the budget at `c` = 8 (p95 952.7 ms) ·
`F-3` one competing writer taking the whole read surface down for 5.0 s ·
`F-4` the uncapped linear-in-range payload at the budget boundary ·
`F-5` the ~2.8-core server CPU ceiling ·
`F-6` a 147–186 MB steady-state RSS against 58 MB at boot.
