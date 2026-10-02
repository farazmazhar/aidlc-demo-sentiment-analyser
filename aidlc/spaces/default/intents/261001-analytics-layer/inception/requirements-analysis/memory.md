<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-02T10:32:43Z - read the description's "reuse a simple tokenizer" as licensing a promotion of the existing private `_WORD` regex rather than writing a new one, and split tokenization from significance-filtering into two operations so the offline engine's scoring stays byte-for-byte unchanged by the analytics stopword list.
- 2026-10-02T10:32:43Z - read "shares" as a fraction rather than a percentage only after the review challenged it; the first draft invented the unit, and the reviewer's point that a contract choice with no recorded answer behind it should have been a question was accepted as correct.
- 2026-10-02T10:32:43Z - read constraint C-2 ("analytics reads stored rows and does not call the engine") as making the `SentimentClient` reuse requirement vacuous for both analytics endpoints, rather than as a missing engine integration to be built.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-02T10:32:43Z - put five review findings to the human instead of closing them in the revision: whether this feature fixes R-01, the share unit, inverted-range behaviour, an `import_id` matching no rows, and the page's `import_id` disposition. Four were genuine policy choices the artifact could not settle.
- 2026-10-02T10:32:43Z - left `requirements-analysis-questions.md` untouched after the summary confirmation rather than appending the five review follow-ups, because the confirmation receipt binds the file's content hash and editing it to hold post-review answers would risk invalidating a receipt the review already validated against.
- 2026-10-02T10:32:43Z - added a scalability NFR that imposes no cap on the unbounded series, after the review caught NFR1 claiming "no unbounded result set exists" when nothing bounded the series length; the honest bound is stated instead of an invented ceiling.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-02T10:32:43Z - accepted all eight affirmed practices obligations into this feature over shipping only the touched ones, roughly doubling the work past the analytics layer, on the human's explicit choice.
- 2026-10-02T10:32:43Z - chose to fix R-01 rather than ship a known-failing reproducing test, because the affirmed Q5 rule closes R-01's exemption and a test that documents a still-broken defect would leave FR8.4 and FR8.5 unable to both hold.
- 2026-10-02T10:32:43Z - restricted tokenization to ASCII letters and recorded non-Latin scripts as an accepted limitation (FR4.6) rather than adding Unicode segmentation, because the two-runtime-dependency cap forbids a segmentation library and the description asked only for a simple tokenizer.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-02T10:32:43Z - the lockfile format and its consuming install command are unset, so FR7.1's "every install resolves to the same set" has no determinable pass/fail until Contract Design fixes both.
- 2026-10-02T10:32:43Z - which secret scanner and dependency audit tool FR7.3 requires is unresolved; the four known fake-key fixtures must be allowlisted before whichever tool's first run.
- 2026-10-02T10:32:43Z - the licence FR7.4 requires is unchosen; every installed dependency is permissive, so nothing forces the decision.
- 2026-10-02T10:32:43Z - constraint C-12's soft one-session target is now at risk: eight practices obligations and an R-01 fix landed in the same feature as the analytics layer.
