<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-09-30T10:30:00Z — condensed the draft's thirty-odd candidate questions into eight, covering the five practice areas and only the decisions evidence could not settle; every option carried the drafted answer so the human chose between reasoned positions rather than from a blank page.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-09-30T10:30:00Z — the first guided batch was not written back immediately: one answer came back as "Other" (one branch per scope, merged and tagged with the scope name) and another as "Mixed" without naming the split, so the batch was discussed and re-asked before any answer reached the file; only the settled Q2 and Q3 were written at that point.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-09-30T10:30:00Z — the human's coverage answer counts the whole application against the 80% floor, so tests for the live Jev client become construction work instead of the floor passing by excluding it; the cheaper reading was available and was not chosen.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-09-30T10:30:00Z — where the CI job that runs the suite and the coverage floor lives, given this scope skips the CI Pipeline stage; recorded in the questions file and evidence.md for design and build to settle.
