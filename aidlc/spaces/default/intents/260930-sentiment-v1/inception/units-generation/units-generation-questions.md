# Units Generation — Clarifying Questions

Context: this stage turns the five components into the units of work that Construction will build and
describes what can depend on what. It decides topology only — the order in which work actually ships
belongs to Delivery Planning, which consumes this DAG.

The app is one localhost service with one page and one API, plus the five components from Domain
Design (Configuration, Persistence, SentimentEngines, AnalysisService, WebSurface) and three entities
(AnalysisRecord, EngineSettings, SessionCredential). The intent's constraints stay in force: two
runtime dependencies, no cloud, no Docker, single local user.

---

## Q1. What is the unit boundary strategy?

- A. One unit per deployable: the whole application is a single `service` unit
- B. Two units: the application as one `service` unit, plus a `spec` unit holding the HTTP/JSON contract
- C. Five units mirroring the components (each component its own unit)
- X. Other (please specify)

[Answer]: A. One unit per deployable: the whole application is a single `service` unit

## Q2. How fine should the units be?

- A. Coarse — one or two units, matching the single deployable
- B. Medium — three to five units, grouped where components share a lifecycle
- C. Fine — one unit per component, five or more
- X. Other (please specify)

[Answer]: A. Coarse — one or two units, matching the single deployable

## Q3. How should dependencies and parallelism be treated?

- A. Strict topological edges only; no parallel units (a single chain)
- B. Edges only where a real dependency exists, leaving genuinely independent units parallelisable
- C. Every unit depends on the persistence unit (shared state as a hub)
- X. Other (please specify)

[Answer]: A. Strict topological edges only; no parallel units (a single chain)

## Q4. What deployment model applies?

The affirmed constraints are localhost only, no cloud and no container.

- A. Monolithic local deploy: one process, one unit
- B. Hybrid: the application deploys as one process, with a separately versioned contract/spec artifact
- C. Independent units that could deploy separately later
- X. Other (please specify)

[Answer]: A. Monolithic local deploy: one process, one unit

## Q5. How is the in-process handoff between the analysis service and the engines treated across units?

Domain Design records an in-process event handoff (ADR-003) and the architecture review notes it has
no owning component or message shape yet.

- A. Keep it inside the single unit; the seam is an internal interface, not a unit boundary
- B. Make it an explicit integration point between two units, with the request/result shapes written here
- C. Simplify back to a direct synchronous call and drop the handoff
- X. Other (please specify)

[Answer]: A. Keep it inside the single unit; the seam is an internal interface, not a unit boundary
