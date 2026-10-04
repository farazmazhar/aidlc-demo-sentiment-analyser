# Deployment Log — intent `261004-analytics-view-packaging`

> **Stage:** `deployment-execution` (operation) · lead `aidlc-pipeline-deploy-agent` ·
> support `aidlc-developer-agent` · **Date:** 2026-10-04 ·
> **Release under test:** the working tree at HEAD `4b67c03` ·
> **Companion to:** `smoke-test-results.md`, `health-check-report.md`,
> `deployment-execution-questions.md`
> · **Record:**
> `aidlc/spaces/default/intents/261004-analytics-view-packaging/operation/deployment-execution`

---

## 1. What "execute the deployment" means here

`memory/team.md` § Deployment fixes the model: **"Deployment is a localhost checkout, and
a commit is the release."** There are no environment tiers, no container, no registry and
no IaC. So the executable content of this stage is: **run the release procedure
`cd-config.md` §3 R1–R8 and prove the released thing actually serves.** Everything below
is the output of a command run in this stage.

**Standing safety constraint:** the operator's `data/sentiment.db` must end this stage
byte-identical. It did — verified by sha256 **and** mtime, before and after (§5).

---

## 2. Step-by-step record of R1–R8

### R1 — Confirm the tree and the release commit

```
$ git log --oneline -1
4b67c03 docs: report the unreachable per-Unit completion receipt
$ git describe --tags
feature-15-g4b67c03
$ git remote -v
origin  https://github.com/farazmazhar/aidlc-demo-sentiment-analyser.git (fetch)
origin  https://github.com/farazmazhar/aidlc-demo-sentiment-analyser.git (push)
$ git status --short   (head)
 M README.md
 M app/static/app.js
 M app/static/index.html
 M pyproject.toml
 M tests/test_page.py
?? Makefile  ?? LICENSE  ?? requirements.lock  ?? .secrets.baseline
```

**Result: PASS with a recorded condition.** The application change **is in the working
tree, uncommitted**; HEAD `4b67c03` predates it. A git remote now exists (contrary to
`memory/team.md`'s "no remote") but carries no CI workflow. Both are the human's release
decisions (§ Q5 in `deployment-execution-questions.md`).

### R2 — Install into a venv

The `.venv` is present and the package is installed editable
(`very-cool-sentiment-analysis-0.1.0`). The bare system-interpreter form exits 1 under
PEP 668, as `cd-config.md` R2 records; the venv form is the release form. `requirements.lock`
now pins the resolved set.

### R3 — Run the gate set

```
$ make verify
... 198 passed in 1.91s
Required test coverage of 80% reached. Total coverage: 97.06%
ruff check: All checks passed!
ruff format --check: 30 files already formatted
detect-secrets: (clean)
pip-audit: No known vulnerabilities found
```

**Result: PASS.** 198 passed, 0 failed; coverage 97.06 % against the 80 % floor; secret
scan and dependency audit clean. This is the single-command gate that replaces the prior
intent's separate R3/R4.

### R4 — Protect the store before anything starts the app

```
$ SHA=$(git rev-parse --short HEAD)      # 4b67c03
$ cp data/sentiment.db "data/sentiment.db.bak-$SHA"
$ sha256sum data/sentiment.db data/sentiment.db.bak-4b67c03
2a4574cf05238ff031afd0c0e022ee4cd1c14cab949110027f176350436d42e7  data/sentiment.db
2a4574cf05238ff031afd0c0e022ee4cd1c14cab949110027f176350436d42e7  data/sentiment.db.bak-4b67c03
```

**Result: PASS.** The backup is byte-identical. This is the only mitigation that exists
for the one irreversible asset (`/data/` is gitignored; no commit contains a copy).

### R5 — Throwaway-store smoke

Run from `cd-config.md` §5 with the store path isolated by a throwaway CWD. The real
store's mtime was unchanged afterwards. The full real-HTTP surface is in
`smoke-test-results.md`: **14 checks, 14 passed, 0 failed**, plus the cutover below.

### R6 — Cut over (recreate)

The actual release, booted against the operator's real store on the enforced loopback
bind:

```
$ env -u APPIMAGE .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000

GET /v1/health           -> 200  {"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
GET /v2/analytics/summary -> 200  {"total":7,"counts":{"positive":3,"negative":3,"neutral":1},
                                    "shares":{"positive":0.4286,"negative":0.4286,"neutral":0.1429},
                                    "mean_confidence":0.9786,"mean_confidence_row_count":7,"series":[…2 days…]}
GET /v2/analytics/terms   -> 200  {"positive":[…],"negative":[…]}
GET /                     -> 200  (page carries range-from, range-to, range-status,
                                    terms-positive, terms-negative, summary-partial, terms-partial)

$ ss -ltnp | grep 8000
LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:* users:(("python",pid=…,fd=6))

kill -TERM -> exit 143 (SIGTERM)
STORE SHA256 UNCHANGED
STORE MTIME UNCHANGED
```

**Result: PASS.** Three load-bearing facts: the release **serves** the changed page and
both `/v2` endpoints over real HTTP; the bind is **loopback only**; and the store is
**provably write-neutral** (sha256 and mtime unchanged — the file was not opened for
writing, because there is no schema step to run at v4).

### R7 — Tag the release

**NOT EXECUTED — deliberately, a human decision.** See Q5: the change is uncommitted, and
whether and how to commit/tag/push this scope is the human's.

---

## 3. Rollback path reachable from the state left behind

| Runbook | Reachable? | Evidence |
|---|---|---|
| **RB1** — migration fails at startup | Reachable, not triggered | `app/db.py`'s rollback-and-re-raise; the failure signature is the port never opening. Inherited from the prior intent's rehearsal. |
| **RB2** — roll back the release commit | Reachable | `git describe --tags` → `feature`; the prior release tag is an ancestor of HEAD; `git checkout` works (and with the remote present, `git fetch` is now also possible). |
| **RB3** — the store is damaged or gone | Recovery entry now exists | `data/sentiment.db.bak-4b67c03`, sha256 `2a4574cf…d42e7`, byte-identical. |

This release adds no schema step, so RB2 costs one `checkout` and one restart with **no
data recovery**. RB3 remains total loss without the R4 backup, which now exists.

---

## 4. Pre-deployment checks — measured

| Question | Answer |
|---|---|
| Pre-deployment checks passing? | **Yes** — `make verify` green; R4/R5/R6 pass. |
| Migrations required and tested? | **Not required** — no schema step; store write-neutral. The v3 → v4 step is inherited as tested and idempotent. |
| Dependent services healthy? | **None exist**; OpenRouter offline and the app healthy without it; the store is healthy and backed up. |
| Deployment window? | **None**, and none invented. |

---

## 5. Repository and store state left behind

### 5.1 The operator's store — byte-identical

| | Before | After |
|---|---|---|
| sha256 | `2a4574cf05238ff031afd0c0e022ee4cd1c14cab949110027f176350436d42e7` | same |
| mtime | `2026-10-03 23:59:14.115475300 +0500` | same |
| `schema_meta.version` | `4` | `4` |
| indexes | 3 | 3 |
| rows | 7 | 7 |

The only file added under `data/` is `data/sentiment.db.bak-4b67c03` (R4), inside the
gitignored `/data/`. Every throwaway store lived under a `mktemp -d` scratch tree.

### 5.2 Git — nothing committed, tagged, merged or pushed

HEAD is still `4b67c03`; no new tag; the working branch is `main`; no push. The dirty
paths are this intent's own change plus `aidlc/` record files. **No application source
file was changed by this stage.**

### 5.3 No process left running

The cutover `uvicorn` and the smoke-suite subprocess were both terminated; ports 8000 and
8213 are free.

---

## 6. Result summary

| Step | Executed? | Result |
|---|---|---|
| R1 tree / commit / remote | yes | HEAD `4b67c03`; change uncommitted; a remote exists; no CI workflow |
| R2 install | yes | editable install present; PEP 668 blocks the bare form |
| R3 gate set | yes | `make verify` green — 198 passed, 97.06 % |
| R4 store backup | yes | `data/sentiment.db.bak-4b67c03`, byte-identical |
| R5 throwaway smoke | yes | 14/14 checks pass; real store untouched |
| R6 cutover | yes | serves `/`, `/v1/health`, both `/v2` endpoints; loopback-only; store sha256 **and** mtime unchanged |
| R7 tag | **no — human decision** | change is uncommitted |
| smoke suite | yes | **14 checks, 14 passed, 0 failed** over real HTTP |

**Deployment outcome: SUCCESSFUL.** The release installs, passes its full gate set,
boots on the loopback bind, serves the new analytics view and both `/v2` endpoints over
real HTTP, refuses malformed requests correctly, and left the operator's store
byte-identical. The remaining step — committing and tagging the release — is a human
decision and is not this stage's to take.
