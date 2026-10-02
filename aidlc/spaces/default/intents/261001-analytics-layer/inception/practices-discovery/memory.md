<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-01T22:12:29Z - read the interview answers as authoritative over spoke positions: where a spoke proposed a rule the human never ruled on, it stayed out of `discovered-rules.md` even when its evidence was the strongest in the run (the security-suppression rule).
- 2026-10-01T22:12:29Z - treated the fourteen interview answers as the only human-stated hard constraints, so rules were derived from the answers rather than from what the code happens to do; observed conventions stayed conventions.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-01T22:12:29Z - presented the fourteen interview questions in two rounds of eight and six rather than one batch, because the audit log binds one recorded answer per human turn and a single batch of fourteen could not be discharged.
- 2026-10-01T22:12:29Z - recorded seven answers from a seven-number reply against eight questions, and six from a seven-number reply against six, rather than guessing the misaligned ones; the surplus or missing item was surfaced to the human instead of assumed.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-01T22:12:29Z - dropped `mean intensity` from the requirement rather than reporting a null field or synthesising a proxy, because a retired column cannot answer the question and a proxy would invent a number the user never defined.
- 2026-10-01T22:12:29Z - chose a platform-neutral verification script over a pre-commit hook and over a provider CI job for the gates, because there is no git remote, so a provider workflow file would be a file that cannot run.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
