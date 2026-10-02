# Contract Design — Plan (fast-tracked)

> One question, eight drafted decisions inside it. Reply `accept` to take all eight
> as written, or name the number you want changed (`4: B`, `accept except 6`).

## Q1 — Accept the drafted contract plan?

The eight decisions below are the drafted positions. Each is grounded in the code
or in a ruling this workflow already made, not in the requirements prose alone —
a prior intent's contract review caught three critical mismatches by comparing its
contract against the running routes, so that comparison is already done here.

1. **Three contracts are pinned.** (a) The public `/v2` HTTP surface, consumed by
   the page's script. (b) The inter-unit `U3 → U1` boundary. (c) The inter-unit
   `U1 → U2` boundary that the DAG *suppresses* but the import graph requires —
   pinning it is what stops the suppressed edge becoming a surprise.
2. **Mechanism is HTTP/JSON for the public surface and plain Python calls for the
   two inter-unit boundaries**, the latter pinned as shared-schema contracts
   rather than OpenAPI, because inside one deployable an inter-unit boundary is an
   import, not a wire protocol.
3. **Both analytics response payloads are pinned field by field** — name, type,
   nullability and rounding — exactly as `FR2` and `FR3` fix them, including the
   error envelope's exactly-two-key shape and the absence of a `field` member.
4. **The version prefix becomes a named contract constant on both sides.**
   `app.js:10` holds its own `const API = "/v1"` and nothing asserts it matches the
   backend; the contract names both locations and requires them to agree. This is
   the cheapest fix for the likeliest silent break in the feature.
5. **Additive-only within `/v2`; anything breaking needs a new prefix.** A consumer
   ignores unknown fields. The `/v1` surface is frozen outright.
6. **Errors, timeouts and retries are stated, with no retry.** Every status and
   machine code is named; the page surfaces a failure rather than auto-retrying,
   because a silent retry would make a stale range look current. Request timeout
   is the client's own choice and is recorded as explicitly unspecified.
7. **`U1` owns the `/v2` public surface and the `U3 → U1` boundary; `U2` owns the
   `U1 → U2` boundary**, because it owns the module being called. The summary
   states how a change is agreed.
8. **This contract supplements the `/v1` one rather than replacing it.** It
   describes `/v2` plus the two inter-unit boundaries, names the README's HTTP
   surface table as the `/v1` record of truth, and requires both to agree after the
   change.

A. Accept all eight as drafted
B. Accept except for the items I name
C. Other (please specify)

[Answer]: A. Accept all eight as drafted — three contracts (the public `/v2` surface, `U3 → U1`, and the suppressed `U1 → U2`), HTTP/JSON at the public surface with plain Python calls pinned as shared schemas at the inter-unit edges, both payloads pinned field by field, the prefix a named constant on both sides, additive-only within `/v2` with `/v1` frozen, every status and machine code stated with no retry, `U1` and `U2` owning their respective boundaries, and this contract supplementing rather than replacing the `/v1` one.

## Consolidated Summary Confirmation

- **Three contracts are pinned.** The public `/v2` HTTP surface, the inter-unit `U3 → U1` boundary, and the inter-unit `U1 → U2` boundary the DAG suppresses but the import graph requires.
- **The mechanism is HTTP/JSON at the public surface and plain Python calls at the two inter-unit edges**, the latter pinned as shared-schema contracts because inside one deployable an inter-unit boundary is an import rather than a wire protocol.
- **Both analytics payloads are pinned field by field** — name, type, nullability and rounding — matching what `FR2` and `FR3` fix, including the error envelope's exactly-two-key shape and the deliberately absent `field` member.
- **The version prefix becomes a named contract constant on both sides.** `app.js` carries its own `const API = "/v1"` and nothing asserts it matches the backend; the contract names both locations and requires them to agree.
- **Additive-only within `/v2`; breaking changes need a new prefix.** A consumer ignores unknown fields, and `/v1` is frozen outright.
- **Every status and machine code is stated, and there is no retry.** The page surfaces a failure rather than auto-retrying, and the request timeout is recorded as explicitly unspecified.
- **Ownership is assigned**: `U1` owns the `/v2` public surface and the `U3 → U1` boundary, `U2` owns the `U1 → U2` boundary because it owns the module being called.
- **This contract supplements the `/v1` contract** rather than replacing it; the README's HTTP surface table remains the `/v1` record of truth, and both must agree after the change.

- `Looks correct`
- `Request changes`

[Answer]: Looks correct
