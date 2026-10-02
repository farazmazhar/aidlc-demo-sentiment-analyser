# Discovered Rules

> **Lead draft for intent `261001-analytics-layer`, integrated at Step 5.** Nothing
> here is affirmed until the gate. Exactly the constraints below were stated by a
> human — either in an interview, or carried forward from an earlier affirmation —
> and behaviour the scan merely observed is not promoted to a rule; it stays a
> convention in `team-practices.md`. Where a spoke *proposed* a rule and the human
> did not adopt it, it is not here.
> Each non-blank line below that is not a comment or a heading is a rule, and is
> promoted verbatim under the matching heading in
> `aidlc/spaces/default/memory/project.md` at the affirmation gate.

Sources, per line:

- **(affirmed 2026-09-30)** — carried forward unchanged from the prior affirmation;
  already live in `memory/project.md`.
- **(affirmed 2026-10-01)** — stated by the human in this run's feasibility interview
  and recorded in
  `aidlc/spaces/default/intents/261001-analytics-layer/ideation/feasibility/constraint-register.md`
  as `C-1`, `C-5`, `C-6`, sourced to `[desc]` (the human's own written request) or to
  a numbered interview answer.
- **(affirmed 2026-10-02, Qn)** — stated by the human in this run's practices-discovery
  interview; `Qn` is the question number in
  `practices-discovery-questions.md`.

## Mandated

ALWAYS keep the app localhost-only: bound to loopback (127.0.0.1) and unauthenticated by design; any non-loopback bind, hosted deploy or change to the authentication posture requires a fresh threat model. (affirmed 2026-09-30; reaffirmed 2026-10-02, Q11)
ALWAYS enforce that loopback bind at startup so a non-loopback host fails loudly; a documented uvicorn default is documentation, not enforcement, and the `HOST` constant must be the thing the run path actually consumes. (affirmed 2026-10-02, Q11)
ALWAYS route every failure the application code raises through the single error envelope; framework-generated routing errors (unknown path, wrong method, missing static asset) keep FastAPI's `{"detail": …}` shape. (affirmed 2026-09-30)
ALWAYS declare runtime dependencies as exactly two — `fastapi` and `uvicorn` — and keep every development tool (test runner, coverage, linter, formatter, and any type checker added later) in the `dev` extra, so the runtime declaration never names more than those two. Resolution pulling transitive distributions behind them is expected and is not a breach of this rule; declaring a third runtime dependency is. (affirmed 2026-10-01, constraint `C-6`; mechanically enforced by `tests/test_config.py`, which asserts the declared list. Restated at Step 5 because "exactly two runtime packages" is false in distribution terms — 14 distributions install, one of them `opentelemetry-api`, hard-required by `fastapi` and chosen by nobody.)
ALWAYS evolve the SQLite schema additively and idempotently, so a store already in use migrates forward in place without losing a row and without a destructive rebuild of the data; adding a table or an index is preferred over changing an existing column, and a migration that cannot preserve every row must fail loudly and roll back rather than discard data. (affirmed 2026-10-01, constraint `C-1`; the in-place, one-transaction, rollback-on-`BaseException` migration in `app/db.py` is the evidence this rule describes)
ALWAYS write every commit as `<scope>: <summary> (<scope> scope)`, with a body listing what changed and ending in the measured result, followed by the trailer `Produced by the AI-DLC <scope> workflow for intent <id>.` (affirmed 2026-10-02, Q1)
ALWAYS run the standing gates — the whole-application 80 % line-coverage floor, the `filterwarnings = ["error"]` filter, and the pinned `ruff` rule set — from a platform-neutral verification script that the developer runs. A pre-commit hook does not replace it and a provider CI job does not replace it; with no git remote, a hosted workflow file is a file that has never run. (affirmed 2026-10-02, Q3)
ALWAYS ship a dependency lockfile with hashes, so every install resolves to the same set rather than to whatever the newest compatible versions are that day. (affirmed 2026-10-02, Q6)
ALWAYS put aggregate read queries in the dedicated read module beside `repository` and call them from the route; the service layer is not inserted into the read path. (affirmed 2026-10-02, Q9)
ALWAYS express the layer boundaries as `ruff` `TID251` `banned-api` entries rather than leaving them as prose, so that a boundary breach is a lint failure instead of something only a reviewer can notice. (affirmed 2026-10-02, Q10)
ALWAYS run secret scanning and a dependency audit as part of verification, with the known fake-key fixtures allowlisted so the first run produces signal rather than noise. (affirmed 2026-10-02, Q12)
ALWAYS keep the linter's `target-version` matched to `requires-python`, so the project's static analysis targets the interpreter the application actually runs on. (affirmed 2026-10-02, Q13)
ALWAYS pin computed aggregate results with hand-written expected values stated per requirement, and always assert that indexes created by a migration still exist afterwards; the coverage floor is not a substitute for either. (affirmed 2026-10-02, Q14)

## Forbidden

NEVER commit, log, print, paste, or attach a real credential (the OpenRouter key or any future secret) into the repository or any artifact under `aidlc/`; the only permitted locations are the gitignored `config.local.toml` and process memory. (affirmed 2026-09-30)
NEVER introduce a new external service, hosted dependency, cloud component or network call to compute anything for this app; every capability, including analytics, is computed in-process from locally stored state. (affirmed 2026-10-01, constraint `C-5`)
NEVER ship a defect without a test that reproduces it. R-01's exemption is closed with this rule; closing it requires fixing the in-process ASGI harness first, because no test written against today's harness can reproduce it. (affirmed 2026-10-02, Q5)