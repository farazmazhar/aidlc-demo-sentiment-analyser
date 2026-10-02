# Evidence — Practices Discovery

> **Integrated at Step 5 for intent `261001-analytics-layer`.** What the lead
> inspected, what each of the three blind spokes inspected independently, what the
> human decided, what was corrected, and what remains unresolved. Nothing here is
> affirmed until the gate. Numbers were re-verified at `beeb587` during integration;
> every correction listed under "Corrections applied" was checked against the source
> before it was written into `team-practices.md`.

## What this turn inspected

**Reverse-engineering artifacts (fresh full rescan, all eight).**
`business-overview.md`, `architecture.md`, `code-structure.md`, `technology-stack.md`,
`dependencies.md`, `code-quality-assessment.md`, `component-inventory.md`,
`api-documentation.md`, all under `aidlc/spaces/default/codekb/sentiment-opencode/`.
The store's own header records that the counts were re-measured at `beeb587`, so they
were treated as a claim to check rather than as fact.

**The repository directly**, because the stage requires evidence for branching
strategy, deployment cadence, environment topology and visible conventions:

| Inspected | How |
|---|---|
| Git history | `git log` (full bodies, author/committer identity and dates), `git rev-list --count HEAD`, `git tag -l`, `git for-each-ref refs/tags` with peel, `git branch -a`, `git remote -v`, `git status --porcelain` |
| CI / deployment configuration | `ls -a` at the root plus a recursive sweep for `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci`, `azure-pipelines.yml`, `.pre-commit-config.yaml`, `Makefile`, `tox.ini`, `noxfile.py`, `Taskfile*`, `justfile`, `Dockerfile*`, `compose.y*ml`, and every `*.yml`/`*.yaml` — **zero matches** outside the AI-DLC harness tree |
| Test suite | `.venv/bin/python -m pytest -q` (full run, re-measured during integration) |
| Lint / format | `.venv/bin/ruff check app tests`, `ruff format --check app tests`, `ruff --version`, `ruff rule TID251` |
| Manifest and tool config | `pyproject.toml` in full; `.gitignore` (application section); `config.example.toml` |
| Contract of record | `README.md` in full, including the `## HTTP surface` table (19 rows) and the single-line verification command |
| Local store state | `data/sentiment.db` queried directly for `schema_meta.version`, column list, row count, index list |
| Conventions | `grep` for suppressions (`pragma: no cover`, `noqa`, `type: ignore`, file-level `ruff: noqa`), `from __future__ import annotations` per module, `Single responsibility:` lines, every `except` in `app/`, `print(`, `TODO/FIXME/HACK/XXX`, `ensure_page_state`, `V1_PREFIX`, concurrency terms in `tests/`, and `CREATE INDEX` across `app/` and `tests/` |
| Installed dependency closure | `.venv/bin/python -m pip list --format=freeze`; `importlib.metadata.requires("fastapi")` read from installed metadata, not from documentation |
| Lint probes | `ruff check --stdin-filename app/_probe.py -` against the project's own config, so `per-file-ignores` did not apply and no file was written to the repo |
| Active-space baseline | `aidlc/spaces/default/memory/team.md` (all five sections, non-empty) and `memory/project.md` |
| Prior run of this stage | `aidlc/spaces/default/intents/260930-sentiment-v1/inception/practices-discovery/` |
| Current intent's already-affirmed inputs | `aidlc-state.md`, `ideation/intent-capture/intent-statement.md`, `ideation/feasibility/constraint-register.md` (C-1…C-12), the prior intent's `operation/deployment-execution/` artifacts |
| Scope definitions | `.aidlc/scopes/aidlc-{feature,classic,express}.md` |

**Measurements, reproduced at `beeb587` (CPython 3.14.7, ruff 0.16.9):**

```
pytest -q                            → 118 passed; TOTAL 679 stmts, 27 miss, 96.02% (floor 80%)
ruff check app tests                 → All checks passed!
ruff format --check app tests        → 24 files already formatted
git rev-list --count HEAD            → 2
git branch -a                        → * main
git remote -v                        → (empty)
git log --format='%an <%ae>' | sort -u → Faraz Mazhar <farazmazhar@users.noreply.github.com>
except BaseException in app/         → app/db.py:163   (exactly one)
grep -rn ensure_page_state           → no match anywhere in the repository
from __future__ import annotations   → 11 of 12 app/ modules (app/__init__.py is the exception)
CREATE INDEX in app/ or tests/       → no matches
importlib.metadata.requires("fastapi")
  → includes 'opentelemetry-api>=1.44.0' as a non-extra hard dependency
pip list (runtime closure)           → 14 distributions, opentelemetry-api==1.45.0
LICENSE / COPYING                    → none
```

## What each participant inspected or inferred

### The lead (pipeline-deploy)

Inspected all of the above. **Inferred**: the branching strategy is not merely
unviolated but exercised twice; the deployment topology (one process, one loopback
bind, one SQLite file, no tiers); the deployment cadence (one squashed commit per
finished scope *is* the release); the localhost deploy procedure the `express` intent
followed; and that `ci-pipeline` / `deployment-pipeline` now have a stage to live in
because `feature` marks all 33 stages EXECUTE. **Not inferred from a snapshot**:
any maximum branch age, any commit-signature or co-author expectation, the order in
which individual tests were written, and what a thin slice means when the work is a
layer on top of a working app.

### aidlc-quality-agent (spoke, blind)

Re-measured rather than re-derived, and ran configurations the lead did not. Ran the
suite with the floor raised (exit 1 — the floor really bites); forced branch coverage
(98 branches, **3 partial**: `app/db.py:208`, `app/main.py:49`,
`app/routes.py:385->387`); ran all 11 test modules standalone (**all pass in
isolation** — module independence, not merely aggregate greenness); copied the source
tree without `.git` (**117 passed / 1 failed**, `git check-ignore` exit 128 — the suite
carries an undeclared environmental precondition); timed three full runs
(**1074/1174/1203 ms**); and confirmed `git remote -v` is empty and that
`git ls-files` matches only framework hooks and knowledge files — no `.github/`, no CI
config, no Makefile, no pre-commit. Read `pyproject.toml`, `tests/conftest.py`,
`tests/test_page.py`, `tests/test_config.py:140-180`, `app/db.py`, `README.md:244-266`.
**Inferred**: the methodology/ordering fields are corroborated on test *levels* and
uncorroborated on test *order*, because squashing destroyed the ordering evidence;
the gate-home options are not peers without a remote; and three coverage gaps sit on
this intent's critical path — no `AVG`/`GROUP BY`/`strftime`/`json_extract` assertion
exists anywhere, so aggregate correctness is invisible to a line-coverage gate;
`_rebuild_analyses` drops every index and no test inspects
`sqlite_master WHERE type='index'`; and R-01 cannot be reproduced by any test written
against the current `asyncio.run`-per-request harness. Its findings are folded into
`## Testing Posture`.

### aidlc-developer-agent (spoke, blind)

Read `app/routes.py`, `app/service.py`, `app/repository.py`, `app/db.py`,
`app/models.py`, `app/main.py`, `app/sentiment.py`, `app/dummy_client.py`,
`app/static/app.js`, `tests/test_page.py`, `tests/conftest.py`, `pyproject.toml`, the
README's storage/HTTP/file-layout sections, and the store — plus grep-level reads of
`app/config.py`, `app/session_auth.py` and `app/openrouter_client.py`. Reproduced the
lead's counts exactly (`#:` 71 across 10 modules, `Single responsibility:` 11 of 12,
four `# noqa: S310`, four `# pragma: no cover`, zero `TODO`/`FIXME`, zero `print()`)
and **falsified four claims**: the no-broad-catch invariant (§ Corrections 1), the
layer chain as described (§ Corrections 5), the test-naming convention as described,
and two stale CodeKB rows (§ Corrections 6). **Inferred**: the tokeniser placement is
not a deadlock — `app/sentiment.py` is a leaf that imports nothing from `app` and
already owns `LABELS`, so it is a valid home for a promoted public pattern; adding a
column to `analyses` is an eight-place edit across three modules and the README, which
is why a separate table is the one-place alternative; and `init_db`'s two-arm branch
has no place for a second table's DDL, with `CREATE_SCHEMA_META_TABLE`-after-the-branch
as the established placement to copy.

### aidlc-devsecops-agent (spoke, blind)

Ran the full automation-surface sweep (zero hits), read the lint configuration, the
test configuration, the dependency manifest, `.gitignore` and every commit. Scanned
**every blob in every commit** for nine real key shapes: zero real hits; the raw
`sk-or-v1-` matches resolve to six obvious placeholders. Took an offline licence
inventory of the 21 installed third-party distributions (MIT ×12, BSD-3-Clause ×4,
BSD-2-Clause ×1, Apache-2.0 ×2, PSF-2.0 ×1, `packaging` dual) — all permissive, so no
licence finding, only a licence absence. Probed the `S` rule set with
`--stdin-filename`: counted 73 `S` rules with **13 preview-gated**, all of them
import-side blacklists. **Inferred**: "the practice is clean and the tooling is absent"
are two different statements and only the second is a process gap; the topology means
residual supply-chain exposure is local at install time and local in-process rather
than remote; and the loopback rule currently rests on uvicorn's default rather than on
`HOST`, which has no call site.

## The interview — fourteen recorded decisions

Every answer below is the human's, recorded verbatim in
`practices-discovery-questions.md`. **Where a spoke's position and an answer disagreed,
the answer won**, and the disagreements are listed under Corrections.

| # | Area | Decision | Where it landed |
|---|---|---|---|
| Q1 | Way of Working | Commit shape affirmed: `<scope>: <summary> (<scope> scope)`, changed-list body, `Produced by the AI-DLC …` trailer | `## Way of Working`; **ALWAYS** rule |
| Q2 | Walking Skeleton | Default kept; for this feature the slice is **one analytics endpoint end to end** — route, aggregate SQL, page render | `## Walking Skeleton` (not a rule — a per-feature sequencing) |
| Q3 | Testing Posture | The three gates run from a **platform-neutral verification script** the developer runs — not a pre-commit hook, not a provider CI job | `## Testing Posture`; **ALWAYS** rule |
| Q4 | Testing Posture | **80 % line floor unchanged**; branch coverage stays off | `## Testing Posture` (a setting, not a rule) |
| Q5 | Testing Posture | **Every defect ships a test that reproduces it** — which requires fixing the in-process ASGI harness first | `## Testing Posture`; **NEVER** rule |
| Q6 | Deployment | **Add a lockfile with hashes now** | `## Deployment`; **ALWAYS** rule |
| Q7 | Code Style | **`/v2`** — a new versioned router; the existing `/v1` contract left untouched | `## Code Style` (not a rule — see "deliberately not promoted") |
| Q8 | Code Style | **Drop `mean intensity`**; the column is retired and null on every row | `## Code Style` (not a rule — a requirement correction) |
| Q9 | Code Style | Aggregate queries live in a **new read module beside `repository`**; the service layer is not inserted into the read path | `## Code Style`; **ALWAYS** rule |
| Q10 | Code Style | **Add `ruff TID` (`banned-api`)** so the layer boundaries become mechanical gate failures | `## Code Style`; **ALWAYS** rule |
| Q11 | Deployment | **Enforce the loopback bind at startup** so a non-loopback host fails loudly | `## Deployment`; **ALWAYS** rule |
| Q12 | Deployment | **Adopt secret scanning and a dependency audit**; the known fake-key fixtures allowlisted so the first run is signal | `## Deployment`; **ALWAYS** rule |
| Q13 | Code Style | **Match `ruff` `target-version` to `requires-python`**, and **add a `LICENSE`** | `## Code Style` / `## Deployment`; target-version as an **ALWAYS** rule, the `LICENSE` as a deliverable |
| Q14 | Testing Posture | **Hand-written expected values per requirement** for the analytics aggregates, **plus a test that the new indexes survive a migration** (`sqlite_master` inspection) | `## Testing Posture`; **ALWAYS** rule |

**Rulings that reach past this stage** and must be carried forward by their owners:
Q8 removes `mean intensity` from the requirement and puts the retired column out of
scope. Q7 puts the analytics endpoints on `/v2` and settles the conflict between the
intent description and constraint `C-4` in favour of the description — `C-4`'s `/v1`
paraphrase cites the same human text that says `/v2`, so the register contains a
paraphrase defect that the human has now overruled. Q2 makes one endpoint end-to-end
the first unit of work. Q5 converts R-01's harness limitation from an accepted gap
into team policy to close. Q3 makes the verification script construction work with an
owner. Q6 makes a lockfile a deliverable. Q14 requires the index-survival assertion
because `_rebuild_analyses` drops every index on `analyses` today.

## Corrections applied — the three spokes falsified seven lines in the draft

Each of these was verified against the source during integration before being written
into `team-practices.md`. None was carried forward, because these sections are about to
become the team's standing memory and a false rule there is worse than no rule.

1. **"No bare `except` and no broad catch anywhere" — false, and the grep offered as
   proof could not support it.** `grep -E 'except\s*:' app/` rules out the *bare* form
   only. `app/db.py:163` catches **`BaseException`**, inside the migration's
   `BEGIN`/`try`/`rollback()`/`raise`/`commit()` block — a legitimate
   rollback-and-re-raise, not a swallow, but the one broad handler in `app/`. Restated
   accurately: no bare `except:`, no `except Exception:`, every handler names a
   specific type or a deliberate two-type tuple, and **exactly one** `BaseException`
   handler exists and is named as the migration's rollback. The developer agent also
   found a third unremarked idiom — the skip-and-continue two-tuple at
   `app/service.py:180` — now given a stated purpose.
2. **`filterwarnings = ["error"]` is broader than "the deprecation canary".** It
   promotes **every** warning from **every** source to a suite failure. With no
   lockfile and floors two major versions behind what is installed (`pytest 9.1.1`
   against `>=8`, `pytest-cov 7.1.0` against `>=5`), **the suite's pass/fail state is
   a function of the resolved dependency set, not of the code.** The quality agent
   objected to this wording; it is corrected, and it is now tied to Q6's lockfile.
3. **The single-author identity in the baseline never existed.** `git remote -v` is
   empty and `git log --format='%an <%ae>' | sort -u` returns one line —
   `Faraz Mazhar <farazmazhar@users.noreply.github.com>`. The named identity
   `very-cool-sentiment-analysis <demo@local>` appears nowhere in this history. The
   *substance* (one author, no co-authors, no merges, no second human reviewer, no
   remote) still holds and is kept; the invented identity is dropped.
4. **"Exactly two runtime packages" is false in distribution terms, and the CodeKB's
   telemetry row is wrong on both counts.** `fastapi 0.142.2` declares a hard,
   non-extra dependency on `opentelemetry-api>=1.44.0` — read from installed metadata,
   not documentation — so **14** runtime distributions install. The cap is
   declaration-level and `tests/test_config.py:141` asserts the declared list, so the
   **rule was restated** to say "declare exactly two … resolution pulling transitives
   is expected and is not a breach". `technology-stack.md:57` records
   `opentelemetry-api 1.45.1` reached "through `anyio`"; installed is **1.45.0** and
   `fastapi` requires it directly. Recorded as a stale row.
5. **The layer chain was described more cleanly than the code runs it — and the draft
   missed the arrangement entirely.** `app/service.py` holds **no read function at
   all**, and `app/routes.py:31` imports `DEFAULT_LIST_LIMIT`, `list_analyses` and
   `list_analyses_by_import_id` straight from `app.repository`, calling them at `:177`
   and `:242`. So every read goes `routes → repository` and bypasses `service`, and
   the `routes → repository` edge was absent from the boundary the draft affirmed.
   **Q9 resolves it**: aggregate queries live in a new read module beside
   `repository`, called from the route, and the service layer is not inserted into
   the read path. That turns the accident into an explicit, recorded arrangement, and
   it is written up as such — with the honest note that until 2026-10-02 it was an
   accident of where the functions happened to land, not a decision.
6. **Two CodeKB rows are stale and must not reach a later stage as authority.**
   `architecture.md:502` names **`ensure_page_state`**, which **exists nowhere in this
   repository** — the connection owner is `get_connection` (`app/routes.py:92`);
   `code-structure.md:208` records `from __future__ import annotations` as applying to
   **all 12** modules when it applies to **11** (`app/__init__.py` does not). Both are
   named in `team-practices.md` so a later stage cannot cite them uncritically.
7. **The security and automation absence must not read as coverage.** There is **no
   secret scanner, no dependency audit, no SAST, no DAST, no pre-commit hook, no CI,
   no SBOM and no licence policy**, none of `pip-audit`/`bandit`/`semgrep`/`gitleaks`/
   `detect-secrets`/`safety`/`trivy` is installed, and PyPI is reachable — so the
   absence is a decision, not a limitation. It is now stated as a plain list, in the
   same breath as the other half: **the secret practice is genuinely clean** (every
   blob in every commit scanned, zero real credentials, all six `sk-or-v1-` values
   obvious placeholders). Two further corrections ride with it: **`S105` does not fire
   on `API_KEY`** — probed directly against the project's own config, it fires on
   `SECRET` and not on `API_KEY`, which is the most likely name for this project's one
   secret — so "secrets are caught by the lint rule set" is not claimed; and **13 of
   ruff's 73 `S` rules are preview-gated** (all import-side blacklists), while
   `except Exception:` is caught by nothing because `BLE001` is not selected, and ruff
   has no TLS or cipher analogue at all. The only automated security assertion in the
   repository checks that the config string contains the letter `"S"`; it never runs
   ruff and cannot fail on a code defect, and is no longer allowed to read as a gate.

## Baseline drift — where `memory/team.md` is now factually out of date

The baseline is the affirmed position and most of it survives. These lines do not, and
the integrated draft corrects each rather than carrying it forward. **The human
confirms or changes each at the gate.**

| Section | Baseline says | Reality at `beeb587` | Evidence |
|---|---|---|---|
| Way of Working | `main` holds only the harness (`0268a5d`); the app sits on unmerged `v1-classic` at `5b328fc` | Neither commit exists. `main` = 2 commits, both scopes squashed and tagged; no feature branch survives | `git rev-list --count HEAD` → 2; `git branch -a` → `* main`; tags `v1-classic`→`4eb9b74`, `express`→`beeb587` |
| Way of Working | one author identity, `very-cool-sentiment-analysis <demo@local>` | Every commit is `Faraz Mazhar <farazmazhar@users.noreply.github.com>`; the named identity is absent from the history | `git log --format='%an <%ae>' \| sort -u` → one line |
| Way of Working | "no tag exists unless the merge step writes one" | Two annotated tags exist, both written by that step | `git for-each-ref refs/tags`; `git tag -n20 -l` |
| Way of Working | commit-message shape "not yet affirmed" | **Affirmed by Q1** and promoted to a rule | `practices-discovery-questions.md` Round 1 |
| Walking Skeleton | this run is the exemption (`skeleton: off` for `classic`) | This scope is `feature`, which declares `skeleton: on` — first live exercise; Q2 kept the default | `aidlc-feature.md:8`; Round 1 |
| Testing Posture | 52 tests in 9 modules, "52 passed in 0.33 s" | 118 tests from 109 functions in 11 modules | `pytest -q`; per-module `def test_` counts |
| Testing Posture | coverage 70.2 %, "the floor fails today", covering the live engine is construction work | 96.02 % over 679 statements; floor passes with ~16 points of headroom; `app/openrouter_client.py` at 92 % | `pytest -q` coverage table; `tests/test_live_client.py` |
| Testing Posture | the coverage/lint gate's home is "open … this scope skips the CI Pipeline stage" | **Decided by Q3**: a platform-neutral verification script. `ci-pipeline` and `deployment-pipeline` both execute for the first time | `aidlc-feature.md` (33 stages, all EXECUTE) |
| Testing Posture | regression policy "not yet affirmed" | **Decided by Q5**: every defect ships a reproducing test; R-01's exemption closes with it | Round 1 |
| Testing Posture | dev extra is `pytest` only; README's "exactly three packages" is false | Dev extra is `pytest`, `pytest-cov`, `ruff`; the NFR3 comment and the README were both corrected | `pyproject.toml:18-24`; `README.md:23-29` |
| Testing Posture | `filterwarnings` is "only a FastAPI/pydantic deprecation canary" | It fails on **any** warning from **any** source, and with no lockfile the suite's state depends on the resolved dependency set | Correction 2 |
| Deployment | "localhost only" is binding | Rule unchanged, but **not enforced** — `HOST` has no call site; Q11 decides to enforce it at startup | `app/main.py:36`; `tests/test_routes.py:334-338` |
| Deployment | "a schema change is handled by recreating the local database" | Still true as a licence, but weaker: the code is at schema v3 while this checkout's file is still v2 with no `import_id`, no index on `analyses` and 0 rows | `data/sentiment.db` queried directly; `SCHEMA_VERSION = 3` |
| Code Style | `ruff` unadopted; 16 findings; line-length and `B008` policy open | Adopted, configured, clean on both checks; line length 100; `extend-immutable-calls` configured | `ruff check` / `ruff format --check`; `pyproject.toml` |
| Code Style | `F401` — `tests/test_auth_routes.py` imports `pytest` unused | Gone | `ruff check` → *All checks passed!* |
| Code Style | import ordering not isort-clean in four files | `I` is selected and the check is green | `ruff check app tests` |
| Code Style | tests use `test_<behaviour>` names | The real convention is a full prose sentence stating the expected outcome, route-prefixed where applicable | `tests/test_routes.py:342` and siblings |
| Code Style | "no bare `except` and no broad catch anywhere" | **False** — see Correction 1 | `app/db.py:163` |

**Baseline claims re-checked and found still current**, carried forward unchanged: one
branch per scope squashed and tagged; no second human reviewer; no remote; no
CI/hook/container/IaC artefact; localhost-only as the only deployment target; a test
asserting the two-declaration dependency cap; parameter-bound SQL only; no `print()`
in `app/`; `textContent`-only rendering; zero `TODO`/`FIXME`; the dependency-cap reasons
for the hand-rolled ASGI harness and for no browser automation; the offline guard;
zero mock objects; the four `S310` suppressions as the whole security-suppression
budget; and no `LICENSE` in the repository (now a deliverable under Q13).

## Unresolved uncertainty

Carried forward rather than answered here. Items 1–3 are open again by design, because
the human's answers created work that later stages own.

1. **Which secret scanner and which dependency audit tool.** Q12 decides to adopt
   them; it does not name them. Neither is installed. The choice is unowned, and the
   allowlist of the known fake-key fixtures has to be authored alongside whichever
   tool lands, or the first run is noise.
2. **What the lockfile is and how it is consumed.** Q6 decides a lockfile with hashes
   *now*; the format (`requirements.lock`, `constraints.txt`, a tool-managed lock) and
   the install command that consumes it are not chosen. The constraint that shapes
   the choice: `filterwarnings = ["error"]` makes the suite's pass/fail state depend
   on the resolved set, and Q3 puts a verification script — not a hosted job — where
   that set will be resolved.
3. **What "hand-written expected values" produces for an aggregate over a date
   range.** Q14 requires them per requirement and requires the index-survival
   assertion; it does not settle whether the fixtures are inline literals, a golden
   file, or a seed-and-assert shape, nor what the acceptable UTC-edge bucket boundary
   is.
4. **The tokeniser's home.** Q9 settles where aggregate *queries* live; it does not
   settle where the term-extraction pattern lives. `app/sentiment.py` is the
   evidence-supported candidate (a leaf importing nothing from `app`, already owning
   `LABELS`), but "significant term" — stopwords, minimum length, case handling — is
   still undefined, and the intent statement carries that as a tagged assumption.
5. **Type checking.** Annotations are 100 % applied and unenforced; no `mypy`, no
   `pyright`, no `py.typed`. Cheap to adopt, never decided.
6. **Recovery expectations at schema v3 → v4.** "Delete `data/sentiment.db`" is still
   licensed, but a real store is no longer disposable, there is still no migration
   tool and no backup path, and Q14's index assertion implies the migration path is
   about to run for real. Whether a backup expectation is being affirmed or the cheap
   recovery stays sanctioned is a human judgement.
7. **Named ownership for dependency updates and emergency patches.** Q6 pins the
   resolution; nothing names an owner or an audit cadence for the lockfile itself, and
   there is still no remote and still no update bot.
8. **The `TID251` banned-api surface.** Q10 decides the mechanism; the exact entries
   and their per-file scoping are a construction decision. Note the precedent the
   devsecops agent flagged and did **not** turn into a rule: never widening a
   security-rule suppression outside `tests/`. It is well-evidenced (four `S310`
   suppressions, zero file-level `# ruff: noqa`, `per-file-ignores` scoped to `tests/*`
   with a written reason, `B008` silenced by configuration) and it was proposed as a
   `NEVER` candidate — **but the human did not adopt it**, so it is not here.
9. **The `LICENSE` choice itself.** Q13 decides a licence file exists; it does not
   choose a licence. The installed project distribution currently carries an empty
   licence expression, and every dependency is permissive.
10. **Whether the `C-5` / `opentelemetry-api` tension is a constraint or a note.**
    Nobody chose that dependency; it arrives with FastAPI, and the next FastAPI minor
    could add another. `C-5`'s wording says "introduce", which covers deliberate
    choices but not transitive arrivals. The quality agent and the devsecops agent
    both put this to the interview; the interview did not rule on it, so
    `discovered-rules.md` says "introduce" and the tension is recorded here rather
    than resolved.
11. **Suite-alone versus suite-plus-boot in the verification script.** Q3 settles
    where the gates run, not what the script contains. The README's documented
    verification boots the app and reads `/v1/health` but never touches the changed
    path; for this intent the changed path is two new endpoints, and "exercise the
    changed path" is currently a manual habit with nothing behind it.

## What was deliberately not promoted to a rule

`discovered-rules.md` carries thirteen `ALWAYS` lines and three `NEVER` lines. Each is
a constraint a human stated — carried forward from the 2026-09-30 affirmation, sourced
to a `C-` constraint from the feasibility interview, or sourced to a numbered answer
here. Observed behaviour stayed a convention in `team-practices.md` even where the
repository enforces it mechanically. Named here so the omissions are a visible choice
and the human can promote any of them by saying so:

- **Q7's `/v2` router and untouched `/v1`.** Human-stated and hard-edged, but it is a
  decision about the shape of *this* intent's endpoints. Promoting it would freeze the
  project's public contract against a future intent that legitimately wants to extend
  `/v1`. It is recorded in `## Code Style` and belongs to Requirements Analysis and
  Contract Design.
- **Q2's one-endpoint slice.** A per-feature sequencing decision, and the standing
  default it confirms is already in `## Walking Skeleton`.
- **Q4's unchanged 80 % line floor with branch coverage off.** A setting decision, and
  the cost of it (3 invisible partial branches) is recorded where it can be read.
- **Q8's dropped `mean intensity`.** A requirement correction, not a standing
  constraint; `## Code Style` records it so the column's retirement is not reopened.
- **Q13's `LICENSE`.** A deliverable, not a constraint on how work is done.
- **Never widening a security-rule suppression outside `tests/`** — the devsecops
  agent's strongest evidence-backed candidate, proposed as a `NEVER` line and **not
  adopted by the human**, so it is not a rule.
- **A paired change to the lint rule set and the matching `tests/test_config.py`
  assertion** — proposed by the devsecops agent on the grounds that the shape already
  exists in the repository. The human did not adopt it.
- The error-handling invariants, the no-junk-drawer rule, parameter-bound SQL only,
  `textContent`-only rendering, `SentimentClient` as the only route to an engine with
  `get_client` as the sole construction site, connection ownership at the HTTP edge,
  the module-docstring `Single responsibility:` declaration, and refusing rather than
  substituting — all strongly observed, all left as conventions.