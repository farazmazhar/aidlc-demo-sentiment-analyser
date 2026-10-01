# Code Quality Assessment — `very-cool-sentiment-analysis`

> Derived from the developer scan
> (`inception/reverse-engineering/developer-scan.md`), which performed a
> **read-only** scan: no build, linter or test suite was executed. Statements
> about test health are therefore about what exists, not about today's pass/fail
> state. The only run evidence available is
> `.pytest_cache/v/cache/lastfailed`, which held `{}` at scan time.

## Scorecard

| Dimension | Rating | Summary |
|---|---|---|
| Test suite breadth | good | 52 test functions across 9 modules, one per production module with tests, plus a shared harness |
| Test coverage of risk | weak | The 250-line live client has **zero** coverage; coverage is not measured at all |
| Linting / formatting / typing gates | absent | No linter, formatter or type checker is configured or run |
| CI/CD | absent | Nothing automates install, lint or test on a change |
| Documentation | strong | 189-line README, requirement-id-bearing module docstrings, commented constants, an `AGENTS.md` |
| Internal consistency | strong | One error envelope, one record contract, parameterised SQL only, secrets always redacted |
| Maintainability | fair | Clean layering and no cycles, but four hand-written copies of the record contract and one 263-line module that the intent does not ask for |

## Test Suite

**Layout.** `tests/` is the only test root (`testpaths = ["tests"]`), with 10
files and 1 407 lines:

| File | Test functions | Focus |
|---|---|---|
| `tests/test_config.py` | 7 | Mode/key resolution, unsupported mode, live-without-key, the gitignore assertion |
| `tests/test_db.py` | 2 | First-run schema creation, idempotence |
| `tests/test_repository.py` | 2 | Insert-then-read-back with all fields; newest-first limit |
| `tests/test_dummy_client.py` | 6 | Label decisions, fixed probabilities, intensity/model/provider, no network |
| `tests/test_service.py` | 3 | Persist-and-return, empty/whitespace rejection, client substitutability |
| `tests/test_routes.py` | 6 | `POST /analyze` stored record, invalid text without persisting, `/analyses` ordering and limit, `/health` mode |
| `tests/test_page.py` | 2 | Served markup and page assets |
| `tests/test_session_auth.py` | 12 | PKCE challenge, exchange with the announced verifier, expiry, disconnect, redaction, TTL |
| `tests/test_auth_routes.py` | 12 | Start/callback/disconnect routes, indicator payload, credential-drop on rejection |
| `tests/conftest.py` | — | Harness: `asgi_request()`, `AsgiResponse`, fixtures |

**Harness characteristics** (all of which a v1 change must keep intact):

- A hand-rolled **in-process ASGI caller** builds a raw ASGI scope, enters the
  app's `lifespan_context` and collects response messages, because `TestClient`
  would need `httpx`, which the dependency cap forbids
  (`tests/conftest.py:5-9`).
- A session-scoped autouse **`offline_guard`** monkeypatches
  `socket.socket.connect` to raise, so any accidental network use fails the run
  loudly (`tests/conftest.py:129-146`).
- `tmp_settings` / `tmp_db_path` point every test at a `tmp_path` database, so no
  test reads the real `config.local.toml` or `data/sentiment.db`
  (`tests/conftest.py:149-168`).
- Assertions read values back out of **real SQLite** and the **served markup**,
  not out of mocks (`tests/test_repository.py`, `tests/test_routes.py`,
  `tests/test_page.py`).
- `filterwarnings = ["error"]` turns any warning into a failure — the only
  mechanical gate in the project.
- `tests/test_config.py::test_local_config_is_gitignored` shells out to
  `git check-ignore` and is documented to skip silently when `git` is absent
  (`tests/test_config.py:128-129`).

**What is not covered (the honest gap).**

| Area | Status | Evidence |
|---|---|---|
| `app/openrouter_client.py` (250 lines) | never imported, constructed or called by any test — the offline guard makes that structural | `app/openrouter_client.py:10-12` states it; `tests/conftest.py:129-146` enforces it |
| The live insertion path | exercised only with `SentimentResult` fakes injected by tests | `tests/test_service.py`, `tests/test_routes.py` |
| Browser execution of `app/static/app.js` | never executed; `test_page.py` asserts served markup and `data-testid` hooks only (page/assets contract level) | `tests/test_page.py`, `README.md` "Notes" |
| The PKCE exchange itself | covered through an injected exchanger double, never over the network | `app/session_auth.py:148-160`, `tests/test_session_auth.py` |

**Coverage measurement: absent.** No `pytest-cov`, no `[tool.coverage]`, no
`--cov` in `addopts`, no floor, no badge. The active `classic` scope expects an
80 % line-coverage floor for Construction and there is currently no measurement
that could verify it — or detect a regression in the untested live client.

## Linting, Formatting and Static Analysis

**Absent.** Verified by inspection of the repository root and `pyproject.toml`:
no `ruff`, `flake8`, `pylint`, `mypy`, `black`, `isort` or `pre-commit`
configuration; no `.ruff.toml`, `ruff.toml`, `setup.cfg`, `tox.ini` or
`.pre-commit-config.yaml`. Import order, annotation style and docstring content
rest entirely on convention and review.

The code is nevertheless internally consistent (see below), which means adopting
a linter would mostly formalise existing habits rather than force a rewrite.

## CI/CD

**Absent.** No `.github/` directory or workflow file, no `.gitlab-ci.yml`, no
Jenkinsfile, no pipeline or deployment configuration. Nothing automates
install, lint, test or packaging on a change; `filterwarnings = ["error"]` plus a
human running `pytest` is the entire quality gate.

## Documentation Quality

**Strong**, and the strongest signal in the repository:

- `README.md` (189 lines) covers prerequisites, setup, run, test, the in-app
  authorization flow, both modes, all six config-resolution rules, storage, the
  full HTTP surface table, the file layout, and an explicit "Notes" section on
  what is *not* tested.
- `AGENTS.md` (59 lines) documents the AI-DLC harness layout and conventions for
  this repository.
- Every `app/` module carries a docstring naming its single responsibility and
  the requirement ids it satisfies (`FR1.1`–`FR5.5`), and every non-obvious
  function or constant is commented — e.g. the lazy import rationale in
  `app/service.py:78-79` and the `now` seam in `app/repository.py:46-49`.
- `config.example.toml` documents each setting inline, including the
  "never commit a real value" warning.

**Two documentation defects:**

1. `very_cool_sentiment_analysis.egg-info/PKG-INFO` embeds an **older** README
   (its config rules still show rule 5 as "fails at startup", its HTTP table
   lists 6 routes, its file layout omits `session_auth.py` and the two auth test
   modules). Documentation rendered from the installed metadata will be wrong.
2. `app/main.py:33-34` still states that no authentication or session code
   exists anywhere in the app, which the four `/auth/*` routes and
   `app/session_auth.py` contradict.

## Consistency Positives

- One error envelope for every failure, with four codes asserted by tests
  (`app/routes.py:41-57`, `app/main.py:93-96`).
- One record contract (`RECORD_FIELDS`) used by storage and the wire
  (`app/models.py:20-30`).
- Parameterised SQL only; no string interpolation in `app/db.py` or
  `app/repository.py`.
- Secrets redacted in `Settings.__repr__`, `SessionCredential.__repr__` and
  `OpenRouterClient.__repr__`, with tests asserting the key never appears in a
  rendered setting, a log record or any endpoint body
  (`tests/test_config.py::test_api_key_is_never_logged`,
  `tests/test_auth_routes.py::test_no_endpoint_ever_exposes_the_key`,
  `tests/test_session_auth.py::test_the_credential_never_renders_its_key`).
- Deterministic seams everywhere a clock, an exchange or a timestamp is
  involved.

## Technical Debt Register

Ordered as the developer scan reported them; severity is this synthesis's
assessment of the effect on the next stages.

| # | Signal | Severity | Evidence | Why it matters |
|---|---|---|---|---|
| TD-1 | In-app OAuth flow contradicts the v1 intent's "no auth" + manual config key | **high** | `app/session_auth.py`, `app/routes.py:125-167`, 24 of 52 tests, page indicator, `config.example.toml` | The largest single divergence between code and intent; every later stage must decide keep-or-remove |
| TD-2 | Config rule 5 supersedes the fail-fast behaviour the intent still asks for | **high** | `app/config.py:111-123`, `tests/test_config.py:70-85`, `README.md` | A silent semantic difference: live mode without a key now runs the offline engine |
| TD-3 | Per-request SQLite connection with default thread affinity | **medium** | `app/routes.py:70-76`, `app/db.py:51-63` | Overlapping requests can raise `sqlite3.ProgrammingError`; recorded as an accepted limitation in `aidlc/spaces/default/memory/project.md`, still unresolved in code |
| TD-4 | No coverage measurement, and a 250-line module no test touches | **medium** | `pyproject.toml` (no coverage config), `app/openrouter_client.py` | A regression in the live path would be invisible to CI-less development |
| TD-5 | No linting, formatting or CI to enforce the conventions the code already follows | **medium** | repository root, `pyproject.toml` | The sole mechanical gate is `filterwarnings = ["error"]`; `test_config.py` even shells out to `git` |
| TD-6 | Stale generated metadata | **low-medium** | `very_cool_sentiment_analysis.egg-info/PKG-INFO`, `SOURCES.txt` | Misleads readers of installed metadata; `SOURCES.txt` omits `session_auth.py` and the auth tests |
| TD-7 | Four hand-written copies of the same field list | **low-medium** | `app/models.py:20-30,64-93`, `app/db.py:18-48` | Drift is prevented only by tests |
| TD-8 | Import-time application construction | **low** | `app/__init__.py:8`, `app/main.py:101` | Importing any submodule builds a FastAPI app and a `SessionAuth` as a side effect |
| TD-9 | Stale comment contradicting the code | **low** | `app/main.py:33-34` | Misleads a reader about whether auth exists |
| TD-10 | Naming drift on both clients | **low** | `app/dummy_client.py:75`, `app/openrouter_client.py:76` | Cosmetic; matters only if requirement text names classes |
| TD-11 | `data/sentiment.db` holds live local state at schema version 1 with no migration mechanism | **low** | `app/db.py:14,66-83`, `data/sentiment.db` (12 rows) | Any future schema change is a hand-written delta; `SCHEMA_VERSION` is written but never compared |
| TD-12 | Dummy engine output is fixed by design and incomparable with live rows | **low** | `app/dummy_client.py:56-66`, `app/dummy_client.py:95-106` | Stored dummy rows carry no signal; `model`/`provider` are the only way to tell modes apart |

## Component Risk Ratings

| Component | Risk | Reason |
|---|---|---|
| HTTP API Surface | high | Widest fan-out; holds page, API, auth routes and error mapping in one 221-line file |
| Live OpenRouter Engine | high | Zero automated coverage and the only component that can fabricate a wrong answer if its typed-reading rules are relaxed |
| Session Authorization | medium-high | Largest module, live secrets in memory, and outside the stated v1 scope |
| Persistence and Schema | medium | Connection lifecycle risk accepted but unresolved; no migration path |
| Analysis Orchestration | medium | Owns credential precedence; errors here change which engine actually runs |
| Web UI | low-medium | Verified only at the served-markup level; no browser execution |
| Offline Dummy Engine, Record and Request Contracts, Configuration and Settings, Sentiment Engine Interface, Application Assembly | low | Small, well-covered, no cycles |

## Recommended Gates for the Next Stages

Only what the evidence supports; nothing here is a requirement invented for this
assessment.

1. If the live client stays, add a scoped test for its **typed-answer reading**
   (the pure helpers `_read_choice` / `_read_score`) so the "never guess" rule has
   a regression guard; the network call itself can remain double-injected.
2. Add a coverage measurement and a floor if the `classic` scope's 80 % line
   expectation is to be verified at Build and Test.
3. Adopt a linter/formatter (the org rule already defers to project config) and a
   minimal CI job running install + lint + `pytest`.
4. Decide TD-1 and TD-2 explicitly before any code change, since both change the
   observable contract.
5. If the connection lifecycle is touched, decide `check_same_thread` and the
   connection lifecycle explicitly rather than inheriting `sqlite3.connect()`
   defaults.
6. Regenerate or delete `very_cool_sentiment_analysis.egg-info/` so it stops
   contradicting the repository.
