# Observability Setup Questions — CSV Bulk Import / Export

> Stage: **observability-setup** (Operation, scope `express`, depth Minimal).
> Intent: `csv-bulk-import` (`261001-csv-bulk-import`).
> No `nfr-design` / `infrastructure-design` artifacts exist (express skips them);
> the observable surface below is derived from the approved requirements, the
> workspace configuration, Build and Test results, and the Deployment Execution
> evidence. No missing design artifact was invented.

## Context for the decisions

The app is a **single-process, localhost-only, single-user** service. There is no
hosted environment, no CloudWatch account, no metrics backend, and no on-call
rotation (team `## Deployment`: "a commit is the release", no tiers). The only
existing observability is the app's own stdout logging (module loggers plus one
startup line) and the versioned health endpoint.

## Derived decisions (no open questions)

- **Golden signals.** For a single local user the meaningful signals are
  *errors* and *availability*; latency and saturation are observed only as the
  process's own speed, and traffic is one user. Signals are read from the
  `uvicorn` stdout stream and `GET /v1/health`.
- **SLOs / SLIs.** There is no contractual SLO. The minimum applicable objective
  is documented in `slo-config.md` as a local, best-effort target over the health
  endpoint and the error envelope; it is not measured by a monitoring stack.
- **Dashboards.** No hosted dashboard exists or is warranted; the local
  equivalent (process output + health endpoint) is documented in `dashboards.md`.
- **Log retention / aggregation.** The app writes to stdout only; there is no
  log aggregation or retention policy. Local query recipes are in
  `log-queries.md`.
- **Tracing.** There is no distributed tracing — the app is one process — so
  `tracing-config.md` records why it does not apply.
- **Anomaly detection.** There is no metrics backend to baseline; the local
  proxy is a human noticing repeated error lines (`anomaly-config.md`).
- **Escalation.** One person is user, operator, and decision-maker; there is no
  on-call rotation. No escalation decision is required.

Because every listed item is determined by the project's own configuration and
deployment evidence, there are **no open questions** for this stage.
