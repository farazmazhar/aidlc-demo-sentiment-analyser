## Developer Code Scan Results

### Scan Coverage

**Snapshot binding**
- Pre-scan `source_fingerprint` (as supplied by the conductor): `git:35fb8af515dd89605a695e792f0a934f7cd460f8`
- Pre-scan `store_generation`: `sha256:17b87212bab44711b368b21c93dade0b7cb93010edaa37a3dd64ecc174540379`
- Pre-scan `paths`: `["app","tests","pyproject.toml","config.example.toml","README.md"]`
- Observed `HEAD` at scan time: `4b67c0355912546cb35e6eefd58067fd47e991b5` (`main`, clean working tree for every focused path — `git status --short app tests pyproject.toml README.md config.example.toml` is empty).
- Every deeply analyzed path below is inside the focused set. No deep path was taken outside it.

- **Analyzed deeply** (repo-relative; read in full by this run unless marked):
  - `app/routes.py` (502 lines) — the entire HTTP surface: page, `/v1` router, `/v2` analytics router, `/auth/*`, error-envelope handlers.
  - `app/analytics.py` (374) — the read module: `resolve_range`, `read_summary`, `read_terms`, series/rounding/ranking helpers.
  - `app/terms.py` (201) — `tokenize` + `significant_terms`, the promoted tokeniser and `STOPWORDS`.
  - `app/main.py` (163) — `create_app`, lifespan, loopback enforcement, router/static/exception wiring.
  - `app/models.py` (246) — wire + storage dataclasses and the four computed analytics shapes.
  - `app/db.py` (339) — schema v4 DDL, in-place migration, index creation, `connect`.
  - `app/config.py` (151) — `Settings`, `load_settings`, mode resolution, redaction.
  - `app/service.py` (214) — `analyze_text`, `import_texts`, `get_client`, `effective_connection`.
  - `app/static/index.html` (351) — the single page: header/nav, analyse, summary, terms placeholder, history, styles.
  - `app/static/app.js` (322) — all fetch call sites, summary rendering, connection indicator.
  - `tests/conftest.py` (315) — the ASGI harness, `concurrent_requests`, `application_started`, `offline_guard`, tmp fixtures.
  - `tests/test_analytics_routes.py` (804) — full read; the `/v2` acceptance tests, R-01 concurrency tests, envelope codes.
  - `tests/test_page.py` (171) — full read; the served-markup/asset contract and `REQUIRED_TEST_IDS`.
  - `tests/test_config.py` (180) — full read; mode resolution, redaction, dependency-cap assertion, gitignore assertion.
  - `tests/test_terms.py` (212) — full read; tokeniser parity and engine-scoring parity.
  - `tests/test_migration_indexes.py` (542) — header + DDL fixtures + purpose read (v3→v4 migration, index survival, read-only proof).
  - `tests/test_analytics_read.py` (561) — header + purpose read (read module against real SQLite).
  - `pyproject.toml` — build, dependencies, pytest/coverage/ruff config.
  - `config.example.toml` — committed config template.
  - `README.md` — HTTP-surface tables, storage/migration contract, file layout, limitations, verify-it-end-to-end.
- **Re-verified by targeted grep against the prior intent's full scan** (unchanged engine/leaf modules outside the intent's change area, not re-read line by line this run):
  - `app/dummy_client.py` (103), `app/repository.py` (102), `app/sentiment.py` (84), `app/openrouter_client.py` (232), `app/session_auth.py` (259), `app/__init__.py` (10).
- **Skimmed only**:
  - `aidlc/spaces/default/intents/261001-analytics-layer/` — read `inception/reverse-engineering/developer-scan.md` and searched audit/reviews for `FR7.3`, `G9/G10`, secret-scanner and packaging context; not re-derived.
  - `aidlc/spaces/default/memory/{org,team,project}.md`, `phases/inception.md` — read for active-space rules (Testing Posture, Code Style, Forbidden/Mandated/Corrections).
  - `.aidlc/knowledge/aidlc-shared/*`, `.aidlc/knowledge/aidlc-developer-agent/*` — mandated knowledge preflight + artifact template.
  - `ENGINE-DEFECT-REPORT.md` — read for why this is a fresh intent (u3/u4 unreachable in the prior intent).
  - `docs/OUTCOMES.md`, `docs/SCOPES.md` — listed only.
  - `data/sentiment.db` — probed live with `sqlite3` (schema/version/indexes/row count); not read as text.
  - `.venv/` — `importlib.metadata` version probe only; `site-packages` not read.
  - `.aidlc/`, `.opencode/`, `AGENTS.md`, `opencode.json`, `.gitignore`, `very_cool_sentiment_analysis.egg-info/`, `.coverage`, caches — harness/build artefacts, not application code.

### Packages Found

- `very-cool-sentiment-analysis` — application distribution (declared in `pyproject.toml`, `packages = ["app"]`) — Python 3.11+ — localhost-only sentiment-analysis web app: typed classification, local SQLite history, one page, a `/v1` JSON API, a `/v2` analytics API, and an opt-in live client.
- `app` — the single importable package — Python — 14 modules plus `app/static/{index.html,app.js}` (`package-data = static/*`). New since the prior scan: `app/analytics.py` and `app/terms.py`.
- `tests` — the single test package — Python — in-process ASGI suite, now 15 `test_*.py` modules plus `conftest.py`.
- No `scripts/`, no `Makefile`, no packaging/lockfile artefact, no `LICENSE`, no `src/` layout, no sub-packages.

### Build System

- **Type**: PEP 517 / setuptools via `pyproject.toml`; no Makefile, tox, nox, Dockerfile, pre-commit config, or CI workflow.
- **Config Files**: `pyproject.toml` (only manifest), `config.example.toml` (template; `config.local.toml` is gitignored at `.gitignore:90`).
- **Build/runtime commands**: `python -m pytest -q`, `python -m ruff check app tests`, `python -m ruff format --check app tests`, `uvicorn app:app --reload`.
- **Executable verification command** (`README.md:348-352`): install `.[dev]` → `python -m pytest -q` → boot uvicorn on `127.0.0.1:8141` → read `/v1/health`. It runs install + pytest + a health probe but **no lint step, no secret scan and no dependency audit**.
- **Internal import graph** (one direction per layer; no cycles found): leaves `config`, `models`, `sentiment`, `terms` → `repository`, `db`, `dummy_client`, `openrouter_client` → `service` → `routes` → `main` → `__init__`. `app/analytics` sits beside `repository` as a read module and is imported by `routes`; it imports `models`, `sentiment`, `terms`. `app/terms` is a leaf importing nothing from `app`. `app/service` still imports `app.openrouter_client` function-locally (`app/service.py:103`).

### APIs Discovered

- **`/v1` JSON API (frozen, `BR4.2`)** — `app/routes.py`, `v1_router` (`app/routes.py:171`), `V1_PREFIX = "/v1"` (`:59`) — 6 endpoints: `POST /v1/analyze`, `GET /v1/analyses`, `POST /v1/analyses/import`, `GET /v1/analyses/export`, `GET /v1/health`.
- **`/v2` analytics API (read-only, additive, `BR4.7`)** — `app/routes.py`, `v2_router` (`:174`), `V2_PREFIX = "/v2"` (`:65`) — 2 endpoints:
  - `GET /v2/analytics/summary` (`:339`) — query `from`, `to`, `import_id`; returns the six-field summary; `422 VALIDATION_FAILED` on bad/inverted bounds; `500 STORAGE_FAILURE` on a store read error.
  - `GET /v2/analytics/terms` (`:372`) — query `from`, `to`, `import_id`, `limit` (`Query(DEFAULT_TERM_LIMIT, ge=1)`); returns `{positive, negative}`; same failure surface.
- **Unversioned page/support surface** — `router` (`:168`) — `GET /`, `GET /static/*`, `GET /auth/status`, `GET /auth/openrouter/start`, `GET /auth/callback`, `POST /auth/disconnect`.
- **Error envelope** — `error_response` (`app/routes.py:91`), exactly `{code, message}`. Codes: `VALIDATION_FAILED`, `INVALID_TEXT`, `LIVE_KEY_MISSING`, `SENTIMENT_ENGINE_ERROR`, `AUTH_EXPIRED`, `IMPORT_NOT_FOUND`, and the one addition `STORAGE_FAILURE` (`:79`). Framework 404/405 keep FastAPI's `{"detail": …}`.
- **Internal read seam** — `app.analytics.read_summary` / `read_terms` take the request's `sqlite3.Connection`; `resolve_range` is shared by both endpoints so their populations match (`BR1.5`). No service call in the read path (project rule Q9 honoured).
- **Outbound (live only, never in tests)**: `POST https://openrouter.ai/api/alpha/decisions` (`app/openrouter_client.py`), PKCE exchange `POST https://openrouter.ai/api/v1/auth/keys` (`app/session_auth.py`).

### Frameworks & Libraries

Re-measured this run via `importlib.metadata` (`.venv`, CPython **3.14.7**):

| Package | Declared floor | Installed |
|---|---|---|
| fastapi | `>=0.110` | **0.142.2** |
| uvicorn | `>=0.27` | **0.54.0** |
| starlette | (transitive) | **1.7.0** |
| pydantic | (transitive) | **2.13.5** |
| anyio | (transitive) | **4.15.1** |
| opentelemetry-api | (transitive, via fastapi) | **1.45.0** |
| pytest | `>=8` (dev) | **9.1.1** |
| pytest-cov | `>=5` (dev) | **7.1.0** |
| coverage | (dev, via pytest-cov) | **7.16.2** |
| ruff | `>=0.6` (dev) | **0.16.9** |

- Runtime declaration is **exactly two** (`fastapi`, `uvicorn`) — asserted by `tests/test_config.py:141-160`.
- Deliberately absent: `httpx` (so `fastapi.testclient` is unusable) and any browser-automation package. No frontend framework or bundler; the UI is one hand-written HTML file plus one vanilla script.
- SQLite: bundled `sqlite3`, library 3.53.4 with `strftime` and JSON functions available.

### Test Coverage

- **Test Directories**: `tests/` (single directory, no sub-folders). 15 `test_*.py` modules plus `conftest.py` (5,259 lines total).
- **Test Frameworks**: `pytest` only. No `unittest`, no `hypothesis`, no `mock`. Doubles are hand-written classes; substitution is `monkeypatch.setattr` at the consumer import name; `asgi_request` uses `asyncio.run` per call. `concurrent_requests` + `application_started` add genuine multi-thread overlap.
- **Coverage Config**: enforced twice — `addopts` (`--cov=app --cov-report=term-missing --cov-fail-under=80`) and `[tool.coverage.report] fail_under = 80`; `source = ["app"]`; `filterwarnings = ["error"]`; `testpaths = ["tests"]`.
- **Re-measured this run**: `python -m pytest -q` → **192 passed, 0 failed, 0 skipped**; line coverage **97.06%** (884 statements, 26 missed) against the 80% floor. Module misses: `app/session_auth.py` 85% (84-120), `app/openrouter_client.py` 92% (89-96), `app/main.py` 98% (103), `app/routes.py` 99% (257-258, the `csv.Error` branch). All other modules 100%. This corroborates the project description's "192 tests at 97.06% coverage" exactly.
- **Test functions per module** (175 `def test_` in source, expanded by 6 parametrize sites to 192 collected): `test_analytics_routes` 25, `test_routes` 17, `test_bulk_import` 16, `test_analytics_read` 15, `test_auth_routes` 12, `test_session_auth` 12, `test_config` 10, `test_terms` 10, `test_live_client` 9, `test_migration_indexes` 9, `test_page` 9, `test_service` 9, `test_db` 8, `test_repository` 8, `test_dummy_client` 6.
- **Offline enforcement**: session-scoped autouse `offline_guard` (`tests/conftest.py:278-295`) monkeypatches `socket.socket.connect` to raise; `tests/test_analytics_routes.py:778-804` proves it armed.
- **Isolation**: `tmp_settings` / `tmp_db_path` point every test at `tmp_path`; no test touches `config.local.toml` or `data/sentiment.db`.
- **Frontend limit, stated in the suite**: `tests/test_page.py` asserts served **markup** and served **asset** properties only. Nothing executes `app.js`. This is the instrument gap that blocks NFR4.6 and NFR4.7 today.

### Code Quality Indicators

- **Linting**: `ruff` configured entirely in `pyproject.toml`; re-measured this run: `ruff check app tests` → **All checks passed!**; `ruff format --check app tests` → **30 files already formatted** (ruff 0.16.9). `line-length = 100`, `target-version = "py311"` (matches `requires-python = ">=3.11"`), `select = ["E","F","W","I","N","UP","S","B","C4","SIM"]`, B008 silenced by config for `fastapi.Depends`/`fastapi.Query`, `per-file-ignores` for `tests/*`.
- **Type checking**: absent (no mypy/pyright/py.typed).
- **CI/CD**: **none** — no `.github/`, no workflow file, no pre-commit config, no Docker. The gates run only when a developer runs them.
- **Documentation**: README is maintained and current: it carries the `/v1` table (19 rows), a new `/v2` analytics table, the storage/migration contract, the file layout (now listing `analytics.py`, `terms.py`, and the four analytics test modules), the known-limitations section, and the verify-it-end-to-end block. Every `app/` module still opens with a "Single responsibility:" docstring, including the two new ones.
- **File sizes**: largest are `app/routes.py` (502) and `tests/test_analytics_routes.py` (804). No `app/` file exceeds 502 lines.
- **Error handling**: specific exception types only; one deliberate `except BaseException` rollback-and-re-raise in `app/db.py:241`; analytics routes add a narrow `except sqlite3.Error` returning `500 STORAGE_FAILURE` and logging through the module logger. No bare `except:`.
- **Structural conventions held**: `from __future__ import annotations` in 13 of 14 `app/` modules (exception: the 10-line `app/__init__.py`); `#:` prose constants; no `pydantic` in `app/`; parameter-bound SQL only; no junk-drawer module.

### Technical Debt Signals

- **The analytics view is only half-built — this is the intent's core gap.** The nav (`nav-summary`, `nav-terms`) and the summary region already exist (`app/static/index.html:185-195`, `:269-313`), but:
  - the **terms section is a static placeholder** — `<section id="terms-section">` with a `<p>` and no term-list containers (`app/static/index.html:326-331`);
  - there is **no date-range control anywhere** (no date inputs; grep of both static files finds none);
  - `app.js` has **no terms fetch** and **no range parameters** — `refreshSummary` calls `${API_V2}/analytics/summary` with no query string (`app/static/app.js:238-255`), and only `refreshHistory()` + `refreshSummary()` run at load (`:313-314`);
  - there is **no partial-failure marker** (NFR4.6): `resetAnalyticsRegions`/`renderSummary` manage only the summary's own three regions (`:163-169`, `:221-235`); there is no second error region and no logic that renders one section succeeding while another fails;
  - there is **no superseded-response guard** (NFR4.7): no `AbortController`, no request sequence counter, no "discard a stale response" path exists in `app.js`.
- **NFR4.6 and NFR4.7 have no test instrument under the current dependency cap.** `tests/test_page.py` can only assert static markup/asset properties (its module docstring states browser execution is excluded). A future failing-terms/succeeding-summary state or an out-of-order response cannot be decided by any permitted test today; the criteria must be restated as static asset assertions plus the manual end-to-end line (the prior user-stories review reached the same conclusion — see `261001-analytics-layer` reviews R-10).
- **Packaging instruments named by this intent do not exist yet.** No verification script, no secret scanner, no dependency audit, and no secret-scan allowlist exist anywhere in the tree (grep for `pip-audit`/`bandit`/`detect-secrets`/`gitleaks`/`verification script` across `app/`, `tests/`, `pyproject.toml`, `README.md`, `config.example.toml`, `docs/` returns nothing). The only automated "tripwire" is `tests/test_config.py:141`, which asserts the ruff `S` set is selected and `fail_under == 80` — a config assertion, not a scan.
- **Secret-scanner allowlist targets (measured)**: 7 test files carry `sk-or-v1-*` fake-key literals — `tests/test_auth_routes.py:25-26`, `tests/test_config.py:23`, `tests/test_live_client.py:27`, `tests/test_routes.py:268`, `tests/test_service.py:95,181`, plus the negative assertion at `tests/test_analytics_routes.py:559`. These must be allowlisted so the first run produces signal.
- **Platform obligations from the prior intent remain open** (`u4-platform-packaging` was never reached): no lockfile with hashes, no `LICENSE`, and no ruff `TID251` `banned-api` entries (`pyproject.toml` selects `E,F,W,I,N,UP,S,B,C4,SIM` but **not** `TID`). The team rules and `project.md ## Mandated` require all three; this intent only explicitly re-scopes the verification script, secret scanner and dependency audit.
- **README doc drift**: `README.md:287` describes `app/analytics.py` as "`AnalyticsRead`: range resolution, aggregates, series, ranking", but no `AnalyticsRead` symbol exists in `app/analytics.py` (the surface is `ResolvedRange`, `resolve_range`, `read_summary`, `read_terms`). Minor, but the README is the "contract of record".
- **No response models / OpenAPI enforcement**: handlers return bare `JSONResponse`/`list[dict]`, so `/openapi.json` cannot describe the real shapes; contracts are pinned by hand-written test constants (`SUMMARY_FIELDS`, `TERMS_FIELDS` in `tests/test_analytics_routes.py`).
- **`/v1/analyses/export` duplicates the record shape positionally** (`app/routes.py:290-309` unpacking fields by hand) — a shape change is a two-place edit.
- **Coverage gaps are the production HTTP transports** (`app/openrouter_client.py:89-96`, `app/session_auth.py:84-120`) plus one `csv.Error` branch (`app/routes.py:257-258`) — all deliberately bypassed by injected seams.
- **Working tree carries build artefacts** (`.coverage`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`) — all gitignored, harmless.
- **`data/sentiment.db` local artefact** is now at `schema_meta.version = 4` with the three named indexes present and 7 rows; `/data/` is gitignored.
- **Zero `TODO`/`FIXME`/`HACK`/`XXX`** markers in `app/` or `tests/`.

## Handoff Summary

- **Intent-relevant finding**: the server half of the analytics feature is complete and heavily tested; the **view half is a scaffold**, and that is precisely the seam this intent must fill.
  1. **The terms section is a placeholder and the range control is absent.** `app/static/index.html:326-331` holds an empty `<section id="terms-section">` with a prose `<p>`; both static files contain no date input. The summary region (`:269-313`) and the nav links (`nav-summary`, `nav-terms` at `:192-193`) already exist. `tests/test_page.py:19-49` already pins `nav-summary`, `nav-terms`, `analytics-summary`, `analytics-empty`, `analytics-error` and the summary hooks, but pins **no terms hook names** — the new markup must extend `REQUIRED_TEST_IDS`.
  2. **`app.js` needs a terms fetch, range parameters, a partial-failure marker and a superseded-response guard.** Today `refreshSummary` fetches `${API_V2}/analytics/summary` with no query string (`:242`), and no request-sequencing or two-section error state exists. The two `/v2` handlers already accept `from`/`to`/`import_id` and are fully exercised (`app/routes.py:339-403`; `tests/test_analytics_routes.py`). The shared `resolve_range` guarantees both endpoints describe one population (`app/analytics.py:125-138`), so a single range control can drive both fetches.
  3. **NFR4.6/NFR4.7 have no decidable instrument under the dependency cap.** The suite deliberately never executes `app.js` (`tests/test_page.py:1-7`). Closing these NFRs means restating them as static served-asset assertions (e.g. the script carries a sequence guard; each section's render site references only its own endpoint's fields) and moving the observable runtime behaviour to the single manual end-to-end line.
  4. **The packaging deliverables are greenfield files.** No verification script, secret scanner, dependency audit or allowlist exists. The natural insertion points are the repo root (a script the README can call) and `pyproject.toml` (a new `dev` extra for the scanner/audit tool, keeping the runtime list at two). The scanner's first-run allowlist must cover the 7 fake-key fixture files listed above.
  5. **The existing gates are the baseline to preserve.** Before changes: 192 passed / 97.06% / `ruff check` clean / `ruff format --check` clean / offline guard armed. `filterwarnings = ["error"]` means any new deprecation from a scanner/audit tool is a hard suite failure only if it runs inside pytest.
- **Risks / follow-up**:
  - **`/v1` and the frozen envelope must not move.** The only shape freedom is the `/v2` body and the single `STORAGE_FAILURE` code already added; `tests/test_analytics_routes.py:563-568` asserts `/v1` is untouched.
  - **Runtime dependency cap.** Any secret scanner / dependency-audit tool must live in the `dev` extra, never the runtime list; `tests/test_config.py:148-151` asserts the list is exactly `["fastapi","uvicorn"]` and will fail otherwise. A `TID251`/lockfile obligation is also outstanding and may belong in the same packaging change.
  - **The `filterwarnings = ["error"]` gate makes suite pass/fail a function of the resolved toolchain**, and there is no lockfile; a newly added dev tool can shift resolved transitive versions. The scanner/audit runner should be a separate script invocation, not an in-suite fixture, to avoid coupling the suite to tool deprecations.
  - **Browser behaviour is untestable here.** Do not plan NFR4.6/NFR4.7 close-out on a browser-driving test; the cap forbids the dependency. Their verifiable half is static asset structure + the manual line.
  - **Prior-intent context is authoritative and consistent with the code** (`FR7.3` secret scanner owned by `u4-platform-packaging`; `G9/G10` named absent in the prior CI config; `FR7.2` the verification script). This scan's measurements match the project description's "192 tests at 97.06%".
  - **Two stale CodeKB rows from the prior intent** are recorded in `team.md` and must not be relayed as authority: `architecture.md:502` names a non-existent `ensure_page_state` (the real connection owner is `get_connection`, `app/routes.py:114`), and `code-structure.md:208` says `from __future__ import annotations` applies to "All 12 modules" (it applies to 13 of the current 14, all but `app/__init__.py`).
  - **Scope honesty**: I did not analyse the `.aidlc/` engine, the `.opencode/` adapter, `.venv/` contents, the `aidlc/` workflow record prose, or the existing `codekb/` store's prose; `data/sentiment.db` was probed, not read as text. The active-space practice rules were read for exactly the topics the brief named (Testing Posture, Code Style, Forbidden/Mandated/Corrections).
