# Reliability Requirements — `u1-application`

## Requirements

```yaml
requirements:
  - id: NFR1.1
    category: reliability
    statement: With no key and no network, the app still serves every capability except the live engine.
    rationale: Offline-first is the product's promise; a missing key or an unreachable provider degrades one engine, never the app.
    verification: the suite runs offline with no key and no network; the smoke run starts the app with neither
  - id: NFR1.2
    category: reliability
    statement: The suite fails loudly if anything tries to reach the network.
    rationale: An offline suite that silently reaches the network is worse than one that fails, because it hides a real dependency.
    verification: the test harness blocks outbound use and raises on it
  - id: NFR-R1
    category: reliability
    statement: A refused submission leaves the store untouched.
    rationale: A partial write on a refused request would corrupt the history's meaning.
    verification: asserted per refusal path in the suite
  - id: NFR-R2
    category: reliability
    statement: A schema change keeps existing rows or fails visibly; it never discards data silently.
    rationale: The user's history is the only durable state; losing it silently is the worst failure this tool can have.
    verification: a migration test against a pre-existing store
  - id: NFR-R3
    category: reliability
    statement: A rejected or missing credential degrades the app to the offline engine rather than breaking it.
    rationale: The live path is optional by design; its failure must not be fatal to the session.
    verification: asserted by the suite over the credential lifecycle
```

## Failure posture

The app has one durable artifact — the local store — and one optional external dependency. The
reliability targets are therefore about the two: protect the store across schema changes, and treat
the live engine as an optional capability whose failure is a clear message rather than an outage.
