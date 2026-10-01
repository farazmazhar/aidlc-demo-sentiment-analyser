# Tracing Configuration — CSV Bulk Import / Export

> **Not applicable.** This app is a single process; there is no distributed
> request path to trace and no tracing backend (no X-Ray, no OpenTelemetry
> collector). This file records that finding rather than inventing a trace setup.

## Why tracing does not apply

- **One process, one datastore.** `app.routes` → `app.service` → the
  `SentimentClient` adapter → `app.repository` → the local SQLite file all run
  inside the single `uvicorn` process. There is no service boundary to
  instrument and no cross-service latency to attribute.
- **No tracing backend.** The team runs no X-Ray, Jaeger, or OpenTelemetry
  collector; instrumenting one would add a runtime dependency, which the
  project's two-dependency cap forbids (`NFR1`).
- **The request path is already visible.** Each request produces a `uvicorn`
  access line and any application error produces an envelope response; the
  surrounding log lines are enough to localise a problem in one process
  (`log-queries.md`).

## If a hosted, multi-service deployment is introduced

Tracing would then be warranted: propagate a request/trace id across services and
instrument the outbound calls (today only the live OpenRouter engine and the PKCE
exchange leave the machine). That is a future change, not part of this scope.
