# Log Queries — CSV Bulk Import / Export

> Local equivalents of Logs-Insights-style queries, run against the app's stdout
> stream (there is no CloudWatch Logs). Point the running server's output at a
> file (`uvicorn app:app > app.log 2>&1`) and use these recipes.

## Recipes

**Startup line (confirms the resolved mode, never the key):**

```bash
grep -F "Sentiment analysis app ready" app.log
```

**All bulk-import requests and their status:**

```bash
grep -E "POST /v1/analyses/import" app.log
```

**All export requests:**

```bash
grep -E "GET /v1/analyses/export" app.log
```

**Only failed requests (non-2xx access lines):**

```bash
grep -E "HTTP/1.1\" [45][0-9][0-9]" app.log
```

**Application error-envelope responses (the machine codes):**

```bash
grep -oE '"code":"[A-Z_]+"' app.log | sort | uniq -c
```

**Count requests by path:**

```bash
grep -oE '"(GET|POST) [^ ]+' app.log | sort | uniq -c
```

**Live-mode engine failures specifically:**

```bash
grep -F "SENTIMENT_ENGINE_ERROR" app.log
grep -F "AUTH_EXPIRED" app.log
```

## Notes

- The app emits one structured startup line and uses module loggers; `uvicorn`
  emits the per-request access lines. There is no JSON log format configured and
  no log aggregation, so these `grep` recipes are the whole query surface.
- The credential is never written to the log stream (existing guarantee,
  `NFR4`), so these recipes are safe to run and share.
