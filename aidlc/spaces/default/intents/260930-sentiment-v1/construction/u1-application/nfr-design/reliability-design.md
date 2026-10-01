# Reliability Design — `u1-application`

## Design solutions

| Requirement | Design solution |
|---|---|
| NFR1.1 | The engine resolution defaults to the offline implementation whenever no credential is usable, so a missing key or an unreachable provider removes one capability and leaves the rest of the app working. |
| NFR1.2 | The test harness blocks outbound use and raises on any attempt, so the offline guarantee is enforced rather than assumed. |
| NFR-R1 | Refusal happens before any store work: validation, engine resolution and engine failure all return before the write step, so a refused request cannot leave a partial row. |
| NFR-R2 | The schema change runs at start, before the server accepts a request, and adds a column in place. It never drops or recreates the store; a failure stops startup loudly instead of continuing with a half-migrated file. |
| NFR-R3 | A rejected credential is discarded and resolution falls back to the offline engine for the rest of the session; the failure surfaces as state, not as an exception that ends the request path. |

## Shape of the design

One durable artifact (the store) and one optional external dependency (the live provider). The design
protects the first with an in-place, start-time migration behind a loud failure, and contains the
second behind the resolver so its absence is a state rather than an outage.

## Deliberately absent

Retries on the live call: a retry hides a failing provider behind latency the user did not ask for, and
the human chose no automatic retry. A user-initiated re-submission is the retry.
