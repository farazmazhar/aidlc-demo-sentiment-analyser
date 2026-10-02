# Intent Backlog

Priority scheme: **MoSCoW** (chosen for a fixed feature boundary; every item is Must-have per the scope answers). This is the proto-Unit backlog; Units Generation and Delivery Planning refine it into Units and Bolts.

| ID | Proto-Unit | Description | Priority | Depends on | Planned order |
|----|-----------|-------------|----------|-----------|---------------|
| U1 | Additive analytics migration | Add the tables/indexes analytics needs, via an additive, idempotent migration; never a destructive change | Must have | — | 1 |
| U2 | Terms endpoint | `GET /v2/analytics/terms?from=&to=&limit=` returning the most frequent significant terms in positive versus negative texts, computed in-process | Must have | U1 | 2 |
| U3 | Summary endpoint | `GET /v2/analytics/summary?from=&to=&import_id=` returning totals, per-label counts and shares, mean confidence, mean intensity, and a per-day time series | Must have | U1 | 3 |
| U4 | Analytics page/section | A second page/section rendering the time series, label breakdown, and top-term lists, with a date-range control, offline against the dummy client | Must have | U2, U3 | 4 |

Priorities reflect the confirmed answers: all four capabilities are must-have and nothing is nice-to-have. [Q2] The dependency chain is migration → endpoints → page. [Q3] The order applies the **risk-first** preference: U1 (the migration mechanism) and U2 (term extraction, a named unknown) lead, U3 follows, and U4 (the page) comes last because it consumes both endpoints. [Q4] There are no hard deadlines affecting the order. [Q5]

## Coverage

Each of the four build capabilities in `scope-document.md` maps to exactly one proto-Unit above, and every proto-Unit traces to the intent statement and the feasibility constraints. The fifth in-scope item — the offline requirement-driven tests — is deliberately not a proto-Unit of its own: it is delivered alongside each capability and verified at Build and Test. No build capability is left unowned.
