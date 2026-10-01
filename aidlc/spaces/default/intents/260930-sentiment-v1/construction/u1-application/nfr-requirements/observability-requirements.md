# Observability Requirements — `u1-application`

## Requirements

```yaml
requirements:
  - id: NFR6.1
    category: observability
    statement: The health endpoint reports the active engine and whether the live engine is connected.
    rationale: Which engine answered is the persona's central question; the health surface is where a script or a person asks it.
    verification: asserted over the health response
  - id: NFR6.2
    category: observability
    statement: Startup records the active mode, and a missing key is recorded as a warning naming the config file.
    rationale: A quiet fallback to the offline engine is the failure mode that makes a user distrust the tool.
    verification: asserted over captured logs
  - id: NFR6.3
    category: observability
    statement: No log record contains credential material.
    rationale: Logs are the most likely place for a secret to escape a local tool.
    verification: asserted over captured logs
  - id: NFR4.1
    category: observability
    statement: The quality gate reports line coverage for the whole application against the affirmed floor.
    rationale: The floor is the only mechanical statement about how much of the system is proven; without a report it is a wish.
    verification: the coverage tool's report in the verification command
  - id: NFR4.2
    category: observability
    statement: The suite's result is the visibility a change gets before it ships, since there is no pipeline.
    rationale: The affirmed posture names a CI job, but this scope skips the pipeline stage; recording the gap keeps it visible rather than assumed.
    verification: the verification command is run at every unit checkpoint
```

## What a user can observe

| Question | Where it is answered |
|---|---|
| Which engine is active? | The page's indicator, the health endpoint, the startup log |
| Is the live model connected? | The health payload's connection state and its reason |
| Did the app fall back? | The startup warning, and the connection state after a rejected credential |
| How much of the system is proven? | The coverage report from the check |

## Recorded gap

The affirmed team practice expects the coverage floor to run in a CI job. This scope skips the CI
pipeline stage, so today the floor runs only when the verification command runs. That gap is recorded
here and in the phase's open questions rather than being silently accepted.
