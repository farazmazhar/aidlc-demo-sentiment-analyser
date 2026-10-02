# Team Allocation — sentiment-opencode v2 analytics layer

> **Intent:** `261001-analytics-layer` · stage `delivery-planning` (inception).
>
> This artifact assigns each **Bolt** (one build pass over a piece of the work,
> ending in something that runs) to the **mob** that owns it — a mob being the
> small cross-functional group that executes a Bolt together.

## The mob model for this intent

**Team Formation was SKIPped in Ideation** (`1.5` is marked `[S]` in
`aidlc-state.md`), so no multi-team structure was formed and there is no
team-to-Bolt mapping to inherit. Per the delivery-planning rules for a skipped
Team Formation stage, every Bolt is executed by the single AI agent
**`aidlc-developer-agent`**. In this intent a **mob** therefore means one AI
developer agent working the whole Bolt — the AI-DLC "small mob, broad agents"
model reduced to its one-agent minimum, not a human ensemble.

There is no Program Board here. A Program Board is the artifact that tracks
several teams' concurrent Bolts; with exactly one mob there is nothing to
coordinate across teams, so this document is a single-mob allocation instead.

## Bolt-to-mob assignment

| Bolt | Unit (directory) | Owner mob | Notes |
|---|---|---|---|
| 1 | `U1` — `u1-analytics-slice` (the walking skeleton) | `aidlc-developer-agent` | The slice is built before later Units; its integrated check and human checkpoint happen in Construction. |
| 2 | `U2` — `u2-term-extraction` | `aidlc-developer-agent` | Must land before `U1`'s terms work completes (the suppressed `U1 → U2` edge). |
| 3 | `U3` — `u3-analytics-view` | `aidlc-developer-agent` | Depends on Bolt 1. |
| 4 | `U4` — `u4-platform-packaging` | `aidlc-developer-agent` | Independent of every other Bolt. |

## Concurrency and ownership

- One mob, so there is no cross-mob hand-off to schedule. The plan's parallel-safe
  observation (that `U2` and `U4` are independent of `U1`) is a property of the
  dependency DAG, not an instruction to run several mobs.
- `U1`'s terms work (`US3.1`, `US3.2`, the term-list part of `US6.2`) is owned by
  the same mob as `U2`, but must not be sequenced ahead of `U2`: it imports `U2`'s
  module. The unit-level reason is in
  `inception/units-generation/unit-of-work-dependency.md`; the sequencing
  consequence is in `bolt-plan.md` and `risk-and-sequencing-rationale.md`.
- **Branching follows the affirmed team practice** (`memory/team.md` `## Way of
  Working`): one branch per intent or scope, squash-merged into `main` as a single
  commit tagged with the scope name, evidenced by the two prior scope commits.
  The commit subject follows the affirmed shape
  `<scope>: <summary> (<scope> scope)` with the body and trailer the team
  affirmed. No long-lived Bolt branch is implied by this allocation.
- No human reviewer exists for this repository (`git remote -v` is empty, one
  author); review is self-review plus agent review, and the guard policy is
  `relaxed`.
