# Risk and Sequencing Rationale — sentiment-opencode v2 analytics layer

> **Intent:** `261001-analytics-layer` · stage `delivery-planning` (inception).
>
> This artifact explains why the Bolts are ordered as they are. A **Bolt** is one
> build pass over a piece of the work, ending in something that runs. This file
> stands alone; the order itself is in `bolt-plan.md`.

## The chosen heuristic: risk-first, with the walking skeleton first

Two heuristics were used together, and they agree on the first Bolt:

- **Risk-first.** Sequence the highest-uncertainty work early so decisions are
  calibrated before dependent work commits. The two riskiest pieces in this
  initiative are (a) the additive v3 → v4 migration, which runs in place against a
  store already in use and could lose data if it is wrong, and (b) the R-01
  defect, a SQLite connection thread-affinity bug that opened in one thread-pool
  worker and was used by the endpoint in another — overlapping requests raise
  `sqlite3.ProgrammingError` while sequential ones pass, so it is invisible to a
  single-threaded test. Both live in `U1`, so risk-first puts `U1` first.
- **Walking skeleton first.** The **walking skeleton** is the smallest working
  end-to-end slice built before the feature breadth goes in, to prove the pieces
  connect. This scope declares `skeleton: on`, and the runtime now resolves
  `u2-term-extraction` as the first Unit — a change made on 2026-10-04 when the
  `U1 → U2` edge was recorded in the DAG. `U1` remains a genuine end-to-end slice
  — schema migration → `/v2` route → `AnalyticsRead` aggregate → summary region of
  the page — and it is the first *integrated* path this plan builds, in Bolt 2.

**The two arguments now diverge, and that is recorded rather than smoothed over.**
Risk-first puts `U1` first (it carries the R-01 fix and the migration). Walking-
skeleton-first puts `U2` first, because that is what the recorded topology resolves.
The plan follows the topology, because the alternative — a skeleton the engine
cannot honour — is what produced the `app/terms.py` violation this record now
carries. The risk-first argument still governs `U1`'s content; it no longer governs
its position.

## Why each later Bolt sits where it does

- **Bolt 1 — `U2` (`u2-term-extraction`).** The tokenizer promotion and
  significance filter are ordered **first**, and this was changed on 2026-10-04.
  `U1`'s terms handler and `AnalyticsRead`'s term ranking import `U2`'s
  `TermExtraction` module. That dependency is now recorded as a `depends_on` entry
  in `unit-of-work-dependency.md` rather than suppressed, which demotes
  `u1-analytics-slice` from a DAG root and makes `U2` the Unit the `skeleton: on`
  rule resolves first.

  **Why it moved.** Previously `U2` was sequenced second and the constraint that
  `U1`'s terms work must not precede it was placed on this plan as a prose
  obligation. That obligation could not bind the engine: the engine resolves the
  first unsettled Unit from the edge block and does not consume `bolt-plan.md` for
  walk order. The result was that `U1` was walked first, built its terms path, and
  authored `app/terms.py` — a module assigned to `U2`. The dependency existed
  anyway; only the ordering had been suppressed. Recording the edge makes the
  obligation structural, at the cost of the skeleton becoming a library rather
  than an integrated slice.

- **Bolt 2 — `U1` (`u1-analytics-slice`).** The analytics slice, now ordered after
  `U2` because of the declared edge. **`U1`'s terms work (`US3.1`, `US3.2`, the
  term-list part of `US6.2`) is integrated here and imports `U2`'s module, so it
  can no longer be sequenced ahead of `U2` — the topology forbids it.** `U1`'s
  summary path is the first *integrated* end-to-end path this plan builds.
- **Bolt 3 — `U3` (`u3-analytics-view`).** The completed view depends on `U1` and
  consumes `U2`'s output only indirectly, through `U1`'s `/v2/analytics/terms`
  HTTP response; it never imports `U2`. It is last of the three feature Bolts
  because it cannot be resolved before `U1`, and because there is no value in
  drawing a view against endpoints that do not yet answer.
- **Bolt 4 — `U4` (`u4-platform-packaging`).** The lockfile, verification script,
  scanning, audit, `LICENSE`, `ruff` rules, `target-version` and README are
  independent of every other Bolt. `U4` is placed last because its verification
  script is more useful once there is a full suite to run, and because no other
  Bolt waits on it.

## Deviation from topological order, flagged

The chosen order (`U1 → U2 → U3 → U4`) **is** a valid topological order of the
machine-readable edge block: the only edge in that block is `u3-analytics-view →
u1-analytics-slice`, and `U1` precedes `U3`. No deviation is hidden there.

**There is no longer a deviation to flag.** The previously recorded deviation was
that `U1`'s full scope depends on `U2` while `U1` was built first. The `U1 → U2`
edge is now recorded in the DAG, so `U2` precedes `U1` in both the topology and
this plan and the deviation is closed rather than justified. The dependency remains
partial in its *effect* — it constrains `U1`'s **terms** path, while the **summary**
path is genuinely independent of `U2` (the summary buckets and averages stored rows
and never extracts terms) — which is why `U1`'s summary slice can still be the
first integrated path to run once `U2` exists.

## Why no formal scoring model was applied

Three named heuristics were considered and each was set aside:

- **Cohn (relative risk/value story-point ranking).** Cohn's approach sequences
  work by a coarse relative ranking of value and risk rather than a weighted
  formula. It was not used because the ranking it would produce is already forced
  by topology: `U2` precedes `U1`, `U1` precedes `U3`, and the only genuinely open
  choice is where `U4` sits — argued above on risk.
- **Reinertsen CD3 (Cost of Delay ÷ Duration).** CD3 scores a job by the money its
  delay costs divided by how long it takes. It was not used because nothing in
  this intent has a measurable cost of delay: it is a single-user localhost tool
  with no time-criticality driver, no revenue attached to a day's delay, and no
  deadline. A CD3 number would be invented, not measured.
- **SAFe WSJF (Weighted Shortest Job First).** **WSJF** scores a job as
  (user-business value + time criticality + risk-reduction value) ÷ job size, and
  ships the highest score first. It was not used for the same reason and one more:
  with one developer and four Bolts, a weighted score would produce a ranking the
  dependency DAG already forces. Assigning weights would add ceremony without
  changing the order, and could make the order look more objective than the real
  judgement behind it.

The judgement that remains genuinely human is the one captured here: which Bolt
proves what, and in what order confidence is earned. No scoring model can derive
that from the DAG, which is why this file argues it in prose instead.

## Confidence earned Bolt by Bolt

| Bolt | What shipping it proves |
|---|---|
| 1 — `U1` | An in-use store migrates forward in place without losing a row and with its three indexes intact; genuinely concurrent requests stop failing; stored row → aggregate → served view hangs together. |
| 2 — `U2` | Promoting the only tokenizer leaves offline scoring unchanged; the analytics filter cannot reach sentiment scoring. |
| 3 — `U3` | The three readouts describe one population across a range change; a failed read never looks like an empty one. |
| 4 — `U4` | Installs resolve identically; the standing gates run from one script; a boundary breach fails lint. |
