# Cross-Unit Final Coverage Gate — `u1-application`

Stage-level gate for Build and Test. Enumerates every `FR` and `NFR` from
`inception/requirements-analysis/requirements.md`, every three-segment `AC` from
`inception/user-stories/stories.md`, and checks each against the traceability artifacts:
`construction/u1-application/code-generation/traceability.json` (the only unit in this workflow).

## Method

- **FR and NFR IDs** are enumerated from `requirements.md`.
- **AC IDs** are enumerated from `stories.md` (44 in total).
- A unit's coverage entry with status `OK` counts as covered; `N/A` counts only for the two targets
  the requirements explicitly record as deliberate absences (`NFR-P3`, `NFR-SC1`).

## Functional requirements (29)

All 29 FR IDs are referenced by the user stories in `stories.md`
(`FR1.1`–`FR1.6`, `FR2.1`–`FR2.4`, `FR3.1`–`FR3.6`, `FR4.1`–`FR4.7`, `FR5.1`–`FR5.4`, `FR6.1`–`FR6.2`).
Each FR's acceptance criteria are covered `OK` in the unit traceability table (see the AC section
below), so every FR is covered **transitively** through its story/AC.

| FR group | FR IDs | Owning Unit | Covered | Evidence |
|---|---|---|---|---|
| FR1 Configuration & engine selection | FR1.1–FR1.6 | u1-application | yes (via US1.x ACs) | app/config.py, app/service.py, tests/test_config.py |
| FR2 Engine contract | FR2.1–FR2.4 | u1-application | yes (via US3.x ACs) | app/sentiment.py, app/openrouter_client.py, tests/test_live_client.py |
| FR3 Persistence | FR3.1–FR3.6 | u1-application | yes (via US4.x/US7.x ACs) | app/db.py, app/models.py, app/repository.py, tests/test_db.py |
| FR4 HTTP surface & page | FR4.1–FR4.7 | u1-application | yes (via US2.x/US4.x/US5.x ACs) | app/routes.py, app/static/*, tests/test_routes.py, tests/test_page.py |
| FR5 Live-engine sign-in | FR5.1–FR5.4 | u1-application | yes (via US5.x/US6.x ACs) | app/session_auth.py, tests/test_session_auth.py, tests/test_auth_routes.py |
| FR6 Code-level convergence | FR6.1–FR6.2 | u1-application | yes (via US1.2 ACs) | app/dummy_client.py, app/openrouter_client.py, app/main.py |

**Recorded structural note (not a failure):** the per-stage `traceability.json` shape carries
`AC`/`BR`/`NFR` IDs, not bare `FR` IDs, so no stage-level traceability entry names an `FR` directly.
The mechanical FR check therefore resolves through `stories.md` (FR → story → AC) rather than through
a direct FR row. No FR is left without a story or without covered ACs; the gap is in the id shape the
traceability artifacts use, recorded here so the reader can see it.

## Non-functional requirements

Top-level NFRs from `requirements.md`:

| ID | Covered | Evidence |
|---|---|---|
| NFR1 Offline-first | OK | NFR1.1, NFR1.2 (app/service.py, tests/conftest.py) |
| NFR2 Secret containment | OK | NFR2.1, NFR2.2 (app/config.py, app/session_auth.py) |
| NFR3 Dependency weight | OK | NFR3.1, NFR3.2 (pyproject.toml) |
| NFR4 Test coverage & cadence | OK | NFR4.1, NFR4.2 (pyproject.toml, tests/conftest.py) |
| NFR5 Local-only operation | OK | NFR5.1, NFR5.2 (app/main.py) |
| NFR6 Observable mode | OK | NFR6.1, NFR6.2, NFR6.3 (app/service.py, app/config.py) |

Detailed and derived NFRs (from the unit's `nfr-requirements`/`nfr-design` chain), all present `OK`
in the unit traceability table:

`NFR1.1`, `NFR1.2`, `NFR2.1`, `NFR2.2`, `NFR3.1`, `NFR3.2`, `NFR4.1`, `NFR4.2`, `NFR5.1`, `NFR5.2`,
`NFR6.1`, `NFR6.2`, `NFR6.3`, `NFR-S1`, `NFR-SC2`, `NFR-SC3`, `NFR-P1`, `NFR-P2`, `NFR-R1`, `NFR-R2`,
`NFR-R3`, `NFR-TS1`, `NFR-TS2` — all `OK`.

Deliberate absences recorded `N/A` with justification: `NFR-SC1`, `NFR-P3`.

## Acceptance criteria (44)

All 44 AC IDs from `stories.md` are covered `OK` in
`construction/u1-application/code-generation/traceability.json`:

`AC1.1.1`–`AC1.1.3`, `AC1.2.1`–`AC1.2.3`, `AC2.1.1`–`AC2.1.3`, `AC2.2.1`–`AC2.2.3`,
`AC3.1.1`–`AC3.1.3`, `AC4.1.1`–`AC4.1.4`, `AC5.1.1`–`AC5.1.4`, `AC5.2.1`–`AC5.2.3`,
`AC5.3.1`–`AC5.3.3`, `AC6.1.1`–`AC6.1.5`, `AC7.1.1`–`AC7.1.4`, `AC8.1.1`–`AC8.1.3`,
`AC9.1.1`–`AC9.1.3`. Each entry's target is an existing workspace-relative implementation or test
file; the `traceability` sensor reports 0 gaps, 0 orphans and 0 invalid targets over the full set.

## Verdict

**PASS.** Every acceptance criterion and every NFR is covered; every FR is covered transitively
through its user stories and their covered ACs. No element is uncovered. The one structural note
(FR IDs not carried directly by the traceability artifacts) is recorded above and is not an execution
gap.
