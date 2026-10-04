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
| U1 | `u1-analytics-slice` | `service` | `u2-term-extraction` |
| U2 | `u2-term-extraction` | `library` | — (root) |
| U3 | `u3-analytics-view` | `ui` | `u1-analytics-slice` |
| U4 | `u4-platform-packaging` | `packaging` | — (root) |

> **The `u1-analytics-slice -> u2-term-extraction` edge is now recorded, not
> suppressed.** It was previously held out of this column and out of the edge
> block to keep `u1-analytics-slice` a root, so that the `skeleton: on` ruling
> could make it the first unit the engine builds. That suppression is what put
> `u1-analytics-slice` ahead of `u2-term-extraction` at runtime, and `u1` then
> authored `app/terms.py` — a module this document assigns to `u2` — because the
> engine walked it first and its approved plan told it to build the terms path.
> The `review-and-correction` note under **"The U1 → U2 edge"** states the
> correction in full. **The consequence, stated plainly: `u2-term-extraction` is
> now the root the skeleton ruling has to name, and the walking skeleton is that
> module rather than `u1`'s summary slice.**

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
    depends_on: [u2-term-extraction]
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

**What this block encodes.** It records the **complete** topology, including the
`u1-analytics-slice -> u2-term-extraction` import edge that was previously
suppressed. The block is the authoritative input to the downstream batch fan-out
and the construction-unit resolution, so recording the edge here is what makes
the engine build `u2-term-extraction` before `u1-analytics-slice`. See
**"The U1 → U2 edge"** for why it is recorded rather than suppressed.

## Prose DAG

```
                        (root)
                  u2-term-extraction
                         ^
                         |  (declared import edge u1 -> u2)
                         |
                  u1-analytics-slice ──────────┐
                         ^                     |
                         |                     v
                         |              u3-analytics-view
                         |
              u4-platform-packaging  (root, independent)
```

Text fallback (adjacency form; `X -> [Y]` reads "X depends on Y"):

```
u1-analytics-slice    -> [u2-term-extraction]
u2-term-extraction    -> []
u3-analytics-view     -> [u1-analytics-slice]
u4-platform-packaging -> []
```

The `u1 -> u2` edge is now a **declared** edge: it is part of the machine-readable
block above. It does **not** reach `u3-analytics-view`, whose committed edge is
`u1-analytics-slice` alone.

**Acyclic.** Two roots (`u2-term-extraction`, `u4-platform-packaging`) and one
chain `u2 -> u1 -> u3`. No cycle exists; no existing component boundary moves.

## The U1 → U2 edge — a real dependency, recorded rather than suppressed

**The real dependency.** `u1-analytics-slice` owns the `/v2/analytics/terms` handler
and the `AnalyticsRead` module it calls. Both reach `u2-term-extraction`:
`components.md` declares `AnalyticsRead -> TermExtraction` ("extracts significant
terms from the text of rows in range") and `HTTP API Surface -> AnalyticsRead`, and
the `Integration points` table below states the same. This is a genuine **build and
import** dependency: U1's terms capability cannot be built or integrated until U2's
`TermExtraction` module exists and exports `tokenize`/`significant_terms`. It is not
an HTTP call and not optional for U1's **full** scope.

**Why it was previously not an edge in the block, and why that changed.** This
scope declares `skeleton: on`, and the human ruling (Q5) fixes `u1-analytics-slice`
as the **integrated slice** — the first resolved unit, which must run end to end
before any later unit exists. Adding `depends_on: [u2-term-extraction]` to
`u1-analytics-slice` places U2 in an earlier topological batch and makes U1
non-root, changing which unit the runtime resolves as the skeleton. That was the
reason for suppressing the edge.

**The suppression was removed, and this note records why.** It preserved the
skeleton's dependence-free property at the cost of the ordering it was meant to
protect. At runtime the engine resolves the first *unsettled* unit from the edge
block, and with `u1-analytics-slice` recorded as a root it walked `u1` first. `u1`'s
approved plan then told it to build the terms path, so `u1` authored
`app/terms.py` — a module this document assigns to `u2-term-extraction` — and the
resulting `u1 -> u2` import edge existed anyway. The suppression did not prevent
the dependency; it prevented the *ordering* while allowing the *violation*.

**What reconciles it now.** The dependency is real for U1's **terms** capability;
the **summary slice** the skeleton ruling protects is genuinely independent of U2
(the summary computation buckets and averages stored rows and never extracts
terms). With the edge recorded, `u2-term-extraction` becomes **the root the
skeleton ruling has to name**, and the walking skeleton is that module — a
fan-out-0 library with two operations and a parity test — rather than `u1`'s
summary slice. **This is a deliberate change to which unit is the skeleton, made
by human ruling on 2026-10-04**, in exchange for an ordering the engine can
actually enforce. `u1`'s summary path remains the first thing that runs end to
end once `u2` exists.

**The obligation is now structural, not procedural.** The previous version of this
document placed the sequencing constraint on Delivery Planning, which cannot bind
the engine — the stage definition states that the engine does not consume
`bolt-plan.md` for walk order. The constraint is therefore enforced by the edge
block instead:

- There is no longer an `understates U1's full scope` gap: `u1-analytics-slice`
  now declares its real dependency.
- Delivery Planning still must not sequence U1's terms work (`US3.1`, `US3.2`, and
  the term-list part of `US6.2`) ahead of U2 — but it no longer *can*, because the
  engine resolves U2 first by topology.

**Why not instead drop the terms handler from U1?** That is the other honest option
the review offered, and it was rejected here because the human ruling (Q2) places
the `/v2` HTTP surface — both handlers — in U1, and the story map assigns `US3.1`,
`US3.2` to U1. Moving the terms handler out would re-open the human's unit
decomposition. Recording the edge preserves the human ruling on *who owns the
handler* while enforcing the ordering the review requires.

**Topological batches** (computed from the block above by level, each level sorted):

```
batch 1: [u2-term-extraction, u4-platform-packaging]
batch 2: [u1-analytics-slice]
batch 3: [u3-analytics-view]
```

The batch listing is a **constraint**, not a plan: it says `u1-analytics-slice`
cannot be resolved before `u2-term-extraction`, and `u3-analytics-view` cannot be
resolved before `u1-analytics-slice`. It does **not** say which root to work first
among `batch 1`. Because `u1-analytics-slice` now declares its real dependency, the
ordering that Delivery Planning previously had to enforce by hand is enforced by
the topology instead.

## Integration points

| From | To | What crosses the boundary | Failure behaviour |
|---|---|---|---|
| U1 (`v2_router` terms handler / `AnalyticsRead`) | U2 (`TermExtraction` module) | **The declared `u1-analytics-slice -> u2-term-extraction` build/import edge** (see above). U1's terms path imports U2's `significant_terms` operation on the text of rows in range; the handler receives ranked entries back. | A storage failure on the read answers 500 through U1's envelope; a malformed parameter is refused 422 before any computation. U2 holds no connection and raises no HTTP failure of its own. The edge is declared, so the engine resolves U2 before U1 and the ordering cannot be inverted. |
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
  U1's dependency on U2 is the declared edge stated above. The edge set is no
  longer inverted relative to the imports the components imply.
- **Net effect.** The committed edge is `u3-analytics-view -> u1-analytics-slice`.
  This is *stronger* than the edge it replaces (U1 is now genuinely ordered before
  U3) and it matches U3's actual stories.

**The U1 ↔ U2 integration point is real and is declared.** It is stated in full
above under **"The U1 → U2 edge"**, with the skeleton rationale and the ordering
consequence. The edge block now records `u1-analytics-slice`'s dependency on
`u2-term-extraction`, so `u1-analytics-slice` is no longer a root and the engine
resolves `u2-term-extraction` first.

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
  one real integration point (the terms path) that is declared in the edge block
  — so this concurrency is safe for U1's **summary path**, and U1's **terms path**
  still completes only once U2 exists (see **"The U1 → U2 edge"**).
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
chooses among them**, subject to the declared-edge ordering above: it cannot
place U1's terms work before U2.

## Skeleton slice — identification and how it runs first

This scope declares `skeleton: on` (`.aidlc/scopes/aidlc-feature.md`), and the
runtime resolves the first unit of the first sorted batch as the skeleton. Because
the edge block records `u1-analytics-slice`'s dependency on `u2-term-extraction`,
`batch 1` is now `[u2-term-extraction, u4-platform-packaging]` and it sorts as
`u2-term-extraction`.

> **The skeleton unit is `u2-term-extraction` (U2).** This changed on 2026-10-04 by
> human ruling, when the `U1 → U2` edge was recorded in place of the suppression
> that had held `u1-analytics-slice` as a root. The previous version of this section
> named `u1-analytics-slice` as the skeleton — which is unit (1) from the human's
> Q2 decomposition ruling and the integrated slice the human ruled in Q5 — and that
> ruling was **not** withdrawn. What changed is the mechanism: with the edge
> declared, the engine cannot resolve U1 before U2, so the root it names as the
> skeleton is `u2-term-extraction`.

**What the skeleton now proves, and its honest limits.** `u2-term-extraction` is a
fan-out-0 library that imports nothing from `app`. Its slice is narrower than the
previous skeleton's: the module exists, exports exactly two operations —
`tokenize(text)` and `significant_terms(tokens)` — and the parity test shows the
offline engine's scoring is byte-identical before and after the private `_WORD`
regex is deleted. **It does not run an end-to-end path through storage and HTTP.**
That is a real reduction in what "walking skeleton" buys for this scope, and it is
the price of an ordering the engine can enforce. The integrated end-to-end path
through schema, route, read and render is `u1-analytics-slice`, which runs
immediately after and is unchanged in content.

**Why U1's summary slice still runs before later units.** U1's summary path reaches
none of the other three units:

- It **does** need U2 in the edge block now, but only for the terms capability.
  The summary computation is bucketing and averaging over stored rows; it never
  extracts terms. Recording the edge costs U1 its root status; it does not change
  what the summary path itself requires.
- It does **not** need U3. The slice renders the **summary region**; the full view
  — nav, range control, term sections, loading/partial states — is U3. The slice's
  render is enough to prove the client/server seam.
- It does **not** need U4. The lockfile, verification script, scanners, LICENSE,
  lint rules, `target-version` and README are repository artifacts that no runtime
  path imports.

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

- It **does** need U2 in the edge block now, but only for the terms capability.
  The summary computation is bucketing and averaging over stored rows; it never
  extracts terms. Recording the edge costs U1 its root status; it does not change
  what the summary path itself requires.
- It does **not** need U3. The slice renders the **summary region**; the full view
  — nav, range control, term sections, loading/partial states — is U3. The slice's
  render is enough to prove the client/server seam.
- It does **not** need U4. The lockfile, verification script, scanners, LICENSE,
  lint rules, `target-version` and README are repository artifacts that no runtime
  path imports.

**The human's Q5 ruling is preserved in substance.** It fixed the summary slice as
the thing that must run end to end before later units, and that is still what runs
first in the chain: `u2-term-extraction` resolves first as a matter of topology, and
`u1-analytics-slice`'s summary path is the first *integrated* path to run. What the
ruling no longer governs is which unit the engine calls the skeleton.

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
- **The real `U1 → U2` import edge is declared in the edge block** (recorded
  2026-10-04, replacing an earlier suppression). `u1-analytics-slice` is therefore
  **not** a root and **not** the unit the runtime calls the skeleton; the ordering
  is enforced by topology rather than by a Delivery Planning obligation that could
  not bind the engine. See **"The U1 → U2 edge"** above.
- `u3-analytics-view` depends on `u1-analytics-slice` alone; the earlier
  `u3 -> u2` edge was wrong and is removed (U3 fetches, never imports).
