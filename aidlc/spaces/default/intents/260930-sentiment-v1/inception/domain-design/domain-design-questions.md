# Domain Design — Clarifying Questions

Context: this stage names the logical building blocks the v1 code will be organised into. The app
already exists as 12 Python modules in `app/` (config, db, repository, models, sentiment, dummy_client,
openrouter_client, service, routes, session_auth, main) plus the static page, and the code knowledge
base records those modules and their responsibilities. Nothing here decides deployment topology,
technology or NFR patterns.

The answers shape the component catalogue (`components.md`), the entity-ownership table, and the ADR
log (`decisions.md`).

---

## Q1. How coarse should the components be?

- A. Keep today's module families as the component set: configuration, persistence, engine interface, the two engines, analysis service, HTTP surface, session authorization, web UI (eight or nine components)
- B. Collapse to around five: configuration, persistence, sentiment engines, analysis service, web surface
- C. A finer cut that separates entities and contracts from behaviour (for example a records component distinct from the repository)
- X. Other (please specify)

[Answer]: B. Collapse to around five: configuration, persistence, sentiment engines, analysis service, web surface

## Q2. Who owns the analysis record?

- A. The persistence component owns it, as today
- B. A records/contracts component owns the shape, and persistence stores it
- C. The analysis service owns it, and persistence is a pure store
- X. Other (please specify)

[Answer]: A. The persistence component owns it, as today

## Q3. How do the analysis service and the engines interact?

- A. Synchronous calls through the existing interface, as today
- B. A registry the service resolves the active engine from, still synchronous
- C. An event/queue style handoff between service and engines
- X. Other (please specify)

[Answer]: C. An event/queue style handoff between service and engines — recorded as an in-process handoff, since the affirmed constraints exclude any external broker (localhost only, no cloud, two runtime dependencies)

## Q4. How is the web surface decomposed?

The page, the JSON API and the health endpoint all live in one module today, and the refined mockups
introduce several page states.

- A. Keep one web-surface component owning routes, the page and its states
- B. Split the JSON API from the page/static surface into two components
- C. Split further: routes, page state handling, and the connection indicator as separate components
- X. Other (please specify)

[Answer]: A. Keep one web-surface component owning routes, the page and its states

## Q5. How should the existing code be treated in brownfield terms?

- A. Keep today's module boundaries and package layout; the work renames and converges in place
- B. Regroup the modules into sub-packages that mirror the new components
- C. Restructure more aggressively where the current layout obscures a boundary
- X. Other (please specify)

[Answer]: A. Keep today's module boundaries and package layout; the work renames and converges in place
