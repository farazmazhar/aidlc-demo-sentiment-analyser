# Build and Test Summary — intent `261001-analytics-layer`, Unit `u1-analytics-slice`

> **Stage:** `build-and-test` (construction) · lead `aidlc-quality-agent` ·
> **Test strategy:** `standard` · **Scope:** `feature` · **Depth:** Standard ·
> **Construction Autonomy Mode:** `autonomous` · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/construction/build-and-test`
>
> **Inputs this stage consumed** (the stage frontmatter's `consumes`):
> `construction/u1-analytics-slice/code-generation/code-generation-plan.md` ·
> `construction/u1-analytics-slice/code-generation/unit-test-instructions.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md`.
>
> **Sibling deliverables in this directory:** `build-instructions.md`,
> `integration-test-instructions.md`, `performance-test-instructions.md`,
> `security-test-instructions.md`, `test-results.md`, `cross-unit-traceability.md`.

## 1. Overall build status and prerequisites

| | |
|---|---|
| **Build status** | **SUCCESS** — every build and test command documented in `build-instructions.md` and the three instruction files passed, **with one recorded-command step blocked by the host interpreter (PEP 668) and two targets `Unverified`** |
| **Blocking conditions** | 2 `Unverified` targets (`NFR4.6`, `NFR4.7`) → the stage's failure predicate fires; see §6 and `test-results.md` § Failure handling |
| Prerequisites | CPython ≥ 3.11 (measured **3.14.7**), `pip`, a **git working tree** (required by `tests/test_config.py::test_local_config_is_gitignored`), network for the first install only |
| Environment variables | none |
| Services started | none; the app is a single loopback process over a local SQLite file |
| Application source modified by this stage | **none** |
| Existing test files modified by this stage | **none** |
| Test files added by this stage | **none** — and see §7 for why adding one was not the fix |

### 1.1 Command results, all executed in this run

| # | Command | Result |
|---|---|---|
| 1 | `python -m pip install -e ".[dev]"` (verification command step 1) | **exit 1 — PEP 668 `externally-managed-environment`** |
| 1a | same command against a **pristine clone of `HEAD` `aa0b1e4`** | **exit 1 — identical.** Proven pre-existing |
| 1b | remedy A: `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"` | **exit 0** — `Successfully installed … very-cool-sentiment-analysis-0.1.0` |
| 1c | remedy B: `python -m pip install --dry-run --break-system-packages -e ".[dev]"` | **exit 0** — `Would install very-cool-sentiment-analysis-0.1.0`; every dependency already satisfied |
| 2 | `python -m compileall -q app tests` | exit 0 |
| 3 | `python -m ruff check app tests` (ruff 0.16.9) | `All checks passed!` — exit 0 |
| 4 | `python -m ruff format --check app tests` | `30 files already formatted` — exit 0 |
| 5 | `python -c "import app.main …"` (import smoke test) | `very-cool-sentiment-analysis /v2 ['/v2/analytics/summary', '/v2/analytics/terms']` |
| 6 | `python -m pytest -q` (**whole suite** — the coverage gate) | **192 passed**, 1.65 s, `884 stmts / 26 missed / 97.06 %`, floor 80 % reached, **exit 0** |
| 7 | recorded per-unit command from `unit-test-instructions.md` | **67 passed**, `66 %`, **exit 0** |
| 8 | integration selection (4 files, `--no-cov`) | **53 tests**, all pass, exit 0 |
| 9 | verification command step 2 `python -m pytest -q` (verbatim) | exit 0 |
| 10 | verification command step 3 — real `uvicorn` on `127.0.0.1:8141` reading `/v1/health` (verbatim) | exit 0 — `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}` |
| 11 | security static checks (as printed in `security-test-instructions.md` §3.1) | `STATIC CHECKS PASSED`, exit 0 |
| 12 | security DAST probe — 40 injection probes + refusal shapes + loopback enforcement (as printed in §3.2) | `DAST PROBE PASSED`, exit 0 |
| 13 | performance scenario, run directly to read the raw numbers | `{"summary": [15.24 ms, 200], "terms": [25.04 ms, 200], "series_length": [0.0, 365]}` |
| 14 | the same suite re-run inside the remedy venv (fresh install, no lockfile) | **192 passed**, `97.06 %` |

### 1.2 The one environmental failure, stated plainly

**The recorded verification command's step 1 fails on this host, and it is not this
code's fault.**

* `python` resolves to `/usr/bin/python` → `/usr/bin/python3.14`, an Arch
  **externally-managed** system interpreter (PEP 668). `pip install -e` into it is
  refused with `error: externally-managed-environment`.
* **Proven pre-existing:** the same command fails identically on a pristine clone of
  `HEAD` (`aa0b1e4`) with none of this Unit's writes present. The baseline would have
  failed the same way.
* **Remedies, both executed and both succeeding:** a virtual environment (pip's own
  recommendation, **exit 0**, and the whole suite is green inside it), or
  `--break-system-packages` (**exit 0** on a dry run; every dependency already
  resolves, so the block is purely the write refusal).
* **No defined quality target is `Unverified` because of it.** The target inventory
  contains no target whose instrument is "`pip install -e ".[dev]"` exits 0 against the
  *system* interpreter". Every target below is measured by a test, an executable
  check, or a lint gate, and all of those run unchanged under either remedy.
* **Nothing was weakened to make it pass.** The `dev` extra, the two-package runtime
  declaration and the 80 % floor are untouched, and `pyproject.toml` and `app/` are
  byte-identical to the Bolt 1 commit (`git diff --stat HEAD -- pyproject.toml app/` is
  empty).

A second environmental trap was found and fixed **inside this stage's remit**, as an
environment-setup change with **no file edited**: the shell exports
`APPIMAGE=…opencode-desktop-linux-x86_64.AppImage`, which makes CPython report the
AppImage as `sys.executable`, so `test_each_analytics_endpoint_answers_inside_the_budget`
— which spawns `[sys.executable, "-c", …]` to measure the budget without coverage
instrumentation — failed with exit code 130. Prefixing the commands with
`env -u APPIMAGE` makes the whole suite green. Proof: `build-instructions.md` §6.

## 2. Test type inventory

Test strategy is **`standard`**, which requires `integration-test-instructions.md`;
measurable performance and security NFRs exist, so
`performance-test-instructions.md` and `security-test-instructions.md` were generated
as well.

| Test type | Generated? | Where it lives | Measured |
|---|---|---|---|
| Unit (lower level) | inherited per-Unit | `tests/test_analytics_read.py` (23), `tests/test_terms.py` (10) | in the 192 |
| Acceptance / API level (written **before** the implementation, per the affirmed `custom` posture) | inherited per-Unit | `tests/test_analytics_routes.py` (25) | in the 192 |
| Integration — cross-boundary | **this file set** | `integration-test-instructions.md` | 53 tests |
| Performance — budget, statement count, series extent | **this file set** | `performance-test-instructions.md` | 4 targets, all executed |
| Security — SAST, DAST, auth posture, injection | **this file set** | `security-test-instructions.md` | 6 + 3 targets, all executed |
| Contract tests | **not generated** | — | No consumer/provider boundary exists: one process, one repository, one versioned HTTP surface whose shapes are pinned by hand-written expected values in the endpoint tests. Generating a contract-test framework would add a dependency the affirmed cap forbids. |
| E2E (browser) | **not generated** | — | `tests/test_page.py:1-6` records why: the served markup and the served script are pinned, and no browser or JS test runner is configured. A browser runner would be a new third-party dev dependency. |
| Accessibility | **not generated** | — | `inception/refined-mockups/accessibility-checklist.md` is a human checklist, and no accessibility NFR with a measurable value exists in `nfr-requirements/`. |

## 3. Coverage expectations and result per unit

| Scope | Expected | Measured | Verdict |
|---|---|---|---|
| **Whole application line coverage** (the affirmed gate) | **≥ 80 %**, stated twice (`addopts --cov-fail-under=80` and `[tool.coverage.report] fail_under = 80`) | **97.06 %** — 884 statements, 26 missed | **Met**, 17.06 points of headroom |
| `app/analytics.py` (created this Unit) | counted in the whole-app floor | **100 %** (112 stmts, 0 missed) | Met |
| `app/terms.py` (created this Unit) | counted in the whole-app floor | **100 %** (11 stmts, 0 missed) | Met |
| `app/db.py` (modified this Unit) | counted in the whole-app floor | **100 %** (78 stmts, 0 missed) | Met |
| `app/models.py` (created this Unit) | counted in the whole-app floor | **100 %** (65 stmts, 0 missed) | Met |
| `app/main.py` (modified this Unit) | counted in the whole-app floor | 98 % (53 stmts, 1 missed — line 103, pre-existing) | Met |
| `app/routes.py` (modified this Unit) | counted in the whole-app floor | 99 % (172 stmts, 2 missed — lines 257–258, the pre-existing `/v1` `csv.Error` branch) | Met |
| Unit-scoped command | **no coverage gate by the recorded amendment** — read the number, not the exit code | 66 % | residual disclosed, not a failure |
| Branch coverage | **off by affirmed decision** (2026-10-02): 98 branches, 3 partial (`app/db.py:208`, `app/main.py:49`, `app/routes.py:385->387`), invisible to a line floor | not measured | disclosed cost of the decision |

**All 26 missed lines are pre-existing** and none is in a module this Unit created.
`app/session_auth.py:84-120` (17) and `app/openrouter_client.py:89-96` (6) are the two
production HTTP transports, untested because the affirmed dependency cap (exactly two
runtime packages) forbids an HTTP client library, so every test injects an exchanger or
a transport.

## 4. Target Verification Matrix

The inventory is **26 measurable targets** — every `NFRx.y` defined in
`construction/u1-analytics-slice/nfr-requirements/` (performance `NFR1.1`–`NFR1.4`;
security `NFR2.1`–`NFR2.6`; reliability `NFR3.1`–`NFR3.2` and `NFR4.1`–`NFR4.7`;
observability `NFR8.1`–`NFR8.3`; scalability `NFR9.1`–`NFR9.4`) — plus every target
restated in `construction/u1-analytics-slice/nfr-design/`. The `nfr-design/` artifacts
add **no new measurable value**: `logical-components.md` and `scalability-design.md`
were read and contain patterns *declared inapplicable with stated reasons*, not
thresholds. `NFR5`, `NFR6` and `NFR7` are declared `N/A` by
`nfr-requirements/traceability.json` as invariants with no sub-numberable value, so
they are not applicable measurable targets and carry no row. The functionally-sourced
**concurrency constraint** (`FR1.6`, `BR6.3`, `FR8.4`) has **no inception NFR parent**
and is deliberately not sub-numbered, so it is not a target row either — it was
executed and its evidence is in §5.

No row is `N/A`: the source inventory found 26 applicable measurable targets, and an
applicable target may never use `N/A`.

**Totals: 24 `Met` · 0 `Not Met` · 2 `Unverified` · 0 `N/A`.**

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|---|---|---|---|---|---|---|
| `NFR1.1` | `nfr-requirements/performance-requirements.md` § Performance targets | `GET /v2/analytics/summary` answers in **under 200 ms** over a store of 10,000 analyses spanning **365 distinct UTC days** | **15.24 ms**, HTTP `200` | `tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget`; raw JSON from the scenario re-run (`performance-test-instructions.md` §4); `test-results.md` § Coverage | Build and Test (executed here) | **Met** |
| `NFR1.2` | same file | `GET /v2/analytics/terms` answers in **under 200 ms** over the same fixture, **without coverage instrumentation** | **25.04 ms**, HTTP `200`, measured in a subprocess with no pytest and therefore no `--cov` | same test; the subprocess shape is visible in `tests/test_analytics_read.py:532`; `performance-test-instructions.md` §3.6 | Build and Test | **Met** |
| `NFR1.3` | same file | SQL statement count is **independent of how many days the resolved range covers** | **1** statement over a 7-day range and **1** over a 365-day range, and that statement carries `GROUP BY` | `tests/test_analytics_read.py::test_the_statement_count_does_not_grow_with_the_number_of_days` (`sqlite3` trace hook) | Build and Test | **Met** |
| `NFR1.4` | same file + `nfr-design/performance-design.md` §2.2 | An unbounded summary over the fixture returns **exactly 365 entries** — one per UTC day — so series work follows the range, not the 10,000 rows | **365** entries; `total` 10,000; the series sums to 10,000; first and last dates pinned | `tests/test_analytics_read.py::test_the_unbounded_series_length_is_the_fixture_span_not_the_row_count` | Build and Test | **Met** |
| `NFR2.1` | `nfr-requirements/security-requirements.md` § Authentication and authorization | The analytics endpoints add **no authentication and no authorization** and change none of the existing posture | No new security scheme, dependency, route guard or `Depends(...)` other than `get_connection` in either `/v2` handler; `create_app` adds no `Security`/`HTTPBasic`/`OAuth2`; the whole `/v1` and `/auth/*` suite is green unchanged | `tests/test_analytics_routes.py::test_v1_routes_are_untouched_by_the_v2_surface`; `tests/test_auth_routes.py` (12) + `tests/test_session_auth.py` (12) green; handler signatures inspected at `app/routes.py:339-378` | Build and Test | **Met** |
| `NFR2.2` | `security-requirements.md` § Egress and data protection | **No new egress path of any kind**; the analytics code imports no HTTP client, opens no socket, calls no engine, adds no credential | 0 forbidden imports across `analytics.py` / `terms.py` / `models.py` against a 12-module denylist; the armed offline guard is **proved** to fire | `security-test-instructions.md` §3.1 check 1; `tests/test_analytics_routes.py::test_the_analytics_endpoints_are_proved_offline_by_an_armed_guard` (independently verified red without the guard) | Build and Test | **Met** |
| `NFR2.3` | same file | **All SQL is parameter-bound**; no value reaches a statement by interpolation or concatenation | 9 `execute`/`executemany` call sites, all parameter-bound; 0 statement texts built at call time; 0 `executescript`; 16 DML literals checked, 0 without a `?` inside the read path; **40 injection probes → 422 or 200, never 500, and 0 error-text leaks** | `security-test-instructions.md` §3.1 checks 2–4 (proved red on a deliberately broken copy) and §3.2 | Build and Test | **Met** |
| `NFR2.4` | same file | **The loopback bind is enforced at startup**; a non-loopback host fails loudly rather than serving | `create_app(host="0.0.0.0")` → `NonLoopbackBindError: Refusing to bind '0.0.0.0': this app is unauthenticated and holds the operator's API key…` | `security-test-instructions.md` §3.2; `tests/test_routes.py::test_the_server_binds_loopback_only`; design at `app/main.py:resolve_bind_host` | Build and Test | **Met** |
| `NFR2.5` | same file | **No credential is added anywhere** — no code path, response body, log record or artifact | 0 credential-shaped literal assignments in `app/` (the `S105`-misses-`API_KEY` hole, covered); the existing redaction assertions are green; no analytics response schema carries a credential field; the DAST probe carries no key | `security-test-instructions.md` §3.1 check 6 and §3.3; `tests/test_config.py::test_the_key_is_never_rendered_or_logged`; DAST probe with `Settings(mode="offline", api_key=None)` | Build and Test | **Met** |
| `NFR2.6` | same file § Compliance | The change stays within the privacy and localhost-only rules; the declared runtime dependency list is unchanged | `pyproject.toml` byte-identical to the Bolt 1 commit; the dependency-cap assertion passes; no new egress, loopback enforced, no credential | `tests/test_config.py::test_the_manifest_declares_two_runtime_dependencies_and_the_dev_tools`; `git diff --stat HEAD -- pyproject.toml app/` is empty | Build and Test | **Met** |
| `NFR3.1` | `nfr-requirements/reliability-requirements.md` § Read-only guarantee | Both endpoints are `GET` and perform **no write, no schema change and no access bookkeeping** | Row count, schema and content unchanged across analytics requests; the DAST probe's 50+ requests left the row count at 1 | `tests/test_migration_indexes.py::test_reading_analytics_never_changes_the_store`; `security-test-instructions.md` §3.2 read-only block | Build and Test | **Met** |
| `NFR3.2` | same file | The read path issues **no mutating operation of any kind** — no `INSERT`/`UPDATE`/`DELETE`, no DDL, no state-changing `PRAGMA` | The traced statement set on the request's own connection contains no mutating form | `tests/test_migration_indexes.py::test_the_analytics_read_path_issues_no_mutating_statement` | Build and Test | **Met** |
| `NFR4.1` | `reliability-requirements.md` § Distinguishable failures | A malformed parameter yields **422 naming its own field** in the message text; an inverted range names **both** `query.from` and `query.to`; nothing is computed; no silent default or clamp | 5 refusal shapes verified over real HTTP: 422, envelope exactly `{code, message}`, correct field named, both fields on the inverted range; 40 injection payloads refused rather than coerced | `tests/test_analytics_routes.py` refusal tests + `security-test-instructions.md` §3.2 | Build and Test | **Met** |
| `NFR4.2` | same file | A **storage failure is a 500 carrying a machine code distinct from every validation code** (`STORAGE_FAILURE`) | Both handlers return 500 `STORAGE_FAILURE`; distinct from `VALIDATION_FAILED` | `tests/test_analytics_routes.py::test_summary_answers_a_storage_failure_with_its_own_machine_code` and `::test_terms_answers_a_storage_failure_with_the_same_machine_code` | Build and Test | **Met** |
| `NFR4.3` | same file | A **failed request never renders as a plausible-looking empty result** — a 422 and a 500 are visibly different from an empty result, on the wire and in the view | Three structurally distinct outcomes observed: `200` with the frozen empty body; `422 VALIDATION_FAILED`; `500 STORAGE_FAILURE`. Never a `404` for emptiness | `security-test-instructions.md` §3.2 empty-success block; `tests/test_analytics_routes.py::test_summary_over_a_range_matching_no_rows_is_an_empty_success`; `…::test_terms_over_an_empty_range_is_two_empty_lists_and_nothing_else` | Build and Test | **Met** |
| `NFR4.4` | same file | The **refuse-never-substitute convention governs every null**: a share is `null` on a zero denominator, a mean with no inputs is `null`, a label with no rows yields an empty list — never a fabricated `0.0`, never `null`-as-empty, never a padded list | All four cases pinned against hand-written expected values, including the exact half-up tie (`36/128` → `0.2813` and its mean) which `round()` would have rounded half-even | `tests/test_analytics_read.py::test_the_summary_aggregates_are_the_hand_computed_values`, `::test_a_share_and_a_mean_tie_round_half_up_not_half_even`, `::test_a_label_with_no_rows_yields_an_empty_list_and_not_none` | Build and Test | **Met** |
| `NFR4.5` | same file | The additive migration is **idempotent and preserves every row**; it never completes partially, and a store it cannot read **rolls back and re-raises** | v3 → v4 with every row and column intact; a v4 store is a no-op; the three indexes exist **by name** on both the fresh and migrating path; a store the step cannot preserve rolls back and raises loudly | the 9 tests in `tests/test_migration_indexes.py`, including `::test_the_rebuild_issues_the_index_statements_itself_and_leaves_nothing_to_a_later_step` (verified to have teeth: removing the re-creation turns it red while the outcome-only sibling stays green) | Build and Test | **Met** |
| **`NFR4.6`** | same file | **Graceful degradation is per-section, not all-or-nothing**: a section that succeeds while another fails shows the successful section **plus a partial-failure marker**, so the two never silently disagree about the range | **Not executable in this Unit.** The instrument the requirement names is `AC6.5.3` / `AC6.5.5`, both of which need a **second analytics section**. This Unit completes the summary region end to end; the two term-list containers are `u3-analytics-view`'s (`unit-of-work-story-map.md`'s cross-cutting table). `code-generation/traceability.json` records `NFR4.6` as `N/A` — *"recorded N/A rather than OK so the unbuilt half is not claimed"* | `…/code-generation/traceability.json` → `NFR4.6`; `nfr-requirements/reliability-requirements.md` § NFR4.6 | **Unverified** — owning work is `u3-analytics-view`'s own code-generation + build-and-test pass, which is **not** a validation stage, so this cannot be deferred | 
| **`NFR4.7`** | same file | **No silent retry**, and an out-of-order late response from a superseded range is **discarded** rather than allowed to overwrite current data | **Not executable in this Unit.** The named instrument is the `AC6.5.2` out-of-order test, which needs a **range control** to supersede — also `u3-analytics-view`'s. The *participating* half is delivered and asserted: the summary region issues exactly one fetch and no retry | `tests/test_page.py` (exactly one summary fetch, pinned); `…/code-generation/traceability.json` → `NFR4.7` | **Unverified** — owning work is `u3-analytics-view`'s own code-generation + build-and-test pass, which is **not** a validation stage |
| `NFR8.1` | `nfr-requirements/observability-requirements.md` § Logging | An analytics failure is **visible through the module logger** — logged as a record, never swallowed, never `print()`ed | A provoked storage failure emits a log record through the module logger; `print()` appears **0** times across all 15 modules in `app/` | `tests/test_analytics_routes.py::test_a_storage_failure_is_logged_through_the_module_logger_with_its_code`; `security-test-instructions.md` §3.1 check 5 | Build and Test | **Met** |
| `NFR8.2` | same file | A failure with a machine code travels through the envelope **and** appears in the application log, so the wire surface and the log agree | The same test asserts both halves: the response carries `STORAGE_FAILURE` **and** the log record carries it | `tests/test_analytics_routes.py::test_a_storage_failure_is_logged_through_the_module_logger_with_its_code`. This target found a real defect during Code Generation — the code was on the wire but not in the log — which was fixed; `code-summary.md` § Deviations (e) | Build and Test | **Met** |
| `NFR8.3` | same file | **No request parameter is interpolated into statement text, and no credential appears in any log record** | 0 statement texts built at call time; 0 credential-shaped literals in `app/`; the existing redaction assertions (reprs, `record.__dict__`, `/`, `/v1/health`, `/auth/status` bodies) are green | `security-test-instructions.md` §3.1 checks 2–3 and check 6; `tests/test_config.py::test_the_key_is_never_rendered_or_logged` | Build and Test | **Met** |
| `NFR9.1` | `nfr-requirements/scalability-requirements.md` § Load profile | **Series length equals the number of UTC days in the resolved range**; an empty range returns an empty series; the work is a function of the range, never of the store's row count | 365 entries for the 365-day range; gap days zero-filled inside a matched range; an unmatched range returns `[]` (never a zero-filled span) | `tests/test_analytics_read.py::test_the_unbounded_series_length_is_the_fixture_span_not_the_row_count`; `tests/test_analytics_routes.py::test_a_day_with_no_rows_inside_a_matched_range_is_zero_filled`; `::test_summary_over_a_range_matching_no_rows_is_an_empty_success` | Build and Test | **Met** |
| `NFR9.2` | same file | **No response grows with the size of the store**; at most `limit` (default 10) entries materialised **per list** | Default 10 per list; an oversized `limit` is honoured, never clamped; a label with no rows yields `[]` | `tests/test_analytics_read.py::test_the_default_limit_is_ten_per_list_and_an_oversized_one_is_honoured`, `::test_a_label_with_no_rows_yields_an_empty_list_and_not_none`; `tests/test_analytics_routes.py::test_terms_honours_the_limit_per_list_without_clamping_an_oversized_one` | Build and Test | **Met** |
| `NFR9.3` | same file | The unbounded series is **capped by nothing, deliberately** — the omission is a policy decision for a future scope, not an oversight | No cap imposed; the unbounded range resolves to the earliest stored UTC day through today inclusive and its length equals that span, as stated | `tests/test_analytics_read.py::test_an_unbounded_read_runs_from_the_earliest_stored_day_through_today`; `tests/test_analytics_routes.py::test_summary_with_neither_bound_runs_from_the_earliest_stored_day_through_today` | Build and Test | **Met** |
| `NFR9.4` | same file | **Statement count does not grow with the range span** | 1 statement at 7 days, 1 at 365 days — the same instrument as `NFR1.3` | `tests/test_analytics_read.py::test_the_statement_count_does_not_grow_with_the_number_of_days` | Build and Test | **Met** |

### 4.1 The two `Unverified` rows, and why neither is `Not Met`

Neither target was executed and failed — each is **unexecutable in this Unit**, which is
a different verdict from a failure:

* `NFR4.6` needs two analytics sections to make one fail while the other succeeds. This
  Unit ships one section; the second belongs to `u3-analytics-view`.
* `NFR4.7` needs a range control to supersede so a late response can arrive out of
  order. No range control exists yet; it is `u3-analytics-view`'s deliverable.

`nfr-requirements/reliability-requirements.md` itself already notes this for `NFR4.7`
(*"the markup behaviour is `u3-analytics-view`'s; the rule participates in this unit's
summary region"*), and Code Generation recorded both as `N/A` with the reason *"recorded
N/A rather than OK so the unbuilt half is not claimed."*

**Why `N/A` was not available here.** `N/A` is valid only where the source inventory
found **no applicable measurable target**. The inventory found 26, and both of these
carry an id, a statement and a named instrument. Redefining them as "the participating
half this Unit delivered" would be weakening a defined quality target so a step passes,
which the stage definition forbids and which this stage will not do.

## 5. Constraints that are not targets, executed anyway

The **cross-thread concurrency constraint** has no inception NFR parent (it traces to
`FR1.6`, `BR6.3`, `FR8.4`, and `nfr-requirements/review-01` R-01 corrected exactly that
mis-parenting), so it carries no target row. It was executed because it is the defect
this Unit exists to close:

* two genuinely overlapping analytics requests, both asserted to overlap, both `200`;
* the driver opened on one thread and used **and** closed on another behind a barrier —
  this is the load-bearing instrument, and it was verified **red** with
  `ProgrammingError('SQLite objects created in a thread can only be used in that same
  thread…')` when `check_same_thread` is reverted;
* a 24-request soak, and `init_db` asserted to run **exactly once** across a concurrent
  batch (schema initialisation hoisted out of the per-request path).

The first draft of that overlap test stayed **green** with `check_same_thread` reverted,
because anyio's worker pool reused an idle thread; it was therefore worthless and was
replaced. `code-summary.md` §3 records this.

## 6. Readiness assessment

| Question | Answer |
|---|---|
| **Build-ready?** | **Yes.** Every module byte-compiles, lints clean under the pinned rule set, is format-clean, imports and assembles, and both dependency remedies install the project successfully. |
| **Test-ready?** | **Yes.** 192 tests pass with zero mocks against real SQLite and real served markup, the offline guard is proved armed, the whole-application 80 % floor passes with 17.06 points of headroom, and the suite is order- and module-independent. |
| **Deployment-ready?** | **Not yet, and the gate is not this stage's to close.** Two `Unverified` targets stand, both belonging to `u3-analytics-view`; the walking-skeleton checkpoint requires the human's approval; `ci-pipeline` (3.7) has not run; and `code-summary.md` § R-02 discloses a live unit-boundary violation (`app/terms.py` authored by U1, attribution `u2-term-extraction`) that only a Delivery Planning re-run resolves. |

## 7. Known limitations and outstanding items

1. **`NFR4.6` and `NFR4.7` are `Unverified`.** They cannot be executed until
   `u3-analytics-view` builds the second analytics section and the range control. **No
   test was invented to close them**: a test written against markup that does not exist
   yet would assert nothing, and adding tests is not the fix for a missing deliverable.
   Escalated per the failure ladder in `test-results.md` § Failure handling.
2. **The recorded verification command's step 1 is blocked on this host** by PEP 668.
   Pre-existing, proven, and remediable two ways (§1.2). Whether the *recorded command
   itself* should be rewritten to use a venv is a Delivery Planning decision; this stage
   did not rewrite it.
3. **The `APPIMAGE` environment variable corrupts `sys.executable` on this host.** One
   test fails without `env -u APPIMAGE` for that reason alone. The remedy is a prefix,
   not a code change; it should be recorded in the repository's own verification script
   when `FR7.2` (one command that runs the gates) is built in `u4-platform-packaging`.
4. **The U1 → U2 unit-boundary violation is live.** `app/terms.py` exists but is
   attributed to `u2-term-extraction` by `tech-stack-decisions.md:49`,
   `unit-of-work.md:96` and `contract-summary.md` §4. `u2-term-extraction` must **adopt**
   the module and owns the stopword-set decision; changing the set would move three U1
   manifest writes. Disclosed by Code Generation (`code-summary.md` § R-02, § R-09);
   Build and Test reports it, does not re-decide it, and did not modify it.
5. **No browser execution.** The served script is pinned by assertion, never run
   (`tests/test_page.py:1-6`).
6. **The two production HTTP transports remain untested** (23 of the 26 missed lines),
   because the affirmed dependency cap forbids an HTTP client library.
7. **No secret scanner and no dependency audit exist** (`FR7.3`, a
   `u4-platform-packaging` obligation), so `NFR2.5` and `NFR8.3` rest on the instruments
   named above rather than on a scanner.
8. **`ruff` `TID251` banned-api boundaries are not configured** (`FR7.5`, also
   `u4-platform-packaging`), so the layer boundary is not lint-enforced today. The
   static check in `security-test-instructions.md` §3.1 check 1 is the instrument that
   exists instead, and it is scoped rather than presented as the rule the team affirmed.
9. **There is no lockfile** (an affirmed gap, `FR7.1`), so a fresh install resolves a
   newer toolchain than the declared floors. Measured here: the system `ruff` is 0.16.9
   and the fresh-venv `ruff` is 0.16.10, and the whole suite passes under both — but the
   suite's pass/fail state is a function of the resolved dependency set, not of the code.

## 8. Approval gate

```
# :hammer: Build and Test Complete
```

Instruction sets generated: `build-instructions.md`, `integration-test-instructions.md`,
`performance-test-instructions.md`, `security-test-instructions.md`.
Results: **build success**, **192 tests passed / 0 failed / 0 skipped**, whole-application
line coverage **97.06 %**, **24 targets `Met` / 0 `Not Met` / 2 `Unverified` / 0 `N/A`**,
and a **fail-state finding requiring a human decision** (§6, §7.1 and
`test-results.md` § Failure handling).

**Review:** `aidlc/spaces/default/intents/261001-analytics-layer/construction/build-and-test/`