# Code Generation Plan — `u1-application`

## Scope

One unit (`U1`, kind `service`), one Bolt, brownfield. The repository already carries twelve
application modules, ten test modules and a running page; this pass converges them onto the v1
contract in `contract-summary.md` rather than rebuilding what works. Every step below is a change to
running code, taken in the risk-first order Delivery Planning recorded: engine path → storage path →
failure paths → interface.

## Ordering rules applied

The Testing Contract below is custom: acceptance/API tests are written against the requirement before
the implementation they cover, and lower-level unit tests are written after each layer's
implementation. Neither is converted into layer-local TDD. Test-runner readiness (Step 1) comes
before the first executable test step, and every run command in `unit-test-instructions.md` is exact
and scoped to this unit.

## Decisions this plan fixes

The contract left four questions open; the plan answers them, so implementation never has to choose
mid-step.

| # | Open question (`contract-summary.md`) | Decision |
|---|---|---|
| D1 | Machine code and status for a live attempt with no usable key | `503` with the envelope code `LIVE_KEY_MISSING`; the message names `config.local.toml` |
| D2 | Default for an absent `limit` on `GET /v1/analyses` | `50` rows — the value `app/repository.py` already names as `DEFAULT_LIST_LIMIT`, now documented |
| D3 | Whether the `/v1` prefix also covers health | Yes: `/v1/health`. The page's own `/` and `/static/*` stay unversioned, and the `/auth/*` support routes stay unversioned as page support that carries no data contract |
| D4 | Outbound timeout for the live call | one named constant, `10` seconds, carried by the injected transport |

## Steps

### Step 1 — Baseline and test-runner readiness

*(plan-profile step 2 — runner readiness before the first test-first step.)*

- [x] Install and run the existing suite untouched — `python -m pip install -e ".[dev]"`, then
      `python -m pytest -q` — and record the green baseline (52 passed) this Bolt must keep.
- [x] Add the development tooling the stories require to `[project.optional-dependencies].dev`: the
      coverage plugin and `ruff`. Runtime dependencies stay exactly `fastapi` and `uvicorn`
      (NFR3.1, NFR3.2, AC1.1.3).
- [x] Pin the tool configuration instead of leaving it to a tool default: an explicit `[tool.ruff]`
      rule set including the security (`S`) rules, and the coverage settings (`--cov=app`,
      `--cov-fail-under=80` over the whole application) (NFR-TS1, NFR-TS2, C4, AC9.1.3).
- [x] Record every exact command in `unit-test-instructions.md` — suite, coverage, lint/format and
      the end-to-end check — and confirm each runs from the repository root.

*Trace: US1.1 (AC1.1.2, AC1.1.3), US9.1 (AC9.1.2, AC9.1.3), BR7.1, BR7.2, BR8.3.*

### Step 2 — Acceptance/API tests first: the `/v1` surface

*(plan-profile step 3 — written before the implementation that satisfies them; red until Steps 3–7 land.)*

- [x] `tests/test_routes.py`: `POST /v1/analyze` returns the stored record's exact field set — `id`,
      `text`, `label`, `probabilities` as an object keyed by label with all three labels present,
      `confidence`, `model`, `provider`, `created_at` — and no `intensity` (AC2.1.2, BR3.2, BR3.4).
- [x] `tests/test_routes.py`: empty or whitespace-only text is `422` with `INVALID_TEXT` in the app's
      one envelope, and no row is written (AC2.2.1, AC2.2.2, BR4.1, BR4.3).
- [x] `tests/test_routes.py`: `GET /v1/analyses` is newest-first; `limit=n` with n ≥ 1 returns at most
      n rows; a limit below 1 or non-numeric is `422` with `VALIDATION_FAILED` and is not silently
      changed; an absent limit applies the documented default (AC4.1.1–AC4.1.4, BR3.5, BR3.6, D2).
- [x] `tests/test_routes.py`: `GET /v1/health` reports the active mode and the connection state, with
      a reason when not connected, and never credential material (AC5.3.1, BR4.4).
- [x] `tests/test_routes.py`: a submission while live was requested with no usable key is `503` with
      `LIVE_KEY_MISSING`, its message names `config.local.toml`, and nothing is stored (AC5.2.2,
      BR1.4, BR4.3, D1).
- [x] `tests/test_routes.py`: every app-raised failure carries the one envelope, and the pre-v1 data
      paths (`/analyze`, `/analyses`, `/health`) are no longer served (BR4.2, BR4.3).

*Trace: US2.1, US2.2, US4.1, US5.2, US5.3, US8.1.*

### Step 3 — Engine path

- [x] `app/sentiment.py`: one engine interface with the typed result the contract requires — chosen
      label, a probability per label, confidence — and the validity rules that make an unreadable or
      incomplete result a failure rather than a guess (BR2.1–BR2.3, AC3.1.3).
- [x] Rename both implementations to their v1 names everywhere they are imported or constructed:
      `DummyClient` → `DummySentimentClient` (`app/dummy_client.py`) and `OpenRouterClient` →
      `OpenRouterJevSentimentClient` (`app/openrouter_client.py`), including every test that builds
      them (AC1.2.2, BR8.2).
- [x] `app/openrouter_client.py`: ask the choice question with exactly `positive`, `negative` and
      `neutral`; read the answer only as typed data; fail the attempt when the answer cannot be read
      that way; take its transport as an injected dependency carrying the one timeout constant; keep
      the credential out of every representation (BR2.1, BR2.2, BR5.1, D4, AC3.1.1, AC3.1.2).
- [x] After the implementation, the unit tests: the offline client keeps its deterministic behaviour
      under the renamed interface (`tests/test_dummy_client.py`), and a new `tests/test_live_client.py`
      drives request construction, typed-answer reading, the unreadable-answer failure and a
      provider-rejected credential through the injected transport, with no network (AC9.1.1, BR7.2).

*Trace: US3.1, US5.1, US6.1 (the rejected credential), US9.1.*

### Step 4 — Storage path and the in-place migration

- [x] `app/models.py`: drop `intensity` from `RECORD_FIELDS`, the `AnalysisRecord` dataclass and
      `to_dict()`, so the stored shape and the wire shape stay identical (BR3.2, BR3.4, AC2.1.2).
- [x] `app/db.py`: the v1 schema — `provider` present and `intensity` nullable, so a new row can leave
      the retired attribute unset — plus a startup migration that brings a pre-v1 store to it: add a
      missing column in place, rebuild the table where a column constraint must change, copy every row
      and record the applied version in `schema_meta` (BR3.1, BR3.3, AC7.1.1–AC7.1.3).
- [x] `app/repository.py`: write the v1 attribute set (no `intensity` on new rows), read a pre-v1 row
      without back-filling the retired attribute, and keep newest-first ordering with the named
      default limit (BR3.2, BR3.4, BR3.5, D2, AC7.1.4).
- [x] After the implementation, the tests: `tests/test_db.py` and `tests/test_repository.py` extend to
      a migration against a real pre-existing store created with the older shape, including a row that
      carries `intensity`, asserting the row survives and a new row leaves the attribute unset
      (AC7.1.2, AC7.1.3).

*Trace: US7.1.*

### Step 5 — Failure paths and boundary validation

- [x] `app/config.py`: resolution order — a usable session credential, then a configured live mode
      with a key, then offline; the default model `typesafe/jev-1.13`; redaction in every
      representation; and the startup warning that names `config.local.toml` when live was requested
      with no usable key, never credential material (BR1.1–BR1.3, BR1.5, BR5.1, AC5.2.1, AC5.3.3).
- [x] The live-attempt refusal: when live was requested and no key is usable, refuse the submission
      with `503` and `LIVE_KEY_MISSING` through the one envelope, name the config file, and store
      nothing (BR1.4, BR4.3, D1, AC5.2.2).
- [x] Boundary validation: empty or whitespace-only text and an invalid `limit` refuse before any
      store work, through the same envelope, and the absent-limit default is a named constant rather
      than an implementer's choice (BR3.5, BR3.6, BR4.1, BR4.3, D2, AC2.2.1, AC4.1.3, AC4.1.4).
- [x] Update the existing test that pins today's silent fallback so that it pins the explicit refusal
      instead (AC5.2.1, AC5.2.2).
- [x] `app/service.py`: the engine dispatcher stays the one seam that publishes a request and receives
      a typed result, carries engine failures back as results, and never constructs a concrete client
      it was not handed (BR1.4, AC3.1.3).
- [x] After each layer, its tests: configuration precedence and redaction (`tests/test_config.py`),
      the refusal paths leaving the store untouched (`tests/test_service.py`), and the envelope codes
      at the boundary (`tests/test_routes.py`).

*Trace: US2.2, US5.1, US5.2, US8.1.*

### Step 6 — The interface (page)

- [x] `app/static/index.html` and `app/static/app.js`: render the five reachable states — loading,
      empty, success, invalid input and the live-attempt failure — from the health/connection payload
      and the last result (AC5.3.2, AC6.1.5).
- [x] Remove the intensity affordance from the lede and the result panel, and show which engine
      produced each result, so an offline stand-in is never mistaken for the live model (AC2.1.3,
      BR3.4).
- [x] Fix the connection indicator's contrast and target size, and announce its state changes through
      a live region instead of implying them with colour alone (AC5.3.2).
- [x] Point the page's calls at `/v1` (`/v1/analyze`, `/v1/analyses`, `/v1/health`) (BR4.2, D3).
- [x] The sign-in flow: the credential is held in memory only, never rendered or logged, discarded
      when the provider rejects it with the reason shown on the page, and each of its failure paths —
      stray callback, blank code, refused exchange, expired verifier — reports on the page and leaves
      the app usable on the offline engine (BR5.1, BR6.1, BR6.2, AC6.1.1–AC6.1.5).
- [x] After the implementation, the tests: `tests/test_page.py` for the served states and the
      announcement, and `tests/test_auth_routes.py` with `tests/test_session_auth.py` for the
      discard-and-fall-back path (AC6.1.4).

*Trace: US2.1, US5.3, US6.1.*

### Step 7 — Test configuration

*(plan-profile step 4's test configuration, kept beside the layer tests it runs.)*

- [x] `[tool.pytest.ini_options]` keeps `testpaths`, `addopts` and the `filterwarnings = ["error"]`
      gate, and gains the coverage settings so the documented command fails below the 80% line floor
      over `app/` (AC9.1.2, BR7.1).
- [x] Keep the outbound-network block in `tests/conftest.py`: the live client is exercised through
      its injected transport, and any outbound use still fails the run (AC1.1.2, BR7.2).
- [x] Keep five to eight tests per component and the integration coverage of the store and the HTTP
      boundaries, which is the Standard strategy's volume.

*Trace: US9.1, US1.1.*

### Step 8 — Environment and build configuration

*(plan-profile step 5.)*

- [x] `pyproject.toml`: exactly two runtime dependencies, the development tools under the `dev`
      extra, `config.example.toml` still placeholder-only and `config.local.toml` still gitignored
      (AC1.1.3, AC8.1.3, NFR3.1).
- [x] The server start path binds loopback only through one constant, and `data/` stays ignored and
      created on first run (BR3.1, BR5.2, AC1.1.1, AC8.1.2).
- [x] The record's verification command no longer described the project: it probed the retired
      `/health`, which now returns 404 (the architecture check reproduced `HTTP Error 404`, exit 1).
      The replacement was proposed to the human and recorded through the verification-command flow —
      it probes `/v1/health` and names the interpreter:
      `.venv/bin/python -m pip install -e ".[dev]" && .venv/bin/python -m pytest -q &&
      .venv/bin/python -c "… urlopen('http://127.0.0.1:8141/v1/health') …"`.

*Trace: US1.1, US8.1, US9.1.*

### Step 9 — Documentation and traceability

*(plan-profile step 6.)*

- [x] `README.md` and the manifest's dependency commentary are corrected in the same change that
      makes them true: the dependency list, the runtime package count, the authentication description
      and the new development tools (AC1.2.1, AC1.2.3, BR8.1).
- [x] The stale authentication comment in `app/main.py` is rewritten to match the sign-in flow that
      exists (AC1.2.3).
- [x] `source-manifest.json` lists every application-source path this unit creates, modifies or
      deletes — including `app/static/*` and `pyproject.toml` — as the engine's strict schema
      requires.
- [x] `traceability.json` maps every assigned AC and every referenced `NFRx.y` / `BRx.y` to an
      existing workspace-relative implementation or test file.

*Trace: US1.2, US9.1.*

### Step 10 — Findings from the architecture check

*(advisory findings raised in this stage attempt, folded in before the plan is re-confirmed.)*

- [x] `app/routes.py` / `app/session_auth.py`: `/v1/health` must carry `reason` only when the app is
      not connected. A resolvable live engine currently answers `connected: true` together with
      `reason: "Not connected to OpenRouter."`, which contradicts the contract's `Health.reason`
      (AC5.3.1). Pin the connected payload with its test.
- [x] `app/models.py`: `AnalyzeRequest` must reject unknown request-body fields — the contract sets
      `additionalProperties: false`, and `POST /v1/analyze {"text": "hi", "extra": 123}` currently
      returns `200` and silently ignores the extra field. Pin the refusal through the one envelope.
- [x] `app/models.py`: a migrated row whose `provider` is NULL must not render the literal `"None"`
      on `GET /v1/analyses`. Decide the wire representation (omitted, or JSON null) and pin it with a
      test against a migrated store.

*Trace: US5.3 (R-02), US2.1 (R-03), US7.1 (R-04).*

### Step 11 — Revision 1: findings from the architecture review

*(raised by the architecture review on this unit; the human asked for all four to be fixed before re-review.)*

- [x] R-01 (Major) — `app/db.py` `_migrate_analyses`: make the two migration strategies compose. A pre-v1 store that both lacks `provider` and carries `intensity NOT NULL` must migrate without `sqlite3.IntegrityError` — rebuild before adding columns, add a missing column with a usable default, or tolerate NULL during the copy — and add a `tests/test_db.py` case that sets both triggers at once.
- [x] R-02 (Major) — close the migrated-row `provider` deviation at the contract-owner level: either amend `contract-summary.md` / `entities.md` to admit an unknown provider (null or an explicit sentinel such as `"unknown"`) as the recorded wire shape, or emit a schema-conformant string for migrated rows. Record the decision where the contract lives, not only in the stage summary.
- [x] R-03 (Minor) — reconcile `functional-design/rules.md` BR4.3's wording (machine code, message and details) with the shipped two-field `{code, message}` envelope, or record the accepted deviation in the functional design.
- [x] R-04 (Minor) — `app/db.py`: restore the documented constraints after the `ADD COLUMN` step, or document the intentional divergence between the recorded schema version and the physical column constraints, and pin it in `tests/test_db.py`.

*Trace: US7.1 (R-01, R-02, R-04), US2.2/US8.1 (R-03).*

## Files expected to change

- **Application:** `app/config.py`, `app/sentiment.py`, `app/dummy_client.py`,
  `app/openrouter_client.py`, `app/db.py`, `app/models.py`, `app/repository.py`, `app/service.py`,
  `app/routes.py`, `app/main.py`, `app/session_auth.py`, `app/static/index.html`, `app/static/app.js`.
- **Tests:** `tests/test_config.py`, `tests/test_dummy_client.py`, `tests/test_db.py`,
  `tests/test_repository.py`, `tests/test_service.py`, `tests/test_routes.py`, `tests/test_page.py`,
  `tests/test_session_auth.py`, `tests/test_auth_routes.py`, `tests/conftest.py`, plus the new
  `tests/test_live_client.py`.
- **Manifest and docs:** `pyproject.toml`, `README.md`.

## Story traceability

| Story | Steps |
|---|---|
| US1.1 Install, run and test it locally, offline by default | 1, 2, 7, 8 |
| US1.2 Documentation, names and manifest tell the truth | 3, 9 |
| US2.1 Submit text and get a labelled result with its alternatives | 2, 6 |
| US2.2 Empty input is refused and nothing is stored | 2, 5, 6 |
| US3.1 The answer is read as typed data, never guessed from prose | 3 |
| US4.1 See previous analyses newest-first, with a defined limit | 2, 4 |
| US5.1 Choose the live model, with a stated credential precedence | 3, 5 |
| US5.2 A live attempt without a usable key fails with an instruction | 2, 5 |
| US5.3 The active engine and connection state are always visible | 2, 6 |
| US6.1 Connect from the page, keep the credential in memory, drop a rejected one | 3, 6 |
| US7.1 Stored results keep the v1 contract through an in-place migration | 4 |
| US8.1 The key never leaks and the app never leaves the machine | 2, 5, 6, 8 |
| US9.1 The live client is proven by tests and the coverage floor holds | 1, 3, 7, 9 |

## Definition of done

Every story in `unit-of-work-story-map.md` is implemented and covered by tests the installed tooling
can run; the record's verification command is green (it probes `/v1/health`); line coverage over the whole application,
including the live client exercised offline, is at least 80%; the pinned ruff rule set (with its
security rules) passes; and the page, the API and the health endpoint behave as `contract-summary.md`
states — including the `/v1` prefix and the corrected response shapes.

## Approval

This plan is the approval artifact: no implementation starts until you approve it. The approval binds
this plan, the Testing Contract below and `unit-test-instructions.md`.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "Acceptance/API tests come first — written against the requirement or acceptance criteria before the implementation — and lower-level unit tests come after the implementation.",
  "scope": "classic",
  "test_strategy": "standard",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Ordering**: Acceptance/API tests come first — written against the requirement or acceptance\n  criteria before the implementation — and lower-level unit tests come after the implementation.\n\n- **Framework and configuration** (observed): pytest only, configured in `[tool.pytest.ini_options]`\n  — `testpaths = [\"tests\"]`, `addopts = \"-q\"`, `filterwarnings = [\"error\"]`. The warnings filter is\n  the project's only mechanical gate today, and it doubles as its only upgrade canary: any\n  deprecation warning from FastAPI or pydantic on Python 3.14 becomes a failure. The suite was\n  measured green at this commit — **52 passed in 0.33 s** — so the gate is currently satisfied, not\n  aspirational. Note that `addopts = \"-q\"` suppresses per-test names, which a pipeline log parser\n  will care about.\n\n- **Test types present** (observed): 52 test functions in **9 `tests/test_*.py` modules** (auth_routes\n  12, session_auth 12, config 7, dummy_client 6, routes 6, service 3, db 2, repository 2, page 2),\n  plus the `tests/conftest.py` harness which contains no tests. The types are behavioural unit tests\n  per module, API-level tests driven through a hand-rolled in-process ASGI harness (`asgi_request()`\n  builds a raw scope, enters the lifespan and collects messages — no server starts, and `httpx` /\n  `TestClient` are absent by design), and page/markup contract tests pinning 9 `data-testid` hooks\n  plus `GET /static/app.js` being served as JavaScript. There are no tests against live external\n  services, no browser execution, no performance tests, and **no concurrency test at all** —\n  `grep` for thread/concurrency terms in `tests/` returns nothing. That last gap is material: it maps\n  onto R-01 (per-request `sqlite3.connect` on default thread affinity, `app/routes.py:70-76`,\n  `app/db.py:51-63`), the one defect this workspace has ever recorded and accepted.\n\n- **Test surface and doubles policy** (observed): assertions read values back out of real SQLite and\n  the real served markup, never out of mocks — there are **zero mock objects** in `tests/`, and\n  exactly two `monkeypatch` uses (`tests/test_auth_routes.py:205,223`). Doubles sit only at process\n  seams: an injected `exchanger` / `clock` in the authorization flow (`tests/test_session_auth.py:189`)\n  and an injectable `now` in the repository and service tests. A session-scoped autouse\n  `offline_guard` replaces `socket.socket.connect` with a raiser (`tests/conftest.py:129-146`), so an\n  accidental outbound call fails the run and an all-dummy run proves the suite never used the\n  network. `tmp_path`-based settings and DB paths mean no test reads `config.local.toml` or\n  `data/sentiment.db`, and `tests/test_config.py:126-143` shells out to `git check-ignore` as an\n  executable assertion that the key file cannot be committed.\n\n- **Boundary discipline** (observed): tests pin the observable contract, not implementation echoes —\n  422 for empty or whitespace-only text *with a row-count assertion of 0*, `limit` below 1 or\n  non-numeric → 422 naming `field == \"query.limit\"` and never a silent clamp, newest-first ordering,\n  `/health` reporting the resolved mode, and secret redaction asserted in reprs, in log records\n  (including `record.__dict__`) and in the `/`, `/health` and `/auth/status` bodies.\n\n- **Explicitly untested, by design** (observed): `app/openrouter_client.py` — the live engine, 149\n  executable lines — is never imported, constructed or called by the suite; the PKCE exchange\n  `exchange_code_at_openrouter()` is unexecuted and the flow is tested through `FakeExchanger`; the\n  browser script `app/static/app.js` is not executed. `README.md` records the substitute coverage as\n  code review plus a manual live smoke run. The suite cannot perform that smoke run, so who runs it\n  and when (pre-merge or pre-release) remains an open point for design and build.\n\n- **Coverage** — affirmed: **add a coverage tool, count the whole application, enforce an 80 % line\n  floor, and run the suite plus the floor in a CI job.** Measured today with a throwaway standard\n  library tracer: **556/792 lines = 70.2 % across all 12 application modules**, or **86.5 %** if the\n  never-imported live client is excluded (0/149). The floor therefore **fails today**, and covering\n  the live engine — at least its pure typed readers `_read_choice` / `_read_score` — is construction\n  work in this scope, not an optional extra. Two measurement facts to carry forward: the tracer must\n  be installed on new threads (`threading.settrace`), because FastAPI runs every endpoint here in an\n  anyio worker thread and a naive in-process measurement reads `app/routes.py` at 47 % instead of\n  91 %; and `pytest-cov` / `coverage` are not installed, so the pragmas the team already writes\n  (`app/repository.py:20`, `app/service.py:75`, `tests/test_config.py:128`) now need a policy for what\n  counts. The other half of this decision is open by construction: this scope skips the CI Pipeline\n  stage, so **where that CI job lives is an open point for design and build** — a local `addopts`\n  floor, a pre-push hook, or the pipeline itself once one exists.\n\n- **Dev-tool dependency cap** (observed, needs one confirmation): NFR3 in `pyproject.toml` caps\n  *runtime* dependencies at two (`fastapi` + `uvicorn`), with `pytest` as the only dev extra. A\n  coverage tool and a linter are development tools, so they do not change the runtime count — but the\n  NFR3 comment and the README's \"exactly three packages beyond the standard library\" line become\n  false the moment either is added, and must be updated in the same change.\n\n- **Verification command** (affirmed): **install** (`python -m pip install -e \".[dev]\"`), **run\n  `pytest`**, then **start the app locally and exercise the changed path**. This is the command later\n  stages use to prove a unit works end to end; `pytest` alone is not enough, because the suite never\n  starts a server and never resolves `uvicorn app:app`.\n\n- **Regression policy** (not yet affirmed): nothing runs the suite on a change, and no rule yet says\n  whether every defect must ship a reproducing test. The precedent to decide against is R-01: a\n  concurrency defect was recorded and accepted, and no test in the suite reproduces it."
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
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
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
      "Custom ordering - Acceptance/API tests come first — written against the requirement or acceptance criteria before the implementation — and lower-level unit tests come after the implementation.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:cbbeddf16ca99baf6e9a0b577960d9c822a35b896f0893990ae95d3babd5fb70",
  "contract_sha256": "sha256:d8c322c1bfcfec6cfae4e53346d2f9a85a44ec170084cf08ea993e67277df6d0"
}
```


