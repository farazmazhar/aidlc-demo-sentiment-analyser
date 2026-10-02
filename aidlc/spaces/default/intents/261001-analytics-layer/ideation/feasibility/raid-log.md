# RAID Log

## Risks

| ID | Risk | Likelihood | Impact | Treatment | Source |
|----|------|-----------|--------|-----------|--------|
| R-1 | The project has no migration mechanism; an additive, idempotent migration is net-new work rather than a pattern to copy | Medium | Medium | Mitigate: pin the migration approach in Requirements Analysis and Design before building | [Q7] [desc] |
| R-2 | The soft one-session timeline is optimistic against the full `feature` scope (33 stages) | Medium | Low | Accept: the target is explicitly soft, not a fixed deadline | [Q4] |
| R-3 | Raw submitted/imported text may be personal data, stored unencrypted with no retention or delete path; the analytics layer raises the value of the stored corpus | Medium | Medium | Mitigate within existing posture: analytics adds no new egress path; any retention/delete work is pre-existing and out of scope unless elected | [Q2] |
| R-4 | New tests must stay fully offline (no network, no key) while the existing suite remains green | Low | Medium | Mitigate: reuse the existing dummy-client and offline-test patterns | [desc] |

## Assumptions

| ID | Assumption | Status | Source |
|----|------------|--------|--------|
| A-1 | The existing `/v1` JSON conventions and the single error envelope can be reused unchanged for the new `/v2` endpoints | hypothesis — to confirm in Requirements Analysis | [Q1] [desc] |
| A-2 | The most frequent "significant terms" can be extracted with a simple in-process tokenizer and no external service | hypothesis — definition of "significant" still open | [desc] |
| A-3 | The second page/section can be rendered with the existing static assets and no front-end library | hypothesis — native-HTML precedent from prior work | [desc] |

## Issues

| ID | Issue | Status | Source |
|----|-------|--------|--------|
| I-1 | The biggest technical uncertainty was not yet defined by the user; the migration, term extraction, and offline rendering remain named unknowns | Open | [Q7] |
| I-2 | The stored schema version is written but never compared, and a schema change is today handled by recreating the local database — there is no migration runner | Open | [desc] |

## Dependencies

| ID | Dependency | Status | Source |
|----|------------|--------|--------|
| D-1 | The additive migration must not disturb existing rows or the existing column/`CREATE TABLE` contract | Open | [Q1] [desc] |
| D-2 | The stored analyses, and any CSV-import `import_id` values, are the data source; the endpoints depend on their existing shape | Open | [desc] |
| D-3 | The existing offline test suite (no network, no key) must remain green | Open | [desc] |
