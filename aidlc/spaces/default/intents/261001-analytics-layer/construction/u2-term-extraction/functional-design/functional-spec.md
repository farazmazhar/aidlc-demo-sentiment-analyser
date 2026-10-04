# Functional Specification — `u2-term-extraction`

> **Intent:** `261001-analytics-layer` · stage `functional-design` (construction) ·
> unit `u2-term-extraction` (kind `library`).
>
> **This file is the source of truth for this unit's workflows.** It carries the two
> ordered behaviours the unit performs. `entities.md` is legitimately empty
> (`TermExtraction` owns no entity); `rules.md` carries the decision logic this file
> sequences. No ER diagram is derived, because there are no entities to relate.

## 1. What this unit is

`TermExtraction` is the repository's single tokeniser. It sits beside `app/sentiment.py`
as a fan-out-0 leaf: it imports nothing from `app`, performs no I/O, and holds no
connection. Two callers depend on it — the offline sentiment engine, which needs word
tokens, and the analytics read path, which needs filtered significant terms.

The unit's whole purpose is to make one word-splitting rule exist instead of two. Before
it, the offline engine held a private `_WORD` pattern; the analytics path needed the same
splitting but with a length and stopword filter applied. Promoting the tokeniser and
splitting it into two operations is what lets the second caller filter without the first
caller's behaviour changing at all.

## 2. Module surface

**This project is written before the code; the surface below is the specification the
implementation must satisfy.**

> **Code Generation must ADOPT the existing `app/terms.py` — it must not rewrite it.**
> The module already exists: it was authored by `u1-analytics-slice` under the previously
> suppressed `U1 → U2` ordering, which is the unit-boundary violation disclosed in
> `u1-analytics-slice`'s plan and code summary. It is now this unit's module to own.
> Adopting means: keep the five names and their behaviour as specified here, keep the
> offline engine's `tokenize`-only import, and treat the parity and isolation tests as
> this unit's inherited evidence rather than writing new ones from nothing.
>
> **What is explicitly this unit's to change:** the stopword-membership decision (contract
> open point `O9`, still open — see `rules.md` `BR4.3`). Nothing else in the surface is
> open for redesign, and a rewrite that re-derives `TOKEN_PATTERN` or `MIN_TERM_LENGTH`
> would break `BR5.1` by risking a change to engine scoring.

| Name | Kind | Signature / value | Owner rule |
|---|---|---|---|
| `TOKEN_PATTERN` | constant | `str` — `[a-z']+` | `BR4.1` |
| `MIN_TERM_LENGTH` | constant | `int` — `3` | `BR4.2` |
| `STOPWORDS` | constant | `frozenset[str]` | `BR4.3`, `BR4.4` |
| `tokenize` | function | `(str) -> list[str]` | `BR1.1`, `BR2.*` |
| `significant_terms` | function | `(Sequence[str]) -> list[str]` | `BR1.2`, `BR3.*` |

Per `BR5.3`, `app/dummy_client.py` no longer holds a pattern of its own and imports no
private name from this module. Per `BR6.1`, this module imports nothing from `app`.
Per `BR6.2`, all five names above are pure — no I/O, no clock, no randomness.

## 3. Workflow 1 — tokenising text into words

**Caller:** the offline sentiment engine, via `app/dummy_client.py`.
**Operation:** `tokenize(text)`.

1. Receive `text` as a `str`.
2. **Lowercase it.** Case is not a token character and must not affect membership
   (`BR2.2`).
3. **Scan for maximal runs of `[a-z']`.** Any other character — digit, punctuation,
   whitespace, underscore, dot, hyphen, accented Latin, non-Latin script — ends the
   current run and begins a boundary (`BR2.1`).
4. **Return the runs, in order, as a list of `str`.** No filtering of any kind is
   applied at this step. Short tokens and stopwords are returned like any other
   (`BR1.1`).
5. If step 3 matched nothing — the text was empty, whitespace-only, punctuation-only,
   or entirely in a script outside `[a-z]` — **return an empty list**, not an error
   (`BR2.3`, `BR6.3`).

**The caller's obligation, and the one thing that can go wrong.** The engine must call
*only* this operation (`BR5.2`). If it called `significant_terms` instead, then a keyword
shorter than three characters — or one that happens to be a stopword — would stop being
counted, and the returned label could change for inputs that previously scored one way.
That failure is silent and produces plausible output, which is why `BR1.1` and `BR5.2`
exist as separate rules and why the parity test is required.

**Ordering note.** `tokenize` is the only operation that reads raw text. Everything
downstream operates on its output, so there is exactly one place where the
word-splitting rule is expressed (`BR4.1`).

## 4. Workflow 2 — filtering tokens down to significant terms

**Caller:** the analytics read path (`AnalyticsRead`, owned by `u1-analytics-slice`),
reaching it through the terms endpoint.
**Operation:** `significant_terms(tokens)`.

1. Receive `tokens`, an already-tokenised `Sequence[str]`. **This operation never
   tokenises** (`BR1.2`): if a caller passes raw text, the sequence is iterated
   character by character and the output is nonsense. The failure is not
   self-announcing, which is why the signature annotates `Sequence[str]`.
2. For each token, in input order, apply **two independent tests** (`BR3.1`, `BR3.2`):
   - **Length.** Keep only if `len(token) >= MIN_TERM_LENGTH`.
   - **Stopword.** Discard if `token.lower()` is in `STOPWORDS`. The lowercasing is
     required even though `tokenize` already lowercased, because this operation's
     domain permits any `Sequence[str]` and the rule must hold on its own.
3. **Preserve input order, and do not deduplicate, reorder or count** (`BR3.4`). A
   token appearing twice appears twice in the result. Counting and ranking belong to
   the caller, which accumulates into a `Counter`.
4. **Return the surviving tokens as a list of `str`.**
5. If nothing survives — every token was short, or a stopword, or the input was
   empty — **return an empty list** (`BR3.3`, `BR6.3`). The caller renders that
   label's list as empty and does not fabricate a top-N.

**Why the two tests are independent rather than composed.** A token can fail either
test or both; the outcome is the same, but the rules are pinned separately
(`AC4.1.1` for length, `AC4.1.2` for stopwords) so that a regression in one does not
hide behind the other.

**The empty case is the covered case, not an accident.** `AC4.1.5` requires that text
made entirely of stopwords yields an empty list, and `AC4.1.6` requires that a store
whose rows are all one label yields an empty list for the other label. Both are
reachable in normal use, and both are specified as successes (`BR3.3`).

## 5. Workflow 3 — the offline engine's refactor

**Caller:** this unit owns the refactor; the engine is changed, not written.

1. **Delete** `_WORD` from `app/dummy_client.py` and the `re` import it needed
   (`BR5.3`).
2. **Import `tokenize`** from this module and call it wherever the private pattern was
   used.
3. **Change nothing else about the engine's decision path.** The keyword tables, the
   comparison logic and the returned `SentimentResult` are untouched (`BR5.1`).
4. **Prove the result is unchanged.** A parity test asserts the engine's output over a
   corpus is identical before and after. The corpus must be shown to discriminate: it
   fails if the class widens to include digits, and it fails if the length or stopword
   filter is applied to scoring.
5. **Prove the filter cannot reach scoring.** A test asserts the engine calls only
   `tokenize`, so the analytics filter is structurally unable to influence a label
   (`BR5.2`, `AC4.2.3`).

**An honest limit on step 4, recorded.** No keyword is a stopword, and the engine's
shortest keyword is **exactly three characters** (`bad`, `sad`, `poor`) — so the length
filter is not inert on the keyword set: it would *keep* every keyword, because three
is `MIN_TERM_LENGTH` itself. What the corpus therefore cannot distinguish is not
"was the filter applied" in general but the specific inversion that matters: applying
the filter changes no label on ordinary text, because no keyword is short enough to be
dropped and none is a stopword. Both runs produce identical labels and the parity test
passes either way.

*(An earlier draft of this note said the shortest keyword is "longer than three
characters". That premise was false — it is exactly three — and the review caught it.
The conclusion survives the corrected premise, but the threshold's edge is closer than
the draft implied: a single character removed from `MIN_TERM_LENGTH` would start
dropping real keywords.)*

The parity test therefore has to be complemented by an *instrument* test on the
operation boundary (step 5). Relying on step 4 alone would have produced a green test
with no teeth, which is the failure mode this note exists to prevent.

## 6. What this unit does not do

- **It does not count, rank, or cap.** `Counter` accumulation, tie-breaking and the
  `limit` parameter belong to `AnalyticsRead` in `u1-analytics-slice` (`BR3.4`).
- **It does not read the store.** It never holds a connection and imports nothing from
  `app` (`BR6.1`).
- **It does not decide what a "significant" term means beyond length and stopwords.**
  No stemming, no lemmatisation, no frequency threshold at this layer.
- **It does not handle non-Latin scripts.** A term written entirely in a non-Latin
  script contributes nothing, because `[a-z']` does not match it. This is a **recorded
  accepted limitation** (`AC4.1.3`), not an oversight.

## 7. State transitions

None. This unit owns no lifecycle entity, so there are no transitions to specify — the
same fact `entities.md` records. A token's existence lasts for the duration of one call.

## 8. Traceability into the acceptance criteria

| Criterion | Where it is satisfied |
|---|---|
| `AC4.1.1` | Workflow 2 step 2, length test — `BR3.1` |
| `AC4.1.2` | Workflow 2 step 2, stopword test — `BR3.2` |
| `AC4.1.3` | Workflow 1 step 3, boundary rule — `BR2.1`; limitation in §6 |
| `AC4.1.4` | §2 surface, `STOPWORDS` — `BR4.3` |
| `AC4.1.5` | Workflow 2 step 5 — `BR3.3` |
| `AC4.1.6` | Workflow 2 step 5, and §4's covered-case note — `BR3.3` |
| `AC4.2.1` | Workflow 3 step 1 — `BR5.3`, `BR4.1` |
| `AC4.2.2` | Workflow 3 steps 3–4 — `BR5.1` |
| `AC4.2.3` | Workflow 3 step 5, and Workflows 1/2 separation — `BR1.1`, `BR5.2` |

## 9. Cross-cutting acceptance criteria this unit also carries

The story map's cross-cutting table reaches two of U1's stories into this unit, because
the properties they assert hold for the leaf module too. They are satisfied here, and
they are mapped in `traceability.json` rather than left implicit:

| Criterion | Where it is satisfied |
|---|---|
| `AC8.2.1` | §1 and §6: the module makes no network call, holds no HTTP client and does no model inference — `BR6.1`, `BR6.2` |
| `AC8.2.2` | §2: no key reaches any constant, function or artifact — `BR6.2` |
| `AC8.2.3` | §1 and §6: the module imports nothing from `app` and never touches the live client — `BR6.1`, `BR6.2` |
| `AC8.6.1` | §2: the surface carries a docstring, full annotations, `from __future__ import annotations`, no underscore-public helpers and `UPPER_CASE` semantic constants — `BR4.5`, `BR6.1` |
| `AC8.6.2` | §2: no request or response shape is declared here at all; the module returns plain `str` sequences — `BR6.1` |
| `AC8.6.3` | §2: there is no `utils.py` or `helpers.py`; every name lives with the concept it serves — `BR6.1` |
| `AC8.6.4` | §6: the module consumes no configuration value, so it adds none — `BR6.2` |

`AC8.6.2` and `AC8.6.4` are satisfied in the **negative** sense their own text allows:
`AC8.6.2` requires stdlib dataclasses and no `pydantic`, and this unit declares no shape
at all; `AC8.6.4` requires that if no configuration value is needed then none is added,
and none is.
