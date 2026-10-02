# Security Design — `u1-analytics-slice`

> **Intent:** `261001-analytics-layer` · stage `nfr-design` (construction) ·
> unit `u1-analytics-slice` (kind `service`).
>
> **Review artifact.** This is the file the `aidlc-architecture-reviewer-agent` is
> assigned for this stage.
>
> **Upstream inputs.** `nfr-requirements/security-requirements.md` (`NFR2.1`–`NFR2.6`,
> the T1–T5 threat dispositions, and the cross-reference that `NFR3` is reliability
> not security), `nfr-requirements/observability-requirements.md` (`NFR8.3` — the
> log-side half of the same parameter-binding rule), the functional design
> (`rules.md` `BR2.7`, `BR2.8`, `BR2.9`, `BR4.1`–`BR4.3`, `BR4.5`, `BR4.6`,
> `BR6.5`; `functional-spec.md` Workflows 1–3), the contracts
> (`contract-summary.md` §2 C1 — the frozen `{code, message}` envelope and
> `STORAGE_FAILURE`; §4 C3; §8 UC1), the component catalogue and ADRs
> (`components.md` `HTTP API Surface`, `Configuration and Settings`,
> `AnalyticsRead`; `decisions.md` ADR-003, ADR-006, ADR-008, ADR-009), and the
> affirmed rules in `memory/project.md` (localhost-only; the four NEVER/ALWAYS
> mandates) and `memory/team.md` (§Deployment). Accepted assessment:
> `nfr-design-questions.md` Q1 option A.
>
> **This is a design artifact.** It states architectural patterns, strategies and
> decisions, not implementation.

## Security posture in one paragraph

This unit adds **no new security mechanism**, and that absence is the design. The
app stays **loopback-only and unauthenticated by design** (`NFR2.1`, `C-10`, the
affirmed "ALWAYS keep the app localhost-only"). The two new endpoints are
read-only `GET`s over data the operator already owns, computed in process, with
**no new egress** (`NFR2.2`), **no credential** (`NFR2.5`) and **parameter-bound
SQL** (`NFR2.3`). The one real change to the security posture is a hardening: the
**loopback bind is now enforced at startup** (`NFR2.4`), not merely documented —
this is the design's central security contribution and it closes threat T5.

## 1. Authentication and authorization

**Design decision: add none, and state the absence explicitly.** There is no user
model, no role model and no per-endpoint authorization in this system. The correct
posture for this unit is the *absence* of a new auth mechanism, not the addition
of one (`security-requirements.md` §Authentication and authorization).

| Aspect | Design | Why |
|---|---|---|
| Authentication | Unchanged: the app is unauthenticated by design (`NFR2.1`). | It serves one operator on loopback; there is no identity to authenticate. |
| Authorization | None; both `/v2` reads are open to any loopback caller. | The data is rows the same operator wrote; there is no privilege boundary to enforce. |
| Posture change | Any non-loopback bind, hosted deploy, or change to the auth posture requires a fresh threat model and is **out of scope**. | Affirmed team rule (`NFR2.1`, `C-10`); the design records the boundary rather than silently widening it. |

The design deliberately does **not** introduce a token, an API key check, a CORS
policy or a CSRF token: each would be a mechanism with no threat to defend on a
loopback, unauthenticated, single-operator surface, and the affirmed rules forbid
widening the surface to justify one.

## 2. Egress and data protection (the zero-egress invariant)

**Design decision: no new egress path of any kind.** The analytics read path
computes every aggregate in-process from locally stored rows (`BR2.8`). This is
enforced by construction and by the environment, not by convention alone.

| Control | Design | Instrument / enforcement |
|---|---|---|
| No outbound client | The analytics modules import no HTTP client, no socket, no `urllib`; they call no sentiment engine. | Import/static inspection (`NFR2.2`); `TID251` banned-api lint entries make a forbidden import a lint failure (`FR7.5`). |
| No socket reachable at test time | The session-scoped offline guard is armed across the suite, so a socket call raises. | `FR8.5`; the guard's arming is itself proved by a test. |
| No credential on the path | Live-mode credentials (the OpenRouter key) never reach the analytics path; no analytics code path, response body, log record or artifact carries a credential. | Response schemas carry no credential field (`contract-summary.md` §2); existing redaction assertions (reprs, `record.__dict__`, `/`, `/health`, `/auth/status` bodies) stay green (`NFR2.5`). |
| At-rest / privacy | `C-9`: stored text may be personal data. This unit adds no new egress and no retention/delete path; it reads the existing store only. | Restated so the obligation is seen considered, not ignored (`T4`). |

**The parameter-binding rule is the same rule as the logging rule.** No value
reaches a statement by interpolation (`BR2.9`), and no credential — and no
interpolated statement text — appears in any log record (`BR4.6`, `NFR8.3`).
These are designed once, in §3 and in `observability-design.md` §2, and cross-
referenced so the two files cannot drift.

## 3. Input validation and injection defence

**Design decision: refuse at the boundary, before computation, and bind every
value.**

### 3.1 Parameter-bound statements only

Every statement uses `?` placeholders; no statement text is built by
interpolation or concatenation (`BR2.9`, `NFR2.3`). The design's rule is
absolute: statement *text* is a compile-time constant in the read module; the
only things that vary are bound parameters. This closes threat **T2** (SQL
injection through `from`/`to`/`import_id`/`limit`) at the mechanism level — even a
hostile parameter value is data, never syntax.

```python
# Design shape only — statement text is constant; the value is bound.
_CURSOR.execute("... WHERE created_at >= ? AND created_at <= ?", (lo, hi))
```

### 3.2 Refuse malformed input before computing anything

Malformed values are rejected at the route, **before** the read module is called
(`NFR4.1`, `BR4.2`, `BR4.3`), so a refused request computes nothing:

- A `from`/`to` that cannot be read as a UTC date → `422` `VALIDATION_FAILED`
  whose message names `query.from` or `query.to`.
- An inverted range (`from` later than `to`) → one `422` naming **both**
  `query.from` and `query.to`.
- A `limit` below 1 or non-numeric (terms only) → `422` naming `query.limit`;
  never silently defaulted or clamped.
- `import_id` is **opaque** with no parse step (`contract-summary.md` §2, UC1), so
  there is no `import_id` parse failure to trigger and no test is written for one
  (see §7 threat T2 note).

A no-match range is **not** a validation failure: it is a `200` empty result
(`BR4.4`), because emptiness is not an error. The design keeps "invalid" and
"empty" structurally separate.

### 3.3 The frozen error envelope

All application-raised failures travel through the single existing
`{code, message}` envelope (`BR4.1`, ADR-003). The envelope has **no `field`
member and no `errors`/`details` array**; the offending parameter is named in the
message text. `STORAGE_FAILURE` is the only permitted addition to the code set
(`contract-summary.md` §2, `BR4.5`). Framework-generated routing errors
(unknown path, wrong method, missing asset) keep FastAPI's own `{"detail": …}`
shape and stay outside the envelope. This single-construction-site design is what
keeps the envelope from drifting into a stack-trace or detail leak.

### 3.4 No stack-trace leakage

A storage failure is mapped to `500 STORAGE_FAILURE` with a controlled message
(`BR4.5`); the underlying exception is **logged through the module logger**
(`BR4.6`) and never placed in the response body. The wire surface and the log
agree on the code, and only the log may carry detail.

## 4. Startup enforcement of the loopback bind (the central hardening)

**Design decision: enforce the loopback bind at startup; a non-loopback host
fails loudly.** This is the unit's one real security-posture change, and it closes
threat **T5** — the principal risk this unit could introduce (a bind that exposes
an unauthenticated app holding the operator's key).

| Aspect | Design | Source |
|---|---|---|
| What changes | The run path consumes the `HOST` constant and refuses to serve a non-loopback host, failing with an explanation at startup. | `NFR2.4`, `BR6.5`, `FR7.6` |
| Why it is needed | Today `HOST = "127.0.0.1"` has **no call site in the run path**; the documented `uvicorn app:app --reload` uses uvicorn's own default, so `--host 0.0.0.0` would expose the app while every test still passes. | `team.md` §Deployment |
| Why a documented default is not enforcement | A documented default is documentation; the constant must be **the value the run path actually consumes**. | Affirmed rule `memory/project.md`; `BR6.5` |
| Normal path unchanged | A loopback run is the normal local run, unchanged. | `BR6.5` |
| Instrument | The startup-enforcement test (`FR7.6`): supplying a non-loopback host must make startup fail with an explanation; a constant-only assertion is insufficient (`BR6.5`). | `NFR2.4` |

```text
startup():
    if not is_loopback(HOST): raise ConfigError(naming HOST)   # fail loudly
    app.run(host=HOST)                                          # consume the constant
```

## 5. Secrets management

**Design decision: no secret is added, read, or carried on the analytics path.**

- No analytics code path introduces a credential (`NFR2.5`); the endpoints read
  local rows and require no key.
- Live-mode credentials already live only in the gitignored `config.local.toml`
  and process memory (affirmed NEVER rule, `memory/project.md`); the analytics
  path never touches them.
- `Configuration and Settings` gains **no new configuration value** for analytics
  (`BR2.15`); all analytics behaviour is computed or a request parameter.

**Cross-unit dependency, stated honestly (per the review correction R-02).** The
secret-scanning gate affirmed by `FR7.3` **does not exist yet**; it is a
`u4-platform-packaging` obligation (`team.md` §Supply chain; `tech-stack-decisions.md`
Open items). It is named here only as a downstream dependency, **not** as an
instrument this unit can run today. The instruments that exist **now** are the
existing redaction assertions, the schema inspection (no credential field), the
armed offline guard, and the dependency-cap assertion.

## 6. Compliance and the dependency cap

| Obligation | Design | Instrument |
|---|---|---|
| Privacy / localhost-only | No new egress; loopback enforced; no credential committed/logged/printed/pasted. | `NFR2.6`; the packaging unit's gates (`FR7.1`–`FR7.4`). |
| No new runtime dependency | This unit declares no new runtime dependency; it is stdlib and existing-dependency only. | The dependency-cap assertion in `tests/test_config.py` (declared list unchanged) stays green (`C-6`). |
| Licence/audit surface | Repository-level, owned by the packaging unit; this unit adds no dependency and triggers no new licence or audit surface. | `FR7.1`, `FR7.3` (packaging unit). |
| Transitive `opentelemetry-api` | Nothing in `app/` imports it and no SDK/exporter is installed, so it is not an egress path (`A5`). | Unchanged by this work. |

## 7. Threat model — dispositions carried whole

Read the whole table so a later stage does not mistake an accepted low risk for
an open finding.

| # | Threat | Design disposition | Source |
|---|---|---|---|
| **T1** | New attack surface from `/v2` reads | Two read-only `GET`s, loopback-only, unauthenticated by design, computed in process. No write surface, no egress, no credential handling. | `NFR2.1`, `NFR2.2`, `BR2.7`, `BR2.8` |
| **T2** | SQL injection via `from`/`to`/`import_id`/`limit` | Refused at the boundary before computation (`BR4.2`, `BR2.6`) and every statement parameter-bound (`BR2.9`). `import_id` is opaque with no parse step, so its only failure mode is "matches nothing" → `200` empty (UC1). | `NFR2.3`, `BR2.9` |
| **T3** | Data exposure through the response | Response carries aggregates over the operator's own rows on a loopback surface; no credential, no raw text, no PII field. Terms are derived tokens; `resolved_range` is not serialised (UC3). | `contract-summary.md` §2, `entities.md` |
| **T4** | Data-at-rest / privacy | `C-9`: stored text may be personal data. No new egress, no retention/delete path; reads the existing store only. Restated, considered, not ignored. | `NFR2`, `C-9` |
| **T5** | Non-loopback exposure of the unauthenticated app | Closed by **enforcement at startup** (§4), not by a documented default. | `NFR2.4`, `BR6.5`, `FR7.6` |
| T4-risk | A secret scanner would strengthen the no-credential claim | Not available in this unit; recorded as a `u4-platform-packaging` dependency (§5), not claimed as coverage. | review-01 R-02 |

## 8. Traceability

| NFR (this unit) | Design solution (this file) |
|---|---|
| `NFR2.1` | §1 — no auth/authz added; posture stated and bounded. |
| `NFR2.2` | §2 — zero-egress invariant; import/static inspection + armed offline guard. |
| `NFR2.3` | §3.1 — parameter-bound statements only. |
| `NFR2.4` | §4 — loopback bind enforced at startup. |
| `NFR2.5` | §5 — no credential; scanner recorded as a downstream dependency. |
| `NFR2.6` | §6 — compliance within `C-9`/`C-10`/`C-11`; unchanged declared dependency list. |
| `NFR8.3` (log side) | §2 — no credential and no interpolated statement text in a log record; cross-referenced to `observability-design.md` §2. |

Full id-level enumeration is in `traceability.json`.
