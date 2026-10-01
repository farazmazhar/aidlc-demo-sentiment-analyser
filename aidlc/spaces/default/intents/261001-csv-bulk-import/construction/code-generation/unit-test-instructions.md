# Unit Test Instructions — CSV Bulk Import / Export (stage-level)

> Target: **stage-level** zero-Unit Code Generation. Scope: `express`, test strategy
> **Minimal**, brownfield. Methodology **custom**: acceptance/API tests first, then
> implementation, then lower-level unit tests.

## Framework and Configuration

- **Framework:** `pytest` (already installed; no new dependency).
- **Configuration:** `[tool.pytest.ini_options]` in `pyproject.toml` is used unchanged —
  `testpaths = ["tests"]`, `addopts = "-q"`, `filterwarnings = ["error"]`.
  The warnings filter is the mechanical gate: any deprecation warning is a failure.
- **No new test dependency** (`httpx`/`TestClient` stay absent by design), no new config file,
  no new dev extra.

## Exact command to run this stage's tests

```bash
python -m pytest tests/test_bulk_import.py tests/test_db.py tests/test_repository.py tests/test_service.py tests/test_routes.py -q
```

This is scoped to the new module and the modules the change touches. The full suite
(`python -m pytest`) is run in Step 8 of the plan and again by Build and Test; this scoped
command is the inner loop and must be runnable before the first acceptance/API test is written.

## Bash command is the runner; no server is started

Tests drive the app in process through the existing `tests/conftest.py` harness
(`create_app(tmp_settings)` + `asgi_request(...)`), which enters the lifespan and collects
messages directly. `uvicorn app:app` is never resolved by the suite; the end-to-end live
exercise belongs to the team's recorded verification command, not here.

## Scope and volume (Minimal strategy)

- One verifiable test per requirement (FR1, FR2, FR3, FR4) at the narrowest effective level.
- At least one happy-path unit test per changed component (models, db, repository, service, routes).
- Acceptance/API tests come **first** (Step 2 of the plan), written against the FR acceptance
  criteria in `requirements.md` before the implementation; lower-level unit tests come **after**
  the implementation (Step 7).
- Express adds no extra new-test floor; the existing suite must remain green.

## Expected coverage targets

Minimal strategy: requirement-driven coverage — every functional requirement and every new
error branch has a test, and every changed component has a happy path. There is no numeric
coverage floor in this scope (the 80% floor belongs to `classic`-family scopes and is not part
of `express`).

## Mocking / stubbing guidance

- **No mock objects.** Assertions read values back out of real SQLite and real responses,
  matching the existing suite.
- Doubles only at process seams already provided: the injected `now` on
  `analyze_text` / `insert_analysis` if a deterministic timestamp is needed, and the engine
  seam (`SentimentClient`) for an engine-failure row. Prefer a tiny in-test `SentimentClient`
  stub over a mock library so the failure path is exercised without touching the network.
- The session autouse `offline_guard` (`tests/conftest.py`) makes any socket connect fail,
  so an accidental outbound call fails the run.

## Test data management

- Use `tmp_path`-based settings and DB paths; never read `config.local.toml`, `data/sentiment.db`,
  or the network.
- Build CSV request bodies as `bytes` in-test and pass them to `asgi_request` with a
  `text/csv` content type (and one case each for an unsupported content type and an
  unparseable body).
- Read persisted rows back out of the real SQLite file to assert the breakdown and the
  `import_id` grouping; assert the export body is the exact expected CSV.
