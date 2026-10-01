# Requirements — `very-cool-sentiment-analysis` v1

> Intent `260930-sentiment-v1`, scope `classic`, depth Standard. Sources: the verbatim initial
> description (`project-description.json`), the reverse-engineering CodeKB for this repository, the
> team practices affirmed in this workflow, and the nine answered clarifying questions in
> `requirements-analysis-questions.md`. Every requirement below traces to one of those.

## Intent Analysis

The user wants the existing local sentiment-analysis app turned into a v1 that can be relied on:
one small service, runnable on a laptop with no credentials, that either scores text offline with a
deterministic stand-in engine or, when a key is present, scores it through the Jev model on
OpenRouter, storing every result locally and showing it in a page and a JSON API.

The scan established that the v1 core already exists — the engine interface with two
implementations, SQLite persistence, the page and history, `POST /analyze` and `GET /analyses`, and
an offline default. The work is therefore convergence and hardening, not construction from zero: the
value lies in making the engine contract exact, closing the drift between the code and the intent,
and putting the untested half of the system under test.

## Functional Requirements

### FR1 — Configuration and engine selection

- **FR1.1** The app resolves its active engine from one local TOML config file, defaulting to the
  offline engine when no config file or key is present.
- **FR1.2** Live mode is selected by configuration; when a key is available it is used as the Bearer
  credential for the OpenRouter Decisions API.
- **FR1.3** When live mode is configured but no key is available, the app starts on the offline
  engine and logs a warning; a live analysis attempt then fails with a clear message naming the
  config file to fill in. It does not fail at startup.
- **FR1.4** The model id is configuration with the default `typesafe/jev-1.13`.
- **FR1.5** The key is never hardcoded, printed, logged or written to storage, and every value that
  can hold it renders `<redacted>` in its representation.
- **FR1.6** The active engine mode is reported in the app's logs and through the health endpoint.

### FR2 — Sentiment engine contract

- **FR2.1** One engine interface has exactly two implementations: `DummySentimentClient`
  (deterministic canned results, no network, no key) and `OpenRouterJevSentimentClient` (the live
  Jev call). The offline implementation is the default for development and for every test.
- **FR2.2** The live implementation calls the OpenRouter Decisions API with the Jev model, asks a
  Choice question whose options are exactly `positive`, `negative`, and `neutral`, and reads back the
  selected label, the per-option probabilities, and the confidence.
- **FR2.3** Every result is taken from the typed answer — selected option, probability per option,
  confidence. Free text is never parsed to derive a label, and a result that cannot be read as typed
  data is an error, not a guess.
- **FR2.4** Probabilities are a value per label; the label set is exactly the three options, and the
  chosen label is one of them.

### FR3 — Persistence

- **FR3.1** Results are stored in one local SQLite file, `data/sentiment.db`, created on first run by
  an initialisation step.
- **FR3.2** Each stored row carries: the submitted text, the chosen label, the per-label
  probabilities as JSON, the confidence, the model id, the provider, and the creation timestamp.
- **FR3.3** A schema migration runs on startup and adds any missing column in place, keeping
  existing rows.
- **FR3.4** The history is read newest-first with a caller-set limit.
- **FR3.5** `provider` records which engine produced the row, so a stored result can be attributed to
  the offline or the live engine.
- **FR3.6** Existing rows keep their values; a column the v1 contract no longer produces is left
  unwritten for new rows rather than back-filled with invented data.

### FR4 — HTTP surface and page

- **FR4.1** `POST /analyze` accepts text, scores it with the active engine, persists the result, and
  returns the stored record.
- **FR4.2** `GET /analyses` returns stored analyses newest-first, limited by a caller-supplied limit.
- **FR4.3** A health endpoint reports the active engine mode and the connection state.
- **FR4.4** One page submits text and shows the label, the confidence, and the probabilities, plus a
  history view of previous analyses.
- **FR4.5** Text that is empty or whitespace only is rejected with `422 INVALID_TEXT` and nothing is
  written.
- **FR4.6** A limit below 1, or one that is not a number, is rejected with `422 VALIDATION_FAILED`
  and is never silently clamped.
- **FR4.7** The server binds `127.0.0.1` only.

### FR5 — Connecting the live engine from the page

- **FR5.1** The in-app OpenRouter sign-in flow (PKCE, S256) remains the primary way to connect the
  live engine, with the config-file key as the fallback; both paths lead to the same engine contract.
- **FR5.2** A credential obtained through the flow lives in process memory for the session only; it
  is never written to disk, logged, or returned in a response body.
- **FR5.3** The page shows whether the live engine is connected and which engine is active.
- **FR5.4** A credential the provider rejects is dropped, so the app falls back to the offline engine
  instead of retrying a dead key.

### FR6 — Code-level convergence

- **FR6.1** The two engine implementations carry the names `DummySentimentClient` and
  `OpenRouterJevSentimentClient`, with the interface and its call sites updated.
- **FR6.2** The stale statement that the app has no authentication is removed, since the sign-in flow
  documented in FR5 exists.

## Non-Functional Requirements

- **NFR1 — Offline-first.** Development and the whole test suite run with no key and no network
  access; no test reaches OpenRouter. The suite fails loudly if anything tries.
- **NFR2 — Secret containment.** The key exists only in the gitignored local config file or in
  process memory. It is never committed, logged, printed, or persisted.
- **NFR3 — Dependency weight.** Runtime dependencies stay at two (`fastapi`, `uvicorn`) with the
  standard-library `sqlite3` for storage; development-only tooling may add a test runner, a coverage
  tool, and a linter/formatter.
- **NFR4 — Test coverage and cadence.** Line coverage of the whole application, including the live
  client, is at least 80%, enforced by a tool; the live client is tested offline by building the
  request and parsing a response with an injected transport. Acceptance/API tests are written before
  the implementation they cover, lower-level unit tests after it.
- **NFR5 — Local-only operation.** The app runs on localhost for a single user, with no cloud
  component, no container requirement, and no account system beyond the OpenRouter sign-in flow.
- **NFR6 — Observable mode.** The active engine and connection state are visible from the page, the
  health endpoint, and the logs, so a user can tell which engine produced a result.

## Constraints

- **C1** The app is Python with FastAPI and the standard-library `sqlite3`; the project is built in
  Python, overriding the initial description's TypeScript-on-Bun preference.
- **C2** The OpenRouter API key is supplied manually in the gitignored `config.local.toml`, or
  obtained through the in-app flow; it is never committed.
- **C3** Localhost only: no cloud, no Docker, no hosted deployment, no auth accounts.
- **C4** Code style is enforced mechanically with `ruff` (formatting and linting, including its
  security rules), run as a pre-commit hook or a stage check.
- **C5** One local SQLite file is the only durable state, and deleting it is an accepted recovery.
- **C6** The OpenRouter Decisions API shape is taken as given; no requirement changes it.

## Assumptions

- **A1** Three of the clarifying answers deliberately depart from the initial description, and the
  answers govern: the in-app sign-in flow is kept rather than removed; live mode with no key warns
  and fails on attempt rather than failing at startup; intensity is dropped from v1 rather than
  stored.
- **A2** The dummy engine's fixed per-label intensity values are no longer part of the contract; they
  are dead weight unless a later stage finds a use for them.
- **A3** The requirement ids cited in the existing module docstrings refer to the finished prior
  intent; carrying them forward or restating traceability is part of the v1 work rather than a new
  requirement.
- **A4** No concurrency target is defined for v1: the app serves one local user, and the previously
  accepted limitation around SQLite connection handling is not a v1 target.

## Out of Scope

- Multi-user support, accounts, tenancy, and any authentication other than the OpenRouter sign-in
  flow.
- Cloud hosting, containers, and deployment pipelines.
- Retention, deletion, or export of stored analyses.
- Intensity scoring for new rows, and the Score question in the engine contract.
- Any change to the OpenRouter model or to the Decisions API contract.
- Operating-system packaging beyond a local editable install.

## Open Questions

- Where the job that runs the suite and the coverage floor lives, given this scope skips the CI
  Pipeline stage: a local pre-commit/pre-push hook, a build-and-test step, or a pipeline added later.
- Whether `provider` is a free-form string or a fixed set of values, and what the offline engine
  records there.
- Whether the unused dummy intensity values are deleted with the rest of the intensity plumbing or
  left in place.
- The provider-side limit on stored text: live mode sends the submitted text to OpenRouter, and no
  length bound is specified beyond what the page and API currently accept.
