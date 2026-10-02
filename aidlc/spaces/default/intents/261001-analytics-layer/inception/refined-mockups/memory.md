<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T12:40:00Z - read the wireframes' header-and-nav shell as a drawing of structure the page does not have rather than as a description of it, and asked rather than designed around it: index.html has no header, nav or footer, and History is a section rather than an entry point.
- 2026-10-02T12:40:00Z - read "raw error codes are never shown to the user" as a claim about the shipped app rather than about the wireframe's intent, checked it against app.js, found it false, and recorded the analytics view's code-free error text as a deliberate divergence from shipped behaviour instead of quietly matching either one.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T12:40:00Z - asked five questions this stage could have answered by designing around them, because the header-and-nav question changed the page the human uses daily and the other four changed stated behaviour rather than presentation.
- 2026-10-02T12:40:00Z - dropped the wireframes' footer and added no media query rather than restoring either, because the footer's reassurance already lives in the connection indicator and the shipped stylesheet contains no media query at all; both were put to the human and accepted as deliberate omissions.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T12:40:00Z - chose a full nav with three views over adding a single Analytics entry, knowing it restructures a page the human uses daily and changes History's load behaviour, because the story set's own acceptance criterion requires a third entry alongside two that exist.
- 2026-10-02T12:40:00Z - kept the per-day text list a subset of the payload (date and total) rather than a full mirror, accepting that the list is not a complete textual rendering of every field the API returns, so that it stays an exact text equivalent of the plotted line.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T12:40:00Z - FR2.7 fixes four-decimal share rounding with no tie rule, and a tie is reachable: over a denominator of 128 a count of 36 is exactly 0.28125, so half-up gives 0.2813 and half-even 0.2812. FR8.2 requires a hand-pinned share value, so that value is implementation-defined until a rule exists. Registered for requirements.md Revision 3; the mockups pick a tie-free fixture and take no side.
- 2026-10-02T12:40:00Z - whether analytics-partial is acceptable as a polite status region under the ruling that there is only one error surface; the design resolved it that way and flagged it as readable either way.
