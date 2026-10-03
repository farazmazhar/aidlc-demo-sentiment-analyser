# Integration Test Instructions — intent `261001-analytics-layer`, Unit `u1-analytics-slice`

> **Stage:** `build-and-test` (construction) · **Test strategy:** `standard`
> (which requires this file) · **Record:** `aidlc/spaces/default/intents/261001-analytics-layer`
>
> **Inputs this file was derived from** (the stage's declared `consumes`):
> `construction/u1-analytics-slice/code-generation/code-generation-plan.md` ·
> `construction/u1-analytics-slice/code-generation/unit-test-instructions.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md`, and the
> measurable target inventory in `construction/u1-analytics-slice/nfr-requirements/` +
> `construction/u1-analytics-slice/nfr-design/`.

## 1. Framework and configuration

There is **one** test framework and **no marker-based tiering**: `pytest`, configured
entirely in `pyproject.toml`.

| Setting | Value | Where |
|---|---|---|
| `testpaths` | `["tests"]` | `[tool.pytest.ini_options]` |
| `addopts` | `-q --cov=app --cov-report=term-missing --cov-fail-under=80` | `[tool.pytest.ini_options]` |
| `filterwarnings` | `["error"]` | `[tool.pytest.ini_options]` — every warning from every source is a failure |
| coverage source | `["app"]` — the **whole** application, including the live client the offline suite does not import | `[tool.coverage.run]` |
| coverage floor | `80` lines, stated twice (`addopts` and `[tool.coverage.report] fail_under`) | never lowered to make a step pass |
| markers | **none** — no `integration` marker exists | — |
| fixtures | `tmp_path`-scoped settings and database paths; `offline_guard` (session, autouse); `asgi_request`; `concurrent_requests`; `application_started`; `serve_started` | `tests/conftest.py` |

**There is no integration marker, so integration tests are selected by file path.**
That is deliberate: the repository's standing policy is that assertions read values
back out of **real** SQLite and **real** served markup, never out of a double of the
thing under test, so the "integration" tests are simply the ones that cross a
process boundary. There are **zero mock objects** in the suite; `monkeypatch` is the
sanctioned substitution instrument and is used only at real process seams.

### 1.1 The `APPIMAGE` prefix — read this before running anything

On this host the shell exports `APPIMAGE=…opencode-desktop-linux-x86_64.AppImage`,
which makes CPython report the AppImage as `sys.executable`. One test spawns
`sys.executable` and then fails with exit code 130 for an environmental reason.
**Every command in this file is prefixed `env -u APPIMAGE`.** Full explanation and
proof: `build-instructions.md` §6.

## 2. How to run

All commands run from the repository root.

### 2.1 The whole suite — the gate that carries the coverage floor

```bash
env -u APPIMAGE python -m pytest -q
```

Measured: **192 passed**, 1.65 s, `TOTAL 884 stmts / 26 missed / 97.06 %`,
`Required test coverage of 80% reached`, **exit 0**.

### 2.2 The integration selection (this file's subject)

```bash
env -u APPIMAGE python -m pytest -q \
  tests/test_analytics_routes.py \
  tests/test_migration_indexes.py \
  tests/test_page.py \
  tests/test_terms.py \
  --no-cov
```

Measured: **53 tests**, all passing. These are the four files that cross a process
boundary — the served ASGI application, the real migration against a real file, the
real served markup and served script, and the engine/tokeniser parity instrument.

`--no-cov` is used because `addopts` applies the **whole-application** floor to
*every* run, and a four-file subset cannot cover the whole application (it scores
66 %). Coverage is a whole-suite property; see §4.

### 2.3 The recorded per-unit command (from `unit-test-instructions.md`)

```bash
env -u APPIMAGE python -m pytest -q \
  tests/test_analytics_read.py \
  tests/test_analytics_routes.py \
  tests/test_terms.py \
  tests/test_migration_indexes.py \
  --cov-fail-under=0
```

Measured: **67 passed**, **exit 0**, `TOTAL 884 stmts / 301 missed / 66 %`.

> **The documented residual, restated because it is a real gap and not a green
> light.** That command carries `--cov-fail-under=0` (amended and reasoned in
> `unit-test-instructions.md`), so **it has no coverage gate of any kind**: it
> exits 0 at 66 %. Read the number; do not rely on its exit code. The whole-suite
> floor is untouched — `addopts` still carries `--cov-fail-under=80` and
> `[tool.coverage.report] fail_under = 80` is unchanged, so §2.1 still exits
> non-zero below 80 %.

### 2.4 Named-test selection

```bash
# Boundary: the two handlers end to end over real SQLite.
env -u APPIMAGE python -m pytest --no-cov -q tests/test_analytics_routes.py

# Boundary: the additive migration, index survival, read-only and no-mutation.
env -u APPIMAGE python -m pytest --no-cov -q tests/test_migration_indexes.py

# Boundary: served markup and the served script.
env -u APPIMAGE python -m pytest --no-cov -q tests/test_page.py

# One test by name.
env -u APPIMAGE python -m pytest --no-cov -q \
  "tests/test_analytics_routes.py::test_the_analytics_endpoints_are_proved_offline_by_an_armed_guard"

# Show names and per-test outcomes (addopts' `-q` hides them).
env -u APPIMAGE python -m pytest -p no:cacheprovider -v --no-cov tests/test_analytics_routes.py

# Count without running (fast inventory).
env -u APPIMAGE python -m pytest --collect-only -q --no-cov -p no:cacheprovider
```

Measured inventory (`--collect-only`, 15 modules):

| Module | Tests | Module | Tests |
|---|---|---|---|
| `test_analytics_read.py` | 23 | `test_live_client.py` | 15 |
| `test_analytics_routes.py` | 25 | `test_bulk_import.py` | 17 |
| `test_migration_indexes.py` | 9 | `test_routes.py` | 17 |
| `test_page.py` | 9 | `test_auth_routes.py` | 12 |
| `test_terms.py` | 10 | `test_session_auth.py` | 12 |
| `test_config.py` | 11 | `test_db.py` | 8 |
| `test_dummy_client.py` | 6 | `test_repository.py` | 8 |
| `test_service.py` | 10 | **Total** | **192** |

## 3. What each integration boundary is, and what pins it

| # | Boundary crossed | Tests | What is actually exercised |
|---|---|---|---|
| I1 | HTTP edge → read module → real SQLite | 25 in `test_analytics_routes.py` | The two `/v2` handlers served by the real application against a real migrated store: hand-pinned aggregates, inclusive UTC day bounds, a single bound, zero-filled days, empty success, unmatched `import_id`, all three `422` refusals, both `500 STORAGE_FAILURE` paths, `/v1` unchanged, prefix equality |
| I2 | Startup → migration → schema (`v3` → `v4`) → real file | 9 in `test_migration_indexes.py` | Row-preserving additive step, idempotency on an already-`v4` store, the three indexes by name on both the fresh and migrating path, index survival after a real rebuild, the rebuild issuing the `CREATE INDEX` statements itself, loud rollback, read-only before/after, no mutating statement traced on the request's own connection |
| I3 | Server → browser-facing markup and script | 9 in `test_page.py` | 16 analytics `data-testid` hooks present in the served HTML, the served `app.js` carrying the `API_V2` prefix and exactly one summary fetch, `position: fixed` gone |
| I4 | Tokeniser → offline engine (the U1→U2 seam) | 10 in `test_terms.py` | The end-to-end parity instrument (a 17-text corpus, all three labels) **and** the sharp instrument: an exhaustive sweep of all 1,110 strings of length 1–3 asserting token-for-token equality with `re.compile(r"[a-z']+").findall(text.lower())` |
| I5 | Threads → connection lifecycle (R-01) | 3 in `test_analytics_routes.py` | The driver opened on one thread and used/closed on another behind a barrier; two genuinely overlapping requests both `200`; a 24-request soak; `init_db` asserted to run exactly once across a concurrent batch |
| I6 | Offline guard → the whole suite | 1 in `test_analytics_routes.py` | The guard is **proved armed**, not merely present: the analytics endpoints are exercised with `socket.socket.connect` replaced by a raiser, and the test fails on `ConnectionRefusedError` if that assignment is removed |

### 3.1 Cross-unit interaction — the seam worth naming

`app/analytics.py:41` holds a live **`U1 → U2`** import edge:

```python
from app.terms import significant_terms, tokenize
```

`app/terms.py` is attributed to `u2-term-extraction` by three inception artifacts and
was authored here anyway, because the approved plan step assigned it to this Unit and
the engine could not sequence U2 first. `code-summary.md` § Deviations (d) and §
Post-review amendments R-02 disclose this in full; **Build and Test does not
re-decide it.** What Build and Test does is report the consequence for testing:

* the seam is covered by `tests/test_terms.py` (10 tests), so the cross-unit import is
  exercised, not assumed;
* `u2-term-extraction` **must adopt** `app/terms.py` rather than re-derive it, and
  should expect to edit three U1 manifest writes if it decides the stopword set
  differently (`code-summary.md` § R-09);
* until U2 runs, the binding recorded in `unit-of-work.md:96` is violated. That is a
  **disclosed deviation**, not a Build and Test finding, and it is listed as a known
  limitation in `build-and-test-summary.md`.

Two further seams are exercised without being special: `app/dummy_client.py` imports
the same `tokenize` (so the offline engine's scoring is pinned unchanged), and
`app/db.py`'s migration is what `app/analytics.py`'s reads stand on (I2 + I1
together).

## 4. Expected coverage for this strategy level

**Strategy `standard` + `feature` scope floor.** The binding coverage requirement is
the affirmed **whole-application 80 % line floor**, and the measurement is the
**whole application** (`source = ["app"]`), not the unit:

| Scope of the run | Coverage command | Floor applied? | Measured |
|---|---|---|---|
| **Whole suite** (§2.1) | `--cov-fail-under=80` + `fail_under = 80` | **Yes — this is the gate** | **97.06 %** (884 stmts, 26 missed) |
| Unit-scoped (§2.3) | `--cov-fail-under=0` | No — by the recorded amendment | 66 % |
| Integration selection (§2.2) | `--no-cov` | No | not reported |

Per-module, on the whole-suite run:

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| `app/analytics.py` | 112 | 0 | **100 %** |
| `app/terms.py` | 11 | 0 | **100 %** |
| `app/db.py` | 78 | 0 | **100 %** |
| `app/models.py` | 65 | 0 | **100 %** |
| `app/config.py` | 54 | 0 | 100 % |
| `app/dummy_client.py` | 22 | 0 | 100 % |
| `app/repository.py` | 23 | 0 | 100 % |
| `app/sentiment.py` | 22 | 0 | 100 % |
| `app/service.py` | 73 | 0 | 100 % |
| `app/__init__.py` | 2 | 0 | 100 % |
| `app/main.py` | 53 | 1 | 98 % (line 103) |
| `app/routes.py` | 172 | 2 | 99 % (lines 257–258, a `csv.Error` branch) |
| `app/openrouter_client.py` | 80 | 6 | 92 % (lines 89–96) |
| `app/session_auth.py` | 117 | 17 | 85 % (lines 84–120) |

**All 26 missed lines are pre-existing** and none is in a module this Unit created.
`session_auth.py:84-120` and `openrouter_client.py:89-96` are the two production HTTP
transports; every test injects an exchanger or a transport because the affirmed
dependency cap (exactly two runtime packages) forbids an HTTP client library.
`routes.py:257-258` is the `/v1` bulk-import `csv.Error` branch — untouched by this
Unit (it was lines 217–218 before this Unit added code above it).

**Branch coverage is off by affirmed decision** (`team.md` § Testing Posture,
2026-10-02), and the cost is recorded there: 98 branches with 3 partial
(`app/db.py:208`, `app/main.py:49`, and the partial edge `app/routes.py:385->387`),
none of which an 80 % line floor can see. Build and Test does not turn it on and
does not weaken the line floor.

## 5. Test data management and environment setup

| Concern | Arrangement |
|---|---|
| Isolation | Every test builds its own store under `tmp_path` (`Settings(db_path=tmp_path / "sentiment.db")`). **No test reads `config.local.toml` or `data/sentiment.db`.** |
| Schema | `db.init_db()` runs in the application's lifespan and is idempotent, so every in-process request exercises migration idempotency for free. |
| Performance fixture | 10,000 analyses pinned to span **exactly 365 distinct UTC days** — the span is part of the target, not a convenience (`NFR1.1`). It lives in `tmp_path` and costs a few MB. |
| Deterministic dates | `app.analytics.resolve_range` takes a `today` seam; tests pin it, so the unbounded case does not depend on the wall clock. |
| Network | Forbidden. The session-scoped autouse `offline_guard` replaces `socket.socket.connect` with a raiser, and `I6` proves the guard is armed. |
| Credentials | None required. Live-mode paths inject a fake transport; the real key is gitignored and never reaches a test. |
| Git | Required — `tests/test_config.py` shells out to `git check-ignore`. |
| Environment variables | None. |

## 6. Known gaps in the integration surface

Stated here rather than discovered later. These are **disclosed limitations**, each
already recorded upstream; none is a Build and Test finding.

1. **No browser execution.** `app/static/app.js` is served and its markup is pinned;
   nothing in the suite runs it (`tests/test_page.py:1-6` states the reason). No
   JavaScript test runner is configured.
2. **The two production HTTP transports are untested** (23 of the 26 missed lines),
   by the dependency cap.
3. **The cross-section partial-failure marker and the out-of-order-response discard
   are not testable in this Unit.** `NFR4.6` and `NFR4.7` need a *second* analytics
   section and a *range control*, both owned by `u3-analytics-view`. Their verdict is
   `Unverified` in `build-and-test-summary.md`; the evidence and the owning work are
   recorded there. **No test was invented to cover them**, because a test written
   against markup that does not exist yet would assert nothing.
4. **No secret scanner and no dependency audit.** `FR7.3` is a
   `u4-platform-packaging` obligation; `team.md` records that no scanner exists today.
   The instruments `security-test-instructions.md` uses instead are named there.