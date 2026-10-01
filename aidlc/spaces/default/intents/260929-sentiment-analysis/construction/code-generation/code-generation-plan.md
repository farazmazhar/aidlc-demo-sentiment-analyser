# Code Generation Plan — very-cool-sentiment-analysis

- **Intent**: `260929-sentiment-analysis`
- **Stage**: code-generation (`3.5`, Construction)
- **Record**: `aidlc/spaces/default/intents/260929-sentiment-analysis/construction/code-generation/`
- **Scope**: `poc` (depth Minimal, review cap advisory, guard policy relaxed)
- **Project type**: Greenfield
- **Test strategy**: Minimal
- **Iteration**: one implementation iteration (zero-Unit directive — no Unit DAG, no Bolt/worktree ceremony)
- **Plan date**: 2026-09-29

---

## 1. Inputs and Traceability Target

| Input | Path | Status |
|---|---|---|
| Requirements (source of record) | `inception/requirements-analysis/requirements.md` | present — FR1–FR5 (29 sub-IDs), NFR1–NFR6, A1–A2, constraints, out-of-scope — 37 IDs in total, every one mapped in §6 |
| Confirmed answers | `inception/requirements-analysis/requirements-analysis-questions.md` | present — `[Q1]`–`[Q5]` all answered |
| Approved intent | `ideation/intent-capture/intent-statement.md` | present — success metrics |
| Unit of work | `inception/units-generation/` | **absent by design** — `units-generation` is SKIP in `poc` |
| Functional design / NFR requirements / NFR design / infrastructure design | `construction/<unit>/…` | **absent by design** — stages `3.1`–`3.4` are SKIP in `poc` |
| Domain design / contract design | `inception/domain-design/`, `inception/contract-design/` | **absent by design** — SKIP in `poc` |
| User stories | `inception/user-stories/` | **absent by design** — `user-stories` is SKIP in `poc` |

**Story-to-code-step traceability.** This intent has no Unit DAG and no user stories, so there is no `US{n}.{m}` identifier to map against. Per the stage's zero-Unit rule the work is scoped from Requirements Analysis and the workspace, and the traceability key is therefore the requirement ID: every plan step below names the `FR`/`NFR`/`A` IDs it implements, and §6 maps every requirement ID in `requirements.md` to its implementing file and its verifying test or smoke step. No requirement is left unmapped and no mapping cites an ID that does not exist in `requirements.md`.

**Missing-artifact policy.** Nothing above is invented: the absent artifacts are absent because `poc` skips their stages, and their content is not required to build this app (one process, one page, two JSON routes, one SQLite file).

---

## 2. Architecture and File Layout (decided, not open)

One Python process serving one HTML page, three JSON routes, and one SQLite file on localhost. No auth, no cloud, no Docker. The sentiment engine is reachable only through one interface with two implementations.

```
very-cool-sentiment-analysis/            # repo root — application code lives here, never under aidlc/
├── pyproject.toml                       # deps + pytest configuration + build metadata
├── config.example.toml                  # committed; placeholder only, no secret
├── config.local.toml                    # gitignored; developer-supplied key + mode
├── .gitignore                           # config.local.toml, data/, caches, .venv
├── README.md                            # setup, dev/test commands, config, modes
├── app/                                 # application package; ASGI entry `app:app`
│   ├── __init__.py                      # public re-export: `from app.main import app`
│   ├── main.py                          # create_app() factory, lifespan, logging, HOST bind, static mount
│   ├── config.py                        # Settings + load_settings(); mode/key resolution
│   ├── models.py                        # request/response schemas + JSON record shape
│   ├── db.py                            # sqlite3 connection + schema init/migration
│   ├── repository.py                    # insert_analysis(), list_analyses(); AnalysisRecord
│   ├── sentiment.py                     # SentimentClient protocol + SentimentResult + label constants
│   ├── dummy_client.py                  # keyword-based offline client (default)
│   ├── openrouter_client.py             # Jev/OpenRouter live client (never exercised by tests)
│   ├── service.py                       # analysis orchestration: validate → client → persist
│   ├── routes.py                        # POST /analyze, GET /analyses, GET /health, GET /
│   └── static/
│       ├── index.html                   # submit form, result panel, history list
│       └── app.js                       # fetch() calls to /analyze and /analyses
├── tests/
│   ├── conftest.py                      # in-process ASGI harness, tmp DB fixture, offline guard
│   ├── test_config.py
│   ├── test_dummy_client.py
│   ├── test_db.py
│   ├── test_repository.py
│   ├── test_service.py
│   ├── test_routes.py
│   └── test_page.py
└── data/                                # gitignored; created on first run
    └── sentiment.db                     # the single SQLite file
```

**Dependencies (exactly three beyond the standard library).** `fastapi`, `uvicorn` (runtime) and `pytest` (dev). The live client and the config reader use only the standard library — `urllib.request` for the HTTP call, `tomllib` for the TOML config, `sqlite3` for storage — so no HTTP client or TOML parser is added. `fastapi.testclient.TestClient` is **not** used: it would pull in `httpx` and break the dependency cap, so route tests drive the ASGI app through a small stdlib harness in `tests/conftest.py`.

**Commands.** Dev: `uvicorn app:app --reload`. Tests: `pytest` (or the scoped form recorded in `unit-test-instructions.md`).

---

## 3. Interface and Contract Decisions

These are the concrete shapes the build pass implements; every one is derived from `requirements.md` and no requirement is widened.

### 3.1 Configuration (`app/config.py`)

```python
@dataclass(frozen=True)
class Settings:
    mode: Literal["dummy", "openrouter"]
    api_key: str | None
    model: str            # "typesafe/jev-1.13"
    db_path: Path         # data/sentiment.db
    config_path: Path     # config.local.toml

def load_settings(config_path: Path = Path("config.local.toml"),
                  db_path: Path = Path("data/sentiment.db")) -> Settings: ...
```

Resolution rules, in order:

1. Config file **absent** → `mode="dummy"`, `api_key=None`. (FR1.2, NFR1)
2. Config file present and it **states no `mode`** → `mode="dummy"`. (FR1.2)
3. Config file present with `mode="dummy"` → dummy; any key in the file is ignored by the dummy path. (FR1.1, FR1.2)
4. Config file present with `mode="openrouter"` and a non-empty key → live client. (FR1.1, FR2.3)
5. Config file present with `mode="openrouter"` and a missing/empty key → raise `ConfigError` whose message names the config file to fill in. **Hard failure, never a silent fallback to dummy.** (FR1.3)
6. Any other `mode` value → `ConfigError` naming the accepted values. (FR1.1)

> **Interpretation of FR1.2 vs FR1.3 (requirements review `R-01`).** FR1.2's literal "or the key inside it, is absent" and FR1.3's "in live mode … shall fail" prescribe opposite outcomes for one input: a config file that selects `openrouter` with an empty key. This plan adopts the deterministic reading requested by `R-01` — mode comes from the config file; an explicit `openrouter` with an empty/missing key fails per FR1.3; only a file that states no mode (including an absent file) defaults to dummy per FR1.2. Recorded here because the two IDs alone do not disambiguate; it is a resolution of existing text, not a new requirement.

The API key **never** appears in `Settings.__repr__`/`__str__` (both render `<redacted>`), never appears in a log line, and is never written to SQLite. (FR1.5, NFR2)

### 3.2 Sentiment engine (`app/sentiment.py`, `app/dummy_client.py`, `app/openrouter_client.py`)

```python
LABELS = ("positive", "negative", "neutral")

@dataclass(frozen=True)
class SentimentResult:
    label: Literal["positive", "negative", "neutral"]
    probabilities: dict[str, float]   # keyed by label, sums to ~1.0
    confidence: float
    intensity: float                  # -1.0 .. 1.0
    model: str
    provider: str

@runtime_checkable
class SentimentClient(Protocol):
    def analyze(self, text: str) -> SentimentResult: ...
```

- **`DummyClient`** (default, offline). `POSITIVE_WORDS` / `NEGATIVE_WORDS` frozensets; a positive keyword count above the negative count → `positive`, the reverse → `negative`, otherwise `neutral`. `LABEL_PROBABILITIES` is a fixed per-label triple; `INTENSITY_BY_LABEL = {"positive": 0.6, "negative": -0.6, "neutral": 0.0}`. `model="dummy-keyword-v1"`, `provider="local-dummy"`. Performs no network access and needs no key. (FR2.2, FR2.5, FR2.7)
- **`OpenRouterClient`** (live, opt-in). `POST https://openrouter.ai/api/alpha/decisions` with `Authorization: Bearer <key>` and model id `typesafe/jev-1.13`; body carries one **Choice** question whose options are exactly `positive`, `negative`, `neutral` and one **Score** question over the range −1..1. Reads the selected label, the per-option probabilities, the confidence and the score from the **typed** response fields only; `model="typesafe/jev-1.13"`, `provider="openrouter"`. Branches only on typed results — it never parses free text. On a network error, a non-2xx response, or a response missing a typed Choice/Score result it raises `SentimentEngineError` and persists nothing. HTTP via stdlib `urllib.request` with a bounded timeout. (FR2.3, FR2.4, FR2.5, FR2.6, FR2.7, NFR3)
- **Swappability.** `app/service.py` and everything above it depend on the `SentimentClient` protocol only; neither the routes, the repository, nor the page imports a concrete client. (FR2.1, NFR5)
- **Test isolation.** No test constructs or calls `OpenRouterClient`. (FR5.5)

### 3.3 Storage (`app/db.py`, `app/repository.py`)

Single file at `data/sentiment.db`, created with its parent directory on first run; no manual setup. (FR3.1, FR3.2, NFR6)

```sql
CREATE TABLE IF NOT EXISTS analyses (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT    NOT NULL,
  label         TEXT    NOT NULL CHECK (label IN ('positive','negative','neutral')),
  probabilities TEXT    NOT NULL,          -- JSON object keyed by label
  confidence    REAL    NOT NULL,
  intensity     REAL    NOT NULL,
  model         TEXT    NOT NULL,
  provider      TEXT    NOT NULL,
  created_at    TEXT    NOT NULL           -- ISO 8601 UTC, e.g. 2026-09-29T11:51:07Z
);
CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
```

`init_db()` is idempotent (`CREATE TABLE IF NOT EXISTS`, `schema_meta.version = 1`) and runs from the app lifespan, so a fresh checkout reaches a usable state with no manual step. `insert_analysis()` writes one row and returns the stored `AnalysisRecord` (`created_at` injected via a `now` seam for deterministic tests); `list_analyses(limit=50)` returns newest-first by `ORDER BY id DESC LIMIT ?`. (FR3.3, FR3.4)

`AnalysisRecord.to_dict()` isolates the value encodings pinned by the review (`R-05`): `probabilities` is a **JSON object keyed by label** (never an array) and `created_at` is an **ISO 8601 UTC string ending in `Z`**. (FR4.5)

### 3.4 HTTP surface (`app/routes.py`, `app/main.py`)

| Route | Request | Response | Requirements |
|---|---|---|---|
| `GET /` | — | the HTML page (form + result + history) | FR4.1, FR4.2 |
| `POST /analyze` | `{"text": "<non-empty string>"}` | `200` + full stored record | FR4.3, FR4.5 |
| `POST /analyze` | `text` missing / empty / whitespace-only | `422` + error envelope, **no row persisted** | FR4.3, `R-02` |
| `GET /analyses?limit=50` | `limit` int ≥ 1, default `50` | `200` + `{"analyses": [record, …]}`, newest-first, `{"analyses": []}` when empty | FR4.4, FR4.5 |
| `GET /analyses?limit=0\|-1\|"abc"` | — | `422` + error envelope | FR4.4, `R-04` |
| `GET /health` | — | `{"status": "ok", "mode": "<active mode>"}` | FR4.6, FR1.4 |

Error envelope for every non-2xx: `{"error": {"code": "<MACHINE_CODE>", "message": "<human message>", "details": [...]}}`.

> **Interpretations recorded for review findings.** `R-02`: empty/whitespace/absent `text` on `POST /analyze` is rejected with `422` and no row is written — this pins the boundary the requirement left open. `R-04`: `limit` is validated as an integer ≥ 1 (default 50) and an out-of-range or non-integer value is a `422`, not a silent clamp — pinning the validation rule `R-04` asked for. `R-05`: value encodings pinned in §3.3. These resolve existing requirement text; none of them adds a capability the requirements do not already describe.

- Single ASGI app on a single port serving both the page and the JSON API. (A2)
- Lifespan: load settings → `init_db()` → log exactly one startup line naming the active mode; the key is never in it. (FR1.4, FR1.5, FR3.2)
- `create_app(settings: Settings | None = None)` factory so tests inject settings pointing at a temporary database.
- `HOST = "127.0.0.1"` is the only bind address used by the run entry point and is documented as the dev command's bind; no auth middleware exists anywhere. (FR4.7, NFR4)

### 3.5 Frontend (`app/static/`)

One static HTML page plus vanilla JS, served from the app (no template engine — `jinja2` is not a permitted dependency). The form posts to `/analyze`, renders `label`, `confidence` and the per-label probabilities, then refreshes the history list from `/analyses?limit=50`. (FR4.1, FR4.2)

Stable `data-testid` hooks on the interactive elements, per the developer agent's automation-friendly code rule: `analyze-form`, `analyze-input`, `analyze-submit-button`, `result-panel`, `error-panel`, `history-list`, `history-item`.

---

## Testing Contract

```json
{
  "version": 1,
  "methodology": "test-after",
  "source": "org",
  "ordering": "implement each applicable testable layer, then write and run that layer's tests.",
  "scope": "poc",
  "test_strategy": "minimal",
  "project_type": "greenfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    }
  ],
  "obligations": {
    "strategy": "minimal",
    "strategy_volume": [
      "One verifiable test per requirement at the narrowest effective level.",
      "At least one happy-path unit test per component.",
      "Unit tests are the default; a bugfix/security scope floor may require an integration or E2E regression when that is the narrowest level that reproduces the defect."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "test-after",
    "runner_step": "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Bootstrap the minimal test runner/configuration and record the exact unit-scoped command.",
      "Data model / database behavior - implement.",
      "Data model / database behavior - write and run its tests after implementation.",
      "Repository / data access - implement.",
      "Repository / data access - write and run its tests after implementation.",
      "Business logic - implement.",
      "Business logic - write and run its tests after implementation.",
      "API / endpoint - implement.",
      "API / endpoint - write and run its tests after implementation.",
      "Frontend behavior - implement.",
      "Frontend behavior - write and run its tests after implementation.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:c5db1280ba0333b655bcf97bdcaeaa0fd9cc0f50807a6ee879935b8aff3e17e0",
  "contract_sha256": "sha256:be5041ec2297dded1a31f328fae6a86555cf649f231018ea8168c9bb8dd811a5"
}
```

The contract below is pasted unchanged from the resolver output for this intent's resolved posture (`org.md` `## Testing Posture`, scope `poc`, strategy Minimal, greenfield).

**How the contract drives this plan.** Methodology is `test-after` with ordering "implement each applicable testable layer, then write and run that layer's tests", so each testable layer below appears as an implement step immediately followed by its test step — no Red step precedes an implementation, and no layer is skipped. All five `testable_layers` apply to this app (the frontend is a real, served page), so none is omitted. Test-runner readiness (Step 2) precedes the first test step, per `runner_ready_before_first_test`. `poc` scope adds no extra new-test floor; the Minimal strategy obligations are the whole testing obligation, and the existing suite (empty at greenfield start) must end green.

---

## 5. Implementation Steps

Ordering follows `plan_profile.steps` exactly. Each step lists the requirement IDs it implements.

### Step 1 — Project structure and production configuration skeleton

- [x] Create the `app/` package with `__init__.py` (public re-export `from app.main import app` so `uvicorn app:app` resolves) and empty-but-documented module placeholders for `config.py`, `models.py`, `db.py`, `repository.py`, `sentiment.py`, `dummy_client.py`, `openrouter_client.py`, `service.py`, `routes.py`, `main.py`. — FR5.1, A2
- [x] Create `tests/` with `conftest.py` reserved for the harness built in Step 2. — FR5.2
- [x] Write `pyproject.toml` with project metadata, `requires-python = ">=3.11"`, runtime dependencies `fastapi` and `uvicorn`, and the `dev` extra carrying `pytest`. — NFR3, A1
- [x] Commit `config.example.toml` containing `mode = "dummy"` and an empty/placeholder `api_key` with comments explaining that the real file is `config.local.toml`, and carrying no secret value. — FR1.6, NFR2
- [x] Write `.gitignore` with `config.local.toml`, `data/`, `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.venv/`. — FR1.6, NFR2
- [x] Create the gitignored `data/` directory placeholder note in `README.md` only; the directory itself is created at first run by `init_db()` in Step 3. — FR3.1, NFR6
- [x] Confirm the skeleton is importable (`python -c "import app"`) and that a stub `app/main.py` exposing `app` makes `uvicorn app:app --reload` start and stop cleanly before any feature code lands. — FR5.1

### Step 2 — Bootstrap the minimal test runner/configuration and record the exact unit-scoped command

- [x] Add `[tool.pytest.ini_options]` to `pyproject.toml`: `testpaths = ["tests"]`, `addopts = "-q"`, `filterwarnings = ["error"]`; declare no pytest plugins, so the runner needs only `pytest` itself. — FR5.2, NFR3
- [x] Record the exact scoped command for this work in `unit-test-instructions.md`: `python -m pytest tests -q` (stage-level scope; this intent is zero-Unit so `tests/` **is** this work's suite), plus one exact per-layer file command for each of the seven test files. Never a bare project-wide `pytest` without the path. — FR5.2
- [x] Build the in-process ASGI harness in `tests/conftest.py`: an `asgi_request(app, method, path, json_body=None, query="")` helper that enters `app.router.lifespan_context(app)`, builds a minimal HTTP `scope`, calls the app, and returns `(status_code, parsed_json_or_text)`. This replaces `fastapi.testclient.TestClient` so `httpx` is never added. — FR5.2, NFR3, FR4.3
- [x] Add the `tmp_settings` fixture: a `Settings` (or `create_app()` argument set) pointing `db_path` at `tmp_path/"sentiment.db"`, `mode="dummy"`, `api_key=None`, so no test ever reads or writes the real `config.local.toml` or `data/sentiment.db`. — FR5.3, FR3.1
- [x] Add the session-wide offline guard: an autouse fixture that makes `socket.socket.connect` raise, so any accidental network use fails the suite loudly rather than silently reaching OpenRouter. — FR5.3, FR5.5, NFR1
- [x] Prove runner readiness: `python -m pytest --version` and `python -m pytest tests -q` both execute, so the recorded command is runnable before the first test is written (an empty run at this point is expected; no placeholder test is added to fake it). — FR5.2

### Step 3 — Data model / database behavior — implement

- [x] Implement `app/db.py`: `connect(db_path)` returning `sqlite3.Connection` with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`. — FR3.1
- [x] Implement `init_db(db_path)`: create the parent directory, create the `analyses` table (§3.3) with the `label` CHECK constraint, create `schema_meta` and record `version = 1`, and run on every start so first-run setup is automatic and re-runs are no-ops. — FR3.2, FR3.1, NFR6
- [x] Pin the row contract: `text`, `label`, `probabilities` (JSON object), `confidence`, `intensity`, `model`, `provider`, `created_at` (ISO 8601 UTC). — FR3.3
- [x] Implement `app/models.py`: the `AnalysisRecord` dataclass with `to_dict()` producing exactly the field set and encodings of §3.3, and the request/response schemas for `/analyze` (`text: str`) and the record response. — FR4.5, FR3.3

### Step 4 — Data model / database behavior — write and run its tests after implementation

- [x] Write `tests/test_db.py::test_init_creates_database_and_schema_on_first_run`: a fresh `tmp_path` with no `data/` directory yields a created file and an `analyses` table whose columns match §3.3. — FR3.1, FR3.2, NFR6
- [x] Write `tests/test_db.py::test_init_is_idempotent`: calling `init_db()` twice leaves the schema and any existing rows intact. — FR3.2
- [x] Run `python -m pytest tests/test_db.py -q` and get it green before moving on. — FR5.2, FR5.4

### Step 5 — Repository / data access — implement

- [x] Implement `app/repository.py::insert_analysis(conn, text, result, now=None)`: serialize `result.probabilities` with `json.dumps` into the `probabilities` column, write the remaining scalar fields, and return the stored `AnalysisRecord` read back from the database (so the returned `id` and `created_at` are the persisted values, not the in-memory payload). — FR3.3
- [x] Implement `app/repository.py::list_analyses(conn, limit=50)`: `SELECT … ORDER BY id DESC LIMIT ?`, newest-first, returning a list of `AnalysisRecord`. — FR3.4, FR4.4
- [x] Add the `now` seam (default `datetime.now(timezone.utc)`) formatted as ISO 8601 UTC with a `Z` suffix, so timestamps are injectable and the stored encoding is deterministic. — FR3.3, FR4.5

### Step 6 — Repository / data access — write and run its tests after implementation

- [x] Write `tests/test_repository.py::test_insert_returns_stored_row_with_all_fields`: insert one analysis, assert every field of the returned record plus that `probabilities` round-trips as a label-keyed object and `created_at` matches the injected ISO 8601 UTC instant. — FR3.3, FR4.5
- [x] Write `tests/test_repository.py::test_list_analyses_newest_first_with_limit`: insert three rows with distinct injected timestamps, assert the order is newest-first and that `limit=2` returns exactly the two newest. — FR3.4, FR4.4
- [x] Run `python -m pytest tests/test_repository.py -q` and get it green. — FR5.2, FR5.4

### Step 7 — Business logic — implement

- [x] Implement `app/sentiment.py`: `LABELS`, the frozen `SentimentResult` dataclass (`label`, `probabilities`, `confidence`, `intensity`, `model`, `provider`), and the `@runtime_checkable SentimentClient` protocol with a single `analyze(text) -> SentimentResult` method. — FR2.1, FR2.7, NFR5
- [x] Implement `app/dummy_client.py::DummyClient`: keyword-list classification (positive vs. negative counts, neutral otherwise), fixed per-label probability triples, fixed intensity per label, `model="dummy-keyword-v1"`, `provider="local-dummy"`, and no network access of any kind. — FR2.2, FR2.5, FR2.7
- [x] Implement `app/openrouter_client.py::OpenRouterClient`: `POST https://openrouter.ai/api/alpha/decisions` via stdlib `urllib.request` with `Authorization: Bearer <key>`, model id `typesafe/jev-1.13`, one Choice question over `positive`/`negative`/`neutral`, one Score question over −1..1; read the typed label, probabilities, confidence and score; raise `SentimentEngineError` on network failure, non-2xx, or a missing typed result; branch on typed fields only and never parse free text. — FR2.3, FR2.4, FR2.5, FR2.6, FR2.7, NFR3
- [x] Implement `app/config.py`: the frozen `Settings` dataclass, `load_settings()` implementing the six ordered rules of §3.1, `ConfigError` naming the config file, key redaction in `__repr__`/`__str__`, and `tomllib`-based parsing. — FR1.1, FR1.2, FR1.3, FR1.5, FR1.6, NFR1
- [x] Implement `app/service.py::analyze_text(client, conn, text, now=None)`: strip the incoming text, reject empty/whitespace with `InvalidTextError` **before** any client call or write, call `client.analyze()` through the protocol, persist via `insert_analysis()`, and return the stored record. Depend on `SentimentClient` only — never on a concrete client. — FR4.3, FR3.3, FR2.1, NFR5
- [x] Implement `app/service.py::get_client(settings)`: return `DummyClient()` for `mode="dummy"`, `OpenRouterClient(settings.api_key, settings.model)` for `mode="openrouter"`, and nothing else. — FR2.1, FR1.1

### Step 8 — Business logic — write and run its tests after implementation

- [x] Write `tests/test_config.py::test_mode_defaults_to_dummy_when_config_missing`: `load_settings()` against a non-existent path returns `mode="dummy"`, `api_key=None`. — FR1.2, NFR1
- [x] Write `tests/test_config.py::test_mode_and_key_read_from_config_file`: a config file stating `mode="openrouter"` with a key yields that mode and key. — FR1.1
- [x] Write `tests/test_config.py::test_live_mode_with_empty_key_fails_naming_config_file`: `mode="openrouter"` with a missing or empty key raises `ConfigError` whose message contains the config file name. — FR1.3, FR1.6
- [x] Write `tests/test_config.py::test_api_key_is_never_logged`: `repr()`/`str()` of `Settings` and every log record emitted while loading a config containing a key contain neither the key nor a substring of it. — FR1.5, NFR2
- [x] Write `tests/test_config.py::test_example_config_parses_with_placeholder_key`: `config.example.toml` parses with `tomllib` and its `api_key` is empty or an obvious placeholder, so the committed example carries no secret. — FR1.6, NFR2
- [x] Write `tests/test_config.py::test_local_config_is_gitignored`: `git check-ignore -q config.local.toml` succeeds (skipped only if `git` is unavailable on the machine), proving the real config cannot be committed. — FR1.6, NFR2
- [x] Write `tests/test_dummy_client.py::test_dummy_labels_positive_keyword`, `…::test_dummy_labels_negative_keyword` and `…::test_dummy_labels_neutral_otherwise`: deterministic labels for one positive keyword, one negative keyword, and keyword-free text. — FR2.2
- [x] Write `tests/test_dummy_client.py::test_dummy_fixed_probabilities_per_label`: the same input always yields the same label-keyed probability triple, and the triple sums to ~1.0 for each label. — FR2.2
- [x] Write `tests/test_dummy_client.py::test_dummy_result_carries_intensity_model_and_provider`: the result carries the fixed intensity and the dummy `model`/`provider` values. — FR2.5, FR2.7
- [x] Write `tests/test_dummy_client.py::test_dummy_makes_no_network_call`: the session-wide `socket.connect` guard is armed, so a dummy analysis completing proves no network access; no key is present in the environment or config. — FR2.2, FR5.3, NFR1
- [x] Write `tests/test_service.py::test_service_rejects_empty_or_whitespace_text`: empty, whitespace-only, and missing text raise `InvalidTextError` and leave the `analyses` table row count unchanged. — FR4.3 (`R-02`)
- [x] Write `tests/test_service.py::test_service_persists_and_returns_record`: one analysis through `DummyClient` and a temp database lands exactly one row and returns the stored record. — FR4.3, FR3.3
- [x] Write `tests/test_service.py::test_client_is_substitutable_behind_the_interface`: a small local duck-typed stub implementing `analyze()` is passed where `SentimentClient` is expected; its returned label, probabilities, confidence, intensity, model and provider flow through the real repository into a persisted record and back out, proving the engine is replaceable without touching storage or the API. — FR2.1, NFR5
- [x] Run `python -m pytest tests/test_config.py tests/test_dummy_client.py tests/test_service.py -q` and get them green. — FR5.2, FR5.4

### Step 9 — API / endpoint — implement

- [x] Implement `app/routes.py::POST /analyze`: validate `text` at the boundary, delegate to `service.analyze_text()`, and return `200` with the full stored record. — FR4.3, FR4.5
- [x] Implement the invalid-input path: missing, empty, or whitespace-only `text` returns `422` with the error envelope and persists nothing. — FR4.3 (`R-02`)
- [x] Implement `app/routes.py::GET /analyses`: `limit: int = Query(50, ge=1)`, newest-first, wrapped as `{"analyses": [...]}`, and `{"analyses": []}` for an empty history; a non-integer or out-of-range `limit` returns `422` with the error envelope (no silent clamping). — FR4.4, FR4.5 (`R-04`)
- [x] Implement `app/routes.py::GET /health` returning `{"status": "ok", "mode": <active mode>}`. — FR4.6, FR1.4
- [x] Implement `app/routes.py::GET /` returning the static page (Step 11) and mount `/static` via `StaticFiles` for `app.js`, with no template engine. — FR4.1, FR4.2
- [x] Implement `app/main.py`: the `create_app(settings=None)` factory, the lifespan that loads settings, calls `init_db()`, and logs one startup line naming the active mode (never the key), and the module-level `app = create_app()` that `uvicorn app:app` imports. — FR1.4, FR1.5, FR3.2, FR5.1, A2
- [x] Pin the bind: the run entry point binds `127.0.0.1` only, and no authentication, session, or CORS middleware is added anywhere. — FR4.7, NFR4
- [x] Map expected failures to the consistent error envelope `{"error": {"code", "message", "details"}}` at the boundary; unexpected exceptions propagate to FastAPI's 500 rather than being swallowed. — FR4.3

### Step 10 — API / endpoint — write and run its tests after implementation

- [x] Write `tests/test_routes.py::test_post_analyze_returns_stored_record`: `POST /analyze` with dummy-mode settings returns `200` and a record carrying `id`, `text`, `label`, `probabilities`, `confidence`, `intensity`, `model`, `provider` and `created_at`, with `created_at` matching the ISO 8601 UTC encoding. — FR4.3, FR4.5
- [x] Write `tests/test_routes.py::test_post_analyze_rejects_invalid_text_without_persisting`: empty, whitespace-only and absent `text` each return `422` and leave the row count unchanged. — FR4.3 (`R-02`)
- [x] Write `tests/test_routes.py::test_get_analyses_newest_first_with_default_limit`: after more than three analyses, the response is newest-first and defaults to `limit=50`; an empty history returns `{"analyses": []}`. — FR4.4, FR4.5
- [x] Write `tests/test_routes.py::test_get_analyses_rejects_invalid_limit`: `limit=0`, `limit=-1` and `limit=abc` each return `422`. — FR4.4 (`R-04`)
- [x] Write `tests/test_routes.py::test_health_reports_active_mode`: `/health` reports the mode from injected settings for both `dummy` and `openrouter`. — FR4.6, FR1.4
- [x] Write `tests/test_routes.py::test_analyze_uses_the_injected_client_not_a_network_client`: with the offline guard armed, a successful `POST /analyze` proves the request path never reaches a network client. — FR5.3, FR5.5, NFR1
- [x] Run `python -m pytest tests/test_routes.py -q` and get it green. — FR5.2, FR5.4

### Step 11 — Frontend behavior — implement

- [x] Write `app/static/index.html`: one textarea/input plus a submit button inside a form, a result panel showing `label`, `confidence` and the per-label probabilities, and a history list container. Static HTML only — no template engine. — FR4.1, FR4.2
- [x] Add stable `data-testid` attributes to every interactive element: `analyze-form`, `analyze-input`, `analyze-submit-button`, `result-panel`, `error-panel`, `history-list`, `history-item`. — FR4.1, FR4.2
- [x] Write `app/static/app.js`: submit the form to `POST /analyze` with `fetch`, render the returned label/confidence/probabilities into the result panel, and render an error message from the error envelope on a non-2xx response; refresh the history from `GET /analyses?limit=50` on load and after each submission. — FR4.1, FR4.2, FR4.3
- [x] Keep the page free of any sentiment logic of its own: it displays what the API returns and never computes a label client-side. — FR4.1, NFR5

### Step 12 — Frontend behavior — write and run its tests after implementation

- [x] Write `tests/test_page.py::test_index_page_renders_form_result_and_history`: `GET /` returns `200` with `content-type: text/html` and serves markup containing the analyze form, the result panel and the history list, each carrying its required `data-testid`. — FR4.1, FR4.2
- [x] Write `tests/test_page.py::test_page_assets_are_served`: `GET /static/app.js` returns `200` with a JavaScript content type, so the page's submit and history behavior can actually load. — FR4.1, FR4.2
- [x] Run `python -m pytest tests/test_page.py -q` and get it green, then run the whole scoped suite `python -m pytest tests -q`. — FR5.2, FR5.4
- [x] Note the verification limit: browser-side execution of `app.js` is not exercised (no browser-automation dependency is permitted under the dependency cap), so the page is verified at the served-markup contract level, which is the narrowest effective level available here. — FR4.1, FR4.2, NFR3

### Step 13 — Environment/build configuration

- [x] Finalize `pyproject.toml`: `[project]` metadata, `requires-python`, `dependencies = ["fastapi…", "uvicorn…"]`, `[project.optional-dependencies] dev = ["pytest…"]`, `[tool.pytest.ini_options]` from Step 2, and a setuptools build backend so `pip install -e ".[dev]"` works without adding a runtime dependency. — NFR3, A1, FR5.2
- [x] Verify the dependency cap: after `python -m pip install -e ".[dev]"`, the top-level third-party imports used by the codebase are exactly `fastapi`, `uvicorn`, `pytest` (everything else is stdlib — `sqlite3`, `tomllib`, `urllib.request`, `json`, `dataclasses`, `pathlib`, `logging`, `datetime`, `typing`). — NFR3
- [x] Confirm `.gitignore` excludes `config.local.toml` and `data/` while `config.example.toml` stays tracked, and that `config.example.toml` still contains no secret. — FR1.6, NFR2
- [x] Document the dev command `uvicorn app:app --reload` as the single command that starts the app. — FR5.1
- [x] Record the test command `pytest` as the single command that runs the suite, resolving through `testpaths = ["tests"]`. — FR5.2
- [x] Smoke-run the real surface: start `uvicorn app:app --port <ephemeral>` with no `config.local.toml` present, then confirm (a) the startup output names the active mode `dummy`, (b) `GET /health` returns `{"status": "ok", "mode": "dummy"}`, (c) `GET /` returns the page, (d) `POST /analyze` with dummy-mode text returns a stored record that then appears in `GET /analyses`, and (e) the file `data/sentiment.db` now exists with rows in it. — FR1.4, FR3.1, FR3.2, FR4.1, FR4.3, FR4.4, FR4.6, NFR6
- [x] Verify the localhost-only bind behaviourally: the server accepts connections on `127.0.0.1` and refuses a connection to the same port on the machine's non-loopback address; no auth is required or present on any route. — FR4.7, NFR4
- [x] Confirm there are no deployment artifacts: no Dockerfile, no compose file, no IaC template, and no cloud or CI configuration. `poc` excludes them and NFR4 forbids containers; their absence is deliberate, not an omission to be fixed later. — NFR4

### Step 14 — Documentation and traceability

- [x] Write `README.md` at the repo root: prerequisites, `pip install -e ".[dev]"`, the dev command, the test command, the two modes, how to create `config.local.toml` from the example, where the database lives, and the file layout from §2. — FR5.1, FR5.2, FR1.6, NFR6
- [x] Add module-level docstrings to each `app/*.py` module stating its single responsibility and its requirement IDs, and docstrings on `load_settings`, `init_db`, `insert_analysis`, `list_analyses`, `analyze_text` and each route documenting the contract and the failure modes. — FR1.3, FR3.2, FR4.3, FR4.4
- [x] Write the stage's `code-summary.md` recording what was built, the exact commands run, and the observed results. — FR5.4
- [x] Write the stage's `traceability.json` mapping every requirement ID in §6 to its implementing file and its verifying test or smoke step, marking the live-client-only requirements (`FR2.3`, `FR2.4`, `FR2.6`) as `N/A` for automated coverage with the reason "live OpenRouter client is never exercised by tests (FR5.5)". — FR5.4, FR5.5
- [x] Update the intent's memory/audit trail through the stage's normal channels — do not hand-edit state. — FR5.4
- [x] Final check: `python -m pytest tests -q` is green, the app is runnable with no config file and no key, and the plan's checkbox steps all correspond to something that exists on disk. — FR5.2, FR5.3, NFR1

---

## 6. Requirement → Verification Traceability

Every requirement ID in `requirements.md` appears exactly once. "Verification" names the test function from Steps 4/6/8/10/12, or the Step 13/14 smoke step where a pytest test is not the narrowest effective level.

| ID | Implemented by | Verified by |
|---|---|---|
| FR1.1 | `app/config.py::load_settings` | `test_mode_and_key_read_from_config_file` |
| FR1.2 | `app/config.py::load_settings` (rules 1–3) | `test_mode_defaults_to_dummy_when_config_missing` |
| FR1.3 | `app/config.py::load_settings` (rule 5) + `ConfigError` | `test_live_mode_with_empty_key_fails_naming_config_file` |
| FR1.4 | `app/main.py` lifespan log; `app/routes.py::GET /health` | `test_health_reports_active_mode`; Step 13 smoke (a) and (b) |
| FR1.5 | `app/config.py` redaction; logging discipline | `test_api_key_is_never_logged` |
| FR1.6 | `config.example.toml`; `.gitignore` | `test_example_config_parses_with_placeholder_key`; `test_local_config_is_gitignored` |
| FR2.1 | `app/sentiment.py` protocol; `app/service.py::get_client`; `app/dummy_client.py`; `app/openrouter_client.py` | `test_client_is_substitutable_behind_the_interface` |
| FR2.2 | `app/dummy_client.py::DummyClient` | `test_dummy_labels_positive_keyword`, `test_dummy_labels_negative_keyword`, `test_dummy_labels_neutral_otherwise`, `test_dummy_fixed_probabilities_per_label`, `test_dummy_makes_no_network_call` |
| FR2.3 | `app/openrouter_client.py` | Not covered by tests (FR5.5) — live-only; manual live smoke with a key, out of the automated suite |
| FR2.4 | `app/openrouter_client.py` | Not covered by tests (FR5.5) — live-only; manual live smoke with a key |
| FR2.5 | `app/openrouter_client.py` (Score question); `app/dummy_client.py` (fixed value) | `test_dummy_result_carries_intensity_model_and_provider` |
| FR2.6 | `app/openrouter_client.py` (typed-field branching only) | Not covered by tests (FR5.5) — live-only; code review at Step 7 |
| FR2.7 | `app/sentiment.py::SentimentResult`; both clients | `test_dummy_result_carries_intensity_model_and_provider` |
| FR3.1 | `app/db.py`; `Settings.db_path` | `test_init_creates_database_and_schema_on_first_run`; Step 13 smoke (e) |
| FR3.2 | `app/db.py::init_db`; `app/main.py` lifespan | `test_init_creates_database_and_schema_on_first_run`, `test_init_is_idempotent` |
| FR3.3 | `app/db.py` schema; `app/repository.py::insert_analysis` | `test_insert_returns_stored_row_with_all_fields`, `test_service_persists_and_returns_record` |
| FR3.4 | `app/repository.py::list_analyses` | `test_list_analyses_newest_first_with_limit` |
| FR4.1 | `app/static/index.html`; `app/static/app.js`; `app/routes.py::GET /` | `test_index_page_renders_form_result_and_history`, `test_page_assets_are_served` |
| FR4.2 | `app/static/index.html` (history list); `app/static/app.js`; `GET /analyses` | `test_index_page_renders_form_result_and_history` |
| FR4.3 | `app/routes.py::POST /analyze`; `app/service.py::analyze_text` | `test_post_analyze_returns_stored_record`, `test_post_analyze_rejects_invalid_text_without_persisting`, `test_service_rejects_empty_or_whitespace_text` |
| FR4.4 | `app/routes.py::GET /analyses`; `app/repository.py::list_analyses` | `test_get_analyses_newest_first_with_default_limit`, `test_get_analyses_rejects_invalid_limit` |
| FR4.5 | `app/models.py::AnalysisRecord.to_dict` | `test_post_analyze_returns_stored_record`, `test_get_analyses_newest_first_with_default_limit` |
| FR4.6 | `app/routes.py::GET /health` | `test_health_reports_active_mode` |
| FR4.7 | `app/main.py` (`HOST = 127.0.0.1`, no auth middleware) | Step 13 localhost-bind verification |
| FR5.1 | `pyproject.toml`; `README.md`; `app:app` entry | Step 13 smoke (dev command starts the app) |
| FR5.2 | `pyproject.toml` `[tool.pytest.ini_options]` | Step 2 runner readiness; Step 12 whole-suite run |
| FR5.3 | `tests/conftest.py` (dummy settings, socket guard) | `test_dummy_makes_no_network_call`, `test_analyze_uses_the_injected_client_not_a_network_client` |
| FR5.4 | `tests/test_config.py`, `test_dummy_client.py`, `test_db.py`, `test_repository.py`, `test_service.py`, `test_routes.py`, `test_page.py` | the whole scoped suite `python -m pytest tests -q` |
| FR5.5 | `app/openrouter_client.py` (behind the interface) | Session-wide offline guard armed in `conftest.py`; no test targets the live client (see `traceability.json`) |
| NFR1 | `app/config.py` default; `conftest.py` | `test_mode_defaults_to_dummy_when_config_missing`, `test_dummy_makes_no_network_call` |
| NFR2 | `config.example.toml`; `.gitignore`; `Settings` redaction | `test_example_config_parses_with_placeholder_key`, `test_local_config_is_gitignored`, `test_api_key_is_never_logged` |
| NFR3 | `pyproject.toml` dependency set; stdlib-only client/config/db internals | Step 13 dependency-cap check |
| NFR4 | `app/main.py` bind; no auth; no deployment artifacts | Step 13 localhost-bind verification and deployment-artifact check |
| NFR5 | `app/sentiment.py` protocol; `app/service.py` dependency direction | `test_client_is_substitutable_behind_the_interface` |
| NFR6 | `app/db.py::init_db` (directory + schema creation) | `test_init_creates_database_and_schema_on_first_run` |
| A1 | `pyproject.toml` declares and installs the dependencies | Step 1 and Step 13 |
| A2 | `app/main.py` — one app, one port, page + JSON API | `test_index_page_renders_form_result_and_history`, `test_health_reports_active_mode` |

---

## 7. Deliberate Omissions

| Stage checklist item | Decision | Reason |
|---|---|---|
| Integration tests | Omitted | Minimal strategy makes unit tests the default; the endpoint layer is already verified against the real SQLite file through the in-process ASGI harness, which is the narrowest level that covers the request→persist→read path. `poc` adds no new-test floor. |
| E2E tests | Omitted | No browser-automation dependency is permitted under the dependency cap (NFR3/NFR4); the page is verified at the served-markup contract level. |
| Database migrations | Folded into Step 3 | FR3.2 requires an init/migration step that creates the schema on first run; with one table and no prior version there is nothing to migrate. `schema_meta.version` is written so a later change has a hook. |
| Deployment artifacts (Dockerfile, IaC) | Omitted | NFR4 excludes containers and cloud services; this is a localhost-only single-user app. |
| Authentication / authorization | Omitted | Explicitly out of scope; FR4.7 requires no auth. |
| CI pipeline configuration | Omitted | `ci-pipeline` is SKIP in `poc`. |
| Coverage threshold configuration | Omitted | `poc` adds no extra new-test floor and no line-coverage gate; the Minimal obligation is requirement-driven coverage, evidenced by §6. No threshold is set, and none may be lowered to make a step pass. |

---

## 8. Definition of Done for This Plan

- All 14 steps are ticked and every checkbox corresponds to a file or a recorded command result on disk.
- `python -m pytest tests -q` is green with no test requiring a network connection, an API key, or `config.local.toml`.
- The app starts with `uvicorn app:app --reload` from a fresh checkout with no config file, reports `dummy` mode, accepts text on the page, persists it to `data/sentiment.db`, and shows it in the history view.
- `data/sentiment.db` is created automatically on first run; `config.local.toml` is absent from version control and `config.example.toml` contains no secret.
- Every requirement ID in §6 is verified by the named test or smoke step; the three live-client-only requirements are explicitly recorded as not covered by tests because FR5.5 forbids exercising that client.
