# Phase Check — Construction → Operation

Workflow: `261001-analytics-layer` (scope `feature`, Standard depth, Standard test
strategy, unit-major / serial / checkpoint-enabled construction).

Produced by: stage `ci-pipeline` (construction), Step 5 — Phase Boundary
Verification.

## Verdict

# ❌ FAIL — the Construction → Operation transition is STOPPED

The stage definition is unambiguous: *"If any traceability file is missing or any
unresolved finding remains, stop the Construction → Operation transition and revisit
the owning stage."*

**Both of its conditions are met.** Traceability files are missing (three of four
Units have none, because they have not been built), **and** unresolved findings
remain (the cross-Unit FR/NFR/AC gate **FAILED** as written; the Build and Test
target matrix carries **2 `Unverified`** targets; and one unit-boundary violation
is live and disclosed). **Construction is not complete and this check does not mark
it complete.**

| # | What the stage asked this check to confirm | Verdict |
|---|---|---|
| 1 | **All Units built and tested** | ❌ **FAIL** — **1 of 4** Units built |
| 2 | **All code-generation tables have no unresolved findings, and the cross-Unit FR/NFR/AC gate passed** | ❌ **FAIL** — the gate's own recorded verdict is `❌ FAIL — as written` |
| 3 | **The CI quality gates enforce the build and test commands recorded by Build and Test** | ✅ **PASS** — the only one of the three that passes |
| — | **A traceability file is missing** (stage-level `code-generation/traceability.json`; three per-Unit files) | ❌ **FAIL** — see §2 |

---

## 1. What was read

| Input | Path | Read |
|---|---|---|
| Cross-Unit FR/NFR/AC gate | `construction/build-and-test/cross-unit-traceability.md` | ✅ full |
| Per-Unit code-generation traceability | `construction/u1-analytics-slice/code-generation/traceability.json` | ✅ all 155 rows, re-read independently |
| Build and Test target matrix | `construction/build-and-test/test-results.md` §5, `build-and-test-summary.md` §4 | ✅ |
| Per-Unit code summary | `construction/u1-analytics-slice/code-generation/code-summary.md` | ✅ |
| Unit Infrastructure Design (the routing) | `construction/u1-analytics-slice/infrastructure-design/cicd-pipeline.md` | ✅ |
| Unit topology | `inception/units-generation/unit-of-work.md`, `unit-of-work-dependency.md` | ✅ |
| This stage's own gates | `construction/ci-pipeline/quality-gates.md`, `ci-config.md` | ✅ |

**This check re-derived Build and Test's arithmetic rather than accepting it**, and
reproduced it exactly:

| Set | Enumerated | `OK` in a read traceability | non-`OK` | absent from every read traceability |
|---|---|---|---|---|
| `FR` (from `requirements.md`) | **76** | **0** | 0 | **76** |
| `NFR` (from `requirements.md`) | **9** | **0** | 0 | **9** |
| `AC` (three-segment, from `stories.md`) | **130** | **83** | 1 (`AC2.4.3`, `N/A`) | **46** |
| **Total** | **215** | **83** | **1** | **131** |

Independently confirmed from the traceability file: 155 coverage rows = **152 `OK`**
+ **3 `N/A`** (`AC2.4.3`, `NFR4.6`, `NFR4.7`); **zero `FR` rows exist in any
code-generation traceability**; and **all 152 `OK` targets resolve to files that
exist on disk** (0 missing).

---

## 2. Finding 1 — Three of four Units are not built. **Owning stage: the three unbuilt Units themselves.**

`unit-of-work.md` defines four Units and this is **Bolt 1 of 4** under unit-major,
serial, checkpoint-enabled Construction (`aidlc-state.md` → Runtime State:
`Construction Checkpoints: enabled`, `Construction Iteration: unit-major`,
`Construction Execution: serial`).

| Unit | Directory | Depends on | Built? | Its `code-generation/traceability.json` |
|---|---|---|---|---|
| **U1** | `u1-analytics-slice` | — (root) | ✅ **yes** — this is the subject | **exists** — 155 rows |
| **U2** | `u2-term-extraction` | — (root) | ❌ no | **does not exist** |
| **U3** | `u3-analytics-view` | U1 | ❌ no | **does not exist** |
| **U4** | `u4-platform-packaging` | — (root) | ❌ no | **does not exist** |

**All 46 absent `AC` ids belong to those three Units** (cross-unit-traceability
§5.3):

| Owning Unit | Absent `AC` ids | Count |
|---|---|---|
| **U2** `u2-term-extraction` | `AC4.1.1`–`AC4.1.6`, `AC4.2.1`–`AC4.2.3` | **9** |
| **U3** `u3-analytics-view` | `AC6.1.1`–`AC6.1.4`, `AC6.3.1`–`AC6.3.6`, `AC6.4.1`–`AC6.4.4`, `AC6.5.1`–`AC6.5.5` | **19** |
| **U4** `u4-platform-packaging` | `AC7.1.1`–`AC7.1.3`, `AC7.2.1`–`AC7.2.3`, `AC7.3.1`–`AC7.3.3`, `AC7.4.1`–`AC7.4.2`, `AC7.5.1`–`AC7.5.2`, `AC7.8.1`–`AC7.8.2`, `AC7.9.1`–`AC7.9.3` | **18** |

This is **not** a defect of Bolt 1 — it is work that has not been built yet, in the
order `unit-of-work-dependency.md` records. It is nevertheless an unresolved finding
for the purposes of this boundary, because the stage asked whether **all** Units are
built and tested and the answer is **no**.

**The same reason removes all 9 `NFR` parent ids:** `NFR5`, `NFR6`, `NFR7` are
declared `N/A` upstream as **invariants with no sub-numberable value** (no `NFR5.y`
exists), and `NFR1`–`NFR4`/`NFR8`/`NFR9` are **parent** ids the construction stages
sub-numbered into the 26 `NFRx.y` targets — of which **24 are `OK`** and **2 are
`N/A`** (see Finding 3).

**Also absent: the stage-level `construction/code-generation/traceability.json`.**
This is **not a missing file in the sense of an omission** — the stage-level
`code-generation` was **SKIPped in favour of per-Unit runs**
(`aidlc-state.md` → `- [S] code-generation — EXECUTE`, i.e. skipped via
`--stage`/`--phase` jump; likewise `[S] functional-design` and `[S]
infrastructure-design`). `cross-unit-traceability.md` §1 records the same fact.
Recorded here so the boundary record is complete, not as a defect.

---

## 3. Finding 2 — The cross-Unit FR/NFR/AC gate FAILED as written. **Owning stage: `build-and-test`'s gate specification, plus `code-generation`'s traceability contract.**

The gate's own recorded verdict, read from its file, is:

> `# ❌ FAIL — as written` — *"215 ids enumerated, 83 covered, with two independent
> causes."*

### Cause 1 (granularity) — no `FR` id is ever a row in a code-generation traceability

**Verified independently in this check:** `u1-analytics-slice`'s `traceability.json`
carries 45 `BR`, 83 `AC` and 26 `NFR` rows — and **zero `FR` rows.**

The trace this project builds runs **`FR → AC → BR → code`**, so `FR` coverage is
necessarily *transitive*: an `FR` is covered only if the acceptance criteria of the
stories that own it are covered. §6.1 of the gate resolves each `FR` along exactly
that chain and records the result:

| Resolution | Count | `FR` ids |
|---|---|---|
| Covered, every criterion `OK` | **42** | `FR1`, `FR1.1`–`FR1.6`; `FR2.1`–`FR2.9`, `FR2.13`; `FR3`, `FR3.1`–`FR3.8`; `FR5`, `FR5.1`–`FR5.7`; `FR6.2`; `FR7.6`, `FR7.7`; `FR8.2`–`FR8.5`, `FR8.7`–`FR8.9` |
| Present but one criterion is the `N/A` `AC2.4.3` | **6** | `FR2`, `FR2.10`, `FR2.11`, `FR2.12`, `FR8`, `FR8.1` |
| **Covered in part** — some criteria `OK`, others belong to an unbuilt Unit | **5** | `FR6`, `FR7`, `FR8`, `FR8.1`, `FR8.6` (`FR8`/`FR8.1` appear in both the `N/A` and `PARTIAL` lists) |
| **No coverage at all** — every criterion belongs to an unbuilt Unit | **22** | `FR4` family (7 → U2); `FR6` family (8 → U3); `FR7` sub-family (7 → U4) |
| **Not a requirement id at all** | **1** | `FR3.9` — occurs only inside superseded Revision 1 review prose, as the label *"R-12 (`FR3.9`'s deferral list)"*; `inception/user-stories/traceability.json` already records this finding |

42 + 6 + 5 + 22 + 1 = **76**. ✔ matches the enumeration.

> **Owning stage for Cause 1: `code-generation`'s traceability contract, with the
> gate specification as the second owner.** As `cross-unit-traceability.md` §8 puts
> it: *"The literal gate — 'covered with status `OK` in at least one entry' — cannot
> be satisfied for any `FR` by the file it tells me to read, in this repository, for
> any Unit. That is a **reporting-shape gap in code-generation's traceability
> contract**, not evidence that the requirements are unimplemented."* The gate
> proposes two fixes and applies neither, correctly: scope the gate to settled Units,
> **or** require code-generation's traceability to carry `FR` rows resolved
> transitively from their `AC`s, so Cause 1 disappears and Cause 2 becomes the only
> remaining cause — *"which is the honest one."*
>
> **This check does not choose between them.** *"Changing either the gate's
> specification or the upstream traceability contract is not this stage's remit."*

### Cause 2 (sequencing) — the enumerated set is intent-wide; only Bolt 1 of 4 exists

See Finding 1. All 46 absent `AC` ids belong to U2, U3 or U4.

### The reading that is useful — and is **not** what the literal gate says

Within **U1's own declared scope** the coverage is sound: **83 of 84** `AC` ids
declared by `u1-analytics-slice`'s `functional-design` traceability are `OK`, and
**every one of their 83 target files exists on disk** (checked individually: **0
missing**). This check re-verified that existence claim independently against the
traceability file: **152 of 152 `OK` targets resolve to files that exist, 0 missing.**

**Two findings Build and Test surfaced at its own gate, restated because they bear
on the boundary:**

* **`AC6.2.1` is split across two Units and is satisfied by neither alone.**
  `unit-of-work-story-map.md`'s cross-cutting table says so outright: *"Neither unit
  alone satisfies `AC6.2.1`; both rows ship the story."* U1 delivers the series and
  label-breakdown summary region; U3 delivers the two term-list containers. **U1's
  half is demonstrable and the criterion is not yet fully met.**
* **`AC2.4.3` is a correct `N/A`, not a gap** — and it is the only one in U1's
  scope. `import_id` is pinned as an opaque string with no parse step (contract
  `UC1`), so no input can trigger a `422` naming `query.import_id`; an unmatched id
  is the `200` empty result of `AC2.4.2` / `BR4.4`. No test was written for the
  impossible `422` — correctly.

---

## 4. Finding 3 — Two measurable NFR targets are `Unverified`. **Owning stage: `u3-analytics-view`'s own code-generation and Build and Test passes.**

Build and Test's finalised matrix: **24 `Met` · 0 `Not Met` · 2 `Unverified` · 0
`N/A`** out of **26** applicable measurable targets. The stage's failure predicate
fired on the two.

| Target | Expected | Why it cannot execute in U1 | Owning Unit / stage |
|---|---|---|---|
| **`NFR4.6`** — per-section graceful degradation: a section that succeeds while another fails shows the successful section **plus a partial-failure marker** | The named instruments are **`AC6.5.3` / `AC6.5.5`**, both of which need a **second analytics section**. U1 completes the summary region end to end; the two term-list containers are U3's (`unit-of-work-story-map.md`'s cross-cutting table) | **`u3-analytics-view` (Bolt 3)** — its own `code-generation` + its own `build-and-test` |
| **`NFR4.7`** — no silent retry, and an out-of-order late response from a superseded range is **discarded** | The named instrument is **`AC6.5.2`**, which needs a **range control** to supersede. No range control exists; U3's is the deliverable | **`u3-analytics-view` (Bolt 3)** — its own `code-generation` + its own `build-and-test` |

**Neither was deferred to a validation stage, and neither can be.** `test-results.md`
§5.1 states it plainly: *"the deferral clause requires a **deployed or production-like
environment** **and** a later validation stage that explicitly owns the check. Neither
`NFR4.6` nor `NFR4.7` needs a deployed environment — they need markup and a control
that a **later Bolt of this same stage** must build. `ci-pipeline` and the Operation
stages, including `performance-validation`, own neither of them."*

**`ci-pipeline` — this stage — explicitly disclaims ownership of both.** They need a
second analytics section and a range control, which are `u3-analytics-view`'s
deliverables. `quality-gates.md` §6 records: *"**No gate is defined for either, and
none can be** until that Unit ships its markup."* Inventing a gate for markup that
does not exist would assert nothing.

**No test was invented to close them**, and Build and Test walked its full failure
ladder to rung 4 before escalating. The human was shown four impact-estimated paths
and chose **A — Accept**: carry both as `Unverified` into `u3-analytics-view`, where
`AC6.5.2` / `AC6.5.3` / `AC6.5.5` become buildable. What the acceptance supplies is
**the missing ownership rung 2 identified** — the targets now have a named owning
Unit instead of no owner at all. It does **not** reclassify either as `Met`, and the
stage's failure predicate **still fired**.

**Consequence for the boundary: these two behaviours ship unverified until Bolt 3.**
If Bolt 3 slips, they ship unverified. That risk is recorded rather than removed.

---

## 5. Finding 4 — A live U1 → U2 unit-boundary violation. **Owning stage: Delivery Planning (to fix the Bolt order), then `code-generation` for `u2-term-extraction` (to adopt the module).**

Disclosed by Code Generation (`code-summary.md` § Deviations (d), § Post-review
amendments **R-02**, **R-09**) and reported, not re-decided, by Build and Test
(`build-and-test-summary.md` §7.4).

| Fact | Source |
|---|---|
| `app/terms.py` **was authored by U1** | `code-summary.md` §R-02 |
| Three inception artifacts **forbid** it — *"term tokenisation is delegated to `u2-term-extraction` … **this unit consumes it, does not re-implement it**"* (`tech-stack-decisions.md:49`); *"U1 **does not own** the `TermExtraction` module (U2)"* (`unit-of-work.md:96`); `contract-summary.md` §4 repeats the attribution | quoted in `code-summary.md` §R-02 |
| The approved **plan step 5** told U1 to promote the tokeniser, and the plan could not sequence U2 first | `code-summary.md` §R-02: `next` substitutes the next *unsettled* Unit, and a Unit cannot be left unsettled without pausing it, which hard-stops the loop |
| `app/analytics.py:41` still holds a live `U1 → U2` import edge | `integration-test-instructions.md` §3.1 |
| `source-manifest.json` still claims `app/terms.py` and `tests/test_terms.py` | `code-summary.md` §R-02 |
| The stopword set is U2's decision (contract open point **O9**, §6), and U1 has already **chosen and test-pinned** it | `code-summary.md` §R-09 |
| U2 **must adopt**, not re-derive, and should expect to edit **three U1 manifest writes** if it decides the set differently | `code-summary.md` §R-02, §R-09 |

> **"What is actually true right now, stated without hedging"** — `code-summary.md`
> §R-02: *"`app/terms.py` was authored by U1, which the inception artifacts forbid.
> Nothing has been re-pointed. The `U1 → U2` edge was recorded as **suppressed**,
> which permitted U1 to proceed. It did not permit U1 to write U2's module, and U1
> did. Until U2 runs, the binding recorded in `unit-of-work.md:96` is violated, and
> this note is the disclosure rather than a claim of compliance."*

**Owning stage, and the honest answer about reachability.** The correct order —
deliver `u2-term-extraction` **before** U1's terms path — is *"not reachable from
inside the current engine state"* and needs **a Delivery Planning re-run** to move
the Bolt sequence, replaying Bolt 1 forward with fresh reviews. That is
`code-summary.md`'s explicit statement, and this check does not contradict it.
**Until then the binding is violated, and the disclosure is not a claim of
compliance.**

---

## 6. Finding 5 — The recorded verification command still fails its first step. **Owning stage: Delivery Planning (it is a human-approved artifact) — decision pending with the human.**

| Fact | Source |
|---|---|
| `verification-command.txt` step 1 is `python -m pip install -e ".[dev]"`, which **exits 1** with PEP 668 `externally-managed-environment` on this host's externally-managed `/usr/bin/python3.14` | `test-results.md` §3.2, `build-instructions.md` §2.2 |
| **Proven pre-existing** — identical failure on a pristine clone of `HEAD` `aa0b1e4` with none of this Unit's writes present. The baseline would have failed the same way. | `test-results.md` §3.2 |
| Steps 2 and 3 **pass verbatim** — 192 passed / 97.06 %, then `{"mode":"offline","connected":false,…}` | `test-results.md` §1 |
| Both remedies execute successfully: a venv (**exit 0**, suite green inside it) and `--break-system-packages` (**exit 0** dry-run — every dependency already satisfied, so the block is purely the write refusal) | `build-instructions.md` §2.3 |
| **No quality target is `Unverified` because of it** — no target's instrument is *"`pip install -e ".[dev]"` exits 0 against the system interpreter"* | `build-instructions.md` §2.4 |
| Build and Test's option D — rewrite the command to use a venv — **was not taken**, because it edits a **human-approved** Delivery Planning artifact | `test-results.md` §6, Halt-and-ask resolution |
| **It is not treated as a pass.** *"Option D remains open and undone."* | `test-results.md` §6 |

**Recorded rather than absorbed.** The remedy exists and is proven, so this blocks
nothing downstream; but the human-approved artifact still exits 1 on every
externally-managed host, and this check will not present a documented remedy as a
green step. Carried as **`ci-pipeline-questions.md` Q6**, open, with three
impact-estimated options.

---

## 7. Finding 6 — No gate in this project runs automatically, and the `feature` scope's CI requirement is therefore unsatisfied. **Owning stage: the human (`Q1`, the repository-hosting decision) and `u4-platform-packaging` (`FR7.2`).**

Not a traceability finding, but it belongs in the boundary record because it changes
what "the gates passed" can mean.

| Fact | Source |
|---|---|
| `memory/org.md` § Testing Posture: for `mvp`, `enterprise`, `feature`, `infra`, `classic` — *"add an 80 % line-coverage floor and **CI execution before merge**."* The active scope is **`feature`**. | `aidlc-state.md` → Scope: `feature` |
| **There is no CI and no git remote.** `git remote -v` is empty; no `.github/`, `.gitlab-ci.yml`, `Jenkinsfile`, `buildspec.yml`, `.circleci/`, `azure-pipelines.yml`. | measured in this stage; `memory/team.md` § Way of Working, § Deployment |
| Therefore **every gate in `quality-gates.md` is executed by a human in a terminal.** Nothing blocks anything automatically. | `ci-config.md` §1.1 |
| `memory/team.md` § Enforcement Summary: *"An unrun gate is not a gate; a documented default is not enforcement."* | quoted |
| The scope-level requirement is **narrower than "CI must be the enforcement mechanism"** — it says *CI execution before merge*. `FR7.2` explicitly makes a platform-neutral script, *"not a provider CI job,"* the thing that runs the standing gates. | `requirements.md` `FR7.2` |

**Reading.** The 80 % floor is satisfied (**97.06 %**). The **CI execution** half is
**currently unsatisfiable**, not waived: no remote exists, so nothing can trigger a
job. It becomes satisfiable the day a remote exists, which is
`ci-pipeline-questions.md` Q1 — a human decision this stage takes no position on.

**What is real today** is the standing verification command: install → `pytest -q`
→ boot real `uvicorn` on `127.0.0.1:8141` and read `/v1/health`. That is J1, J6 and
J9, and it is a genuine end-to-end gate a human runs before every squash-merge.

---

## 8. The one check that PASSES — and it is this stage's own

> **Check 3: "Confirm the CI quality gates enforce the build and test commands
> recorded by Build and Test." → ✅ PASS.**

This check is not self-serving; it is the one item the stage definition asks that
this stage is actually positioned to answer. It was verified command by command
against `test-results.md` §1 and §2, `build-and-test-summary.md` §1.1,
`build-instructions.md` §4–§6, and the three `*-test-instructions.md` files.

| Command Build and Test recorded | Gate | Executed again in this stage | Result |
|---|---|---|---|
| `python -m compileall -q app tests` (§1.1 row 2) | G1 | ✅ | **exit 0** |
| `python -m ruff check app tests` (§1.1 row 3) | G2 | ✅ | **`All checks passed!`, exit 0** |
| `python -m ruff format --check app tests` (§1.1 row 4) | G3 | ✅ | **`30 files already formatted`, exit 0** |
| `python -c "import app.main …"` (§1.1 row 5) | G7 | ✅ | `very-cool-sentiment-analysis /v2 ['/v2/analytics/summary', '/v2/analytics/terms']` |
| `python -m pytest -q` — whole suite (§1.1 row 6) | G4, G5, G6, G11, G12, G13, G14 | ✅ twice — host interpreter **and** the J1 venv | **192 passed / 0 failed / 0 skipped / 0 errors / 0 warnings, 1.67 s, 884 stmts / 26 missed / 97.06 %**, exit 0 |
| `python -m pytest -q <integration selection> --no-cov` (§1.1 row 8) | *(not a gate — recorded)* | not re-run; **deliberately not used as a gate** | 53 tests, exit 0 |
| recorded command step 3 — real `uvicorn` on `127.0.0.1:8141` → `/v1/health` (§1.1 row 10) | G8 | not re-run here | exit 0, `{"mode":"offline",…}` |
| `security-test-instructions.md` §3.1 static checks (§1.1 row 11) | G9 | — | **`STATIC CHECKS PASSED`, exit 0**; **file not in the repository** |
| `security-test-instructions.md` §3.2 DAST probe (§1.1 row 12) | G10 | — | **`DAST PROBE PASSED`, exit 0**; **file not in the repository** |
| `python -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"` (§1.1 row 1b, Remedy A) | J1 prerequisite | ✅ environment present, `.venv/bin/python -V` → 3.14.7 | recorded **exit 0** |
| `python -m pytest -q <per-unit selection> --cov-fail-under=0` (§1.1 row 7) | *(not a gate — recorded)* | not re-run; **deliberately not used as a gate** | 67 passed / 66 % / exit 0 |

**Every gate in `quality-gates.md` traces to a command Build and Test actually
executed and recorded. No gate was invented.**

**Three gates are defined but cannot run, and that is recorded rather than hidden:**
G9 and G10 (their instruments are heredocs inside
`security-test-instructions.md`, never committed — owned by
**`u4-platform-packaging`**), and the **coverage-delta gate**, which is *unbuildable*
rather than merely absent: `pyproject.toml` configures **no machine-readable output
at all** — no `--junit-xml`, no coverage XML, no `-ra` — so there is no artefact to
diff against a previous run. `memory/team.md` calls that *"the first gate of the
standard quality-gate set"* and states it *"is currently unbuildable."* Full table
with owners: `quality-gates.md` §5.

**Honouring the unit's routing.** `u1-analytics-slice`'s Infrastructure Design
deliberately designed **no** pipeline and routed the work here
(`cicd-pipeline.md` §3: *"The full build → test → security-scan → deploy pipeline —
The CI Pipeline stage (`ci-pipeline`) … The stage that owns pipeline design is where
a pipeline belongs; duplicating it here would create two sources of truth for one
pipeline."*). **That routing is honoured, not contradicted:** `ci-config.md` §9
duplicates none of `u4-platform-packaging`'s deliverables and names the intended
convergence — when `FR7.2`'s script lands, J1–J9 become **arguments to it** rather
than a parallel copy of its body.

---

## 9. Unresolved findings — owner per item

| # | Unresolved finding | Named owning stage | Blocking the transition? |
|---|---|---|---|
| **U1** | **U2, U3 and U4 are not built** — 46 `AC` ids, 22 `FR` ids with no coverage, and 3 missing per-Unit `traceability.json` files | **`u2-term-extraction`, `u3-analytics-view`, `u4-platform-packaging`** — each Unit's own `code-generation` + `build-and-test` | **Yes** |
| **U2** | **The cross-Unit FR/NFR/AC gate FAILED as written** — 215 enumerated, 83 covered, 131 uncovered | **`build-and-test`** (gate specification) **and `code-generation`** (the traceability contract carries no `FR` rows). §8's two options: scope the gate to settled Units, **or** require `FR` rows resolved transitively. **Not this stage's to choose** | **Yes** |
| **U3** | **`NFR4.6` `Unverified`** — per-section graceful degradation; needs a second analytics section (`AC6.5.3` / `AC6.5.5`) | **`u3-analytics-view`** (Bolt 3) — its own `code-generation` + `build-and-test`. Accepted as debt by the human. **Not** a validation stage, so it cannot be deferred to Operation | **Yes** |
| **U4** | **`NFR4.7` `Unverified`** — no silent retry; out-of-order response discarded; needs a range control (`AC6.5.2`) | **`u3-analytics-view`** (Bolt 3) — same. Accepted as debt by the human | **Yes** |
| **U5** | **Live U1 → U2 unit-boundary violation** — `app/terms.py` authored by U1 against three inception artifacts; the `U1 → U2` import edge is live; the stopword set was chosen and pinned by U1 though `O9` assigns it to U2 | **`Delivery Planning`** — a re-run to move the Bolt order is the only reachable fix (`code-summary.md` §R-02: *"not reachable from inside the current engine state"*), then **`code-generation` for `u2-term-extraction`** to adopt the module and own the set | **Yes** |
| **U6** | **`AC6.2.1` is satisfied by neither Unit alone** — *"Neither unit alone satisfies `AC6.2.1`; both rows ship the story"* (`unit-of-work-story-map.md`) | **`u3-analytics-view`** (the two term-list containers) | **Yes** |
| **U7** | **The recorded verification command's step 1 exits 1** on externally-managed hosts; the human declined the rewrite (option D) | **The human**, via **`Delivery Planning`** — it is a human-approved artifact. `ci-pipeline-questions.md` Q6 | No — remedied and proven, but **not treated as a pass** |
| **U8** | **No gate runs automatically**; the `feature` scope's *"CI execution before merge"* is unsatisfiable with no remote | **The human** (`ci-pipeline-questions.md` Q1 — the repository-hosting decision, which every provider option is downstream of) **and `u4-platform-packaging`** (`FR7.2`, which lands the script any CI job would then call) | No — but recorded so the requirement is not silently dropped |
| **U9** | **`G9` and `G10` cannot run** — both instruments are heredocs inside `security-test-instructions.md`, never committed | **`u4-platform-packaging`** — as repository files, invoked from `FR7.2`'s script (G9 check 6 also overlaps `FR7.3`'s secret scan) | No — the jobs and commands are specified; only the files are missing |
| **U10** | **The coverage-delta gate is unbuildable** — no `--junit-xml`, no coverage XML, no `-ra`; no artefact to diff | **`u4-platform-packaging`** alongside `FR7.2`, or a **`code-generation`** pass over `pyproject.toml`. Needs no new dependency | No |
| **U11** | **`FR7.1` / `FR7.2` / `FR7.3` / `FR7.4` / `FR7.5` / `FR7.8` / `FR7.9` have no coverage at all** — 18 of the 46 absent `AC` ids are U4's, and the dependency audit (`FR7.3`) is unbuildable *before* the lockfile (`FR7.1`) exists | **`u4-platform-packaging`** | **Yes** (it is a cause of U1) |

**Nine blocking findings, two non-blocking.** The blocking set is not a judgement
this check made about severity; it is what the stage definition's predicate
produces: *unresolved findings remain*.

---

## 10. What the standing gates actually measured

Recorded so that "the gates passed" is never read as more than it is.

| Measure | Value | Verdict |
|---|---|---|
| Test suite | **192 passed / 0 failed / 0 skipped / 0 errors / 0 warnings**, 1.67 s | **Met** |
| Whole-application line coverage (`source = ["app"]`) | **97.06 %** — 884 statements, 26 missed | **Met**, 17.06 points of headroom over the affirmed 80 % floor, which is stated twice in `pyproject.toml` |
| Branch coverage | **off by affirmed decision** (2026-10-02); 98 branches, 3 partial, none visible to a line floor | Disclosed cost, not a failure |
| Lint (`ruff check app tests`) | `All checks passed!` | **Met** |
| Format (`ruff format --check app tests`) | `30 files already formatted` | **Met** |
| Import / assembly smoke | `/v2 ['/v2/analytics/summary', '/v2/analytics/terms']` | **Met** |
| Runtime smoke (real `uvicorn`, `127.0.0.1:8141`) | `{"mode":"offline","connected":false,"reason":"Not connected to OpenRouter."}` | **Met** |
| Static security checks | `STATIC CHECKS PASSED` (5 named findings on a deliberately broken copy — **teeth proven**) | **Met** — but the file is not in the repository |
| DAST probe (40 injection probes + 5 refusal shapes + read-only + loopback) | `DAST PROBE PASSED`, never a 500, 0 error-text leaks | **Met** — but the file is not in the repository |
| Latency budget over 10,000 rows / 365 UTC days | summary **15.24 ms**, terms **25.04 ms** vs a 200 ms budget | **Met** — a single cold measurement on one machine, **not** a percentile |
| Measurable NFR targets | **24 `Met` / 0 `Not Met` / 2 `Unverified` / 0 `N/A`** of 26 | **Not clean** — U3, U4 |
| Dependency resolution stability | **no lockfile**; system `ruff` 0.16.9 vs fresh-venv `ruff` 0.16.10, suite green under both | **Gap** — the suite's pass/fail state is a function of the resolved dependency set, not of the code |
| Unit-boundary compliance | `app/terms.py` authored by U1 against three inception artifacts | **Gap** — U5 |

**Nothing above was weakened to make a step pass.** `pyproject.toml` and `app/` are
byte-identical to the Bolt 1 commit (`git diff --stat HEAD -- pyproject.toml app/` is
empty). The 80 % floor, the `dev` extra and the two-package runtime declaration are
untouched. No test was invented to close an `Unverified` target.

---

## 11. Overall

**Construction is not complete. The transition to Operation is STOPPED and is not
recommended on this record.**

Of the stage definition's three confirmations, **two fail** — only 1 of 4 Units is
built and tested, and the cross-Unit FR/NFR/AC gate's own recorded verdict is
`❌ FAIL — as written`. **Eleven unresolved findings are itemised in §9, each with a
named owning stage.** Nine are blocking.

This check does **not** mark Construction complete, does **not** reclassify any
`Unverified` verdict, and does **not** choose between the two fixes `build-and-test`
proposed for its own gate — all three would be overreach for a stage whose remit is
pipeline design.

**The correct next actions, in order:**

1. **Continue the Bolt sequence** — `u2-term-extraction` (which also **adopts**
   `app/terms.py` and owns the stopword set), then `u3-analytics-view` (which
   clears `NFR4.6`, `NFR4.7` and the `AC6.2.1` half), then
   `u4-platform-packaging` (which clears the 18 absent `FR7.*` `AC`s and lands the
   files G9/G10 and the `FR7.2` script need). On a unit-major serial run, **the
   Construction → Operation transition is only meaningful after Bolt 4.**
2. **A Delivery Planning re-run** to move `u2-term-extraction` ahead of U1's terms
   path — the only reachable fix for U5, per `code-summary.md` §R-02.
3. **A human decision on `FR7.3`'s tool choices and the `Q6` verification-command
   rewrite**, both impact-estimated and both recorded as not taken.

**One caveat on Cause 1 of Finding 2, so this record does not overstate the failure.**
The literal gate cannot pass in this repository **for any Unit, ever**, as
currently specified — because no `FR` id is a row in the file the gate is told to
read. That is a **reporting-shape gap**, not evidence that the requirements are
unimplemented: 42 `FR` ids are covered with every criterion `OK`, and all 83 of U1's
`OK` `AC` targets exist on disk. The honest reading is that **Cause 1 is a defect in
how coverage is reported and Cause 2 is real unfinished work** — which is precisely
the resolution `cross-unit-traceability.md` §8 recommends, and why the gate names
Cause 2 *"the honest one."* Recording both keeps the failure from being attributed
to the wrong cause.

Human approval of this phase check: ☐ approved  ☐ changes requested

**Approval is not recommended on the current record.** The verdict above is
advisory for the human's decision; it does not advance the workflow, and nothing
here should be read as having advanced it.