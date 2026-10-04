# Scopes

Every AI-DLC intent that has run in this repository, and what each one left behind.

Five intents, four distinct scopes, all `complete`. Read from
`aidlc/spaces/default/intents/intents.json`; stage counts from each intent's
`aidlc-state.md`.

| Intent | Scope | Stages completed | Tag | Commit |
|---|---|---|---|---|
| `sentiment-analysis` | `poc` | 7 of 33 | — | — |
| `sentiment-v1` | `classic` | 14 of 33 | `v1-classic` | `4eb9b74` |
| `csv-bulk-import` | `express` | 9 of 33 | `express` | `beeb587` |
| `analytics-layer` | `feature` | 26 of 33 | `feature` | `f3b5185` |
| `analytics-view-packaging` | `express` | 10 of 33 | `express-2` | `bf49881` |

**On the denominator.** 33 is the compiled stage-graph size, which every intent
carries. The `feature` scope's own runtime summary reports **26 of 30** instead,
because it excludes the three workspace-bootstrap stages
(`workspace-scaffold`, `workspace-detection`, `state-init`) — they are marked
untracked in that scope's validity advisory. Both figures are correct on their own
basis; 33 is used here so all four rows are comparable.

Scope is the depth dial: it decides how many stages run and how many gates a human
holds. The four scopes here are deliberately different sizes, and the spread in
outcome below is mostly that dial doing its job.

---

## 1. `poc` — sentiment-analysis

**Sep 29. 7 stages. No release tag.**

The original intent: build the app. Its `project-description.json` is the most
detailed brief in the repository and specifies the engine (Jev on OpenRouter,
`typesafe/jev-1.13`), the `SentimentClient` interface with two implementations,
the SQLite schema, and the requirement that dev and tests run with **no key and
no network**.

It ran Ideation, Inception and part of Construction, then stopped at
`build-and-test`. Status is `complete`.

**Why there is no `poc` tag, and why that is not an oversight.** This intent
produced **no commit of its own**. `main`'s initial commit is
`4eb9b74`, which is the `v1-classic` release, and it is the commit where the
application code first entered version control — 25 `app/` and `tests/` files,
including everything the poc built. The poc's work reached the repository
*through* the classic scope's squashed commit.

That is why `## Way of Working` in `team.md` reads the way it does:

> *"Affirmed 2026-09-30, when `main` still carried only the harness and the
> application sat on an unmerged `v1-classic`."*

The practice was written **after** the poc, in response to exactly this: the
application existed but had never been released on its own. Tagging `poc` at
`4eb9b74` would mean pointing two tags at one commit, which is worse than
recording that the poc had no release of its own.

---

## 2. `classic` — sentiment-v1

**Sep 30. 14 stages, 4 skipped. Tagged `v1-classic` → `4eb9b74`.**

Hardened the poc output to a releasable v1. This is the commit that made the
application exist in version control at all: `app/` and `tests/` in full, plus the
whole AI-DLC harness shell.

Four stages skipped, recorded with reasons rather than fabricated. Its design work
established several constraints the later scopes inherited:

- **exactly two declared runtime dependencies** — `fastapi` and `uvicorn`
- **declared versus resolved** — two declared, fourteen resolved, and the
  distinction is asserted by a test so it cannot blur
- **offline by default** — the session-wide socket guard in `tests/conftest.py`
  originated here and every later scope kept it armed
- **`## Deployment`** — "a localhost checkout, and a commit is the release"

---

## 3. `express` — csv-bulk-import

**Sep 30. 9 stages, 1 skipped. Tagged `express` → `beeb587`.**

The lightest scope in the set, and the clearest demonstration of what the dial
buys you: requirements to a working feature in nine stages.

Added CSV bulk import and export. It touched **11 files** across `app/` and
`tests/` — `db.py`, `models.py`, `repository.py`, `routes.py`, `service.py` and
six test modules. The `import_id` grouping column and the `GET /v1/analyses/export`
surface both come from here.

The export surface it shipped is the one that later stages had to characterise
rather than fix: it requires an `import_id`, excludes every row whose
`import_id` is `NULL`, and its column list omits `probabilities` and `intensity`.
So it is a view of one import, **not** a backup — on a three-row store it returns
one row. That limitation is recorded in the README and as `BL-04` in the feature
scope's backlog.

---

## 4. `feature` — analytics-layer

**Oct 1–3. 26 of 30 stages. Tagged `feature` → `f3b5185`.**

The heaviest scope here, and the one this session ran end to end: 48.6 hours
wall-clock, 232 artefacts, 110 learnings captured, 415 sensor fires.

Added a read-only analytics layer — `GET /v2/analytics/summary`,
`GET /v2/analytics/terms`, a second page section, the additive `v3 → v4` migration
with its three named indexes, and the connection-model fix for risk R-01.

Delivered: **192 tests passing, 97.06 % line coverage** against an 80 % floor,
ruff clean, `/v1` untouched.

### What it did not finish

- **Three of four planned Units were never built.** `u2-term-extraction`,
  `u3-analytics-view` and `u4-platform-packaging` do not exist. The
  Construction → Operation boundary verdict is **FAIL** with eleven findings.
- **Two NFR targets ship `Unverified`** — `NFR4.6` and `NFR4.7`, both owned by
  `u3-analytics-view`.
- **`app/terms.py` is a disclosed unit-boundary violation.** It belongs to
  `u2-term-extraction`; three inception artefacts forbid `u1` from building it,
  and `unit-of-work.md:62` records the obligation that U1's terms work must not
  be sequenced ahead of U2. Root cause is Delivery Planning's ordering, not the
  code. Disclosed in the plan, the code summary and the stage diary.
- **Twelve post-ship defects** found by the Operation phase and left unfixed, led
  by a writer lockout that takes 100 % of reads down for five seconds because
  `app/db.py:213` sets no `busy_timeout`.

### Why three Units were never built — the framework went haywire

The three unbuilt Units are **not** a scoping choice. The **engine wedged**: the
per-Unit walk stopped in `u2-term-extraction`'s `code-generation` stage on an
unreachable `UNIT_COMPLETED` receipt (`UNIT_COMPLETION_MISSING`), reproduced three
times with no exit using the engine's own verbs.

The loop is closed because the two remedies the engine offers are jointly
unsatisfiable:

- `request-review` produces a recordable `REVIEW_COMPLETED`, but `unit start` is
  refused while a recovery `ask` holds routing — *"the engine currently routes a ask
  directive"* — and that ask re-arms on the next `next`.
- The other remedy, a redo-jump, emits `STAGE_JUMPED`, which invalidates every prior
  review receipt — so the jump destroys the very receipt the Unit needs, and the walk
  is back at `UNIT_COMPLETION_MISSING`.

Two contributing defects made it unfixable from inside the review: the dispatched
reviewer's `write` is refused by the plan-approval guard
(`CODE_GENERATION_EXECUTION_INELIGIBLE`, because the review file lives outside the
stage record directory), and the permitted shell workaround changes the source
fingerprint, so the verdict is then refused as *"source changed after
REVIEW_REQUESTED"* — **producing the review is what invalidates the review**. A
stale compiled `bolt_dag` compounded the routing.

`u2-term-extraction` was complete in substance — the module adopted, its defect
fixed, the artifacts written, a `READY` review on disk — but the walk will not
advance past an unsettled Unit, so `u3-analytics-view` and `u4-platform-packaging`
were **unreachable in that intent**. The engine's own recommendation was to route
around it: start a fresh intent rather than continue one whose walk is wedged.
**§5 is that fresh intent.** Full detail, the reproduction table and the
recommendations: [`../ENGINE-DEFECT-REPORT.md`](../ENGINE-DEFECT-REPORT.md).

Full detail in [`OUTCOMES.md`](OUTCOMES.md) and the ranked backlog in
`operation/feedback-optimization/feedback-loop.md`.

### The tag sits two commits behind `main`

`feature` points at `f3b5185`, the audited end of the Operation phase. The two
commits after it are documentation — this file and the README correction — and
were deliberately left outside the release. `aa0b1e4` is where the code landed;
`f3b5185` is where the Operation record ends.

---

## 5. `express` (second run) — analytics-view-packaging

**Oct 4. 10 of 10 in-scope stages. Tagged `express-2` → `bf49881`.**

The follow-on that finished the analytics layer — and it was **required**, because
the framework wedged the previous intent (§4, "Why three Units were never built —
the framework went haywire"). The `feature` scope shipped the `/v2` server but its
per-Unit walk reached an unreachable completion receipt before the view and the
packaging landed, so `u3-analytics-view` and `u4-platform-packaging` could not be
reached **in that intent**. The engine's own recommendation was to route around it
with a fresh intent; this is that intent, re-running the two remaining deliverables
under the lighter `express` dial.

Added the **analytics view wiring** — the terms section, the date-range control,
the per-section partial-failure marker (`NFR4.6`) and the supersede / no-silent-retry
guard (`NFR4.7`) — and the **platform packaging**: a `make verify` gate,
`detect-secrets`, `pip-audit`, a hashed `requirements.lock`, an MIT `LICENSE`, and
`ruff TID251` boundary rules.

Measured: **198 tests passing, 97.06 % line coverage** against the 80 % floor,
`make verify` green end to end, a 14/14 real-HTTP smoke run, and the operator's
store byte-identical (sha256 and mtime). `/v1` untouched; runtime dependencies still
exactly two.

**Why `express-2` and not `express`.** The `express` tag already names the
`csv-bulk-import` release, and a scope tag is a release name. Rather than force-move a
published tag, this second `express` run carries `express-2`.

**What it closed.** The two targets the `feature` scope left `Unverified` — `NFR4.6`
and `NFR4.7` — now ship with static served-asset assertions plus the manual end-to-end
step (no browser execution is admitted under the two-package cap). Of the three unbuilt
`feature` units, `u3-analytics-view` and `u4-platform-packaging` land here as one
stage-level iteration; `u2-term-extraction` had already been built by the prior intent.

**Still open** (full detail in
[`OUTCOMES-analytics-view-packaging.md`](OUTCOMES-analytics-view-packaging.md)): a git
remote now exists (contrary to `team.md`'s "no remote"); the summary series width is
unbounded; a `422` emits no application log line; the `uvicorn --host` bind bypass; log
retention; and the accepted R-01 thread-affinity limitation.

---

## The pattern across all five

**Each scope left the next one better-constrained.** The poc wrote the brief.
`classic` turned it into a release and wrote the dependency cap and the offline
guard. The first `express` run added a surface and a migration. `feature` added a
read path and a version prefix. The second `express` run added the view wiring and
the packaging instruments — the gate (`make verify`), the secret scan, the
dependency audit and the lockfile. Nothing in `analytics-layer` or
`analytics-view-packaging` changed a `/v1` behaviour.

**Four of five carry a tag, and the fifth's absence is the record.** The
convention was affirmed on Sep 30, between the poc and `classic`.

**Every scope's Open questions outlived it.** `team.md` and `project.md` now hold
185 learned entries — 42 in `team.md` and 143 in `project.md`. `project.md` is
almost entirely the residue of the `feature` scope: the shape of its trade-offs is
still readable, lesson by lesson, in the order they were learned.

**One gap worth noticing.** The `poc` and `classic` scopes both stopped at
`build-and-test` as their last recorded stage, and both are marked `complete`.
That is the scope boundary working — those workflows never ran Operation phases —
but it means the early intents have no incident-response, performance-validation
or feedback record. Both `express` runs and `feature` reached Operation, and the
findings that now shape how this app is documented all come from `feature` (with the
second `express` run closing the two `Unverified` targets that scope left behind).