<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

## Interpretations
- 2026-10-03T12:20:00Z — read the stage's CloudWatch/X-Ray output list as unbuildable here (no account, no CLI, no IaC, and `C-6` capping runtime deps at two) and designed the observability that genuinely exists instead: two real log streams on a live process, an enumerable migration lifecycle, and thresholds derived from measured distributions.
- 2026-10-03T12:23:00Z — read "publish the distribution, not the single figure" as the rule for every latency threshold. The recorded 15.24/25.04 ms came from one run; a 25-run distribution puts terms at p50 30.08 with a 59.28 ms max, so the single figure understated the tail and the alarm thresholds were set from the tail.
- 2026-10-03T12:25:00Z — read "error-rate threshold" as undefendable with 27 requests and no traffic history, and used absolute counts instead of inventing a percentage.

## Deviations
- 2026-10-03T12:22:00Z — the dispatch brief asserted that `app/analytics.py` logs failures; it does not. The record is emitted at `app/routes.py:364,398`. Corrected the premise rather than writing an artifact that contradicted the code.
- 2026-10-03T12:27:00Z — upgraded `health-check-report.md` §2.3's `--host` bypass from code-reading to measurement: `resolve_bind_host("127.0.0.2")` refuses, yet the CLI bound and served 200 with no refusal logged. The claim got stronger and the artifact it came from got corrected.
- 2026-10-03T12:29:00Z — recorded the store's file mode as measured (644) against the check's expected 600, and left it anomalous rather than normalising it.

## Tradeoffs
- 2026-10-03T12:31:00Z — proved stream attribution by running the server with a logger-naming format rather than inferring it from configuration, because stdout/stderr interleaving is exactly the kind of thing that is wrong in the docs and right in practice.
- 2026-10-03T12:33:00Z — ran the logging revert test on a scratch copy so the failure it produced (`the storage failure was swallowed rather than logged`, while the response assertions still passed) could be observed without touching the workspace.

## Open questions
- 2026-10-03T12:40:00Z — a 422 emits no application record at all: measured 4 x 422, 0 records. `NFR8.2` names both codes but the test covers only the storage path. A real observability hole.
- 2026-10-03T12:41:00Z — the shipped `logger.error` carries no stack trace although two design artifacts claim "code and stack". The requirement is met; the artifact is not.
- 2026-10-03T12:42:00Z — a failed startup emits no `app.*` record; it surfaces through `uvicorn.error` (measured: 0 application records, exit 3, port never opened). An operator watching only application logs would see nothing.
- 2026-10-03T12:43:00Z — the access log carries no duration field, so every latency figure in this project is stopwatch-measured rather than read from a log line.
- 2026-10-03T12:44:00Z — there is still no alerting channel of any kind, and no store backup. Every threshold in `alarms.md` is marked manual for that reason.
