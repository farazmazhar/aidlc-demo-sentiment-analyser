# Scope Definition

## In Scope

- An **additive, idempotent migration** that adds tables/indexes for analytics without any destructive change to the existing schema. [Q1] [Q2] [desc]
- **`GET /v2/analytics/summary?from=&to=&import_id=`** returning total analyses, per-label counts and shares, mean confidence, mean intensity, and a per-day time series. [Q1] [desc]
- **`GET /v2/analytics/terms?from=&to=&limit=`** returning the most frequent significant terms in positive versus negative texts, in-process and with no external service. [Q1] [desc]
- A **second page/section** rendering the time series, the label breakdown, and the top-term lists, with a date-range control, working fully offline against the dummy client. [Q1] [desc]
- **Offline, requirement-driven tests** covering the new endpoints (empty range, populated range, `import_id` filter, term extraction), with the existing suite staying green. [desc]

## Out of Scope

- Rewriting the existing sentiment engine, persistence contracts, `SentimentClient` interface, or single-page UI. [desc]
- Any new external service or new data egress path; analytics is computed in-process from stored rows. [desc]
- Destructive schema changes of any kind. [desc]
- A retention or delete endpoint for stored raw text. This is a pre-existing gap, not part of this change unless separately elected. [feasibility-assessment R-3]

## Scope Boundary Reasoning

All four capabilities (migration, both endpoints, and the page/section) are **must-have**; nothing was identified as nice-to-have. [Q2] The minimum viable scope is therefore the full stated feature, not a subset. [Q1] The capabilities have a dependency chain — migration first, then the endpoints, then the page — and the chosen sequencing preference is **risk-first**, so the additive migration and the term extraction (the named unknowns) are tackled before the page. [Q3] [Q4] There are no hard deadlines; the one-session target is soft. [Q5]

## Value Stream Map

| Capability | Value to the developer | How we know it worked |
|------------|------------------------|------------------------|
| Additive analytics migration | Makes the already-stored rows addressable for analytics without risking existing data | Existing suite stays green; schema change is additive and idempotent. [Q1] [desc] |
| Summary endpoint | Answers "how much, what mix, how confident, and how is it trending?" in one call | Correct aggregates returned for seeded data. [Q1] [desc] |
| Terms endpoint | Shows what the positive and negative text actually says | Correct top terms returned for seeded data. [Q1] [desc] |
| Page/section | Lets the developer read the picture at a glance instead of by hand | Page renders the series, breakdown, and term lists and respects the date range. [Q1] [desc] |
