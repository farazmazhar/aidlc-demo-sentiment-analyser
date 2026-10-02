# Story Map — sentiment-opencode v2 analytics layer

> **Intent:** `261001-analytics-layer` · stage `units-generation` (inception).
>
> Every one of the **35 stories** in `inception/user-stories/stories.md` is mapped
> here by `USx.y` to its implementing unit **`U{n}`** and construction **directory**
> `u{n}-{description}`. Because the User Stories triage merged the second half of
> the migration into `US5.1`, the story set carries a **36th id** — `US5.2` — which
> the traceability sensor still reads from the merge note and from
> `AC5.2.1`/`AC5.2.2`; it is mapped explicitly below as the merged half. **36 ids,
> 36 rows, no `GAP`.**
>
> This map is authoritative for the `traceability` sensor: each `OK` target in
> `traceability.json` is a `U{n}` id that also appears on that story's row here.

## Unit legend

| Unit ID | Directory | Kind |
|---|---|---|
| U1 | `u1-analytics-slice` | `service` |
| U2 | `u2-term-extraction` | `library` |
| U3 | `u3-analytics-view` | `ui` |
| U4 | `u4-platform-packaging` | `packaging` |

## Story → unit matrix

| Story | Title | Unit ID | Directory | Notes |
|---|---|---|---|---|
| `US1.1` | Analytics queries behind one read module | U1 | `u1-analytics-slice` | The `AnalyticsRead` module and the route→read edge. *Slice.* |
| `US1.2` | Concurrent requests that no longer fail | U1 | `u1-analytics-slice` | R-01 fix owned by the connection module (Q7, ADR-006). The concurrency test's harness is `US7.7`, also in U1. |
| `US2.1` | Totals, label breakdown and confidence | U1 | `u1-analytics-slice` | The summary computation and the summary route. *Slice.* |
| `US2.2` | Date range resolution | U1 | `u1-analytics-slice` | Shared range resolution in `AnalyticsRead`. |
| `US2.3` | A continuous per-day series | U1 | `u1-analytics-slice` | One-grouped-query series plus in-process zero-fill. |
| `US2.4` | Empty, refused and failed answers told apart | U1 | `u1-analytics-slice` | Read-side shape plus the one error envelope and its new 500 code. |
| `US2.5` | Reading analytics never changes the data | U1 | `u1-analytics-slice` | Read-only guarantee on the `AnalyticsRead` surface. |
| `US3.1` | Ranked top terms per list | U1 | `u1-analytics-slice` | Terms handler and ranking live in U1; consumes U2's `significant_terms`. |
| `US3.2` | Terms and summary describing the same rows | U1 | `u1-analytics-slice` | One range resolution shared by both endpoints. |
| `US4.1` | Significant terms extracted the simple way | U2 | `u2-term-extraction` | 3-character minimum, stopword constant, accepted non-Latin limitation. |
| `US4.2` | One tokenizer, two jobs, engine untouched | U2 | `u2-term-extraction` | Two operations + the offline engine's scoring-parity refactor. |
| `US5.1` | A schema step that only adds | U1 | `u1-analytics-slice` | Additive v3 → v4 migration, idempotency, same-transaction version bump. |
| `US5.2` | Indexes that survive a rebuild — the merged half of `US5.1` | U1 | `u1-analytics-slice` | **Merged into `US5.1` by the User Stories triage; no `###` heading, but the sensor reads the id from the merge note and `AC5.2.1`/`AC5.2.2`.** Delivered by the same U1 migration work: the three named indexes and the explicit re-creation in `_rebuild_analyses`. |
| `US6.1` | An analytics entry in the shell I already use | U3 | `u3-analytics-view` | Third top-level entry, nav/header and `data-testid` hooks. |
| `US6.2` | The three readouts | U1 | `u1-analytics-slice` | *Slice.* **Split across U1 and U3 — see the cross-cutting table.** U1 delivers the series and label-breakdown summary region that completes the summary path end to end (the slice half); U3 delivers the two term-list containers `AC6.2.1` also requires (the full-view half). Declared target is U1 (the slice is the primary deliverable). |
| `US6.3` | A range control that starts at everything | U3 | `u3-analytics-view` | Labelled range control, unbounded default, reset; no `import_id`/`limit` control. |
| `US6.4` | A failed read never looks like an empty one | U3 | `u3-analytics-view` | Inline error region, 422/500 distinction, native rendering, accessibility. |
| `US6.5` | A view that shows what it is doing | U3 | `u3-analytics-view` | Loading, partial-failure and superseded-response states. |
| `US7.1` | Reproducible installs | U4 | `u4-platform-packaging` | Lockfile with hashes plus the install command that consumes it. |
| `US7.2` | One command that runs the gates | U4 | `u4-platform-packaging` | Platform-neutral verification script; neither a hook nor a CI job. |
| `US7.3` | Scanning that would catch a real key | U4 | `u4-platform-packaging` | Secret scanning + dependency audit, invoked by the verification script. |
| `US7.4` | A licence on the project | U4 | `u4-platform-packaging` | `LICENSE` file and the distribution's licence declaration. |
| `US7.5` | Boundaries that fail the build | U4 | `u4-platform-packaging` | `ruff TID251` banned-api entries. |
| `US7.6` | A server that refuses to leave the loopback | U1 | `u1-analytics-slice` | Loopback-bind enforcement at startup, in `Application Assembly` (a runtime component, not packaging). |
| `US7.7` | A test harness that can host concurrency | U1 | `u1-analytics-slice` | The replaced ASGI harness lands with the slice so the R-01 concurrency test can run; it is a prerequisite of `US1.2`. **Decided here: the harness work lands in U1, not U4.** |
| `US7.8` | Static analysis aimed at the Python we run | U4 | `u4-platform-packaging` | `ruff target-version` matched to `requires-python`. |
| `US7.9` | Documentation that matches the code | U4 | `u4-platform-packaging` | README updates. Cross-cutting content: describes the U1 `/v2` surface and the U3 view; story-level dependency on `US2.1`, `US3.1`, `US6.1`, carried as content, not as a DAG edge (Q6). |
| `US8.1` | Answers inside the performance budget | U1 | `u1-analytics-slice` | 10,000-row budget and constant statement count, verified by U1's tests. |
| `US8.2` | No new way for data to leave | U1 | `u1-analytics-slice` | Cross-cutting: also holds for U2's leaf module; declared target is U1. |
| `US8.3` | A read that cannot mutate | U1 | `u1-analytics-slice` | Read-only surface + lint boundary (U4's rule set). Cross-cutting with U4's `TID251`. |
| `US8.4` | Failures that stay distinguishable | U1 | `u1-analytics-slice` | Distinguishable statuses/codes through the one envelope. |
| `US8.5` | Nothing about `/v1` changes | U1 | `u1-analytics-slice` | `/v1` routes, envelope shape, `SentimentClient` unchanged. |
| `US8.6` | New code that reads like the old | U1 | `u1-analytics-slice` | Cross-cutting: the module conventions apply to U1's `AnalyticsRead` and U2's `TermExtraction`; declared target is U1. |
| `US8.7` | Tests that touch the real thing | U1 | `u1-analytics-slice` | Real SQLite/real markup, offline guard armed. **Decided here: this lands with U1's harness/test work, not U4.** |
| `US8.8` | A failure I can actually see | U1 | `u1-analytics-slice` | Failure logged through the module logger, no credential, no interpolated SQL. |
| `US8.9` | Work that stays proportionate | U1 | `u1-analytics-slice` | Bounded series length and `limit`-bounded term-list size. |

## Cross-cutting stories

These stories exercise more than one unit. Each still has exactly one **declared
target** (the unit in the matrix above) so the traceability join stays
single-valued; the cross-unit reach is recorded here.

| Story | Declared target | Also reaches | Why |
|---|---|---|---|
| `US6.2` | U1 | U3 | **`US6.2` is split by deliverable part.** `AC6.2.1` requires containers for the series, the label breakdown **and both term lists**. U1 delivers the series + breakdown summary region (the slice, and the declared target); U3 delivers the two term-list containers that live in the full view. Neither unit alone satisfies `AC6.2.1`; both rows ship the story. |
| `US7.9` | U4 | U1, U3 | The README's contract-of-record table and file tree describe the `/v2` surface and the view. Content dependency, not a DAG edge. |
| `US8.2` | U1 | U2 | "No new egress" holds for the leaf module too; the declared target is the primary new module set. |
| `US8.3` | U1 | U4 | The read-only guarantee is behavioural (U1) and lint-enforced as an import boundary (`TID251`, U4). |
| `US8.6` | U1 | U2 | The module conventions apply to both new modules; the declared target is the larger new module. |

## Story implementation order within each unit

This is a **within-unit** sequencing constraint derived from the stories' own stated
dependencies. It is not a cross-unit plan and does not rank units.

**U1 (`u1-analytics-slice`)**
The migration and the connection/read foundation precede the endpoints they
support: `US5.1` (with `US5.2`) and `US1.1` first; then `US2.1 → US2.2 → US2.3` and
`US2.4`; the terms endpoint `US3.1 → US3.2` **follows U2's extraction interface**
(the real, suppressed `U1 → U2` edge — see `unit-of-work-dependency.md`) and precedes
the slice's view region (`US6.2`'s U1 half, the series + breakdown). `US7.7` (harness)
precedes `US1.2` (the concurrency fix it proves); `US7.6` is independent of the data
path. The NFR stories `US8.1`–`US8.9` are verified as the capabilities they protect
land.

**U2 (`u2-term-extraction`)**
`US4.2` (promote the tokenizer, prove scoring parity) precedes `US4.1` (build the
filter on top of the promoted tokenizer), matching the story set's own
`US4.2 → US4.1` edge.

**U3 (`u3-analytics-view`)**
`US6.1` (the shell entry) provides the home for the view; `US6.3` (range control),
`US6.4` (error states) and `US6.5` (loading/partial states) all depend on `US6.2`.
U3 delivers **`US6.2`'s term-list half** (the two containers `AC6.2.1` requires) and
renders the ranked entries U1's `/v2/analytics/terms` response returns. **U3 depends
on U1 alone** — it fetches over U1's HTTP endpoints and never imports U2's
`TermExtraction`; the earlier claim that U3 depends on U2 was wrong and is corrected
in `unit-of-work-dependency.md`.

**U4 (`u4-platform-packaging`)**
The gates (`US7.2`) precede the checks that hang off them (`US7.3` scanning,
`US7.5` boundaries); `US7.1` (lockfile), `US7.4` (LICENSE), `US7.8` (`target-
version`) and `US7.9` (README) are independent of each other within the unit.

## Coverage verification

**Every story assigned.** The 36 upstream ids (`US1.1`–`US8.9` plus the merged
`US5.2`) each appear on exactly one **declared-target** row above with a `U{n}` id
and a directory. `US6.2` additionally reaches U3 and is recorded in the cross-cutting
table; its declared target remains U1. Breakdown by story group:

| Group | Stories | Declared target unit |
|---|---|---|
| US1 | `US1.1`, `US1.2` | U1 |
| US2 | `US2.1`–`US2.5` (5) | U1 |
| US3 | `US3.1`, `US3.2` | U1 |
| US4 | `US4.1`, `US4.2` | U2 |
| US5 | `US5.1` + merged `US5.2` | U1 |
| US6 | `US6.1`–`US6.5` (5) | `US6.2` → U1 (declared; also reaches U3); `US6.1`, `US6.3`, `US6.4`, `US6.5` → U3 |
| US7 | `US7.1`–`US7.9` (9) | `US7.1`–`US7.5`, `US7.8`, `US7.9` → U4; `US7.6`, `US7.7` → U1 |
| US8 | `US8.1`–`US8.9` (9) | U1 |
| **Total** | **36 ids (35 headings + `US5.2`)** | 4 units |

**Count per unit (by declared target).**

| Unit | Story count | Stories (declared target) |
|---|---|---|
| U1 `u1-analytics-slice` | 23 | US1.1, US1.2, US2.1–US2.5, US3.1, US3.2, US5.1, US5.2, US6.2, US7.6, US7.7, US8.1–US8.9 |
| U2 `u2-term-extraction` | 2 | US4.1, US4.2 |
| U3 `u3-analytics-view` | 4 | US6.1, US6.3, US6.4, US6.5 |
| U4 `u4-platform-packaging` | 7 | US7.1, US7.2, US7.3, US7.4, US7.5, US7.8, US7.9 |

**Every unit has stories.** No unit is empty: U1 (23), U2 (2), U3 (4), U4 (7).
Sum: 36 declared targets across 36 ids. ✓ In addition, **U3 carries the `US6.2`
term-list half** as a second deliverable row (cross-cutting), so `US6.2` is covered
by both U1 and U3 without changing the declared-target totals above.

**No `GAP`.** Every story has a declared destination. The two stories the brief
flagged for a decision — `US7.7` (ASGI harness) and `US8.7` (real-value tests) —
are assigned to **U1**, because the harness replacement and its test contract land
with the slice that proves the R-01 concurrency fix; they are not packaging
artifacts.

**Story-level dependencies not shown as DAG edges.** `US7.9`'s content dependency
on `US2.1`/`US3.1`/`US6.1`, and the `US5.1 → US7.9` and `US4.2 → US7.9` edges in
`stories.md`, are recorded here and in `unit-of-work-dependency.md` rather than
turned into a `u4-platform-packaging` edge, because the human ruled the platform
unit independent (Q6).

**Real dependency suppressed from the DAG.** U1's terms work (`US3.1`, `US3.2`) — and
the term-ranking part of `US6.2` — imports U2's `TermExtraction` module. That is a
real `U1 → U2` build edge, deliberately not recorded as a `depends_on` entry so U1
stays the `skeleton: on` integrated slice. It is stated in full — with the obligation
that Delivery Planning must not sequence U1's terms work ahead of U2 — in
`unit-of-work-dependency.md` under **"The suppressed U1 → U2 edge"**.
