# Monitoring Design — `u1-application`

## What is monitored, and how

| Signal | Source | Consumer | Threshold |
|---|---|---|---|
| Active engine and connection state | The health endpoint and the page indicator | A person, or the smoke check | Any state other than "offline" or "live and connected" is worth noticing |
| Startup mode and a missing-key warning | The process's own log output | The person who started it | A warning appears whenever live was requested with no usable key |
| Analysis outcome | The response the page shows | The user | A refusal is visible as text, not silence |
| Suite result and coverage | The checkpoint verification command | The workflow's checkpoint record | Coverage below the floor fails the check |
| Store health | Startup success | The person who started it | A migration failure stops startup loudly |

## There is no telemetry

Nothing is sent anywhere. No metrics service, no log aggregator, no error tracker: every signal above
is visible on the machine that produced it. That is a consequence of the localhost-only constraint
rather than an oversight, and it is the reason the health endpoint and the startup log carry more
weight here than they would in a hosted service.

## The gap this unit cannot close

The affirmed team practice expects the suite and the coverage floor to run in a pipeline. This scope
skips the pipeline stage, so the check runs only when a checkpoint runs it. The gap is recorded in
three places — the NFR requirements, the NFR design, and the CI pipeline artifact beside this file —
so a later workflow can close it without re-deriving it.
