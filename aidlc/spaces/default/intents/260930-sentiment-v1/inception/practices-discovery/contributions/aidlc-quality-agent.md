**Collaborator:** aidlc-quality-agent

## Contribution

Scope: the testing/quality angle only — what the suite actually does, what it costs,
what the `classic` 80 % floor would need, and which decisions the interview must
settle. Everything below was read or executed against the repo at HEAD `5b328fc`
(`v1-classic`), with `.venv` (CPython 3.14.7, pytest 9.1.1). No application source
was modified.

### 1. I ran the suite: it is green, and it is essentially free

- `.venv/bin/python -m pytest` → **`52 passed in 0.33s`, exit 0**.
- `git status --porcelain` shows only `aidlc/` paths dirty; `app/` and `tests/` are
  clean, so the result is attributable to the committed tree.

This closes the caveat in `evidence.md` §5 ("today's suite state is unverified") and
the matching honesty note in `code-quality-assessment.md`. Two consequences the
interview should have in hand:

1. The project's only mechanical gate — `filterwarnings = ["error"]`
   (`pyproject.toml:26-29`) — is *currently satisfied*, not aspirational. Note what
   it doubles as: any deprecation warning from FastAPI/pydantic on Python 3.14
   becomes a failure, so it is also the project's only upgrade canary, and nothing
   runs it on a change.
2. A whole-suite gate costs ~0.3 s. "There is no CI" is a decision about intent
   (platform, maintenance), not about runtime cost — a pre-push hook or an
   `addopts`-wired floor is nearly free.

### 2. Corrections to the draft (file-anchored)

1. **"52 test functions across 10 files"** (`team-practices.md` §Testing Posture)
   conflates the harness with the tests. Measured: 52 functions in **9
   `tests/test_*.py` modules** — auth_routes 12, session_auth 12, config 7,
   dummy_client 6, routes 6, service 3, db 2, repository 2, page 2 — **plus**
   `tests/conftest.py` (harness, 0 tests). The CodeKB scorecard states it precisely
   ("52 test functions across 9 modules … plus a shared harness",
   `code-quality-assessment.md` §Scorecard, §Test Suite).
2. **The `test-after`/`implement-then-test` inference stays `inferred`** and should
   not be strengthened: no Gherkin/scenario artifact exists, tests are one file per
   production module, and a snapshot cannot show ordering. But say what the suite
   *does*, because that part is observed and is what later stages must preserve:
   - In-process ASGI harness only — `asgi_request()` builds a raw scope, enters the
     app's lifespan and collects messages (`tests/conftest.py:44-127`); **no server
     is started, no `httpx`/`TestClient`** (absent by design, `tests/conftest.py:5-9`).
   - A session-scoped autouse `offline_guard` replaces `socket.socket.connect` with
     a raiser (`tests/conftest.py:129-146`) — the standing invariant that makes an
     all-dummy test run *prove* no network use.
   - `tmp_settings`/`tmp_db_path` point every test at `tmp_path`; no test reads
     `config.local.toml` or `data/sentiment.db` (`tests/conftest.py:149-168`).
   - Doubles sit only at process seams: injected `exchanger`/`clock`
     (`tests/test_session_auth.py:189`), injectable `now`
     (`tests/test_repository.py:44,82`, `tests/test_service.py:52,69`). There are
     **exactly two `monkeypatch` uses** (`tests/test_auth_routes.py:205,223`) and
     **zero mock objects** anywhere in `tests/`.
   - `tests/test_page.py` pins 9 `data-testid` automation hooks plus
     `GET /static/app.js` being served as JavaScript — the de-facto UI contract that
     `app/static/app.js` depends on and the only guard on the page.
3. **Boundary discipline (observed)** is confirmed by files read: 422 for empty text
   *with a row-count assertion of 0* (`tests/test_routes.py`), invalid `limit` →
   422 with `field == "query.limit"` and no silent clamp, newest-first ordering,
   `/health` reporting the *resolved* mode, and secret redaction asserted in repr,
   in log records and in `record.__dict__`
   (`tests/test_config.py:112-125`, `rendered.count("<redacted>") == 2`). These are
   genuine contract pins, not implementation echoes.
4. **`addopts = "-q"`** (`pyproject.toml:28`) buys quiet output at the cost of
   per-test names in a failure log — irrelevant until a pipeline parses the output,
   worth knowing when someone wires one.

### 3. The number the interview is missing: line coverage as it stands

`coverage`/`pytest-cov` are genuinely absent (not installed in `.venv`; no
`[tool.coverage]`, no `--cov`), so I measured with a throwaway stdlib probe outside
the repo (`trace.Trace` + `threading.settrace` + `dis` line starts), then deleted it.

| module | lines hit / executable | cover |
|---|---|---|
| `app/sentiment.py` | 22/24 | 91.7 % |
| `app/dummy_client.py` | 40/41 | 97.6 % |
| `app/models.py` | 47/48 | 97.9 % |
| `app/db.py` | 25/26 | 96.2 % |
| `app/config.py` | 62/68 | 91.2 % |
| `app/main.py` | 46/51 | 90.2 % |
| `app/routes.py` | 120/132 | 90.9 % |
| `app/repository.py` | 37/45 | 82.2 % |
| `app/session_auth.py` | 119/152 | 78.3 % |
| `app/service.py` | 35/52 | **67.3 %** |
| `app/__init__.py` | 3/4 | 75.0 % |
| `app/openrouter_client.py` | **0/149** | **0.0 %** (never imported) |
| **total, all 12 modules** | **556/792** | **70.2 %** |
| **total, minus the live client** | **556/643** | **86.5 %** |

Two method notes that matter for anyone re-measuring:

- The tracer must be installed on new threads (`threading.settrace`). FastAPI runs
  every endpoint here in an anyio worker thread (all handlers are sync `def`,
  `app/routes.py:82-171`); without thread tracing `app/routes.py` reads 47 %, not
  91 %. A naive in-process measurement will under-report this suite badly.
- Numbers are ± a few points against `coverage.py` (`dis` line starts vs statement
  coverage; my per-line attribution had artifacts, the aggregates did not). The
  decision-relevant gap — 70 % vs 86 % — is far outside that error.

**Reading:** whether the `classic` floor is met *today* depends entirely on the
denominator. Pinned with `--cov=app`, pytest-cov counts the never-imported live
client at 0 % and the project sits at ≈70 % → **the floor fails**. Without a source
pin (or with the live client omitted), the exercised application is at ≈86 % → **the
floor passes**. The draft's question "is the floor wanted?" is therefore really two
questions: *does the live engine count*, and *who runs the measurement*.

### 4. What an 80 % floor concretely requires (no CI exists)

1. Add the tool: `pytest-cov` (or `coverage`) to the `dev` extra
   (`pyproject.toml:17-18`, currently only `pytest>=8`). Runtime dependency count
   stays at the capped two — NFR3 is a runtime cap, not a dev-tool cap; the interview
   should still confirm that reading.
2. Pin the denominator: `[tool.coverage.run] source = ["app"]` (or `--cov=app`) plus
   an explicit `omit = ["app/openrouter_client.py"]` **with the reason recorded**, or
   accept a lower, honest floor. Note the team already writes coverage pragmas
   without a coverage tool — `app/repository.py:20`, `app/service.py:75`,
   `tests/test_config.py:128` — so the convention exists and only needs a policy.
3. Wire it where it will actually run. Because there is no pipeline, the cheapest
   real gate is `addopts = "--cov=app --cov-fail-under=80"` in
   `[tool.pytest.ini_options]` (`pyproject.toml:26-29`): a bare `pytest` then fails
   locally, at ~1 s total cost, with no CI at all. A pipeline (install + pytest) or a
   pre-push hook is the alternative answer.
4. Say who verifies it. Org rules already put the floor on Build and Test ("Build and
   Test verifies defined coverage floors"), so the floor needs a *local* enforcement
   point to be meaningful mid-Bolt.

### 5. Exclusions that are deliberate — affirm them, don't "fix" them

- **Live engine**: never imported, constructed or called by the suite; the
  offline guard makes it structural (`tests/conftest.py:129-146`; the lazy import at
  `app/service.py:74-82` exists so "no test run touches it"). README "Notes"
  documents the substitute coverage (code review + a manual live smoke run).
- **PKCE exchange**: `exchange_code_at_openrouter()` (`app/session_auth.py:78-121`)
  is unexecuted by design; the flow is tested through `FakeExchanger`
  (`tests/test_session_auth.py:189`).
- **Browser script**: `app/static/app.js` is never executed; `tests/test_page.py:4-6`
  says so and cites the dependency cap.

If v1 keeps these exclusions, the interview must still name **who runs the manual
live smoke run and when** (pre-merge? pre-release?) — the suite cannot, and the draft
is right to ask.

### 6. Real gaps no exclusion explains

- **`app/service.py` 67 %**: the uncovered remainder is the live-mode branch (lazy
  import + `OpenRouterClient` construction, `app/service.py:74-90`) — structural, and
  the straight consequence of §5.
- **Two 502 handlers** (`app/routes.py:199-213`) appear unexercised by my
  approximation (line-level attribution is the part I trust least — worth a direct
  check with real coverage before anyone acts on it).
- **No concurrency test exists at all**: `grep -rn "thread\|concurrent\|ProgrammingError" tests/` returns nothing, while R-01 (per-request `sqlite3.connect` on default
  thread affinity, `app/routes.py:70-76`, `app/db.py:51-63`) is the one defect this
  workspace has ever recorded. I did not re-run the scenario — the record is ground
  truth. So the draft's question "must a reproducing test land with a bug fix?" has a
  concrete, already-relevant example behind it.
- **No test starts uvicorn or proves `uvicorn app:app` resolves**; the import path is
  only exercised indirectly through `from app.main import create_app`. End-to-end
  proof lives entirely in the previous intent's live smoke run — which is exactly why
  a recorded Construction Verification Command (still unset in
  `aidlc-state.md`) should include a live run, not just `pytest`.
- **Coverage regressions are invisible**: with no measurement and no runner, a
  change can delete tests or break the live path silently.

### 7. Test patterns a practice line should capture (each cited)

1. Every database-touching test uses `tmp_path`; never `data/sentiment.db`
   (`tests/conftest.py:149-168`).
2. Assertions read values back out of real SQLite and the served markup — not out of
   mocks (`tests/test_routes.py` row-count reads, `tests/test_repository.py`,
   `tests/test_page.py`).
3. Doubles only at process boundaries — clock, PKCE exchange, `now`
   (`tests/test_session_auth.py:189`, `tests/test_repository.py:44,82`,
   `tests/test_service.py:52,69`).
4. The offline guard is a standing invariant, not a per-test choice
   (`tests/conftest.py:129-146`).
5. Error-contract assertions name the offending field (`query.limit`) and assert no
   write happened, not merely the status code (`tests/test_routes.py`).
6. Redaction is asserted in all three leak surfaces: repr, log records and endpoint
   bodies (`tests/test_config.py:112-125`,
   `tests/test_auth_routes.py::test_no_endpoint_ever_exposes_the_key`).
7. The page contract is `data-testid` hooks + asset serving (`tests/test_page.py`).
8. `filterwarnings = ["error"]` — keep it (it is the only gate there is), and accept
   that dependency bumps must run the suite.

### 8. Interview decisions, in answerable form

1. **Coverage denominator.** Does the 80 % floor count the live engine that the suite
   deliberately never imports? "Yes, count everything" → the floor fails today
   (~70 %) and needs new tests or a recorded exclusion. "Count only exercised code"
   → ~86 % today and the work is wiring.
2. **Who measures and when.** `pytest-cov` in `addopts` (runs on every bare `pytest`,
   ~1 s, no CI), a pre-push hook, or a code-only pipeline (install + pytest)? The
   suite costs 0.33 s, so cost is not the reason to say no.
3. **Bug regressions.** Must every defect ship a reproducing test? If yes, R-01
   (thread affinity) is an immediate backlog item: there is no concurrency test in
   the suite today. If no, record how a defect without a requirement is dispositioned
   (that is literally what happened last time).
4. **The three structural exclusions.** Live engine, PKCE exchange, browser script —
   keep all three as policy? And who runs the manual live smoke run, at which point?
5. **Dev-tool dependency cap.** Is adding `pytest-cov` (and optionally `ruff`) to the
   `dev` extra acceptable? NFR3 caps *runtime* dependencies at two; the dev extra
   holds only `pytest` today. Objective fact for that answer: `ruff 0.16.9` already
   exists on this machine (`/usr/bin/ruff`) and the venv has no coverage tool, so a
   lint trial costs no manifest change while a coverage floor does.
6. **Recorded verification command.** Should the intent's still-unset Construction
   Verification Command be fixed now as "install + `pytest` + a local live smoke run"
   so Build and Test proves each unit the same way (the suite alone never starts a
   server)?

### 9. What answers would change my assessment

- If the floor counts `--cov=app` including the live client, the current suite **fails
  the scope's floor** and adding a scoped test for the live client's pure typed readers
  (`_read_choice`/`_read_score` — the CodeKB's recommendation 1) becomes required
  work, not optional; if it excludes the live client, no new tests are required at
  all.
- If the team affirms anything stricter than test-after (TDD/test-first, or "every
  defect ships a test"), my ordering statement and the R-01 disposition both change:
  R-01 becomes an open, currently-untested defect rather than a closed accepted risk.
- If they choose a pipeline over local `addopts`, the floor becomes enforceable at
  merge but stays unenforceable mid-Bolt — my §4 wiring recommendation flips to the
  pipeline.
- If they keep the live engine as a *supported* v1 mode rather than a carry-over,
  the 0 % module is no longer acceptable under any denominator and the exclusions in
  §5 must be revisited.

## Positions

- AGREE: The pytest-only framework, layout and config claims — `testpaths`, `addopts = "-q"`, `filterwarnings = ["error"]` are exactly as `pyproject.toml:26-29` states, and I confirmed the suite also *passes* (`52 passed in 0.33s`).
- AGREE: "Coverage (observed): not measured at all … nothing in the repository can currently verify it" — verified in `pyproject.toml`, the `dev` extra, and the installed `.venv` package list; the draft should now carry the measured numbers instead of leaving the question blind.
- AGREE: "Regression policy (needs human decision)" and the no-CI framing — nothing runs the suite on a change; the choice is intent, not cost.
- AGREE: The two untested surfaces are stated accurately and with the right cause (offline guard is structural; `app.js` is unexecuted by design), and the draft correctly refuses to call the 80 % floor an observed project practice — it is a framework default for `classic`.
- AGREE: The walking-skeleton reading (scope flag decides; end-to-end verification is nevertheless real and manual) is consistent with the one live smoke run on record and with the unset Construction Verification Command.
- OBJECT: "52 test functions across 10 files" — imprecise; it is 52 in 9 `tests/test_*.py` modules plus the `conftest.py` harness (0 tests), as the CodeKB scorecard itself words it.
- OBJECT: Presenting the coverage question (draft Testing Posture, "Coverage", and open question 2) with no measured value — the runnable facts are ~70 % including the never-imported live client and ~86 % without it, which turn "do you want the floor?" into "what counts in the denominator?", the actual decision.
- OBJECT: "No tests against live external services, no browser execution, no performance tests" omits **no concurrency test**, the one gap that maps onto a defect this workspace already recorded and accepted (R-01); the regression-policy question should be answered against that precedent.
