# Dashboards — CSV Bulk Import / Export

> Minimal observable surface for a single-process, localhost-only app. No
> CloudWatch (or other hosted) dashboard exists or is warranted.

## The local "dashboard"

There is no metrics backend to render a dashboard from. The operational view of
the running service is two local sources:

1. **The process's stdout stream** — `uvicorn` access lines and the app's own
   log lines (including the single startup line naming the active mode). This is
   the real-time view of traffic and errors.
2. **`GET /v1/health`** — the resolved engine mode, the `connected` flag, and a
   reason when disconnected. This is the one always-on, machine-readable signal.

## What to look at, in order

| Signal | Source | How to read it |
|--------|--------|----------------|
| Availability | `GET /v1/health` | `200` with `mode` means the process is serving |
| Errors | stdout | Non-2xx access lines, and `{code,message}` envelope responses |
| Traffic | stdout | Access lines for `/v1/analyses/import` and `/v1/analyses/export` |
| Latency / saturation | stdout timing | Only meaningful locally; one user, one process |

## Why no hosted dashboard

The team's deployment practice defines a localhost checkout with no environment
tiers; there is no CloudWatch namespace, no metrics pipeline, and no second user
to serve. Adding a hosted dashboard would invent an environment that does not
exist. If a hosted deployment is ever introduced, this file is the placeholder
for the golden-signals dashboard that would replace the local view.
