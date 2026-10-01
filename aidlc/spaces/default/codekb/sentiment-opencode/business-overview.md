# Business Overview — `sentiment-opencode`

> Synthesized by the architect (link 2 of 2) from the developer code scan at
> HEAD `4eb9b74c4197114181dab641c177c569f2058c24`; every claim is grounded in
> that scan and re-checked against the source. See
> `reverse-engineering-timestamp.md` for the run record and scope.

## Business Domain

Local, single-user text-sentiment analysis. The system is a small self-contained
web app that classifies a short piece of text into one of three sentiment labels
and keeps a local history. It is explicitly **not** a multi-tenant service: there
is no account model, no authentication of its own, no cloud deployment and no
notion of a second user. The only credential in the system is the operator's own
OpenRouter API key, used outbound only when the live engine is active.

## Purpose

Give one person a private, loopback-only way to answer "what is the sentiment of
this text?" — with a typed, explainable answer — while defaulting to a fully
offline, deterministic engine so the app (and its entire test suite) works with
no network and no key.

## Key Functionality

| Capability | What it does | Where it lives |
|---|---|---|
| Analyse one text | Accepts `{"text": "..."}`, resolves the engine, stores the result, returns the stored record | `POST /v1/analyze`, `app/routes.py:130` |
| Browse history | Returns stored analyses newest-first, default page size 50 | `GET /v1/analyses`, `app/routes.py:153` |
| Engine-mode resolution | Chooses session credential → configured live key → offline dummy, from an optional local TOML file | `app/config.py`, `app/service.py:72` |
| Live connection (in-app) | PKCE (S256) sign-in to OpenRouter; the key lives in process memory only | `app/session_auth.py`, `/auth/*`, `app/routes.py:189` |
| Health / connection status | Reports active mode, `connected` flag and, only when disconnected, a reason | `GET /v1/health`, `GET /auth/status` |
| Local persistence | Creates and migrates one SQLite file on startup; stores records and schema version | `app/db.py`, `app/repository.py` |
| Page | Single HTML page: submit form, result panel, history, connection indicator | `app/static/index.html`, `app/static/app.js` |

## Capabilities Deliberately Absent

Recorded so later stages do not mistake an omission for an oversight:

- **No bulk or CSV surface.** A grep for `csv|import_id|bulk|multipart|upload`
  across `app/`, `tests/`, `README.md` and `pyproject.toml` returns nothing at
  HEAD. The `import_id` column, `POST /v1/analyses/import` and
  `GET /v1/analyses/export` described by the active intent do **not** exist yet.
- **No retention or delete endpoint.** Stored text can only be removed by
  deleting the database file.
- **No multi-user, no auth of its own, no CORS and no CSP.** Loopback binding is
  the entire access-control story.
- **No export/import of any kind** and no OpenAPI/Swagger artifact committed
  (FastAPI serves a runtime schema only).

## Domain Concepts and Glossary

| Concept | Meaning | Source |
|---|---|---|
| Analysis | One text plus the engine's typed decision, stored as a row | `app/models.py` |
| `AnalysisRecord` | The stored/returned record: `id, text, label, probabilities, confidence, model, provider, created_at` | `app/models.py:75-108` |
| `SentimentResult` | An engine's typed decision: `label, probabilities, confidence, model, provider` | `app/sentiment.py:23-36` |
| `SentimentClient` | The one interface every engine implements (`analyze(text) -> SentimentResult`) | `app/sentiment.py:78-84` |
| Label | One of `positive`, `negative`, `neutral` | `app/sentiment.py:20` |
| `provider` | Which engine produced a row: `offline`, `openrouter`, or the migration sentinel `unknown` | `app/dummy_client.py:66`, `app/openrouter_client.py:46`, `app/models.py:41` |
| Mode | What the app *intends* to use: `offline` or `live` (a live request with no key still records `live`) | `app/config.py:30,63` |
| Connection source | Where the live credential came from: `session`, `config`, or none | `app/service.py:56-61` |
| Session credential | An OpenRouter key obtained in-app, held in process memory, never written to disk | `app/session_auth.py:123-136` |
| `import_id` *(proposed)* | The shared grouping key the active intent adds to bulk-imported rows — not present at HEAD | active intent description |

## Business Rules in Force

- Text that is missing, empty or whitespace-only is refused before the engine is
  called and before anything is written (`app/service.py:104-113`).
- A stored label is always one of the three allowed labels, enforced both by the
  engine validator and by a SQL `CHECK` constraint (`app/db.py:40`).
- With no config file the app runs the offline dummy engine; live mode must be
  explicitly requested and needs a usable key (`app/config.py:114-151`).
- The app is loopback-only and unauthenticated by design; a non-loopback bind or
  a change to the authentication posture requires a fresh threat model
  (`project.md`, Mandated).
- Every failure the application itself raises travels through one error envelope
  `{code, message}`; framework routing errors keep FastAPI's `{"detail": ...}`
  (`app/routes.py:56-66`, `project.md`, Mandated).
- A real credential never appears in the repository, logs, responses or any
  `aidlc/` artifact; the only permitted homes are gitignored
  `config.local.toml` and process memory (`project.md`, Forbidden).

## Operational Context

- Durable state is exactly one gitignored SQLite file, `data/sentiment.db`.
  At HEAD it is schema `version = 2` with **0 rows** (read-only inspection).
- A fresh checkout needs no manual setup: the parent directory, the schema and
  the schema-version row are created on first startup (`app/db.py:121-159`).
- "Deployment" is a localhost checkout; a commit is the release. One process on
  `127.0.0.1` (`README.md:31-37`).

## Intent Relevance (CSV Bulk Import / Export)

The active intent's whole surface is a natural extension of three existing,
clean seams, and the repository already contains the exact insertion points:

1. **Engine seam** — `SentimentClient.analyze` (`app/sentiment.py:78-84`) with
   the offline `DummySentimentClient` (`app/dummy_client.py:71-101`) selected in
   the single factory `service.get_client` (`app/service.py:72-90`). The
   per-text orchestration a bulk loop should call is
   `service.analyze_text(client, connection, text, now=None)`
   (`app/service.py:116-132`), which persists via
   `repository.insert_analysis` (`app/repository.py:40-69`).
2. **Route seam** — `v1_router` is mounted with `prefix="/v1"`
   (`app/routes.py:44,121`); `POST /v1/analyses/import` and
   `GET /v1/analyses/export` are additive sub-paths beside the existing
   `GET /v1/analyses`.
3. **Schema seam** — `CREATE_ANALYSES_TABLE` (`app/db.py:36-48`), the pinned
   `ANALYSES_COLUMNS` tuple (`app/db.py:58-68`), `_V1_NOT_NULL_COLUMNS`
   (`app/db.py:72-74`), `_ADD_COLUMN_SQL` (`app/db.py:87-97`) and the explicit
   rebuild copy list (`app/db.py:106-111`); `SCHEMA_VERSION = 2`
   (`app/db.py:32`) must bump for an added `import_id`.

The design constraints the intent inherits — the two-runtime-dependency cap
(`python-multipart` is **not** installed), the four hand-written copies of the
record contract, the undefined batch-failure semantics, and the offline test
harness — are inventoried in `architecture.md` and `code-quality-assessment.md`
and must be honoured by Requirements Analysis and Construction.
