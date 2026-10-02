# Unit Dependency DAG — sentiment-opencode v2 analytics layer

> **Topology only.** This document describes what can depend on what. It does
> **not** recommend an implementation order and does **not** identify a critical
> path. Delivery Planning (Stage 2.9) chooses the economic path through this DAG.
>
> Edges read **"A depends on B"** — A needs B built or integrated before A is
> complete. With one deployable (Q1), these are **build and integration**
> dependencies, not network boundaries. There is no service call anywhere in this
> DAG: the four units ship as one application.

## Unit set

| Unit | Directory | Kind | Direct DAG dependencies |
|---|---|---|---|
| U1 | `u1-analytics-slice` | `service` | — (root) |
| U2 | `u2-term-extraction` | `library` | — (root) |
| U3 | `u3-analytics-view` | `ui` | `u1-analytics-slice` |
| U4 | `u4-platform-packaging` | `packaging` | — (root) |

> **Read the "Direct DAG dependencies" column with the suppressed-edge note
> below.** It lists the dependencies the edge block *records*, not every real
> build dependency U1's full scope carries. `U1` additionally holds a real
> `u1-analytics-slice -> u2-term-extraction` import edge that the `skeleton: on`
> ruling suppresses from this column and from the edge block. That suppression is
> stated in full under **"The suppressed U1 → U2 edge"** — it is not silent.

## The machine-readable edge block

The fenced `yaml` block below is the authoritative mirror of the prose DAG. The
downstream batch fan-out and the construction-unit resolution are computed from
**this block**, not from the prose. It is well-formed and cycle-free: every unit is
named exactly once, every dependency is a declared unit, there is no self-edge, and
each `kind` is one of `service | spec | ui | packaging | library`.

```yaml
units:
  - name: u1-analytics-slice
    kind: service
    depends_on: []
  - name: u2-term-extraction
    kind: library
    depends_on: []
  - name: u3-analytics-view
    kind: ui
    depends_on: [u1-analytics-slice]
  - name: u4-platform-packaging
    kind: packaging
    depends_on: []
```

**What this block does and does not encode.** The block encodes the *skeleton-safe*
topology: the dependencies that must hold for the ordered units. It does **not**
encode the `u1-analytics-slice -> u2-term-extraction` import edge, because that
edge would demote `u1-analytics-slice` from root and change which unit the
`skeleton: on` rule resolves first. The block therefore records a **deliberately
constrained view** of a real dependency; see **"The suppressed U1 → U2 edge"** for
the statement, the reason, and the obligation this places on Delivery Planning.

## Prose DAG

```
        (root)              (root)                        (root)
  u1-analytics-slice    u2-term-extraction          u4-platform-packaging
          |    :
          |    :  (real import edge u1 -> u2, suppressed by the
          |    :   skeleton ruling — see below; NOT a DAG edge)
          |    v
          |  (not drawn into u3)
          |
          v
   u3-analytics-view
```

Text fallback (adjacency form; `X -> [Y]` reads "X depends on Y"):

```
u1-analytics-slice    -> []                       # + suppressed: -> [u2-term-extraction]
u2-term-extraction    -> []
u3-analytics-view     -> [u1-analytics-slice]
u4-platform-packaging -> []
```

The dotted `u1 --> u2` edge is drawn to make the suppressed dependency visible; it is
**not** part of the machine-readable block and must not be read as one, and it does
**not** reach `u3-analytics-view`. The committed DAG edge into `u3-analytics-view` is
`u1-analytics-slice` alone.

**Acyclic.** Three roots (`u1-analytics-slice`, `u2-term-extraction`,
`u4-platform-packaging`) and one leaf-ward edge into `u3-analytics-view`. No
cycle exists; no existing component boundary moves.

## The suppressed U1 → U2 edge — a real dependency, represented in a constrained way

**The real dependency.** `u1-analytics-slice` owns the `/v2/analytics/terms` handler
and the `AnalyticsRead` module it calls. Both reach `u2-term-extraction`:
`components.md` declares `AnalyticsRead -> TermExtraction` ("extracts significant
terms from the text of rows in range") and `HTTP API Surface -> AnalyticsRead`, and
the `Integration points` table below states the same. This is a genuine **build and
import** dependency: U1's terms capability cannot be built or integrated until U2's
`TermExtraction` module exists and exports `tokenize`/`significant_terms`. It is not
an HTTP call and not optional for U1's **full** scope.

**Why it is not an edge in the block.** This scope declares `skeleton: on`, and the
human ruling (Q5) fixes `u1-analytics-slice` as the **integrated slice** — the first
resolved unit, which must run end to end before any later unit exists. Adding
`depends_on: [u2-term-extraction]` to `u1-analytics-slice` would place U2 in an
earlier topological batch and make U1 non-root, changing which unit the runtime
resolves as the skeleton. The skeleton's dependence-free property is therefore
**deliberately preserved by constraining** how the real edge is represented: it is
recorded in prose, in the integration-point table, and in the U1 unit record
(`unit-of-work.md`), not as a machine-readable `depends_on` entry.

**What reconciles the contradiction.** The dependency is real only for U1's
**terms** capability; the **summary slice** that the skeleton ruling protects is
genuinely independent of U2 (the summary computation buckets and averages stored
rows and never extracts terms — see **"Skeleton slice"** below). The skeleton is
satisfied by the summary path, and the suppressed edge is a constraint on the rest
of U1's scope.

**The obligation this places on Delivery Planning.** This is stated plainly so the
constraint cannot be mistaken for independence:

- The edge block's `u1-analytics-slice: depends_on: []` **understates U1's full
  scope**. It is true for the summary slice, not for U1's terms work.
- Delivery Planning **must not sequence U1's terms work (`US3.1`, `US3.2`, and the
  term-list part of `US6.2`) ahead of U2**. Doing so would violate the real import
  edge even though the edge block permits it topologically.
- The safe reading: `u2-term-extraction` may proceed in parallel with U1, but U1's
  terms path is **complete only once U2 exists**. U1's summary path is complete
  without U2.

**Why not instead drop the terms handler from U1?** That is the other honest option
the review offered, and it was rejected here because the human ruling (Q2) places
the `/v2` HTTP surface — both handlers — in U1, and the story map assigns `US3.1`,
`US3.2` to U1. Moving the terms handler out would re-open the human's unit
decomposition. The suppressed-edge representation preserves the human ruling while
stating the constraint the review requires.

**Topological batches** (computed from the block above by level, each level sorted):

```
batch 1: [u1-analytics-slice, u2-term-extraction, u4-platform-packaging]
batch 2: [u3-analytics-view]
```

The batch listing is a **constraint**, not a plan: it says `u3-analytics-view` cannot
be resolved before `u1-analytics-slice`, and that the three roots have no recorded
dependency between them. It does **not** say which root to work first. Note that
`batch 1`'s independence of `u1` and `u2` is the *recorded* topology; it is qualified
by the suppressed `u1 -> u2` edge stated above.

## Integration points

| From | To | What crosses the boundary | Failure behaviour |
|---|---|---|---|
| U1 (`v2_router` terms handler / `AnalyticsRead`) | U2 (`TermExtraction` module) | **A real build/import edge, suppressed from the DAG edge block** (see above). U1's terms path imports U2's `significant_terms` operation on the text of rows in range; the handler receives ranked entries back. | A storage failure on the read answers 500 through U1's envelope; a malformed parameter is refused 422 before any computation. U2 holds no connection and raises no HTTP failure of its own. Because the edge is suppressed, Delivery Planning must not sequence U1's terms work ahead of U2. |
| U1 (offline engine refactor) | U2 (`tokenize`) | The offline engine calls **tokenize only**; the analytics filter is never applied to scoring. | A change to the filter cannot reach scoring because the operations are separate; a parity test pins the engine's behaviour. |
| U3 (view script) | U1 (`/v2` endpoints) | **The committed `u3-analytics-view -> u1-analytics-slice` DAG edge.** Two HTTP fetches (summary and terms) with the same resolved bounds; responses carry the computed shapes, including the ranked term lists U1 computes. | A failed fetch renders an inline error naming the failure; a late superseded response is discarded; a partial success renders the succeeded section plus a partial-failure notice. |
| U4 (README + verification script) | U1, U3 | The README describes the `/v2` surface and the new modules; the verification script runs the gates over the delivered code. | **Story-level content dependency, not a DAG edge** — see the note below. |

**Correcting the earlier `u3 -> u2` edge.** An earlier revision of this document
gave `u3-analytics-view` a dependency on `u2-term-extraction` justified by "the term
lists". That edge was **wrong** and is removed. The reasoning, from the component
import graph and the assigned stories:

- **What U3 imports.** U3 is the `Web UI` change. `components.md` gives `Web UI ->
  HTTP API Surface` and nothing else: the view fetches `/v1` and the two `/v2`
  endpoints over HTTP. It never imports `TermExtraction`, and none of its stories
  (`US6.1`, `US6.3`, `US6.4`, `US6.5`) reference U2's module. So there is **no U3 ->
  U2 edge**.
- **Where the term lists actually come from.** `US6.2`'s term-list rendering is
  delivered by U3, but the **ranked term data** it renders is computed by U1's
  `AnalyticsRead` (which is what imports U2) and crosses to U3 **over U1's
  `/v2/analytics/terms` HTTP response**. U3's dependency is therefore on U1, and
  U1's dependency on U2 is the suppressed edge stated above. The edge set is no
  longer inverted relative to the imports the components imply.
- **Net effect.** The committed edge is `u3-analytics-view -> u1-analytics-slice`.
  This is *stronger* than the edge it replaces (U1 is now genuinely ordered before
  U3) and it matches U3's actual stories.

**The U1 ↔ U2 integration point is real and is suppressed, deliberately.** It is
stated in full above under **"The suppressed U1 → U2 edge"**, with the skeleton
rationale and the Delivery Planning obligation. The edge block keeps
`u1-analytics-slice` a root — which also lets it start in parallel with
`u2-term-extraction` **for its summary path** (Q6).

**The U4 content dependency is recorded as a fact, not an edge.** The README
stories (`US7.9`) name `US2.1`, `US3.1` and `US6.1` as story-level dependencies,
because the contract-of-record table must describe the delivered surface. At unit
granularity the human ruled the platform unit **independent of everything** (Q6),
so `u4-platform-packaging` carries `depends_on: []`. The content dependency is
carried in the story map and in the unit's implementation notes rather than as a
DAG edge, so U4 can start at any point in the plan Delivery Planning chooses.

## Parallel-development opportunities

Multiple valid topological orderings exist. The genuinely independent sets — units
with **no dependency between them** — are:

- **Set A — `{u1-analytics-slice, u2-term-extraction, u4-platform-packaging}`.**
  All three are recorded roots. None depends on another **in the edge block**. They
  can be started concurrently. `u1-analytics-slice` and `u2-term-extraction` share
  one real integration point (the terms path) that is suppressed from the edge block
  — so this concurrency is safe for U1's **summary path**, and U1's **terms path**
  still completes only once U2 exists (see **"The suppressed U1 → U2 edge"**).
- **Set B — `{u4-platform-packaging}` against everything.**
  Stated separately because it is the strongest independence: the packaging unit
  depends on no unit and no unit depends on it. It can be worked at any time
  relative to Set A and U3.
- **`u3-analytics-view` is the only ordered unit.** It depends on
  `u1-analytics-slice` — the unit whose endpoints it fetches and whose `/v2` term
  responses carry the ranked term lists it renders. It does **not** depend on
  `u2-term-extraction`: it never imports U2, and the term data reaches it over U1's
  HTTP surface. It cannot be resolved before `u1-analytics-slice`. It is not part of
  any independent set with U1.

No single topological order is forced. The DAG admits at least these orderings:
`u1 → u2 → u3 → u4`, `u2 → u4 → u1 → u3`, `u4 → u2 → u1 → u3`, and any interleaving
that places `u3-analytics-view` after `u1-analytics-slice`. **Delivery Planning
chooses among them**, subject to the suppressed-edge obligation above: it must not
place U1's terms work before U2.

## Skeleton slice — identification and how it runs first

This scope declares `skeleton: on` (`.aidlc/scopes/aidlc-feature.md`), and the
runtime resolves the first unit of the first sorted batch as the skeleton. Because
`batch 1` sorts as `[u1-analytics-slice, u2-term-extraction, u4-platform-packaging]`,
**the skeleton unit is `u1-analytics-slice` (U1)** — which is also unit (1) from the
human's decomposition ruling (Q2) and the integrated slice the human ruled (Q5).

**`u1-analytics-slice` is the integrated slice, not a bare layer or a design
document.** It runs the whole analytics path for the summary endpoint end to end,
before any later unit exists:

1. **Schema** — `db.init_db` performs the additive v3 → v4 migration and creates the
   three named indexes on startup.
2. **Route** — `main.create_app` mounts `v2_router`; the `/v2/analytics/summary`
   handler exists and answers.
3. **Read** — `AnalyticsRead` resolves the range and computes `total`, `counts`,
   `shares`, both mean fields and the per-day series from stored rows.
4. **Render** — the summary region of the page consumes that response, so the
   slice's integration path is exercised from stored row to served view.

**How it can run before later units.** U1's summary path reaches none of the other
three units:

- It does **not** need U2 **for the summary slice**. The summary computation is
  bucketing and averaging over stored rows; it never extracts terms.
  `TermExtraction` first enters on the `/v2/analytics/terms` path, which is part of
  U1's surface but **not** part of the summary slice. U1 is therefore complete as a
  running slice with U2 absent — **but U1's full scope is not**: the terms handler
  and `AnalyticsRead`'s term ranking import U2's module, which is the real
  `u1 -> u2` edge suppressed from the edge block and stated in full above. The
  skeleton's independence is a property of the summary slice, not of U1's whole
  scope.
- It does **not** need U3. The slice renders the **summary region**; the full view
  — nav, range control, term sections, loading/partial states — is U3. The slice's
  render is enough to prove the client/server seam.
- It does **not** need U4. The lockfile, verification script, scanners, LICENSE,
  lint rules, `target-version` and README are repository artifacts that no runtime
  path imports.

This is exactly why U1 is declared a root: the human's ruling makes the **summary
slice** dependency-free. The one capability within U1 that does reach another unit —
the terms endpoint and `AnalyticsRead`'s ranking reaching U2 — is **not** part of
the slice. It is a real dependency represented in a constrained way, named above as
the suppressed `U1 → U2` edge, and it does not change which unit the skeleton
resolves.

**What the slice proves at its end.** A populated store answers `GET
/v2/analytics/summary` over a real range, the per-day series and label mix render in
the page, and the same response is asserted by an offline test reading real SQLite
and real served markup. The concurrency harness U1 owns lets the R-01 fix be proved
against genuinely overlapping requests at the same time.

**What it deliberately does not prove.** Term extraction, the term lists and the
full view states are later units. The slice is the smallest slice that runs the
whole way through, not an isolated design or a single layer.

## Constraints carried by this DAG

- One deployable (Q1): no unit is a network boundary; the DAG is build/integration
  topology only.
- Four units (Q2), each with the `kind` that fits (Q4).
- One `packaging` unit owns all seven platform obligations (Q3); nothing is
  homeless.
- The R-01 fix lands in the unit that owns the connection semantics — U1 (Q7,
  ADR-006).
- Independent sets are stated so Delivery Planning can choose; no single order is
  forced (Q6).
- **A real `U1 → U2` import edge is suppressed from the edge block** so U1 stays the
  skeleton slice; it is stated in prose and, with its Delivery Planning obligation,
  under **"The suppressed U1 → U2 edge"** above. Delivery Planning must not sequence
  U1's terms work ahead of U2.
- `u3-analytics-view` depends on `u1-analytics-slice` alone; the earlier
  `u3 -> u2` edge was wrong and is removed (U3 fetches, never imports).
