# CD Pipeline Configuration — intent `261001-analytics-layer`

> **Stage:** `deployment-pipeline` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> **Scope:** `feature` · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/deployment-pipeline`
>
> **Inputs this artifact was derived from** (the stage's declared `consumes`, in
> full, plus the code and memory it was measured against):
> `construction/ci-pipeline/ci-config.md` · `construction/ci-pipeline/quality-gates.md` ·
> `construction/u1-analytics-slice/infrastructure-design/infrastructure-specification.md` ·
> `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` ·
> `construction/build-and-test/build-instructions.md` ·
> `memory/team.md` (§ Deployment, § Way of Working) · `memory/project.md` ·
> `app/db.py` · `app/main.py` · `app/config.py` ·
> `tests/test_migration_indexes.py` · `README.md` · the git history.
>
> **This is a design artifact.** It adds no file to the repository root. §1 states
> what it is instead.

---

## 1. The decision, and what this configuration therefore is

**There is no CD pipeline in this project, and this stage did not invent one. What
is configured here is the *release procedure* — the ordered, human-run sequence
that takes a verified commit to a running loopback process over a real store — plus
the one release-shaped hazard that this intent introduces for the first time in the
project's history.**

The stage is `CONDITIONAL` — *"execute when CD pipeline needs creation or significant
modification."* The CD half of that condition is **not** met and is recorded as such
rather than filled in: there is no git remote, no runner, no environment tier, no
registry and no IaC, so there is nothing to configure a pipeline *against*. The
release half **is** met, and the evidence is in the code rather than in an absence:

> **`app/db.py:60` declares `SCHEMA_VERSION = 4`, and `init_db` (`app/db.py:219`)
> runs on every application startup against the operator's real, gitignored
> `data/sentiment.db`.** A release commit in this repository now carries a schema
> step with a real failure mode. `memory/team.md` § Deployment and `u1`'s
> `cicd-pipeline.md` §1 both record *"there is no rollback procedure to write,
> because there is no deployment."* That sentence was true at schema version 3 and
> **is no longer true at version 4**, because the release is now the thing that
> mutates durable state.

Measured corroboration, not inference: `memory/team.md` records this checkout's
local store at `schema_meta.version = 2`; reading it now returns `4`, carrying all
three named indexes, with 0 rows. Something in this project's own verification runs
migrated the operator's real store, and §5 shows exactly what and how.

So this file configures the release, `deployment-strategy.md` names the strategy
that release uses, and `rollback-runbook.md` writes the procedure that neither of the
two upstream artifacts wrote because neither could have — the schema step did not
exist when they were authored.

---

## 2. What a CD pipeline declares, answered from evidence

A CD configuration normally declares four things. Each is answered here by what this
repository actually contains.

| Concern | Configuration | Source |
|---|---|---|
| **Trigger** — what starts a release | **A human, at a terminal.** No automatic trigger is possible: a pipeline is a program that runs on an event, and there is no event source. | `git remote -v` → empty. `ci-config.md` §1: *"no push destination, no pull request, no `merge_group`, no hosted runner."* |
| **Target** — what is deployed to | **One loopback process** on `127.0.0.1:8000`, serving one gitignored SQLite file. | `app/main.py:45-46` `HOST = "127.0.0.1"`, `PORT = 8000`; `app/config.py:39` `DEFAULT_DB_PATH = Path("data/sentiment.db")`; `memory/team.md` § Deployment |
| **Artifact** — what is released | **The git commit**, identified by an annotated tag named after the scope. No package, no image, no wheel, no SBOM. | `memory/team.md` § Deployment: *"no package or image is ever published"*; § Way of Working: *"tag that commit with the scope name."* Two executions: `v1-classic` → `4eb9b74`, `express` → `beeb587` |
| **Promotion** — what moves between environments | **Nothing.** There is exactly one environment. | `memory/team.md` § Deployment: *"The framework default — deploy-on merge to staging behind a manual production gate — has no counterpart here, because the environments it assumes do not exist."* |

**The released commit is not yet tagged.** The scope has **8 commits and no tag**
(`17acbb5`, `aad7494`, `3d405e5`, `9c005e9`, `b2c49bd`, `aa0b1e4`, plus the
uncommitted Bolt-1 stage artifacts) — one per completed stage, consistent with the
one-commit-per-scope rule, because this scope is not finished. §4 step **R8** is
where the tag is written. `ci-config.md` §10 reaches the same reading independently.

---

## 3. The release procedure — R1 … R8

Eight ordered steps. Every command is either recorded by an upstream artifact or was
executed in this run; the provenance column says which. **Every command is prefixed
`env -u APPIMAGE`** — measured, not stylistic: CPython 3.14 resolves `sys.executable`
to the desktop AppImage when `APPIMAGE` is exported, which breaks the one spawned
interpreter in the suite (`build-instructions.md` §6; `ci-config.md` §4.0).

| # | Step | Command | Why it is here |
|---|---|---|---|
| **R1** | Confirm the tree is clean and the release commit is the one you mean | `git status --short` · `git log --oneline -1` · `git describe --tags` | There is no remote, so `git status` against nothing is the only pre-flight that exists. `git describe` names the last release tag, which is the rollback target in `rollback-runbook.md` §2. |
| **R2** | Install into a venv | `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"` | The recorded verification command's bare `python -m pip install -e ".[dev]"` **exits 1** on this host (PEP 668, externally-managed `/usr/bin/python3.14`), proven pre-existing on a pristine clone of `HEAD`. The venv form exits 0. `build-instructions.md` §2.3 Remedy A; `ci-config.md` §4.1. **Divergence from the approved artifact, carried deliberately** — see `deployment-pipeline-questions.md` Q6. |
| **R3** | Run the gate set | `.venv/bin/python -m pytest -q` | Carries **7 of the 14 blocking gates** (G4, G5, G6, G11, G12, G13, G14). `quality-gates.md` §2. |
| **R4** | Lint and format | `.venv/bin/python -m ruff check app tests` · `.venv/bin/python -m ruff format --check app tests` | G2, G3. `quality-gates.md` §2. |
| **R5** | **Protect the store before anything starts the app** | `cp data/sentiment.db data/sentiment.db.bak-$(git rev-parse --short HEAD)` | **New, and it is the step this intent makes necessary.** `data/` is gitignored, so **no commit contains a copy of the store and there is no backup path** — `memory/team.md` § Deployment records exactly this: *"no migration tool, no backup path and no rollback procedure to write."* A schema step now runs on the real file at startup, so the file gets a copy first. See §5 and `rollback-runbook.md` §5. |
| **R6** | **Smoke the release against a throwaway store, not the real one** | See the command in §5 | The `express`-intent localhost-deployment precedent (`memory/team.md` § Deployment), reduced to its cheapest form: *"choose a throwaway temporary database so the real store is untouched."* Measured in this run: **exit 0**, `{"mode":"offline","connected":false,…}`, throwaway store created, **real store's mtime unchanged**. |
| **R7** | Cut over | stop the running process; start it on the new commit: `uvicorn app:app` | The strategy is **recreate** — see `deployment-strategy.md` §2. There is one process and it is replaced. |
| **R8** | Tag the release | `git tag -a <scope-name> -m "<scope-name> scope release"` | The tag *is* the release (`memory/team.md` § Way of Working). `ci-config.md` §5 gives the tag trigger **no job**, because *"there is nothing to build, sign, publish or promote."* |

**What R1–R8 deliberately is not.** It is not a trigger, not a runner, not a gate
that blocks anything, and not a promotion. Every step is a human action in a
terminal, in order. `quality-gates.md` §1.1 already states the consequence without
needing restating here: *"What is genuinely enforced mechanically, with no human in
the loop? **Nothing.**"*

---

## 4. Preconditions any future CD configuration must honour

The same facts that gated CI gate a release, and they are stated once here rather
than re-derived. Sources: `ci-config.md` §6 (P1–P6), `quality-gates.md` §1.2.

| # | Precondition | If violated |
|---|---|---|
| D1 | The source is a **git working tree** (`.git` + `.gitignore` present) | `tests/test_config.py` shells out to `git check-ignore`; without a checkout it exits 128 and one test fails with a message that reads like a credential leak |
| D2 | `git` is on `PATH` | the suite's single `pytest.skip` fires, silently weakening G4 |
| D3 | `env -u APPIMAGE` on every interpreter invocation | the latency-budget test fails `assert 130 == 0` — an environmental failure wearing the costume of a performance regression |
| D4 | CPython ≥ 3.11; measured 3.14.7 | import or parse failure |
| D5 | Install is a **venv** | R2 exits 1 on an externally-managed interpreter |
| D6 | The bind stays loopback | `create_app(host="0.0.0.0")` raises `NonLoopbackBindError` — **by design**, `app/main.py:65`, gate G12 |
| D7 | No release step reaches the network except R2 | the offline guard (`G13`) is the instrument; only the install resolves from the index |

---

## 5. The hazard this intent introduces, measured

**Running the app migrates the operator's real store, in place, at startup.**

The chain is short and entirely in the code:

1. `app/main.py:163` builds `app = create_app()` at module scope.
2. `create_app`'s lifespan calls `db.init_db(resolved.db_path)` (`app/main.py:132`).
3. With no injected settings, `load_settings()` resolves `DEFAULT_DB_PATH` =
   `Path("data/sentiment.db")` (`app/config.py:39`), and
4. `init_db` (`app/db.py:219`) opens `BEGIN`, migrates or creates, creates
   `schema_meta`, runs `_ensure_indexes`, records version `4`, and commits.

So **any** `uvicorn app:app` from the repository root — including the standing
verification command's own step 3, which boots the real `app.main:app` — migrates
`data/sentiment.db`. That is why the local store moved from version 2 to 4 during
this project's own Bolt-1 verification, and it is why R5 and R6 exist.

**The store path is CWD-relative**, and that is the cheap fix. `DEFAULT_DB_PATH` is
the *relative* `Path("data/sentiment.db")`, and `connect()` (`app/db.py:193`) creates
the parent directory on demand — so booting the real application from a different
working directory creates a throwaway store there and never touches the real one.
Measured in this run, unmodified command apart from `cwd` and `PYTHONPATH`:

```
exit code 0
stdout    {"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
throwaway store created : True   -> <scratch>/data/sentiment.db
  its schema            : version 4, 4 indexes, 0 rows
real store untouched    : True    (mtime_ns unchanged)
```

R6, therefore:

```bash
env -u APPIMAGE PYTHONPATH="$PWD" .venv/bin/python -c \
  "import os,threading,time,urllib.request,uvicorn; os.chdir('$(mktemp -d)'); \
   from app.main import app as a; \
   threading.Thread(target=uvicorn.run,args=(a,),kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'},daemon=True).start(); \
   time.sleep(2); \
   print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"
```

`os.chdir` into a fresh temporary directory **after** `PYTHONPATH` is set and the
interpreter has started: the import of `app` still resolves through `PYTHONPATH`,
and every relative path the process then opens — the store above all — lands in the
throwaway tree. This is the `express` precedent with the store isolated by directory
rather than by an injected `Settings`, which keeps the command readable as one line.

**R5 and R6 together are the whole mitigation, and neither adds a dependency, a
service or a file to the repository.** `cp` and `mktemp` are POSIX; nothing new is
declared, so this stays inside the two-package runtime cap (`C-5`, `NFR2.6`, gate
G11) and inside the localhost-only rule.

---

## 6. What this configuration deliberately does not contain

| Not configured | Why — stated rather than left blank |
|---|---|
| **A provider workflow file** | `git remote -v` is empty. `ci-config.md` §1 and §8 already record that a provider adapter is a **Tier-1 artifact that has never executed**, blocked on a remote, and give it as a worked example rather than a configuration. Writing a second one for the CD half would duplicate a decision that stage already made. |
| **Environment tiers or a promotion matrix** | There is one environment. `memory/team.md` § Deployment: the deploy-on-merge-to-staging default *"has no counterpart here."* `deployment-strategy.md` §6 records the checklist honestly instead of inventing tiers. |
| **An approval gate** | No second human reviewer exists — `memory/team.md` § Way of Working: *"one author, no co-authors… no second human reviewer."* `ci-pipeline-questions.md` Q7 already recorded that a gate which cannot fail is worse than no gate. |
| **A secret, secret store or credential scope** | No step in R1–R8 needs a credential. R6 constructs no key and reads no `config.local.toml`; the mode is `offline`. **A pipeline that declares no secret cannot leak one** (`quality-gates.md` §1.1 D-table; `ci-config.md` §8 note 2). |
| **An artifact registry, retention policy or provenance upload** | Nothing is published. The release's provenance is the tag plus the committed audit shard. `ci-config.md` §7 records that there is **nothing machine-readable to upload** today: no `--junit-xml`, no coverage XML. |
| **A coverage-delta or flaky-test gate** | Unbuildable — `quality-gates.md` §5 gives the reason and the owner (`u4-platform-packaging`, `FR7.1`/`FR7.2`). Re-deciding it here would pre-empt that unit. |
| **A branch-age gate, deployment window or freeze calendar** | `memory/team.md` § Way of Working: *"No maximum branch age has ever been affirmed and we are not inventing one."* A one-developer localhost release has no window to freeze. |
| **A monitoring or alerting integration** | There is no process supervisor and nothing to alert on. Observability for the app's own behaviour is `u3-analytics-view`'s and the operation phase's territory, not a CD concern. |
| **Anything about `u4-platform-packaging`'s verification script** | R3 and R4 are the command form of the same three standing gates `FR7.2` will wrap in a script. When it lands, R3/R4 become an argument to it rather than a parallel copy — `ci-config.md` §9 names that convergence as the intended destination. Not duplicated here. |

---

## 7. Provenance

| Claim in this file | Where it is verified |
|---|---|
| `SCHEMA_VERSION = 4`, transactional `init_db`, `_ensure_indexes`, the rebuild path | `app/db.py:60, 219, 249, 322` |
| Loopback bind enforced on every startup path | `app/main.py:45, 65, 83, 132, 163` |
| The store path is relative and created on demand | `app/config.py:39`; `app/db.py:193` (`path.parent.mkdir(parents=True, exist_ok=True)`) |
| The migration's failure rolls back completely and re-raises | `tests/test_migration_indexes.py:398`; reproduced in this run against real `uvicorn` — process **exit 1**, port never opens, store byte-identical |
| Idempotency of the step at v4 | `tests/test_migration_indexes.py:246` |
| Index survival across the rebuild | `tests/test_migration_indexes.py:324, 348` |
| Rollback of the **code** against a v4 store is safe | **measured in this run** — see `rollback-runbook.md` §3 |
| No remote, no CI, no runner | `git remote -v` empty; `ci-config.md` §1 |
| The release is a tagged commit | `git tag -l` → `express`, `v1-classic`; `memory/team.md` § Way of Working |
| Every gate in R3/R4 and its measured result | `quality-gates.md` §2 |
| R2's PEP 668 failure and the venv remedy | `build-instructions.md` §2.3; `test-results.md` §3.2 |
| The `express` localhost-deployment precedent this reduces | `memory/team.md` § Deployment |