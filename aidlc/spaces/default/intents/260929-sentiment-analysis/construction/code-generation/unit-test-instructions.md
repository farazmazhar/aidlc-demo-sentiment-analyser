# Unit Test Instructions — very-cool-sentiment-analysis

- **Intent**: `260929-sentiment-analysis`
- **Stage**: code-generation (`3.5`)
- **Record**: `aidlc/spaces/default/intents/260929-sentiment-analysis/construction/code-generation/`
- **Scope**: `poc` — test strategy **Minimal** (depth Minimal), project type Greenfield
- **Companion plan**: `code-generation-plan.md` (this file is presented with it for Plan Approval)

## 1. Scope of "this work's tests"

This intent is a **zero-Unit** directive: there is no Unit DAG and no per-Unit record directory, so the unit-scoped test scope resolves at stage level. This work is the entire application, so its test scope is the whole `tests/` directory — seven test files plus the shared harness:

| File | Layer (per the Testing Contract) |
|---|---|
| `tests/conftest.py` | shared harness — no test functions |
| `tests/test_db.py` | Data model / database behavior |
| `tests/test_repository.py` | Repository / data access |
| `tests/test_config.py` | Business logic (configuration and mode resolution) |
| `tests/test_dummy_client.py` | Business logic (sentiment engine) |
| `tests/test_service.py` | Business logic (analysis orchestration) |
| `tests/test_routes.py` | API / endpoint |
| `tests/test_page.py` | Frontend behavior |

## 2. Test framework setup and configuration

- **Framework**: `pytest` — the only test dependency. No plugins, no `pytest-cov`, no `httpx`, no browser automation. Declared as the `dev` extra in `pyproject.toml`.
- **Configuration** (in `pyproject.toml`, so no separate config file exists):

  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  addopts = "-q"
  filterwarnings = ["error"]
  ```

  `testpaths` makes a bare `pytest` resolve to this work's suite and nothing else; `filterwarnings = ["error"]` turns warnings into failures so a deprecation cannot be introduced quietly.
- **Install**: `python -m pip install -e ".[dev]"` from the repo root. That installs exactly `fastapi`, `uvicorn` and `pytest` beyond the standard library (NFR3).
- **No `fastapi.testclient.TestClient`.** `TestClient` requires `httpx`, which the dependency cap forbids, so `tests/conftest.py` provides a small in-process ASGI harness instead (§5). Route and page tests use it.

## 3. Exact commands

**The recorded command for this work (stage-scoped):**

```
python -m pytest tests -q
```

Run it from the repo root. This is the command Build and Test executes for this work item: it is scoped to the exact `tests/` path rather than a bare project-wide `pytest`, and because this intent is zero-Unit it is the full extent of this work's suite.

**Narrow per-layer commands** (what each implement-then-test step in the plan runs):

| Layer | Command |
|---|---|
| Data model / database behavior | `python -m pytest tests/test_db.py -q` |
| Repository / data access | `python -m pytest tests/test_repository.py -q` |
| Business logic (config + engine + service) | `python -m pytest tests/test_config.py tests/test_dummy_client.py tests/test_service.py -q` |
| API / endpoint | `python -m pytest tests/test_routes.py -q` |
| Frontend behavior | `python -m pytest tests/test_page.py -q` |
| Runner readiness check (Step 2, before the first test exists) | `python -m pytest --version` |

Never run a bare `pytest` with no path as the recorded command, and never substitute `python -m unittest`; the single developer-facing test command from FR5.2 remains `pytest`, which resolves through `testpaths`.

## 4. Expected coverage targets

- **Strategy: Minimal** — one verifiable test per requirement at the narrowest effective level, plus at least one happy-path unit test per component. Coverage is assessed as *requirement coverage*, not as a line percentage.
- **Expected volume**: 27 test functions across the five testable layers, sized by requirement coverage rather than by component count. The plan's §6 table maps all 29 `FR` sub-IDs plus `NFR1`–`NFR6` and `A1`/`A2` — 37 IDs in total — to a named test or smoke step, so coverage is checkable by reading that table rather than by a number.
- **Why 27 and not fewer**: the Minimal obligation is one verifiable test per requirement at the narrowest effective level, and this requirement set carries 37 IDs, so requirement coverage sets the volume; grouping only merges IDs that describe a single observable behavior (for example the three dummy label outcomes and the invalid-input cases). This sits above the "approximately 5-15" size hint quoted for Minimal, and that is the intended trade-off: requirement coverage is the obligation, the size hint is guidance, and no test here is padding. `poc` adds no extra floor beyond this.

  | Test file | Planned functions |
  |---|---|
  | `tests/test_db.py` | 2 |
  | `tests/test_repository.py` | 2 |
  | `tests/test_config.py` | 6 |
  | `tests/test_dummy_client.py` | 6 |
  | `tests/test_service.py` | 3 |
  | `tests/test_routes.py` | 6 |
  | `tests/test_page.py` | 2 |
  | **Total** | **27** |
- **No line-coverage threshold applies.** `poc` adds no extra new-test floor, and no coverage percentage gate is configured for this work. No threshold exists to lower; if a step fails, fix the code, not the target.
- **Not covered by tests, by requirement**: FR2.3, FR2.4 and FR2.6 describe the live OpenRouter client, which FR5.5 forbids tests from exercising. They are recorded as `N/A` with that reason in `traceability.json` and are verified by a manual live smoke run outside the automated suite.
- **Suite must end green.** The scope floor is additive: the Minimal obligations above apply, and the existing suite (empty at greenfield start) must remain green throughout.

## 5. Mocking and stubbing guidance

- **The OpenRouter client is never exercised.** No test imports, constructs, or calls `OpenRouterClient`, and no test asserts on its URL, headers or payload. That client is verified by code review and by a manual live smoke run with a real key.
- **No network, ever.** `tests/conftest.py` installs an autouse session-wide guard that makes `socket.socket.connect` raise. Any accidental outbound connection fails the suite loudly instead of silently reaching OpenRouter. This is the enforcement mechanism behind FR5.3, FR5.5 and NFR1.
- **No key required.** Tests run with no `config.local.toml` present and no key in the environment. A test that needs a key is a design error.
- **Preferred double is a real in-process seam, not a mock.** Tests inject `Settings` into `create_app(...)` pointing `mode="dummy"` at a temporary database. Because the dummy client *is* the offline implementation, most tests need no double at all.
- **Exactly one hand-written stub is permitted**: a small local duck-typed class implementing `analyze(text) -> SentimentResult`, used solely by `test_client_is_substitutable_behind_the_interface` to prove the engine can be replaced without touching storage or the API (FR2.1, NFR5). It lives in the test file that uses it.
- **Never patch the code under test.** Do not monkeypatch internal functions, the repository, the service, or the routes to force a pass, and do not assert that a patched callable was called — that verifies wiring, not behavior. `monkeypatch` is used only for the environment-level concerns above (the socket guard, temporary config paths) and for injecting a fixed timestamp.
- **No assertion may be satisfied by the double echoing itself.** Assert on values that passed through real code — the row read back from SQLite, the JSON response parsed from the ASGI response, the served HTML — not on values the stub returned directly.

## 6. Test data management

- **Never touch the real database.** Every test that persists uses `tmp_path` and a fresh database file inside it. `data/sentiment.db` is a runtime artifact and is never created, read, or deleted by a test.
- **Never read the real config.** Every test constructs its own settings or writes a throwaway config file under `tmp_path`; the repo's `config.local.toml` is never a test input.
- **Isolation per test.** The app is built per test through `create_app(settings)` with a per-test database path, so no state leaks between tests and no shared mutable fixture exists.
- **Deterministic timestamps.** `insert_analysis()` and `analyze_text()` accept a `now` seam; tests inject a fixed `datetime` and assert on the exact stored ISO 8601 UTC string (for example `2026-09-29T12:00:00Z`) instead of matching a pattern.
- **Meaningful, minimal inputs.** Keyword samples are named for what they demonstrate (`text_with_positive_keyword`, `text_with_no_keywords`), and history-ordering tests insert three rows with distinct injected timestamps so newest-first is observable.
- **No committed fixtures or golden files.** All data is built inside the tests; there is no shared fixture directory to drift.
- **Cleanup is automatic.** `tmp_path` is removed by pytest; no test performs manual teardown.

## 7. Summary for Plan Approval

| Item | Value |
|---|---|
| Framework | `pytest` (only test dependency; no plugins) |
| Configuration | `[tool.pytest.ini_options]` in `pyproject.toml` — `testpaths = ["tests"]`, `addopts = "-q"`, `filterwarnings = ["error"]` |
| Scoped run command | `python -m pytest tests -q` (stage-level scope; zero-Unit intent) |
| Per-layer commands | one exact `tests/test_<layer>.py` path per layer (§3) |
| Expected tests | 27 test functions across the five testable layers, covering every requirement ID in the plan's §6 traceability table |
| Coverage target | requirement-driven per the Minimal strategy; **no** line-coverage gate for `poc` |
| Network / key | never — session-wide `socket.connect` guard; the OpenRouter client is never exercised |
| Test data | per-test `tmp_path` SQLite files and settings; no real config, no real database, no committed fixtures |
| Known verification limit | browser-side execution of `app.js` is not tested (no browser-automation dependency is permitted); the page is verified at the served-markup contract level |
