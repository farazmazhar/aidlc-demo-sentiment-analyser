# Tech Stack Decisions — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-requirements` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **This file records selections, it does not propose alternatives.** The
> technology is **fixed by the brownfield baseline** (Python, FastAPI, `uvicorn`,
> SQLite, standard library only), established by the running code and the CodeKB,
> with `C-6` capping *declared* runtime dependencies at two. Each entry below
> states the selection, the evidence that fixed it, and the consequence for this
> unit — not a menu of candidates.

## Selections

| Layer | Selection | Fixed by | Rationale / consequence for this unit |
|---|---|---|---|
| **Language** | **Python**, `>=3.11` declared; `ruff` `target-version` matched to `requires-python` | `pyproject.toml:10`; `technology-stack.md` §Languages; `FR7.8`; team rule | All new analytics code is Python. No second language. `from __future__ import annotations` in every new module. |
| **HTTP framework** | **FastAPI** (declared floor `>=0.110`) | Running code; `technology-stack.md` §Runtime Framework; `C-4` | The `/v2` router is a FastAPI `APIRouter(prefix=V2_PREFIX)`; both handlers land on it (`D3` extension seam). FastAPI's binding enforces `limit`'s `ge=1` and ignores unknown query params (a `limit` on the summary is ignored, `contract-summary.md` §5 P8). |
| **ASGI server** | **`uvicorn`** (declared floor `>=0.27`) | Running code; `technology-stack.md` | The run path is `uvicorn app:app --reload`. The loopback enforcement (`NFR2.4`) changes the run path to consume the `HOST` constant; no server swap. |
| **Storage engine** | **SQLite**, bundled with CPython (3.53.4 verified) | `technology-stack.md` §Database; `C-1` | Aggregates use `GROUP BY`, `strftime('%Y-%m-%d', …)` and parameter-bound statements — all verified available in the bundled library. No new dependency. |
| **DB driver** | **stdlib `sqlite3`** | `technology-stack.md` | No third-party driver. The read module or the HTTP edge binds values with `?` placeholders (`NFR2.3`). |
| **Data shapes (request/response)** | **stdlib `dataclasses`** — never `pydantic` in `app/` | `team.md` §Code Style; `NFR6`; `A1` | The analytics wire payloads are plain dicts built from dataclasses, following the existing no-response-model convention; the contract is pinned by hand-written constants in tests (`TD-8`) rather than a response model. |
| **Validation library** | **None added** — the standard-library plain-data shapes | `team.md` §Conventions; `FR1.5`; `NFR6` | Query-parameter validation stays with FastAPI's own binding plus explicit route checks; no third-party validator. |
| **Linter / formatter** | **`ruff` 0.16.9**, explicit rule set `["E","F","W","I","N","UP","S","B","C4","SIM"]` | `pyproject.toml`; `technology-stack.md` §Tooling; team rule | New modules must pass `ruff check` and `ruff format --check`. `TID251` `banned-api` (`FR7.5`) turns a layer-boundary breach into a lint failure. |
| **Test runner** | **`pytest`** (floor `>=8`) with **`pytest-cov`** (`>=5`) | `pyproject.toml`; `technology-stack.md` | The `FR8.9` fixture and the `FR8.2`/`FR8.4` tests run under pytest; the 80 % whole-application line-coverage floor applies on every run (`addopts`). |
| **Orchestration / scheduling** | **None** | `C-5`; `technology-stack.md` §Build System ("Absent") | No Makefile/Docker/CI is *present*; `FR7.2` adds a platform-neutral verification script, owned by the packaging unit, not a change to this unit's stack. |

## Cap and dependency posture

- **The cap is `C-6`: the project caps *declared* runtime dependencies at two**
  (`fastapi`, `uvicorn`), enforced by `tests/test_config.py` asserting the declared
  list. Transitive distributions resolved behind them are expected and do not
  breach the cap (project rule, affirmed 2026-10-02).
- **This unit declares no new runtime dependency.** The analytics layer is stdlib
  and existing-dependency only: it introduces no HTTP client, no validator, no
  chart library, no task scheduler. The instrument for that claim is the
  dependency-cap assertion staying green with an unchanged declared list.
- **Transitive note.** `fastapi` hard-requires `opentelemetry-api`; nothing in
  `app/` imports it and no SDK/exporter is installed, so there is no egress
  (`A5`). This is unchanged by the analytics work and requires no action here.

## Standard-library modules this unit relies on (already in use)

| Module | Where it lands | Source |
|---|---|---|
| `sqlite3` | aggregate reads + the `FR8.9` trace hook | `technology-stack.md` §Standard Library |
| `datetime` / `datetime.UTC` | UTC day resolution and bucketing | same |
| `collections` | term counting/ranking (stdlib Counter or plain dict) | same |
| `re` / string membership | term tokenisation is delegated to `u2-term-extraction` (`app/terms.py`); this unit consumes it, does not re-implement it | `contract-summary.md` C3 |
| `logging` | module logger for the failure path (`NFR8.1`) | same |

## What is deliberately *not* chosen (and why)

These are not alternatives under consideration — they are named so a reader does
not mistake their absence for an oversight:

- **`pydantic` in `app/`** — forbidden by the two-package cap and the standing
  convention; request/record shapes stay stdlib dataclasses (`A1`, `NFR6`).
- **An HTTP client library** — forbidden by `C-6`; this unit adds no outbound call
  anyway (`NFR2.2`), and the contract fixes "no retry, no timeout" because there
  is nothing to call.
- **A chart/UI library** — forbidden by `C-6`; the view uses native HTML and the
  page's existing classes (`FR6.6`).
- **A browser-automation test dependency** — forbidden by `C-6`; the view's
  behaviour is untested by design (`NFR7`; `TD-11`), and real served markup is
  asserted instead (`BR6.6`).

## Open items carried by the technology, not decided here

- **Lockfile format and install command** (`FR7.1`) — unresolved upstream; a
  packaging-unit obligation, not this unit's.
- **Secret scanner and dependency-audit tool** (`FR7.3`) — unresolved upstream;
  packaging-unit obligation.
- **Type checker** — absent by decision (`technology-stack.md` §Type checking); no
  new one is selected here.
