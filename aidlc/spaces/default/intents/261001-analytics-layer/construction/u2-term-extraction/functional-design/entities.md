# Entity Model — `u2-term-extraction`

> **Intent:** `261001-analytics-layer` · stage `functional-design` (construction) ·
> unit `u2-term-extraction` (kind `library`).
>
> **Source of truth.** The fenced ```yaml block below is authoritative. The prose
> that follows it is a derived view.
>
> **This unit owns no entity, and that is a decision rather than an omission.**
> ADR-005 and `components.md`'s Entity Ownership table both list `TermExtraction`
> with none. `unit-of-work.md:150` pre-records the expectation: this file is
> **explicitly empty**, with that statement, "rather than invent a model U2 does
> not have". An empty block is the honest artifact; a fabricated entity here would
> be the defect.

```yaml
entities: []
```

## Why there is no entity

A **term** is not an entity in this system. It has no identity, no lifecycle and no
persistence: `significant_terms` returns a sequence of plain strings, and the ranked
`{term, count}` pairs the analytics endpoints return are computed value shapes
(ADR-005), assembled per request in memory and discarded with it. Nothing a caller
can hold is addressable, versionable or referable — which is the whole test for
whether something is an entity.

Three concrete consequences, each verifiable in the code:

| Question | Answer for this unit |
|---|---|
| Does it own a database table, column or index? | No. `app/db.py` gains nothing from U2. |
| Does anything hold an identifier for it? | No. Tokens are `str`; ranked entries are `(str, int)` pairs. |
| Does it have a lifecycle with states? | No. A token exists for the duration of one call. |

## What crosses this unit's boundary instead

The unit's real surface is **three module-level constants and two functions**. They
are contracts, not entities, and they are specified in `functional-spec.md` as
module surface rather than modelled here.

| Name | Kind | Why it is not an entity |
|---|---|---|
| `TOKEN_PATTERN` | constant | A regular-expression string. Not addressable. |
| `MIN_TERM_LENGTH` | constant | An integer. Not addressable. |
| `STOPWORDS` | constant | A `frozenset[str]`. Not addressable — see `rules.md` `BR4.3`. |
| `tokenize` | function | Stateless, total, side-effect free. |
| `significant_terms` | function | Depends only on its argument. |

## The one thing that *is* persisted, and where it lives

`analyses.text` holds the input text a reader later tokenises. **That column is owned
by U1's `Persistence and Schema` component, not by this unit.** U2 reads nothing from
the store directly — it never holds a connection, which is why `terms.py` imports
nothing from `app` and why the isolation test in `test_terms.py` can prove it.

The distinction matters for the boundary: U1 stores text, U2 turns text into terms,
and the analytics handler joins them. If U2 ever grew a store dependency, that join
would move and the fan-out-0 property would be lost.
