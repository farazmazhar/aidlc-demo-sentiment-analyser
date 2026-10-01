# Reverse Engineering Timestamp

## Run Record

- Date: 2026-10-01
- Commit: 4eb9b74c4197114181dab641c177c569f2058c24

## What Ran

| Link | Agent | Output |
|---|---|---|
| 1 | `aidlc-developer-agent` | `inception/reverse-engineering/developer-scan.md` — full read-only code scan |
| 2 | `aidlc-architect-agent` (this synthesis) | the nine CodeKB artifacts of this candidate |

- **Stage**: `reverse-engineering` (inception phase, pipeline mode), intent
  `csv-bulk-import` (`261001-csv-bulk-import`), space `default`, scope `express`.
- **Store decision (conductor, Step 1 guard)**: `NO_STORE` — this is the first
  CodeKB for this repo, so no human reuse question was needed.
- **Breadth**: **FULL RESCAN** — this candidate wholesale replaces all nine
  artifacts and the Scope of Analysis block below is built only from this run.
- **Repo set**: an unrecorded project-root repository (single repo at the
  workspace root); no repo suffix on any path. Publish directory:
  `aidlc/spaces/default/codekb/sentiment-opencode/`.
- **HEAD at synthesis**: `4eb9b74c4197114181dab641c177c569f2058c24` ("v1-classic:
  harden sentiment-analysis app to v1 (classic scope)", branch `main`), unchanged
  from the scan.
- **Scan method**: read-only. No file outside the developer handoff and this
  staging directory was written; no build, linter or test suite was executed by
  this link. `data/sentiment.db` was inspected read-only (schema and row count).

## Provenance of Each Artifact

| Artifact | Principal basis |
|---|---|
| `business-overview.md` | Developer scan "Packages Found", "APIs Discovered", "Handoff Summary"; module docstrings; `README.md` |
| `architecture.md` | Developer scan "Build Dependencies" and cross-module call graph; source reads of `service`, `routes`, `db`, `main` |
| `code-structure.md` | Developer scan "Packages Found"; working-tree line counts; import graph |
| `api-documentation.md` | `app/routes.py`, `app/main.py`, `app/models.py`; developer scan "APIs Discovered" |
| `component-inventory.md` | Developer scan "Packages Found" module-by-module purpose list, regrouped into 12 logical building blocks |
| `technology-stack.md` | `pyproject.toml`; installed `.venv` distribution metadata |
| `dependencies.md` | `pyproject.toml`; source imports; installed `.venv` metadata |
| `code-quality-assessment.md` | Developer scan "Test Coverage", "Code Quality Indicators", "Technical Debt Signals"; re-verified test/line counts |
| `reverse-engineering-timestamp.md` | This run record, the developer's Scan Coverage, and the mint command |

## Scope of This Run

Deeply covered (the whole application repository): the entire `app/` package
including its static page and script, the entire `tests/` suite, and the
repository's build, configuration, documentation and ignore files
(`pyproject.toml`, `config.example.toml`, `README.md`, `AGENTS.md`, `.gitignore`,
`opencode.json`).

Read deeply but **excluded from `analyzed.paths`** — runtime or generated
artifacts that are gitignored, so they are not part of the tracked source
coverage this block fingerprints and hashing them would make the store report a
false STALE verdict on the next run:

- `data/sentiment.db` — local runtime state; inspected read-only (schema
  `version = 2`, 0 rows) and described in `technology-stack.md` and
  `component-inventory.md`.
- `app/__pycache__/`, `tests/__pycache__/` — compiled bytecode caches.
- `.ruff_cache/` — self-ignoring linter cache.
- `.venv/` — installed distribution metadata was listed only to pin versions.

Only skimmed (at directory granularity, not deep-read): `.opencode/` (harness
agents/command/plugin, no application code), `.aidlc/` (framework engine,
agents, protocols, skills), `aidlc/` (workspace memory, prior intent record, this
intent's record, audit and engine state), and `.git/`.

The minted fingerprint below therefore covers the tracked src/manifest/config/doc/
ignore paths of this run via the repo root.

## Notes for the Next Rerun

- The fingerprint is the verbatim output of
  `bun .aidlc/tools/aidlc.ts engine workspace codekb-scope-diff --mint --paths ./`
  run from the project root with `--repo` omitted (unrecorded project-root repo).
- Component names in the block match the headings of `component-inventory.md`
  verbatim; the rerun guard compares them literally.
- `kind: full` is claimed because this run deep-scanned the whole application
  repository and `analyzed.paths` includes `./`; a future focused scan of this
  store must read all nine existing artifacts first and preserve prior prose
  outside the newly analyzed area.
- Steering is stale: `aidlc/spaces/default/memory/team.md` describes an earlier
  commit (`0268a5d`/`5b328fc`) and a 52-test suite; the code at `4eb9b74` is
  authoritative (94 tests, coverage floor and `ruff` configured and green). The
  prior CodeKB store (`codekb/very-cool-sentiment-analysis/`) also predates this
  merge and must not be trusted verbatim.
- Behavioural contracts in force at this commit (preserve or change
  deliberately): `uvicorn app:app` resolves; the record field order and
  `probabilities` as a JSON object keyed by label; `created_at` as ISO 8601 UTC
  ending in `Z`; the five machine codes and the single `{code, message}`
  envelope; the framework-error boundary (`{"detail": ...}`).
- Test-harness constraints any change must keep intact: no `httpx` (hand-rolled
  in-process ASGI caller), the session-wide socket-blocking `offline_guard`,
  `tmp_path`-scoped settings, `filterwarnings = ["error"]`, and the 80% coverage
  floor applied by `addopts`.
- Known accepted limitation to re-decide if the connection lifecycle is touched:
  per-request `sqlite3` connections rely on default thread affinity
  (`app/routes.py:79-85`, `app/db.py:130`), recorded in
  `aidlc/spaces/default/memory/project.md` under Corrections.
- Intent-relevant seams for `csv-bulk-import`: engine seam
  (`app/sentiment.py:78-84`, `app/dummy_client.py:71-101`,
  `app/service.py:72-90,116-132`), route seam (`app/routes.py:44,121`), and
  schema seam (`app/db.py:32,36-48,58-68,72-74,87-97,106-111`).

## Scope of Analysis

```yaml
scope_version: 1
kind: full
intent: csv-bulk-import
fingerprint: b212a85db8c21470c36acc527d511d630bd042a3
analyzed:
  paths:
    - ./
  components:
    - Application Assembly
    - Configuration and Settings
    - Record and Request Contracts
    - Sentiment Engine Interface
    - Offline Dummy Engine
    - Live OpenRouter Engine
    - Session Authorization
    - Analysis Orchestration
    - Persistence and Schema
    - HTTP API Surface
    - Web UI
    - Test Harness and Suite
shallow:
  paths:
    - .venv/
    - .opencode/
    - .aidlc/
    - aidlc/
    - data/
    - app/__pycache__/
    - tests/__pycache__/
    - .ruff_cache/
    - .git/
```
