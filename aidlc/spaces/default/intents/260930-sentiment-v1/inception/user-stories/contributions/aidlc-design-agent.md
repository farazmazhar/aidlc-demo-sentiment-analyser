**Collaborator:** aidlc-design-agent

## Contribution

Lens: user experience and persona fidelity — read against the app that actually ships
(`app/static/index.html`, `app/static/app.js`) and the backend paths those two files call
(`app/config.py`, `app/service.py`, `app/routes.py`).

### 1. Verdict

The persona work is faithful and the story set is well-shaped as a first cut: goal-framed wording,
Given/When/Then criteria, stable ids, spot-on prioritisation of the analyze-and-read journey. What
it is not yet usable for is the handoff to design. Three classes of defect recur:

1. **Criteria written from the API's point of view are captioned as things the user sees** — the
   user-visible half is often the *opposite* of what the AC asserts (US1.2, US4.3).
2. **The journey in the story map is not the journey the page runs** — history loads before the user
   does anything, and "choose the engine"/"connect the live model" are one control, not two steps.
3. **Whole screen states the page visibly has are absent from the story set** — the empty state, the
   loading state, the return leg of the sign-in redirect, and what remains on screen after a failure.

Everything below is anchored to a story id, an AC id, or a file line.

### 2. Persona fidelity (P1)

**Faithful on identity.** One persona is right, and for the right reason: the CodeKB's actor table
(`business-overview.md`, "Actors and Stakeholders") names exactly one human — "Local user (single
human operator)" — and the operator row is the same person doing install/config work; `team.md`
(`## Way of Working`) independently confirms "no second human reviewer in this project …
one person as sole user, operator and decision-maker". Q1 = A is honoured, and the
"hats, not personas" framing in `personas.md` is the correct reading of that evidence.

**Four context facts are missing, and each one would change a story:**

| Missing context | Evidence it is unresolved | Story it changes |
|---|---|---|
| **Viewport / device.** P1 "opens the page in a browser" but the page declares no viewport policy beyond a meta tag and has **no media queries at all**; the pill is `position: fixed` (`index.html:75-93`) and the layout is one fluid column (`index.html:12-16`). | `index.html` — zero `@media` rules | Makes US2/US3/US4 responsive obligations decidable. Either state "desktop browser on the same machine is the only v1 target" (then drop touch/responsive ACs entirely) or add a mobile AC. Today the story set is silent, so design will invent it. |
| **Typical text length and language.** "Score a piece of text" is never sized. There is no `maxlength` and no counter on the textarea (`index.html:127-134`), no bound in the API, and the requirements file itself leaves "the provider-side limit on stored text" open (`requirements.md`, Open Questions). | `index.html:127-134`; `requirements.md` Open Questions | US1.1 (input bounds), US3.1 (a history row renders the full text — `.history-text` has no truncation, `index.html:177`) |
| **The offline engine is a low-fidelity stand-in.** P1's goal "judge whether to trust it" cannot be evaluated without knowing the offline numbers are fixed (`dummy_client.py` fixed probability triples and per-label intensity; CodeKB BR-12: "Dummy-mode rows are deterministic and carry no real signal … not comparable with live-mode rows"). | `business-overview.md` BR-12; `component-inventory.md`, "Offline Dummy Engine" | US1.1 AC1.1.3 and US2.1 — with no disclosure AC, the page shows a confident "0.600" that means nothing |
| **First run vs. returning user.** P1's first paint is the pill (red) plus "No analyses yet." The two cases differ in what the page shows and when — see §5.1 for the flash-of-wrong-empty-state defect this produces. | `app.js:67,80`; `index.html:169` | Adds/justifies the empty-state and loading stories that are currently missing |

`personas.md` is otherwise accurate: it correctly records that the key lives in the gitignored
`config.local.toml` or in process memory (`app/session_auth.py`, `SessionCredential`),
and the "which engine answered" pain point is real — it is simply not *served* by the current ACs
(§3, row US4.4).

### 3. Acceptance-criteria audit — observable vs. internal fact

`O` = the stated outcome is visible to a person using the page. `I` = the criterion is an internal
fact (HTTP status, log line, table column, test-run property) wearing a user-story hat.

| AC | O/I | What a person actually observes, per the code |
|---|---|---|
| AC1.1.1, AC1.1.2, AC1.1.3 | **O** | Correct. `renderResult` fills the panel (`app.js:48-62`); `submitAnalysis` calls `renderHistory` without a reload (`app.js:89-107`); the dummy path returns 200 offline (`app/config.py:108-121`, `app/routes.py:89-99`). |
| AC1.2.1 | **I** | `422 INVALID_TEXT` is never reached from the page: `app.js:113-116` trims and short-circuits with `showError("Enter some text to analyse.")` before any fetch. |
| AC1.2.3 | **I — and false for this path** | There is no envelope on the user's empty-input path; the user gets a hardcoded English sentence in the shared `error-panel` (`app.js:113-116`). |
| AC2.1.1 | **O** | Correct, but **incomplete**: the same panel also renders "Intensity" (`index.html:157`) and the lede promises "an intensity score" (`index.html:122`) — see §5.3. |
| AC2.1.2, AC2.1.3 | **I** | Label-set and typed-answer guarantees are contract facts. Their user-visible form is "an error message appears and no result is shown", which is not what the AC says. |
| AC3.1.1 | **I (in part)** | The page shows text, label, confidence and **raw** `created_at` (`app.js:71-76`). Probabilities, model id and provider are **stored but never rendered** — so half this criterion is an API contract, and the other half silently pre-decides row content. |
| AC3.1.2, AC3.1.3, AC3.1.4 | **I** | `app.js:80` hardcodes `/analyses?limit=50`; no UI exists to set or read a limit. All three are API-only. |
| AC4.1.1 | **O/I** | The deterministic result is observable; "no outbound network call" is not. |
| AC4.1.2 | **I** | "The test suite passes with no key and no network" is a CI property (`tests/conftest.py` `offline_guard`, per `team.md`). It belongs in US6, not in P1's story. |
| AC4.2.1–AC4.2.3 | **I** | Credential precedence is decided in `effective_connection` (`app/service.py:31-57`). The user-visible proxy — the pill's text/colour — is only implied. |
| AC4.2.4 | **I** | Stored `model`/`provider` are not shown anywhere on the page. |
| AC4.3.1 | **I** | "Records a warning naming the missing key" is a log line. |
| AC4.3.2 | **I — and unreachable as written** | See §4.2. |
| AC4.3.3 | **O** | Correct in substance, but see §4.2: the *reason* is in a `title` attribute only (`app.js:139-141`). |
| AC4.4.1, AC4.4.3 | **I** | `/health` and the logs are not user surfaces. |
| AC4.4.2 | **O** | Correct — the pill repaints from `/auth/status` (`app.js:147-156`). |
| AC5.1.1 | **O (weakly)** | Observable only as the pill turning green. Nothing covers the redirect's **return leg** (§4.3). |
| AC5.1.2, AC5.1.3 | **I** | "No credential survives a restart" and "never in a body/log" are the secret-containment tests (NFR2), not user-visible criteria. |
| AC5.2.1 | **I** | The user-visible proxy (error shown, pill turns red) is not stated. |
| AC5.2.2 | **O (partly)** | "not connected with a reason" — the reason is `title`-only; visible text is the fixed string "OpenRouter: not connected" (`app.js:142-144`). |
| AC6.1.1–AC6.1.3, AC6.2.1–AC6.2.4, AC6.3.1–AC6.3.2 | **I** | These are operator/developer and build facts. Legitimate for this persona-as-operator, but they are not screen outcomes, and grouping them under "Open and run" on the journey axis is what makes the map read as a user journey when it is not. |

**Action:** keep one user-visible restatement in the story and move the assertion to US6 (or to the
traceability target), so the acceptance tests written first against these criteria are written
against the right contract.

### 4. The journey the draft describes vs. the journey the page runs

**4.1 The map's horizontal axis does not match the page.**

The real first-run path, read off `app.js` and `index.html`:

```
page load
  └─ refreshHistory() fires before the user touches anything           (app.js:128)
  └─ pill repaints from /auth/status, then every 20s                   (app.js:175)
  └─ (optional) click the pill  ->  full-page redirect to OpenRouter   (app.js:159-168)
        and back via /auth/callback                                    (routes.py:146-157)
paste text -> Analyse -> button disables -> result panel -> history row  (app.js:109-126)
```

Two consequences for the map:

- **"Review history" precedes "Submit text"** for a returning user, because history is fetched on
  load. The map puts them in the opposite order.
- **"Choose the engine" and "Connect the live model" are one control.** Engine selection is config
  or session state; the only page affordance is the pill's click (`app.js:159-168`). US4.1, US4.3
  and US4.4 are *properties of the system*, not steps the user takes. Cut the axis three ways —
  **on load / user-initiated action / system property** — or refined-mockups will go hunting for
  four engine screens that do not exist.

**4.2 US4.3's criteria cannot all be true, and none of them are the story the persona needs.**

`AC4.3.1` sets up "live mode chosen, no usable key". In that state `load_settings` returns
`mode="openrouter", api_key=None` with the explicit comment that this is "no longer a startup
failure" (`app/config.py:112-121`); `effective_connection` therefore yields `mode="dummy"`
(`app/service.py:31-57`) and `get_client` builds `DummyClient` (`app/service.py:60-82`). A submit
returns **200 with an offline result**. There is no reachable "attempt a live analysis" in that
state, so **AC4.3.2's failure and AC4.3.3's not-connected reading describe a state the story's own
Given block cannot produce.** The only live-attempt failure in the system is a *rejected session
credential* → 502 `AUTH_EXPIRED` (`app/routes.py:211-221`) — that is US5.2's territory.

What the user actually experiences here, and what the story should say, is the persona's own top
pain point inverted: **a submit succeeds, offline, while the page shows a red pill and no other
explanation.** The missing AC is the disclosure — an offline result must be unmistakable on the
result itself, not only on a pill the user may not connect to the number they are reading.

**4.3 The sign-in return leg is a dead end.**

`/auth/callback` redirects to `/?auth=failed` on a missing code or a failed exchange, and to
`/?auth=connected` on success (`app/routes.py:151,156-157`). **`app.js` never reads the query
string** (verified: no `URLSearchParams`, no `location.search` anywhere in the file). So a denied
or failed authorization reloads the page and tells the user **nothing**; the only signal is the pill
still being red. This is exactly the "what do they see after a failure" question, and no story or AC
covers it. Add to US5.1: the return leg's outcome is stated on the page (success, and each failure —
missing code, exchange failure), plus the pending state while the browser is away at OpenRouter.

**4.4 Disconnecting has a control and no story.**

`POST /auth/disconnect` exists (`app/routes.py:161-168`) and the pill's click performs it
(`app.js:164-168`), but no requirement mentions disconnecting and no story covers it. Either add
US5.3 or record the control as deliberately unspecified — a user-visible affordance cannot be absent
from the set and still be handed to design.

### 5. Screen states the page has and the story set does not

Applying the five-state rule (empty / loading / success / error / partial) to what
`app.js` + `index.html` actually render:

**5.1 Empty state — and a real defect in it.** `history-empty` ("No analyses yet.", `index.html:169`)
is visible in the initial markup, and `historyEmpty.hidden` is only recomputed *after* the fetch
resolves (`app.js:67,79-86`). A returning user with stored rows therefore sees a **flash of the
wrong empty state** on every load, and there is no loading indicator for history at all. Also, the
empty state offers no primary action, against the workspace guide's "illustration + explanation +
primary action" rule. No AC covers the first-run screen — which is the very first thing P1 sees.

**5.2 Loading state.** On submit, the only in-flight feedback is `submitButton.disabled = true`
(`app.js:118-124`). No label change, no spinner, no timeout message. In live mode this is a
multi-second network round trip to OpenRouter with the user staring at a greyed button. No story
covers it; the guide's loading rule (feedback plus a timeout message after 5s) is unaddressed.

**5.3 Partial/edge state — intensity will render "NaN".** `index.html:157` renders an "Intensity"
line, the lede promises "an intensity score" (`index.html:122`), and `app.js:51` formats it
unconditionally. Requirements A1 and Out-of-Scope **drop intensity from v1** ("intensity is dropped
from v1 rather than stored"). Untouched, v1 ships a result panel reading `Intensity: NaN` and a lede
promising a value that no longer exists. This is a user-visible consequence of a scope decision with
no story and no AC — it needs one line in US2.1 or an explicit removal story.

**5.4 Error state — two defects, neither covered.** (a) `submitAnalysis` returns on `!response.ok`
after `showError(...)` **without clearing `resultPanel`** (`app.js:96-99`), so a failed submit
leaves the *previous* result fully visible next to a fresh error, with nothing marking it stale —
the user can read the old label as the new answer. (b) `readErrorMessage` renders
`` `${payload.error.code}: ${payload.error.message}` `` (`app.js:29`), so the user is shown
"SENTIMENT_ENGINE_ERROR: …" / "AUTH_EXPIRED: …" — raw machine codes in the UI, which the workspace's
own guide forbids (heuristic 9, "Never show raw error codes"). The code belongs in the payload; the
visible text should name the action ("… supply a key in config.local.toml").

**5.5 Long text.** No `maxlength`, no counter, and `.history-text` renders the submitted text whole
(`index.html:177`). A long paste is unranged in the input and unbounded in the list. Either add
a bound or an AC for the long-text rendering; the requirements already flag the live-mode provider
limit as open.

### 6. Where the draft decides UI that is design's to decide

The wording is goal-first, which is right — but three criteria pin presentation and should be
restated as observability of the fact:

- **AC3.1.1** mandates that a history *row* carry probabilities, model id and provider. Whether a
  row shows probabilities inline, behind an expansion, or not at all is a design decision. Restate:
  the values are reachable from the history view.
- **AC4.4.2** pins the current pill. Restate: some surface on the page shows the active engine and
  connection state, and it updates without a restart.
- **US3.1's goal** — "when I ask for a number of them" — describes a control the page does not have
  (`app.js:80` hardcodes 50). Either this is an API story, or it is a genuine design question
  ("does the page need a limit or a 'show more' control?"). Do not leave it phrased as an existing
  user action.

What the draft does **not** decide, and should not: layout, colour, where the pill sits, modal
vs. redirect for sign-in. Good — keep it that way.

### 7. Accessibility baseline to fold into the AC text (WCAG 2.1 AA)

Applied to the surfaces that exist today; this is a baseline, not a claim about the human behind P1.

- **Connection state is colour-coded and its reason is invisible.** The pill conveys state by
  `#b00020` / `#1a7f37` (`index.html:75-93`) on `background: Canvas` while the page opts into
  `color-scheme: light dark` (`index.html:9`). In the dark scheme, over a canvas of #121212–#1e1e1e,
  those resolve to roughly **2.3–2.9:1** (red) and **3.3–4.1:1** (green) at 0.85rem — below the
  4.5:1 normal-text minimum at every plausible dark `Canvas` value (arithmetic on the declared
  colours; the exact figure depends on the browser). The text label is present, which saves 1.4.1;
  contrast still fails.
- **A state change is announced to nobody.** `setInterval(refreshConnection, 20000)` (`app.js:175`)
  can flip the pill when a credential expires, with no `aria-live` region; a screen-reader user is
  never told the engine changed.
- **The reason is hover-only.** `connectionIndicator.title` carries connected/reason and the
  click instruction (`app.js:139-141`). `title` is not reachable by keyboard or touch, so AC5.2.2's
  "with a reason" is not actually perceptible. Need a visible text affordance.
- **Touch targets below the guide's floor.** The pill (0.35rem/0.85rem padding, `index.html:75-93`)
  and the submit button (0.5rem/1rem, `index.html:35-38`) both resolve to roughly 34–40px, under the
  44×44 minimum the workspace's own accessibility guide states.
- **Positive notes, so they are not lost in the fix:** the error panel is `role="alert"`
  (`index.html:140`), the result panel is `aria-live="polite"` (`index.html:145`), the textarea has
  a real `<label for>` (`index.html:126`), and rendering is `textContent` throughout (no XSS sink).

Suggested AC text (paste-ready, add to the relevant stories):

- *Given the page in either colour scheme, when I read the connection state, then the visible text
  names the state and the reason, and the text meets 4.5:1 against its background.*
- *Given the connection state changes while the page is open, when it changes, then the change is
  announced through an `aria-live` region.*
- *Given a failed submit, when the error is shown, then no machine code is rendered and any previous
  result is cleared or explicitly marked out of date.*
- *Given the page is loading its history, then no "No analyses yet." message is shown before the
  stored rows arrive.*

### 8. Concrete edits, in the lead's format

1. **US4.3 — rewrite.** Goal stays (one-step fix). Criteria: (a) with live mode selected and no key,
   the page reads not-connected at all times and a submit still returns an offline result;
   (b) that result is visibly marked as produced by the offline stand-in; (c) the connection reason
   names the file to fill in and is visible as text, not a tooltip. Drop the unreachable
   "live analysis attempt fails" criterion or move it to US5.2's rejected-credential path.
2. **US1.2 — split.** UI criterion: an inline message beside the textarea, focus moved to it, no new
   history row. API criterion (`422 INVALID_TEXT` + envelope) moves to the boundary/US6 group.
3. **US3.1 — split.** User story keeps ordering, row content reachable, and the empty/loading states.
   The three limit criteria move to an API-boundary story.
4. **US4.1 — trim.** AC4.1.2 (offline suite) moves to US6.1, where the testing posture already lives.
5. **US2.1 — add** the intensity resolution (remove the row and fix the lede, or keep it in scope)
   and the "offline result is disclosed" criterion.
6. **US5 — add** the return-leg outcomes, the pending state, and disconnect (or record disconnect as
   deliberately unspecified).
7. **US6.2 — reconcile with `team.md` `## Deployment`** ("Deleting `data/sentiment.db` is acceptable
   recovery, and a schema change is handled by recreating the local database") before this stays a
   Must Have. As written it promises in-place migration keeping rows, the CodeKB records only
   `CREATE TABLE IF NOT EXISTS`, and the persona names "losing stored results to a schema change" as
   a pain point. One of the two artifacts has to move.
8. **Provenance.** `stories.md` opens with "Q4 = A" and "Q5 = A", but `user-stories-questions.md`
   lines 66 and 78 carry empty `[Answer]:` fields. The *substance* the draft applied matches option A
   in both cases, so this is a write-back gap, not a wrong choice — but the answers must be recorded
   or the citation removed before the stage closes.

## Positions

- **AGREE:** One persona (Q1 = A) is faithful to the scan's single human actor — `business-overview.md` "Actors and Stakeholders" names one local user and one operator, and `team.md` independently records one person as sole user, operator and decision-maker.
- **AGREE:** Goal-first wording with Given/When/Then criteria satisfies the inception phase rule and gives the first-written acceptance tests a usable source.
- **AGREE:** MoSCoW with nothing marked "Won't Have" is consistent with the requirements' closed Out-of-Scope list; adding a cut here would invent a decision that belongs to delivery-planning.
- **AGREE:** AC1.1.1–AC1.1.3, AC2.1.1, AC4.3.3 and AC4.4.2 are genuinely user-observable and match the shipped page.
- **OBJECT:** AC4.3.2 and AC4.3.3 cannot hold in the state AC4.3.1 describes — `app/config.py:112-121` makes live-mode-without-a-key start on the dummy engine, so a submit returns 200 with an offline result and no "live analysis attempt" exists to fail; the only such failure is the rejected-credential path in US5.2.
- **OBJECT:** US1.2 is tested against a path the page never takes — `app.js:113-116` trims and short-circuits empty input before any fetch, so AC1.2.1's `422 INVALID_TEXT` and AC1.2.3's envelope are unreachable from the page and AC1.2.3 is false for the user's actual empty-input refusal.
- **OBJECT:** AC4.1.2, AC4.4.1, AC4.4.3, AC5.1.2, AC5.1.3 and all of AC6.2.1–AC6.2.4 are internal facts (test-run properties, log lines, `/health`, storage columns) presented as user-story criteria; keep a user-visible restatement in the story and move the assertion to US6 so the pre-written acceptance tests target the right contract.
- **OBJECT:** The story map's journey does not match the page — history is fetched on load before any user action (`app.js:128`), and "Choose the engine" plus "Connect the live model" are one control (`app.js:159-168`), while three of US4's four Must-Haves are system properties rather than steps.
- **OBJECT:** US3.1's goal "when I ask for a number of them" describes an interface that does not exist — `app.js:80` hardcodes `/analyses?limit=50` with no UI control, making AC3.1.2–AC3.1.4 API-only.
- **OBJECT:** The sign-in return leg is uncovered and silent — `/auth/callback` redirects to `/?auth=failed` or `/?auth=connected` (`app/routes.py:151,156-157`) and `app.js` never reads the query string, so a denied or failed authorization gives the user no feedback at all.
- **OBJECT:** The persona's central pain point — telling which engine produced a result — is not served by any AC: `provider`/`model` are stored but never rendered (`app.js:71-76`), and the pill reports only the current state, so a row produced live looks identical to one produced offline.
- **OBJECT:** The draft promises a user-visible Intensity (`index.html:122,157`; `app.js:51`) that v1's own scope deletes (A1, Out of Scope), so an untouched implementation renders `Intensity: NaN` and keeps the lede's promise — a user-visible gap with no story or AC.
- **OBJECT:** US6.2's in-place-migration promise contradicts the team's affirmed recovery practice (`team.md` `## Deployment`: deleting `data/sentiment.db` is acceptable recovery and a schema change is handled by recreating the database) — **this is a judgement call for the human rather than a knowledge dispute**: either FR3.3/US6.2 becomes real construction work and the recovery practice is re-affirmed, or the persona's "losing stored results" pain is dropped and US6.2's criteria become a documented recreate path.
- **OBJECT:** The failure path leaves a stale result on screen — `app.js:96-99` returns on a non-2xx without clearing `resultPanel` — so after a failed submit the previous label stays readable as if it were the new answer; no AC addresses it.
- **OBJECT:** The page renders raw machine codes to the user (`app.js:29` formats `code: message`), which the workspace's own UX guide forbids (heuristic 9); no AC requires the code to stay in the payload while the visible text names the action.
- **OBJECT:** The empty, loading and partial states are absent from the story set although the page visibly has them, including a flash of the wrong empty state for returning users (`index.html:169` is visible in the initial markup while `app.js:67,79-86` only recomputes it after the fetch).
- **OBJECT:** Accessibility gaps that no AC covers — the connection state's colour pair fails 4.5:1 against the dark `Canvas` the page opts into (`index.html:9,75-93`), the state change is never announced (`app.js:175`), the reason lives in a hover-only `title` (`app.js:139-141`), and the pill and submit button fall under the guide's 44×44 touch-target floor.
- **OBJECT:** `stories.md` cites "Q4 = A" and "Q5 = A" while `user-stories-questions.md` lines 66 and 78 have empty `[Answer]:` fields — the applied substance matches option A in both cases, so this needs a write-back of the answers (or removal of the citation), not a changed decision.
- **OBJECT:** `personas.md` does not fix the viewport, the typical text length/language, the offline engine's low fidelity, or first-run vs. returning use — each of which changes at least one story; the page's total absence of media queries makes the viewport a decision, not a detail.
