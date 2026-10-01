# Evidence — `260930-sentiment-v1` (practices-discovery, integrated)

> Final record of the practices-discovery stage: what each participant inspected, what they
> inferred, the eight decisions the human recorded at the interview with their rationale, the three
> blind reviews' findings and corrections, and everything still unresolved. The affirmed practices
> themselves are in `team-practices.md`; the three hard constraints are in `discovered-rules.md`.

## 1. What this discovery covered

| Item | Value |
|---|---|
| Intent | `260930-sentiment-v1` (scope `classic`, depth Standard) |
| Active space | `default` |
| Project type | Brownfield (declared in `aidlc/spaces/default/intents/260930-sentiment-v1/aidlc-state.md`) |
| Record dir | `aidlc/spaces/default/intents/260930-sentiment-v1/inception/practices-discovery/` |
| CodeKB root | `aidlc/spaces/default/codekb/very-cool-sentiment-analysis/` |
| Repo HEAD | `5b328fc96766679e98f3fc4effc39198a2811744` on branch `v1-classic` |
| Date | 2026-09-30 |
| Participants | Lead (`aidlc-pipeline-deploy-agent`), then three blind support reviews (`aidlc-quality-agent`, `aidlc-developer-agent`, `aidlc-devsecops-agent`), then the human interview |

**Method.** The lead pass was read-only and non-executing: it read the reverse-engineering
artifacts, the repository manifests and documentation, the git history and topology, and the AI-DLC
workspace records, **without opening application source or running the suite, the app or a linter**.
The three reviews added what the lead lacked: the developer and quality reviews opened the
application and test source, and the quality review executed the suite and measured coverage; the
developer and quality reviews each ran a scoped read-only probe (an error-envelope probe and a
throwaway coverage tracer, the latter deleted afterwards). The devsecops review stayed read-only,
like the lead. The human interview then supplied the intent the evidence could not.

## 2. What each participant inspected and inferred

### 2.1 Lead — `aidlc-pipeline-deploy-agent` (draft author)

**Inspected:** the five CodeKB artifacts (`code-structure.md`, `technology-stack.md`,
`dependencies.md`, `code-quality-assessment.md`, `architecture.md`, `business-overview.md`) and this
intent's `inception/reverse-engineering/developer-scan.md`; `pyproject.toml`, `README.md`,
`config.example.toml`, `.gitignore`, `AGENTS.md`; `git log` / `git show --stat` / `git diff --stat
main..HEAD` / `git status --porcelain`; `memory/org.md`, `memory/team.md`, `memory/project.md`,
`memory/phases/inception.md`, `.aidlc/scopes/aidlc-classic.md`, `aidlc-state.md`, `intents.json` and
the prior `260929-sentiment-analysis` intent record; and a root listing plus globs confirming the
absence of any CI, deployment or tooling configuration.

**Inferred (13 items, afterwards classified):** the branch-per-scope topology and the unmerged
`v1-classic`; one author identity and no second human reviewer; coarse milestone-shaped commits with
a scope-prefixed subject (n=2); `skeleton: off` for this intent and no skeleton artifact ever
produced; end-to-end verification nevertheless real and manual (the prior build started the server
on `127.0.0.1:8141`); implement-then-test ordering (from the prior plan's per-layer commands, no
scenario artifact anywhere); tests asserting against real SQLite and real served markup with doubles
only at process boundaries; coverage unmeasured while the scope expects 80 %; boundary and error
contracts pinned by tests; no deployment of any kind (no pipeline, environment, container or tag);
the recorded "no cloud / no Docker" constraint; twelve conventions holding across the application
modules; and none of them mechanically enforced. `memory/team.md` was empty of affirmed practice, so
there was no prior team preference to preserve — every choice had to be asked, not inherited.

**Limits the lead declared, and which the reviews later closed:** no execution evidence (the suite's
state was unverified), no application source opened first-hand (conventions were inherited from the
CodeKB), and a two-commit, one-day history that makes every cadence claim the weakest class of
inference available.

### 2.2 `aidlc-developer-agent` (code and module-organization angle)

**Inspected and executed:** all 12 `app/*.py`, `tests/conftest.py` and every `tests/test_*.py`
header, `pyproject.toml`, `README.md`; an AST scan for return annotations and docstrings; an
import-graph rebuild; and one scoped, read-only probe against the real application (using the repo's
own in-process harness) to test the error-envelope claim. Measured a read-only `ruff 0.16.9` run
(`--isolated --no-cache`). Did not run the suite and did not edit source.

**Found:** the draft's Code Style claims about annotations (2), underscore-private helpers (4),
naming (5), parameterised SQL (8), redacted reprs (9), class-less pure helpers (11) and freeform
docstrings (12) were independently reverified as correct; the enforcement gap was confirmed and
measured. Seven claims were corrected (§4.1). It also surfaced structural conventions the draft did
not name at all: the flat by-layer package with an acyclic import graph, the single `SentimentClient`
hexagonal seam chosen in one place, and connection ownership sitting in the HTTP layer — the boundary
where the accepted thread-affinity risk (R-01) lives.

### 2.3 `aidlc-quality-agent` (test/quality angle)

**Inspected and executed:** the repo at HEAD `5b328fc` with `.venv` (CPython 3.14.7, pytest 9.1.1).
Ran `.venv/bin/python -m pytest` → **52 passed in 0.33 s, exit 0**, attributable to the committed
tree (`git status --porcelain` showed only `aidlc/` paths dirty). Measured line coverage with a
throwaway standard-library tracer (`trace.Trace` + `threading.settrace` + `dis` line starts), then
deleted it. Grepped `tests/` for thread/concurrency terms. Modified no application source.

**Found:** the suite is green and essentially free, which closed the lead's "today's suite state is
unverified" caveat; measured coverage of 70.2 % across all 12 modules and 86.5 % excluding the live
client, which converted the draft's blind "is the floor wanted?" question into the real decision —
*what counts in the denominator*; four deliberate exclusions (live engine, PKCE exchange, browser
script, and mirroring them, `app/service.py`'s live-mode branch); the untested 502 handlers; **no
concurrency test at all**, mapping onto R-01; no test starting uvicorn or proving `uvicorn app:app`
resolves; and invisible coverage regressions. It also documented eight test patterns worth preserving
(§4.2). Notably, the tracer must use `threading.settrace`: FastAPI runs every endpoint here in an
anyio worker thread, and a naive in-process measurement reads `app/routes.py` at 47 % instead of 91 %.

### 2.4 `aidlc-devsecops-agent` (security and supply-chain angle)

**Inspected:** the four draft artifacts, the reverse-engineering artifacts, the scan handoff and the
application source and manifests directly — `.gitignore`, `app/config.py`, `app/session_auth.py`,
`app/main.py`, `app/routes.py`, `app/service.py`, `app/openrouter_client.py`, `app/static/app.js`,
`pyproject.toml`, `README.md`, the test files anchoring secret handling — plus `git remote -v` and
globs for scanner/CI/pre-commit configuration. Did **not** run the suite, the app or a scanner, and
kept the empirical layer separate from the code-reading layer.

**Found:** the secret-handling design holds for the surfaces it covers (never rendered, never logged,
never in a record shape, key file gitignored and asserted by `git check-ignore`) but **does not hold
for the workflow's own record files**: `aidlc/`, `codekb/`, `README.md`, `app/` and `tests/` are all
tracked, so a real key pasted into any of them commits by default, with no scanner, hook, CI or remote
to catch it — and unlike a code bug that is irreversible. Two qualifications it asked the draft to
carry: "redacted" means "not rendered", not "not obtainable" (`Settings.api_key` is a public dataclass
field; `OpenRouterClient._api_key` a plain attribute), and the in-memory session credential is
process-wide, so anything that can reach loopback can spend the key through `POST /analyze` — a
deliberate consequence of localhost-only, and the reason loopback binding belongs in a rule rather
than a README sentence. It also named the gaps the draft never mentioned: static analysis, secret
scanning, dependency pinning/updating, and what data leaves the machine (§4.3). It recommended
exactly one hard constraint (the credential rule) and advised against minting rules for the other
observed conventions — but the human went further and affirmed three (§5.8).

## 3. Inferences, source by source

### 3.1 Reverse-engineering artifacts (the declared upstream)

All under `aidlc/spaces/default/codekb/very-cool-sentiment-analysis/`, synthesised from the developer
scan at `aidlc/spaces/default/intents/260930-sentiment-v1/inception/reverse-engineering/developer-scan.md`.

| Source | What it contributed |
|---|---|
| `code-structure.md` | Module layout and sizes (12 modules, 1 498 lines; 10 test files, 1 407 lines); the observable conventions; the non-application trees that must not be mistaken for code. |
| `technology-stack.md` | Python ≥ 3.11 (running on 3.14.7), FastAPI + uvicorn, stdlib `sqlite3` and `tomllib`, vanilla JS with no build step; pytest as the only dev dependency; verified absence of linters, formatters, type checkers, CI/CD, coverage tooling and containers. |
| `dependencies.md` | The declared cap (2 runtime + 1 dev direct packages, no HTTP client library, no lockfile); the dependency-policy constraints; the service dependencies whose only failure behaviour is a failed request. |
| `code-quality-assessment.md` | The scorecard (test breadth good, coverage of risk weak, lint/CI absent, documentation strong); the 80 % floor with no measurement to verify it; the explicit untested areas; the technical-debt register, including the zero-coverage live client (TD-1, TD-5, TD-7). |
| `architecture.md` | The single-process layered monolith with one hexagonal seam, the acyclic dependency direction, the rejected alternatives, and the live-engine failure branches. |
| `business-overview.md` | The single-user localhost-only product shape; twelve business rules; the actors; the four code-vs-intent divergences (the in-app authorization flow, config rule 5, class-name drift, a stale comment). |

One internal contradiction in the sources was caught by the developer review and resolved in favour
of the TD-7 half: `code-quality-assessment.md`'s "Consistency Positives" says `RECORD_FIELDS` is
"used by storage and the wire", while its own TD-7 says the record contract has "four hand-written
copies". The latter is correct (§4.1, correction 3).

### 3.2 Git history and topology

| Observation | Command | Practice relevance |
|---|---|---|
| 2 commits, 1 author identity `very-cool-sentiment-analysis <demo@local>`; no merge commits; no tags | `git log`, `git shortlog`, `git tag` | No branch/merge policy is observable; a single identity means no second human review exists. |
| `main` = `0268a5d Initial commit` (harness + memory only); `v1-classic` (HEAD, one ahead) = `5b328fc` (application, tests, docs, prior intent record) | `git show --stat`, `git diff --stat main..HEAD` | The application is not on `main`; the working model is branch-per-scope, unmerged. |
| Working tree dirty: modified `memory/project.md`; untracked `codekb/` and the live intent record | `git status --porcelain` | Commit cadence is coarse and lags the work. |
| Commit subjects `v1-classic: …` and `Initial commit` | `git log --format` | Weak scope-prefixed subject signal (n=2). |
| Commits dated 2026-09-29 15:03 and 2026-09-30 12:35 (+05:00) | `git log --date=iso` | The open branch is about a day old; nothing establishes a branch-lifetime norm. |
| No git remote | `git remote -v` | "Which CI platform" presupposes a hosting decision that has not been made. |

### 3.3 Manifests, documentation and configuration absence

`pyproject.toml`: PEP 621 metadata, `version = "0.1.0"`, `requires-python = ">=3.11"`, the
dependency-cap (NFR3) comment, the `dev` extra carrying only `pytest`, and
`[tool.pytest.ini_options]` with `testpaths`, `addopts = "-q"` and `filterwarnings = ["error"]`; no
linter, formatter, type-checker or coverage section. `README.md` (189 lines): install/run/test
commands, the two engine modes, six configuration-resolution rules, the HTTP surface table, storage,
and a "Notes" section stating that the live client is covered by code review and a manual live smoke
run, that the PKCE exchange is injected as a double, and that browser-side `app.js` execution is not
tested. `config.example.toml`: committed placeholder, `api_key = ""`, documenting that
`config.local.toml` is the only place a key may live. `.gitignore`: `config.local.toml`, `/data/`,
caches, plus the AI-DLC committed-vs-ignored split. `AGENTS.md`: harness onboarding, including the
commit-the-`aidlc/`-tree expectation.

**Verified absence** at the repository root: no `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`,
`buildspec.yml`, `cdk.json`, `.circleci/`, `.travis.yml`, `azure-pipelines.yml`, `Dockerfile`,
compose file, Kubernetes manifest, `Makefile`, `tox.ini`, `setup.cfg` or `.pre-commit-config.yaml`;
no `ruff.toml`/`.ruff.toml`, `mypy.ini`, lockfile (`uv.lock`, `poetry.lock`, `pdm.lock`),
`requirements*.txt`, `.gitleaks.toml` or Dependabot/Renovate config either. The tracker directory is
the generated, stale `very_cool_sentiment_analysis.egg-info/`. The only mechanical gate in the
project is `filterwarnings = ["error"]`.

### 3.4 Workspace records

| Source | What it contributed |
|---|---|
| `memory/org.md` | The framework defaults, treated as candidates only: trunk-based short-lived branches with squash-merge to `main`; per-scope testing defaults (`test-after`; 80 % line floor + CI before merge for the `classic` family); deploy-on-merge to staging with manual production approval; code style deferred to project configuration, linted "in CI before merge". |
| `memory/team.md` | Empty of affirmed practice — every section body is HTML-comment placeholder text only (empty-template rule, `aidlc-shared/rules-reading.md` § 1). No baseline to preserve. |
| `memory/project.md` | A project `## Tech Stack` line (Python, learned 2026-09-29) and five `## Corrections` entries from earlier stages — including R-01 (sqlite3 connection thread affinity) accepted as a known limitation, which is the precedent behind the testing gap below. |
| `memory/phases/inception.md` | Phase guardrails: testable requirements, ADRs with alternatives, Given/When/Then acceptance criteria, traceability. They shape artifact formats, not test cadence. |
| `.aidlc/scopes/aidlc-classic.md` | `skeleton: off`, `review_cap: advisory`, `guard_policy: relaxed`, `sensors: on`, `learnings: on`, `summary_confirmation: off`; skips Ideation, CI Pipeline and all seven Operation stages. |
| `aidlc-state.md` | Brownfield, `classic`, Standard depth, Standard test strategy, `Construction Checkpoints: enabled`, `Construction Iteration: unit-major`, `Construction Execution: serial`, `Construction Verification Command` **unset** (now supplied by the interview — §5, Q3). |
| Prior intent `260929-sentiment-analysis` (scope `poc`) | The richest behavioural evidence: the one-person stakeholder map; a Code Generation plan of per-layer "implement-then-test" commands; a Build and Test record with 27 tests green plus a live end-to-end smoke run on `127.0.0.1:8141`; the recorded "localhost only, no auth/cloud/Docker" requirement; and review R-01, grounded by running the server under concurrent load. |
| `intents.json` | Two intents; the `poc` scope has no practices-discovery, which is why no prior affirmation exists. |

### 3.5 Inferences and their strength

| # | Area | Reading | Strength | Status after the interview |
|---|---|---|---|---|
| I-1 | Way of Working | A branch named for the work item carries one large unmerged commit; the framework default is neither followed nor refused. | needs human decision | **resolved** — one branch per intent/scope, squash, scope-name tag (Q1) |
| I-2 | Way of Working | One author identity, one-person stakeholder map: no second human reviewer. | inferred | carried as fact, not as an affirmed review rule |
| I-3 | Way of Working | Coarse, milestone-shaped commits with a scope-prefixed subject. | inferred (n=2) | partly resolved — squash fixes `main`; message convention still open |
| I-4 | Walking Skeleton | No thin-slice ceremony for this intent (`skeleton: off`); none ever produced. | observed | **superseded as a standing rule** — slice first by default on future work (Q2) |
| I-5 | Walking Skeleton | End-to-end verification is real and manual (prior live smoke run). | observed | **strengthened** — one recorded verification command (Q3) |
| I-6 | Testing Posture | Ordering is implement-then-test. | inferred | **corrected** — `custom`: acceptance/API first, unit after (Q4) |
| I-7 | Testing Posture | Assertions against real storage and real served output; doubles only at process boundaries. | observed | affirmed as preserved practice |
| I-8 | Testing Posture | Coverage unmeasured while the scope expects 80 %; the live engine untested by design. | observed | **resolved** — tool + whole-app 80 % floor + CI job (Q5) |
| I-9 | Testing Posture | Boundary and error contracts pinned by tests. | observed | kept, with the security review's C1 scope fix |
| I-10 | Deployment | No deployment: no pipeline, environment, container or tag; local `uvicorn` over a gitignored SQLite file. | observed | **resolved** — localhost checkout, commit is the release (Q6) |
| I-11 | Deployment | The "no cloud / no Docker" requirement constrains future automation. | observed (prior record, not memory) | **resolved** — now a binding rule (Q8-B) |
| I-12 | Code Style | Twelve conventions hold consistently across the application modules. | observed | kept, with seven corrections (§4.1) |
| I-13 | Code Style | None of them is mechanically enforced. | observed | **resolved** — adopt `ruff`, format + lint + security rules (Q7) |

## 4. The three reviews: findings and corrections

### 4.1 `aidlc-developer-agent` — seven corrections, plus structural conventions

| # | Draft claim | Correction | Disposition |
|---|---|---|---|
| 1 | "One error envelope … covers every non-2xx response" | It covers every error the application raises, and nothing else. Handlers are registered for four exception types (`app/main.py:93-96`; `error_response` `app/routes.py:41-57`). Reproduced against the real app: `GET /nope` → 404, `POST /health` → 405, `GET /static/missing.js` → 404, all `{"detail": …}`. The draft's consequence ("a handler that bypassed it would break both page and tests") holds only for app-raised errors; no test covers a 404. | Applied in `team-practices.md` `## Code Style` (Errors), and scoped in the `discovered-rules.md` Mandated line. |
| 2 | "Module constants … documented with `#:` comments", incl. "the TTL constants in `app/session_auth.py`" | Over-claimed: 39 `UPPER_CASE` constants, **20 with no adjacent `#:`**; `EXCHANGE_TIMEOUT_SECONDS` (`app/session_auth.py:53`) is one of them, so the example was half wrong. | Applied — the bullet now states what is and is not documented. |
| 3 | "`app/` does not import pydantic … sharing one field list" | Pydantic half verified (zero references; stdlib dataclasses). The "one field list" is **not** mechanically shared: `RECORD_FIELDS` (`app/models.py:20`) is referenced nowhere, and the contract exists as four hand-written copies (`models.py:47-62`, `models.py:64-77`, `ANALYSES_COLUMNS` + `CREATE TABLE` in `app/db.py:15-48`), kept in sync by tests (CodeKB TD-7). | Applied — "one documented contract, four hand-written copies"; the single-source decision recorded as open. |
| 4 | "Every module … naming its single responsibility and the requirement ids it satisfies" | Two exceptions: `app/__init__.py` (10-line re-export shim, no "Single responsibility" line) and `app/session_auth.py` (line present, no requirement id at all — it postdates the prior intent). Draft open question 4 is therefore present drift, not future risk. | Applied — 11 of 12, exceptions named; also noted `app/main.py:33-34`'s now-false "no authentication … exists anywhere in this app". |
| 5 | "Domain exceptions … mapped to status codes only in `app/routes.py`" | Imprecise: three of five become envelope responses through handlers in `app/main.py:93-96`; `AuthExchangeError` is caught inline (`app/routes.py:154`) and answered with a **302 redirect**; `ConfigError` is never mapped to a status — it surfaces as a **startup failure** via `load_settings()` (`app/main.py:66`), with its other raise site pragma-guarded unreachable (`app/service.py:75-76`). | Applied — the real mapping is written out. |
| 6 | "twelve application modules" and "52 test functions across 10 files" | 12 includes the `app/__init__.py` shim (conventions live in 11 substantive modules; `app/static/` is 360 lines, untested by design). 10 files includes `tests/conftest.py`; the 52 functions live in **9 test modules**. | Applied — counts aligned with the CodeKB so later stages cite stable numbers. |
| 7 | "English prose docstrings … freeform" | `tests/conftest.py`'s docstring uses Sphinx `:func:` roles while `app/` uses backticks — one file is a one-off. | Applied — recorded as a one-off with the decision left open. |

**Unclaimed conventions the developer surfaced (now in `## Code Style`):** no bare `except` and no
broad catch, with `from exc` on all 8 wrapping raises; no `print()` in `app/` and the key never
logged; no junk-drawer `utils.py`/`helpers.py` (a pure helper lives in its owning module); import
groups ordered stdlib / third-party / `app.*` but **not** isort-clean within groups in 4 files;
4-space indent, double quotes, trailing commas, longest line 109 chars, 10 lines over 88; and two
`# pragma: no cover` plus two `# type: ignore[method-assign]` markers anticipating tooling that does
not exist. **Structural conventions:** the flat by-layer acyclic package, the single hexagonal seam
(`SentimentClient` Protocol, `app/sentiment.py:56-61`, chosen only in `get_client`), and connection
ownership confined to the HTTP layer (`get_connection`, `app/routes.py:70-76`) — the boundary where
R-01 lives.

**Measured enforcement baseline:** 16 ruff findings, 9 auto-fixable (`B008`×6, `I001`×4, `UP035`×2,
`UP037`×2, `SIM117`×1, `F401`×1), `ruff format --check` reformatting 12 of 22 files. The `B008` trap
(all six are `Depends(...)` in defaults, FastAPI's documented idiom) and the conflict between the
org "run in CI" rule and a scope with no CI stage are the two decisions the interview had to make.

### 4.2 `aidlc-quality-agent` — measured coverage and the concurrency gap

**Corrections:**

1. "52 test functions across 10 files" → 52 functions in 9 `tests/test_*.py` modules plus the
   `conftest.py` harness (0 tests); the CodeKB scorecard words it the same way. *Applied.*
2. The `test-after` inference should not be strengthened by evidence (a snapshot cannot show
   ordering) — but the suite's observed mechanics should be written down, because they are what later
   stages must preserve. *Applied* — the harness's shape, the offline guard, `tmp_path` isolation,
   the two `monkeypatch` uses, zero mocks, and the `data-testid` page contract are all recorded.
3. Boundary discipline confirmed by file read: 422 with a row-count assertion of 0, `field ==
   "query.limit"` with no silent clamp, newest-first ordering, `/health` reporting the resolved mode,
   and redaction asserted in repr, log records and `record.__dict__`. *Applied.*
4. `addopts = "-q"` buys quiet output at the cost of per-test names in a failure log — relevant once
   a pipeline parses the output. *Applied as a note.*

**Measured coverage (12 modules, all lines):** `openrouter_client.py` 0/149 (0.0 %), `service.py`
67.3 %, `__init__.py` 75.0 %, `session_auth.py` 78.3 %, `repository.py` 82.2 %, `routes.py` 90.9 %,
`main.py` 90.2 %, `config.py` 91.2 %, `sentiment.py` 91.7 %, `db.py` 96.2 %, `models.py` 97.9 %,
`dummy_client.py` 97.6 %; **total 556/792 = 70.2 %**, or **86.5 %** excluding the live client. Two
method notes: the tracer must use `threading.settrace` (endpoints run in anyio worker threads), and
the numbers are ± a few points against `coverage.py` while the decision-relevant gap (70 % vs 86 %)
is far outside that error.

**Gap it named, which the draft omitted:** **no concurrency test exists at all**
(`grep -rn "thread\|concurrent\|ProgrammingError" tests/` returns nothing), while R-01 — per-request
`sqlite3.connect` on default thread affinity (`app/routes.py:70-76`, `app/db.py:51-63`) — is the one
defect this workspace has ever recorded. *Applied* in `## Testing Posture` (test types) and carried as
the precedent behind the unanswered regression policy.

**Other findings:** the two 502 handlers (`app/routes.py:199-213`) appear unexercised by the
approximate measurement, flagged as the least-trusted part of it (line-level attribution) and worth a
direct check with real coverage; no test starts uvicorn or proves `uvicorn app:app` resolves; and
coverage regressions are invisible today.

### 4.3 `aidlc-devsecops-agent` — C1–C3, plus the named gap

| ID | Finding | Disposition |
|---|---|---|
| **C1** | Over-claim: "the API key never appears in […] **any** response body". The assertion covers `/`, `/health` and `/auth/status` (`tests/test_auth_routes.py:120-127`); `/analyze` and `/analyses` cannot be exercised with a live credential because the offline guard forbids the outbound call. The property holds for them **by construction** (no key field reaches a record shape). | Applied — cited as construction, not as an endpoint sweep. |
| **C2** | Imprecision: "redacted **by construction**" should scope to the rendered surface, and not be read as protection against `dataclasses.asdict`, `vars(client)` or a debugger dumping locals. | Applied — "redacted means not rendered, not not-obtainable", with the public field and plain attribute named. |
| **C3** | Unsupported framing: the "no cloud / no Docker" constraint lives in the prior intent's requirements record (`260929-sentiment-analysis`), **not** in `memory/project.md`, `memory/team.md` or any scope file, so it constrained nothing mechanically. | Resolved — the human affirmed localhost-only as a binding rule (Q8-B), so it now binds through `discovered-rules.md` → `project.md` Mandated. |
| **C4** | Gap: the draft's five areas never mentioned static analysis, secret scanning, dependency pinning/updating, or what data leaves the machine. | Applied — static analysis in `## Code Style` (ruff `S` rules) and secret scanning under Secrets; dependency pinning and data egress in `## Deployment`. |

Also applied from that review: the secret-handling property table (holds for rendering/logging/record
shapes; **does not hold** for the tracked workflow record files, with no detection anywhere); the
irreversibility argument that justified the one recommended rule; the four fake fixtures matching
OpenRouter's real key shape, which force an allowlist on any future scanner; the accepted low risks
(no CSP, no CSRF/`Origin` check on `POST /auth/disconnect`, no PKCE `state`, Host-derived
`callback_url`) recorded rather than turned into work items; and its recommendation not to mint rules
for parameterised SQL, pydantic, or repr-redaction — a recommendation the human partially overrode by
affirming the envelope as well (§5.8).

## 5. The interview: decisions and rationale

Source: `<record>/practices-discovery-questions.md`, complete, with the human's own added detail. The
answers are the authoritative record of intent; the rationale below is taken from the recorded answer
and from the option it selected.

**Q1 — Versioning and landing.** *Answered X (other): one branch per intent or scope, merged into
`main` when the work is finished, squashed to a single commit on `main`, and that commit tagged with
the scope name (e.g. `v1-classic` squashed into one commit, tagged `v1-classic`).*
Rationale: the framework default (short-lived branches resolved in 1–2 days) assumes Bolt-sized
increments; this project's unit of work is a whole intent or scope, which is why one branch per
scope fits better. Squashing keeps `main` linear, and the scope-name tag makes the release point
recoverable from `main` alone — something the framework default does not provide, because it carries
no tag.

**Q2 — Walking skeleton.** *B: yes, build a thin end-to-end slice first by default on future work;
this run stays as it is.* Rationale: the failure mode a slice prevents — pieces that do not connect
— is the expensive one, and here it is cheap to prevent because the app already runs end to end. The
scope flag `skeleton: off` still governs this intent, so the default changes future work without
disturbing the run in flight.

**Q3 — Verification command.** *A: install, run `pytest`, then start the app locally and exercise the
changed path; record it as the project's verification command.* Rationale: the suite never starts a
server and never resolves `uvicorn app:app`, so `pytest` alone cannot prove a change works end to
end; the command must include a local live exercise. This also fills the intent's previously unset
`Construction Verification Command`. Recorded in `team-practices.md` `## Testing Posture` and
`## Walking Skeleton`.

**Q4 — Test cadence.** *C (`custom`): acceptance/API tests first, lower-level unit tests after the
implementation.* Rationale: the acceptance surface is the stable contract, so it is written first;
the lower-level unit tests follow the implementation details they pin. Affirmed as
`- **Methodology**: custom` with the one-line ordering sentence.

**Q5 — Coverage floor.** *A: add a coverage tool, count the whole application (floor fails today at
~70 %), enforce 80 %, and run the suite plus the floor in a CI job.* Rationale: counting the whole
application keeps the floor from being satisfied by omitting an inconvenient module; the consequence
is accepted rather than engineered away — covering the live client becomes construction work in this
scope. The open point that follows: this scope skips the CI Pipeline stage, so where the CI job lives
is for design and build to place. Measured baseline recorded: 70.2 % all modules / 86.5 % excluding
the live client.

**Q6 — Release story and local data.** *A: localhost checkout is the whole story; a commit is the
release; deleting `data/sentiment.db` is acceptable recovery.* Rationale: one local user, no second
deployment target, and the SQLite file is local history that can be recreated — so a migration or
backup mechanism would buy nothing at this stage. The release point itself is the squashed,
scope-tagged commit from Q1.

**Q7 — Code style enforcement.** *A: adopt `ruff` for formatting and linting, with an explicit rule
set including its security rules, run as a pre-commit hook or a stage check.* Rationale: one dev
dependency covers formatting, linting and a static-analysis floor (the `S` rules) — the cheapest
enforcement available for a project that has none — and the dependency cap it might collide with is a
runtime cap, so dev tooling is not an NFR3 violation (though the NFR3 comment and the README's
package count must be corrected in the same change). The org rule's "run in CI" is unmet by
construction in this scope, hence the pre-commit-hook-or-stage-check framing.

**Q8 — Binding constraints.** *A, B, C: the credential rule, localhost-only, and the single error
envelope.* Rationale: these three are the constraints whose violation is consequential or
irreversible — a pasted credential cannot be un-compromised, a non-loopback bind or an auth change
invalidates the whole threat model, and a second error shape breaks the one contract every client
reads. The other candidates (pydantic, parameterised SQL, repr-redaction) stay observations: a test
already catches their violation, so a rule adds cost without changing behaviour. Notable divergence
from the reviews: the security review recommended exactly one rule and advised against the envelope;
the developer review's shortlist had eight. The human's three are what bind.

## 6. Open points carried to integration — and their disposition

| Open point (from the questions file) | Where it now lives |
|---|---|
| The whole application is under the 80 % floor, so tests for the live Jev client become construction work, and the floor must run in a CI job even though this scope skips the CI Pipeline stage — where that job lives is an open point for design and build. | `team-practices.md` `## Testing Posture` (Coverage and explicit-untested bullets); stated as an open point, plus the coverage numbers so construction can size the work. |
| Q4's `custom` needs its ordering sentence (acceptance/API first, lower-level unit tests after implementation). | `team-practices.md` `## Testing Posture` — `- **Ordering**:` one-liner; `Methodology: custom`. |
| Q1's answer adds a scope-name tag on the merged commit, which the framework default does not carry. | `team-practices.md` `## Way of Working` — the tag is named and flagged as ours, so later stages do not assume a tag exists by default. |

## 7. Unresolved uncertainty

**Interview answers that leave a decision to a later stage:**

1. **Where the coverage CI job lives** — no CI exists and `classic` skips the CI Pipeline stage; the
   candidates are an `addopts`-wired local floor (`--cov=app --cov-fail-under=80`, ~1 s, no CI at
   all), a pre-push hook, or a pipeline that does not exist yet.
2. **What counts in the denominator, mechanically** — the human's answer puts the whole application
   under the floor, but the *instrumentation* still needs a policy: whether to pin
   `[tool.coverage.run] source = ["app"]`, how to treat the live client while it is being covered, and
   what to do with the existing pragmas (`app/repository.py:20`, `app/service.py:75`,
   `tests/test_config.py:128`) now that a tool will read them.
3. **Who runs the manual live smoke run, and when** (pre-merge or pre-release) — the suite cannot,
   and the exclusions stay.
4. **Where the `ruff` gate runs** — pre-commit hook or a lint step inside Build and Test; the
   interview fixed the tool, the rule set and its inclusion of security rules, but not the host.
5. **Two settings that must land with the `ruff` commit** — line length (88 flags 18 lines, 100
   changes 2) and the `B008`/`Depends` policy (`extend-immutable-calls` for `fastapi.Depends` is the
   recommended answer, but it is not yet selected).
6. **The dev/runtime dependency-cap reading** — NFR3 caps runtime dependencies; the answer assumes
   that reading, and the `pyproject.toml` comment plus the README's "exactly three packages" line
   must be corrected in the same change as any tooling addition.

**Open questions the reviews raised that the interview did not answer:**

7. **Bug-regression policy** — must every defect ship a reproducing test? R-01 is the precedent: a
   concurrency defect recorded and accepted, with no concurrency test in the suite today.
8. **The record contract** — single-source `RECORD_FIELDS` (and delete the copies) or keep the manual
   duplication and its test guard; and either way, decide what `app/models.py:20` is for, since
   nothing reads it today.
9. **Module organisation threshold** — `app/` stays flat one-file-per-layer and at what size that
   changes; the layout itself is affirmed, the trigger is not.
10. **Requirement-id citations in docstrings** — keep citing the prior intent's `FR…` ids
    (`app/session_auth.py` already cites none; `app/main.py:33-34` is now false), or switch to a
    lighter rule — and who updates a comment when the code moves.
11. **A type checker** — the annotation convention is 100 % applied with zero suppressions in `app/`,
    so enforcement is nearly free; the two `# type: ignore` comments in `tests/conftest.py:142,146`
    already anticipate one. Not adopted by the interview.
12. **Docstring cross-reference style** — `tests/conftest.py` uses Sphinx `:func:` roles and `app/`
    uses backticks; pick one, or accept the one-off.
13. **Review before merge, commit-message convention and branch age** — no second human exists, and
    the interview fixed the branch/merge/tag shape but not the review, subject or lifetime rules.
14. **Supply chain** — keep floating floors and audit by hand, or add a lockfile plus a periodic
    audit; and who owns dependency updates and the emergency-patch path for a CVE in a package that
    runs beside the key.
15. **Secret scanning** — whether a scanner is required in a repo with no remote and no CI (a
    pre-commit hook is the only place it can run today), and if so, the documented allowlist for the
    four fake fixture keys.
16. **Data retention and egress** — is "input text stored unencrypted locally and, in live mode, sent
    to OpenRouter" acceptable as the standing posture, or is a retention/delete obligation wanted?
17. **A git remote and a CI platform** — the platform question presupposes a hosting decision that
    has not been made; the answer determines whether secret scanning and dependency automation can be
    hosted at all.
18. **Whether the live engine stays a supported v1 mode** — if it does, its 0 % module is less
    acceptable under any denominator and the manual smoke run becomes a standing obligation.

**Measurement uncertainty that a later stage should re-check with real tooling:**

19. The two 502 handlers (`app/routes.py:199-213`) appear unexercised by the approximate measurement,
    which the quality review flagged as its least-trusted result — line-level attribution, not
    aggregate. Worth a direct check once `pytest-cov` is installed.
20. Coverage figures are ± a few points against `coverage.py` (`dis` line starts vs statement
    coverage); the decision-relevant gap (70 % vs 86 %) is far outside that error, but the exact
    numbers are not.
21. The suite was green (52 passed in 0.33 s) at `5b328fc`; a later commit changes that, and no gate
    currently notices.
22. No secret scanner, linter or SAST tool was actually run by the security review, and `ruff` was
    run out-of-tree with `--isolated --no-cache` — so no finding was produced by a tool the project
    itself configures. That is a property of the project, not of the reviews.

## 8. Caveats

- **The lead pass executed nothing.** Conventions inherited from the CodeKB were cross-checked for
  internal consistency but not re-read line-by-line; the developer review later re-verified them
  first-hand, and the quality review later executed the suite.
- **Small-sample git history.** Two commits, one author, one day of branch age — every cadence claim
  (I-2, I-3, branch lifetime) is the weakest class of inference available, and the interview's Q1
  answer is the only thing that raises it above accident.
- **`memory/team.md` was empty of affirmed practice**, so there was no baseline to preserve and no
  re-run context: every choice in `team-practices.md` comes from the interview, not from precedent.
- **Vocabulary.** The process nouns in `memory/*.md` ("Bolt", "walking skeleton", "guard policy") are
  framework terms; the questions were asked in plain language and the answers are recorded in the
  team's own words.
- **The security review's distinction is preserved in this record:** what the code guarantees about
  the secret (checked, anchored to files) is kept apart from what the project guarantees about its own
  records (nothing, today) — the second is why the credential rule exists.
