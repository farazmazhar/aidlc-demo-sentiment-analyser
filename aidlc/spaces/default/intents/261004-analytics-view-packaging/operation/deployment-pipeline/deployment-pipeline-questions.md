# Deployment Pipeline Questions — intent `261004-analytics-view-packaging`

> **Stage:** `deployment-pipeline` (operation), Step 2 · lead `aidlc-pipeline-deploy-agent`
> **Record:** `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/deployment-pipeline`
> **Inputs derived from:** the prior intent's `261001-analytics-layer/operation/deployment-pipeline/*` ·
> `construction/build-and-test/*` · `memory/team.md` § Deployment and § Way of Working ·
> `memory/project.md` · `app/db.py` · `app/main.py` · `app/config.py` · the current requirements
> (`inception/requirements-analysis/requirements.md`) · the new `Makefile` / `requirements.lock`.

The stage definition names five questions. All five are answered from evidence that
already exists — the repository, the prior intent's release record, and this intent's
own approved requirements — so none is put to the human as a new decision. Two items
are recorded as genuinely open and are the human's or a later stage's.

| # | Question | Status | Answered by |
|---|---|---|---|
| Q1 | Deployment strategy — blue/green, canary, rolling? | ANSWERED | `memory/team.md` § Deployment; `deployment-strategy.md` §2–§3 |
| Q2 | Environment promotion gates (dev → staging → prod)? | ANSWERED — none exist | `memory/team.md` § Deployment; one bind address |
| Q3 | Production approval workflow? | ANSWERED — no production, no second person | `memory/team.md` § Way of Working |
| Q4 | Rollback procedure? | ANSWERED | `rollback-runbook.md` |
| Q5 | Feature-flag strategy (AppConfig, CloudWatch Evidently)? | ANSWERED — none, with a named alternative | `deployment-strategy.md` §7; `C-4`/`C-5` |
| Q6 | Adopt `make verify` as the release gate step, replacing the prior intent's separate R3/R4 commands? | ANSWERED — yes | this intent's `requirements.md` FR2.1; `cd-config.md` §3 |
| Q7 | Should the manual end-to-end boot step (which migrates the real store) become a release step? | OPEN — the human's | `rollback-runbook.md` §4; see below |

## Q1–Q5 — answered from evidence

- **Q1 — strategy.** Process: **recreate** (stop the one loopback process, start it on the
  new commit). Schema: **no change this release** — `SCHEMA_VERSION` stays `4`, so unlike
  the prior intent there is no schema step in this release. Traffic-shaping strategies
  (blue/green, canary, rolling, A/B) presuppose two versions serving traffic; there is
  one process, one address, one operator.
- **Q2 — promotion gates.** There is one environment, so there is nothing to promote
  between. The substitute is the throwaway-store smoke (`cd-config.md` R6), which runs
  the real app through real `uvicorn` against a disposable store.
- **Q3 — production approval.** No production exists and there is no second human
  reviewer (`memory/team.md` § Way of Working). A gate that cannot fail is worse than no
  gate.
- **Q4 — rollback.** `rollback-runbook.md`. Because this release adds no schema step,
  rolling the code back is a pure `git checkout` with no data recovery.
- **Q5 — feature flags.** None, and none is warranted: there is no flag mechanism in the
  code; the release's risk control is the frozen `/v1` boundary and an additive page
  change; and `C-4`/`C-5` rule out any hosted flag service.

## Q6 — `make verify` becomes the release gate step

**Answer: yes.** FR2.1 makes `make verify` the platform-neutral verification entry point
(install → `ruff check` → `ruff format --check` → `pytest` with the coverage floor →
secret scan → dependency audit). The prior intent's release procedure ran those gates as
separate commands (its R3/R4) and explicitly named this convergence as the intended
destination once the script landed. It has now landed, so `cd-config.md` §3 replaces R3/R4
with a single `make verify`, and R2 installs from the committed `requirements.lock`.

## Q7 — the manual boot step migrates the real store

**Status: OPEN, and it is the human's.** The prior intent's deployment-pipeline Q6
recorded that booting the real `app.main:app` from the repository root migrates the
operator's real `data/sentiment.db`, because `DEFAULT_DB_PATH` is the CWD-relative
`Path("data/sentiment.db")`. `make verify` does **not** boot the app (the suite never
starts a server), so the automated gate no longer has this hazard. The README's
documented manual end-to-end step still does. `cd-config.md` R5 (copy the store first)
and R6 (smoke against a throwaway CWD) are the mitigation; whether the README's manual
step should also run from a throwaway CWD is a documentation change to a
human-approved artifact and remains the human's call. Not re-asked here.
