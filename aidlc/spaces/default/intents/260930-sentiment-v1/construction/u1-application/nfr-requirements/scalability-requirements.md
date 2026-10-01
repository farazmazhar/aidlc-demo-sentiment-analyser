# Scalability Requirements — `u1-application`

## Requirements

```yaml
requirements:
  - id: NFR-SC1
    category: scalability
    statement: No horizontal or concurrent-user scaling target applies.
    rationale: >
      Single local user, one process, one local store. The requirements record no concurrency target
      (assumption A4), and the previously accepted limitation around concurrent database access is
      not a v1 target.
    verification: n/a — recorded as a deliberate absence
  - id: NFR-SC2
    category: scalability
    statement: History grows without a retention limit and must stay readable as it does.
    rationale: The human chose no retention or deletion path for v1, so the history read is the one path that degrades if it is unindexed or unbounded.
    verification: the history read is bounded by a limit parameter at the boundary
  - id: NFR-SC3
    category: scalability
    statement: The store remains a single local file; no service, cache or queue is introduced to scale it.
    rationale: The dependency cap and the local-only constraint; a second process would also break the "one command to run" promise.
    verification: reviewed at the unit checkpoint
```

## What would change if the tool had to grow

Recorded for orientation, not as a requirement: a shared deployment would need the API's
authentication restored, a retention policy, and a real concurrency story for the store. None of that
is v1, and naming it here keeps a later reader from assuming the current shape was a failure to plan.
