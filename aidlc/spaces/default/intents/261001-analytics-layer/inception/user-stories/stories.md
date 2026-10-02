# User Stories — sentiment-opencode v2 analytics layer

> **Revision 2**, addressing the advisory review recorded at
> `.aidlc-engine/reviews/user-stories/stage/5c0e27715c3878e5/1.review.md`
> (`NOT-READY`, 2 Critical / 13 Major / 7 Minor). Both Criticals were inherited
> from `requirements.md` rather than introduced here, and are dispositioned in
> **Corrections required in `requirements.md`** below.
>
> **35 stories, one persona, eight groups.** The plan questions in
> `user-stories-questions.md` settled: one persona (Q1); every `FR7` obligation and
> the R-01 fix become stories of their own (Q2); groups map to the FR feature
> groups (Q3); one story per coherent contract (Q4); and all nine NFRs become
> stories (Q5). Q4 estimated 14–18 stories; honouring Q2 and Q5 literally produces
> 35, and the human chose to accept the overhead rather than re-group work it had
> said it wanted kept whole.
>
> **`FR8` is not a story group.** The nine test requirements (`FR8.1`–`FR8.9`) were
> not covered by Q2 or Q5 and are carried as acceptance criteria inside the
> stories they protect. **Group `US8` therefore covers the NFRs, not `FR8`** — the
> numbering is deliberate and the mismatch is called out here so no reader assumes
> `US8.x` implements `FR8.x`.
>
> **Format.** `As a [persona], I want [goal], so that [benefit].` Acceptance
> criteria are Given/When/Then. Priority is MoSCoW; the approved scope is unchanged
> by a priority label, and priority informs Delivery Planning rather than trimming
> anything out of it.
>
> **Upstream inputs this set was built from.** `requirements.md` (Requirements
> Analysis, the authority for every `FR`/`NFR` id below); `personas.md` (this
> stage's persona draft); `user-stories-assessment.md` (the Execute decision);
> `user-stories-questions.md` (the plan and its five answers).
> `business-overview.md` and `component-inventory.md` from
> `aidlc/spaces/default/codekb/sentiment-opencode/` supplied the domain vocabulary
> and the component seams the stories must not cross — the read layer is a new
> component beside `repository`, and no story may put a query in the route.
> `team-practices.md` supplied the testing posture (`Methodology: custom`, the
> acceptance-before-implementation `Ordering`, the no-mock doubles policy) and the
> four accidents that must not be codified, one of which — the private `_WORD`
> regex — is the direct ancestor of `US4.2`.

## Story map

| Group | Feature | Stories | Covers |
|---|---|---|---|
| US1 | Analytics read layer and connection handling | 2 | `FR1.1`–`FR1.6` |
| US2 | Summary endpoint | 5 | `FR2.1`–`FR2.13` |
| US3 | Terms endpoint | 2 | `FR3.1`–`FR3.8` |
| US4 | Term extraction | 2 | `FR4.1`–`FR4.6` |
| US5 | Additive migration | **1** (`US5.2` merged into `US5.1`) | `FR5.1`–`FR5.7` |
| US6 | Analytics view | 5 | `FR6.1`–`FR6.9` |
| US7 | Platform obligations | 9 | `FR7.1`–`FR7.9` |
| US8 | Quality attributes | 9 | `NFR1`–`NFR9` |
| **Total** | | **35** | 85 upstream ids: 84 `OK`, 1 `N/A`, 0 gaps, 0 orphan stories |

**Dependency order** (derived from the stories' own dependencies, recorded so the
sequence is comprehensible — not an economic plan, which is Delivery Planning's
call). Seven edges the first draft omitted and the mob found are marked `+`:

```
US4.2 ──▶ US4.1 ──▶ US3.1 ──▶ US3.2
                 └──▶ US2.1 ──▶ US2.2 ──▶ US2.3
                                   └──▶ US2.4
US1.1 ──▶ US2.1
US5.1 ──▶ US7.9          (the migration lands before the README is updated)
US7.7 ──▶ US1.2
US3.1 ──▶ US2.5
US4.2 ──▶ US7.9
US2.1, US2.2, US2.3, US3.1 ──▶ US6.2 ──▶ US6.3, US6.4 ──▶ US6.5
US7.3 ──▶ US7.2           (US7.3 states its criterion as a dependency of the gates)
US6.1, US8.2, US8.3, US8.5, US8.6 independent of the analytics path
```

**`US7.2 → US7.5` was removed** — the mob verified it is not a real edge. The
verification script and the `TID251` rule set are both config the same commit
touches, but neither must exist for the other.

**The affirmed thin slice is `US1.1 → US2.1 → US2.2 → US2.3 → US6.2`.**
The first draft named `US1.1 → US2.1 → US6.2`, and the developer participant showed
it is **not demonstrable**: `AC6.2.1` renders the per-day series, which is
`US2.3`'s output behind `US2.2`'s range resolution, and neither was in the slice or
in `US6.2`'s dependency list. **Corrected again by the review (`R-03`):** the first
correction put `US2.2` and `US2.3` in the slice but left them out of the dependency
*graph*, so the two sections still disagreed and the slice reproduced the very defect
it was meant to fix. The graph above now carries every edge the slice names.

## Corrections required in `requirements.md`

Six defects in the approved requirements artifact were verified against the shipped
code or against this story set. This stage cannot edit an approved upstream
artifact, so they are registered here and in its Revision 2 section:

| Requirement | Defect | Correction |
|---|---|---|
| `FR2.8` | Specifies averaging "only the rows that carry a confidence value" with a null result for an empty contributor set. `confidence` is `NOT NULL` and the rebuild aborts on a NULL, so the branch is unreachable. | `mean_confidence` averages every row in range, **rounded to four decimals**; `mean_confidence_row_count` equals `total`. The four-decimal rule must be retained in the correction — the first story-side fix dropped it. |
| `FR2.9` / `FR2.10` | **Never reconciled.** `FR2.9` requires one zero-filled entry per day in the resolved range; `FR2.10` requires an empty series for an empty range. Both cannot hold. | Ruled at Q10: a range matching **no rows** returns an empty series; zero-filling applies only to the internal gaps of a range that matched at least one row. `FR2.9` must be qualified accordingly. |
| `FR2.11` | Requires the envelope to carry `field == "query.from"`. The envelope is exactly `{code, message}` with `additionalProperties: false`, so a third key is impossible and `errors[0]` cannot name two fields. | Ruled at Q11: one `VALIDATION_FAILED` whose **message text** names the offending parameter — and both `query.from` and `query.to` for an inverted range. `FR2.12`'s "one new machine code" allowance is unaffected. |
| `FR5.2` | Says the migration creates "**exactly** these indexes, and no others". `sqlite_master` also holds an autoindex the same `init_db` creates, so "exactly three indexes" is false as written. | The requirement must state the three indexes **by name**, and the assertion must match by name. |
| `FR5.3` | Requires index declarations "in `CREATE_ANALYSES_TABLE`". SQLite's `CREATE TABLE` has **no** index declaration — verified rejected by two participants independently. | The rebuild re-creates the indexes explicitly as statements after the copy. |
| `FR7.3` | Says "the **four** known fake-key fixtures". `team.md` repeats the figure; the developer counted **six** literals matching the real key shape. | Reconcile the count before writing any scanner's allowlist. This artifact states no number. |
| `FR6.8` | Cites `[RM-5]` and `[RM-5]` elsewhere. **No `RM-n` ids exist in the Rough Mockups artifacts at all** — the review verified the whole family is unsourceable. | Cite the wireframes finding by its actual heading or section, not by an invented `RM-n`. |

---

## US1 — Analytics read layer and connection handling

### US1.1 — Analytics queries behind one read module  · *slice* · Must Have

**As the Solo Maintainer, I want the analytics queries gathered in one place beside the repository, so that the existing layer boundaries stay true as I add a second kind of read.**

Covers `FR1.1`–`FR1.5` · Depends on: nothing

- **AC1.1.1** Given the route module's body, When I read it, Then no SQL string and no query helper call appears in it — every aggregate lives in the analytics read module. *Decidable by reading the modules; the review (`R-09`) found the original phrased this as a runtime observation no test could decide.*
- **AC1.1.2** Given the read module is called, When I inspect its body, Then it takes the connection as a parameter and never calls `connect` or `close` — it does not own the lifecycle.
- **AC1.1.3** Given any aggregate query, When its SQL is inspected, Then every value is parameter-bound and no SQL text is built by interpolation. **This is the single owning criterion for parameter binding across the feature**; `AC8.2.3` no longer repeats it.
- **AC1.1.4** Given the read module's docstring, When it is read, Then it names a single `Single responsibility:` line in the form the existing eleven modules use.
- **AC1.1.5** *(`FR8.1`)* Given both analytics endpoints, When they are exercised with no network, Then both answer entirely from the local store with the offline guard armed.

### US1.2 — Concurrent requests that no longer fail · Must Have

**As the Solo Maintainer, I want overlapping requests to work reliably, so that I can leave the analytics view open while I keep working and never see a failure I cannot explain.**

Covers `FR1.6` · Depends on: `US7.7`

- **AC1.2.1** Given two genuinely overlapping concurrent requests against either analytics endpoint, When both are in flight, Then neither raises `sqlite3.ProgrammingError`. *Strengthened by the mob round: "overlapping" alone can be satisfied on a single thread and would prove nothing. The harness must place the two requests on different threads and the test must assert that they overlapped.*
- **AC1.2.2** Given the concurrency test, When it runs against the fixed harness, Then it passes; and the story carries the **obligation** that reverting the thread-affinity decision makes it fail — checked by the team, not by a conditional clause inside a criterion. *(`FR8.4`) Restated by the mob round: the original wording hid a meta-claim inside a conditional, which no test can decide.*
- **AC1.2.3** Given the module that owns the connection, When its docstring is read, Then it states the chosen thread-affinity decision and the connection lifecycle explicitly, so a later reader sees what was chosen rather than inferring a default.

---

## US2 — Summary endpoint

### US2.1 — Totals, label breakdown and confidence · *slice* · Must Have

**As the Solo Maintainer, I want one call that tells me how much I have analysed, in what mix, and how confident the calls were, so that I can judge the shape of my history without reading rows.**

Covers `FR2.1`, `FR2.3`, `FR2.7`, `FR2.8` (`FR8.2`) · Depends on: `US1.1`

- **AC2.1.1** Given a store with a known seeded mix of labels, When I request the summary, Then `total` equals the number of rows in range and each label's count equals its seeded occurrence, each pinned by a hand-written expected value.
- **AC2.1.2** Given the same store, When I read `shares`, Then each is the label's count over `total` as a **fraction rounded to four decimal places**, never a percentage.
- **AC2.1.3** Given any range, When I read `mean_confidence`, Then it is the arithmetic mean of `confidence` over **every** row in range **rounded to four decimal places**, and `mean_confidence_row_count` equals `total`. *Simplified by triage: the mob verified `confidence` is `NOT NULL` in the shipped schema and that `_is_v1_shape` rebuilds any store that disagrees, so a row without a confidence value cannot exist and the null-tolerant branch could never be exercised. The four-decimal rounding is restored by the review (`R-06`): the simplification had dropped `FR2.8`'s rounding rule, and `FR8.2` requires a hand-pinned value that rounding makes deterministic.*
- **AC2.1.4** Given a range matching no rows, When I read `shares`, Then every share is `null` — **not `0.0`**. *Added by the mob round: this was named by `FR8.2` and pinned by no criterion, so an empty range could have answered `0.0` and passed the whole set. That is the fabricated-number defect the persona's G4 and PN2 exist to prevent.*
- **AC2.1.5** *(`R-14`, corrected by the review)* Given the existing `/v1` endpoints, When I call them after this change, Then each answers exactly as its pre-existing test asserts. **The baseline is the existing suite, not a byte comparison** — the original wording named no baseline and is undefinable after the change. `AC8.5.1` owns the suite-wide form of this.

### US2.2 — Date range resolution · Must Have

**As the Solo Maintainer, I want the range I ask for to mean exactly what I typed, so that a number I read is about the days I meant.**

Covers `FR2.4`, `FR2.5`, `FR2.6` · Depends on: `US2.1`

- **AC2.2.1** Given `from=2026-03-02&to=2026-03-04`, When the summary is computed, Then rows on all three UTC calendar days are included and `2026-03-05` is not — and the fixture **seeds a row on `2026-03-05`**, so the exclusion half of this criterion can fail.
- **AC2.2.2** Given `to` falls on a day with rows timestamped late in that UTC day (23:59:59Z), When the range resolves, Then those rows are included.
- **AC2.2.3** Given only `from`, When the range resolves, Then it spans that day through now; given only `to`, it spans the beginning of history through that day. Neither bound is silently dropped.
- **AC2.2.4** Given neither bound and no `import_id`, When the range resolves, Then it spans the earliest stored analysis date through today inclusive.
- **AC2.2.5** *(`R-04`, added by the review)* Given `from` equal to `to`, When the range resolves, Then exactly that one UTC day is in range — not zero days and not two.
- **AC2.2.6** *(`R-04`, added by the review)* Given a range spanning a month boundary, for example `from=2026-01-30&to=2026-02-02`, When the series is read, Then the days are `01-30`, `01-31`, `02-01` and `02-02` — so no day is skipped or duplicated at the boundary.

### US2.3 — A continuous per-day series · Must Have

**As the Solo Maintainer, I want a day for every day in the range even when nothing happened on it, so that I can see the gaps instead of inferring them from a jump in the line.**

Covers `FR2.9` (`FR8.2`) · Depends on: `US2.2`

- **AC2.3.1** Given a range spanning five days **in which at least one row matched**, When the series is read, Then it holds exactly five entries in ascending date order, and the three empty days report `total` 0, all counts 0 and all shares `null`. **Zero-filling applies only inside a range that matched something; a range that matched nothing returns an empty series (`AC2.4.1`).** *(Corrected by the review's Critical R-01: the original criterion claimed "one entry per day in the resolved range" unconditionally, which contradicted `AC2.4.1` and made two criteria unsatisfiable at once. The human's ruling at Q10 keeps the empty series for a no-match range and limits zero-fill to the internal gaps of a populated one.)*
- **AC2.3.2** Given any populated day, When its entry is read, Then it carries `date`, `total`, `counts`, `shares`, `mean_confidence` **and** `mean_confidence_row_count`.
- **AC2.3.3** Given a populated day, When its entry is read, Then its `mean_confidence_row_count` equals that day's `total`, and its zero-filled siblings carry `null` for both mean fields — so a day with data is never confused with a day without. *(Rewritten by the mob round: the original criterion assumed a per-day subset mean, which the `NOT NULL` finding made unreachable.)*

### US2.4 — Empty, refused and failed answers told apart · Must Have

**As the Solo Maintainer, I want an empty answer, a rejected question and a broken query to look different, so that I never read a failure as "no data".**

Covers `FR2.10`, `FR2.11`, `FR2.12` (`FR8.1`) · Depends on: `US2.2`

- **AC2.4.1** Given a range matching no rows, When I request the summary, Then I get a **200** with `total` 0 and an empty series — never a 404.
- **AC2.4.2** Given an `import_id` that matches nothing, When I request the summary, Then the answer is identical to an empty range: 200, empty series, and **no** store-wide zero-fill.
- **AC2.4.3** Given a malformed `from`, `to` or `import_id`, When I request the summary, Then I get a **422** with `code == "VALIDATION_FAILED"` whose **message text names the offending parameter** — `"query.from"`, `"query.to"` or `"query.import_id"` — exactly as the existing `query.limit` failure does, and nothing is computed. *Corrected by the review's Critical R-02: the original criterion asserted a `field` JSON member, but the envelope is exactly `{code, message}` with `additionalProperties: false`, so a third key is impossible without breaking the frozen shape (`AC8.5.2`).*
- **AC2.4.4** Given `from` later than `to`, When I request the summary, Then I get a **422** with `code == "VALIDATION_FAILED"` whose **message text names both `query.from` and `query.to` as the offending pair**, and the series never applies. *The human's ruling at Q11: one envelope entry naming both fields, rather than two entries or a new machine code, so the shape stays frozen and no second error body is invented.*
- **AC2.4.5** *(`R-19`, added by the review)* Given a negative `limit`, or a `limit` larger than the number of distinct terms in range, When I request the terms, Then the negative value answers 422 naming `query.limit` and the oversized value is honoured by returning every available term, not clamped.
- **AC2.4.5** Given the storage layer raises while reading, When I request the summary, Then I get a **500** carrying a machine code **different from every validation code**, so an unavailable query is never mistaken for a malformed parameter.

### US2.5 — Reading analytics never changes the data · Must Have

**As the Solo Maintainer, I want reading the analytics to leave my store exactly as it was, so that looking at my data carries no risk.**

Covers `FR2.13` · Depends on: `US2.1`

- **AC2.5.1** Given a store, When I capture its row count, schema and content hash, then call either analytics endpoint any number of times, Then all three are identical afterwards.
- **AC2.5.2** Given the analytics read module's body, When I read every SQL string it contains, Then none is an `INSERT`, `UPDATE`, `DELETE` or DDL statement, and the module records no access bookkeeping such as a last-read timestamp. *Bounded to SQL strings and a timestamp, per the review (`R-17`), which found the original open-world "none issues" phrasing had no decidable boundary.*

---

## US3 — Terms endpoint

### US3.1 — Ranked top terms per list · Must Have

**As the Solo Maintainer, I want the most frequent words in my positive and negative text, ranked and readable, so that I can see what the sentiment is actually made of.**

Covers `FR3.1`–`FR3.5`, `FR3.7` (`FR8.2`) · Depends on: `US4.1`

- **AC3.1.1** Given a seeded store with known positive and negative text, When I request the terms, Then each list carries at most 10 entries by default, each with a term and a count, and nothing else — no share, no score.
- **AC3.1.2** Given two terms with equal counts, When the list is read, Then the tie is broken alphabetically, so the order is stable and pinnable by a hand-written expected value.
- **AC3.1.3** Given `limit=1`, When I request the terms, Then each list carries exactly one entry; given `limit=0` or a non-numeric value, I get a **422** naming `field == "query.limit"`.
- **AC3.1.4** Given a label with no rows in range, When I read the response, Then that list is an empty array — never `null`, never a padded top-N.
- **AC3.1.5** Given `import_id` is supplied, When I request the terms, Then only rows of that import contribute, so both endpoints filter identically.

### US3.2 — Terms and summary describing the same rows · Must Have

**As the Solo Maintainer, I want the term lists and the label breakdown computed from exactly the same rows, so that the two halves of the view can never disagree.**

Covers `FR3.6`, `FR3.8` (`FR8.1`) · Depends on: `US3.1`

- **AC3.2.1** Given any range, When I compare the terms endpoint against the summary endpoint, Then both resolve the range identically, including an inverted range, a single bound, an unmatched `import_id` and an empty range.
- **AC3.2.2** Given rows labelled `neutral`, When I request the terms, Then those rows contribute to neither the positive nor the negative list.
- **AC3.2.3** Given a range that is empty for the terms endpoint, When I read it, Then the shape matches the summary's empty shape rather than inventing a different one.

---

## US4 — Term extraction

### US4.1 — Significant terms extracted the simple way · Must Have

**As the Solo Maintainer, I want the obvious filler words left out, so that the ranked list tells me something instead of repeating "the" and "and".**

Covers `FR4.1`, `FR4.2`, `FR4.3`, `FR4.4`, `FR4.6` (`FR8.1`) · Depends on: `US4.2`

- **AC4.1.1** Given text containing words of one, two, three and many characters, When terms are extracted, Then only tokens of **three or more** characters survive.
- **AC4.1.2** Given a token present in the in-repo stopword list in any case, When terms are extracted, Then it is excluded after lowercasing.
- **AC4.1.3** Given text with digits, punctuation or non-Latin scripts, When terms are extracted, Then those runs are token boundaries rather than token characters — and a term written entirely in a non-Latin script contributes nothing, which is a recorded accepted limitation.
- **AC4.1.4** Given the stopword list, When I inspect it, Then it is a single constant held in the repository and applied case-insensitively; no corpus is downloaded and no service is called.
- **AC4.1.5** *(`R-04`, added by the review)* Given text made **entirely** of stopwords, When terms are extracted, Then the label's list is empty rather than a padded or fabricated top-N.
- **AC4.1.6** *(`R-04`, added by the review)* Given a store whose rows are **all one label**, When I request the terms, Then the other label's list is empty and the populated one is unaffected — so an all-positive or all-negative store is a covered case rather than an accident.

### US4.2 — One tokenizer, two jobs, engine untouched · Must Have

**As the Solo Maintainer, I want the word-splitting rule defined once, so that the sentiment engine and the analytics never disagree about what a word is.**

Covers `FR4.5` · Depends on: nothing

- **AC4.2.1** Given the promoted tokenizer module, When I look for `_WORD`, Then the private regex inside the offline engine is gone, and no module imports another module's private name or duplicates the pattern.
- **AC4.2.2** Given the dummy engine's scoring, When its behaviour is compared before and after this change, Then it is **identical** — the 3-character minimum and the stopword list apply to analytics term extraction and not to sentiment scoring.
- **AC4.2.3** Given the tokenizer module's public surface, When I read it, Then tokenizing text and filtering tokens down to significant terms are **two distinct operations**, so a caller cannot accidentally apply the analytics filter to engine scoring.

---

## US5 — Additive migration

### US5.1 — A schema step that only adds · Must Have

**As the Solo Maintainer, I want the schema change to add without removing anything, so that my existing stored analyses survive it untouched.**

Covers `FR5.1`, `FR5.4`, `FR5.5`, `FR5.6`, `FR5.7` (`C-1`) · Depends on: nothing

- **AC5.1.1** Given a store at the previous schema version holding real rows, When the app starts, Then the migration completes and every pre-existing row is still present with its original values.
- **AC5.1.2** Given a store already at the new version, When the app starts, Then the migration is a no-op and nothing changes.
- **AC5.1.3** Given a store whose shape the migration cannot read, When the app starts, Then startup **fails loudly and rolls back** rather than completing partially.
- **AC5.1.4** Given the migration, When its DDL is inspected, Then it is placed after the migrate-or-create branch so it runs on both paths, following the placement `schema_meta` already uses. *(Restated by the mob round: the original criterion described a new table this change does not add.)*
- **AC5.1.5** Given the migration, When it completes, Then the stored schema version reads 4 and the version bump landed in the same transaction as the migration.

**`US5.1` second half — indexes that survive a rebuild** *(merged by triage; no
separate story id, so it does not appear in `traceability.json`)*

> The developer participant verified the additive migration and its index
> assertion are one edit, and splitting them produced a story whose index half
> could not fail independently.

- **AC5.2.1** Given a migrating store, When the migration completes, Then an index named `idx_analyses_created_at` on `created_at`, `idx_analyses_import_id` on `import_id`, and `idx_analyses_label_created_at` on `(label, created_at)` all exist. *(`FR8.3`) Restated by the mob round: the original criterion said "exactly three indexes", which is false — `sqlite_master` also holds an autoindex the same `init_db` creates. The criterion now names the three indexes instead of counting every `type='index'` row.*
- **AC5.2.2** Given the table-rebuild path (`RENAME` → `CREATE TABLE` → `COPY` → `DROP TABLE`), When it completes, Then all three indexes exist again. **The rebuild re-creates them explicitly as statements after the copy.** *Rewritten by the mob round after both the developer and the quality participants verified that SQLite's `CREATE TABLE` has no index declaration — the mechanism named in the original criterion, and in `FR5.3`, does not exist. This is a correction to `requirements.md` and is registered below.*

---

## US6 — Analytics view

> **Restated by triage.** The quality participant verified that nothing in the
> suite executes `app.js` and that the two-runtime-dependency cap forbids adding a
> browser-automation library, so six of this group's original criteria were
> unobservable by any test. This group is therefore written as **markup and asset
> contracts the page tests assert statically**, with the end-to-end behaviour
> carried by one manual exercise line in the standing verification command. The
> accessibility criteria are **split per state and per region**, because the
> original single bundled criterion reproduced, at a coarser granularity, the exact
> mistake a prior intent's review flagged in this same project.

### US6.1 — An analytics entry in the shell I already use · Must Have

**As the Solo Maintainer, I want analytics to be a third entry on the page I already open, so that I do not have to learn or remember a second place.**

Covers `FR6.1`, `FR6.9` (`FR8.6`, `C-3`) · Depends on: nothing

- **AC6.1.1** Given the served markup of the existing page, When I inspect it, Then a third top-level entry appears alongside the two that exist, and no second site or separate URL tree is introduced.
- **AC6.1.2** Given the served markup, When I read the analytics entry, Then it carries `data-testid` hooks that are **named at Refined Mockups and added to `REQUIRED_TEST_IDS` in `tests/test_page.py`** — the pinned constant the existing page tests assert — rather than a new pinning convention. *Corrected by the review (`R-18`): the original said "the page module's pinned constant", but the constant lives in the test module; and it named no hook, which left `FR8.6` undemonstrable.*
- **AC6.1.3** Given the static asset requests the view needs, When they are served, Then they come from the same asset route as the current page's script and styles, with the same content type.
- **AC6.1.4** *(`R-05`)* Given the served markup, When I inspect the header entries, Then the analytics entry carries `aria-current` while it is the active view, so assistive technology can tell which entry is current.

### US6.2 — The three readouts · *slice* · Must Have

**As the Solo Maintainer, I want the trend, the mix and the words together in one view, so that I can read the whole picture without making three separate requests by hand.**

Covers `FR6.2` (`FR8.6`) · Depends on: `US2.1`, `US2.2`, `US2.3`, `US3.1`

- **AC6.2.1** Given the served markup of the analytics view, When I inspect it, Then a container exists for the per-day series, one for the label breakdown with counts and shares, and one for each of the two term lists at the top 10 per list.
- **AC6.2.2** Given the view's script, When I inspect its data-fetch sites, Then each of the three sections has exactly one fetch to its own endpoint and none reads a value the endpoint did not return.
- **AC6.2.5** *(`R-05`, added by the review)* Given the breakdown region, When I inspect its markup, Then each label's **share is rendered from the response's fraction** and a `null` share renders as an explicit no-share marker rather than as `0%`. The rough mockups specify percentages and a fabricated `0%` for a zero-share label; `FR2.7` rules a fraction and a `null` on a zero denominator, so the view must not manufacture a percentage or a zero the API refused to state.
- **AC6.2.3** Given the view's script, When I inspect its prefix constants, Then **the `/v2` analytics prefix it fetches matches the router's**, and a static assertion pins them. *Added by the mob round: the frontend holds an independent copy of the version prefix that nothing asserts against the backend, and the existing suite has no assertion of that kind. This is the cheapest available check for the likeliest silent break in the whole feature.*
- **AC6.2.4** *(`FR8.6`, added by the mob round)* Given the analytics markup, When the page contract tests run, Then every analytics hook is asserted in the same style as the existing page's, so a renamed hook fails rather than silently passing.

### US6.3 — A range control that starts at everything · Must Have

**As the Solo Maintainer, I want to narrow the view by date and have it start by showing me everything, so that I see the whole history before I hide any of it.**

Covers `FR6.3`, `FR6.4` · Depends on: `US6.2`, `US6.5`

- **AC6.3.1** Given the view on first load, When no range has been chosen, Then the script requests both endpoints with no bounds, and the markup shows an unbounded state rather than a range someone invented.
- **AC6.3.2** Given I change the range, When the response for that range arrives, Then all three sections are updated **together** from that one range's responses, and never a mix of two populations.
- **AC6.3.3** *(`R-05`)* Given the range control, When I look for an import filter, Then there is none; `import_id` stays API-only, so the page never presents a filtered population it cannot label.
- **AC6.3.4** *(`R-05`)* Given the range control, When I look for a way back to the default, Then a control exists that clears the range and returns the view to all history.
- **AC6.3.5** *(`R-19`, added by the review)* **Ruled: there is no `limit` control on the page.** The term lists always show the affirmed top 10 per list; `limit` is an API parameter only. This closes a question the review raised rather than leaving it for Refined Mockups to decide implicitly.
- **AC6.3.6** Given the range control during a refetch, its disabled or active state is asserted as part of `US6.5`'s markup contract, not here.

### US6.4 — A failed read never looks like an empty one · Must Have

**As the Solo Maintainer, I want a broken query to look broken, so that I never mistake a failure for the absence of data.**

Covers `FR6.5`, `FR6.6`, `FR6.7`, `FR6.8` · Depends on: `US6.2`

- **AC6.4.1** Given a request that fails, When the response arrives, Then the markup contains a dedicated inline error region that names the failure — not an empty chart and not a silent blank — and that region is distinct from the empty-result region.
- **AC6.4.2** Given a 422 and a 500, When each is rendered, Then each is shown as an error rather than as an empty success, and the two are distinguishable from each other.
- **AC6.4.3** Given the view with the dummy client and no network, When it loads, Then the script's only outbound requests are to its own two analytics endpoints — asserted statically by the script's fetch sites and dynamically by the standing manual exercise with the offline guard armed.
- **AC6.4.4** Given the rendering, When I inspect it, Then it uses native HTML elements and the page's existing class names — no chart library and no new front-end dependency.
- **AC6.4.5a** *(`FR6.8`, range control region)* Given the range control's markup, When I inspect it, Then it has an associated label element or `aria-label` naming the date range. **Decidable by static markup assertion.**
- **AC6.4.5b** *(`FR6.8`, series region)* Given the series region's markup, When I inspect it, Then the per-day values are present as text or in a table alongside any drawing — the series is not conveyed by drawn geometry alone. **Decidable by static markup assertion.**
- **AC6.4.5c** *(`FR6.8`, status region)* Given the status region's markup, When I inspect it, Then it carries `role="status"` or `aria-live`, so a change is announced. **Decidable by static markup assertion.** *Split into three criteria by the review (`R-11`): the single bundled id was one assertion with three `Given/When/Then` triples chained by "and", and the original "announced" clause was undecidable without executing `app.js`.*

### US6.5 — A view that shows what it is doing · Must Have

**As the Solo Maintainer, I want the view to tell me when it is still working and when only part of it arrived, so that a slow or half-answered screen is never read as an answer.**

> **Added by the mob round.** The design participant found that **no story owned
> the in-flight state**, and that `AC6.3.2` as originally written constrained only
> the *settled* state — which meant the most natural implementation of the story
> (two independent fetches, no ordering discipline) would violate it. That makes
> the criterion unfalsifiable as written. This story owns the states, and
> `AC6.3.2` now depends on it.

Covers `FR6.4`, `FR6.8` · Depends on: `US6.2`

> The loading and partial states came from the Rough Mockups wireframes' screen
> states. **No `RM-n` finding ids are cited anywhere in this set**: the review
> verified that no such ids exist in the Ideation artifacts, so the earlier
> `[RM-n]` tags were unsourceable and are gone rather than renumbered.

- **AC6.5.1** Given a request in flight, When the view is rendered, Then a loading state is shown for that section rather than an empty one, and it is announced to assistive technology.
- **AC6.5.2** Given two requests in flight for one range change, When they complete out of order, Then **only the newest range's responses are rendered**; a late response from a superseded range is discarded rather than overwriting current data. *Carried from the mob round and explicitly exempted from the Q9 rewrite: the discard rule is a property of the script's code path, verified by reading it, not of the served markup.*
- **AC6.5.3** Given one section's request succeeds while another's fails, When both complete, Then the view shows the successful section and a partial-failure error for the failed one — never two sections silently disagreeing about which range they describe. *Same exemption as `AC6.5.2`.*
- **AC6.5.4** *(`R-05`)* Given the view, When I look for a route back to the existing Analyze entry, Then one exists, so leaving the analytics view costs no navigation the rest of the page does not already offer.
- **AC6.5.5** Given the loading and partial states, When their markup is asserted, Then each is a distinct region — so the tests can tell a loading screen from an empty screen from an error screen.

---

## US7 — Platform obligations

> These nine exist because the human affirmed them at Practices Discovery and then
> ruled them in-scope for this feature `[Q1-practices]`. They are written as
> benefits to P1 rather than as engineering chores, because a practice is a licence
> to copy and an unrewarded chore is not.

### US7.1 — Reproducible installs · Must Have

**As the Solo Maintainer, I want the same install on any machine, so that a working setup does not stop working without a code change.**

Covers `FR7.1` · Depends on: nothing

- **AC7.1.1** Given the project, When I install it from the lockfile on a clean environment, Then every distribution resolves to the exact version recorded, with hashes verified.
- **AC7.1.2** Given the recorded set, When I install it **twice into two separate clean environments**, Then the resolved distributions are identical. *Corrected by the review (`R-12`): the original said "on different machines", which contradicts the persona's own re-scoping of G5 to "every time" rather than "any machine" — this project has one machine and no remote — and which cannot be demonstrated here. Two clean environments is the same property, decided locally.*
- **AC7.1.3** Given the lockfile, When I inspect the install path, Then the documented install command consumes it rather than re-resolving.

### US7.2 — One command that runs the gates · Must Have

**As the Solo Maintainer, I want one command that proves the gates, so that "it works on my machine" stops being the whole verification story.**

Covers `FR7.2` · Depends on: nothing

- **AC7.2.1** Given the verification script, When I run it, Then it runs the whole-application 80 % coverage floor, the warnings-as-errors filter and the pinned `ruff` rule set.
- **AC7.2.2** Given a failing gate, When the script exits, Then it exits non-zero, so a broken state cannot be reported as verified.
- **AC7.2.3** Given the script, When I inspect it, Then it is platform-neutral — not a pre-commit hook and not a provider CI job, which cannot run here because there is no git remote.

### US7.3 — Scanning that would catch a real key · Must Have

**As the Solo Maintainer, I want a scan that would actually catch a leaked key, so that the clean history I have today stays clean by mechanism and not by luck.**

Covers `FR7.3` (`C-11`) · Depends on: `US7.2`

- **AC7.3.1** Given secret scanning runs, When it completes, Then it is invoked **by the verification script** — the same entry point `AC7.2.1` names — rather than being a separate manual step.
- **AC7.3.2** Given the known fake-key fixtures in the test tree, When the scan runs, Then they are allowlisted so the first run reports signal rather than known-fake noise. *Corrected by the mob round: this criterion asserted "four" fixtures, matching `team.md`. The developer participant counted six literals matching the real key shape. The count is left unstated rather than asserted, because the two counts disagree and the disagreement is a question for the practices that recorded the original figure, not something a criterion should hard-code.*
- **AC7.3.3** Given a dependency audit, When it runs, Then a known-vulnerable resolved version is reported rather than passing silently.

### US7.4 — A licence on the project · Should Have

**As the Solo Maintainer, I want the project to carry a licence, so that what I have built says plainly how it may be used.**

Covers `FR7.4` · Depends on: nothing

- **AC7.4.1** Given the repository root, When I look for a licence, Then one is present and names a specific licence.
- **AC7.4.2** Given the installed distribution, When its metadata is inspected, Then it declares that same licence rather than an empty expression.

### US7.5 — Boundaries that fail the build · Must Have

**As the Solo Maintainer, I want a layer boundary breach to fail the lint rather than wait for me to notice it, so that the structure I rely on cannot quietly erode.**

Covers `FR7.5` · Depends on: `US7.2`

- **AC7.5.1** Given `ruff TID251` (`banned-api`) entries for the layer boundaries, When a module imports something it must not, Then the lint fails.
- **AC7.5.2** Given the existing code, When the new rule set is applied, Then the application is clean, so the rule reports real breaches rather than noise.

### US7.6 — A server that refuses to leave the loopback · Must Have

**As the Solo Maintainer, I want a non-loopback bind to fail loudly at startup, so that my unauthenticated app holding my API key can never be exposed by a flag I mistyped.**

Covers `FR7.6` (`C-10`) · Depends on: nothing

- **AC7.6.1** Given a non-loopback host, When the app starts, Then startup fails loudly with an explanation rather than serving.
- **AC7.6.2** Given the `HOST` constant, When I trace the run path, Then it is the value the run path actually consumes — a documented `uvicorn` default is not enforcement.
- **AC7.6.3** Given the loopback bind, When the app starts normally, Then nothing about the working local run changes.

### US7.7 — A test harness that can host concurrency · Must Have

**As the Solo Maintainer, I want the test harness able to issue genuinely concurrent requests, so that a concurrency defect can finally be proved fixed rather than assumed fixed.**

Covers `FR7.7` · Depends on: nothing

- **AC7.7.1** Given the replaced harness, When a test issues concurrent requests, Then they run on different threads and genuinely overlap, rather than each getting a fresh event loop and running sequentially.
- **AC7.7.2** Given the harness's lifespan handling, When two concurrent requests each re-enter it, Then **schema initialisation is hoisted out of the per-request path**, so the concurrency test fails on the connection defect rather than on a `database is locked` error from two simultaneous migrations. *Added by the mob round: the developer participant verified that concurrent `init_db` raises `database is locked`, so without this the R-01 test would have gone red for the wrong reason and the fix would have been declared broken.*
- **AC7.7.3** Given the offline guard, When the new harness runs, Then it stays armed and an accidental outbound call still fails the run.
- **AC7.7.4** Given the existing tests, When they run on the new harness, Then they still pass — the harness is replaced, not extended around. Every one of the existing call sites is updated, since the harness's signature changes.
- **AC7.7.5** Given the statement-count measurement in `AC8.1.2`, When it runs, Then it measures a single lifespan entry, so the count is deterministic rather than multiplied by the harness's per-request re-entry.

### US7.8 — Static analysis aimed at the Python we run · Must Have

**As the Solo Maintainer, I want the linter checking the interpreter I actually run, so that my only static security analysis is not aimed at a Python the app never uses.**

Covers `FR7.8` · Depends on: nothing

- **AC7.8.1** Given `lint.target-version`, When it is compared with `requires-python`, Then they match.
- **AC7.8.2** Given the change, When `ruff check` runs, Then the application is still clean.

### US7.9 — Documentation that matches the code · Must Have

**As the Solo Maintainer, I want the README to describe the surface I now have, so that the document I treat as the contract does not lie to me.**

Covers `FR7.9` · Depends on: `US2.1`, `US3.1`, `US6.1`

- **AC7.9.1** Given the README's HTTP surface table, When I read it, Then both new `/v2` analytics endpoints appear on it.
- **AC7.9.2** Given the README's file layout tree, When I read it, Then every new module is listed.
- **AC7.9.3** Given the README's storage section, When I read it, Then it describes the new indexes and the schema step.

---

## US8 — Quality attributes  · *(`NFR1`–`NFR9`; not `FR8`)*

### US8.1 — Answers inside the performance budget · Must Have

**As the Solo Maintainer, I want the analytics to answer quickly on a real store, so that reading them stays something I actually do.**

Covers `NFR1` (`FR8.9`) · Depends on: `US2.1`, `US2.3`, `US3.1`

- **AC8.1.1** Given 10,000 stored analyses, When either endpoint is exercised, Then it answers within **200 ms**. *Restated by the mob round: the quality participant found the criterion said "the stated budget" without stating one, so nothing could decide it.*
- **AC8.1.2** Given the same fixture, When SQL statements are counted, Then the count is **independent of how many days the range covers** — the series comes from one grouped query, never a query per day. *The mob verified these two criteria do **not** conflict: one grouped query plus Python-side zero-fill satisfies both. Neither said where the fill happens, so this criterion now names it.*
- **AC8.1.3** *(`FR8.9`, added by the mob round)* Given the 10,000-row fixture, When the **terms** endpoint is exercised over a range containing all of them, Then it answers within the same budget. The count assertion alone measures the easy half of `NFR1`; the terms path scans unbounded text volume and is the half most likely to miss the budget.
- **AC8.1.4** *(`FR8.9`, added by the mob round)* Given the suite runs with coverage enabled by default in `addopts`, When this budget is measured, Then it is measured **without** coverage instrumentation, so the wall-clock figure describes the application rather than the instrumented run.

### US8.2 — No new way for data to leave · Must Have

**As the Solo Maintainer, I want the analytics layer to add no way for my text to leave this machine, so that adding a feature does not quietly widen my privacy exposure.**

Covers `NFR2` (`C-5`, `C-9`, `C-11`) · Depends on: `US1.1`

- **AC8.2.1** Given the analytics modules, When their imports and calls are inspected, Then there is no network call, no HTTP client and no model inference.
- **AC8.2.2** Given the new code, When it is inspected for credentials, Then no key is added to any code path, response body, log record or artifact.
- **AC8.2.3** Given the new code, When it is inspected for outbound calls, Then no module imports an HTTP client, a socket, or the sentiment engine's live client — analytics reads stored rows and calls no engine. *Corrected by the review (`R-09`): this criterion was a verbatim duplicate of `AC1.1.3`, which owns parameter binding.*

### US8.3 — A read that cannot mutate · Must Have

**As the Solo Maintainer, I want the analytics layer to have no mutating capability at all, so that a read cannot reach a write even by accident.**

Covers `NFR3` · Depends on: `US1.1`, `US7.5`

- **AC8.3.1** Given the read module's public surface, When it is inspected, Then it exposes no mutating operation, and the boundary rules prevent it importing the ones that would.
- **AC8.3.2** *Corrected by the mob round, restated by the review.* The original criterion claimed `ruff TID251` would fail a write attempted from the analytics layer. **It cannot.** `banned-api` is an import rule; the developer participant verified it does not fire on `conn.execute(...)`. The guarantee is stated as two facts, each with its own instrument: **lint enforces which modules may be imported** (`US7.5`, `AC7.5.1`), and **the absence of a write is proved behaviourally** by `AC2.5.1` and `AC2.5.2`. This criterion asserts no test of its own; it records the split so no reader expects a lint failure that cannot happen.

### US8.4 — Failures that stay distinguishable · Must Have

**As the Solo Maintainer, I want each kind of bad answer to stay its own kind, so that a fix targets the real cause.**

Covers `NFR4` · Depends on: `US2.4`

- **AC8.4.1** Given a malformed parameter, an inverted range, an unmatched `import_id` and a storage failure, When each occurs, Then each produces a distinguishable status and machine code.
- **AC8.4.2** Given any of those, When the response is read, Then none of them is rendered anywhere as an empty success.

### US8.5 — Nothing about `/v1` changes · Must Have

**As the Solo Maintainer, I want the analytics work to leave every existing endpoint alone, so that adding a feature breaks nothing I already rely on.**

Covers `NFR5` (`C-4` as amended by `[Q7]`) · Depends on: nothing

- **AC8.5.1** Given the existing suite, When it runs unchanged, Then every pre-existing test passes with the same result as before the change.
- **AC8.5.2** Given the error envelope, When the change is complete, Then its **shape** is unchanged; the code set gains exactly one member, for a storage failure, and nothing else moves.
- **AC8.5.3** Given the `SentimentClient` interface and its two adapters, When I compare behaviour before and after, Then it is unchanged, and the interface gains no member.

### US8.6 — New code that reads like the old · Must Have

**As the Solo Maintainer, I want the new modules to look like the ones I already maintain, so that the codebase stays one codebase.**

Covers `NFR6` · Depends on: nothing

- **AC8.6.1** Given each new module, When it is inspected, Then **each of the following holds as a separate decidable check**: it opens with a docstring carrying a `Single responsibility:` line; every function is fully annotated; it declares `from __future__ import annotations`; its helpers are underscore-prefixed; its semantic constants are `UPPER_CASE` with a `#:` comment. *Split into five decidable checks by the review (`R-13`, `R-17`): the original single criterion bundled four properties and left `from __future__`, underscore-private helpers and the config convention with no criterion anywhere in the set, even though `NFR6` mapped `OK`.*
- **AC8.6.2** Given the request and response shapes, When I inspect them, Then they are stdlib dataclasses and no `pydantic` appears in `app/`.
- **AC8.6.3** Given the new modules, When I look for a `utils.py` or `helpers.py`, Then neither exists; a helper lives with the concept it serves.
- **AC8.6.4** *(`R-13`, added by the review)* Given the analytics configuration, When I inspect it, Then it follows the `config.example.toml` / gitignored `config.local.toml` convention exactly — and if the analytics layer needs **no** new configuration value, then it adds none, which is itself the decidable outcome.

### US8.7 — Tests that touch the real thing · Must Have

**As the Solo Maintainer, I want my tests to read real values out of real storage and real served markup, so that a passing suite means the thing actually works.**

Covers `NFR7` (`FR8.5`, `FR8.7`) · Depends on: `US7.7`

- **AC8.7.1** Given any new test, When it asserts, Then the value is read back from real SQLite or real served markup, never out of a mock of the thing under test.
- **AC8.7.2** Given the whole suite, When it runs, Then it is green with no network and no API key, and the offline guard is still proven armed by a test. *(`FR8.5`)*
- **AC8.7.3** The acceptance-before-implementation discipline is **carried by reference to the team's Testing Contract, not asserted here** (`FR8.7`). The quality participant verified the ordering is unverifiable in a repository that squashes one commit per scope — the history destroys the evidence of which file was written first. *Recorded by the review (`R-20`) as an `AC` id carrying no assertion; it is kept as an id because `FR8.7` must land somewhere, and it is explicitly not a test.*
- **AC8.7.4** Given the coverage floor, When the suite runs with coverage, Then the whole-application 80 % line floor still holds, counting the new modules.

### US8.8 — A failure I can actually see · Must Have

**As the Solo Maintainer, I want an analytics failure recorded where I will find it, so that diagnosing it does not begin with guesswork.**

Covers `NFR8` · Depends on: `US2.4`

- **AC8.8.1** Given an analytics failure, When it is raised, Then it appears in the application log through the module logger.
- **AC8.8.2** Given a logged analytics failure, When I read the log record, Then no credential appears and no request parameter is concatenated into SQL text. *Corrected by the review (`R-09`), which found the original phrased as an undecidable runtime observation; the decidable form is the two properties above, checkable by reading the logging call.*

### US8.9 — Work that stays proportionate · Should Have

**As the Solo Maintainer, I want the analytics layer's work to be bounded by what I asked for, so that adding a view does not become an unbounded report.**

Covers `NFR9` · Depends on: `US2.3`

- **AC8.9.1** Given a bounded range, When the series is produced, Then its length equals the number of UTC days in that range.
- **AC8.9.2** Given an unbounded range, When the series is produced, Then its length equals the span of the stored data, and this is documented as the one quantity that can grow without a caller-imposed bound.
- **AC8.9.3** Given any store size, When I read a terms response, Then its size is bounded by `limit` per list and never by the number of distinct terms present.

---

## INVEST compliance notes

| Criterion | How this set satisfies it |
|---|---|
| **Independent** | Every story names its own dependencies explicitly. `US7.*` and `US8.5`–`US8.6` have none and can start at any time. The only chains are the real ones: the tokenizer promotion precedes extraction, the migration precedes the index assertion, the harness precedes the concurrency fix. |
| **Negotiable** | The acceptance criteria pin observable behaviour and error shapes. Implementation choices — query shape, module name, markup shape, chart technique — are left open to Design and Code Generation. |
| **Valuable** | Every story states a P1 benefit. The `US7` stories are the weakest on this criterion and are the reason they are written as benefits rather than chores; if one cannot be phrased as a benefit it should be cut, not kept as an obligation. |
| **Estimable** | Each story is one coherent contract. The two largest are `US2.1` and `US7.2`, both of which are bounded by a fixed, enumerable check list. |
| **Small** | The largest risk is `US6.2`, which spans three sections; if it proves too large at estimation, splitting it per section is the intended move and would not break any dependency. |
| **Testable** | Every acceptance criterion is an observable assertion, and `FR8.2`'s hand-pinned aggregate list is carried inside `AC2.1.1`, `AC2.3.*` and `AC3.1.*` rather than restated separately. |

## Dependency and relationship summary

- **The affirmed thin slice is `US1.1` → `US2.1` → `US6.2`**: one analytics endpoint end-to-end — route, aggregate SQL, page render — before the second endpoint goes in.
- **Two independent defect-and-tool pairs** run alongside and do not block the slice: `US7.7` → `US1.2` (harness, then the R-01 fix) and `US5.1` → `US5.2` (migration, then index survival).
- **`US4.2` precedes everything in the terms path**, because promoting the tokenizer without changing engine behaviour is what makes `US4.1` safe to add.
- **Nothing in `US7` blocks the analytics feature itself.** They were ruled in-scope as a set; if sequencing pressure appears, Delivery Planning may take them last without any story becoming unowned.