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
- 2026-10-03T14:05:00Z — read "SLO compliance report" as having no honest numeric answer here, and declined to manufacture one. A burn rate needs a real error budget over a real window; nothing computes an SLI and no window elapses. The substitute is six verification-window gates, all met on their stated single-client fixture, one of which breaks the moment a second client appears.
- 2026-10-03T14:08:00Z — read "cost analysis" as the cost of a local app (dependency count, store growth, process memory, payload bytes) rather than a dollar figure. No dollar figure is estimated anywhere in the artifact set.
- 2026-10-03T14:10:00Z — read "configuration drift" as unobservable in the AWS Config sense but real in five other classes: requirements corrected after code existed, unit-boundary violations, records that measurement disproved, absences that are drift-free by decision, and measured behaviours no requirement claims.

## Deviations
- 2026-10-03T14:12:00Z — discarded the first RSS readings rather than publishing them: the pid lookup had matched the shell instead of the python process. Corrected figures agree with the recorded boot floor, and the wrong ones went nowhere.
- 2026-10-03T14:14:00Z — recorded 8 SLO-report elements, 10 AWS cost elements and 8 drift elements as not-applicable per element, each with its ruling rule and its local substitute, rather than omitting them or filling them with estimates.

## Tradeoffs
- 2026-10-03T14:16:00Z — ranked the backlog by consequence rather than effort, which puts an XS-sized fix (a `busy_timeout`) third behind finishing three Units and creating a backup. The ordering is the argument: a five-second total read outage outranks a tidy diff, but it does not outrank shipping the feature.
- 2026-10-03T14:18:00Z — treated the four upstream-correction revisions and the two unit-boundary violations as drift with named owners rather than as settled history, because they are still live obligations on the record.
- 2026-10-03T14:20:00Z — measured the empty-schema store at 32768 B (8 x 4096 B pages) and growth at 266.2 B/row first-hand to corroborate the load fixture's 288.8 B/row, rather than inheriting the fixture's figure.

## Open questions
- 2026-10-03T14:25:00Z — BL-01 needs a Delivery Planning re-run to fix the Bolt order that put `u1` before `u2-term-extraction`. That is the single change that would clear the most findings.
- 2026-10-03T14:26:00Z — BL-02 needs a human decision, not code: whether the store gets a release-time copy, a per-incident copy, or neither. A per-boot copy was considered and not proposed, because the migration hazard is conditional and a habitual `cp` would erode release discipline.
- 2026-10-03T14:27:00Z — BL-04 is a requirements question before it is a code question: what the export surface is for, given it cannot reach single-analysis rows.
