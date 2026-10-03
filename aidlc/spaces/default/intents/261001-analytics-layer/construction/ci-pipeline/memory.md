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
- 2026-10-03T09:55:00Z — read "the repository has no git remote" as the governing fact for the whole stage rather than an obstacle to work around: it decides which parts of a pipeline are executable today and which are deferred, and it is why no gate runs automatically in this project at all.
- 2026-10-03T09:58:00Z — read the phase-boundary check's own instruction ("if any unresolved finding remains, stop the transition") as binding, and wrote FAIL with a named owning stage per finding instead of reporting a partial pass.
- 2026-10-03T10:00:00Z — read "linter and type-check sensors" as inapplicable rather than green: their globs match TypeScript/JavaScript, the project is pure Python by affirmed mandate, and forcing a fire would have produced a tick no instrument earned.

## Tradeoffs
- 2026-10-03T10:05:00Z — specified J7 and J8 (static security, DAST probe) fully while leaving their instruments uncommitted, rather than re-authoring them here. Build and Test proved both have teeth; `u4-platform-packaging` owns landing them, and duplicating them would repeat the boundary violation R-02 already discloses for `app/terms.py`.
- 2026-10-03T10:06:00Z — used the venv install as J1 rather than the recorded command's bare `pip install`, because the recorded form exits 1 under PEP 668. The recorded command is left untouched and its step-1 failure stays on the record as the human declined to rewrite it.
- 2026-10-03T10:08:00Z — recorded coverage-delta, flaky detection, secret scan, dependency audit and layer-boundary gates as unbuildable with a named owner each, rather than omitting them silently or inventing instruments to satisfy them.

## Open questions
- 2026-10-03T10:10:00Z — the CI tool is the one genuinely open question among the four the stage requires. GitHub Actions is presented as a worked example explicitly labelled as a choice with no evidence behind it, because there is no remote to inspect.
- 2026-10-03T10:11:00Z — a hosted runner's socket policy is unresolved: this suite asserts no network access, and a hosted runner's own traffic model has to be reconciled with that assertion before Tier 1 can run.
- 2026-10-03T10:12:00Z — whether one author satisfies `FR7.2`'s reviewer requirement is unresolved, and it changes what the merge gate can legitimately enforce.
