**Collaborator:** aidlc-design-agent

## Contribution

I reviewed the persona and the story set for user-experience fidelity and persona
fidelity only — what the person would recognise, and whether the stories actually
cover the experience the wireframes drew. Everything below names a story id, a
wireframe finding id, or a persona line, so it can be integrated or overruled
directly. The "belongs to Refined Mockups" items are separated out at the end so
they are not mistaken for defects here.

---

### 1. Coverage of the six wireframe findings

`rough-mockups/reviews/review-01.md` left R-01 to R-06 open. Here is where they land
in `stories.md` after the draft.

| Finding | Closed by | Verdict from a UX standpoint |
|---|---|---|
| **R-01** — default date range unspecified and Screen 1 self-contradictory | `AC6.3.1` + `AC2.2.4` | **Partially.** The *request* default is now closed (no bounds, all stored history). The *displayed* range is not. Nothing says what the two date fields render when the range is "everything" — so Screen 1's exact contradiction (blank inputs sitting above a fully populated all-history series) is what will get built. |
| **R-02** — accessibility notes only for the populated state | `AC6.4.5` | **Not closed.** See §5. One criterion, three clauses, whole view. No keyboard entry point, no focus order, no landmark-per-state, and nothing at all for the two controls the review named: the empty state's `[ Go to Analyze ]` and the error state's `[ Clear the range ]`. |
| **R-03** — the failed-request surface has no screen and no retry | `US6.4` (`AC6.4.1`, `AC6.4.2`) | **Partially.** See §4. Distinction is covered; **recovery is not**. The confirmed flow's "Retry, or adjust the range" has no owning criterion anywhere in the set. |
| **R-04** — `import_id` UI disposition unstated | `AC6.3.3` | **Closed.** Correctly, and it honours the persona's non-goal list. |
| **R-05** — header missing `History`; Analytics entry shown as active | `AC6.1.1` | **Half closed.** The third entry is covered. The active/current indication — `aria-current` or any equivalent — is unowned, and it is an accessibility criterion, not polish. |
| **R-06** — top-N, per-term count meaning, `limit` control | `AC6.2.1` ("top 10 per list") | **Half closed.** Top-N is closed. What the per-term count *represents* is unowned — the wireframe drew `(12)` ambiguously and the story inherits that ambiguity straight into the view. Whether a `limit` control is in scope for the page is unstated: the `import_id` disposition got a criterion (`AC6.3.3`), `limit` got nothing. |

**Two of the five drawn screen states have no owning story at all.**

- **Loading (Screen 3).** No story, no criterion, nothing about what is on screen
  between a change and its response. This is the single largest hole in the set and
  §4 is about it.
- **Partial / edge (Screen 5).** Nothing owns the *presentation*: the `( none )`
  placeholder in an empty polarity list, `0%` written as text so nothing depends on
  colour, a single-day axis, an all-positive breakdown. `AC3.1.4` owns the empty
  *array* at the API; nothing owns the empty *list* on the page.

So: five screens drawn, one fully owned, the error surface half-owned, two unowned.
Three interactive controls exist in the wireframes (`Go to Analyze`, `Clear the
range`, the third header entry) and **no acceptance criterion names any of them.**

---

### 2. Persona fidelity

**2.1 `P1` means two different things in the same file.** The persona is `P1 — The
Solo Maintainer`; the pain-point table runs `P1` to `P8`. "P1 did not ask for one"
under *What this persona does not want* is therefore ambiguous — persona or first
pain? Rename the pains (`PN-1` … `PN-8`) or the persona. One-character fix, real
ambiguity cost.

**2.2 Five of the seven goals are written in the system's voice, not the person's.**
G3–G7 read as *"the system guarantees X"*: "Trust that reading analytics cannot
lose, corrupt or silently alter stored data", "Trust that a number shown on screen
came from a real, complete calculation", "Install and verify the same way every
time", "Trust that the app stays on the loopback", "Have the documentation match the
code". A developer would say "I don't want to lose my rows", "I want last week's
number to be about last week", "I don't want to expose my API key by mistyping a
flag". The current phrasing has the effect of making US7.1–US7.9 look
persona-derived when they are in fact requirement restatements — which is exactly
how a hygiene list ends up carrying the word "persona". Rewrite G3–G7 in the first
person, and mark G5–G7 as *project* obligations rather than reader goals.

**2.3 G5 contradicts the persona's own Context.** G5 says "on **any machine**";
Context says "one machine, one local checkout, … no git remote". There is no second
machine. The real pain (P4) is that *tomorrow's* resolve differs from *today's on the
same machine*. This matters downstream: `AC7.1.2` — "compare two installs on
**different machines**" — is the fantasy, and on a one-machine project it is the
harder thing to test, not the easier one. Rewrite both as the same-machine,
before-and-after comparison.

**2.4 The persona has no trigger, and that is what let the riskiest decision through.**
G1–G7 all say *what* P1 wants and never *when*. Nothing records whether P1 opens this
view after every batch, once a week, or only when something looks wrong. That single
missing fact is the one that should govern the default range — and because the
persona does not state it, the default was picked (`AC6.3.1`, all history, unbounded)
without anything in `personas.md` pushing back. See §6.

**2.5 The persona never says what P1 does today.** The strongest fidelity test for a
"there is no summary of any kind" pain is the status quo, and it is absent: does P1
count rows in a terminal, scroll History, or just remember? That absence is why G1's
"without reading rows by hand" reads as a slogan rather than an observation.

**2.6 Nothing in the persona asks for a chart — but the whole view is built on one.**
G1 asks to see "how that mix moves over time". That is a need for *trend data*, not
for a drawn time series. Yet Screen 1, Screen 3 and Screen 5 all commit to a plotted
graphic, and because no chart library is permitted (AC6.4.4) it must be hand-built
from native HTML/CSS at real cost. The most visual decision in this feature traces to
no goal and no pain. Either G1 should say P1 reads the shape of the trend (and the
persona should carry that belief as something the designer must earn), or the story
set should leave the visualisation genuinely open — which is a legitimate and cheaper
answer, and is currently foreclosed by the wireframes.

**2.7 Four sections argue the artifact's own existence instead of describing a person.**
"There are none, and that is the finding", "The persona exists to make the 'so that'
clause of each story answerable", "Recorded so the story set can be checked against
it, because a persona artifact that only lists desires produces a feature nobody
asked for". These are notes-to-self in a persona file. They are good notes — they
belong in `memory.md`, and the persona should be left describing a person.

**2.8 The persona's own rule is stated and then not applied.** It says: *"Where a
story is phrased around trust rather than capability (`US1.2`, `US5.1`, `US5.2`,
`US7.6`), the acceptance criteria are the deliverable, because there is no second pair
of eyes."* Apply that test to the whole set and the list is much longer — US2.5,
US7.1, US7.3, US7.5, US8.2, US8.3, US8.5, US8.6, US8.7, US8.8 and US8.9 are all
trust-phrased. Those eleven criteria sets carry the entire verification burden for a
one-person project and receive no more scrutiny than the four the persona named.
Either apply the rule to the eleven, or say in the persona why only four qualify.

**2.9 P6 and the story set tell different stories about the view.** Pain P6 justifies
the concurrency fix by "a page that polls on a date range is exactly the trigger
pattern". Nothing in the story set polls, refreshes on an interval, or refetches on a
timer — `AC6.3.2` is the only refetch trigger and it is user-initiated. Either the
persona's rationale overstates, or the view is meant to poll and no story owns it (and
a polling view would need its own state and its own announcement criterion). Pick
one; do not leave the persona asserting a trigger the view does not have.

---

### 3. The story set describes the widget where it should describe the need

**`US6.1` names a slot, not a need.** All three criteria assert sameness: a third
entry, the same test-id constant, the same asset mechanism. None is about whether P1
can *get to* the analytics. Missing at need level: what the entry is called, where it
sits in the header, whether it is reachable in one action from **both** existing tabs
(the confirmed flow only shows it from Analyze), and whether it announces itself as
current when you are already on it (that is R-05's `aria-current`, unowned).
`AC6.1.2` in particular is a pinning-convention criterion with no user-visible
consequence; it belongs with the page contract tests or `NFR6`, not as an acceptance
criterion of a user story.

**`US6.3` bundles two separable things** — the narrowing capability and the default
policy — into one story and one dependency edge. The default is the riskiest decision
in the view (§6). Fusing it to the control means revising it means revising the
control story. Split it: `US6.3` = narrowing, and a separate criterion (or story) for
the default.

**`US6.4` is a bin, not a contract.** Titled *"A failed read never looks like an
empty one"* and covering `FR6.5`–`FR6.8`, but only two of its five criteria are about
failure. `AC6.4.3` (works offline) and `AC6.4.4` (no chart library) are unrelated to
the story's "so that". Retitle it to what it actually is, or split the failure surface
out from the rendering-constraints pair — and note that `AC6.4.5`, the
accessibility criterion, is currently filed under *failure*, which is how a catch-all
gets written in the first place.

**`AC6.2.2` is the best criterion in the set** and I want it on the record: "no
section is filled from a value the endpoint did not return" is a fabrication guard, and
that is precisely the property a hand-built native-HTML view needs pinned.

---

### 4. The range control: the in-flight state is real and unowned

This is the finding I would not sign off without.

`AC6.3.1` says the view starts at all history. `AC6.3.2` says that after a range
change refetch completes, the series, breakdown and both term lists all describe the
same range — *"never a mix of two populations"*. Both constrain the **settled** state.

**Nothing owns what the view shows between the click and the response**, and the
hazard is precisely the one `AC6.3.2` was written to prevent:

1. **Two independent fetches.** `US6.3` changes the range and both endpoints refetch.
   The summary can return while the terms are still in flight. The view therefore
   renders a *new* series beside an *old* term list for a few hundred milliseconds —
   the mixed population, arrived at by a route the criterion does not cover.
2. **Out-of-order responses.** Change the range twice quickly. Response A can land
   after response B, and the *settled* state is now a mix. As written, `AC6.3.2` is
   violable by the most natural implementation of the story, which means it is not
   currently a criterion a developer can pass or fail.
3. **Stale-beside-fresh on failure.** One endpoint 500s while the other succeeds. The
   view has a fresh series and a failed terms section. `AC6.4.1` says show an inline
   error — it does not say *which regions* stop showing their previous values and
   which retain them, and "retain the last good terms from the old range" is a
   different and much more misleading screen than "this region is unavailable".
4. **Undefined on an empty store.** `AC6.3.1` says "all stored history". With no rows
   there is no earliest date (`AC2.2.4` is undefined), and a first-run view — the one
   moment a new user is guaranteed to arrive — has no stated behaviour. Screen 2's
   copy ("widen the range above") is actively wrong in that case: there is nothing to
   widen. **An empty store and an empty range are two different states and the set
   renders them identically.**
5. **No cancellation, no announcement.** Nothing says an in-flight request is
   abandoned when a newer change supersedes it, and nothing says what is announced to
   a screen reader during a range change (`AC6.4.5` covers "status changes" only in
   general terms).

**What I would add**, as need-level statements rather than markup:

- A criterion that the view names the range it is currently showing, in the control
  itself — which is what R-01 was actually about, and which closes Screen 1's
  contradiction from the story side rather than only from the endpoint side.
- A criterion that no region renders data from a superseded range, and that a late
  response for an older range is discarded rather than painted.
- A criterion for the in-flight state: what replaces the current values, for how long,
  and what happens on a slow response. **This needs its own story.** It is Screen 3,
  and Screen 3 has no owner.
- A criterion separating **first run (empty store)** from **empty range**, each with
  its own copy and its own recovery action.

---

### 5. Accessibility: `AC6.4.5` is the wrong unit, and it repeats a mistake already flagged

The basics are enumerated in the rough-mockups answer Q6 (keyboard operable, visible
focus, labels not colour-only, adequate contrast), across seven regions plus an
all-screens line in the wireframes' accessibility notes, and again in `FR6.8`'s "the
accessibility basics already recorded for the page". `AC6.4.5` compresses all of that
into one sentence for the whole view.

**No — one criterion per region is not the right granularity, and per-view is
strictly worse.** Three reasons:

1. **It is not falsifiable in parts.** `AC6.4.5` joins three independent assertions
   with "and": the control is labelled, the series is exposed, status changes are
   announced. A pass on two is indistinguishable from a pass on three, so the
   criterion cannot localise a defect or drive a test that reports something useful.
2. **Accessibility failures live at the *state × region* intersection.** "The
   `Clear the range` button is reachable by Tab" is a statement about the error state;
   "the skeleton blocks are not focus traps" is a statement about the loading state.
   A per-region note was already flagged in this very intent
   (`project.md`, learned 2026-10-01: *"wrote accessibility notes per component region
   rather than per screen … the advisory review flagged this as a miss of the
   stage's one-line-per-screen requirement"*, review finding R-02). The reviewer's
   reasoning was that the regions do **not** simply repeat across states. The draft has
   reproduced that mistake one level up: per-region became per-view.
3. **It is structurally blocked.** There is no loading-state story and no empty-state
   story, so there is nothing to hang a per-state accessibility note on. The catch-all
   is a symptom. Fixing granularity without first adding the missing state stories just
   redistributes the same omission.

**What I would do:** give accessibility one criterion per *state × region* pair for
the states that exist, split across at least two stories — the control (label, focus
order, entry point, `aria-live` for validation) and each rendered state (empty,
loading, error) including its own controls' keyboard entry and focus landing. Then, per
R-02, state explicitly whether the header and footer persist during loading, error and
partial states.

**One more thing `AC6.4.5` does not say**, which R-05 already asked for: how the
current header entry is announced. `aria-current` on the Analytics entry is an
accessibility criterion and it is currently owned by nothing.

---

### 6. The unbounded default is a judgment call, not a defect — and it needs the human

I want to be precise here, because this is the one place where I think the story set
may be **right** and still dangerous.

`FR6.3` ruled the default: all history, no bounds. `AC6.3.1` carries it. I am not
asking for that to be overturned. But the combination of `AC6.3.1` (default =
everything, unbounded) with `AC8.9.2` ("the one quantity that can grow without a
caller-imposed bound") means **the default first view of a year-old store renders a
hand-drawn, native-HTML, dependency-free chart with one point per UTC day** — a
thousand-odd marks, no zoom, no downsampling, and no library permitted to help
(`AC6.4.4`). The stories bound the *response* (`US8.9`) and nothing bounds the
*render*.

P1's goal G1 is "see how that mix moves over time". A first view that cannot be read
fails G1 on the first day it is used. And because `personas.md` records no trigger
(§2.4), nothing in the persona argued the other way.

This is a **judgment call** in the §5 sense, and it belongs to the human, not to me
and not silently to Delivery Planning. Either:

- **(a)** keep all-history as the default and add a criterion that the view stays
  readable as the span grows (downsampling, or a stated maximum rendered length) —
  which is a new obligation on a feature the human scoped tightly; or
- **(b)** default to a bounded trailing window, which reverses an `FR6.3` ruling and
  therefore needs the requirements stage, not this one.

I flag it; I do not choose. What I object to is that the consequence was never named
in any artifact, so it will be discovered during Refined Mockups or later.

---

### 7. Non-goals check — honest result

The persona's *What this persona does not want* list is the strongest part of the
artifact and the story set respects all four items: no chart library (`AC6.4.4`), no
write or delete endpoint anywhere, no hosted anything, `import_id` kept API-only
(`AC6.3.3`). **No story delivers a listed non-goal.** Two near-misses worth naming:

- The no-library guard was written against the *library*, so the hand-drawn chart
  itself passes unexamined (§2.6).
- The unbounded default (§6) is not on the list — but a person who "wants a picture at
  a glance" and gets 1,000 unaggregated points has not been served by it.

I would add one line to the non-goals list: **"a visualisation P1 did not ask for."**

---

### 8. Belongs to Refined Mockups — not objections at this stage

I am explicitly *not* objecting to any of these; naming them so the lead does not read
this file as asking for markup decisions here:

- Exact markup for the breakdown (table vs list), the series graphic, the term lists.
- The literal copy for each error and empty state, and whether `[ Try again ]` is a
  button or re-applying the range.
- Focus-ring styling, contrast values, `aria-live` politeness level, `prefers-reduced-motion`.
- The narrow-layout stacking rules and breakpoint values.
- The stopword list contents (`FR4.4` already assigns these to Design).
- Whether the series is drawn or listed at all — *provided* §6 and §2.6 are settled,
  because if the visualisation is kept it is a real cost.

### 9. If I were ranking the fixes

1. Add the **in-flight / superseded-range** story (§4) — the biggest hole, and it sits
   directly under the set's most-emphasised guarantee.
2. Add the **loading state** story; the empty state needs its own (§1).
3. Split **`AC6.4.5`** into per-state, per-region criteria and give accessibility its
   own home instead of filing it under the failure story (§5).
4. Add a **recovery** criterion to `US6.4` so the confirmed flow's "Retry, or adjust
   the range" is owned (§4).
5. Put the **unbounded default** to the human as a structured question (§6).
6. Fix the **persona**: `P1` collision, G3–G7 voice, G5's "any machine", add a
   trigger and a status quo (§2).
7. Unbundle **`US6.3`**, re-title **`US6.4`**, and name the per-term count and the
   `limit` disposition (§3, R-06).

## Positions

- AGREE: one persona, honoured without inventing a second reader — the answer to Q1 was
  the right one and the story set correctly refuses "so that reviewers can see" phrasing.
- AGREE: the *What this persona does not want* section — it is the most useful part of
  the persona and every one of its four items is honoured somewhere in the criteria.
- AGREE: `AC6.2.2` ("no section is filled from a value the endpoint did not return") —
  pin this; it is the criterion that protects a hand-built view from fabricating numbers.
- AGREE: `AC6.3.3` closing R-04 by keeping `import_id` API-only — correct, and it keeps
  the page from presenting a population it cannot label.
- AGREE: `AC2.1.5` ("every response is byte-identical to before") and `AC3.2.3` — the
  shape-parity pins are the right instinct.
- AGREE: the `US8`-covers-NFRs-not-`FR8` mismatch is called out in the header rather than
  left for a reader to trip over.
- OBJECT: no story owns the in-flight state, and `AC6.3.2` is violable by the most
  natural implementation — two independent fetches with no ordering guard produce
  exactly the mixed population it forbids.
- OBJECT: no story owns Screen 3 (loading) or Screen 5 (partial) as presentations, and
  three controls drawn in the wireframes (`Go to Analyze`, `Clear the range`, the active
  header entry) are named by no criterion at all.
- OBJECT: `AC6.4.5` is one criterion for several basics, at a coarser granularity than
  the mistake this intent's own prior review already flagged; accessibility failures live
  at the state × region intersection, not at the view.
- OBJECT: `US6.1` and `US6.3` describe entries and a control rather than the need;
  `US6.4` is a bin whose title agrees with two of its five criteria.
- OBJECT: `US6.4` covers distinction but not recovery — the confirmed flow promises
  "Retry, or adjust the range" and no criterion owns a retry path or a recovery action.
- OBJECT: `personas.md` collides `P1` (persona) with `P1`–`P8` (pains), writes five
  goals in the system's voice, and claims "on any machine" against a Context that says
  one machine.
- OBJECT: the persona records no trigger and no status quo, which is why the unbounded
  all-history default was adopted without anything pushing back — that combination is a
  judgment call for the human, not a defect I am claiming here.
- OBJECT: nothing in the persona asks for a chart, yet a hand-drawn chart is the view's
  central commitment; the non-goal list forbids the library and therefore passes the
  chart unexamined.
- OBJECT: pain P6 justifies the concurrency fix by a page that polls, and no story
  polls — persona and stories disagree about the view.
- OBJECT: R-06's per-term count semantics (texts vs occurrences) is unowned, so the
  ambiguous `(12)` in the wireframe reaches the view unchallenged.
- OBJECT: an empty store and an empty range are indistinguishable in the set, and
  Screen 2's "widen the range above" copy is wrong for a first-run view.