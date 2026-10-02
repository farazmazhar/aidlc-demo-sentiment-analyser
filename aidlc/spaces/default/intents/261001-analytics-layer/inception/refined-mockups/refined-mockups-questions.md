# Refined Mockups — Design Questions

> Brownfield, existing UI. The rough wireframes came from Ideation; the story set
> and requirements came from Inception. Three questions were answered before this
> file was written, because the wireframes described a page that does not exist.

## Q1 — How is the analytics view reached?

**Answered.** The wireframes draw a `header` with `[ Analyze ] [ Analytics ]`
links and a `footer`. `app/static/index.html` has **no `header`, no `nav` and no
`footer`** — the page is a fixed connection button plus a bare `<main>` holding the
form, an error panel, a result panel and a History *section*. So `US6.1.1`'s "a
third top-level entry alongside the two that exist" rested on a fiction.

**Ruling: option 1.** Add a real `nav` landmark with three links — Analyze,
History, Analytics — so the story is literally true. The existing History section
moves under its own link.

## Q2 — Where do analytics errors render?

**Answered.** The page already has `section[data-testid="error-panel"]` with
`role="alert"` for the analyze flow.

**Ruling: option 1.** Reuse it. One error surface app-wide. `US6.4.1`'s
requirement that an error region be distinct from the empty-result region is met by
the *empty* region, not by a second error panel.

## Q3 — How is a share rendered?

**Answered.** The wireframes render percentages (`62%`, `30%`, `8%`) and show a
zero-share label as `0%`. The ruled API returns a **fraction**, and `null` when
`total` is zero.

**Ruling: option 1.** Render the fraction as a percentage for display; render a
`null` share as an explicit no-share marker. The wireframes' `0%` is corrected by
this ruling.

---

## Q4 — How is the per-day series drawn?

The wireframes draw a line-ish ASCII plot with axis labels. `FR6.6` and `NFR6`
admit no chart library, and the runtime cap of two packages admits none either.
Native options: an SVG polyline, a table plus a text summary, or CSS-positioned
bars.

A. **SVG polyline** plus the per-day values also present as text — closest to the
   wireframes, still zero dependencies
B. **Table only**, with no graphic. Simplest, fully accessible, but loses the
   trend-at-a-glance the persona's `G8` asks for
C. **SVG polyline for wide viewports, table only below the breakpoint** — one
   layout that satisfies both
D. Other (please specify)

[Answer]: A. An SVG polyline with the per-day values also present as text. The text list carries `date` and `total` only (Q8 ruling A), so it is an exact text equivalent of the plotted line.

## Q5 — What is the default date range in the two date inputs?

`Q10` at Requirements Analysis ruled the API's default is **unbounded — all
history, no bounds**. `AC6.3.1` requires the view to show an unbounded state
"rather than a range someone invented". So what do the two inputs *display* on
first load?

A. **Both empty**, with a placeholder such as `all time`, and the view showing all
   history. This is what `AC6.3.1` describes
B. Pre-filled with the earliest stored date and today — concrete, but the
   displayed range is a snapshot that goes stale
C. **From** empty, **To** empty, with an "All time" chip beside them
D. Other (please specify)

[Answer]: A. Both inputs empty, with the 'all time' wording as **visible text beside the control**. The placeholder mechanism Q9 named was impossible: browsers do not render `placeholder` on `type="date"`, so the inputs stay `type="date"` and keep their native picker (Q9 ruling A).

## Q6 — What is the analytics view's relationship to the two existing panels?

Option 1 above added a nav with three links. That implies the analyze form, the
result panel and History become views rather than always-visible sections.

A. **Three views in one page**, switched by the nav: Analyze shows the form and
   result panel; History shows the history list; Analytics shows the four regions.
   One page, three views, `aria-current` on the active link
B. **Analytics is added as a fourth region** below the existing content, and the
   nav links are anchors that scroll. Less restructuring, but the nav's "entries"
   are then not views
C. Other (please specify)

[Answer]: A. Three views in one page switched by the nav, with `aria-current` on the active link.

## Q7 — Does the nav appear on every view, and what is in it?

The connection indicator is currently `position: fixed` at the top-left. If a nav
is added, does the indicator move into the header, and does the nav carry a title?

A. A `header` containing the `h1` and the `nav`; the connection indicator moves
   into it as a non-fixed element. The three links are `Analyze`, `History`,
   `Analytics`, with `aria-current="page"` on the active one
B. A `nav` only, with the `h1` left where it is inside `main`
C. Other (please specify)

[Answer]: A. A `header` landmark containing the `h1` and the `nav`, with the connection indicator moving into it as a non-fixed element.

## Q8 — What does the per-day text list carry?

`AC2.3.2` has each series entry carry `date`, `total`, `counts`, `shares`,
`mean_confidence` and `mean_confidence_row_count`. The design's text list carried
`date` and `total` only, making it an exact text equivalent of the plotted line
rather than a complete one.

A. `date` and `total` only — the list mirrors the plotted line exactly
B. `date`, `total`, the per-label counts and shares, and `mean_confidence` per day
C. Other (please specify)

[Answer]: A. `date` and `total` only.

## Q9 — The "all time" placeholder cannot exist

Q5 asked for a placeholder in the two date inputs. Browsers do not render
`placeholder` on `type="date"`, so the literal mechanism is impossible.

A. Accept the visible-text approach beside the control; drop the placeholder
B. Switch to `type="text"` with a real placeholder
C. Other (please specify)

[Answer]: A. Visible text beside the control; the inputs stay `type="date"` so the native picker and keyboard behaviour are preserved.

## Q10 — Two fetch-behaviour changes the nav ruling causes

Three views means History and Analytics fetch on **activation** rather than page
load, and Analytics refetches on every activation. No story asks for either.

A. Accept both as consequences of the ruling
B. Keep History eager on load; only Analytics fetches on activation
C. Other (please specify)

[Answer]: A. Accept both, recorded as changes to existing behaviour that the nav ruling caused.

## Q11 — The footer and the media query

The wireframes' `footer` was dropped, and the narrow layout uses content-driven
wrap thresholds instead of a named `@media` query — the shipped stylesheet has none.

A. Accept both — no footer, content-driven wrapping
B. Restore the footer with a short reassurance line
C. Other (please specify)

[Answer]: A. Accept both, recorded as deliberate omissions.

## Upstream corrections this stage found

Registered for `requirements.md` Revision 3 rather than silently absorbed:

| Requirement | Defect |
|---|---|
| `FR2.7` | Rounds shares to four decimal places but states **no tie rule**, and a tie is reachable — over a denominator of 128, a count of 36 is exactly `0.28125`, so half-up gives `0.2813` and half-even `0.2812`. `FR8.2` requires a hand-pinned share value, so that value is **implementation-defined** until a tie rule exists. The mockups choose a fixture with no tie and take no side. |
| `FR6.8` | Cites `[RM-5]`; confirmed unsourceable — no `RM-n` ids exist in the Ideation artifacts. Already in Revision 2; restated here because this stage needed the citation and could not use it. |
| `FR6.5` / wireframes | The wireframes assert "raw error codes are never shown to the user". `app.js`'s `readErrorMessage` prefixes `${payload.code}:`, so the existing Analyze flow **already shows one**. The analytics view diverges deliberately and says so. |
| Brief corrections | `tests/test_page.py`'s `REQUIRED_TEST_IDS` pins **14** of 16 hooks, not 12; the two unpinned are `history-item-text` and `history-item-meta` inside the `<template>`. The `<template>` also lives inside `<main>`. |

## Consolidated Summary Confirmation

- **A real `nav` landmark is added**, carrying Analyze, History and Analytics as three links, and the page becomes three views in one document switched by that nav, with `aria-current` on the active link.
- **The existing `error-panel` is reused** for analytics errors. One error surface app-wide; no second error panel is specified, and the empty-result region is what makes an error distinguishable from an empty answer.
- **Shares render as percentages for display, and a `null` share renders as an explicit no-share marker** — never `0.00%`. The wireframes' bare `0%` for a zero-share label is corrected by this ruling.
- **The per-day series is a native SVG polyline**, with the per-day values also present as text. The text list carries `date` and `total` only, so it is an exact text equivalent of the plotted line rather than a mirror of every field the API returns.
- **Both date inputs ship empty**, with the "all time" wording as visible text beside the control. The placeholder mechanism Q5 named is impossible on `type="date"`, and the inputs keep their native picker.
- **A `header` holds the `h1` and the `nav`**, and the connection indicator moves into it as a non-fixed element.
- **Two fetch-behaviour changes are accepted as consequences of the nav ruling**: History and Analytics fetch on activation rather than on page load, and Analytics refetches on every activation. Neither is requested by a story or covered by an acceptance criterion.
- **The footer is dropped and no `@media` query is added** — both deliberate. The narrow layout wraps on content-driven thresholds.
- **`Mean intensity` appears nowhere**, and the shipped page test forbids the phrase in the served page; the summary carries total analyses and mean confidence only.
- **Two of the brief's own facts were wrong and are corrected**: `REQUIRED_TEST_IDS` pins 14 of 16 hooks, not 12, and the two unpinned ones sit inside a `<template>` that lives in `<main>`.
- **The "raw codes are never shown" claim is false of the shipped app.** `app.js` already prefixes `${payload.code}:`, so the analytics view's code-free error text is a deliberate divergence from shipped behaviour, recorded as such.
- **Four upstream defects are registered for `requirements.md` Revision 3**, including that `FR2.7` fixes four-decimal share rounding with **no tie rule** while `FR8.2` requires a hand-pinned value — over a denominator of 128 a count of 36 is exactly `0.28125`, so the pinned value is currently implementation-defined.

- `Looks correct`
- `Request changes`

[Answer]: Looks correct
