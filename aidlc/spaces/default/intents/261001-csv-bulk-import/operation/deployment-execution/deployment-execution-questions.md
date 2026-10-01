# Deployment Execution Questions — CSV Bulk Import / Export

> Stage: **deployment-execution** (Operation, scope `express`, depth Minimal).
> Intent: `csv-bulk-import` (`261001-csv-bulk-import`).
> The Deployment Pipeline stage was skipped (no CD pipeline applies), so its
> `cd-config` / `deployment-strategy` artifacts are absent by design; the real
> run path is the team's affirmed one — `python -m pip install -e ".[dev]"` then
> `uvicorn app:app` bound to `127.0.0.1`.

## Pre-deployment checks (resolved from evidence)

- **Build and tests passing?** Yes — `python -m pytest` → 118 passed, coverage
  96.02% (`construction/build-and-test/test-results.md`).
- **Database migration required and tested?** The added `import_id` column takes
  the schema from v2 to v3; `init_db` migrates in place on startup and the
  migration is covered by `tests/test_db.py`. The live `data/sentiment.db` is at
  v2 with 0 rows.
- **Dependent services available?** None — the offline dummy engine is the
  default; no external service is required for the smoke test.
- **Deployment window?** Not applicable — a localhost checkout; there are no
  environment tiers and no freeze windows.

## Q1. Which database should the live smoke test use?

**Context:** the smoke test starts the real ASGI app through `uvicorn` on
loopback and exercises the changed path (`POST /v1/analyses/import`, `GET
/v1/analyses/export`, `/health`). That run writes rows, so it needs a database.

- **A.** Use the real `data/sentiment.db`. It is migrated v2 → v3 on startup and
  stores the smoke-test rows; this matches the team's affirmed verification
  command exactly (and the prior intent's live run). The file is gitignored, and
  deleting it remains acceptable recovery.
- **B.** Use a throwaway temporary database, leaving `data/sentiment.db`
  untouched. The app is still served by real `uvicorn` on loopback; only the
  database path differs.
- **X.** Other (please specify)

[Answer]: B
