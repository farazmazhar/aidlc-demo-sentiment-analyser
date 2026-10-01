# Requirements — very-cool-sentiment-analysis

Source of record for this stage: `ideation/intent-capture/intent-statement.md` (the approved intent)
and `requirements-analysis-questions.md` (the confirmed answers, cited below as `[Q1]`–`[Q5]`).
`[desc]` cites the authoritative original request.

## Intent Analysis

- **Goal**: a small, self-contained local web app that turns a short piece of text into a typed sentiment label, so that an upcoming demo or walkthrough has a working local example. [`intent-statement.md`]
- **Shape**: greenfield, one developer as the only user, one local process, one SQLite file, localhost only. [`intent-statement.md`] [Q1]
- **Technology**: Python with FastAPI + uvicorn for HTTP, the standard-library `sqlite3` module for storage, and pytest for tests. This overrides the original request's preference for TypeScript on Bun/Node. [Q1]
- **Not a goal**: any LLM, chat, or prose-generation capability. Jev's typed decisions are the only model call. [desc]

## Functional Requirements

### FR1 — Configuration and mode selection

- **FR1.1** The app shall read its settings from a local config file holding the OpenRouter API key and the active mode (`dummy` or `openrouter`). [Q2]
- **FR1.2** The app shall default to the dummy mode when the config file, or the key inside it, is absent. [desc] [Q2]
- **FR1.3** In live mode, when the key is missing or empty, the app shall fail with a message that names the config file to fill in. [desc]
- **FR1.4** The app shall report the active mode in its startup output and in the health endpoint. [desc]
- **FR1.5** The app shall never print, log, or persist the API key. [desc]
- **FR1.6** `config.local.toml` shall be gitignored, and only `config.example.toml` with a placeholder value shall be committed. [Q2] [desc]

### FR2 — Sentiment engine

- **FR2.1** The app shall define one `SentimentClient` interface with two implementations: a dummy client and the OpenRouter/Jev client. [desc]
- **FR2.2** The dummy client shall decide the label from keyword lists (a few positive and negative words, neutral otherwise) and return fixed per-label probabilities. It shall perform no network access and need no key. [Q3] [desc]
- **FR2.3** The live client shall call `POST https://openrouter.ai/api/alpha/decisions` with `Authorization: Bearer <key>` and model id `typesafe/jev-1.13` (alias `~typesafe/jev-latest`). [desc]
- **FR2.4** The live client shall ask a Choice question with the options `positive`, `negative`, `neutral`, and read back the selected label, the per-option probabilities, and the confidence. [desc]
- **FR2.5** The live client shall ask a Score question for intensity in the range −1..1 alongside the Choice, and the dummy client shall return a fixed intensity value. [Q4] [desc]
- **FR2.6** The client shall branch only on the typed result of those questions; it shall never parse free text from the model. [desc]
- **FR2.7** Each result shall carry the model id and the provider used. [desc]

### FR3 — Storage

- **FR3.1** The app shall store analyses in a single SQLite file at `data/sentiment.db`. [desc]
- **FR3.2** An init/migration step shall create the database and its schema on first run, with no manual setup. [desc]
- **FR3.3** Each stored row shall hold the input text, the chosen label, the per-label probabilities as JSON, the confidence, the intensity score, the model id, the provider, and `created_at`. [desc] [Q4]
- **FR3.4** Stored analyses shall be readable in newest-first order. [Q5]

### FR4 — Web interface and JSON API

- **FR4.1** The app shall serve one page where the developer submits text and sees the resulting label, confidence, and per-label probabilities. [desc]
- **FR4.2** The page shall include a small history view of past analyses. [desc]
- **FR4.3** `POST /analyze` shall accept text, run it through the active client, persist the result, and return the stored record. [Q5] [desc]
- **FR4.4** `GET /analyses` shall return stored analyses newest-first with a `?limit=` parameter defaulting to 50. [Q5]
- **FR4.5** A returned record shall carry `id`, `text`, `label`, `probabilities`, `confidence`, `intensity`, `model`, `provider`, and `created_at`. [Q5]
- **FR4.6** A health endpoint shall report the active mode. [desc] [FR1.4]
- **FR4.7** The server shall bind to localhost only and expose no authentication. [desc]

### FR5 — Development and test workflow

- **FR5.1** `dev` shall run with a single command (`uvicorn app:app --reload`). [Q1] [desc]
- **FR5.2** The test suite shall run with a single command (`pytest`). [Q1] [desc]
- **FR5.3** Every test shall run fully offline against the dummy client; no test may need an API key or reach OpenRouter. [desc]
- **FR5.4** Tests shall cover the dummy path, the database read/write path, and the request handler. [desc]
- **FR5.5** The OpenRouter client shall sit behind the `SentimentClient` interface and shall never be exercised by tests. [desc]

## Non-Functional Requirements

- **NFR1 Offline by default**: with no config file present, development and the whole test suite run with no network access and no credentials. [desc]
- **NFR2 Secret handling**: the API key exists only in the gitignored config file; the committed example file contains no secret. [desc] [Q2]
- **NFR3 Dependency weight**: the app stays dependency-light — FastAPI, uvicorn, and pytest beyond the standard library. [Q1] [desc]
- **NFR4 Deployment surface**: localhost, single user, no authentication, no cloud service, no Docker. [desc]
- **NFR5 Swappability**: the sentiment engine is reachable only through one interface, so the client can be replaced without touching the API, storage, or page. [desc]
- **NFR6 First-run readiness**: a fresh checkout reaches a usable state after one init step, with the database created automatically. [desc] [FR3.2]

## Constraints

- The implementation language and stack are fixed by the project's recorded technology choice: Python with FastAPI + uvicorn, the standard-library `sqlite3` module, and pytest. [Q1]
- The sentiment engine is the Jev model `typesafe/jev-1.13` through the OpenRouter Decisions API; no other provider is used. [desc]
- The API key is supplied manually by the developer in the local config file, never by the app. [desc] [Q2]
- Storage is a single local file, `data/sentiment.db`. [desc]
- The app is localhost-only. [desc]

## Assumptions

- **A1** Third-party dependencies are declared in `pyproject.toml` and installed before the dev and test commands run. Rationale: `[Q1]` fixed the tools but not the packaging mechanism, and `pyproject.toml` is the standard Python location for declaring them. [Q1]
- **A2** The page and the JSON API are served by the same process and port. Rationale: `[desc]` describes one small local app with a page plus two JSON routes, and `[Q1]` names one ASGI app (`app:app`). [desc] [Q1]

## Out of Scope

- Authentication, user accounts, and authorization of any kind. [desc]
- Cloud hosting, deployment pipelines, and containers (including Docker). [desc]
- Multi-user or concurrent-writer concerns: the app is single-user and local. [desc]
- Any LLM, chat, or free-text generation step, and any prose parsing of model output. [desc] [FR2.6]
- Model providers other than OpenRouter. [desc]
- Non-localhost network exposure. [desc]

## Open Questions

- When the demo or walkthrough happens, and whether it must run in live mode or can run on the dummy client — carried over from `intent-statement.md`. It does not block the requirements above, which cover both modes. [`intent-statement.md`]
