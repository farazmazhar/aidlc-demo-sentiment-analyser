# Code Generation Plan — `u2-term-extraction`

> **Unit:** `u2-term-extraction` (kind `library`) · **the resolved walking skeleton.**
> **This is an ADOPTION, not a build.** `app/terms.py` already exists and already
> satisfies every item of this Bolt's Definition of Done. Nothing in this plan
> writes it from scratch; the steps verify the inherited module against the
> specification, record what this unit now owns, and close the one code defect a
> review found.
>
> **Methodology:** custom — acceptance- and API-level tests are written against the
> requirement **before** the implementation; lower-level unit tests are written
> **after**. Both already exist for this unit (10 tests in `tests/test_terms.py`),
> written under U1 when the module was built. Step 1 confirms their runner; no
> Red/Green cycle is planned, because this posture is not TDD.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "Acceptance- and API-level tests are written against the requirement or acceptance criterion before the implementation, and lower-level unit tests are written after the implementation.",
  "scope": "feature",
  "test_strategy": "standard",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Ordering**: Acceptance- and API-level tests are written against the requirement or acceptance criterion before the implementation, and lower-level unit tests are written after the implementation.\n\nBoth fields carry the 2026-09-30 affirmed answer unchanged, and the 2026-10-02\ninterview did not disturb them. `custom` is the right label because the answer mixes\ncadences, and the mix is visible in the artifact: API/acceptance level in\n`test_routes` (15), `test_bulk_import` (16), `test_auth_routes` (12), `test_page`\n(4); lower-level unit level in `test_db` (8), `test_repository` (8), `test_service`\n(9), `test_live_client` (9).\n\nWe state the limit of that corroboration plainly, because it is the honest reading:\n**the repository corroborates both test *levels*, and cannot corroborate the test\n*order*.** Two squashed commits, no surviving branch and no intra-commit ordering\nmeans the history physically destroys the evidence of which test was written first.\nThe ordering sentence is affirmed team practice carried forward on the human's\nauthority, not a conclusion drawn from the code.\n\n**Framework and configuration** (measured at `beeb587`, `.venv` CPython 3.14.7):\n`pytest` only — no `unittest`, no `hypothesis`, no `asyncio` marker.\n`[tool.pytest.ini_options]` sets `testpaths = [\"tests\"]`,\n`addopts = \"-q --cov=app --cov-report=term-missing --cov-fail-under=80\"`, and\n`filterwarnings = [\"error\"]`.\n\n> **Correction to our own earlier description.** We called the warnings filter \"the\n> project's only deprecation canary — a FastAPI or pydantic deprecation on 3.14 is a\n> hard failure.\" **That was too narrow.** `filterwarnings = [\"error\"]` promotes\n> **every** warning from **every** source to a suite failure: pytest's own\n> deprecations, a transitive `DeprecationWarning`, a `ResourceWarning`. Combined\n> with the second fact — there is no lockfile, so the installed toolchain sits **two\n> major versions past every declared floor** (`pytest 9.1.1` against `>=8`,\n> `pytest-cov 7.1.0` against `>=5`, `starlette 1.7.0`, `pydantic 2.13.5`) — the\n> suite's pass/fail state is a function of **the resolved dependency set, not of the\n> code**. A fresh `pip install -e \".[dev]\"` on any other machine resolves something\n> different. That is not a hypothetical; it is the normal state of this manifest\n> today, and it is the single strongest technical argument for the lockfile decided\n> under `## Deployment`.\n\n**Coverage** (affirmed; line coverage only, confirmed 2026-10-02):\n\n- **The whole application is measured** — `[tool.coverage.run] source = [\"app\"]`,\n  including the live client the offline suite does not import.\n- **The floor is 80 % lines**, stated twice so it cannot be skipped by forgetting a\n  flag: in `addopts` (`--cov-fail-under=80`) and in `[tool.coverage.report]\n  fail_under = 80`. `show_missing = true`. It is a genuinely enforcing gate, not a\n  printed notice: raising the floor to 99 on the command line makes the run exit 1.\n- **Branch coverage stays off** (2026-10-02). We measured what turning it on would\n  reveal: 98 branches, **3 partial** — `app/db.py:208`, `app/main.py:49`, and the\n  partial edge `app/routes.py:385->387` — none of which the 80 % line floor can see.\n  We are recording the cost of the decision as well as the decision, because line\n  coverage is the weakest signal available for a feature made of conditional\n  aggregation over a date range: every `if` whose false branch is never taken still\n  counts as covered.\n- **Measured now: `118 passed`, 679 statements, 27 missed, `96.02 %`.**\n\n**(Correction)** Our baseline recorded the floor as *failing* — *\"556/792 lines =\n70.2 % across all 12 application modules\"*, *\"the floor therefore fails today\"*.\nThat work is done. `tests/test_live_client.py` (9 functions) covers the\nanswer-reading side of the live engine through an injected transport, so\n`app/openrouter_client.py` reads **92 %** rather than 0 %. The floor now passes\nwith about 16 points of headroom. The whole count also moved — 679 measured\nstatements against the baseline's 792.\n\n**Test surface** (measured): **118 collected tests from 109 test functions**,\nexpanded by 5 parametrization sites, across **11 `tests/test_*.py` modules** plus\n`tests/conftest.py` (176 lines, harness only). Per module: `test_routes` 15,\n`test_bulk_import` 16, `test_auth_routes` 12, `test_session_auth` 12, `test_config`\n10, `test_service` 9, `test_live_client` 9, `test_db` 8, `test_repository` 8,\n`test_dummy_client` 6, `test_page` 4. Our baseline's \"52 tests in 9 modules, 52\npassed in 0.33 s\" is twice-stale; any later stage citing it will be wrong.\n\n**All 11 test modules pass standalone.** The suite is order-independent *and*\nmodule-independent, not merely green in aggregate. That is the property that makes\nan automatic gate safe to trust here, and it is the strongest available argument for\nturning the gates on. A full suite run with coverage costs **about 1.1 seconds**;\ncost is not a reason to leave the gates opt-in.\n\n**Test doubles policy** (unchanged, and still the strongest thing about this suite):\nassertions read values back out of real SQLite and real served markup, never out of\ndoubles. **Zero mock objects** — no `unittest.mock`, no `unittest` at all; eight\nhand-written classes (`FakeExchanger`, `StubTransport`, `DuckTypedClient`,\n`FailingOnBoomClient`, `IncompleteClient`, `UnsupportedLabelClient`,\n`RejectingClient`, `FailingClient`) sit at real process seams. `monkeypatch` **is**\nour sanctioned substitution instrument, used at the consumer's import name\n(`monkeypatch.setattr(\"app.routes.get_client\", …)`) — so \"zero mock objects\" must\nnever be promoted to \"no substitution\". The session-scoped autouse `offline_guard`\nreplaces `socket.socket.connect` with a raiser, and\n**`tests/test_dummy_client.py` actively proves the guard is armed**, so a\nsilently-broken guard cannot make the suite pass while it reaches the network.\n`tmp_path`-scoped settings and DB paths mean no test reads `config.local.toml` or\n`data/sentiment.db`, and `tests/test_config.py` shells out to `git check-ignore` as\nan executable assertion that the key file cannot be committed.\n\n**Boundary discipline** (unchanged): a refusal that half-succeeded would fail,\nbecause row-count assertions of 0 accompany the status-code assertions. `limit`\nbelow 1 or non-numeric answers `422` naming `field == \"query.limit\"`, never a\nsilent clamp; history is newest-first; `/v1/health` reports the resolved mode;\nsecret redaction is asserted in reprs, in log records including `record.__dict__`,\nand in the `/`, `/v1/health` and `/auth/status` bodies.\n\n### Where the gates run — decided 2026-10-02\n\n**The three gates — the whole-application 80 % coverage floor, the\nwarnings-as-errors filter, and the pinned `ruff` rule set — run from a\nplatform-neutral verification script (or make target) that the developer runs.**\nNot a pre-commit hook. Not a provider CI job. Both rejected by name, and both now\nrules in `discovered-rules.md`.\n\nThe options were not peers, and the reason is worth keeping so nobody reopens the\nquestion as if they were: **`git remote -v` is empty and there is no CI provider of\nany kind.** A provider workflow file written today would be a file that has never\nexecuted and cannot execute until a remote exists. A pre-commit hook is real and\nlocal, but it never sees a dependency bump and never runs in CI, so it cannot be the\nwhole gate. A script that a human and any future CI job can both call is the only\noption that is true today and stays true on any host.\n\n**What the gate cannot yet express.** `pyproject.toml` configures **no\nmachine-readable output at all**: `-q` means a default run prints dots and no test\nnames, `--cov-report=term-missing` is a human table, and there is no\n`--junit-xml`, no coverage XML and no `-ra`. So per-test annotations have nothing\nto consume, a flaky-test list cannot be produced, and — the one that matters most —\n**\"coverage did not decrease\" is not expressible as a gate today**, because there is\nno coverage artifact to diff against the previous run. That is the first gate of the\nstandard quality-gate set and it is currently unbuildable.\n\n**One precondition nobody had written down**: the suite needs a git working tree. A\nfull source tree copied without `.git` gives 117 passed / 1 failed, because\n`git check-ignore` exits 128 and `tests/test_config.py`'s `shutil.which(\"git\")`\nguard covers git-absent, not git-present-but-not-a-checkout. Any gate that receives\nsource without `.git` goes red with a message that reads like a credential leak.\n\n### Every defect ships a reproducing test — decided 2026-10-02\n\n**Yes. Every defect we fix ships with a test that reproduces it.** This closes a\nquestion that had been open since 2026-09-30, and it reverses the standing precedent:\nR-01, the cross-thread SQLite connection defect, was recorded and accepted with no\ntest reproducing it. Under this policy R-01's exception is closed too.\n\nThe answer has a prerequisite, and it is not \"add a test\":\n`tests/conftest.py:136` calls `asyncio.run` per request, so every API test runs on\na fresh event loop, single-threaded and strictly sequential. **No test written\nagainst today's harness can reproduce R-01, however carefully written** — the fix is\na different harness shape (a real `uvicorn` on a loopback port, or explicit\nthreads), and that harness work comes first. The page this intent adds polls on a\ndate range, which is the access pattern most likely to trigger the defect, so the\ngap is on this work's critical path rather than in the far distance.\n\n### Computed numbers get hand-written expected values — decided 2026-10-02\n\n**Hand-written expected values, stated per requirement, for the analytics\naggregates — and a test that the new indexes survive a migration**, by inspecting\n`sqlite_master`. Both halves are rules.\n\nThe reason is a measurement, not a preference. There is **no `AVG(`, no\n`GROUP BY`, no `strftime(` and no `json_extract`** anywhere in `app/` or `tests/`\ntoday; the only SQL in the suite is `SELECT COUNT(*) FROM analyses`, used for\nrow-count assertions. So the 96.02 % figure says nothing whatsoever about whether a\ndate bucket, an average, a NULL `confidence` or an empty date range is computed\ncorrectly. A `strftime` bucket boundary off by one day at the UTC edge — given\n`repository.py:41` normalises to `%Y-%m-%dT%H:%M:%SZ` — would leave the suite fully\ngreen and the floor fully satisfied.\n\nThe second half is a known-dormant loss rather than an accepted one. `_rebuild_analyses`\n(`app/db.py:233`) does `RENAME` → `CREATE TABLE` → `COPY` → `DROP TABLE`, and\n`CREATE_ANALYSES_TABLE` declares **no index at all** — so an index added to that\nDDL is silently destroyed on any migrating store, with no warning possible. The\nsuite contains no `CREATE INDEX` and no assertion over\n`sqlite_master WHERE type='index'`; the single `sqlite_master` assertion\n(`test_db.py:103`) filters `type = 'table'` only. **No warning is possible,\nbecause the only implementation that drops them is one the suite never inspects\nafterwards.** This intent adds indexes and a v3 → v4 migration, so it will trigger\nit.\n\n### Explicitly untested, by design\n\n- **No browser execution at all.** `app/static/app.js` is served and its markup is\n  pinned; nothing in the suite runs it. `tests/test_page.py:1-6` states the reason.\n- **The two production HTTP transports** — `app/session_auth.py:84-120` (17\n  statements) and `app/openrouter_client.py:89-96` (6 statements), 23 of the 27\n  missed lines. Every test injects a transport or an exchanger, because the\n  dependency cap forbids an HTTP client library.\n- **No concurrency test whatsoever.** `grep -niE 'thread|concurren|parallel'` over\n  `tests/` returns nothing — and, per the ruling above, the harness cannot host one\n  in its present shape.\n- Three single-line misses remain: a `csv.Error` branch, a `PRAGMA table_info`\n  absence guard, and a logging-handler guard.\n\n**The verification command** (affirmed): **install** (`python -m pip install -e\n\".[dev]\"`), **run `pytest`**, then **start the app locally and exercise the changed\npath**. The README records it as a single copy-paste line that installs, runs the\nsuite with the floor applied, boots uvicorn on `127.0.0.1:8141` and reads\n`/v1/health`. Still necessary: the suite never starts a server and never resolves\n`uvicorn app:app`."
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Meet an 80% line-coverage floor.",
      "Run the selected tests in CI before merge."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "custom",
    "runner_step": "Verify the existing test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Verify the existing test runner/configuration and record the exact unit-scoped command.",
      "Custom ordering - Acceptance- and API-level tests are written against the requirement or acceptance criterion before the implementation, and lower-level unit tests are written after the implementation.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:86a0f8ed6743fb53d412015623e8b25dd177695bd0788ebdde0d5e69ec70c7c7",
  "contract_sha256": "sha256:4fa6a564e29604c2aea16a539170f0b5269f0d608f83106f4fd8b316b34d7b75"
}
```

## Plan steps

- [x] **Step 1 — Verify the test runner.** Confirm the unit-scoped command runs green on the adopted module before any change. `tests/test_terms.py`, 10 tests.
- [x] **Step 2 — Adoption boundary.** Record what this unit now *owns* versus what it *inherits*: the five names are U2's, the parity and isolation tests are U2's inherited evidence, and the offline engine's `tokenize`-only import is U2's to keep. No file is rewritten to accomplish this; the ownership moves in the record.
- [x] **Step 3 — Close the R-01 code defect.** `significant_terms` compared `token not in STOPWORDS` without lowercasing, while `BR3.2` requires a case-insensitive test. Verified reachable only by a caller passing mixed-case tokens (the real path always lowercases first), and fixed because the operation's declared domain is any `Sequence[str]`.
- [x] **Step 4 — Verify the two-operation split holds.** Assert the engine consumes `tokenize` alone and that `significant_terms` is absent from the engine's source, so the analytics filter is structurally unable to reach sentiment scoring.
- [x] **Step 5 — Verify scoring parity.** Confirm the engine's output is unchanged, and confirm the parity test has an instrument to complement it — an ordinary corpus cannot distinguish "filter applied" from "not applied" here, because no keyword is a stopword and the shortest keyword is exactly `MIN_TERM_LENGTH`.
- [x] **Step 6 — Verify the constants.** `TOKEN_PATTERN`, `MIN_TERM_LENGTH` and `STOPWORDS` are module-level, typed, SCREAMING_SNAKE_CASE, and owned here; `STOPWORDS` holds 134 words and contains no sentiment-bearing term.
- [x] **Step 7 — Verify the leaf boundary.** The module imports nothing from `app` and performs no I/O. Re-checked after the Step 3 edit, because an edit is how a leaf acquires an import.
- [x] **Step 8 — Coverage and the verification command.** Hold the whole-application line floor with this module counted, and run the intent-level verification command.

## Step-to-criterion traceability

| Step | Criteria |
|---|---|
| 1 | `AC4.1.*`, `AC4.2.*` (runner readiness) |
| 2 | `AC4.2.1`, `AC4.2.3` |
| 3 | `AC4.1.2` |
| 4 | `AC4.2.2`, `AC4.2.3` |
| 5 | `AC4.2.2` |
| 6 | `AC4.1.1`, `AC4.1.4`, `AC8.6.1` |
| 7 | `AC8.2.1`, `AC8.2.3`, `BR6.1` |
| 8 | `NFR7` |

## Out of scope for this unit

Counting, ranking and the `limit` cap belong to `AnalyticsRead` in `u1-analytics-slice`.
The store is U1's. Non-Latin scripts contributing nothing is a recorded accepted
limitation, not a gap to close here (`AC4.1.3`).
