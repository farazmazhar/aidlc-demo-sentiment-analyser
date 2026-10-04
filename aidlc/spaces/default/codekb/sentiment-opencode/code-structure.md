# Code Structure — `very-cool-sentiment-analysis` (repo `sentiment-opencode`)

## Repository Layout

Flat at the root: one importable package, one test package, no `src/` layout, no
namespace package, no sub-packages, no vendored third-party code inside `app/`.

```
.
├── app/                          the application package (14 modules + static assets)
│   ├── __init__.py               10    ASGI re-export, so `uvicorn app:app` resolves
│   ├── main.py                  163    application factory, lifespan, wiring
│   ├── routes.py                502    the entire HTTP surface (/ , /v1 , /v2 , /auth/*)
│   ├── models.py                246    request/response, record + the four analytics shapes
│   ├── repository.py            102    row DML — the only module that inserts/selects rows
│   ├── analytics.py             374    the aggregate read layer behind both /v2 endpoints
│   ├── db.py                    339    connection, DDL, in-place migration (v4) + indexes
│   ├── service.py               214    orchestration + engine resolution
│   ├── sentiment.py              84    the engine interface and its typed result
│   ├── terms.py                 201    the promoted tokeniser + stopword filter (leaf)
│   ├── config.py                151    settings, mode resolution, redaction
│   ├── session_auth.py          259    in-app PKCE, credential in process memory
│   ├── dummy_client.py          103    offline keyword engine (consumes app.terms)
│   ├── openrouter_client.py     232    live Jev client + transport protocol
│   └── static/
│       ├── index.html           351    the page: markup + inline CSS
│       └── app.js               322    page behaviour, fetch sites to /v1, /v2, /auth/*
├── tests/                        the test package (conftest + 15 test modules, 5 259 lines)
├── pyproject.toml                        the only manifest: build, deps, pytest, coverage, ruff
├── config.example.toml                   committed config template (must never hold a secret)
├── README.md                             365 lines — the API contract of record
├── opencode.json                         AI-DLC harness config, NOT a build manifest
├── data/sentiment.db                     gitignored local runtime state (now schema v4)
└── .venv/                                installed environment
```

## Packages Found

| Package | Type | Language | Purpose | Declared at |
|---|---|---|---|---|
| `very-cool-sentiment-analysis` | application distribution | Python 3.11+ | The project. A localhost-only sentiment analysis web app. | `pyproject.toml` `[project]`; ships `packages = ["app"]` |
| `app` | importable package | Python | All 14 modules plus `static/` (`package-data = ["static/*"]`) | `pyproject.toml` `[tool.setuptools]` |
| `tests` | test package | Python | In-process ASGI acceptance + unit suite; `tests/conftest.py` is imported as `tests.conftest` by every route test | not packaged |

There is exactly **one** distributable package and **one** test package. The
package has no internal packaging-level dependency on any other local module;
internal coupling is by import only.

## File Classification

| Class | Files | Purpose |
|---|---|---|
| **Composition root** | `app/__init__.py`, `app/main.py` | Builds the application and owns startup. `__init__.py` exists solely so `uvicorn app:app` resolves without naming `app.main`. |
| **HTTP edge** | `app/routes.py` (502) | Translates HTTP into service or read calls and failures into one envelope. Holds the `/`, `/v1`, `/v2` and `/auth/*` surfaces. No sentiment logic, no SQL. |
| **Application core** | `app/service.py`, `app/sentiment.py` | Orchestration and the engine abstraction. Neither imports `fastapi`. |
| **Contracts** | `app/models.py` | The wire and storage shape of one analysis, plus the four computed analytics shapes (`AnalyticsSummary`, `AnalyticsSeriesEntry`, `AnalyticsTerms`, `TermFrequencyEntry`), so the shapes cannot drift. |
| **Outbound adapters** | `app/dummy_client.py`, `app/openrouter_client.py`, `app/session_auth.py` | Everything that talks to something outside the process. `session_auth` carries its own outbound call rather than sharing the live client's transport. |
| **Persistence** | `app/repository.py`, `app/db.py` | Split deliberately: `db.py` owns the **DDL, the connection, the migration and the indexes**; `repository.py` owns **row DML and row↔record mapping**. |
| **Analytics read** | `app/analytics.py` (374) | The aggregate read layer behind both `/v2` endpoints: range resolution, the grouped summary, the zero-filled series and term ranking. Takes the request's connection, opens none, writes nothing, calls no engine. |
| **Term extraction** | `app/terms.py` (201) | The single promoted tokeniser (`tokenize`, `TOKEN_PATTERN`) plus the significance filter (`significant_terms`, `STOPWORDS`, `MIN_TERM_LENGTH`). A leaf that imports nothing from `app`. |
| **Configuration** | `app/config.py` | Mode resolution, the key, and redaction. A leaf with high fan-in. |
| **Frontend** | `app/static/index.html`, `app/static/app.js` | One page. No framework, no bundler, no npm, no `package.json`. |
| **Tests** | `tests/conftest.py`, `tests/test_*.py` (15) | See **code-quality-assessment.md** for the harness and measured coverage. |
| **Manifest / docs / config template** | `pyproject.toml`, `README.md`, `config.example.toml`, `.gitignore` | Build + tool config; the contract of record; the committed template. |
| **Not application code** | `.aidlc/`, `.opencode/`, `aidlc/`, `.commandcode/`, `.git/`, `.venv/`, caches | AI-DLC harness engine and workflow record; harness adapter; VCS; installed environment; build artefacts. |

## Module Size Profile

No file exceeds 500 lines. Sizes are stable and consistent with a small system
that has grown by one capability at a time.

| Size band | Files |
|---|---|
| > 300 lines | `app/routes.py` (502) — the HTTP surface, by accumulation of endpoints; `app/analytics.py` (374) — the aggregate read layer |
| 200–299 | `app/db.py` (339), `app/static/index.html` (351), `app/static/app.js` (322), `app/session_auth.py` (259), `app/models.py` (246), `app/openrouter_client.py` (232), `app/service.py` (214), `app/terms.py` (201) |
| 100–199 | `app/main.py` (163), `app/config.py` (151), `app/dummy_client.py` (103), `app/repository.py` (102) |
| < 100 | `app/sentiment.py` (84), `app/__init__.py` (10) |

Function sizes are small: the longest are `import_texts` (41 lines,
`app/service.py:129`) and `SessionAuth.complete` (41 lines), both linear
sequences rather than deep control flow. No class exceeds 100 lines.

## Internal Organization: By Layer, Not by Feature

`app/` is a **flat by-layer package**. The ordering below is the descending
chain; the per-edge adjacency table is in **dependencies.md**.

```
  app/__init__.py                    re-export
        │
  app/main.py                        composition root
        │
  app/routes.py                      HTTP edge
        │
        ├──► app/service.py ────────► app/session_auth.py
        │         │                            │
        │         ├──► app/dummy_client.py ──► app/terms.py   (leaf)
        │         ├──► app/openrouter_client.py (function-local)
        │         ├──► app/sentiment.py                        (leaf)
        │         ├──► app/repository.py ──► app/models.py
        │         ├──► app/config.py                           (leaf)
        │         └──► app/models.py                           (leaf)
        │
        ├──► app/repository.py        (row reads, straight from the route)
        └──► app/analytics.py ──► app/models.py, app/sentiment.py, app/terms.py

  app/db.py ──► app/models.py   (imports UNKNOWN_PROVIDER only)
```

At this size a flat by-layer package is idiomatic FastAPI, and the layering is
genuinely respected rather than merely documented (no SQL in `routes.py`, no HTTP
in `service.py`, no runtime engine dependency in `repository.py`). The point at
which `app/` should split by feature is not decided anywhere in the codebase —
it is an open question, not an implicit choice. See **architecture.md** §
Improvement Opportunities.

## Code Patterns in Use

### 1. Module docstring as a boundary declaration

All 14 modules open with a docstring, and each carries an explicit
**`Single responsibility:`** line naming what the module does *not* do — the two
new modules (`analytics.py`, `terms.py`) included:

- `app/routes.py:3-6` — "No sentiment logic and no SQL live here"
- `app/repository.py:4-6` — "Depends on nothing from the sentiment engine at runtime"
- `app/service.py:4-7` — "It depends on the interface and on the repository, never on the API layer, and the dispatcher never constructs a concrete client it was not handed"
- `app/db.py:3-6` — "own the shape and lifecycle of the local database file"

This is the codebase's own boundary enforcement mechanism, and it is stronger
than most projects manage, because the negative claim ("no X here") is stated
next to the positive one.

### 2. Embedded traceability identifiers

The source carries requirement, business-rule, acceptance-criterion, risk and
decision IDs in docstrings and inline comments: `FR4.1`, `NFR3.1`, `BR4.3`,
`AC7.1.2`, `R-01`, `R-04`, `D1`–`D4`, `W1`. The same IDs appear in the README.
The consequence is that the code is self-describing against its own requirement
set — a reader can find the justification for any rule without a separate
document. (The IDs are dense enough to be noise to someone without the prior
artifacts; a reader outside that lineage will find them heavier than helpful.)

### 3. Protocol-as-interface, chosen in one function

`SentimentClient` (`app/sentiment.py:78`) is a `@runtime_checkable` `Protocol`
with a single `analyze` method. Two implementations satisfy it structurally, and
neither is registered anywhere. `get_client` (`app/service.py:76`) is the sole
construction site. `HttpTransport` (`app/openrouter_client.py:69`) is a second,
narrower protocol used the same way.

### 4. Function-local import to keep a module unloaded

```python
def _live_client(api_key: str, model: str) -> SentimentClient:
    from app.openrouter_client import OpenRouterJevSentimentClient   # app/service.py:103
    return OpenRouterJevSentimentClient(api_key=api_key, model=model)
```

The offline path never imports — let alone executes — the module that performs
real HTTP. This is also why the live client's lines are uncovered: nothing in the
offline suite imports it. The static-import graph in **dependencies.md** records
`service → openrouter_client` as a *dynamic* edge, not a static one.

### 5. Injectable seams instead of mocks

Every external influence is a parameter: `settings` and `session_auth` into
`create_app`; `now: datetime | None` into `insert_analysis` and `analyze_text`;
`client: SentimentClient` into `analyze_text` and `import_texts`; `connection`
into every repository function; `transport` into the live client; `exchanger`
into the session store. The test suite adds **zero** mock objects — its doubles
are hand-written classes at those same seams.

### 6. Sync generators for per-request resources

`get_connection` (`app/routes.py:92`) is a plain `def` generator dependency, so
FastAPI runs it in an anyio worker thread and closes the connection in a
`finally`. This is also where the accepted cross-thread defect lives (TD-5 in
**code-quality-assessment.md**). All handlers are synchronous `def` for the same
reason: the storage driver is synchronous.

### 7. Constants with a `#:` doc comment

Semantic constants carry `#:` prose that states *why* — `SCHEMA_VERSION`,
`ANALYSES_COLUMNS`, `LABELS`, `V1_PREFIX`, `PENDING_TTL_SECONDS`, the error
codes, `EXPORT_COLUMNS`. This is a deliberate convention, applied consistently
to the constants that encode a contract.

### 8. Single error-envelope builder

Every application-raised failure is rendered by `error_response(status_code,
code, message)` (`app/routes.py:69`). There is exactly one place the envelope
shape is written, so it cannot drift. Five exception handlers are registered at
`app/main.py:94-98`.

### 9. Redaction by `__repr__`

`Settings`, `SessionCredential` and `OpenRouterClient` each define a `__repr__`
that renders the key as `<redacted>`. Note the honest limit: **redacted means
"not rendered", not "not obtainable"** — the key is a public dataclass field, so
`dataclasses.asdict` or a locals dump would still expose it.

### 10. No junk-drawer module

There is no `utils.py` or `helpers.py`. A pure helper lives in the module that
owns its concept (`format_timestamp` in `repository.py`,
`create_code_verifier` / `code_challenge_for` in `session_auth.py`,
`validate_result` in `sentiment.py`). The one genuinely shared concern — the
tokeniser — now has its own named home rather than hiding as a private of an
unrelated module: `app/terms.py` (A4), consumed by both `app/dummy_client` and
`app.analytics`.

## Conventions Observed

| Convention | State | Notes |
|---|---|---|
| `from __future__ import annotations` | 13 of 14 modules — all but the 10-line `app/__init__.py` | |
| Type annotations | Every public function fully annotated | 100% applied; **no type checker** enforces it, and there is no `py.typed` marker |
| Constant naming | `UPPER_CASE`; privates `_`-prefixed; class attributes lower-case (`model`, `provider` on the clients) | |
| Naming | `snake_case` modules/functions/variables, `PascalCase` classes and type aliases, `snake_case` test functions | |
| Import layout | stdlib / third-party / `app.*`, blank line between groups | Ordering within a group is `ruff`-clean today (`I` is in the selected rule set) |
| Formatting | 4-space indent, double quotes, LF line endings, `line-length = 100` | Enforced by `ruff format --check` |
| Docstrings | English, freeform prose, sentence case. No Google/NumPy section format anywhere in `app/` or `tests/` | `tests/conftest.py` is the one exception: it uses Sphinx `:func:` cross-reference roles |
| Errors | No bare `except:` and no `except Exception:`; every handler names a specific type or a deliberate two-type tuple, and every wrapping `raise` uses `from exc`. One deliberate `except BaseException` rollback-and-re-raise lives in the migration (`app/db.py`) | |
| Output | `print()` never appears in `app/`. Logging via module loggers (`app.routes`, `app.main`, `app.config`); the key is never logged | |
| SQL | Parameter-bound throughout (`?` placeholders); only DDL and static filters are literal. No string interpolation | |
| Pydantic | **Not imported by application code** — deliberate, see A1 in **architecture.md** | |
| Comment markers | **Zero** `TODO`/`FIXME`/`HACK`/`XXX` in `app/` or `tests/` | |
| Suppressions | Narrow and justified: `# pragma: no cover` on unreachable-by-construction branches, `# noqa: S310` on the two `urllib` bodies with a "hardcoded https constant" comment, `# noqa: S105` on the `app/terms.py` token-pattern constant, and two `# type: ignore[method-assign]` in the offline guard | No blanket suppressions |

## Frontend Structure

| Aspect | Reality |
|---|---|
| Files | One HTML file with inline `<style>` (`app/static/index.html`, 351 lines), plus one vanilla ES-module-free script (`app/static/app.js`, 322 lines) |
| Framework / bundler / npm | **None.** No `package.json`, no lockfile, no build step |
| API base | Two client-side prefix constants: `const API = "/v1";` (`app/static/app.js:14`) and `const API_V2 = "/v2";` (`:15`) — an independent second copy of each prefix that nothing asserts matches the backend |
| Outbound calls | Five `fetch` sites: history load (`:106`), analyze submit (`:116`), **analytics summary** (`:242`), health poll (`:277`), auth disconnect (`:305`). No terms fetch, no range parameters, no `AbortController` |
| Automation hooks | `data-testid` attributes pinned by `REQUIRED_TEST_IDS` in `tests/test_page.py`; every interactive element carries a stable hook |
| Accessibility affordances | `role="alert"` on the error panel, `role="status"` + `aria-live="polite"` on the connection indicator and result panel |
| Navigation | A three-link nav now exists (`nav-summary` `app/static/index.html:192`, `nav-terms` `:193`) and an analytics summary region (`analytics-summary`, `:270`). The terms section (`:328`) is a **static placeholder** with no term-list containers, and no date-range control exists anywhere. `tests/test_page.py` asserts this markup must not contain the word `intensity` |
| Rendering safety | All rendering goes through `textContent`; there is no HTML injection sink. This is the reason the absence of a CSP is recorded as a low accepted risk |
| Asset serving | `StaticFiles` mounted at `/static` (`app/main.py:92`); `GET /` re-reads `index.html` from disk on **every** request, so a markup edit is live without a restart |

The test ids are pinned by `REQUIRED_TEST_IDS` in `tests/test_page.py`, which
already names `nav-summary`, `nav-terms`, `analytics-summary`, `analytics-empty`
and `analytics-error` but pins **no terms hook names** — the view work must
extend that list. Any new view needs its own required-id list and must reuse the
`asgi_request` harness, because `fastapi.testclient` is unavailable under the
two-package runtime cap (no `httpx`).

## Build and Configuration Files

| File | Role |
|---|---|
| `pyproject.toml` | The **only** manifest. Declares the build backend, the two runtime dependencies, the three dev extras, `packages = ["app"]`, `package-data`, and four tool config blocks (`pytest`, `coverage` ×2, `ruff` ×4). |
| `config.example.toml` | The committed configuration template. Must never hold a real secret — the header says so explicitly. |
| `config.local.toml` | The gitignored runtime config, and the only permitted on-disk location for a key. Its absence is the offline default. |
| `README.md` | 365 lines and genuinely maintained: setup, run, test/lint commands, connection flow, the two modes, configuration, storage and migration contract, the **HTTP surface table**, the file-layout tree, known limitations, and an end-to-end verification command. |
| `.gitignore` | Excludes `config.local.toml`, `/data/`, `.venv/`, `.coverage`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`. |

**No** Makefile, Dockerfile, `noxfile.py`, `tox.ini`, CI workflow, pre-commit
config or ADR directory exists.

## What Is Deliberately Absent

Each absence is a decision with a reason, not an oversight:

- **No `src/` layout** — one package, one import root.
- **No response models / OpenAPI contract** — the reason is A1's cost, recorded
  as TD-8 in **code-quality-assessment.md**.
- **No pydantic in application code** — keeps the runtime cap at two packages.
- **No frontend framework or bundler** — the same cap, plus the fact that the
  page is one document.
- **No type checker** — annotations are present and unenforced.
- **No `utils.py`** — helpers live with the concept they serve.
- **No ADR directory or `docs/`** — the README's HTTP surface table *is* the
  contract of record.
- **No CI, no pre-commit hook, no lockfile, no secret scanner, no dependency
  audit** — the gates run only when a developer runs them. Adding the last three
  is the active intent's second half.

External dependency versions are in **technology-stack.md**; the module import
graph is in **dependencies.md**; per-component responsibility is in
**component-inventory.md**; endpoints and payloads are in
**api-documentation.md**; measured coverage, lint status, CI status and the debt
register are in **code-quality-assessment.md**.