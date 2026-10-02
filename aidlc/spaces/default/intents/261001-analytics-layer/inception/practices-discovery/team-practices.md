# Team Practices — sentiment-opencode

> **Integrated at Step 5 for intent `261001-analytics-layer`.** This is the lead's
> final integration of the three blind support reviews with the fourteen recorded
> answers in `practices-discovery-questions.md`. **The interview wins** wherever a
> spoke's position and an answer disagree. Our affirmed baseline in
> `aidlc/spaces/default/memory/team.md` is carried forward and checked against a
> fresh full rescan of the repository at `beeb587`; where our own baseline is now
> factually wrong, this says so and gives the evidence instead of repeating it.
> Evidence lines are in `evidence.md`. Nothing here is affirmed until the gate.

## Way of Working

**We work one branch per intent or scope, squash it into `main` as a single
commit, and tag that commit with the scope name.** Affirmed 2026-09-30, when `main`
still carried only the harness and the application sat on an unmerged `v1-classic`.
The repository has since caught up with the rule rather than diverging from it, so
it now stands on two completed executions instead of one intention.

What the history shows at `beeb587`:

| Commit | Subject | Tag |
|---|---|---|
| `4eb9b74` | `v1-classic: harden sentiment-analysis app to v1 (classic scope)` | annotated tag `v1-classic` → `4eb9b74` |
| `beeb587` | `express: add CSV bulk import / export endpoints (express scope)` | annotated tag `express` → `beeb587` |

`git branch --list` returns only `main`. There is no surviving feature branch, no
merge commit and no third commit — so "one branch per scope, squashed" is what
actually happened, twice, and each scope's name is on a tag pointing at its own
single commit.

**Our commit messages now have an affirmed shape** (2026-10-02), which until this
interview was only an observation from one sample of each kind:

- **Subject**: `<scope>: <summary> (<scope> scope)`.
- **Body**: a changed list — what went in — ending with the measured result.
- **Trailer**: `Produced by the AI-DLC <scope> workflow for intent <id>.`

`v1-classic` has an empty body, which does not satisfy the shape; `express`
satisfies it fully. Both existing commits satisfy the subject form. This is a rule
now, in `discovered-rules.md`, not a pattern a future author may copy from one
sample.

**Corrections to our own baseline.** Three lines in the affirmed `team.md` no
longer match the repository. We correct them rather than carry them forward,
because the next stage will read them as fact:

- The baseline said *"`main` currently holds only the AI-DLC harness (`0268a5d
  Initial commit`); the whole application lives in `5b328fc` on `v1-classic`, one
  commit ahead and unmerged."* **Neither commit exists in this history.**
  `git rev-list --count HEAD` is 2, there is no initial commit, and both scopes
  have been squashed onto `main`. The sentence described a transient state that
  the merge then resolved.
- The baseline said the repository has *one author identity,
  `very-cool-sentiment-analysis <demo@local>`.* **That identity never existed
  here.** `git log --format='%an <%ae>' | sort -u` returns exactly one line —
  `Faraz Mazhar <farazmazhar@users.noreply.github.com>` — and the named identity
  appears nowhere in the history. The *substance* of the claim still holds and we
  keep it: one author, no co-authors, no merges, and therefore no second human
  reviewer. The reason built on it (review-before-land is self-review plus agent
  review) also still holds.
- The baseline said *no tag exists unless the merge step writes one.* Two now
  exist, and they were written by exactly that step.

**There is still no second human reviewer, and still no remote.** `git remote -v`
returns empty — no remote, no pull requests, no review comments. Nothing in the
repository implies a review step. The feasibility register records the same
constraint from this run's interview (`C-7`: stage reviews are advisory;
review-before-land is self-review plus agent review), and this scope's guard policy
is `relaxed`. That part of the baseline is current, not drift.

**Cadence is coarse and milestone-shaped.** The two commits are 1 h 42 min apart
(2026-10-01, 20:15 and 21:57 +0500). One commit per finished scope, landing at the
end of a run. **No maximum branch age has ever been affirmed and we are not
inventing one.** No commit-signature or co-author expectation exists either.

## Walking Skeleton

**We build a thin end-to-end slice first, by default, on future work.** A walking
skeleton is a minimal version that runs the whole way through — built before the
real features go in, to prove the pieces connect. Unchanged since 2026-09-30, and
confirmed again on 2026-10-02.

**This run is the first live exercise of the ceremony.** Both prior scopes declared
`skeleton: off` (`.aidlc/scopes/aidlc-classic.md:6`,
`.aidlc/scopes/aidlc-express.md:8`), so the baseline's exemption sentence — "this
run is the exception that proves the rule" — no longer applies. The scope we
resolved to is `feature`, which declares `skeleton: on`
(`.aidlc/scopes/aidlc-feature.md:8`). The standing default is the answer, and it
was kept.

**For this feature the slice is one analytics endpoint end to end** (2026-10-02):
route, aggregate SQL, page render — before the second endpoint goes in. That is the
concrete reading of "thin slice" when the work is a layer *on top of* a working
app rather than the first end-to-end path through it. The intent treats all four
capabilities as must-have, which is compatible with slicing but does not by itself
say so; this answer says so.

**No thin-slice ceremony is not the same as no end-to-end proof.** The proof is the
standing verification command under `## Testing Posture`: install, run the suite,
then start the app and exercise the changed path. Both prior intents did exactly
that against a real server — the `v1` run on `127.0.0.1:8141`, the `express` deploy
on `127.0.0.1:8137` — and those runs, not the suite alone, are the evidence that
each change works end to end.

## Testing Posture

- **Methodology**: custom
- **Ordering**: Acceptance- and API-level tests are written against the requirement or acceptance criterion before the implementation, and lower-level unit tests are written after the implementation.

Both fields carry the 2026-09-30 affirmed answer unchanged, and the 2026-10-02
interview did not disturb them. `custom` is the right label because the answer mixes
cadences, and the mix is visible in the artifact: API/acceptance level in
`test_routes` (15), `test_bulk_import` (16), `test_auth_routes` (12), `test_page`
(4); lower-level unit level in `test_db` (8), `test_repository` (8), `test_service`
(9), `test_live_client` (9).

We state the limit of that corroboration plainly, because it is the honest reading:
**the repository corroborates both test *levels*, and cannot corroborate the test
*order*.** Two squashed commits, no surviving branch and no intra-commit ordering
means the history physically destroys the evidence of which test was written first.
The ordering sentence is affirmed team practice carried forward on the human's
authority, not a conclusion drawn from the code.

**Framework and configuration** (measured at `beeb587`, `.venv` CPython 3.14.7):
`pytest` only — no `unittest`, no `hypothesis`, no `asyncio` marker.
`[tool.pytest.ini_options]` sets `testpaths = ["tests"]`,
`addopts = "-q --cov=app --cov-report=term-missing --cov-fail-under=80"`, and
`filterwarnings = ["error"]`.

> **Correction to our own earlier description.** We called the warnings filter "the
> project's only deprecation canary — a FastAPI or pydantic deprecation on 3.14 is a
> hard failure." **That was too narrow.** `filterwarnings = ["error"]` promotes
> **every** warning from **every** source to a suite failure: pytest's own
> deprecations, a transitive `DeprecationWarning`, a `ResourceWarning`. Combined
> with the second fact — there is no lockfile, so the installed toolchain sits **two
> major versions past every declared floor** (`pytest 9.1.1` against `>=8`,
> `pytest-cov 7.1.0` against `>=5`, `starlette 1.7.0`, `pydantic 2.13.5`) — the
> suite's pass/fail state is a function of **the resolved dependency set, not of the
> code**. A fresh `pip install -e ".[dev]"` on any other machine resolves something
> different. That is not a hypothetical; it is the normal state of this manifest
> today, and it is the single strongest technical argument for the lockfile decided
> under `## Deployment`.

**Coverage** (affirmed; line coverage only, confirmed 2026-10-02):

- **The whole application is measured** — `[tool.coverage.run] source = ["app"]`,
  including the live client the offline suite does not import.
- **The floor is 80 % lines**, stated twice so it cannot be skipped by forgetting a
  flag: in `addopts` (`--cov-fail-under=80`) and in `[tool.coverage.report]
  fail_under = 80`. `show_missing = true`. It is a genuinely enforcing gate, not a
  printed notice: raising the floor to 99 on the command line makes the run exit 1.
- **Branch coverage stays off** (2026-10-02). We measured what turning it on would
  reveal: 98 branches, **3 partial** — `app/db.py:208`, `app/main.py:49`, and the
  partial edge `app/routes.py:385->387` — none of which the 80 % line floor can see.
  We are recording the cost of the decision as well as the decision, because line
  coverage is the weakest signal available for a feature made of conditional
  aggregation over a date range: every `if` whose false branch is never taken still
  counts as covered.
- **Measured now: `118 passed`, 679 statements, 27 missed, `96.02 %`.**

**(Correction)** Our baseline recorded the floor as *failing* — *"556/792 lines =
70.2 % across all 12 application modules"*, *"the floor therefore fails today"*.
That work is done. `tests/test_live_client.py` (9 functions) covers the
answer-reading side of the live engine through an injected transport, so
`app/openrouter_client.py` reads **92 %** rather than 0 %. The floor now passes
with about 16 points of headroom. The whole count also moved — 679 measured
statements against the baseline's 792.

**Test surface** (measured): **118 collected tests from 109 test functions**,
expanded by 5 parametrization sites, across **11 `tests/test_*.py` modules** plus
`tests/conftest.py` (176 lines, harness only). Per module: `test_routes` 15,
`test_bulk_import` 16, `test_auth_routes` 12, `test_session_auth` 12, `test_config`
10, `test_service` 9, `test_live_client` 9, `test_db` 8, `test_repository` 8,
`test_dummy_client` 6, `test_page` 4. Our baseline's "52 tests in 9 modules, 52
passed in 0.33 s" is twice-stale; any later stage citing it will be wrong.

**All 11 test modules pass standalone.** The suite is order-independent *and*
module-independent, not merely green in aggregate. That is the property that makes
an automatic gate safe to trust here, and it is the strongest available argument for
turning the gates on. A full suite run with coverage costs **about 1.1 seconds**;
cost is not a reason to leave the gates opt-in.

**Test doubles policy** (unchanged, and still the strongest thing about this suite):
assertions read values back out of real SQLite and real served markup, never out of
doubles. **Zero mock objects** — no `unittest.mock`, no `unittest` at all; eight
hand-written classes (`FakeExchanger`, `StubTransport`, `DuckTypedClient`,
`FailingOnBoomClient`, `IncompleteClient`, `UnsupportedLabelClient`,
`RejectingClient`, `FailingClient`) sit at real process seams. `monkeypatch` **is**
our sanctioned substitution instrument, used at the consumer's import name
(`monkeypatch.setattr("app.routes.get_client", …)`) — so "zero mock objects" must
never be promoted to "no substitution". The session-scoped autouse `offline_guard`
replaces `socket.socket.connect` with a raiser, and
**`tests/test_dummy_client.py` actively proves the guard is armed**, so a
silently-broken guard cannot make the suite pass while it reaches the network.
`tmp_path`-scoped settings and DB paths mean no test reads `config.local.toml` or
`data/sentiment.db`, and `tests/test_config.py` shells out to `git check-ignore` as
an executable assertion that the key file cannot be committed.

**Boundary discipline** (unchanged): a refusal that half-succeeded would fail,
because row-count assertions of 0 accompany the status-code assertions. `limit`
below 1 or non-numeric answers `422` naming `field == "query.limit"`, never a
silent clamp; history is newest-first; `/v1/health` reports the resolved mode;
secret redaction is asserted in reprs, in log records including `record.__dict__`,
and in the `/`, `/v1/health` and `/auth/status` bodies.

### Where the gates run — decided 2026-10-02

**The three gates — the whole-application 80 % coverage floor, the
warnings-as-errors filter, and the pinned `ruff` rule set — run from a
platform-neutral verification script (or make target) that the developer runs.**
Not a pre-commit hook. Not a provider CI job. Both rejected by name, and both now
rules in `discovered-rules.md`.

The options were not peers, and the reason is worth keeping so nobody reopens the
question as if they were: **`git remote -v` is empty and there is no CI provider of
any kind.** A provider workflow file written today would be a file that has never
executed and cannot execute until a remote exists. A pre-commit hook is real and
local, but it never sees a dependency bump and never runs in CI, so it cannot be the
whole gate. A script that a human and any future CI job can both call is the only
option that is true today and stays true on any host.

**What the gate cannot yet express.** `pyproject.toml` configures **no
machine-readable output at all**: `-q` means a default run prints dots and no test
names, `--cov-report=term-missing` is a human table, and there is no
`--junit-xml`, no coverage XML and no `-ra`. So per-test annotations have nothing
to consume, a flaky-test list cannot be produced, and — the one that matters most —
**"coverage did not decrease" is not expressible as a gate today**, because there is
no coverage artifact to diff against the previous run. That is the first gate of the
standard quality-gate set and it is currently unbuildable.

**One precondition nobody had written down**: the suite needs a git working tree. A
full source tree copied without `.git` gives 117 passed / 1 failed, because
`git check-ignore` exits 128 and `tests/test_config.py`'s `shutil.which("git")`
guard covers git-absent, not git-present-but-not-a-checkout. Any gate that receives
source without `.git` goes red with a message that reads like a credential leak.

### Every defect ships a reproducing test — decided 2026-10-02

**Yes. Every defect we fix ships with a test that reproduces it.** This closes a
question that had been open since 2026-09-30, and it reverses the standing precedent:
R-01, the cross-thread SQLite connection defect, was recorded and accepted with no
test reproducing it. Under this policy R-01's exception is closed too.

The answer has a prerequisite, and it is not "add a test":
`tests/conftest.py:136` calls `asyncio.run` per request, so every API test runs on
a fresh event loop, single-threaded and strictly sequential. **No test written
against today's harness can reproduce R-01, however carefully written** — the fix is
a different harness shape (a real `uvicorn` on a loopback port, or explicit
threads), and that harness work comes first. The page this intent adds polls on a
date range, which is the access pattern most likely to trigger the defect, so the
gap is on this work's critical path rather than in the far distance.

### Computed numbers get hand-written expected values — decided 2026-10-02

**Hand-written expected values, stated per requirement, for the analytics
aggregates — and a test that the new indexes survive a migration**, by inspecting
`sqlite_master`. Both halves are rules.

The reason is a measurement, not a preference. There is **no `AVG(`, no
`GROUP BY`, no `strftime(` and no `json_extract`** anywhere in `app/` or `tests/`
today; the only SQL in the suite is `SELECT COUNT(*) FROM analyses`, used for
row-count assertions. So the 96.02 % figure says nothing whatsoever about whether a
date bucket, an average, a NULL `confidence` or an empty date range is computed
correctly. A `strftime` bucket boundary off by one day at the UTC edge — given
`repository.py:41` normalises to `%Y-%m-%dT%H:%M:%SZ` — would leave the suite fully
green and the floor fully satisfied.

The second half is a known-dormant loss rather than an accepted one. `_rebuild_analyses`
(`app/db.py:233`) does `RENAME` → `CREATE TABLE` → `COPY` → `DROP TABLE`, and
`CREATE_ANALYSES_TABLE` declares **no index at all** — so an index added to that
DDL is silently destroyed on any migrating store, with no warning possible. The
suite contains no `CREATE INDEX` and no assertion over
`sqlite_master WHERE type='index'`; the single `sqlite_master` assertion
(`test_db.py:103`) filters `type = 'table'` only. **No warning is possible,
because the only implementation that drops them is one the suite never inspects
afterwards.** This intent adds indexes and a v3 → v4 migration, so it will trigger
it.

### Explicitly untested, by design

- **No browser execution at all.** `app/static/app.js` is served and its markup is
  pinned; nothing in the suite runs it. `tests/test_page.py:1-6` states the reason.
- **The two production HTTP transports** — `app/session_auth.py:84-120` (17
  statements) and `app/openrouter_client.py:89-96` (6 statements), 23 of the 27
  missed lines. Every test injects a transport or an exchanger, because the
  dependency cap forbids an HTTP client library.
- **No concurrency test whatsoever.** `grep -niE 'thread|concurren|parallel'` over
  `tests/` returns nothing — and, per the ruling above, the harness cannot host one
  in its present shape.
- Three single-line misses remain: a `csv.Error` branch, a `PRAGMA table_info`
  absence guard, and a logging-handler guard.

**The verification command** (affirmed): **install** (`python -m pip install -e
".[dev]"`), **run `pytest`**, then **start the app locally and exercise the changed
path**. The README records it as a single copy-paste line that installs, runs the
suite with the floor applied, boots uvicorn on `127.0.0.1:8141` and reads
`/v1/health`. Still necessary: the suite never starts a server and never resolves
`uvicorn app:app`.

## Deployment

**Deployment is a localhost checkout, and a commit is the release.** No environment
tiers, no container, no hosted service, no IaC. The only documented run path is
`python -m pip install -e ".[dev]"` then `uvicorn app:app --reload`, one process
bound to `127.0.0.1:8000`. The released artifact is the squashed commit tagged with
the scope name (see `## Way of Working`); the version stays `0.1.0`, the install is
editable, and no package or image is ever published. The framework default — deploy
on merge to staging behind a manual production gate — has no counterpart here,
because the environments it assumes do not exist.

**Two *declared* runtime dependencies, fourteen *resolved*.** This distinction
matters and our earlier draft blurred it. We declare **exactly two** — `fastapi` and
`uvicorn` — with every development tool in the `dev` extra. That is the cap, and
`tests/test_config.py:141` asserts the `project.dependencies` *list*, so it is
declaration-level by construction. But **14 distributions install today**, and one of
them is not ours to choose: **`fastapi 0.142.2` declares a hard, non-extra
dependency on `opentelemetry-api>=1.44.0`** (1.45.0 installed), reached directly from
FastAPI rather than through `anyio`. Nothing in `app/` imports `opentelemetry` or
`otel`, and with no OTel SDK or exporter installed there is no automatic egress — so
this is not an active finding. It is simply the kind of transitive a "two packages"
rationale never contemplated, sitting next to the no-hosted-dependency constraint.

**Supply chain — we are adding a lockfile with hashes now (2026-10-02).** Until it
lands, dependencies are **floors, not pins** (`fastapi>=0.110`, `uvicorn>=0.27`,
`pytest>=8`, `pytest-cov>=5`, `ruff>=0.6`, build backend `setuptools>=68`): no
lockfile, no hashes, no constraints file, no `requirements.txt`, so each install
resolves the newest compatible version of roughly a dozen transitive packages.
`setuptools` **is not an installed distribution in `.venv`** — PEP 517 build
isolation means every `pip install -e ".[dev]"`, our single documented install
command, downloads `setuptools>=68` fresh, unpinned and unhashed, into a temporary
isolated environment and **executes `setuptools.build_meta` as code**. There is no
audit command, no update bot and still no named owner for dependency updates or
emergency patches.

**Scanning — we are adopting secret scanning and a dependency audit (2026-10-02),
with the four known fake-key fixtures allowlisted so the first run is signal rather
than noise.**

Stating the absence plainly, because **absence must not read as coverage**. In this
repository there is **no secret scanner, no dependency audit, no SAST, no DAST, no
pre-commit hook, no CI, no SBOM, no licence policy and no audit cadence.** A search
for `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci`, `azure-pipelines.yml`,
`.pre-commit-config.yaml`, `Makefile`, `tox.ini`, `noxfile.py`, `Taskfile*`,
`justfile`, `.semgrep*`, `.bandit`, `.gitleaks.toml`, `.trivy*`, `.snyk`,
`.checkov*`, `renovate.json`, `.dependabot/` and every `*lock`/`*constraints*`
filename returns zero hits outside the AI-DLC harness tree; `.git/hooks` holds only
`.sample` files; and none of `pip-audit`, `bandit`, `semgrep`, `gitleaks`,
`detect-secrets`, `safety` or `trivy` is installed. PyPI *is* reachable from this
machine, so the absence is a decision rather than a capability limitation.

And stating the other half, because those are two different statements: **our secret
practice is genuinely clean.** Every blob in every commit was scanned for real key
shapes — `sk-…`, `AKIA…`, `BEGIN … PRIVATE KEY`, `ghp_…`, `github_pat_…`, Slack
tokens, `AIza…`, JWT-shaped strings, and `api_key/secret/password/token = <24+
chars>` — with **zero real hits**; the raw `sk-or-v1-` matches all resolve to obvious
placeholders (`0123456789abcdef0123456789abcdef`, `from-config`, `live-key`,
`not-used-here`, `session`, `session-key`). The clean practice is real; the tooling
that would enforce it is absent. Only the second is a process gap, and reporting only
the first would let a future scope add a real key with nothing to notice.

**Loopback is now enforced rather than documented (2026-10-02).** Our baseline called
localhost-only "binding" on the strength of a documented default. It was not
enforced: `HOST = "127.0.0.1"` (`app/main.py:36`) is asserted by
`tests/test_routes.py:334-338`, but **`HOST` has no call site in the run path** — the
documented invocation is `uvicorn app:app --reload`, so the bind is uvicorn's own
default, not our constant. `uvicorn app:app --host 0.0.0.0` would expose an
unauthenticated app holding the operator's API key and **every test would still
pass**. The decision: **enforce the loopback bind at startup, so a non-loopback host
fails loudly.** That needs no dependency at all. The rule itself is unchanged and
still binding — loopback bind, unauthenticated by design, any non-loopback bind,
hosted deploy or change to the authentication posture requires a fresh threat model.

**`ci-pipeline` and `deployment-pipeline` run for the first time in this project.**
This scope is `feature`, which marks all 33 stages `EXECUTE`; both prior scopes
skipped them. That is why the question of where the gates live was open in 2026-09-30
and is answered above. One constraint that decides what a future job may do: a
**code-only** job (install → lint → `pytest`) is topology-neutral and safe under the
localhost-only rule; anything that binds a non-loopback interface or needs a live
credential is not.

**Local data and recovery.** Durable state is one gitignored SQLite file,
`data/sentiment.db`, created on first run. **Deleting it is still acceptable
recovery** — but that sentence is weaker than it reads, and we would rather say why
than repeat it:

- The code is at **schema version 3**; the local file in this checkout still reports
  **`schema_meta.version = 2`** with no `import_id` column, no index on `analyses`
  and 0 rows. The v2 → v3 path has therefore never run against this machine's file,
  and cannot be exercised here without losing the (empty) store.
- Real stores are no longer disposable. A v1 store holds rows with their original
  `intensity` values and their `import_id` grouping; the import/export feature is
  now the user's way of moving data out. This intent adds a further additive step on
  top (v3 → v4) plus indexes, so "recreate the database" is a choice with a cost.
- There is still no migration tool, no backup path and no rollback procedure to
  write, because there is no deployment. Recovery means stopping the process,
  deleting or restoring the local file, and checking out the previous commit.

**The localhost deployment precedent, established by the `express` intent** — worth
carrying as the procedure rather than improvising it again: choose a throwaway
temporary database so the real store is untouched, serve the real
`app.main:create_app` through real `uvicorn` on a loopback port with settings
injected so no real config or key is read, smoke-test the changed path over HTTP,
then stop the process. That run passed pre-deployment checks (118 passed / 96.02 %
coverage), migrated v2 → v3 on startup, and needed no rollback.

**Data egress** (unchanged). `POST /v1/analyze` stores submitted text unencrypted in
the gitignored database, and in live mode the same text goes to OpenRouter.
`POST /v1/analyses/import` takes a whole CSV of text. There is no retention or delete
endpoint. The analytics layer reads this same data, so this is worth restating before
new read paths are added.

**Accepted low risks under this trust model** (recorded, not work items): no CSP or
other security headers; no CSRF token or `Origin` check on the body-less
`POST /auth/disconnect`; no PKCE `state` parameter (`app/session_auth.py:163-180`);
`callback_url` derived from the request `Host` header (`app/routes.py:137-142`).
These stay low because there is no XSS sink in `app.js` (all rendering is
`textContent`), the PKCE `code_verifier` never leaves the process, and there is no
CORS configuration to misconfigure. One positive finding, worth stating because
"stdlib `urllib` instead of `requests`" reads as a downgrade until you check: neither
outbound call installs a custom `ssl` context, so both use Python's default
certificate verification. **There is no TLS-verification bypass anywhere in `app/`.**

**A `LICENSE` is coming (2026-10-02).** The repository has no `LICENSE`, no
`COPYING`, no `license` field in `pyproject.toml`, and the project's own installed
distribution carries an empty licence expression. Every installed dependency is
permissive (MIT ×12, BSD-3-Clause ×4, BSD-2-Clause ×1, Apache-2.0 ×2, PSF-2.0 ×1, plus
`packaging` as `Apache-2.0 OR BSD-2-Clause`), so there is **no licence finding** — only
a licence absence, now closed.

## Code Style

**`ruff` is adopted for both formatting and linting, with an explicit rule set that
includes its security rules.** Both checks are green at this commit —
`ruff check app tests` → *All checks passed!*, `ruff format --check app tests` →
*24 files already formatted* (measured, ruff 0.16.9). The adoption question our
baseline left open is closed, and settled the way the baseline recommended:

| Setting | Value |
|---|---|
| `line-length` | `100` |
| `target-version` | matches `requires-python` — was `"py311"`, **matched 2026-10-02** |
| `lint.select` | `["E","F","W","I","N","UP","S","B","C4","SIM"]` — explicit and reviewed, not a drifting default; `S` is the security set |
| `lint.flake8-bugbear.extend-immutable-calls` | `["fastapi.Depends","fastapi.Query"]` — B008 silenced **by configuration**, not by `# noqa` |
| `lint.per-file-ignores` for `tests/*` | `["S101","S105","S106","S603","S607"]` — the security rules still apply **in full to `app/`** |
| `format.quote-style` / `format.line-ending` | `"double"` / `"lf"` |

**Two corrections to the security set's description**, because our earlier draft
overclaimed it. Selecting `S` is a real selection — ruff 0.16.9 ships 73 `S` rules and
zero removed rules — but **13 of the 73 are preview-gated and therefore inactive**
under a plain `select`, and all 13 are the *import-side* blacklist checks (`S401`
telnetlib, `S403` pickle, `S404` subprocess, the XML parsers, `S411` xmlrpc, `S412`
httpoxy, `S413` pycrypto, `S415` pyghmi). The net catches the dangerous *call*, not
the dangerous *import*. And for secrets it is narrower than it sounds: **`S105` fires
on `SECRET = "…"` and does not fire on `API_KEY = "…"`** — `API_KEY` is not among
the identifiers ruff treats as credential-shaped, and it is the single most likely
name for the one secret this project has. Nothing catches it today because the real
key is gitignored and held in memory, so the hole is latent rather than open.

**What the lint rule set does not catch**, so nobody later mistakes these for gates:
`except Exception:` — `BLE001` is not selected, so the commonest broad-catch mistake
is caught by nothing (bare `except:` *is* caught, by `E722`); `print()`
(`T20` not selected); `breakpoint()` (`T10` not selected); naive `datetime.now()`
(`DTZ` not selected); and any TLS or cipher assertion, for which ruff has no
analogue at all. Nor does `target-version` cover the runtime it now matches —
`"py311"` aimed our only static security analysis at a Python the app never runs
(CPython 3.14.7), which is why it is matched now.

The one automated security assertion in the repository is
`tests/test_config.py:141`, and it is worth naming accurately: it asserts that the
config **string contains the letter `"S"`** and that `fail_under == 80`. It never
runs ruff, does not assert which `S` rules are active, and cannot fail on a code
defect. It is a useful tripwire against silent rule-set erosion. It is not a
security gate.

**Error handling — stated accurately this time.** Our baseline claimed *"no bare
`except` and no broad catch anywhere"*, and the grep offered as proof
(`grep -E 'except\s*:' app/`) **cannot support that claim**; it only rules out the
bare form. The true and more useful statement:

- **No bare `except:` anywhere in `app/`, and no `except Exception:` either.**
- **Every handler names a specific type** or a deliberate two-type tuple:
  `app/config.py:84,88`, `app/openrouter_client.py:95,170,182`,
  `app/routes.py:113,213,217,323`, `app/service.py:180`,
  `app/session_auth.py:100,105,112,207`.
- **Every wrapping `raise` uses `from exc`**, and `print()` never appears in `app/`;
  logging goes through module loggers and the key is never logged.
- **There is exactly one broad handler, and it is deliberate:**
  `except BaseException` at **`app/db.py:163`**, inside the migration's
  `BEGIN` / `try` / `rollback()` / `raise` / `commit()` block. It is
  rollback-and-re-raise, not a swallow — a failed migration stops startup loudly
  instead of leaving a half-migrated file — and it is the one handler a reader
  should be pointed at rather than the one a rule should hide.

Three error idioms are in use and each is deliberate: **refuse** (raise, or answer
`422`), **roll back and re-raise** (the migration), and **skip and continue**
(`app/service.py:180` catches a two-type tuple mid-loop during a bulk import). We
had no stated rule for which to use; there is now a stated example of each.

### Where reads go — an accident that is now an arrangement

**Writes and engine calls go through `service`; reads go straight from the route to
the query layer.** `app/service.py`'s entire public surface is `effective_connection`,
`get_client`, `require_text`, `ImportSummary`, `new_import_id`, `import_texts`,
`analyze_text` — **it holds no read or query function at all**, and `app/routes.py:31`
imports `DEFAULT_LIST_LIMIT`, `list_analyses` and `list_analyses_by_import_id` from
`app.repository` and calls them directly at `app/routes.py:177` and `:242`.

Until now that arrangement was an accident of where the functions happened to land,
and our draft described the layer chain as if HTTP reached persistence only through
`service` — which is not what the code does. **The team has now ruled it explicit
(2026-10-02): aggregate queries live in a new read module beside `repository`,
called from the route. The service layer is not inserted into the read path.** The
analytics layer is *entirely* reads, so this intent is where the accident becomes a
recorded arrangement — which is exactly why it is written down.

**Layer boundaries become machine-checked (2026-10-02).** The three promises below
were prose in module docstrings and in the CodeKB, with nothing enforcing them. We
are adding **`ruff` `TID251` (`banned-api`)** so a boundary breach is a lint failure.
`TID251` is available in the pinned 0.16.9 and this is a config-only change —
consistent with the stance we already took, which is an explicitly reviewed rule
selection rather than a drifting default, with a written reason beside each entry.

### Boundaries we are keeping

`app/` is a **flat by-layer package**, not feature-sliced: leaves (`config`,
`models`, `sentiment`) → `repository`, `db`, `dummy_client`, `openrouter_client` →
`service` → `routes` → `main` → `__init__`. The import graph is acyclic and
descending. One hexagonal seam: `SentimentClient` (`app/sentiment.py:78`) with two
adapters, chosen in exactly one function (`get_client`, `app/service.py`). Connection
ownership sits at the HTTP edge: only `app/routes.py:92` touches the `sqlite3` driver
and the connection lifecycle, and `repository`/`service` receive a connection. That
boundary is also where the accepted cross-thread defect lives, so affirming it is what
keeps connection handling from spreading.

**One structural constraint the next change must know.** `init_db` (`app/db.py:145`)
is a two-arm branch — migrate if the table exists, else create — with
`CREATE_SCHEMA_META_TABLE` *after* the branch. A new table's DDL therefore has to be
added in two places or the branch refactored, and **the codebase has already solved
exactly this once**: `schema_meta` is created after the branch, on every path. That
is the placement to copy, and it is free here because `asgi_request` re-enters the
lifespan on every call (`tests/conftest.py:102`) — so the suite exercises the
migration path on **every** in-process request. That is a free idempotency test the
design should lean on.

### The tokeniser

**Do not import `_WORD` from another module, and do not copy the regex.** The
repository has exactly one tokenizer, `_WORD = re.compile(r"[a-z']+")` at
`app/dummy_client.py:68`, underscore-private inside the *offline engine*. The
analytics term extraction needs a stopword set, a minimum length and probably case
handling — none of which an engine-grade splitter has an opinion about, which is why
this is not a reuse question at all. Our no-`utils.py` convention forbids a
junk-drawer module, and `app/sentiment.py` is a leaf that imports nothing from `app`
and already owns `LABELS`, the closed vocabulary every analytics aggregate is bucketed
over. That is the natural home for a promoted public pattern.

### Conventions the code holds

- **Module docstring as a boundary declaration.** All 12 modules open with a
  docstring; **11 carry an explicit `Single responsibility:` line naming what the
  module does *not* contain** (`app/routes.py:3-6` — "No sentiment logic and no SQL
  live here"). The negative clause is what makes a flat by-layer package auditable
  without an architecture document.
- **Types**: full annotations everywhere, **zero suppressions in `app/`**.
  `from __future__ import annotations` in **11 of 12** `app/` modules — the exception
  is the 10-line `app/__init__.py` re-export shim.
- **Constants**: `UPPER_CASE`; privates `_`-prefixed. Semantic constants carry a `#:`
  prose comment (71 across 10 modules). `app/service.py` carries none, using a class
  docstring instead — a variant, not a counterexample.
- **Naming**: `snake_case` modules, functions and tests; `PascalCase` classes and
  type aliases; tests are `tests/test_<module>.py`, and the function names are **a
  full prose sentence stating the expected outcome, prefixed by the route where one
  applies** — `test_v1_analyze_returns_the_stored_record_field_set`,
  `test_v1_analyses_is_a_bare_array_newest_first`,
  `test_a_body_that_is_not_the_declared_object_is_refused`,
  `test_pre_v1_data_paths_are_no_longer_served`. Our earlier draft understated this
  as `test_<behaviour>`, and it is a candidate for affirmation, so it is affirmed in
  its real shape here.
- **Refuse, never substitute**: `limit: int = Query(50, ge=1)` rather than a silent
  clamp; `None` for an empty aggregate rather than a fabricated `0.0`;
  `UNKNOWN_PROVIDER = "unknown"` rather than `null` or `"None"`; a retired attribute
  never back-filled with an invented number. This is the most consistent pattern in
  the repository and it spans `db.py`, `repository.py`, `models.py` and `service.py`.
- **Read back after write**: `insert_analysis` returns the row it re-`SELECT`ed
  (`app/repository.py:76-77`), never the in-memory payload, so the returned object
  is the persisted object.
- **One construction site per external dependency, plus a function-local import to
  keep a module unloaded**: `from app.openrouter_client import …` sits *inside*
  `_live_client` (`app/service.py:103`) so the offline path never loads the module
  that performs HTTP.
- **A retired path gets a test asserting it is gone**
  (`test_pre_v1_data_paths_are_no_longer_served`,
  `test_the_page_has_no_intensity_affordance`).
- **The hand-written constant in the test module is the contract**: each test module
  pins what it protects at the top with a `#:` comment — `RECORD_FIELDS`,
  `ENVELOPE_FIELDS`, `ISO_8601_UTC`, `REQUIRED_TEST_IDS`. It is the codebase's stated
  substitute for response models, and it has a real cost: the nine-field record now
  lives in `models.py`, `test_routes.py`, the README prose *and* a positional list in
  `app/routes.py:252-263`. The analytics endpoints follow it rather than invent a new
  pinning style.
- **Suppressions: nine in total, all narrow and justified** — 4 ×
  `# pragma: no cover` (unreachable-by-construction branches), 4 × `# noqa: S310` on
  the `urllib` calls with a "hardcoded https constant" comment, 2 ×
  `# type: ignore[method-assign]` in the offline guard. **Zero file-level
  `# ruff: noqa`.** The four `S310` suppressions are the **entire security-suppression
  budget** in the repository — four, consistently applied with written justifications
  across two completed scopes.
- **Zero `TODO`/`FIXME`/`HACK`/`XXX`** anywhere in `app/` or `tests/`.
- **Imports**: stdlib / third-party / `app.*`, one blank line between groups, with
  ordering *within* a group now mechanically settled — `I` is selected and
  `ruff check` is green.
- **Docstrings**: English freeform prose, sentence case, no Google/NumPy section
  format anywhere. `tests/conftest.py` is the one outlier — it uses Sphinx `:func:`
  cross-reference roles — so if freeform prose is the rule, that file is the one to
  bring in line.
- **SQL**: parameter-bound only; every statement in `app/db.py` and
  `app/repository.py` uses `?` placeholders, with no string interpolation.
- **No `pydantic` in `app/`**: request and record shapes are stdlib dataclasses,
  keeping the validation library FastAPI happens to use out of application code. The
  cost is that no response model exists, so FastAPI's `/openapi.json` cannot describe
  the real shapes and contracts are pinned only by hand-written constants in the
  tests.
- **No junk-drawer module**: no `utils.py`, no `helpers.py`; a pure helper lives in the
  module that owns the concept, which is also what keeps it testable without a
  fixture.

### Four accidents that must not be codified

A team practice is a licence to copy, so these are recorded as accidents rather than
conventions:

1. **The duplicated `urllib` bodies** in `session_auth.py:88-120` and
   `openrouter_client.py:89-96`. It reads as a principle; it is the residue of a
   boundary that forbade those two modules importing each other. Its fingerprint is
   still in the tree — all four `# noqa: S310` suppressions exist *only* because of
   the duplication. Codified as a practice, the next author duplicates a third time.
   This intent adds no third outbound call, so nothing forces the decision now.
2. **`_WORD` living inside an engine**, per the tokeniser ruling above.
3. **Naming drift around the schema version**: `SCHEMA_VERSION = 3` coexists with
   `_is_v1_shape` (`app/db.py:195`), an `init_db` docstring that says "bring its
   schema to v1", a `CREATE_ANALYSES_TABLE` comment saying "the v1 physical schema",
   and a `main.py` comment saying "brought to the v1 shape". Harmless at v3, actively
   misleading at v4.
4. **`service.py` carrying no `#:` line**, covered above as a variant.

### Two decisions from this interview that reach the HTTP surface

**The analytics endpoints are `/v2`, on a new versioned router, with the existing
`/v1` contract left untouched (2026-10-02).** The code has exactly one prefix,
`V1_PREFIX = "/v1"` (`app/routes.py:49`), and the CodeKB records business rule BR4.2
as "data routes are versioned under `/v1`". The intent description named `/v2` twice;
constraint `C-4` paraphrased that same text as `/v1`. This ruling settles the
conflict in favour of the description. Two consequences to carry: the frontend holds
an **independent second copy** of the prefix (`app/static/app.js:10`, with fetch
sites at `:87`, `:97`, `:157`, `:185`) and nothing asserts the two copies match; and
`test_pre_v1_data_paths_are_no_longer_served` is the instrument for proving a route
was retired, so it is the instrument for the new router's contract too.

**`mean intensity` is dropped from the summary (2026-10-02).** `intensity` is a
deliberately retired column: absent from `RECORD_FIELDS`, never written by
`_INSERT_SQL`, never read by `from_row`, `NULL` on every row the application has ever
written, and asserted absent from the served markup by
`tests/test_page.py:64-68`. `AVG(intensity)` would therefore return a permanent
`null`. The field is removed from the requirement; the column is out of scope and no
migration resurrects it.

### Two stale CodeKB rows that must not reach a later stage as authority

- `architecture.md:502` names **`ensure_page_state`** as the connection-ownership
  improvement. **`ensure_page_state` does not exist anywhere in this repository.**
  The connection owner is `get_connection` (`app/routes.py:92`). Any stage that reads
  that row verbatim will look for a function that is not there.
- `code-structure.md:208` records `from __future__ import annotations` as applying to
  **"All 12 modules"**. It applies to **11**; `app/__init__.py` does not have it.
- (Minor, same class of problem) `technology-stack.md:57` records
  `opentelemetry-api 1.45.1` reached "through `anyio`". Installed is **1.45.0**, and
  `fastapi` requires it directly — `starlette` needs it only under its `full` extra.
  It is cleanest available proof that the CodeKB's "Installed" columns are a
  one-time snapshot nothing keeps honest.

### The README is part of the change

The CodeKB calls the README's `## HTTP surface` table "the contract of record". A new
router, endpoint, module or test module means hand-editing that table (**19 rows
today**), the `## File layout` tree (every module listed by hand), and usually
`## Storage`. A "one-line" prefix change is not one line.

### Enforcement summary

The mechanical gates are the warnings-as-errors filter, the 80 % whole-application
line-coverage floor, and the pinned `ruff` rule set — plus, now, `TID251`
`banned-api` for the layer boundaries. Where they run is decided: a
**platform-neutral verification script the developer runs**, neither a pre-commit hook
nor a provider CI job. What does **not** exist is worth stating in the same breath:
no CI, no pre-commit hook, no secret scanner, no dependency audit, no SAST and no
DAST. An unrun gate is not a gate; a documented default is not enforcement. Both
sentences have been load-bearing in this project and both still are.