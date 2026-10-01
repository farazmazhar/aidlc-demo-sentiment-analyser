# Refined Mockups — Clarifying Questions

Context: this stage refines the interface for the v1 app from the user stories and the requirements.
The classic scope skips the earlier rough-mockups step, so there are no wireframes or user-flow
artifacts to read; the mockups below are designed directly from the stories (`stories.md`, 13 stories,
45 acceptance criteria) and the requirements. The app today is one page (`app/static/index.html` plus
`app/static/app.js`): a text box, a result panel, a history list, and a connection indicator.

Known constraints: localhost only, one persona (the local user), a desktop browser, no design system
or component library in the project, and the team's test posture (acceptance tests first) means these
specifications must be checkable.

---

## Q1. How far should the interface change?

The page works today and the stories mostly refine behaviour rather than invent screens.

- A. Refine the existing single page in place: same sections, clarified states, no structural rework
- B. Restructure the page — separate the analyse and history areas more clearly, still one page
- C. Add a second page for history
- X. Other (please specify)

[Answer]: A. Refine the existing single page in place: same sections, clarified states, no structural rework

## Q2. Which states must each screen specify?

A screen specification that only covers the happy path is not testable. The app already has an empty
state on load and an error path for bad input.

- A. All of them: loading, empty, success, invalid input, live-mode failure, offline-versus-live, and long text
- B. The ones the app can actually reach today: loading, empty, success, invalid input, live-mode failure
- C. Happy path plus invalid input only
- X. Other (please specify)

[Answer]: B. The ones the app can actually reach today: loading, empty, success, invalid input, live-mode failure

## Q3. What is the accessibility target, and are the known gaps in v1 scope?

The independent design review measured two gaps in the current page: the connection-state colours fall
below the 4.5:1 contrast minimum in the dark scheme the page opts into, and the indicator and submit
control fall under the 44×44 touch-target floor. Nothing owns either today.

- A. WCAG 2.1 AA as the target, with both gaps fixed in v1 and a checklist that records each criterion
- B. WCAG 2.1 AA as the target, but record the contrast and touch-target gaps as knowingly deferred with a reason
- C. Keyboard and screen-reader basics only; no stated WCAG level
- X. Other (please specify)

[Answer]: A. WCAG 2.1 AA as the target, with both gaps fixed in v1 and a checklist that records each criterion

## Q4. What happens to the intensity affordance on the page?

Requirements drop intensity from the v1 contract, but the page's lede still promises "an intensity
score" and the result panel renders an Intensity line.

- A. Remove the Intensity line and correct the lede, so the page matches the contract
- B. Keep the line and show it as unavailable
- C. Leave both untouched in v1
- X. Other (please specify)

[Answer]: A. Remove the Intensity line and correct the lede, so the page matches the contract

## Q5. What responsive behaviour should the specification cover?

The page declares a viewport and has no media queries at all today; the persona's context is a desktop
browser.

- A. Desktop-only: state it explicitly, and specify the minimum supported width and what happens below it
- B. Add one narrow breakpoint so the page stays usable on a laptop split-screen or tablet width
- C. Full responsive behaviour across phone, tablet and desktop
- X. Other (please specify)

[Answer]: C. Full responsive behaviour across phone, tablet and desktop
