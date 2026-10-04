# Stage Diary — nfr-requirements, `u2-term-extraction`

## Interpretations
- 2026-10-04T09:40:00Z — read the **four absent requirement files** as correct rather than an
  omission, and verified it against the stage frontmatter rather than assuming: `produces_kinds`
  restricts `performance-requirements`, `scalability-requirements`, `reliability-requirements`
  and `observability-requirements` to `[service]`, and this unit is kind `library`. Three
  artifacts is the right count, not a truncated set.
- 2026-10-04T09:44:00Z — read the module's security surface as genuinely near-empty and said so
  per element. Five of six STRIDE categories do not apply and each says why with the reason,
  rather than being padded into a threat model a pure function does not have.

## Deviations
- 2026-10-04T09:48:00Z — **the parent NFR numbering was wrong and the review caught it.**
  The security requirements were keyed to `NFR1`, which is canonically **Performance**;
  Security is `NFR2`. Corrected throughout: six sub-requirements renumbered, the traceability
  parent map rebuilt, and the header carries a note recording the slip rather than a silent fix.
- 2026-10-04T09:52:00Z — **two verification methods named instruments that do not exist.** An
  `ast` import-closure check and a fan-out-0 isolation test were both cited; `grep` finds
  neither anywhere in the repository. Both entries now name what actually exists — the module's
  real three-line import list, and the offline guard at `tests/conftest.py:286` — with an
  explicit statement that the invented checks are absent and must be written if wanted. A third
  instance of the same class was caught in `NFR2.2`, which had implied a fake-key allowlist
  existed when `FR7.3` is open and `u4-platform-packaging` owns it.
- 2026-10-04T09:56:00Z — **the `N/A` on `NFR7` was too broad and is corrected to `OK`.** The
  parent is Testability; it is stated in terms of SQLite and markup because that is the
  feature-level framing, and this unit owns `tests/test_terms.py` with ten tests. Marking it
  `N/A` avoided work by misreading the parent's scope.

## Tradeoffs
- 2026-10-04T09:58:00Z — **recorded the DoS gap as open rather than covered.** An earlier draft
  claimed `u1-analytics-slice` bounds the input by reading rows from a range. The review
  correctly rejected that: a range bounds the **number of rows**, not the size of any one
  `text` column, and contract C3 declares this boundary's input as "any `str`" with no cap
  anywhere. The artifact now states the gap, names who owns closing it (`u1` for the read path,
  Requirements Analysis for the contract) and routes it to the backlog instead of marking it
  handled.
- 2026-10-04T10:00:00Z — declined to add a cap inside the module even to close the gap. A policy
  limit in a pure function is invisible to callers and untestable at the right layer; the fix
  belongs upstream, and this unit's contribution is to record the gap rather than paper over it.

## Open questions
- 2026-10-04T10:02:00Z — **nothing bounds the size of a stored `text` column.** A single very
  large row reaches `tokenize` unbounded and allocates a proportional token list. Not this
  unit's to close; recorded in `security-requirements.md` and in `traceability.json`'s `NFR2` row.
- 2026-10-04T10:04:00Z — no `ast` import-closure check and no credential scanner exist. Both are
  named in verification sections as absent. `u4-platform-packaging` owns the scanner (`FR7.3`).
