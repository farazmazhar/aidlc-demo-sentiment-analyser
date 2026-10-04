# External Dependency Map — sentiment-opencode v2 analytics layer

> **Intent:** `261001-analytics-layer` · stage `delivery-planning` (inception).
>
> This artifact maps **gated items** — things outside the team that hold a
> **Bolt** (one build pass over a piece of the work, ending in something that
> runs) — to the Bolt they would block. A gated item is normally an external API,
> a data-availability window, an approval lead time, or another team's hand-off.

## Verdict: empty

**There is no external dependency in this intent.** Concretely, there is:

- **No external API.** The analytics layer computes everything in-process from
  local SQLite rows. The intent's constraint `C-5` forbids introducing a new
  external service, hosted dependency, cloud component or network call for any
  capability; this holds across the whole feature.
- **No data window.** The analytics reads rows already stored by the existing
  app; there is no upstream feed, batch window or refresh schedule to wait on.
- **No approval lead time.** There is no regulator, no vendor onboarding and no
  procurement gate. The only human approval points are the workflow's own gates,
  which are not external dependencies.
- **No other team.** The repository has one author and no remote, and this intent
  forms no human team (Team Formation was SKIPped; `team-allocation.md` records
  the single AI mob). No unit waits on a hand-off from anyone outside this
  workflow.

Because there is nothing external to map, this map is deliberately near-empty.
No entry is invented to fill it.

## The one internal sequencing constraint worth naming

The only relationship that can hold a capability back is **internal** to the
workflow and is therefore recorded here only so it is not mistaken for an
external dependency:

| Constraint | From → To | Type | Bolt affected | Handled by |
|---|---|---|---|---|
| The declared `U1 → U2` edge | `U1`'s terms handler and term ranking → `U2`'s `TermExtraction` module | **Internal** build/import dependency inside this repository | Bolt 2 (`U1`) | Now enforced by topology: `U2` is Bolt 1 and resolves first. See `bolt-plan.md` and `risk-and-sequencing-rationale.md`. |

This is **not** an external dependency. `U2` is part of this same intent, is
owned by the same mob, and is built by this same workflow; it lives in
`inception/units-generation/unit-of-work-dependency.md` as a real import edge
that the `skeleton: on` ruling previously suppressed from the machine-readable DAG
block and which is now recorded there. It
appears here only to state plainly that nothing outside the team gates a Bolt —
the one gating relationship is between two Bolts in this plan.
