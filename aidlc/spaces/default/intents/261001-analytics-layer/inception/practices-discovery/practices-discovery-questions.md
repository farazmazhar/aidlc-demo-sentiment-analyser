# Practices Discovery — Interview Questions

> Brownfield re-run. Each question below is one the lead draft and the three
> independent contributions could **not** settle from evidence. The default shown
> is the currently affirmed content of `aidlc/spaces/default/memory/team.md` (the
> 2026-09-30 affirmation), which is what a re-run presents as the starting point.
> Answers are recorded here as they are given; Step 5 integration reads this file.

## Round 1

### Q1 — Way of Working: commit message convention

**Default today:** un-affirmed. The baseline records the commit-message convention
and any maximum branch age as "not yet affirmed".

**Evidence:** both commits on `main` use `<scope>: <summary> (<scope> scope)`. The
`express` body is a bullet list of changes ending in the measured result and a
`Produced by the AI-DLC express workflow for intent csv-bulk-import.` trailer;
the `v1-classic` body is empty. Two samples is not a convention.

---

### Q2 — Walking Skeleton: does the thin-slice default still stand?

**Default today:** "We build a thin end-to-end slice first, by default, on future
work." A walking skeleton is a minimal version that runs the whole way through,
built before the real features go in to prove the pieces connect.

**Evidence:** both prior scopes declared `skeleton: off`, so the ceremony has never
actually run in this project. This scope is `feature`, which declares
`skeleton: on` — the first live exercise. The intent treats all four capabilities
as must-have and adds a layer *on top of* a working app, so "the slice" needs a
concrete reading.

---

### Q3 — Testing Posture: where do the three gates actually run?

**Default today:** "Today nothing automated stands between a change and a usable
build." The three gates exist — `filterwarnings = ["error"]`, the 80 % whole-app
coverage floor, and the pinned `ruff` rule set — all green, all opt-in.

**Evidence:** `git remote -v` is empty, no CI provider, no pre-commit hook, no
Makefile. This scope runs `ci-pipeline` (2.7) and `deployment-pipeline` (3.1) for
the first time in this project, so the question now has a home — but a provider
workflow file cannot run without a remote. The full suite with coverage measures
~1.1 s, so a gate is cheap.

---

### Q4 — Testing Posture: line coverage or line plus branch?

**Default today:** 80 % **line** floor, whole application counted, enforced
twice (`--cov-fail-under=80` and `fail_under = 80`).

**Evidence:** measured 118 passed, 679 statements, 27 missed, 96.02 %. Branch
coverage is not enabled, so three partial branches are invisible to the floor.

---

### Q5 — Testing Posture: must every defect ship a test that reproduces it?

**Default today:** not affirmed. The precedent is R-01, the cross-thread SQLite
defect — recorded, accepted, and reproduced by no test in the suite.

**Evidence:** the in-process ASGI harness calls `asyncio.run` per request, so no
test written against today's harness can reproduce R-01; reproducing it needs a
harness change first. The page this intent adds polls on a date range, which is
the access pattern most likely to trigger it.

---

### Q6 — Deployment: floating dependency floors — accepted risk or a gap to close?

**Default today:** recorded as open — "keep floating floors with manual audit, or
add a lockfile plus a periodic audit check — and who owns dependency updates and
the emergency-patch path." Unresolved since 2026-09-30.

**Evidence:** floors not pins (`fastapi>=0.110`, `uvicorn>=0.27`, `pytest>=8`,
`pytest-cov>=5`, `ruff>=0.6`, `setuptools>=68`); no lockfile, hashes, constraints
file or `requirements.txt`. `setuptools` is absent from the venv, so every
`pip install -e ".[dev]"` downloads and executes a fresh unpinned build backend.
In live mode the process holds a valid API key while all of it runs in-process.

---

### Q7 — Code Style: `/v1` or `/v2` for the analytics routes?

**Default today:** the affirmed business rule BR4.2 — data routes are versioned
under `/v1`. The code has exactly one prefix, `V1_PREFIX = "/v1"`.

**Evidence:** this is a conflict between two of the human's own records of the
same intent, so no snapshot can settle it. The intent description names
`GET /v2/analytics/summary` and `GET /v2/analytics/terms` twice, describing `/v1`
only as the status quo; the constraint register paraphrases that same text as
C-4, "follow the existing `/v1` conventions". There is no `/v2` anywhere in `app/`
or the README.

---

### Q8 — Code Style: what happens to `mean intensity`?

**Default today:** the intent summary is expected to carry a mean intensity.
Reversing Engineering found it unimplementable as written.

**Evidence:** `intensity` is a **retired** column — nullable, never written since
v1, absent from `RECORD_FIELDS`, never read by `from_row`, and asserted absent
from served markup in tests. `AVG(intensity)` returns `NULL` for every row the
app writes. The intent's own instruction is that an ambiguous requirement gets
asked about rather than guessed.

---

## Recorded answers — Round 1

| # | Area | Answer |
|---|---|---|
| Q1 | Way of Working | Affirmed: `<scope>: <summary> (<scope> scope)`, with the changed-list body and the `Produced by the AI-DLC …` trailer. |
| Q2 | Walking Skeleton | Default kept. For this feature the slice is **one analytics endpoint end-to-end** — route, aggregate SQL, page render — before the second endpoint goes in. |
| Q3 | Testing Posture | The three gates run from a **platform-neutral verification script** (or make target) the developer runs. Not a pre-commit hook, not a provider CI job. |
| Q4 | Testing Posture | **80 % line floor unchanged**; branch coverage stays off. |
| Q5 | Testing Posture | **Every defect ships a test that reproduces it** — which requires fixing the in-process ASGI harness first. |
| Q6 | Deployment | **Add a lockfile with hashes now.** |
| Q7 | Code Style | **`/v2`** — a new versioned router; the existing `/v1` contract is left untouched. |
| Q8 | Code Style | **Drop `mean intensity`** from the summary. The column is retired and null on every row, so the field is removed from the requirement. |

## Recorded answers — Round 2

| # | Area | Answer |
|---|---|---|
| Q9 | Code Style | Aggregate queries live in a **new read module beside `repository`**, matching how reads already work. The service layer is not inserted into the read path. |
| Q10 | Code Style | **Add `ruff TID` (`banned-api`)** so the affirmed layer boundaries become mechanical gate failures instead of prose. |
| Q11 | Deployment | **Enforce the loopback bind at startup**, so a non-loopback host fails loudly. |
| Q12 | Deployment | **Adopt secret scanning and a dependency audit.** The four known fake-key fixtures must be allowlisted so the first run is signal, not noise. |
| Q13 | Code Style | **Match `ruff` `target-version` to `requires-python`**, and **add a `LICENSE`**. |
| Q14 | Testing Posture | **Hand-written expected values per requirement** for the analytics aggregates, **plus a test that the new indexes survive a migration** (`sqlite_master` inspection). |

## Rulings that reach past this stage

These answers change work that later stages own. Carry them forward explicitly.

- **Q8 — `mean intensity` is dropped** from the summary endpoint. The retired
  `intensity` column is out of scope; no migration resurrects it.
- **Q7 — the analytics endpoints are `/v2`**, on a new versioned router, with the
  `/v1` contract untouched. This settles the conflict between the intent
  description and constraint `C-4` in favour of the description.
- **Q2 — the first unit of work is one analytics endpoint end-to-end** (route,
  aggregate SQL, page render) before the second endpoint goes in.
- **Q5 — every defect ships a reproducing test**, which requires fixing the
  in-process ASGI harness first. R-01's harness limitation is now team policy to
  close, not an accepted gap.
- **Q3 — the gates get a platform-neutral verification script**, so a new
  verification path is construction work with an owner.
- **Q6 — a dependency lockfile with hashes lands**, so every install becomes
  reproducible.
- **Q14 — the index-survival assertion is required**, because `_rebuild_analyses`
  drops every index on `analyses`; an index added by migration does not survive
  today.


## Round 2 — as asked

### Q9 — Code Style: where do read paths go?

**Evidence:** every existing read goes `routes → repository`, bypassing `service`,
which holds no read function at all. The analytics layer is *entirely* reads, so
"reads bypass the service layer" is an accident here that this intent would turn
into a convention. The flattened layer stack has one natural home for aggregate
queries (a new module beside `repository`), and `app/sentiment.py` is a fan-out-0
leaf that already owns `LABELS` — a third candidate for the term tokenizer, which
currently lives as a private regex inside the offline engine.

### Q10 — Code Style: should the layer boundaries become machine-checked?

**Evidence:** the import graph is acyclic and descending, and the module docstrings
carry a `Single responsibility:` boundary declaration. But `lint.select` does not
include `TID`, so the three promises are prose, not gates. `ruff rule TID251`
(`banned-api`) is available in the pinned 0.16.9 — the three promises could become
three gate failures for a config-only change.

### Q11 — Deployment: should loopback-only become mechanically binding?

**Evidence:** "localhost only, no auth" stands as an affirmed rule. But `HOST` has
no call site in the run path, so `uvicorn app:app --host 0.0.0.0` would expose an
unauthenticated app holding the API key, and every test would still pass. The rule
is currently a convention with no enforcement.

### Q12 — Deployment: adopt any security scanning now?

**Evidence:** no secret scanner, no dependency audit, no SAST, no pre-commit hook,
no CI. PyPI is reachable, so the absence is a decision rather than a limitation.
Four fake keys in the tree already match the real key shape, so any scanner's
first run needs those allowlisted or it is noise the team learns to ignore.
`C-5` also needs a ruling: `fastapi` now hard-depends on `opentelemetry-api`,
putting 14 runtime distributions behind the "no hosted dependencies" rule.

### Q13 — Code Style: two smaller settings

**Evidence:** `lint.target-version = "py311"` while the runtime is CPython 3.14.7 —
the project's only static security analysis targets a Python the app never runs.
And the repository has no `LICENSE` and no licence policy.

### Q14 — Testing Posture: how are the analytics numbers pinned?

**Evidence:** no `AVG` / `GROUP BY` / `strftime` / `json_extract` assertion exists
anywhere in the suite, so a wrong date-bucket boundary would stay green under the
80 % line floor. Likewise `_rebuild_analyses` drops every index on `analyses` and
no test inspects `sqlite_master WHERE type='index'`, so the indexes this intent
adds would vanish silently on any migrating store.
## Consolidated Summary Confirmation

Everything below is what this stage produced and what promotion would write into
the space's standing memory. Read it as the whole change, not as a digest.

**What was produced**

Four artifacts under `inception/practices-discovery/`, plus one contribution file
per support agent:

- `team-practices.md` — the five sections, in team voice
- `discovered-rules.md` — 13 `ALWAYS` and 3 `NEVER` rules, each source-stamped
- `evidence.md` — what each participant inspected or inferred, all fourteen
  decisions, and 11 unresolved items
- `practices-discovery-timestamp.md` — `Discovered: 2026-10-01T22:11:46Z at commit beeb587`
- `contributions/aidlc-quality-agent.md`, `contributions/aidlc-developer-agent.md`,
  `contributions/aidlc-devsecops-agent.md`

**The fourteen decisions, and what each changes**
| # | Decision | Effect on standing memory |
|---|---|---|
| Q1 | Commit shape `<scope>: <summary> (<scope> scope)` affirmed | `Way of Working` promoted from observation to rule |
| Q2 | Thin-slice default kept; slice = one analytics endpoint end-to-end | `Walking Skeleton` gains a concrete reading |
| Q3 | Gates run from a platform-neutral verification script | closes the "where do the gates live" open point |
| Q4 | 80 % line floor unchanged; branch coverage off | 3 measured partial branches recorded as the cost |
| Q5 | Every defect ships a reproducing test | closes an open point and reverses the R-01 precedent |
| Q6 | Dependency lockfile with hashes | supply chain moves from open to scheduled work |
| Q7 | Analytics endpoints are `/v2`; `/v1` untouched | settles the description-vs-`C-4` conflict |
| Q8 | `mean intensity` dropped from the summary | the retired column stays retired |
| Q9 | Aggregate queries in a new read module beside `repository` | turns a long-standing accident into a recorded arrangement |
| Q10 | `ruff TID` (`banned-api`) added | layer boundaries become gate failures, not prose |
| Q11 | Loopback bind enforced at startup | upgrades a documentation claim to enforcement |
| Q12 | Secret scanning and a dependency audit adopted | the four known fake keys need allowlisting |
| Q13 | `target-version` matches `requires-python`; a `LICENSE` is added | fixes an analysis targeting an unused Python |
| Q14 | Hand-written expected values, plus an index-survival test | the migration path is asserted, not assumed |

**Three claims the review falsified, and how they were handled**

1. **"No broad catch anywhere" was false.** `app/db.py:163` catches
   `BaseException` for the migration rollback, and the grep offered as proof could
   not support the claim. Restated accurately, with that one site named, rather
   than promoted into a rule.
2. **"Exactly two runtime packages" was false in distribution terms.**
   `fastapi` now hard-depends on `opentelemetry-api`. The rule was restated to
   "declare exactly two; transitives are expected", which matches what
   `tests/test_config.py` actually asserts.
3. **Two CodeKB rows are stale** and are named in both `team-practices.md` and
   `evidence.md` so no later stage cites them as authority: `ensure_page_state`
   (exists nowhere; the owner is `get_connection`) and a `from __future__` count
   of 12 where it is 11.

Also corrected: `filterwarnings = ["error"]` fails on any warning from any
source, and with no lockfile the suite's pass/fail state depends on the resolved
dependency set; the baseline's single-author identity never existed in this
history; there is no scanner, audit, SAST, hook or CI, and that must not read as
coverage; `S105` does not fire on `API_KEY`.

**Deliberately not made rules**

Eight candidates stayed out of `discovered-rules.md`, all listed in `evidence.md`
so the choice is visible and reversible: Q7's router shape, Q2's per-feature
slice, Q4's floor setting, Q8's dropped field, Q13's `LICENSE` as a deliverable,
and two rules the security spoke proposed that **you never ruled on** — never
widening security suppressions outside `tests/`, and pairing any lint rule-set
change with its config test. The security-suppression rule had the strongest
evidence in the run and is still absent, because it was not human-stated.

**Known tension, recorded not resolved**

**Q12 never ruled on whether "no external services" reaches a transitively-pulled
telemetry API.** The rule still reads "introduce", and the tension is recorded in
`evidence.md` rather than silently resolved either way.

[Answer]: Looks correct
