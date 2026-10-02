# Functional Design — `u1-analytics-slice` (fast-tracked)

> One question, the drafted plan inside it. Reply `accept` to take it, or name the
> line you want changed. This unit is the walking skeleton: the additive v3 → v4
> migration with its three indexes, the `/v2` router and summary endpoint, the
> `AnalyticsRead` module, the R-01 connection fix, and the summary region of the
> view.
>
> These artifacts are **technology-agnostic by contract** — no SQL, no Python, no
> framework references. The concrete shapes live in `contract-summary.md`; this
> stage describes the business logic and the data model.

## Q1 — Accept the drafted functional design plan?

1. **Entities.** Four, and only one is persisted. `StoredAnalysis` is **owned by
   Persistence and Schema**, not by this unit — it is listed here because this
   unit reads it, and the catalogue says exactly one component owns each entity.
   `AnalyticsSummary`, `AnalyticsSeriesEntry` and `AnalyticsTermList` are
   **computed, never stored** (ADR-005), and this unit owns them. Attribute-level
   detail: identifier, logical type, required/unique, allowed values, and
   references — no physical types, no DDL.
2. **Business rules**, grouped `BR1`–`BR6`, each with a statement, category,
   trigger, an IF/THEN in plain language, violation behaviour and a source
   requirement id:
   - `BR1` range resolution — UTC calendar days, both ends inclusive, a single
     bound never dropped, the unbounded span, and the inverted-range refusal.
   - `BR2` aggregation — totals, per-label counts, shares as a four-decimal
     fraction, the zero-denominator `null`, and the mean-confidence coverage count.
   - `BR3` the per-day series — one entry per day inside a matched range, the
     zero-filled gap, and the no-match empty series.
   - `BR4` refusal shapes — 422 through the envelope naming the offending field in
     its message, the storage-failure 500 with its own code, and one no-match rule.
   - `BR5` the migration — additive only, idempotent, the three named indexes,
     index re-creation after a rebuild, and the loud rollback.
   - `BR6` connection handling — the explicit thread-affinity decision and the
     lifecycle, which is what closes R-01.
3. **Workflows** in `functional-spec.md`: the summary request end to end, the
   startup migration, and the refetch that supersedes an in-flight response. State
   machines only where one exists — the migration is one; the summary request is a
   workflow, not a lifecycle.
4. **No `frontend-components.md` for this unit.** The unit's kind is `service`, so
   that artifact is not in its matrix — **but this unit owns the summary region of
   the view**, which the story map assigns to `US6.2` here. Rather than silently
   drop those UI rules, they are recorded as rules (`BR2`'s rendering-facing ones)
   and the detailed component specification is named as `u3-analytics-view`'s to
   carry, with a cross-reference both ways.
5. **Traceability** enumerates every acceptance criterion this unit owns and maps
   each to the `BRx.y` rules that satisfy it, with a `reverse` array explaining any
   rule that intentionally has no owning criterion.
6. **No new questions beyond this one.** Any ambiguity found during generation is
   recorded as an open point for the gate rather than raised as a fresh question.

A. Accept the plan as drafted
B. Accept except for the items I name
C. Other (please specify)

[Answer]: A. Accept the plan as drafted.

## Consolidated Summary Confirmation

- **Four entities, one persisted.** `StoredAnalysis` is owned by Persistence and Schema; this unit reads it but does not own it. `AnalyticsSummary`, `AnalyticsSeriesEntry` and `AnalyticsTermList` are computed, never stored.
- **Rules are grouped `BR1`–`BR6`** — range resolution, aggregation, the per-day series, refusal shapes, the migration, and connection handling — each carrying a trigger, an IF/THEN, its violation behaviour and the requirement it comes from.
- **Workflows cover** the summary request end to end, the startup migration, and the refetch that supersedes an in-flight response. A state machine is stated only where one genuinely exists.
- **No `frontend-components.md` for this unit**, because its kind is `service`; the summary region's rendering rules are recorded as rules and the detailed component specification is cross-referenced to `u3-analytics-view` rather than dropped.
- **Traceability** maps every acceptance criterion this unit owns to the `BRx.y` rules that satisfy it, with a `reverse` array explaining any rule that intentionally has no owning criterion.
- **No further questions** were raised; anything ambiguous during generation is recorded as an open point at the gate.

- `Looks correct`
- `Request changes`

[Answer]: Looks correct
