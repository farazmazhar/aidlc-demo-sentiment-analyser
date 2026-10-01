# Project-Level Rules

> Project-specific specialisation and corrections. Loaded after `org.md` and
> `team.md` as strict-additive guidance; contradictions with broader policy
> are rejected. Populated by practices-discovery and the self-learning loop.
>
> Use sparingly: most teams don't need a project layer. Reach for it
> only when this specific project needs stable, durable guidance beyond the
> team practice (for example, package-specific release checks or an additional
> regression suite for a legacy component).

## Way of Working

<!-- Project-specific specialisation. Example: -->
<!-- This monorepo requires package-scoped branch names and a package owner -->
<!-- review in addition to the team's normal merge policy. -->

## Walking Skeleton

<!-- Project-specific specialisation. Example: -->
<!-- The walking skeleton must exercise the legacy service adapter as well -->
<!-- as the new service boundary. -->

## Testing Posture

<!-- Project-specific specialisation. -->

## Guard Policy

<!-- Project-specific. Mode: strict, relaxed, or off. Strict here holds for every intent and cannot be changed from chat. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

<!-- Project-specific specialisation. -->

## Code Style

<!-- Project-specific specialisation. -->

## Tech Stack

<!-- Technology choices locked for this project. -->

- Build it in Python — this project is built in Python, overriding the original request's preference for TypeScript on Bun/Node. (learned 2026-09-29) <!-- cid:260929-sentiment-analysis:intent-capture:5302a80fce8548da55d30e775f4eede61208facc61e9f80568ce4b4ba70d3471 -->

## Decided

<!-- Decisions made in earlier stages that should not be re-asked. -->
<!-- Format: DECIDED: [decision] (Stage [slug], [date]) -->

## Scope Overrides

<!-- Custom scope rules for this project. -->

## Forbidden

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: NEVER [behavior] (affirmed [date]) -->
<!-- Example: NEVER throw exceptions across service layer boundaries (affirmed 2026-05-17) -->

NEVER commit, log, print, paste, or attach a real credential (the OpenRouter key or any future secret) into the repository or any artifact under `aidlc/`; the only permitted locations are the gitignored `config.local.toml` and process memory. (affirmed 2026-09-30)

## Mandated

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: ALWAYS [behavior] (affirmed [date]) -->
<!-- Example: ALWAYS use Result<T,E> for fallible operations in service layer (affirmed 2026-05-17) -->

ALWAYS keep the app localhost-only: bound to loopback (127.0.0.1) and unauthenticated by design; any non-loopback bind, hosted deploy or change to the authentication posture requires a fresh threat model. (affirmed 2026-09-30)

ALWAYS route every failure the application code raises through the single error envelope; framework-generated routing errors (unknown path, wrong method, missing static asset) keep FastAPI's `{"detail": …}` shape. (affirmed 2026-09-30)

## Corrections

<!-- Project-specific corrections from human feedback. -->
<!-- Format: NEVER/ALWAYS [behavior] (learned [date]) -->
- The review's two Major findings were both boundary gaps of the same kind: the mode-precedence rule (FR1.2 vs FR1.3) and undefined empty-input behaviour on POST /analyze. Write the precedence rule and the invalid-input behaviour explicitly while drafting requirements, before the summary checkpoint, rather than leaving them to a reviewer. (learned 2026-09-29) <!-- cid:260929-sentiment-analysis:requirements-analysis:4296742ea31bdaf4a0e4718e35d1d62f7419a5de13ae8d1429cd11cd3ffac41a -->
- The review's Major finding (R-01) was a thread-affinity bug: a sqlite3 connection created in a FastAPI sync-generator dependency is opened in one thread-pool worker and used by the endpoint in another, so overlapping requests raise sqlite3.ProgrammingError while sequential ones pass. When a connection is created per request, decide check_same_thread and the connection lifecycle explicitly instead of inheriting the default. (learned 2026-09-29) <!-- cid:260929-sentiment-analysis:code-generation:566d27e59349ea455bf2c3ab77a8df50e4810fa80474ddf4f52c5176cac6ff13 -->
- The Minimal strategy generates no additional test-instruction files, so the supporting security review (secret handling, parameterised SQL, boundary validation, no stack-trace leakage) was recorded as a section of the Build and Test Summary instead of its own instruction file; the file set stays exactly what the strategy prescribes. (learned 2026-09-29) <!-- cid:260929-sentiment-analysis:build-and-test:bf9209556196d89d6ea72efa624e9a2aa6e52761567b6e9a5a5ea1b79fa9aabe -->
- The accepted Code Generation review risk (R-01, SQLite connection thread-affinity) is recorded as a known limitation with its evidence, not as a failed target: no requirement in this scope defines a concurrency target, the human accepted the finding at the Code Generation gate, and the sequential single-user flow the requirements describe passes. (learned 2026-09-29) <!-- cid:260929-sentiment-analysis:build-and-test:bfef8567193ba3d17fc79d1a46ef28b8018e8f8c52096abc078be6346e81b070 -->
- handed the developer the repo root and the chosen breadth and let it discover the source surface itself; no application source was inspected before that dispatch, so the deep-versus-skimmed coverage set is the scan's own evidence rather than a precomputed file list. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:reverse-engineering:417ae991def39cedb9b7dcbdd6745e8f8862a90bdce9e57c3764da9a91023104 -->
- condensed the draft's thirty-odd candidate questions into eight, covering the five practice areas and only the decisions evidence could not settle; every option carried the drafted answer so the human chose between reasoned positions rather than from a blank page. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:practices-discovery:f9a4c1b174b604ce7ba9d3d877c82403e021a4e58196d4beedda699120d8f965 -->
- the first guided batch was not written back immediately: one answer came back as "Other" (one branch per scope, merged and tagged with the scope name) and another as "Mixed" without naming the split, so the batch was discussed and re-asked before any answer reached the file; only the settled Q2 and Q3 were written at that point. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:practices-discovery:5b24c7cb59faac235e3fcd54a6dc124688ed4b813bc62a88cf9ea89fbff7f805 -->
- the human's coverage answer counts the whole application against the 80% floor, so tests for the live Jev client become construction work instead of the floor passing by excluding it; the cheaper reading was available and was not chosen. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:practices-discovery:8fac61a6ec53e6238e9cf66ab06919998bf8dafd91cde65af495d3ca13de91be -->
- read the three answers that depart from the initial description (keep the in-app sign-in flow, warn rather than fail at startup, drop intensity) as deliberate informed overrides rather than as contradictions to re-open, because each question's own text named the conflicting description before the human chose; they are recorded as an assumption in the artifact. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:requirements-analysis:2efc5df52367f00ac5c4e0b2d87644b9aa3f3bef5d72293672ca4d9e21065081 -->
- loaded the product-agent knowledge set selectively (persona, principles, brownfield safeguards, rules-reading, verification, requirements guide) instead of every path the directive listed; the remaining entries are templates and schemas the stage body never consults. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:requirements-analysis:a0df30349361a78ef7389abdf509a08b8103636b7c5a08018f6aaa30d18e1f0f -->
- read the three independent reviews as adversarial evidence rather than as opinions to weigh, and folded each finding that could be checked against the code or the requirements into the revision, keeping only the two the reviewers themselves flagged as human judgement calls. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:user-stories:2b851aae630df0f85c09690c207b4e9367ef34c4abdc3e077a99b21b12c0f256 -->
- the draft's 13 stories became 13 different ones: nine requirement statements the first cut left unowned now have stories, four single-statement stories were merged into wider ones, and the live-attempt story was rewritten after the human's ruling rather than carrying the reviewer's contradiction into the gate. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:user-stories:5ba9d209bcb2ec5be8c30c2e6fe802384bb88aa5039c41f2b55b20e23f52491f -->
- asked the human for one mid-stage ruling (the live-attempt behaviour) instead of writing both candidate criteria into the artifact or silently choosing between the story and the test that pins today's behaviour. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:user-stories:ccdff2fade7828b7e7573861b64e9e1e87de1a8abcabd22e5576822ed3159b55 -->
- designed the mockups directly from the stories and requirements because this scope skips the rough-mockups step and no wireframe exists; the missing input is named in the artifact rather than filled with invented wireframes. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:refined-mockups:29d91bba4f8869147359c69af6dea73db4a12e7436ad9b9807470bcfc40c9034 -->
- the specification maps every component to native HTML and the page's existing class names instead of inventing a design system, because the project has none and caps its dependencies at two runtime packages; the mapping artifact states that decision rather than implying a library exists. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:refined-mockups:7c3ece630d6909bc9d81b6c2ad2481c1111eb1a63bc1cc93b7052468873d558f -->
- specified only the states the app can actually reach (loading, empty, success, invalid input, live-mode failure) rather than a full state matrix including long-text and offline-versus-live as separate screens; those two live inside the success state and the indicator so the checklist stays checkable. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:refined-mockups:cb6969d853d3705e74756ab1bc6201e6617c25357d79f3f47fae16afd2adbc72 -->
- read the human's "event/queue style handoff" answer as an in-process handoff rather than a broker-backed one, because the intent's constraints (localhost only, no cloud, two runtime dependencies) rule an external broker out; the reading is written into the answer cell and into ADR-003 so it can be corrected at the gate rather than discovered in Construction. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:domain-design:53bf950c53b9a449d56ff27c297f029f88b4ae5cad5a41467016cc0ce04faf56 -->
- read the "strict topological edges only, no parallel units" answer as satisfied trivially by a single-unit DAG rather than as a demand for a chain of units; the artifact states that no parallel opportunity exists rather than inventing units to order. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:units-generation:95e19cd8bb726bb53fcf639e8d6ace0c7f22bab7edfd0621d34126daa70b5690 -->
- the story map carries a reading order for the work inside the single unit; the stage note forbids recommending an implementation order, so the section is labelled as a comprehension order derived from the stories' own dependencies and explicitly leaves economic sequencing to Delivery Planning. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:units-generation:94d684ae7887b6e02958e6aade0181089e1523d1e0191532be848a1a0c104ed9 -->
- kept the page's own routes out of the data contract (they serve markup with no schema) while including the health endpoint inside the versioned surface, because the answers pinned "the HTTP surface the unit exposes" as the boundary rather than only the JSON API. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:contract-design:983b43c531e9fda6d4878bd87ca60ab5a2cc6bd53736cde4d3b665334757de0e -->
- wrote the version prefix into the contract as `/v1` even though the running routes have no prefix today; the contract therefore describes a change the code must make rather than the current state, which the artifact states so nobody reads it as documentation of what exists. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:contract-design:8f6c6c7cad5b288ffc19c2b8830a02d563c35b99c5defca7f937a7ab39c32d06 -->
- the first draft described the API from the requirements and stories instead of from the running routes, and the review caught three critical mismatches (paths unversioned in code, the history response wrapped, the error envelope nested under `error` with a details array) plus the health fields, the auth endpoints and the engine status codes; the lesson is that a contract artifact must be read back against the code it describes before the review, not after. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:contract-design:153d40255c3003a080ebda030c5665a838b6b3ff3496c68e93cf87274723bdb2 -->
- left four contract points as open questions (the live-refusal machine code and status, the absent-limit default, whether health is versioned, the outbound timeout value) instead of inventing values, since Code Generation can wire a stated number but cannot choose a policy. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:contract-design:7aa744c0ec490ceb6f5f635a5aed4b96f48de5f8808af6b6db112b688c7724c0 -->
- read the human's "riskiest parts first" answer as an ordering *inside* the single Bolt rather than as a demand for several Bolts, because the same person chose one Bolt for the unit; the two answers only cohere that way. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:delivery-planning:b5e898000f469c23fdc2d73b0a8b30c669ea4dc2ccfe832852ed80beeb8e2fa8 -->
- proposed a verification command that installs, runs the suite and then boots the app and reads its health endpoint, rather than the suite alone, because the team's affirmed command includes a real run; I ran it before proposing it (52 tests pass, health answers) so the human approves something proven, not something plausible. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:delivery-planning:dc830ab624ec55edf235aef4736e099e03b5cd1856c147f9d5a83dec030cadc3 -->
- the verification-command approval could not be recorded: the workspace's harness projection names an unsupported harness, so no receipt could bind the human's "Approve"; the field is left unset and the first Construction checkpoint will ask again rather than the approval being faked. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:delivery-planning:0e9a8be3ddaa1d600c54cac24d0e6dba6048dd9bb84e4c70778dad0b42d48ed0 -->
- one Bolt for the whole unit with a risk-first internal order, rather than several thin Bolts cutting across it: the unit is one deployable, and splitting it would multiply the checkpoint overhead without buying a smaller risk surface. (learned 2026-09-30) <!-- cid:260930-sentiment-v1:delivery-planning:56630ff9edf55e805fdcd4743f6f62fc82344f00787e5309db5c50b09bf56623 -->
