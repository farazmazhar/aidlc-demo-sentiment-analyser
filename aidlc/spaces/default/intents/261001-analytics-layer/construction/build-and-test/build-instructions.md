# Build Instructions — intent `261001-analytics-layer`, Unit `u1-analytics-slice`

> **Stage:** `build-and-test` (construction) · **Test strategy:** `standard` ·
> **Scope:** `feature` · **Record:** `aidlc/spaces/default/intents/261001-analytics-layer`
>
> **Inputs this file was derived from** (the stage's declared `consumes`):
> `construction/u1-analytics-slice/code-generation/code-generation-plan.md` ·
> `construction/u1-analytics-slice/code-generation/unit-test-instructions.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md`, plus the
> measurable target inventory in `construction/u1-analytics-slice/nfr-requirements/` and
> `construction/u1-analytics-slice/nfr-design/`.

This project is **pure Python with no build step in the compiler sense**. There is
no bundler, no transpiler and no container image to produce: `pip install -e`
places an editable pointer, and the "build" is therefore (1) a byte-compilation
check that every module parses, (2) the pinned `ruff` lint and format gates, and
(3) an import smoke test that the application actually assembles.

## 1. Prerequisites

| Requirement | Value | Verified |
|---|---|---|
| Interpreter | CPython `>=3.11` (`pyproject.toml` `requires-python`); measured **3.14.7** | `python -V` |
| Package manager | `pip` (bundled with the interpreter) | `python -m pip --version` |
| Build backend | `setuptools>=68` (declared in `[build-system]`) | resolved at install time |
| Network | **Only for the first install.** Nothing in the test run reaches the network — a session-scoped autouse guard replaces `socket.socket.connect` with a raiser, so a network call fails the suite. | `tests/conftest.py` `offline_guard`; `tests/test_dummy_client.py` |
| Git working tree | **Required.** `tests/test_config.py::test_local_config_is_gitignored` shells out to `git check-ignore`; a source tree copied without `.git` yields 1 failing test that reads like a credential leak. | `git rev-parse --is-inside-work-tree` |
| Disk | The largest fixture is the 10,000-row performance store in `tmp_path`; a few MB. | — |

No environment variable is required to build or test. No database is required: every
test scopes its settings and database to `tmp_path`, so no test reads
`config.local.toml` or `data/sentiment.db`.

## 2. Dependency installation

### 2.1 The recorded command

```bash
python -m pip install -e ".[dev]"
```

This is step 1 of the intent's recorded Construction Verification Command
(`<record>/verification-command.txt`).

### 2.2 Measured result on this host — and the reason

**It fails, and the failure is the interpreter's, not this code's.**

```
$ python -m pip install -e ".[dev]"
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try 'pacman -S
    python-xyz', where xyz is the package you are trying to
    install.
...
note: ... You can override this, at the risk of breaking your Python installation or OS distribution provider, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
$ echo $?
1
```

`python` resolves to `/usr/bin/python` → `/usr/bin/python3.14`, and
`/usr/lib/python3.14/EXTERNALLY-MANAGED` marks that interpreter as externally managed
(PEP 668). Arch's system Python refuses to accept `pip install` into it.

**Proven pre-existing.** The same command was run against a pristine clone of
`HEAD` (`aa0b1e4`, "feature: Bolt 1 code generation — the analytics slice") in a
separate directory, with none of this Unit's writes present. It fails identically.
The baseline commit would have failed the same way.

### 2.3 The two remedies, both proven here

**Remedy A — a virtual environment (pip's own recommendation, preferred).**

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

**Measured:** exit **0**. `Successfully installed … very-cool-sentiment-analysis-0.1.0`
into a throwaway venv on CPython 3.14.7, and the whole suite then runs green inside
that venv (`192 passed`, 97.06 %). The repository already contains a `.venv` with
the same content.

**Remedy B — `--break-system-packages` (writes into the user site directory).**

```bash
python -m pip install --dry-run --break-system-packages -e ".[dev]"
```

**Measured:** exit **0**, `Would install very-cool-sentiment-analysis-0.1.0` —
every runtime and dev dependency already resolves as *already satisfied*, so the
block is purely the write refusal, not an unsatisfiable dependency set.
`--dry-run` is used here so this evidence run does not mutate the operator's
interpreter; drop the flag to actually install.

**What this costs.** Nothing, and nothing is weakened. The dependency set, the
`dev` extra and the pinned ruff rule set are untouched; only the location the
packages land in changes.

### 2.4 Which target, if any, is Unverified because of the PEP 668 block

**None.** The inventory of measurable targets in `nfr-requirements/` and
`nfr-design/` contains no target whose instrument is "`pip install -e ".[dev]"`
exits 0 against the *system* interpreter". Every declared target is measured by a
`pytest` test, an executable static/DAST check, or a lint gate, and all of those
run unchanged under either remedy. The block is recorded as an environmental
constraint on the recorded command, not as a failed quality target.

## 3. Environment setup

| Step | Command | Purpose |
|---|---|---|
| 3.1 (optional) local config | `cp config.example.toml config.local.toml` | Only for a human running the app in **live** mode. `config.local.toml` is gitignored. Tests never read it. |
| 3.2 data directory | `mkdir -p data` | The default `db_path` is `data/sentiment.db`; the app creates the file and the parent on first start. Tests use `tmp_path` instead. |
| 3.3 environment variables | none | No variable is read by the application or the suite. |

There is no external service to start. There is no migration step outside
`init_db`, which runs at application startup and is idempotent (schema version 4).

## 4. Build commands

Run from the repository root.

```bash
# 4.1 Byte-compilation: every module in app/ and tests/ parses.
python -m compileall -q app tests          # measured: exit 0

# 4.2 Lint gate — the pinned, reviewed rule set including the `S` security set.
python -m ruff check app tests             # measured: "All checks passed!"  exit 0

# 4.3 Format gate.
python -m ruff format --check app tests    # measured: "30 files already formatted"  exit 0

# 4.4 Import smoke test: the application assembles and the analytics router mounts.
python -c "import app.main as m; print(m.app.title, m.v2_router.prefix, [r.path for r in m.v2_router.routes])"
```

Measured output:

```
very-cool-sentiment-analysis /v2 ['/v2/analytics/summary', '/v2/analytics/terms']
```

It is the cheapest proof that the build produced a working application rather than
a collection of parsable files. (Read `v2_router.routes`, not `app.routes`: this
FastAPI version wraps an included router in an object with no `.path`.)

## 5. Build verification

```bash
# 5.1 The whole suite with the affirmed whole-application coverage floor applied.
python -m pytest -q
# measured: 192 passed, TOTAL 884 stmts / 26 missed / 97.06 %, floor 80 % reached, exit 0

# 5.2 The recorded Construction Verification Command, end to end.
cat aidlc/spaces/default/intents/261001-analytics-layer/verification-command.txt
```

The recorded command is a three-step `&&` chain: install, `pytest -q`, then boot
real `uvicorn` on `127.0.0.1:8141` and read `/v1/health`.

**Measured, step by step (this host):**

| Step | Command | Result |
|---|---|---|
| 1 | `python -m pip install -e ".[dev]"` | **exit 1 — PEP 668**, pre-existing on pristine `HEAD`; both remedies proven in §2.3 |
| 2 | `python -m pytest -q` | **exit 0** — 192 passed, 97.06 % |
| 3 | the `uvicorn` / `/v1/health` one-liner | **exit 0** — `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}` |

Steps 2 and 3 were executed **verbatim** as recorded. Step 1 was executed verbatim
and failed; the two substitutes in §2.3 were executed in full and both succeed.

**Build status: SUCCESS under either documented remedy; the recorded command's
step 1 is blocked by the host interpreter (PEP 668), which is an environmental
constraint and is not attributed to this code.**

## 6. Environment gotcha you will hit on this host: `APPIMAGE` corrupts `sys.executable`

One failure here is **not** a code defect and will otherwise look like one.

```bash
# WRONG on this host — one test fails with exit code 130
python -m pytest -q
# FAILED tests/test_analytics_read.py::test_each_analytics_endpoint_answers_inside_the_budget
#   CompletedProcess(args=['/home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage', '-c', ...], returncode=130)

# RIGHT — 192 passed
env -u APPIMAGE python -m pytest -q
```

**Cause.** The shell exports `APPIMAGE=/home/faraz/.local/bin/opencode-desktop-linux-x86_64.AppImage`.
CPython 3.14 honours that variable when resolving `sys.executable`, so
`sys.executable` reports the AppImage path instead of `/usr/bin/python3.14`. The
performance test spawns `[sys.executable, "-c", scenario, tmp]`
(`tests/test_analytics_read.py:552`) to measure the budget **without** coverage
instrumentation; the AppImage rejects `-c` and exits 130.

**Proof it is environmental, not a test or code defect.**

```bash
python -c "import sys; print(sys.executable)"                      # → …AppImage
env -u APPIMAGE python -c "import sys; print(sys.executable)"     # → /usr/bin/python
```

**Remedy.** Prefix every test, lint or server command in this repository with
`env -u APPIMAGE`. This is the *only* change Build and Test made to the execution
environment: **no application source file and no existing test file was modified.**
Every command in `integration-test-instructions.md`,
`performance-test-instructions.md` and `security-test-instructions.md` carries the
prefix.

## 7. Troubleshooting common build issues

| Symptom | Cause | Fix |
|---|---|---|
| `error: externally-managed-environment` | PEP 668 — Arch's system Python | §2.3 Remedy A (venv, preferred) or Remedy B (`--break-system-packages`) |
| `test_each_analytics_endpoint_answers_inside_the_budget` fails, `returncode=130`, `sys.executable` is an AppImage | `APPIMAGE` leaking into `sys.executable` | §6 — `env -u APPIMAGE` |
| `tests/test_config.py::test_local_config_is_gitignored` fails with exit 128 | Source tree without `.git` | Build and test from a git checkout |
| Every test fails on `ConnectionRefusedError` / `socket` | The offline guard is armed and something tried to open a socket | Correct — that is the guard working. No test may reach the network. |
| `Required test coverage of 80% not reached` on a **subset** run | `addopts` applies the whole-application floor to every run; a partial run cannot cover the whole app | Use the whole-suite command for the floor. `unit-test-instructions.md` records the same residual and the `--cov-fail-under=0` amendment for the scoped per-unit run. |
| `ModuleNotFoundError: No module named 'app'` | Running `python` from outside the repository root, or the editable install never happened | Run from the repository root, or `PYTHONPATH=.` |
| `ruff` reports a different rule set than expected | There is **no lockfile** (an affirmed gap, `FR7.1`), so a fresh install resolves newer tools than the declared floors | Pin what you need, or use the repository `.venv` |