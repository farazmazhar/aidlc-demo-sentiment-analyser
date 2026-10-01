# Practices Discovery — Interview Questions

Answers from the evidence-based draft (`team-practices.md`) and the three independent reviews
(`contributions/`) are recorded below each option line where they exist. Nothing here is affirmed
until the affirmation gate.

Evidence summary, so the questions stand on their own:

- `main` holds only the AI-DLC harness; the whole application (app, tests, README, pyproject,
  config example) sits on the unmerged branch `v1-classic`, one commit ahead.
- Two commits total, one author identity, no merges, no tags, no CI, no linter, no coverage tool,
  no deployment or container configuration.
- The suite is `pytest` — 52 tests in 9 test modules plus a `conftest.py` harness — run by hand. It
  is green at the current commit (52 passed in 0.33s). `tests/conftest.py` blocks network use, so
  any accidental outbound call fails the run; it contains no concurrency test.
- The live Jev/OpenRouter client is not exercised by any test; the README says review plus a manual
  live smoke run covers it.
- Real SQLite file `data/sentiment.db`, gitignored, no migrations; the API key lives only in the
  gitignored `config.local.toml`.
- The thin-slice-first step ("walking skeleton") is off for this scope, so no slice ceremony ran.

---

## Q1. How should work be versioned and landed?

Today `main` carries only the harness and the app is on an unmerged branch, so no merge style has
ever been exercised here. Framework default is short-lived branches off `main`, squash-merged.
This decides both the branching rule and where the finished v1 ends up.

- A. Short-lived branches off `main`, squash-merged within a day or two, and `v1-classic` merges into `main` when it is done
- B. One branch per intent or scope; merged into `main` when the work is finished, keeping its commits
- C. One branch per intent or scope; squashed into `main` when the work is finished
- D. Work directly on `main`
- X. Other (please specify)

[Answer]: X. Other — one branch per intent or scope, merged into `main` when the work is finished, squashed to a single commit on `main`, and that commit tagged with the scope name (e.g. branch `v1-classic` squashed into one commit on `main`, tagged `v1-classic`)

## Q2. Build a thin end-to-end slice first?

A walking skeleton is a minimal version that runs the whole way through, built first to prove the
pieces connect before the real features go in. This scope says no for this run; the question is
whether that should be the standing rule for future work here.

- A. Only when a scope already asks for it (this run: off, so no slice step)
- B. Yes — build a thin end-to-end slice first by default on future work
- C. No — never run that step in this project
- X. Other (please specify)

[Answer]: B. Yes — build a thin end-to-end slice first by default on future work

## Q3. What single command should later stages use to prove a change works end to end?

The record needs one approved command it can run to demonstrate a unit actually works, rather than
each stage inventing its own. The suite never starts a server, so a command that only runs `pytest`
does not exercise the running app.

- A. Install, run `pytest`, then start the app locally and exercise the changed path (record this as the project's verification command)
- B. Run `pytest` alone
- C. No fixed command — decide per change
- X. Other (please specify)

[Answer]: A. Install, run `pytest`, then start the app locally and exercise the changed path (record this as the project's verification command)

## Q4. Do tests come before or after the code?

The draft infers test-after from the prior intent's stage instructions; a snapshot cannot show which
was written first. If the real cadence mixes, the recorded value becomes `custom`.

- A. Test-after: implement the layer, then write and run that layer's tests
- B. Test-first (TDD): write the failing test, then the code
- C. Mixed — say which part comes first and which comes after (`custom`)
- X. Other (please specify)

[Answer]: C. Mixed (`custom`) — acceptance/API tests first, lower-level unit tests after

## Q5. Coverage floor, and where does the suite run?

Measured with a standard-library tracer over the current tree: about **70% of lines across all 12
application modules**, or about **86.5% if the never-imported live Jev client is excluded** (its 149
lines sit at 0%). The `classic` scope expects an 80% line floor, so whether it passes today depends
on what counts in the denominator — that is the decision here, and separately nothing measures
coverage or runs the suite automatically.

- A. Add a coverage tool, count the whole application (floor fails today at ~70%), enforce 80%, and run the suite plus the floor in a CI job
- B. Add a coverage tool, exclude the untested live client (floor passes at ~86%), enforce 80%, run in CI
- C. Add the coverage tool and the 80% floor, verified locally — no CI
- D. No coverage floor; running `pytest` before committing is the whole gate
- X. Other (please specify)

[Answer]: A. Add a coverage tool, count the whole application (floor fails today at ~70%), enforce 80%, and run the suite plus the floor in a CI job

## Q6. What is the release story, and how does local data survive a change?

There is no deployment configuration of any kind, the version is `0.1.0` with no tag, and durable
state is one gitignored SQLite file with no migration or backup path.

- A. Localhost checkout is the whole story; a commit is the release; deleting `data/sentiment.db` is an acceptable recovery
- B. Same, plus a version tag and a changelog entry per release
- C. Add a minimal pipeline on push (install, lint, `pytest`), still localhost-only
- D. Add a real migration and backup path for the SQLite file
- X. Other (please specify)

[Answer]: A. Localhost checkout is the whole story; a commit is the release; deleting `data/sentiment.db` is an acceptable recovery

## Q7. Should code style be enforced mechanically?

Twelve conventions hold across the code (module docstrings, full annotations, `#:` constant docs,
domain exceptions mapped at the edge, one error envelope, parameterised SQL only, redacted `repr`s,
no pydantic in `app/`), and nothing enforces any of them: no formatter, linter, or type checker is
configured. Measured context: a `ruff` 0.16.9 binary exists on this machine outside the project, and
run against `app/` it reports 16 findings (9 auto-fixable, 6 of them the documented FastAPI idiom for
dependency defaults) and would reformat 12 of 22 files. The project deliberately caps dependencies.

- A. Adopt `ruff` for formatting and linting with an explicit rule set (including its security rules), run as a pre-commit hook or a stage check
- B. Adopt `black` plus `flake8` instead
- C. Keep convention-and-review-only, and state that choice in the team rules
- X. Other (please specify)

[Answer]: A. Adopt `ruff` for formatting and linting with an explicit rule set (including its security rules), run as a pre-commit hook or a stage check

## Q8. Anything to make binding rather than merely observed? (select all that apply)

Observed conventions become team practice; only constraints you state here become hard `ALWAYS` /
`NEVER` rules in the project's memory. The credential line is the one the security review judged
warranted, because a real key pasted into any committed record file would land in git with nothing
scanning for it — and any scanner would need an allowlist, since four test fixtures already use fake
keys shaped exactly like real ones.

- A. NEVER commit, log, print, or paste a real credential into the repository or any workflow record file
- B. ALWAYS keep the app localhost-only (no cloud, no Docker, no hosted deploy)
- C. ALWAYS route every failure through the single error envelope
- D. NEVER use pydantic models inside `app/` code (stdlib dataclasses only)
- E. None — leave all of the above as observations
- X. Other (please specify)

[Answer]: A, B, C — the credential rule, localhost-only, and the single error envelope

## Open points carried to integration

- Q5's answer puts the whole application under the 80% floor, so tests for the live Jev client
  become construction work, and the floor has to run in a CI job even though this scope skips the CI
  Pipeline stage — where that job lives is an open point for design and build.
- Q4's answer (`custom`) needs its ordering sentence in `team-practices.md`: acceptance/API tests
  first, lower-level unit tests after implementation.
- Q1's answer adds a scope-name tag on the merged commit, which the framework default does not carry.
