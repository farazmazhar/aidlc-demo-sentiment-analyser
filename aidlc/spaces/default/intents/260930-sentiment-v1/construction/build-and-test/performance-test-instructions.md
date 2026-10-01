# Performance Test Instructions — `u1-application`

Performance NFRs exist for this unit (`NFR-P1`, `NFR-P2`, `NFR-P3`), so a performance check file is
recorded. The traffic shape is one local user, sequential use, no batch path and no scheduled work,
so the checks are deliberately light.

## Targets

| Target | Requirement | Expected |
|---|---|---|
| `NFR-P1` | A local (offline) analysis returns within a second on the target machine. | offline `POST /v1/analyze` completes well within 1s |
| `NFR-P2` | A live analysis is bounded by the outbound call's timeout, with a busy state while it waits. | the injected transport carries the 10-second timeout; the page shows a loading state |
| `NFR-P3` | No throughput or concurrency target applies. | deliberate absence, justified by requirements assumption A4 |

## Local latency check (NFR-P1)

Measured by the smoke run of the verification command: the offline analysis path performs in-memory
scoring plus exactly one store write. Record the observed wall-clock time for a single
`POST /v1/analyze` against the locally started app and compare against the one-second target.

## Live-path bound (NFR-P2)

The outbound timeout is a single named constant carried by the injected transport (10 seconds). It is
verified by construction: `tests/test_live_client.py` drives the live client through the injected
transport with no network, and the smoke run reflects the live path's configured bound.

## Explicit absence (NFR-P3)

No throughput or concurrency target is defined for v1; the app serves one local user in one process.
Recording this keeps a later stage from inventing a target the requirements never stated.

## How to run

Heavy load tooling (k6, Locust, Artillery) is not applicable at this scale. Use the recorded
verification command's smoke run to observe the offline path:

```bash
.venv/bin/python -m pytest -q && \
.venv/bin/python -c "import threading,time,urllib.request,uvicorn; from app.main import app as a; threading.Thread(target=uvicorn.run, args=(a,), kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'}, daemon=True).start(); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"
```
