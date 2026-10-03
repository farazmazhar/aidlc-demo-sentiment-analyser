# Test Results — intent `261001-analytics-layer`, Unit `u1-analytics-slice`

> **Stage:** `build-and-test` (construction) · **Test strategy:** `standard` ·
> **Record:** `aidlc/spaces/default/intents/261001-analytics-layer/construction/build-and-test`
>
> **Inputs this stage consumed** (the stage frontmatter's `consumes`):
> `construction/u1-analytics-slice/code-generation/code-generation-plan.md` ·
> `construction/u1-analytics-slice/code-generation/unit-test-instructions.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md`.

## 1. Build status

**SUCCESS, with two recorded qualifications that are stated rather than absorbed.**

| Step | Command | Exit | Result |
|---|---|---|---|
| Install (verification command **step 1**) | `python -m pip install -e ".[dev]"` | **1** | **PEP 668 `externally-managed-environment`** — the host's system interpreter refuses `pip install`. Proven pre-existing (identical failure on a pristine clone of `HEAD` `aa0b1e4`). |
| Install — remedy A | `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"` | **0** | `Successfully installed … very-cool-sentiment-analysis-0.1.0` |
| Install — remedy B | `python -m pip install --dry-run --break-system-packages -e ".[dev]"` | **0** | `Would install very-cool-sentiment-analysis-0.1.0` — every dependency already satisfied |
| Byte-compile | `python -m compileall -q app tests` | 0 | clean |
| Lint | `python -m ruff check app tests` | 0 | `All checks passed!` (ruff 0.16.9) |
| Format | `python -m ruff format --check app tests` | 0 | `30 files already formatted` |
| Import smoke | `python -c "import app.main …"` | 0 | `very-cool-sentiment-analysis /v2 ['/v2/analytics/summary', '/v2/analytics/terms']` |
| Verification **step 2** (verbatim) | `python -m pytest -q` | 0 | 192 passed, 97.06 % |
| Verification **step 3** (verbatim) | real `uvicorn` on `127.0.0.1:8141` → `/v1/health` | 0 | `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}` |

**Did the PEP 668 block make any target `Unverified`? No.** The target inventory
contains no target whose instrument is "`pip install -e ".[dev]"` exits 0 against the
*system* interpreter". Every target in §4 is measured by a `pytest` test, an
executable static/DAST check, or a lint gate, and all of those run unchanged under
either remedy. The remedy is pip's own advice (`python -m venv path/to/venv`, or
`--break-system-packages`). **Nothing was weakened**: the `dev` extra, the
two-package runtime declaration and the 80 % floor are untouched, and `pyproject.toml`
and `app/` are byte-identical to the Bolt 1 commit (`git diff --stat HEAD -- pyproject.toml app/`
is empty).

## 2. Test results

### 2.1 The gate run — the whole suite

```
$ env -u APPIMAGE python -m pytest -q
........................................................................ [ 37%]
........................................................................ [ 75%]
................................................                         [100%]
```

| Metric | Value |
|---|---|
| **Total** | **192** |
| **Passed** | **192** |
| **Failed** | **0** |
| **Skipped** | **0.** The suite contains exactly one `pytest.skip` guard — `tests/test_config.py:166`, `pytest.skip("git is not available on this machine")` — and it did not fire on this host. There is no `skipif` and no `xfail` anywhere, and `-ra` reports nothing. |
| **Errors** | **0** |
| **Warnings** | **0** — `filterwarnings = ["error"]` would have made any warning a failure |
| Duration | 1.65 s |
| Exit code | **0** |
| Baseline before this Unit | 118 passed, 96.02 % |

### 2.2 The recorded per-unit command (`unit-test-instructions.md`)

```
$ env -u APPIMAGE python -m pytest -q tests/test_analytics_read.py tests/test_analytics_routes.py \
    tests/test_terms.py tests/test_migration_indexes.py --cov-fail-under=0
```

67 tests, **67 passed, 0 failed, 0 skipped**, `TOTAL 884 stmts / 301 missed / 66 %`,
**exit 0**. Reported once, not summed into the 192 — the per-unit files are a subset
of the whole suite, and double-counting them would overstate the total.

> The command carries `--cov-fail-under=0` by the amendment reasoned in
> `unit-test-instructions.md`, so it has **no coverage gate**: it exits 0 at 66 %.
> Read the number, not the exit code. The whole-suite floor is untouched.

### 2.3 Integration selection (`integration-test-instructions.md` §2.2)

```
$ env -u APPIMAGE python -m pytest -q tests/test_analytics_routes.py tests/test_migration_indexes.py \
    tests/test_page.py tests/test_terms.py --no-cov
```

53 tests, **53 passed, 0 failed, 0 skipped**, exit 0.

### 2.4 Non-`pytest` checks

| Check | Result |
|---|---|
| `security-test-instructions.md` §3.1 static checks (as printed in the artifact) | `STATIC CHECKS PASSED`, exit 0 |
| the same checks against a **deliberately broken copy** of `app/` | `STATIC CHECKS FAILED`, exit 1, with 5 named findings — the checks have teeth |
| `security-test-instructions.md` §3.2 DAST probe (as printed in the artifact) | `DAST PROBE PASSED`, exit 0 — 40 injection probes, 5 refusal shapes, empty-success shapes, read-only, loopback enforcement |
| whole suite re-run inside the remedy venv (fresh install, no lockfile) | **192 passed**, 97.06 % |

## 3. Failure details

### 3.1 Resolved — the one failing test in the first run

```
FAILED tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget
E   AssertionError:
E   assert 130 == 0
E    +  where 130 = CompletedProcess(args=['/home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage',
E        '-c', '\nimport json, sqlite3,...urements))\n', '/tmp/pytest-of-faraz/pytest-16/…'],
E        returncode=130, stdout='', stderr='').returncode
tests/test_analytics_read.py:552: AssertionError
```

| | |
|---|---|
| **Test** | `tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget` |
| **Assertion** | `assert completed.returncode == 0` at `tests/test_analytics_read.py:552` |
| **Root cause** | The test spawns `[sys.executable, "-c", scenario, tmp]` so the 200 ms budget is measured in an interpreter with no pytest and therefore no `--cov` (`BR3.6`, `AC8.1.4`). The shell exports `APPIMAGE=/home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage`; CPython 3.14 honours that variable when resolving `sys.executable`, so the spawn launched the AppImage with `-c` and the AppImage exited **130**. |
| **Proof it is environmental** | `python -c "import sys; print(sys.executable)"` → `/home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage`; `env -u APPIMAGE python -c "import sys; print(sys.executable)"` → `/usr/bin/python`. The AppImage, given `-c`, is not a Python interpreter. |
| **Fix applied** | Environment-setup fix only: prefix every command with `env -u APPIMAGE`. **No application source file and no existing test file was modified.** `git status --porcelain` shows no change under `app/` or `tests/`. |
| **After the fix** | 192 passed, exit 0, budget measured at **summary 15.24 ms / terms 25.04 ms**, both `200`. |
| **Class** | Harness environment, not product code. `NFR1.1` and `NFR1.2` are `Met`, not `Unverified`. |

### 3.2 Unresolved, and deliberately so — `python -m pip install -e ".[dev]"`

| | |
|---|---|
| **Command** | verification command step 1 |
| **Assertion** | exit 1, `error: externally-managed-environment` (PEP 668) |
| **Evidence it is pre-existing** | The identical command fails identically on a fresh `git clone` of `HEAD` `aa0b1e4`, with none of this Unit's 17 source and test writes present. The failure is a property of `/usr/bin/python3.14` on Arch, not of this change. |
| **Remedies, both executed and both succeeding** | `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"` → exit 0, and the whole suite is green inside it; `python -m pip install --dry-run --break-system-packages -e ".[dev]"` → exit 0, `Would install very-cool-sentiment-analysis-0.1.0`. |
| **Effect on the target matrix** | **None.** No target's instrument depends on installing into the system interpreter. |
| **Why it is not silently passed** | It is reported as a **failed step** of the recorded command, in the build status table, in `build-instructions.md` §2.2, and in `build-and-test-summary.md` §1.2. Whether the *recorded command itself* should be rewritten to use a venv is a Delivery Planning decision this stage did not take. |

### 3.3 No other failure

No assertion failed, no test errored, no test was skipped, no warning was raised, and
no lint or format finding was produced.

## 4. Coverage report

Whole-application line coverage, measured on the whole-suite run
(`[tool.coverage.run] source = ["app"]`, so the **whole** application is measured,
including the live client the offline suite never imports):

```
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
app/__init__.py                2      0   100%
app/analytics.py             112      0   100%
app/config.py                 54      0   100%
app/db.py                     78      0   100%
app/dummy_client.py           22      0   100%
app/main.py                   53      1    98%   103
app/models.py                 65      0   100%
app/openrouter_client.py      80      6    92%   89-96
app/repository.py             23      0   100%
app/routes.py                172      2    99%   257-258
app/sentiment.py              22      0   100%
app/service.py                73      0   100%
app/session_auth.py          117     17    85%   84-120
app/terms.py                  11      0   100%
--------------------------------------------------------
TOTAL                        884     26    97%
Required test coverage of 80% reached. Total coverage: 97.06%
```

| | |
|---|---|
| **Total coverage** | **97.06 %** (884 statements, 26 missed) |
| **Floor** | **80 %**, enforced twice (`addopts --cov-fail-under=80` and `[tool.coverage.report] fail_under = 80`) — a real gate: raising it on the command line makes the run exit 1 |
| Headroom | 17.06 points |
| Baseline before this Unit | 96.02 % (679 statements, 27 missed) |
| Branch coverage | **Off by affirmed decision** (`team.md`, 2026-10-02). Measured cost: 98 branches, 3 partial — `app/db.py:208`, `app/main.py:49`, `app/routes.py:385->387` — none visible to a line floor. Not turned on and not weakened here. |

**All 26 missed lines are pre-existing**, and none is in a module this Unit created:

* `app/session_auth.py:84-120` (17) and `app/openrouter_client.py:89-96` (6) — the two
  production HTTP transports. Every test injects an exchanger or a transport because
  the affirmed dependency cap (exactly two runtime packages) forbids an HTTP client
  library.
* `app/routes.py:257-258` — the `csv.Error` branch of the `/v1` bulk-import CSV parse.
  Pre-existing; it was lines 217–218 before this Unit added code above it.
* `app/main.py:103` — the `if not logging.getLogger().handlers` false arm.

## 5. Finalized Target Verification Matrix

**Source-complete inventory: 26 applicable measurable targets.** Every `NFRx.y` in
`construction/u1-analytics-slice/nfr-requirements/` — `NFR1.1`–`NFR1.4`, `NFR2.1`–`NFR2.6`,
`NFR3.1`–`NFR3.2`, `NFR4.1`–`NFR4.7`, `NFR8.1`–`NFR8.3`, `NFR9.1`–`NFR9.4` — plus every
target restated in `construction/u1-analytics-slice/nfr-design/`. The `nfr-design/`
artifacts were each read and add **no new measurable value** (`logical-components.md`
and `scalability-design.md` declare patterns inapplicable with stated reasons rather
than stating thresholds). `NFR5`/`NFR6`/`NFR7` are declared `N/A` upstream as
invariants with no sub-numberable value, so they are not applicable measurable targets
and carry no row; the functionally-sourced concurrency constraint has no inception NFR
parent and carries no row either. **No row uses `N/A`** — an applicable target may
never use it, and the inventory found applicable targets.

**No `Pending` verdict remains.**

**Totals: 24 `Met` · 0 `Not Met` · 2 `Unverified` · 0 `N/A`.**

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|---|---|---|---|---|---|---|
| `NFR1.1` | `nfr-requirements/performance-requirements.md` § Performance targets | summary answers **under 200 ms** over 10,000 rows / 365 distinct UTC days | **15.24 ms**, HTTP `200` | `tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget`; raw scenario re-run, `performance-test-instructions.md` §4 | — executed here | **Met** |
| `NFR1.2` | same | terms answers **under 200 ms** over the same fixture, measured **without coverage instrumentation** | **25.04 ms**, HTTP `200`, subprocess with no pytest and no `--cov` | same test; subprocess at `tests/test_analytics_read.py:532` | — executed here | **Met** |
| `NFR1.3` | same | statement count **independent of the range's day count** | **1** at 7 days, **1** at 365 days, statement carries `GROUP BY` | `::test_the_statement_count_does_not_grow_with_the_number_of_days` (`sqlite3` trace hook) | — executed here | **Met** |
| `NFR1.4` | same; `nfr-design/performance-design.md` §2.2 | unbounded summary returns **exactly 365 entries** over 10,000 rows | **365**; `total` 10,000; series sums to 10,000 | `::test_the_unbounded_series_length_is_the_fixture_span_not_the_row_count` | — executed here | **Met** |
| `NFR2.1` | `nfr-requirements/security-requirements.md` § Authentication and authorization | **no authentication and no authorization added**; posture unchanged | no new scheme/guard; both handlers depend only on `get_connection`; `/v1` and `/auth/*` suites green unchanged | `tests/test_analytics_routes.py::test_v1_routes_are_untouched_by_the_v2_surface`; `test_auth_routes.py` (12) + `test_session_auth.py` (12); `app/routes.py:339-378` | — executed here | **Met** |
| `NFR2.2` | `security-requirements.md` § Egress and data protection | **no new egress path of any kind** | 0 forbidden imports in the three read-path modules vs a 12-module denylist; the offline guard is **proved** to fire | `security-test-instructions.md` §3.1 check 1; `::test_the_analytics_endpoints_are_proved_offline_by_an_armed_guard` | — executed here | **Met** |
| `NFR2.3` | same | **all SQL parameter-bound**; nothing interpolated or concatenated | 9 call sites all parameter-bound; 0 statement texts built at call time; 0 `executescript`; **40 injection probes → 422 or 200, never 500**, 0 error-text leaks | `security-test-instructions.md` §3.1 checks 2–4 (red on a broken copy) and §3.2 | — executed here | **Met** |
| `NFR2.4` | same | **loopback bind enforced at startup**; non-loopback fails loudly | `create_app(host="0.0.0.0")` → `NonLoopbackBindError: Refusing to bind '0.0.0.0'…` | `security-test-instructions.md` §3.2; `tests/test_routes.py::test_the_server_binds_loopback_only`; `app/main.py:resolve_bind_host` | — executed here | **Met** |
| `NFR2.5` | same | **no credential added anywhere** | 0 credential-shaped literal assignments in `app/`; redaction assertions green; no credential field in any analytics response schema | `security-test-instructions.md` §3.1 check 6, §3.3; `tests/test_config.py::test_the_key_is_never_rendered_or_logged` | — executed here | **Met** |
| `NFR2.6` | same § Compliance | within the privacy and localhost-only rules; declared runtime dependency list unchanged | `pyproject.toml` byte-identical to the Bolt 1 commit; dependency-cap assertion passes | `tests/test_config.py::test_the_manifest_declares_two_runtime_dependencies_and_the_dev_tools`; `git diff --stat HEAD -- pyproject.toml app/` empty | — executed here | **Met** |
| `NFR3.1` | `nfr-requirements/reliability-requirements.md` § Read-only guarantee | **no write, no schema change, no access bookkeeping** | row count / schema / content unchanged; the DAST probe's 50+ requests left the row count at 1 | `tests/test_migration_indexes.py::test_reading_analytics_never_changes_the_store`; `security-test-instructions.md` §3.2 | — executed here | **Met** |
| `NFR3.2` | same | **no mutating operation of any kind** in the read path | the traced statement set on the request's own connection contains no mutating form | `::test_the_analytics_read_path_issues_no_mutating_statement` | — executed here | **Met** |
| `NFR4.1` | `reliability-requirements.md` § Distinguishable failures | **422 naming its own field**; inverted range names **both**; nothing computed; no silent default or clamp | 5 refusal shapes verified over real HTTP; envelope exactly `{code, message}`; both fields on the inverted range; 40 hostile payloads refused | `tests/test_analytics_routes.py` refusal tests; `security-test-instructions.md` §3.2 | — executed here | **Met** |
| `NFR4.2` | same | storage failure is **500 `STORAGE_FAILURE`**, distinct from every validation code | both handlers 500 `STORAGE_FAILURE`, distinct from `VALIDATION_FAILED` | `::test_summary_answers_a_storage_failure_with_its_own_machine_code`; `::test_terms_answers_a_storage_failure_with_the_same_machine_code` | — executed here | **Met** |
| `NFR4.3` | same | a **failed request never renders as a plausible-looking empty result** | three distinct outcomes observed: `200` frozen-empty, `422 VALIDATION_FAILED`, `500 STORAGE_FAILURE`; never a `404` for emptiness | `security-test-instructions.md` §3.2; `::test_summary_over_a_range_matching_no_rows_is_an_empty_success`; `::test_terms_over_an_empty_range_is_two_empty_lists_and_nothing_else` | — executed here | **Met** |
| `NFR4.4` | same | refuse-never-substitute for **every** null | share `null` on a zero denominator, mean `null` with no inputs, empty label → `[]`; the exact half-up tie pinned (`36/128` → `0.2813`) | `::test_the_summary_aggregates_are_the_hand_computed_values`; `::test_a_share_and_a_mean_tie_round_half_up_not_half_even`; `::test_a_label_with_no_rows_yields_an_empty_list_and_not_none` | — executed here | **Met** |
| `NFR4.5` | same | additive migration **idempotent, row-preserving**, loud rollback | v3→v4 keeps every row and column; v4 store is a no-op; three indexes by name on both paths; an unpreservable store rolls back and re-raises | the 9 tests in `tests/test_migration_indexes.py`, incl. `::test_the_rebuild_issues_the_index_statements_itself_and_leaves_nothing_to_a_later_step` (verified red when the re-creation is removed, while the outcome-only sibling stays green) | — executed here | **Met** |
| **`NFR4.6`** | same | **per-section graceful degradation**: one section succeeding while another fails shows the successful section **plus a partial-failure marker** | **not executable in this Unit** — the named instruments `AC6.5.3` / `AC6.5.5` need a **second analytics section**; the two term-list containers belong to `u3-analytics-view`. The *participating* half is delivered: summary / empty / error are three distinct regions and a failed fetch renders in place. Code Generation recorded `N/A` with the reason *"recorded N/A rather than OK so the unbuilt half is not claimed"* | `…/code-generation/traceability.json` → `NFR4.6`; `nfr-requirements/reliability-requirements.md` § NFR4.6; `app/static/index.html`, `tests/test_page.py` | **Unverified** — owning work is `u3-analytics-view`'s own code-generation + build-and-test pass, which is **not** a validation stage, so it cannot be deferred | 
| **`NFR4.7`** | same | **no silent retry**; an out-of-order late response from a superseded range is **discarded** | **not executable in this Unit** — the named instrument `AC6.5.2` needs a **range control** to supersede, which is `u3-analytics-view`'s deliverable. The *participating* half is delivered and asserted: exactly one summary fetch, no retry | `tests/test_page.py`; `…/code-generation/traceability.json` → `NFR4.7` | **Unverified** — owning work is `u3-analytics-view`'s own code-generation + build-and-test pass, which is **not** a validation stage |
| `NFR8.1` | `nfr-requirements/observability-requirements.md` § Logging | failure **visible through the module logger**, never swallowed, never `print()`ed | a provoked storage failure emits a log record through the module logger; `print()` appears **0** times in all 15 modules of `app/` | `::test_a_storage_failure_is_logged_through_the_module_logger_with_its_code`; `security-test-instructions.md` §3.1 check 5 | — executed here | **Met** |
| `NFR8.2` | same | the machine code travels on the envelope **and** appears in the log | the same test asserts both halves | `::test_a_storage_failure_is_logged_through_the_module_logger_with_its_code`; `code-summary.md` § Deviations (e) records the defect this target found and its fix | — executed here | **Met** |
| `NFR8.3` | same | **no parameter interpolated into statement text; no credential in any log record** | 0 statement texts built at call time; 0 credential-shaped literals; redaction assertions (reprs, `record.__dict__`, `/`, `/v1/health`, `/auth/status` bodies) green | `security-test-instructions.md` §3.1 checks 2–3 and 6; `tests/test_config.py::test_the_key_is_never_rendered_or_logged` | — executed here | **Met** |
| `NFR9.1` | `nfr-requirements/scalability-requirements.md` § Load profile | **series length equals the UTC days in the resolved range**; an empty range returns an empty series | 365 entries for 365 days; gap days zero-filled; an unmatched range returns `[]` | `::test_the_unbounded_series_length_is_the_fixture_span_not_the_row_count`; `::test_a_day_with_no_rows_inside_a_matched_range_is_zero_filled`; `::test_summary_over_a_range_matching_no_rows_is_an_empty_success` | — executed here | **Met** |
| `NFR9.2` | same | **no response grows with the store**; ≤ `limit` entries **per list** | default 10 per list; an oversized `limit` honoured, never clamped; a label with no rows → `[]` | `::test_the_default_limit_is_ten_per_list_and_an_oversized_one_is_honoured`; `::test_terms_honours_the_limit_per_list_without_clamping_an_oversized_one` | — executed here | **Met** |
| `NFR9.3` | same | the unbounded series is **capped by nothing, deliberately** | no cap imposed; the unbounded range resolves to the earliest stored UTC day through today and its length equals that span | `::test_an_unbounded_read_runs_from_the_earliest_stored_day_through_today`; `::test_summary_with_neither_bound_runs_from_the_earliest_stored_day_through_today` | — executed here | **Met** |
| `NFR9.4` | same | **statement count does not grow with the range span** | 1 at 7 days, 1 at 365 days | `::test_the_statement_count_does_not_grow_with_the_number_of_days` (same instrument as `NFR1.3`) | — executed here | **Met** |

### 5.1 Nothing is deferred to a later stage

No target's Actual reads "pending a later stage". Two targets are `Unverified` because
they are **not executable in this Unit** and because the work that would execute them
is **not a validation stage**:

* No deferral under the stage's clause, which requires a *deployed or production-like
  environment* **and** a later validation stage that explicitly owns the check. Neither
  `NFR4.6` nor `NFR4.7` needs a deployed environment — they need markup and a control
  that a *later Bolt of this same stage* must build. `ci-pipeline` and the Operation
  stages, including `performance-validation`, own neither of them.
* `NFR4.6` and `NFR4.7` are therefore `Unverified`, not "deferred successfully", and
  they **cannot contribute to a successful stage result**.

## 6. Failure handling — the escalation ladder, walked in order

The failure predicate fired: two applicable targets are `Unverified`.

### Rung 1 — in-stage fix (max 2 attempts)

| Attempt | What | Outcome |
|---|---|---|
| 1 | Fix the failing command. The one failing test was traced to `APPIMAGE` corrupting `sys.executable`; fixed with `env -u APPIMAGE`. | **Resolved** — 192 passed. Environment-setup change only; no file edited. |
| 2 | Find an in-stage fix for `NFR4.6` / `NFR4.7`. | **None exists.** Both need deliverable markup this Unit does not own and must not build: a second analytics section (`NFR4.6`) and a range control (`NFR4.7`), both `u3-analytics-view`'s per `unit-of-work-story-map.md`'s cross-cutting table. Adding a test against markup that does not exist would assert nothing. No test file was added. |

### Rung 2 — classify and estimate impact

* **Root cause location:** **upstream, and outside generated source.** It is a *scope and
  sequencing* decision recorded in `inception/units-generation/unit-of-work.md` and
  `unit-of-work-story-map.md`, combined with `nfr-requirements/reliability-requirements.md`
  hanging `NFR4.6` / `NFR4.7` partly on this Unit ("the rule participates in this unit's
  summary region") while naming instruments that only `u3-analytics-view` can satisfy.
  Code Generation detected the same thing and recorded both as `N/A` with the honest
  reason rather than claiming them.
* **Swappable-dimension search:** performed across the dimensions the ladder names —
  library/version, container image, instance type, algorithm, flag. **No identifiable
  fix exists in any of them.** No dependency, image, driver or flag change creates a
  second analytics section or a range control. Declaring a feasible path out of scope on
  an unestimated-effort assumption is forbidden, so the impact of each *real* candidate
  path is estimated below instead.
* **Therefore rung 3's precondition ("an impact-estimated fix exists") is not met.**

### Candidate paths, each with its estimated impact

| Path | What it means | Estimated impact |
|---|---|---|
| **A. Accept the two `Unverified` verdicts for this Bolt** and carry them to `u3-analytics-view`'s own code-generation + build-and-test pass, where `AC6.5.2`/`AC6.5.3`/`AC6.5.5` become buildable. | Nothing changes in code or sequence; the walking-skeleton checkpoint records two open targets. | **Effort:** one line in the checkpoint record. **Cost:** £0. **Risk:** the two view-reliability behaviours ship without having been verified anywhere until Bolt 3; if Bolt 3 slips, they ship unverified. **Reversibility:** full — they are verified or not at Bolt 3 either way. |
| **B. Re-run Delivery Planning to sequence `u2-term-extraction` (and then `u3-analytics-view`) ahead of `u1-analytics-slice`'s view half.** | Fixes the sequencing fault Code Generation's R-02 already identified as lying in Delivery Planning's Bolt order. | **Effort:** a Delivery Planning re-run plus a replay of the affected Bolts. **Cost:** £0 in tooling; the whole of Bolt 1's already-approved code-generation and its reviews must be replayed forward (Modify, never Redo). **Risk:** high — it re-opens a settled Bolt and invalidates current-attempt reviews (`STAGE_JUMPED` invalidates the prior reviews, and approval fails without replacements). **Reversibility:** poor mid-replay. |
| **C. Build the second analytics section and the range control inside `u1-analytics-slice` now.** | Makes `NFR4.6` / `NFR4.7` executable immediately. | **Effort:** ~2 × the size of the slice's existing view work (three story groups' worth). **Cost:** £0. **Risk:** high and structural — it duplicates `u3-analytics-view`'s deliverable inside U1, deepens the boundary violation R-02 already discloses, and would need `u3-analytics-view` to adopt the markup, repeating exactly the mistake `code-summary.md` § R-02 criticises for `app/terms.py`. **Reversibility:** poor. |
| **D. Rewrite the recorded verification command to use a venv**, so step 1 stops failing on externally-managed hosts. | Removes the PEP 668 noise permanently. | **Effort:** minutes. **Cost:** £0. **Risk:** low — but it edits a **human-approved** Delivery Planning artifact, which is not this stage's to rewrite silently. **Reversibility:** full. |

### Rung 3 — autonomous bounded loop-back: **did not fire**

Mode is `autonomous`, but rung 3 requires *an impact-estimated fix in a swappable
dimension*, and rung 2 established that none exists. The two remaining paths (B and C)
are large re-openings of settled work, not swappable-dimension repairs, and choosing
between them is a human judgement about delivery order. No jump was performed.

### Rung 4 — halt-and-ask: **fired**

No identifiable fix exists in a swappable dimension, so this is the **no-fix variant**:
the "Retry with fix" option is **deliberately not offered**, because offering it would
mean inventing a fix to retry with. The decision belongs to the human, and it is a
question about delivery order rather than about code.

**Halt-and-ask question, for the human:**

> Build and Test on `u1-analytics-slice` is green on every executed command — 192 tests
> pass, whole-application coverage 97.06 % against an 80 % floor, and 24 of 26 measurable
> NFR targets are `Met`. Two targets are `Unverified`: `NFR4.6` (per-section graceful
> degradation) and `NFR4.7` (no silent retry; out-of-order response discarded). Neither
> can be executed here, because both need the second analytics section and the date-range
> control that `u3-analytics-view` owns, and no validation stage in the current plan owns
> them either. How would you like to proceed?
>
> - **A. Accept** — carry both as `Unverified` into `u3-analytics-view`, where their
>   acceptance criteria become buildable. Impact: minutes of record-keeping, £0, and the
>   two behaviours stay unverified until Bolt 3.
> - **B. Re-run Delivery Planning** to put `u2-term-extraction` and the view work ahead of
>   this Bolt's terms/view halves. Impact: a Delivery Planning re-run and a forward replay
>   of Bolt 1 with fresh reviews; invalidates current-attempt reviews; poor reversibility.
> - **C. Absorb the view work into this Bolt** so both targets are verifiable now.
>   Impact: roughly double this Unit's view work; duplicates `u3-analytics-view`'s
>   deliverable and deepens the disclosed unit-boundary violation; poor reversibility.
> - **D. Rewrite the recorded verification command** to install into a venv, so PEP 668
>   stops blocking its first step on externally-managed hosts. Impact: minutes, £0, fully
>   reversible — but it edits a human-approved Delivery Planning artifact, so it needs
>   your approval.

### Halt-and-ask resolution — the human's decision

**Accepted: option A.** The human was shown all four impact-estimated paths and chose
**Accept** — carry `NFR4.6` and `NFR4.7` as `Unverified` into `u3-analytics-view`, whose
deliverables make their acceptance criteria buildable. Option D was **not** taken.

What this resolution does and does not do:

- `NFR4.6` and `NFR4.7` keep the verdict **`Unverified`**. Nothing here reclassifies them,
  and the acceptance does not make them `Met` — it records *who* verifies them and when.
- The stage's **failure predicate still fired**, and this record says so rather than
  reclassifying the outcome. What the decision supplies is the missing ownership that rung2
  identified: the targets now have a named owning Unit instead of no owner at all.
- The debt is explicit and carried forward: **both behaviours are unverified until Bolt 3**
  (`u3-analytics-view`) completes its code generation and its own Build and Test pass.
  `u3-analytics-view` must treat `NFR4.6` and `NFR4.7` as inbound requirements, not as new
  work discovered there.
- Option D remains open and undone: the recorded verification command still fails its first
  step on externally-managed hosts. That is recorded in `build-instructions.md` with the venv
  remedy and its evidence, and it is **not** treated as a pass.

## 7. Loop-Back Log

**No autonomous loop-back was performed, so this ledger holds zero entries.** The
counter (the count of `### Loop-back N` entries, maximum 3 per intent) is therefore
**0 / 3** and the bound is not exhausted.

| Rung | Fired? | Why |
|---|---|---|
| 1 — in-stage fix | **Yes, twice** | attempt 1 resolved the failing command (the `APPIMAGE` environment fix); attempt 2 found no in-stage fix for the two `Unverified` targets |
| 2 — classify and estimate impact | **Yes** | root cause located upstream in the unit split; no fix in a swappable dimension; four candidate paths impact-estimated |
| 3 — autonomous bounded loop-back | **No** | its precondition — an impact-estimated fix in a swappable dimension — is not met |
| 4 — halt-and-ask | **Yes** | no identifiable fix in a swappable dimension; the no-fix variant is presented in §6 and the decision is the human's |

If a future run does loop back, this section is **append-only**: one
`### Loop-back N — <ISO timestamp>` entry per attempt carrying Diagnosis /
Root-cause stage / Planned fix / Estimated impact, and Build and Test must re-enter with
**Modify** (never **Redo**, which would erase this ledger).