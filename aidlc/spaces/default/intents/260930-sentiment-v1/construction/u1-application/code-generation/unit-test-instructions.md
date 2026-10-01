# Unit Test Instructions — `u1-application`

## Posture

The team's affirmed cadence applies: acceptance/API tests are written before the implementation they
cover, and lower-level unit tests follow each layer's implementation. A change is complete only when
the suite is green, the lint rules pass, and line coverage over the whole application meets the
eighty-percent floor.

## Running this unit's tests

This unit is the whole application, so its test tree is `tests/`. Every command runs from the
repository root, offline, with no key and no `config.local.toml` present.

| What | Exact command |
|---|---|
| Install (development) | `python -m pip install -e ".[dev]"` |
| This unit's suite | `python -m pytest -q tests/test_config.py tests/test_dummy_client.py tests/test_live_client.py tests/test_db.py tests/test_repository.py tests/test_service.py tests/test_routes.py tests/test_page.py tests/test_session_auth.py tests/test_auth_routes.py` |
| Coverage, with the floor applied | `python -m pytest -q tests/test_config.py tests/test_dummy_client.py tests/test_live_client.py tests/test_db.py tests/test_repository.py tests/test_service.py tests/test_routes.py tests/test_page.py tests/test_session_auth.py tests/test_auth_routes.py --cov=app --cov-report=term-missing --cov-fail-under=80` |
| Lint | `python -m ruff check app tests` |
| Format check | `python -m ruff format --check app tests` |
| End-to-end check | the record's verification command: `.venv/bin/python -m pip install -e ".[dev]" && .venv/bin/python -m pytest -q && .venv/bin/python -c "import threading,time,urllib.request,uvicorn; from app.main import app as a; threading.Thread(target=uvicorn.run, args=(a,), kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'}, daemon=True).start(); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"` |

The file list names every test module of this unit explicitly, so no other unit's tests are re-run and
no bare project-wide command is used. `tests/test_live_client.py` is created by Step 3 of the plan;
until it exists, every command above applies with that path omitted.

## Test framework setup and configuration

- The runner is pytest, configured in `[tool.pytest.ini_options]`: `testpaths = ["tests"]`,
  `addopts = "-q"` and `filterwarnings = ["error"]`. Keep the warnings gate: a FastAPI or pydantic
  deprecation warning is a test failure, and it is the project's only upgrade canary.
- Coverage is a plugin of the same runner, added to the `dev` extra in Step 1 and configured on the
  coverage command above (`--cov=app`, `--cov-report=term-missing`, `--cov-fail-under=80`).
- Lint and format are `ruff`, with the explicit rule set pinned in `[tool.ruff]` (including the `S`
  security rules) rather than left to a tool default.
- The outbound-network block in `tests/conftest.py` stays in place; any test that reaches the network
  still fails the run.

## Expected coverage

Line coverage is measured over `app/` — the whole application, live client included — and must be at
least 80%; the run fails below it. Coverage of the test tree itself is not the metric.

## Mocking and stubbing

- The live client's transport is injected: tests pass a stub returning a recorded answer, so request
  construction, typed-answer reading and the unreadable-answer failure are asserted with no network
  call (BR7.2).
- Use the seams the code already exposes — the injected `now` timestamp, the database path, the config
  path and the injected transport — instead of patching module internals.
- Do not stub the store: persistence behaviour is asserted against a real SQLite file in a temporary
  directory, including a file created with the pre-v1 shape.

## Test data management

- A migrated store is built as a real SQLite file with the older shape, in a temporary path, and the
  test asserts that its rows survive the startup migration and that a newly written row leaves the
  retired attribute unset.
- No test reads or writes `data/sentiment.db`, and no test needs a key or a config file.
- Tests stay deterministic: no wall-clock dependence, no reliance on ordering beyond newest-first.
