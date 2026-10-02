# Security Requirements — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-requirements` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Review artifact.** This is the file the `aidlc-architecture-reviewer-agent` is
> assigned for this stage.
>
> **Source of truth.** Every requirement below derives from inception `NFR2`
> (egress, parameter binding, loopback, credentials) or from the constraint
> register (`C-5`, `C-10`, `C-11`) and the affirmed project/team rules. None is
> invented here. Detailed requirements carry their inception parent id plus a
> sub-number and name their **measuring instrument**.

## Authentication and authorization

| ID | Requirement | Measuring instrument | Source |
|---|---|---|---|
| **NFR2.1** | The analytics endpoints add **no authentication and no authorization** and change none of the existing posture: the app stays loopback-only and unauthenticated by design, exactly as `NFR2`/`C-10` require. Any non-loopback bind, hosted deploy or change to the authentication posture requires a fresh threat model and is out of scope. | The loopback-enforcement test of `NFR2.4` proves the process cannot serve a non-loopback interface; the existing suite staying green proves the posture is unchanged — `BR4.7` governs the `/v1` surface (it scopes to `/v1` routes, response shapes, the envelope and the client interface), while the unversioned `/auth/*` routes are governed by `BR6.6` (real served values, armed offline guard, suite green). | `NFR2`; `C-10`; `BR4.7` (`/v1`); `BR6.6` (`/auth/*`); team mandate "keep the app localhost-only" |

There is no user model, no role model and no per-endpoint authorization in this
system. Stating that explicitly is the requirement: the correct posture for this
unit is the *absence* of a new auth mechanism, not the addition of one.

## Egress and data protection

| ID | Requirement | Measuring instrument | Source |
|---|---|---|---|
| **NFR2.2** | There is **no new egress path of any kind**: the analytics read path computes every aggregate in-process from locally stored rows. The analytics code imports no HTTP client, opens no socket, calls no sentiment engine, and adds no credential to any code path, response body, log record or artifact. | Import/static inspection of the new analytics modules (no `urllib`, no `socket`, no HTTP-client import, no engine call), reinforced by the session-scoped offline guard armed across the suite (`FR8.5`) — a socket call would raise, so the suite itself is the instrument as well as the assertion. The `TID251` `banned-api` lint entries (`FR7.5`) make a forbidden import a lint failure. | `NFR2`; `C-5`; `C-9`; `BR2.8`; project rule "never introduce a new external service … network call" |
| **NFR2.3** | **All SQL is parameter-bound.** No value reaches a statement by string interpolation or concatenation; every statement uses `?` placeholders. | Code inspection of the read module and route (`BR2.9`) plus the `ruff` `S` security rules selected in `pyproject.toml`, which flag unsafe SQL construction patterns; the repository convention is asserted by the existing suite's parameter-bound-only style and the new statements inherit it. | `NFR2`; `BR2.9`; team convention "SQL: parameter-bound only" |
| **NFR2.4** | **The loopback bind is enforced at startup.** A non-loopback host fails loudly rather than serving; a documented `uvicorn` default is not enforcement, and the `HOST` constant is the value the run path actually consumes. | The startup-enforcement test (`FR7.6`): supplying a non-loopback host must make startup fail with an explanation; the loopback run path remains the normal local run. `BR6.5` requires the constant be what the run path consumes, so a test that only asserts the constant's value is insufficient. | `NFR2`; `FR7.6`; `BR6.5`; `C-10`; team mandate "enforce the loopback bind at startup" |
| **NFR2.5** | **No credential is added anywhere.** No real credential appears in any code path, response body, log record or artifact. The analytics endpoints read local rows and require no key; live-mode credentials (the OpenRouter key) never reach the analytics path. | The instruments that exist **in this unit today**: (a) the existing suite's redaction assertions (`reprs`, `record.__dict__`, `/`, `/health`, `/auth/status` bodies) stay green, proving no credential reaches a response or log record; (b) the analytics response schemas carry no credential field (`contract-summary.md` §2 "no response body carries credential material"); (c) the session-scoped offline guard (`FR8.5`) is armed across the suite, so a credential-exfiltrating call would raise. **Cross-unit dependency (not this unit's instrument):** the secret-scanning gate affirmed by `FR7.3` does **not exist yet** — `team.md` records "no secret scanner, no dependency audit, no CI", and `tech-stack-decisions.md` records the scanner as a `u4-platform-packaging` obligation. It is named here only as a dependency on `u4-platform-packaging`; it is not a measuring instrument available to `u1` now. | `NFR2`; `C-11`; `FR7.3` (scanner — owned by `u4-platform-packaging`); project rule "never commit, log, print, paste, or attach a real credential" |

## Threat considerations

The trust model is unchanged and must be read whole, so a later stage does not
mistake an accepted low risk for an open finding.

| # | Threat / question | Disposition for this unit | Source |
|---|---|---|---|
| **T1 — New attack surface from `/v2` reads** | The two endpoints are read-only `GET`s, loopback-only, unauthenticated by design, and computed in-process. They add no write surface (`NFR3`), no egress (`NFR2.2`) and no credential handling (`NFR2.5`), so the new surface is a limited read of data the same operator already wrote. | `NFR2.1`, `NFR2.2`; `BR2.7`; `BR2.8` |
| **T2 — SQL injection through `from`/`to`/`import_id`/`limit`** | Refused at the boundary: malformed values are rejected before computation (`BR4.2`, `BR2.6`), and every statement is parameter-bound (`NFR2.3`). No parameter is interpolated into statement text — the same rule that governs the log record (`NFR8`). | `NFR2.3`; `BR2.9` |
| **T3 — Data exposure through the response** | The response carries aggregates over rows the operator already owns, on a loopback surface. No credential, no raw text and no PII field is added: terms are derived tokens, not stored text (`AnalyticsTermList`). `resolved_range` is deliberately not serialised (`contract-summary.md` UC3). | `contract-summary.md` §2; `entities.md` |
| **T4 — Data-at-rest and privacy obligations** | `C-9` records that stored text may be personal data. This unit adds **no new egress** and **no retention/delete path** (both out of scope). The analytics read touches the existing store only, so it neither widens exposure nor introduces a new transfer. Restated here so a reader sees the obligation was considered, not ignored. | `NFR2`; `C-9`; `requirements.md` Out of Scope |
| **T5 — Non-loopback exposure of the unauthenticated app** | The principal risk this unit could introduce (a bind that exposes an unauthenticated app holding the operator's key) is closed by enforcement at startup rather than by a documented default. | `NFR2.4`; `BR6.5`; `FR7.6` |

## Compliance

| ID | Requirement | Measuring instrument | Source |
|---|---|---|---|
| **NFR2.6** | The change stays within the project's privacy and localhost-only rules: no new egress (`NFR2.2`), loopback enforced (`NFR2.4`), no credential committed, logged, printed or pasted (`NFR2.5`). The `LICENSE` obligation (`FR7.4`) and the lockfile/audit obligations (`FR7.1`, `FR7.3`) are repository-level and owned by the packaging unit, not this one; this unit adds no dependency and so triggers no new licence or audit surface. | The packaging unit's gates (`FR7.1`–`FR7.4`); this unit's instrument is that the declared runtime dependency list is unchanged — `tests/test_config.py`'s dependency-cap assertion (`C-6`) stays green, proving no third runtime dependency was declared. | `NFR2`; `C-5`, `C-9`, `C-10`, `C-11`; `FR7.1`–`FR7.4` |

## Cross-reference — the read-only guarantee is reliability, not security

`NFR3` (read-only; no write, schema change or access bookkeeping) has a security
*flavour* but is owned by **`reliability-requirements.md`** (`NFR3.1`), because its
subject is the correctness guarantee of a `GET`, not an access-control boundary.
It is cross-referenced here so the reviewer sees it was not dropped, and not
duplicated so the two files cannot drift.
