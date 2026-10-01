# Code Quality Assessment — `sentiment-opencode`

> Synthesized from the developer scan at HEAD
> `4eb9b74c4197114181dab641c177c569f2058c24`. Counts were re-verified against
> the tree (86 `def test_*` functions; 12 + 2 source files; 11 test files).

## Test Coverage

- **Test location**: `tests/` only (`testpaths = ["tests"]`).
- **Frameworks**: `pytest` + `pytest-cov`; `filterwarnings = ["error"]` turns any
  deprecation warning into a failure.
- **Coverage config**: present and enforced on every run —
  `addopts = "-q --cov=app --cov-report=term-missing --cov-fail-under=80"`,
  `[tool.coverage.run] source = ["app"]`, `[tool.coverage.report] fail_under = 80`.
  Asserted as configured input by `tests/test_config.py:141-160`.
- **Measured at scan time** (`.venv/bin/python -m pytest -q -p no:cacheprovider`,
  coverage data written to `/tmp/opencode`): **94 tests collected, 94 passed**
  (86 `def test_*` functions expanded by parametrization), **96.03% line coverage
  over `app/`** (605 statements, 24 missed).
- **Per-module weak spots**: `app/session_auth.py` 85% (the network exchange
  body, `84-120`); `app/openrouter_client.py` 92% (`urllib_transport`, `89-96`);
  `app/main.py` 98% (logging fallback, line ~49). All other modules 100%.
- **Test shape**: API-level via `tests/test_routes.py` (15 functions) and
  `tests/test_auth_routes.py` (12); behavioural units for db (6), repository (6),
  service (6), dummy_client (6), live_client (9), config (10), session_auth (12);
  markup contract `tests/test_page.py` (4).
- **Offline harness**: `tests/conftest.py` provides a hand-rolled in-process ASGI
  caller `asgi_request()` (no `httpx`/`TestClient`, deliberate under the
  dependency cap), a session-scoped autouse `offline_guard` that replaces
  `socket.socket.connect` with a raiser, and `tmp_settings` / `tmp_db_path`
  fixtures. Assertions read values back from real SQLite and served markup, not
  from mocks (zero mock objects; two `monkeypatch` uses).

## Test Gaps

- **`app/static/app.js` is not executed** by the suite; only served markup and
  route contracts are pinned (`README.md:69-71`).
- **The live engine's production transport (`urllib_transport`) never runs** in
  tests; the `offline_guard` makes that structural. The request builder and typed
  reader are covered through the injected transport.
- **No concurrency test exists** anywhere — `grep` for thread/concurrency terms
  in `tests/` returns nothing. This maps directly to the accepted R-01 risk.
- **No tests against live external services, no browser execution, no performance
  tests.**

## Linting & Formatting

- **Ruff**, configured in `pyproject.toml` (`[tool.ruff] line-length = 100`,
  `target-version = "py311"`; `[tool.ruff.lint] select =
  ["E","F","W","I","N","UP","S","B","C4","SIM"]` including the `S` security set;
  `extend-immutable-calls` for `fastapi.Depends`/`fastapi.Query`; per-file
  ignores for tests).
- At scan time `ruff check app tests` → **All checks passed**, and
  `ruff format --check app tests` → **23 files already formatted**.
- The org/team rule that a linter runs "in CI before merge" has no CI home here;
  `ruff` is a local/dev-extra gate only.

## CI/CD

**None.** No workflow YAML, no `Dockerfile`, no `Makefile`, no
`.pre-commit-config.yaml`. The only mechanical gates are run locally: pytest's
`filterwarnings = ["error"]`, the coverage floor in `addopts`, and `ruff`. There
is no dependency audit, no secret scanner and no lockfile.

## Documentation Quality

- **`README.md` (256 lines) is thorough**: setup, run, modes, full config
  resolution, storage/migration, a complete HTTP surface table, file layout,
  known limitations, and an end-to-end verify command.
- Every one of the 12 `app/*.py` modules opens with a docstring naming a single
  responsibility and usually citing prior-intent requirement ids. Two known
  exceptions: `app/__init__.py` has no "Single responsibility" line, and
  `app/session_auth.py` cites no requirement id. `app/main.py:33-34`'s comment
  that no authentication exists is stale.
- No `docs/` directory and no committed OpenAPI spec; FastAPI's runtime
  `/openapi.json` is not asserted anywhere.

## Technical Debt Signals

| ID | Signal | Evidence | Impact |
|---|---|---|---|
| TD-1 | **SQLite connection thread affinity (accepted, documented)** — one connection per request opened in a sync-generator dependency with default `check_same_thread=True` | `app/routes.py:79-85`, `app/db.py:130`, `README.md:237-243` | Overlapping requests can raise `sqlite3.ProgrammingError`; no concurrency test |
| TD-2 | **Record contract has four hand-written copies** — `RECORD_FIELDS`, `AnalysisRecord` fields, `to_dict()` literal, `ANALYSES_COLUMNS` + DDL — plus an independent test-local field set | `app/models.py:25-34,88-108`, `app/db.py:36-68`, `tests/test_routes.py:27-36` | Any new column must be threaded through all copies and exact-field-set assertions |
| TD-3 | **`schema_meta.version` is written but never compared**; migration driven by physical shape | `app/db.py:115-118,153,186-200` | The recorded version is not load-bearing |
| TD-4 | **Legacy `intensity` column retained** as nullable for pre-v1 rows; never surfaced | `app/db.py:43`, `app/models.py:12-14` | Dead-ish column kept for backward compatibility |
| TD-5 | **Browser script untested** | `app/static/app.js` (201 lines), `tests/test_page.py` | Regressions in page behaviour are invisible to the suite |
| TD-6 | **No secret scanner / dependency audit / lockfile**; fake key fixtures match OpenRouter's real shape | `tests/test_config.py:23`, `tests/test_live_client.py:27`, `tests/test_auth_routes.py:25-26`, `tests/test_session_auth.py:26` | A committed secret would not be detected; installs float |
| TD-7 | **`RECORD_FIELDS` is unreferenced** by any code or test | `app/models.py:25-34` | Dead constant that nonetheless must stay in sync |
| TD-8 | **`app/routes.py` is the widest fan-out** — page, API, auth and error mapping share one file | `app/routes.py` (282 lines) | Single point of combinatorial change |

**Suppressions, all deliberate and few**: 5 × `# noqa: S310` on hardcoded-https
stdlib URL calls (`app/openrouter_client.py:89,93`; `app/session_auth.py:88,96`),
2 × `# type: ignore[method-assign]` (`tests/conftest.py:141,145`), 4 ×
`# pragma: no cover` (`app/db.py:181`, `app/repository.py:20`,
`app/routes.py:248`, `tests/test_config.py:165`). **Zero TODO/FIXME/HACK/XXX**
anywhere in `app/` or `tests/` (grep clean).

## Strengths

- Small, coherent, fully-typed codebase with an acyclic one-way import graph and
  a single hexagonal seam that genuinely makes the engine swappable.
- High, honestly-measured line coverage (96%) with values asserted from real
  SQLite rather than mocks, plus a session-wide offline guard that makes
  "no network" a property, not an assumption.
- One error envelope for every application failure, with a documented boundary
  against framework routing errors.
- Key redaction is tested across repr, log records and response bodies.
- No dead TODOs, no bare `except`, parameterised SQL only.

## Intent-Relevant Quality Risks (CSV Import/Export)

1. **TD-2 is the largest construction hazard**: adding `import_id` to the
   persisted record touches models, DDL, the column tuple, insert SQL, migration
   copy SQL, `to_dict()`, `from_row()` and several exact-field-set assertions.
   Requirements/design must decide explicitly whether `import_id` is part of the
   **returned** record contract or storage-only.
2. **TD-1 (batch concurrency)**: a bulk import multiplies requests/rows; the
   existing single-writer SQLite path and thread-affinity caveat must be
   respected or deliberately addressed.
3. **Offline test constraint**: new import/export tests must drive
   `create_app(tmp_settings)` through `asgi_request` and read values back from
   real SQLite, matching the existing pattern; `httpx` and multipart cannot be
   introduced.
4. **Undefined batch-failure semantics**: `analyze_text` writes nothing and
   raises on the first bad row; there is no cross-row transaction boundary, so
   per-row skip-vs-abort and partial-`import_id` persistence must be decided.
