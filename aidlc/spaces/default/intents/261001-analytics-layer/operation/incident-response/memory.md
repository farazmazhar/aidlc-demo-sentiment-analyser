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
- 2026-10-03T13:05:00Z — read the stage's declared output list (SSM Automation runbooks, AWS Incident Manager, AWS Backup, PagerDuty, an on-call rotation, an escalation matrix with named humans) as inapplicable **per element**, and answered the Step-2 questions from measurement instead. There is no rota to ask the human about, so asking one would have been asking them to invent a second person.
- 2026-10-03T13:10:00Z — read "escalation path" as satisfied by recording the path's **terminal state** (the operator, for every severity) rather than by naming a responder. `memory/phases/operation.md` § Incident Response asks runbooks to carry escalation paths and contact information; the honest fulfilment is a path of length one plus machine-local facts (port, file path, check command), because there is no second person to contact.
- 2026-10-03T13:15:00Z — read RB3's deliberate "no procedure" as something to **re-state and quantify**, not to fill. Measuring the whole position (0 commits, 1 manual R5 copy, no `scripts/`, no backup API) showed the gap is wider than upstream recorded: `POST /v1/analyses/export` requires an `import_id`, excludes every `import_id IS NULL` row, and returns 404 for a store of only single-analysis rows — so the export is a *view*, not a backup.
- 2026-10-03T13:20:00Z — classified eleven failure modes by **consequence, never by likelihood**, because the largest real request sample this project has produced is 27 (`alarms.md` §4). Any "most likely failure mode" ranking would have been invented.
- 2026-10-03T13:25:00Z — read `/v1/health`'s blindness to the store as an incident-response fact rather than an observability footnote, and made it OG-4: measured `200` in 1.4 ms while every analytics read returned `500`, so the endpoint an operator trusts most cannot detect the failure the analytics layer actually has.

## Deviations
- 2026-10-03T13:30:00Z — wrote **no SSM Automation document**, for any failure mode. There is no Systems Manager, because there is no AWS account, no CLI, no credential and no IaC (`infrastructure-specification.md` §5); a runbook inside a service that does not exist is a document about nothing. The eleven procedures are shell in `runbooks.md`, each verified by running it.
- 2026-10-03T13:35:00Z — wrote **no** status-update cadence, no incident-commander role and no contact table. `incident-plan.md` §3.1/§3.2 answer both substitutions with "nothing, and that is the honest answer", and §5 substitutes a durable per-incident file — which is *better* here than a channel, because there is no audience to orient and a file survives the terminal.
- 2026-10-03T13:40:00Z — did **not** correct `health-check-report.md` §2.3, which names `python -m app.main` as a documented run path. Measured: `app/main.py` has no `__main__` guard, so that invocation exits with a `RuntimeWarning` and never opens the port. It is another stage's artifact, and adding the guard would be a code change — so it is recorded as **OQ-IR-5** with the measurement rather than fixed here.

## Tradeoffs
- 2026-10-03T13:45:00Z — re-measured RB1 and RB2 instead of inheriting them, at the cost of about ten minutes, because `runbooks.md` §6.1 inlines RB2 and an inlined runbook that drifts from its source is worse than no runbook. Both reproduced: RB1 store byte-identical after the failure, RB2 2 rows → 2 rows with all three indexes surviving and an idempotent re-upgrade.
- 2026-10-03T13:50:00Z — quoted the **5.0 s per failing request** figure rather than only the `database is locked` string. The string says what happened; the 5 s says what it costs, and the cost is the thing an operator needs at 1am. It also forced the honest corollary: IR-1 is transient, so the runbook says *do not restart*.
- 2026-10-03T13:55:00Z — kept `alarms.md` §5's four-level severity scheme rather than designing one for this stage, so severities stay comparable across the operation phase. The criteria were rewritten against measured failure modes; the shape was inherited.
- 2026-10-03T14:00:00Z — quoted a reproduction that first **failed to fail**. A v3 store boots cleanly, because the current relation already *is* v1-shaped so the rebuild never runs and no `CHECK` is exercised; the trigger is an older physical shape (missing `import_id`) plus an out-of-domain label. Stating the trigger precisely mattered more than a clean-looking reproduction, because "a v3 store" is the obvious wrong answer.

## Open questions
- 2026-10-03T14:05:00Z — **OQ-IR-1** (highest value): how often should the store be copied? Release-step-only (today), per-boot, or per-incident. Nothing in `team.md`/`project.md` settles it, it is a decision about the operator's own machine and data, and it is the difference between an RPO of "one session" and an unbounded one. Per-boot is not obviously safe to propose either: F-01 warns the migration hazard is conditional, and a habitual `cp` would erode the release discipline R5 actually provides.
- 2026-10-03T14:10:00Z — **OQ-IR-2**: should `app/db.py` set an explicit `busy_timeout`? Measured: none is set, so CPython's 5.0 s default applies, and a contended read blocks for 5 s and *still* fails. Raise it (wait longer, succeed more, stall a worker thread), shorten it (fail fast), or leave it. `reliability-design.md` §5 rules out read-path retries, but a driver timeout is not a retry, so that ruling does not decide it.
- 2026-10-03T14:15:00Z — **OQ-IR-3** and **OQ-IR-4** both change frozen contracts and belong to the units that own them, not to an operations stage: `EXPORT_COLUMNS` omits `probabilities` and `intensity` (so even a successful export is lossy), and `/v1/health` does not read the store (so it cannot detect IR-1). Adding a store read to a health endpoint also makes health fail for a reason unrelated to process health — a real trade, not a monitoring tweak.
- 2026-10-03T14:20:00Z — five upstream observability open items stay open and are re-referenced rather than re-opened (**OQ-1** series-width cap, **OQ-2** `422` logging, **OQ-3** the `--host` bypass, **OQ-4** store mode `644`, **OQ-5** log redirection). **OQ-5** is the cheapest available improvement to every row of `incident-plan.md` §6 — one shell redirect — and it is still not taken.
- 2026-10-03T14:25:00Z — no open question was manufactured to fill the file. All five Step-2 questions are answered from measurement, and §3 holds only decisions this stage is not authorised to take.

## Interpretations
- 2026-10-03T12:55:00Z — read the escalation matrix's empty cells as the finding rather than a gap to fill: with one operator, "no escalation path exists; the operator is the last resort" is the accurate row, and a manufactured rota would be fiction.
- 2026-10-03T12:58:00Z — read RTO as the detection time rather than the restart time. Restart-to-serving measured 0.45-0.52 s and diagnosis under 10 s, but nothing detects anything, so "notice" is unbounded. Quoting the half-second alone would have been a fiction.
- 2026-10-03T13:00:00Z — read RPO as "since the last manual copy" and then measured what that copy actually is: exactly one, byte-identical, created by luck during a release rather than by design.

## Deviations
- 2026-10-03T13:02:00Z — did not touch `health-check-report.md` §2.3, which names `python -m app.main` as a documented run path. It was verified not to serve (RuntimeWarning, exit 0, no listener). Correcting another stage's artifact is not this stage's remit, so it is parked as OQ-IR-5 with the measurement rather than edited in place.
- 2026-10-03T13:04:00Z — reproduced every failure mode in this stage rather than inheriting the previous stage's description of it. Four of them behaved differently on reproduction.

## Tradeoffs
- 2026-10-03T13:06:00Z — wrote the runbook's IR-1 instruction as "do not restart", because the fault was measured transient (a retry succeeded 2.63 s after a failure) while `app/db.py:213` sets no `busy_timeout` so CPython's 5.0 s default applies and the request still fails. Restart is the reflex and it is the wrong one here.
- 2026-10-03T13:08:00Z — declined to propose per-boot store copying as the obvious fix for the missing backup. F-01 shows the migration hazard is conditional, and a habitual `cp` would erode the release discipline R5 provides. OQ-IR-1 is left open with that trade named.
- 2026-10-03T13:10:00Z — replaced "status updates every 15-30 minutes" with a durable per-incident file, because with no stakeholder there is nothing to update and a file outlives the session's terminal.

## Open questions
- 2026-10-03T13:15:00Z — OQ-IR-1: how often the store should be copied. Release-step-only today, per-boot, or per-incident. Per-boot is not obviously safe to propose.
- 2026-10-03T13:16:00Z — OQ-IR-5: `health-check-report.md` §2.3 names a run path that does not serve. Correct in place, or leave parked?
- 2026-10-03T13:17:00Z — `/v1/health` answered 200 in 1.4 ms while every analytics read was 500. A green health line cannot detect IR-1, which weakens the health check as an operational signal.
- 2026-10-03T13:18:00Z — `rb1`'s stated trigger is wrong: a v3 store boots clean because the current relation already is v1-shaped. The rebuild fires only on an older physical shape plus an out-of-domain label.
- 2026-10-03T13:19:00Z — `/v2/analytics/terms` is width-insensitive (136 B, 2.2 ms at a 100-year range), which localises the unbounded-payload latency defect to `/summary` alone.
