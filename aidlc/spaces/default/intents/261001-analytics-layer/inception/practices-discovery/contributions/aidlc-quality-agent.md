**Collaborator:** aidlc-quality-agent

## Contribution

Review from the testing and quality-gate standpoint only. I re-measured the
repository at `beeb587` rather than re-deriving the lead's numbers, and I ran the
suite in configurations the lead did not. Everything below is either a command I
ran (marked **measured**) or a reading of a file (marked **read**). Where I
disagree with the draft I say so precisely; where I confirm it I say what confirms
it, so the lead can carry the numbers forward with a second source.

### 1. What I measured

`.venv/bin/python`, CPython 3.14.7, working tree at `beeb587`, nothing written
outside `/tmp/opencode/`.

| # | Command | Result |
|---|---|---|
| 1 | `pytest -q` | **118 passed, 0 failed, 0 skipped, 0 errors in 0.76 s**; TOTAL 679 stmts / 27 miss / **96.02 %**; exit 0 |
| 2 | `pytest --cov-fail-under=99 --cov-report=` (clean `COVERAGE_FILE`) | 118 passed, **exit 1** — the floor really does fail the run |
| 3 | `pytest` (configured floor) | **exit 0** |
| 4 | `pytest --cov-branch --cov-report=term-missing --cov-fail-under=0` (clean `COVERAGE_FILE`) | 679 stmts / 27 miss / **98 branches, 3 partial**; partials at `app/db.py:208`, `app/main.py:49`, `app/routes.py:385->387` |
| 5 | each of the 11 `tests/test_*.py` run standalone | **all 11 pass in isolation** (109 functions total) |
| 6 | `pytest --collect-only` | exit **0**, but *prints* `FAIL Required test coverage of 80% not reached. Total coverage: 46.24%` |
| 7 | full source tree copied to `/tmp` **without `.git`**, then `pytest` | **117 passed, 1 failed** — `tests/test_config.py::test_local_config_is_gitignored`, `git check-ignore` exit **128**, `fatal: not a git repository` |
| 8 | wall clock, 3 full runs | **1074 / 1174 / 1203 ms** including interpreter start |
| 9 | `ruff check app tests` | `All checks passed!`, exit 0 |
| 10 | `ruff format --check app tests` | `24 files already formatted`, exit 0 |
| 11 | `git remote -v` | **empty — no remote** |
| 12 | `git ls-files \| grep -iE 'github\|gitlab\|jenkins\|azure\|pre-commit\|circle\|travis\|buildkite\|Makefile\|tox\|nox'` | only `.aidlc/hooks/*.ts` and `.aidlc/knowledge/…` — **framework hooks, not project gates**. No `.github/`, no CI config, no `Makefile`, no pre-commit |

**Read:** `pyproject.toml`, `tests/conftest.py`, `tests/test_page.py`,
`tests/test_config.py:140-180`, `app/db.py:36-53,107,122,174,188,225-250`,
`README.md:244-266`, `.aidlc/scopes/aidlc-feature.md`.

**Toolchain actually installed, against declared floors** (**measured** via
`pip list`): `pytest 9.1.1` (floor `>=8`), `pytest-cov 7.1.0` (floor `>=5`),
`coverage 7.16.2`, `ruff 0.16.9` (floor `>=0.6`), `fastapi 0.142.2`,
`starlette 1.7.0`, `pydantic 2.13.5`, `uvicorn 0.54.0`. No lockfile, no
constraints file. The suite is green on a toolchain **two major versions past
every declared floor**.

### 2. The two structured fields: coherent, and the coherence is defensible

`- **Methodology**: custom` plus the split Ordering sentence is internally
consistent and I would carry both forward. The corroboration is weaker than the
draft implies, and the draft's own `evidence.md:89` already says so honestly — I
endorse that line and want it preserved into the integrated artifact.

- **What the repo *does* corroborate** (**measured**, #1 and #5): the suite
  contains **both** test levels the sentence names. API/acceptance level:
  `test_routes` (15), `test_bulk_import` (16), `test_auth_routes` (12),
  `test_page` (4). Lower-level unit level: `test_db` (8), `test_repository` (8),
  `test_service` (9), `test_live_client` (9). A mixed cadence is therefore
  *visible in the artifact* even though its *order* is not.
- **What the repo cannot corroborate** (**inferred**): the ordering itself. Two
  squashed commits, no surviving branch, no intra-commit ordering — the history
  physically destroys the evidence. "the shape of the suite is consistent with
  it" (draft, Testing Posture) is the right hedge; I would go one step further in
  the integrated text and say plainly that ordering is affirmed team practice
  carried forward, corroborated on test *levels* and uncorroborated on test
  *order*.

So: `custom` stays. It is the correct label for a suite that demonstrably holds
both levels, and the stage's own definition of `custom` ("mixes cadences") is
satisfied by the evidence available.

### 3. The gates: what is real, what is aspirational, what has no home

The draft's Enforcement Summary calls three gates "real … all opt-in". That is
accurate but too generous in one direction and too vague in another.

**Real, and I verified each one actually bites** (**measured** #2, #3, #9, #10):

| Gate | Verified how |
|---|---|
| 80 % coverage floor | raising the floor to 99 on the CLI → **exit 1**; at 80 → exit 0. The "stated twice so it cannot be skipped" design works, and it is a *failing* gate, not a printed notice |
| `filterwarnings = ["error"]` | the suite is green ⇒ **zero** warnings are emitted by any source |
| `ruff check` / `ruff format --check` | both exit 0, both green |

**Correction the lead should apply.** The draft calls `filterwarnings` "the
project's only deprecation canary" and then describes it as catching "a FastAPI
or pydantic deprecation on 3.14". It is broader and more consequential than
that: `filterwarnings = ["error"]` promotes **every** warning from **every**
source to a suite failure — pytest's own deprecations, a transitive
`DeprecationWarning`, a `ResourceWarning`. Combined with the measured toolchain
drift (no lockfile, floors two major versions behind what is installed), the
suite's green/red state is a function of the resolved dependency set, not of the
code. A fresh `pip install -e ".[dev]"` on a CI runner will resolve something
different from this machine. That is not a hypothetical: it is the normal state
of this manifest today. **This is the single strongest technical argument for
pinning the toolchain inside the CI job rather than floating it** — and the
draft's Deployment section raises supply chain without ever connecting it to the
quality gate.

**Correction on the `-q` note.** The draft's one-clause remark is right and
under-developed. **Measured:** a default `pytest` run prints only dots — no test
names. And `pyproject.toml` configures **no machine-readable output at all**:
`--cov-report=term-missing` is a human table, there is no `--cov-report=xml`, no
`--junit-xml`, no `-ra`. Consequences a gate will hit immediately: no per-test PR
annotations, no flaky-test list, and — the one that matters most — **"coverage
did not decrease" is not expressible as a gate today**, because there is no
machine-readable coverage artifact to diff against the previous run. That is
Gate 1 of the standard quality-gate set, and it is currently unbuildable.

One honest note against my own hypothesis: I expected `pytest --collect-only` to
trip the coverage floor and produce a spurious failure. **Measured: it exits 0**
(#6), it only *prints* a misleading `FAIL … 46.24%` line. Automation is not
broken; a human reading a log can be misled. Minor, worth one clause, not more.

**Where the gate has no home — the sharper version.** The draft says
`ci-pipeline` is on the plan so "where the gate lives is no longer an open
question with no home; it is a decision for the interview". True, and then
immediately undercut by a hard constraint the draft does not state: **there is
no remote** (**measured** #11) and **no CI provider of any kind** (#12). So the
`ci-pipeline` stage has a *stage* to live in but no *runtime* to run in. A
`.github/workflows/ci.yml` written today would be a file that has never executed
and cannot execute until a remote exists. The three real options are therefore
not symmetric:

1. a **platform-neutral verification script** (e.g. `scripts/verify.sh` or a
   `make verify` target) that both a human and any future CI job calls — the only
   option that is *true today* and stays true on any host;
2. a **pre-commit hook** — real, local, but it never sees a dependency bump and
   never runs in CI, so it cannot be the whole gate;
3. a **provider workflow file** — aspirational until a remote exists, and it
   would encode the toolchain-pinning decision before anyone can test it.

Option 1 is the one I would put to the human as the recommendation. I cannot
settle it — it is a judgment about how this team wants to work — but the draft
should stop describing the choice as merely "a pre-commit hook, a Build-and-Test
step, or a CI job", because the first two and the third are not peers when there
is no remote.

**And the cheapest fact nobody has put in the artifact** (**measured** #8): the
full suite with coverage **costs about 1.1 seconds**. The whole documented
verification (install, suite, boot uvicorn, read `/v1/health`) is a ~4-second
copy-paste line. Cost is not an argument against an automatic gate here, and the
draft never says so.

### 4. Coverage: measured, and the gaps that will actually bite *this* intent

The draft's coverage section is the strongest part of the document and its
numbers are correct — I reproduced 679/27/96.02 % exactly. Three gaps are missing
from its "Explicitly untested, by design" list, and all three are on this
intent's critical path rather than in the far distance.

**(a) Line coverage only — `branch` is not enabled.** **Measured** (#4):
`[tool.coverage.run]` sets `source = ["app"]` and nothing else; there is no
`branch = true`. With branch measurement forced on, the suite has **98 branches
with 3 partial** — `app/db.py:208`, `app/main.py:49`, and the partial edge
`app/routes.py:385->387` — none of which the 80 % line floor can see at all. The
draft says "the floor is 80 % lines", which is *correct as written* and is the
problem: for a feature that is mostly **conditional aggregation over a date
range**, line coverage is the weakest signal available. Every `if` whose false
branch is never taken still counts as covered. This is a one-line config change
plus a re-based threshold, and it is a decision the human should make on purpose
rather than discover later. *(Inferred: for the new analytics queries the
line/branch divergence will widen; I did not write the queries, so I am not
putting a number on it.)*

**(b) The analytics layer's own correctness surface has zero tests today.**
**Measured** by grep across `tests/` and `app/`: there is **no `AVG(`, no
`GROUP BY`, no `strftime(`, and no `json_extract`** anywhere in either tree. The
only SQL in `tests/` is `SELECT COUNT(*) FROM analyses`, and every one of those
is a row-count assertion supporting the boundary discipline the draft already
credits. `app/` today has no aggregation at all. The consequence: **the 96.02 %
figure says nothing whatsoever about whether a date bucket, an average, a NULL
`confidence`, or an empty date range is computed correctly.** A subtly wrong
`strftime` bucket boundary — off-by-one-day at the UTC edge, given
`repository.py:41` normalises to `%Y-%m-%dT%H:%M:%SZ` — would leave the suite
fully green and the 80 % floor fully satisfied. Line coverage on a module that is
90 % straight-line SQL and `if` statements will be ~100 % whether or not the
numbers are right. This is the largest single place the plan will under-test, and
it is not mentioned anywhere in the draft. It needs golden-fixture tests on
computed results — not a coverage number.

**(c) Index loss across the migration is untested, and this intent will trigger
it.** **Read** `app/db.py`: `_rebuild_analyses` (`:230-243`) does
`ALTER TABLE … RENAME` → `CREATE TABLE` → `COPY` → `DROP TABLE`, and
`CREATE_ANALYSES_TABLE` (`:39-53`) **declares no indexes at all**. **Measured**
by grep: `tests/` contains **no `CREATE INDEX` and no assertion over
`sqlite_master WHERE type='index'`** — the single `sqlite_master` assertion in
the suite (`test_db.py:103`) filters `type = 'table'` only. So if this intent
adds the indexes a date-range query needs *and* the v3 → v4 migration, a store
that goes through the rebuild path **silently loses every index with no warning
and no failing test** — and no warning is possible, because the only
implementation to drop them is one the suite never inspects afterwards. The
local store currently reports `version = 2`, 0 rows, and **no index on
`analyses`** at all, so the v2 → v3 path has still never run here. The draft
lists the two uncovered HTTP transports and three one-line misses as
"untested by design" but omits this, which is a *known-dormant* loss rather than
an accepted one.

**(d) No concurrency test — and the existing harness cannot host one.** The draft
is right that `grep -niE 'thread|concurren|parallel' tests/` returns nothing and
right that this is the gap it most wants closed. One sharpening: **read**
`tests/conftest.py:136` — `asgi_request` calls `asyncio.run` per request, so every
API test is a fresh event loop, single-threaded, strictly sequential. The accepted
R-01 defect (a per-request `sqlite3.Connection` created in one anyio worker
thread and closed in another) **cannot be reproduced by any test written against
the current harness**, however carefully written. Fixing it is not "add a test";
it needs a different harness shape — a real `uvicorn` on a loopback port, or
explicit threads. Since this intent's page polls on a date range, that is exactly
the trigger pattern. Worth naming so the interview does not promise a fix that
the harness cannot deliver.

**(e) A genuine strength the draft does not claim, and should.** **Measured**
(#5): **all 11 test modules pass standalone.** The suite is order-independent and
module-independent, not just green in aggregate. That is the property that makes
an automated gate safe to trust, and it is the strongest argument available for
saying "turn the gates on" — there is no hidden inter-test coupling for a
parallel or partial CI run to expose. The draft's praise is reserved for the
doubles policy; this deserves a line too.

**(f) The intensity tripwire is page-scoped.** **Read** `tests/test_page.py:64-68`:
`assert "intensity" not in markup.lower()` runs against **`GET /` only**. If the
retired-attribute decision (CodeKB TD-4) is resolved by rendering mean intensity
on the index page, this test fires and the team is told. If it is resolved by
adding the field to a separate analytics route or a JSON body, **this test stays
green and nothing catches it.** The contract decision is not mine to make, but the
testing consequence is: the human should know the existing suite catches one
placement and not the others before answering.

### 5. What the evidence settles, and what only the human can settle

**Settled by evidence — do not spend an interview question on these.** The gate
costs ~1.1 s (#8). The suite is order- and module-independent (#5). The suite has
an undeclared hard precondition: **it needs a git working tree** (#7). Branch
coverage is off, with 3 invisible partial branches (#4). Aggregate SQL has no
tests (#b). Index loss is untested (#c). The toolchain floats two major versions
past its floors and every warning is an error (§3). No machine-readable test or
coverage output exists (§3). R-01 needs a new harness, not a new test (#d).

**Needs the human.** Offered as the questions, in the interview's own words:

1. **"Where should the checks run, given there is no remote?"** The options are
   not peers: a script anyone (and any future CI) can run, a local pre-commit
   hook, or a hosted-workflow file that cannot run yet. *My recommendation: the
   script.*
2. **"Should the automatic check be the test suite alone, or the suite plus
   starting the app?"** The README's documented verification boots the app and
   reads `/v1/health` — it never touches the changed path. For this intent the
   changed path is two new endpoints, and "exercise the changed path" is currently
   a manual habit with no script behind it.
3. **"Do you want the 80 % limit to count lines only, or also branches?"** Branch
   measurement is currently off and would need the threshold re-based. Cheap to
   turn on now; harder to introduce once a number is being quoted everywhere.
4. **"Must every defect found ship with a test that reproduces it?"** R-01 is
   recorded, accepted, and has no test. The team has never ruled on this, and
   this intent is the first likely to trip the defect.
5. **"For the new analytics numbers, do we want fixed examples with known
   expected results, checked independently of the coverage limit?"** Aggregate
   correctness is invisible to a line-coverage gate — this is the one gap where a
   green suite would tell you almost nothing.
6. **"The two real network calls stay untested by design, since the tests always
   inject a transport — is that a standing decision or an accident of how the
   tests are written?"** This intent does not touch either. Worth stating as a
   choice rather than leaving it as an artefact.

### 6. One note on the lead's framing I want on the record

The draft's Testing Posture section is, on the whole, careful and honest: the
baseline-drift call-outs are correct, the counts are reproducible, the doubles
policy is the right thing to praise, and `evidence.md` is explicit about what was
*not* inferred. My substantive objections are narrow and mostly additive: the
`filterwarnings` description is understated, the "three real gates" summary omits
the two that a CI job cannot currently use, the gate-home question is constrained
by the absent remote in a way the draft does not say, and the three
analytics-specific coverage gaps in §4 are absent entirely. None of that is a
reason to change the Methodology or Ordering fields. Both should survive
integration unchanged.

## Positions

- AGREE: `Methodology: custom` and the split Ordering sentence stand, carried
  forward unchanged — both test levels the sentence names are measurably present
  in the suite (API/acceptance in `test_routes`/`test_bulk_import`/`test_auth_routes`/
  `test_page`; unit in `test_db`/`test_repository`/`test_service`/`test_live_client`),
  so the `custom` label is earned even though the squash left no ordering evidence.
- AGREE: every measured number in the draft's Testing Posture section — I
  reproduced 118 passed / 679 statements / 27 missed / 96.02 %, 11 modules,
  109 functions, 5 parametrize sites, 24 files formatted, ruff green.
- AGREE: the 80 % floor is a genuinely enforcing gate, not a printed notice —
  measured exit 1 with the floor raised, exit 0 at the configured value; the
  "stated twice" design works.
- AGREE: the regression policy is genuinely undecided and the R-01 precedent is
  the right thing to decide against — and it should be decided explicitly,
  because a polling date-range page is the trigger pattern.
- AGREE: "no concurrency test whatsoever" is the gap the draft says it most wants
  closed — with the sharpening that the current `asyncio.run`-per-request harness
  cannot host such a test, so the fix is a harness change, not a test addition.
- AGREE: the CI gates have a stage to live in now that `feature` marks all 33
  stages EXECUTE (verified in `.aidlc/scopes/aidlc-feature.md`).
- OBJECT: "`filterwarnings` … is still the project's only deprecation canary" —
  it promotes *every* warning from *every* source to a failure, and with no
  lockfile and floors two major versions behind what is installed (pytest 9.1.1 vs
  `>=8`, starlette 1.7.0, pydantic 2.13.5), the suite's pass/fail state is a
  function of the resolved dependency set rather than the code; the description
  should say so, because it is the strongest argument for pinning the CI toolchain.
- OBJECT: "three real gates, all opt-in" understates the problem — there are no
  machine-readable test or coverage artifacts at all (default output is bare dots;
  `--cov-report=term-missing` only), so "coverage did not decrease" is not
  expressible as a gate today and per-test CI annotations have nothing to consume.
- OBJECT: the gate-home question is presented as a free choice between "a
  pre-commit hook, a Build-and-Test step, or a CI job" — with `git remote -v`
  empty and no CI provider present, the third is a file that cannot run, so the
  options are not peers and the draft should name the constraint.
- OBJECT: the "Explicitly untested, by design" list omits three gaps that are on
  this intent's critical path — no `AVG`/`GROUP BY`/`strftime`/`json_extract`
  test exists anywhere, so aggregate correctness is invisible to a line-coverage
  gate; `_rebuild_analyses` drops every index and no test inspects
  `sqlite_master WHERE type='index'`, so the indexes this intent adds vanish
  silently on any migrating store; and `branch` is not enabled, leaving 3 partial
  branches (`app/db.py:208`, `app/main.py:49`, `app/routes.py:385->387`)
  invisible to the 80 % line floor.
- OBJECT: the draft never quantifies what a gate would cost — measured, the full
  suite with coverage is ~1.1 s, so cost is not a reason to leave the gates
  opt-in, and saying so would materially strengthen the interview's framing.
- OBJECT: the intensity tripwire (`tests/test_page.py:64-68`) reads `GET /` only,
  so it fires for a mean-intensity field on the index page and stays silent for
  one on a separate analytics route or in a JSON body; the human should know the
  scope of the existing guard before answering TD-4.
- OBJECT: the suite carries an undeclared environmental precondition — a full
  source tree without `.git` gives 117 passed / 1 failed with
  `git check-ignore` exit 128, because the `shutil.which("git")` guard only covers
  git-absent, not git-present-but-not-a-checkout; any CI shape that receives
  source without `.git` goes red with a message that reads like a credential leak.
- MISSING: module independence is a real, measured strength (all 11 modules pass
  standalone) and is the best available argument that an automatic gate is
  low-risk here; the draft praises the doubles policy and leaves this out.
- MISSING: six questions only the human can settle, listed in §5 — gate shape
  under an absent remote, suite-alone vs suite-plus-boot, line vs branch floor,
  defect-reproduces-test policy, golden fixtures for the analytics numbers, and
  whether the two unexercised HTTP transports are a standing decision or an
  accident of injection.
