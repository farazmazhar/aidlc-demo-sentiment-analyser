# Performance Requirements — `u1-application`

## Targets

```yaml
requirements:
  - id: NFR-P1
    category: performance
    statement: A local (offline) analysis returns within a second on the target machine.
    rationale: >
      The offline engine is deterministic keyword logic and the only work besides it is one store
      write; a second is generous headroom rather than a tuned figure, and it makes the page's busy
      state effectively invisible for offline use.
    verification: measured by a smoke run of the verification command
  - id: NFR-P2
    category: performance
    statement: A live analysis is bounded by the outbound call's timeout, and the caller is told it is working while it waits.
    rationale: The live path's duration belongs to the provider, not to this unit; the contract pins a timeout and refuses rather than hanging.
    verification: the page shows its loading state; the outbound timeout is configured
  - id: NFR-P3
    category: performance
    statement: No throughput or concurrency target applies.
    rationale: >
      One local user, one process. The requirements record this explicitly (assumption A4), so a
      throughput figure would be invented rather than required.
    verification: n/a — recorded as a deliberate absence
```

## Notes

The one number that matters is already in the code and the contract: the outbound live call's
timeout. Everything else here is a statement that no target exists, which is itself the requirement —
it stops a later stage from inventing one.

## Traffic shape

Single user, sequential use, no batch path and no scheduled work. The busiest realistic session is a
handful of submissions and a history read.
