# Accessibility Checklist — `very-cool-sentiment-analysis` v1

Target (answer Q3 = A): **WCAG 2.1 Level AA**, with the two gaps the design review measured fixed in
v1 rather than deferred. Each row names the level, the requirement, the page state it applies to, the
current status, and the story that owns the fix. "Verify" means the criterion is plausibly met but the
specification requires a check rather than an assumption.

| WCAG | Criterion | Applies to | Status | Owner |
|---|---|---|---|---|
| 1.1.1 | Non-text content | The connection dot is decorative (`aria-hidden="true"`); no informative images exist | Met | — |
| 1.3.1 | Info and relationships | One `h1`, region headings as `h2`, native lists for probabilities and history, `<label for>` on the textarea | Met | — |
| 1.3.5 | Identify input purpose | No personal-data fields (one free-text box) | N/A | — |
| 1.4.1 | Use of colour | The indicator carries a text label as well as a dot; each probability shows its number as text beside the bar | To fix where the bar colour is the only difference between rows | US5.3 |
| 1.4.3 | Contrast (minimum) | All text ≥ 4.5:1, large text ≥ 3:1 — **the connection-state colours fall below 4.5:1 in the dark scheme the page opts into** | **Fail today → fix in v1** | US5.3, AC5.3.2 |
| 1.4.4 | Resize text | 200% zoom without loss of content or function; the page becomes fully responsive in v1, so re-verify after the layout change | Verify | US5.3 |
| 1.4.11 | Non-text contrast | Probability bars, indicator dot, focus ring and button borders ≥ 3:1 | Verify | US5.3 |
| 2.1.1 | Keyboard | Every control is a native `textarea`, `button` or link; the sign-in flow is a navigation and comes back to a focusable control | Met (verify the return leg) | US6.1, AC6.1.5 |
| 2.4.3 | Focus order | Tab order follows the visual order: header indicator → textarea → submit → result → history | Met | — |
| 2.4.7 | Focus visible | Visible focus indicator on every interactive element (≥ 2px, 3:1 against its background); `outline: none` is not permitted | To fix where the current styles suppress it | US5.3 |
| 2.5.5 | Target size (44×44 project floor; AAA in WCAG 2.1) | The indicator and the submit control are below the floor today | **Fail today → fix in v1** | US5.3, AC5.3.2 |
| 3.2.1 | On focus | Focusing a control changes nothing | Met | — |
| 3.2.2 | On input | Submitting requires an explicit button activation — no auto-submit | Met | — |
| 3.3.1 | Error identification | Empty input and the live-attempt refusal are described in text with an icon, not by colour alone | Met | US2.2, US5.2 |
| 3.3.2 | Labels or instructions | The textarea has a visible label and the lede states what the page does | Met | — |
| 3.3.3 | Error suggestion | The live-attempt refusal names `config.local.toml`; invalid input says what to enter | Met | US5.2, AC5.2.2 |
| 4.1.2 | Name, role, value | Native elements carry their own semantics; the indicator exposes its state in text | Met | — |
| 4.1.3 | Status messages | Result updates, engine-state changes and refusals announce through `role="status"` / `role="alert"` live regions — the page has no live region today | To add in v1 | US5.3, AC5.3.2 |

## The two measured gaps, and what "fixed" means

1. **Contrast (1.4.3).** The connection indicator's colours were measured below the 4.5:1 minimum in
   the dark scheme the page opts into. Fixed means: the indicator's text and its dot meet 4.5:1 and
   3:1 respectively in every state the component defines (offline, live-requested-no-key, connecting,
   live, rejected), checked with a contrast tool and recorded in the pull request.
2. **Target size (2.5.5, adopted at the project's 44×44 floor).** The indicator and the submit control
   are smaller than that floor. Fixed means both become at least 44×44 CSS pixels, including their
   padding, at every breakpoint — without making the header row taller than its content needs.

## How this checklist is verified

- Automated: a browser-based audit (Lighthouse/axe) over each state in `mockups.md`.
- Keyboard: unplug the mouse and complete every story journey, including the refusal paths.
- Screen reader: verify the three live-region announcements (result, engine state, refusal).
- Zoom: 200% and 400%.
- Contrast: measured per state, results recorded next to the criterion.

## Deliberately out of v1 scope

- WCAG 2.2 success criteria (including its 24×24 target-size minimum) — the project adopts the 44×44
  floor instead, which is stricter.
- Full screen-reader conformance testing on Windows and Android readers: the persona is one local user
  on a desktop browser, and the checklist's screen-reader checks are run manually there.
