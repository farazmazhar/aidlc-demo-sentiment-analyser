# Alarms — CSV Bulk Import / Export

> This is a single-process, localhost-only app with no monitoring service, so
> there are **no automated alarms**. This file documents the two conditions a
> human should watch and why they are not automated.

## Conditions worth watching

| # | Condition | Symptom | Action |
|---|-----------|---------|--------|
| A1 | Service not answering | `GET /v1/health` does not return `200`, or the process is not listed | Restart the process (`uvicorn app:app`); check the stdout stream for the startup line |
| A2 | Repeated error responses | More than a few `{code,message}` error lines, especially `SENTIMENT_ENGINE_ERROR` (502) or `AUTH_EXPIRED` (502) in live mode | Read the surrounding lines; for live mode, reconnect the key from the page or fall back to the offline engine |

## Why no automated alarms

The team's deployment practice has no environment tiers, no hosted monitoring,
and no on-call rotation — there is no notification target and no metrics backend
for an alarm to evaluate. An alarm with nowhere to fire would be noise, not
safety. The local check (`GET /v1/health`) is the minimum viable signal, and it
is already present.

## Thresholds if a hosted deployment is ever added

For a future hosted deployment, alarm on **symptoms**, not causes: error rate
(`5xx / total`) over a 5-minute window, and availability of the health endpoint.
Do not alarm on CPU or memory directly. The application already emits one error
envelope with machine codes, so an error-rate alarm can key off those codes.
