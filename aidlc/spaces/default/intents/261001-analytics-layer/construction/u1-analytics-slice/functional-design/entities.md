# Entities — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `functional-design` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Source of truth.** The fenced ```yaml block below is authoritative for the
> entity model. The human-readable summary that follows it is a derived view.
>
> **Four entities, exactly one persisted.** `StoredAnalysis` is **owned by
> `Persistence and Schema`**, not by this unit — it is described here only because
> this unit reads it, and the "exactly one owner" rule is stated explicitly so the
> ownership does not drift. `AnalyticsSummary`, `AnalyticsSeriesEntry` and
> `AnalyticsTermList` are **computed on request, never stored** (ADR-005); this unit
> owns them.
>
> **Depth.** Attribute-level only: identifier, logical type, required/unique,
> allowed values, references and constraints. **No physical types and no DDL** —
> those belong to Code Generation.
>
> **Series extent (R-01).** `AnalyticsSummary.series` spans the **resolved range**,
> not merely the span that happened to match rows. When no bound is supplied the
> resolved range is the earliest stored analysis UTC day through **today inclusive**,
> so days between the last stored analysis and today **are** present and zero-filled;
> with bounds it is every UTC day in the resolved bounds. For a range that matched at
> least one row every day of the resolved range yields an entry (zero-filled when it
> held no rows); a range that matched **no** rows yields an **empty** series, never a
> zero-filled span. The three cases are stated separately and authoritatively in
> `rules.md` `BR1.3`/`BR3.1`/`BR3.2`; the phrase "span of stored data" in `AC8.9.2` is
> the *length* of that same resolved-range series in the unbounded case, not a second
> extent definition.

## Entity model — source of truth

The fenced block below is authoritative; the derived summary follows it.

```yaml
entities:
  - name: StoredAnalysis
    owner: Persistence and Schema          # NOT owned by this unit; read-only here
    owned_by_this_unit: false
    persisted: true
    lifecycle: persisted row in the local store
    description: >
      One analysis the application has stored: the analysed text, its label and the
      engine's decision metadata. This unit reads it to compute the analytics
      aggregates and never writes it. The migration that keeps this entity readable
      at schema v4 is owned by Persistence and Schema (ADR-004).
    identifier: id
    attributes:
      - name: id
        type: integer
        required: true
        unique: true
        constraints: server-assigned surrogate key; stable for the life of the row
      - name: text
        type: string
        required: true
        constraints: the analysed text; the input to term extraction
      - name: label
        type: enum
        required: true
        allowed_values: [positive, negative, neutral]
        constraints: closed vocabulary shared with the sentiment interface
      - name: probabilities
        type: object
        required: true
        constraints: keyed by the same closed label vocabulary; each value a number
      - name: confidence
        type: number
        required: true
        constraints: never null in a readable store; the input to every mean
      - name: intensity
        type: number
        required: false
        constraints: >
          RETIRED. Never written by the application, null on every
          application-produced row, not read by this unit, and never resurrected by
          the migration. Listed only so the row shape is stated whole.
      - name: model
        type: string
        required: true
      - name: provider
        type: string
        required: true
      - name: created_at
        type: timestamp
        required: true
        constraints: >
          UTC, second precision, ISO-8601 form ending in `Z`. The per-day series
          buckets on this value's UTC calendar date.
      - name: import_id
        type: string
        required: false
        constraints: >
          OPAQUE. Server-minted grouping key for a bulk import. No parse step and
          therefore no parse failure; an id that matches no rows is an empty
          population, not an error.
    entity_constraints:
      - label is one of positive, negative, neutral
      - confidence is present on every row that can be read (a store that disagrees is rebuilt by Persistence and Schema)
      - created_at is UTC and second-precision
      - import_id is opaque and has no validating shape
    relationships: []

  - name: AnalyticsSummary
    owner: u1-analytics-slice                 # AnalyticsRead computed shape
    owned_by_this_unit: true
    persisted: false
    lifecycle: computed per request; never stored, written or cached
    description: >
      The summary answer: how many rows are in the resolved range and filter, their
      label mix, the mean confidence and the per-day series. Produced by one read
      pass over the rows in range. `resolved_range` is the in-process identifier and
      is deliberately NOT serialised onto the wire (contract UC3; the wire payload is
      the six fields below).
    identifier: resolved_range
    attributes:
      - name: resolved_range
        type: object
        required: true
        constraints: >
          In-process only — the resolved day bounds (either may be unbounded) after
          applying `from`/`to`/`import_id`. Not part of the response payload.
      - name: total
        type: integer
        required: true
        constraints: ">= 0; equals the number of rows in the resolved range after the import_id filter"
      - name: counts
        type: object
        required: true
        constraints: keyed by the closed label vocabulary; all three labels always present; each value an integer >= 0
      - name: shares
        type: object
        required: true
        constraints: keyed by the closed label vocabulary; each value a fraction in [0,1] rounded to four decimals, or null when total is 0
      - name: mean_confidence
        type: number
        required: true
        constraints: arithmetic mean of confidence over every row in range, rounded to four decimals; null iff total is 0
      - name: mean_confidence_row_count
        type: integer
        required: true
        constraints: ">= 0; always equals total (0 when total is 0)"
      - name: series
        type: array
        required: true
        constraints: >
          ordered ascending by date; exactly one AnalyticsSeriesEntry per UTC calendar
          day in the resolved range when the range matched at least one row; empty when
          no row matched. The resolved range is the three-case rule of BR1.3: both
          bounds present -> the resolved bounds; one bound present -> that half-open
          span (BR1.2); neither bound and no import_id -> the earliest stored analysis
          UTC day through today inclusive; a matched import_id with no bounds -> the
          span of the matching rows. Edge days of a matched range carry no rows and are
          zero-filled exactly as BR3.2 specifies.
    entity_constraints:
      - counts and shares always carry all three labels
      - shares and mean_confidence are null exactly when their denominator is 0 — never a fabricated 0.0
      - series is empty when no row matched, never a zero-filled span
      - resolved_range is not serialised
    relationships:
      - target: StoredAnalysis
        target_owner: Persistence and Schema
        cardinality: one-to-many
        direction: one AnalyticsSummary aggregates zero or more StoredAnalysis rows (the rows of the resolved range); the summary is derived from the stored rows, so the summary is the "one" and the stored analyses are the "many"
      - target: AnalyticsSeriesEntry
        cardinality: one-to-many
        direction: AnalyticsSummary contains zero or more AnalyticsSeriesEntry values

  - name: AnalyticsSeriesEntry
    owner: u1-analytics-slice                 # AnalyticsRead computed shape
    owned_by_this_unit: true
    persisted: false
    lifecycle: computed per request; never stored
    description: >
      One UTC calendar day inside a range that matched at least one row: the day's
      totals, label mix, shares and mean confidence, zero-filled when the day itself
      held no rows.
    identifier: date
    attributes:
      - name: date
        type: string
        required: true
        constraints: a UTC calendar day written YYYY-MM-DD; unique within one summary's series
      - name: total
        type: integer
        required: true
        constraints: ">= 0; the day's row count"
      - name: counts
        type: object
        required: true
        constraints: keyed by the closed label vocabulary; all three labels present
      - name: shares
        type: object
        required: true
        constraints: each a fraction in [0,1] rounded to four decimals, or null when the day's total is 0
      - name: mean_confidence
        type: number
        required: true
        constraints: four-decimal mean over the day's rows; null iff the day's total is 0
      - name: mean_confidence_row_count
        type: integer
        required: true
        constraints: ">= 0; equals the day's total (0 on a zero-filled day)"
    entity_constraints:
      - all six fields are always present, even when a value is 0 or null
      - a day with no rows inside a matched range is zero-filled with null shares and a null mean, and row_count 0
      - a populated day never carries a null mean
    relationships:
      - target: StoredAnalysis
        target_owner: Persistence and Schema
        cardinality: one-to-many
        direction: one AnalyticsSeriesEntry aggregates zero or more StoredAnalysis rows whose created-at UTC date equals its date; the entry is the "one" and those stored rows are the "many" (a zero-filled entry aggregates none)

  - name: AnalyticsTermList
    owner: u1-analytics-slice                 # AnalyticsRead computed shape
    owned_by_this_unit: true
    persisted: false
    lifecycle: computed per request; never stored
    description: >
      One ranked term list for a sentiment label. The two lists (positive and
      negative) are the same shape with different label membership, so they are
      modelled as one entity discriminated by `label` (ADR-005 explicitly permits
      Functional Design to fuse the catalogue's finer split). Terms are derived from
      the text of the rows the list's label selects.
    identifier: label
    attributes:
      - name: label
        type: enum
        required: true
        allowed_values: [positive, negative]
        constraints: there is no neutral list; neutral rows contribute to neither
      - name: items
        type: array
        required: true
        constraints: >
          Ranked entries, each an immutable value pair {term: string, count: integer
          >= 1}. Ordered by count descending with ties broken alphabetically. At most
          `limit` entries (default 10). Empty when the label has no rows in range —
          never null and never padded.
    entity_constraints:
      - label is positive or negative only
      - an entry carries term and count and nothing else (no share, score or weighting)
      - term is a significant term (>= 3 characters, absent from the fixed stopword constant)
      - a label with no rows yields an empty items array
    relationships:
      - target: StoredAnalysis
        target_owner: Persistence and Schema
        cardinality: one-to-many
        direction: one AnalyticsTermList is derived from the text of zero or more StoredAnalysis rows carrying its label; the list is the "one" and those stored rows are the "many" (a label with no rows derives from none)
```

## Ownership and persistence

**Exactly one owner per entity.** `StoredAnalysis` belongs to `Persistence and Schema`; the three computed shapes belong to this unit's `AnalyticsRead`. The three schema indexes are schema artifacts, not entities.

## Derived summary

Four entities. `StoredAnalysis` is the only persisted one and is owned by
`Persistence and Schema` (recorded in the `components.md` Entity Ownership table);
this unit reads it and owns none of its writes. The remaining three are **computed
value shapes** owned by this unit's `AnalyticsRead` module: they are produced on
request and never stored, so the analytics feature implies no table, no migration
and no index of its own (ADR-005). The three schema indexes named by the migration
are schema artifacts owned by `Persistence and Schema`, not entities.

The `components.md` catalogue records five computed shapes (`AnalyticsSummary`,
`AnalyticsSeriesEntry`, `TermFrequencyEntry`, `PositiveTermList`, `NegativeTermList`).
This artifact consolidates the last three into one `AnalyticsTermList` entity with a
`label` discriminator and an item value pair, because the two lists are structurally
identical and differ only in label membership. ADR-005 explicitly leaves that fuse-or-
split call to Functional Design. The wire shapes are pinned by
`contract-summary.md` §2, not by this file: `resolved_range` stays in-process and is
not serialised.
