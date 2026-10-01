# Observability Design — `u1-application`

## Design solutions

| Requirement | Design solution |
|---|---|
| NFR6.1 | One connection-state payload (active mode, connected flag, reason) is produced in one place and consumed by both the health endpoint and the page indicator, so the two cannot disagree. |
| NFR6.2 | Startup records the resolved mode, and a requested-but-unusable live mode records a warning naming the config file. The warning is emitted before the server starts accepting requests. |
| NFR6.3 | Log lines are built from the same redacted representations the rest of the app uses, so a credential cannot enter a log through a formatting path. |
| NFR4.1 | The coverage report is produced by the verification command, over the whole application, and compared against the floor at every unit checkpoint. |
| NFR4.2 | The suite's result and the coverage report are the visibility a change gets, since the scope runs no pipeline; the check is the gate. |

## Surfaces

| Surface | Content | Consumer |
|---|---|---|
| Health endpoint | Active mode, connected flag, reason | A script, the page, the smoke check |
| Page indicator | The same state, in words, with the reason reachable by focus | The user |
| Startup log | Active mode; a warning when a requested live mode has no usable key | The user reading the terminal |
| Checkpoint verification | Suite result and coverage report | The checkpoint record |

## Recorded gap

The affirmed practice expects the coverage floor to run in a pipeline; this scope skips the pipeline
stage. The gap is stated here rather than implied away, and it is the one observability item a later
workflow can close without touching this unit's design.
