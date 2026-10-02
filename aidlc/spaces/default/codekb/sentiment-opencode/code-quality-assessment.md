# Code Quality Assessment — `very-cool-sentiment-analysis` (repo `sentiment-opencode`)

All numbers in this artifact were **re-measured during this synthesis** against
commit `beeb587`, not carried over from the scan. Commands and results are
reproduced so they can be re-run.

## Headline

| Signal | State | Assessment |
|---|---|---|
| Tests | **118 passed**, 0 failed, 0 skipped | Green |
| Line coverage | **96.02%** (679 statements, 27 missed) against an **80%** floor | Far above the floor |
| Lint | `ruff check app tests` → *All checks passed!* | Clean |
| Format | `ruff format --check app tests` → *24 files already formatted* | Clean |
| CI/CD | **None** | The largest process-level gap |
| Type checking | **None** | Annotations are 100% applied and entirely unenforced |
| Test doubles | **Zero mock objects** | Every double is a hand-written class at a real seam |
| Documentation | Strong and unusually traceable | The README *is* the contract of record |

The short version: this is a small, disciplined codebase with an unusually
honest documentation practice, whose weaknesses are concentrated in **three
places** — the database migration path, the absence of any automated gate, and
the frontend having zero execution coverage.

---

## Test Coverage

### Test surface

| | |
|---|---|
| Directory | `tests/` — one directory, no sub-directories, no fixtures directory |
| Harness | `tests/conftest.py` (176 lines) — `asgi_request`, `offline_guard`, `tmp_settings`, `tmp_db_path` |
| Framework | `pytest` **only**. No `unittest`, no `hypothesis`, no `asyncio` marker |
| Mocking library | **none** — not even `unittest.mock` |
| Parametrization | 5 sites, expanding 109 test functions to 118 collected tests |

| Module | Functions | Lines | What it pins |
|---|---|---|---|
| `tests/test_db.py` | 8 | 436 | schema creation, migration from pre-v1, column order, NOT NULL flags, label CHECK, `intensity` absence |
| `tests/test_routes.py` | 15 | 363 | the full `/v1` contract, the envelope, the record field set, `limit` handling |
| `tests/test_bulk_import.py` | 16 | 315 | CSV parsing, header skip, per-row skipping, `import_id` grouping, export round trip |
| `tests/test_service.py` | 9 | 304 | orchestration order W1, engine resolution precedence, `ImportSummary` aggregation |
| `tests/test_auth_routes.py` | 12 | 259 | the `/auth/*` routes and their redirect behaviour |
| `tests/test_repository.py` | 8 | 237 | DML, `format_timestamp`, `import_id` scoping, `intensity` never read |
| `tests/test_live_client.py` | 9 | 220 | typed answer reading, error mapping, transport injection |
| `tests/test_session_auth.py` | 12 | 196 | PKCE verifier/challenge, expiry, credential redaction, injected exchanger |
| `tests/test_config.py` | 10 | 180 | the six resolution outcomes, redaction, `git check-ignore`, the dependency-cap assertion |
| `tests/test_dummy_client.py` | 6 | 84 | keyword classification, and that the offline guard is actually armed |
| `tests/test_page.py` | 4 | 77 | served markup, 14 `data-testid` hooks, `role="status"`, `aria-live`, asset content type, absence of `intensity` |

The largest test module covers the **migration path** — 436 lines against 243
lines of `app/db.py`. That ratio is the clearest signal of where this project's
risk actually lives.

### Measured coverage

Command: `python -m pytest -q`

```
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
app/__init__.py                2      0   100%
app/config.py                 54      0   100%
app/db.py                     66      1    98%   208
app/dummy_client.py           23      0   100%
app/main.py                   42      1    98%   49
app/models.py                 33      0   100%
app/openrouter_client.py      80      6    92%   89-96
app/repository.py             23      0   100%
app/routes.py                144      2    99%   217-218
app/sentiment.py              22      0   100%
app/service.py                73      0   100%
app/session_auth.py          117     17    85%   84-120
--------------------------------------------------------
TOTAL                        679     27    96%
Required test coverage of 80% reached. Total coverage: 96.02%
```

Seven of twelve modules are at **100%**. The 27 missed statements are:

| Uncovered block | Lines | Why |
|---|---|---|
| `exchange_code_at_openrouter` body | `app/session_auth.py:84-120` | Every test injects a double, so the real `urllib` request is never built |
| `urllib_transport` body | `app/openrouter_client.py:89-96` | Same reason — the transport is always injected |
| `csv.Error` branch | `app/routes.py:217-218` | Hard to provoke; Python's `csv` reader is permissive |
| `PRAGMA table_info` absence guard | `app/db.py:208` | A table always has DDL text |
| logging-handler guard | `app/main.py:49` | Environment-dependent |

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
| Browser-side execution of `app.js` | No browser-automation dependency is permitted under the cap; `tests/test_page.py:1-6` states this explicitly | The page's behaviour is unverified. The markup and the asset are pinned; **nothing that runs is** |
| Concurrency | No thread/concurrency test exists anywhere | The accepted R-01 defect has **no reproducing test** |
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
24 files already formatted
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
convention a checker would enforce: `from __future__ import annotations` in all
12 modules and full annotations on **every** public function, with only two
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

The coverage floor, the ruff rule set and the 118 green tests are therefore the
**only** safety net, and they run only when whoever is working remembers to run
them. That is TD-10.

---

## Documentation Quality

**Strong, and unusually traceable for a project of this size.**

| Artifact | State |
|---|---|
| `README.md` (266 lines) | Genuinely maintained: setup, run, test/lint commands, the in-app connection flow, the two modes, configuration, the storage/migration contract, the **HTTP surface table** (all 11 routes, each with its behaviour), the file-layout tree, known limitations, and an end-to-end verification command. Every route and constant in the table matches the code. |
| Module docstrings | All 12 modules; 11 carry an explicit `Single responsibility:` line naming what the module does **not** contain |
| Function docstrings | Present throughout, frequently citing the rule the function enforces |
| Embedded traceability | `FR4.1`, `NFR3.1`, `BR4.3`, `AC7.1.2`, `R-01`, `R-04`, `D1`–`D4`, `W1` appear in docstrings and comments throughout `app/` and `tests/`, and the same IDs are used in the README |
| Constants | Semantic constants carry `#:` prose stating why |
| **Absent** | No `docs/` directory, no ADRs, no OpenAPI spec file, no changelog |

The traceability density is a genuine strength — the code is self-describing
against its own requirement set. It is also a readability cost for anyone
without those upstream artifacts, and the IDs are not mechanically generated, so
they can drift from the requirements they cite. Treat them as a human-maintained
cross-reference, not a verified link.

**Structural metrics.** No file exceeds 500 lines. Longest functions are
`import_texts` (41) and `SessionAuth.complete` (41), both linear loops. No class
exceeds 100 lines. No SQL in `routes.py`, no sentiment logic in `routes.py`, no
HTTP in `service.py`. No circular imports. Zero `TODO`/`FIXME`/`HACK`/`XXX`.

**Suppressions: nine, all narrow and justified.**

| Count | Suppression | Justification |
|---|---|---|
| 4 | `# pragma: no cover` | Branches unreachable by construction: `app/db.py:190`, `app/repository.py:22`, `app/routes.py:353`, `tests/test_config.py:165` |
| 4 | `# noqa: S310` on `urllib` calls | The endpoint is a hardcoded `https` constant, commented as such: `app/openrouter_client.py:89,93`; `app/session_auth.py:88,96` |
| 2 | `# type: ignore[method-assign]` | Replacing `socket.socket.connect` in the offline guard: `tests/conftest.py:152,156` |

No blanket suppressions, no file-level `# ruff: noqa`.

---

## Technical Debt Register

Severity is about **cost to the next change**, not about correctness today.

### TD-1 — The migration silently drops every index on `analyses` · **High**

`_rebuild_analyses` (`app/db.py:233-243`) renames the table to `analyses_pre_v1`,
creates a fresh `analyses` from `CREATE_ANALYSES_TABLE`, copies rows, and drops
the old table. `CREATE_ANALYSES_TABLE` (`app/db.py:40-53`) **declares no indexes
at all**, so nothing recreates them.

**Verified empirically** at this commit: a store carrying
`CREATE INDEX idx_analyses_created ON analyses(created_at)` plus a second,
unrelated table and one row at schema version 2 came out of `init_db` with the
columns correct, the row preserved (including its `intensity` value), the side
table untouched and the version bumped to 3 — and `sqlite_master` reporting
**zero** indexes on `analyses`. Running `init_db` a second time is idempotent and
changes nothing, so the index is simply gone for good.

**Why it matters.** An index added to `CREATE_ANALYSES_TABLE` disappears on any
migrating store, with no warning and no failed assertion. The only current
mitigation is that `analyses` has no index to lose today.

**Fix shape.** Create the index idempotently **inside `init_db`, after** the
rebuild branch — `CREATE INDEX IF NOT EXISTS` — since `init_db` runs on every
startup. A separate table is untouched by the rebuild and needs nothing.

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

### TD-3 — The committed dev database is one schema version behind the code · **Low**

`data/sentiment.db` reports `schema_meta.version = 2` with columns lacking
`import_id`, while `SCHEMA_VERSION = 3`. It holds 0 rows and `/data/` is
gitignored (`.gitignore:94`), so this is local machine state only — but it means
**the v2 → v3 path has never actually run against that file**.

### TD-4 — The retired `intensity` attribute makes a "mean intensity" metric impossible · **High (contract, not code)**

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
`NULL` for every row written since v1. Any requirement asking for a mean
intensity is asking for a value this system does not produce. This is the one
requirement that **cannot be implemented as written without a human decision** —
return `null`, omit the field, or reintroduce a written intensity column (which
reverses a v1 decision and breaks the page assertion). See §Unresolved Contract
Conflict below.

### TD-5 — Accepted cross-thread SQLite defect, inherited by every new endpoint · **Medium (known, accepted)**

A per-request `sqlite3.Connection` created in one anyio worker thread
(`get_connection`, `app/routes.py:92-98`) and closed in another raises
`sqlite3.ProgrammingError` and answers `500` when requests overlap. Sequential use
is unaffected. The README records it and the fix as explicitly out of scope for
v1, and the finding was accepted by the human at the Code Generation gate.

**Why it is still worth naming.** `get_connection` is the single place it
happens, so **every current and future endpoint inherits it**, and a polling,
date-range-filtered analytics page is precisely the access pattern most likely to
expose it. Treat it as a known, already-documented constraint — and note that
one decision in one function would fix it for everything.

### TD-6 — `_WORD` is the only tokenizer, and it lives in the wrong module · **Medium**

`app/dummy_client.py:68` declares `_WORD = re.compile(r"[a-z']+")`, used at
line 83. It is the **only** tokenizer in the codebase, it is underscore-private,
and it sits in the *offline engine* rather than in a shared place.

**Consequence.** Any second consumer either reaches into an unrelated module's
private name or duplicates the regex. The codebase has **no** `utils.py` or
`helpers.py` by a deliberate convention (a helper lives with the concept it
serves), so there is no obvious destination — which is exactly why this needs a
named decision rather than an import.

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
two-package cap, and `tests/test_page.py:1-6` says so plainly. The practical
consequence: a behavioural regression in the page — a wrong fetch URL, a broken
`textContent` write, a date-filter handler that never fires — would pass the whole
suite. This scope includes no CI and no new dev dependency, so the gap is
structural rather than a choice to make here.

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
| TD-1 | High | The migration silently drops every index on `analyses` |
| TD-4 | High (contract) | Retired `intensity` makes a mean-intensity metric impossible |
| TD-10 | High (process) | No CI — every gate is opt-in |
| TD-2 | Medium | A new column on `analyses` is a five-place edit |
| TD-5 | Medium | Accepted cross-thread SQLite defect, inherited by every new endpoint |
| TD-6 | Medium | The only tokenizer is a private of the offline engine |
| TD-7 | Medium | No pagination beyond a bare `LIMIT` |
| TD-8 | Medium | The record contract has four copies plus a positional fifth |
| TD-11 | Medium | Zero browser-side execution coverage |
| TD-3 | Low | The committed dev database is one schema version behind |
| TD-9 | Low (by design) | The two production HTTP transports are uncovered |

---

## Unresolved Contract Conflict

One finding from the scan that is a **requirement question, not a code defect**,
recorded here so it is not lost between stages.

The active intent asks for **"mean intensity"** in the analytics summary.
`intensity` is a **deliberately retired** attribute (TD-4, BR3.4). This is not a
gap the implementation can close by doing more work — the three possible
outcomes are all decisions:

| Option | Consequence |
|---|---|
| Return `mean_intensity: null` | Honest, and consistent with the in-repo precedent A3 (`mean_confidence` is `null` when nothing was imported). Needs a stated contract for the null case |
| Omit the field entirely | Also honest; the client then cannot distinguish "no such metric" from "zero" |
| Reintroduce a written `intensity` column | **Reverses a v1 decision.** Breaks `tests/test_page.py:64-68`, the record contract, and BR3.4, and requires a schema change plus a migration |

The intent's own instruction is that an ambiguous requirement should be raised
rather than guessed. This is that item, raised at synthesis time because it is
cheaper to surface here than to discover during code generation.

---

## Verified Working, Worth Preserving

Not debt — the properties a change should not break. Each is verified in this
run unless marked.

| Property | Evidence |
|---|---|
| The suite is green and the floor is satisfied | **Re-measured:** 118 passed, 96.02% |
| The lint and format checks are clean | **Re-measured:** both green |
| No test can reach the network | `offline_guard` replaces `socket.socket.connect`; `tests/test_dummy_client.py` proves the guard is armed |
| No test touches the real database or config | `tmp_path`-scoped fixtures |
| `init_db` is idempotent | **Re-measured:** run twice against a migrated store, no change |
| Migration preserves rows and unrelated tables | **Re-measured:** the row and its `intensity` value survived; a side table survived |
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