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
- 2026-10-03T11:40:00Z — read "execute the deployment" as genuinely executable rather than ceremonial: the release is a commit, so the work is verifying checks, releasing, and proving the released thing serves over real HTTP.
- 2026-10-03T11:43:00Z — read "dependent services healthy" as satisfied by there being none, and recorded that as the finding rather than manufacturing a dependency to check.
- 2026-10-03T11:46:00Z — read the migration step as "exists, tested, not required" and proved the no-op non-vacuously: the real boot was inert, so the genuine v3 -> v4 transition was run on an isolated seeded copy driven to v3 by the old code's own init_db.

## Deviations
- 2026-10-03T11:48:00Z — R8 (the release tag) was deliberately not executed. Creating a tag is a human decision; the step is recorded with its exact command and left for the operator.
- 2026-10-03T11:50:00Z — recorded a caveat that cuts against the enforcement this stage was asked to confirm: `uvicorn --host` on the CLI bypasses `resolve_bind_host`, so the bind is enforced on the documented run path but a hand-typed `--host 0.0.0.0` would override it. Hidden, that would have turned a real gap into a false assurance.
- 2026-10-03T11:52:00Z — the first smoke run showed 8 failures, all of them defects in the harness's expected substrings (compact vs spaced JSON) plus one wrong expected code. Every HTTP status the app returned was already correct. Recorded as a harness correction, not an application fix, and no application behaviour was changed.

## Tradeoffs
- 2026-10-03T11:54:00Z — took R5's store backup inside the gitignored path before cutover, accepting a stray `.bak` file over an unrecoverable migration. It is the only copy of the operator's data that has ever existed.
- 2026-10-03T11:56:00Z — seeded smoke data through the real write path (`/v1/analyze`, `/v1/analyses`) rather than inserting rows directly, accepting slower setup for a smoke test that exercises the same code a user does.
- 2026-10-03T11:58:00Z — raised the unbounded-series payload as an observation routed to `u3-analytics-view` rather than filing it as a defect or fixing it here: a 100-year window returns 36,525 zero-filled entries, and the contract sets no bound. That is a contract decision, not a code-generation one.

## Open questions
- 2026-10-03T12:00:00Z — the release tag R8 is unexecuted and remains the operator's decision.
- 2026-10-03T12:01:00Z — the `--host` bypass means loopback enforcement is a property of the documented run path, not of the process. Whether to close that is an operations decision with a security consequence.
- 2026-10-03T12:02:00Z - the analytics payload grows linearly with the requested range and nothing bounds it. A 100-year window answers with roughly 7 MB. Routed to `u3-analytics-view` as an open question.
