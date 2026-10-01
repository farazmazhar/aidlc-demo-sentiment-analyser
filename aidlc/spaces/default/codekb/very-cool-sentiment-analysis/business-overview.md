# Business Overview — `very-cool-sentiment-analysis`

> Reverse-engineering synthesis of the developer scan
> (`inception/reverse-engineering/developer-scan.md`). Every statement below is
> traceable to a scanned path; file references are repo-relative.

## Business Domain

**Local text sentiment analysis.** The product is a single-user, localhost-only
web tool that reads a short piece of text and returns a typed sentiment
decision — `positive`, `negative` or `neutral` — together with a confidence, a
signed intensity in −1..1, and the per-label probabilities
(`app/sentiment.py`, `app/models.py`, `README.md`).

The domain is deliberately narrow: no tenancy, no accounts, no multi-user
concepts, no cloud infrastructure. The value proposition is *a sentiment API you
can run on your own machine* — offline by default, with one opt-in path to a
hosted model (`README.md`, "The two modes").

## Purpose

Provide a small, dependency-light service that:

1. scores one piece of submitted text with a swappable sentiment engine,
2. stores every scored analysis in a local SQLite file, and
3. exposes the same result over HTTP and through a single web page.

The stated engineering constraints baked into the manifest are "dependency
light" (2 runtime + 1 dev package, `pyproject.toml`) and "storage is the
standard-library `sqlite3`" (`README.md`, Prerequisites).

## Key Functionality

| # | Business capability | What it does | Primary evidence |
|---|---|---|---|
| 1 | **Score a text** | `POST /analyze` cleans the text, chooses the engine, calls it, and returns the record **as persisted** | `app/routes.py:89-99`, `app/service.py:85-104`, `app/repository.py:38-70` |
| 2 | **Persist and browse history** | One SQLite row per analysis; history read newest-first with a caller-set limit (default 50) | `app/db.py:38-83`, `app/repository.py:73-80`, `app/routes.py:102-109` |
| 3 | **Select the engine** | Two modes — offline keyword engine (default) and live OpenRouter Jev model — resolved from one local TOML file | `app/config.py:73-125`, `app/dummy_client.py`, `app/openrouter_client.py` |
| 4 | **Report the live connection state** | One `effective_connection` payload (`connected`, `source`, `mode`, `model`, `reason`) drives `/health`, `/auth/status` and the page indicator | `app/service.py:31-57`, `app/routes.py:113-134` |
| 5 | **Connect the live model from the page** | In-app OpenRouter PKCE (S256) authorization; the credential lives in process memory only | `app/session_auth.py`, `app/routes.py:125-167`, `app/static/app.js:130-175` |
| 6 | **Keep secrets and data local** | The key is never rendered, logged or stored; the database is a gitignored local file | `app/config.py:27-52`, `app/session_auth.py:78-121`, `.gitignore` (`/data/`), `README.md` |
| 7 | **Fail in one shape** | Every non-2xx response uses a single error envelope with one of four codes | `app/routes.py:41-57`, `app/main.py:93-96` |

## Business Rules Observed in the Code

These are the domain invariants a future change must preserve; each is
enforced somewhere in the scanned source.

| Rule | Statement | Evidence |
|---|---|---|
| BR-1 | A label is exactly one of `positive`, `negative`, `neutral` | `app/sentiment.py:16` (`LABELS`); SQL `CHECK` in `app/db.py:18-30` |
| BR-2 | `probabilities` is a JSON **object keyed by label**, never an array; every label has an entry | `app/models.py:79-93` (`from_row`), `app/openrouter_client.py:194-229` (all three labels required) |
| BR-3 | `created_at` is an ISO 8601 UTC timestamp ending in `Z` | `app/repository.py:33-35` (`format_timestamp`) |
| BR-4 | `intensity` is signed and clamped to −1..1 | `app/openrouter_client.py:72-73,232-250`; fixed per-label values in `app/dummy_client.py:56-66` |
| BR-5 | Empty or whitespace-only text is rejected with `422 INVALID_TEXT` and **nothing is written** | `app/service.py:95-103`, `app/routes.py:192-199` |
| BR-6 | `limit` must be `>= 1`; `0`, `-1` or a non-number is `422 VALIDATION_FAILED` — never silently clamped | `app/routes.py:102-108`, `README.md` (HTTP surface) |
| BR-7 | With no configuration at all the app runs the offline engine (an offline default, not an error) | `app/config.py:93-112` |
| BR-8 | Selecting live mode without a key is **not** a startup failure: the app starts unconnected on the offline engine | `app/config.py:111-123` (rule 5, supersedes the earlier fail-fast rule) |
| BR-9 | The API key never appears in a repr, a log line or any response body | `app/config.py:27,47-52`; `app/session_auth.py:125-138`; `app/openrouter_client.py:93-95`; asserted by tests |
| BR-10 | The server binds `127.0.0.1` only | `app/main.py:35-36` (`HOST`, `PORT`) |
| BR-11 | A rejected credential is dropped, so the app falls back to the offline engine instead of retrying a dead key | `app/routes.py:211-221` (`handle_auth_error`), `app/session_auth.py:240-244` (`expire`) |
| BR-12 | Dummy-mode rows are deterministic and carry no real signal: fixed probability triples and fixed intensity per label | `app/dummy_client.py:56-66,81-106` |

## Actors and Stakeholders

| Actor | Interest | Evidence |
|---|---|---|
| **Local user** (single human operator) | Submit text, read the result and history, optionally connect the live model | `app/static/index.html` (form, result panel, history, indicator), `README.md` |
| **Operator/developer** | Install, run (`uvicorn app:app`), test (`pytest`), configure one local TOML file | `README.md`, `pyproject.toml` |
| **OpenRouter** (external service) | Supplies the authorization endpoint, the key-exchange endpoint and the live Decisions API | `app/session_auth.py:40-41`, `app/openrouter_client.py:30` |
| **AI-DLC record** (requirements source) | Prior intent `260929-sentiment-analysis` supplied requirement ids `FR1.1`–`FR5.5` and `NFR1`–`NFR6`, cited throughout the module docstrings | `app/*.py` docstrings, e.g. `app/config.py:1-9`, `app/service.py:1-8` |

The active v1 intent (`260930-sentiment-v1`) is the intent this CodeKB serves.

## Intent Alignment — Where the Code Diverges from v1

The code is not a blank slate: it already implements the v1 core, and the
divergence is **drift, not absence** (developer scan, "Handoff Summary" and
"Technical Debt Signals").

| # | Divergence | Code evidence | v1 intent says |
|---|---|---|---|
| D-1 | An in-app OpenRouter PKCE authorization flow exists, with a session credential in process memory, four `/auth/*` routes and 24 of the 52 tests | `app/session_auth.py`, `app/routes.py:125-167`, `app/static/index.html:105-116`, `app/static/app.js:130-175`, `tests/test_session_auth.py`, `tests/test_auth_routes.py` | "no auth", key supplied manually in the gitignored `config.local.toml` |
| D-2 | Live mode with a missing key starts **unconnected on the offline engine** (config rule 5) | `app/config.py:111-123`, `tests/test_config.py:70-85` | live mode with a missing key should fail with a clear error naming the file to fill in |
| D-3 | Client class names are `DummyClient` / `OpenRouterClient` | `app/dummy_client.py:75`, `app/openrouter_client.py:76` | names them `DummySentimentClient` / `OpenRouterJevSentimentClient` |
| D-4 | `app/main.py:33-34` still says "No authentication, session or CORS middleware exists anywhere in this app" | `app/main.py:33-34` | stale comment predating the auth flow |

D-1 and D-2 are the material scope questions for the next stages; D-3 and D-4
are naming/documentation drift with no runtime effect.

## Traceability — Capability to Prior-Intent Requirement Ids

The docstrings of `app/` cite the prior intent's ids directly, so the code's own
claim of coverage is readable from the source:

| Capability | Requirement ids cited in code |
|---|---|
| Configuration and mode resolution | `FR1.1`–`FR1.6`, `NFR1`, `NFR2` (`app/config.py:1-9`) |
| Engine interface and the two engines | `FR2.1`–`FR2.7`, `NFR3`, `NFR5` (`app/sentiment.py:1-8`, `app/dummy_client.py:1-7`, `app/openrouter_client.py:1-12`) |
| Persistence and schema | `FR3.1`–`FR3.4`, `NFR6` (`app/db.py:1-7`, `app/repository.py:1-10`) |
| HTTP surface, page and health | `FR4.1`–`FR4.7` (`app/routes.py:1-6`, `app/main.py:1-7`) |
| Offline-first testing | `FR5.5`, `NFR1` (`app/main.py:1-7`, `app/openrouter_client.py:10-12`) |

Carry these ids forward, or the docstring references dangle (developer scan,
"Risks / follow-up").
