# Bolt Plan — sentiment-opencode v2 analytics layer

## Upstream inputs this plan is built from

This plan sequences work that other Inception stages defined, and it reads them
directly rather than restating them:

- **`unit-of-work.md`**, **`unit-of-work-dependency.md`** and
  **`unit-of-work-story-map.md`** (Units Generation) — the four Units, the
  dependency DAG this sequence must respect, and the story-to-Unit mapping that
  defines each Bolt's scope.
- **`requirements.md`** (Requirements Analysis, including its Revision 2
  corrections) — the `FR`/`NFR` obligations each Bolt's Definition of Done must
  satisfy.
- **`stories.md`** (User Stories) — the 35 acceptance-criteria sets a Bolt is only
  done when it meets.
- **`mockups.md`** (Refined Mockups) — the five screen states and the three-view
  shell that Bolt 3 delivers.
- **`components.md`** (Domain Design) — the component boundaries each Unit is built
  from, and the record that `AnalyticsRead` and `TermExtraction` are the new
  building blocks.
- **`contract-summary.md`** (Contract Design) — the three pinned boundaries,
  including the declared `U1 → U2` edge that places `U2` ahead of `U1` in this
  plan.
- **`team-practices.md`** (Practices Discovery) — the affirmed `Way of Working`,
  `Walking Skeleton` and `Deployment` statements this plan follows, including that
  `skeleton: on` resolves the first DAG root as the skeleton — which this plan now
  states is `u2-term-extraction`.

> **Intent:** `261001-analytics-layer` · stage `delivery-planning` (inception).
>
> This is the ordered sequence of **Bolts** for Construction. A **Bolt** is one
> build pass over a piece of the work, ending in something that runs. A **mob** is
> the small group that owns and executes a Bolt; here it is the single AI agent
> named in `team-allocation.md`.
>
> **This artifact plans; it does not build.** Nothing below is presented as
> already done. The walking-skeleton integrated check and the human checkpoint
> happen in Construction, against the verification command recorded for this
> intent — not here. The engine does not read this file to decide what to build
> first: it reads the Unit DAG in
> `inception/units-generation/unit-of-work-dependency.md`. This file chooses the
> economic order through that DAG; the DAG chooses the topology.
>
> **One Unit of Work per Bolt.** Each row bundles exactly one Unit (an **Unit of
> Work** is a work-boundary inside the single app — not a separately deployable
> service). `U1` is XL and `U3` is L, so Bolts 2 and 3 are substantial; splitting
> `U1` would detach the integrated slice, and splitting `U3` would separate the view
> from the only endpoint it reads.

## Sequence at a glance

| Bolt | Unit (directory) | Kind | Walking skeleton? | Depends on | Mob |
|---|---|---|---|---|---|
| 1 | `U2` — `u2-term-extraction` | `library` | **Yes — the resolved skeleton unit** | — (DAG root) | `aidlc-developer-agent` |
| 2 | `U1` — `u1-analytics-slice` | `service` | No | Bolt 1 (`U2`) | `aidlc-developer-agent` |
| 3 | `U3` — `u3-analytics-view` | `ui` | No | Bolt 2 (`U1`) | `aidlc-developer-agent` |
| 4 | `U4` — `u4-platform-packaging` | `packaging` | No | — (DAG root) | `aidlc-developer-agent` |

## `skeleton: on` — the first resolved DAG Unit

This scope declares `skeleton: on` (`.aidlc/scopes/aidlc-feature.md`) and
`memory/team.md` affirms a thin end-to-end slice first. The **walking skeleton**
is the smallest working version of the whole path — built before the real feature
breadth goes in, to prove the pieces connect. The runtime resolves the first Unit
of the first sorted DAG batch, and that is **`u2-term-extraction` (`U2`)**:
`U2` and `U4` are the dependency-free roots in the machine-readable edge block
(`U1` declares its dependency on `U2` as of 2026-10-04), and `u2-term-extraction`
sorts first among them.

> **The skeleton changed, and the honest consequence is recorded here.** Bolt
> order previously placed `U1` first and made it the skeleton; `U2` was sequenced
> second because the suppressed `U1 → U2` edge forced its position. Recording that
> edge in the DAG is what makes the engine resolve `U2` first. But `U2` is a
> fan-out-0 library, so the skeleton is now the tokeniser module plus its parity
> test — **not** a path through storage and HTTP. This Bolt plan therefore places
> `U2` first on topology while noting that the first *integrated* end-to-end path
> is still Bolt 2 (`U1`), which runs immediately after.

**Explicit statement: the first resolved DAG Unit is `u2-term-extraction`.** Its
expected demo and its prerequisites are given in Bolt 1 below. A first
design-stage review does not demonstrate a working skeleton; only the integrated
end-to-end run does, and that run belongs to Construction.

---

## Bolt 2 — `u1-analytics-slice` (`U1`)

**Included Unit(s) of Work:** `U1` only.

**Walking-skeleton marker:** no — but this is the **first integrated end-to-end
path** the plan builds (schema migration → `/v2` route → `AnalyticsRead` aggregate
→ summary region of the page). The Unit the `skeleton: on` rule resolves is `U2`
in Bolt 1; see the note under **`skeleton: on` — the first resolved DAG Unit**.

**Mob that owns it:** `aidlc-developer-agent` (the single AI mob; Team Formation
was skipped in Ideation — see `team-allocation.md`).

**Definition of Done.** The Bolt is done when, on a throwaway store:

- the additive, idempotent v3 → v4 migration runs in place at startup, drops,
  renames and retypes nothing, preserves every row, and rolls back in one
  transaction on failure;
- the three indexes exist **by name** — `idx_analyses_created_at`,
  `idx_analyses_import_id`, `idx_analyses_label_created_at` — and the TD-1
  `_rebuild_analyses` copy step re-creates them explicitly after the table is
  rebuilt, because SQLite's `CREATE TABLE` declares no index;
- the schema version bump and the migration land in the same transaction;
- `GET /v2/analytics/summary` answers `200`/`422`/`500` through the one existing
  error envelope, with one new storage-failure machine code and no new envelope
  member;
- `AnalyticsRead` computes `total`, per-label `counts` and `shares` (fractions in
  `[0,1]`, four decimals, `null` on a zero denominator), `mean_confidence`,
  `mean_confidence_row_count` and the per-day series, all from stored rows with
  every statement parameter-bound and no write path;
- range resolution is shared and correct: both bounds inclusive, a single bound
  never dropped, an unmatched `import_id` behaving like an empty range (empty
  series, no store-wide zero-fill), an inverted range refused `422`;
- the R-01 defect is fixed: the connection module states its thread-affinity and
  lifecycle decision explicitly, the replaced ASGI harness can host genuinely
  concurrent requests, and the concurrency test fails when the fix is reverted;
- the loopback bind is enforced at startup rather than merely documented;
- the summary region of the page renders the per-day series and the label
  breakdown from the live response;
- the offline test suite is green with no network and no key, the whole-application
  80 % line-coverage floor holds, and the existing `/v1` suite stays green.

**Scope boundary that this Bolt does not claim.** `U1`'s full scope also carries
the `/v2/analytics/terms` handler and the term-ranking part of `AnalyticsRead`.
Those consume `U2`'s module and are governed by the declared `U1 → U2` edge
(below). Bolt 1 does not claim the terms path complete; that path is integrated
once Bolt 2 lands. The summary path that the skeleton protects is genuinely
independent of `U2`.

**Confidence hypothesis — what shipping this Bolt will prove.** That an existing
store migrates forward in place with its indexes intact and no row lost, and that
genuinely overlapping requests no longer raise `sqlite3.ProgrammingError`. These
are the two riskiest pieces in the whole initiative — a data-losing migration and
a thread-affinity defect that sequential tests cannot catch — and shipping this
Bolt validates both before any later Bolt is built on top of them. It also proves
the client/server seam: stored row → computed aggregate → served view.

**Expected demo.** A real `uvicorn` run against a throwaway database, bound to
loopback, returning a live `GET /v2/analytics/summary` response over a populated
range, with the per-day series and label mix visible in the page. An offline test
asserts the same values against real SQLite and real served markup, and the
concurrency test runs two overlapping requests and passes. The integrated check
and human checkpoint belong to Construction.

**Prerequisites (explicit).**

- The existing application at schema version 3, with its `/v1` surface, single
  SQLite file and single-page shell intact — this is a brownfield extension, not
  a rewrite.
- A throwaway SQLite database for the demo, so the real store is never touched.
- The offline dummy engine in use (no network, no OpenRouter key).
- None of `U2`, `U3` or `U4` is required for the summary slice; `U1` is a DAG
  root for this reason.

---

## Bolt 1 — `u2-term-extraction` (`U2`) — the resolved walking skeleton

**Included Unit(s) of Work:** `U2` only.

**Walking-skeleton marker:** yes — the Unit the `skeleton: on` rule resolves
first, as of 2026-10-04. Its slice is the module and its parity test, not a path
through storage and HTTP; see the note under **`skeleton: on` — the first resolved
DAG Unit** for what that does and does not prove.

**Mob that owns it:** `aidlc-developer-agent`.

**Definition of Done.**

- `TermExtraction` exists as a new module beside `app/sentiment.py` and exposes
  exactly two distinct operations — `tokenize(text)` and
  `significant_terms(tokens)` — so the analytics filter can never be applied to
  sentiment scoring.
- The single word-splitting rule (maximal runs of ASCII lowercase letters and
  apostrophes), the 3-character minimum and the single versioned in-repo English
  stopword constant are owned here.
- The offline engine's private `_WORD` regex is deleted, the engine calls only
  `tokenize`, and a parity test pins identical offline scoring before and after.
- The module imports nothing from `app` (a fan-out-0 leaf) and carries the
  codebase's module conventions.
- Offline tests cover term extraction (empty range, populated range, `import_id`
  filter) with no network and no key.

**Confidence hypothesis — what shipping this Bolt will prove.** That promoting
the repository's only tokenizer leaves the offline engine's scoring behaviour
unchanged, and that the two-operation split makes the stopword/3-character filter
structurally unable to reach sentiment scoring. It also proves `U2`'s interface is
ready for `U1`'s terms path to consume.

**Expected demo.** The parity test showing identical offline scores before and
after the refactor, plus term-extraction output over a seeded positive/negative
fixture.

**Why it is sequenced first.** `U1`'s terms handler and `AnalyticsRead`'s term
ranking import this module, and that dependency is now a declared `depends_on`
entry rather than a suppression. It was previously sequenced second with the
ordering placed on this plan as a prose obligation — an obligation that could not
bind the engine, which is why `U1` was walked first and authored `app/terms.py`.
Recording the edge makes `U1`'s position depend on this module structurally.

---

## Bolt 3 — `u3-analytics-view` (`U3`)

**Included Unit(s) of Work:** `U3` only.

**Walking-skeleton marker:** no.

**Mob that owns it:** `aidlc-developer-agent`.

**Definition of Done.**

- The existing single-page shell gains a header, a nav with three view entries,
  and a third top-level analytics view served from the existing static-asset
  route — not a second site.
- The view renders the per-day series, the label breakdown with counts and shares,
  and **both** ranked term lists (the term-list containers required by
  `AC6.2.1`), plus a labelled date-range control with an unbounded default and an
  explicit `Show all time` reset.
- Changing the range refetches **both** `/v2` endpoints with the same bounds so all
  sections describe one population.
- Loading, empty, partial-failure and error states are distinct regions; a failed
  fetch renders an inline error rather than an empty-looking view; a superseded
  late response is discarded; a `null` share renders as an explicit no-share
  marker, never a fabricated `0%`.
- Rendering is native HTML with `textContent` everywhere; no chart library and no
  new front-end dependency; the analytics prefix constant is asserted equal to the
  backend `V2_PREFIX`.
- Accessibility basics hold: labelled range control, series exposed as text or a
  table, live status region, `aria-current` on the active nav entry.

**Confidence hypothesis — what shipping this Bolt will prove.** That the three
readouts describe one population consistently across a range change, and that a
failed read never looks like an empty one — the two view behaviours a static test
can pin.

**Expected demo.** A range change that refetches both endpoints and updates all
three readouts together, plus the static markup assertions and the standing manual
exercise line over the served page.

**Why it is sequenced third.** `U3` depends on `U1` alone: it fetches `U1`'s `/v2`
responses over HTTP and never imports `U2`'s module. It cannot be resolved before
Bolt 2.

---

## Bolt 4 — `u4-platform-packaging` (`U4`)

**Included Unit(s) of Work:** `U4` only.

**Walking-skeleton marker:** no.

**Mob that owns it:** `aidlc-developer-agent`.

**Definition of Done.**

- A dependency lockfile with hashes ships, with the documented install command
  consuming it.
- A platform-neutral verification script runs the standing gates — the
  whole-application 80 % line-coverage floor, the `filterwarnings = ["error"]`
  filter, and the pinned `ruff` rule set — as a developer-run script, not a
  pre-commit hook (there is no remote and no CI provider).
- Secret scanning and a dependency audit run from that script, with the known
  fake-key fixtures allowlisted against their actual literals so the first run is
  signal rather than noise.
- A `LICENSE` file exists and the distribution's licence declaration is set.
- The `ruff` `TID251` `banned-api` entries express the layer boundaries, and
  `target-version` matches `requires-python`.
- The README's HTTP surface table, file-layout tree and storage section describe
  the delivered `/v2` surface and the new modules and indexes.

**Confidence hypothesis — what shipping this Bolt will prove.** That every install
resolves to the same set rather than to the newest compatible versions, that the
gates run in one command from a fresh checkout, and that a layer-boundary breach
is a lint failure rather than something only a reviewer notices.

**Expected demo.** Running the verification script end to end, showing the
scanner and audit output, and showing `ruff` firing on an intentional boundary
breach.

**Why it is sequenced fourth.** `U4` is independent of everything — no unit
depends on it and it depends on no unit — so it could run at any point. It is
placed last because its verification script is more useful once there is a full
suite to run, and because no other Bolt waits on it.

---

## Mob ownership, Bolt size, and parallel safety

- **Mob per Bolt.** Every Bolt above is owned by the single mob
  `aidlc-developer-agent`. Team Formation was SKIPped in Ideation, so no human
  team was formed; `team-allocation.md` states the assignment in full.
- **One Unit per Bolt.** No Bolt bundles two Units and none slices across Units.
  The Unit DAG admits several valid orders; this plan chooses one.
- **Parallel-safe observation about `U2` and `U4`.** `U2` (Bolt 2) and `U4`
  (Bolt 4) have no dependency on `U1` or on each other, so in principle they could
  be built alongside Bolt 1. With one developer and one mob this changes nothing
  in practice; it is recorded so the DAG's freedom is not mistaken for a mandate
  to serialise. The one real constraint on that freedom is the declared
  `U1 → U2` edge below.
- **The declared `U1 → U2` edge — a sequencing constraint on `U1`'s terms work.**
  `U1`'s terms handler and `AnalyticsRead`'s term ranking import `U2`'s
  `TermExtraction` module. This is a real build/import dependency that
  `unit-of-work-dependency.md` records in prose rather than as a `depends_on`
  entry, and no longer suppressed. **Consequence for this plan: `U1`'s terms work
  (`US3.1`, `US3.2`, and the term-list part of `US6.2`) cannot be sequenced ahead
  of `U2` — the topology forbids it.** `U1` is Bolt 2 and `U2` is Bolt 1, so this
  is satisfied structurally rather than by a plan obligation.
- **No formal scoring model underlies this order.** The rationale — risk-first,
  walking-skeleton-first, and the declared-edge constraint — is argued in
  `risk-and-sequencing-rationale.md`.

## Traceability

Every Bolt traces to a Unit; every Unit traces to stories in
`inception/units-generation/unit-of-work-story-map.md` and to requirements in
`inception/requirements-analysis/requirements.md`. No Bolt introduces work that is
not already owned by a Unit.
