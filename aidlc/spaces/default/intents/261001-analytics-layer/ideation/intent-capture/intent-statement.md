## Problem Statement

The app already stores every text analysis, but it never summarises them: the developer cannot see totals, per-label counts and shares, average confidence or intensity, or how sentiment moves over time without reading rows by hand. [Q1] The requested change is an analytics layer on top of the stored analyses, keeping the existing sentiment engine and persistence contracts as they are. [desc]

## Target Customer

The developer alone — the person who runs the app locally, submits or imports text, and reads the resulting analytics. [Q2] There is no separate operator, reviewer, or end-user group beyond that single person. [Q5]

## Success Metrics

- `GET /v2/analytics/summary?from=&to=&import_id=` returns total analyses, per-label counts and shares, mean confidence, mean intensity, and a per-day time series over the requested date range and optional import. [desc]
- `GET /v2/analytics/terms?from=&to=&limit=` returns the most frequent significant terms in positive versus negative texts, computed with a simple tokenizer and no external service. [desc]
- A second page/section renders the time series, the label breakdown, and the top-term lists, with a date-range control, working fully offline against the dummy client. [desc]
- Schema changes are additive and idempotent; there is no destructive change to the existing SQLite schema or to the existing engine/persistence contracts. [desc]
- The new endpoints are covered by offline, requirement-driven tests (empty range, populated range, import_id filter, term extraction) and the existing suite stays green with no network and no key. [desc]
- These stated acceptance criteria are the bar for the work. [Q3]

## Initiative Trigger

The stored analysis history is now large or valuable enough that aggregate insight is worth building. [Q4]

## Initial Scope Signal

The workflow-selected scope is `feature` (Standard depth, all 33 stages). [scope]

The user-confirmed product boundary matches it: plan the full lifecycle — both analytics endpoints, the second page, the additive migration, and the offline tests as specified. [Q7]

## Assumptions & Open Questions

- [assumption] The precise definition of a "significant" term for `/v2/analytics/terms` (stopword set, minimum length, stemming, case folding) is not fixed by the request; the request requires only reusing a simple tokenizer with no external services. [desc] To be pinned in Requirements Analysis.
- [assumption] "A second page/section" leaves the placement open — a separate page or a section on the existing single-page UI. [desc] To be settled in Design.
