# Outcomes Pack

**Scope**: `express` (depth Minimal, test strategy Minimal)
**Stages delivered**: 10 approved / 10 total (in-scope); 33 stages in the compiled graph
**Duration**: ~108 min (workflow started `2026-10-04T12:12:43Z`, completed `2026-10-04T14:00:56Z`)
**Intent**: `261004-analytics-view-packaging` · **Release**: commit `bf49881`, tag `express-2`
**Release document date**: 2026-10-04

> **Count provenance.** The usual source is `bun .aidlc/tools/aidlc.ts engine runtime summary --json`, but no
> `runtime-graph.json` exists for this intent (express compiled none), so the tool reports no data. The counts
> here come from `<record>/aidlc-state.md` (`Total Stages: 10`, `Completed: 10`) and the git history.
> Learnings are `off` for the `express` scope, so no memory entries or learnings were captured by ritual.

---

## 0. Why this scope exists — the framework defect it routed around

This intent exists to finish work the previous intent could not. The `feature`
scope (`261001-analytics-layer`) shipped the `/v2` analytics server, but its
per-Unit `code-generation` walk **wedged** in `u2-term-extraction` on an unreachable
`UNIT_COMPLETED` receipt (`UNIT_COMPLETION_MISSING`), reproduced three times with no
exit using the engine's own verbs.

The loop is closed because the two remedies the engine offers are jointly
unsatisfiable: `request-review` produces a recordable `REVIEW_COMPLETED`, but
`unit start` is refused while a recovery `ask` holds routing — *"the engine currently
routes a ask directive"* — and that ask re-arms on every `next`; the alternative, a
redo-jump, emits `STAGE_JUMPED`, which invalidates every prior review receipt — so
the jump destroys the receipt the Unit needs. Two contributing defects made it
unfixable from inside the review: the dispatched reviewer's `write` is refused by the
plan-approval guard (`CODE_GENERATION_EXECUTION_INELIGIBLE`, because the review file
lives outside the stage record directory), and the permitted shell workaround changes
the source fingerprint, so the verdict is then refused as *"source changed after
REVIEW_REQUESTED"* — producing the review is what invalidates the review. A stale
compiled `bolt_dag` compounded the routing.

`u2-term-extraction` was complete in substance, but the walk will not advance past an
unsettled Unit, so `u3-analytics-view` and `u4-platform-packaging` were **unreachable
in that intent**. The engine's own recommendation was to route around it — start a
fresh intent rather than continue one whose walk is wedged. **This scope is that
fresh intent:** it re-ran the two remaining deliverables under the `express` dial and
closed the two targets (`NFR4.6`, `NFR4.7`) the `feature` scope left `Unverified`.

Full detail, the reproduction table and the recommendations are in
[`../ENGINE-DEFECT-REPORT.md`](../ENGINE-DEFECT-REPORT.md).

---

## 1. What Was Built

This workflow finished the two remaining analytics-layer deliverables for
**sentiment-opencode** (repo `very-cool-sentiment-analysis`), a single-operator,
localhost-only text-sentiment app. The server half of the analytics layer
(`/v2/analytics/summary`, `/v2/analytics/terms`) already existed; this workflow added
the **view wiring** and the **platform packaging**.

**1. The analytics view** (`app/static/index.html`, `app/static/app.js`)

- The static terms placeholder is replaced with two ranked term lists (positive and
  negative, top 10 per list, each term with its count).
- A shared, labelled **date-range control** (default: all history, no bounds; no
  `import_id` control). Changing it refetches **both** `/v2` endpoints on the same
  bounds, so the summary and the terms describe one population.
- **NFR4.6** — a per-section partial-failure marker (`summary-partial`,
  `terms-partial`): a failure in one section never blanks the other.
- **NFR4.7** — no silent retry, and a superseded out-of-order response is discarded
  via an `AbortController` plus a monotonically increasing request token.
- An inline error state derived from the `{code, message}` envelope, plus accessibility
  basics (labelled inputs, live status, assistive-tech-exposed term data).

**2. The platform packaging**

- `Makefile` → **`make verify`**: install → `ruff check` → `ruff format --check` →
  `pytest` (80 % coverage floor) → `detect-secrets` → `pip-audit`.
- `detect-secrets` with `.secrets.baseline` allowlisting the fake-key test fixtures.
- `pip-audit` dependency audit against a **hashed `requirements.lock`**.
- `LICENSE` (MIT), declared in `pyproject.toml` (PEP 639).
- `ruff` **`TID251`** `banned-api` layer-boundary rules.

**Key architectural decisions** (full list in §5): the frozen `/v1` contract is
untouched; runtime dependencies stay at exactly `fastapi` + `uvicorn`; the page gains no
new front-end dependency; the analytics read path keeps its "route → read module" shape.

**Tech stack (measured):** Python 3.14.7 (targets ≥ 3.11), FastAPI 0.142.2, uvicorn
0.54.0, SQLite 3.53.4, pytest 9.1.1, ruff 0.16.9, detect-secrets, pip-audit, uv (lockfile).

---

## 2. Repository Structure

```
.
├── app/                      the application package (14 modules + static assets)
│   ├── static/
│   │   ├── index.html        the page: nav, analyze, history, analytics summary + terms, range control
│   │   └── app.js            page behaviour: two /v2 fetches, term rendering, partial-failure markers, supersede guard
│   ├── analytics.py          aggregate read layer behind both /v2 endpoints
│   ├── terms.py              tokeniser + stopword filter (leaf)
│   ├── routes.py             the HTTP surface (/ , /v1 , /v2 , /auth/*)
│   ├── db.py                 connection, DDL, in-place migration (v4) + indexes
│   ├── main.py               application factory, lifespan, wiring
│   └── …                     service, repository, models, sentiment, config, session_auth, dummy_client, openrouter_client
├── tests/                    pytest suite (conftest + test modules; 198 tests)
├── Makefile                  `make verify` (the release gate) and `make lock`
├── requirements.lock         hashed lockfile
├── .secrets.baseline         detect-secrets allowlist
├── LICENSE                   MIT
├── pyproject.toml            the only manifest: build, deps, pytest, coverage, ruff, TID251
├── README.md                 the contract of record (HTTP surface table, file layout, verification)
├── config.example.toml       committed config template (never a secret)
├── data/sentiment.db         gitignored local runtime state (schema v4)
└── aidlc/                    the AI-DLC workspace record (state, audit, artifacts, codekb, memory)
```

---

## 3. Setup Guide

**Prerequisites:** Python 3.11+ (verified on 3.14.7), `pip`, GNU `make`, `git`.
No cloud account, no container runtime, no database server.

```bash
# install (venv form; the bare system-python form exits 1 under PEP 668)
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

**Environment variables:** none required for build or tests. Live (OpenRouter) mode only:
copy `config.example.toml` to `config.local.toml` and set the key there (gitignored,
never committed). The app runs `offline` on the dummy engine without it.

**Run the tests / gates:**

```bash
make verify          # install -> ruff check -> ruff format --check -> pytest (80% floor) -> secret scan -> audit
```

---

## 4. Build and Deploy

- **Build:** there is no compile/bundle step; the editable install is the build.
- **Test suite:** `make verify` → **198 passed, 0 failed**; **97.06 %** whole-application
  line coverage against the **80 %** floor; `ruff` clean; `detect-secrets` clean;
  `pip-audit` reports no known vulnerabilities.
- **Run:** `uvicorn app:app` (binds `127.0.0.1:8000`; a non-loopback bind is refused by
  `resolve_bind_host`, except via the `uvicorn --host` CLI bypass — see §8).
- **Deploy:** the release procedure is `operation/deployment-pipeline/cd-config.md`
  R1–R8. There is no CD pipeline (no runner, no environment tiers); the release is a
  tagged commit. This release's cutover was verified over real HTTP: `/v1/health`, both
  `/v2` endpoints and `/` answered `200`, the bind was loopback-only, and the operator's
  store was left byte-identical (sha256 **and** mtime). Smoke suite: **14/14 passed**.
- **Infrastructure:** none generated (no IaC; `C-4`/`C-5` forbid a cloud component).

---

## 5. Architecture Decisions

| # | Decision | Why |
|---|---|---|
| 1 | `/v1` frozen; analytics on an additive `/v2` router | versioned data routes; a compatibility boundary, not a flag |
| 2 | Aggregate reads live in `app/analytics.py` beside `repository`, called from the route | the service layer is not inserted into the read path (`Q9`) |
| 3 | Runtime dependencies stay exactly `fastapi` + `uvicorn` | the two-package cap; every new tool is in the `dev` extra |
| 4 | No `pydantic` in `app/` | keeps the validation library out of application code |
| 5 | The view is client-side only; no new front-end dependency | the cap admits no chart library; native HTML + existing classes |
| 6 | NFR4.6/NFR4.7 verified by static served-asset assertions + a manual end-to-end step | no browser execution is admitted under the cap |
| 7 | `make verify` is the single release gate | replaces separate gate commands; a script a human (and any future CI) can call |
| 8 | Hashed lockfile via `uv` | `pip-compile --generate-hashes` did not complete in 580 s; `uv` is an allowed format |
| 9 | `ruff TID251` boundary rules | a boundary breach becomes a lint failure, not a reviewer-only concern |
| 10 | Schema unchanged (`SCHEMA_VERSION = 4`) | this release ships no schema step, so rollback is a pure code checkout |

**Constraints that shaped the design:** `/v1` unchanged; runtime deps exactly two; no
`pydantic` in `app/`; no new external service; all tests offline with the session guard
armed; the pinned analytics contract (4-dp half-up shares with `null` on a zero
denominator; empty range → empty series; zero-fill only internal gaps).

---

## 6. What to Commit vs Archive

| Artifact | Action | Destination |
|---|---|---|
| Application code (`app/`, `tests/`, `Makefile`, `LICENSE`, `requirements.lock`, `.secrets.baseline`, `pyproject.toml`, `README.md`) | **Committed** | this repo (commit `bf49881`, tag `express-2`) |
| `aidlc/` workspace record (state, artifacts, codekb, memory, audit shards) | **Committed** | this repo (per the workspace's git-integration rule) |
| `<record>/audit/*.md` shards | Committed here; for an external app repo, archive to a compliance store | — |
| Stage question files, `aidlc-state.md` | Committed as workflow record | — |
| `data/sentiment.db` and `data/sentiment.db.bak-*` | **Never committed** (gitignored) | local only |
| `config.local.toml` | **Never committed** (holds the key) | local only |
| `.commandcode/` (harness scratch) | **Not committed** (left untracked) | — |

---

## 7. Workflow Footprint

- **Stages:** 10 approved, 0 failed, 0 pending (in-scope); 33 in the compiled graph.
- **Phases:** Initialization 3/3 · Inception 2/2 · Construction 2/2 · Operation 3/3.
- **Memory entries captured:** 0 (learnings `off` for `express`).
- **Learnings captured:** 0 from orchestrator, 0 from user additions (learnings `off`).
- **Reviewers:** none (express `review_cap: none`).
- **Sensors / summary confirmation:** off (scope defaults).

---

## 8. Known Limitations and What to Tackle Next

**Deferred / open items**

1. **Commit and tag** — done in this release (`bf49881`, tag `express-2`). The release
   was committed with the team's `<scope>: <summary> (<scope> scope)` shape and the
   `Produced by the AI-DLC …` trailer.
2. **The git remote drift** — a remote now exists (`origin` → GitHub), contrary to
   `memory/team.md` § Way of Working's "no remote". It carries no CI workflow. The
   deployment-pipeline artifacts were corrected; **the team memory itself still carries
   the stale claim** and should be corrected at the next practices pass.
3. **The analytics summary series width is unbounded** — a 100-year `from`/`to` range
   returns ~7 MB / 36,525 zero-filled entries (~235 ms, over the 200 ms budget) with a
   single stored row. The behaviour is the documented contract; bounding it is a design
   decision for the analytics-surface owner.
4. **A `422` emits no application log line** — only the storage branch logs. Closing it
   is a code change plus a decision about whether a mistyped date is worth a line.
5. **The `uvicorn --host` CLI bypass** — `uvicorn app:app --host 0.0.0.0` bypasses
   `resolve_bind_host`. The documented run path is enforced; the CLI form is not.
6. **Log retention** — none by decision; a session's log exists only if redirected.
7. **No automated instrument for NFR4.6/NFR4.7** — pinned statically and exercised
   manually; no browser execution under the cap.
8. **Accepted limitation R-01** — SQLite per-request connection thread affinity; no
   concurrency target is in scope.

**Recommended next steps**

- Fix the team-memory "no remote" claim and decide whether to push tags/branches to
  `origin` as the release channel.
- If the view's client behaviour needs real coverage, decide whether to admit a
  dev-only JS test runner (still no runtime dependency) or accept the manual evidence.
- Consider a follow-up scope for the deferred prior-FR7 items (startup loopback
  enforcement on the CLI path, the ASGI test-harness replacement).
- Keep the expand-only schema discipline: a destructive schema change must not ship in
  the same release as the code that stops using the column.
