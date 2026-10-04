# CD Pipeline Configuration — intent `261004-analytics-view-packaging`

> **Stage:** `deployment-pipeline` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Scope:** `express` · **Record:**
> `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/deployment-pipeline`
>
> **Inputs derived from:** the prior intent's `261001-analytics-layer/operation/deployment-pipeline/*`
> · `construction/build-and-test/{build-instructions,build-and-test-summary,test-results}.md`
> · `memory/team.md` (§ Deployment, § Way of Working) · `memory/project.md` ·
> `app/db.py` · `app/main.py` · `app/config.py` · `Makefile` · `requirements.lock` · the git history.
>
> **This is a design artifact.** It adds no file to the repository root.

---

## 1. The decision, and what this configuration is

**There is still no CD pipeline in this project, and this stage did not invent one.
What is configured here is the *release procedure* — the ordered, human-run sequence
that takes a verified commit to a running loopback process — updated for the two
instruments this intent adds: a single `make verify` gate and a hashed lockfile.**

The stage is `CONDITIONAL` — *"execute when CD pipeline needs creation or significant
modification."* The CD half is still not met: there is no runner, no environment tier,
no registry and no IaC, and no CI workflow of any kind, so there is nothing to configure
a pipeline against. (Correction, measured at Deployment Execution: a git remote **does**
now exist — `origin` → `https://github.com/farazmazhar/aidlc-demo-sentiment-analyser.git`
— contrary to `memory/team.md` § Way of Working's "no remote". It carries no workflows,
so it changes where a release tag can be pushed, not whether a pipeline runs.) The
**release-configuration half is met**, because this intent changes the release
procedure in two concrete ways:

1. **`make verify` now exists** (FR2.1) and supersedes the prior intent's separate gate
   commands (its R3/R4) — the convergence that intent named as its intended destination.
2. **A hashed lockfile now exists** (`requirements.lock`, FR2.4), so a release install
   can be made reproducible instead of re-resolving the dependency set.

Unlike the prior intent, **this release carries no schema step**: `app/db.py:60` still
declares `SCHEMA_VERSION = 4`, and this change touches only static page assets and
repository-level tooling. Rollback is therefore a pure `git checkout` (see
`rollback-runbook.md`).

---

## 2. What a CD pipeline declares, answered from evidence

| Concern | Configuration | Source |
|---|---|---|
| **Trigger** | **A human, at a terminal.** No automatic trigger fires: a remote exists but carries no CI workflow. | `git remote -v` → `origin` (GitHub); no `.github/workflows` |
| **Target** | **One loopback process** on `127.0.0.1:8000`, serving one gitignored SQLite file. | `app/main.py:45-46` `HOST`/`PORT`; `app/config.py` `DEFAULT_DB_PATH` |
| **Artifact** | **The git commit**, identified by an annotated tag named after the scope. No package, image, wheel or SBOM. | `memory/team.md` § Deployment / § Way of Working; tags `v1-classic`, `express`, `feature` |
| **Promotion** | **Nothing.** There is exactly one environment. | `memory/team.md` § Deployment |

The released commit is not yet tagged for this scope; R8 writes the tag.

---

## 3. The release procedure — R1 … R8

Eight ordered steps. Every command is either recorded by an upstream artifact or was
executed in this run.

| # | Step | Command | Why it is here |
|---|---|---|---|
| **R1** | Confirm the tree is clean and the release commit is the one you mean | `git status --short` · `git log --oneline -1` · `git describe --tags` | `git status` is the pre-flight; `git describe` names the last release tag — the rollback target. (A remote now exists, so `git status` can also be compared against `origin/main`.) |
| **R2** | Install into a venv, from the lockfile | `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"` (or install `requirements.lock` with hashes) | The bare `python -m pip install -e ".[dev]"` exits 1 on an externally-managed interpreter (PEP 668); the venv form exits 0. `requirements.lock` now pins the resolved set. |
| **R3** | **Run the gate set — one command** | `make verify` | Replaces the prior intent's separate R3/R4. Carries install, `ruff check`, `ruff format --check`, `pytest` with the 80 % floor, the secret scan and the dependency audit. |
| **R4** | **Protect the store before anything starts the app** | `cp data/sentiment.db data/sentiment.db.bak-$(git rev-parse --short HEAD)` | `data/` is gitignored; no commit contains a copy. This release adds no schema step, but the manual boot still runs `init_db` on the real store, so the copy stays cheap insurance. |
| **R5** | **Smoke the release against a throwaway store, not the real one** | see §5 | Runs the real `app.main:app` through real `uvicorn` with the store path isolated by a throwaway CWD. The real store's mtime is unchanged. |
| **R6** | Cut over | stop the running process; start it on the new commit: `uvicorn app:app` | The strategy is **recreate** — one process, replaced. |
| **R7** | Tag the release | `git tag -a <scope-name> -m "<scope-name> scope release"` | The tag *is* the release (`memory/team.md` § Way of Working). |
| **R8** | Confirm serving | `GET /v1/health` on `127.0.0.1:8000`, then exercise the changed page path | The release is not done until the changed path serves. |

**What R1–R8 deliberately is not.** Not a trigger, not a runner, not a blocking gate, and
not a promotion. Every step is a human action in a terminal, in order.

---

## 4. Preconditions any future CD configuration must honour

| # | Precondition | If violated |
|---|---|---|
| D1 | The source is a **git working tree** (`.git` + `.gitignore` present) | `tests/test_config.py` shells out to `git check-ignore`; without a checkout it exits 128 |
| D2 | `git` is on `PATH` | the suite's single `pytest.skip` fires, silently weakening the gate |
| D3 | CPython ≥ 3.11; measured 3.14.7 | import or parse failure |
| D4 | Install is a **venv** | R2 exits 1 on an externally-managed interpreter |
| D5 | The bind stays loopback | `create_app(host="0.0.0.0")` raises `NonLoopbackBindError` — by design |
| D6 | No release step reaches the network except R2/R3's install and `pip-audit` | the offline guard is the instrument; the suite itself never touches the network |

---

## 5. The throwaway-store smoke (R5)

Booting the real application from the repository root migrates `data/sentiment.db`
(`app/config.py`'s `DEFAULT_DB_PATH` is the CWD-relative `Path("data/sentiment.db")`).
The cheap fix is to boot from a different working directory, so every relative path the
process opens — the store above all — lands in a throwaway tree:

```bash
PYTHONPATH="$PWD" .venv/bin/python -c \
  "import os,threading,time,urllib.request,uvicorn; os.chdir('$(mktemp -d)'); \
   from app.main import app as a; \
   threading.Thread(target=uvicorn.run,args=(a,),kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'},daemon=True).start(); \
   time.sleep(2); \
   print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"
```

`os.chdir` into a fresh temporary directory **after** `PYTHONPATH` is set: the import of
`app` still resolves through `PYTHONPATH`, and the throwaway store is created there. `cp`
and `mktemp` are POSIX; nothing new is declared, so this stays inside the two-package
runtime cap and the localhost-only rule.

---

## 6. What this configuration deliberately does not contain

| Not configured | Why |
|---|---|
| **A provider workflow file** | No `.github/workflows` (or other provider config) exists; a hosted workflow written today would be a file that has never run. |
| **Environment tiers or a promotion matrix** | There is one environment. |
| **An approval gate** | No second human reviewer exists. |
| **A secret, secret store or credential scope** | No release step needs a credential; a pipeline that declares no secret cannot leak one. |
| **An artifact registry, retention policy or provenance upload** | Nothing is published. |
| **A coverage-delta or flaky-test gate** | The coverage floor is enforced by `make verify`; a coverage-delta gate has no artifact to diff. |
| **A branch-age gate, deployment window or freeze calendar** | No maximum branch age has been affirmed, and a one-operator localhost release has no window to freeze. |
| **A monitoring or alerting integration** | No process supervisor exists; observability is the Observability Setup stage's territory. |

---

## 7. Provenance

| Claim | Where it is verified |
|---|---|
| `SCHEMA_VERSION = 4`; no schema change in this release | `app/db.py:60`; `construction/code-generation/code-summary.md` |
| Loopback bind enforced on every startup path | `app/main.py:45, 65, 83` |
| The store path is relative and created on demand | `app/config.py`; `app/db.py` `connect()` |
| `make verify` runs the six gates | `Makefile`; `make -n verify`; `make verify` output |
| A hashed lockfile is committed | `requirements.lock`; `pip-audit -r requirements.lock` |
| A remote exists (`origin`), but no CI workflow and no runner | `git remote -v`; no `.github/workflows` |
| The release is a tagged commit | `git tag -l` → `v1-classic`, `express`, `feature` |
| Build and Test is green | `construction/build-and-test/test-results.md` (198 passed, 97.06 %) |
