# Dependencies — `very-cool-sentiment-analysis`

> Derived from the developer scan
> (`inception/reverse-engineering/developer-scan.md`) and verified against
> `pyproject.toml` and the installed distribution metadata in `./.venv`.

## 1. External Dependencies (declared)

`pyproject.toml` is the single manifest; `very_cool_sentiment_analysis.egg-info/requires.txt`
mirrors it and adds nothing.

| Scope | Package | Declaration | Purpose |
|---|---|---|---|
| runtime | `fastapi` | `>=0.110` | ASGI app, routing, dependencies, static files, exception handlers |
| runtime | `uvicorn` | `>=0.27` | Development ASGI server; never imported by application code |
| dev (`dev` extra) | `pytest` | `>=8` | Test framework and runner |

Nothing else is declared. There is no lockfile, no `requirements.txt`, no
constraints file, and no vendored dependency.

## 2. External Dependencies (installed, including transitive)

Read from `*.dist-info` directory names in `./.venv`
(`.venv/lib/python3.14/site-packages/`):

| Package | Installed | Required by | Type |
|---|---|---|---|
| `fastapi` | 0.141.1 | direct (runtime) | runtime |
| `uvicorn` | 0.54.0 | direct (runtime) | runtime |
| `starlette` | 1.7.0 | fastapi | transitive |
| `pydantic` | 2.13.5 | fastapi | transitive (never imported by `app/`) |
| `pydantic_core` | 2.46.5 | pydantic | transitive |
| `anyio` | 4.15.1 | starlette | transitive |
| `annotated_types` | 0.8.0 | pydantic | transitive |
| `annotated_doc` | 0.0.5 | fastapi | transitive |
| `typing_extensions` | 4.16.0 | fastapi/pydantic | transitive |
| `typing_inspection` | 0.4.4 | pydantic | transitive |
| `click` | 8.5.0 | uvicorn | transitive (CLI) |
| `h11` | 0.16.0 | uvicorn | transitive |
| `idna` | 3.20 | anyio/uvicorn | transitive |
| `pytest` | 9.1.1 | direct (dev) | dev |
| `pluggy` | 1.6.0 | pytest | dev, transitive |
| `iniconfig` | 2.3.0 | pytest | dev, transitive |
| `packaging` | 26.3 | pytest | dev, transitive |
| `pygments` | 2.21.0 | pytest | dev, transitive |
| `very_cool_sentiment_analysis` | 0.1.0 | this project | editable install |
| `pip` | 26.2.1 | toolchain | not an application dependency |

Worth noting for any later stage: the installed set contains **no HTTP client
library**. `httpx` is deliberately absent, which is why the test harness
hand-rolls an in-process ASGI caller (`tests/conftest.py:5-9`, `README.md`
"Notes").

## 3. Package-to-Package Dependency Edges

| Consumer | Depends on | Nature |
|---|---|---|
| `app` | `fastapi` | runtime, imported by `app/main.py`, `app/routes.py` |
| `app` | the Python standard library | `tomllib`, `sqlite3`, `urllib`, `json`, `hashlib`, `base64`, `secrets`, `threading`, `time`, `logging`, `re`, `dataclasses`, `pathlib`, `typing`, `datetime`, `contextlib`, `collections.abc` |
| `app` | `uvicorn` | **declared but not imported** — used only as the run command |
| `tests` | `pytest` | test framework |
| `tests` | `app` | imports modules directly and drives the app in-process |
| `tests` | `socket`, `asyncio`, `json` | stdlib harness plumbing |
| `app` | `pydantic` | **none** — deliberately avoided; FastAPI uses it internally (`app/models.py:1-11`) |

## 4. Internal Cross-Component Dependencies

Component names match `component-inventory.md`.

```
Application Assembly ---------> Configuration and Settings
Application Assembly ---------> Persistence and Schema
Application Assembly ---------> HTTP API Surface
Application Assembly ---------> Analysis Orchestration
Application Assembly ---------> Sentiment Engine Interface
Application Assembly ---------> Session Authorization

HTTP API Surface -------------> Persistence and Schema
HTTP API Surface -------------> Configuration and Settings
HTTP API Surface -------------> Record and Request Contracts
HTTP API Surface -------------> Analysis Orchestration
HTTP API Surface -------------> Sentiment Engine Interface
HTTP API Surface -------------> Session Authorization

Analysis Orchestration -------> Configuration and Settings
Analysis Orchestration -------> Offline Dummy Engine
Analysis Orchestration -------> Record and Request Contracts
Analysis Orchestration -------> Persistence and Schema
Analysis Orchestration -------> Sentiment Engine Interface
Analysis Orchestration -------> Session Authorization
Analysis Orchestration -------> Live OpenRouter Engine   (lazy import, live path only)

Persistence and Schema -------> Record and Request Contracts
Persistence and Schema -------> Sentiment Engine Interface  (TYPE_CHECKING only)

Offline Dummy Engine ---------> Sentiment Engine Interface
Live OpenRouter Engine -------> Sentiment Engine Interface

Configuration and Settings ---> (none internal)
Record and Request Contracts -> (none internal)
Sentiment Engine Interface ---> (none internal)
```

Properties of this graph:

- **Acyclic.** No module imports a module that imports it back; the developer
  scan verified the same shape at module granularity.
- **Two legal seams only.** Engines are reachable solely through
  `SentimentClient`, and engine construction happens solely in
  `service.get_client()` (`app/service.py:60-82`).
- **One lazy edge.** `analysis orchestration -> live openrouter engine` is an
  import inside the function, so the offline path never loads the live module
  (`app/service.py:80-82`).
- **Typing-only edge.** `persistence -> sentiment engine interface` exists under
  `TYPE_CHECKING` and imposes no runtime coupling
  (`app/repository.py:20-21`).

## 5. Service Dependencies (runtime, external)

| Dependency | Direction | Failure behaviour today | Evidence |
|---|---|---|---|
| `https://openrouter.ai/api/alpha/decisions` | outbound (live mode) | HTTP 401/403 drops the credential and answers `502 AUTH_EXPIRED`; any other failure answers `502 SENTIMENT_ENGINE_ERROR`; nothing is persisted | `app/openrouter_client.py:122-190`, `app/routes.py:202-221` |
| `https://openrouter.ai/api/v1/auth/keys` | outbound (connect flow) | Raises `AuthExchangeError`, expires the flow and redirects to `/?auth=failed` | `app/session_auth.py:78-121`, `app/routes.py:146-159` |
| `https://openrouter.ai/auth` | browser redirect | No server-side call; a failed authorization simply never returns a code | `app/session_auth.py:163-180` |
| Local filesystem: `data/` and `data/sentiment.db` | in-process | The parent directory is created on demand; no other setup step | `app/db.py:51-63` |
| Local filesystem: `config.local.toml` | in-process, optional | Absence is the documented offline default; invalid TOML is a startup `ConfigError` | `app/config.py:60-71,93-112` |

No retry, backoff, circuit breaker or rate limiter is implemented anywhere: a
failed live call fails the request. The only resilience behaviour is the
credential drop on 401/403 (`app/routes.py:211-221`).

## 6. Dependency Policy Constraints to Preserve

1. **The cap is a requirement, not a preference** (NFR3): `fastapi` + `uvicorn`
   at runtime, `pytest` for dev, nothing else. Adding an HTTP client, an ORM, a
   settings library, a template engine or a browser-automation package would
   break the stated constraint *and* the existing test harness assumptions
   (no `httpx`, no network).
2. **`app/` must not import pydantic.** Request validation is FastAPI's
   internal concern; the record shape lives in `app/models.py`
   (`app/models.py:1-11`).
3. **The offline test path must stay importable without the live client.**
   `app/openrouter_client.py` must remain reachable only through the lazy
   import in `app/service.py:80-82`.
4. **Version floors, not pins.** `fastapi>=0.110`, `uvicorn>=0.27`,
   `pytest>=8`; this checkout resolves to 0.141.1 / 0.54.0 / 9.1.1.
