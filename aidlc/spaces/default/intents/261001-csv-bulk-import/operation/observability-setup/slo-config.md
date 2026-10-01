# SLO Configuration — CSV Bulk Import / Export

> A single-user, localhost-only app has no contractual SLO. This file records the
> **minimum** reliability objective the deployment evidence supports, and states
> plainly that it is not measured by a monitoring stack.

## Service Level Indicators (SLIs)

| SLI | Definition | Measurement source |
|-----|------------|--------------------|
| Availability | `GET /v1/health` returns `200` while the process runs | health endpoint |
| Error rate | share of requests answered with the error envelope (`{code,message}`) rather than `2xx` | stdout access/log lines |

Latency, throughput, and correctness SLIs are not defined: there is one user and
one process, and the smoke test (Deployment Execution) already exercises the
correctness path end to end.

## Service Level Objective (SLO)

- **Availability:** the service is considered available whenever its process is
  running and `/v1/health` answers `200`. There is no rolling-window target —
  the app is started on demand by its single user.
- **Error rate:** no target is set. Every error is an application error the user
  can act on locally (invalid input, live-mode failure); there is no population
  of requests to average over.

## Error budget

Not applicable. An error budget exists to trade reliability against feature
velocity across a team and a population of users; neither exists here.

## Measurement

There is no measurement stack. The SLO is checked by hand: the process is up and
`/v1/health` answers. If a hosted deployment is introduced, this file is where
the 30-day rolling-window availability and latency SLOs, plus their error-budget
policy, would be recorded.
