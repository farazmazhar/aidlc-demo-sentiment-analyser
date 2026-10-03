# CI Pipeline Questions — intent `261001-analytics-layer`

> **Stage:** `ci-pipeline` (construction), Step 2 and Step 3 · lead
> `aidlc-pipeline-deploy-agent` · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/construction/ci-pipeline`
>
> **Inputs this artifact was derived from** (the stage's declared `consumes`, plus
> the routing decision that brought this work here):
> `construction/u1-analytics-slice/code-generation/code-summary.md` ·
> `construction/build-and-test/build-and-test-summary.md` ·
> `construction/build-and-test/test-results.md` (the frontmatter slug is
> `build-test-results`) · `construction/build-and-test/build-instructions.md` ·
> `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` ·
> `inception/units-generation/unit-of-work.md` · `memory/org.md`,
> `memory/team.md`, `memory/project.md`, `memory/phases/construction.md`.

---

## 0. Summary — three of the four required questions are already answered

The stage definition asks four questions. **Three are settled by an affirmed
practice or by the absence of a remote, and are recorded below as answered with
their source rather than re-opened as open questions.** Manufacturing an open
question where the repository has already decided would be the failure mode here.

| # | Question | Status | Answered by |
|---|---|---|---|
| **Q1** | What CI tool is in use — CodePipeline, CodeBuild, GitHub Actions, Jenkins? | **OPEN — genuinely** | *nothing*; see §1 |
| **Q2** | What is the branch strategy? | **ANSWERED** | `memory/org.md` § Way of Working + `memory/team.md` § Way of Working, demonstrated by 8 commits and 2 tags |
| **Q3** | What quality gates are required before merge? | **ANSWERED** | `FR7.2`, `memory/team.md` § Testing Posture, `memory/project.md` mandate Q3, `org.md` § Testing Posture |
| **Q4** | What artifact repositories are used — ECR, CodeArtifact, S3? | **ANSWERED — none** | `memory/team.md` § Deployment: *"no package or image is ever published"* |
| **Q5** | May a hosted CI job bind a loopback socket and start a process? | **OPEN** | *nothing*; see §5 |
| **Q6** | Should the recorded verification command be rewritten to install into a venv? | **OPEN — the human's, explicitly** | `test-results.md` §6, option D **not taken**; see §6 |
| **Q7** | Does the merge require a second human reviewer, given there is one author? | **OPEN** | *nothing*; see §7 |

**What is deliberately not asked.** No question about deployment strategy
(blue-green / canary / rolling) — `memory/team.md` § Deployment: there is no
deployment to strategy, and `u1`'s Infrastructure Design §1 already recorded that
disposition per-concern. No question about promotion gates — there are no
environments to promote between. No question about coverage thresholds — the 80 %
floor is affirmed and stated twice. No question about branch age, batch size or
merge cadence — *"No maximum branch age has ever been affirmed and we are not
inventing one."* Re-asking any of these would be re-litigating a recorded decision.

---

## 1. Q1 — What CI tool is in use?

**Status: OPEN. This is the one genuinely unanswered question among the four, and
it is open because the repository says nothing about it.**

### 1.1 What the evidence settles

| Probe | Result |
|---|---|
| `git remote -v` | **empty — no output** |
| `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`, `.circleci/`, `azure-pipelines.yml` | **none exist** |
| `.pre-commit-config.yaml`, `Makefile`, `tox.ini`, `noxfile.py`, `justfile` | **none exist** |
| Any hosted account, runner, or provider credential referenced by the tree | **none** |
| `memory/team.md` § Way of Working: *"There is still no second human reviewer, and still no remote. `git remote -v` returns empty — no remote, no pull requests, no review comments."* | confirmed, still current |

### 1.2 Why the answer is not "GitHub Actions" or "CodePipeline"

The stage definition names four candidates. **None of the four can be inferred, and
two of the four are refuted:**

* **GitHub Actions, Jenkins, CircleCI, Azure Pipelines** — all four require a
  **hosted repository with a remote** to receive a push. With `git remote -v` empty,
  all four are *equally* unexecutable and equally unevidenced. Writing a GitHub
  workflow today would be choosing by habit, not by evidence.
* **AWS CodePipeline / CodeBuild** — additionally refuted by the project's own
  constraints, independent of the absent remote. `memory/project.md` `## Forbidden`
  (affirmed 2026-10-01, `C-5`): *"NEVER introduce a new external service, hosted
  dependency, cloud component or network call to compute anything for this app."*
  `memory/team.md` § Deployment: *"No container, no hosted service, no IaC."*
  AWS CodePipeline is a hosted external service. Adopting it would be a change to
  the project's trust model that needs a fresh threat model, not a CI decision.

### 1.3 The question underneath the question

**Every provider option is blocked by one and the same fact: there is no git
remote.** This narrows the decision enormously and is worth stating plainly, because
it means the CI-tool question is downstream of a repository-hosting decision that
has not been made:

> Adding a hosted runner — of any vendor — requires first deciding to put this
> repository somewhere hosted at all. **No provider is the right answer to the
> question that is actually being asked**, which is *where should this repository
> live?*

### 1.4 Options, impact-estimated

| Option | What it means | Impact |
|---|---|---|
| **A. Defer — no provider chosen** | The pipeline stays Tier 0 (§ `ci-config.md` §2): the nine jobs and their exact commands, executable by a human today, with the provider adapter left as a worked example. | **Effort:** zero beyond this stage. **Cost:** £0. **Risk:** the moment a remote is created under time pressure, someone designs the adapter from scratch instead of transcribing it. **Reversibility:** total — `ci-config.md` §8 is already the transcription. |
| **B. Create a hosted remote now, provider chosen with it** | Decide where the repository lives; the provider follows from that decision; land `u4`'s script; then promote the adapter. | **Effort:** an account, a push, and `u4`'s `FR7.2` deliverable. **Cost:** £0 in tooling. **Risk:** hosting this tree means hosting the AI-DLC record — including the per-clone audit shards — which is a decision about *where the team's workflow history lives*, not only about CI. It should be made deliberately. **Reversibility:** a repository can be migrated, but the audit shards' per-clone identity would need care. |
| **C. Self-hosted runner on the existing machine** | A runner daemon on the Arch host. | **Effort:** moderate, and it makes the developer machine a piece of CI infrastructure. **Cost:** the runner inherits this host's PEP 668 externally-managed interpreter and its `APPIMAGE` environment variable — which `ci-config.md` §4.0 handles with a prefix. **Risk: HIGH and disqualifying** — `memory/team.md` § Deployment's constraint is that the app is localhost-only and the operator's API key lives on that machine. A CI daemon there is a standing process next to the secret. **Reversibility:** poor. |
| **D. Never host; keep gates on the verification script** | Accept option A permanently. `FR7.2`'s script *is* the gate, run by a human before every squash-merge. | **Effort:** `u4`'s existing scope. **Cost:** £0. **Risk:** every gate stays a human action, so a gate that is skipped is not detected by anything. **Reversibility:** total. |

**What this stage recommends, and how firmly.** The decision is the human's and
this stage takes **no position on where the repository should live.** What it does
record is that **A and D are indistinguishable today** (both mean "no remote yet"),
and that the sequencing any option needs is the same: `u4-platform-packaging` lands
`FR7.2`'s script first, and the provider adapter becomes a transcription rather than
a design.

---

## 2. Q2 — What is the branch strategy?

**Status: ANSWERED from two affirmed layers and two completed executions. This is
not an open question and is not re-opened here.**

### 2.1 The answer

**Trunk-based development on `main`. One branch per intent or scope. Squash-merge
into `main` as a single commit. Tag that commit with the scope name.**

### 2.2 Sources, in resolution order

| Layer | Source | What it says |
|---|---|---|
| `org.md` (broadest) | `## Way of Working` | *"We use **trunk-based development**. All work merges to `main` via short-lived feature branches (typically resolved within 1-2 days)."* · *"For Construction worktrees, the worktree base branch is `main` and the merge target is `main`."* · *"If our project requires multiple environments (staging, production), we still keep one trunk and gate releases via tags or environment-specific deployment configs — not via long-lived release branches."* · *"We **squash-merge** Bolt branches into `main`. Each Bolt becomes one commit on the trunk, named by the Bolt slug."* |
| `team.md` (team specialisation) | `## Way of Working` | *"**We work one branch per intent or scope, squash it into `main` as a single commit, and tag that commit with the scope name.**"* Affirmed 2026-09-30. |
| `team.md` (same section) | evidence table | `v1-classic` → `4eb9b74` (annotated tag `v1-classic`); `express` → `beeb587` (annotated tag `express`). `git branch --list` returns only `main` — *"no surviving feature branch, no merge commit and no third commit — so 'one branch per scope, squashed' is what actually happened, twice."* |

`team.md` is a strict-additive specialisation of `org.md` and does not contradict
it: one trunk, short-lived branches, squash-merge. **Two layers agree and two
completed executions demonstrate it.**

### 2.3 What this implies for the pipeline, concretely

| Implication | Where it lands in `ci-config.md` |
|---|---|
| The gate runs on `main`, not on a release branch | §5, push trigger |
| There is no release branch to protect, so there is nothing to branch-protect except `main` itself | §5, pull-request trigger |
| **The release unit is the annotated tag**, not a commit — so a tag-triggered pipeline has nothing to build, sign or publish | §5, tag trigger, and the reasoning for giving it **no job** |
| Squash-merge means `main` holds one commit per Bolt, so **the audit log — not the git history — is the provenance record**. `org.md` accepts the loss of intermediate commits on that basis: *"the audit log preserves the full event sequence anyway."* | §10 |
| The commit messages are shaped: `<scope>: <summary> (<scope> scope)`, a body ending in the measured result, and the trailer `Produced by the AI-DLC <scope> workflow for intent <id>.` (`memory/project.md` `## Mandated`, affirmed 2026-10-02, Q1) | not a pipeline concern — no commit-message lint is designed, and none is proposed |
| **A current observation, stated so nobody calls it drift**: the `feature` scope has **6 commits and no tag** (`17acbb5`, `aad7494`, `3d405e5`, `9c005e9`, `b2c49bd`, `aa0b1e4`) — one per completed stage, Bolt 1 of 4. That is **consistent with the rule**, not a violation: the rule is one commit per *scope*, and this scope is not finished. The consequence for the pipeline is that a push-to-`main` gate fires **six times** on this scope's internal commits, none of which is a release — which is the correct behaviour for a gate meant to catch an unverified commit, and precisely why the release unit is the tag. | §5, §10 |

### 2.4 One sub-answer the team explicitly declined to give

**There is no maximum branch age.** `team.md` § Way of Working: *"**No maximum
branch age has ever been affirmed and we are not inventing one.** No
commit-signature or co-author expectation exists either."* `ci-config.md` §5
therefore designs **no `schedule` trigger** — a nightly job failing on a stale
branch would invent exactly the age limit that was not affirmed.

---

## 3. Q3 — What quality gates are required before merge?

**Status: ANSWERED from evidence, including which gate blocks what. The full
definitions and their instruments are in `quality-gates.md`.**

### 3.1 The answer

**Fourteen blocking gates, in nine jobs, all traceable to a command Build and Test
executed and recorded — plus the standing verification command itself, which is the
human-facing form of the same gate set.**

| Gate | Instrument | Threshold | Measured |
|---|---|---|---|
| G1 compile | `python -m compileall -q app tests` | exit 0 | exit 0 |
| G2 lint | `python -m ruff check app tests` | **zero** findings | *All checks passed!* |
| G3 format | `python -m ruff format --check app tests` | **zero** files to reformat | *30 files already formatted* |
| G4 test suite | `python -m pytest -q` | 192 passed / 0 failed / **0 skipped** / 0 errors / 0 warnings | 192 passed |
| G5 coverage floor | the same command | **≥ 80 %** of `source = ["app"]`, stated twice in `pyproject.toml` | **97.06 %** (884 stmts / 26 missed) |
| G6 warnings-as-errors | the same command (`filterwarnings = ["error"]`) | **0** warnings | 0 |
| G7 assembly smoke | `python -c "import app.main …"` | exit 0 **and** `['/v2/analytics/summary', '/v2/analytics/terms']` | exactly that |
| G8 runtime smoke | the recorded command's step 3, verbatim | exit 0 and `{"mode":"offline",…}` | exit 0 |
| G9 static security | `tools/security_static_checks.py` | `STATIC CHECKS PASSED`, exit 0 | passed — **but the file is not in the repository** |
| G10 DAST probe | `tools/security_dast_probe.py` | `DAST PROBE PASSED`, exit 0 | passed — **but the file is not in the repository** |
| G11 dependency cap | `tests/test_config.py::test_the_manifest_declares_two_runtime_dependencies_and_the_dev_tools` | exit 0 | green |
| G12 loopback enforcement | `tests/test_routes.py::test_the_server_binds_loopback_only` | exit 0 | green |
| G13 offline guard | `tests/test_analytics_routes.py::test_the_analytics_endpoints_are_proved_offline_by_an_armed_guard` | exit 0 | green |
| G14 latency budget | `tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget` | **< 200 ms** per endpoint | 15.24 ms / 25.04 ms |

### 3.2 Sources

| Source | What it fixes |
|---|---|
| **`FR7.2`** (`requirements.md`) | *"A platform-neutral verification script ships, and it is what runs the standing gates — the 80 % whole-application line-coverage floor, the warnings-as-errors filter and the pinned `ruff` rule set. **It is neither a pre-commit hook nor a provider CI job.**"* — This is the load-bearing sentence. It fixes both the gate **set** and the **shape** of what runs it. |
| `memory/team.md` § Testing Posture, *"Where the gates run — decided 2026-10-02"* | *"The three gates — the whole-application 80 % coverage floor, the warnings-as-errors filter, and the pinned `ruff` rule set — run from a platform-neutral verification script (or make target) that the developer runs. **Not a pre-commit hook. Not a provider CI job. Both rejected by name.**"* And the reason, which is still exactly right: *"`git remote -v` is empty and there is no CI provider of any kind. A provider workflow file written today would be a file that has never executed and cannot execute until a remote exists. A pre-commit hook is real and local, but it never sees a dependency bump and never runs in CI, so it cannot be the whole gate."* |
| `memory/project.md` `## Mandated` (affirmed 2026-10-02, Q3) | *"ALWAYS run the standing gates … from a platform-neutral verification script that the developer runs. A pre-commit hook does not replace it and a provider CI job does not replace it."* |
| `memory/org.md` § Testing Posture | For `feature`: *"add an 80 % line-coverage floor and **CI execution before merge**."* — the scope-level requirement CI execution answers. Note the narrowness: it asks for **CI execution**, not for CI *to be the enforcement mechanism*. |
| `memory/org.md` § Code Style | *"Linter: ESLint, Ruff, … Run in CI before merge; **failure blocks the PR**."* — G2's block-on-merge provenance. |
| `memory/team.md` § Testing Posture | The standing verification command: *"**install**, **run `pytest`**, then **start the app locally and exercise the changed path**"* — which is J1, J6 and J9. |
| `test-results.md` §2.1, §2.4, §4; `build-and-test-summary.md` §1.1 | Every measured result in the table above |

### 3.3 The two gates that cannot run today, named rather than dropped

**G9 and G10 are real, measured and proved — and their instruments are not in the
repository.** Both exist only as heredocs inside
`security-test-instructions.md` §3.1 and §3.2. Landing them is
**`u4-platform-packaging`**'s, under `FR7.2`'s script and `FR7.3`'s secret scan.
`ci-config.md` §4.7–§4.8 specify the jobs and commands; they do not re-author the
scripts, because writing them here would create two sources of truth that can drift.

### 3.4 The gate that is **refused**

**"Coverage did not decrease."** This is *the first gate of the standard quality-gate
set* by `team.md`'s own account, and it is **unbuildable today**: `pyproject.toml`
configures **no machine-readable output at all** — `-q` prints dots and no test
names, `--cov-report=term-missing` is a human table, and there is no `--junit-xml`,
no coverage XML and no `-ra`. With no coverage artefact there is nothing to diff
against the previous run. `team.md` § Testing Posture: *"That is the first gate of
the standard quality-gate set and it is currently unbuildable."*

Recorded as **cannot-be-built**, not as "considered and not needed". The fix is a
`pyproject.toml` configuration change (`--cov-report=xml`) plus a diff step — **no
new dependency**, so it stays inside the two-package cap. Named in
`quality-gates.md` §5 with its owner; **not proposed as work in this stage**, because
the recorded method for changing this repository's test configuration is Code
Generation and the packaging unit, not a pipeline design.

---

## 4. Q4 — What artifact repositories are used — ECR, CodeArtifact, S3?

**Status: ANSWERED: none. The answer is fixed by an affirmed practice and by the
absence of any publishable artifact, and it is answered by *negation* rather than by
choice.**

### 4.1 The answer

**No artifact repository of any kind exists, and none is planned.** The released
artifact is **the git commit**, identified by an **annotated tag named after the
scope**.

### 4.2 Sources

| Source | The sentence that settles it |
|---|---|
| `memory/team.md` § Deployment | *"**Deployment is a localhost checkout, and a commit is the release.** … The released artifact is the squashed commit tagged with the scope name (see `## Way of Working`); the version stays `0.1.0`, the install is **editable**, and **no package or image is ever published**."* |
| `memory/team.md` § Deployment | *"The framework default — deploy on merge to staging behind a manual production gate — has no counterpart here, because the environments it assumes do not exist."* |
| `memory/team.md` § Way of Working | *"…squash it into `main` as a single commit, and **tag that commit with the scope name**."* |
| `u1`'s Infrastructure Design `cicd-pipeline.md` §1 | Artifact management / registry: **"None. No package or image is ever published."** · Deployment strategy: **"None. There is no deployment to strategy."** · Environment promotion: **"None."** · Rollback: **"None to write… recovery is stop the process, delete or restore the local file, check out the previous commit."** |
| `inception/requirements-analysis/requirements.md` | The whole of `FR7` is *repository* obligations — a lockfile, a verification script, a licence, lint config, README. **There is no publish requirement anywhere in the requirement set.** A project with a packaging unit and no packaging requirement is the cleanest available proof that nothing is published. |
| `memory/project.md` `## Forbidden` (`C-5`) | *"NEVER introduce a new external service, hosted dependency, cloud component…"* — ECR, CodeArtifact, PyPI and a container registry are all external services. |

### 4.3 What plays the role instead, concretely

| Concern the question is really asking | The answer here |
|---|---|
| Where is the released artifact? | **the git commit**, reached through an annotated tag: `v1-classic` → `4eb9b74`, `express` → `beeb587` |
| What is its version? | `0.1.0` in `pyproject.toml`, and it stays there — the version does not move per release |
| What is its provenance? | the tag names the scope; the commit body ends in the measured result; the trailer is `Produced by the AI-DLC <scope> workflow for intent <id>.`; and the **full event sequence** is in the version-controlled audit shard `aidlc/spaces/default/intents/261001-analytics-layer/audit/verycool-96b70e2019ac.md`. `org.md` relies on exactly this: *"the audit log preserves the full event sequence anyway."* |
| What would a CI adapter upload? | Currently **nothing in machine-readable form**: test output is dots on stdout, coverage is a human table. The first upload that becomes possible is a coverage XML, and that needs the `pyproject.toml` change §3.4 names. |
| What is the rollback? | *"stop the process, delete or restore the local file, and check out the previous commit"* (`team.md`). A rollback is a `git checkout`. There is nothing to roll back *to* because nothing was promoted *from* anything. |

---

## 5. Q5 — May a hosted CI job bind a loopback socket and start a process?

**Status: OPEN. This is a policy the team has never affirmed, and the pipeline
depends on it for four of its nine jobs.**

### 5.1 Why it is a real question

`memory/team.md` § Deployment draws the line, and the line is precise:

> *"One constraint that decides what a future job may do: a **code-only** job
> (install → lint → `pytest`) is topology-neutral and safe under the
> localhost-only rule; anything that binds a non-loopback interface or needs a live
> credential is not."*

`ci-config.md` respects the letter of that rule — **no job in the design binds a
non-loopback interface, and no job needs a live credential**. But the rule does not
settle the question, because a **hosted runner is itself someone else's machine**.
"Loopback" on a hosted runner means loopback inside a VM the provider controls, on
a network the provider owns, on hardware the team does not administer.

That matters concretely for four jobs:

| Job | What it starts | Without permission |
|---|---|---|
| J8 DAST probe | real `uvicorn` on `127.0.0.1:8142` | **G10 cannot be automated.** It stays a local-only instrument forever. |
| J9 runtime smoke | real `uvicorn` on `127.0.0.1:8141` | **G8 cannot be automated.** The most important "does it actually run" gate becomes a human-only gate. |
| J5 assemble smoke | no socket; imports only | fine |
| J6 test suite | no socket — the session-scoped `offline_guard` **replaces `socket.socket.connect` with a raiser**, so the suite *cannot* open one even if it tried (G13 proves the guard is armed) | fine |
| J7 static security | no socket; `ast` parsing only | fine |

**So the question is narrow and worth answering: is 5 of 14 gates automatable, or
9?** A "no" is a perfectly workable answer — it means the verification script stays
the primary gate, exactly as `FR7.2` intends, and CI automates only the code-only
portion. A "yes" adds nothing except convenience.

### 5.2 Options, impact-estimated

| Option | Impact |
|---|---|
| **A. Code-only jobs on the hosted runner; J8/J9 stay local** | **Effort:** zero — it is the default `ci-config.md` §8 adapter, with J8/J9 moved out. **Cost:** £0. **Risk:** none identified; the split matches `team.md`'s own wording precisely. **Reversibility:** total. **Alignment:** highest with `FR7.2`'s "neither a pre-commit hook nor a provider CI job" — CI becomes an *additional* runner of the code-only gates, never the enforcement mechanism. |
| **B. All nine jobs on the hosted runner, loopback only, no credentials** | **Effort:** minutes. **Cost:** £0. **Risk:** low in principle — no egress, no secret, no non-loopback bind. **Unresolved:** whether the team wants *any* process listening on a provider's machine, which is a trust-boundary statement the project has not made. **Reversibility:** total. |
| **C. No hosted runner at all; the verification script is the whole gate** | **Effort:** `u4`'s existing scope. **Cost:** £0. **Risk:** a skipped gate is undetectable. **Reversibility:** total. This is §1's option D. |

**What this stage recommends.** **A**, for one reason that is not about security:
under A, the standing verification script stays the *primary* gate and CI is
redundant confirmation, which is exactly the relationship `FR7.2` was written to
create. Under B, CI silently becomes the primary gate for eight of the fourteen —
which is a drift toward `org.md`'s framework default that nobody decided on.

**The decision is the human's.** It is recorded, not taken.

---

## 6. Q6 — Should the recorded verification command be rewritten to install into a venv?

**Status: OPEN — and it is explicitly the human's, because Build and Test already
put it to them and the human declined.**

### 6.1 The recorded artifact

`aidlc/spaces/default/intents/261001-analytics-layer/verification-command.txt`:

```bash
python -m pip install -e ".[dev]" && python -m pytest -q && python -c "import threading,time,urllib.request,uvicorn; from app.main import app as a; threading.Thread(target=uvicorn.run, args=(a,), kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'}, daemon=True).start(); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"
```

### 6.2 The measured failure

**Step 1 exits 1** on an externally-managed interpreter (PEP 668, Arch's
`/usr/bin/python3.14`). Steps 2 and 3 **pass verbatim** — 192 passed / 97.06 %,
then `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}`.

**Proven pre-existing**: the identical command fails identically on a pristine
clone of `HEAD` `aa0b1e4` with none of this Unit's writes present. The baseline would
have failed the same way. Both remedies were executed and both succeed: a venv
(**exit 0**, suite green inside it) and `--break-system-packages` (**exit 0** on a
dry run — every dependency already satisfied, so the block is purely the write
refusal).

### 6.3 Why it is still open despite a working remedy existing

Build and Test walked its failure ladder and reached rung 4. Its option D was:

> *"Rewrite the recorded verification command to install into a venv, so step 1 stops
> failing on externally-managed hosts. **Impact: minutes, £0, fully reversible — but
> it edits a human-approved Delivery Planning artifact, so it needs your approval.**"*

**The human chose option A** (accept the two `Unverified` targets) and **option D was
not taken.** `test-results.md` §6, Halt-and-ask resolution: *"Option D remains open
and undone: the recorded verification command still fails its first step on
externally-managed hosts. That is recorded in `build-instructions.md` with the venv
remedy and its evidence, and it is **not** treated as a pass."*

### 6.4 What this stage did about it, precisely

**`ci-config.md` uses the working venv form in J1 and does not touch the recorded
artifact.** Those are different files with different owners: the pipeline design is
this stage's; `verification-command.txt` is a human-approved Delivery Planning
artifact. The pipeline is specified against what *works*, and the divergence is
recorded here so a reader comparing J1 to the recorded command sees a deliberate
difference rather than an error.

**This is a divergence between two artifacts, not a rewrite of one.** It is also the
only place in this stage where the design departs from a human-approved instruction,
so it is stated in all three of `ci-config.md` §4.1, `quality-gates.md` §1.2 (P5),
and here.

### 6.5 The options

| Option | Impact |
|---|---|
| **A. Rewrite the recorded command's step 1 to `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"`** | **Effort:** minutes. **Cost:** £0. **Risk:** low; it edits an approved artifact, which is the whole reason it needs the human. **Reversibility:** total. **Benefit:** the recorded command stops failing on every externally-managed host, permanently, and `u4`'s `FR7.2` script inherits the fix rather than encoding a workaround. |
| **B. Leave it, and keep documenting the remedy in `build-instructions.md` §2.3** | **Effort:** zero. **Cost:** every future host that is externally-managed sees a red first step in a document that is presented as *the* verification command, and the person running it has to know the remedy exists. **Risk:** the failure reads as a repository defect rather than an interpreter policy. **Status quo — Build and Test's recorded state.** |
| **C. Leave it and add a host-precondition line** (e.g. *"step 1 requires a non-externally-managed interpreter, or use the venv remedy"*) | **Effort:** minutes. **Cost:** £0. **Risk:** documentation of a defect where a fix is available; `phases/construction.md`'s error-handling rule prefers *fail fast* to a silent degradation, and a note beside a failing step is neither. |

**This stage takes no position and does not re-ask Build and Test's halt-and-ask.**
It is surfaced because `ci-config.md` §4.1's J1 depends on the answer's shape.

---

## 7. Q7 — Does the merge require a second human reviewer?

**Status: OPEN, and it is open because there is nobody to review.**

### 7.1 The evidence

| Source | What it records |
|---|---|
| `memory/team.md` § Way of Working | *"one author, no co-authors, no merges, and therefore **no second human reviewer**."* `git log --format='%an <%ae>' \| sort -u` returns exactly one line. |
| `memory/team.md` § Way of Working | *"review-before-land is self-review plus agent review"* |
| `memory/team.md` § Way of Working | *"`git remote -v` returns empty — no remote, no pull requests, no review comments. **Nothing in the repository implies a review step.**"* |
| `memory/team.md` § Way of Working | *"the feasibility register records the same constraint from this run's interview (`C-7`: **stage reviews are advisory**; review-before-land is self-review plus agent review), and this scope's guard policy is `relaxed`."* |

### 7.2 Why it is a pipeline question and not a people question

With one author and no remote, a pull request has exactly one participant. A
required reviewer would be unsatisfiable, which either blocks every merge forever or
gets waived every time — a gate that is always bypassed is worse than no gate.

`org.md`'s framework default (*"Production deploys gate on a separate manual
approval — typically tech lead + product owner sign-off"*) is already overridden by
`team.md` § Deployment: those environments *"do not exist."* There is no production
to gate, and no second person to press the button.

### 7.3 Options, impact-estimated

| Option | Impact |
|---|---|
| **A. No human review gate; the 14 automated gates are the merge condition** | **Effort:** zero. **Cost:** £0. **Risk:** the merge condition is exactly as strong as the weakest gate, and today two of them (G9, G10) cannot run at all — so the *effective* condition is 12 of 14. **Reversibility:** total. |
| **B. Required reviewer, accepted from the same person** | **Effort:** minutes. **Cost:** a formality that costs a second of ceremony per merge. **Risk:** **worse than A.** A gate that cannot fail teaches the team to dismiss gates, and this project has already recorded that lesson — *"An unrun gate is not a gate."* |
| **C. Agent review as the review gate** | Already the practice (*"self-review plus agent review"*, `C-7`). **Cost:** advisory-only under `relaxed` guard policy, so it cannot block. **Risk:** none; it is the status quo and it is already working. |

**What this stage recommends: A, with C unchanged.** The 14 gates plus the walking-
skeleton checkpoint's explicit human approval are the merge condition; nothing
pretends to be a review that is not one.

---

## 8. Cross-Unit obligations this stage references rather than duplicates

| Obligation | Owning unit | How this stage relates to it |
|---|---|---|
| Verification script running the three standing gates (`FR7.2`) | **`u4-platform-packaging`** | `ci-config.md` §9 names the convergence as the intended destination: when the script lands, J1–J9 become arguments to it. **Not duplicated here.** |
| Secret scanning + dependency audit (`FR7.3`) | **`u4-platform-packaging`** | Not designed as jobs. `quality-gates.md` §5 records their absence and notes the audit is unbuildable **before** the lockfile exists. |
| Lockfile with hashes (`FR7.1`) | **`u4-platform-packaging`** | The pip cache design notes that resolution is not pinned today and that this is *why* the suite's pass/fail state is a function of the resolved dependency set. |
| `ruff TID251` layer boundaries (`FR7.5`) | **`u4-platform-packaging`** | Not a lint gate — the rule set is not configured. G2 runs the rule set that exists; a job invoking a rule that does not exist is a red light with no defect behind it. |
| The two security scripts (G9, G10) | **`u4-platform-packaging`** (as repository files) | Jobs and commands specified; **contents not re-authored.** `quality-gates.md` §4 states the three reasons, the second of which (divergence) is decisive. |
| `NFR4.6`, `NFR4.7` — the two `Unverified` targets | **`u3-analytics-view`** (Bolt 3) | Carried as accepted debt. **No gate is defined for either and none can be** until that Unit ships the second analytics section and the range control. |
| The pipeline itself | **this stage** | `u1`'s Infrastructure Design §3 routed it here explicitly, and that routing is honoured rather than contradicted. |

---

## 9. Position of this stage

**Four questions asked by the stage definition: three answered from evidence with a
named source, one genuinely open.** Three further questions raised because the
evidence left them genuinely open and the pipeline's design depends on the answers.
Seven questions that were **not** asked because the repository has already decided
them — re-asking any of those would be re-litigating a recorded decision, which
`memory/org.md` § Forbidden names as a thing agents must never do.

**No answer in this file was inferred from habit.** The provider is not chosen
because nothing in the repository selects one; the two AWS options are named as
refuted with the rule that refutes them, not as unlikely; the branch strategy is not
guessed because two affirmed layers and two completed executions state it.

**And the boundary this file will not cross:** every gate it names has an instrument
Build and Test actually ran and recorded, and every gate it *cannot* name is
recorded as unbuildable with the reason and an owner. A gate invented to fill a
table would be worse than an empty row, because an empty row can still be audited.