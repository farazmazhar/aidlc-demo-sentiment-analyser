<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-09-30T16:10:00Z — designed the mockups directly from the stories and requirements because this scope skips the rough-mockups step and no wireframe exists; the missing input is named in the artifact rather than filled with invented wireframes.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-09-30T16:10:00Z — the specification maps every component to native HTML and the page's existing class names instead of inventing a design system, because the project has none and caps its dependencies at two runtime packages; the mapping artifact states that decision rather than implying a library exists.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-09-30T16:10:00Z — specified only the states the app can actually reach (loading, empty, success, invalid input, live-mode failure) rather than a full state matrix including long-text and offline-versus-live as separate screens; those two live inside the success state and the indicator so the checklist stays checkable.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-09-30T16:10:00Z — whether the two accessibility gaps (connection-state contrast, the 44×44 target floor) can be verified without a browser-based audit in the tooling the project permits; the checklist names the verification method but no automated check exists yet.
