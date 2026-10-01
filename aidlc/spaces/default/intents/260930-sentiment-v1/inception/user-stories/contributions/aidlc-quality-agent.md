**Collaborator:** aidlc-quality-agent

## Contribution

**Review lens:** testability. Question asked of every criterion: *can this be turned into an
automated test, as written, with the tooling this project permits?* Assessed against the affirmed
posture (`team.md` `## Testing Posture`: acceptance/API tests first, then unit tests; 80 % line
coverage over the whole application; `pytest` only, `filterwarnings = ["error"]`, no `httpx` /
`TestClient`, zero mocks, doubles only at process seams, session-scoped `offline_guard`) and against
the suite as it exists.

**Read for this review:** `stories.md` (13 stories, 39 criteria), `personas.md`,
`user-stories-questions.md`, `user-stories-assessment.md`, `requirements.md`, `team-practices.md`,
`memory/{org,team,project}.md`, `memory/phases/inception.md`, `tests/conftest.py` and all nine
`tests/test_*.py` modules, and `app/{service,openrouter_client,dummy_client,sentiment,db,models,routes,main}.py`
plus `app/static/app.js`.

### Bottom line

1. **The criteria set is testable in outline but not in detail.** 21 of 39 criteria map cleanly onto
   a test that can be written today with the existing harness; 8 need a seam the draft never names;
   10 are blocked because the observable is undefined (an unnamed status, code, field, log line, or
   default); the remainder are page/ops surfaces that the permitted tooling cannot reach.
2. **The largest single defect is that NFR4's injected transport is invisible in the stories.** Five
   criteria require the live engine to actually answer, parse or reject; `app/openrouter_client.py`
   has no transport parameter and `get_client` (`app/service.py:54-68`) constructs it with
   `(api_key, model)` only. Without a named seam those criteria can only be satisfied by the
   monkeypatch pattern the suite already uses for the rejection path
   (`tests/test_auth_routes.py:205-223`) — which leaves the live client at the 0/149 lines `team.md`
   measured, so the affirmed 80 % floor still fails after the stories are delivered.
3. **Three criteria are not just untestable but contradictory**, and one of them contradicts a
   currently green test: `AC4.3.2` (live attempt without a key fails, naming the config file) against
   `tests/test_auth_routes.py::test_live_mode_without_any_key_starts_red_rather_than_failing` and
   `app/service.py:64-68`. That is the one finding I would not integrate without a human ruling.

---

### A. Criteria that cannot be automated as written

Grouped by *why*; the missing piece is named for each. Group A1 is fixable in the stories, A2 needs
the seam in §B, A3 needs a decision.

#### A1 — The observable is undefined (test would have to invent the assertion)

| Criterion | Why it cannot be written as-is | What is missing |
|---|---|---|
| **AC4.3.1** | "records a warning naming the missing key" — no warning exists anywhere in `app/` (the only two log calls are `app/main.py:77` info and `app/routes.py:155` warning), and "naming the missing key" is ambiguous: naming the *credential* is forbidden by `project.md ## Forbidden` ("NEVER commit, log, print … a real credential") and by NFR2. | Fix the meaning ("names the gitignored config file and records that no key is set"), the logger, the level, and the message shape. |
| **AC4.3.2** | "a documented status and machine code" — neither is named. `app/routes.py` defines four codes (`VALIDATION_FAILED`, `INVALID_TEXT`, `SENTIMENT_ENGINE_ERROR`, `AUTH_EXPIRED`); this failure is none of them. Its precondition is also unreachable: see §E/§Positions — today a live-mode-no-key request runs the dummy engine and returns 200. | Name the status and code, and name the trigger that makes an analysis a *live* attempt. |
| **AC4.4.3** | "when I read the logs, then the active mode at that time is recorded" — no per-analysis log line exists (`app/main.py:77` logs once at startup; `app/routes.py:155` only on exchange failure). | Name the level and message; decide whether startup logging (`main.py:77`) already discharges FR1.6 or whether a per-analysis line is required. |
| **AC4.4.2** | "the page's indicator reflects the new state without a restart" — the mechanism exists in `app/static/app.js:175` (`setInterval(refreshConnection, 20000)`) but is neither stated in the criterion nor testable (the suite does not execute `app.js`, `tests/test_page.py` asserts markup only). | Either restate as the observable `/auth/status` fact on one app instance (then it is a duplicate of AC4.4.1 — see §E) or define the polling contract as the thing being accepted. |
| **AC3.1.4** | "uses the documented default rather than being unbounded" — 50 appears nowhere in the draft; `tests/test_routes.py::test_get_analyses_newest_first_with_default_limit` submits 4 rows, which cannot distinguish "default 50" from "unbounded". | Name the default value; the test must write at least default+1 rows. |
| **AC6.2.1** | "a missing column" is unnamed, and no migration exists (`app/db.py:57-80` is `CREATE TABLE IF NOT EXISTS` only). | Name the column (and the DDL change) so the test asserts the right one. |
| **AC6.2.3** | "the field the new contract no longer produces" is unnamed, and the storage side is undecided: `intensity REAL NOT NULL` (`app/db.py:19`) cannot be left unwritten for new rows without a DDL change. The record shape returned for a legacy row is also undefined (key absent? key present with the legacy value?). | Name the field; decide drop-column / nullable / keep-writing; define the read shape for legacy rows. |
| **AC3.1.1** | The field list (text, label, confidence, probabilities, model id, provider, timestamp) silently omits `id`, while `tests/test_routes.py:21-34` pins `RECORD_FIELDS` **including** `intensity`, `app/models.py:20` defines it, and `tests/test_routes.py` asserts `set(response.body) == RECORD_FIELDS`. `intensity` is being dropped (A2, FR3.6) but no criterion says so. | Pin the exact response field set (with or without `id`; `intensity` in or out) — the acceptance test is a set equality, so this is not cosmetic. |
| **AC4.1.1** | "a deterministic result" is undefined: which fields must be equal across two identical submissions (`id` and `created_at` cannot be)? | State the determinism domain (label, probabilities, confidence, model, provider). |

#### A2 — Needs a seam the stories do not mention (see §B)

`AC2.1.3`, `AC4.2.1`, `AC4.2.2`, `AC4.2.4` (live half), `AC6.2.4` (live half), and `AC5.2.1` in its
deep form. Details in §B.

#### A3 — Surfaces the permitted tooling cannot reach

`AC1.1.1` ("the result panel shows…"), `AC1.1.2` ("without reloading the app"), `AC4.3.3`
("when I look at the page"), `AC5.2.2` ("when I look at the page"), `AC6.1.1` (installs and **starts
bound to loopback**), `AC6.1.2` (run the documented test command), `AC6.3.1`, `AC6.3.2`.

- The page halves: `tests/test_page.py` asserts `data-testid` hooks and that `/static/app.js` is
  served; `app.js` is never executed. The dependency cap (NFR3, `pyproject.toml:11-18`) admits "a
  test runner, a coverage tool, and a linter" — no browser driver. So each page-worded criterion is
  only testable through its API proxy (`POST /analyze` body, `/auth/status`), and the criterion
  should say so. **Missing:** an explicit statement that the page obligation is discharged at the
  markup-contract level (as `tests/test_page.py` already does), or a JS test runner added to the dev
  extra.
- `AC6.1.1`/`AC6.1.2`: no test in the suite starts a server — `tests/conftest.py` drives the ASGI
  application in-process and never binds a socket, so "bound to loopback" (FR4.7, a **Mandated**
  project rule) currently has no executable evidence at all, only the manual run recorded in
  `team.md ## Testing Posture`. **Missing:** either state that these two are verified by the manual
  verification command (then they are not acceptance criteria for a test-first workflow and should be
  marked as such), or add the subprocess smoke test proposed in §H3.
- `AC6.3.1`/`AC6.3.2`: documentation-text claims. The only way to make them fail is a source-text
  assertion, which the team's affirmed boundary discipline rejects ("tests pin the observable
  contract, not implementation echoes"). Recommend demoting both to a review checklist item (see §F).

---

### B. The seam the draft never names — the injected transport

NFR4 says the live client must be tested offline "by building the request and parsing a response
with an injected transport". The draft's criteria assume that outcome but never name the seam, and
the code does not have it: `OpenRouterClient.__init__` takes `(api_key, model, timeout)` and
`_post_decisions` calls `urllib.request.urlopen` directly. Consequences:

1. **The criteria that need it.** `AC2.1.3` (a response whose typed answer is unreadable → error, not
   a guess), `AC4.2.1` / `AC4.2.2` (session credential / config key → *the live engine answers*),
   `AC4.2.4` / `AC6.2.4` (a live answer's stored `model` and `provider`), `AC5.2.1` in its deep form
   (a provider-rejected credential is dropped). As written these are request-level statements ("when
   I submit text", "when an analysis is attempted"), so they demand the transport seam; a
   unit-level rewrite of `AC2.1.3` ("the answer reader rejects an unreadable typed answer") *is*
   testable today without any seam, because `_read_choice` / `_read_score` are pure static methods
   over an `answers` dict (`app/openrouter_client.py:180-256`). The story should say which of the two
   it means.
2. **The existing monkeypatch is not a substitute.** `tests/test_auth_routes.py:205-223` patches
   `app.routes.get_client` with a stub that raises `SentimentAuthError`. That tests the route's
   reaction, not the decision: `AUTH_REJECTED_STATUSES = {401, 403}` and the mapping in
   `_post_decisions` stay unexecuted, so a regression there ships silently while AC5.2.1 stays
   green. Same shape for AC4.2.1/4.2.2/4.2.4: a stub proves the wiring, not that the live engine
   produced the answer.
3. **The coverage consequence is quantified.** `team.md` measured the live client at **0/149 lines,
   70.2 % overall** — the design decision that the 80 % floor counts the whole application (not the
   86.5 % excluding the live client) makes the transport seam construction work, not an option. Even
   with a perfect seam, the floor needs the pure readers covered, which argues for a criterion that
   states the reader contract explicitly.
4. **A criterion is missing entirely: the request contract.** No criterion states what the live
   request must contain, yet NFR4 requires the request to be *built* in tests. FR2.2/FR2.4 fix it in
   the requirements (endpoint, Jev model from config, choice options exactly the three labels) and
   `app/openrouter_client.py` implements it (`ENDPOINT`, `CHOICE_QUESTION_KEY`, `CHOICE_CRITERIA`,
   `SCORE_CRITERIA`). Add, under US4.2:

   > **AC4.2.5** Given live mode, when a text is analysed, then the request sent to the engine names
   > the configured model id, carries the credential as a Bearer token and never in the URL, and asks
   > a choice question whose options are exactly `positive`, `negative`, `neutral`.

   Without it, the request half of the live client has no acceptance criterion to be written from —
   which is exactly the half that carries the credential-handling risk.

**Recommended seam statement to integrate into the questions file / stories preamble:**
> `OpenRouterClient` accepts an injected transport (a callable `(request) -> (status, body)`), used by
> every test and defaulting to the standard-library opener in production; `get_client` passes it
> through one optional parameter so an app-level test can exercise the live path with the
> `offline_guard` still armed.

That keeps FR5.5's spirit (the module is loaded only when live mode is selected — `app/service.py:71`
imports it lazily) while making the live path reachable from `pytest`.

---

### C. Behaviour left as an implementation detail that the tests must nevertheless pin

| Item | Where it is decided today | Why it must move into the criteria |
|---|---|---|
| The error-envelope **machine-code vocabulary** | `app/routes.py:10-14` (four codes). Draft names `INVALID_TEXT` (AC1.2.1) and `VALIDATION_FAILED` (AC3.1.3) and leaves two codes unnamed (AC2.1.3, AC4.3.2, AC5.2.1). | Acceptance tests come first; an unnamed code cannot be asserted. Name `SENTIMENT_ENGINE_ERROR` and `AUTH_EXPIRED` in the criteria that need them. |
| **Which rejection produces which code** | `tests/test_routes.py:64` asserts `code in {"INVALID_TEXT", "VALIDATION_FAILED"}` — an assertion that cannot fail on the distinction it exists to pin. | US1.2 must decide: empty/whitespace → `INVALID_TEXT`; a missing `text` field → `VALIDATION_FAILED`. Then tighten the test to an equality. |
| The **`provider` vocabulary** | `requirements.md ## Open Questions` ("free-form string or fixed set … what the offline engine records"); `app/dummy_client.py` `PROVIDER = "local-dummy"`, `app/openrouter_client.py` `PROVIDER = "openrouter"`. | AC4.2.4/AC6.2.4 assert the value "identifies" the engine; a test needs the literal set. |
| The **default history limit** | `app/routes.py` (`GET /analyses`) | AC3.1.4 — see A1. |
| The **migration DDL** | absent (`app/db.py`) | AC6.2.1/AC6.2.3 — see A1. |
| The **startup warning** and **per-analysis mode log** | absent | AC4.3.1/AC4.4.3 — see A1. |
| The **transport** | absent | §B. |
| FR6.1's **client rename** | `app/sentiment.py` docstring / `app/dummy_client.py` / `app/openrouter_client.py`; `tests/test_service.py` and `tests/test_dummy_client.py` import `DummyClient`. | No criterion covers FR6.1 at all. Either add an import-contract criterion (`from app.sentiment import DummySentimentClient, OpenRouterJevSentimentClient`) or record it in `traceability.json` as construction work with an explicit `N/A`; leaving it unmentioned is the one place the stories and requirements visibly diverge. |
| NFR4's **80 % floor itself** | `team.md ## Testing Posture`: the tool's home is "an open point for design and build"; `pyproject.toml` has no coverage config. | No criterion asserts the floor or the acceptance-first ordering. US6.1 should carry it (proposed wording in §H2) — otherwise the change that adds the coverage tool has no acceptance criterion, and the floor's home stays open for a second stage. |

---

### D. Failure / edge path per story (plan required one per story)

| Story | Failure-or-edge criterion present? | Note |
|---|---|---|
| US1.1 | partial (AC1.1.3 = offline fallback) | no criterion for the engine failing mid-request; arguably covered by AC2.1.3. |
| US1.2 | yes (all three) | missing-field code undecided (§C). |
| US2.1 | yes (AC2.1.3) | blocked on the seam; status/code unnamed. |
| US3.1 | yes (AC3.1.3, AC3.1.4) | good. |
| **US4.1** | **no** | "no outbound network call" is a property, not a failure path; also below the 3-criterion floor (2). |
| **US4.2** | **no** | no criterion for a transient engine failure (non-401/403): `SentimentEngineError` → 502, nothing persisted. That is where "does a failure fall back to offline?" lives, and it is unanswered. |
| US4.3 | yes (AC4.3.2) | blocked — see §A1/§Positions. |
| **US4.4** | **no** | AC4.4.2 has no defined trigger; AC4.4.3 has no log line. |
| **US5.1** | **no** | the sign-in flow's own failures (stray callback, blank code, refused exchange, expired pending verifier) exist in code and are covered by four tests (`tests/test_session_auth.py`, `tests/test_auth_routes.py`) yet appear in **no criterion**. US5.2 covers a rejected *credential* (runtime 401), which is a different path. |
| US5.2 | yes | but see the seam note in §B2. |
| **US6.1** | **no** | 2 testable claims, 1 manual claim; below the floor only if AC6.1.1/6.1.2 are demoted (see §H3). |
| US6.2 | yes (migration is the edge) | AC6.2.1/6.2.3 blocked on naming. |
| **US6.3** | **no** | both criteria are documentation text; see §F. |

Stories below the plan's 3–6 criteria floor: **US4.1, US5.2, US6.3** (2 each). Total criteria: 39.

---

### E. Duplicate criteria (identical or near-identical assertions)

1. **AC1.1.3 ≈ AC4.1.1 ≈ AC4.2.3** — all three assert "no config / no key → the offline engine
   answers without error". One test satisfies all three (and
   `tests/test_routes.py::test_analyze_uses_the_injected_client_not_a_network_client` already
   does). Keep AC4.2.3 (it is the third branch of the precedence triad 4.2.1/4.2.2/4.2.3) and
   AC4.1.1 (adds determinism); reduce AC1.1.3 to its unique part (no error is surfaced to the user)
   or drop it.
2. **AC1.1.2 ≈ AC3.1.1** — once "without reloading the app" is removed as untestable (§A3), AC1.1.2's
   remaining claim ("stored and appears at the top of the history") is exactly AC3.1.1's
   newest-first assertion. Recommend folding AC1.1.2's testable half into AC3.1.1 and rewording
   AC1.1.2 as the round-trip identity (`POST /analyze` returns the record the next `GET /analyses`
   returns first) — which is distinct and already true (`tests/test_routes.py` asserts it).
3. **AC4.3.3 ≈ AC5.2.2 ≈ AC4.4.1** — all assert `connected is False` / the connection state. AC4.3.3
   is strictly weaker than AC5.2.2 (no `reason`), so its test would be a subset of AC5.2.2's. Give
   AC4.3.3 the `reason` too, or merge.
4. **AC4.2.4 ≈ AC6.2.4** — `provider` (and model) identifying the engine, once for the live path and
   once for storage. Same assertion at two levels; keep one and reference the other.
5. **AC2.1.1 ≈ AC3.1.1** — label + confidence + probabilities present, once on the result panel and
   once on a history row. Acceptable, but say in AC3.1.1 that the row carries *the same* values
   (a round-trip equality) so the two tests are not the same assertion twice.
6. **AC6.1.3 ≈ AC6.3.1** — the runtime-dependency count appears in both (testable in 6.1.3 via
   `tomllib`, untestable in 6.3.1). Keep 6.1.3; demote 6.3.1.
7. **AC1.2.1 vs AC1.2.3** — the envelope-shape assertion is a refinement of the 422 assertion; they
   can be one test. Not harmful, but note it when writing the acceptance test so one test is not
   duplicated as two.

---

### F. Stories that would land with no test that could fail

- **US6.3 (both criteria).** Documentation claims; the honest test is a source-text assertion, which
  the team's boundary discipline forbids. Recommend: keep the *mechanical* half in AC6.1.3
  (`pyproject.toml` runtime deps unchanged) and move the README/NFR3-comment upkeep to a review
  checklist item in the change, not an acceptance criterion.
- **US4.4, in its current wording.** AC4.4.1 is covered (`tests/test_routes.py::test_health_reports_active_mode`);
  AC4.4.2 collapses into AC4.4.1 unless the page poll is made the subject; AC4.4.3 has no log line to
  assert. So US4.4's new content is currently one uncovered endpoint assertion.
- **US6.1's AC6.1.1 / AC6.1.2** unless the manual-run status is stated (then they are not tests at
  all) or the subprocess test in §H3 is added.
- **The page halves of AC1.1.1, AC1.1.2, AC4.3.3, AC5.2.2** — the API proxy can fail a test; the
  page sentence cannot.
- **AC5.1.2 as written risks the opposite failure — a test that passes vacuously.** "When the process
  restarts, then no credential survives" is trivially true for a fresh in-memory store on a new app
  object. The meaningful test must assert on *disk*: run the flow, then assert no file under the
  test's tmp tree contains the credential (precedent for filesystem assertions:
  `tests/test_config.py::test_local_config_is_gitignored`), and that the only new artefact is the
  SQLite file.
- **Existing weak assertion worth tightening while we are here:** `tests/test_routes.py:64`
  (`code in {...}`) cannot fail on the code it exists to pin — see §C.

---

### G. Impact on the existing suite, and reverse traceability

The v1 contract changes invalidate existing tests; the lead should carry this list into the delivery
plan so the change is not read as an unexplained test rewrite.

| Existing test surface | Why it must change |
|---|---|
| `tests/test_routes.py:21-34` (`RECORD_FIELDS` incl. `intensity`) and the `intensity == 0.6` / `model == "dummy-keyword-v1"` / `provider == "local-dummy"` assertions | the record field set is being decided by AC3.1.1 + FR3.6/A2. |
| `tests/test_dummy_client.py` (all 6, esp. `INTENSITY_BY_LABEL` imports and `test_dummy_result_carries_intensity_model_and_provider`) | A2 makes the intensity plumbing dead weight. |
| `tests/test_service.py` (`DuckTypedClient`, `SentimentResult(intensity=…)`) and `tests/test_repository.py` (`_result()`, `record.intensity`) | construct `SentimentResult` with the field being dropped. |
| `tests/test_db.py` (`columns == ANALYSES_COLUMNS`, inserts with `intensity`) | `ANALYSES_COLUMNS` / `CREATE TABLE` (`app/db.py:15-48`, `intensity REAL NOT NULL`) changes with the migration. |
| `tests/test_service.py`, `tests/test_dummy_client.py` | import `DummyClient`; FR6.1 renames both clients. |
| `tests/conftest.py::offline_guard` | must stay armed while the live path is exercised through an injected transport; a test that injects a real opener would silently defeat it. |

**Reverse traceability — behaviours that have tests today but no acceptance criterion** (each will
be an orphan in `traceability.json`, and the verification protocol checks coverage in both
directions):

- `POST /auth/disconnect` — `tests/test_auth_routes.py::test_disconnect_returns_the_app_to_the_offline_engine`.
- The exchange-failure paths — `test_callback_without_a_pending_flow_stays_red_and_says_why`,
  `test_callback_without_a_code_stays_red`, `test_a_refused_code_keeps_the_app_red_and_reports_the_reason`
  (`tests/test_auth_routes.py`); `test_complete_without_a_pending_flow_fails_and_stays_disconnected`,
  `test_complete_rejects_a_blank_code`, `test_a_code_from_an_earlier_tab_still_completes`,
  `test_pending_verifiers_are_dropped_when_the_code_window_closes` (`tests/test_session_auth.py`).
- Pending-verifier TTL / expiry (`tests/test_session_auth.py`) and `SessionAuth.expire`.
- `/static/app.js` serving and the 9 `data-testid` hooks (`tests/test_page.py`).
- PKCE S256 derivation (`tests/test_session_auth.py::test_code_challenge_is_the_base64url_sha256_of_the_verifier`).
- The `label` CHECK constraint (`tests/test_db.py`) — i.e. the "engine returned a readable but
  out-of-set label" case, which today escapes as `sqlite3.IntegrityError`, not the envelope. No
  criterion covers it, and the project's Mandated envelope rule makes that a defect surface worth a
  criterion (or an explicit `N/A`).

---

### H. Integrable additions (proposed wording; the lead owns the final text)

**H1 — Criteria to add or amend**

1. Add **AC4.2.5** (request contract) under US4.2 — wording in §B4.
2. Amend **AC2.1.3** to name the observable: "…then the request fails with `502` and
   `SENTIMENT_ENGINE_ERROR` in the app's envelope, and no row is written (`FR2.3`)". Add the
   unit-level twin: "the answer reader rejects a choice answer whose label is outside the three, or
   whose per-option probabilities are missing."
3. Amend **AC4.3.1**: "…records a warning that names the gitignored config file and states that no
   key is set, without rendering credential material." Add the logger name/level and drop the
   ambiguous "naming the missing key".
4. Amend **AC4.3.2** only after the trigger is ruled on (§Positions); the criterion must name both
   the status and the code.
5. Amend **AC4.4.3** to name the level and message, or fold it into AC4.4.1 if startup logging
   (`app/main.py:77`) is judged sufficient for FR1.6.
6. Amend **AC3.1.1** to pin the exact response field set and whether an analysis row carries
   `intensity`; make AC1.1.2 the POST→GET round-trip identity instead of the untestable
   "without reloading".
7. Name the default limit in **AC3.1.4**, the missing column in **AC6.2.1**, the dropped field and
   its legacy read shape in **AC6.2.3**, and the determinism domain in **AC4.1.1**.
8. Add **AC5.1.4** (the sign-in flow's failure path) or accept the orphan list in §G explicitly:
   "Given a refused or absent authorization code, when the callback runs, then the app stays
   disconnected and the page reports the reason."
9. Add the coverage-floor criterion under US6.1 (see §H2).
10. Record FR6.1 in `traceability.json` (construction work or an import-contract criterion).

**H2 — Coverage floor as a criterion (US6.1)**

> **AC6.1.4** Given the installed dev environment, when the documented coverage command runs, then it
> reports line coverage of `app/` including `openrouter_client.py`, fails below the 80 % floor, and
> the job that runs it is named in the README.

This closes the open point `team.md` records ("where that CI job lives is an open point for design
and build") inside the stage that already owns the tooling change, rather than leaving it to
construction.

**H3 — One criterion for the loopback rule that can fail (US6.1)**

FR4.7 / the Mandated localhost-only rule (C3, C5) has no executable evidence today. Proposed:

> **AC6.1.5** Given the documented run command, when the app is started in a subprocess, then a
> request to `127.0.0.1:<port>` succeeds and a connection attempt to the machine's non-loopback
> address is refused.

If the lead judges the subprocess test too heavy for `classic`, then AC6.1.1 should say explicitly
that the binding claim is verified by the manual verification run in `team.md ## Testing Posture`,
not by the suite — otherwise the criterion reads as automated and is not.

**H4 — Criterion → test map (for the acceptance-test-first pass)**

| Criteria | Existing test to keep/extend | New test needed |
|---|---|---|
| AC1.1.1, AC1.1.2, AC2.1.1, AC2.1.2 | `tests/test_routes.py::test_post_analyze_returns_stored_record` | API-level label/probability-key assertion |
| AC1.1.3, AC4.1.1, AC4.1.2, AC4.2.3 | `tests/test_routes.py::test_analyze_uses_the_injected_client_not_a_network_client`; `tests/conftest.py::offline_guard`; `tests/test_dummy_client.py::test_dummy_makes_no_network_call` | determinism (two submissions, same fields) |
| AC1.2.1, AC1.2.2, AC1.2.3 | `tests/test_routes.py::test_post_analyze_rejects_invalid_text_without_persisting`; `tests/test_service.py::test_service_rejects_empty_or_whitespace_text` | tighten the code assertion to equality |
| AC2.1.3 | — | unit: `_read_choice`/`_read_score` rejections; request-level: transport seam |
| AC3.1.1, AC3.1.2, AC3.1.3, AC3.1.4 | `tests/test_routes.py::test_get_analyses_newest_first_with_default_limit`, `::test_get_analyses_rejects_invalid_limit`; `tests/test_repository.py::test_list_analyses_newest_first_with_limit` | assert the default value itself |
| AC4.2.1, AC4.2.2, AC4.2.4, AC4.2.5 | `tests/test_auth_routes.py` (`_app`, `_connect`, `FakeExchanger` are the harness to reuse) | live path through the injected transport; precedence triad asserted on the analysis, not only on `/auth/status` |
| AC4.3.1, AC4.3.3 | `tests/test_auth_routes.py::test_live_mode_without_any_key_starts_red_rather_than_failing`; `tests/test_config.py::test_api_key_is_never_logged` (caplog pattern) | startup-warning assertion; reason assertion |
| AC4.3.2 | — | **blocked on the trigger ruling**; contradicts the existing test above |
| AC4.4.1, AC4.4.3 | `tests/test_routes.py::test_health_reports_active_mode` | per-analysis log assertion (blocked on wording) |
| AC5.1.1, AC5.1.3, AC5.2.1, AC5.2.2 | `tests/test_auth_routes.py` (connect / no-key-exposed / rejected-credential tests); `tests/test_config.py::test_api_key_is_never_logged`; `tests/test_session_auth.py::test_the_credential_never_renders_its_key` | add `/analyze` and `/analyses` to the no-leak sweep; deep 401 path through the transport |
| AC5.1.2 | — | filesystem assertion (no credential on disk) |
| AC6.1.3, AC6.2.2, AC6.2.4 (offline) | `tests/test_db.py::test_init_creates_database_and_schema_on_first_run`; `tests/test_config.py::test_example_config_parses_with_placeholder_key` (tomllib pattern) | manifest assertion for AC6.1.3 |
| AC6.2.1, AC6.2.3 | — | legacy-DB fixture + migration test (blocked on naming) |
| AC6.1.1, AC6.1.2 | — | subprocess smoke test, or demote to manual |
| AC6.3.1, AC6.3.2 | — | none (demote to checklist) |

**H5 — Record consistency.** `user-stories-questions.md` has a blank `[Answer]:` for Q4 and Q5, while
`stories.md` claims "Q4 = A" and "Q5 = A" (and the assessment leans on the testing posture). Either
the answers were given elsewhere and should be written back, or the MoSCoW and 3–6-criteria/one-
failure-path basis for the draft is unrecorded. Recorded here only as an observation — I did not edit
your files.

---

## Positions

- AGREE: One persona and journey-based breakdown — it makes the API-level test set a flat list of
  independent tests, and every story's criteria are reachable through `POST /analyze`, `GET /analyses`,
  `/health`, `/auth/*` or storage, which is exactly the surface the existing harness already drives.
- AGREE: US3.1's `limit` boundary (AC3.1.2–AC3.1.4) is the best-specified block in the draft —
  no-clamp, explicit default, and a real lower bound; it is the model the other boundary criteria
  should follow.
- AGREE: Preserving FR ids in the criteria (e.g. AC1.2.1 → FR4.5) — it is what makes the
  criterion→test map and `traceability.json` mechanical.
- OBJECT: **AC4.3.2 is contradictory and contradicts a green test.** It requires a live attempt to
  fail when no key exists, but `get_client` (`app/service.py:64-68`) resolves "live mode, no key" to
  the dummy engine and returns 200, and `tests/test_auth_routes.py::test_live_mode_without_any_key_starts_red_rather_than_failing`
  asserts that behaviour. The criterion also names no status or code. **Judgement call for the
  human:** either the surface must gain an explicit live-attempt trigger (then FR1.3's sentence and
  that test change), or AC4.3.2 must be dropped in favour of AC4.3.1 + AC4.3.3 alone.
- OBJECT: The stories never name the injected transport that NFR4 requires, so AC2.1.3, AC4.2.1,
  AC4.2.2, AC4.2.4 and the live half of AC6.2.4 have no reachable seam — and with `get_client`
  constructing `OpenRouterClient(api_key, model)` (`app/service.py:67`) the live client stays at the
  0/149 lines `team.md` measured, so the affirmed 80 % floor still fails. Knowledge dispute, not a
  judgement call: the seam plus AC4.2.5 (request contract) settles it.
- OBJECT: AC2.1.3 must name its status and machine code, and AC4.3.2 must name both. "Fails with an
  error" is not an acceptance criterion when acceptance tests are written first, and the four-code
  envelope is already a Mandated project rule.
- OBJECT: AC3.1.1 must pin the response field set, including whether `id` and `intensity` appear.
  As written it cannot be turned into a set-equality test without contradicting
  `tests/test_routes.py:21-34`.
- OBJECT: AC6.2.1 and AC6.2.3 name neither the column nor the field, and `intensity REAL NOT NULL`
  (`app/db.py:19`) makes "left unwritten for new rows" undecidable until the DDL is chosen.
- OBJECT: US6.3 has no automatable criterion (both are documentation text) and should be demoted to a
  review check, with only AC6.1.3 (dependency count) kept as a test. US4.1, US5.2 and US6.3 also sit
  below the plan's 3-criterion floor.
- OBJECT: US5.1 lacks the sign-in failure path, and four existing tests
  (`tests/test_session_auth.py`, `tests/test_auth_routes.py`) plus `/auth/disconnect` have no
  criterion at all — those become orphans in both the criteria set and `traceability.json`.
- OBJECT: AC5.1.2 as written passes vacuously on a fresh in-memory store; it must assert on disk.
- OBJECT: No criterion covers FR6.1 (client rename) or NFR4's coverage floor; both should be
  discharged explicitly (an import-contract criterion or an `N/A`/construction mapping, and
  AC6.1.4 as proposed) rather than left to construction.
- OBJECT: AC1.1.3 ≈ AC4.1.1 ≈ AC4.2.3, AC1.1.2 ≈ AC3.1.1, AC4.3.3 ⊂ AC5.2.2, and AC4.2.4 ≈
  AC6.2.4 duplicate assertions; without trimming, the first acceptance-test pass writes the same
  test twice and the coverage report gains nothing. **Judgement call:** trimming is the lead's call;
  the duplicated *precedence triad* (4.2.1–4.2.3) is worth keeping intact even though AC4.2.3
  overlaps AC1.1.3.
- OBJECT: The page-worded halves of AC1.1.1, AC1.1.2, AC4.3.3, AC4.4.2 and AC5.2.2 cannot fail a
  test under the dependency cap (no browser driver in NFR3's dev list) — state the markup-contract
  substitute explicitly, or those criteria read as automated when they are not. **Judgement call:**
  adding a JS test runner to the dev extra would make them real, at the cost of scope.
