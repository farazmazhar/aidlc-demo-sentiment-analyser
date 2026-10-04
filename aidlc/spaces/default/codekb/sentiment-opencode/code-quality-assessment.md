# Code Quality Assessment — `very-cool-sentiment-analysis` (repo `sentiment-opencode`)

All numbers in this artifact were **re-measured by the focused scan** at commit
`4b67c03`; the prior full-rescan numbers (at `beeb587`) are superseded and were
not carried forward. Commands and results are reproduced so they can be re-run.

## Headline

| Signal | State | Assessment |
|---|---|---|
| Tests | **192 passed**, 0 failed, 0 skipped | Green |
| Line coverage | **97.06%** (884 statements, 26 missed) against an **80%** floor | Far above the floor |
| Lint | `ruff check app tests` → *All checks passed!* | Clean |
| Format | `ruff format --check app tests` → *30 files already formatted* | Clean |
| CI/CD | **None** | The largest process-level gap; the active intent adds a verification script, not CI |
| Type checking | **None** | Annotations are 100% applied and entirely unenforced |
| Test doubles | **Zero mock objects** | Every double is a hand-written class at a real seam |
| Documentation | Strong and unusually traceable | The README *is* the contract of record, though it now carries minor drift (TD-14) |
| Analytics view | **Half-built** | The server half is complete and tested; the page half is a scaffold (TD-12) |
| Packaging instruments | **Absent** | No verification script, secret scanner, dependency audit or allowlist (TD-13) |

The short version: this is a small, disciplined codebase with an unusually
honest documentation practice. Its weaknesses are concentrated in **four
places** — the remaining database-migration hazard (a five-place column edit),
the absence of any automated gate or scan, the analytics **view** having no
execution coverage, and the packaging instruments not existing yet.

---

## Test Coverage

### Test surface

| | |
|---|---|
| Directory | `tests/` — one directory, no sub-directories, no fixtures directory |
| Harness | `tests/conftest.py` (315 lines) — `asgi_request`, `application_started`, `concurrent_requests`, `offline_guard`, `tmp_settings`, `tmp_db_path` |
| Framework | `pytest` **only**. No `unittest`, no `hypothesis`, no `asyncio` marker |
| Mocking library | **none** — not even `unittest.mock` |
| Parametrization | 6 sites, expanding 175 test functions to 192 collected tests |
| Total | 5 259 lines across 15 test modules plus `conftest.py` |

| Module | Functions | Lines | What it pins |
|---|---|---|---|
| `tests/test_analytics_routes.py` | 25 | 804 | the `/v2` contract, the range parameters, the envelope codes, the R-01 concurrency reproduction |
| `tests/test_routes.py` | 17 | 416 | the full `/v1` contract, the envelope, the record field set, `limit` handling |
| `tests/test_bulk_import.py` | 16 | 315 | CSV parsing, header skip, per-row skipping, `import_id` grouping, export round trip |
| `tests/test_analytics_read.py` | 15 | 561 | the read module against real SQLite: range resolution, series, ranking, shares |
| `tests/test_auth_routes.py` | 12 | 259 | the `/auth/*` routes and their redirect behaviour |
| `tests/test_session_auth.py` | 12 | 196 | PKCE verifier/challenge, expiry, credential redaction, injected exchanger |
| `tests/test_config.py` | 10 | 180 | the six resolution outcomes, redaction, `git check-ignore`, the dependency-cap assertion |
| `tests/test_terms.py` | 10 | 212 | tokeniser parity and engine-scoring parity against the promoted tokeniser |
| `tests/test_live_client.py` | 9 | 220 | typed answer reading, error mapping, transport injection |
| `tests/test_migration_indexes.py` | 9 | 542 | the v3→v4 migration, index survival, the read-only proof |
| `tests/test_page.py` | 9 | 171 | served markup, the required test ids, `role`/`aria-live`, asset content type, absence of `intensity` |
| `tests/test_service.py` | 9 | 304 | orchestration order W1, engine resolution precedence, `ImportSummary` aggregation |
| `tests/test_db.py` | 8 | 443 | schema creation, migration from pre-v1, column order, NOT NULL flags, label CHECK, `intensity` absence |
| `tests/test_repository.py` | 8 | 237 | row DML, `format_timestamp`, `import_id` scoping, `intensity` never read |
| `tests/test_dummy_client.py` | 6 | 84 | keyword classification, and that the offline guard is actually armed |

The largest test modules cover the **analytics read path** —
`test_analytics_routes.py` (804) and `test_analytics_read.py` (561) against 374
lines of `app/analytics.py` — plus `test_migration_indexes.py` (542) against 339
lines of `app/db.py`. That ratio is the clearest signal of where this project's
risk actually lives.

### Measured coverage

Command: `python -m pytest -q` → **192 passed**, line coverage **97.06%**
(884 statements, 26 missed) against the 80% floor.

Per-module misses (every other module is at 100%):

| Module | Cover | Missing |
|---|---|---|
| `app/session_auth.py` | 85% | 84-120 |
| `app/openrouter_client.py` | 92% | 89-96 |
| `app/main.py` | 98% | 103 |
| `app/routes.py` | 99% | 257-258 |

Ten of fourteen modules are at **100%**. The 26 missed statements are:

| Uncovered block | Lines | Why |
|---|---|---|
| `exchange_code_at_openrouter` body | `app/session_auth.py:84-120` | Every test injects a double, so the real `urllib` request is never built |
| `urllib_transport` body | `app/openrouter_client.py:89-96` | Same reason — the transport is always injected |
| logging-handler guard | `app/main.py:103` | Environment-dependent |
| `csv.Error` branch | `app/routes.py:257-258` | Hard to provoke; Python's `csv` reader is permissive |

The first two are **by design** — the dependency cap forbids an HTTP client
library, so the transport is the injection point. The cost is that the two places
that build and parse real HTTP are unexercised (TD-9).

### Coverage configuration — enforced twice over

| Setting | Value | Effect |
|---|---|---|
| `pyproject.toml` `addopts` | `--cov=app --cov-report=term-missing --cov-fail-under=80` | **Applied to every run**, not only to a run that remembers to ask for it |
| `[tool.coverage.run] source` | `["app"]` | Measures the **whole application**, including the never-imported live client |
| `[tool.coverage.report] fail_under` | `80` | The floor is an input, never lowered to make a step pass |
| `[tool.coverage.report] show_missing` | `true` | Uncovered lines visible — this is how the two transport gaps were located |
| `filterwarnings` | `["error"]` | A FastAPI or pydantic deprecation is a **hard suite failure** |

Placing the floor in `addopts` *and* under `[tool.coverage]` is deliberate belt
and braces: forgetting to pass `--cov` cannot silently skip the gate.

### Test quality — what the suite does well

- **Real assertions, not mock echoes.** Values are read back out of **real
  SQLite and real served markup**. Doubles sit only at process seams.
- **The offline guard is itself tested.** `tests/test_dummy_client.py:70-84`
  actively proves the socket blocker is armed, so a silently-broken guard cannot
  make the suite pass while it reaches the network.
- **Complete isolation.** `tmp_settings` and `tmp_db_path` point every test at
  `tmp_path`. No test reads `config.local.toml` or `data/sentiment.db`.
- **An executable security assertion.** `tests/test_config.py` shells out to
  `git check-ignore` to prove the key file cannot be committed.
- **Row-count assertions accompany status-code assertions.** A `422` test also
  asserts nothing was written — so a refusal that half-succeeded would fail.
- **Contract constants live in the tests.** `tests/test_routes.py:28-41` and
  `tests/test_bulk_import.py:27-33` declare their own record and summary field
  sets, which is what substitutes for response models (see TD-8).
- **Boundary discipline.** `limit` below 1 or non-numeric → `422` naming
  `field == "query.limit"` and never a silent clamp; newest-first ordering;
  `/health` reporting the resolved mode; secret redaction asserted in reprs, in
  log records **including `record.__dict__`**, and in the `/`, `/health` and
  `/auth/status` bodies.

### Test quality — what the suite does not cover

| Gap | Why | Consequence |
|---|---|---|
| Browser-side execution of `app.js` | No browser-automation dependency is permitted under the cap; `tests/test_page.py` states this explicitly | The page's behaviour is unverified. The markup and the asset are pinned; **nothing that runs is**. This is now the blocker for NFR4.6/NFR4.7 (TD-12) |
| The two production HTTP transports | Injected doubles by design | TD-9 |
| Real PostgreSQL/SQLite-server behaviour | N/A — the store is a local file | — |
| Performance / load | None, and none needed at local scale | — |

The redaction property "never in a response body" holds **by construction** for
the routes with no test — because no key field reaches a record — not by an
endpoint sweep. Worth knowing which kind of guarantee you are relying on.

---

## Linting

`ruff`, configured entirely in `pyproject.toml`. Both checks are green at this
commit.

```console
$ python -m ruff check app tests
All checks passed!
$ python -m ruff format --check app tests
30 files already formatted
```

| Setting | Value | Note |
|---|---|---|
| `line-length` | `100` | |
| `target-version` | `"py311"` | Matches `requires-python` |
| `lint.select` | `["E","F","W","I","N","UP","S","B","C4","SIM"]` | An **explicit, reviewed selection**, not a drifting default. `S` is the security set |
| `extend-immutable-calls` | `["fastapi.Depends","fastapi.Query"]` | B008 silenced by configuration, not by a `# noqa` |
| `per-file-ignores` for `tests/*` | `["S101","S105","S106","S603","S607"]` | Tests assert by construction, hold obviously-fake fixture credentials, and shell out to `git`. **`app/` is held to the security rules in full** |
| `format.quote-style` / `line-ending` | `"double"` / `"lf"` | |

The `ruff` adoption is recorded in team memory as the settled answer to a
measured baseline of 16 findings — so the "clean" result above is the outcome of
a deliberate configuration decision, not of not running the tool.

### Type checking

**Absent.** No `mypy`, no `pyright`, no `py.typed` marker.

This matters more than usual here, because the codebase already holds to the
convention a checker would enforce: `from __future__ import annotations` in 13 of
14 modules and full annotations on **every** public function, with only two
`# type: ignore[method-assign]` suppressions in the entire tree (both in the
offline guard, `tests/conftest.py:152,156`). The two `# type: ignore` comments
already anticipate a checker. Adding one would be close to free — the convention
is already 100% applied.

---

## CI/CD

**None.** No `.github/`, no `.gitlab-ci.yml`, no Jenkinsfile, no pre-commit
config, no GitHub Actions, no Docker.

Verification is a documented manual sequence:

```console
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check app tests
python -m ruff format --check app tests
```

plus an end-to-end command that boots the app on `127.0.0.1:8141` and reads
`/v1/health`. The affirmed team posture is exactly this — install, run the
suite, then start the app and exercise the changed path — because `pytest` alone
never starts a server and never resolves `uvicorn app:app`.

The coverage floor, the ruff rule set and the 192 green tests are therefore the
**only** safety net, and they run only when whoever is working remembers to run
them. That is TD-10.

---

## Documentation Quality

**Strong, and unusually traceable for a project of this size.**

| Artifact | State |
|---|---|
| `README.md` (365 lines) | Genuinely maintained: setup, run, test/lint commands, the in-app connection flow, the two modes, configuration, the storage/migration contract, the **HTTP surface table** (now including the `/v2` analytics rows), the file-layout tree (now listing `analytics.py`, `terms.py` and the four analytics test modules), known limitations, and an end-to-end verification command. It now carries one minor drift (TD-14). |
| Module docstrings | All 14 modules, each carrying an explicit `Single responsibility:` line naming what the module does **not** contain (the two new modules included) |
| Function docstrings | Present throughout, frequently citing the rule the function enforces |
| Embedded traceability | `FR4.1`, `NFR3.1`, `BR4.3`, `AC7.1.2`, `R-01`, `R-04`, `D1`–`D4`, `W1` appear in docstrings and comments throughout `app/` and `tests/`, and the same IDs are used in the README |
| Constants | Semantic constants carry `#:` prose stating why |
| **Absent** | No `docs/` directory, no ADRs, no OpenAPI spec file, no changelog |

The traceability density is a genuine strength — the code is self-describing
against its own requirement set. It is also a readability cost for anyone
without those upstream artifacts, and the IDs are not mechanically generated, so
they can drift from the requirements they cite. Treat them as a human-maintained
cross-reference, not a verified link.

**Structural metrics.** The largest module is `app/routes.py` at 502 lines; the
largest test module is `tests/test_analytics_routes.py` at 804. Longest functions
are `import_texts` (41) and `SessionAuth.complete` (41), both linear loops. No
class exceeds 100 lines. No SQL in `routes.py`, no sentiment logic there, no HTTP
in `service.py`; the analytics read module imports nothing from `fastapi` and
opens no socket. No circular imports. Zero `TODO`/`FIXME`/`HACK`/`XXX`.

**Suppressions: narrow and justified.**

| Count | Suppression | Justification |
|---|---|---|
| 4 | `# pragma: no cover` | Branches unreachable by construction: `app/db.py`, `app/repository.py`, `app/routes.py`, `tests/test_config.py` |
| 4 | `# noqa: S310` on `urllib` calls | The endpoint is a hardcoded `https` constant, commented as such: `app/openrouter_client.py`; `app/session_auth.py` |
| 1 | `# noqa: S105` on the token pattern | `TOKEN_PATTERN` is a word regex, not a credential: `app/terms.py:27` |
| 2 | `# type: ignore[method-assign]` | Replacing `socket.socket.connect` in the offline guard: `tests/conftest.py` |

No blanket suppressions, no file-level `# ruff: noqa`.

---

## Technical Debt Register

Severity is about **cost to the next change**, not about correctness today.

### TD-1 — The migration dropped every index on `analyses` · **CLOSED**

`_rebuild_analyses` renames the table to `analyses_pre_v1`, creates a fresh
`analyses` from `CREATE_ANALYSES_TABLE`, copies rows, and drops the old table.
Because that DDL declared no indexes, an index on `analyses` was silently lost on
any migrating store — verified empirically at `beeb587`.

**Closed in `261001-analytics-layer`.** `init_db` now creates the three named
analytics indexes idempotently **after** the migrate-or-create branch
(`CREATE INDEX IF NOT EXISTS`), and `_rebuild_analyses` re-creates all three by
name as steps after the copy. `tests/test_migration_indexes.py` (9 functions,
542 lines) asserts that the indexes survive a v3 → v4 migration. The lesson
survives as a pattern: an index on a rebuilt table must be created outside the
table's own DDL.

### TD-2 — Adding a column to `analyses` is a five-place edit · **Medium**

A new column must be added in all of:

| # | Location | What breaks if missed |
|---|---|---|
| 1 | `ANALYSES_COLUMNS` (`app/db.py:63-74`) | `_is_v1_shape` compares `tuple(info) != ANALYSES_COLUMNS` — the store reports the wrong shape and is rebuilt on every startup |
| 2 | `CREATE_ANALYSES_TABLE` (`app/db.py:40-53`) | the rebuilt table has no such column; the copy then aborts |
| 3 | `_ADD_COLUMN_SQL` (`app/db.py:94-105`) | a pre-existing store cannot gain the column; `_migrate_analyses` skips it |
| 4 | `_V1_NOT_NULL_COLUMNS` (`app/db.py:79-81`) | `_is_v1_shape` compares the NOT NULL flag per column |
| 5 | the explicit column list in `_COPY_ROWS_INTO_V1_TABLE` (`app/db.py:114-120`) | the row copy selects a column that does not exist |

Any one missed produces either a false v1 shape or an aborted copy. **A separate
table, or an index created idempotently in `init_db`, is far cheaper** — and a
separate table was verified to survive both migration paths.

### TD-3 — The local dev database has migrated forward in place · **CLOSED (observed)**

`data/sentiment.db` now reports `schema_meta.version = 4` with the three named
indexes present and 7 rows, so the store has migrated v2 → v3 → v4 in place
without loss. `/data/` is gitignored, so this is local machine state only. The
observation is kept because it is the one live migration the project can point
to; the v2 → v3 → v4 path has now actually run against that file.

### TD-4 — The retired `intensity` attribute still makes a "mean intensity" metric impossible · **CLOSED (contract)**

`intensity` is a **retired** column, and its retirement is deliberate and
asserted in three test files:

- the column is nullable and **never written by new rows** (`app/db.py:47`)
- it is **absent from `RECORD_FIELDS`** (`app/models.py:25-35`)
- it is **never read** by `AnalysisRecord.from_row` (`app/models.py:117-144`)
- `tests/test_page.py:64-68` asserts the string `intensity` is **absent from the
  served page markup**; `tests/test_db.py` and `tests/test_repository.py` pin its
  absence from the contract
- it exists only on pre-v1 rows, whose values are preserved untouched and never
  back-filled (BR3.4)

**Consequence.** `AVG(intensity)` over the current `analyses` table returns
`NULL` for every row written since v1. **Resolved:** the prior intent
(`261001-analytics-layer`) dropped `mean intensity` from the summary requirement
rather than reporting a null or synthesising a proxy, so no live requirement asks
for it. The column stays retired; a future request for a mean intensity is still
asking for a value this system does not produce.

### TD-5 — Cross-thread SQLite connection affinity (R-01) · **CLOSED**

A per-request `sqlite3.Connection` created in one anyio worker thread
(`get_connection`, `app/routes.py:114`) and used from another raised
`sqlite3.ProgrammingError` when requests overlapped; sequential use was
unaffected. The team rule that every defect ships a reproducing test closed
R-01's exemption, and the old ASGI harness could not host such a test.

**Closed in `261001-analytics-layer`.** `app/db.py` now decides thread affinity
explicitly: `connect` opens with `check_same_thread=False`, safe only under the
documented request-scoped invariant — one connection per request, closed in that
request's own `finally`, never pooled, cached, stored on a module global or
shared between concurrent requests. The harness grew `concurrent_requests` +
`application_started`, and `tests/test_analytics_routes.py` carries the
reproduction. The flag is **not** a licence to share a connection across threads:
re-enable the guard or make any pooling thread-safe before introducing it.

### TD-6 — The tokeniser lived in the wrong module · **CLOSED**

`_WORD = re.compile(r"[a-z']+")` was underscore-private inside
`app/dummy_client.py` and was the **only** tokeniser in the codebase, so a second
consumer either reached into an unrelated module's private name or duplicated the
regex.

**Closed in `261001-analytics-layer`.** The pattern is promoted to the leaf
`app/terms.py`, exposed through `tokenize()` (no filters, so the engine's scoring
is byte-for-byte unchanged) and `significant_terms()` (the length + stopword
filter). Both `app.dummy_client` and `app.analytics` consume it, and
`tests/test_terms.py` pins tokeniser and engine-scoring parity (A4).

### TD-7 — No pagination beyond a bare `LIMIT` · **Medium**

`list_analyses` (`app/repository.py:80-87`) is `ORDER BY id DESC LIMIT ?` with no
offset, no cursor and no total count. The API surface carries **no pagination
metadata at all**.

**Consequence.** A growing history cannot be walked — only the newest `limit`
rows are reachable — and a client cannot know how much more there is.

### TD-8 — The record contract has four hand-maintained copies and no response model · **Medium**

The nine-field contract exists in four places, kept in sync by tests rather than
mechanically:

| Copy | Location |
|---|---|
| `RECORD_FIELDS` | `app/models.py:25-35` — and **nothing in the code reads it** |
| the `AnalysisRecord` field declarations | `app/models.py` |
| the literal in `to_dict()` | `app/models.py` |
| `ANALYSES_COLUMNS` + the `CREATE TABLE` text | `app/db.py:40-74` |

A **fifth** copy exists positionally in the export route, which writes seven
columns by unpacking each `AnalysisRecord` field **by hand**
(`app/routes.py:253-264`) rather than from `to_dict()` or `dataclasses.fields`. A
change to the record shape, or a new export column, must be edited in two places
— and those two can silently drift, with no test comparing them.

Compounding it: because no handler declares a response model, FastAPI's generated
`/openapi.json` **cannot describe the real shapes**. Contracts are pinned only by
hand-written constants in two test modules.

### TD-9 — Coverage gaps concentrated in the two production HTTP transports · **Low (by design)**

`app/openrouter_client.py:89-96` and `app/session_auth.py:84-120` are uncovered
because every test injects a transport or an exchanger. Acceptable under the
dependency cap, but it means the two places that build and parse real HTTP are
unexercised. The two modules duplicate their `urllib` request construction rather
than sharing a helper (a cohesion-over-DRY choice — see **dependencies.md**), which
is why there are two uncovered bodies rather than one.

### TD-10 — No CI, so every quality gate is opt-in · **High (process)**

There is no CI, no pre-commit hook, and no other automated trigger. The 80%
coverage floor, the pinned ruff rule set and the 118 green tests are enforced
only by whoever remembers to run them locally. This is the single largest
process-level debt signal, and it is the one most easily fixed by the next scope
that includes a pipeline.

### TD-11 — Zero browser-side execution coverage · **Medium**

`app.js` is served and its markup contract is pinned, but **nothing in the suite
executes it**. No browser-automation dependency is permitted under the
two-package cap, and `tests/test_page.py` says so plainly. The practical
consequence: a behavioural regression in the page — a wrong fetch URL, a broken
`textContent` write, a date-filter handler that never fires — would pass the whole
suite. This is now the specific blocker for NFR4.6 and NFR4.7 (see TD-12).

### TD-12 — The analytics view is a scaffold, and it is this intent's gap · **High (intent-relevant)**

The server half of analytics is complete and heavily tested; the page half is not.

- The nav (`nav-summary`, `nav-terms`) and the summary region already exist
  (`app/static/index.html:192-193`, `:270`), but the terms section (`:328`) is a
  **static placeholder** with no term-list containers.
- There is **no date-range control** anywhere, and `refreshSummary` fetches
  `${API_V2}/analytics/summary` with **no query string** (`app/static/app.js:242`);
  there is no terms fetch.
- There is **no partial-failure marker** (NFR4.6): only the summary's own regions
  are managed, so one section cannot visibly succeed while another fails.
- There is **no superseded-response guard** (NFR4.7): no `AbortController` and no
  request-sequence counter exists.

**Why it is decidable but not testable today.** `tests/test_page.py` deliberately
never executes `app.js` (TD-11), and the cap forbids browser automation, so
NFR4.6/NFR4.7 must be restated as static served-asset assertions (the script
carries a sequence guard; each section's render site references only its own
endpoint's fields) plus the single manual end-to-end line. The active intent
`261004-analytics-view-packaging` fills this.

### TD-13 — No packaging instruments exist · **Medium (intent-relevant)**

No verification script, secret scanner, dependency audit or allowlist exists
anywhere in the tree. The only automated "tripwire" is `tests/test_config.py`,
which asserts the ruff `S` set is selected and `fail_under == 80` — a config
assertion, not a scan.

- The `dev` extra is the correct home for the scanner/audit tool, so the runtime
  list stays exactly `["fastapi", "uvicorn"]` (`tests/test_config.py:141-160`).
- The scanner's first-run allowlist must cover the fake-key fixtures — the
  `sk-or-v1-*` literals in the test files (`tests/test_auth_routes.py`,
  `tests/test_config.py`, `tests/test_live_client.py`, `tests/test_routes.py`,
  `tests/test_service.py`, and the negative assertion in
  `tests/test_analytics_routes.py`).
- `filterwarnings = ["error"]` makes suite pass/fail a function of the resolved
  toolchain, so the scanner/audit runner should be a **separate script
  invocation**, not an in-suite fixture.

The active intent is the change that adds these.

### TD-14 — README drift: a named symbol that does not exist · **Low**

`README.md:287` describes `app/analytics.py` as "`AnalyticsRead`: range
resolution, aggregates, series, ranking", but **no `AnalyticsRead` symbol exists**
in `app/analytics.py` (the surface is `ResolvedRange`, `resolve_range`,
`read_summary`, `read_terms`). Minor, but the README is the "contract of record".

### TD-15 — Three platform obligations from the prior intent are still open · **Medium**

`261001-analytics-layer`'s platform work (`u4-platform-packaging`) was never
reached, so three repository-level obligations remain: no lockfile with hashes,
no `LICENSE`, and no `ruff` `TID251` `banned-api` entries (`pyproject.toml`
selects `E,F,W,I,N,UP,S,B,C4,SIM` but **not** `TID`). The team/project rules
(`## Mandated`) require all three. This intent explicitly re-scopes the
verification script, secret scanner and dependency audit; the other three remain
outstanding.

### Observed, not debt

- **Untracked local artefacts.** `.coverage`, `.pytest_cache/`, `.ruff_cache/`,
  `__pycache__/` are present in the working tree. All gitignored
  (`.gitignore:99-103`), so harmless — the tree is simply not pristine.
- **`RECORD_FIELDS` has no reader.** Named in TD-8; the open question is whether
  it is intended as the single source of truth or is vestigial.
- **Migration backfill scope.** `_COPY_ROWS_INTO_V1_TABLE` backfills only
  `provider` (`app/db.py:119`). A store missing a value in any *other* added
  column aborts the copy with an `IntegrityError` — which, inside the
  transaction, becomes a **loud startup failure** rather than data loss. That is
  the safe outcome, but it is a narrower guarantee than "every pre-v1 store
  migrates".
- **Version floors, not pins.** No lockfile, no hashes, no audit cadence, no
  update owner. Noted in **technology-stack.md** §Supply Chain Posture.

### Debt summary

| ID | Severity | One line |
|---|---|---|
| TD-12 | High (intent) | The analytics view is a scaffold — no terms fetch, no range control, no partial-failure marker, no superseded-response guard |
| TD-10 | High (process) | No CI — every gate is opt-in |
| TD-2 | Medium | A new column on `analyses` is a five-place edit |
| TD-7 | Medium | No pagination beyond a bare `LIMIT` |
| TD-8 | Medium | The record contract has several copies plus a positional export copy |
| TD-11 | Medium | Zero browser-side execution coverage — now the NFR4.6/NFR4.7 blocker |
| TD-13 | Medium (intent) | No verification script, secret scanner, dependency audit or allowlist exists |
| TD-15 | Medium | Lockfile, LICENSE and `TID251` obligations from the prior intent are open |
| TD-9 | Low (by design) | The two production HTTP transports are uncovered |
| TD-14 | Low | README names a non-existent `AnalyticsRead` symbol |
| TD-1 | — | **Closed** — the migration now creates and preserves the indexes |
| TD-3 | — | **Closed** — the local DB has migrated to v4 with its indexes and rows |
| TD-4 | — | **Closed** — `mean intensity` was dropped from the requirement |
| TD-5 | — | **Closed** — R-01 fixed (`check_same_thread=False` + the request-scoped invariant) and reproduced by test |
| TD-6 | — | **Closed** — the tokeniser is the leaf `app/terms.py` |

---

## Resolved Contract Conflict, and the One Still Open

**Resolved (prior intent).** An earlier scan raised "mean intensity" as a
requirement question because `intensity` is retired (TD-4, BR3.4).
`261001-analytics-layer` settled it by **dropping the field from the summary
requirement** rather than reporting a null or reintroducing the column, so the
conflict no longer blocks anything. It is recorded as closed rather than deleted,
because a future request could reopen it.

**Still open (this intent).** NFR4.6 and NFR4.7 are stated as runtime page
behaviours (one section can fail while another succeeds; a superseded response is
discarded), but the dependency cap forbids browser automation and
`tests/test_page.py` never executes `app.js`. So the criteria **have no decidable
instrument today** (TD-12, TD-11). Their verifiable half is static served-asset
structure plus the single manual end-to-end line; any acceptance criterion that
demands a browser assertion cannot be met under the cap. Raised here because it
is cheaper to surface at synthesis than to discover during code generation.

---

## Verified Working, Worth Preserving

Not debt — the properties a change should not break. Each is verified in this
run unless marked.

| Property | Evidence |
|---|---|
| The suite is green and the floor is satisfied | **Re-measured by the scan:** 192 passed, 97.06% |
| The lint and format checks are clean | **Re-measured by the scan:** both green (30 files) |
| No test can reach the network | `offline_guard` replaces `socket.socket.connect`; `tests/test_dummy_client.py` proves the guard is armed |
| No test touches the real database or config | `tmp_path`-scoped fixtures |
| `init_db` is idempotent | **Re-measured:** run twice against a migrated store, no change |
| Migration preserves rows, indexes and unrelated tables | **Re-measured:** the row and its `intensity` value survived; a side table survived; the three analytics indexes survive a v3 → v4 migration (`tests/test_migration_indexes.py`) |
| A migration that cannot preserve every row fails loudly | one transaction, `rollback()` on any `BaseException` |
| SQLite JSON1 and `strftime` are available | **Re-measured:** `json_extract` and `strftime('%Y-%m-%d', …)` both work |
| The dependency cap holds | asserted by `tests/test_config.py` |
| Nothing is fabricated and stored | validation gates before the engine; `validate_result` before the insert |
| The returned record is the persisted record | `insert_analysis` re-reads the row by id |

For the layer rules, the component boundaries and the extension seams, see
**architecture.md** and **component-inventory.md**. For endpoints and payloads,
**api-documentation.md**. For versions and tool configuration,
**technology-stack.md**. For the module import graph,
**dependencies.md**.