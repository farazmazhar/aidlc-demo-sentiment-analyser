# Contract Design — Clarifying Questions

Context: this stage pins the formal contracts the system must honour before code is written. The
system is a single `service` unit (`U1`) with no inter-unit boundaries, so the boundary to pin is its
HTTP surface: the page and any other local client call `POST /analyze`, `GET /analyses` and the health
endpoint, and the app calls the OpenRouter Decisions API outbound in live mode. The record shape
(`AnalysisRecord`) and the error envelope cross that boundary too.

Answers shape the contract summary: the boundary table, the per-contract spec blocks, the ownership
rules and the open questions.

---

## Q1. Which boundaries are contracts?

- A. The HTTP surface the unit exposes (`POST /analyze`, `GET /analyses`, the health endpoint, plus the page's own routes) — pinned as one OpenAPI contract
- B. The HTTP surface plus the outbound OpenRouter Decisions API call as a separate contract
- C. The HTTP surface plus the stored record shape as a shared-schema contract
- X. Other (please specify)

[Answer]: A. The HTTP surface the unit exposes (`POST /analyze`, `GET /analyses`, the health endpoint, plus the page's own routes) — pinned as one OpenAPI contract

## Q2. What mechanism does each boundary use?

- A. Synchronous REST/HTTP (an OpenAPI-style spec), with the in-process handoff staying internal
- B. REST/HTTP for the API and an event/message spec for the engine handoff
- C. REST/HTTP only, with no spec for anything else
- X. Other (please specify)

[Answer]: A. Synchronous REST/HTTP (an OpenAPI-style spec), with the in-process handoff staying internal

## Q3. What versioning and breaking-change policy applies?

The only consumer today is the page in the same unit, and the app is localhost-only with one user.

- A. No version prefix; additive changes only, unknown fields ignored, and a breaking change is allowed because the only client ships with the server
- B. A `/v1` prefix on the JSON API, with additive changes only
- C. Version only if and when a second client appears
- X. Other (please specify)

[Answer]: B. A `/v1` prefix on the JSON API, with additive changes only

## Q4. What error, timeout and retry behaviour belongs in the contract?

- A. The single error envelope with its machine codes, a stated timeout on the outbound live call, and no automatic retry
- B. The envelope, a timeout, and one bounded retry on the live call
- C. The envelope only; timeouts and retries stay implementation details
- X. Other (please specify)

[Answer]: A. The single error envelope with its machine codes, a stated timeout on the outbound live call, and no automatic retry

## Q5. Who owns the contract spec?

- A. The single unit owns it, and any change to it is approved by you at this stage's gate
- B. The unit owns it and changes need no approval, since one team owns both sides
- C. Ownership is deferred to a later stage
- X. Other (please specify)

[Answer]: A. The single unit owns it, and any change to it is approved by you at this stage's gate
