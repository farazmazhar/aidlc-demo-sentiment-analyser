# User Stories — `very-cool-sentiment-analysis` v1

Persona: **P1, the local user** (`personas.md`). Journey-based breakdown (plan Q2 = A), value-sized
(plan Q3 = B), MoSCoW with nothing marked *Won't Have* (plan Q4 = A), 3–6 acceptance criteria per
story including the failure path (plan Q5 = A).

**Integrated after the mob review.** The three independent reviews found real contradictions in the
Round 0 draft, and this revision folds them in: the engine-selection precedence is now stated, the
live-attempt behaviour follows the Q6 ruling (an explicit attempt path, not a silent fallback), the
history limit has a defined default, the nine requirement statements the first draft left unowned now
have stories, and criteria that asserted internal facts were rewritten to observables or moved to the
story that owns them. Two objections were recorded as the human's to weigh at the gate rather than
resolved here: whether the dropped intensity field is really gone from the wire contract, and whether
preserving history through a migration is worth more than the affirmed "delete the file" recovery
(see `user-stories-assessment.md` and the completion summary).

Story map axes: journey step (horizontal) × priority (vertical). Areas: run and configure → submit →
read the result → history → choose the engine → connect the live model → keep what is stored.

---

## US1 — Run it

### US1.1 Install, run and test it locally, offline by default — *Must Have*

As P1, I want to clone, install, run and test the app with no credentials, so that I can use and
work on it before deciding anything about the live model. (`FR1.1`, `NFR1`, `NFR3`)

- **AC1.1.1** Given a fresh clone and no config file or key anywhere, when I follow the README, then the app installs, starts bound to `127.0.0.1`, and serves the page and the API. (`FR4.7`)
- **AC1.1.2** Given that environment, when I run the documented test command, then the whole suite runs and passes with no key and with outbound network use blocked.
- **AC1.1.3** Given the manifest, when I read its dependency lists, then the runtime dependencies are the two the project declares and the test, coverage and lint tooling sit under the development extra.

### US1.2 Documentation, names and manifest tell the truth — *Should Have*

As P1, I want the project to describe itself accurately, so that I am not misled by stale claims.
(`FR6.1`, `FR6.2`, `NFR3`; review R-04, and the developer review's naming findings)

- **AC1.2.1** Given the change that adds the coverage tool and the linter, when it lands, then the README's dependency statements and the manifest's dependency commentary are updated in the same change.
- **AC1.2.2** Given the engine implementations, when I read their names, then they are `DummySentimentClient` and `OpenRouterJevSentimentClient` everywhere they are imported or constructed.
- **AC1.2.3** Given the application's own documentation, when it describes authentication, then the statement matches the sign-in flow that exists.

---

## US2 — Submit text and read the result

### US2.1 Submit text and get a labelled result with its alternatives — *Must Have*

As P1, I want to submit text and immediately see the label, the confidence and the other labels'
scores, so that I can judge the answer. (`FR4.1`, `FR4.4`, `FR2.2`, `FR2.4`)

- **AC2.1.1** Given the running app, when I submit non-empty text, then the result shows one label from `positive` / `negative` / `neutral`, the confidence, and a probability for each of the three labels.
- **AC2.1.2** Given the same submission, when the request returns, then the response carries the stored record's field set — id, text, label, the per-label probabilities as an object keyed by label, confidence, model, provider and timestamp — and the row appears at the top of the history.
- **AC2.1.3** Given an offline answer, when the result is displayed, then it is clear that the offline stand-in produced it rather than the live model. *(the design review's persona-pain point: which engine answered)*

### US2.2 Empty input is refused and nothing is stored — *Must Have*

As P1, I want empty or whitespace-only submissions refused clearly, so that my history never fills
with meaningless rows. (`FR4.5`)

- **AC2.2.1** Given the API, when I submit an empty string or whitespace only, then the response is `422` with the machine code `INVALID_TEXT` in the app's single error envelope.
- **AC2.2.2** Given such a refusal, when I read the history, then no new row exists.
- **AC2.2.3** Given the page rather than the API, when I submit an empty value, then the page shows the same refusal message and sends no request that creates a row.

---

## US3 — Trust the engine contract

### US3.1 The answer is read as typed data, never guessed from prose — *Must Have*

As P1, I want the label to come from the engine's typed answer, so that I never receive a label
invented from free text. (`FR2.1`, `FR2.3`)

- **AC3.1.1** Given a live request, when it is sent, then it asks a choice question whose options are exactly `positive`, `negative`, `neutral`, with the per-option probabilities and confidence read back from the typed answer.
- **AC3.1.2** Given a typed answer that cannot be read as a label plus per-option probabilities, when the client returns, then the request fails rather than yielding a guessed label.
- **AC3.1.3** Given the two implementations behind the one interface, when either is exercised, then the same result shape comes back and neither path can be reached without going through the interface. (`FR2.1`)

---

## US4 — Browse history

### US4.1 See previous analyses newest-first, with a defined limit — *Must Have*

As P1, I want the history to list my analyses newest-first and behave predictably when I ask for a
number of them. (`FR3.4`, `FR4.2`, `FR4.6`)

- **AC4.1.1** Given several stored analyses, when I read the history, then rows are newest-first and each carries id, text, label, probabilities, confidence, model, provider and timestamp.
- **AC4.1.2** Given a `limit` of *n* greater than or equal to 1, when I request the history, then at most *n* rows come back.
- **AC4.1.3** Given a `limit` below 1 or one that is not a number, when I request the history, then the response is `422` with `VALIDATION_FAILED` and the value is not silently changed.
- **AC4.1.4** Given no `limit` at all, when I request the history, then the documented default applies — the requirements review's R-02 requires that number to be named, not left to the implementer.

---

## US5 — Choose the engine

### US5.1 Choose the live model, with a stated credential precedence — *Must Have*

As P1, I want to choose the live model and know exactly which credential wins, so that I am never
surprised about which engine answers. (`FR1.2`, `FR1.4`, `FR5.1`)

- **AC5.1.1** Given a session credential from the sign-in flow, when I submit text, then the live engine answers with the configured model regardless of the config file's mode.
- **AC5.1.2** Given no session credential but a config file naming live mode with a key, when I submit text, then the live engine answers.
- **AC5.1.3** Given neither, when I submit text, then the offline engine answers and the default model id is `typesafe/jev-1.13` unless configured otherwise.
- **AC5.1.4** Given a live answer, when the row is stored, then its model and provider identify the live engine.

### US5.2 A live attempt without a usable key fails with an instruction — *Must Have*

As P1, I want a live attempt with no usable key to tell me which file to fill in, so that I can fix
it in one step. (`FR1.3`; the Q6 ruling — an explicit attempt path, replacing today's silent
fallback, and the existing test that pins it is updated)

- **AC5.2.1** Given live mode requested and no usable key, when the app starts, then it starts on the offline engine and records a warning that no key is configured, naming the config file and never any credential material.
- **AC5.2.2** Given that state, when I submit a text while the live engine was requested, then the request fails with a documented status and machine code in the app's error envelope, and the message names the config file to fill in.
- **AC5.2.3** Given that state, when I submit while nothing live was requested, then the offline engine still answers.

### US5.3 The active engine and connection state are always visible — *Must Have*

As P1, I want the page, the health endpoint and the logs to agree about the active engine.
(`FR1.6`, `FR4.3`, `NFR6`)

- **AC5.3.1** Given any running app, when I read the health endpoint, then it reports the active engine mode and whether the live engine is connected.
- **AC5.3.2** Given a change in connection state, when it happens, then the page's indicator reflects it without a restart, and the state is announced rather than implied by colour alone. *(the design review's accessibility finding)*
- **AC5.3.3** Given the app's logs, when I read them, then startup records the active mode and no log line contains credential material.

---

## US6 — Connect the live model from the page

### US6.1 Connect from the page, keep the credential in memory, drop a rejected one — *Must Have*

As P1, I want to connect the live model from the page without writing my key to disk, and I want a
dead credential to stop being used. (`FR5.2`, `FR5.3`, `FR5.4`)

- **AC6.1.1** Given the page, when I complete the sign-in flow, then the app holds a session credential, the live engine becomes available, and the page reflects the connected state.
- **AC6.1.2** Given a completed sign-in, when the process restarts, then no credential survives — nothing was written to disk.
- **AC6.1.3** Given any response body, log line or rendered setting, when I inspect it, then the credential never appears.
- **AC6.1.4** Given a credential the provider rejects, when an analysis is attempted, then the credential is discarded, the app returns to the offline engine, and the page shows not-connected with a reason.
- **AC6.1.5** Given the sign-in flow's own failure paths — a stray callback, a blank code, a refused exchange, an expired verifier — when each occurs, then the page reports it and the app stays usable.

---

## US7 — Keep what is stored

### US7.1 Stored results keep the v1 contract through an in-place migration — *Must Have*

As P1, I want a schema change to add what is missing without wiping what I already have.
(`FR3.1`, `FR3.2`, `FR3.3`, `FR3.5`, `FR3.6`)

- **AC7.1.1** Given a first run with no database, when the app starts, then the file and its schema are created.
- **AC7.1.2** Given an existing database missing a column the v1 contract requires, when the app starts, then the column is added in place and every existing row is still readable.
- **AC7.1.3** Given a row written before this version, when it is read, then the field the v1 contract no longer produces is left as it was rather than back-filled with an invented value, and the shape the field's absence forces on the stored schema is decided explicitly rather than inherited. *(the developer review's `intensity` NOT NULL finding)*
- **AC7.1.4** Given a newly written row, when it is read, then it carries a provider value identifying which engine produced it, and the row's probabilities are keyed by label with every label present.

---

## US8 — Stay private and local

### US8.1 The key never leaks and the app never leaves the machine — *Must Have*

As P1, I want my credential to stay mine and the service to stay on my machine. (`FR1.5`, `FR4.7`, `NFR2`, `NFR5`)

- **AC8.1.1** Given any rendered setting, log record, or response body, when I inspect it, then the key appears nowhere.
- **AC8.1.2** Given the running app, when I probe it from another host, then it is unreachable because it binds loopback only, and nothing in the project requires a cloud service or a container.
- **AC8.1.3** Given the repository, when I check what is committed, then no real credential is present and only the placeholder example config is tracked.

---

## US9 — Prove it

### US9.1 The live client is proven by tests and the coverage floor holds — *Must Have*

As P1, I want the live half of the system covered by tests that never touch the network, so that the
80% floor means something. (`NFR4`, `C4`)

- **AC9.1.1** Given the live client, when it is exercised in tests, then its transport is injected and the request and a recorded response are asserted with no network access.
- **AC9.1.2** Given the whole application, when the suite runs with coverage enabled, then line coverage is at least 80% and the run fails below it.
- **AC9.1.3** Given the linting and formatting rules, when the code is checked, then the configured rules — including the security set — pass, and the check is wired where a change can run it.

---

## Story map (journey × priority)

| Journey step | Must Have | Should Have |
|---|---|---|
| Run it | US1.1 | US1.2 |
| Submit and read | US2.1, US2.2, US3.1 | — |
| Review history | US4.1 | — |
| Choose the engine | US5.1, US5.2, US5.3 | — |
| Connect the live model | US6.1 | — |
| Keep what is stored | US7.1 | — |
| Stay private | US8.1 | — |
| Prove it | US9.1 | — |

## Carried to the gate, not resolved here

- **Intensity on the wire.** The draft's `stories.md` and the running page still show an intensity
  value, while the requirements drop intensity from the v1 contract. The stories above follow the
  requirements; the page and the stored-schema consequence are called out in US7.1's third criterion
  for the human to weigh.
- **Migration versus delete-and-start-over.** Preserving history through a migration (US7.1) is more
  work than the affirmed recovery practice ("deleting the local database is acceptable"), which is
  what the page's own empty state assumes. Both are compatible, but the human may prefer the cheaper
  path; recorded as the one point where the review asked for a ruling.
