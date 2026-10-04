# Code Summary — `analytics-view-packaging` (stage-level)

**Stage:** code-generation (Construction), target `stage-level`
**Scope:** `express` (zero-Unit), depth Minimal
**Testing Contract:** `sha256:ecc3bf8459ad42ce6ec7f5c4311cd6cfdde9084ad0631518587bfc5a141c8cfd`
**Methodology:** custom — acceptance/markup tests first, implementation second, lower-level unit tests after.

## What was built

Two halves, both from the approved plan:

1. **The analytics view (FR1)** — the page's static placeholder terms section is
   replaced with two ranked term lists and a shared, labelled date-range control;
   the served script now drives both `/v2` endpoints on the same bounds, isolates
   a failed section behind a partial-failure marker, and discards a superseded
   out-of-order response.
2. **The platform packaging (FR2)** — a `Makefile` verification entry point, a
   `detect-secrets` allowlist, a `pip-audit` dependency audit, a hashed
   lockfile, an MIT `LICENSE` declared in the metadata, and `ruff TID251`
   layer-boundary rules.

## Files created

| Path | Purpose |
|---|---|
| `Makefile` | `make verify`: install → `ruff check` → `ruff format --check` → `pytest` → secret scan → dependency audit (FR2.1). |
| `LICENSE` | MIT licence text (FR2.5). |
| `requirements.lock` | Hashed lockfile generated with `uv pip compile --generate-hashes --extra dev` (FR2.4). |
| `.secrets.baseline` | `detect-secrets` allowlist recording the repository's fake-key fixtures as reviewed (FR2.2). |

## Files modified

| Path | Change |
|---|---|
| `app/static/index.html` | Added the date-range control, the two term-list containers, the summary/terms partial-failure markers, the terms empty/error regions, and their CSS. |
| `app/static/app.js` | Added the range query builder, the two independent section fetches, the term rendering, the partial-failure marker logic, and the `AbortController` + request-token supersede guard. |
| `tests/test_page.py` | Extended `REQUIRED_TEST_IDS` with the ten new hooks and added six served-markup / served-script contract tests (FR1.9, FR1.10, FR1.11, FR3.3). |
| `pyproject.toml` | Declared the MIT licence and `LICENSE` file; added `detect-secrets`, `pip-audit` and `uv` to the `dev` extra; added `TID` to the lint selection with three `TID251` `banned-api` boundaries and the three exempt files. |
| `README.md` | Updated the setup section, the page description, the test/lint section, the `## HTTP surface` table, the `## File layout` tree and the verification section for the new markup, the `Makefile` and `make verify`. |

No files were deleted.

## Key implementation decisions

- **Two independent section fetches, one shared range.** `refreshAnalytics()` takes
  one request token, aborts the previous request, builds one query string from the
  two date inputs, and issues `refreshSummary()` and `refreshTerms()` in parallel.
  Each returns an outcome (`ok` / `empty` / `error` / `superseded`), so a failure
  in one section never blanks the other.
- **Supersede guard (NFR4.7).** A module-level `analyticsRequestToken` is
  incremented on every refresh and captured by the in-flight call; a response whose
  token is stale returns `"superseded"` before painting. An `AbortController` is
  aborted on the next refresh. There is no automatic resend.
- **Partial-failure markers (NFR4.6).** `summary-partial` and `terms-partial` are
  distinct hidden `role="status"` regions, shown only when that section failed and
  the other succeeded.
- **Terms rendering (FR1.2, FR1.6).** `renderTermList()` builds each `<li>` from two
  `textContent` spans (`term-name`, `term-count`) and appends native elements; the
  endpoint's default limit already bounds each list to 10.
- **Error text (FR1.7).** `readAnalyticsError()` reads the `{code, message}`
  envelope and shows the message, so a `422` and a `500` are visibly different from
  an empty result.
- **Accessibility (FR1.8).** Both date inputs have `<label for>`; `range-status` is
  a `role="status"` live region announced on every refresh; the term data is real
  ordered-list text, not a visual-only drawing.
- **`/v1` untouched.** No route, shape, envelope or client interface changed.
  Runtime dependencies stay exactly `fastapi` + `uvicorn`; every new tool is in the
  `dev` extra.
- **Secret-scan scope.** The scan covers the paths this project authors
  (`app tests config.example.toml pyproject.toml README.md Makefile docs`); the
  framework-owned `aidlc/` harness tree is not scanned. The baseline records the
  findings in the fixture-bearing files so a genuinely new secret still fails.

## Test coverage summary

- Baseline before the change: **192 passed, 884 statements, 26 missed, 97.06 %**.
- After the change: **198 passed** (+6 new page-contract tests), same 884 measured
  statements, **97.06 %** line coverage; the whole-application 80 % floor holds.
- The new tests are served-markup and served-script assertions (the browser script
  is never executed; no browser-automation dependency is admitted). The view's
  manual end-to-end evidence is the documented boot-and-read step in the README,
  which was run and answered `/v1/health`, `/v2/analytics/summary`,
  `/v2/analytics/terms` and `/` over real HTTP on `127.0.0.1:8141`.
- `make verify` runs green end to end (install, `ruff check`, `ruff format
  --check`, `pytest` with the floor, `detect-secrets`, `pip-audit`).
- `TID251` was proved non-vacuous: temporarily importing `app.service` into
  `app/analytics.py` produced a lint failure, and the probe was reverted.

## Deviations from the plan

1. **Lockfile generator is `uv`, not `pip-tools`.** `pip-compile --generate-hashes`
   over the full dev tree did not complete within 580 s; `uv pip compile
   --generate-hashes` produced the same artifact in seconds. The requirements'
   Open Question explicitly listed `uv` as an allowed format. `uv` (not
   `pip-tools`) is therefore the dev-extra tool declared in `pyproject.toml`, and
   `make lock` documents the generation command.
2. **`make verify` keeps the plan's six-step order and does not boot the server.**
   Plan step 9 pins the exact order; the Q2 "manual end-to-end step" is documented
   in the README's verification section and was run as evidence, but is not a
   seventh recipe line.
3. **Two partial-failure marker hooks, not one.** `summary-partial` and
   `terms-partial` are distinct so each section's failure is attributable.
4. **`setuptools` build floor raised `>=68` → `>=77`.** Required for the PEP 639
   `license = "MIT"` / `license-files = ["LICENSE"]` metadata that FR2.5 asks for.
5. **One page test was tightened to the implementation's helper name**
   (`renderTermList(termsPositive, …)`) after the first draft asserted an
   intermediate variable that the final helper does not use; the assertion still
   pins both lists rendered from returned values with `textContent`.
6. **Secret-scan scope excludes the `aidlc/` harness tree**, which is
   framework-owned and not part of the project's authored source.
