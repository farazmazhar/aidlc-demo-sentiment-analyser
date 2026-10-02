<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

## Interpretations
- 2026-10-03T00:00:00Z — read the stage's pattern catalogue as a menu that a single-process localhost app mostly cannot use, and said so per family rather than designing mechanisms with no place to exist.

## Deviations
- 2026-10-03T00:00:00Z — recorded the thread-affinity flag's location as two places (the driver-owning module where it is set, and the HTTP edge where the connection is handed over) after the review showed naming only one would leave Code Generation guessing.

## Tradeoffs
- 2026-10-03T00:00:00Z — wrote the request-scoped connection invariant down as a binding constraint rather than relying on the code's current shape, so disabling the same-thread guard is a justified local decision instead of a general licence to share a connection across threads.

## Open questions
- 2026-10-03T00:00:00Z — the FR8.4 concurrency test and its replaced harness do not exist yet, so the design's claim that reverting the fix turns the test red is a forward obligation to be discharged in Code Generation, not a verified fact.
- 2026-10-03T00:00:00Z — the 200 ms budget and the constant statement count are design claims until the FR8.9 fixture and trace hook are implemented.
