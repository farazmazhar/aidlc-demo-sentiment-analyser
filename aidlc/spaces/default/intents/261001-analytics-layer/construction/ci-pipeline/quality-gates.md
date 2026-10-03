# Quality Gate Definitions — intent `261001-analytics-layer`

> **Stage:** `ci-pipeline` (construction) · lead `aidlc-pipeline-deploy-agent` ·
> **Companion to:** `ci-config.md` (the jobs these gates run in) ·
> **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/construction/ci-pipeline`
>
> **Every gate below names the command Build and Test actually executed and
> recorded.** The sources are `code-summary.md` (the files created and the measured
> results), `build-and-test-summary.md` (§1.1 command table, §4 target matrix),
> `test-results.md` (§1 build status, §2.1 the gate run, §2.4 non-`pytest` checks,
> §4 coverage), `build-instructions.md` (§4 build commands, §5 verification, §7
> troubleshooting), and the three `*-test-instructions.md` files. **No gate in §2
> has an instrument this stage invented.**
>
> **Nothing here runs automatically.** The repository has no CI and no git remote
> (`ci-config.md` §1), so every gate below is executed by a human, in a terminal,
> from a checkout. §1 states what that costs.

---

## 1. Preconditions, and what "blocking" means today

### 1.1 The gates are not automatic, and calling them gates is a statement about intent

`memory/team.md` § Enforcement Summary: *"An unrun gate is not a gate; a documented
default is not enforcement. Both sentences have been load-bearing in this project."*

So, stated precisely:

| Question | Honest answer |
|---|---|
| Do these gates block a merge today? | **No.** There is no remote, no pull request, no protected branch and no runner. Nothing blocks anything. |
| Do they block a merge once a remote exists? | **Yes** — if the human maps them onto required status checks (`ci-config.md` §5, §8). That mapping is a human decision, and `ci-pipeline-questions.md` Q2 flags the wrinkle: with one author and no co-authors, the *only* review-shaped signal a merge gate can have is the check itself. |
| Are they enforced at all today? | **Yes, by a human and by the standing verification command.** `memory/team.md` § Testing Posture records the standing verification as *"install, run `pytest`, then start the app locally and exercise the changed path"* — which is J1, J6 and J9. Running it *is* running most of this gate set. |
| What is genuinely enforced mechanically, with no human in the loop? | **Nothing.** Recorded so the gap is not read as coverage. |

### 1.2 Conditions every gate inherits

| # | Precondition | If violated |
|---|---|---|
| P1 | The source arrives as a **git working tree** (`.git` + `.gitignore` present) | `tests/test_config.py::test_local_config_is_gitignored` shells out to `git check-ignore -q config.local.toml`; without a checkout it exits 128 and **1 test fails with a message that reads like a credential leak** (`memory/team.md` § Testing Posture) |
| P2 | `git` is on `PATH` | the suite's single `pytest.skip` guard fires and the skip count becomes 1, silently weakening G4 |
| P3 | Every command is prefixed `env -u APPIMAGE` | `G14`'s test fails with `assert 130 == 0` — the AppImage launched with `-c`. **Environmental, not a performance regression.** Measured and explained: `build-instructions.md` §6; re-proved in this run (`python -c "import sys;print(sys.executable)"` → `…AppImage`; `env -u APPIMAGE python -c …` → `/usr/bin/python`) |
| P4 | CPython ≥ 3.11; measured **3.14.7** | parse/import failure |
| P5 | Install is a **venv**, not a bare `pip install -e` | the recorded command's step 1 exits **1** with PEP 668 `externally-managed-environment` on an externally-managed interpreter — proven pre-existing on a pristine clone of `HEAD` `aa0b1e4` (`test-results.md` §3.2) |
| P6 | The install step is the **only** step with network access | see G13, which is the gate that proves the property |

### 1.3 What "blocking" means in the definitions below

| Grade | Meaning |
|---|---|
| **BLOCKING** | A non-zero exit fails the job and, once a remote exists, fails the merge. |
| **BLOCKING (file absent)** | The gate is real and measured, but its instrument is **not in the repository**, so it cannot run today. Named as blocked rather than quietly dropped — see §4. |
| **NOT A GATE** | Recorded because its absence must not read as coverage: unbuildable today, off by affirmed decision, or owned by an unbuilt Unit. §5. |

---

## 2. The gate definitions

Fourteen gates. Every one carries the command that instruments it and the measured
result from Build and Test or from this stage's own re-execution.

### G1 — Every module parses

| | |
|---|---|
| **Command** | `.venv/bin/python -m compileall -q app tests` |
| **Pass** | exit 0 |
| **Fail** | any non-zero exit (a `SyntaxError` names the file and line) |
| **Measured** | **exit 0** — re-measured in this run; also `build-instructions.md` §4.1, `build-and-test-summary.md` §1.1 row 2 |
| **Threshold** | none; the gate is the exit code |
| **Blocks** | the merge |
| **Job** | J2 |
| **Why it earns a slot** | it is the cheapest possible statement that `app/` and `tests/` are syntactically valid Python on this interpreter, and it costs well under a second. It cannot detect a semantic fault — that is what the import smoke (G7) and the suite (G4) are for. |

### G2 — The pinned lint rule set

| | |
|---|---|
| **Command** | `.venv/bin/python -m ruff check app tests` |
| **Pass** | exit 0, `All checks passed!` |
| **Fail** | any diagnostic; exit 1 |
| **Measured** | **`All checks passed!`, exit 0** (ruff 0.16.9) — re-measured in this run; `test-results.md` §1, `build-instructions.md` §4.2 |
| **Threshold** | **zero** findings, across `select = ["E","F","W","I","N","UP","S","B","C4","SIM"]` with `line-length = 100`, `target-version = "py311"` |
| **Blocks** | the merge |
| **Job** | J3 |
| **Configuration** | `pyproject.toml` `[tool.ruff.lint]`, `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls`, `[tool.ruff.lint.per-file-ignores]` — an explicit, reviewed selection rather than a drifting default |
| **Two honest limits** | 13 of ruff's 73 `S` rules are **preview-gated and inactive** under a plain `select` (all import-side blacklist checks: `S404` subprocess, `S403` pickle, the XML parsers…). And **`S105` fires on `SECRET = "…"` but not on `API_KEY = "…"`** — `API_KEY` is this project's one real secret's most likely name. G9's check 6 covers that hole; G2 does not. **Not selected, therefore not caught:** `BLE001` (broad `except Exception:`), `T20` (`print()`), `T10` (`breakpoint()`), `DTZ` (naive `datetime.now()`). |

### G3 — The pinned formatter

| | |
|---|---|
| **Command** | `.venv/bin/python -m ruff format --check app tests` |
| **Pass** | exit 0, `N files already formatted` |
| **Fail** | any file would be reformatted; exit 1 |
| **Measured** | **`30 files already formatted`, exit 0** — re-measured in this run; `test-results.md` §1, `build-instructions.md` §4.3 |
| **Blocks** | the merge |
| **Job** | J4 |
| **Note on the count** | 30 files, not the 24 recorded in `memory/team.md` § Code Style — the tree grew by this Unit's 3 new source and 3 new test files. The gate is the exit code, not the count. |

### G4 — The whole suite passes

| | |
|---|---|
| **Command** | `.venv/bin/python -m pytest -q` |
| **Pass** | exit 0, **192 passed** |
| **Fail** | any failed test, error, or collection error; exit 1 |
| **Measured** | **192 passed, 0 failed, 0 errors, 1.67 s, exit 0** — re-measured in this run on both the host interpreter **and** the J1 venv (a fresh install, no lockfile), reproducing `test-results.md` §2.1 and §2.4 row 4 |
| **Thresholds** | **192 passed / 0 failed / 0 skipped / 0 errors / 0 warnings** |
| **Blocks** | the merge |
| **Job** | J6 |
| **Skip count is a measured zero, not a guarantee** | the suite contains exactly **one** `pytest.skip` guard — `tests/test_config.py:166`, `pytest.skip("git is not available on this machine")` — no `skipif`, no `xfail`, and `-ra` reports nothing. It does not fire when `git` is on `PATH` in a real checkout. **If a future adapter ever reports a non-zero skip count, that is P2 failing silently and this gate should be treated as not run.** |
| **This gate is a whole-suite property** | `addopts` applies `--cov-fail-under=80` to *every* invocation, so a partial run exits 1 with `Required test coverage of 80% not reached` even when nothing failed. Two upstream commands carry opt-outs — the scoped per-unit command (`--cov-fail-under=0`, 67 passed / 66 % / exit 0) and the four-file integration selection (`--no-cov`, 53 tests / exit 0). **Neither is used as a gate.** Recorded so nobody reaches for one to make a red job green. |
| **Every module passes standalone** | `team.md` § Testing Posture: all 15 test modules pass standalone, so the suite is order- *and* module-independent. That is the property that makes an automatic gate safe to trust here — and the reason no shard is needed. |

### G5 — Whole-application line-coverage floor

| | |
|---|---|
| **Command** | the **same** `pytest -q` invocation as G4 — the floor is in `addopts` and in `[tool.coverage.report]`, not in a separate step |
| **Pass** | total line coverage of `source = ["app"]` **≥ 80 %** |
| **Fail** | below 80 %; pytest exits 1 with `Required test coverage of 80% not reached` |
| **Measured** | **97.06 %** — 884 statements, 26 missed, **17.06 points of headroom**. `test-results.md` §4 records the full per-module table |
| **Threshold** | **80 %**, stated **twice**: `--cov-fail-under=80` in `addopts` and `fail_under = 80` in `[tool.coverage.report]`. Stated twice so it cannot be skipped by forgetting a flag. `team.md`: *"It is a genuinely enforcing gate, not a printed notice: raising the floor to 99 on the command line makes the run exit 1."* |
| **What is measured** | **the whole application** — `source = ["app"]`, including `app/openrouter_client.py`, the live client the offline suite never imports. The human's coverage answer counts the whole app against the floor, so the live client became construction work rather than the floor passing by excluding it. |
| **Baseline movement** | 96.02 % (679 stmts / 27 missed) before this Unit → **97.06 %** (884 / 26) after |
| **All 26 misses are pre-existing** | `app/session_auth.py:84-120` (17) and `app/openrouter_client.py:89-96` (6) — the two production HTTP transports, untested because the affirmed two-package dependency cap forbids an HTTP client library, so every test injects a transport or exchanger. Plus `app/routes.py:257-258` (the `/v1` bulk-import `csv.Error` branch) and `app/main.py:103`. **None is in a module this Unit created**; `analytics.py`, `terms.py`, `db.py`, `models.py` all read 100 %. |
| **Branch coverage is off, by affirmed decision** | `team.md` (2026-10-02): 98 branches, 3 partial (`app/db.py:208`, `app/main.py:49`, `app/routes.py:385->387`), **none visible to a line floor**. The decision stands; the cost is recorded. Not turned on, not weakened. |

### G6 — Warnings-as-errors

| | |
|---|---|
| **Command** | the **same** `pytest -q` invocation — `filterwarnings = ["error"]` in `[tool.pytest.ini_options]` |
| **Pass** | **0 warnings** |
| **Fail** | **any** warning from **any** source; the run fails |
| **Measured** | **0 warnings** — `test-results.md` §2.1 |
| **Blocks** | the merge |
| **Why it is stricter than it sounds** | `team.md` § Testing Posture corrects an earlier over-narrow description of this: it does **not** merely catch a FastAPI or pydantic deprecation. It promotes **every** warning from **every** source — pytest's own deprecations, a transitive `DeprecationWarning`, a `ResourceWarning`. |
| **And why that is a risk, recorded not hidden** | there is **no lockfile**, so the installed toolchain sits two major versions past every declared floor (`pytest 9.1.1` against `>=8`, `pytest-cov 7.1.0` against `>=5`, `starlette 1.7.0`, `pydantic 2.13.5`). **The suite's pass/fail state is therefore a function of the resolved dependency set, not of the code.** A fresh `pip install -e ".[dev]"` on any other machine resolves something different. That is the single strongest technical argument for the lockfile decided under `memory/team.md` § Deployment, and G6 is where it bites first. |

### G7 — The application assembles

| | |
|---|---|
| **Command** | `.venv/bin/python -c "import app.main as m; print(m.app.title, m.v2_router.prefix, [r.path for r in m.v2_router.routes])"` |
| **Pass** | exit 0 and the route list is `['/v2/analytics/summary', '/v2/analytics/terms']` on prefix `/v2` |
| **Fail** | non-zero exit (import error, circular import, a missing module) **or** a changed/empty route list |
| **Measured** | `very-cool-sentiment-analysis /v2 ['/v2/analytics/summary', '/v2/analytics/terms']`, exit 0 — re-measured in this run; `build-instructions.md` §4.4 |
| **Blocks** | the merge |
| **Job** | J5 |
| **Why the route list is part of the assertion** | `build-instructions.md`: *"It is the cheapest proof that the build produced a working application rather than a collection of parsable files."* Read **`v2_router.routes`**, not `app.routes` — this FastAPI version wraps an included router in an object with no `.path`. An empty or missing list would be a silent regression that no other gate in this file would catch: the suite would still pass against the old surface. |

### G8 — The application starts and answers over real HTTP

| | |
|---|---|
| **Command** | `.venv/bin/python -c "import threading,time,urllib.request,uvicorn; from app.main import app as a; threading.Thread(target=uvicorn.run, args=(a,), kwargs={'host':'127.0.0.1','port':8141,'log_level':'warning'}, daemon=True).start(); time.sleep(2); print(urllib.request.urlopen('http://127.0.0.1:8141/v1/health').read().decode())"` — **step 3 of the recorded verification command, verbatim** (`verification-command.txt`) |
| **Pass** | exit 0 and `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}` |
| **Fail** | any non-zero exit, a connection refused, or a body that is not that JSON |
| **Measured** | **exit 0**, that exact body — `test-results.md` §1 and §1.1 row 10, executed verbatim |
| **Blocks** | the merge |
| **Job** | J9 |
| **Why it cannot be folded into G4** | the suite **never starts a server and never resolves `uvicorn app:app`** (`team.md` § Testing Posture: *"Still necessary"*). Every in-process test drives the ASGI app through `asgi_request`, so a packaging or lifespan failure is invisible to the whole suite. |
| **This intent's extension** | the recorded command stops at `/v1/health`, which cannot see the change this intent made. J9 therefore adds one further step over the same real server, on the same loopback port, exercising `/v2/analytics/summary` and `/v2/analytics/terms`. Both return `200`; on a fresh store both return an empty series, which is the **correct** answer — `NFR4.3` requires a *failed* request never to render as a plausible empty result, and an empty population *is* an empty success (`AC2.4.2`). |
| **Credential** | **none.** `mode` is `offline`; no API key exists in the process. |

### G9 — Static security: no egress, no interpolated SQL, no credential literal

> **BLOCKING (file absent).** The instrument is real, measured, and *proved to have
> teeth* — but it is **not in the repository**. It exists only as a heredoc inside
> `security-test-instructions.md` §3.1. See §4.

| | |
|---|---|
| **Command** | `.venv/bin/python tools/security_static_checks.py` |
| **Pass** | `STATIC CHECKS PASSED`, exit 0 |
| **Fail** | `STATIC CHECKS FAILED`, exit 1, with named findings |
| **Measured** | `STATIC CHECKS PASSED`, exit 0 — `test-results.md` §2.4 row 1 |
| **The six checks and their counts** | (1) zero egress from `analytics.py` / `terms.py` / `models.py` against a 12-module denylist → **0 findings** · (2+3) 9 `execute`/`executemany` call sites, **0** statement texts built at call time, **0** parameterless statements in the read path, 0 `executescript` · (4) 16 DML literals, **0** without a `?` in the read path · (5) 0 `print()` across all 15 modules of `app/` · (6) **0** credential literals across 7 credential-shaped identifiers — **this is the `S105`-does-not-fire-on-`API_KEY` hole, covered** |
| **Teeth, demonstrated not asserted** | against a deliberately broken copy of `app/` (`import urllib.request` added to `analytics.py`; the grouped read's statement changed to `statement + " LIMIT " + str(len(rows))`; `API_KEY = "sk-or-v1-realsecret"` added to `db.py`) the same script reports `STATIC CHECKS FAILED` with exactly **5** findings: `analytics.py:29 forbidden import urllib.request` · two × `statement text is built by BinOp/Call at call time` · `execute with no bound parameters in the read path` · `db.py:61 API_KEY hardcoded credential` |
| **Blocks** | the merge — once the file lands |
| **Jobs** | J7 |
| **Deliberately informational, not failures** | `app/db.py:232` `BEGIN`, `db.py:215` and `db.py:270` `PRAGMA`, and 9 parameterless statements outside the read path (schema DDL, `PRAGMA user_version`, `SELECT sql FROM sqlite_master`, and the three `CREATE INDEX` re-creations after a rebuild). None takes a request value, so none can carry one. |
| **Owner of the missing file** | **`u4-platform-packaging`** — `unit-of-work.md` U4 owns *"the platform-neutral verification script"*, and this check's check 6 overlaps `FR7.3`'s secret scan, which is the same unit's. `ci-config.md` §4.7 does not re-author it. |

### G10 — Dynamic security: injection and refusal shapes against real `uvicorn`

> **BLOCKING (file absent).** Same situation as G9: the probe is a heredoc inside
> `security-test-instructions.md` §3.2, never committed. See §4.

| | |
|---|---|
| **Command** | `.venv/bin/python tools/security_dast_probe.py` |
| **Pass** | `DAST PROBE PASSED`, exit 0 |
| **Fail** | any assertion failure; exit 1 |
| **Measured** | `DAST PROBE PASSED`, exit 0 — `test-results.md` §2.4 row 3 |
| **The six probe classes** | **40 injection probes** (2 endpoints × 4 parameters × 5 payloads): `from`/`to` → `422`, `limit` on `/terms` → `422`, `import_id` → `200` (opaque, matches nothing), `limit` on `/summary` → `200` (the summary declares no `limit`) — **never a `500`** · **0** error-text leaks (`Traceback`, `sqlite3.`, `OperationalError`, `SQLITE_`) across all 40 bodies · **5 × `422`** with an envelope of exactly `{code, message}`, the message naming `query.from` / `query.to` / `query.limit`, and **both** bounds on an inverted range · empty success is `200` with `total 0` / `series []`, **never a `404`** · read-only: the row count was still **1** after 50+ requests · loopback: `create_app(host="0.0.0.0")` raised `NonLoopbackBindError` |
| **Blocks** | the merge — once the file lands |
| **Job** | J8 |
| **Topology and credentials** | binds **`127.0.0.1:8142`** and nothing else; constructs `Settings(mode="offline", api_key=None)`; seeds its own `tmp_path` store. **No credential exists in this job, so no CI secret is needed and none could leak.** This is what keeps it inside the affirmed localhost-only rule (`team.md` § Deployment: a code-only job is topology-neutral; nothing binds a non-loopback interface or needs a live credential). |
| **Owner of the missing file** | **`u4-platform-packaging`**, same reason as G9. |

### G11 — The runtime dependency cap holds

| | |
|---|---|
| **Command** | `.venv/bin/python -m pytest --no-cov -q "tests/test_config.py::test_the_manifest_declares_two_runtime_dependencies_and_the_dev_tools"` — also executed inside G4 |
| **Pass** | exit 0. The test asserts `[requirement.split(">=")[0] …] == ["fastapi", "uvicorn"]`, that `pytest`, `pytest-cov` and `ruff` all start a `dev` entry, that `"S" in ruff_config["select"]`, and that `fail_under == 80` |
| **Fail** | a third runtime package declared; a dev tool promoted out of the `dev` extra; `"S"` removed from the ruff selection; the floor changed |
| **Measured** | green — `test-results.md` §5 row `NFR2.6`; re-measured individually in this run |
| **Blocks** | the merge |
| **Job** | J6 |
| **The tripwire's real value** | it asserts the config *string contains the letter* `"S"` and that `fail_under == 80`. It never runs ruff, never asserts which `S` rules are active, and **cannot fail on a code defect**. Its value is against **silent rule-set erosion** — someone deleting `"S"` from `select`, or moving the floor. It is **not** a security gate, and `team.md` § Code Style says so directly. |
| **Resolution is not covered** | 14 distributions install today from 2 declared; one of them (`opentelemetry-api 1.45.0`) is hard-required by `fastapi` itself and reached directly rather than through `anyio`. The manifest rule is declaration-level by construction and this gate is its instrument. |

### G12 — The loopback bind is enforced, not documented

| | |
|---|---|
| **Command** | `.venv/bin/python -m pytest --no-cov -q "tests/test_routes.py::test_the_server_binds_loopback_only"` — also executed inside G4 |
| **Pass** | exit 0 |
| **Fail** | `app.main.create_app(host="0.0.0.0")` starts instead of raising `NonLoopbackBindError` |
| **Measured** | green — `test-results.md` §5 row `NFR2.4`, which records the raised message: *"Refusing to bind '0.0.0.0': this app is unauthenticated and holds the operator's API key…"*. Re-measured individually in this run |
| **Blocks** | the merge |
| **Why it is a gate and not documentation** | `team.md` § Deployment records the state before this Unit plainly: `HOST = "127.0.0.1"` was asserted by a test but **had no call site in the run path**, so `uvicorn app:app --host 0.0.0.0` would expose an unauthenticated app holding the operator's key **and every test would still pass**. The affirmed decision was to enforce the bind at startup. This gate is that enforcement's only instrument. |
| **Affirmed scope** | `memory/project.md` `## Mandated`: *"any non-loopback bind, hosted deploy or change to the authentication posture requires a fresh threat model"* — this gate is the mechanical half of that sentence |

### G13 — The suite is proved offline (and therefore no pipeline step may reach the network)

| | |
|---|---|
| **Command** | `.venv/bin/python -m pytest --no-cov -q "tests/test_analytics_routes.py::test_the_analytics_endpoints_are_proved_offline_by_an_armed_guard"` — also executed inside G4 |
| **Pass** | exit 0. The test exercises the analytics endpoints with `socket.socket.connect` replaced by a raiser, and **fails on `ConnectionRefusedError` if that assignment is removed** — verified to have teeth during Code Generation |
| **Fail** | the guard is present but silently broken, or anything reaches the network |
| **Measured** | green — `test-results.md` §5 row `NFR2.2`; re-measured individually in this run |
| **Blocks** | the merge — **and it blocks the pipeline itself** |
| **The rule this gate enforces over the pipeline** | *"No pipeline step you may design may reach a network."* The mechanism: the session-scoped autouse `offline_guard` in `tests/conftest.py` replaces `socket.socket.connect` with a raiser, and `tests/test_dummy_client.py` **actively proves the guard is armed** so a silently-broken guard cannot make the suite pass while it reaches the network. `build-instructions.md` §7: *"Every test fails on `ConnectionRefusedError` → Correct — that is the guard working."* |
| **Consequence for `ci-config.md`** | only **J1** has network access. Every other job in the pipeline runs with the offline property enforced at the process level, not merely by intention. This is the mechanical form of "no new external service, hosted dependency, cloud component or network call" (`memory/project.md` `## Forbidden`, `C-5`). |

### G14 — The 200 ms latency budget, measured without coverage instrumentation

| | |
|---|---|
| **Command** | `.venv/bin/python -m pytest --no-cov -q "tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget"` — also executed inside G4 |
| **Pass** | exit 0: both endpoints answer `200`, both inside **200 ms**, and the unbounded summary's series length equals the fixture span |
| **Fail** | either endpoint over 200 ms, any non-`200`, or a series length ≠ the span |
| **Measured** | **summary 15.24 ms**, **terms 25.04 ms**, both `200`, over 10,000 rows spanning exactly **365** distinct UTC days. Verbatim: `{"summary": [15.241942000102426, 200], "terms": [25.04308499965191, 200], "series_length": [0.0, 365]}` — `test-results.md` §5 rows `NFR1.1`/`NFR1.2`, `performance-test-instructions.md` §4 |
| **Threshold** | **< 200 ms per request** (`NFR1.1`, `NFR1.2`); headroom **92 %** and **87 %** |
| **Blocks** | the merge |
| **Job** | J6 |
| **Why the measurement lives in a subprocess** | `addopts` applies `--cov` on *every* invocation and coverage instrumentation inflates wall time, so a budget measured inside the suite would describe the **harness**, not the application. The test spawns `[sys.executable, "-c", scenario, tmp_path]` — a separate interpreter with no pytest and therefore no `pytest-cov`. **This is exactly why P3 (`env -u APPIMAGE`) is a hard precondition:** without it that spawn launches the AppImage and exits 130. |
| **How to read the number honestly** | this is a **single cold measurement on one machine with no concurrency**, not a percentile over sustained load. It satisfies the target as written — the requirement states one budget over a pinned fixture — and it **does not establish p95/p99**. Introducing percentiles would be inventing a target. |
| **The floor cannot substitute for it** | `security-test-instructions.md` §4: *"The coverage floor says **nothing** about injection safety… and `team.md` records why: there is no `AVG(`, no `GROUP BY`, no `strftime(` anywhere in the codebase before this Unit, so the pre-existing 96 % figure could not have detected a `strftime` bucket boundary off by one day at the UTC edge."* The defence is the **hand-written expected values**, G4, and this gate — not the coverage number. |

---

## 3. What each gate blocks

| Gate | Merge (once a remote exists) | Blocking job today? | Runnable today? | Named owner of any blocker |
|---|---|---|---|---|
| G1 compile | **blocks** | J2 | ✅ exit 0 | — |
| G2 lint | **blocks** | J3 | ✅ *All checks passed!* | — |
| G3 format | **blocks** | J4 | ✅ *30 files already formatted* | — |
| G4 test suite | **blocks** | J6 | ✅ 192 passed / 0 skipped | — |
| G5 coverage floor | **blocks** | J6 (same command) | ✅ 97.06 % vs 80 % | — |
| G6 warnings-as-errors | **blocks** | J6 (same command) | ✅ 0 warnings | — |
| G7 assembly smoke | **blocks** | J5 | ✅ both `/v2` routes | — |
| G8 runtime smoke | **blocks** | J9 | ✅ `/v1/health` answers | — |
| G9 static security | **blocks, once the file lands** | J7 | ❌ **file not in the repository** | `u4-platform-packaging` |
| G10 DAST probe | **blocks, once the file lands** | J8 | ❌ **file not in the repository** | `u4-platform-packaging` |
| G11 dependency cap | **blocks** | J6 | ✅ | — |
| G12 loopback enforcement | **blocks** | J6 | ✅ | — |
| G13 offline guard | **blocks** | J6 | ✅ | — |
| G14 latency budget | **blocks** | J6 | ✅ 15.24 ms / 25.04 ms | — |

**No gate is advisory, and none is informational.** Every instrument above has a
recorded pass **and** a demonstrated failure mode: G2, G3, G4, G8 by exit code; G9
by the deliberately-broken-copy run; G11 by the manifest literal; G12 by the raised
`NonLoopbackBindError`; G13 by removing the guard's assignment; G14 by the budget
assertion. A gate whose failure mode nobody has demonstrated is a hope, and this
project's own memory says an unrun gate is not a gate.

**One gate is deliberately not defined as blocking, and it is a scope fact rather
than a judgement:** the **walking-skeleton checkpoint** requires the human's
approval, and no automated gate can substitute for it (`memory/org.md` § Walking
Skeleton: *"require the human's skeleton checkpoint approval. A first design-stage
review does not demonstrate a working skeleton"*).

---

## 4. The two gates that cannot run today — and it is a missing file, not a missing command

| | G9 (static security) | G10 (DAST probe) |
|---|---|---|
| Instrument exists | **yes** — a complete, stdlib-only `ast` walker | **yes** — a complete probe against real `uvicorn` |
| Measured green | **yes** — `STATIC CHECKS PASSED`, exit 0 | **yes** — `DAST PROBE PASSED`, exit 0 |
| Proved to have teeth | **yes** — 5 named findings on a broken copy | **partly** — the assertions are `assert` statements against observed HTTP behaviour, so a defect fails them; the "broken copy" demonstration was run for G9 only |
| **In the repository** | **no** — it is a heredoc inside `security-test-instructions.md` §3.1 | **no** — a heredoc inside §3.2 |
| Runnable by anyone, today | **no** | **no** |
| Owning stage | **`u4-platform-packaging`** | **`u4-platform-packaging`** |

**Why this stage does not simply commit the two scripts.** Three reasons, and the
second is the decisive one:

1. **Remit.** `unit-of-work.md` U4 *Owns*: *"the platform-neutral verification script
   and the three gates it runs"*, and *"secret scanning and the dependency audit,
   invoked from that script"*. Both scripts are repository-level verification
   tooling. `u1`'s Infrastructure Design routed the *pipeline* here and the
   *packaging* there (`cicd-pipeline.md` §3), and honouring that routing is the
   whole point.
2. **Divergence.** Writing the files here would create two sources of truth — the
   heredoc in the artifact and a committed script that can drift from it — and
   would pre-empt the choice of *where* they live and *what invokes them*. A
   pipeline that hard-codes a path the packaging unit may name differently is a
   pipeline that breaks for a reason unrelated to any change.
3. **The brief.** This stage produces the design; whether a file lands is `u4`'s
   deliverable and a human's decision.

**What is specified instead:** the job, its exact command, its pass condition, its
measured result and its position in the graph (`ci-config.md` §3, §4.7, §4.8). The
moment `u4` lands the files, J7 and J8 are one path-string change — and
`ci-config.md` §8's commented sibling job is written to be uncommented exactly then.

---

## 5. Gates that **cannot** be built today — recorded so absence is not read as coverage

`memory/team.md` § Deployment: *"Stating the absence plainly, because **absence
must not read as coverage**."* Every row below is a gate a reader could reasonably
expect to find in this file, with the reason it is not here.

| Expected gate | Why it does not exist | What would be needed | Owner |
|---|---|---|---|
| **"Coverage did not decrease"** (the delta gate) | **Unbuildable.** `pyproject.toml` configures **no machine-readable output at all**: `-q` prints dots and no test names, `--cov-report=term-missing` is a human table, and there is **no `--junit-xml`, no coverage XML and no `-ra`**. There is therefore **no coverage artefact to diff against the previous run**. `team.md` § Testing Posture calls this *"the first gate of the standard quality-gate set"* and *"currently unbuildable"*. | `addopts` gaining `--cov-report=xml` (writing `coverage.xml`) plus a job step that fetches the previous `coverage.xml` and fails on a decrease. **A `pyproject.toml` configuration change**, not a new tool — and no new dependency, so it stays inside the two-package cap. | Verification tooling: `u4-platform-packaging` alongside `FR7.2`, or a Code Generation pass over `pyproject.toml` |
| **Flaky-test detection** | Same root cause. With no `--junit-xml` there are **no per-test annotations**, so there is nothing for a flaky list to be built from. | the same `--junit-xml` flag | same |
| **Per-test / named-test reporting** | `-q` with no `-ra` prints **no test names**. A red job's log says a count, not which test. | `-ra` in `addopts`, or `--junit-xml` | same |
| **Branch coverage** | **Off by affirmed decision** (2026-10-02), with the cost recorded: 98 branches, 3 partial, none visible to an 80 % line floor. | a decision reversal. Not proposed here; the reasoning for line-only is `team.md`'s. | — (affirmed decision, not a gap) |
| **Secret scanning** | **Does not exist.** No `gitleaks`, `detect-secrets`, `trufflehog` or equivalent is installed, and no `.pre-commit-config.yaml` exists. `team.md` records PyPI *is* reachable, so *"the absence is a decision rather than a capability limitation"*. G9's check 6 (0 credential literals in `app/`) is what exists instead, and it **cannot see git history** — the team separately scanned **every blob in every commit** and found zero real hits, with the raw `sk-or-v1-` matches all resolving to placeholders. | `FR7.3`: a scanner plus a dependency audit, with the four known fake-key fixtures allowlisted so the first run is signal rather than noise | **`u4-platform-packaging`** |
| **Dependency audit** (`pip-audit`, `safety`, `trivy`) | **Does not exist.** Related to the gap above: with **no lockfile**, **no constraints file**, **no `requirements.txt`** and no hashes, there is no pinned set to audit — every install resolves roughly a dozen transitives fresh. And `setuptools` is **not an installed distribution** at all: PEP 517 build isolation downloads `setuptools>=68` unpinned and unhashed into a temporary environment and **executes `setuptools.build_meta` as code**. | `FR7.1` (lockfile with hashes) **then** `FR7.3` (audit) — the audit is unbuildable before the lockfile, because there is nothing stable to audit | **`u4-platform-packaging`** |
| **Install reproducibility** | **Fails today by environment.** The recorded verification command's step 1 exits 1 with PEP 668 on an externally-managed interpreter — proven pre-existing on a pristine clone of `HEAD` `aa0b1e4`. Separately, with no lockfile the resolved toolchain differs between hosts (system `ruff` 0.16.9, fresh-venv `ruff` 0.16.10; the suite passes under both). | the lockfile (`FR7.1`) for resolution stability; for PEP 668, a recorded-command decision — `ci-pipeline-questions.md` Q4 | `FR7.1` → **`u4-platform-packaging`**; Q4 → **the human** |
| **Layer-boundary enforcement (`TID251`)** | **Not configured.** The affirmative rule exists (`memory/project.md`: *"express the layer boundaries as `ruff` `TID251` `banned-api` entries so that a boundary breach is a lint failure"*), and `TID251` is available in the pinned ruff — but the entries are not written, so the boundary is **not** lint-enforced. G9's check 1 is the instrument that exists instead, and it is **scoped** rather than presented as the rule the team affirmed. | `FR7.5`: the `TID251` entries. Config-only, no new dependency. Note `TID251` is an **import** rule — it does not fire on a write; the read-only guarantee is proved behaviourally in G4 and G10. | **`u4-platform-packaging`** |
| **`print()` / broad-catch / naive-datetime lint** | **Not selected.** `T20`, `BLE001`, `DTZ` are not in the rule set. G9's check 5 covers `print()` (0 across 15 modules) and `team.md` records the error-handling facts behind them (0 bare `except:`, 0 `except Exception:` in `app/`, exactly one deliberate `except BaseException` at `app/db.py:163` which is rollback-and-re-raise). | selecting `T20` / `BLE001` / `DTZ`. **Not proposed here** — the current selection is affirmed as deliberate and reviewed, and widening it is a `Code Style` decision. | the team, via `## Code Style` |
| **HTTPS / TLS assertions** | **No analogue exists.** `team.md` § Deployment: *"nor does any outbound call install a custom `ssl` context, so both use Python's default certificate verification. There is **no TLS-verification bypass anywhere in `app/`**"* — that is an audit result, not a lint rule. No tool in this repository can assert it. | nothing available; recorded as a reviewed audit fact | — |
| **Browser / JavaScript execution** | **None configured.** `app/static/app.js` is served and its markup and script text are **pinned by assertion**, but nothing runs it (`tests/test_page.py:1-6` states the reason). A browser runner would be a new third-party dev dependency, and the two-package runtime cap plus the no-new-dependency posture argue against one. The served script *is* covered by G4 through `tests/test_page.py` — as pinned text, not as executed behaviour. | a JS test runner, if a future scope decides the view's behaviour needs one | a future scope, deliberately |
| **Concurrency / load gate** | **No such target exists.** `performance-test-instructions.md` §7 records why: no RPS target, no ramp-up/steady-state/spike/soak phases (all presuppose a multi-user service), no percentiles, no autoscaling. The concurrency posture is a *failure-behaviour* constraint, not a throughput target, and it is pinned by tests inside G4. | a future scope adding such a target, which would then name `performance-validation` as its owner | a future scope |
| **Contract tests** | **Not generated, deliberately.** *"No consumer/provider boundary exists: one process, one repository, one versioned HTTP surface whose shapes are pinned by hand-written expected values in the endpoint tests."* A contract-test framework would add a dependency the affirmed cap forbids. | a second consumer | — (a reasoned absence) |

---

## 6. Gate-to-NFR map — every target that has an instrument

**24 `Met` · 0 `Not Met` · 2 `Unverified` · 0 `N/A`** — Build and Test's finalised
matrix (`test-results.md` §5). Every `Met` row resolves to one of the gates above.

| Gate | NFR targets it verifies |
|---|---|
| G2 lint | `NFR2.1` (no new scheme/guard — `tests/test_analytics_routes.py::test_v1_routes_are_untouched_by_the_v2_surface`), `NFR2.2` (no forbidden import, jointly with G9), `NFR6` (module conventions — the affirmed invariant) |
| G4 test suite | `NFR3.1`, `NFR3.2`, `NFR4.1`, `NFR4.3`, `NFR4.4`, `NFR4.5`, `NFR8.1`, `NFR8.2`, `NFR9.1`, `NFR9.2`, `NFR9.3` and the `/v1`-untouched half of `NFR2.1` — all asserted by tests inside the one invocation |
| G5 coverage | the whole-application floor; `NFR2.6`'s "no new module missed the floor" half, with every new module at 100 % |
| G9 static security | `NFR2.2` (0 forbidden imports), `NFR2.3` (parameter-bound SQL, jointly with G10), `NFR2.5` / `NFR8.3` (no credential literal — the `S105`-misses-`API_KEY` hole), `NFR8.1` (0 `print()`) |
| G10 DAST | `NFR2.3` (40 probes, never a 500, 0 leaks), `NFR2.4` (loopback refusal), `NFR3.1` (row count survives 50+ requests), `NFR4.1` (5 refusal shapes naming their fields), `NFR4.3` (empty success is 200, never a 404) |
| G11 dependency cap | `NFR2.6` |
| G12 loopback | `NFR2.4` |
| G13 offline guard | `NFR2.2` — the guard **proved armed** |
| G14 latency budget | `NFR1.1`, `NFR1.2`, and jointly with G4 `NFR1.3`, `NFR1.4`, `NFR9.4` (statement count constant in range length; series length = the range, not the store) |
| — | **`NFR4.6` — `Unverified`.** Per-section graceful degradation needs a **second analytics section** to make one fail while the other succeeds; `NFR4.7` — `Unverified`. No silent retry, and a superseded range's out-of-order response discarded, needs a **range control** to supersede. Both instruments (`AC6.5.2`, `AC6.5.3`, `AC6.5.5`) belong to `u3-analytics-view`. **No gate is defined for either, and none can be** until that Unit ships its markup. Carried as accepted debt into Bolt 3 by the human's explicit ruling. |

---

## 7. One command set, three consumers

The relationship between this stage, the human, and `u4-platform-packaging` — stated
once so the next reader does not mistake three overlapping things for three
competing designs.

| Consumer | What it runs | Who owns it |
|---|---|---|
| **The human, today** | the standing verification command: install → `pytest -q` → boot real `uvicorn` on `127.0.0.1:8141` and read `/v1/health`. With the venv remedy for the install step. | recorded in `verification-command.txt`; the remedy is `build-instructions.md` §2.3 |
| **A future CI job** | J1–J9 (`ci-config.md` §3–§4) — the same commands plus the two security scripts and the `/v2` extension | this stage (design only; the file is `u4`'s to land) |
| **`u4-platform-packaging`'s verification script** | *"the platform-neutral verification script that runs the standing gates — the whole-application 80 % line-coverage floor, the warnings-as-errors filter and the pinned `ruff` rule set"* (`FR7.2`), plus secret scanning and the dependency audit *invoked from that script* (`FR7.3`) | **`u4-platform-packaging`** |

**The convergence is the intended destination.** `memory/team.md` § Testing Posture
decided this on 2026-10-02 and the reasoning survives intact: *"A script that a
human and any future CI job can both call is the only option that is true today and
stays true on any host."* The moment `u4`'s script exists, **J1–J9 become arguments
to it** rather than a parallel copy of its body — and that convergence is recorded in
`ci-config.md` §9 as the single most likely future edit, so it is a planned change
rather than a discovery.

**What must not converge.** The two security scripts (G9, G10) are verification
instruments whose *content* Build and Test wrote and reviewed; they land as files
`u4` owns, and this stage pins only their command and pass condition. Rewriting
their checks from memory here would be inventing an instrument, which is the one
thing this file refuses to do.