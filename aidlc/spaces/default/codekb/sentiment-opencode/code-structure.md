# Code Structure — `sentiment-opencode`

> Synthesized from the developer scan at HEAD
> `4eb9b74c4197114181dab641c177c569f2058c24` and verified against the source.

## Repository Layout

The repo is an unrecorded project-root repository: the application lives at the
workspace root, not in a subdirectory.

```
.
├── app/                     # the one installable package (flat, by layer)
│   ├── __init__.py          # re-export shim: `from app.main import app`
│   ├── main.py              # create_app() factory, lifespan, HOST bind
│   ├── config.py            # Settings + load_settings(), mode resolution
│   ├── models.py            # AnalyzeRequest, AnalysisRecord, RECORD_FIELDS
│   ├── db.py                # sqlite3 connect/init, DDL, in-place migration
│   ├── repository.py        # insert_analysis(), list_analyses()
│   ├── sentiment.py         # LABELS, SentimentResult, SentimentClient, validate_result
│   ├── dummy_client.py      # offline keyword engine (default)
│   ├── openrouter_client.py # live Jev/OpenRouter engine, injected transport
│   ├── session_auth.py      # in-app PKCE flow, process-memory credential
│   ├── service.py           # analyze_text(), get_client(), effective_connection()
│   ├── routes.py            # page, /v1 API, /auth routes, error envelope
│   └── static/
│       ├── index.html       # the page + connection indicator
│       └── app.js           # fetch/render/history/indicator
├── tests/                   # pytest suite (10 test modules + conftest)
├── pyproject.toml           # metadata, deps, pytest/coverage/ruff config
├── config.example.toml      # committed placeholder config
├── README.md                # setup, run, modes, HTTP surface, limitations
├── AGENTS.md                # AI-DLC harness onboarding (from AI-DLC)
├── opencode.json            # opencode harness config (not application code)
└── .gitignore               # AI-DLC + application ignore rules
```

## Package Organization

A single installable package `app` (`pyproject.toml:36`, `packages = ["app"]`),
organised **flat by layer**, not feature-sliced. The import graph is acyclic and
one-directional:

```
leaves:  config, models, db, sentiment
adapters: repository, dummy_client, openrouter_client
service:  service
edge:     routes
assembly: main -> __init__
```

`app/__init__.py` exists only so `uvicorn app:app` resolves; importing any
submodule builds the FastAPI application at import time as a side effect
(`app/main.py:103`).

## File Classification

| File | Lines | Category | Responsibility |
|---|---:|---|---|
| `app/__init__.py` | 10 | Configuration (assembly shim) | Re-export `app` for `uvicorn app:app` |
| `app/main.py` | 103 | Configuration / composition root | App factory, lifespan, router mounts, exception handlers, HOST/PORT |
| `app/config.py` | 151 | Configuration | `Settings` dataclass + six-rule mode resolution; key redaction |
| `app/models.py` | 133 | Model/Entity | `AnalyzeRequest`, `AnalysisRecord` (+ `to_dict`/`from_row`), `RECORD_FIELDS`, `undeclared_body_fields` |
| `app/db.py` | 234 | Repository/DAO + Migration | Connection, DDL, schema version, in-place migration |
| `app/repository.py` | 79 | Repository/DAO | `insert_analysis`, `list_analyses`, timestamp formatting |
| `app/sentiment.py` | 84 | Model/Entity + Interface | `LABELS`, `SentimentResult`, engine exceptions, `SentimentClient` Protocol, `validate_result` |
| `app/dummy_client.py` | 101 | Service/adapter | Deterministic offline keyword engine |
| `app/openrouter_client.py` | 232 | Service/adapter | Live Jev engine over one injected HTTP transport |
| `app/session_auth.py` | 259 | Service (infrastructure) | PKCE flow, in-memory session credential |
| `app/service.py` | 132 | Service/UseCase | Input validation, engine resolution, per-text orchestration |
| `app/routes.py` | 282 | Controller/Handler + Middleware | Page, `/v1` API, `/auth` routes, exception handlers, error envelope |
| `app/static/index.html` | 193 | Static/Asset | Page markup and `data-testid` hooks |
| `app/static/app.js` | 201 | Static/Asset | Fetch/render/history/indicator behaviour |
| `tests/conftest.py` | 165 | Test (harness) | In-process ASGI caller, offline guard, tmp fixtures |
| `tests/test_*.py` (10 files) | 2,138 | Test | Behavioural unit and API-level tests |

No `utils.py` or `helpers.py`: a pure helper lives in the module that owns the
concept (`format_timestamp`, `create_code_verifier`, `code_challenge_for`).

## Code Patterns

- **Stdlib-only contracts.** `app/models.py` and `app/sentiment.py` use
  `dataclasses`/`Protocol`, not pydantic; FastAPI accepts a plain dataclass body.
  This keeps the validation library out of `app/` (NFR3).
- **One Protocol, injected adapters.** Engines implement
  `SentimentClient.analyze`; the concrete engine is resolved only in
  `service.get_client`, and the live module is imported *lazily* inside
  `_live_client` (`app/service.py:93-101`) so the offline path never loads it.
- **Dependency injection via FastAPI `Depends`.** `get_settings`,
  `get_session_auth` and `get_connection` read from `request.app.state`; tests
  inject `create_app(settings, session_auth)`.
- **Injectable seams for determinism.** `analyze_text(..., now=None)`,
  `insert_analysis(..., now=None)`, `SessionAuth(exchanger, clock)` and
  `OpenRouterJevSentimentClient(transport, timeout)` let tests run offline.
- **Domain errors at the core, HTTP mapping at the edge.** `InvalidTextError`,
  `LiveKeyMissingError`, `SentimentEngineError`, `SentimentAuthError`,
  `AuthExchangeError`, `ConfigError` are raised in `app/` modules and mapped to
  the envelope in `app/routes.py` / `app/main.py`.
- **Single connection owner.** Only the HTTP layer touches the `sqlite3` driver
  and the connection lifecycle (`get_connection`, `app/routes.py:79-85`);
  repository and service receive a connection.
- **Parameterised SQL only.** Every statement uses `?` placeholders; DDL text
  lives in named module constants.
- **Lazy typing-only imports.** `app/repository.py` imports `SentimentResult`
  under `TYPE_CHECKING` (`# pragma: no cover`), so persistence has no runtime
  engine dependency.
- **Key-redacting `__repr__`.** `Settings`, `SessionCredential` and
  `OpenRouterJevSentimentClient` all override `__repr__`/`__str__`.

## Naming and Style Conventions

- Modules/functions `snake_case`; classes/type aliases `PascalCase`
  (`Mode = Literal[...]`); constants `UPPER_CASE`, semantic ones carrying `#:`
  doc comments.
- Helpers and state are underscore-prefixed (`_live_client`, `_read_choice`,
  `_pending`, `_configure_logging`, `_INSERT_SQL`, `_WORD`).
- Tests are `tests/test_<module>.py` with `test_<behaviour>` names.
- Every substantive module opens with a docstring naming one responsibility and
  usually citing prior-intent requirement ids.
- Full type annotations and `from __future__ import annotations` in all
  substantive modules.
- Imports grouped stdlib / third-party / `app.*`; 4-space indent, double quotes,
  trailing commas. `ruff` is configured (`line-length = 100`, security rules `S`)
  and reports clean at HEAD.
- Error handling: no bare `except`; every handler names a specific type and every
  wrapping raise uses `from exc`; `print()` never appears in `app/`.

## Intent-Relevant Structural Notes (CSV Import/Export)

- Routes are mounted from two `APIRouter`s: `v1_router` (`prefix="/v1"`,
  `app/routes.py:44,121`) and the unversioned `router` (`app/routes.py:118`).
  New bulk endpoints belong on `v1_router` as additive sub-paths under
  `/analyses`.
- There is no CSV, multipart or `import_id` code anywhere at HEAD.
- `app/static/app.js` is the only JavaScript and is not executed by the suite;
  a CSV UI change would extend the served-markup contract only.
