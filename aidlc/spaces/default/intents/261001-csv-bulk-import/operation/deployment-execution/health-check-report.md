# Health Check Report — CSV Bulk Import / Export

> Stage: **deployment-execution**. Real app served by `uvicorn` at
> `http://127.0.0.1:8137`, offline engine, throwaway database.

## Startup

```
INFO:     Started server process [167104]
INFO:     Waiting for application startup.
INFO:     Sentiment analysis app ready in offline mode (OpenRouter not connected)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8137 (Press CTRL+C to quit)
```

The startup line reports the resolved mode (`offline`) and never a credential; the
schema was created/migrated by `init_db` during the lifespan before the server
began accepting requests.

## Health endpoint

`GET /v1/health` → **`200 OK`**

```json
{"mode": "offline", "connected": false, "reason": "Not connected to OpenRouter."}
```

This matches the pre-change contract: the endpoint reports the resolved engine
mode, the connection flag, and a reason only when disconnected.

## Routing note

The unversioned `GET /health` returns `404` with FastAPI's framework shape
(`{"detail":"Not Found"}`). That is expected and pre-existing — the app's health
endpoint is versioned at `/v1/health`, and framework-generated routing errors are
intentionally outside the application error envelope (project rule). It is not a
regression from this change.

## Verdict

**Healthy.** The process started cleanly, the database initialised, the engine
resolved to the offline dummy, loopback binding held, and `/v1/health` answered
`200`. No alarms, no rollback conditions.
