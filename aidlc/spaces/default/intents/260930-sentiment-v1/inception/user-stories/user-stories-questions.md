# User Stories — Story Plan and Questions

## Plan

**Persona development approach.** One persona: the local user. The reverse-engineering scan found a
single human — the same person runs the app, submits text, reads results and history, and configures
the engine — so the operator and the API client are facets of that one user rather than separate
personas. The operator-facing needs (install, configure the key, see which engine is active) are
covered as stories under that persona.

**Story format.** Standard form, `As a [persona], I want [goal], so that [benefit]`, with INVEST
checks noted. Stable IDs: stories `US{group}.{seq}` (for example `US1.1`), acceptance criteria
`AC{group}.{seq}.{criterion}` (for example `AC1.1.1`), each criterion in Given/When/Then.

**Breakdown approach.** By capability area along the user journey: submit and score, read the result,
browse history, select the engine, connect the live model, and run and configure. The story map's
horizontal axis is that journey; its vertical axis is priority.

**Granularity.** Value-sized stories rather than one per requirement statement: roughly 10–14 stories,
each covering two to four related statements from `requirements.md`, so every story is independently
deliverable and testable.

**Prioritization.** MoSCoW (Must / Should / Could / Won't Have) per story. The MVP boundary is decided
formally in Delivery Planning; these priorities are its input.

**Traceability.** Every `FR` and `NFR` id in `requirements.md` gets a coverage row in
`traceability.json`, with `OK` targets naming real `US` ids.

## Questions

## Q1. Who are the personas?

- A. One persona: the local user who runs the app and uses it
- B. Two personas: the local user who analyses text, and the operator who installs and configures it
- C. Two personas: the local user, and an application client that calls the JSON API
- X. Other (please specify)

[Answer]: A. One persona: the local user who runs the app and uses it

## Q2. How should the stories be broken down?

- A. By capability area along the user journey: submit and score, read the result, browse history, select the engine, connect the live model, run and configure
- B. By the requirement groups already in `requirements.md` (`FR1`–`FR6`)
- C. By workflow step only, one story per step of the analyze journey
- D. By the two modes: a story set for offline use, a story set for live use
- X. Other (please specify)

[Answer]: A. By capability area along the user journey: submit and score, read the result, browse history, select the engine, connect the live model, run and configure

## Q3. How granular should the stories be?

- A. Every statement becomes its own story (roughly 29 stories, each with 3–6 acceptance criteria)
- B. Group statements into value-sized stories — roughly 10–14 stories, each covering two to four related statements
- C. A minimal set of about six end-to-end stories, with the requirements listed beneath each
- X. Other (please specify)

[Answer]: B. Group statements into value-sized stories — roughly 10–14 stories, each covering two to four related statements

## Q4. How should priority be expressed?

- A. MoSCoW on every story, with nothing marked "Won't Have" — everything in the requirements stays in scope
- B. MoSCoW on every story, plus a proposed "Won't Have" cut so the MVP boundary is visible now
- C. MoSCoW on every story, and a proposed order of delivery in addition
- X. Other (please specify)

[Answer]: A. MoSCoW on every story, with nothing marked "Won't Have" — everything in the requirements stays in scope

## Q5. How deep should acceptance criteria go?

The affirmed testing posture writes acceptance/API tests before implementation, so these criteria are
what those tests are built from.

- A. 3–6 criteria per story, always including the failure or edge path alongside the happy path
- B. One happy-path criterion per story, with edge cases left to the later stages
- C. Criteria only for the stories marked Must Have; lighter notes for the rest
- X. Other (please specify)

[Answer]: A. 3–6 criteria per story, always including the failure or edge path alongside the happy path

---

## Q6. How should a live attempt without a usable key behave?

Raised by the mob's independent reviews, so it is answered before the stories are finalised. Your
answer to Q2 (warn at startup, fail on a live attempt) now meets a contradiction on the ground: the
app currently resolves live-mode-without-a-key straight to the offline engine, so a submission
returns a normal offline result and there is no moment at which a "live attempt" fails. An existing
green test pins that behaviour, and one story's criterion (AC4.3.2) asserts the opposite.

- A. Add an explicit attempt path: when the user submits while the live engine was requested and no key is usable, the request fails with the clear message and code, and the existing test is updated to match; the offline default still applies when nothing live was requested
- B. Keep the silent fallback: relax the story to "the app always shows which engine answered and warns that no key is set", and drop the failing-attempt criterion
- C. Fail at startup instead, as the original description asked, and update the test: the app refuses to run live mode without a key
- X. Other (please specify)

[Answer]: A. Add an explicit attempt path: when the user submits while the live engine was requested and no key is usable, the request fails with the clear message and code, and the existing test is updated to match; the offline default still applies when nothing live was requested
