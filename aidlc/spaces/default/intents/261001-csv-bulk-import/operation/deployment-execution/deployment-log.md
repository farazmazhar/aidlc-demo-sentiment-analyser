# Deployment Execution Log — CSV Bulk Import / Export

> Stage: **deployment-execution** (Operation, scope `express`).
> Intent: `csv-bulk-import` (`261001-csv-bulk-import`).
> Target: the project's only real deployment — a localhost checkout run with
> `uvicorn`, bound to loopback. There is no hosted environment, container, or IaC
> (Deployment Pipeline was skipped by design).

## Deployment decision

- **Environment:** local loopback (`127.0.0.1`), the only target the team's
  `## Deployment` practice defines.
- **Database:** a throwaway temporary database (chosen at the pre-deployment
  question), so the real `data/sentiment.db` is left untouched.
- **Artifact:** the working-tree source at HEAD `4eb9b74` (plus the uncommitted
  CSV feature changes), installed editable in place.

## Steps executed

1. **Pre-deployment checks** — all green: Build and Test 118 passed / coverage
   96.02%; no dependent services (offline dummy engine); no deployment window
   (localhost); schema migration is the app's own startup `init_db` (v2 → v3).
2. **Start the real service** — served the actual ASGI app
   (`app.main:create_app`) through real `uvicorn`, host `127.0.0.1`, port `8137`,
   with `load_settings(config_path=<absent>, db_path=<temp>/sentiment.db)` so the
   engine resolved to offline and no real config or key was read.
3. **Smoke tests** — exercised the changed path over HTTP (`/v1/health`, import,
   export, unknown-id export, wrong content type, existing history). Results in
   `smoke-test-results.md`; health in `health-check-report.md`.
4. **Stop the service** — the server process was terminated; the temporary
   database and logs remain under `/tmp/opencode/smoke.<id>/`.

## Startup output (verbatim)

```
INFO:     Started server process [167104]
INFO:     Waiting for application startup.
INFO:     Sentiment analysis app ready in offline mode (OpenRouter not connected)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8137 (Press CTRL+C to quit)
```

## Result

**Deployment succeeded.** The real app resolved `uvicorn app:app`, bound loopback,
created its schema on startup, and served the new bulk import/export endpoints and
the existing endpoints correctly. No rollback was needed.

## Rollback

Per the team's practice, recovery is trivial and local: stop the process and, if
desired, delete the local database file (here, the throwaway temp DB). There is no
deployed artifact to revert; "a commit is the release", and the previous commit is
the rollback target.

## Notes / deviations

- The unversioned `GET /health` returns `404` (framework routing error, FastAPI's
  `{"detail":"Not Found"}` shape); health is served at `GET /v1/health`, which is
  what the smoke test used. This is existing behaviour, not a change from this
  feature.
