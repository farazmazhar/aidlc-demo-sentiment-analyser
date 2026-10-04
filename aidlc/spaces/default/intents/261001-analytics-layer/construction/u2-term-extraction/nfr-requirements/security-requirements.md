# Security Requirements — `u2-term-extraction`

> **Intent:** `261001-analytics-layer` · stage `nfr-requirements` (construction) ·
> unit `u2-term-extraction` (kind `library`).
>
> **Upstream inputs.** This unit's `functional-spec.md` (the module surface and its three
> workflows), `rules.md` (the `BR6.1`/`BR6.2` isolation and purity rules these
> requirements are the NFR-side of), `requirements.md` (the canonical `NFR2` Security
> parent), and `contract-summary.md` (contract **C3**, which declares this boundary's
> input as "any `str`" — the fact `NFR2`'s DoS discussion turns on).
>
> **Scope note.** A fan-out-0 pure-function module has a small security surface, and
> this file is correspondingly short. The honest position is that **this unit invents
> no security control** — it *avoids* the classes of defect that would create one. That
> is recorded per element rather than padded into a threat model the module does not
> need. `NFR5`/`NFR6`/`NFR7`-family concerns live in `u1-analytics-slice`'s
> requirements, where the HTTP surface and the store are.

## Threat surface — STRIDE over what actually exists

The module's data flow is: **caller passes `str` → module returns `list[str]`**. There
is no external entity, no data store, no network boundary and no credential. Walking
STRIDE against that:

| Threat | Applicable? | Why, with the evidence |
|---|---|---|
| **S**poofing | **No** | Nothing authenticates. The module has no caller identity, no token, no session. It cannot be impersonated because there is nothing to impersonate. |
| **T**ampering | **No** | Nothing is persisted or transmitted. Input arrives in memory, output leaves in memory. There is no at-rest or in-transit representation to modify. |
| **R**epudiation | **No** | No auditable action occurs. The module performs no state change anyone could deny. |
| **I**nformation disclosure | **No** | The module cannot leak: it holds no secret, opens no channel, and its only output is a subsequence of its input. A token that a caller passed in cannot reach anywhere the caller did not already have it. |
| **D**enial of service | **Bounded** | See below — the only real one. |
| **E**levation of privilege | **No** | No privilege exists to elevate. The module calls nothing and touches nothing. |

**The one applicable threat, stated precisely — and it is not fully covered.** `tokenize`
and `significant_terms` are linear in their input and neither bounds it. A caller passing
a very large string allocates a token list proportional to it.

**An earlier draft said `u1-analytics-slice` bounds this by reading rows from a range.
That is wrong, and the review caught it.** A range bounds the **number of rows**, not the
size of any one row's `text` column: contract C3 declares the terms input as "any `str`"
and **no cap on `text` exists anywhere in the record**. So a single very large stored row
reaches this module unbounded. The honest statement is:

- **This module sets no cap, and should not.** A policy limit inside a pure function would
  be invisible to callers and untestable at the right layer.
- **No cap exists upstream either.** That is a live gap, not a satisfied requirement, and
  it is **not this unit's to close** — it belongs to `u1-analytics-slice` (which owns the
  read path and the `text` column's use) or to Requirements Analysis (which owns the
  contract).
- **It is recorded here as open** rather than marked handled, so it reaches the backlog
  instead of disappearing. See `traceability.json`'s `NFR2` row and the U2 diary.

## Requirements

### `NFR2.1` — No network access from this module

- **Metric:** imported-module closure of `app/terms.py`.
- **Target:** contains no network-capable module (no `socket`, `http`, `urllib`,
  `requests`, `httpx`, `ssl`).
- **Verification:** two instruments that exist. The `technology-stack` record confirms
  the interpreter and its stdlib baseline, which is what makes `re` and `collections.abc`
  legitimate here. (1) The module's **actual import list**
  is inspectable and is exactly three lines (`__future__`, `re`, `collections.abc`), none
  network-capable. (2) The session-wide offline guard in `tests/conftest.py:286` replaces
  `socket.socket.connect` with a function that raises, so any socket connection anywhere
  in the suite fails the run. **There is no `ast` import-closure check in this repository** —
  an earlier draft named one and the review caught it. If a future change wants that
  guarantee enforced rather than inspected, the check has to be written.
- **Source:** `NFR2` (Security) and the feature's offline guarantee in `NFR2`; `FR4.4`, `AC8.2.1`.

### `NFR2.2` — No credential can reach this module

- **Metric:** occurrence of credential-shaped literals or key-bearing identifiers.
- **Target:** zero. The module holds constants only, and all three are non-secret
  (`TOKEN_PATTERN`, `MIN_TERM_LENGTH`, `STOPWORDS`).
- **Verification:** by **inspection of the module's three constants and three imports**,
  which is decisive at this size. **There is no credential scanner and no fake-key
  allowlist in this repository** — `FR7.3` is open and `u4-platform-packaging` owns it; an
  earlier draft implied an allowance existed and the review caught it. Until that
  scanner lands, this requirement's evidence is inspection plus the absence of any
  credential-shaped token in the file.
- **Source:** `FR8.2`-family, `AC8.2.2`.

### `NFR2.3` — No outbound call of any kind, including to the sentiment engine

- **Metric:** imports of `app.openrouter_client` or any live-transport symbol.
- **Target:** zero. The module imports **nothing from `app` at all** (`BR6.1`).
- **Verification:** the module's import list itself — `__future__`, `re`,
  `collections.abc.Sequence`, and no `app` symbol. **There is no test that asserts the
  fan-out-0 property by name**; an earlier draft named one and the review caught it.
  What does exist is the offline guard (`NFR2.1`), which would fail the run if any code
  path opened a connection.
- **Source:** `AC8.2.3`, `components.md` `TermExtraction` boundary.

### `NFR2.4` — No I/O, so no side channel

- **Metric:** filesystem, database, clock or randomness calls reachable from the module.
- **Target:** zero. Both operations are pure (`BR6.2`, `BR6.3`).
- **Verification:** the import list again — a module that performs no I/O imports no
  module capable of it, and `re` and `collections.abc` are neither.
- **Source:** `NFR2`, `BR6.2`.

### `NFR2.5` — Input is treated as untrusted text, never as a format

- **Metric:** any parse, eval, deserialise or format string applied to input.
- **Target:** zero. Input is matched against a fixed character class and otherwise
  discarded. There is no injection surface: the module builds no statement, no command
  and no markup.
- **Verification:** by inspection of the two operations, both of which are a list
  comprehension over a regex match.
- **Source:** `AC8.2.1`, `AC8.2.3`, and the OWASP injection class generally.

### `NFR2.6` — The stopword set is in-repo and never fetched

- **Metric:** runtime acquisition of the stopword list.
- **Target:** none. `STOPWORDS` is a module constant (`BR4.3`).
- **Why it is a security requirement and not only a functional one:** fetching a word
  list at runtime would create the module's *only* egress path and its first external
  dependency, in a unit whose whole value is being a dependency-free leaf.
- **Verification:** the offline guard, plus the absence of any HTTP import (see `NFR2.1`).
- **Source:** `FR4.4`, `AC4.1.4`.

## What this unit deliberately does NOT claim

- **No rate limiting, no input-size cap, no timeout.** All three are caller concerns.
  A cap here would be a policy the module has no basis to set, and `u1-analytics-slice`
  is where a bound belongs.
- **No logging, no metrics, no audit records.** A pure function that logged would gain
  an I/O path and lose the fan-out-0 property.
- **No encryption, no key management, no secret handling.** There is nothing to protect.
- **No authentication or authorisation.** The module has no callers it can identify.

Each absence above is a decision with a reason, not a gap left unexamined.
