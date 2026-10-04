# Stage Diary — functional-design, `u2-term-extraction`

## Interpretations
- 2026-10-04T09:10:00Z — read `unit-of-work.md:150`'s expectation that U2's `entities.md`
  and `rules.md` be **explicitly empty** and agreed with it for entities, disagreed for rules.
  `TermExtraction` genuinely owns no entity — ADR-005 and `components.md` both say so, and
  a token has no identity or lifecycle — so `entities: []` is the honest artifact.
- 2026-10-04T09:14:00Z — read the same expectation for `rules.md` as **too small an
  estimate**, and departed from it deliberately with the departure disclosed in the file
  itself. The unit record predicted "no business rule of its own beyond the single
  word-splitting/stopword constant". Twenty rules across six groups is the reality: the
  two-operation split, the filtering order, case-insensitivity and scoring parity are all
  decisions with a right answer, and tests already pin three of them. An empty file would
  have hidden six groups of real constraint.

## Deviations
- 2026-10-04T09:18:00Z — wrote 20 rules where the unit record expected roughly none, and
  recorded that as a deviation inside `rules.md` rather than silently. The alternative —
  an empty file matching the expectation — would have been accurate about the unit's size
  and wrong about its content.
- 2026-10-04T09:20:00Z — left contract open point **O9** open. `BR4.3` fixes the stopword
  set's shape and governance; `BR4.4` fixes one property of its contents. Which particular
  words belong in the set remains U2's decision and is not settled here.

## Tradeoffs
- 2026-10-04T09:22:00Z — wrote the parity-test limit into the spec rather than leaving it
  implicit. The engine's shortest keyword exceeds three characters and no keyword is a
  stopword, so an ordinary corpus cannot distinguish "the filter was applied" from "it was
  not" — both produce the same labels. Recording that means the parity test has to be
  complemented by an operation-boundary instrument rather than trusted alone, which is how a
  green test with no teeth gets avoided.
- 2026-10-04T09:24:00Z — specified the two filter tests as **independent rules** (`BR3.1`,
  `BR3.2`) even though a token failing either is discarded either way, so a regression in one
  cannot hide behind the other, matching how `AC4.1.1` and `AC4.1.2` are pinned separately.

## Open questions
- 2026-10-04T09:26:00Z — `app/terms.py` already exists, built by `u1-analytics-slice` under
  the previously suppressed ordering. This stage specifies the module that exists rather than
  a hypothetical one, so U2's Code Generation must **adopt** the file rather than rewrite it.
  The stopword membership it inherits is U2's to confirm or change.
- 2026-10-04T09:28:00Z — `BR5.2` is the rule most likely to be broken by accident: the engine
  and the analytics path both tokenise, and calling the filter in the wrong place produces
  plausible output with a changed label. It has no natural test that catches it by outcome,
  which is why it is paired with an operation-boundary assertion.
