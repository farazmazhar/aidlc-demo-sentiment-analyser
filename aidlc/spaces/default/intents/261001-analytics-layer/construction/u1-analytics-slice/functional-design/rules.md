# Business Rules — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `functional-design` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Source of truth.** The fenced ```yaml block below is authoritative for the
> business rules. The human-readable summary table and the "Adjacent
> contradictions" note that follow it are derived views.
>
> **Six groups.** `BR1` range resolution · `BR2` aggregation, computation and the
> summary region's rendering rules · `BR3` the per-day series and the computed
> response's proportional work · `BR4` refusal, failure and observability shapes ·
> `BR5` the additive migration · `BR6` connection handling, concurrency and the
> process-exposure boundary. Every rule names the requirement it comes from.
>
> **Ruled (R-06) — this note is superseded.** The four-decimal rounding **tie
> rule** was left open when this artifact was first drafted, and the human has
> since **ruled it half-up** at this stage's gate. `BR2.2`/`BR2.3` now carry the
> ruling inline rather than a placeholder, and the same is recorded in
> `functional-spec.md`. The ruling also settles contract open point **O1**. A
> pinned test may now exercise a tie.

```yaml
rules:

  # ------------------------------------------------------------------ BR1
  - id: BR1.1
    statement: >
      `from` and `to` are UTC calendar dates written YYYY-MM-DD; both bounds are
      inclusive, `to` bounding the whole of that UTC day.
    category: calculation
    applies_to: Both /v2 analytics endpoints; the resolved range.
    trigger: A request supplies `from` and/or `to`.
    logic: >
      IF both bounds are supplied, THEN the range is every UTC calendar day from
      `from` through `to` inclusive — a row timestamped 23:59:59Z on the `to` day is
      in range, and the following day is not.
    violation: A malformed date is refused per BR4.2; there is no other violation behaviour.
    source: FR2.4

  - id: BR1.2
    statement: A single bound is never dropped.
    category: calculation
    applies_to: Both /v2 analytics endpoints.
    trigger: Exactly one of `from`, `to` is supplied.
    logic: >
      IF only `from` is supplied, THEN the range runs from that day through now;
      IF only `to` is supplied, THEN it runs from the beginning of history through
      that day.
    violation: Silently ignoring a supplied bound is a defect; the bound always participates.
    source: FR2.5

  - id: BR1.3
    statement: >
      With neither bound and no `import_id`, the resolved range spans the earliest
      stored analysis UTC day through today inclusive; a matched `import_id` with no
      bounds spans the matching rows.
    category: calculation
    applies_to: Both /v2 analytics endpoints.
    trigger: Neither bound is supplied.
    logic: >
      IF neither bound and no `import_id`, THEN the earliest stored analysis UTC day
      through today inclusive; IF a matched `import_id` and no bounds, THEN the span
      of the matching rows (empty if none).
    violation: >
      An unmatched `import_id` does not inherit the store-wide default span; it is an
      empty population handled by BR4.4.
    source: FR2.6 (Q12)

  - id: BR1.4
    statement: An inverted range (`from` later than `to`) is refused, never silently emptied.
    category: validation
    applies_to: Both /v2 analytics endpoints.
    trigger: "`from` and `to` are supplied and `from` is later than `to`."
    logic: >
      IF `from` is later than `to`, THEN refuse before computing anything; the refusal
      names both bounds.
    violation: 422 VALIDATION_FAILED via BR4.3; the series never applies.
    source: FR2.11 (Q11 / R-04)

  - id: BR1.5
    statement: >
      Range resolution is identical for both endpoints; summary and terms never
      disagree about which rows are in range or what an empty answer looks like.
    category: constraint
    applies_to: Summary and terms.
    trigger: Either endpoint resolves a range.
    logic: >
      IF both endpoints are given the same bounds and `import_id`, THEN they resolve
      the same row set, including an inverted range (both refused), a single bound, an
      unmatched `import_id` (both empty) and an empty range (both empty with a matching
      shape).
    violation: A disagreement is a contract defect; the shared resolution must be pinned by tests.
    source: FR3.8

  # ------------------------------------------------------------------ BR2
  - id: BR2.1
    statement: >
      The summary reports `total` = the number of rows in the resolved range and
      `counts` = a per-label count over the closed label vocabulary, every label
      present even when zero.
    category: calculation
    applies_to: AnalyticsSummary.
    trigger: A summary is computed.
    logic: >
      IF rows are in range, THEN total counts every row and counts carries each
      label's occurrence; positive, negative and neutral are all present, zero-valued
      labels included.
    violation: A missing label key or a count that omits a zero label is an incomplete answer.
    source: FR2.1, FR2.3, FR3.6

  - id: BR2.2
    statement: >
      A share is that label's count divided by total, expressed as a fraction in [0,1]
      rounded to four decimal places; it is null when total is 0.
    category: calculation
    applies_to: AnalyticsSummary and AnalyticsSeriesEntry.
    trigger: Shares are computed.
    logic: >
      IF total is greater than 0, THEN share = count / total rounded to four decimal
      places as a fraction; IF total is 0, THEN share = null (never 0.0).
    violation: A fabricated 0.0 is refused; the project refuses rather than substitutes a number.
    source: FR2.7 (R-08)
    rounding_tie_rule: "half-up: round half up: a value exactly at a four-decimal tie rounds away from zero (0.28125 becomes 0.2813). Ruled by the human at the Functional Design gate; settles contract open point O1."

  - id: BR2.3
    statement: >
      `mean_confidence` is the arithmetic mean of `confidence` over every row in range,
      rounded to four decimal places; `mean_confidence_row_count` equals `total`.
    category: calculation
    applies_to: AnalyticsSummary and AnalyticsSeriesEntry.
    trigger: The mean is computed.
    logic: >
      IF total is greater than 0, THEN the mean is over all rows and row_count equals
      total; IF total is 0, THEN mean = null and row_count = 0.
    violation: >
      The null-tolerant subset mean is unreachable — confidence is required on every
      row — so the row count simply states the denominator.
    source: FR2.8 (Revision 2)
    rounding_tie_rule: "half-up: round half up: a value exactly at a four-decimal tie rounds away from zero (0.28125 becomes 0.2813). Ruled by the human at the Functional Design gate; settles contract open point O1."

  - id: BR2.4
    statement: >
      A term list carries ranked entry pairs {term, count} only, at most `limit` per
      list (default 10); only positive and negative rows contribute; a label with no
      rows yields an empty array.
    category: calculation
    applies_to: AnalyticsTermList.
    trigger: Term lists are computed.
    logic: >
      IF a row is labelled neutral, THEN it contributes to neither list; IF a label has
      no rows in range, THEN its array is empty, never null and never padded; IF more
      terms are available than `limit`, THEN only the top `limit` are materialised.
    violation: A null list, a padded list or a neutral contribution is a defect.
    source: FR3.3, FR3.6, FR3.7

  - id: BR2.5
    statement: >
      Terms are ordered by count descending with ties broken alphabetically; each entry
      carries term and count and nothing else.
    category: calculation
    applies_to: AnalyticsTermList items.
    trigger: A term list is ranked.
    logic: >
      IF two terms have equal counts, THEN order them alphabetically; the order is total
      and stable so a hand-written expected value can pin it; no share, score or
      weighting is emitted.
    violation: An unstable or unstated order defeats the pinned expected value.
    source: FR3.5, FR3.3

  - id: BR2.6
    statement: >
      `limit` defaults to 10 and applies per list; a value below 1 or non-numeric is
      refused and an oversized value is honoured rather than clamped.
    category: validation
    applies_to: Terms endpoint.
    trigger: "`limit` is supplied or defaulted."
    logic: >
      IF `limit` is absent, THEN 10; IF `limit` is below 1 or not a number, THEN refuse
      per BR4.2; IF `limit` exceeds the number of distinct terms in range, THEN return
      every available term without clamping.
    violation: A silent clamp or a substituted default is refused.
    source: FR3.3, FR3.4

  - id: BR2.7
    statement: >
      Computing analytics performs no write and no access bookkeeping; the read path
      issues no mutating operation of any kind and records no last-read state.
    category: constraint
    applies_to: AnalyticsRead and both endpoints.
    trigger: Any analytics request.
    logic: >
      IF either endpoint is called any number of times, THEN the store's row count,
      schema and content hash are unchanged and no timestamp or bookkeeping is written.
    violation: Any mutation or bookkeeping violates the read-only guarantee.
    source: FR2.13, NFR3

  - id: BR2.8
    statement: >
      Every aggregate is computed in-process from stored rows; there is no network call,
      no HTTP client, no socket, no model inference and no credential anywhere in the
      analytics path.
    category: constraint
    applies_to: AnalyticsRead and the analytics modules.
    trigger: Imports, calls and outputs are inspected.
    logic: >
      IF the analytics code is inspected, THEN it imports no HTTP client or socket,
      calls no engine, and adds no credential to any code path, response body, log
      record or artifact.
    violation: Any new egress path breaches the privacy constraint.
    source: FR1.2, NFR2

  - id: BR2.9
    statement: Every aggregate statement is parameter-bound; no statement text is built by interpolation.
    category: constraint
    applies_to: AnalyticsRead.
    trigger: An aggregate query is inspected.
    logic: >
      IF any value reaches a statement, THEN it does so as a bound parameter, never
      concatenated into the statement text.
    violation: Interpolation is a security and correctness defect.
    source: FR1.4

  - id: BR2.10
    statement: >
      All aggregate reads live in one read module beside the repository and are called
      from the route; the route holds no statement and no query helper, and the service
      layer is not inserted into the read path.
    category: constraint
    applies_to: HTTP route and AnalyticsRead.
    trigger: The route module's body is read.
    logic: >
      IF the route body is inspected, THEN it contains no statement text and no query
      helper call; every aggregate is in the read module and reads go route -> read
      module, never route -> service.
    violation: A statement in the route, or a service insertion, erodes the recorded boundary.
    source: FR1.1

  # --- rendering-facing rules for the summary region the slice completes -------
  - id: BR2.11
    statement: >
      The summary region provides a container for the per-day series and one for the
      label breakdown, each with exactly one fetch to its own endpoint, and renders no
      value an endpoint did not return.
    category: policy
    applies_to: Summary region of the view (delivered by this unit; detailed component specification carried by u3-analytics-view).
    trigger: The view's markup and fetch sites are inspected.
    logic: >
      IF a summary section is rendered, THEN it has exactly one fetch to its endpoint
      and renders only returned values; both the series container and the breakdown
      container exist.
    violation: A missing container or a second fetch is a contract defect.
    source: FR6.2

  - id: BR2.12
    statement: >
      A share is rendered from the response's fraction, and a null share renders as an
      explicit no-share marker, never a fabricated 0%.
    category: policy
    applies_to: The summary region's label breakdown.
    trigger: A breakdown share is rendered.
    logic: >
      IF the response share is a number, THEN render a percentage derived from the
      fraction; IF the share is null, THEN render an explicit no-share marker.
    violation: Rendering 0% for a null share fabricates a number the endpoint refused to state.
    source: FR2.7, AC6.2.5

  - id: BR2.13
    statement: >
      The view's analytics version-prefix constant equals the backend /v2 prefix
      constant, pinned by a static assertion.
    category: constraint
    applies_to: The summary region's fetch path and the backend router.
    trigger: The view's prefix constants are inspected.
    logic: IF either prefix constant changes, THEN the static assertion fails.
    violation: A silent prefix drift breaks every analytics fetch.
    source: FR6.9, contract-summary.md §5 (AC6.2.3)

  - id: BR2.14
    statement: >
      Analytics markup hooks are added to the existing pinned test-id convention and
      asserted in the same style as the existing page's hooks.
    category: policy
    applies_to: Summary region markup and the page contract tests.
    trigger: The page contract tests run.
    logic: >
      IF an analytics hook is renamed or removed, THEN a page contract test fails
      rather than silently passing.
    violation: A hook outside the pinned convention is not asserted.
    source: FR6.9 (AC6.2.4)

  - id: BR2.15
    statement: >
      New modules follow the codebase conventions: one responsibility per module, all
      parameters and return values typed, internal helpers kept private to the module,
      constants in the house style, the standard-library plain-data shapes rather than a
      third-party validation library, no junk-drawer module, and no new configuration
      value.
    category: policy
    applies_to: AnalyticsRead and the new module set.
    trigger: A new module is inspected.
    logic: >
      IF a new module is reviewed, THEN each convention above holds as a separate
      decidable check; IF the analytics layer needs no new configuration value, THEN it
      adds none, which is itself the decidable outcome.
    violation: A convention miss makes the new code read unlike the codebase.
    source: FR1.5, NFR6

  # ------------------------------------------------------------------ BR3
  # --- the series extent is pinned by BR1.3 + BR3.1 + BR3.2 together ----------------
  # Three separate cases, stated so no implementer must guess the default path:
  #   (a) neither bound -> resolved range is earliest stored analysis UTC day
  #       through today inclusive; days after the last stored analysis and up to
  #       today ARE included and zero-filled (a trailing empty "today" is emitted);
  #   (b) bounds supplied -> resolved range is every UTC day in the resolved range;
  #   (c) no rows matched -> empty series (BR3.3), never a zero-filled span.
  # Zero-filling applies inside a range that matched at least one row. In case (a)
  # the resolved range always contains at least the earliest stored day, so if the
  # store holds any row at all the range matched one and zero-fill applies; an empty
  # store yields the empty series of case (c).
  # AC8.9.2's "span of the stored data" is the LENGTH of that same resolved-range
  # series in the unbounded case (NFR9), not a second extent definition.

  - id: BR3.1
    statement: >
      Extent. A range that matched at least one row yields exactly one entry per UTC
      calendar day in the resolved range, ascending and continuous.
    category: calculation
    applies_to: AnalyticsSummary.series.
    trigger: A populated range is read.
    logic: >
      IF the range matched at least one row, THEN the series holds one entry per UTC
      day from the resolved range's first day to its last day inclusive, in ascending
      date order; no day inside the range is skipped or duplicated, including across a
      month boundary. The resolved range is the three-case rule of BR1.3: both bounds
      present -> the resolved bounds; a single bound -> the half-open span of BR1.2;
      neither bound and no import_id -> the earliest stored analysis UTC day through
      today inclusive; a matched import_id with no bounds -> the span of the matching
      rows (leading and trailing empty days included).
    violation: >
      A gap, a duplicate day, or a series that stops at the last stored row instead of
      running to the resolved range's end (today, in the unbounded case) is a series
      defect.
    source: FR2.9 (Q12; length per NFR9)

  - id: BR3.2
    statement: >
      Zero-fill. A day with no rows inside a matched range — whether an internal gap
      or an edge day of the resolved range (leading or trailing, e.g. days between the
      last stored analysis and today) — reports total 0, all counts 0, all shares null,
      mean_confidence null, and mean_confidence_row_count 0, which is that day's total.
    category: calculation
    applies_to: AnalyticsSeriesEntry.
    trigger: A matched range has a day with no rows, internal or at an edge.
    logic: >
      IF a day inside a matched range has no rows, THEN its entry carries total 0, zero
      counts, null shares, a null mean and row_count 0, with no distinction between an
      internal gap and an edge day; a populated day carries its real values with
      row_count equal to its total.
    violation: >
      Omitting the day, or reporting a subset mean, confuses a day with data with a day
      without. The correct zero-day row count is 0, not null (see contradictions).
    source: FR2.9, contract-summary.md §7 P4 (Q12)

  - id: BR3.3
    statement: >
      A range that matches no rows returns an empty series, never a zero-filled span
      and never a 404.
    category: calculation
    applies_to: AnalyticsSummary.series and both endpoints' empty shape.
    trigger: No rows match the resolved range and filter.
    logic: >
      IF no rows match, THEN the summary's series is empty with total 0; zero-filling
      applies only inside a range that matched at least one row, so an edge day is
      zero-filled only when some row matched somewhere in the resolved range; the terms
      endpoint's empty body is exactly {positive: [], negative: []} and carries no
      total, no series and no summary fields.
    violation: A zero-filled empty span contradicts the reconciled rule.
    source: FR2.10 (Q10)

  - id: BR3.4
    statement: >
      The series is produced by one grouped read over the range plus an in-process fill,
      so the number of statements executed is independent of the number of days.
    category: calculation
    applies_to: AnalyticsRead series computation.
    trigger: The series is produced.
    logic: >
      IF the range covers N days, THEN the statement count does not grow with N; the
      grouping is one read and the fill is in-process.
    violation: A read per day violates the performance requirement and the statement-count assertion.
    source: NFR1, FR8.9

  - id: BR3.5
    statement: >
      Every series entry carries `date`, `total`, `counts`, `shares`, `mean_confidence`
      and `mean_confidence_row_count`.
    category: constraint
    applies_to: AnalyticsSeriesEntry.
    trigger: An entry is built.
    logic: >
      IF an entry is serialised, THEN all six fields are present; none is omitted when
      its value is zero or null.
    violation: A missing field makes a day's mean indistinguishable from an absent one.
    source: FR2.9 (R-09)

  - id: BR3.6
    statement: >
      Each endpoint answers within 200 ms over 10,000 stored analyses, measured without
      coverage instrumentation, including the terms path.
    category: calculation
    applies_to: Both endpoints.
    trigger: The performance test runs.
    logic: >
      IF the 10,000-row fixture is exercised, THEN each endpoint — summary and terms —
      answers inside the budget, and the measurement is taken without coverage
      instrumentation.
    violation: A budget miss is a performance-requirement failure.
    source: NFR1, FR8.9

  # ------------------------------------------------------------------ BR4
  - id: BR4.1
    statement: >
      Validation failures travel through the single existing error envelope, which is
      exactly {code, message} with no field, errors or details member; the message text
      itself names the offending parameter.
    category: validation
    applies_to: Both /v2 analytics endpoints.
    trigger: A parameter is malformed, or a range is inverted.
    logic: >
      IF a validation failure occurs, THEN the response is one envelope entry whose code
      is VALIDATION_FAILED and whose message text names the offending parameter
      (query.from, query.to or query.limit; both query.from and query.to for an inverted
      range), with nothing computed.
    violation: Adding a field member or a second error body breaks the frozen envelope shape.
    source: FR2.12, NFR5, Revision 2

  - id: BR4.2
    statement: >
      A malformed `from`/`to` or a `limit` below 1 or non-numeric is refused with 422
      naming that parameter, and nothing is computed.
    category: validation
    applies_to: Summary (`from`/`to`) and terms (`from`/`to`/`limit`).
    trigger: A supplied parameter cannot be read.
    logic: >
      IF `from` or `to` cannot be read as a UTC date, THEN 422 naming query.from or
      query.to; IF `limit` is below 1 or non-numeric, THEN 422 naming query.limit; no
      parameter is ever silently defaulted or clamped.
    violation: Nothing is computed on a refused request; a refusal that half-succeeded is a defect.
    source: FR2.11, FR3.4

  - id: BR4.3
    statement: >
      An inverted range is refused with one VALIDATION_FAILED whose message names both
      `query.from` and `query.to`; the series never applies.
    category: validation
    applies_to: Both /v2 analytics endpoints.
    trigger: "`from` is later than `to`."
    logic: >
      IF `from` is later than `to`, THEN the refusal names both fields in the message
      text (the envelope cannot carry two field members); nothing is computed.
    violation: A silently emptied range would hide a caller error.
    source: FR2.11 (Q11 / R-04)

  - id: BR4.4
    statement: >
      A no-match answer is a success, not a failure: a range or import_id matching no
      rows is a 200 in each endpoint's own frozen empty shape — never 404 and never a
      store-wide zero-fill.
    category: policy
    applies_to: Both /v2 analytics endpoints.
    trigger: The range matches no rows.
    logic: >
      IF no rows match the range or a supplied `import_id`, THEN 200 and no store-wide
      zero-fill; the summary's empty body is total 0 with an empty series (its six-field
      shape), while the terms' empty body is exactly {positive: [], negative: []} with
      no total, no series and no summary fields; an unmatched `import_id` is identical
      to an empty range.
    violation: A 404, or a zero-filled span, misreports emptiness as failure; adding summary fields to the terms body breaks the frozen C1 schema.
    source: FR2.10 (R-03)

  - id: BR4.5
    statement: >
      A storage failure is a 500 carrying the machine code STORAGE_FAILURE, distinct
      from every validation code; that addition is the only permitted change to the
      envelope's code set.
    category: validation
    applies_to: Both /v2 analytics endpoints.
    trigger: The storage layer raises while reading.
    logic: >
      IF a storage read raises, THEN 500 with code STORAGE_FAILURE; IF the failure is a
      validation failure, THEN VALIDATION_FAILED; the two are always distinguishable.
    violation: An unavailable query mistaken for a malformed parameter misdirects the fix.
    source: FR2.12, NFR4

  - id: BR4.6
    statement: >
      An analytics failure is logged through the module logger, with no credential and
      no request parameter concatenated into statement text.
    category: policy
    applies_to: Analytics failure handling.
    trigger: An analytics failure is raised.
    logic: >
      IF a failure occurs, THEN a log record is written through the module logger; the
      record contains no credential and no parameter is interpolated into statement text.
    violation: A silent failure or a leaked value breaches the observability and privacy requirements.
    source: NFR8

  - id: BR4.7
    statement: >
      The /v1 routes, response shapes, error-envelope shape and the sentiment-client
      interface and its adapters are unchanged; only the envelope's code set gains the
      one storage-failure member.
    category: constraint
    applies_to: The existing /v1 surface and the shared envelope.
    trigger: The change is complete and the existing suite runs.
    logic: >
      IF the existing suite runs unchanged, THEN every pre-existing test passes; the
      envelope shape does not move; the client interface gains no member.
    violation: Any /v1 change, or a second envelope-shape change, breaks compatibility.
    source: NFR5

  # ------------------------------------------------------------------ BR5
  - id: BR5.1
    statement: >
      The schema step from v3 to v4 is additive only: no column is dropped, renamed or
      retyped and no row is discarded or rewritten.
    category: constraint
    applies_to: The startup migration.
    trigger: The app starts against a v3 store.
    logic: >
      IF a v3 store is migrated, THEN every pre-existing row survives with its original
      values.
    violation: A destructive change breaches the reuse-the-store constraint.
    source: FR5.1

  - id: BR5.2
    statement: The migration is idempotent — against a store already at v4 it is a no-op that changes and loses nothing.
    category: constraint
    applies_to: The startup migration.
    trigger: The app starts against a v4 store.
    logic: IF the store is already at v4, THEN the step changes nothing and loses nothing.
    violation: A non-idempotent step would fail on every subsequent start.
    source: FR5.4

  - id: BR5.3
    statement: >
      The step creates exactly three named indexes — `idx_analyses_created_at` on the
      created-at column, `idx_analyses_import_id` on the import-id column, and
      `idx_analyses_label_created_at` on the label-plus-created-at pair — matched by name.
    category: constraint
    applies_to: The migrated schema.
    trigger: The migration completes.
    logic: >
      IF the migration completes, THEN all three indexes exist by name; the assertion
      matches by name and never counts every index row, because an unrelated
      auto-generated index also exists.
    violation: Asserting "exactly three" fails against an unrelated implicit index.
    source: FR5.2 (R-19)

  - id: BR5.4
    statement: The table-rebuild path re-creates all three indexes explicitly as steps after the copy.
    category: constraint
    applies_to: The rebuild path (rename -> create -> copy -> drop).
    trigger: A migrating store triggers the rebuild.
    logic: >
      IF the rebuild runs, THEN after the copy it re-creates the three indexes as
      explicit steps, because a create-table declaration has no way to declare an index.
    violation: A rebuild without re-creation silently destroys every index — the pre-existing defect.
    source: FR5.3 (Revision 2)

  - id: BR5.5
    statement: >
      The stored schema version is bumped to 4 in the same transaction as the migration;
      a step that cannot preserve every row fails loudly and rolls back rather than
      completing partially.
    category: policy
    applies_to: The migration transaction.
    trigger: The migration runs, or an unreadable store is encountered.
    logic: >
      IF the migration completes, THEN the stored version reads 4 and was written in the
      same transaction; IF any row cannot be preserved, THEN roll back and re-raise so
      startup halts loudly.
    violation: A partial migration or a mismatched version is never committed.
    source: FR5.6, FR5.7

  - id: BR5.6
    statement: >
      The index-creating step is placed after the migrate-or-create branch, so it runs on
      both the migrate path and the fresh-create path.
    category: constraint
    applies_to: The startup schema initialisation.
    trigger: The app starts, on either path.
    logic: >
      IF the app starts, THEN the index-creating step runs after the branch, following
      the placement the schema-version table already uses, so both paths create the
      indexes.
    violation: Placing the step inside one branch leaves the other path without indexes.
    source: FR5.5 (AC5.1.4)

  # ------------------------------------------------------------------ BR6
  - id: BR6.1
    statement: The read module receives the connection the HTTP edge owns and never opens, closes or owns one itself.
    category: constraint
    applies_to: AnalyticsRead.
    trigger: The read module's body is inspected.
    logic: >
      IF the read module is called, THEN it takes the connection as a parameter and calls
      no open or close operation.
    violation: A second connection-lifecycle site would spread connection ownership.
    source: FR1.3

  - id: BR6.2
    statement: >
      The module that owns the connection decides its thread affinity and lifecycle
      explicitly and states the decision in the module's own documentation.
    category: policy
    applies_to: The connection-owning module at the HTTP edge.
    trigger: The module's documentation is read.
    logic: >
      IF the module documentation is read, THEN it states the chosen thread-affinity
      decision and the connection lifecycle explicitly, rather than leaving a later
      reader to infer a default.
    violation: An inherited default reproduces the cross-thread defect unknowingly.
    source: FR1.6 (R-01)

  - id: BR6.3
    statement: >
      Two genuinely overlapping concurrent requests against either endpoint raise no
      cross-thread connection error; reverting the thread-affinity decision makes the
      concurrency test fail.
    category: constraint
    applies_to: Both endpoints and the concurrency test.
    trigger: Two overlapping requests are in flight on different threads.
    logic: >
      IF two requests genuinely overlap, THEN neither raises the cross-thread connection
      error; the test asserts the overlap and passes only because the decision is applied.
    violation: The defect returning must make the test red, not green.
    source: FR1.6, FR8.4

  - id: BR6.4
    statement: >
      The replaced test harness issues genuinely concurrent requests on different
      threads, hoists schema initialisation out of the per-request path, keeps the
      offline guard armed, and updates every existing call site.
    category: policy
    applies_to: Test harness and suite.
    trigger: The harness runs concurrent requests.
    logic: >
      IF two requests each re-enter the harness, THEN they overlap on different threads;
      schema initialisation runs once so the test fails on the connection defect rather
      than on a locked-schema error; the existing tests still pass; the statement-count
      measurement observes a single application-startup initialisation.
    violation: A per-request migration makes the concurrency test red for the wrong reason.
    source: FR7.7, FR8.4

  - id: BR6.5
    statement: >
      The run path enforces the loopback bind at startup: a non-loopback host fails
      loudly with an explanation, and the bind constant is the value the run path
      consumes.
    category: policy
    applies_to: Application startup and the run path.
    trigger: The app starts, or a non-loopback host is supplied.
    logic: >
      IF the host is loopback, THEN the normal local run is unchanged; IF the host is not
      loopback, THEN startup fails loudly rather than serving; a documented server
      default is not enforcement.
    violation: Serving on a non-loopback interface exposes an unauthenticated app holding the operator's key.
    source: FR7.6

  - id: BR6.6
    statement: >
      Tests assert against real storage and real served markup, the suite is green with
      no network and no API key, and the offline guard is proven armed;
      acceptance-before-implementation is carried by reference to the team's testing
      contract, not asserted here.
    category: policy
    applies_to: Test suite.
    trigger: The suite runs, or a new test asserts.
    logic: >
      IF a new test asserts, THEN the value is read back from real storage or real served
      markup, never from a double of the thing under test; the offline guard is armed and
      a test proves it; the coverage floor holds; the test-ordering practice is referenced
      rather than asserted.
    violation: A test double of the subject makes a green suite meaningless.
    source: NFR7, FR8.5, FR8.7
```

## Rules summary

| Rule | Category | Applies to | One-line statement | Source |
|---|---|---|---|---|
| `BR1.1` | calculation | Both endpoints | Inclusive UTC calendar-day bounds; `to` covers the whole day | FR2.4 |
| `BR1.2` | calculation | Both endpoints | A single bound is never dropped | FR2.5 |
| `BR1.3` | calculation | Both endpoints | Unbounded span = earliest day..today; matched `import_id` = its rows | FR2.6 |
| `BR1.4` | validation | Both endpoints | Inverted range is refused, never silently emptied | FR2.11 |
| `BR1.5` | constraint | Both endpoints | Resolution is identical for summary and terms | FR3.8 |
| `BR2.1` | calculation | AnalyticsSummary | `total` + per-label counts over the closed vocabulary | FR2.1/2.3/3.6 |
| `BR2.2` | calculation | Summary, series | Shares = 4-decimal fraction; `null` on a zero denominator | FR2.7 |
| `BR2.3` | calculation | Summary, series | Mean confidence over all rows, 4-decimal; row count = total | FR2.8 |
| `BR2.4` | calculation | AnalyticsTermList | Terms per label; neutral contributes to neither; empty not null | FR3.3/3.6/3.7 |
| `BR2.5` | calculation | Term list items | Count desc, alphabetical ties, term+count only | FR3.5 |
| `BR2.6` | validation | Terms endpoint | `limit` default 10; below 1 refused; oversized honoured | FR3.3/3.4 |
| `BR2.7` | constraint | AnalyticsRead | Read-only; no mutating operation and no access bookkeeping | FR2.13 |
| `BR2.8` | constraint | Analytics modules | In-process only; no egress, no credential | FR1.2, NFR2 |
| `BR2.9` | constraint | AnalyticsRead | Parameter-bound statements only | FR1.4 |
| `BR2.10` | constraint | Route + read module | Aggregates in one read module; route holds no statement | FR1.1 |
| `BR2.11` | policy | Summary region | Series + breakdown containers; one fetch per section | FR6.2 |
| `BR2.12` | policy | Label breakdown | Render the fraction; `null` share = no-share marker, never 0% | FR2.7 |
| `BR2.13` | constraint | View + router | The view's `/v2` prefix equals the router's, statically asserted | FR6.9 |
| `BR2.14` | policy | Summary region markup | Hooks pinned in the existing test-id convention | FR6.9 |
| `BR2.15` | policy | New modules | One responsibility per module; typed; no third-party validator; no new config | FR1.5, NFR6 |
| `BR3.1` | calculation | Series | One entry per UTC day of the matched resolved range, including edge days | FR2.9 |
| `BR3.2` | calculation | Series entry | Any gap or edge day zero-filled; zero-day row count = 0 | FR2.9 |
| `BR3.3` | calculation | Series | No-match range yields an empty series, never a 404 | FR2.10 |
| `BR3.4` | calculation | Series | One grouped read + in-process fill; statement count day-independent | NFR1, FR8.9 |
| `BR3.5` | constraint | Series entry | All six fields always present | FR2.9 |
| `BR3.6` | calculation | Both endpoints | 200 ms budget over 10,000 rows, measured without coverage | NFR1, FR8.9 |
| `BR4.1` | validation | Both endpoints | Envelope is `{code, message}`; message names the field; no `field` member | FR2.12 |
| `BR4.2` | validation | Both endpoints | Malformed `from`/`to`/`limit` refused 422; nothing computed | FR2.11, FR3.4 |
| `BR4.3` | validation | Both endpoints | Inverted range: one 422 naming both bounds | FR2.11 |
| `BR4.4` | policy | Both endpoints | No-match is 200 in each endpoint's own frozen empty shape, never 404 | FR2.10 |
| `BR4.5` | validation | Both endpoints | Storage failure 500 `STORAGE_FAILURE`, distinct from validation | FR2.12 |
| `BR4.6` | policy | Failure handling | Logged via the module logger; no credential; no parameter interpolated into statement text | NFR8 |
| `BR4.7` | constraint | `/v1` + envelope | `/v1`, envelope shape and client interface unchanged | NFR5 |
| `BR5.1` | constraint | Migration | Additive only; no column or row lost | FR5.1 |
| `BR5.2` | constraint | Migration | Idempotent; an already-v4 store is a no-op | FR5.4 |
| `BR5.3` | constraint | Migrated schema | Three named indexes, matched by name | FR5.2 |
| `BR5.4` | constraint | Rebuild path | Indexes re-created explicitly after the copy | FR5.3 |
| `BR5.5` | policy | Migration transaction | Version 4 written in the same transaction; fail loud + roll back | FR5.6/5.7 |
| `BR5.6` | constraint | Schema initialisation | Index step after the migrate-or-create branch, on both paths | FR5.5 |
| `BR6.1` | constraint | AnalyticsRead | Connection is received, never opened or closed | FR1.3 |
| `BR6.2` | policy | Connection module | Thread affinity and lifecycle decided explicitly, stated in the module's documentation | FR1.6 |
| `BR6.3` | constraint | Both endpoints | Concurrent overlapping requests raise no cross-thread error | FR1.6, FR8.4 |
| `BR6.4` | policy | Harness + suite | Concurrent threads; schema init hoisted; every call site updated | FR7.7 |
| `BR6.5` | policy | Startup + run path | Loopback enforced at startup; non-loopback fails loudly | FR7.6 |
| `BR6.6` | policy | Test suite | Real storage/markup, guard armed, coverage floor; ordering by reference | NFR7 |

## Adjacent contradictions (for the gate)

These are upstream defects this unit must not paper over. They are stated here,
against the rules above, so the traceability gate sees them explicitly.

1. **`AC2.4.3` is unreachable as written (contract UC1).** The criterion requires
   a 422 naming `query.import_id` for a "malformed `import_id`". The contract pins
   `import_id` as an **opaque string** with **no parse step**, so it has no parse
   failure to fail; an unmatched id is a 200 empty result (`AC2.4.2`, `BR4.4`). The
   `from`/`to` halves of the same criterion **are reachable and are owned by
   `BR4.2`**. `AC2.4.3` is therefore recorded as **`N/A`** in `traceability.json`:
   the unreachable `import_id` clause identifies no BR target, and the reachable
   `from`/`to` halves map to `BR4.2`. No test is written for the `import_id` 422,
   because no input can produce it.

2. **`AC2.3.3`'s second clause is self-contradictory (contract UC2).** It says a
   zero-filled sibling day carries `null` for **both** mean fields, while its own
   first clause and `AC2.1.3` say `mean_confidence_row_count` equals that day's
   `total`. Both cannot hold on a zero day. **`BR3.2` pins the correct reading:**
   `mean_confidence` = `null` and `mean_confidence_row_count` = `0` (the day's
   `total`). `AC2.3.3` is mapped `OK` to `BR3.2` with the defect noted in the
   traceability entry.

3. **`AC2.4.5` is a duplicate id in `stories.md`.** It appears twice: once (from
   `R-19`) for the terms `limit` refusal and an oversized value, and once for the
   500 storage-failure code. The traceability entry for `AC2.4.5` covers both
   clauses, mapping to `BR2.6`/`BR4.2` (limit) and `BR4.5` (500), with a note.

4. **`field ==` phrasing in `AC2.4.3` / `AC3.1.3`.** Both say the 422 names a
   `field` member. The envelope is exactly `{code, message}` with
   `additionalProperties: false` (verified against the running code); `BR4.1`
   pins the message-text form. Map to `BR4.1`/`BR4.2`, not to a `field` member.

5. **Rounding tie rule is unspecified (contract O1).** `BR2.2`/`BR2.3` pin
   four-decimal rounding but not a tie rule. The human is choosing it now; this
   stage does **not** invent one. Each rule carries a labelled
   `RULED HALF-UP (R-06)` placeholder for a follow-up edit to fill, and
   the flag at the top of this file marks it as pending rather than settled.
