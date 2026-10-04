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
- 2026-10-02T15:00:00Z — read the scope's unit-major/serial/checkpoint-enabled defaults as binding on the plan rather than re-openable here, so the delivery artifacts describe four one-Unit Bolts under those settings and do not propose changing them.
- 2026-10-02T15:00:00Z — read "the first resolved DAG Unit is the smallest working integrated slice" as a constraint the plan must verify rather than assume, and recorded U1's prerequisites and reach explicitly instead of presenting Bolt 1 as already built.

## Deviations
- 2026-10-02T15:00:00Z — the Construction staffing and mode question was put to the human at Inception rather than after Bolt 1's verified skeleton, which the affirmed rule prescribes for skeleton-on. The human's preference (one session, continue automatically) is recorded here and in the plan; the formal autonomous grant is deferred to the post-skeleton point, where it needs a fresh human turn anyway, so the choice is not re-asked.

## Tradeoffs
- 2026-10-02T15:00:00Z — proposed the README's already-proven install-plus-suite-plus-health command as the intent-level verification command over a hypothetical script, accepting that it proves the app boots rather than the analytics slice; FR7.2's script in Bolt 4 is what closes that gap.
- 2026-10-02T15:00:00Z — chose no formal WSJF scoring over a scored ranking, because with one developer and four Bolts the DAG already forces the order and a score would only dress up a choice already made.

## Open questions
- 2026-10-02T15:00:00Z — the four carried-forward contract points (the rounding tie rule, the stopword list and module filename, the analytics-partial surface, and the request timeout) are registered for Construction rather than resolved here.
- 2026-10-02T15:00:00Z — whether the analytics-half of the skeleton's end-to-end proof should extend the verification command once FR7.2's script exists, or stay a manual exercise.

## Re-run — 2026-10-04, the Bolt-ordering correction

## Interpretations
- 2026-10-04T08:45:00Z — read the re-run's purpose as **fixing the mechanism, not the
  record**. `bolt-plan.md` already stated the correct ordering ("Bolt 2 may not be
  deferred behind Bolt 1's terms capability"), and the stage definition states plainly
  that the engine does not consume `bolt-plan.md` for walk order. So renumbering the
  Bolts would have produced a better-looking plan that changed nothing at runtime.
- 2026-10-04T08:48:00Z — read the suppressed `U1 → U2` edge as the **cause** of the
  violation rather than a mitigation of it. The suppression kept `u1-analytics-slice` a
  root so the skeleton ruling could name it first; the engine then walked U1, whose
  approved plan told it to build the terms path, and U1 authored `app/terms.py`. The
  suppression did not prevent the dependency — it prevented the ordering while allowing
  the violation.

## Deviations
- 2026-10-04T08:50:00Z — **the `u1-analytics-slice -> u2-term-extraction` edge is
  recorded in the machine-readable block**, replacing the suppression. This is a change
  to a human-ruled artifact (Q5 fixed `u1-analytics-slice` as the integrated slice) and
  it was made by explicit human decision on 2026-10-04, offered as the only option that
  changes engine behaviour.
- 2026-10-04T08:52:00Z — **the walking skeleton is now `u2-term-extraction`**, and this
  is recorded as a cost rather than presented as an improvement. U2 is a fan-out-0
  library, so the skeleton is its parity test rather than a path through storage and
  HTTP. `u1-analytics-slice` remains the first *integrated* end-to-end path and runs
  immediately after.
- 2026-10-04T08:54:00Z — corrected **every** artifact that asserted the suppression as
  current: `unit-of-work-dependency.md` (including the batch listing, the prose DAG, the
  skeleton section and the constraints list), `unit-of-work.md`, `bolt-plan.md`,
  `risk-and-sequencing-rationale.md`, `team-allocation.md`,
  `external-dependency-map.md`, `unit-of-work-story-map.md`, `contract-summary.md`,
  `contract-design-questions.md` and `delivery-planning-questions.md`. Ten files, because
  leaving any one of them asserting a suppression that no longer exists is the exact
  defect class this correction exists to remove.

## Tradeoffs
- 2026-10-04T08:56:00Z — accepted a weaker skeleton for a structural ordering guarantee.
  The alternative was keeping a strong skeleton on paper while the engine inverted the
  one dependency that mattered.
- 2026-10-04T08:58:00Z — did **not** renumber `U1`/`U2` identities. The units keep their
  names and their Q2 decomposition; only their position changes. Renaming would have
  invalidated every artifact that references them for no benefit.
- 2026-10-04T09:00:00Z — recorded the cost explicitly in the plan itself rather than only
  in this diary, so a reader opening `bolt-plan.md` at the gate sees that the skeleton
  changed and what it now fails to prove.

## Open questions
- 2026-10-04T09:02:00Z — `u1-analytics-slice` is already built against the previous
  ordering and `app/terms.py` already exists. Recording the edge fixes the *order* going
  forward; it does not unbuild U1. `u2-term-extraction` must therefore **adopt** the
  existing module rather than re-derive it, which is recorded in `unit-of-work.md`'s U2
  section.
- 2026-10-04T09:04:00Z — the recorded verification command and the CI pipeline were
  designed against the old Bolt order. Neither depends on which unit runs first, so
  neither needs changing; this is noted so a later reader does not go looking.
