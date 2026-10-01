# Anomaly Detection Configuration — CSV Bulk Import / Export

> **Not applicable as an automated feature.** There is no metrics backend with a
> baseline for CloudWatch-style anomaly detection to learn from. This file
> records the local proxy and the trigger for revisiting.

## Why automated anomaly detection does not apply

- Anomaly detection needs a time series of metrics with a stable pattern. This
  app emits no metrics and has one user, so there is no baseline to learn and
  no deviation to detect automatically.
- The two signals that exist (`GET /v1/health`, stdout log lines) are already
  checked directly (`alarms.md`, `log-queries.md`).

## Local proxy for "anomaly"

A human notices an anomaly when a pattern changes:

- the health endpoint stops answering or changes mode unexpectedly;
- error-envelope lines appear where they normally do not;
- bulk import/export stops returning `2xx`.

Any of these is acted on directly, without a detection layer in between.

## Trigger to revisit

Add anomaly detection (and the metrics it needs) only if the app moves to a
hosted deployment with real traffic. At that point, enable it on latency and
error-rate series with a 2-standard-deviation band, combined with static
thresholds for acute failures.
