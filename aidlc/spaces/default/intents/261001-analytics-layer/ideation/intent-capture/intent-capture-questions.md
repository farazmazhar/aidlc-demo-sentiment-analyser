## Sources

- [desc] Initial description: "Build \"sentiment-opencode v2\": add an analytics layer to the existing sentiment app.\n\nContext: this app already implements text sentiment via Jev/OpenRouter (dummy + live clients behind one interface), SQLite persistence, a single-page UI + /v1 JSON API, and CSV bulk import/export (see ./app and the completed poc/classic/express intents). Treat it as brownfield: run reverse-engineering, keep what works, and extend it — do not rewrite the existing engine/persistence contracts.\n\nGoal: an analytics layer on top of stored analyses.\n- Add GET /v2/analytics/summary?from=&to=&import_id= returning: total analyses, per-label counts and shares, mean confidence, mean intensity, and a per-day time series.\n- Add GET /v2/analytics/terms?from=&to=&limit= returning the most frequent significant terms in positive vs negative texts (reuse a simple tokenizer; no external services).\n- Add a second page/section that renders the time series, the label breakdown, and the top-term lists, with a date-range control, so it works fully offline against the dummy client.\n\nConstraints:\n- Reuse the existing SentimentClient interface, SQLite schema (add tables/indexes only via migration, never a destructive change), error envelope, and config.example.toml / gitignored config.local.toml convention.\n- No new external services; analytics computed in-process from stored rows.\n- Tests: offline, requirement-driven, covering the new endpoints (empty range, populated range, import_id filter, term extraction) plus the existing suite staying green.\n\nAcceptance criteria: the new endpoints return correct aggregates for seeded data; the page renders them and respects the date range; migrations are additive and idempotent; all tests pass with no network and no key.\n\nIf any requirement is ambiguous, ask me before building rather than guessing."
- [scope] Workflow-selected scope: `feature`.

## Q1. What business problem does the analytics layer solve — what can you do with the stored analyses that you cannot do today?

A. Today each analysis is stored but never summarised: I cannot see totals, per-label shares, average confidence or intensity, or how sentiment moves over time without reading rows by hand.
B. I cannot see what the text is actually saying — the most frequent significant terms in positive versus negative texts are invisible today.
C. Both: I need the aggregate picture (counts, shares, averages, a per-day trend) and the term-level picture, shown together and filterable by date range.
D. The stored history is already sufficient; the gap is purely that the app never surfaces it in a form I can read at a glance.
E. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. Who is the customer, and what pain are they experiencing today?

A. Me alone, as the developer/operator who runs the app locally and reads the analytics myself.
B. A small team that uses the app to tag text and wants to review sentiment trends without exporting CSV and analysing it elsewhere.
C. Whoever evaluates this work, who needs to see the analytics layer run end to end offline.
D. Not identified
X. Other (please specify)

[Answer]: A

## Q3. What does success look like — which measurable outcomes tell you this worked?

A. The stated acceptance criteria are the bar: the new endpoints return correct aggregates for seeded data, and the page renders them and respects the date range.
B. Correctness plus durability: migrations are additive and idempotent, and the existing engine/persistence contracts are untouched.
C. Correctness plus test evidence: offline, requirement-driven tests cover the new endpoints (empty range, populated range, import_id filter, term extraction) and the existing suite stays green with no network and no key.
D. All of the above — the acceptance criteria, the additive/idempotent migration, and the offline test evidence together.
E. Not yet defined
X. Other (please specify)

[Answer]: A

## Q4. What triggered this initiative now?

A. The stored analysis history is now large or valuable enough that aggregate insight is worth building.
B. A planned demo or evaluation of this exercise needs the analytics layer visible.
C. A specific reporting question about the stored data came up that the app cannot answer today.
D. Not applicable
X. Other (please specify)

[Answer]: A

## Q5. Who are the key stakeholders — who decides scope and priority, and who influences those decisions?

A. Only me: I decide scope and priority, and nobody else influences it.
B. I decide; reviewers or evaluators of this work influence the direction.
C. A small group (2-5 people) uses it, one person sets priority, and at least one other influences it.
D. Not identified
X. Other (please specify)

[Answer]: A

## Q6. Are there communication requirements or a reporting cadence for this work?

A. None — no reporting cadence is needed.
B. A short written summary when the work completes is enough.
C. Regular progress updates are expected while it is being built.
D. Not identified
X. Other (please specify)

[Answer]: B

## Q7. The workflow was started with the `feature` scope (Standard depth, all 33 stages). Does that match the product boundary you have in mind?

A. Yes — plan the full lifecycle: build both analytics endpoints, the second page, the additive migration, and the offline tests as specified.
B. Narrower — this is an analytics-API spike; the second page/section matters less than the endpoints and the migration.
C. Broader — this is the first slice of an analytics product we intend to extend and keep using.
D. Not sure — let's discuss the boundary.
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

## Assumption Confirmation

The following assumptions remain. Accept them and continue, or convert them to follow-up questions.

- The precise definition of a "significant" term for `/v2/analytics/terms` (stopword set, minimum length, stemming, case folding) is not fixed; the request requires only reusing a simple tokenizer with no external services.
- "A second page/section" leaves the placement open — a separate page or a section on the existing single-page UI.

A. Accept assumptions
B. Convert to follow-up questions

[Answer]: A. Accept assumptions
