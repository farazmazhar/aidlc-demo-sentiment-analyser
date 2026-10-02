<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-01T21:01:52Z - read the intent as an unrecorded project-root repo: the store directory is still `codekb/sentiment-opencode/`, but the link receipts and the developer handoff carry no repo qualifier or suffix, because the intent's registry row records no repo identity.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-01T21:01:52Z - renamed the developer's handoff from `developer-scan-sentiment-opencode.md` to `developer-scan.md` before minting link 1, because the receipt tool requires the unrecorded-project-root filename; the content was untouched and no receipt existed yet.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-01T21:01:52Z - took the full-rescan option on a STALE store rather than a focused merge, so the prior store's prose is replaced wholesale instead of being partially preserved and partly demoted.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
