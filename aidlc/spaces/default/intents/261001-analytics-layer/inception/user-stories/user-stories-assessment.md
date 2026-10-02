# User Stories — Assessment

## Decision

**Execute.**

## Rationale

User stories add value here, though less obviously than in a typical feature.

The intent's `condition` executes when user-facing features, multiple personas,
complex business logic or cross-team work is involved. **One of those holds: there
is a user-facing surface.** This change adds a third top-level entry to an existing
page that the developer reads to answer questions about their own data — a time
series, a label breakdown and two ranked term lists. A UI with a date-range control
and a distinct failure surface is precisely the kind of thing whose acceptance
criteria are cheaper to write as stories than to retrofit onto requirements
afterwards.

Two of the stage's usual justifications do **not** hold, and pretending otherwise
would weaken the artifact:

- **There is one persona, not several.** The developer is simultaneously the only
  user, the operator and the decision-maker. There is no second reader to model, so
  stories cannot be differentiated by role.
- **There is no cross-team coordination.** No stakeholders, no reporting cadence,
  no influencers. `C-7` records one developer and advisory stage reviews.

What stories genuinely buy on this change:

1. **Vertical slicing against a real sequence.** The affirmed walking-skeleton
   practice requires the first slice to be one analytics endpoint end-to-end
   (route → aggregate SQL → page render) before the second. A story set is the
   natural place to express that order and its dependencies; a requirements list
   does not.
2. **Acceptance criteria for computed numbers.** `FR8.2` enumerates every aggregate
   that must carry a hand-written expected value. Written as Given/When/Then per
   story, that list becomes directly automatable; left in requirements it stays a
   paragraph.
3. **A home for the eight practices obligations.** `FR7.1`–`FR7.9` are engineering
   work with no end-user surface, and `FR1.6` is a defect fix. Each is invisible in
   a story set unless a decision is made about whether it belongs there — and the
   prior intent's review already found that requirement statements with no owning
   story were a real gap.

## Factors considered

| Factor | Reading |
|---|---|
| Project type | Brownfield extension of a working local app |
| User-facing scope | **Yes** — a new view inside the existing single-page shell (`FR6.1`) |
| Personas | **One** — the developer alone `[desc]`, confirmed at intent capture |
| Complexity signals | Moderate — two endpoints, one additive migration, one view, plus eight platform obligations and one defect fix |
| Cross-team | **None** — `C-7`, one developer, advisory reviews |
| Requirement count | 8 FR groups (85 numbered requirements) and 9 NFRs, which is the load the story set has to absorb |
| Team practice | Walking skeleton **on**; "one analytics endpoint end-to-end" is the affirmed slice `[Q2]` |
| Team testing posture | `custom` — acceptance/API criteria before implementation, unit tests after `[team]` |

## Key areas where stories will add the most value

1. **The two read paths** (summary, terms) — each has a distinct contract, a
   distinct set of refusal shapes, and its own set of hand-pinned aggregates.
2. **The view** — the date-range control, the four rendering states, and the
   requirement that the view never presents a failed request as an empty result.
3. **The additive migration** — additive, idempotent, and index-preserving, which is
   a property with a failure mode (silent index loss) no happy-path story catches.
4. **The R-01 fix** — a defect that the prior intent recorded and accepted, now
   closed, and the one story here whose "so that" is about trust rather than
   capability.
5. **The platform obligations** — lockfile, verification script, scanning,
   `LICENSE`, `TID251`, loopback enforcement, `target-version`, harness fix.

## What would have made skipping defensible

Recorded so the decision can be revisited rather than defended: with a single
persona, no external user and no cross-team work, the stories will largely restate
requirements in a different shape. If the plan questions below conclude that the
story set adds nothing beyond `FR8.2`'s acceptance list, **skipping would be a
legitimate call** — and this artifact records that it was available rather than
taken by default.