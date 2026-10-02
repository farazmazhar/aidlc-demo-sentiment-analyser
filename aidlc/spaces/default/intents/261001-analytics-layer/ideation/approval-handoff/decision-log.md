# Decision Log — Ideation phase

Every decision recorded during the Ideation phase, with the stage and the answer that produced it.

| ID | Decision | Stage | Source |
|----|----------|-------|--------|
| D-01 | The target customer is the developer alone, as sole user and operator | Intent Capture | Q2 |
| D-02 | The initiative is triggered by the stored analysis history becoming large or valuable enough to summarise | Intent Capture | Q4 |
| D-03 | Success is measured against the stated acceptance criteria (correct aggregates for seeded data; the page renders them and respects the date range) | Intent Capture | Q3 |
| D-04 | The product boundary is the full feature scope — both endpoints, the second page, and the additive migration | Intent Capture | Q7 |
| D-05 | Two open items (the definition of a "significant" term; a separate page versus a section) are retained as assumptions, not resolved by guessing | Intent Capture | Assumption Confirmation — `A. Accept assumptions` |
| D-06 | Stage reviews run as a single advisory pass; findings are carried to the human gate rather than self-revised | Intent Capture | Reviewer disposition |
| D-07 | Market Research is skipped — internal single-user tool, no market, build-vs-buy pre-settled by the request's constraints | Market Research | Stage condition |
| D-08 | Feasibility is executed rather than skipped — brownfield integration constraints and open technical uncertainty meet the stage's execute condition | Feasibility | Stage condition |
| D-09 | Privacy obligations are in scope; the analytics endpoints add no new egress path | Feasibility | Q2 |
| D-10 | No cloud / AWS assessment applies — localhost-only by rule | Feasibility | Q6 |
| D-11 | The biggest technical uncertainty is recorded as "not yet defined" and carried as an open RAID item rather than invented | Feasibility | Q7 |
| D-12 | Minimum viable scope is the full stated feature; all four capabilities are must-have, nothing nice-to-have | Scope Definition | Q1, Q2 |
| D-13 | Capability order is migration → terms endpoint → summary endpoint → page (risk-first) | Scope Definition | Q3, Q4 |
| D-14 | There are no hard deadlines; the one-session target is soft | Scope Definition | Q5 |
| D-15 | Team Formation is skipped — solo developer, no team, no capacity pool | Team Formation | Stage condition |
| D-16 | The analytics feature is an entry point inside the existing single-page shell, not a separate site | Rough Mockups | Q1 |
| D-17 | Core flow: open the app → go to analytics → see the default date range rendered → adjust the range → the view updates | Rough Mockups | Q2 |
| D-18 | Information hierarchy: date-range control, per-day time series, label breakdown, then the two top-term lists | Rough Mockups | Q3 |
| D-19 | No design system and no front-end library — native HTML and the page's existing class names | Rough Mockups | Q4 |
| D-20 | Desktop/laptop first, with the same order stacked on a narrow screen | Rough Mockups | Q5 |
| D-21 | WCAG 2.1 AA basics matching the existing page | Rough Mockups | Q6 |
| D-22 | All five screen states are drawn, including the error surface required by the binding error-envelope rule | Rough Mockups | Stage body |
| D-23 | Four open items carried forward: the default date-range rule, the failed-request error surface, `import_id`'s UI disposition, and the top-terms default | Rough Mockups | `reviews/review-01.md` |
| D-24 | Stakeholder agreement, risk acknowledgement, resource availability, and mockup alignment are all confirmed | Approval & Handoff | Q1–Q4 |
| D-25 | Mob staffing is not applicable | Approval & Handoff | Q6 |
| D-26 | Market Research must run before this handoff is approved | Approval & Handoff | Q7 |