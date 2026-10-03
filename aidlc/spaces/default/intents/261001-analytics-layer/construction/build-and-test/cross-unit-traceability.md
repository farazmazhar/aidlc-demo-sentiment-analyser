# Cross-Unit Traceability Gate — intent `261001-analytics-layer`

> **Stage:** `build-and-test` (construction) · step-level gate: *Cross-Unit Final
> Coverage Gate* · **Record:**
> `aidlc/spaces/default/intents/261001-analytics-layer/construction/build-and-test`
>
> **Inputs this stage consumed** (the stage frontmatter's `consumes`):
> `construction/u1-analytics-slice/code-generation/code-generation-plan.md` ·
> `construction/u1-analytics-slice/code-generation/unit-test-instructions.md` ·
> `construction/u1-analytics-slice/code-generation/code-summary.md`.

## 1. What this gate is, and the files it reads

This is a **stage-level** gate, not the Construction phase boundary. It enumerates:

* every `FR` and every `NFR` in `inception/requirements-analysis/requirements.md`;
* every three-segment `AC` in `inception/user-stories/stories.md` (that stage executed);

and checks each against the coverage arrays of

* the **stage-level** `construction/code-generation/traceability.json` — **absent**,
  because the stage-level `code-generation` was SKIPped in favour of per-Unit runs
  (`aidlc-state.md` → Stage Progress: `[S] code-generation`), and
* every per-Unit `construction/*/code-generation/traceability.json` — **exactly one
  exists**, `construction/u1-analytics-slice/code-generation/traceability.json`.

**Enumerated inventory: 215 ids — 76 `FR`, 9 `NFR`, 130 `AC`.**

## 2. Verdict

# ❌ FAIL — as written

| Enumerated set | Total | `OK` in a read traceability | non-`OK` | absent from every read traceability |
|---|---|---|---|---|
| `FR` (from `requirements.md`) | 76 | **0** | 0 | **76** |
| `NFR` (from `requirements.md`) | 9 | **0** | 0 | **9** |
| `AC` (three-segment, from `stories.md`) | 130 | **83** | 1 (`AC2.4.3`, `N/A`) | **46** |
| **Total** | **215** | **83** | **1** | **131** |

Every uncovered element is listed in §5 and per id in §6. Three findings must be
surfaced at the approval gate (§7).

## 3. Why it fails — two independent reasons, stated separately

### Reason 1 — granularity: no `FR{n}` id appears in *any* code-generation traceability

`code-generation`'s `upstream_ids` and `coverage` arrays carry `BR{n}.{m}`,
`AC{n}.{m}.{seq}` and `NFR{n}.{y}` ids. **No `FR` id appears at all.** The trace this
project builds runs `FR → AC → BR → code`, so `FR` coverage is necessarily
*transitive*: an `FR` is covered only if the acceptance criteria of the stories that
own it are covered. §6.1 resolves each `FR` along exactly that chain and records the
result. The literal gate — "covered with status `OK` in at least one entry" — cannot be
satisfied for any `FR` by the file it tells me to read, in this repository, for any
Unit. That is a **reporting-shape gap in code-generation's traceability contract**, not
evidence that the requirements are unimplemented.

### Reason 2 — sequencing: the enumerated set is intent-wide, but only Bolt 1 of 4 exists

`units-generation/unit-of-work.md` defines four Units and this is **Bolt 1 of 4** under
unit-major, serial, checkpoint-enabled construction:

| Unit | Directory | Depends on | Built? |
|---|---|---|---|
| U1 | `u1-analytics-slice` | — (root) | **yes — this stage's subject** |
| U2 | `u2-term-extraction` | — (root) | no |
| U3 | `u3-analytics-view` | U1 | no |
| U4 | `u4-platform-packaging` | — (root) | no |

All **46** absent `AC` ids belong to U2, U3 or U4. They are not gaps in this Bolt; they
are work that has not been built yet, in the order
`unit-of-work-dependency.md` records. The same reason removes 5 `NFR` ids:
`NFR5`, `NFR6` and `NFR7` are declared `N/A` upstream as invariants with no
sub-numberable value, and `NFR1`–`NFR4`/`NFR8`/`NFR9` are **parent** ids that the
construction stages sub-numbered into the 26 `NFRx.y` targets — the parents are covered
by their children, which are all `OK`.

### The reading that is useful, and is **not** what the literal gate says

Within U1's own declared scope the coverage is sound: **83 of 84** `AC` ids declared by
`u1-analytics-slice`'s own `functional-design` traceability are `OK`, and **every one of
their 83 target files exists on disk** (checked individually; zero `MISSING`). The single
non-`OK` row, `AC2.4.3`, is declared `N/A` with a substantive reason rather than
claimed: `import_id` is pinned as an opaque string with no parse step (contract `UC1`),
so no input can trigger a `422` naming `query.import_id`; the reachable `from`/`to`
halves are delivered by `BR4.2`. That is a correct `N/A`, and it is the only one in
U1's scope.

## 4. Target-file existence check

Every `OK` entry's target was resolved to a repository path and checked with `os.path.exists`:

| Result | Count |
|---|---|
| `OK` entries whose target file **exists** | **83 of 83** |
| `OK` entries whose target file is **missing** | **0** |

The two `OK` entries whose target is prose rather than a path (`AC1.2.3`,
`AC8.5.3`) name `app/db.py` and `app/sentiment.py` respectively inside their note text,
and both files exist.

## 5. Every uncovered element

### 5.1 `FR` ids with no `OK` row anywhere (76 of 76)

All of them, for the Reason 1 / Reason 2 reasons above. Individually, by transitive
resolution:

* **42 `FR` ids covered with every criterion `OK`:** `FR1`, `FR1.1`–`FR1.6`;
  `FR2.1`–`FR2.9`, `FR2.13`; `FR3`, `FR3.1`–`FR3.8`; `FR5`, `FR5.1`–`FR5.7`;
  `FR6.2`; `FR7.6`, `FR7.7`; `FR8.2`–`FR8.5`, `FR8.7`–`FR8.9`.
* **6 `FR` ids whose every criterion is present but one is the `N/A` criterion** rather
  than `OK` — the `AC2.4.3` `N/A` of §5.4: `FR2`, `FR2.10`, `FR2.11`, `FR2.12`, `FR8`,
  `FR8.1`.
* **5 `FR` ids covered in part**, because some criteria they own are `OK` and others
  belong to an unbuilt Unit: `FR6`, `FR7`, `FR8`, `FR8.1`, `FR8.6`. (`FR8` and `FR8.1`
  appear in both lists: they carry the `N/A` criterion *and* reach into unbuilt Units.)
* **22 `FR` ids with no coverage at all**, because every criterion they own belongs to an
  unbuilt Unit: the `FR4` family (`FR4`, `FR4.1`–`FR4.6` → U2, 7 ids); the `FR6` family
  (`FR6.1`, `FR6.3`, `FR6.4`, `FR6.5`, `FR6.6`, `FR6.7`, `FR6.8`, `FR6.9` → U3, 8 ids);
  and the `FR7` sub-family (`FR7.1`–`FR7.5`, `FR7.8`, `FR7.9` → U4, 7 ids).
* **`FR3.9` is not a requirement id at all.** It occurs in `requirements.md` only inside
  the Revision 1 review-findings prose, as the label *"R-12 (`FR3.9`'s deferral
  list)"*, naming `FR3.9`'s deferral list in a superseded first draft. The terms
  endpoint's real requirements are `FR3.1`–`FR3.8`, all covered.
  `inception/user-stories/traceability.json` already records this exact finding. It is
  surfaced here so the gate's own enumeration does not read as a missing requirement.

42 + 6 + 5 + 22 + 1 (`FR3.9`) = **76**, matching the enumeration.

The per-id rows in §6.1 record the machine-derived resolution
(`OK (transitively)` / `PARTIAL` / `NOT COVERED`) from the presence or absence of `AC`
rows in the traceability. The `AC2.4.3` nuance is stated here because it is a *status* of
one criterion rather than the presence or absence of a row, which is why the
machine-derived label for those six reads `OK (transitively)`.

### 5.2 `NFR` ids with no `OK` row anywhere (9 of 9)

| `NFR` | Why |
|---|---|
| `NFR1`, `NFR2`, `NFR3`, `NFR4`, `NFR8`, `NFR9` | Parent ids. Covered by their sub-numbered children — `NFR1.1`–`NFR1.4`, `NFR2.1`–`NFR2.6`, `NFR3.1`–`NFR3.2`, `NFR4.1`–`NFR4.7`, `NFR8.1`–`NFR8.3`, `NFR9.1`–`NFR9.4` — of which **24 are `OK` and 2 (`NFR4.6`, `NFR4.7`) are `N/A` with a recorded reason.** |
| `NFR5` | Compatibility (`/v1` freeze, envelope shape, `SentimentClient` interface unchanged) — declared `N/A` upstream as an **invariant, not a target**; no `NFR5.y` exists. Verified by the `/v1` suite staying green. |
| `NFR6` | Maintainability (module conventions, stdlib dataclasses, no third-party validator) — declared `N/A` upstream as an invariant. Enforced by the pinned `ruff` rule set, measured green. |
| `NFR7` | Testability (real SQLite, real served markup, no browser automation) — declared `N/A` upstream as an invariant; it constrains how instruments are built rather than being a target. |

### 5.3 `AC` ids absent from every read traceability (46 of 46)

| Owning Unit | Absent `AC` ids | Count |
|---|---|---|
| **U2** `u2-term-extraction` | `AC4.1.1`–`AC4.1.6`, `AC4.2.1`–`AC4.2.3` | 9 |
| **U3** `u3-analytics-view` | `AC6.1.1`–`AC6.1.4`, `AC6.3.1`–`AC6.3.6`, `AC6.4.1`–`AC6.4.4`, `AC6.5.1`–`AC6.5.5` | 19 |
| **U4** `u4-platform-packaging` | `AC7.1.1`–`AC7.1.3`, `AC7.2.1`–`AC7.2.3`, `AC7.3.1`–`AC7.3.3`, `AC7.4.1`–`AC7.4.2`, `AC7.5.1`–`AC7.5.2`, `AC7.8.1`–`AC7.8.2`, `AC7.9.1`–`AC7.9.3` | 18 |

### 5.4 `AC` ids present but not `OK` (1 of 130)

| `AC` | Status | Reason as recorded |
|---|---|---|
| `AC2.4.3` | `N/A` | **UNREACHABLE** (contract `UC1`), carried from functional design. `import_id` is pinned as an opaque string with no parse step, so no input can trigger a `422` naming `query.import_id`; an unmatched id is the `200` empty result of `AC2.4.2`/`BR4.4`. The reachable `from`/`to` halves of the criterion **are** delivered by `BR4.2`. No test was written for the impossible `import_id` 422 — correctly. |

## 6. Per-id coverage

### 6.1 `FR` — 76 ids, resolved along `FR → US → AC → target`

The "coverage" column is the transitive resolution of the `FR` through the stories that
own it (`inception/user-stories/traceability.json`) to the `AC` rows that
`u1-analytics-slice`'s code-generation traceability declares. **No `FR` id appears as a
row in that file** — that is Reason 1.

| `FR` | Owning stories (`US`) | `AC` rows found | Coverage |
|---|---|---|---|

| `FR1` | US1.1, US1.2 | 8 | OK (transitively) |
| `FR1.1` | US1.1 | 5 | OK (transitively) |
| `FR1.2` | US1.1 | 5 | OK (transitively) |
| `FR1.3` | US1.1 | 5 | OK (transitively) |
| `FR1.4` | US1.1 | 5 | OK (transitively) |
| `FR1.5` | US1.1 | 5 | OK (transitively) |
| `FR1.6` | US1.2 | 3 | OK (transitively) |
| `FR2` | US2.1, US2.4, US2.5, US2.2, US2.3 | 21 | OK (transitively) |
| `FR2.1` | US2.1 | 5 | OK (transitively) |
| `FR2.2` | US2.2 | 6 | OK (transitively) |
| `FR2.3` | US2.1 | 5 | OK (transitively) |
| `FR2.4` | US2.2 | 6 | OK (transitively) |
| `FR2.5` | US2.2 | 6 | OK (transitively) |
| `FR2.6` | US2.2 | 6 | OK (transitively) |
| `FR2.7` | US2.1 | 5 | OK (transitively) |
| `FR2.8` | US2.1 | 5 | OK (transitively) |
| `FR2.9` | US2.3 | 3 | OK (transitively) |
| `FR2.10` | US2.4 | 5 | OK (transitively) |
| `FR2.11` | US2.4 | 5 | OK (transitively) |
| `FR2.12` | US2.4 | 5 | OK (transitively) |
| `FR2.13` | US2.5 | 2 | OK (transitively) |
| `FR3` | US3.1, US3.2 | 8 | OK (transitively) |
| `FR3.1` | US3.1 | 5 | OK (transitively) |
| `FR3.2` | US3.1 | 5 | OK (transitively) |
| `FR3.3` | US3.1 | 5 | OK (transitively) |
| `FR3.4` | US3.1 | 5 | OK (transitively) |
| `FR3.5` | US3.1 | 5 | OK (transitively) |
| `FR3.6` | US3.2 | 3 | OK (transitively) |
| `FR3.7` | US3.1 | 5 | OK (transitively) |
| `FR3.8` | US3.2 | 3 | OK (transitively) |
| `FR3.9` | — | 0 | NOT COVERED |
| `FR4` | US4.1, US4.2 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC4.1.1`, `AC4.1.2`, `AC4.1.3`, `AC4.1.4`, `AC4.1.5`, `AC4.1.6`, `AC4.2.1`, `AC4.2.2`, `AC4.2.3` |
| `FR4.1` | US4.1 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC4.1.1`, `AC4.1.2`, `AC4.1.3`, `AC4.1.4`, `AC4.1.5`, `AC4.1.6` |
| `FR4.2` | US4.1 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC4.1.1`, `AC4.1.2`, `AC4.1.3`, `AC4.1.4`, `AC4.1.5`, `AC4.1.6` |
| `FR4.3` | US4.1 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC4.1.1`, `AC4.1.2`, `AC4.1.3`, `AC4.1.4`, `AC4.1.5`, `AC4.1.6` |
| `FR4.4` | US4.1 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC4.1.1`, `AC4.1.2`, `AC4.1.3`, `AC4.1.4`, `AC4.1.5`, `AC4.1.6` |
| `FR4.5` | US4.2 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC4.2.1`, `AC4.2.2`, `AC4.2.3` |
| `FR4.6` | US4.1 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC4.1.1`, `AC4.1.2`, `AC4.1.3`, `AC4.1.4`, `AC4.1.5`, `AC4.1.6` |
| `FR5` | US5.1 | 5 | OK (transitively) |
| `FR5.1` | US5.1 | 5 | OK (transitively) |
| `FR5.2` | US5.1 | 5 | OK (transitively) |
| `FR5.3` | US5.1 | 5 | OK (transitively) |
| `FR5.4` | US5.1 | 5 | OK (transitively) |
| `FR5.5` | US5.1 | 5 | OK (transitively) |
| `FR5.6` | US5.1 | 5 | OK (transitively) |
| `FR5.7` | US5.1 | 5 | OK (transitively) |
| `FR6` | US6.1, US6.2, US6.3, US6.5, US6.4 | 5 | PARTIAL — unbuilt ACs: `AC6.1.1`, `AC6.1.2`, `AC6.1.3`, `AC6.1.4`, `AC6.3.1`, `AC6.3.2`, `AC6.3.3`, `AC6.3.4`, `AC6.3.5`, `AC6.3.6`, `AC6.5.1`, `AC6.5.2`, `AC6.5.3`, `AC6.5.4`, `AC6.5.5`, `AC6.4.1`, `AC6.4.2`, `AC6.4.3`, `AC6.4.4` |
| `FR6.1` | US6.1 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC6.1.1`, `AC6.1.2`, `AC6.1.3`, `AC6.1.4` |
| `FR6.2` | US6.2 | 5 | OK (transitively) |
| `FR6.3` | US6.3 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC6.3.1`, `AC6.3.2`, `AC6.3.3`, `AC6.3.4`, `AC6.3.5`, `AC6.3.6` |
| `FR6.4` | US6.3, US6.5 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC6.3.1`, `AC6.3.2`, `AC6.3.3`, `AC6.3.4`, `AC6.3.5`, `AC6.3.6`, `AC6.5.1`, `AC6.5.2`, `AC6.5.3`, `AC6.5.4`, `AC6.5.5` |
| `FR6.5` | US6.4 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC6.4.1`, `AC6.4.2`, `AC6.4.3`, `AC6.4.4` |
| `FR6.6` | US6.4 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC6.4.1`, `AC6.4.2`, `AC6.4.3`, `AC6.4.4` |
| `FR6.7` | US6.4 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC6.4.1`, `AC6.4.2`, `AC6.4.3`, `AC6.4.4` |
| `FR6.8` | US6.4 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC6.4.1`, `AC6.4.2`, `AC6.4.3`, `AC6.4.4` |
| `FR6.9` | US6.1 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC6.1.1`, `AC6.1.2`, `AC6.1.3`, `AC6.1.4` |
| `FR7` | US7.1, US7.2, US7.3, US7.4, US7.5, US7.6, US7.7, US7.8, US7.9 | 8 | PARTIAL — unbuilt ACs: `AC7.1.1`, `AC7.1.2`, `AC7.1.3`, `AC7.2.1`, `AC7.2.2`, `AC7.2.3`, `AC7.3.1`, `AC7.3.2`, `AC7.3.3`, `AC7.4.1`, `AC7.4.2`, `AC7.5.1`, `AC7.5.2`, `AC7.8.1`, `AC7.8.2`, `AC7.9.1`, `AC7.9.2`, `AC7.9.3` |
| `FR7.1` | US7.1 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC7.1.1`, `AC7.1.2`, `AC7.1.3` |
| `FR7.2` | US7.2 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC7.2.1`, `AC7.2.2`, `AC7.2.3` |
| `FR7.3` | US7.3 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC7.3.1`, `AC7.3.2`, `AC7.3.3` |
| `FR7.4` | US7.4 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC7.4.1`, `AC7.4.2` |
| `FR7.5` | US7.5 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC7.5.1`, `AC7.5.2` |
| `FR7.6` | US7.6 | 3 | OK (transitively) |
| `FR7.7` | US7.7 | 5 | OK (transitively) |
| `FR7.8` | US7.8 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC7.8.1`, `AC7.8.2` |
| `FR7.9` | US7.9 | 0 | NOT COVERED — all criteria belong to unbuilt Units: `AC7.9.1`, `AC7.9.2`, `AC7.9.3` |
| `FR8` | US2.4, US3.2, US4.1, US2.1, US2.3, US3.1, US5.1, US1.2, US7.7, US8.7, US6.1, US6.2, US8.1 | 47 | PARTIAL — unbuilt ACs: `AC4.1.1`, `AC4.1.2`, `AC4.1.3`, `AC4.1.4`, `AC4.1.5`, `AC4.1.6`, `AC6.1.1`, `AC6.1.2`, `AC6.1.3`, `AC6.1.4` |
| `FR8.1` | US2.4, US3.2, US4.1 | 8 | PARTIAL — unbuilt ACs: `AC4.1.1`, `AC4.1.2`, `AC4.1.3`, `AC4.1.4`, `AC4.1.5`, `AC4.1.6` |
| `FR8.2` | US2.1, US2.3, US3.1 | 13 | OK (transitively) |
| `FR8.3` | US5.1 | 5 | OK (transitively) |
| `FR8.4` | US1.2, US7.7 | 8 | OK (transitively) |
| `FR8.5` | US8.7 | 4 | OK (transitively) |
| `FR8.6` | US6.1, US6.2 | 5 | PARTIAL — unbuilt ACs: `AC6.1.1`, `AC6.1.2`, `AC6.1.3`, `AC6.1.4` |
| `FR8.7` | US8.7 | 4 | OK (transitively) |
| `FR8.8` | US8.7 | 4 | OK (transitively) |
| `FR8.9` | US8.1 | 4 | OK (transitively) |

### 6.2 `AC` — 130 three-segment ids

| `AC` | Owning Unit | Status in code-generation traceability | Target file | Exists? |
|---|---|---|---|---|

| `AC1.1.1` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC1.1.2` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC1.1.3` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC1.1.4` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC1.1.5` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC1.2.1` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC1.2.2` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC1.2.3` | U1 `u1-analytics-slice` | OK | `app/db.py` | exists |
| `AC2.1.1` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.1.2` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.1.3` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.1.4` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.1.5` | U1 `u1-analytics-slice` | OK | `app/routes.py` | exists |
| `AC2.2.1` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.2.2` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.2.3` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.2.4` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.2.5` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.2.6` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.3.1` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.3.2` | U1 `u1-analytics-slice` | OK | `app/models.py` | exists |
| `AC2.3.3` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.4.1` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC2.4.2` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC2.4.3` | U1 `u1-analytics-slice` | N/A | `UNREACHABLE` | n/a (prose) |
| `AC2.4.4` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC2.4.5` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC2.5.1` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC2.5.2` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC3.1.1` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC3.1.2` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC3.1.3` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC3.1.4` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC3.1.5` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC3.2.1` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC3.2.2` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC3.2.3` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC4.1.1` | — | **ABSENT** | — | — |
| `AC4.1.2` | — | **ABSENT** | — | — |
| `AC4.1.3` | — | **ABSENT** | — | — |
| `AC4.1.4` | — | **ABSENT** | — | — |
| `AC4.1.5` | — | **ABSENT** | — | — |
| `AC4.1.6` | — | **ABSENT** | — | — |
| `AC4.2.1` | — | **ABSENT** | — | — |
| `AC4.2.2` | — | **ABSENT** | — | — |
| `AC4.2.3` | — | **ABSENT** | — | — |
| `AC5.1.1` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC5.1.2` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC5.1.3` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC5.1.4` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC5.1.5` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC5.2.1` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC5.2.2` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC6.1.1` | — | **ABSENT** | — | — |
| `AC6.1.2` | — | **ABSENT** | — | — |
| `AC6.1.3` | — | **ABSENT** | — | — |
| `AC6.1.4` | — | **ABSENT** | — | — |
| `AC6.2.1` | U1 `u1-analytics-slice` | OK | `app/static/index.html` | exists |
| `AC6.2.2` | U1 `u1-analytics-slice` | OK | `app/static/index.html` | exists |
| `AC6.2.3` | U1 `u1-analytics-slice` | OK | `app/static/app.js` | exists |
| `AC6.2.4` | U1 `u1-analytics-slice` | OK | `tests/test_page.py` | exists |
| `AC6.2.5` | U1 `u1-analytics-slice` | OK | `app/static/app.js` | exists |
| `AC6.3.1` | — | **ABSENT** | — | — |
| `AC6.3.2` | — | **ABSENT** | — | — |
| `AC6.3.3` | — | **ABSENT** | — | — |
| `AC6.3.4` | — | **ABSENT** | — | — |
| `AC6.3.5` | — | **ABSENT** | — | — |
| `AC6.3.6` | — | **ABSENT** | — | — |
| `AC6.4.1` | — | **ABSENT** | — | — |
| `AC6.4.2` | — | **ABSENT** | — | — |
| `AC6.4.3` | — | **ABSENT** | — | — |
| `AC6.4.4` | — | **ABSENT** | — | — |
| `AC6.5.1` | — | **ABSENT** | — | — |
| `AC6.5.2` | — | **ABSENT** | — | — |
| `AC6.5.3` | — | **ABSENT** | — | — |
| `AC6.5.4` | — | **ABSENT** | — | — |
| `AC6.5.5` | — | **ABSENT** | — | — |
| `AC7.1.1` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.1.2` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.1.3` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.2.1` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.2.2` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.2.3` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.3.1` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.3.2` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.3.3` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.4.1` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.4.2` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.5.1` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.5.2` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.6.1` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC7.6.2` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC7.6.3` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_routes.py` | exists |
| `AC7.7.1` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC7.7.2` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC7.7.3` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC7.7.4` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC7.7.5` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC7.8.1` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.8.2` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.9.1` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.9.2` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC7.9.3` | U4 `u4-platform-packaging` | **ABSENT** | — | — |
| `AC8.1.1` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_read.py` | exists |
| `AC8.1.2` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_read.py` | exists |
| `AC8.1.3` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_read.py` | exists |
| `AC8.1.4` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_read.py` | exists |
| `AC8.2.1` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.2.2` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.2.3` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.3.1` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC8.3.2` | U1 `u1-analytics-slice` | OK | `tests/test_migration_indexes.py` | exists |
| `AC8.4.1` | U1 `u1-analytics-slice` | OK | `app/routes.py` | exists |
| `AC8.4.2` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.5.1` | U1 `u1-analytics-slice` | OK | `app/routes.py` | exists |
| `AC8.5.2` | U1 `u1-analytics-slice` | OK | `app/routes.py` | exists |
| `AC8.5.3` | U1 `u1-analytics-slice` | OK | `app/sentiment.py` | exists |
| `AC8.6.1` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.6.2` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.6.3` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.6.4` | U1 `u1-analytics-slice` | OK | `app/config.py` | exists |
| `AC8.7.1` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC8.7.2` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC8.7.3` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC8.7.4` | U1 `u1-analytics-slice` | OK | `tests/conftest.py` | exists |
| `AC8.8.1` | U1 `u1-analytics-slice` | OK | `app/routes.py` | exists |
| `AC8.8.2` | U1 `u1-analytics-slice` | OK | `app/routes.py` | exists |
| `AC8.9.1` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.9.2` | U1 `u1-analytics-slice` | OK | `app/analytics.py` | exists |
| `AC8.9.3` | U1 `u1-analytics-slice` | OK | `tests/test_analytics_read.py` | exists |

### 6.3 `NFR` — 9 ids from `requirements.md`

| `NFR` | Status in code-generation traceability | Note |
|---|---|---|
| `NFR1` | not a row | parent; covered by `NFR1.1`–`NFR1.4` (all `OK`) |
| `NFR2` | not a row | parent; covered by `NFR2.1`–`NFR2.6` (all `OK`) |
| `NFR3` | not a row | parent; covered by `NFR3.1`, `NFR3.2` (both `OK`) |
| `NFR4` | not a row | parent; covered by `NFR4.1`–`NFR4.7` (`NFR4.6`, `NFR4.7` `N/A` — see `test-results.md` §5) |
| `NFR5` | not a row | `N/A` upstream — invariant, no `NFR5.y` exists |
| `NFR6` | not a row | `N/A` upstream — invariant, no `NFR6.y` exists |
| `NFR7` | not a row | `N/A` upstream — invariant, no `NFR7.y` exists |
| `NFR8` | not a row | parent; covered by `NFR8.1`–`NFR8.3` (all `OK`) |
| `NFR9` | not a row | parent; covered by `NFR9.1`–`NFR9.4` (all `OK`) |

Note that the 26 `NFRx.y` targets in `build-and-test-summary.md` §4 and
`test-results.md` §5 are drawn from `u1-analytics-slice/nfr-requirements/`, which is the
authoritative sub-numbering. The 9 parent ids here are the inception-level set and are
covered by their children.

## 7. Findings to surface at the approval gate

1. **The literal gate cannot pass in this repository, and the reason is structural, not
   a defect of this Bolt.** Two independent causes: no `FR` id is ever a row in a
   code-generation traceability (Reason 1), and 46 `AC` ids belong to three Units that
   have not been built (Reason 2). 215 enumerated, 83 covered, 131 uncovered.
2. **`AC6.2.1` is split across two Units and is satisfied by neither alone.**
   `unit-of-work-story-map.md`'s cross-cutting table states it: *"Neither unit alone
   satisfies `AC6.2.1`; both rows ship the story."* U1 delivers the series and
   label-breakdown summary region; U3 delivers the two term-list containers. Its
   traceability row carries that note explicitly. At the walking-skeleton checkpoint,
   U1's half is demonstrable and the criterion is **not** yet fully met.
3. **`AC2.4.3` is a correct `N/A`, not a gap.** It is the only non-`OK` row in U1's scope
   and its reason is a contract fact (opaque `import_id`), not an omission.

## 8. Recommendation for this gate's future runs

The gate as specified is a *phase-boundary* check run at *unit* granularity, which
makes it unpassable on every Bolt except the last. Two options for the human, neither
of which this stage will apply on its own:

* **Scope the gate to the settled Units** — enumerate `FR`/`NFR`/`AC` only for the Units
  whose `code-generation` has settled, and report the rest as "not yet in scope".
* **Or require code-generation's traceability to carry `FR` rows**, resolving each `FR`
  transitively from its `AC`s, so Reason 1 disappears and Reason 2 becomes the only
  remaining cause — which is the honest one.

Recorded here as a Build and Test finding, surfaced at the approval gate, and **not**
acted on: changing either the gate's specification or the upstream traceability contract
is not this stage's remit.
