# CI Pipeline Configuration — intent `261001-analytics-layer`

> **Stage:** `ci-pipeline` (construction) · lead `aidlc-pipeline-deploy-agent` ·
> **Scope:** `feature` · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/construction/ci-pipeline`
>
> **Inputs this artifact was derived from** (the stage's declared `consumes`, plus
> the routing decision that brought this work here):
> `construction/u1-analytics-slice/code-generation/code-summary.md` ·
> `construction/build-and-test/build-and-test-summary.md` ·
> `construction/build-and-test/test-results.md` (the stage frontmatter names it
> `build-test-results`) · `construction/build-and-test/build-instructions.md` ·
> the three `build-and-test/*-test-instructions.md` files ·
> `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` ·
> `inception/units-generation/unit-of-work.md` ·
> `aidlc/spaces/default/intents/261001-analytics-layer/verification-command.txt` ·
> the affirmed practices in `memory/org.md`, `memory/team.md`, `memory/project.md`
> and `memory/phases/construction.md`.
>
> **This is a design artifact.** It adds no file to the repository root. Whether a
> workflow file actually lands is `u4-platform-packaging`'s deliverable and a
> human decision, and §1 states why that ordering is not a formality.

---

## 1. The one fact that governs this stage

**This repository has no CI of any kind, and it has no git remote.**

| Probe | Command | Result |
|---|---|---|
| Hosted CI configuration | `ls .github .gitlab-ci.yml Jenkinsfile buildspec.yml .circleci azure-pipelines.yml` | **none of them exist** |
| Other gate tooling | `.pre-commit-config.yaml`, `Makefile`, `tox.ini`, `noxfile.py`, `justfile`, `.semgrep*`, `.bandit` | **none of them exist** |
| Git remote | `git remote -v` | **empty — no output** |
| Branch inventory | `git branch --list` | `* main` only |
| Commit inventory | `git log --oneline \| wc -l` | **8**, HEAD `aa0b1e4` |
| Release tags | `git tag -l` | `v1-classic` → `4eb9b74`, `express` → `beeb587` |

That single fact rules out and defers very different things, and it is worth
separating them, because "we have no CI yet" is not the same statement as "we
cannot design CI".

**What it rules out, immediately and permanently:**

* **Any automatic gate.** A pipeline is a program that runs on an event. There is
  no event source — no push destination, no pull request, no `merge_group`, no
  hosted runner. Every gate in `quality-gates.md` is therefore run **by a human,
  in a terminal**, and *nothing in this repository runs a gate automatically*.
  `memory/team.md` § Enforcement Summary already says this in its own words: *"An
  unrun gate is not a gate; a documented default is not enforcement."*
* **Any deployment pipeline.** `memory/team.md` § Deployment: *"Deployment is a
  localhost checkout, and a commit is the release."* There is one loopback
  `uvicorn` process over one gitignored SQLite file, no container, no hosted
  service, no environment tier, no IaC. A deploy job would have nothing to deploy.
* **Any artifact registry.** *"no package or image is ever published"* — so not ECR,
  not CodeArtifact, not PyPI, not a container registry, not an S3 release bucket.
  §8 resolves what plays that role instead.
* **Any secret in CI.** No job can hold the operator's OpenRouter key, because no
  job exists to hold it. This is also the correct posture, not a gap: `memory/project.md`
  `## Forbidden` forbids committing a credential, and the project mandate forbids
  hosted dependencies outright (`C-5`).

**What it defers, and defers rather than decides:**

* **Which CI tool.** No provider is implied by an absent remote — see
  `ci-pipeline-questions.md` Q1, which is the one genuinely open question this
  stage carries.
* **Every hosted-runner concern**: billing, runner image, secret storage,
  retention, fork-PR policy, `GITHUB_TOKEN` scope. All of them become questions the
  day a remote exists and none of them is answered by writing them down now.
* **Whether a job may bind a socket.** `memory/team.md` § Deployment draws the line
  precisely: *"a **code-only** job (install → lint → `pytest`) is topology-neutral
  and safe under the localhost-only rule; anything that binds a non-loopback
  interface or needs a live credential is not."* This design keeps every job
  **loopback-only and credential-free**, which satisfies that line as written. But
  whether a *hosted* runner may open a loopback listener at all — the runner is
  itself a hosted VM, so "loopback" means "loopback inside someone else's machine"
  — is a policy the team has never affirmed. Recorded as open, not decided.

**What this stage does *not* do, and why that is not evasion.** The unit's
Infrastructure Design read the same facts and routed the pipeline work here rather
than inventing one: *"A provider workflow file written here would be a file that
has **never executed and cannot execute until a remote exists** — the exact argument
the team used on 2026-10-02 when it decided where the gates run."*
(`construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` § 2).
That routing is honoured here: §3–§7 are the design the routing asked for, and §9
names what stays with `u4-platform-packaging`.

---

## 2. Two tiers, and exactly what is executable today

The pipeline is specified in two tiers. The split is not presentational — it is the
difference between a definition that has executed in this repository and one that
has not, and this artifact will not blur it.

| Tier | What it is | Executable today? | Measured here? |
|---|---|---|---|
| **Tier 0 — the job definition** | Nine jobs, each with its exact command string, its ordering, its gates and its preconditions. Provider-neutral: plain POSIX shell over CPython. | **Yes.** Requires a working tree, CPython ≥ 3.11 and network for the first install only. Nothing else. | **Yes — every Tier 0 command was executed in this run** (§4 records the exit code of each) |
| **Tier 1 — the provider adapter** | A complete workflow YAML binding Tier 0 to one concrete runner, plus its trigger set, cache keys and branch-protection mapping. | **No.** Blocked on a git remote existing. Nothing in this repository has ever executed it. | **No.** It cannot be measured without a remote, and this artifact will not claim otherwise |

**Why Tier 0 is a real pipeline and not a wish list.** It is the unit of work a
runner executes, it has a job graph with declared dependencies, and every command in
it is a command Build and Test already ran and recorded. Any future provider
adapter is a transcription of Tier 0 into that provider's YAML dialect — a
mechanical, reviewable step, not a redesign. That is the property that makes the
design worth writing while the remote is absent.

**Why Tier 1 is included at all, given that it cannot run.** Because the stage
definition asks for *"CI pipeline configuration (buildspec.yml, workflow YAML, or
equivalent)"* and a design that stops at Tier 0 would leave the human to invent the
provider binding themselves under time pressure at the moment they create the
remote. §7 gives it as a **worked example** (`actions/checkout`, `setup-python`,
`upload-artifact` — the most common outcome of "add a remote"), explicitly labelled
as a choice this stage has **no evidence for**, so the human can substitute another
provider's dialect without re-deriving the graph.

---

## 3. The job graph

```mermaid
flowchart TD
    J1["J1 · install<br/>venv + pip install -e .[dev]"] --> J2["J2 · compile<br/>compileall app tests"]
    J1 --> J3["J3 · lint<br/>ruff check app tests"]
    J1 --> J4["J4 · format<br/>ruff format --check app tests"]
    J1 --> J5["J5 · assemble smoke<br/>import app.main, read the /v2 routes"]
    J1 --> J6["J6 · test + coverage<br/>pytest -q (whole suite)"]
    J1 --> J7["J7 · static security<br/>ast walker, 6 checks"]
    J1 --> J8["J8 · dynamic probe<br/>40 injection probes vs real uvicorn"]
    J5 --> J9["J9 · runtime smoke<br/>real uvicorn on 127.0.0.1:8141"]
    J1 --> J9
```

Text fallback, because a diagram is not a specification:

1. **J1 install** runs first and everything else depends on it.
2. **J2, J3, J4, J5, J6, J7, J8** then run in **parallel** — they are independent
   of each other. J2/J3/J4 read files; J5 imports; J6 runs the suite; J7 parses;
   J8 boots its own server. No one of them mutates state another reads (every test
   scopes its store to `tmp_path`; `integration-test-instructions.md` §5).
3. **J9 runtime smoke** additionally requires **J5** to have passed, so that a
   process that cannot even import is never booted.

**There is deliberately no sharding.** The whole suite is **1.67 s** and the whole
lint is milliseconds (`test-results.md` §2.1, measured again in this run). Splitting
192 tests across four runners to save 1.2 s would add four checkout/install cycles
to buy a rounding error. This is a measured decision, not an omission.

| Job | Name | Blocking? | Runnable **today**? | Gates it carries |
|---|---|---|---|---|
| J1 | install | **yes** | yes | — (prerequisite; its own failure is the gate) |
| J2 | compile | **yes** | yes | G1 |
| J3 | lint | **yes** | yes | G2 |
| J4 | format | **yes** | yes | G3 |
| J5 | assemble smoke | **yes** | yes | G7 |
| J6 | test + coverage | **yes** | yes | G4, G5, G6, G11, G12, G13, G14 |
| J7 | static security | **yes** | **no — see §4.7** | G9 |
| J8 | dynamic probe | **yes** | **no — see §4.8** | G10 |
| J9 | runtime smoke | **yes** | yes | G8 |

Eight blocking jobs, no advisory ones. The reason there is nothing advisory: every
instrument below has a recorded pass **and** a demonstrated failure mode, so none of
them is advisory in the "might be noisy" sense. Where an instrument's *value* is
disputed — the two `Unverified` NFR targets — that is recorded as an unresolved
finding in the phase-boundary verdict, not converted into a soft gate.

---

## 4. Job specifications — exact commands

Every command below is `bash`, runs from the repository root, and is prefixed
`env -u APPIMAGE`. **The prefix is portable and harmless where `APPIMAGE` is
unset** — verified in this run: `env -u DEFINITELY_NOT_SET_12345 python -c "…"`
exits 0 — so the identical command string works on this host and on a hosted
runner. §4.0 explains why the prefix exists at all.

### 4.0 Why every command carries `env -u APPIMAGE`

The shell exports
`APPIMAGE=/home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage`. CPython
3.14 honours that variable when resolving `sys.executable`, so:

```
$ python -c "import sys; print(sys.executable)"
/home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage
$ env -u APPIMAGE python -c "import sys; print(sys.executable)"
/usr/bin/python
```

`tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget`
spawns `[sys.executable, "-c", scenario, tmp_path]` so the 200 ms budget is measured
in an interpreter with no `pytest` and therefore no `--cov`. Without the prefix that
spawn launches the AppImage, the AppImage rejects `-c`, and the test fails with
`assert 130 == 0` — an environmental failure wearing the costume of a performance
regression. Proof and remedy: `build-instructions.md` § 6; both commands above
re-measured in this run.

This is an **environment-setup fix, not a code change.** No application source file
and no test file was modified to accommodate it. `memory/team.md` § Testing Posture
already records that `u4-platform-packaging`'s verification script should carry the
prefix as part of `FR7.2`; the same applies to every job here.

### 4.1 J1 — install

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

**This is not the recorded verification command's step 1, and the difference is the
whole point.** The recorded command
(`aidlc/spaces/default/intents/261001-analytics-layer/verification-command.txt`)
begins:

```bash
python -m pip install -e ".[dev]" && python -m pytest -q && python -c "…uvicorn on 127.0.0.1:8141…"
```

On this host that first step **fails**:

```
error: externally-managed-environment
× This environment is externally managed
…
note: … You can override this, at the risk of breaking your Python installation … by passing --break-system-packages.
$ echo $?
1
```

`python` resolves to `/usr/bin/python` → `/usr/bin/python3.14`, an Arch
**externally-managed** system interpreter (PEP 668). Build and Test proved this is
**pre-existing**: the identical command fails identically on a pristine clone of
`HEAD` (`aa0b1e4`) with none of this Unit's 17 source and test writes present
(`build-instructions.md` §2.2, `test-results.md` §3.2). The baseline would have
failed the same way.

**The venv form above is Remedy A from that same document**, measured **exit 0**
(`Successfully installed … very-cool-sentiment-analysis-0.1.0`), with the whole
suite green inside it. Re-measured in this run:

| Check | Result |
|---|---|
| `.venv/bin/python -V` | `Python 3.14.7` |
| `.venv/bin/python -m pytest -q` | **192 passed**, `884 stmts / 26 missed / 97.06 %`, floor reached, **exit 0** |

**Remedy B** (`--break-system-packages`) was **not** chosen: it writes into the
operator's interpreter, and a pipeline that mutates the runner's system Python is a
worse default than one that does not. A CI runner is disposable and a developer
machine is not; the same command is right on both, and that is the whole test.

> **This does not rewrite the human-approved verification command.** Option D of
> Build and Test's halt-and-ask was explicitly **not taken**
> (`test-results.md` §6, Halt-and-ask resolution). The pipeline uses the working
> form; the recorded artifact still says what the human approved. Reconciling the
> two is a Delivery Planning decision and is carried as
> `ci-pipeline-questions.md` Q4.

**Network:** this is the **only** step that touches the network. Everything after
J1 is offline by construction — `build-instructions.md` §1 says so, and J6 proves it
(§4.6, G13).

### 4.2 J2 — compile

```bash
.venv/bin/python -m compileall -q app tests
```

**Measured this run: exit 0.** The cheapest proof that every module in `app/` and
`tests/` parses. `build-instructions.md` §4.1.

### 4.3 J3 — lint

```bash
.venv/bin/python -m ruff check app tests
```

**Measured this run: `All checks passed!`, exit 0** (ruff 0.16.9). The rule set is
the pinned, explicitly reviewed selection in `pyproject.toml` —
`["E","F","W","I","N","UP","S","B","C4","SIM"]`, `line-length = 100`,
`target-version = "py311"` — with `S` (the security set) applying **in full to
`app/`**; only `S101`, `S105`, `S106`, `S603`, `S607` are exempted, and only for
`tests/*`. `build-instructions.md` §4.2, `memory/team.md` § Code Style.

Two limits belong beside this gate so a later reader does not mistake it for
coverage of the security set:

* 13 of ruff's 73 `S` rules are **preview-gated** and inactive under a plain
  `select`; all 13 are import-side blacklist checks (`S404` subprocess, `S403`
  pickle, the XML parsers …). The net catches the dangerous **call**, not the
  dangerous **import**.
* For secrets it is narrower than it sounds: **`S105` fires on `SECRET = "…"` and
  does not fire on `API_KEY = "…"`** — and `API_KEY` is the single most likely name
  for this project's one secret. J7's check 6 covers that hole; J3 does not.

### 4.4 J4 — format

```bash
.venv/bin/python -m ruff format --check app tests
```

**Measured this run: `30 files already formatted`, exit 0.**
`build-instructions.md` §4.3. Blocking because the team's formatting decision is
`ruff format` with `quote-style = "double"` and `line-ending = "lf"`, and an
unformatted file is a diff no reviewer asked for.

### 4.5 J5 — assemble smoke

```bash
.venv/bin/python -c "import app.main as m; print(m.app.title, m.v2_router.prefix, [r.path for r in m.v2_router.routes])"
```

**Measured this run:**

```
very-cool-sentiment-analysis /v2 ['/v2/analytics/summary', '/v2/analytics/terms']
```

`build-instructions.md` §4.4 calls it *"the cheapest proof that the build produced a
working application rather than a collection of parsable files"*. Read
`v2_router.routes`, not `app.routes` — this FastAPI version wraps an included router
in an object with no `.path`.

### 4.6 J6 — test + coverage

```bash
.venv/bin/python -m pytest -q
```

**Measured this run, twice (host interpreter and the J1 venv): `192 passed`, 0
failed, 0 skipped, 0 errors, 0 warnings, 1.67 s, `884 stmts / 26 missed / 97.06 %`,
`Required test coverage of 80% reached`, exit 0.**

This one command carries **seven of the fourteen defined gates** (G4, G5, G6, G11,
G12, G13, G14). That is not gate-stuffing; it is what `pyproject.toml` does:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --cov=app --cov-report=term-missing --cov-fail-under=80"
filterwarnings = ["error"]

[tool.coverage.run]
source = ["app"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

Four separate properties are enforced by that single invocation, and each is
independently observable:

| Property | Mechanism | Today |
|---|---|---|
| The suite passes | pytest exit code | **192 passed** |
| Whole-application line coverage ≥ 80 % | `--cov-fail-under=80` **and** `fail_under = 80` — stated twice so it cannot be skipped by forgetting a flag | **97.06 %** (884 / 858 covered), 17.06 points of headroom |
| Zero warnings of any kind | `filterwarnings = ["error"]` | **0** warnings |
| The suite never touches the network | session-scoped autouse `offline_guard` replaces `socket.socket.connect` with a raiser | proved armed by its own test |

**Two properties the exit code does *not* report**, both stated because the team
recorded them and a pipeline that hides them would be worse than the current state:

* **Skip count is 0 today, and that is a measurement, not a guarantee.** The suite
  contains exactly one `pytest.skip` guard —
  `tests/test_config.py:166`, `pytest.skip("git is not available on this machine")`
  — and there is no `skipif` and no `xfail` anywhere. On any runner with `git` on
  `PATH` it does not fire. See §6 for the precondition that guarantees this.
* **The coverage floor is a whole-suite property.** `addopts` applies it to *every*
  invocation, so a partial run exits 1 with `Required test coverage of 80% not
  reached` even when nothing failed. Two upstream commands therefore carry explicit
  opt-outs, and both are recorded residuals rather than silent relaxations:
  `unit-test-instructions.md`'s scoped command carries `--cov-fail-under=0` (measured
  67 passed / 66 % / exit 0), and `integration-test-instructions.md` §2.2's
  four-file selection carries `--no-cov` (measured 53 tests / exit 0). **Neither is
  used as a gate in this pipeline** — J6 always runs the whole suite. They are
  recorded here so a future adapter does not reach for them to make a red job green.

### 4.7 J7 — static security

```bash
.venv/bin/python <repository>/tools/security_static_checks.py
```

Six stdlib-`ast` checks: (1) zero egress from the analytics read path against a
12-module denylist; (2+3) every `execute`/`executemany` passes bound parameters and
no statement text is built at call time; (4) every DML literal carries a `?`;
(5) no `print()` anywhere in `app/`; (6) no hardcoded credential literal.

**Measured by Build and Test: `STATIC CHECKS PASSED`, exit 0** — 9 execute call
sites all parameter-bound, 0 statement texts built at call time, 16 DML literals with
0 failures in the read path, 0 `print()` across 15 modules, 0 credential literals
across 7 credential-shaped identifiers. **And proved to have teeth:** against a
deliberately broken copy of `app/` the same script reports `STATIC CHECKS FAILED`
with exactly 5 named findings (`security-test-instructions.md` §3.1).

> **This job is NOT runnable today, and the reason is a missing file, not a missing
> command.** The script exists only as a heredoc **inside an artifact**
> (`security-test-instructions.md` §3.1). It has never been committed to the
> repository, so there is nothing for any job — human or hosted — to invoke. Landing
> it as a repository file belongs with the packaging obligations (`FR7.2`'s
> verification script; its check 6 overlaps `FR7.3`'s secret scan), which
> `unit-of-work.md` assigns to **`u4-platform-packaging`**. This stage specifies the
> job and the command; it does not re-author or duplicate the script.
>
> The command string above is therefore written against a path that does not yet
> exist. It is the *contract*; `u4` supplies the file.

### 4.8 J8 — dynamic security probe

```bash
.venv/bin/python <repository>/tools/security_dast_probe.py
```

Drives 40 injection payloads (2 endpoints × 4 parameters × 5 payloads) plus 5
refusal shapes, the empty-success shapes, a read-only check and a loopback-enforcement
check, against **real `uvicorn` on `127.0.0.1:8142`**.

**Measured by Build and Test: `DAST PROBE PASSED`, exit 0.** 40 probes answered
`422` or `200` and **never a `500`**; 0 hits for `Traceback`, `sqlite3.`,
`OperationalError`, `SQLITE_` across all 40 bodies; 5 × `422` with an envelope of
exactly `{code, message}` naming `query.from` / `query.to` / `query.limit` and both
bounds on an inverted range; empty success is `200`, never a `404`; the row count was
still 1 after 50+ requests; `create_app(host="0.0.0.0")` raised
`NonLoopbackBindError`.

Three properties keep this job inside the affirmed localhost-only rule:

* it binds **`127.0.0.1`** and nothing else — a non-loopback bind is *refused* by
  the application itself, which is the assertion at the end of the probe;
* it constructs `Settings(mode="offline", api_key=None)` — **no credential exists
  in this job**, so no CI secret is needed and none could be leaked;
* it seeds its own `tmp_path` store and never reads `config.local.toml` or
  `data/sentiment.db`.

> **Same missing-file blocker as J7.** The probe is a heredoc inside
> `security-test-instructions.md` §3.2, not a committed file. Same owner
> (`u4-platform-packaging`), same reason: repository tooling.

### 4.9 J9 — runtime smoke

```bash
.venv/bin/python -c "import threading,time,urllib.request,uvicorn; from app.main import app as a; threading.Thread(target=uvicorn.run, args=(a,), kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'}, daemon=True).start(); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"
```

**This is step 3 of the recorded verification command, verbatim.** Build and Test
executed it verbatim and measured **exit 0** with:

```
{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}
```

It is blocking because the team's standing verification command is *"install, run
`pytest`, then start the app locally and exercise the changed path"* — the third
clause is this job — and because the suite itself never starts a server and never
resolves `uvicorn app:app`. `memory/team.md` § Testing Posture.

**The extension this stage adds, and why.** The recorded command stops at
`/v1/health`. For *this intent* the changed path is `/v2/analytics/summary` and
`/v2/analytics/terms`, and `/v1/health` cannot see them. So J9 carries one further
step after the verbatim command, over the same real server on the same loopback
port:

```bash
# exercise the changed path over real HTTP — both /v2 endpoints, plus a refusal
.venv/bin/python -c "import json,urllib.request; [print(p, urllib.request.urlopen('http://127.0.0.1:8141'+p).status) for p in ('/v2/analytics/summary','/v2/analytics/terms')]"
```

This is the `express`-intent localhost-deployment precedent from `memory/team.md` §
Deployment, reduced to its cheapest form: choose a throwaway store, serve the real
`app.main:app` through real `uvicorn` on a loopback port, smoke-test the changed
path over HTTP, stop the process. **It is an extension of the human-approved
command, not a replacement** — the verbatim step still runs and still gates.

**Both `/v2` calls return `200` with an empty series on a fresh store**, which is
the correct answer and not a failure: `NFR4.3` requires a failed request never to
render as a plausible-looking empty result, and an empty population over a fresh
store *is* an empty success (`AC2.4.2`). The refusal shapes are asserted by the
suite (§4.6) and by J8, not here; duplicating 40 injection probes in a shell one-liner
would be ceremony, not coverage.

---

## 5. Triggers

| Trigger | Fires on | Runs | Why, or why not |
|---|---|---|---|
| **push to `main`** | every commit landing on the trunk | the blocking set J1→J9 | `memory/org.md` § Way of Working: trunk-based, all work merges to `main`. A commit that lands unverified is a commit nobody checked. **Currently inoperative: no remote receives a push.** |
| **push to a non-`main` branch** | any topic branch | the blocking set J1→J6 (J7/J8/J9 optional — see below) | `memory/org.md`: *"short-lived feature branches (typically resolved within 1-2 days)"*. Verifying on the branch rather than only at the merge point is what makes a squash-merge safe. **Currently inoperative.** |
| **pull request** | PR opened / synchronised | the same blocking set, as required status checks | `memory/team.md` § Way of Working records **one author and no co-authors**, so there is no second human reviewer; a PR check is therefore the *only* review-shaped signal a merge gate could have. With one author it is close to a formality — see `ci-pipeline-questions.md` Q2. **Currently inoperative.** |
| **tag `<scope-name>`** | the annotated tag `memory/team.md` § Way of Working requires per scope | **no job** | The tag *is* the release. `express` → `beeb587` and `v1-classic` → `4eb9b74` are the two completed executions. There is nothing to build, sign, publish or promote, so a tag-triggered job would be a no-op dressed as a pipeline. **Currently inoperative.** |
| **`schedule` (cron)** | — | **none, deliberately** | No remote, so no scheduler exists. And even with one: `memory/team.md` records that *"No maximum branch age has ever been affirmed and we are not inventing one."* A nightly job that fails on a stale branch would invent exactly that age limit. **Not designed.** |
| **manual dispatch** | a human presses the button | the blocking set | The only way to re-run the set without pushing a commit — which matters here, because §4.1's install step fails on externally-managed interpreters and re-running is a normal act of verification. **Currently inoperative.** |

**On PR granularity.** With a single deployable and a 1.67 s suite, a PR gate and a
push gate run identical commands on identical code. Both are specified because both
cost the same and one of them is wrong per event; collapsing them is a configuration
choice for whoever creates the remote, and it is recorded here rather than decided.

---

## 6. Preconditions any adapter must honour

These are not style preferences. Each one is a fact about this repository that will
make a job red with a message that reads like something else.

| # | Precondition | Why it exists | If violated |
|---|---|---|---|
| P1 | **The checkout must contain `.git` and `.gitignore`** | `tests/test_config.py::test_local_config_is_gitignored` shells out to `git check-ignore -q config.local.toml` in the repository root | `git check-ignore` exits 128; **1 test fails with a message that reads like a credential leak.** `memory/team.md` § Testing Posture: *"A full source tree copied without `.git` gives 117 passed / 1 failed… Any gate that receives source without `.git` goes red with a message that reads like a credential leak."* Every mainstream provider's checkout includes `.git`, including a shallow clone — so this is satisfied by default, and is recorded because the failure mode is so misleading. |
| P2 | **No test may reach the network** | the session-scoped autouse `offline_guard` replaces `socket.socket.connect` with a raiser, and `tests/test_dummy_client.py` **proves the guard is armed** | Any socket attempt fails the suite with `ConnectionRefusedError`. That is the guard working. `build-instructions.md` §7. |
| P3 | **`git` must be on `PATH`** | the same test as P1; its `shutil.which("git")` guard covers git-*absent* by skipping, but not git-present-but-not-a-checkout | the single `pytest.skip` fires and the skip count becomes 1, silently weakening G4 |
| P4 | **CPython ≥ 3.11** (`requires-python`); measured 3.14.7 | the floor in `pyproject.toml` | an unresolved import or a syntax error at parse time |
| P5 | **Network for J1 only** | no lockfile exists (`FR7.1`, unbuilt) so every install resolves from the index | an air-gapped runner cannot install; see §7 for the mitigation |
| P6 | **No credential is available to any job, and none is needed** | the app's one secret is the operator's OpenRouter key; it is gitignored and never in an artifact | — (this precondition exists so that a future adapter does not *add* a secret; the DAST probe passes `api_key=None`, and every live-mode test injects a fake transport) |

---

## 7. Caching

| Cache | Key | Contents | Worth it? |
|---|---|---|---|
| **pip wheel cache** | `~/.cache/pip`, keyed on the SHA-256 of `pyproject.toml` | downloaded wheels and sdists | **Yes.** Saves download time and index traffic on every run after the first. It does **not** affect resolution: pip's cache is content-addressed, so a cached wheel never changes which version is selected. That is the right property while the lockfile is absent — resolution still hits the index, so a stale resolution cannot be served from cache. **The cost is the inverse: with no `FR7.1` lockfile, two runs on two days can legitimately resolve different versions.** `build-and-test-summary.md` §7.9 measured it: the system `ruff` is 0.16.9 and a fresh venv's is 0.16.10, and the suite passes under both. The pipeline is reproducible *today* by luck of tolerance, not by construction. |
| **ruff cache** | `~/.cache/ruff`, keyed on `pyproject.toml` + `app/**` + `tests/**` | ruff's parse/analysis cache | **Yes**, though the saving is milliseconds at 30 files. Harmless. |
| **`.pytest_cache`** | **not cached** | — | It is per-runner state with no cross-run value; J6 runs with `-p no:cacheprovider` in the measured invocations, so nothing is produced to cache. |
| **the `.venv` itself** | **not cached** | — | **Do not.** A venv is not relocatable: `pyvenv.cfg` and the editable-install pointer in `very_cool_sentiment_analysis.egg-info` embed absolute paths. Copying one between runners yields an importable-looking tree that resolves nothing. Cache the wheels; rebuild the venv. |
| **coverage report** | **cannot be cached** | nothing exists to store | This is the important one. `pyproject.toml` configures **no machine-readable output at all**: `-q` prints dots and no test names, `--cov-report=term-missing` is a human table, and there is **no `--junit-xml`, no coverage XML and no `-ra`**. So there is no coverage artefact to diff against a previous run, and — *"the one that matters most"* — **`"coverage did not decrease" is not expressible as a gate today, because there is no coverage artifact to diff against the previous run. That is the first gate of the standard quality-gate set and it is currently unbuildable.** (`memory/team.md` § Testing Posture, "What the gate cannot yet express".) §8 of `quality-gates.md` records the missing flags and the named owner. |

---

## 8. Provider adapter (Tier 1) — worked example, **not** evidence-backed

> **No provider is selected by this stage, because nothing in the repository
> selects one.** There is no remote, no account, no existing workflow and no team
> tooling. The YAML below is a **mechanical transcription of §3–§4 into one
> provider's dialect**, given as the most likely outcome of "add a remote" so the
> human is not asked to design one under time pressure. Substituting another
> provider's dialect requires re-writing the *syntax* only — the graph, the command
> strings, the ordering and the gate set are unchanged.
>
> **It has never executed. It must not be recorded as if it had.**

```yaml
# .github/workflows/verify.yml — WORKED EXAMPLE. Blocked: this repository has no
# git remote, so nothing can trigger this file. See ci-config.md §1 and §2.
name: verify
on:
  push:
    branches: ["main"]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read          # read-only; no job writes to the repository

concurrency:
  group: verify-${{ github.ref }}
  cancel-in-progress: true

jobs:
  verify:
    runs-on: ubuntu-latest
    # P1/P3: a provider checkout includes .git and .gitignore, so
    # tests/test_config.py::test_local_config_is_gitignored can shell out to
    # `git check-ignore`. Verify by reading the first job's log for 192 passed
    # and 0 skipped.
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.14"     # measured 3.14.7; >= 3.11 is the floor
          cache: pip
          cache-dependency-path: pyproject.toml

      # J1 — §4.1. The venv form, not the recorded command's bare
      # `python -m pip install -e ".[dev]"`, which exits 1 on an
      # externally-managed interpreter (PEP 668). See ci-pipeline-questions.md Q4.
      - name: J1 install
        run: |
          python -m venv .venv
          .venv/bin/python -m pip install -e ".[dev]"

      - name: J2 compile
        run: .venv/bin/python -m compileall -q app tests

      - name: J3 lint
        run: .venv/bin/python -m ruff check app tests

      - name: J4 format
        run: .venv/bin/python -m ruff format --check app tests

      - name: J5 assemble smoke
        run: |
          .venv/bin/python -c "import app.main as m; print(m.app.title, m.v2_router.prefix, [r.path for r in m.v2_router.routes])"

      # J6 — the blocking gate. G4, G5, G6, G11, G12, G13, G14 all live here.
      - name: J6 test + coverage
        run: .venv/bin/python -m pytest -q

      # J7 — §4.7. The script is not committed yet; u4-platform-packaging owns it.
      - name: J7 static security
        run: .venv/bin/python tools/security_static_checks.py
        continue-on-error: false

      # J8 — §4.8. Same missing-file blocker as J7.
      - name: J8 dynamic probe
        run: .venv/bin/python tools/security_dast_probe.py

      # J9 — §4.9. Step 3 of the recorded verification command, verbatim, then the
      # changed path this intent actually added.
      - name: J9 runtime smoke
        run: |
          .venv/bin/python -c "import threading,time,urllib.request,uvicorn; from app.main import app as a; threading.Thread(target=uvicorn.run, args=(a,), kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'}, daemon=True).start(); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"

  # KEEP THIS BLOCK UNCOMMENTED ONLY AFTER u4-platform-packaging COMMITS
  # tools/security_static_checks.py and tools/security_dast_probe.py. Enabling a
  # path that does not exist turns the merge gate red for a reason that has
  # nothing to do with the change under test.
  #
  #   security:
  #     needs: verify
  #     runs-on: ubuntu-latest
  #     steps:
  #       - uses: actions/checkout@v4
  #       - uses: actions/setup-python@v5
  #         with: { python-version: "3.14", cache: pip, cache-dependency-path: pyproject.toml }
  #       - run: python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"
  #       - run: .venv/bin/python tools/security_static_checks.py
  #       - run: .venv/bin/python tools/security_dast_probe.py
```

**Four notes on the adapter, because the shape of a provider file is where an
honest design usually goes wrong:**

1. **`permissions: contents: read`.** No job writes to the repository, so no job
   gets write scope. There is no deployment to deploy and no artefact to publish,
   so this is the whole permission surface.
2. **No secret is declared anywhere in the file.** Not one. The project has one
   real secret, it belongs to the operator's machine, and no job in this pipeline
   needs it — the DAST probe constructs `Settings(mode="offline", api_key=None)` and
   every live-mode test injects a fake transport. **A pipeline that never declares
   a secret cannot leak one.**
3. **J7 and J8 are shown in the blocking job but commented in the sibling job.**
   Their scripts do not exist, so an adapter that enables them today fails for a
   reason unrelated to the change under test. The honest sequence is: land `u4`'s
   files first, then promote them to blocking — which is why the sibling job is
   written but not enabled, rather than omitted.
4. **The file path `.github/workflows/verify.yml` is a proposal, not a write.**
   This stage writes nothing to the repository root. Landing it is `u4`'s
   deliverable under `FR7.2` and a human's decision, and it is only meaningful once
   a remote exists.

---

## 9. What this design deliberately does not do

| Not done | Why |
|---|---|
| **No pre-commit hook** | Affirmed and rejected **by name**, twice: `memory/team.md` § Testing Posture and `memory/project.md` mandate Q3 — *"A pre-commit hook does not replace it and a provider CI job does not replace it; with no git remote, a hosted workflow file is a file that has never run."* `unit-of-work.md` U4 notes: *"The verification script is neither a pre-commit hook nor a provider CI job — there is no remote and no CI provider (FR7.2)."* |
| **No container image, no image build, no registry** | `C-5` forbids a new external service or cloud component; `memory/team.md` § Deployment says no image is ever published. |
| **No deploy job, no environment tiers, no promotion** | There is nothing to promote between. `org.md` § Deployment's *"deploy on merge to staging behind a manual production gate"* has no counterpart — `team.md` overrides it with *"the environments it assumes do not exist."* |
| **No approval gate** | Same reason. There is no staging environment to protect and, per `team.md` § Way of Working, **no second human reviewer** to press approve. |
| **No secret scanner, no dependency audit job** | They do not exist. `FR7.3` is a `u4-platform-packaging` obligation; `team.md` § Deployment lists the absence as *"a decision rather than a capability limitation"* (PyPI is reachable). Designing a job for a tool that is not chosen would be inventing a gate with no instrument behind it. |
| **No coverage-delta gate, no flaky-test gate** | Unbuildable today — §7 explains why, and `quality-gates.md` §8 records the missing flags. |
| **No branch-age gate, no batch size, no velocity metric** | `memory/team.md`: *"No maximum branch age has ever been affirmed and we are not inventing one."* |
| **No `TID251` layer-boundary lint job** | The rule set is not configured (`FR7.5`, unbuilt). J3 runs the rule set that exists; a job invoking a rule that does not exist is a red light with no defect behind it. |
| **No test sharding or parallelism** | 1.67 s. §3. |
| **No code duplicated from `u4-platform-packaging`** | `unit-of-work.md` U4 owns *"the platform-neutral verification script and the three gates it runs"*, *"secret scanning and the dependency audit, invoked from that script"*, the lockfile, and the `TID251` / `target-version` config. When that script lands, **J1–J9 should become arguments to it**, not parallel copies of its body. That convergence is the single most likely future edit to this artifact, and it is recorded here so it is a planned change rather than a discovery. |

---

## 10. Provenance and traceability

| Concern | Where it lives | Traceable? |
|---|---|---|
| The commands in §4 | `build-instructions.md` §4–§6; the three `*-test-instructions.md` files | **Yes** — every one has a recorded exit code |
| The gates in `quality-gates.md` | `test-results.md` §2.1, §2.4, §4; `build-and-test-summary.md` §1.1 | **Yes** — 14 commands, 14 measured results |
| The test totals | `code-summary.md` §3 — 192 passed, 97.06 % | **Yes** |
| Why no pipeline at Unit level | `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` §3 | **Yes** — routed here explicitly |
| Why the gates run from a script | `memory/team.md` § Testing Posture, "Where the gates run — decided 2026-10-02"; `FR7.2` | **Yes** |
| **A released commit's provenance** | **the annotated tag** named after the scope (`v1-classic` → `4eb9b74`, `express` → `beeb587`) | **Yes** — this is the artifact repository (§8 of `quality-gates.md`) |
| **Who did what, in order** | the AI-DLC audit shard `aidlc/spaces/default/intents/261001-analytics-layer/audit/verycool-96b70e2019ac.md`, version-controlled with the tree | **Yes** — `memory/team.md` § Way of Working relies on it: *"the audit log preserves the full event sequence anyway"*, which is the stated reason squash-merge's loss of intermediate commits is acceptable |
| The phase boundary for this pipeline | `aidlc/spaces/default/intents/261001-analytics-layer/verification/phase-check-construction.md` | **Yes — and it is NOT a pass** |

**One fact about commit granularity that the pipeline design has to respect.**
`memory/org.md` § Way of Working: *"We **squash-merge** Bolt branches into `main`.
Each Bolt becomes one commit on the trunk, named by the Bolt slug."*
`memory/team.md` § Way of Working states the same rule at scope granularity: *"one
branch per intent or scope, squash it into `main` as a single commit, and tag that
commit with the scope name."*

The repository's two completed executions match both rules exactly. **The current
`feature` scope has 6 commits and no tag** — `17acbb5`, `aad7494`, `3d405e5`,
`9c005e9`, `b2c49bd`, `aa0b1e4`, one per completed stage, Bolt 1 of 4 — which is
**consistent with the rule, not drift**: the rule is one commit per *scope*, and
this scope is not finished. The consequence for this pipeline is concrete: a
push-to-`main` gate would fire **six times** on this scope's internal commits, none
of which is a release. That is the correct behaviour for a gate whose job is to
catch an unverified commit, and it is exactly why the release unit is the **tag**,
not the commit (§5).

---

## 11. Approval gate

```
# :gear: CI Pipeline Complete
```

**Delivered:** `ci-config.md` (this file) · `quality-gates.md` ·
`ci-pipeline-questions.md` ·
`../verification/phase-check-construction.md`.

**Measured:** 8 blocking jobs specified; **every Tier 0 command executed in this
run** — `compileall` exit 0, `ruff check` *All checks passed!*, `ruff format
--check` *30 files already formatted*, import smoke
`very-cool-sentiment-analysis /v2 ['/v2/analytics/summary', '/v2/analytics/terms']`,
`pytest -q` **192 passed / 97.06 % / exit 0** (host interpreter *and* the J1 venv),
`.venv/bin/python -V` 3.14.7.

**Executable today:** J1–J6 and J9. **Blocked on a missing repository file owned by
`u4-platform-packaging`:** J7, J8. **Blocked on the absent git remote:** the whole
of Tier 1, and therefore every trigger in §5.

**A fail-state finding is attached and is not absorbed:** the cross-Unit FR/NFR/AC
gate **FAILED** and Build and Test's target matrix carries **2 `Unverified`**
targets. The Construction → Operation transition is **stopped** in
`../verification/phase-check-construction.md`, with the owning stage named for each
unresolved item.

### Sensors

| Sensor | Result | Note |
|---|---|---|
| `required-sections` | **passed** — fired on all three outputs | no `memory/templates/*.md` resolves for this stage, so the generic ≥ 2 H2 floor applied; each file exceeds it substantially |
| `upstream-coverage` | **passed** — fired on all three outputs | all three `consumes` targets (`code-summary`, `build-and-test-summary`, `build-test-results`) are cited in each file's provenance header, and the producing directory `construction/build-and-test/` also appears as a path segment |
| `linter` | **INAPPLICABLE — not fired** | its `matches` glob is `**/*.{ts,js}`; this stage produces **markdown design artifacts only**, and the project has **0** `.ts`/`.js`/`.tsx` files in the output directory |
| `type-check` | **INAPPLICABLE — not fired** | its `matches` glob is `**/*.{ts,tsx}`; same reason, and additionally there is **no `tsconfig.json` and no `tsc`** anywhere in this repository |

**On the two inapplicable sensors, stated rather than forced.** Both are
`kind: deterministic`, `fire_on`-gated code-shape sensors whose `matches` patterns
select **TypeScript/JavaScript files**. This stage's three outputs are `.md` design
documents, so neither sensor's glob can select them; firing either would produce a
green tick that no instrument had earned, which is the failure mode
`memory/team.md` warns about — *"An unrun gate is not a gate"* — in its inverted
form. The project is pure Python by affirmed mandate (`memory/project.md`
`## Tech Stack`: *"Build it in Python … overriding the original request's preference
for TypeScript on Bun/Node"*), and `aidlc-state.md` records `Languages: Python`,
`Build System: python (pyproject.toml)`. **The repository's real lint gate is `ruff`,
which this pipeline designs as job J3 / gate G2** — measured `All checks passed!` in
this run.