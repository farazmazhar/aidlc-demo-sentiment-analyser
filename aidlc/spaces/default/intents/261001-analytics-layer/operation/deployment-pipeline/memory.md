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
- 2026-10-03T10:30:00Z — read the CONDITIONAL skip test against the current schema version rather than the deployment model: `## Deployment` and u1's `cicd-pipeline.md` both said "there is no rollback procedure to write, because there is no deployment", and that was true at schema v3 but false once `init_db` began running an additive step against the operator's real store on every startup. The stage applies narrowly for that reason and for no other.
- 2026-10-03T10:33:00Z — read "CD pipeline needs creation" as unmet while "significant modification" did not apply either, and recorded the CD half as inapplicable per element with the rule that rules it out, rather than staging a blue/green pipeline for a project with one process and one file.
- 2026-10-03T10:36:00Z — read the absence of a remote as a constraint on automation only, not on the release procedure itself: every step of R1-R8 is either upstream-recorded or was executed in this run, so the procedure is verifiable by hand today.

## Deviations
- 2026-10-03T10:34:00Z — the standard zero-downtime checklist is answered honestly rather than ticked: most items are N/A, and each names the substitute that actually applies to a recreate strategy on one local process.

## Tradeoffs
- 2026-10-03T10:38:00Z — measured backward compatibility (v3 `init_db` runs clean on a v4 store, rows preserved, all three indexes surviving, then re-upgrades idempotently) rather than asserting it, and made that measurement the justification for expand-only. It is what turns rollback into a `git checkout` instead of a data-recovery exercise.
- 2026-10-03T10:40:00Z — wrote RB3 (destroyed store) with no procedure, deliberately, so its absence is unambiguous rather than implied. An invented recovery path would be worse than a named gap.
- 2026-10-03T10:42:00Z — declined to take the store-mutating step-3 rewrite (Q6) because the human already declined a similar edit to the same artifact; it is recorded as open and theirs to decide.

## Open questions
- 2026-10-03T10:45:00Z — the approved verification command's step 3 migrates the operator's real store, because the default DB path is CWD-relative. A measured `os.chdir` isolation exists but changing the approved command needs the human.
- 2026-10-03T10:46:00Z — whether the pre-release store backup belongs in the README or as an `FR7` requirement is unresolved and is a product decision, not an operations one.
- 2026-10-03T10:47:00Z — the recorded schema version's measured ability to move backwards is a property worth a guard, but no test is proposed here: the property that actually protects a release is already covered.
