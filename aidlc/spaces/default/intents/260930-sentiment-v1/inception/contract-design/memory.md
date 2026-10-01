<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-09-30T17:45:00Z — kept the page's own routes out of the data contract (they serve markup with no schema) while including the health endpoint inside the versioned surface, because the answers pinned "the HTTP surface the unit exposes" as the boundary rather than only the JSON API.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-09-30T17:45:00Z — wrote the version prefix into the contract as `/v1` even though the running routes have no prefix today; the contract therefore describes a change the code must make rather than the current state, which the artifact states so nobody reads it as documentation of what exists.
- 2026-09-30T18:00:00Z — the first draft described the API from the requirements and stories instead of from the running routes, and the review caught three critical mismatches (paths unversioned in code, the history response wrapped, the error envelope nested under `error` with a details array) plus the health fields, the auth endpoints and the engine status codes; the lesson is that a contract artifact must be read back against the code it describes before the review, not after.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-09-30T17:45:00Z — left four contract points as open questions (the live-refusal machine code and status, the absent-limit default, whether health is versioned, the outbound timeout value) instead of inventing values, since Code Generation can wire a stated number but cannot choose a policy.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-09-30T17:45:00Z — whether the `/v1` prefix is worth the churn it costs the page, the tests and the README at this moment, since the only consumer ships with the server; the human confirmed the prefix, and Delivery Planning may still sequence it.
