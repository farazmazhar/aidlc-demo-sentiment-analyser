# Reverse Engineering Timestamp — `sentiment-opencode`

## Run Record

- **Date**: 2026-10-04 (synthesis completed 2026-10-04T12:22:07Z)
- **Commit**: `4b67c0355912546cb35e6eefd58067fd47e991b5`
- **Commit subject**: `docs: report the unreachable per-Unit completion receipt`
- **Branch**: `main`
- **Intent**: `261004-analytics-view-packaging` (scope `express`, depth Minimal)
- **Space**: `default`
- **Repo**: `sentiment-opencode` (an unrecorded project-root repository — no repo
  suffix on any path)

## What Ran

| Link | Agent | Output |
|---|---|---|
| 1 | `aidlc-developer-agent` | `inception/reverse-engineering/developer-scan.md` — read-only **focused** scan of the stale store's changed area |
| 2 | `aidlc-architect-agent` (this synthesis) | the nine CodeKB artifacts of this candidate, merged from the prior store |

- **Breadth**: **FOCUSED scan of a STALE store.** The prior store (intent
  `analytics-layer`, `kind: full`, `analyzed.paths: [./]`, twelve components) was
  built at `beeb587` and its fingerprint no longer matches the tree. This run
  re-analyzed the focused set deeply, preserved the prior prose, updated it where
  the focused scan reached, and **demoted the prior `./` root claim into
  `shallow.paths`** — that whole-repo deep coverage could not be re-verified.
- **HEAD at synthesis**: `4b67c0355912546cb35e6eefd58067fd47e991b5`, unchanged
  from the scan; the working tree was clean for every focused path.
- **Publish directory** (swapped by this link, not authored by it):
  `aidlc/spaces/default/codekb/sentiment-opencode/`.

## Scan Method

**Read-only for application code; this link wrote only inside the staging
directory, a temporary scope-draft file that was deleted after the coverage
backstop, and the shared store via `codekb-publish`.**

| Activity | How |
|---|---|
| Prior-store preservation | Read all nine existing artifacts and the prior `## Scope of Analysis` block before merging; prior prose was copied into the staging directory and edited only where the focused scan changed a fact |
| Module and API reading | The developer link read `app/routes.py`, `app/analytics.py`, `app/terms.py`, `app/main.py`, `app/models.py`, `app/db.py`, `app/config.py`, `app/service.py` and both static assets in full; it re-verified `app/dummy_client.py`, `app/repository.py`, `app/sentiment.py`, `app/openrouter_client.py`, `app/session_auth.py` and `app/__init__.py` by targeted grep against the prior scan |
| Test verification | `python -m pytest -q` → **192 passed, 0 failed, 0 skipped**, **97.06%** line coverage over `app/` (884 statements, 26 missed) against the 80% floor |
| Lint verification | `python -m ruff check app tests` → *All checks passed!*; `python -m ruff format --check app tests` → *30 files already formatted* |
| Version pinning | `importlib.metadata` probe of the installed environment (CPython 3.14.7); bundled SQLite library 3.53.4 |
| Live store probe | `data/sentiment.db` probed read-only with `sqlite3`: `schema_meta.version = 4`, the three named indexes present, 7 rows |
| Scope mint | `codekb-scope-diff --mint --paths app,tests,pyproject.toml,config.example.toml,README.md` → the `fingerprint` recorded below |
| Coverage backstop | A scope draft was compared with `codekb-scope-diff --compare` **before** publishing; the draft was deleted immediately after |
| Knowledge preflight | The shared and architect knowledge directories produce no readable Markdown in this workspace; the memory tree was injected natively and read for the active-space rules |
| Practices | Read `aidlc/spaces/default/memory/{org,team,project}.md` and `phases/inception.md` — rule files, not application code, listed as shallow below |

The shared CodeKB store was **not** written directly — only `codekb-publish`
swapped it, under its compare-and-swap guards.

## Provenance of Each Artifact

| Artifact | Principal basis |
|---|---|
| `business-overview.md` | Developer scan "Packages Found", "APIs Discovered", "Handoff Summary"; the module docstrings; `README.md`; prior-store prose preserved |
| `architecture.md` | The developer scan's import graph and API list; full reads of `main`, `routes`, `service`, `analytics`, `terms`, `repository`, `db`, `models`, `config`; prior-store prose preserved |
| `code-structure.md` | The developer scan "Packages Found"; working-tree line counts; the prior tree updated with `analytics.py` and `terms.py` |
| `api-documentation.md` | `app/routes.py` in full; `app/analytics.py`, `app/models.py`, `app/service.py`, `app/sentiment.py`, `app/config.py`; `README.md`; `app/static/app.js`; prior-store prose preserved |
| `component-inventory.md` | The scan's module purposes, regrouped into the prior store's twelve logical building blocks plus the two new ones (`Analytics Read Layer`, `Term Extraction`) |
| `technology-stack.md` | `pyproject.toml`; installed distribution metadata probed at runtime; bundled SQLite version; the scan's measured baseline |
| `dependencies.md` | `pyproject.toml`; the internal import graph read from every module's import block; the prior adjacency tables updated for the two new modules |
| `code-quality-assessment.md` | The developer scan "Test Coverage", "Code Quality Indicators", "Technical Debt Signals"; the prior debt register updated (TD-1/TD-3/TD-4/TD-5/TD-6 closed, TD-12…TD-15 added) |
| `reverse-engineering-timestamp.md` | This run record, the developer's Scan Coverage, and the mint command |

## Merge Discipline (focused scan of a stale store)

- **`analyzed.paths` / `analyzed.components` are this run's only.** The prior
  store's `./` claim is **not** unioned in.
- **The prior prose is preserved**, not rebuilt from the focused results; it was
  updated only where the focused scan (or a fact the scan corrected) reached.
- **The prior `./` is demoted** into `shallow.paths` alongside the prior shallow
  entries and the newly skimmed areas.
- **`kind: partial`** is recorded, and `./` is deliberately absent from
  `analyzed.paths`; a `full` claim would be false for a focused re-scan.
- **The twelve prior component names are kept** where they still hold; two new
  names were added for the two new modules. No prior component name was dropped.
- **Two stale rows were corrected** rather than carried forward (see Notes).

## What This Run Verified Beyond the Prior Store

| Finding | Status |
|---|---|
| `/v2/analytics/summary` and `/v2/analytics/terms` exist on a third router, additive to the frozen `/v1` | Verified in `app/routes.py`; prior store said "there is no `/v2` router" |
| `app/analytics.py` is the aggregate read module beside `repository`; `app/terms.py` is the promoted tokeniser leaf | Verified; the prior "no aggregate query exists anywhere" claim is superseded |
| The three analytics indexes exist and survive a v3 → v4 migration | Verified by the scan (`tests/test_migration_indexes.py`); closes TD-1 |
| R-01 (cross-thread SQLite affinity) is fixed with `check_same_thread=False` + the request-scoped invariant, and reproduced by `concurrent_requests` | Verified; closes TD-5 |
| `_WORD` is promoted out of the engine into `app/terms.py` | Verified; closes TD-6 |
| The analytics **view** is a scaffold — terms placeholder, no range control, no partial-failure marker, no superseded-response guard | Verified in `app/static/index.html` and `app/static/app.js`; TD-12 |
| No verification script, secret scanner, dependency audit or allowlist exists | Verified by grep; TD-13 |
| `data/sentiment.db` is at schema v4 with the three indexes and 7 rows | Probed read-only |
| The suite is green at 192 tests / 97.06% and both ruff checks are clean | Re-measured by the scan |

## Notes for the Next Rerun

- The `fingerprint` below is the verbatim output of
  `bun .aidlc/tools/aidlc.ts engine workspace codekb-scope-diff --repo sentiment-opencode --mint --paths app,tests,pyproject.toml,config.example.toml,README.md`
  run from the project root. (The block records `app` and `tests` without a
  trailing slash so the paths match the snapshot/publish `--paths` set.)
- **Component names in the block match the `## ` headings of
  `component-inventory.md` verbatim**; the rerun guard compares them literally.
  There are now **fourteen** headings.
- **This is a `kind: partial` store.** A future scan may either re-union against
  a `CURRENT` store or, if the store is `STALE` again, set `analyzed.paths` from
  its own run and demote the prior analyzed paths into `shallow.paths`.
- **Two prior-store rows were corrected and must not be re-relayed as authority.**
  - The prior `architecture.md` named a non-existent `ensure_page_state` as the
    connection owner; the real owner is `get_connection` (`app/routes.py:114`).
    The row is replaced.
  - The prior `code-structure.md` said `from __future__ import annotations`
    applied to "All 12 modules"; it applies to **13 of the 14** (all but
    `app/__init__.py`).
  - The prior `technology-stack.md` recorded `opentelemetry-api 1.45.1` reached
    "through `anyio`"; installed is **1.45.0**, and `fastapi` requires it
    directly.
- **Behavioural contracts in force at this commit** — preserve or change
  deliberately: `uvicorn app:app` resolves; `/v1` is frozen and its nine-field
  record order, `probabilities`-as-object and ISO-8601-Z `created_at` are pinned;
  `/v2` is additive and read-only; the single `{code, message}` envelope now has
  seven codes (`STORAGE_FAILURE` added on the `/v2` side), with framework routing
  errors keeping FastAPI's `{"detail": …}` shape; `/auth/*` failures answered by
  `302` redirect rather than the envelope; localhost-only and unauthenticated.
- **Test-harness constraints any change must keep intact**: no `httpx`, so the
  hand-rolled `asgi_request` caller is the only way to reach the app; the
  session-wide socket-blocking `offline_guard`; `tmp_path`-scoped settings;
  `filterwarnings = ["error"]`; the 80% floor applied by `addopts`; `ruff`'s `S`
  rules held in full for `app/`.
- **Intent-relevant seams for `analytics-view-packaging`**: the Web UI gap
  (TD-12 — terms section placeholder, no range control, no partial-failure
  marker, no superseded-response guard); the packaging gap (TD-13 — verification
  script, secret scanner, dependency audit, allowlist); the harness instrument
  gap (TD-11 — `app.js` is never executed, so NFR4.6/NFR4.7 must be restated as
  static served-asset assertions plus the manual end-to-end line).

## Scope of Analysis

```yaml
scope_version: 1
kind: partial
intent: analytics-view-packaging
fingerprint: 35fb8af515dd89605a695e792f0a934f7cd460f8
analyzed:
  paths:
    - app
    - tests
    - pyproject.toml
    - config.example.toml
    - README.md
  components:
    - Application Assembly
    - Configuration and Settings
    - Record and Request Contracts
    - Sentiment Engine Interface
    - Offline Dummy Engine
    - Live OpenRouter Engine
    - Session Authorization
    - Analysis Orchestration
    - Analytics Read Layer
    - Term Extraction
    - Persistence and Schema
    - HTTP API Surface
    - Web UI
    - Test Harness and Suite
shallow:
  paths:
    - ./
    - .aidlc/
    - .aidlc/knowledge/
    - .aidlc/tools/
    - .aidlc/skills/
    - .aidlc/hooks/
    - .aidlc/agents/
    - .aidlc/sensors/
    - .aidlc/scopes/
    - .aidlc/onboarding.md
    - .opencode/
    - .opencode/agents/
    - .opencode/command/
    - .opencode/plugin/
    - aidlc/spaces/default/codekb/
    - aidlc/spaces/default/intents/261001-analytics-layer/
    - aidlc/spaces/default/memory/
    - docs/
    - ENGINE-DEFECT-REPORT.md
    - data/sentiment.db
    - AGENTS.md
    - opencode.json
    - .gitignore
    - very_cool_sentiment_analysis.egg-info/
    - .venv/
    - .git/
    - .pytest_cache/
    - .ruff_cache/
    - app/__pycache__/
    - tests/__pycache__/
    - .commandcode/
    - .coverage
```
