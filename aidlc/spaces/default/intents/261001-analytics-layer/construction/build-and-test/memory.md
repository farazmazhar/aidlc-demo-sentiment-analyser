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
- 2026-10-03T09:20:00Z — read "the recorded verification command fails" as an environmental constraint to document with evidence, not as a quality target to relax; proved the PEP 668 block pre-existing on a pristine clone of the Bolt's own commit, executed the venv remedy to show the suite is green without it, and weakened nothing.
- 2026-10-03T09:25:00Z — read the stage's failure predicate as firing on the two Unverified targets while every executed command was green, and said exactly that rather than rounding the stage up to a pass.
- 2026-10-03T09:30:00Z — read a target whose instrument needs a deliverable another Unit owns as Unverified, never N/A and never deferred-successfully: no later validation stage owns it, so deferral would have been a fiction.

## Deviations
- 2026-10-03T09:22:00Z — every documented command is prefixed `env -u APPIMAGE`. The shell exports APPIMAGE, which makes CPython report the AppImage as sys.executable and broke a budget test's subprocess spawn with exit 130. Fixed inside this stage's remit with no file edited; recorded because an unprefixed copy of the instructions fails on this host.

## Tradeoffs
- 2026-10-03T09:35:00Z — took the human's Accept on NFR4.6 and NFR4.7 rather than re-running Delivery Planning or absorbing the view work. Accepted two targets staying unverified until Bolt 3 in exchange for not invalidating Bolt 1's reviews and not deepening the disclosed app/terms.py boundary violation.
- 2026-10-03T09:36:00Z — declined to add a test for either unverified target. A test written against markup u3-analytics-view has not built would assert nothing, and adding tests is not the remedy for a missing deliverable.

## Open questions
- 2026-10-03T09:40:00Z — the recorded verification command still fails its first step on externally-managed hosts. Option D (rewrite it to install into a venv) was offered and not taken. It edits a human-approved Delivery Planning artifact, so it stays open deliberately rather than silently.
- 2026-10-03T09:41:00Z — the cross-unit gate verdict is FAIL as written: no FR id is ever a row in a code-generation traceability, and 46 absent ACs belong to the three unbuilt Units. Surfaced at the gate, not acted on; changing the gate's specification or the upstream traceability contract is not this stage's to do.
