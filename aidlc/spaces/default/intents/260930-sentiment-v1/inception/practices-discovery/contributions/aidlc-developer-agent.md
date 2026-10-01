**Collaborator:** aidlc-developer-agent

## Contribution

Scope of this review: the **Code Style** section of `team-practices.md` plus every other
draft claim that touches code, module organization or error handling. Method: I read all
12 `app/*.py`, `tests/conftest.py` and every `tests/test_*.py` header, `pyproject.toml`,
`README.md`, ran the import-graph and docstring checks below, and executed one scoped,
read-only probe against the real application to test the error-envelope claim. I did not
run the suite or edit any source.

### 1. What the draft gets right in `## Code Style` (independently reverified)

| Draft claim | Verdict | Evidence I read |
|---|---|---|
| 2. Full type annotations on every function | **correct** | AST scan: every `def` in `app/*.py` has a return annotation; all 11 substantive modules open with `from __future__ import annotations` |
| 4. Underscore-prefixed private helpers/state | **correct** | `_read_choice`/`_read_score`/`_post_decisions` (`app/openrouter_client.py`), `_pending`/`_drop_expired_pending` (`app/session_auth.py:255`), `_configure_logging`, `_read_config_file`, `_INSERT_SQL`, `_WORD` |
| 5. Naming (`snake_case`/`PascalCase`/`UPPER_CASE`, `test_<module>.py`) | **correct** | test file names and all 52 `test_<behaviour>` functions; type alias `Mode = Literal[...]` (`app/config.py:20`) correctly PascalCase |
| 8. Parameterised SQL only | **correct** | `app/db.py`, `app/repository.py` — every statement uses `?` placeholders |
| 9. Secrets redacted by construction | **correct** | `Settings.__repr__` (`app/config.py:47`), `SessionCredential.__repr__` (`app/session_auth.py:131`), `OpenRouterClient.__repr__` (`app/openrouter_client.py:93-95`) |
| 11. Pure helpers stay class-less module functions | **correct** | `format_timestamp` (`app/repository.py:33`), `create_code_verifier`/`code_challenge_for` (`app/session_auth.py`) |
| 12. Freeform prose docstrings, no section format | **correct** (one exception, §3.7) | zero `Args:`/`Returns:`/`Raises:` anywhere in `app/` or `tests/` |
| Enforcement gap (no linter/formatter/type checker) | **correct and measurable** — see §4 | root listing + `pyproject.toml` |

The Testing Posture bullets that touch code also hold as written: 52 test functions across
9 test modules (I counted them), `filterwarnings = ["error"]` is the only mechanical gate,
and `tests/conftest.py:129-146` is the offline guard that makes `app/openrouter_client.py`
structurally untestable-by-accident.

### 2. Corrections — draft claims the code does not support

Each of these is a wording fix the lead should apply, not a disagreement about the intent.

1. **"One error envelope … covers every non-2xx response" (claim 7) — false.** It covers
   every error *the application raises*, and nothing else. Handlers are registered for four
   exception types only (`app/main.py:93-96`; `error_response` at `app/routes.py:41-57`).
   Framework-generated failures bypass it. I proved this against the real app with the
   repo's own in-process harness:

   | probe | status | body |
   |---|---|---|
   | `GET /nope` | 404 | `{"detail": "Not Found"}` |
   | `POST /health` | 405 | `{"detail": "Method Not Allowed"}` |
   | `GET /static/missing.js` | 404 | `{"detail": "Not Found"}` |

   Suggested wording: *"one error envelope, with four machine codes, for every error the
   application code raises; framework-generated routing errors (unknown path, wrong method,
   missing static asset) still return FastAPI's `{"detail": …}`."* This matters because the
   draft's stated consequence ("a handler that bypassed it would break both [page and
   tests]") is only true for app-raised errors — the tests do not currently cover a 404.

2. **"Module constants … documented with `#:` comments" (claim 3) — over-claimed, and the
   example is wrong.** 39 `UPPER_CASE` module constants exist; **20 have no adjacent `#:`**.
   The second example, "the TTL constants in `app/session_auth.py`", is half wrong:
   `PENDING_TTL_SECONDS` is documented but `EXCHANGE_TIMEOUT_SECONDS` (`app/session_auth.py:53`)
   is not. Suggested wording: *"Constants are `UPPER_CASE`; the semantic ones carry a `#:`
   doc comment (schema version, column order, labels, endpoints, TTLs, error codes); the
   numeric/path defaults, the SQL text and `PORT` do not."*

3. **"`app/` does not import pydantic … sharing one field list" (claim 10) — half true.**
   The pydantic half is verified (zero `pydantic` references in `app/`; `app/models.py` uses
   stdlib dataclasses). The "one field list" is **not** mechanically shared. Verified copies
   of the record contract: `RECORD_FIELDS` (`app/models.py:20`) — referenced **nowhere**
   (not in `app/`, not by tests; `tests/test_routes.py:22` declares its own private set);
   the `AnalysisRecord` field declarations (`app/models.py:47-62`); the hand-written literal
   in `to_dict()` (`app/models.py:64-77`); and `ANALYSES_COLUMNS` + the `CREATE TABLE` text
   (`app/db.py:15-48`). So the honest statement is *"one documented contract, four
   hand-written copies, kept in sync by tests"* — which is exactly the CodeKB's TD-7. Note
   the CodeKB file contradicts itself here (`code-quality-assessment.md` "Consistency
   Positives" says `RECORD_FIELDS` is "used by storage and the wire"; its own TD-7 says
   "four hand-written copies"). The draft inherited the wrong half of that source.

4. **"Naming its single responsibility and the requirement ids it satisfies" (claim 1) —
   two exceptions.** `app/__init__.py`'s docstring names its purpose but has no
   "Single responsibility" line; `app/session_auth.py` has the line but cites **no**
   requirement id at all (it postdates the prior intent). So "every module" is really
   "11 of 12, with `session_auth.py` the known exception" — which sharpens draft open
   question 4 (id staleness) into a real, already-visible drift rather than a future risk.

5. **"Domain exceptions … mapped to status codes only in `app/routes.py`" (claim 6) —
   imprecise.** Three of the five become envelope responses through handlers registered in
   `app/main.py:93-96` (`InvalidTextError`→422, `SentimentEngineError`→502,
   `SentimentAuthError`→502). `AuthExchangeError` is caught inline in the callback route
   (`app/routes.py:154`) and answered with a **302 redirect**, never the envelope.
   `ConfigError` is never mapped to a status at all: it is raised in `app/config.py:67,97`
   and surfaces as a **startup failure** via `load_settings()` in the lifespan
   (`app/main.py:66`); its other raise site is pragma-guarded as unreachable
   (`app/service.py:75-76`).

6. **"Twelve application modules" holding the conventions, and "52 test functions across 10
   files".** 12 counts `app/__init__.py`, a 10-line re-export shim with no functions; the
   conventions are carried by 11 substantive modules (+ 360 lines of `app/static/`, which
   is outside this section and untested by design). 10 files counts `tests/conftest.py`;
   the 52 functions live in 9 test modules (the CodeKB says "9 modules") — keep the two
   counts consistent so later stages don't cite a drifting number.

7. **Minor, docstring style:** `tests/conftest.py`'s module docstring uses Sphinx
   cross-reference roles (`:func:`), while `app/` docstrings use backticks. If "freeform
   prose" is affirmed, decide whether Sphinx roles are in or out — right now one file is a
   one-off.

### 3. Code conventions the draft does not list but the code visibly follows

These are the strongest *unclaimed* signals, and each is a natural ALWAYS/NEVER candidate.

1. **No bare `except`, no broad catch, and causes are chained.** Every handler in `app/`
   names a specific type (`app/config.py:62,66`; `app/openrouter_client.py:161,169,181`;
   `app/routes.py:154`; `app/session_auth.py:99,104,111,209`); zero bare `except`; every
   raise that wraps a caught error uses `from exc` (8 sites). Domain-validation raises
   stand alone, correctly.
2. **No `print()` in `app/`** — logging via module loggers (`app/main.py:36`,
   `app/routes.py:38`), and the key is never logged.
3. **No junk-drawer module**: there is no `utils.py`/`helpers.py`; a pure helper lives in
   the module that owns the concept. This is precisely the convention that erodes first,
   so it is worth stating.
4. **Import block layout** (stdlib / third-party / `app.*`, one blank line between groups)
   is consistent — but ordering *within* a group is not: 4 files are not isort-clean
   (`app/config.py:9`, `app/main.py:9`, `app/routes.py:9`, `tests/test_config.py:9`). So
   "sorted imports" is the norm, not a fact.
5. **Formatting norms**: 4-space indent, double quotes, trailing commas in multi-line
   calls; longest line 109 chars (`app/config.py:125`), only 10 lines exceed 88.
6. **Forward-looking markers exist for tooling that does not exist**: two
   `# pragma: no cover` (`app/repository.py:20`, `app/service.py:75`) and two
   `# type: ignore[method-assign]` (`tests/conftest.py:142,146`). Harmless today; they
   signal the author already expected coverage and a type checker.

### 4. The enforcement gap, measured (the decision the interview must actually make)

- **Verified absence**: no `ruff`/`flake8`/`pylint`/`mypy`/`black`/`isort` section in
  `pyproject.toml`, no `ruff.toml`/`.ruff.toml`/`setup.cfg`/`tox.ini`/
  `.pre-commit-config.yaml` at the root.
- **Measured with a system `ruff` 0.16.9 — not a project dependency — using
  `--isolated --no-cache` (read-only, nothing installed, no config written):** 16 findings
  over `app` + `tests`, 9 auto-fixable: `B008`×6, `I001`×4, `UP035`×2, `UP037`×2,
  `SIM117`×1, `F401`×1 (`tests/test_auth_routes.py:15` imports `pytest` unused).
  `ruff format --check` would reformat **12 of 22** files (same count at line-length 88 and
  100); `--select E501` at 88 flags 18 lines.
- **The trap worth telling the human about**: the 6 `B008` findings are all
  `Depends(...)` in default arguments (`app/routes.py:92,93,104,114,130,162`) — FastAPI's
  own documented idiom. A naive "turn on ruff" decision would force non-idiomatic code or
  a blanket `# noqa`. The interview must decide the *setting*, not just the tool:
  configure `lint.flake8-bugbear.extend-immutable-calls` (ruff's `flake8-bugbear` setting
  for this case) or a per-file ignore for `app/routes.py`.
- **What the numbers mean**: the code is internally consistent but **not
  formatter-canonical**. Adoption cost today is one mechanical commit in a 2-commit
  repository; it only grows.
- **The org rule cannot be satisfied as written.** `memory/org.md` `## Code Style` says to
  adopt the project linter and "Run in CI before merge; failure blocks the PR" — but
  `classic` skips the CI Pipeline stage, so *there is no CI to run it in*. The interview
  must pick a home for the gate: pre-commit hook, a lint step inside Build and Test, a
  named manual habit, or none. `ruff` being present on this machine's PATH is not a
  substitute — an undeclared tool cannot be a gate.
- **Dependency-cap interaction is a real conflict, not a preference.** `pyproject.toml`
  states "Dependency cap (NFR3): fastapi + uvicorn at runtime, pytest for dev, nothing
  else" and `README.md` says the install brings "exactly three packages beyond the standard
  library". Adding `ruff`/`pytest-cov` to `[dev]` falsifies both statements unless they are
  updated in the same change.
- **Cheapest enforcement win**: the annotation convention is already 100 % applied across
  `app/` with zero suppressions there, so a type checker would enforce it almost for free —
  and it is the one convention a linter does *not* cover.

### 5. Module organisation and layer boundaries — absent from the draft, and material

The draft's Code Style section covers micro-style only. The larger, more consequential
conventions here are structural, and the interview should decide them explicitly:

- **`app/` is a flat by-layer package**, not feature-sliced: leaves
  (`config.py`, `models.py`, `db.py`, `sentiment.py`) → `repository.py`, `dummy_client.py`,
  `openrouter_client.py` → `service.py` → `routes.py` → `main.py` → `__init__.py`. I rebuilt
  the graph from imports: acyclic, one direction only.
- **One hexagonal seam**: `SentimentClient` Protocol (`app/sentiment.py:56-61`) with two
  adapters, chosen in exactly one place (`get_client`, `app/service.py`). New engine = new
  adapter, routes/repository/page untouched.
- **Observed boundary rule**: only the HTTP layer touches the `sqlite3` driver and the
  connection lifecycle (`get_connection`, `app/routes.py:70-76`); `repository`/`service`
  receive a connection. That boundary is also where the accepted thread-affinity risk lives
  (already recorded in `memory/project.md` under `## Corrections`). Affirming the rule
  ("connections are opened/closed by the HTTP layer per request; everything below takes a
  connection") makes the accepted limitation explicit and stops connection handling from
  spreading.
- **Decision to add**: as this app grows past ~1.5k lines, does `app/` stay one file per
  layer, or split by feature? At this size the flat layout is idiomatic FastAPI and
  cycle-free; the interview should agree a threshold rather than leave it implicit.

### 6. Interview questions this angle adds (phrased as answerable decisions)

Code Style area — these are additions to the draft's questions 1-5:

1. Do we adopt a formatter + linter now, and at what line length? (Ruff can do both; 88
   changes 18 lines, 100 changes 2. Yes/No + a number.)
2. If yes, what is the `B008`/`Depends` policy — configure
   `extend-immutable-calls` for `fastapi.Depends`, per-file ignore in `app/routes.py`, or
   drop the idiom? (Recommend the first.)
3. Where does the gate run, given `classic` has no CI stage — pre-commit hook, a lint step
   in Build and Test, a manual habit, or nowhere?
4. Does the dependency cap cover dev tooling? If yes, update the NFR3 comment in
   `pyproject.toml` and the README "exactly three packages" line **in the same change**.
5. Which observations become binding ALWAYS/NEVER rules? My shortlist, in priority order:
   no bare or broad `except`; chain with `from exc`; no `print()` in `app/`; every app-raised
   error uses the one envelope; parameterised SQL only; secrets redacted in every `__repr__`;
   stdlib dataclasses rather than pydantic in `app/`; a pure helper lives in its owning
   module (no `utils.py`).
6. The record contract: single-source `RECORD_FIELDS` (use it in `to_dict()` and the tests,
   then delete the copies) or keep the manual duplication and its test guard — and either
   way say what `app/models.py:20` is for, since nothing reads it today.
7. Module organisation: does `app/` stay flat one-file-per-layer, and at what size does that
   change?
8. Requirement-id citations in docstrings/comments: keep citing the prior intent's ids
   (`session_auth.py` already cites none; `app/main.py:33-34`'s "no authentication … exists
   anywhere in this app" is now false), or switch to a lighter rule — and who updates a
   comment when the code moves?
9. Adopt a type checker? Cost is low (full annotations, zero suppressions in `app/`) and it
   is the only way to enforce the annotation convention the draft observes.

### 7. Which answers would change my assessment

- **"Convention-only, no tooling"** → the enforcement paragraph becomes a *documented risk*
  (CodeKB TD-5) rather than an action, and `discovered-rules.md` becomes the only durable
  carrier; I would want at least no-bare-`except` and secret-redaction promoted to
  ALWAYS/NEVER.
- **"Adopt ruff + format"** → the enforcement bullet flips to *observed: enforced*, and the
  measured baseline (16 findings, 12 files to reformat, 6 of them FastAPI idiom) becomes the
  change list for one style commit; the B008 and line-length settings must land in that same
  commit.
- **"Ruff goes into `[dev]`"** → §4's two contradictory documents must be edited in that
  change, else NFR3's comment and the README become false.
- **"Yes to a type checker"** → annotations move from convention to enforced; the two
  `# type: ignore` comments in `tests/conftest.py` become meaningful.
- **"Single-source the record contract"** → `RECORD_FIELDS` becomes load-bearing; otherwise
  it should be deleted as documentation-only.
- **TD-1 resolved either way (keep or remove the in-app auth flow)** → ~24 of 52 tests and
  two modules enter or leave the codebase; any Code Style affirmation phrased around
  `session_auth.py`/`routes.py` examples must be re-checked, and question 8's stale comment
  resolves itself.

## Positions

- **AGREE:** the `## Code Style` "Area strength: observed" rating for the listed
  conventions — I reverified claims 2, 4, 5, 8, 9, 11, 12 directly against the modules.
- **AGREE:** the enforcement gap is real and needs a human answer; I measured it rather than
  asserting it (16 ruff findings / 12 files reformattable / no config anywhere).
- **AGREE:** the Testing Posture bullets on test count, tooling, doubles policy, boundary
  discipline and unmeasured coverage — all reverified (52 functions in 9 modules,
  `filterwarnings = ["error"]` the only gate, no coverage config).
- **AGREE:** "no CI, no deployment, localhost-only run story" — verified by the root listing
  and `README.md`; also AGREE that adding a pipeline collides with the recorded
  no-cloud/no-Docker requirement and that adding a linter does not.
- **OBJECT:** "One error envelope … covers every non-2xx response" — framework-generated
  404/405 return `{"detail": …}`; I reproduced it (see §2.1).
- **OBJECT:** "Module constants … documented with `#:` comments", including the
  "TTL constants in `app/session_auth.py`" example — 20 of 39 constants are undocumented and
  `EXCHANGE_TIMEOUT_SECONDS` is one of them (§2.2).
- **OBJECT:** "request and record shapes are plain dataclasses sharing one field list" — the
  list is hand-duplicated in 4+ places and `app/models.py:20 RECORD_FIELDS` is referenced
  nowhere (§2.3).
- **OBJECT:** "Domain exceptions … mapped to status codes only in `app/routes.py`" —
  `ConfigError` is never mapped to a status (startup failure) and `AuthExchangeError`
  becomes a 302 redirect, not an envelope response (§2.5).
- **OBJECT:** "every module" citing requirement ids and a single responsibility — two real
  exceptions (`app/__init__.py`, `app/session_auth.py`), which turns draft open question 4
  from a future risk into present drift (§2.4).
- **OBJECT:** the "twelve application modules" / "10 files" counts — 12 includes the 10-line
  re-export shim and 10 includes `conftest.py`; align with the CodeKB's "11 substantive
  modules, 9 test modules" so later stages cite stable numbers (§2.6).
- **OBJECT (gap, not error):** the Code Style section says nothing about module
  organisation, the hexagonal seam, or the connection-ownership boundary — for this codebase
  those are the most consequential conventions to affirm, and §5 proposes the decisions.
