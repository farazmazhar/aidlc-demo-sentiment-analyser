# Delivery Planning — Plan (fast-tracked)

> One question, the drafted plan inside it. Reply `accept` to take it, or name the
> line you want changed. This stage chooses the **Bolt sequence** — the order the
> Units of Work are built — through the dependency DAG that Units Generation
> produced. A **Bolt** is one build pass over a piece of the work, ending in
> something that runs.
>
> The engine does not read `bolt-plan.md` to decide what to build first; it reads
> the DAG. So the sequence below must respect the DAG, and `U1` must be the first
> Unit built because this scope declares `skeleton: on`.

## Q1 — Accept the drafted Bolt plan?

**The DAG, for reference.** `u3-analytics-view` depends on `u1-analytics-slice`.
`u1`, `u2` and `u4` are dependency-free roots. A real `u1 → u2` import exists but
is recorded as a **suppressed edge** — the view needs nothing from term extraction,
and only `U1`'s terms handler does.

**Drafted sequencing: risk-first, with the walking skeleton first.**

1. **Bolt 1 — `u1-analytics-slice` (the walking skeleton).** The additive v3 → v4
   migration with its three named indexes, the `/v2` router and the summary
   endpoint, the `AnalyticsRead` module, the R-01 connection fix, and the summary
   region of the view — one analytics path running end to end. **Chosen first
   because it is the skeleton, because it carries the two riskiest pieces (the
   migration that can lose data, and the R-01 defect), and because every other
   Bolt either consumes it or is independent of it.** Its demo is a real
   `uvicorn` run against a throwaway database reading a live summary response.
2. **Bolt 2 — `u2-term-extraction`.** The promoted tokenizer and the
   significance filter, with the offline engine's scoring provably unchanged.
   *Ordered second, not first, because `U1`'s terms handler imports it — the
   suppressed edge means `U1` cannot finish its terms work until this lands.*
3. **Bolt 3 — `u3-analytics-view`.** The view completed: the nav and view
   switching, the term lists, the range control, the loading and partial states.
   *Last of the three feature Bolts because it depends on `U1` and consumes
   `U2`'s output through the endpoint.*
4. **Bolt 4 — `u4-platform-packaging`.** The lockfile, the verification script,
   secret scanning, the dependency audit, the `LICENSE`, the `ruff TID251`
   entries, `target-version`, and the README. *Independent of everything, so it
   could run in parallel at any point; placed last because its verification
   script is more useful once there is a full suite to run, and because no other
   Bolt waits on it.*

**Scoring.** No formal WSJF model is applied. With one developer and four Bolts,
a weighted score would produce a ranking that the DAG already forces — `U3`
cannot precede `U1`, so the only real choices are where `U2` and `U4` sit, and
both are argued above on risk and on the declared edge.

**Parallelism.** `U2` and `U4` have no dependency on `U1` or on each other, so in
principle they could be built alongside Bolt 1. With one developer this changes
nothing in practice; it is recorded so the DAG's freedom is not mistaken for a
mandate to serialise.

**Bolt size.** One Unit per Bolt. `U1` is XL and `U3` is L, so Bolts 1 and 3 are
substantial; splitting `U1` would break the walking skeleton, and splitting `U3`
would separate the view from the only endpoint it reads.

**External dependencies.** None. No external API, no data window, no approval
lead time, no other team. `external-dependency-map.md` will be near-empty and
will say so rather than inventing entries.

A. Accept the four-Bolt plan as drafted
B. Accept except for the items I name
C. Other (please specify)

[Answer]: A. Accept the four-Bolt plan as drafted.

## Consolidated Summary Confirmation

- **Four Bolts, one Unit each.** A Bolt is one build pass over a piece of the work, ending in something that runs.
- **Bolt 1 is the walking skeleton** — `u1-analytics-slice`: the additive v3 → v4 migration with its three named indexes, the `/v2` router and summary endpoint, the `AnalyticsRead` module, the R-01 connection fix, and the summary region of the view, running end to end. It is ordered first because it is the skeleton and because it carries both riskiest pieces: a migration that can lose data, and the cross-thread defect.
- **Bolt 1 is term extraction**, ordered first because the declared `U1 → U2` edge means `U1`'s terms handler imports it, so `U1` cannot finish its terms work until this lands.
- **Bolt 3 completes the view**, depending on Bolt 1.
- **Bolt 4 is the platform packaging** — lockfile, verification script, scanning, audit, `LICENSE`, `TID251`, `target-version` and the README. Independent of everything, placed last because its script is more useful once a full suite exists.
- **No formal scoring model was applied.** With one developer and four Bolts, WSJF, Cohn and Reinertsen CD3 would all reproduce an order the dependency DAG already forces; the only genuine choice is where Bolt 4 sits, and it is argued on risk. The edge is now declared rather than suppressed.
- **`U2` and `U4` are parallel-capable.** With one developer this changes nothing in practice, and it is recorded so the DAG's freedom is not mistaken for a mandate to serialise.
- **Every Bolt is owned by `aidlc-developer-agent`**, because Team Formation was skipped in Ideation and there is no second team.
- **No external dependencies.** The map is near-empty and says so rather than inventing entries; the only gating relationship named is the internal suppressed `U1 → U2` edge.
- **The phase-boundary check passes with no unresolved traceability finding**: user-stories 84 `OK` / 1 `N/A` / 0 `GAP`; domain-design 28 `OK` / 8 `N/A` / 0 `GAP`; units-generation 36 `OK` / 0 `GAP`. Contract Design owns no `traceability.json` by design.
- **Upstream corrections are registered, not open findings.** They sit in `requirements.md`'s Revision 2 and `contract-summary.md`'s upstream-corrections table.

- `Looks correct`
- `Request changes`

[Answer]: Looks correct
