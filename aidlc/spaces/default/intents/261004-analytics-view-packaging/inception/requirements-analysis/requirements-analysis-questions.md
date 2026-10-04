# Requirements Analysis — Clarifying Questions

**Intent:** `analytics-view-packaging` (scope `express`, depth Minimal)
**Stage:** Requirements Analysis (Inception)

This intent adds the two remaining analytics-layer deliverables: the analytics
**view** wiring (terms section + date-range control, closing NFR4.6 and NFR4.7)
and the **platform packaging** instruments (verification script, secret scanner,
dependency audit). The server half (`/v2/analytics/summary`,
`/v2/analytics/terms`) is already complete and tested; `/v1` is frozen; runtime
dependencies stay at exactly two (`fastapi`, `uvicorn`).

Most decisions are already pinned by the description, the prior intent
(`261001-analytics-layer`) and the team's affirmed practices. The questions
below cover only the decisions those sources leave open.

---

## Q1 — Secret scanner and dependency-audit tooling

FR7.3 requires a secret scanner and a dependency audit as part of verification,
and the prior record left the exact tools unresolved. Dev-extra tools are
allowed (the runtime cap of two is untouched), and PyPI is reachable. The first
scanner run must allowlist the repository's fake-key test fixtures (the current
scan counts **seven** files with `sk-or-v1-*` literals, not the four the old
memory said).

**Which tooling should the verification script adopt?**

- A. `detect-secrets` (secret scan) + `pip-audit` (dependency audit) — both pip-installable into the `dev` extra, no separate binary to install.
- B. `detect-secrets` (secret scan) + `safety` (dependency audit) — both pip-installable.
- C. `gitleaks` (secret scan, standalone binary) + `pip-audit` (dependency audit) — requires installing a non-Python binary.
- D. A different pair (name both).
- X. Other (please specify)

[Answer]: A. `detect-secrets` (secret scan) + `pip-audit` (dependency audit) — both pip-installable into the `dev` extra, no separate binary to install. The scanner's allowlist covers the repository's fake-key fixtures (seven files as measured in the current scan).

---

## Q2 — How to verify NFR4.6 and NFR4.7

NFR4.6 (per-section graceful degradation — a partial-failure marker when one
section succeeds and another fails) and NFR4.7 (no silent retry; a superseded
out-of-order response is discarded) live in `app/static/app.js`, which no test
executes — the project deliberately allows **no browser execution** and the
runtime cap admits no browser-automation library. Both targets are currently
`Unverified` for exactly this reason.

**How should these two targets be verified so they can be marked Verified?**

- A. Verify statically: pin the served markup/JS contract in `tests/test_page.py` (the partial-failure marker hook, and the abort/supersede hooks in the script) plus an explicit manual end-to-end step in the verification script. Mark both Verified on that combined evidence.
- B. Add a minimal JavaScript test runner as a **dev-only** tool to execute the supersede logic in isolation (new tooling, still no runtime dependency and still offline).
- C. Leave both targets `Unverified` and record them as accepted gaps.
- X. Other (please specify)

[Answer]: A. Verify statically: pin the served markup/JS contract in `tests/test_page.py` (the partial-failure marker hook, and the abort/supersede hooks in the script) plus an explicit manual end-to-end step in the verification script. Mark both NFR4.6 and NFR4.7 Verified on that combined evidence.

---

## Q3 — Form and location of the verification script

FR7.2 requires a platform-neutral verification script that runs the standing
gates (80% whole-application line-coverage floor, warnings-as-errors, pinned
`ruff` rule set). The team rule says it is a script the developer runs — not a
pre-commit hook and not a provider CI job (there is no remote).

**What form should the verification script take?**

- A. A POSIX shell script at `scripts/verify.sh` (install → secret scan → dependency audit → `ruff check` → `ruff format --check` → `pytest` with the coverage floor).
- B. A `Makefile` target `make verify`.
- C. A Python script at `scripts/verify.py`, invoked as `python scripts/verify.py`.
- X. Other (please specify)

[Answer]: B. A `Makefile` target `make verify`.

---

## Q4 — Packaging scope boundary

The prior intent's FR7 listed eight practices obligations. The description for
this intent names only three packaging deliverables: the verification script,
the secret scanner, and the dependency-audit check. The scan confirms the prior
list's other items are still absent (no lockfile, no `LICENSE`, no `ruff`
`TID251` `banned-api` entries).

**What is this intent's packaging scope?**

- A. Only the three named instruments (verification script, secret scanner, dependency audit); leave the lockfile, `LICENSE`, and `TID251` to a future scope.
- B. Also include the prior FR7 leftovers (lockfile, `LICENSE`, `TID251`) in this intent.
- X. Other (please specify)

[Answer]: B. Also include the prior FR7 leftovers (lockfile, `LICENSE`, `TID251`) in this intent.
