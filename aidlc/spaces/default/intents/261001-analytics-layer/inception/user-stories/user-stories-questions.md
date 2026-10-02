# User Stories — Story Plan Questions

> Standard depth, brownfield. `user-stories-assessment.md` decides **Execute**.
> These questions are the plan decisions the assessment cannot settle. Every
> option carries the drafted answer so the choice is between reasoned positions
> rather than from a blank page.

## Q1 — Who are the users?

The intent capture settled this once — the developer alone, no operator, no
reviewer, no end-user group. Persona *structure* is still open: one persona, or a
split that reflects the two different jobs this change involves (reading
analytics versus running and trusting the app).

A. **One persona** — the developer, exactly as intent capture recorded it
B. **Two personas** — the *reader*, who reads analytics, and the *operator*, who installs, verifies and trusts the app. This is what gives the eight practices obligations a home
C. **One persona with two explicit goal clusters**, kept as a single persona but with the reading goal and the operating goal named separately
D. **Three personas** — reader, operator, and a *reviewer* persona representing the review-before-land concern in `C-7`
E. Other (please specify)

[Answer]: A. One persona - the developer, exactly as intent capture recorded it. The story set is not differentiated by role and no persona split is invented to justify itself.

## Q2 — Do the platform obligations and the R-01 fix become stories?

`FR7.1`–`FR7.9` (lockfile, verification script, secret scanning, dependency audit,
`LICENSE`, `TID251`, loopback enforcement, `target-version`, README) and `FR1.6`
(the cross-thread connection fix) are engineering work with no new end-user
surface. A prior intent's review found requirement statements with no owning story
were a real gap; these are the ones at risk of that.

A. **Yes — each becomes a story**, phrased around the developer's benefit ("so that every install resolves the same set"). Full traceability, and the story set carries the whole scope
B. **Only `FR1.6`** becomes a story, because it fixes a user-visible defect; the nine `FR7` items stay requirements tracked outside the story set
C. **No — none of them become stories.** They stay as requirements and appear in `traceability.json` as `Deferred` to Build and Test
D. Other (please specify)

[Answer]: A. Each becomes a story, phrased around the developer's benefit rather than as a bare engineering task. All of FR7.1-FR7.9 and FR1.6 are owned by a story, so nothing in the requirements set is left without a home in the story set.

## Q3 — How should the story set be broken down?

A. **By feature** — the summary endpoint, the terms endpoint, the view, the migration, the platform obligations. Maps directly to the FR groups, so traceability is obvious
B. **By vertical slice** — each story cuts from the query layer through the route to the rendered output, so every story is independently demonstrable. Closest to the affirmed thin-slice practice
C. **By workflow** — the developer's actual sequence: open the analytics view, read the series, read the breakdown, read the terms, narrow the range, hit a bad date
D. **By epic** — one epic per capability with sub-stories beneath each
E. Other (please specify)

[Answer]: A. By feature - the story groups map directly to the FR groups (read layer, summary, terms, extraction, migration, view, platform obligations), so traceability between a requirement id and a story id is obvious and mechanically checkable.

## Q4 — How fine should the slicing go?

A. **One story per FR group** — 8 stories. Coarse, and each is too large for a
   single sprint on its own
B. **One story per coherent contract** — split so each carries its own refusal
   shapes and its own hand-pinned aggregates, aiming at stories that are
   independently testable. Likely 14–18 stories
C. **As fine as possible** — one story per individual acceptance criterion cluster,
   which maximises independence and maximises overhead
D. Other (please specify)

[Answer]: B. One story per coherent contract. Each story carries its own refusal shapes and its own hand-pinned aggregates, sized to be independently testable.

## Q5 — How should the nine NFRs appear?

A. **NFRs stay NFRs** and appear in `traceability.json` as `Deferred` to NFR Requirements and NFR Design, which own them. No story is created for a non-functional requirement
B. **Each NFR that has an observable user-visible consequence also gets a story** (for example the read-only guarantee and the 200 ms budget), and the rest stay NFRs
C. **All NFRs become stories** so nothing is deferred out of the story set
D. Other (please specify)

[Answer]: C. All nine NFRs become stories, so nothing is deferred out of the story set to NFR Requirements and NFR Design.

## Q6 — Follow-up: Q4's estimate versus Q2 and Q5

Q4 agreed a story count of 14–18. Q2 made each of `FR7.1`–`FR7.9` its own
story, and Q5 made all nine NFRs stories. Honoured together the set lands far past
the estimate, and its shape flows into Delivery Planning, Units Generation and
Contract Design. `FR8` is covered by neither mandate, so its nine test
requirements stay as acceptance criteria inside the owning feature stories rather
than becoming stories of their own.

A. Honour Q2 and Q5 literally; accept the overhead
B. Group the nine `FR7` items into three and group the NFRs by theme, landing near 22
C. Keep one story per `FR7` item and per NFR as chosen; group nothing
D. Other (please specify)

[Answer]: A. Honour Q2 and Q5 literally. Each of `FR7.1`–`FR7.9` is its own story and each of the nine NFRs is its own story. The overhead is accepted knowingly rather than removed by re-grouping work the human had said it wanted kept whole.

## Q7 — Triage: the `mean_confidence` premise was false

The mob verified against the shipped code that `confidence` is `NOT NULL`, that
`_is_v1_shape` rebuilds any store that disagrees, and that the rebuild aborts on a
NULL. So the situation Q13 asked about — rows carrying no confidence value —
cannot occur, which made four criteria unconstructible, including the one
carrying the project's own null-never-`0.0` convention.

A. Simplify: the mean averages every row in range and the row count always equals `total`; the field stays and documents its own denominator
B. Keep the null-tolerant design and make `confidence` nullable so the case is reachable
C. Drop the row-count field and state the mean is always over every row in range
D. Other (please specify)

[Answer]: A. Simplify. The null branch is removed rather than kept as an unreachable branch.

## Q8 — Triage: merging the migration stories

The developer participant verified `US5.1` and `US5.2` are one edit, so splitting
an additive migration from its own index assertion produced a story whose index
half could not fail independently.

A. Merge them into one migration story
B. Keep them separate
C. Other (please specify)

[Answer]: A. Merge them.

## Q9 — Triage: how the view's behaviour is pinned

The quality participant verified that nothing in the suite executes `app.js` and
that the two-runtime-dependency cap forbids adding a browser-automation library,
so six of the view's criteria were unobservable by any test.

A. Restate as markup and asset contracts the page tests assert statically, plus one manual end-to-end line in the verification command
B. Keep the behaviour criteria and rely on the standing manual verification command
C. Other (please specify)

[Answer]: A. Restate as markup and asset contracts plus one manual end-to-end line.

## Q12 — Follow-up (Critical R-01): what does an empty range return?

`AC2.4.1` required an empty range to answer an **empty series**, while `AC2.3.1`
and `AC8.9.1` required **one zero-filled entry per UTC day**. Both cannot hold, so
two criteria could not be met at once. Inherited from `requirements.md`, where
`FR2.9` and `FR2.10` were never reconciled.

A. A bounded range with no rows is **zero-filled**. The empty series applies only
   when the range spans zero days
B. A bounded range with no rows returns an **empty series**. Zero-filling applies
   only to the internal gaps of a range that matched at least one row
C. Empty series for a no-match range, and zero-filled gaps for a populated range,
   distinguished by whether any row matched at all
D. Other (please specify)

[Answer]: B. A range matching no rows returns an empty series. Zero-filling applies only to the internal gaps of a range that matched at least one row.

## Q13 — Follow-up (Critical R-02): how does the envelope name a field?

`AC2.4.3` and `AC2.4.4` asserted a `field` JSON member, but the envelope is exactly
`{code, message}` with `additionalProperties: false` and the message itself names
the field. An inverted range also has to name two fields, which `errors[0]` cannot
do.

A. One `VALIDATION_FAILED` whose **message text names both** `query.from` and `query.to`
B. **Two** `VALIDATION_FAILED` entries, one per field
C. A **new dedicated machine code** for the inverted range
D. Other (please specify)

[Answer]: A. One `VALIDATION_FAILED` whose message text names both `query.from` and `query.to`, matching the existing convention where the message names the offending field. No new envelope member is introduced, so `additionalProperties: false` and `NFR5`'s frozen shape both hold.

## Consolidated Summary Confirmation

- **A range that matches no rows returns an empty series.** Zero-filling applies only to the internal gaps of a range that matched at least one row. This reconciles `FR2.9` with `FR2.10` and unblocks the two criteria that could not both pass.
- **The envelope names fields in its message text, not in a new member.** One `VALIDATION_FAILED` naming `query.from` and `query.to` for an inverted range, matching how `query.limit` is already reported. The frozen `{code, message}` shape holds.
- **`mean_confidence` keeps its four-decimal rounding.** The first fix simplified it correctly but dropped the rounding rule, which `FR8.2` needs to pin a hand-written value.
- **The thin slice's dependency graph was wrong even after the first fix.** `US2.2` and `US2.3` were in the slice but not in the graph, so the two sections still disagreed and the slice reproduced the defect it was meant to fix.
- **Three criteria were reworded from runtime observations into decidable checks** — reading a module's body rather than observing what it does at runtime, and naming the config-file convention, `from __future__ import annotations` and underscore-private helpers as separate assertions, none of which had any criterion before despite `NFR6` mapping `OK`.
- **Two duplicate criteria were removed**, and `AC8.2.3` now says something the read-layer story does not.
- **Four boundary cases were added**: a one-day range, a range spanning a month boundary, an all-stopword extraction, an all-one-label store, a negative `limit`, and a `limit` above the available term count.
- **The share rendering is now pinned.** The wireframes specify percentages and a fabricated `0%`; the view must render the fraction and show `null` as an explicit no-share marker.
- **There is no `limit` control on the page.** Ruled rather than left implicit.
- **Every `RM-n` tag is gone.** The review verified no such ids exist in the Rough Mockups artifacts.
- **Seven corrections are registered against `requirements.md`**, now in its Revision 2 section, including the two Criticals inherited from it.
- **The story count is 35**, with `US5.2` folded into `US5.1` and no longer carrying a story header, and the traceability file regenerated: 84 `OK`, 1 `N/A`, 0 gaps, 0 orphans across 85 upstream ids.

- `Looks correct`
- `Request changes`

[Answer]: Looks correct
