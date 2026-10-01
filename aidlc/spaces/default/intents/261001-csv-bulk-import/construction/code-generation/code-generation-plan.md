# Code Generation Plan — CSV Bulk Import / Export

> Target: **stage-level** (zero-Unit directive; `express` scope skips Units Generation, so this is one implementation iteration under `<record>/construction/code-generation/`).
> Source of truth: `aidlc/spaces/default/intents/261001-csv-bulk-import/inception/requirements-analysis/requirements.md` and the `sentiment-opencode` code knowledge base at HEAD `4eb9b74`.
> Methodology: **custom** — acceptance/API tests first, then implementation, then lower-level unit tests.

## Scope Snapshot

The change adds a bulk CSV import/export surface to the existing localhost-only
sentiment app without touching the single-analysis behaviour or adding a runtime
dependency:

- `POST /v1/analyses/import` — parse a `text/csv` body (one text per row; an exact `text` first row is a header), analyze each row through the existing `SentimentClient` seam, skip unanalyzable rows, persist successes under one server-generated `import_id`, and return `import_id` + imported/skipped counts + per-label counts + mean confidence (FR1).
- `GET /v1/analyses/export?import_id=...` — return the rows for that `import_id` as CSV, newest first, `text/csv` + attachment disposition; unknown id is a `404` envelope (FR2).
- Add a nullable `import_id` to the persisted record and to every copy of the record contract, and return it (null for single analyses) from the existing endpoints (FR3).
- Offline requirement-driven tests; existing suite stays green (FR4).

## Implementation Steps

- [x] **Step 1 — Confirm the test runner and record the exact scoped command.**
  Brownfield: verify the existing pytest configuration in `pyproject.toml` (`testpaths = ["tests"]`, `addopts = "-q"`, `filterwarnings = ["error"]`) and record the exact command that runs this change's tests:
  `python -m pytest tests/test_bulk_import.py tests/test_db.py tests/test_repository.py tests/test_service.py tests/test_routes.py -q`
  No new runner or test dependency is added. *(FR4)*

- [x] **Step 2 — Acceptance/API tests first (custom ordering).**
  Create `tests/test_bulk_import.py` with API-level tests written against the FR1/FR2/FR3 acceptance criteria **before** the implementation, driven through the existing in-process ASGI harness (`create_app` + `asgi_request`) and reading values back from real SQLite (no network, no `httpx`). Cover: happy-path import and export; the exact-`text` header row; blank/engine-failure rows skipped with counts; `422` on an unparseable body and an unsupported content type; `404` envelope on an unknown `import_id`; `422` on a missing `import_id`. *(FR1, FR2, FR1.7)*

- [x] **Step 3 — Record contract and schema: add `import_id`.**
  Add a nullable `import_id` in all four hand-written copies of the contract — `RECORD_FIELDS` and the `AnalysisRecord` fields plus `to_dict()`/`from_row()` in `app/models.py`, and `ANALYSES_COLUMNS` + the `CREATE TABLE`/insert DDL in `app/db.py` — bump `SCHEMA_VERSION`, add the column to `_ADD_COLUMN_SQL` and to the explicit `_COPY_ROWS_INTO_V1_TABLE` rebuild list so existing rows survive with `NULL`. *(FR3.1, FR3.2, FR3.3, FR3.4)*

- [x] **Step 4 — Persistence: insert with `import_id` and query by it.**
  Extend `app/repository.py` so `insert_analysis` can store an `import_id`, and add a `list_analyses_by_import_id(connection, import_id)` that returns matching rows newest first (descending `id`). *(FR1.3, FR2.2, FR2.6)*

- [x] **Step 5 — Business logic: bulk orchestration and aggregation.**
  Add a `service` function that iterates the parsed rows in order, calls the existing per-text seam (`analyze_text`) for each, treats blank/whitespace text as skippable, catches an engine failure for a row and skips it without aborting, persists each success under one `import_id`, and returns the aggregate counts plus the mean confidence (null when nothing was imported). No engine-resolution change. *(FR1.3, FR1.4, FR1.5)*

- [x] **Step 6 — Edge layer: endpoints and error envelope.**
  Add `POST /v1/analyses/import` and `GET /v1/analyses/export` to `v1_router` in `app/routes.py`. Parse the CSV with the standard-library `csv` module; treat an exact `text` first row as a header; build the CSV export with `text/csv` and `Content-Disposition: attachment; filename="analyses-<import_id>.csv"`; add the `IMPORT_NOT_FOUND` code and return `404` through the existing `{code, message}` envelope for an unknown `import_id`, and `422` `VALIDATION_FAILED` for a bad body/content type or a missing `import_id`. *(FR1.1, FR1.6, FR1.7, FR2.1–FR2.5)*

- [x] **Step 7 — Lower-level unit tests after implementation (custom ordering).**
  Add unit tests for the new persistence and aggregation behaviour alongside the existing module tests (`tests/test_db.py`, `tests/test_repository.py`, `tests/test_service.py`), and update the exact-field-set assertions that the additive `import_id` field changes. *(FR4.1)*

- [x] **Step 8 — Run the scoped command and the full suite.**
  Run the Step 1 command, then the full `python -m pytest` suite; both must be green (`filterwarnings = ["error"]` treats any deprecation warning as a failure). Fix regressions rather than weakening a check. *(FR4.1, NFR5)*

- [x] **Step 9 — Documentation and traceability.**
  Update module docstrings for the changed modules and the README's HTTP-surface section; produce `code-summary.md`, `source-manifest.json` (every created/modified application path), and `traceability.json` (FR/NFR → implementation/test file), and record any deviation from this plan. *(FR3, NFR5)*

## Traceability (requirement → plan step)

| Requirement | Plan step(s) |
|---|---|
| FR1.1 import endpoint | Step 6 |
| FR1.2 CSV shape / header | Step 2, Step 6 |
| FR1.3 analyze via existing seam, one `import_id` | Step 3, Step 4, Step 5 |
| FR1.4 skip unanalyzable rows | Step 2, Step 5 |
| FR1.5 import response breakdown | Step 5, Step 6 |
| FR1.6 `200` including skips / zero rows | Step 2, Step 6 |
| FR1.7 `422` invalid input | Step 2, Step 6 |
| FR2.1 export endpoint | Step 6 |
| FR2.2 export columns + newest-first | Step 4, Step 6 |
| FR2.3 export headers | Step 6 |
| FR2.4 `404` unknown id | Step 2, Step 6 |
| FR2.5 `422` missing id | Step 2, Step 6 |
| FR2.6 export scoped to `import_id` | Step 4, Step 6 |
| FR3.1 nullable column | Step 3 |
| FR3.2 record contract (all copies) | Step 3 |
| FR3.3 migration + version bump | Step 3 |
| FR3.4 recovery unchanged | Step 3 |
| FR4.1 offline requirement-driven tests | Step 2, Step 7, Step 8 |
| FR4.2 offline harness, no new test dep | Step 1, Step 2, Step 7 |
| NFR1 dependency cap | Step 1, Step 6 |
| NFR3 error envelope | Step 6 |
| NFR5 backward compatibility | Step 3, Step 7, Step 8 |
| NFR6 testability | Step 1, Step 2, Step 8 |

## Test Files

- `tests/test_bulk_import.py` — new; API-level acceptance tests for import/export (Step 2) and, where cheaper at the API level, the requirement-driven coverage.
- `tests/test_db.py`, `tests/test_repository.py`, `tests/test_service.py` — extended unit tests (Step 7).
- `tests/test_routes.py` — updated exact-field-set assertions for the additive `import_id` field (Step 7).

## Test Configuration

No new test configuration or dependency. The existing pytest configuration in `pyproject.toml` is used unchanged; `filterwarnings = ["error"]` remains the mechanical gate.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "Acceptance/API tests come first — written against the requirement or acceptance criteria before the implementation — and lower-level unit tests come after the implementation.",
  "scope": "express",
  "test_strategy": "minimal",
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
    "strategy": "minimal",
    "strategy_volume": [
      "One verifiable test per requirement at the narrowest effective level.",
      "At least one happy-path unit test per component.",
      "Unit tests are the default; a bugfix/security scope floor may require an integration or E2E regression when that is the narrowest level that reproduces the defect."
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
  "input_sha256": "sha256:949fcde740a70cf86676af308ab5715ad9c64fafdc64ad34f3aa4d69e0bfdc24",
  "contract_sha256": "sha256:90d67be610688942f0a22a56218142a24e8b33b08ee1afb10fca070ce56fce02"
}
```
