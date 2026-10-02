# Units Generation — Decomposition Questions

> **This stage produces topology only.** It describes what can depend on what. It
> does **not** recommend an implementation order and does **not** identify a
> critical path — those are Delivery Planning's economic decisions. Where a
> question below touches ordering, it is asking about a *constraint*, not a plan.
>
> Prior context: `components.md` gives 12 components (10 existing, 2 new); the
> 35-story set gives the coverage obligation; `units-generation` must produce a
> DAG whose **first resolved unit is the smallest working integrated slice**,
> because this scope declares `skeleton: on`.

## Q1 — What is the deployment model?

`C-` records no container, no hosted service, one `uvicorn` process on loopback,
one SQLite file. The only deployable artifact is the whole app.

A. **One deployable.** Every unit is part of the single app; "unit" means a
   work-boundary, not a separately deployable service. The DAG captures build and
   integration dependencies, not network boundaries
B. Split into a backend unit and a UI unit with an HTTP boundary between them —
   two deployables
C. Other (please specify)

[Answer]: A. One deployable. Every unit is part of the single app; "unit" means a work-boundary, not a separately deployable service. The DAG captures build and integration dependencies, not network boundaries.

## Q2 — How many units, and on what boundaries?

Ten components exist and two are new. The feature touches many of them.

A. **Four units** — (1) the additive migration plus the `/v2` HTTP surface and the
   analytics read layer, (2) term extraction plus the tokenizer promotion, (3) the
   analytics view in the existing page, (4) the platform obligations as one
   packaging unit
B. **Three units** — merge (2) into (1), since the tokenizer is a leaf that only
   the terms endpoint and the engine consume
C. **Five units** — split (1) into the migration/schema unit and the analytics-read
   plus HTTP unit, because the migration is the one genuinely risky piece and the
   team's risk-first preference would want it separable
D. Other (please specify)

[Answer]: A. Four units — (1) the additive migration plus the `/v2` HTTP surface plus the analytics read layer, (2) term extraction plus the tokenizer promotion, (3) the analytics view in the existing page, (4) the platform obligations as one packaging unit.

## Q3 — Where do the seven unowned platform stories live?

Domain Design marked `US7.1`–`US7.5`, `US7.8` and `US7.9` (lockfile, verification
script, secret scanning, dependency audit, `LICENSE`, `ruff TID251`,
`target-version`, README) as `N/A` — no component — because they are repository
tooling rather than building blocks. They still need an owning unit.

A. **One `packaging` unit** that owns all seven, so no story is homeless and the
   component catalogue stays free of a fake component
B. Spread them across the units that touch each concern — the lockfile with the
   migration unit, the lint rules with whichever unit the boundaries belong to
C. Leave them unassigned with a named destination and let Delivery Planning place
   them
D. Other (please specify)

[Answer]: A. One `packaging` unit owns all seven platform obligations, so no story is homeless and the component catalogue stays free of a fake component.

## Q4 — What kind is each unit?

`kind` drives which construction design-artifact matrix a unit carries
(`service` / `spec` / `ui` / `packaging` / `library`).

A. Tag each unit with the kind that fits: the analytics backend as `service`, the
   migration as `spec` if it is separable, the view as `ui`, the platform
   obligations as `packaging`
B. Tag everything `service`, treating the whole app as one deployed executable
C. Omit `kind` entirely, so every unit receives the full design-artifact matrix
D. Other (please specify)

[Answer]: A. Tag each unit with the kind that fits — `service`, `spec`, `ui` or `packaging`.

## Q5 — What is the first resolved unit, as the skeleton?

This scope declares `skeleton: on`, so the first unit in DAG order must be the
smallest **working integrated slice** — enough real implementation to exercise its
integration path end to end, not an isolated design document or a bare layer.
The team already ruled the slice is one analytics endpoint end-to-end: route,
aggregate SQL, page render.

A. **One unit that is the whole slice** — the additive migration, the summary
   endpoint and route, and the summary region of the view, running end to end
   before anything else exists
B. Two units, where the first is the migration plus the endpoint and the slice is
   only completed by the second — accept that the first unit alone renders nothing
C. Other (please specify)

[Answer]: A. One unit that **is** the whole integrated slice: the additive migration, the summary endpoint and its route, and the summary region of the view, running end to end before anything else exists.

## Q6 — Do any units run in parallel?

The stage wants the DAG to expose sets of units with no dependency between them.

A. State the genuinely independent sets and let Delivery Planning choose; term
   extraction and the view's shell are plausible independents, the platform
   unit is independent of everything
B. Force a chain so there is exactly one topological order and no choice to make
C. Other (please specify)

[Answer]: A. State the genuinely independent sets and let Delivery Planning choose the economic path.

## Q7 — Where does the R-01 fix land?

The fix is owned by the HTTP API Surface component and is needed before a
concurrency test can pass.

A. Inside the unit that owns the semantics of the failure — the migration and
   service unit, so the connection decision sits with the code that owns the
   connection
B. Inside whichever unit the skeleton lands in, so the fix is proven by the first
   integrated run
C. Its own unit
D. Other (please specify)

[Answer]: A. The R-01 fix lands in the unit that owns the connection semantics, so the connection decision sits with the code that owns the connection.

## Consolidated Summary Confirmation

- **One deployable.** Every unit is part of the single app; "unit" means a work-boundary. The DAG captures build and integration dependencies, not network boundaries.
- **Four units**: `U1 u1-analytics-slice` (`service`), `U2 u2-term-extraction` (`library`), `U3 u3-analytics-view` (`ui`), `U4 u4-platform-packaging` (`packaging`).
- **One packaging unit owns all seven platform stories** — the lockfile, verification script, secret scanning, dependency audit, `LICENSE`, `ruff TID251`, `target-version` and the README.
- **The final edges are `U3 → U1` only.** `U1`, `U2` and `U4` are dependency-free roots, so several valid topological orders exist and Delivery Planning chooses among them.
- **The view's dependency was corrected from `U2` to `U1`.** The review found it inverted: it was justified by "the term lists", which `U1` delivers, not `U2`. `U3` fetches `U1`'s endpoints and never imports `TermExtraction`.
- **A real `U1 → U2` dependency exists and is recorded as suppressed**, not omitted. `U1`'s terms handler imports `U2`'s module, but adding the edge would demote `U1` from a root and break the skeleton ruling. The dependency artifact states the real edge, why it is constrained, and the binding note that Delivery Planning must not sequence `U1`'s terms work ahead of `U2`.
- **`U1` remains the integrated slice** — the migration, the summary endpoint, its route and the summary region of the view, running end to end and reaching none of `U2`, `U3` or `U4`.
- **`US6.2` is recorded as a split deliverable**: `U1` owns the series and label-breakdown region, `U3` owns the two term-list containers its `AC6.2.1` requires. The story map carries a cross-cutting row naming both units.
- **`U2`'s empty design artifacts are intended.** `TermExtraction` owns no entity and no rule, so Functional Design should emit explicitly empty `entities.md` and `rules.md` with the reason rather than skipping them or fabricating a schema.
- **All 35 stories plus the merged `US5.2` are assigned, with no GAPs.**
- **This stage still states topology only.** No implementation order, no critical path, no ranking.

- `Looks correct`
- `Request changes`

[Answer]: Looks correct
