# Units of Work — `very-cool-sentiment-analysis` v1

## Unit summary

One unit (answers Q1 = A, Q2 = A): the whole application is a single deployable. The scope's
walking-skeleton flag is off, so no thin-slice ceremony runs and there is no skeleton marker.

| Unit ID | Name | Directory | Kind | Deployment | Complexity |
|---|---|---|---|---|---|
| U1 | Application | `u1-application` | service | Single local process, monolithic | L |

## U1 — Application

**Description.** The complete localhost sentiment-analysis application: the page, the JSON API, the
engine contract and its two implementations, the analysis sequence, the configuration resolution and
the local SQLite store.

**Boundaries.** Everything the intent ships. The five components from `domain-design/components.md` —
Configuration, Persistence, SentimentEngines, AnalysisService and WebSurface — are internal structure
of this unit, not separate units. Nothing outside the repository is part of the unit except the
OpenRouter endpoints it may call in live mode and the local config file it reads.

**Responsibilities**

- Serve the single page, the JSON API (`POST /analyze`, `GET /analyses`) and the health endpoint.
- Resolve the active engine from `config.local.toml` or the in-app sign-in, defaulting to offline.
- Expose one engine interface with the offline `DummySentimentClient` and the live
  `OpenRouterJevSentimentClient`, and read the live answer only as typed data.
- Validate request boundaries and refuse invalid input without writing anything.
- Own and store the analysis record, creating the database on first run and migrating it in place.
- Hold a session credential in memory only, drop a rejected one, and never render or log it.
- Bind loopback only.

**Design-artifact scope.** As a `service` unit it carries the full construction design matrix
(functional design, NFR requirements, NFR design, infrastructure design, code generation, build and
test) rather than a reduced set.

**Implementation notes and constraints**

- Two runtime dependencies (`fastapi`, `uvicorn`) plus the standard-library `sqlite3`; the coverage
  tool, linter and test runner stay under the development extra.
- Localhost only: no cloud component, no container, no account system.
- The whole test suite runs offline; the live client is exercised through an injected transport.
- The in-process handoff between the analysis service and the engines (ADR-003) is an internal
  interface of this unit, not a unit boundary (answer Q5 = A).
- The class renames required by FR6.1 and the stale authentication comment in `app/main.py` are part
  of this unit's work.
- The repository already contains the twelve application modules and ten test modules; the unit is
  built by converging them, not from scratch.

**Acceptance of the unit as a whole.** Every story in `unit-of-work-story-map.md` is implemented and
its acceptance criteria are covered by tests the installed tooling can run, with the project's
verification command (install, `pytest`, then start the app locally and exercise the changed path)
demonstrating the result end to end.
