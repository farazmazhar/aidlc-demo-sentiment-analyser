# Business Rules — `u2-term-extraction`

> **Intent:** `261001-analytics-layer` · stage `functional-design` (construction) ·
> unit `u2-term-extraction` (kind `library`).
>
> **Source of truth.** The fenced ```yaml block below is authoritative for the
> business rules. The summary table after it is a derived view.
>
> **Six groups.** `BR1` the two operations and their separation · `BR2` tokenisation
> · `BR3` significance filtering · `BR4` the owned constants · `BR5` scoring parity
> and the refactor · `BR6` module isolation and conventions.
>
> **`unit-of-work.md:150` expected this file to be *empty*.** It is not, and the
> reason is recorded rather than glossed. The unit record anticipated "no business
> rule of its own beyond the single word-splitting/stopword constant captured here".
> That estimate was too small: the two-operation split, the filtering order, the
> case-insensitivity requirement and the scoring-parity obligation are all decisions
> with a right and a wrong answer, and tests already pin several of them. An
> explicitly empty file would have hidden six groups of real constraint. **The
> departure from the unit record's expectation is deliberate and this note is the
> disclosure.**
>
> **`BR4.3` carries an open contract question (`O9`).** Stopword *membership* is
> this unit's to decide; U1 used a set and pinned one property of it
> (`test_the_stopword_set_contains_no_sentiment_word`). The rule below fixes the
> set's *shape and governance*, not its contents.

```yaml
rules:
  # ---------------------------------------------------------------- BR1
  # The two operations, and the separation between them.
  - id: BR1.1
    statement: >
      The module exposes exactly two public operations: `tokenize(text)`, which
      turns text into a sequence of word tokens, and `significant_terms(tokens)`,
      which filters an already-tokenised sequence down to significant terms.
    category: constraint
    applies_to: app/terms.py public surface
    trigger: A caller imports the module.
    logic: >
      IF a third public operation is added THEN this rule is violated unless the
      unit record is amended first, because the two-operation split is what makes
      the filter structurally unable to reach sentiment scoring.
    violation_behaviour: >
      A caller could apply the analytics filter to engine scoring, which AC4.2.3
      exists to prevent.
    source: FR4.5, AC4.2.3
  - id: BR1.2
    statement: >
      `significant_terms` accepts an already-tokenised sequence and never
      tokenises. Passing raw text to it is a caller error, not a supported mode.
    category: constraint
    applies_to: significant_terms
    trigger: significant_terms is called.
    logic: >
      IF the argument is a string THEN it is iterated character by character and
      produces nonsense terms; the rule is that callers pass the output of
      `tokenize`, and the signature's `Sequence[str]` annotation states it.
    violation_behaviour: >
      Silent nonsense output rather than an exception. This is why the rule is
      stated: the failure is not self-announcing.
    source: FR4.5, AC4.2.3

  # ---------------------------------------------------------------- BR2
  # Tokenisation.
  - id: BR2.1
    statement: >
      A token is a maximal run of ASCII lowercase letters and apostrophes. Any
      other character — digit, punctuation, whitespace, non-Latin script — is a
      token boundary rather than a token character.
    category: calculation
    applies_to: tokenize
    trigger: tokenize processes text.
    logic: >
      Lowercase the text, then match maximal runs of [a-z'].
    violation_behaviour: >
      A wider class (e.g. including digits) would change what the offline engine
      scores, breaking BR5.1. This is the pinned rule.
    source: FR4.2, AC4.1.3
  - id: BR2.2
    statement: >
      Tokenisation lowercases before matching, so case never affects membership.
    category: calculation
    applies_to: tokenize
    trigger: Text containing uppercase characters is tokenised.
    logic: IF the text contains "WONDERFUL" THEN the token is "wonderful".
    violation_behaviour: >
      Case-sensitive matching would leave stopwords like "The" unfiltered and
      diverge from the offline engine's historical behaviour.
    source: FR4.2, AC4.1.2
  - id: BR2.3
    statement: >
      An empty or all-boundary text yields an empty token sequence, not an error.
    category: validation
    applies_to: tokenize
    trigger: tokenize is called with empty, whitespace-only or punctuation-only text.
    logic: IF the text has no matching run THEN return [].
    violation_behaviour: Raising here would make a legitimate empty result look like
      a failure; BR3.3 already defines the empty result as a success.
    source: FR4.3, AC4.1.5

  # ---------------------------------------------------------------- BR3
  # Significance filtering.
  - id: BR3.1
    statement: >
      A token survives filtering only if its length is at least MIN_TERM_LENGTH
      (three) characters.
    category: calculation
    applies_to: significant_terms
    trigger: significant_terms filters a token sequence.
    logic: >
      IF len(token) >= 3 THEN keep ELSE discard. Applied in addition to, and
      independently of, the stopword test.
    violation_behaviour: >
      A two-character threshold would admit "no", "so", "it" and change both
      analytics endpoints' output.
    source: FR4.1, AC4.1.1
  - id: BR3.2
    statement: >
      A token is excluded when, lowercased, it is a member of STOPWORDS. The
      comparison is case-insensitive.
    category: calculation
    applies_to: significant_terms
    trigger: significant_terms filters a token sequence.
    logic: IF token.lower() in STOPWORDS THEN discard.
    violation_behaviour: >
      A case-sensitive comparison would admit "The" and "And" while rejecting
      "the" and "and" — an inconsistency visible in the term lists.
    source: FR4.3, AC4.1.2, AC4.1.4
  - id: BR3.3
    statement: >
      A sequence in which every token is filtered out yields an empty result, never
      a padded or fabricated list.
    category: policy
    applies_to: significant_terms, and the terms endpoint that consumes it
    trigger: The input is entirely stopwords, entirely short tokens, or empty.
    logic: >
      IF nothing survives THEN return the empty sequence. The caller renders the
      label's list as empty rather than inventing a top-N.
    violation_behaviour: >
      A fabricated list would report terms the text does not contain.
    source: FR4.6, AC4.1.5, AC4.1.6
  - id: BR3.4
    statement: >
      Filtering preserves input order and never reorders, deduplicates or
      aggregates. Ranking and counting are the caller's concern.
    category: constraint
    applies_to: significant_terms
    trigger: significant_terms returns.
    logic: >
      The result is the input sequence with elements removed. A token occurring
      twice appears twice, because the caller's Counter does the counting.
    violation_behaviour: >
      Deduplicating here would make the caller's counts wrong, and the ranked
      output would silently under-report.
    source: FR4.5, FR3.2

  # ---------------------------------------------------------------- BR4
  # The owned constants.
  - id: BR4.1
    statement: >
      The word-splitting pattern is a single named module constant, TOKEN_PATTERN,
      compiled once. No other module holds a copy of it.
    category: constraint
    applies_to: app/terms.py, app/dummy_client.py
    trigger: Any module needs to split text into words.
    logic: >
      IF a module needs word tokens THEN it calls `tokenize`, never a private
      pattern of its own.
    violation_behaviour: >
      Two patterns drift and the engine's scoring silently changes. This is the
      defect the promotion exists to remove.
    source: FR4.5, AC4.2.1
  - id: BR4.2
    statement: >
      MIN_TERM_LENGTH is a single named constant equal to 3, owned here.
    category: constraint
    applies_to: app/terms.py
    trigger: The significance threshold is applied.
    logic: IF a caller needs the threshold THEN it reads MIN_TERM_LENGTH.
    violation_behaviour: >
      A literal 3 at a call site becomes invisible to the test that pins it, and a
      change to the rule would miss that site.
    source: FR4.1, AC4.1.1
  - id: BR4.3
    statement: >
      The stopword set is one in-repo constant, STOPWORDS, of type frozenset[str].
      It is never downloaded and no service is called to obtain it. Membership is
      this unit's decision and is governed by the two properties below.
    category: policy
    applies_to: app/terms.py
    trigger: The stopword test runs, or the set is inspected.
    logic: >
      IF a token is in STOPWORDS THEN it is filtered (BR3.2). The set is immutable
      and contained in the repository.
    violation_behaviour: >
      Fetching a corpus at runtime would break the offline guarantee (BR6.2) and
      introduce an egress path this unit must not have.
    source: FR4.4, AC4.1.4, contract open point O9
  - id: BR4.4
    statement: >
      The stopword set contains no sentiment-bearing word.
    category: policy
    applies_to: STOPWORDS
    trigger: The set is edited.
    logic: >
      IF a word carries sentiment (e.g. "good", "bad", "love", "hate") THEN it must
      not be a member, because the terms endpoint reports the terms that
      characterise a label's text and removing sentiment words would hide the very
      signal the feature exists to surface.
    violation_behaviour: >
      The top-term lists for positive and negative text converge, defeating the
      feature. Pinned by test_the_stopword_set_contains_no_sentiment_word.
    source: FR4.4, AC4.1.4
  - id: BR4.5
    statement: >
      Every constant is module-level, named in SCREAMING_SNAKE_CASE, and typed.
    category: constraint
    applies_to: app/terms.py
    trigger: A constant is added or read.
    logic: IF a value is a constant THEN it is module-level and typed.
    violation_behaviour: >
      An untyped or function-local constant is invisible to the codebase's
      conventions and to the manifest that claims this file.
    source: FR8.6, NFR5

  # ---------------------------------------------------------------- BR5
  # Scoring parity and the refactor.
  - id: BR5.1
    statement: >
      The offline engine's scoring behaviour is byte-identical before and after
      this change, for every input.
    category: constraint
    applies_to: app/dummy_client.py, app/terms.py
    trigger: The engine scores text.
    logic: >
      The engine's decision path is unchanged; only the source of its word tokens
      moves from a private pattern to `tokenize`. The 3-character minimum and the
      stopword set do NOT apply to scoring (BR5.2).
    violation_behaviour: >
      Any change to what the engine returns for any input is a regression, and a
      parity test is required to catch it.
    source: FR4.5, AC4.2.2
  - id: BR5.2
    statement: >
      The significance filter is never applied to sentiment scoring. Only
      `tokenize` reaches the engine.
    category: constraint
    applies_to: app/dummy_client.py
    trigger: The engine tokenises text.
    logic: >
      IF the engine needs words THEN it calls `tokenize` and nothing else. It must
      not call `significant_terms`, because a keyword shorter than three characters
      (or a stopword) would then stop being counted and the label could change.
    violation_behaviour: >
      Silent label changes on inputs containing short sentiment keywords.
    source: FR4.5, AC4.2.2, AC4.2.3
  - id: BR5.3
    statement: >
      The offline engine's private word pattern is deleted, and no module imports
      another module's private name.
    category: constraint
    applies_to: app/dummy_client.py
    trigger: The refactor completes.
    logic: >
      IF a private pattern or private-name import remains THEN the promotion is
      incomplete.
    violation_behaviour: >
      Two sources of truth for word splitting, which is the condition the promotion
      exists to remove.
    source: FR4.5, AC4.2.1

  # ---------------------------------------------------------------- BR6
  # Module isolation and conventions.
  - id: BR6.1
    statement: >
      The module imports nothing from `app`. It is a fan-out-0 leaf.
    category: constraint
    applies_to: app/terms.py
    trigger: The module is imported.
    logic: >
      IF the module needs `app` state, a connection or a model THEN the boundary has
      moved and this rule is violated.
    violation_behaviour: >
      The analytics path would acquire a dependency on storage, and the isolation
      test would fail.
    source: components.md TermExtraction boundary
  - id: BR6.2
    statement: >
      The module performs no I/O of any kind: no network, no filesystem, no
      database, no clock, no randomness. It is a pure function pair.
    category: constraint
    applies_to: app/terms.py
    trigger: Any function of the module runs.
    logic: >
      IF an operation has an effect on the world THEN it does not belong here.
    violation_behaviour: >
      An egress path or a hidden nondeterminism would break the offline guarantee
      the whole test suite depends on.
    source: NFR1.2, FR4.4, AC4.1.4
  - id: BR6.3
    statement: >
      Both operations are total: for every input in their declared domain they
      return a value, and neither raises.
    category: constraint
    applies_to: tokenize, significant_terms
    trigger: Any input is passed.
    logic: >
      IF the input is empty or contains nothing significant THEN the result is an
      empty sequence (BR2.3, BR3.3), not an exception.
    violation_behaviour: >
      A raising leaf would force every caller to add error handling for a case that
      is not an error.
    source: FR4.3, FR4.6
```

## Summary

| Rule | Category | One-line |
|---|---|---|
| `BR1.1` | constraint | Exactly two public operations |
| `BR1.2` | constraint | `significant_terms` filters; never tokenises |
| `BR2.1` | calculation | Token = maximal run of `[a-z']` |
| `BR2.2` | calculation | Lowercase before matching |
| `BR2.3` | validation | Empty text → empty tokens, not an error |
| `BR3.1` | calculation | Length ≥ 3 to survive |
| `BR3.2` | calculation | Stopword test is case-insensitive |
| `BR3.3` | policy | All-filtered → empty, never padded |
| `BR3.4` | constraint | Filtering preserves order; no dedup or counting |
| `BR4.1` | constraint | `TOKEN_PATTERN` is the one word pattern |
| `BR4.2` | constraint | `MIN_TERM_LENGTH` is the one threshold |
| `BR4.3` | policy | `STOPWORDS` is in-repo, immutable, never fetched |
| `BR4.4` | policy | No sentiment-bearing word in the stopword set |
| `BR4.5` | constraint | Constants are module-level, typed, SCREAMING_SNAKE |
| `BR5.1` | constraint | Engine scoring byte-identical |
| `BR5.2` | constraint | The filter never touches scoring |
| `BR5.3` | constraint | The private pattern is gone |
| `BR6.1` | constraint | Imports nothing from `app` (fan-out-0) |
| `BR6.2` | constraint | No I/O whatsoever |
| `BR6.3` | constraint | Both operations are total |

## Adjacent contradictions, recorded

- **`unit-of-work.md:150` expected this file to be empty.** It is not. Six groups of
  real constraint exist, three of which tests already pin. Recorded above rather
  than resolved by deleting the rules.
- **`O9` is open, not closed here.** `BR4.3` fixes the set's shape and governance;
  `BR4.4` fixes one property of its contents. Whether a *particular word* belongs in
  the set remains this unit's decision and is not settled by this stage.
- **`BR5.2` is the rule most likely to be broken by accident.** The engine and the
  analytics path both tokenise, and calling the wrong operation in the wrong place
  produces plausible output with a changed label. It is the reason `BR1.1` exists.
