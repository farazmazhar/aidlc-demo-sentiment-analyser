# Team Practices — `260930-sentiment-v1`

> Affirmed at the practices-discovery interview on 2026-09-30, written in the team's own voice.
> Each section states the practice we commit to and the measured state it sits on; the same content
> is promoted into `aidlc/spaces/default/memory/team.md` at the affirmation gate. Observations the
> interview did not affirm stay observations and are marked as such in the text.

## Way of Working

We work **one branch per intent or scope**. The branch is named for the work item — `v1-classic`
for this intent — and it stays open until the work is finished.

When the work is finished we **merge the branch into `main`, squashed to a single commit**, and we
**tag that commit with the scope name** (`v1-classic` squashed into one commit on `main`, tagged
`v1-classic`). The framework default carries no tag; the per-scope tag is ours, so later stages must
not assume a tag exists unless the merge step writes one.

`main` currently holds only the AI-DLC harness (`0268a5d Initial commit`); the whole application —
app, tests, `README.md`, `pyproject.toml`, `config.example.toml` and the prior intent's record —
lives in the single commit `5b328fc` on `v1-classic`, one commit ahead and unmerged. Everything we
build in v1 lands on `main` through the squash-and-tag path above; this is the first work the path
will carry.

There is **no second human reviewer in this project**. The repository has one author identity
(`very-cool-sentiment-analysis <demo@local>`), and the stakeholder map records one person as sole
user, operator and decision-maker, with no influencers and no reporting cadence. Review before a
change lands is therefore self-review plus the stage's agent review, and this scope caps stage
reviews at advisory (`classic` → `review_cap: advisory`: one pass per stage, no refute-and-repair
loop). Anything stronger — a written checklist, a mandatory reviewer pass, a pull request even for
ourselves — is not yet affirmed.

Commit cadence observed so far is coarse and milestone-shaped, with a scope-prefixed subject
(`v1-classic: …`), on a two-commit history from a single identity. The squash rule above keeps that
shape on `main`; the message convention and any maximum branch age are not yet affirmed.

## Walking Skeleton

**We build a thin end-to-end slice first, by default, on future work.** A walking skeleton is a
minimal version that runs the whole way through, built before the real features go in to prove the
pieces connect. This is now the standing team answer, not a per-scope accident.

This run is the exception that proves the rule: this intent (`260930-sentiment-v1`, scope `classic`)
declares `skeleton: off` in `.aidlc/scopes/aidlc-classic.md`, so no thin-slice ceremony runs here,
and this run stays as it is. A scope declaring `skeleton: off` skips the ceremony; the default
answers the question the scope flag does not.

No thin-slice ceremony is not the same as no end-to-end proof. We still prove a change by running
the real thing, and we now have one recorded command for it (see `## Testing Posture`): install, run
`pytest`, then start the app locally and exercise the changed path. The prior intent did exactly
that — it started the real server on `127.0.0.1:8141` and exercised health, analysis, history and
invalid input — and that run, not the suite alone, is the evidence that the app works end to end.
A repository snapshot can never settle the skeleton question; it is intent, and the intent is
recorded above.

## Testing Posture

- **Methodology**: custom
- **Ordering**: Acceptance/API tests come first — written against the requirement or acceptance
  criteria before the implementation — and lower-level unit tests come after the implementation.

- **Framework and configuration** (observed): pytest only, configured in `[tool.pytest.ini_options]`
  — `testpaths = ["tests"]`, `addopts = "-q"`, `filterwarnings = ["error"]`. The warnings filter is
  the project's only mechanical gate today, and it doubles as its only upgrade canary: any
  deprecation warning from FastAPI or pydantic on Python 3.14 becomes a failure. The suite was
  measured green at this commit — **52 passed in 0.33 s** — so the gate is currently satisfied, not
  aspirational. Note that `addopts = "-q"` suppresses per-test names, which a pipeline log parser
  will care about.

- **Test types present** (observed): 52 test functions in **9 `tests/test_*.py` modules** (auth_routes
  12, session_auth 12, config 7, dummy_client 6, routes 6, service 3, db 2, repository 2, page 2),
  plus the `tests/conftest.py` harness which contains no tests. The types are behavioural unit tests
  per module, API-level tests driven through a hand-rolled in-process ASGI harness (`asgi_request()`
  builds a raw scope, enters the lifespan and collects messages — no server starts, and `httpx` /
  `TestClient` are absent by design), and page/markup contract tests pinning 9 `data-testid` hooks
  plus `GET /static/app.js` being served as JavaScript. There are no tests against live external
  services, no browser execution, no performance tests, and **no concurrency test at all** —
  `grep` for thread/concurrency terms in `tests/` returns nothing. That last gap is material: it maps
  onto R-01 (per-request `sqlite3.connect` on default thread affinity, `app/routes.py:70-76`,
  `app/db.py:51-63`), the one defect this workspace has ever recorded and accepted.

- **Test surface and doubles policy** (observed): assertions read values back out of real SQLite and
  the real served markup, never out of mocks — there are **zero mock objects** in `tests/`, and
  exactly two `monkeypatch` uses (`tests/test_auth_routes.py:205,223`). Doubles sit only at process
  seams: an injected `exchanger` / `clock` in the authorization flow (`tests/test_session_auth.py:189`)
  and an injectable `now` in the repository and service tests. A session-scoped autouse
  `offline_guard` replaces `socket.socket.connect` with a raiser (`tests/conftest.py:129-146`), so an
  accidental outbound call fails the run and an all-dummy run proves the suite never used the
  network. `tmp_path`-based settings and DB paths mean no test reads `config.local.toml` or
  `data/sentiment.db`, and `tests/test_config.py:126-143` shells out to `git check-ignore` as an
  executable assertion that the key file cannot be committed.

- **Boundary discipline** (observed): tests pin the observable contract, not implementation echoes —
  422 for empty or whitespace-only text *with a row-count assertion of 0*, `limit` below 1 or
  non-numeric → 422 naming `field == "query.limit"` and never a silent clamp, newest-first ordering,
  `/health` reporting the resolved mode, and secret redaction asserted in reprs, in log records
  (including `record.__dict__`) and in the `/`, `/health` and `/auth/status` bodies.

- **Explicitly untested, by design** (observed): `app/openrouter_client.py` — the live engine, 149
  executable lines — is never imported, constructed or called by the suite; the PKCE exchange
  `exchange_code_at_openrouter()` is unexecuted and the flow is tested through `FakeExchanger`; the
  browser script `app/static/app.js` is not executed. `README.md` records the substitute coverage as
  code review plus a manual live smoke run. The suite cannot perform that smoke run, so who runs it
  and when (pre-merge or pre-release) remains an open point for design and build.

- **Coverage** — affirmed: **add a coverage tool, count the whole application, enforce an 80 % line
  floor, and run the suite plus the floor in a CI job.** Measured today with a throwaway standard
  library tracer: **556/792 lines = 70.2 % across all 12 application modules**, or **86.5 %** if the
  never-imported live client is excluded (0/149). The floor therefore **fails today**, and covering
  the live engine — at least its pure typed readers `_read_choice` / `_read_score` — is construction
  work in this scope, not an optional extra. Two measurement facts to carry forward: the tracer must
  be installed on new threads (`threading.settrace`), because FastAPI runs every endpoint here in an
  anyio worker thread and a naive in-process measurement reads `app/routes.py` at 47 % instead of
  91 %; and `pytest-cov` / `coverage` are not installed, so the pragmas the team already writes
  (`app/repository.py:20`, `app/service.py:75`, `tests/test_config.py:128`) now need a policy for what
  counts. The other half of this decision is open by construction: this scope skips the CI Pipeline
  stage, so **where that CI job lives is an open point for design and build** — a local `addopts`
  floor, a pre-push hook, or the pipeline itself once one exists.

- **Dev-tool dependency cap** (observed, needs one confirmation): NFR3 in `pyproject.toml` caps
  *runtime* dependencies at two (`fastapi` + `uvicorn`), with `pytest` as the only dev extra. A
  coverage tool and a linter are development tools, so they do not change the runtime count — but the
  NFR3 comment and the README's "exactly three packages beyond the standard library" line become
  false the moment either is added, and must be updated in the same change.

- **Verification command** (affirmed): **install** (`python -m pip install -e ".[dev]"`), **run
  `pytest`**, then **start the app locally and exercise the changed path**. This is the command later
  stages use to prove a unit works end to end; `pytest` alone is not enough, because the suite never
  starts a server and never resolves `uvicorn app:app`.

- **Regression policy** (not yet affirmed): nothing runs the suite on a change, and no rule yet says
  whether every defect must ship a reproducing test. The precedent to decide against is R-01: a
  concurrency defect was recorded and accepted, and no test in the suite reproduces it.

## Deployment

**Deployment is a localhost checkout, and a commit is the release.** There are no environment tiers,
no pipeline, no container and no hosted service; the only documented run path is
`python -m pip install -e ".[dev]"` followed by `uvicorn app:app --reload`, one process bound to
`127.0.0.1`. The released artifact is the squashed commit tagged with the scope name (see
`## Way of Working`); version stays `0.1.0`, the install is editable, and no package or image is
published. The framework default — deploy on merge to staging with a manual production gate — has no
counterpart here because the environments it assumes do not exist.

**What has to pass before we call a change done** is the affirmed verification command above —
install, `pytest`, then a local live exercise of the changed path — and, once the coverage tool
lands, the 80 % floor. Today nothing automated stands between a change and a usable build.

**Local data and recovery.** Durable state is one gitignored SQLite file (`data/sentiment.db`),
created on first run, with a stored schema version that is written but never compared, no migration
mechanism and no backup path. **Deleting `data/sentiment.db` is acceptable recovery**, and a schema
change is handled by recreating the local database. With no deployment there is no deploy rollback
procedure to write: recovery means restoring or deleting the local file and checking out the previous
commit.

**Localhost-only is binding.** The recorded "localhost only, no auth, no cloud, no Docker"
constraint now stands as a project rule (`discovered-rules.md`), not as a claim in an upstream
requirements file. A hosted or container-based deploy would break it; a code-only CI job that
installs, lints and runs `pytest` would not. The app is unauthenticated by design, so any local
process or user that can reach loopback can spend the key through `POST /analyze` — a deliberate
consequence of localhost-only, and the reason loopback binding is a rule rather than a preference.

**Supply chain** (observed, open for design and build). Dependencies are declared as floors, not
pins (`fastapi>=0.110`, `uvicorn>=0.27`, `pytest>=8`, build backend `setuptools>=68`); there is no
lockfile, no hash, no constraints file and no `requirements.txt`, so each install resolves the newest
compatible version of roughly a dozen transitive packages. There is no audit command, no update bot
and no git remote. That matters here rather than as boilerplate: in live mode the process holds a
valid OpenRouter key in memory while all of those packages execute in-process, and PEP 517 runs the
build backend during `pip install`, so a compromised release on that path is a key-exfiltration path
that localhost binding does not mitigate. Open: keep floating floors with manual audit, or add a
lockfile plus a periodic audit check — and who owns dependency updates and the emergency-patch path.

**Data egress** (observed). `POST /analyze` stores the raw input text unencrypted in the gitignored
database, and in live mode the same text is sent to OpenRouter. There is no retention or delete
endpoint. In plain words: the text leaves the machine when the live indicator is green, and it stays
on disk locally otherwise.

**Accepted low risks under this trust model** (recorded, not work items): no CSP or other security
headers; no CSRF token or `Origin` check on the body-less `POST /auth/disconnect`; no PKCE `state`
parameter (`app/session_auth.py:163-180`); `callback_url` derived from the request Host header via
`request.url_for("auth_callback")` (`app/routes.py:137-142`). These stay low because there is no XSS
sink in `app/static/app.js` (rendering is `textContent` throughout), the PKCE `code_verifier` never
leaves the process, and there is no CORS configuration to misconfigure.

## Code Style

**We adopt `ruff` for formatting and linting, with an explicit rule set that includes its security
rules, run as a pre-commit hook or a stage check.** Choosing `ruff` means one development dependency
buys both style and a static-analysis floor (the `S` / flake8-bandit rules), which `black` + `flake8`
would not; the honest alternative — convention and review only — is what the project has today and
is no longer the plan. The org rule that says to run the linter "in CI before merge" cannot be
satisfied as written, because `classic` skips the CI Pipeline stage, so the gate needs a home that
exists: **open for design and build** is the choice between a pre-commit hook and a lint step inside
Build and Test. A `ruff` binary that happens to sit on this machine's PATH is not a gate; the tool
must be declared in the project.

**Adoption baseline** (measured read-only with a system `ruff` 0.16.9, `--isolated --no-cache`):
16 findings over `app/` + `tests/`, 9 auto-fixable — `B008`×6, `I001`×4, `UP035`×2, `UP037`×2,
`SIM117`×1, `F401`×1 (`tests/test_auth_routes.py:15` imports `pytest` unused) — and
`ruff format --check` would reformat **12 of 22 files** (the same count at line length 88 and 100).
This is one mechanical commit in a two-commit repository; it only gets more expensive later. Two
settings must land in that same commit:

- **Line length**: 88 flags 18 lines, 100 changes 2 (longest line today is 109 chars,
  `app/config.py:125`).
- **The `B008` / `Depends` policy**: all six findings are `Depends(...)` in default arguments
  (`app/routes.py:92,93,104,114,130,162`), FastAPI's own documented idiom. Configure
  `lint.flake8-bugbear.extend-immutable-calls` for `fastapi.Depends` rather than forcing
  non-idiomatic code or a blanket `# noqa`.

Adding `ruff` and the coverage tool does not change the runtime dependency cap (NFR3 counts
`fastapi` + `uvicorn`), but the NFR3 comment in `pyproject.toml` and the README's "exactly three
packages" line must be corrected in the same change.

**Conventions the code holds today** (observed across the 11 substantive `app/` modules plus the
10-line `app/__init__.py` re-export shim; the counts here follow the CodeKB's "11 substantive
modules, 9 test modules" so later stages cite stable numbers):

- **Module docstrings**: every substantive module opens with one; 11 of 12 also name a single
  responsibility and cite the prior intent's requirement ids. The exceptions are real:
  `app/__init__.py` has no "Single responsibility" line, and `app/session_auth.py` — which postdates
  the prior intent — cites no requirement id at all. The citations are already drifting, so the
  upkeep rule for them is an open point; `app/main.py:33-34`'s "no authentication … exists anywhere
  in this app" comment is now false.
- **Types**: full annotations on every function and `from __future__ import annotations` in all 11
  substantive modules, with zero suppressions in `app/`. This is the one convention a linter does not
  cover, and it is 100 % applied, so a type checker would enforce it almost for free; the two
  `# type: ignore[method-assign]` comments in `tests/conftest.py:142,146` already anticipate one.
- **Constants**: `UPPER_CASE`; the semantic ones carry a `#:` doc comment (schema version, column
  order, labels, endpoints, TTLs, error codes) while the numeric/path defaults, the SQL text and
  `PORT` do not. **20 of 39 constants have no adjacent `#:`**, including
  `EXCHANGE_TIMEOUT_SECONDS` (`app/session_auth.py:53`).
- **Privacy**: helpers and state are underscore-prefixed (`_read_choice`, `_read_score`,
  `_post_decisions`; `_pending`, `_drop_expired_pending`; `_configure_logging`, `_read_config_file`,
  `_INSERT_SQL`, `_WORD`).
- **Naming**: `snake_case` modules and functions, `PascalCase` classes and type aliases
  (`Mode = Literal[...]`, `app/config.py:20`), `UPPER_CASE` constants; tests are
  `tests/test_<module>.py` with `test_<behaviour>` names.
- **Error handling in code**: no bare `except` and no broad catch anywhere — every handler names a
  specific type (`app/config.py:62,66`; `app/openrouter_client.py:161,169,181`; `app/routes.py:154`;
  `app/session_auth.py:99,104,111,209`) — and every raise that wraps a caught error uses `from exc`
  (8 sites). `print()` never appears in `app/`; logging goes through module loggers and the key is
  never logged.
- **No junk-drawer module**: there is no `utils.py` or `helpers.py`; a pure helper lives in the module
  that owns the concept (`format_timestamp`, `create_code_verifier`, `code_challenge_for`), which is
  also what keeps it testable without a fixture.
- **Imports**: blocks laid out stdlib / third-party / `app.*` with one blank line between groups.
  Ordering *within* a group is not isort-clean in four files (`app/config.py:9`, `app/main.py:9`,
  `app/routes.py:9`, `tests/test_config.py:9`), so "sorted imports" is a norm the new linter will
  settle, not a fact.
- **Formatting**: 4-space indent, double quotes, trailing commas in multi-line calls; only 10 lines
  exceed 88 characters.
- **Docstrings**: English freeform prose in sentence case, no Google/NumPy section format anywhere in
  `app/` or `tests/`. `tests/conftest.py` is a one-off — its docstring uses Sphinx `:func:`
  cross-reference roles, which `app/` does not; if freeform prose is the rule, that file should be
  brought in line.
- **SQL**: parameterised only; every statement in `app/db.py` and `app/repository.py` uses `?`
  placeholders, with no string interpolation.
- **No pydantic in `app/`**: request and record shapes are stdlib dataclasses, keeping the validation
  library FastAPI happens to use out of application code. The record contract, though, is **one
  documented contract with four hand-written copies** — `RECORD_FIELDS` (`app/models.py:20`, which
  nothing references, not even `tests/test_routes.py:22`, which declares its own private set), the
  `AnalysisRecord` field declarations (`app/models.py:47-62`), the literal in `to_dict()`
  (`app/models.py:64-77`), and `ANALYSES_COLUMNS` plus the `CREATE TABLE` text (`app/db.py:15-48`).
  They are kept in sync by tests, not mechanically (CodeKB TD-7). Open: single-source the contract
  and delete the copies, or keep the duplication and its test guard — and either way decide what
  `RECORD_FIELDS` is for, since nothing reads it today.

**Structure and boundaries** (observed, and affirmed as the layout we keep):

- `app/` is a **flat by-layer package**, not feature-sliced: leaves (`config.py`, `models.py`,
  `db.py`, `sentiment.py`) → `repository.py`, `dummy_client.py`, `openrouter_client.py` →
  `service.py` → `routes.py` → `main.py` → `__init__.py`. The import graph is acyclic and points one
  way. At this size it is idiomatic FastAPI; the point at which `app/` should split by feature is an
  open point rather than an implicit decision.
- **One hexagonal seam**: the `SentimentClient` Protocol (`app/sentiment.py:56-61`) with two adapters,
  chosen in exactly one place (`get_client`, `app/service.py`). A new engine is a new adapter; routes,
  repository and page are untouched.
- **Connection ownership**: only the HTTP layer touches the `sqlite3` driver and the connection
  lifecycle (`get_connection`, `app/routes.py:70-76`); `repository` and `service` receive a
  connection. That boundary is also where the accepted thread-affinity risk (R-01) lives, so
  affirming it keeps connection handling from spreading.

**Errors** (observed, and the envelope is a binding rule — `discovered-rules.md`):

- Domain exceptions at the core, HTTP only at the edge, with the real mapping: `InvalidTextError` →
  422, `SentimentEngineError` → 502 and `SentimentAuthError` → 502 become envelope responses through
  handlers registered in `app/main.py:93-96`; `AuthExchangeError` is caught inline in the callback
  route (`app/routes.py:154`) and answered with a **302 redirect**, never the envelope; `ConfigError`
  is never mapped to a status at all — it is raised in `app/config.py:67,97` and surfaces as a
  **startup failure** through `load_settings()` in the lifespan (`app/main.py:66`), with its other
  raise site pragma-guarded as unreachable (`app/service.py:75-76`).
- One error envelope with four machine codes, for every error the application code raises. It does
  **not** cover framework-generated routing errors: `GET /nope` and `GET /static/missing.js` return
  404 `{"detail": "Not Found"}`, and `POST /health` returns 405 `{"detail": "Method Not Allowed"}` —
  reproduced against the real app with the repo's own harness, and not currently covered by any test.

**Secrets** (observed; the credential rule in `discovered-rules.md` makes the handling binding):

- The only place a real credential may live is the gitignored `config.local.toml` or process memory.
  Nothing in a codekb note, evidence file, review, test, README or commit may carry one.
- Redaction is by `__repr__` for every object that can hold a key (`Settings` `app/config.py:47`,
  `SessionCredential` `app/session_auth.py:131`, `OpenRouterClient` `app/openrouter_client.py:93-97`),
  and **"redacted" means "not rendered", not "not obtainable"**: `Settings.api_key` is a public
  dataclass field and `OpenRouterClient._api_key` a plain attribute, so `dataclasses.asdict`, `vars`
  or a debugger that dumps locals would expose the key. The tests pin the three surfaces that matter —
  repr, log records and the `/`, `/health`, `/auth/status` bodies — and the "never in a response
  body" property holds for the remaining routes **by construction** (no key field reaches a record),
  not by an endpoint sweep that does not exist.
- Detection of an accidentally committed secret is **zero**: no scanner, no pre-commit hook, no CI,
  no remote. Four fake keys in the tree already match OpenRouter's real shape —
  `tests/test_config.py:23` (`sk-or-v1-` plus 32 hex characters), shorter variants at
  `tests/test_auth_routes.py:28-29`, `tests/test_session_auth.py:26` and `tests/test_routes.py:136`,
  plus the placeholder at `README.md:96` — so any scanner adopted later needs those known fixtures
  allowlisted, or its first run is noise the team learns to ignore.

**Enforcement summary.** Today the only mechanical gate is `filterwarnings = ["error"]`. After the
`ruff` decision, formatting, linting and the security rules join it; the coverage floor joins once
the coverage tool lands in a place that actually runs.
