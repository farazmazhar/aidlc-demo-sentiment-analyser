# Stage Diary — nfr-requirements, `u2-term-extraction`

## Interpretations
- 2026-10-04T09:40:00Z — read the four absent requirement files as correct rather than an
  omission, verified against the stage frontmatter: `produces_kinds` restricts
  `performance`, `scalability`, `reliability` and `observability` requirements to `[service]`,
  and this unit is kind `library`. Three artifacts is the right count.
- 2026-10-04T09:44:00Z — read the module's security surface as genuinely near-empty and said so
  per element. Five of six STRIDE categories do not apply, each with its reason, rather than
  padded into a threat model a pure function does not have.

## Deviations
- 2026-10-04T09:48:00Z — **the parent NFR numbering was wrong.** Security requirements were
  keyed to `NFR1`, canonically Performance; Security is `NFR2`. Six sub-requirements
  renumbered, the parent map rebuilt, and the header carries the slip rather than a silent fix.
- 2026-10-04T09:52:00Z — **two verification methods named instruments that do not exist**: an
  `ast` import-closure check and a fan-out-0 isolation test. Neither exists anywhere. Both now
  name what does — the real three-line import list and the offline guard at
  `tests/conftest.py:286` — with the absence stated explicitly. A third instance was caught in
  `NFR2.2`, which had implied a fake-key allowlist existed when `FR7.3` is open.
- 2026-10-04T09:56:00Z — **`NFR7` was marked `N/A` too broadly** and is corrected to `OK`. The
  parent is Testability, stated in SQLite-and-markup terms because that is the feature-level
  framing; this unit owns ten tests.
- 2026-10-04T10:20:00Z — **the renumbering was applied to two files and not the third.** The
  first review pass caught the numbering; the second caught that `tech-stack-decisions.md` still
  cited `NFR1.x` and reasserted the very isolation test its sibling had just declared absent.
  Two artifacts contradicting each other about the same guarantee is worse than either being
  wrong alone, because a reader trusts whichever they open first.
- 2026-10-04T10:26:00Z — corrected the dependency-cap citation to **`C-6`**, having first
  written `NFR2.6` (the stopword rule). The cap is a **constraint**, not an NFR; the review
  caught the mis-citation.

## Tradeoffs
- 2026-10-04T09:58:00Z — **recorded the DoS gap as open rather than covered.** An earlier draft
  claimed `u1-analytics-slice` bounds the input by reading rows from a range. A range bounds the
  **number of rows**, not the size of one `text` column, and contract C3 declares this
  boundary's input as "any `str`" with no cap anywhere. The artifact states the gap, names its
  owners, and routes it to the backlog.
- 2026-10-04T10:00:00Z — declined to add an input cap inside the module even to close the gap.
  A policy limit in a pure function is invisible to callers and untestable at the right layer.

## Open questions
- 2026-10-04T10:30:00Z — **nothing bounds the size of a stored `text` column.** A single very
  large row reaches `tokenize` unbounded. Not this unit's to close.
- 2026-10-04T10:31:00Z — no `ast` import-closure check and no credential scanner exist. Both
  named as absent in verification sections. `u4-platform-packaging` owns the scanner (`FR7.3`).
- 2026-10-04T10:32:00Z — three minor mis-citations survive at READY by the reviewer's judgement:
  `NFR2.2` where `NFR2.6` is meant in two rows, and `NFR2.2` where `NFR2.4` is meant in
  `BR6.2`'s source. All resolve to real ids; recorded rather than re-opened.
