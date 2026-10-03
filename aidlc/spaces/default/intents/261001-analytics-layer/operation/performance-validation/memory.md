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
- 2026-10-03T13:30:00Z — read the two carried Unverified targets as still Unverified. A genuine partial outcome appeared during testing (one endpoint answered 200 inside its budget while the other answered 500), and it was explicitly refused as the NFR4.6 instrument: a storage-timing accident produces no view-level partial-failure marker and is invisible to the user. Building the markup here would duplicate `u3-analytics-view`'s deliverable and repeat the disclosed `app/terms.py` boundary violation.
- 2026-10-03T13:32:00Z — read "validate the NFRs" as distinct from "find every performance problem". Six measured findings carry no NFR row because no requirement claims them, and they are reported as findings rather than retrofitted onto a requirement that does not exist.
- 2026-10-03T13:35:00Z — read the unbounded-payload result as a boundary case rather than a breach: p99 199.700 ms against a 200 ms budget is 0.3 ms inside it. The earlier "over budget" reading does not reproduce as a breach on this hardware, and the byte magnitude does.

## Deviations
- 2026-10-03T13:37:00Z — wrote the load generator with the standard library only (`http.client`, `threading`, `concurrent.futures`, `statistics`) rather than adding a load-testing framework, because `C-6` caps declared runtime dependencies at two and the harness had to stay re-runnable by whoever picks this up.
- 2026-10-03T13:39:00Z — ran every scenario against a real `uvicorn` subprocess over loopback with the store isolated by `os.chdir` into a `tempfile.mkdtemp()`, rather than in-process ASGI calls, so the measurement includes the real server, the real socket and the real connection model.

## Tradeoffs
- 2026-10-03T13:41:00Z — included a control scenario (`/v1/health`) at every concurrency level specifically so a superlinear result could not be dismissed as a harness artefact. It reached 2324 rps at c=32 with flat per-request CPU, which is what makes the analytics attribution credible.
- 2026-10-03T13:43:00Z - reproduced the whole ramp across two independent server runs to ~1 % (11.40/11.48, 166.95/166.36, 712.51/715.67 ms) rather than publishing a single run, accepting the cost of a second run for a number that can be trusted.
- 2026-10-03T13:45:00Z — reported `Unverified` for NFR4.6 and NFR4.7 a second time rather than closing them with an instrument built against another Unit's markup. Two open targets cost less than a second disclosed boundary violation.

## Open questions
- 2026-10-03T13:50:00Z — six measured findings have no inception NFR parent: superlinear concurrency degradation, mixed-load budget breach, writer lockout, uncapped linear payload, the ~2.8-core ceiling, and the RSS plateau. The concurrency posture of this system was never specified as a requirement, which is why it went unvalidated until now.
- 2026-10-03T13:51:00Z — throughput peaks at c=2 and falls as clients are added (157.8 rps at c=2, 41.2 at c=64). No requirement states a throughput target, so nothing is breached; but a single-user local app has no reason to care, and the finding matters only if that ever changes.
