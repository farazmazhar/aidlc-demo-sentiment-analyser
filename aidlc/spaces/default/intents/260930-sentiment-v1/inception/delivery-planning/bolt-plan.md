# Bolt Plan — `very-cool-sentiment-analysis` v1

A Bolt is one build pass over a piece of the work, ending in something that runs. This plan is the
economic path through the dependency graph: Units Generation produced the topology (one unit, no
edges), and this stage chose what to do first and how much to do in one pass (answers Q1 = A, Q3 = A).

## Bolt sequence

| # | Bolt | Units of Work | Walking skeleton? | Owner |
|---|---|---|---|---|
| 1 | Converge the v1 contract, storage and engine paths, then finish the interface | `U1` (Application) | No — this scope's skeleton flag is off, so no thin-slice ceremony runs | `aidlc-developer-agent` (AI) |

There is one Bolt because there is one deployable: the whole unit lands in one pass. Nothing here
sequences units against each other, because there is nothing to sequence.

## Bolt 1 — Converge the v1 contract, storage and engine paths, then finish the interface

**Included Units of Work.** `U1` (Application) — every component inside it (Configuration,
Persistence, SentimentEngines, AnalysisService, WebSurface).

**Order inside the Bolt (risk-first).** The work is taken in the order the human chose: the riskiest
parts first, then the interface.

1. The engine path: the typed contract, the offline and live implementations under their v1 names, and
   the live client exercised through an injected transport.
2. The storage path: the `provider` column, the in-place migration against the existing local
   database, and the v1 record shape.
3. The failure paths: the live-attempt refusal, the error envelope's codes, and the boundary
   validation.
4. The interface: the page states, the connection indicator, the accessibility fixes, and the
   documentation and manifest corrections.

**Definition of Done.** Every story in `unit-of-work-story-map.md` is implemented; the project's
verification command runs green; the coverage floor holds over the whole application with the live
client covered offline; the linter and formatter run clean; and the page, the API and the health
endpoint behave as `contract-summary.md` states — including the `/v1` prefix and the response shapes
the contract review corrected.

**Confidence hypothesis — what shipping this Bolt will prove.** That the app can carry a typed,
swappable engine contract (offline and live) over a storage layer that survives a schema change on a
database that already has rows, while keeping the whole test suite offline and the coverage floor
above 80%. If that holds, the intent's riskiest assumptions are settled.

**Expected demo.** Start the app on loopback, submit text, see the label with its confidence and the
per-label probabilities and which engine answered, find the row in the history, restart against the
pre-existing database to show the migration kept its rows, and show an invalid submission refused
without a stored row.

**Prerequisites.** None outside the repository: the workspace root is the source repository, the
database already exists locally, and the live key remains optional.

**Skeleton note.** No walking-skeleton marker applies. The `classic` scope declares the skeleton flag
off, and the application already runs end to end, so there is no first-unit slice to protect. The
engine consumes the Unit DAG, not this file, so nothing here reorders what gets built.
