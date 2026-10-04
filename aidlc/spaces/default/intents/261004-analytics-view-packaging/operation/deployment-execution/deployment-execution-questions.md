# Deployment Execution Questions — intent `261004-analytics-view-packaging`

> **Stage:** `deployment-execution` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> support `aidlc-developer-agent` · **Release under test:** the working tree at HEAD
> `4b67c03` · **Record:**
> `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/deployment-execution`
>
> **Upstream inputs:** `operation/deployment-pipeline/{cd-config,deployment-strategy,rollback-runbook}.md`
> · `construction/build-and-test/{build-instructions,build-and-test-summary,test-results}.md`
> · `memory/team.md` · `memory/project.md`.

## How this file is written

The stage's Step 2 asks four questions. Each is answered from evidence — an affirmed
practice, a recorded artifact, or a measurement this stage made — with its source named.
The genuinely open items are recorded at the end and are the human's.

---

## 1. The four Step-2 questions

### Q1 — Are all pre-deployment checks passing? → **Answered from evidence: yes**

**Source:** this stage's execution of `cd-config.md` R1–R7 (`deployment-log.md` §2) plus
`construction/build-and-test/test-results.md`.

| Check | Result |
|---|---|
| Install (venv form) | `.venv` present; `very-cool-sentiment-analysis-0.1.0` installed editable |
| Gate set — `make verify` | **Green**: 198 passed, 97.06 % coverage, `ruff` clean, `detect-secrets` clean, `pip-audit` no known vulnerabilities |
| Store backup (R4) | `data/sentiment.db.bak-4b67c03`, sha256 byte-identical |
| Throwaway-store smoke (R5) | `{"mode":"offline",…}`; throwaway store created; real store untouched |
| Cutover (R6) | `/v1/health` 200, `/v2/analytics/summary` 200, `/v2/analytics/terms` 200 on `127.0.0.1:8000`; socket loopback-only; real store sha256 **and** mtime unchanged |

**One recorded divergence.** The bare `python -m pip install -e ".[dev]"` exits 1 under
PEP 668 on this host; the venv form exits 0. Already carried by `cd-config.md` R2. With
`requirements.lock` now committed, a reinstall can be pinned.

### Q2 — Are database migrations required and tested? → **Answered from evidence: not required; no schema step ships this release**

**Source:** `app/db.py:60` (`SCHEMA_VERSION = 4`), `deployment-strategy.md` §3, and this
stage's live measurement.

**Not required.** This release changes static page assets and repository-level tooling
only; it adds no column, table or index. `init_db` runs its idempotent no-op at v4. The
operator's store was sampled read-only before and after the cutover: `schema_meta.version
= 4`, all three named indexes present, and **sha256 and mtime both unchanged** — the file
was not opened for writing.

**Tested?** The `v3 → v4` step was proven correct and idempotent by the prior intent's
`deployment-execution` (a real `3 → 4` transition on a seeded isolated copy, rows and
content digest preserved). This stage inherits that measurement and adds the write-neutral
observation above; it does not re-run the `3 → 4` experiment because no schema code
changed.

### Q3 — Are dependent services available and healthy? → **Answered from evidence: there are none; the one external dependency is not connected but the app is healthy without it**

**Source:** this stage's live `/v1/health`; `deployment-strategy.md` §5.

No AWS CLI, no IaC file, no container runtime, no database server. The only external
dependency is OpenRouter, and it is **not connected**:
`{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}`. The app
served its complete read surface — health, both `/v2` endpoints, the page — on the dummy
engine with no credential and no egress. The dependency that matters for a release, the
store, is healthy: present, readable, at v4, three indexes, and now backed up.

### Q4 — What is the deployment window? → **Answered from evidence: there is none, and none is invented**

**Source:** `memory/team.md` § Way of Working; `deployment-strategy.md` §6.

No maximum branch age or freeze window has been affirmed. The recreate cutover's outage
is the interval between two hand-typed commands on a one-user machine with no traffic.

---

## 2. Questions this stage raised while executing

### Q5 — Should the release be committed and tagged? → **GENUINELY OPEN — a human decision**

`memory/team.md` § Way of Working makes the tag the release, and the scope's squash
commit the release artifact. **This stage did not commit or tag anything.**

Two facts the human needs:

1. **The application change is still uncommitted.** `git status --short` shows `README.md`,
   `app/static/app.js`, `app/static/index.html`, `pyproject.toml`, `tests/test_page.py`
   modified and `Makefile`, `LICENSE`, `requirements.lock`, `.secrets.baseline` untracked.
   HEAD is `4b67c03` (`docs: report the unreachable per-Unit completion receipt`), which
   does **not** contain this change. A release tag on `4b67c03` would tag a commit without
   the work; the change must be committed first.
2. **A remote now exists** (`origin` → `https://github.com/farazmazhar/aidlc-demo-sentiment-analyser.git`),
   contrary to `memory/team.md` § Way of Working's "no remote". It carries **no CI
   workflow**, so it changes where the tag can be pushed, not whether a pipeline runs. The
   deployment-pipeline artifacts were corrected for this.

What the human will run, once the change is committed: `git tag -a <scope-name> -m
"<scope-name> scope release" <release-sha>` (and optionally `git push origin <tag>`).

### Q6 — The analytics summary's series width is unbounded → **OPEN, inherited; belongs to the analytics surface's owner**

The prior intent's `deployment-execution` measured that a wide `from`/`to` range returns
one zero-filled series entry per calendar day (a 100-year range → 7 MB). This release does
**not** change the series contract, so the observation stands unchanged; it is inherited,
not re-measured. Whether a maximum range width belongs in the `/v2` request contract is a
design decision, not a deployment one.

### Q7 — Questions this stage did not need to ask

Recorded so their absence is not read as an oversight: environment tier (there is one),
artifact registry (nothing is published), canary threshold (no traffic), feature flag
(none, and the release has no schema step to gate), production approver (no second human),
rollback plan (already written and rehearsed), release backup (R4 ran).

---

## 3. Disposition summary

| # | Question | Disposition |
|---|---|---|
| Q1 | Pre-deployment checks passing? | Answered from evidence — yes (`make verify` green; R4–R6 pass) |
| Q2 | Migrations required and tested? | Answered from evidence — not required; no schema step; store write-neutral |
| Q3 | Dependent services healthy? | Answered from evidence — none; OpenRouter offline; store healthy and backed up |
| Q4 | Deployment window? | Answered from evidence — none, none invented |
| **Q5** | **Commit and tag the release?** | **GENUINELY OPEN — human** |
| Q6 | Bound the series width? | OPEN — inherited; belongs to the analytics-surface owner |
