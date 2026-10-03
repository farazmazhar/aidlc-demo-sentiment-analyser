# Outcomes Pack

**Project**: `very-cool-sentiment-analysis` — analytics layer (`261001-analytics-layer`)
**Scope**: `feature`
**Stages delivered**: 26 approved / 30 total (0 failed, 4 pending)
**Duration**: 2 915 min (48.6 h wall-clock across sessions)
**Release**: annotated tag `feature` → `f3b5185`

---

## 1. What Was Built

A **read-only analytics slice** on top of an existing FastAPI + SQLite sentiment app: two
new `/v2` endpoints, a second page section rendering them, and the plumbing beneath.

### Delivered endpoints

| Endpoint | Behaviour |
|---|---|
| `GET /v2/analytics/summary` | Totals, per-label counts, shares, mean confidence with its row count, and a bounded per-day series |
| `GET /v2/analytics/terms` | Top terms per label, default `limit` 10, alphabetical tie-break |

Both take `from`, `to`, and `import_id`. Dates are inclusive UTC calendar days; a single
bound is never dropped; an unbounded span runs from the earliest stored analysis to today.
An empty range returns an **empty series** — zero-fill happens only for internal gaps of a
range that matched at least one row.

### Delivered alongside

- The additive, idempotent SQLite migration `v3 → v4` with three named indexes
  (`idx_analyses_created_at`, `idx_analyses_import_id`, `idx_analyses_label_created_at`)
- The connection model that closes risk **R-01** (same-thread checking off, request-scoped)
- Enforced loopback bind — a non-loopback host now fails loudly at startup
- A second page section: series as native SVG polyline, label breakdown with shares, and
  distinct empty/error regions, all rendered through `textContent`
- `app/terms.py` — the tokeniser, **a disclosed unit-boundary violation** (§5)

### Measured result

| | |
|---|---|
| Tests | **192 passed** (baseline 118), 0 failed, 0 warnings |
| Coverage | **97.06 %** line, against an affirmed 80 % floor enforced twice |
| Lint | `ruff check` and `ruff format --check` both clean |
| Runtime dependencies | exactly **two** — `fastapi`, `uvicorn` |
| `/v1` | untouched |

`app/analytics.py` and `app/terms.py` are at 100 % line coverage. All 26 missed lines are
pre-existing (`session_auth.py`, `openrouter_client.py`).

### Tech stack

- Python `>=3.11` (developed and validated on 3.14.7), FastAPI `>=0.110`, uvicorn `>=0.27`
- SQLite via stdlib `sqlite3`; stdlib `dataclasses` in `app/` (no pydantic)
- `pytest` + `pytest-cov` + `ruff` in the `dev` extra

---

## 2. Repository Structure

```
app/
  analytics.py     374 lines  AnalyticsRead — range resolution, aggregates, series, ranking
  terms.py         11 stmts   tokenize() + significant_terms(); the promoted tokeniser
  routes.py                 the /v2 router and its two handlers; /v1 unchanged
  db.py                    SCHEMA_VERSION 4, ANALYSES_INDEXES, transactional rebuild
  main.py                  resolve_bind_host / NonLoopbackBindError, run()
  models.py                four stdlib dataclasses
  dummy_client.py          offline engine, delegating to app.terms.tokenize
  static/                  index.html + app.js — header, nav, summary region
tests/
  conftest.py              offline_guard (autouse), concurrent_requests, asgi_request
  test_analytics_read.py   lower-level unit tests + the latency budget test
  test_analytics_routes.py acceptance/API tests, written before the implementation
  test_migration_indexes.py additive migration, indexes by name, loud rollback
  test_terms.py            tokeniser parity
aidlc/spaces/default/intents/261001-analytics-layer/
  232 artefacts across 5 phases, plus the audit shard
```

---

## 3. Setup Guide

**Prerequisites**: Python ≥ 3.11; `bun` for the workflow tooling. No cloud CLI, no
container runtime, no IaC tool — none is used by this project.

```bash
# 1. Install. On an externally-managed interpreter (PEP 668) use a venv:
python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"

# 2. Run the app on loopback
.venv/bin/python -m uvicorn app:app --port 8000

# 3. Tests
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check app tests && .venv/bin/python -m ruff format --check app tests
```

**Environment variables**: none required. `config.local.toml` is optional; the app
defaults to `mode = "offline"` with no API key. `mode = "openrouter"` is the only setting
that would send input text to a third party.

**Two host-specific gotchas**, both measured:

- On hosts that export `APPIMAGE`, CPython reports the AppImage as `sys.executable` and a
  subprocess spawn fails with exit 130. Prefix commands with `env -u APPIMAGE`.
- `python -m pip install -e ".[dev]"` exits 1 under PEP 668. Use the venv form above.

---

## 4. Build and Deploy

There is no build step — pure Python, no compile, no bundle. The release **is** the commit.

```bash
python -m compileall -q app tests                    # exit 0
python -m pytest -q                                  # 192 passed, 97.06%
python -m ruff check app tests && python -m ruff format --check app tests
```

**Deployment**: a loopback `uvicorn` process over one gitignored SQLite file. No
environment tiers, no container, no hosted service, no IaC. Per `team.md` § `Deployment`,
a squashed commit tagged with the scope name is the release; the version stays `0.1.0`; no
package or image is ever published.

**Verified end to end**: 27 smoke checks over a real `uvicorn` subprocess against real
HTTP — `/v1/health`, both `/v2` endpoints with and without parameters, every refusal path,
and the served page. Every status corroborated by the server's own access log.

---

## 5. Architecture Decisions

| Decision | Alternatives rejected | Why |
|---|---|---|
| Shares as a 4-dp half-up fraction, `null` on a zero denominator | rounding half-even; a percentage | half-up ruled at the Functional Design gate; `null` beats `0` for "no denominator" |
| Empty range → **empty series**; zero-fill only internal gaps of a matched range | zero-fill the whole requested range | zero-filling an unmatched range reports data that does not exist |
| Exactly one `SELECT` per analytics read | per-day queries | the statement count must not grow with the range width — verified at 7 / 365 / 3 650 / 36 500 days |
| Unbounded bound carried as two bound parameters with sentinels | a separate code path | proven collision-proof against adversarial stored `created_at` values |
| Error envelope exactly `{code, message}` | a `field` member | the message text names the offending parameter instead |
| Additive migration only, one transaction, loud rollback | destructive migration | additive-only is pinned by the pinned contract; rollback is atomic, verified |
| Indexes re-created as statements after the rebuild | declaring them on `CREATE TABLE` | SQLite's `CREATE TABLE` cannot declare an index, and the rebuild destroys them |
| recreate for the process, expand-only for the schema | blue/green, canary, rolling | blue/green would need a second copy of the one file that cannot be recreated for free |
| No monitoring tier, no alerting channel | adding one | capped by constraints C-5/C-6 and by a single-user local app |

### The one decision that went wrong

**`app/terms.py` was authored by `u1-analytics-slice`, and it does not belong there.**
Three inception artifacts forbid it — `tech-stack-decisions.md:49` ("this unit consumes it,
does not re-implement it"), `unit-of-work.md:96` and `:132`, and `contract-summary.md` § 4 —
and `unit-of-work.md:62` records the Delivery Planning obligation that "U1's terms work must
not be sequenced ahead of U2".

The fault traces to the **approved plan** (step 5) and to **Delivery Planning's ordering**:
`unit-of-work-dependency.md:141-148` places all three roots in batch 1 without saying which
to work first. The engine cannot express the correct order, because `next` substitutes the
first *unsettled* Unit and pausing a Unit hard-stops the whole loop.

Three adversarial review passes found it. My first fix — sequencing U2 *after* U1 — was
withdrawn as wrong, because that is precisely what the rule forbids. It is disclosed in the
plan (marked `⚠ PLAN ERROR`), the code summary, and the stage diary rather than absorbed.
`u2-term-extraction` adopts the module as Bolt 2.

---

## 6. What to Commit vs Archive

| Artifact | Action | Destination |
|---|---|---|
| Application code and tests | Already committed (`aa0b1e4`) | repository root |
| Stage artefacts under `<record>/` | Commit | `aidlc/` — they are the record |
| `<record>/audit/*.md` shard | Commit | `aidlc/` — the append-only ledger |
| Learned practice (`memory/*.md`) | Commit | `aidlc/spaces/default/memory/` |
| Stage questions files | Keep | low value; harmless |
| `runtime-graph.json` | Discard | machine-local, gitignored, recompiled |
| `reviewed-source-*.tsv`, review files | Discard | machine-local |
| `.commandcode/` | Leave untracked | unrelated tool output, not part of this project |

---

## 7. Workflow Footprint

| Metric | Value |
|---|---|
| Stages | **26 approved**, 0 failed, 4 pending |
| Per phase | Initialization 3/3 · Ideation 5/7 · Inception 9/9 · Construction 2/4 · Operation 7/7 |
| Memory entries | **214** — 67 interpretations, 40 deviations, 56 trade-offs, 51 open questions |
| Learnings captured | **110** from orchestrator, 0 from user additions |
| Sensor fires | **415** — 370 passed, 45 failed |
| Commits | 8 for this scope; tag `feature` → `f3b5185` |

**Three of four Units were never built.** `u2-term-extraction`, `u3-analytics-view` and
`u4-platform-packaging` do not exist. The Construction → Operation boundary verdict is
**FAIL** with eleven findings, each carrying a named owning stage.

**Two NFR targets ship `Unverified`** — `NFR4.6` (per-section graceful degradation) and
`NFR4.7` (no silent retry, out-of-order discard). Both need markup `u3-analytics-view`
owns, and no validation stage owns them either, so they cannot be deferred.

The `Construction 2/4` figure understates what ran: five per-unit stages genuinely executed
for `u1-analytics-slice` but their stage checkboxes read `[S]` (skipped via jump), because
under unit-major iteration each stage waits for every unit before it flips, and the
code-generation jump reset them. The per-unit receipts are the accurate record.

---

## 8. Known Limitations and What to Tackle Next

### Delivered but unverified

| Id | Target | Why | Owner |
|---|---|---|---|
| `NFR4.6` | per-section graceful degradation | needs a second analytics section | `u3-analytics-view` |
| `NFR4.7` | discard superseded range, no silent retry | needs the date-range control | `u3-analytics-view` |

### Defects found after shipping, none fixed

| Finding | Measured | Severity |
|---|---|---|
| **Writer lockout** | one competing writer → 6/6 reads `500 STORAGE_FAILURE` at p50 **5 007.9 ms**. `app/db.py:213` sets no `busy_timeout`, so CPython's 5.0 s default applies | **high** — a total read outage from one stray write |
| **Export is a view, not a backup** | `import_id` is required (422 without), `IS NULL` rows excluded, `EXPORT_COLUMNS` omits `probabilities` and `intensity`. On a 3-row store it returned **1 of 3 rows**, and 404 where `summary` reported `total: 2` | **high** — single-analysis rows are structurally unreachable, and that is normal use |
| **No backup mechanism** | 0 commits contain `data/`; one manual copy created by luck during a release | **high** for the operator's data |
| **Superlinear concurrency cost** | the same 240 requests cost 2.8 CPU-s at c=1 and **14.9 CPU-s at c=32**. Throughput peaks at c=2 (157.8 rps) and falls to **41.2 at c=64**. Mixed load at c=8: p95 **952.7 ms**, 4.8× budget | medium — bounded *work* holds, bounded *cost* does not |
| **Uncapped payload** | a 100-year range returns **7 011 966 B / 36 500 entries**; p99 199.700 ms, 0.3 ms *inside* budget | medium |
| **`uvicorn --host` bypasses the bind** | the CLI bound and served 200 where `resolve_bind_host` refuses `127.0.0.2`; no refusal logged | medium — enforcement is a property of the run path, not the process |
| **422 emits no application record** | measured 4 × 422, 0 records | medium — an operator watching app logs sees nothing |
| **Failed startup emits no `app.*` record** | surfaces only through `uvicorn.error`; measured 0 app records, exit 3 | medium |
| **`/v1/health` cannot see a storage failure** | answered 200 in 1.4 ms while every analytics read was 500 | medium |
| **No stack trace on failures** | ships `logger.error`, not `logger.exception`, though two design artefacts claim "code and stack" | low |
| **Store file mode 644** | where the check expects 600 | low |
| **Access log has no duration field** | every latency figure in this project is stopwatch-measured | low |

### Ranked backlog — from `feedback-loop.md`

| | Item | Owner |
|---|---|---|
| **BL-01** | Finish the three unbuilt Units; clears the most findings | the Units + a **Delivery Planning re-run** to fix the Bolt order |
| **BL-02** | Create a backup mechanism | the human, plus `u4` |
| **BL-03** | Set a `busy_timeout` — XS-sized, ranks third by consequence | `u1` |
| **BL-04** | Decide what the export surface is *for* | Requirements Analysis + `u1` |
| **BL-05** | Close the `uvicorn --host` bypass | `u1` + a scope decision |

### Open questions a cycle should pick up

- How often should the store be copied — release-time only, per-boot, or per-incident?
  A per-boot `cp` was considered and **not** proposed: the migration hazard is conditional,
  and a habitual copy would erode release discipline.
- What is the export surface for, given it cannot reach single-analysis rows?
- Does the recorded schema version's measured ability to move *backwards* deserve a guard?
- `health-check-report.md` §2.3 names `python -m app.main` as a documented run path. It was
  measured not to serve (`RuntimeWarning`, exit 0, no listener). Parked as **OQ-IR-5** rather
  than corrected in place, since editing another stage's artefact is not that stage's remit.
- The recorded verification command's step 3 migrates the operator's real store whenever it
  is behind `SCHEMA_VERSION`. A measured `os.chdir` isolation exists; changing the approved
  command needs the human.

### No CI runs automatically

There is **no git remote**. The nine-job pipeline and its 14 gates are fully specified with
exact commands, but nothing is attached to. `feature`'s "CI execution before merge" is
therefore unsatisfiable as things stand. Two gates (`G9` static security, `G10` DAST) have
instruments that exist only as heredocs inside `security-test-instructions.md` — they were
run by Build and Test and proved to have teeth, but they are not committed; `u4` owns
landing them.