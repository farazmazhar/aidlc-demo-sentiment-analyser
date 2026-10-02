<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
- 2026-10-02T00:00:00Z — read ruling 2's unit (1) as owning both `/v2` handlers and the whole read layer, and ruling 5's "summary region" as the `US6.2` readouts that complete the slice. U1 therefore holds the terms endpoint too, and the terms capability's reach into U2 is recorded as a named integration point rather than a DAG edge.
- 2026-10-02T00:00:00Z — `US7.7` (ASGI harness) and `US8.7` (real-value tests) are placed in U1, not U4. The harness is a runtime test instrument that the R-01 concurrency test depends on; leaving it in U4 would put a dependency between the skeleton unit and the packaging unit.
- 2026-10-02T00:00:00Z — `US7.6` (loopback enforcement) is placed in U1, not the packaging unit: it lands in `Application Assembly`, a runtime component, and the brief's packaging set names only `US7.1`–`US7.5`, `US7.8`, `US7.9`.

## Deviations
- 2026-10-02T00:00:00Z — did not draw a `u1-analytics-slice -> u2-term-extraction` edge even though the terms handler consumes U2's operation. Ruling 5 requires U1 to be the first resolved unit, which is only possible if U1 is a DAG root; the edge is instead documented as the one cross-unit integration point. U3 carries the real dependency on both.
- 2026-10-02T00:00:00Z — did not turn `US7.9`'s content dependency on `US2.1`/`US3.1`/`US6.1` into a `u4-platform-packaging` edge, because ruling 6/Q6 declares the platform unit independent of everything; the dependency is recorded in the story map and unit notes.

## Tradeoffs
- 2026-10-02T00:00:00Z — chose to keep both `/v2` handlers in U1 (following ruling 2's explicit "`/v2` HTTP surface") and accept the U1/U2 integration prose, rather than move the terms endpoint into U2 to get a clean `u2 -> u1` edge. Ruling 2's unit framing was judged the stronger constraint.
- 2026-10-02T00:00:00Z — put `US6.2` in U1 because it is marked *slice* and completes the summary path end to end (`US1.1 → US2.1 → US2.2 → US2.3 → US6.2`), even though it also introduces term-list containers whose extraction is U2's. This keeps the skeleton slice whole and leaves `US6.1`/`US6.3`/`US6.4`/`US6.5` in U3.

## Open questions
- 2026-10-02T00:00:00Z — confirm with Delivery Planning that the U1/U2 integration point (terms path) does not need promotion to a DAG edge once the economic plan is chosen; the ruling made U1 first, but a plan that starts U2 first may prefer to model it explicitly.
- 2026-10-02T00:00:00Z — the packaging unit's lockfile format, scanner/audit tool and licence remain open per requirements; they are resolved inside U4 and do not affect this DAG.

## Revision 1 — review findings and the two follow-up rulings

- 2026-10-02T14:10:00Z — **R-02 correction.** The `u3-analytics-view → u2-term-extraction`
  edge was removed and replaced with `u3-analytics-view → u1-analytics-slice`. It had
  been justified by "the term lists", which `US6.2` delivers under `U1`, not `U2`;
  `U3` fetches `U1`'s endpoints and never imports `TermExtraction`. The edge set had
  been inverted relative to the imports the components imply.
- 2026-10-02T14:10:00Z — **R-01 recorded rather than hidden (Q8 ruling).** The real
  `U1 → U2` import is a suppressed edge: it exists, it is stated, and the reason it is
  not drawn is that drawing it demotes `U1` from a DAG root and breaks the skeleton
  ruling. A binding note tells Delivery Planning not to sequence `U1`'s terms work
  ahead of `U2`.
- 2026-10-02T14:10:00Z — **R-03 recorded rather than absorbed (Q9 ruling).** `US6.2` is
  a split deliverable: `U1` owns the series and label-breakdown region, `U3` owns the
  two term-list containers `AC6.2.1` requires. The story map carries a cross-cutting
  row and the `OK` target stays `U1` so the sensor's single-valued join holds.
- 2026-10-02T14:10:00Z — **R-04 confirmed.** `U2`'s empty `entities.md` and `rules.md`
  are intended, not skipped: `TermExtraction` owns no entity or rule, and fabricating
  either would be worse than an explicitly empty artifact.

- 2026-10-02T14:10:00Z — **Revision 1 interpretation.** Read the "first resolved unit"
  requirement as a constraint on the DAG's *shape* rather than on its numbering: `U1` is
  a dependency-free root because the summary slice genuinely needs nothing from the other
  units, not because it was declared first.
- 2026-10-02T14:10:00Z — **Revision 1 tradeoff.** Kept `US6.2`'s `OK` target as `U1`
  after recording its split, because the traceability sensor joins on a single target per
  row; the `U3` half is named on the row and in the reverse entry. A multi-target row
  would have been more expressive and less checkable.
- 2026-10-02T14:10:00Z — **Revision 1 tradeoff.** Chose a suppressed-but-stated edge over
  either a silent omission or a drawn edge, accepting that the DAG alone no longer tells
  the whole dependency truth, in exchange for keeping the skeleton unit valid and the
  constraint auditable in prose.
