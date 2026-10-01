# Dependencies — `sentiment-opencode`

> Synthesized from the developer scan at HEAD
> `4eb9b74c4197114181dab641c177c569f2058c24`; external versions from the
> repo-local `.venv`, internal graph verified against the source imports.

## External Dependencies

### Direct runtime (declared in `pyproject.toml`, capped at two)

| Package | Declared | Installed | Purpose |
|---|---|---|---|
| `fastapi` | `>=0.110` | `0.142.2` | HTTP framework, routing, request validation, exception handling |
| `uvicorn` | `>=0.27` | `0.54.0` | ASGI server (the only documented run path: `uvicorn app:app`) |

The cap is asserted by `tests/test_config.py:141-160`.

### Transitive runtime (pulled by FastAPI; not imported by `app/`)

| Package | Installed | Role |
|---|---|---|
| `starlette` | `1.7.0` | FastAPI's ASGI layer (routing, responses, `StaticFiles`) |
| `pydantic` | `2.13.5` | Request/response validation FastAPI uses internally |
| `pydantic_core` | `2.46.5` | Pydantic's compiled core |
| `anyio` | `4.15.1` | Provides the worker-thread pool FastAPI uses for sync endpoints (relevant to R-01) |

`app/` does not import any of these directly; request and record shapes are
stdlib dataclasses.

### Development tools (the `dev` extra; never in the runtime list)

| Package | Declared | Installed | Purpose |
|---|---|---|---|
| `pytest` | `>=8` | `9.1.1` | Test runner |
| `pytest-cov` | `>=5` | `7.1.0` | Coverage plugin enforcing the 80% floor |
| `coverage` | (via pytest-cov) | `7.16.2` | Coverage measurement |
| `ruff` | `>=0.6` | `0.16.9` | Lint + format (includes security rules `S`) |

### Build-time

| Package | Declared | Purpose |
|---|---|---|
| `setuptools` | `>=68` | PEP 517 build backend (`setuptools.build_meta`) |

There is no `requirements.txt`, lockfile, constraints file, hash pinning or
update bot; each install resolves the newest compatible version of the declared
floors and roughly a dozen transitive packages. No dependency audit or secret
scanner exists.

### Deliberately absent (matters for CSV work)

`python-multipart`, `httpx`, `requests`, `aiofiles` — none installed. A
`multipart/form-data` upload would require adding `python-multipart` and would
break the runtime-dependency cap. CSV must be parsed with the stdlib `csv`
module from a raw or JSON-wrapped body.

## Internal Cross-Package Dependencies

Single installable package `app` (`packages = ["app"]`). Import graph is acyclic
and points one way (leaves → adapters → service → routes → assembly):

```
app/__init__.py          -> app.main
app/main.py              -> app.db, app.config, app.routes, app.sentiment, app.service, app.session_auth
app/routes.py            -> app.db, app.config, app.models, app.repository, app.sentiment, app.service, app.session_auth
app/service.py           -> app.config, app.dummy_client, app.models, app.repository, app.sentiment, app.session_auth
                            (+ app.openrouter_client, LAZY import inside _live_client)
app/repository.py        -> app.models  (+ app.sentiment under TYPE_CHECKING only)
app/db.py                -> app.models (UNKNOWN_PROVIDER only)
app/dummy_client.py      -> app.sentiment
app/openrouter_client.py -> app.sentiment
app/config.py            -> (stdlib only)
app/models.py            -> (stdlib only)
app/sentiment.py         -> (stdlib only)
app/session_auth.py      -> (stdlib only)
app/static/app.js        -> HTTP API Surface over HTTP only (no imports)
tests/*                  -> app.* (imports) and the in-process ASGI application
```

Key properties:

- **No cycles.** No two modules import each other.
- **Lazy edge.** `app/service.py:93-101` imports `app.openrouter_client`
  *inside* `_live_client`, so the offline path never loads the live module
  (NFR1).
- **Typing-only edge.** `app/repository.py:20-21` imports `SentimentResult`
  under `TYPE_CHECKING` with `# pragma: no cover`, so persistence has no runtime
  dependency on the engine.
- **Leaf isolation.** `config.py`, `models.py` and `sentiment.py` import nothing
  from `app/`; `session_auth.py` is also internal-dependency-free.
- **Widest fan-out.** `app/routes.py` depends on six internal modules — the
  single biggest coupling surface.

## Intent-Relevant Dependency Notes (CSV Import/Export)

- An `import_id` column added to the persisted record must be threaded through
  `app/models.py` (`RECORD_FIELDS`, `AnalysisRecord`, `to_dict`, `from_row`) and
  `app/db.py` (`CREATE_ANALYSES_TABLE`, `ANALYSES_COLUMNS`, `_V1_NOT_NULL_COLUMNS`,
  `_ADD_COLUMN_SQL`, `_COPY_ROWS_INTO_V1_TABLE`, `SCHEMA_VERSION`) — plus the
  independent test-local field set in `tests/test_routes.py:27-36`.
- The migration rebuild copies an **explicit** column list; forgetting
  `import_id` there loses the column on every rebuild.
- Any new CSV endpoint depends only on the existing components (routes →
  service → repository/db), so the import graph stays acyclic.
