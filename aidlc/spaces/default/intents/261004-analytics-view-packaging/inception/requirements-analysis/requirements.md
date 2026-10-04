# Requirements — sentiment-opencode analytics view & packaging

**Intent:** `analytics-view-packaging` (scope `express`, depth Minimal)
**Source:** the verbatim initial description (`project-description.json`) plus the
prior intent `261001-analytics-layer` (record
`aidlc/spaces/default/intents/261001-analytics-layer/`), read as provenance rather
than re-derived. The current CodeKB store (`codekb/sentiment-opencode/`) is the
brownfield evidence.

## Intent Analysis

The prior intent added the read-only `/v2` analytics server (`app/analytics.py`,
`app/terms.py`, two endpoints) but its unit walk was wedged before the two
remaining deliverables shipped (see `ENGINE-DEFECT-REPORT.md`). This intent
finishes exactly those two:

1. **The analytics view wiring** — the page carries the nav and the summary
   region, but the terms section is a static placeholder and there is no
   date-range control. Wiring both makes the existing `/v2` endpoints usable from
   the page and gives NFR4.6 and NFR4.7 something to run against.
2. **The platform packaging** — the standing gates run only when a developer
   remembers to run them, and no secret scanner or dependency audit exists at
   all. This intent adds the verification entry point and the two instruments,
   plus the three named leftovers from the prior practices obligations.

The goal is to close the prior record's two `Unverified` NFR targets and to make
the quality gates mechanically runnable — without touching the frozen `/v1`
contract, without a third runtime dependency, and without a new external service.

## Functional Requirements

### FR1 — Analytics view wiring (terms section + date-range control)

- **FR1.1** The analytics view is a third top-level entry inside the existing
  single-page shell, served by the existing static-asset path — not a second
  site and not a separate URL tree. The nav and the summary region already
  exist; the **terms section** is added so both `/v2` endpoints are usable from
  the page. [prior FR6.1, FR6.2][RE]
- **FR1.2** The terms section renders the positive and the negative term lists at
  the affirmed **top 10 per list**, with each term's count. [prior FR6.2][desc]
- **FR1.3** A **date-range control** narrows the view. **The default is all
  history with no bounds.** There is **no `import_id` control on the page**; that
  filter stays API-only, so the page always presents the unfiltered population.
  [prior FR6.3][desc]
- **FR1.4** Changing the range refetches **both** endpoints with the same bounds,
  so the summary and the term lists always describe the same population. [prior
  FR6.4]
- **FR1.5** The view works **fully offline** against the dummy client and issues
  no request other than to its own analytics endpoints. [prior FR6.5][desc]
- **FR1.6** Rendering uses native HTML elements and the page's existing class
  names. No new front-end dependency and no chart library. [prior FR6.6]
- **FR1.7** A failed analytics request renders an inline error state that names
  the failure rather than an empty chart or a silent blank. The endpoint's error
  envelope is the source of that state, so a `422` and a `500` are visibly
  different from an empty result. [prior FR6.7]
- **FR1.8** The view meets the page's existing accessibility basics: the range
  control is labelled, the series/term data is exposed to assistive technology
  rather than drawn only visually, and status changes are announced. [prior
  FR6.8]
- **FR1.9** The view's markup hooks are added to the page module's existing
  pinned test-id constant (`REQUIRED_TEST_IDS` in `tests/test_page.py`),
  following the convention the current page tests assert. [prior FR6.9]
- **FR1.10 — NFR4.6 closure (per-section graceful degradation).** When one
  section succeeds and another fails, a **partial-failure marker** is shown for
  the failed section while the successful section still renders its data. A
  single failed request must not blank the whole view. [desc][prior NFR4.6]
- **FR1.11 — NFR4.7 closure (no silent retry; superseded response discarded).**
  The view performs **no silent automatic retry**, and a **superseded
  out-of-order response is discarded** — a later-issued request's result must
  not be overwritten by an earlier-issued one that returned late. [desc][prior
  NFR4.7]

### FR2 — Platform packaging

- **FR2.1** A platform-neutral verification entry point — a **`Makefile` target
  `make verify`** — runs the standing gates in order: install
  (`python -m pip install -e ".[dev]"`), `ruff check`, `ruff format --check`,
  `pytest` with the 80 % whole-application line-coverage floor, the secret scan,
  and the dependency audit. It is **not** a pre-commit hook and **not** a
  provider CI job (there is no remote). [prior FR7.2][Q3]
- **FR2.2** **Secret scanning** runs via **`detect-secrets`**, with an allowlist
  covering the repository's fake-key fixtures so the first run produces signal
  rather than noise. The current scan counts **seven** fixture-bearing test
  files; that measured count is the one the allowlist must cover. [prior
  FR7.3][Q1][RE]
- **FR2.3** A **dependency audit** runs via **`pip-audit`**. [prior FR7.3][Q1]
- **FR2.4** A **dependency lockfile with hashes** ships, so every install
  resolves to the same set rather than to whatever is newest that day. [prior
  FR7.1][Q4]
- **FR2.5** A **`LICENSE`** file ships and the installed distribution declares
  it. [prior FR7.4][Q4]
- **FR2.6** The layer boundaries are expressed as **`ruff` `TID251`
  `banned-api`** entries, so a boundary breach is a lint failure rather than
  something only a reviewer can notice. [prior FR7.5][Q4]
- **FR2.7** The README's `## HTTP surface` table, its `## File layout` tree and
  its verification section are updated for the new modules, the added markup and
  the `make verify` command; the README's table is this project's contract of
  record. [prior FR7.9]

### FR3 — Tests

- **FR3.1** The existing suite stays green with no network and no API key; the
  session-scoped offline guard stays armed and a test continues to prove the
  guard itself is armed. [desc]
- **FR3.2** The 80 % whole-application line-coverage floor still holds after
  this change, counting any new modules. [team]
- **FR3.3** `tests/test_page.py` pins the analytics view's markup hooks: the
  terms list containers, the date-range control, the **partial-failure marker**
  hook (FR1.10) and the **abort/supersede** hooks in the served script (FR1.11).
  Because no test executes the browser script, these static served-asset
  assertions plus the manual end-to-end step in `make verify` are the combined
  evidence that marks NFR4.6 and NFR4.7 Verified. [Q2][RE]
- **FR3.4** A `make verify` run is the verification evidence for the packaging;
  the lockfile is committed and an install from it is reproducible. [prior
  FR7.2][Q3]
- **FR3.5** The secret scan and dependency audit are invoked from `make verify`
  and documented in the README's verification command. [prior FR7.3]

## Non-Functional Requirements

- **NFR1 — Reliability (view).** A partial section failure is visible and
  isolated (FR1.10); a superseded response never overwrites a newer one
  (FR1.11); a failed request never renders as a plausible-looking empty result.
  Both prior targets move from `Unverified` to `Verified` on the FR3.3 evidence.
- **NFR2 — Compatibility.** The `/v1` contract, the `SentimentClient` interface
  and adapter behaviour, the error-envelope **shape**, and the
  `config.example.toml` / gitignored `config.local.toml` convention are all
  unchanged. The analytics contract already pinned (`shares` as 4-dp half-up
  fractions with `null` on a zero denominator; an empty range returning an empty
  series, not zeros; zero-fill only on internal gaps of a matched range) is
  rendered, not re-derived. [desc]
- **NFR3 — Security.** No new egress path; analytics reads local rows only; all
  SQL parameter-bound; no credential in any code path, response body, log record
  or artifact. Secret scanning and the dependency audit become part of
  verification. [prior NFR2]
- **NFR4 — Maintainability.** New code follows the conventions the codebase
  already holds: module docstring with a `Single responsibility:` line, full
  annotations, `from __future__ import annotations`, `UPPER_CASE` constants with
  `#:` prose comments, underscore-private helpers, and no junk-drawer module.
  Stdlib dataclasses, never `pydantic`, in `app/`. [team]
- **NFR5 — Testability.** Tests reach real SQLite and real served markup, never
  a mock of the thing under test. No browser execution is introduced; the
  runtime dependency cap admits no browser-automation library. [prior NFR7]
- **NFR6 — Performance.** The prior `/v2` performance target (under 200 ms over
  10,000 rows, SQL count independent of range length) remains; this intent adds
  only page-side wiring and no server work. [prior NFR1]

## Constraints

- **C1 — `/v1` must not change.** [desc]
- **C2 — Runtime dependencies stay at exactly two** (`fastapi`, `uvicorn`); every
  new tool (`detect-secrets`, `pip-audit`, any lockfile tool) goes in the `dev`
  extra. [desc][team]
- **C3 — No `pydantic` in `app/`.** [desc]
- **C4 — No new external service; all tests offline** with the session guard
  armed. [desc]
- **C5 — The analytics contract is pinned** and must not be re-derived:
  `shares` are 4-dp half-up fractions with `null` on a zero denominator; an empty
  range returns an empty series, not zeros; zero-fill applies only to internal
  gaps of a matched range. [desc]

## Assumptions

- The seven fake-key fixture files measured by the scan are the complete
  allowlist set for `detect-secrets`.
- `detect-secrets` and `pip-audit` are installable from PyPI on this machine.
- A POSIX `make` is available as the platform-neutral entry point for FR2.1.
- The page can render the partial-failure marker and discard a superseded
  response without a new runtime dependency (plain DOM + `fetch` +
  `AbortController`/request token).

## Out of Scope

- Any change to the `/v1` contract, including health, auth, analyze and the CSV
  import/export endpoints.
- Real-time, streaming or incremental analytics — everything is computed on
  request from stored rows.
- The two prior FR7 items not named in the chosen leftovers — startup loopback
  enforcement and the ASGI test-harness replacement — which remain open for a
  future scope.
- Market validation (the Ideation brief approved as a conditional go with
  "Market validation: pending").

## Open Questions

- **Lockfile format and the install command that consumes it.** FR2.4 requires a
  lockfile with hashes; the format (pip-tools, uv, or `pip --require-hashes`) is
  a Design decision.
- **Which licence.** FR2.5 requires a `LICENSE`; every installed dependency is
  permissive, so no compatibility constraint forces the choice.
- **Whether the deferred loopback-enforcement and ASGI-harness items warrant
  their own follow-up scope.**
