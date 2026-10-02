# Initiative Brief — sentiment-opencode v2 (analytics layer)

## Intent and Problem Statement

The app already stores every text analysis but never summarises it: the developer cannot see totals, per-label counts and shares, average confidence or intensity, or how sentiment moves over time without reading rows by hand. The initiative adds an analytics layer on top of the stored analyses, reusing the existing engine, persistence, UI, and API contracts rather than rewriting them. **Customer:** the developer alone, as sole user and operator. **Trigger:** the stored history is now worth summarising. *(Source: `ideation/intent-capture/intent-statement.md`)*

## Market Validation Summary

**Pending.** Market Research was skipped at Ideation on the grounds that this is an internal, single-user, localhost-only tool with no market or competitors and a build-vs-buy choice already settled by the request's own constraints. The human has recorded that Market Research must now run before this handoff is approved (Q7), so this section is completed in a follow-up pass and re-approved. *(Source: `ideation/approval-handoff/approval-handoff-questions.md` Q5, Q7)*

## Feasibility and Risk Highlights

Feasible, no blocker: every integration surface already exists, and the two new endpoints and the page are computed entirely in-process from stored rows with no new external service.

| Risk | Treatment |
|------|-----------|
| The project has no migration mechanism today; an additive, idempotent migration is net-new work | Pin the approach in Requirements Analysis and Design before building |
| The soft one-session target is optimistic against the full feature scope | Accepted — the target is explicitly soft, not a deadline |
| Raw text may be personal data, stored unencrypted with no retention/delete path | Analytics adds no new egress path; retention work is pre-existing and out of scope unless elected |
| New tests must stay fully offline while the existing suite stays green | Reuse the existing dummy-client and offline-test patterns |

*(Source: `ideation/feasibility/feasibility-assessment.md`, `raid-log.md`)*

## Scope Boundary

**In:** additive idempotent migration; `GET /v2/analytics/summary`; `GET /v2/analytics/terms`; a second page/section with a date-range control; offline requirement-driven tests with the existing suite green.

**Out:** rewriting the engine, persistence contracts, or existing UI; any new external service or egress path; destructive schema changes; a retention/delete endpoint.

All four capabilities are must-have; nothing is nice-to-have. *(Source: `ideation/scope-definition/scope-document.md`, `intent-backlog.md`)*

## Concept Visuals

An **Analytics** entry point inside the existing single-page shell, with the date-range control first, then the per-day time series, then the label breakdown, then the two top-term lists. Native HTML with the page's existing class names — no design system, no front-end library. Five states drawn: populated, empty, loading, error, partial. Desktop-first with a stacked narrow layout; WCAG 2.1 AA basics. *(Source: `ideation/rough-mockups/wireframes.md`, `user-flow.md`)*

Open items carried from the mockup review: the default date-range rule, the failed-request error surface, `import_id`'s UI disposition, and the top-terms default. *(Source: `ideation/rough-mockups/reviews/review-01.md`)*

## Team Plan

Not applicable. This is a solo-developer project: one person is the sole user, operator, and decision-maker, with no influencers, no second reviewer, and no capacity pool. Team Formation was skipped on that basis. *(Source: `ideation/approval-handoff/approval-handoff-questions.md` Q6)*

## Prioritized Backlog

| ID | Proto-Unit | Priority | Depends on | Order |
|----|-----------|----------|-----------|-------|
| U1 | Additive analytics migration | Must have | — | 1 |
| U2 | Terms endpoint | Must have | U1 | 2 |
| U3 | Summary endpoint | Must have | U1 | 3 |
| U4 | Analytics page/section | Must have | U2, U3 | 4 |

Order applies the risk-first preference: the migration and the term extraction are the named unknowns and lead. *(Source: `ideation/scope-definition/intent-backlog.md`)*

## Go / No-Go Recommendation

**Conditional go.** The intent, scope, feasibility, and concept are aligned and the work is feasible with no blocker. Approval is held on one condition: **Market Research must run first**, per the human's decision at Q7. Once it runs and this brief's market validation section is completed, the handoff can be approved and the workflow proceeds to Inception.