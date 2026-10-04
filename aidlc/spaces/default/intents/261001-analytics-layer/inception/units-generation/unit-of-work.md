# Units of Work — sentiment-opencode v2 analytics layer

> **Intent:** `261001-analytics-layer` · stage `units-generation` (inception).
>
> **This stage produces topology only.** It describes what can depend on what. It
> does **not** recommend an implementation order and does **not** identify a
> critical path — those are Delivery Planning's economic decisions (Stage 2.9).
> Where ordering appears below it is a **constraint**, not a plan.
>
> **Deployment model: one deployable.** Every unit below is part of the single
> application; "unit" means a **work-boundary**, not a separately deployable
> service. The DAG in `unit-of-work-dependency.md` captures **build and
> integration** dependencies, not network boundaries. This follows the human
> ruling (Q1) on the absence of any container, hosted service, or second process.
>
> **Four units** (Q2): the integrated analytics slice, term extraction, the
> analytics view, and the platform obligations. Each carries a `kind` (Q4) that
> tells Construction which design-artifact matrix applies to it.

## Upstream inputs this decomposition is built from

- **`components.md`** (Domain Design) — the twelve-row catalogue this DAG groups
  into units. The mapping is deliberate: `AnalyticsRead` and the HTTP API Surface
  land in `U1`, `TermExtraction` is `U2`, the Web UI component is `U3`, and the
  repository-level artifacts that Domain Design marked `N/A` because they are not
  components are `U4`.
- **`decisions.md`** (Domain Design) — the nine ADRs. ADR-005 (computed, not
  persisted, response shapes) is why `AnalyticsRead` can sit in `U1` without a
  schema owner of its own; ADR-008 (no boundary moves) is why no unit exists purely
  to relocate an edge; ADR-009 is why `U4` exists at all.
- **`requirements.md`** — the `FR`/`NFR` obligations each unit must satisfy.
- **`stories.md`** — the 35-story set supplying every unit's coverage obligation;
  the per-story mapping is in `unit-of-work-story-map.md`.

## Unit summary

The stable short id is `U{n}`; the construction directory is `u{n}-{description}`.
Both appear in the table so downstream tools can join story-map ids to filesystem
paths.

| Unit ID | Directory | Name | Kind | Depends on (Unit IDs) | Complexity |
|---|---|---|---|---|---|
| U1 | `u1-analytics-slice` | Analytics slice — migration, `/v2` surface, read layer | `service` | `U2` (declared import edge — see below) | XL |
| U2 | `u2-term-extraction` | Term extraction and tokenizer promotion | `library` | — (root) | S |
| U3 | `u3-analytics-view` | Analytics view in the existing page | `ui` | U1 | L |
| U4 | `u4-platform-packaging` | Platform obligations | `packaging` | — (root) | M |

**DAG-shape note.** `U2` and `U4` are dependency-free roots; `U3` depends on `U1`,
and `U1` depends on `U2`. The chain `U2 -> U1 -> U3` is the committed ordering, with
`U4` independent of all three (Q6). **`U2` is the unit the `skeleton: on` rule now
resolves first**, because `U1` declares its real dependency on `U2` in the edge
block (recorded 2026-10-04). The ruling and its consequences are stated in full in
`unit-of-work-dependency.md`.

**The `U1 → U2` edge, from this unit's side.** U1's summary slice is independent of
U2 in what it computes, but U1's **full scope** is not: its terms handler and
`AnalyticsRead`'s term ranking import U2's `TermExtraction` module. That is a real
build/import edge (`components.md`: `AnalyticsRead -> TermExtraction`), and as of
2026-10-04 it is recorded as a `depends_on` entry rather than suppressed. Its
consequence is that `U1` is no longer a root and `U2` is the unit the skeleton
ruling resolves first. Stated in full in `unit-of-work-dependency.md` under
**"The U1 → U2 edge"**.

---

## U1 — Analytics slice: additive migration, `/v2` surface, analytics read layer

- **Unit ID:** `U1`
- **Directory:** `u1-analytics-slice`
- **Kind:** `service` — this unit delivers the deployed executable's new read
  surface plus the schema step it runs at startup, so it is the executable-bearing
  unit of the feature.
- **Complexity:** XL
- **Deployment model:** part of the single app (one `uvicorn` process on loopback,
  one SQLite file). No separate deployable.

### Description

The whole integrated analytics slice: the additive v3 → v4 migration and its three
named indexes; the new `v2_router` on the `/v2` prefix carrying the summary and
terms read handlers; the new `AnalyticsRead` module beside `repository` that
computes every aggregate; the R-01 cross-thread connection fix; and the summary
region of the new view, running end to end. This is unit (1) from the human ruling
(Q2) and it is the `skeleton: on` integrated slice (Q5).

### Boundaries

**Owns.** The `Persistence and Schema` change (the migration, the three indexes,
the TD-1 `_rebuild_analyses` fix, the version bump); the `HTTP API Surface` change
(the `v2_router`, both analytics handlers, the one error envelope, and the
`get_connection`/R-01 fix); the `AnalyticsRead` module and its five computed value
shapes; the `Application Assembly` change that mounts `v2_router` and enforces the
loopback bind; and the `Test Harness and Suite` change — the replaced concurrency
harness and the new offline analytics tests.

**Does not own.** The `TermExtraction` module (U2), the full analytics view and its
shell/range/error/loading states (U3), and the repository-level packaging and
tooling artifacts (U4). No analytics logic, SQL or view code is added to
`main.py`; no sentiment logic or SQL is added to `routes.py`.

### Responsibilities (what it owns and delivers)

- Own the additive, idempotent v3 → v4 migration and the three indexes
  (`idx_analyses_created_at`, `idx_analyses_import_id`,
  `idx_analyses_label_created_at`), including the explicit index re-creation in
  `_rebuild_analyses` and the same-transaction version bump.
- Own `AnalyticsRead`: all aggregate SQL, range resolution shared by both
  endpoints, zero-fill, share/mean computation (fractions in `[0,1]`, four
  decimals, `null` on a zero denominator) and term ranking.
- Own the `v2_router` and both `/v2` handlers; route reads straight to
  `AnalyticsRead`, never through the service layer; own the one error envelope,
  including the single new storage-failure machine code.
- Own the R-01 fix: the explicit thread-affinity and lifecycle decision in the
  module that creates and closes the connection, stated in its docstring.
- Own the loopback-bind enforcement at startup.
- Own the replaced ASGI test harness (genuinely concurrent requests, schema
  initialisation hoisted out of the per-request path) and the offline analytics
  tests, including the R-01 concurrency reproduction and the 10,000-row
  performance/statement-count verification.
- Own the summary region of the view that completes the slice end to end.

### Implementation notes and constraints

- The read path calls the query layer directly; the service layer is not inserted
  into it (FR1.1, ADR-008).
- The migration is additive only; it drops, renames and retypes nothing and
  preserves every row; a failed migration fails loudly and rolls back in one
  transaction (FR5.1–FR5.7, Revision 2 corrections to FR5.3).
- Every statement is parameter-bound; no SQL string interpolation (FR1.4).
- The new response shapes are computed value shapes, not persisted entities
  (ADR-005); no analytics table, migration or index is implied by them.
- The terms handler and `AnalyticsRead`'s term ranking consume the `TermExtraction`
  module delivered by U2; that is the one cross-unit integration point this unit
  carries, and it is a **real `U1 → U2` import edge**, declared in the edge block as
  of 2026-10-04. The consequence is that U1's terms work (`US3.1`, `US3.2`) cannot
  be sequenced ahead of U2, because the engine resolves U2 first by topology. See
  `unit-of-work-dependency.md` under **"The U1 → U2 edge"**.
- `/v1`, the `SentimentClient` interface and both adapters' behaviour are
  unchanged (NFR5); the envelope's shape is frozen and gains exactly one code.

---

## U2 — Term extraction and tokenizer promotion

- **Unit ID:** `U2`
- **Directory:** `u2-term-extraction`
- **Kind:** `library` — reusable code with no standalone runtime; the module is
  imported by the engine and by the read layer, and is never executed on its own.
  The `library` kind keeps `entities` and `rules` on the construction design
  matrix, but **both are intentionally empty for U2**: `TermExtraction` owns **no
  entity** (ADR-005; `components.md` Entity Ownership lists it with none — its
  outputs are transient token sequences and significant-term sets of plain strings
  with no identity) and defines **no business rule** of its own beyond the single
  word-splitting/stopword constant captured here. Functional Design is expected to
  emit an explicitly empty `entities.md` and `rules.md` for this unit, with that
  statement, rather than invent a model U2 does not have. See Implementation notes.
- **Complexity:** S
- **Deployment model:** part of the single app; no separate deployable.

### Description

The promoted tokenizer module beside `app/sentiment.py`, exposing exactly two
distinct operations — **tokenize** text into word tokens, and **filter** a token
sequence down to significant terms. It owns the single word-splitting rule (maximal
runs of ASCII lowercase letters and apostrophes), the 3-character minimum, and the
single versioned in-repo English stopword constant. The offline engine is refactored
to call **only** `tokenize`, so its scoring behaviour is unchanged. This is unit
(2) from the human ruling (Q2).

**This unit is the walking skeleton as of 2026-10-04.** `U1`'s real dependency on
this module is now declared in the edge block, which makes `U2` the root the
`skeleton: on` rule resolves first. The honest consequence: the skeleton is now a
fan-out-0 library whose slice is the module plus its parity test, **not** an
end-to-end path through storage and HTTP. That is a reduction in what the skeleton
proves for this scope, accepted in exchange for a build order the engine can
enforce. See `unit-of-work-dependency.md` under **"The U1 → U2 edge"** and
**"Skeleton slice"**.

**Adoption note for this unit's Code Generation.** `app/terms.py` already exists in
the repository: `U1` built it under the previously suppressed ordering, which is the
unit-boundary violation disclosed in `u1-analytics-slice`'s plan and code summary.
`U2` **adopts** that module rather than re-deriving it — the tokeniser, the
3-character minimum and `STOPWORDS` are already present and are now this unit's to
own. `U2` also inherits the stopword-membership decision that contract open point
**O9** left to it; `U1` used a set and asserted one property of it, so a change here
would move both analytics endpoints' output and require editing three `U1` manifest
writes.

### Boundaries

**Owns.** The `TermExtraction` module and its stopword constant; the refactor of
`Offline Dummy Engine` that removes its private `_WORD` regex and calls the
promoted tokenizer.

**Does not own.** Aggregate ranking and the term lists (U1's `AnalyticsRead`), the
`/v2/analytics/terms` handler (U1), and anything in the view (U3).

### Responsibilities (what it owns and delivers)

- Own the single word-splitting rule and the stopword constant
  (case-insensitive, applied after lowercasing).
- Expose `tokenize(text)` and `significant_terms(tokens)` as two structurally
  separate operations, so the analytics filter can never be applied to sentiment
  scoring.
- Own the refactor that deletes the offline engine's private `_WORD` regex and
  routes it through `tokenize`; own the scoring-parity guarantee.
- Own no persistence, no engine scoring and no analytics ranking.
- Carry the module conventions the codebase holds 100 % on: a
  `Single responsibility:` docstring line, full annotations,
  `from __future__ import annotations`, `UPPER_CASE` constants with `#:` comments,
  and underscore-private helpers.

### Implementation notes and constraints

- The module is a fan-out-0 leaf: it imports nothing from `app` (ADR-002).
- The two operations are separate so the 3-character minimum and stopword
  exclusion apply to analytics term extraction and **not** to sentiment scoring
  (FR4.5, AC4.2.3).
- No stemming, lemmatisation, POS tagging, weighting, learned model, downloaded
  corpus or external service (FR4.3).
- Runs containing digits, whitespace or non-ASCII characters are token boundaries;
  a non-Latin term contributes nothing — a recorded accepted limitation (FR4.6).
- No `utils.py`/`helpers.py` junk drawer; a helper lives in the module that owns
  the concept.
- **Empty design artifacts, stated so Construction does not demand a model U2 does
  not have.** The `library` kind keeps `entities` and `rules` on U2's design matrix,
  but this unit owns neither: `TermExtraction` owns **no entity** (ADR-005;
  `components.md` Entity Ownership lists it with none) and holds no business rule
  beyond the word-splitting/stopword behaviour already captured here. Functional
  Design is intended to emit an **explicitly empty** `entities.md` and `rules.md`
  for U2, each stating why, rather than skipping them silently or fabricating a
  schema.
- U2 itself has no dependency and no dependent's ordering is fixed by it beyond the
  declared `U1 → U2` edge stated above and the offline engine's `tokenize` import.

---

## U3 — Analytics view in the existing page

- **Unit ID:** `U3`
- **Directory:** `u3-analytics-view`
- **Kind:** `ui` — a frontend surface; it grows the existing single-page shell and
  carries no server-side business logic.
- **Complexity:** L
- **Deployment model:** part of the single app; served from the existing
  static-asset route. No separate deployable and no second site.

### Description

The analytics view as a **third top-level region inside the existing single-page
shell**: the three-view nav and header, the three readouts (per-day series, label
breakdown with counts and shares, and both term lists at top 10), the labelled
date-range control with an explicit unbounded default and an explicit reset, and the
loading / empty / partial-failure / error states. This is unit (3) from the human
ruling (Q2). The view renders the summary region and the two term lists that the
slice (U1) already reaches over its `/v2` endpoints.

### Boundaries

**Owns.** The `Web UI` change: the shell restructure, the analytics view markup, the
two analytics fetches, the range control, and all view states. **It also owns the
term-list rendering portion of `US6.2`** — the two containers for the ranked term
lists that `AC6.2.1` requires — because those containers live in the full view. U1
owns the other part of `US6.2` (the series and label-breakdown summary region that
completes the slice); see `unit-of-work-story-map.md`.

**Does not own.** The two analytics endpoints and their aggregates (U1), the
`TermExtraction` module (U2), and any packaging artifact (U4). **U3 depends on U1
alone and does not depend on U2**: it fetches ranked term data over U1's
`/v2/analytics/terms` HTTP response and never imports `TermExtraction`.

### Responsibilities (what it owns and delivers)

- Own the third top-level entry and the nav/header shell it lives in.
- Own the analytics view's three sections and their exactly-one-fetch-per-section
  discipline, with an assertion pinning the `/v2` prefix against the router's.
- Own the **two term-list containers** required by `AC6.2.1`, rendering the ranked
  entries U1's `/v2/analytics/terms` response returns (the U3 half of `US6.2`).
- Own the date-range control: labelled, unbounded by default, with an explicit
  'Show all time' reset; **no `import_id` control and no `limit` control** (both
  API-only).
- Own the state model: a distinct loading region, a distinct partial-failure
  region, an inline error region naming the failure, and the discard rule for
  superseded-range responses.
- Own the render discipline: native HTML, existing class names, `textContent`
  everywhere, no chart library, no new front-end dependency.
- Own the analytics markup hooks, added to the existing pinned `data-testid`
  convention in `tests/test_page.py` (`REQUIRED_TEST_IDS`).
- Own the accessibility basics: labelled range control, series exposed as text or
  a table, `role="status"`/`aria-live` on the status region, `aria-current` on the
  active nav entry.

### Implementation notes and constraints

- The restricted range is API-only; the page always presents the unfiltered
  population and can never show a filtered subset it cannot label (FR6.3).
- Changing the range refetches both endpoints with the same bounds so all three
  sections describe one population (FR6.4).
- A `null` share renders as an explicit no-share marker, never as a fabricated
  `0%` (AC6.2.5).
- `app.js` stays a single script inside `Web UI`; no second script file and no new
  Web UI component (ADR-007).
- The analytics path never renders the word "intensity" anywhere in the served
  page.
- No browser automation is introduced; the view's behaviour is pinned by static
  markup assertions plus the standing manual exercise line.

---

## U4 — Platform obligations

- **Unit ID:** `U4`
- **Directory:** `u4-platform-packaging`
- **Kind:** `packaging` — build/distribution artefacts; it delivers repository
  tooling, configuration and documentation rather than a runtime building block.
- **Complexity:** M
- **Deployment model:** part of the single repository and its install/verification
  path; no separate deployable.

### Description

The seven platform obligations affirmed at Practices Discovery and ruled in scope
as one packaging unit (Q3): a dependency lockfile with hashes; a platform-neutral
verification script that runs the standing gates; secret scanning and a dependency
audit; a `LICENSE`; the `ruff TID251` banned-api rule set for the layer boundaries;
the `ruff target-version` matched to `requires-python`; and the README updates.
Domain Design models **no component** for these (ADR-009); this unit is where they
land so no story is homeless.

### Boundaries

**Owns.** The repository-root packaging, tooling, lint-configuration and
documentation artifacts named above.

**Does not own.** Any runtime building block. It adds no component to the running
system and touches no application logic.

### Responsibilities (what it owns and delivers)

- Own the lockfile with hashes and the documented install command that consumes it.
- Own the platform-neutral verification script and the three gates it runs — the
  whole-application 80 % line-coverage floor, the warnings-as-errors filter, and
  the pinned `ruff` rule set.
- Own secret scanning and the dependency audit, invoked from that script, with the
  known fake-key fixtures allowlisted so the first run is signal rather than noise.
- Own the `LICENSE` file and the licence declaration in the installed
  distribution's metadata.
- Own the `ruff TID251` `banned-api` entries that express the layer boundaries, and
  the `target-version` matched to `requires-python`.
- Own the README's `## HTTP surface` table, `## File layout` tree and `## Storage`
  section updates for the new router, modules and indexes.

### Implementation notes and constraints

- The verification script is neither a pre-commit hook nor a provider CI job —
  there is no remote and no CI provider (FR7.2).
- The fake-key fixture count is stated nowhere until it is reconciled
  (FR7.3, Revision 2); the scanner's allowlist must be written against the actual
  literals.
- The lockfile format, the scanner/audit tool choice and the specific licence are
  open questions carried from Requirements; they are resolved inside this unit.
- `TID251` is an import rule: it enforces which modules may be imported, not that a
  write never executes (AC8.3.2). The read-only guarantee is proved behaviourally
  in U1.
- The README describes the surface delivered by U1 and U3; that content dependency
  is a story-level fact carried in the story map, not a unit-level DAG edge — the
  human ruled the platform unit independent (Q6).

---

## Cross-unit boundaries at a glance

| Concern | Owning unit | Consuming unit(s) |
|---|---|---|
| v3 → v4 migration, three indexes | U1 | — |
| `AnalyticsRead` aggregate SQL, summary & terms computation | U1 | U3 (renders it over HTTP) |
| `/v2` router and both handlers, error envelope | U1 | U3 (fetches it) |
| R-01 connection fix, thread affinity | U1 | — |
| `TermExtraction` tokenize + significant terms | U2 | U1 (terms endpoint — **declared `U1 → U2` edge**); U3 consumes the ranked result only over U1's HTTP response, not by import |
| Analytics view, shell, range/loading/error states, term-list containers (`US6.2` U3 half) | U3 | — |
| Lockfile, verification script, scanners, LICENSE, ruff config, README | U4 | — |

**The `US6.2` split.** `US6.2` ("the three readouts") spans two units: U1 delivers
the series and label-breakdown summary region that completes the slice, and U3
delivers the two term-list containers. Its declared target remains U1 (the slice is
the primary deliverable); the full cross-cutting record is in
`unit-of-work-story-map.md`.

**No component is left homeless.** Every component the Domain Design catalogue
touches is owned by exactly one unit above, and the seven platform obligations that
Domain Design correctly modelled as no component are owned by U4.
