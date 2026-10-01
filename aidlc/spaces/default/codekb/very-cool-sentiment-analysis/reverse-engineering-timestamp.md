# Reverse Engineering Timestamp

## Run Record

- Date: 2026-09-30
- Commit: 5b328fc96766679e98f3fc4effc39198a2811744

## What Ran

| Link | Agent | Output |
|---|---|---|
| 1 | `aidlc-developer-agent` | `inception/reverse-engineering/developer-scan.md` — full read-only code scan |
| 2 | `aidlc-architect-agent` (this synthesis) | the nine CodeKB artifacts of this candidate |

- **Stage**: `reverse-engineering` (inception phase, pipeline mode), intent
  `260930-sentiment-v1`, space `default`.
- **Store decision (conductor, Step 1 guard)**: `NO_STORE` — this is the first
  CodeKB for repo `very-cool-sentiment-analysis`; `aidlc/spaces/default/codekb/`
  is empty, so this run is a **full rescan** and the scope block below is built
  from this run alone.
- **Pre-scan snapshot**: taken over `./` with `store_generation: none`,
  `source_fingerprint: git:dd8a03fbc67106bef2582c91249e996bc0d31fee`.
- **Scan method**: read-only. No file outside the developer handoff and this
  staging directory was written; no build, linter or test suite was executed by
  either link. File-reading of the runtime database (`data/sentiment.db`) was
  done read-only.
- **HEAD at synthesis**: `5b328fc96766679e98f3fc4effc39198a2811744` ("v1-classic:
  FastAPI + SQLite sentiment analysis app with AI-DLC record"), unchanged from
  the scan. The working tree carried only intent-record edits under `aidlc/`
  (the prior intent's audit shard and `intents.json`) and the untracked
  `aidlc/spaces/default/intents/260930-sentiment-v1/` record — no application
  file differed from the scanned revision.

## Provenance of Each Artifact

| Artifact | Principal basis |
|---|---|
| `business-overview.md` | Developer scan "Packages Found", "APIs Discovered", "Handoff Summary"; module docstrings |
| `architecture.md` | Developer scan "Build Dependencies", cross-module call graph; module reads |
| `code-structure.md` | Developer scan "Packages Found"; working-tree line counts |
| `api-documentation.md` | Developer scan "APIs Discovered"; route handler reads |
| `component-inventory.md` | Developer scan "Packages Found" and the module-by-module purpose list, regrouped into logical building blocks |
| `technology-stack.md` | `pyproject.toml`; installed `*.dist-info` metadata in `./.venv` |
| `dependencies.md` | `pyproject.toml`; `very_cool_sentiment_analysis.egg-info/requires.txt`; installed metadata |
| `code-quality-assessment.md` | Developer scan "Test Coverage", "Code Quality Indicators", "Technical Debt Signals" |
| `reverse-engineering-timestamp.md` | This run record, the developer's `### Scan Coverage`, and the mint command |

## Scope of This Run

Deeply covered (the paths listed in the scope block): the whole application
package `app/` including its static page, the whole test suite `tests/`, and the
repository's build, configuration, documentation and ignore files.

Read deeply but **excluded from `analyzed.paths`** — generated or runtime
artifacts that are gitignored, so they are not part of the tracked source
coverage this block fingerprints, and hashing them would make the store report
a false STALE verdict on the next run:

- `very_cool_sentiment_analysis.egg-info/` — generated setuptools metadata
  (`PKG-INFO`, `SOURCES.txt`, `requires.txt`, `top_level.txt`); already stale
  relative to the tracked tree. Its content is reflected in
  `technology-stack.md` and `code-quality-assessment.md`.
- `data/sentiment.db` — local runtime state (12 rows, `schema_meta.version = 1`);
  inspected read-only and described in `technology-stack.md` and
  `component-inventory.md`.
- `.pytest_cache/v/cache/lastfailed` and `.pytest_cache/v/cache/nodeids` — local test-run
  state; the only run evidence available (`lastfailed` held `{}`).

The minted fingerprint below therefore covers the tracked source, manifest,
configuration, documentation and ignore paths of this run.

Only skimmed (at directory granularity, not deep-read): `.venv/` (only installed
distribution metadata was listed to pin versions), `.omp/` (harness skills,
agents and one adapter extension), `aidlc/` (workspace memory, the prior intent
record, this intent's record, the empty `codekb/`, audit and engine state),
`.pytest_cache/` beyond the two cache files, and `.git/`.

The workspace also contains non-application trees that must not be mistaken for
the codebase: `aidlc/`, `.omp/`, `.venv/`, `.pytest_cache/`, `data/` and the
stale `very_cool_sentiment_analysis.egg-info/`.

## Notes for the Next Rerun

- The fingerprint is the output of
  `bun .aidlc/tools/aidlc.ts engine workspace codekb-scope-diff --mint --paths
  app/,tests/,pyproject.toml,config.example.toml,README.md,AGENTS.md,.gitignore`
  run from the project root with `--repo` omitted (unrecorded project-root repo).
- Component names in the block match the headings of `component-inventory.md`
  verbatim.
- Behavioural contracts in force at this commit (preserve them or change them
  deliberately): `uvicorn app:app` resolves; `GET /health` and `GET /auth/status`
  return the same `effective_connection` payload apart from `status`; the error
  envelope and its four codes; `probabilities` as a JSON object keyed by label;
  `created_at` as ISO 8601 UTC ending in `Z`.
- Test-harness constraints any change must keep intact: no `httpx` (hand-rolled
  in-process ASGI caller), the session-wide socket-blocking `offline_guard`,
  `tmp_path`-scoped settings, and `filterwarnings = ["error"]`.
- Known accepted limitation to re-decide if the connection lifecycle is touched:
  per-request `sqlite3` connections rely on default thread affinity
  (`app/routes.py:70-76`, `app/db.py:51-63`), recorded in
  `aidlc/spaces/default/memory/project.md` under Corrections.

## Scope of Analysis

```yaml
scope_version: 1
kind: partial
intent: 260930-sentiment-v1
fingerprint: 2362e39657955a5a6c4781e6bc2c4477a39eb12c
analyzed:
  paths:
    - app/
    - tests/
    - pyproject.toml
    - config.example.toml
    - README.md
    - AGENTS.md
    - .gitignore
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
    - .omp/
    - aidlc/
    - .pytest_cache/
    - .git/
```
