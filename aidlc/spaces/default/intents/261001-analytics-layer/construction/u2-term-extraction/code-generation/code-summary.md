# Code Summary — `u2-term-extraction`

> **Unit:** `u2-term-extraction` (kind `library`) · the resolved walking skeleton.
> **Stage:** code-generation (construction) · intent `261001-analytics-layer`.

## What this stage actually did

**An adoption.** `app/terms.py` already existed — authored by `u1-analytics-slice`
under the ordering that was later corrected — and already satisfied every item of
this Bolt's Definition of Done before this stage began. This stage verified that
against the specification, recorded the ownership transfer, and closed one code
defect that a review had found.

### Files

| File | Change | Purpose |
|---|---|---|
| `app/terms.py` | **modified** (one line) | The adopted module. The change is the R-01 lowercasing fix in `significant_terms`. |
| `tests/test_terms.py` | **unchanged** | The ten inherited tests. Verified, not rewritten. |

Deliberately **not** written: a new module, a re-derived pattern, a second stopword
list, a helper file, or a test that duplicates an existing one. `BR5.1`'s parity
obligation makes a rewrite risky — re-deriving `TOKEN_PATTERN` is how engine scoring
silently changes — so the adoption is a verification, not a reconstruction.

## Key implementation decisions

**1. Adopt rather than rewrite.** The module exists and works. Rewriting it would
re-derive a pattern whose exact behaviour is pinned by an exhaustive test over 1,110
inputs, for no gain. `unit-of-work.md`'s U2 section says adopt; this stage obeyed it.

**2. The R-01 fix lowercases, even though the real path never needs it.** `tokenize`
already lowercases, so every token reaching `significant_terms` from the analytics
endpoints is lowercase and the defect is unreachable in practice. It was still fixed,
because the operation's declared domain is any `Sequence[str]` (`BR1.2`) and its own
docstring promises an unqualified stopword test. A second caller passing mixed-case
tokens would get inconsistent results — which is the case the rule exists for.

**3. The parity test is not sufficient alone, and this stage says so.** An ordinary
corpus cannot distinguish "the filter was applied to scoring" from "it was not":
no keyword is a stopword, and the shortest keyword (`bad`, `sad`, `poor`) is exactly
`MIN_TERM_LENGTH`, so every keyword survives the length test either way. Both runs
return identical labels. `test_the_offline_engine_never_calls_the_significance_filter`
asserts the *operation boundary* instead, and that is what makes `BR5.2` decidable.
Without it the suite would be green with no teeth.

**4. The leaf boundary was re-checked after the edit.** Step 3 modified the module.
An edit is how a leaf acquires an import, so `BR6.1`/`BR6.2` were re-verified rather
than assumed: the import list is still `__future__`, `re`, `collections.abc`, with
nothing from `app`.

## Definition of Done — verified, not asserted

| DoD item | Evidence |
|---|---|
| Two operations only | public callables in the module resolve to exactly `tokenize`, `significant_terms` |
| Word-splitting rule owned here | `TOKEN_PATTERN == r"[a-z']+"` |
| 3-character minimum owned here | `MIN_TERM_LENGTH == 3` |
| Stopword constant owned here | `STOPWORDS` is an in-repo `frozenset` of **134** words |
| Engine's private `_WORD` deleted | `not hasattr(dummy_client, "_WORD")` |
| Engine calls only `tokenize` | `dummy_client.tokenize is terms.tokenize`; source contains no `significant_terms`, `MIN_TERM_LENGTH` or `STOPWORDS` |
| Parity test exists | exhaustive over 1,110 inputs; corpus shown non-vacuous |
| Fan-out-0 leaf | no `app` import; no I/O |

## Test coverage summary

| | |
|---|---|
| Scoped command | `env -u APPIMAGE python -m pytest -q tests/test_terms.py --cov-fail-under=0` → **10 passed** |
| Full suite | **192 passed**, 0 failed, 0 warnings |
| `app/terms.py` coverage | **100 %** (11 statements, 0 missed) |
| Whole-application coverage | **97.06 %** against the 80 % floor |
| Lint / format | `ruff check` clean; `ruff format --check` clean |

## Deviations from the plan

**None.** Every step landed as written. The one thing worth recording is that **four
of the eight steps were satisfied before this stage ran** — the module arrived
complete. That is a consequence of the ordering correction, not of the plan: U2's
plan was written after the module already existed, and it says so rather than
pretending to build something.

## What this unit now owns, and what it inherits

**Owns:** the five names — `TOKEN_PATTERN`, `MIN_TERM_LENGTH`, `STOPWORDS`,
`tokenize`, `significant_terms` — and the stopword-membership decision that contract
open point **O9** left open. The set holds 134 words and contains no sentiment-bearing
term (`BR4.4`); changing it would move both analytics endpoints' output and require
editing `u1-analytics-slice`'s manifest writes.

**Inherits:** the ten tests as evidence rather than authorship. They were written
against the criteria before the module existed, which is why the ordering satisfied
the team's `custom` posture even though the author was the wrong unit.

## Open items

- **No input-size cap anywhere.** A very large stored `text` column reaches `tokenize`
  unbounded. Recorded as an open gap in `nfr-requirements/security-requirements.md`;
  not this unit's to close.
- **No `ast` import-closure check and no credential scanner** exist. Both named as
  absent in the NFR artifacts. `u4-platform-packaging` owns the scanner (`FR7.3`).
