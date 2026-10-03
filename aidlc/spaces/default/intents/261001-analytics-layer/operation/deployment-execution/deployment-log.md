# Deployment Log — intent `261001-analytics-layer`

> **Stage:** `deployment-execution` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> support `aidlc-developer-agent` (migration step) · **Date:** 2026-10-03 ·
> **Release commit:** `aa0b1e4` (`feature: Bolt 1 code generation — the analytics slice`)
> · **Companion to:** `smoke-test-results.md`, `health-check-report.md`,
> `deployment-execution-questions.md`
> · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/operation/deployment-execution`
>
> **Upstream inputs this execution consumed, in full** (the stage's declared
> `consumes`, plus the rollback runbook): `operation/deployment-pipeline/cd-config.md`
> (`cd-config`, the R1–R8 procedure) · `operation/deployment-pipeline/deployment-strategy.md`
> (`deployment-strategy`) · `operation/deployment-pipeline/rollback-runbook.md`
> (RB1/RB2/RB3) · `operation/environment-provisioning/environment-inventory.md`
> (`environment-inventory`) · `operation/environment-provisioning/validation-report.md`
> (44 checks, F-01) · `construction/build-and-test/test-results.md`
> (`build-test-results`) · `construction/build-and-test/build-instructions.md` ·
> `memory/team.md` § Deployment, § Way of Working, § Testing Posture ·
> `memory/project.md` · `app/main.py` · `app/config.py` · `app/db.py` · `app/routes.py`.

---

## 1. What "execute the deployment" means here, and what was actually executed

`memory/team.md` § Deployment fixes the deployment model for this project:
**"Deployment is a localhost checkout, and a commit is the release."** The release
artifact is the squashed commit tagged with the scope name, the version stays
`0.1.0`, the install is editable, and nothing is published as a package or an
image. There are no environment tiers, no container, no registry and no IaC — each
ruled out per element in `environment-inventory.md` §4 and `validation-report.md` §F.

So the executable content of this stage is: **run the recorded release procedure
`cd-config.md` §3 R1–R8, and prove the released thing actually serves.** Everything
below is the output of a command run in this stage on this machine. Nothing is
transcribed from an upstream artifact as though it had been observed here.

**Every interpreter invocation is prefixed `env -u APPIMAGE`.** That is measured,
not stylistic: with `APPIMAGE` exported, CPython 3.14 resolves `sys.executable` to
the desktop AppImage, which breaks the one spawned interpreter in the suite
(`build-instructions.md` §6, `validation-report.md` V-04).

### 1.1 Standing safety constraint honoured through this whole stage

The operator's `data/sentiment.db` is their gitignored database and had to end
this stage byte-identical to how it was found. **Verified twice — before and after
every group of commands (§5, `health-check-report.md` §4).**

Baseline captured before any release step ran:

```
sha256  c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
mtime   2026-10-03 03:33:42.920985500 +0500
size    32768 bytes
schema_meta.version = 4   (read through SQLite's read-only URI, mode=ro)
indexes  = idx_analyses_created_at, idx_analyses_import_id, idx_analyses_label_created_at
rows     = 0
```

The mechanism that keeps this true is the one `cd-config.md` §5 measured and
`validation-report.md` F-01 corrected: the default DB path is **CWD-relative**
(`app/config.py:39`, `Path("data/sentiment.db")`), `init_db` **writes the store
only when the store is behind `SCHEMA_VERSION`**, and the operator's store is
already at `4`. Every throwaway store built for a test lived in a `mktemp -d`
scratch tree. §4 below records the one deliberate exception — the genuine R7
cutover against the real store — and the measurement proving it was inert.

---

## 2. Step-by-step record of R1–R8, as executed

### R1 — Confirm the tree is clean and the release commit is the one you mean

**Exit status: 0 (all three commands ran).**

```
$ git status --short
 M aidlc/spaces/default/intents/261001-analytics-layer/aidlc-state.md
 M aidlc/spaces/default/intents/261001-analytics-layer/audit/verycool-96b70e2019ac.md
 M aidlc/spaces/default/intents/261001-analytics-layer/construction/u1-analytics-slice/code-generation/code-summary.md
 M aidlc/spaces/default/memory/project.md
?? .commandcode/
?? aidlc/spaces/default/intents/261001-analytics-layer/construction/build-and-test/
?? aidlc/spaces/default/intents/261001-analytics-layer/construction/ci-pipeline/
?? aidlc/spaces/default/intents/261001-analytics-layer/operation/
?? aidlc/spaces/default/intents/261001-analytics-layer/verification/phase-check-construction.md

$ git log --oneline -1
aa0b1e4 feature: Bolt 1 code generation — the analytics slice

$ git describe --tags
express-6-gaa0b1e4

$ git remote -v
(no output — there is no remote, so there is nothing to push to and nothing to compare against)

$ git rev-list --count HEAD
8
```

**Result: PASS, with one recorded condition.** The release commit is `aa0b1e4` and
it is the one intended. `git describe` names `express` as the last release tag,
**6 commits back** — which is the RB2 rollback target, confirmed reachable in §3.

The working tree is **not** clean: four modified records plus five untracked paths,
all of them `aidlc/` record files and one harness scratch directory
(`.commandcode/`). **No application source file is modified or untracked** — the
dirty state is entirely the AI-DLC record of the stages that preceded this one. Per
`memory/team.md` § Way of Working, those record files are committed as part of each
scope's commit; this stage does not commit them, so they are carried forward
uncommitted. See §6.

### R2 — Install into a venv

**Recorded command first, exactly as `cd-config.md` §3 writes it:**

```
$ env -u APPIMAGE python -m pip install -e ".[dev]"
error: externally-managed-environment
hint: See PEP 668 for the detailed specification.
exit = 1
```

**Then the recorded remedy, the venv form:**

```
$ env -u APPIMAGE .venv/bin/python -m pip install -e ".[dev]"
  Uninstalling very-cool-sentiment-analysis-0.1.0:
    Successfully uninstalled very-cool-sentiment-analysis-0.1.0
Successfully installed very-cool-sentiment-analysis-0.1.0
exit = 0
```

**Result: PASS via the remedy; the bare form fails as `cd-config.md` predicted.**
The PEP 668 block is a property of this host's externally-managed system
interpreter (`/usr/lib/python3.14/EXTERNALLY-MANAGED` exists), re-confirmed here
independently of `validation-report.md` V-02 and `build-instructions.md` §2.3.
`git status --short` returned the **same 9 lines** before and after — the editable
install added nothing to the repository.

Version confirmed: `very-cool-sentiment-analysis-0.1.0` — the version stays
`0.1.0`, per `memory/team.md` § Deployment.

### R3 — Run the gate set

**Exit status: 0.**

```
$ env -u APPIMAGE .venv/bin/python -m pytest -q
........................................................................ [ 37%]
........................................................................ [ 75%]
................................................                         [100%]
================================ tests coverage =============================
TOTAL                        884     26    97%
Required test coverage of 80% reached. Total coverage: 97.06%
```

```
$ env -u APPIMAGE .venv/bin/python -m pytest -v --no-header
============================= test session starts ==============================
============================= 192 passed in 1.72s ==============================
```

**Result: PASS — 192 passed, 0 failed, 0 skipped, 0 errors.** The `-q` form's
summary line is suppressed by the project's own `addopts`
(`pyproject.toml:37` carries `-q` already), so the count was read from the
`-v` form. **192 matches the 192 the Build and Test stage recorded**
(`test-results.md` §2.1), so the released commit's suite is identical to the
verified one. Whole-application coverage **97.06 %** against the affirmed 80 %
floor.

Note: `--collect-only` reported a coverage FAILURE (`46.38 %`). That is the
coverage floor being applied to a collection-only run, not a gate failure; the
gate is R3's full run, which passes at 97.06 %.

### R4 — Lint and format

**Exit status: 0 for both commands.**

```
$ env -u APPIMAGE .venv/bin/python -m ruff check app tests
All checks passed!
exit = 0

$ env -u APPIMAGE .venv/bin/python -m ruff format --check app tests
30 files already formatted
exit = 0
```

**Result: PASS.** G2 and G3 green, unchanged from `quality-gates.md` §2.

### R5 — Protect the store before anything starts the app

**Exit status: 0.**

```
$ SHA=$(git rev-parse --short HEAD)      # aa0b1e4
$ cp data/sentiment.db "data/sentiment.db.bak-$SHA"
exit = 0

$ sha256sum data/sentiment.db data/sentiment.db.bak-aa0b1e4
c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39  data/sentiment.db
c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39  data/sentiment.db.bak-aa0b1e4
```

**Result: PASS.** The backup is byte-identical to the store it protects.

This is the step `cd-config.md` §3 introduced for exactly this intent, and it is
the only mitigation that exists for the one irreversible asset in the project.
`rollback-runbook.md` §3 records that no commit contains a copy of the store
(`/data/` is gitignored), there is no replication and no migration tool — so RB3,
if the file were ever lost, would be total data loss. **The backup now exists and
is verified byte-identical.** It is the RB3 recovery entry that was empty until
this release step ran. It lives under the gitignored `/data/`, so it adds nothing
to the repository.

### R6 — Smoke the release against a throwaway store, not the real one

Run verbatim from `cd-config.md` §5, unmodified except for the scratch directory
path:

```bash
SCR=$(mktemp -d)
env -u APPIMAGE PYTHONPATH="$PWD" .venv/bin/python -c "
import os,threading,time,urllib.request,uvicorn; os.chdir('$SCR'); \
from app.main import app as a; \
threading.Thread(target=uvicorn.run,args=(a,),kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'},daemon=True).start(); \
time.sleep(2); \
print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"
```

**Output:**

```
INFO:     Sentiment analysis app ready in offline mode (OpenRouter not connected)
{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
exit = 0
```

**Result: PASS.** Reproduced `cd-config.md` §5 exactly:

| Assertion | Measured |
|---|---|
| `exit code` | **0** |
| body | `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}` |
| throwaway store created | **True** → `/tmp/tmp.SKcuVsbfQ4/data/sentiment.db` |
| real store untouched | **True** — sha256 and mtime both unchanged immediately after |

The isolation works because `os.chdir` happens **after** `PYTHONPATH` is set and the
interpreter has started: the `app` import still resolves through `PYTHONPATH`, and
every relative path the process then opens lands in the throwaway tree.

The full real-HTTP smoke surface — 27 checks over real sockets against a real
`uvicorn` **subprocess** — is in `smoke-test-results.md`. **27 passed, 0 failed.**

### R7 — Cut over (recreate)

`deployment-strategy.md` §2 names **recreate**: the old process is stopped and a
new one starts on the new commit, with no overlap and no warm standby. There was no
process running at the start of this stage, so the cutover is the start itself.

**This is the one step executed against the operator's real store**, deliberately,
because it is the actual release: `uvicorn app:app` from the repository root resolves
the CWD-relative `data/sentiment.db` and runs `init_db` on it. The store's sha256
and mtime were sampled immediately before and immediately after.

```
PRE  sha=c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
PRE  mtime=2026-10-03 03:33:42.920985500 +0500

$ env -u APPIMAGE .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000 --log-level info &

$ curl -sS -w "\nHTTP=%{http_code}\n" http://127.0.0.1:8000/v1/health
{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
HTTP=200

$ curl -sS -w "\nHTTP=%{http_code}\n" http://127.0.0.1:8000/v2/analytics/summary
{"total":0,"counts":{"positive":0,"negative":0,"neutral":0},"shares":{"positive":null,"negative":null,"neutral":null},"mean_confidence":null,"mean_confidence_row_count":0,"series":[]}
HTTP=200

$ ss -ltnp | grep 8000
LISTEN 0  2048  127.0.0.1:8000  0.0.0.0:*  users:(("python",pid=162172,fd=6))

server log:
INFO:     Started server process [162172]
INFO:     Waiting for application startup.
INFO:     Sentiment analysis app ready in offline mode (OpenRouter not connected)
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:58354 - "GET /health HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:47640 - "GET /v1/health HTTP/1.1" 200 OK
INFO:     127.0.0.1:47652 - "GET /v2/analytics/summary HTTP/1.1" 200 OK

kill -TERM -> exit = 143 (SIGTERM)

POST sha=c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39
POST mtime=2026-10-03 03:33:42.920985500 +0500
STORE SHA256 UNCHANGED
STORE MTIME UNCHANGED
```

**Result: PASS — the released commit serves, on loopback, and the store was not
written.** Three things are established here, each load-bearing:

1. **The release serves.** The new `/v2` analytics surface answers `200` over real
   HTTP from the release commit.
2. **The bind is loopback and nothing else.** `ss` shows the socket bound to
   `127.0.0.1:8000` with peer `0.0.0.0:*` — a listening socket on the loopback
   address only, not on a wildcard.
3. **The store is provably write-neutral on a v4 store.** sha256 **and** mtime are
   unchanged, not merely "the content looks the same". This independently
   reproduces `validation-report.md` V-15 and confirms finding **F-01** — the
   startup migration writes **iff** the store is behind `SCHEMA_VERSION`, and on a
   store already at v4 it does not write at all.

The 404 on `GET /health` in the server log is from this stage's own TCP port probe
before the first real request; it is a genuine 404 (there is no unversioned
`/health`) and is recorded rather than hidden.

**R7b — recreate semantics verified explicitly.** Two full cycles, distinct PIDs:

```
cycle 1 pid=162427 health={"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
cycle 1 exited 143 ; port closed after stop (gap, expected)
cycle 2 pid=162663 health={"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
cycle 2 exited 143 ; port closed after stop (gap, expected)
```

No overlap between the old and the new process, and the port is genuinely closed
between them — the one accepted cost of the recreate strategy, measured rather
than asserted.

### R8 — Tag the release

**NOT EXECUTED. Deliberately, by instruction.**

`cd-config.md` §3 R8 is `git tag -a <scope-name> -m "<scope-name> scope release"`.
`memory/team.md` § Way of Working makes the tag the release, so whether this scope's
release tag is written is a **human decision**, not one this stage takes on its
own. The stage boundary in force was explicit: *do not commit, tag, merge or push
anything.*

The tag is the **only** remaining step of the release. R1–R7 are executed and
measured; R8 is a single human action whose input — the verified commit `aa0b1e4` —
is now known good. What that step will produce, if the human runs it:

```
git tag -a analytics-layer -m "analytics-layer scope release" aa0b1e4
```

The tag name is left as a human choice; `cd-config.md` writes it as
`<scope-name>` and the scope here is `analytics-layer`. Nothing else in R1–R8
depends on it, and RB2's rollback target does not depend on it either — `git describe
--tags` currently resolves to `express` either way.

---

## 3. Rollback path reachable from where this stage left things

`rollback-runbook.md` is an operation-phase artifact whose procedures have to be
true of this environment to be usable at all. Verified here, from the exact state
the stage left behind:

| Runbook | Reachability from the state left behind | Evidence |
|---|---|---|
| **RB1** — migration fails at startup | **Reachable in principle; not triggered.** The code path is `app/db.py:241` (`except BaseException: rollback(); raise`), inside the lifespan before the server accepts anything. The distinctive signature — *the port never opens* — was reproduced independently by Environment Provisioning (V-20). | Not re-executed here: re-executing it requires constructing a store the step cannot preserve, which is upstream work already measured and recorded. Recorded as inherited-and-reachable, not as re-measured. |
| **RB2** — roll back the release commit | **Reachable. Target present and an ancestor of HEAD.** `git rev-parse express` → `d3a7703f4c7dbbc04efd2fbdd54bc2356f8acc6f` → `beeb587 express: add CSV bulk import / export endpoints (express scope)`. `git merge-base --is-ancestor <express> HEAD` → **YES**. So `git checkout express` (or `git revert`) works with no remote. | Measured in this stage. |
| **RB3** — the store is damaged or gone | **The recovery entry that was previously empty now exists.** `data/sentiment.db.bak-aa0b1e4`, sha256 `c8be1361…c39`, byte-identical to the store. `mv` it back and the restored store migrates forward idempotently — the idempotency measured in `health-check-report.md` §3. | Created and verified in this stage (R5). |

**The one asymmetry worth stating plainly:** RB2 (roll back the code) costs one
`checkout` and one restart and needs no data recovery, because the v3 → v4 step is
expand-only. RB3 (recover the file) costs everything, because nothing else holds a
copy. **R5 is what makes the second one survivable, and R5 ran.**

---

## 4. Pre-deployment checks — measured, not asserted

The four questions the stage's Step 2 requires. Each is answered by a measurement
in this stage; full derivations and sources are in
`deployment-execution-questions.md`.

| Question | Answer | The measurement |
|---|---|---|
| **Are all pre-deployment checks passing?** | **Yes.** R2 (via the recorded venv remedy), R3, R4 and R5 all returned the exit statuses in §2. The one recorded divergence — the bare `pip install` exiting 1 under PEP 668 — is a property of this host's system interpreter, re-confirmed here, and `cd-config.md` already carries it as a deliberate divergence from the approved artifact. | §2, R2/R3/R4/R5 |
| **Are database migrations required and tested?** | **A migration step exists and is tested; it was NOT required on the operator's store, and it ran as a no-op there.** The `v3 → v4` step was executed deliberately, in isolation, against a seeded copy carrying four real rows: version advanced `3 → 4`, all 4 rows preserved with a byte-identical content digest, all three indexes present, and a re-run was idempotent. On the real store — already at `4` — the step is write-neutral down to the mtime. Full record: `health-check-report.md` §3. | §2 R6/R7, `health-check-report.md` §3 |
| **Are dependent services available and healthy?** | **There are none, and that is measured rather than assumed.** No AWS CLI, no AWS credential in the environment or on disk, no IaC file of any kind, no git remote (`environment-inventory.md` §1.1, M1/M2/M3/M5). The only external dependency is OpenRouter, and it is **not connected** — `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}` from `/v1/health` over real HTTP, so the app served its full read surface in offline mode with the dummy engine. The app is unauthenticated and binds loopback only, so nothing outside the machine depends on it. | §2 R7, `environment-inventory.md` §1.1, `validation-report.md` V-16 |
| **What is the deployment window?** | **There is no window and none is invented.** `memory/team.md` § Way of Working records that no maximum branch age has ever been affirmed, and `deployment-strategy.md` §6 records the freeze-calendar line as *not designed*. A one-operator localhost release has nothing to freeze; the measured outage of the recreate strategy is the interval between the two processes, measured in R7b as a sub-second gap on a port that closed cleanly and reopened cleanly. | R7b, `deployment-strategy.md` §6 |

---

## 5. Repository and store state left behind

### 5.1 The operator's store — byte-identical, verified

| | Before this stage | After this stage |
|---|---|---|
| sha256 | `c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39` | `c8be136113a9bf44f2ade895f9fe2764b130ae52807b95b919edb5e694e39c39` |
| mtime | `2026-10-03 03:33:42.920985500 +0500` | `2026-10-03 03:33:42.920985500 +0500` |
| size | `32768` | `32768` |
| `schema_meta.version` | `4` | `4` (read-only; re-read at the end) |
| indexes | 3 | 3 |
| rows | 0 | 0 |

**Identical on every field.** The mtime is the load-bearing one: an unchanged mtime
means the file was not opened for writing at all.

The only file added under `data/` is `data/sentiment.db.bak-aa0b1e4`, which is R5's
recorded backup and is inside the gitignored `/data/`. **No file was modified,
replaced or deleted.** Every throwaway store built during this stage lived under a
`mktemp -d` scratch directory and none of them was inside the repository.

### 5.2 Git — nothing committed, tagged, merged or pushed

```
$ git log --oneline -1
aa0b1e4 feature: Bolt 1 code generation — the analytics slice     <- unchanged

$ git tag -l
express
v1-classic                                                       <- unchanged, no new tag

$ git remote -v
(no output)                                                       <- nothing to push to

$ git status --short
 M aidlc/spaces/default/intents/261001-analytics-layer/aidlc-state.md
 M aidlc/spaces/default/intents/261001-analytics-layer/audit/verycool-96b70e2019ac.md
 M aidlc/spaces/default/intents/261001-analytics-layer/construction/u1-analytics-slice/code-generation/code-summary.md
 M aidlc/spaces/default/memory/project.md
?? .commandcode/
?? aidlc/spaces/default/intents/261001-analytics-layer/construction/build-and-test/
?? aidlc/spaces/default/intents/261001-analytics-layer/construction/ci-pipeline/
?? aidlc/spaces/default/intents/261001-analytics-layer/operation/
?? aidlc/spaces/default/intents/261001-analytics-layer/verification/phase-check-construction.md
```

- **No commit.** HEAD is still `aa0b1e4`; `git rev-list --count HEAD` is still 8.
- **No tag.** The two pre-existing tags are unchanged; `analytics-layer` does not
  exist. R8 is a human decision (§2 R8).
- **No merge, no rebase, no branch change.** The working branch is unchanged.
- **No push.** There is no remote, so a push was not merely declined — it is
  impossible.
- **No application source file is modified or untracked.** The dirty paths are all
  `aidlc/` record files written by the stages before this one, plus one harness
  scratch directory. This stage's own artifacts are the new
  `operation/deployment-execution/` files.
- **No dependency, no file at the repository root was added.** The editable install
  and the backup copy left `git status` the same 9 lines.

### 5.3 No process left running

Both `uvicorn` processes started in R7 and R7b were terminated with `SIGTERM`
(exit 143) and both stop cycles showed the port closed. The smoke-suite
`uvicorn` subprocess was likewise terminated. **Port 8000 and port 8141 and the
smoke ports are all free.** The stage leaves the machine as it found it, with the
exception of the R5 backup file, which is the point of R5.

---

## 6. Result summary

| Step | Executed? | Exit status | Measured result |
|---|---|---|---|
| **R1** tree / release commit | yes | 0 | release commit `aa0b1e4`; `git describe` → `express-6-gaa0b1e4`; no remote; 8 commits. Tree dirty only in `aidlc/` records. |
| **R2** install | yes, both forms | **1** bare / **0** venv | PEP 668 `externally-managed-environment` on the bare form, as `cd-config.md` records; `very-cool-sentiment-analysis-0.1.0` installed editable into `.venv`. |
| **R3** gate set | yes | 0 | **192 passed**, 0 failed, 1.72 s; coverage **97.06 %** against the 80 % floor. |
| **R4** lint + format | yes | 0 / 0 | `All checks passed!` · `30 files already formatted`. |
| **R5** store backup | yes | 0 | `data/sentiment.db.bak-aa0b1e4` created, sha256 byte-identical. |
| **R6** throwaway-store smoke | yes | 0 | `{"mode":"offline","connected":false,…}`; throwaway store created; **real store's mtime unchanged**. |
| **R7** cutover (recreate) | yes | 0 / 143 | `/v1/health` 200, `/v2/analytics/summary` 200 on `127.0.0.1:8000`; socket bound loopback-only; **store sha256 and mtime both unchanged**; recreate gap confirmed closed-then-open. |
| **R8** tag | **no — human decision** | — | Not executed by instruction. R1–R7 are the whole of the executable release; R8 is one `git tag -a`. |
| **migration `v3 → v4`** | yes, in isolation | 0 | version `3 → 4`, 4 rows preserved with identical digest, 3 indexes, idempotent re-run. A **no-op** on the operator's real store. See `health-check-report.md` §3. |
| **smoke suite** | yes | 0 | **27 checks, 27 passed, 0 failed** over real HTTP against a real `uvicorn` subprocess. See `smoke-test-results.md`. |

**Deployment outcome: SUCCESSFUL.** The commit `aa0b1e4` installs, passes its full
gate set, boots on the loopback bind, serves `/v1/health` and both `/v2/analytics/*`
endpoints with and without parameters, refuses every malformed request with
`422 VALIDATION_FAILED`, serves the page, and left the operator's store
byte-identical. The one remaining step of the release — writing its tag — is a human
decision and is not this stage's to take.
