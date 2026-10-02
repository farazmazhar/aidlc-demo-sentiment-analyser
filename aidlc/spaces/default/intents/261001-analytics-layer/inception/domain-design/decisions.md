# Architecture Decision Records — Domain Design — sentiment-opencode v2 analytics layer

> **Intent:** `261001-analytics-layer` · stage `domain-design` (inception).
>
> This is the durable decision log for the logical building blocks the analytics
> layer adds. Each ADR follows the inception-phase structure — **Context /
> Decision / Consequences / Alternatives Rejected**. The `components.md` Rationale
> table is the quick per-component justification; this file is the record.
>
> The eight boundary rulings in `domain-design-questions.md` are the inputs; where
> a ruling had a real alternative, the rejected options populate the ADR's
> **Alternatives Rejected**.

## ADR Index

| ADR | Title | Status | Date |
|---|---|---|---|
| ADR-001 | Three analytics building blocks, two as new components | Accepted | 2026-10-02 |
| ADR-002 | `TermExtraction` as its own leaf module with two operations | Accepted | 2026-10-02 |
| ADR-003 | The two HTTP handlers join `routes.py` behind a new `v2_router` | Accepted | 2026-10-02 |
| ADR-004 | `db.py` retains ownership of the migration and the three indexes | Accepted | 2026-10-02 |
| ADR-005 | The analytics component owns computed value shapes, not persisted entities | Accepted | 2026-10-02 |
| ADR-006 | The R-01 fix is owned by the HTTP API Surface component | Accepted | 2026-10-02 |
| ADR-007 | The analytics view lives inside Web UI; no second script, no new Web UI component | Accepted | 2026-10-02 |
| ADR-008 | No existing boundary moves; the route → read-module edge is recorded | Accepted | 2026-10-02 |
| ADR-009 | Platform packaging and tooling obligations are not components | Accepted | 2026-10-02 |

---

## ADR-001: Three analytics building blocks, two as new components

### Status
Accepted

### Date
2026-10-02

### Context

The analytics layer needs a place to compute aggregates over stored rows, a place
to define what a "significant term" is, and a place for the view to live. The
CodeKB found `repository.py` is "the natural and uncontested home for aggregate
SQL and is currently clean", `routes.py` is the largest file and highest fan-out
in the system and where every endpoint lands by default, `app.js` already owns
the page behaviour, and the repository has exactly one tokenizer —
`_WORD = re.compile(r"[a-z']+")` at `app/dummy_client.py:68`, underscore-private
inside the offline engine. The team had already ruled that aggregate reads live
in a **dedicated read module beside `repository`** rather than in `repository`
itself, and that reads go `route → read module` and never through `service`.

The force at play is boundary discipline: the codebase is a flat by-layer package
with an acyclic descending import graph, and every module's docstring names what
it does *not* contain. An extension that puts aggregates in the repository, terms
inline, and view logic in a second script would erode three boundaries at once.

### Decision

The feature adds **three logical building blocks**, realised as **two new
top-level components plus growth inside one existing component**:

- **`AnalyticsRead`** — a new component and module beside `repository`, owning
  all aggregate read queries and called from the route.
- **`TermExtraction`** — a new component and leaf module owning the single
  word-splitting rule.
- **The analytics view** — a new logical region **inside the existing `Web UI`
  component**, which grows. It is not a new top-level component.

The count is "three building blocks" as the human ruled; the catalogue records
two new component names plus one existing component whose `behaviour` states what
changes, because ruling 5 forbids a new Web UI component (ADR-007).

### Consequences

**Positive**
- The read path, the tokenizer and the view each land in the boundary that already
  owns that concern, so the existing acyclic descending graph is preserved.
- `AnalyticsRead` is independently testable: it takes a connection and returns
  computed shapes, so the aggregate tests never need a request object.
- The tokenizer is promoted out of an engine into a shared leaf, closing the
  repository's one accidental dependency (TD-6) rather than adding a second.

**Negative**
- `routes.py` grows again (ADR-003), so the file that the CodeKB already names as
  the first boundary an extension should watch becomes larger still.
- A reader counting "three new components" in the ruling will find only two names
  in the catalogue; the third is a growth, and the mismatch is stated explicitly
  so it is not read as an omission.
- `AnalyticsRead` and `repository.py` are peers that both issue SQL against the
  same table from different concerns; keeping them from drifting into each other
  is a discipline, not a mechanical guarantee.

**Neutral**
- Module filenames are indicative here and pinned at Functional Design; the
  catalogue names components, not files.
- The full pre-existing import graph is unchanged; only new edges are added.

### Alternatives Rejected

- **Two components — fold term extraction into the analytics component** (Q1
  option B). Rejected: it matches the team's stated boundaries less well, and it
  would either duplicate the tokenizer or force the engine to depend on the
  analytics module — the entanglement FR4.5 exists to prevent.
- **Four components — the three above plus a `v2` router component** (Q1 option
  C). Rejected: a second HTTP surface would split ownership of the one error
  envelope and the one connection lifecycle, and the `/v2` prefix is exactly the
  pattern `v1_router` already uses inside `routes.py` (ADR-003).
- **Put the tokenizer in `app/sentiment.py`** (Q2 option B). Rejected: it would
  make a fan-out-0 contract leaf the owner of label vocabulary *and* text
  processing — a second responsibility on the file that must stay smallest
  (ADR-002).

### References
- `domain-design-questions.md` Q1, Q2
- `aidlc/spaces/default/codekb/sentiment-opencode/architecture.md` § Extension Seams
- `aidlc/spaces/default/memory/team.md` § "Where reads go", § "Boundaries we are keeping"

---

## ADR-002: `TermExtraction` as its own leaf module with two operations

### Status
Accepted

### Date
2026-10-02

### Context

The only tokenizer in the repository is `_WORD = re.compile(r"[a-z']+")`
(`app/dummy_client.py:68`) — underscore-private, inside the *offline engine*, and
not shared. The analytics layer needs word tokens plus a stopword filter and a
minimum length; the offline engine needs word tokens and nothing else. `team.md`
records a direct prohibition: "Do not import `_WORD` from another module, and do
not copy the regex", and the no-junk-drawer convention forbids a `utils.py`.

The risk is specific and testable: if the analytics filter (3-character minimum,
stopword exclusion) and the engine's tokenizer are the same call, a change to
scoring vocabulary for analytics could silently change sentiment scoring.
`FR4.5` and `US4.2` require the engine's scoring behaviour to be **identical**
before and after, and require the promoted module to expose **two distinct
operations**.

### Decision

`TermExtraction` is a **new component in its own module**, beside `app/sentiment.py`
and not folded into it. It exposes **exactly two operations**:

1. **tokenize** — lowercase, then split into maximal runs of ASCII lowercase
   letters and apostrophes.
2. **filter to significant terms** — a token survives only if it is 3 or more
   characters and absent from the fixed in-repo English stopword list.

The **offline engine calls only the first**. The analytics path calls both. The
stopword list is a single versioned constant applied case-insensitively.

### Consequences

**Positive**
- The two operations are structurally separate, so a caller cannot accidentally
  apply the analytics filter to engine scoring (AC4.2.3).
- The engine's scoring is provably unchanged: it loses its private regex and gains
  one call to `tokenize`.
- The tokenizer now has one public home, closing TD-6 rather than encoding the
  accident.

**Negative**
- One new module is added for what is, on its own, a small amount of code —
  justified only because it has two consumers with deliberately different rules.
- The offline engine changes file, so its tests must confirm scoring parity across
  the refactor (US4.2, AC4.2.2).

**Neutral**
- The specific stopword entries remain an open question for Functional Design
  (`FR4.4` bounds them; the contents are a design choice).
- Non-Latin scripts contribute nothing — a recorded, accepted limitation (FR4.6).

### Alternatives Rejected

- **Add both operations to `app/sentiment.py`** (Q2 option B). Rejected: it makes
  the fan-out-0 contract leaf own the label vocabulary *and* text processing,
  violating its single responsibility, and it mixes the engine's contract with an
  analytics utility.
- **A `TermExtraction` component but keep the module coupling as an option**
  (Q2 option C was "new component whose module is `app/terms.py`, with
  `dummy_client` and the analytics component both calling it"). This is
  substantially the choice made; the naming of the module is deferred, and the
  ruling's binding content — its own component, its own module, two operations —
  is what is recorded.
- **Fold term extraction into `AnalyticsRead`** (Q1 option B, restated at Q2).
  Rejected: it would force the offline engine to depend on the analytics module.

### References
- `domain-design-questions.md` Q2
- `FR4.1`–`FR4.6`, `US4.1`, `US4.2`
- `aidlc/spaces/default/memory/team.md` § "The tokeniser"

---

## ADR-003: The two HTTP handlers join `routes.py` behind a new `v2_router`

### Status
Accepted

### Date
2026-10-02

### Context

`routes.py` is 387 lines, the largest file and the highest fan-out in the system,
and it is where every endpoint lands by default — the CodeKB names its size as the
first boundary an extension should look at. Two new read endpoints are needed on a
new `/v2` prefix. `routes.py` already carries `v1_router` (data contract) and an
unprefixed `router` (page and `/auth/*`), and `D3` in `architecture.md` records
that the two-router split is the established insertion point for a new data
router: "A new data surface gets its own `APIRouter(prefix=…)` and one
`include_router` line."

The new endpoints are reads, and the team ruled that reads call the query layer
directly rather than through `service`.

### Decision

The two handlers join **`routes.py` behind a new `v2_router`** on the `/v2`
prefix. `routes.py` grows; **no new HTTP component and no new routing module** are
introduced. Both handlers call `AnalyticsRead` directly and never
`Analysis Orchestration`. Validation and storage failures travel through the one
existing `error_response` envelope.

### Consequences

**Positive**
- The one error envelope and the one connection lifecycle (`get_connection`) stay
  owned by a single component, so neither can drift.
- The new surface follows the established `/v2` router convention rather than
  inventing a second routing pattern.
- The frontend prefix assertion (US6.2, AC6.2.3) compares two copies that both
  live in known places.

**Negative**
- `routes.py` grows further, and the CodeKB's warning that "the file's growth is
  the metric to watch" becomes more pressing. This is the accepted cost of
  keeping one HTTP surface component.
- A future split of `routes.py` (page vs data vs support routes) is now more
  likely, and this ADR is the record that the split was consciously deferred.

**Neutral**
- `V1_PREFIX` remains; `v2_router` carries its own prefix constant. The `/v1`
  contract, its routes, its response shapes and its tests are unchanged (NFR5).

### Alternatives Rejected

- **A new `AnalyticsRoutes` component in its own module, mounted by `main.py`**
  (Q3 option B). Rejected: it would split ownership of the one error envelope and
  the connection lifecycle across two files for no new concern, and the
  established `v1_router` pattern already provides the insertion point.

### References
- `domain-design-questions.md` Q3
- `FR2.1`, `FR3.1`, `NFR5`, `US8.5`
- `aidlc/spaces/default/codekb/sentiment-opencode/architecture.md` D3, § Extension Seams

---

## ADR-004: `db.py` retains ownership of the migration and the three indexes

### Status
Accepted

### Date
2026-10-02

### Context

The migration and the schema live in `db.py`, which already owns all DDL and the
in-place migration. `db.py` also carries **TD-1**: `_rebuild_analyses` performs
`RENAME` → `CREATE TABLE` → `COPY` → `DROP TABLE` and `CREATE_ANALYSES_TABLE`
declares no index, so an index added to that DDL is **silently destroyed** on any
migrating store. The feature must move the schema v3 → v4 additively and create
three indexes, and a test must assert by name that they survive a rebuild.

`FR5.3` (as corrected in Revision 2) requires the rebuild to re-create the
indexes explicitly as statements after the copy, because SQLite's `CREATE TABLE`
has no index declaration.

### Decision

**`db.py` keeps ownership.** The v3 → v4 migration and the three indexes
(`idx_analyses_created_at`, `idx_analyses_import_id`,
`idx_analyses_label_created_at`) are a **change inside the existing
`Persistence and Schema` component**, not a new component. `_rebuild_analyses`
re-creates the indexes explicitly after the copy. The stored version is bumped to
4 in the same transaction. No separate index or migration owner is introduced.

### Consequences

**Positive**
- The fix lands with the defect: the component that drops indexes is the component
  that re-creates them, so the two cannot diverge.
- The index creation, the migration and the version bump stay inside one
  transaction, preserving FR5.6's fail-loudly-and-roll-back guarantee.
- `init_db`'s existing placement rule (a new DDL statement after the
  migrate-or-create branch, as `schema_meta` already does) is reused rather than
  refactored.

**Negative**
- `db.py` remains "at-risk" per the CodeKB. TD-2 (a new column is a five-place
  edit) is untouched because the feature adds no column; the migration itself is
  still the module's hardest code.
- Naming drift around the schema version (accident 3 in `team.md`) becomes more
  misleading at v4; a later reader must not trust `_is_v1_shape`'s name.

**Neutral**
- The indexes are owned as schema artifacts, recorded in the component's
  `behaviour`, and are **not** domain entities (ADR-005).

### Alternatives Rejected

- **A new `SchemaMigration` component, splitting DDL out of `db.py`** (Q4 option
  B). Rejected: it would separate the migration from the module that owns the
  defect, add a component whose responsibility is already single, and increase the
  amount of code that has to be coordinated around one transaction.

### References
- `domain-design-questions.md` Q4
- `FR5.1`–`FR5.7`, `US5.1`, Revision 2 corrections to `FR5.3`
- `aidlc/spaces/default/codekb/sentiment-opencode/component-inventory.md` TD-1, TD-2

---

## ADR-005: The analytics component owns computed value shapes, not persisted entities

### Status
Accepted

### Date
2026-10-02

### Context

Domain Design captures entities at the ownership-plus-shape level, and every
entity must have exactly one owner. The analytics aggregate is computed on request
from stored rows and is never stored. The question is whether the component that
computes it owns any entity at all, or whether its output shapes are behaviour
rather than entities.

The codebase has a precedent: `ImportSummary` (`app/service.py`) is a computed
aggregate returned to the caller, never persisted, with a mean that is `None`
rather than a fabricated `0.0`.

### Decision

**The analytics component owns computed value shapes only, and owns no stored
entity.** `AnalyticsRead` owns five entities — `AnalyticsSummary`, the per-day
`AnalyticsSeriesEntry`, `TermFrequencyEntry`, `PositiveTermList` and
`NegativeTermList` — each recorded with an explicit **computed, not persisted**
lifecycle. Every **persisted** entity stays owned by `Persistence and Schema`
(`StoredAnalysis`, `SchemaVersion`). `TermExtraction` owns no entity: its outputs
are transient token sequences and significant-term sets of plain strings.

### Consequences

**Positive**
- The persisted/contract boundary stays single-owner: Functional Design can see at
  a glance that no analytics table, migration or index is implied.
- A later stage cannot read the catalogue as "the analytics response is a stored
  entity" and invent a persistence requirement.
- `TermExtraction`'s emptiness is explicit, so its "two operations" are not
  mistaken for an entity model.

**Negative**
- The response shapes are owned by `AnalyticsRead` while the persisted row shape is
  owned by `Persistence and Schema` and its contract by `Record and Request
  Contracts` — three owners around one payload. This is deliberate but is the
  boundary a later stage is most likely to blur, and it is recorded as such.
- `TermFrequencyEntry` and the two list entities are small enough to be arguable as
  one shape repeated; the catalogue keeps them separate so the two term lists
  appear as the ruling requires and Functional Design can fuse or split them.

**Neutral**
- Attribute names are captured; types, validation rules and cardinality are
  deferred to Functional Design.

### Alternatives Rejected

- **No entity entries at all — empty `entities:` list, shapes named only in
  `behaviour`** (Q6 option B). Rejected: it would hide the computed lifecycle of
  the value shapes and make story-to-entity traceability impossible, without
  buying any accuracy.

### References
- `domain-design-questions.md` Q6
- `FR2.3`, `FR2.9`, `FR2.7`, `FR3.3`, `A3`
- `aidlc/spaces/default/codekb/sentiment-opencode/architecture.md` A2/A3

---

## ADR-006: The R-01 fix is owned by the HTTP API Surface component

### Status
Accepted

### Date
2026-10-02

### Context

The team ruled that **this feature fixes R-01**, the accepted cross-thread SQLite
connection defect: concurrent overlapping requests must not raise
`sqlite3.ProgrammingError`, and the connection's thread affinity and lifecycle
must be **decided explicitly in code** rather than inherited from `sqlite3`'s
default, with the decision stated in the owning module's docstring.

`get_connection` (`app/routes.py:92`) is the **only** place the `sqlite3` driver
and the connection lifecycle are touched anywhere in the codebase, and therefore
the only place the defect lives.

### Decision

The **`HTTP API Surface` component owns the R-01 fix**. The chosen thread-affinity
and lifecycle decision is made explicitly and stated in that module's docstring.
**No boundary moves** — connection lifecycle does not relocate to
`Persistence and Schema`. The owned module is the one that already creates and
closes the connection.

### Consequences

**Positive**
- The fix is local to one function, so it fixes the defect for every current and
  future endpoint at once — including the polling analytics page, which is the
  access pattern most likely to expose it.
- The existing ownership rule ("Only the HTTP layer touches `sqlite3` and the
  connection lifecycle") is preserved rather than weakened.
- The fix is demonstrable: `US1.2` and `US7.7` give it a concurrency test and a
  harness that can host genuinely overlapping requests.

**Negative**
- The connection lifecycle stays at the HTTP edge, so any future non-HTTP reader
  that needs a connection must still be handed one. That is the accepted cost of
  keeping the boundary intact.
- The harness replacement (FR7.7) is a prerequisite; without it the fix cannot be
  proved, so the test-harness change is on this feature's critical path.

**Neutral**
- `db.connect` may gain an explicit thread-affinity argument; the choice is stated
  here as "explicit, documented" and pinned to a concrete mechanism at Functional
  Design.

### Alternatives Rejected

- **Persistence and Schema owns it, moving connection lifecycle down to where the
  driver lives** (Q7 option B). Rejected: it would move an existing boundary for a
  fix that does not require the move, and it would put connection ownership in two
  places during the transition. The defect is in the caller, not the driver
  library.

### References
- `domain-design-questions.md` Q7
- `FR1.6`, `FR7.7`, `US1.2`, `US7.7`, `FR8.4`
- `aidlc/spaces/default/codekb/sentiment-opencode/component-inventory.md` TD-5

---

## ADR-007: The analytics view lives inside Web UI; no second script, no new Web UI component

### Status
Accepted

### Date
2026-10-02

### Context

`app.js` is 201 lines and gains the analytics view, the nav, view switching and
two fetches. The existing `Web UI` component owns `index.html` and `app.js`
together. The view must be a third top-level entry inside the existing
single-page shell, added to the existing static-asset serving — not a second site,
not a separate URL tree (FR6.1, C-3).

The page has no build, no bundler, no `package.json` and no framework; it is one
HTML file with an inline `<style>` and one vanilla script. Splitting the script
would create a file seam and a load-order concern the page does not otherwise
have.

### Decision

**`app.js` stays inside `Web UI`, which grows.** The analytics view is a new
logical region of the same component and the same script file. **No second script
file and no new Web UI component** are introduced. The view uses native HTML and
the page's existing class names, renders everything through `textContent`, and
adds no front-end dependency.

### Consequences

**Positive**
- One script, one load path, no build step — consistent with the two-runtime-
  package cap and the no-front-end-dependency rule.
- The existing static-asset serving and the existing `data-testid` pinning
  convention are reused as-is.
- The page's accessibility affordances and its no-XSS-sink property
  (`textContent` everywhere) carry over to the new view.

**Negative**
- `app.js` grows and its execution remains entirely outside the suite (no
  browser automation is permitted), so the view's behaviour is verified only by
  static markup assertions plus one manual exercise line. This is the CodeKB's
  "at-risk" rating on `Web UI`, inherited by the new view.
- The shell restructure (header, nav, three views) is a larger change to existing
  behaviour than "add a view": History and Analytics now fetch on activation
  rather than on page load. That is a consequence of the nav ruling, recorded in
  `mockups.md` §9 open point 7, not a regression.

**Neutral**
- The ruled shell changes (header/nav, three views, `error-panel` above the views,
  the `<template>` relocation) are Functional Design and Code Generation detail;
  the catalogue records only that `Web UI` grows.

### Alternatives Rejected

- **A separate `AnalyticsView` component as a second script file, with `Web UI`
  owning the shell** (Q5 option B). Rejected: it creates a second script and a
  load-order seam for no separation the page needs, against FR6.1's single-shell
  ruling.
- **`AnalyticsView` as a logical component of the same `app.js` file, drawn as its
  own boundary in the catalogue** (Q5 option C). Rejected: ruling 5 forbids a new
  Web UI component; the boundary is a logical region of one component, not a
  catalogue entry with its own dependency edges.

### References
- `domain-design-questions.md` Q5
- `FR6.1`–`FR6.9`, `US6.1`–`US6.5`, `C-3`, `C-6`
- `inception/refined-mockups/mockups.md` §2, §9

---

## ADR-008: No existing boundary moves; the route → read-module edge is recorded

### Status
Accepted

### Date
2026-10-02

### Context

`service.py` holds no read function at all: its entire public surface is writes,
engine selection and connection reporting. `app/routes.py` already imports
`list_analyses` and `list_analyses_by_import_id` from `app.repository` and calls
them directly. Until now that arrangement was an accident of where functions
landed; the team ruled it explicit: aggregate queries live in a new read module
beside `repository`, called from the route, and the service layer is not inserted
into the read path.

The question is whether recording the arrangement should also change any existing
boundary — for example, formally splitting `service` into write-only, or moving
the read path into `service`.

### Decision

**No existing boundary moves.** `Analysis Orchestration` keeps writes and engine
calls; reads never entered it and still do not. The new edge is recorded in the
catalogue: **`HTTP API Surface → AnalyticsRead`** (the route calls the read
module directly). `AnalyticsRead` additionally imports `LABELS` from
`Sentiment Engine Interface` so its aggregates bucket over the closed label set.
The acyclic property remains checkable from the catalogue, and both new edges are
strictly descending.

### Consequences

**Positive**
- The change is additive: no existing module's responsibility changes, so no
  existing test or boundary rule is invalidated.
- The read arrangement is now recorded rather than assumed, which is exactly what
  the team's "Where reads go" practice asked for.
- The catalogue's dependency graph lets a reviewer confirm acyclicity directly.

**Negative**
- `HTTP API Surface` now has a wider fan-out (it already had the highest), and it
  depends on both `AnalyticsRead` and `Analysis Orchestration`. That is inherent
  in one HTTP surface serving both writes and reads.
- `AnalyticsRead` importing `LABELS` creates a dependency from the analytics layer
  onto the engine contract. It is a leaf import with no runtime coupling, but it
  is a new edge a reviewer should see.

**Neutral**
- Whether `service` is *renamed* or annotated as write-only is deferred; the
  ruling chose to record the arrangement rather than restructure for it.

### Alternatives Rejected

- **Formalize `service` as write-only** (the restructuring half of Q8 option B).
  The read-path edge itself was **accepted** and is recorded in the Decision above;
  the additional restructuring — making `service` formally write-only — was
  rejected because it changes a boundary that does not need to change, and the
  acyclic property is already checkable from the catalogue.

### References
- `domain-design-questions.md` Q8
- `FR1.1`, `FR1.3`, `US1.1`
- `aidlc/spaces/default/memory/team.md` § "Where reads go"

---

## ADR-009: Platform packaging and tooling obligations are not components

### Status
Accepted

### Date
2026-10-02

### Context

US7.1–US7.5, US7.8 and US7.9 (lockfile, verification script, secret scanning,
LICENSE, the `ruff` banned-api rule set, `target-version`, and the README) are
affirmed practices that ship with this feature by explicit choice. They are
repository-level packaging, tooling and documentation artifacts. Domain Design
models the logical building blocks of the running system; a component is code you
write that forms a bounded part of that system, not a build artifact or a policy
file.

### Decision

These obligations are **not** modelled as components. They are marked `N/A` —
**not `GAP`** — in `traceability.json`, each with a named destination and the
reason "repository-level packaging/tooling/documentation artifact, not a logical
building block; delivered by later construction and operation stages". Two of the
platform stories — `US7.7` (concurrency harness) and `US8.7` (tests that touch the
real thing) — **do** map, to `Test Harness and Suite`, because FR7.7 genuinely
changes an existing component of the repository.

`N/A` is the correct status rather than `GAP` because **a component model is the
wrong instrument** for repository-level tooling: the story set still owns these
obligations and later construction and operation stages deliver them, so nothing
is unaccounted for. `GAP` is the status the traceability sensor **fails on**; an
implementer who copied a `GAP` marking from this ADR would break the gate. The
distinction is deliberate and mirrors the note in `components.md` under
"Platform obligations are not components".

### Consequences

**Positive**
- The component model stays about the system's structure; a `BuildAndRelease`
  component would be an invented building block that no other stage expects and
  that blurs Domain Design with Construction/Operation.
- The `N/A` routings are explicit and reasoned, so a downstream stage reads them
  as a routing decision rather than an oversight.
- No story is `GAP`, so the traceability gate stays green; the destination column
  is what carries the obligation forward.

**Negative**
- Seven of the thirty-five stories have no component target at this stage. A
  reader scanning `traceability.json` sees those `N/A` rows and must read the
  reason and destination columns rather than assume a missing component or a
  `GAP`.

**Neutral**
- This is registered in the stage return as a boundary the eight rulings do not
  settle: Domain Design's component model does not cover tooling obligations, and
  the routing of `US7.*` platform work is a later-stage concern.

### Alternatives Rejected

- **Invent a `BuildAndRelease` / `PlatformTooling` component to give the platform
  stories a target.** Rejected: it is not a logical building block of the running
  system, it would sit outside the acyclic descending graph the rest of the
  catalogue keeps, and it would force Domain Design to decide tooling that later
  stages own.

### References
- `FR7.1`–`FR7.9`, `US7.1`–`US7.9`
- `inception/domain-design/traceability.json`
