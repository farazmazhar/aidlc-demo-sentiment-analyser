# Integration Test Instructions — `u1-application`

Standard test strategy: unit tests are covered per-unit by Code Generation; this file covers the key
boundary and cross-component interactions for the single unit.

## Scope

Boundaries exercised end to end through the real components (no mocks of the store, no network):

1. **HTTP boundary → request validation**: `POST /v1/analyze` rejects empty/whitespace text (`422
   INVALID_TEXT`) and unknown body fields (`422 VALIDATION_FAILED`) before any store work.
2. **HTTP boundary → service → engine → repository → store**: a valid submission is scored by the
   offline engine, persisted, and returned with the stored record's exact v1 field set.
3. **HTTP boundary → repository → store**: `GET /v1/analyses` returns newest-first with a
   caller-supplied limit, rejecting a limit below 1 or non-numeric.
4. **HTTP boundary → configuration/health**: `GET /v1/health` reports the active mode and connection
   state, and carries `reason` only when not connected.
5. **Live-attempt boundary**: a submission while live was requested with no usable key is `503
   LIVE_KEY_MISSING`, names the config file, and stores nothing.
6. **Store boundary across a schema change**: startup migration against a real pre-v1 SQLite file
   preserves rows and leaves the retired attribute unset on new rows.

## Setup

- Runner: `pytest`, configured in `[tool.pytest.ini_options]` (`testpaths=["tests"]`,
  `addopts="-q"`, `filterwarnings=["error"]`).
- API-level tests drive a hand-rolled in-process ASGI harness (`asgi_request()` in
  `tests/conftest.py`); no server is started and `httpx`/`TestClient` are intentionally absent.
- The session-scoped autouse `offline_guard` replaces `socket.socket.connect` with a raiser, so an
  accidental outbound call fails the run (NFR1.2).
- Database and config paths are `tmp_path`-based; no test reads `data/sentiment.db` or
  `config.local.toml`.

## How to run

```bash
.venv/bin/python -m pytest -q tests/test_routes.py tests/test_service.py tests/test_repository.py \
  tests/test_db.py tests/test_page.py tests/test_session_auth.py tests/test_auth_routes.py
```

## Expected outcomes

- Every listed boundary test passes; refusal paths assert a row-count of 0.
- No outbound network use occurs (the guard would raise).
- The migration test leaves the pre-existing rows readable and writes no invented `provider` for a
  migrated row.

## Test data management

- A migrated store is built as a real SQLite file with the older shape in a temporary path; the test
  asserts rows survive the startup migration.
- Tests are deterministic and order-independent (newest-first ordering is the only ordering
  assumption).
