**Collaborator:** aidlc-developer-agent

## Contribution

Lens: implementability and story sizing, checked against the code that exists today
(`app/`, `tests/`, `pyproject.toml`) and against `requirements.md`.

**Verdict.** The count (13) and the journey breakdown are the right shape, and the draft is honest about
which criteria are API-testable. Three things stop it from being implementation-ready: (a) nine of the
35 requirement statements have no story, and three of the nine — `FR6.1`, `FR6.2`, `NFR4` — are real,
unowned work; (b) one pair of acceptance criteria cannot both be satisfied as written, and several
others are contradicted by behaviour the code deliberately implements and a green test pins; (c) the
largest v1 delta — the record/engine contract convergence implied by `A1`/`A2`, "Out of Scope: intensity
scoring for new rows" and `FR2.2`/`FR3.6` — is folded into a story that only covers the opposite
direction (adding a column).

### 1. Requirement statements with no story

Mechanical check over `stories.md`: 26 ids are cited, **9 are not** — `FR1.5`, `FR2.1`, `FR4.7`,
`FR5.3`, `FR6.1`, `FR6.2`, `NFR2`, `NFR4`, `NFR5`. The plan promises "Every `FR` and `NFR` id in
`requirements.md` gets a coverage row in `traceability.json`, with `OK` targets naming real `US` ids",
so nine rows will have no `OK` target, or will name a story that does not carry the work.

Classified by whether the statement needs new code:

| Id | Statement (abbrev.) | State today | Needs |
|---|---|---|---|
| `FR6.1` | Rename the clients to `DummySentimentClient` / `OpenRouterJevSentimentClient` | names are `DummyClient` (`app/dummy_client.py:75`), `OpenRouterClient` (`app/openrouter_client.py:76`) | **real work, unowned.** Touches `app/dummy_client.py`, `app/openrouter_client.py`, `app/service.py:16,80,82`, `app/sentiment.py:5`, `tests/test_dummy_client.py`, `tests/test_service.py`, `README.md:79,184` |
| `FR6.2` | Remove the stale "no authentication" statement | `app/main.py:33-34` still says no session exists | **real work, folded into the wrong story** (see §4) |
| `NFR4` | 80 % line coverage of the whole app incl. the live client, live client tested offline via an **injected transport** | 70.2 % measured; `OpenRouterClient` is never imported by the suite; **there is no transport seam** — `_post_decisions` calls `urllib.request.urlopen` directly (`app/openrouter_client.py:158`) | **largest unowned chunk.** Needs a seam, new tests, a coverage tool, and the `threading.settrace` caveat |
| `FR4.7` | Server binds `127.0.0.1` only | `HOST`/`PORT` are declared and **never referenced** (`app/main.py:35-36`); no `__main__`, no `uvicorn.run`; the bind exists only as the README command `uvicorn app:app --reload` (`README.md:28`) | **real work** — nothing in code enforces it and no story asserts it |
| `FR1.5`, `NFR2` | Key never rendered/logged/stored; redaction | implemented and pinned (`app/config.py:47-55`, `app/session_auth.py:131`, `tests/test_config.py:96-113`, `tests/test_auth_routes.py:118`) | traceability row only — or cite it from US5.1 AC5.1.3 |
| `FR2.1` | Exactly two implementations, offline default for dev/tests | implemented (`app/service.py:70-82`); AC4.1.2 covers the test-side half | traceability row only |
| `FR5.3` | Page shows connected state and active engine | implemented (`app/static/app.js:136-172`) and asserted by AC4.4.2/AC5.2.2 | traceability row only |
| `NFR5` | Local-only, no cloud/container/accounts | implemented by construction, but nothing *tests* it | fold into the `FR4.7` story |

`FR2.3` is cited only inside AC2.1.3's parenthetical, not in US2.1's id list — the coverage row should
still resolve, but the story's stated scope is narrower than what it asserts.

### 2. Hidden couplings (story A secretly requires B to ship first)

1. **US2.1 → `NFR4`'s missing transport seam.** AC2.1.3 ("a response whose typed answer cannot be read
   as a label … the request fails with an error") is only reachable against the *live* client. Today the
   dummy engine always returns a typed answer, `OpenRouterClient` has no way to feed it a response
   (`app/openrouter_client.py:122-158`), and the session-wide `offline_guard` makes any socket raise
   (`tests/conftest.py:129-146`). US2.1 declares **"Dependencies. None"**; AC2.1.3 cannot be written
   until the injected transport exists.
2. **US2.1 ↔ US6.2 on the record contract.** AC2.1.1 lists label/confidence/probabilities only, and
   AC3.1.1 lists seven fields; the code returns nine (`app/models.py:64-77`, `tests/test_routes.py:22-32`).
   Whichever way the intensity decision goes, both stories edit `app/models.py`, `app/repository.py`,
   `app/db.py` and `app/static/app.js`. Delivered separately, the same field-set tests are rewritten twice.
3. **US4.2 AC4.2.1 introduces a rule the requirements never state.** "a session credential … the live
   engine answers … regardless of the config file's mode" matches the code (`app/service.py:44-45`) but
   appears nowhere in `requirements.md` — the word "precedence" does not occur there, and
   `requirements-analysis/reviews/review-01.md` R-01 (Major, status **New**) asked for exactly this to
   be stated. The AC is implementable; its *origin* is the code plus an unresolved reviewer finding, and
   that should be recorded rather than presented as a settled requirement.
4. **US4.3 reverses behaviour that a green test pins.** AC4.3.1/AC4.3.2 require live-mode-without-key to
   warn and then fail on attempt. Today that state **falls back to the dummy engine silently**:
   `config.py` rule 5 (`app/config.py:111-123`) returns `mode="openrouter", api_key=None`, and
   `get_client` collapses it to `DummyClient` (`app/service.py:44-49,70-72`), which
   `tests/test_config.py:70-85` pins in so many words ("Amends FR1.3, which previously refused to start").
   A developer who writes the AC's test first will find an existing green test asserting the opposite.
5. **US4.4 AC4.4.3 → logging that does not exist.** "Given any analysis … the active mode **at that
   time** is recorded" — the only mode log is the startup line (`app/main.py:77-81`); nothing logs per
   request, and `app/service.py` has no logger. Either the AC narrows to the startup line or a per-analysis
   log line must be added.
6. **US6.3 AC6.3.1 → a story that does not exist.** It is conditioned on "the change that adds the
   coverage tool and the linter" — that change is `NFR4` + `C4` and has no story (§1). US6.1 AC6.1.3
   asserts the same tooling ("test, coverage and lint tooling under the development extra") from a story
   that only covers running the app.
7. **US6.2 → the contract reduction it does not own.** AC6.2.3 says a field "the new contract no longer
   produces" is left as it was. Under `A1` ("intensity is dropped from v1 rather than stored"), `A2`
   ("no longer part of the contract") and "Out of Scope: intensity scoring for new rows, and the Score
   question", that field is `intensity` — and removing it is a change to `SentimentResult`
   (`app/sentiment.py:31`), both engines (`app/dummy_client.py:62,103`,
   `app/openrouter_client.py:109,232-250`), `_INSERT_SQL` (`app/repository.py:26-30,59`), the DDL
   (`app/db.py:23`), `RECORD_FIELDS`/`to_dict`/`from_row` (`app/models.py:20-30,64-93`), the page
   (`app/static/app.js:15,51`, `app/static/index.html:158`) and six test modules. No story owns it.
8. **US6.1 AC6.1.1 → the bind (same as `FR4.7` in §1).** "starts bound to loopback" is only provable by
   reading the README command; an in-process ASGI caller never binds a socket (`tests/conftest.py:44-66`).
9. **US3.1's declared dependency on US1.1 is a fixture dependency, not a delivery dependency.**
   `tests/test_repository.py:71-99` already seeds rows via `insert_analysis`, so AC3.1.1–AC3.1.4 need no
   POST endpoint. Declared as "US1.1 (rows must exist)" the story reads as sequential; the inception
   guardrail ("avoid stories that only make sense in sequence") applies. US6.2 declares the same
   dependency for the same reason; its real coupling is item 7, not US1.1.
10. **US1.1 AC1.1.2 and US3.1 share an assertion surface.** AC1.1.2 asserts the new row "appears at the
    top of the history view", so any change AC3.1.1 makes to the record field list breaks AC1.1.2's test
    as well. Same files: `app/routes.py` handlers, `app/static/app.js:79-107`.

### 3. Acceptance criteria that cannot be implemented as written

1. **Direct contradiction (blocking).** US4.2 **AC4.2.3** — "Given neither [no session credential, no
   config key] … then the offline engine answers" — and US4.3 **AC4.3.2** — "Given live mode chosen and
   no usable key … the request fails" — cover the same state with opposite outcomes. AC4.2.3 must name
   the mode ("no live mode configured") or AC4.3.2 must be narrowed. This is the same FR1.2/FR1.3
   boundary that `review-01.md` R-01/R-05 flagged and that `project.md`'s corrections say to write
   explicitly "rather than leaving it to a reviewer".
2. **US1.2 AC1.2.1 is false for the page path.** "Given the page or the API, when I submit an empty
   string or whitespace only, then the response is `422` … `INVALID_TEXT`" — the page refuses locally
   and sends nothing: `app/static/app.js:111-116` trims and calls `showError("Enter some text to
   analyse.")`, and the form is `novalidate` (`app/static/index.html:125`). No response is produced, so
   the criterion must split: API → 422 `INVALID_TEXT` (already pinned by `tests/test_routes.py:75-85`);
   page → local refusal, no request.
3. **US6.2 AC6.2.3 is impossible against the current schema.** The column is `NOT NULL`
   (`app/db.py:23`), `SentimentResult.intensity` is required (`app/sentiment.py:31`) and
   `insert_analysis` always writes it (`app/repository.py:59`). "Left as it was rather than back-filled"
   for a *new* row means NULL → `sqlite3.IntegrityError`. The story must decide and state the schema
   change (nullable column, a sentinel value, or a default), because "adds any missing column in place"
   (`FR3.3`) does not cover relaxing an existing one.
4. **US6.2 AC6.2.1 has no concrete column.** `FR3.3` says "adds any missing column in place"; `FR3.6`
   says a column the contract "no longer produces" stops being written. v1 does not add a column — it
   removes one from the write path. A migration test for AC6.2.1 can only be written against an invented
   column, so the story would pin a generic capability no requirement exercises. Name the change, or
   state that `FR3.3`'s migration is the v1 hook for *future* schemas and has no v1 column to add.
5. **US4.3 AC4.3.2 names no status and no code.** "using the app's error envelope and a documented status
   and machine code" — the four codes are `VALIDATION_FAILED`, `INVALID_TEXT`, `SENTIMENT_ENGINE_ERROR`,
   `AUTH_EXPIRED` (`app/routes.py:33-36`) and none fits "no key configured". R-05 (Minor, status **New**)
   asked for exactly this decision. Without it the AC is unassertable, and the README HTTP-surface table
   (`README.md:126-139`) must gain the row in the same change.
6. **US3.1 AC3.1.1 disagrees with the code on two fields.** Its list (text, label, confidence,
   probabilities, model, provider, timestamp) omits `id` and `intensity`, both of which the response
   carries today (`app/models.py:64-77`, asserted by `tests/test_routes.py:49-71`). Either the AC is
   incomplete or it silently changes the wire contract — and `id` is load-bearing for the newest-first
   assertions in `tests/test_routes.py:104`.
7. **US6.3 AC6.3.2 points at the wrong kind of file.** `FR6.2`'s named target is a code comment
   (`app/main.py:33-34` per `business-overview.md` D-4), not documentation; the pairing statement in
   `README.md:32` is a separate, arguably correct claim. The AC says "the app's own documentation", so a
   developer following US6.3 alone updates the README and leaves the stale comment, or deletes a README
   sentence that `project.md`'s Mandated rule ("localhost-only … unauthenticated by design") still
   requires. Split: one line for the code comment, one for the README wording.
8. **Already true, so "test first" has no red (methodology note, not a defect).** AC4.1.1, AC4.1.2,
   AC1.1.1–AC1.1.3, AC1.2.2–AC1.2.3, AC3.1.2–AC3.1.4, AC4.2.1–AC4.2.4, AC4.4.1–AC4.4.2, AC5.1.1–AC5.1.3,
   AC5.2.1–AC5.2.2 and AC6.2.2/AC6.2.4 are all satisfied by the code as it stands (evidence:
   `tests/test_routes.py`, `tests/test_config.py`, `tests/test_auth_routes.py:204-235`,
   `tests/test_session_auth.py:149-159`, `tests/test_db.py:26-50`). Under the affirmed posture
   ("acceptance/API tests come first"), these criteria are **characterization tests** — they pass on
   first run. That is legitimate, but the draft should label which stories are *new behaviour* and which
   are *pin the existing behaviour*, so Delivery Planning sequences the real deltas.

### 4. Sizing: splits, merges, and the same-code clusters

Splits (a story that is really two or three):

- **US6.2 → two.** (a) startup migration + first-run creation (`app/db.py:66-83`; note `SCHEMA_VERSION`
  is written and never compared, `app/db.py:13-14,77-81`); (b) the contract reduction that AC6.2.3
  depends on — which belongs with the record/engine contract story, not with the migration.
- **US4.3 → two.** (a) startup warning + offline fallback (the `effective_connection` seam, currently
  silent); (b) fail-on-attempt with a new envelope code — a behaviour reversal (§2.4) with a decision
  attached (§3.5). (b) is the riskier half and is the one that contradicts AC4.2.3.
- **US1.1 → drop AC1.1.3.** It duplicates US4.1 AC4.1.1 (offline default with no key); one behaviour
  asserted in two stories means two tests and an unclear owner for the offline path.

Merges (same code, cheaper together):

- **US4.1 + US4.4 → one.** Both are already implemented and both are about the same two lines
  (`app/service.py:31-57` driving `/health`, `/auth/status`, the startup log and the page indicator).
  US4.1's only unique content is NFR1's offline proof, which AC4.1.2 asserts through the suite.
- **US1.2 + US3.1 → one** ("the API's rejection boundaries"). Same file, same mechanism
  (`app/routes.py:101-109,173-199`), already pinned by `tests/test_routes.py:75-120`, and both are
  one- and four-criterion stories rather than the plan's "two to four related statements".
- **US5.1 + US5.2 → one** ("connect from the page, and drop a rejected credential"). Same files
  (`app/session_auth.py`, `app/routes.py:125-167`, `app/static/app.js:159-168`); US5.2 is 2 criteria and
  is already implemented and tested (`tests/test_auth_routes.py:204-235`).
- **US6.1 + US6.3 → one** ("run it, and keep the manifest and the docs true"). Both edit
  `pyproject.toml` and `README.md`; US6.3 AC6.3.1 is meaningless without US6.1 AC6.1.3's tooling.

Code clusters — deliver these together because they touch the same files:

| Cluster | Files | Stories today |
|---|---|---|
| **A. Engine resolution & visibility** | `app/config.py`, `app/service.py:31-82`, `app/main.py:64-81`, `app/routes.py:112-167`, `app/static/app.js:130-175` | US4.1, US4.2, US4.3, US4.4, US5.1, US5.2 (six stories, one seam) |
| **B. Contract convergence** | `app/sentiment.py`, `app/dummy_client.py`, `app/openrouter_client.py`, `app/models.py`, `app/repository.py`, `app/db.py`, `app/static/*`, 6 test modules | US2.1 + US6.2 + the unowned `FR6.1`/`FR2.2`/`NFR4` work |
| **C. API rejection boundaries** | `app/routes.py:173-199`, `app/service.py:97-101` | US1.2, US3.1 (both done) |
| **D. Tooling & doc honesty** | `pyproject.toml`, `README.md:22`, `app/main.py:33-34` | US6.1, US6.3 + unowned `NFR4`/`C4`/`FR6.2` |

The field-set risk in cluster B is concrete: one change to the record shape must touch five hand-written
copies — `RECORD_FIELDS` (`app/models.py:20`, referenced by nothing), the `to_dict` literal
(`app/models.py:64-77`), `ANALYSES_COLUMNS` + the DDL (`app/db.py:16-48`), the private set in
`tests/test_routes.py:22`, and the raw `INSERT` column lists in `tests/test_db.py:56-58,82-83`. Single-
sourcing the contract is the first step of that story, not an aside.

### 5. What I would ask the lead to change in the draft

1. Add the three unowned stories: **rename/converge the engine contract** (`FR6.1` + `FR2.1` + `FR2.2`
   Score removal + `FR2.3`), **cover the whole app including the live client** (`NFR4` + `C4` + R-04
   docs, which needs the `OpenRouterClient` transport seam), and **localhost-only is enforced**
   (`FR4.7` + `NFR5`). Then `FR6.2`, `FR1.5`, `NFR2`, `FR2.1`, `FR5.3` find owners by citation.
2. Make US2.1 depend explicitly on the transport seam, and move the intensity/`id` decision into the
   contract story so AC6.2.3 lives where the schema change is made.
3. Fix the AC-level defects in §3 (1, 2, 3, 4, 5 are the ones that would stop a developer).
4. Apply the four merges in §4 — 13 stories becomes 12 with the same coverage plus the three new ones,
   and each story then covers the 2–4 statements the plan claims.
5. Label each story **new behaviour** vs **characterization** (§3.8), so the acceptance-test-first
   posture has a red test to drive for at least the real deltas.

## Positions

- AGREE: one persona (Q1 = A) is right for this codebase — one page, one JSON API, one config file, one
  operator, per `app/routes.py:82-98`, `README.md:28-32` and the CodeKB's single local user.
- AGREE: breakdown by capability area (Q2 = A) maps cleanly onto the component boundaries in
  `component-inventory.md`; the six areas are the real seams, and they survive my merges below.
- AGREE: 13 stories is the right order of magnitude for 35 statements, and MoSCoW is applied consistently
  (12 Must, 1 Should — US6.3 — with nothing Won't Have, matching Q4 = A).
- AGREE: the declared US4.3 → US4.2 and US5.2 → US5.1 dependencies are real; AC4.3.2 only makes sense
  once the precedence rule exists.
- AGREE: every acceptance criterion is written Given/When/Then and is phrased as an observable
  response or stored row, which is what the affirmed "acceptance/API tests first" posture needs.
- OBJECT: US4.2 AC4.2.3 and US4.3 AC4.3.2 contradict each other — same precondition ("no session
  credential, no config key"), opposite outcomes.
- OBJECT: US4.3 AC4.3.1/AC4.3.2 reverse behaviour that `app/config.py:111-123` and
  `tests/test_config.py:70-85` deliberately implement and pin; the story must say it supersedes rule 5
  and update that test in the same change.
- OBJECT: US4.3 AC4.3.2 is untestable as written — "a documented status and machine code" names neither,
  and `app/routes.py:33-36` has no code for this failure (review finding R-05, still New).
- OBJECT: US6.2 AC6.2.3 cannot be built against `intensity REAL NOT NULL` (`app/db.py:23`) with
  `SentimentResult.intensity` required (`app/sentiment.py:31`) and always written (`app/repository.py:59`).
- OBJECT: US6.2 AC6.2.1 has no v1 column to add — `FR3.3` (add missing) and `FR3.6` (stop producing)
  point in opposite directions, so the criterion pins a capability nothing exercises.
- OBJECT: US2.1 AC2.1.3 is unreachable today (no injected transport in `app/openrouter_client.py:122-158`;
  sockets blocked by `tests/conftest.py:129-146`) while US2.1 declares "Dependencies. None".
- OBJECT: US3.1 AC3.1.1's field list conflicts with the code on `id` and `intensity`
  (`app/models.py:64-77`, `tests/test_routes.py:22-32`).
- OBJECT: US1.2 AC1.2.1 promises a 422 envelope for the page path, but the page refuses locally and
  sends no request (`app/static/app.js:111-116`).
- OBJECT: US4.4 AC4.4.3 asserts per-analysis mode logging that does not exist — the only mode log is the
  startup line (`app/main.py:77-81`).
- OBJECT: US6.3 AC6.3.1 is conditioned on a tooling change no story owns (`NFR4`, `C4`), and AC6.3.2
  targets documentation while `FR6.2`'s named statement is a code comment (`app/main.py:33-34`).
- OBJECT: US6.1 AC6.1.1 cannot be observed from any test — nothing in the code binds, and `HOST`/`PORT`
  (`app/main.py:35-36`) are unused; `FR4.7` needs its own story with an assertable criterion.
- OBJECT: nine requirement ids have no story (`FR1.5`, `FR2.1`, `FR4.7`, `FR5.3`, `FR6.1`, `FR6.2`,
  `NFR2`, `NFR4`, `NFR5`), and `FR6.1`, `FR6.2`, `NFR4` are unowned *work*, not just missing citations.
- OBJECT: several stories cover a single statement (US1.2 → `FR4.5`, US4.3 → `FR1.3`, US5.2 → `FR5.4`,
  US6.3 → `NFR3`), which contradicts the plan's stated granularity of two to four statements per story.
- OBJECT (judgement call for the human, not a knowledge dispute): the draft attributes "Q4 = A" and
  "Q5 = A", but `user-stories-questions.md` has empty `[Answer]:` cells for both — only Q1–Q3 are
  recorded. Either write the human's Q4/Q5 answers into the plan file or drop the attribution; if the
  answers were given in conversation, the plan file should carry them, since it is the artifact the
  traceability check reads.
- OBJECT (judgement call for the human): whether v1 *removes* `intensity` from the wire record or keeps
  it as a legacy field for old rows only is a product decision the draft does not make. `A1`/`A2` say
  "dropped", "Out of Scope" says only that new rows are not scored, and AC6.2.3 assumes removal. I have
  treated removal as the intent; if the human means "leave the plumbing, stop improving it", the
  contract story shrinks to one AC and US6.2 keeps its schema change.
