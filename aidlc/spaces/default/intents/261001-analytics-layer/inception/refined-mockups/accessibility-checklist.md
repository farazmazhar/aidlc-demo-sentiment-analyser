# Accessibility Checklist — Analytics View (Refined)

> **Target: WCAG 2.1 Level AA.**
>
> **Granularity: one line per screen per region.** A screen with four visible
> regions gets four lines, not one bundled line and not one line per component
> with the screens implied. `US6.4.5a`, `AC6.4.5b` and `AC6.4.5c` were split from
> a single bundled criterion by the User Stories review for exactly this reason —
> the bundled version was one assertion with three `Given/When/Then` triples
> chained by "and". This checklist is written so that no line can be satisfied by
> another line's work.
>
> Each line names a **concrete element** and the **acceptance criterion it
> serves**.
>
> **A note on what can actually be verified here.** `NFR7` forbids introducing
> browser automation, and `tests/test_page.py` asserts served markup statically:
> nothing in this repository executes `app.js`. So the checks below divide into
> three groups, and the table marks which is which:
>
> - **[M]** — decidable by a static markup assertion in `tests/test_page.py`.
> - **[C]** — decidable by reading `app.js` (a code path, no execution).
> - **[V]** — needs a human with a browser, a screen reader or a colour picker.
>   These are **not** verifiable by any test in this repository and are listed
>   again in §4 as the manual verification set.

---

## 1. Screens and their regions

| Screen | State | Visible regions |
|---|---|---|
| **S1** | Analyze, active (page default) | header/nav · header/connection indicator · lede · analyze form · result panel (when a result exists) |
| **S2** | History, active | header/nav · header/connection indicator · history heading + empty message · history list |
| **S3** | Analytics, populated | header/nav · header/connection indicator · view heading · range control · range-state line · summary · series · breakdown · positive terms · negative terms |
| **S4** | Analytics, empty | header/nav · header/connection indicator · view heading · range control · range-state line · empty region |
| **S5** | Analytics, loading | header/nav · header/connection indicator · view heading · range control · loading region · skeletons |
| **S6** | Analytics, error (422, and 500) | header/nav · header/connection indicator · view heading · range control · error panel |
| **S7** | Analytics, partial failure | header/nav · header/connection indicator · view heading · range control · partial status region · series + breakdown (succeeded) · term lists (failed) · error panel |
| **S8** | Analytics, edge — one day, one row, a real zero share, one empty term list | header/nav · header/connection indicator · view heading · range control · summary · series (single point) · breakdown · positive terms · negative terms |
| **S9** | Narrow layout, ≤ 520 px, all three views | reflow of every region above |

---

## 2. S1 — Analyze view (the page's default state)

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header / nav | `header` > `nav[aria-label="Views"]` | A `navigation` landmark exists with an accessible name, so it is distinguishable from any future nav | 1.3.1, 2.4.1 | `AC6.1.1`, `AC6.1.4` | [M] |
| Header / nav | `a[data-testid="nav-analyze"]` | Carries `aria-current="page"`; the other two links carry **no** `aria-current` | 4.1.2 | `AC6.1.4`, ruling 7 | [M] |
| Header / nav | `a[data-testid="nav-analyze"]`, `nav-history`, `nav-analytics` | All three are native links with visible text; each is reachable by `Tab` and activated by `Enter` | 2.1.1, 4.1.2 | `AC6.1.1`, `FR6.6` | [M] |
| Header / nav | `.site-nav a` | Visible text label; no `aria-label` overriding it; no `outline: none` anywhere in the file | 2.4.7, 2.4.11 | `US6.1` | [M] |
| Header / connection | `button[data-testid="connection-status"]` | Remains a native `<button>` with an accessible name from its inner text span; activating it with `Space` still works | 4.1.2, 2.1.1 | `AC5.3.2` preserved | [M] |
| Header / connection | `span[data-testid="connection-status-text"]` | Keeps `role="status"` and `aria-live="polite"`; the state is written in words so colour is never the only signal | 4.1.3, 1.4.1 | `AC5.3.2` | [M] |
| Header / connection | `.connection-indicator` | Loses `position: fixed` and gains a place in DOM order that matches visual order | 1.3.2 | ruling 7 | [M] |
| View heading | `h2#analyze-heading` | Heading order is `h1` (header) → `h2` (view) → `h3` (result), with no level skipped | 1.3.1 | `FR6.8` | [M] |
| Lede | `p.lede` | Plain prose; the only dimmed text on the view is the pre-existing `.lede` opacity | 1.4.3 | — | [V] |
| Analyze form | `label[for="analyze-input"]` + `textarea[data-testid="analyze-input"]` | Visible label bound by `for`; the placeholder is supplementary, never the only label | 3.3.2, 1.3.1 | `AC2.2.3` preserved | [M] |
| Analyze form | `button[data-testid="analyze-submit-button"]` | Focus is never trapped; the button is re-enabled in the existing `finally` block | 2.1.2 | `AC2.2.3` | [C] |
| Result panel | `section[data-testid="result-panel"]` | Keeps `aria-live="polite"`; unchanged by this feature | 4.1.3 | `AC2.1.3` preserved | [M] |
| Result panel | `h2` → `h3` | Heading level change is the only edit; the hook and text are untouched | 1.3.1 | §2.4 of `mockups.md` | [M] |
| Page language | `html[lang="en"]` | Declared and unchanged | 3.1.1 | — | [M] |
| Reflow | `body` | Unchanged; already a single 46 rem fluid column | 1.4.10 | S9 | [M] |

---

## 3. S2 — History view

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header / nav | `a[data-testid="nav-history"]` | Carries `aria-current="page"` while History is the active view, and no `aria-current` otherwise | 4.1.2 | `AC6.1.4` | [M] |
| View region | `section[data-testid="history-view"]` | Named by `aria-labelledby="history-heading"`, so it is a `region` landmark; a **duplicate** `History` heading is not introduced | 1.3.1, 2.4.1 | ruling 6 | [M] |
| Empty message | `p[data-testid="history-empty"]` | Plain text, no colour coding, no icon-only meaning | 1.4.1 | — | [M] |
| History list | `ol[data-testid="history-list"]` | A real ordered list with `list-style: none`; `role="list"` is restored so the list semantics survive the removed marker | 1.3.1 | `FR6.6`, `AC6.4.4` | [M] |
| History list | `li` rows cloned from `template[data-testid="history-item"]` | Each row is `span` + `span`, both populated with `textContent`; no HTML string. The `<template>` currently lives inside `<main>` and is moved to the end of `<body>` | 1.3.1 | `AC6.4.4` | [C] |
| History list | `.history-meta` | Pre-existing `opacity: 0.85`; contrast under both `light` and `dark` schemes is a pre-existing verification item, not introduced here | 1.4.3 | — | [V] |
| Focus | `#history-view` | Focus enters the view on keyboard activation; no focusable element is trapped in a `hidden` view | 2.4.3, 2.1.2 | ruling 6 | [C] |

---

## 4. S3 — Analytics view, populated

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header / nav | `a[data-testid="nav-analytics"]` | Carries `aria-current="page"` while Analytics is active | 4.1.2 | `AC6.1.4` | [M] |
| View region | `section[data-testid="analytics-view"]` | Named `region` via `aria-labelledby="analytics-heading"`; `tabindex="-1"` makes it programmatically focusable **without** entering the tab order | 2.4.3 | `AC6.2.1` | [M] |
| Range control | `form[data-testid="analytics-range-form"]` | A native form; `Enter` in either input submits; `preventDefault` stops navigation | 2.1.1, 3.2.2 | `FR6.3` | [C] |
| Range control | `input[data-testid="analytics-range-from"]` | Bound to a visible `label[for="analytics-range-from"]` reading `From` | 3.3.2, 1.3.1 | `AC6.4.5a` | [M] |
| Range control | `input[data-testid="analytics-range-to"]` | Bound to a visible `label[for="analytics-range-to"]` reading `To` | 3.3.2, 1.3.1 | `AC6.4.5a` | [M] |
| Range control | both `input[type="date"]` | Ship with **no `value`**, so both are empty on first load; and **no `placeholder`**, which browsers do not render on `type="date"` | 3.3.2 | `AC6.3.1`, ruling 5 | [M] |
| Range control | `button[data-testid="analytics-range-apply"]` | `type="submit"`; carries `disabled` while a fetch pair is in flight; reachable by `Tab`, activated by `Enter` or `Space` | 4.1.2, 2.1.1 | `AC6.3.6` | [M] |
| Range control | `button[data-testid="analytics-range-clear"]` | `type="button"`, so it cannot submit the form by accident; `disabled` when both inputs are empty | 4.1.2 | `AC6.3.4` | [M] |
| Range-state line | `p[data-testid="analytics-range-state"]` | States the range in effect in words — `Showing all stored analyses (all time).` — so the unbounded state is announced by text, not inferred from two blank fields | 1.3.1, 3.3.2 | `AC6.3.1` | [M] |
| Loading region | `section[data-testid="analytics-loading"]` | Ships `hidden`; carries `role="status"` **and** `aria-live="polite"`; a **distinct region** from empty and from error | 4.1.3, 1.3.1 | `AC6.4.5c`, `AC6.5.5` | [M] |
| Empty region | `section[data-testid="analytics-empty"]` | Ships `hidden`; distinct element from the error panel, so a test can tell them apart | 1.3.1 | `AC6.4.1`, `AC6.5.5` | [M] |
| Partial region | `section[data-testid="analytics-partial"]` | Ships `hidden`; `role="status"` + `aria-live="polite"`, distinct from the alert | 4.1.3 | `AC6.5.5` | [M] |
| Summary region | `section[data-testid="analytics-summary"]` | Named `region` via `aria-labelledby`; ships `hidden` | 1.3.1 | `FR6.2` | [M] |
| Summary values | `dl.summary-figures` > `dt`/`dd` | Native description list: each `<dt>` is the visible name of its `<dd>`, so "128" is never announced without "Total analyses" | 1.3.1 | `FR2.3` | [M] |
| Summary values | `dd[data-testid="analytics-total"]`, `dd[data-testid="analytics-mean-confidence"]` | Only two figures. `Mean intensity` appears nowhere in the page, and the shipped test forbids the word | 1.3.1 | `FR2.3`, `AC2.1.3` | [M] |
| Summary values | `dd[data-testid="analytics-mean-confidence"]` | A fraction shown as returned; no unit, icon or colour is added that the value does not already carry | 1.3.1 | `FR2.8` | [C] |
| Series region | `section[data-testid="analytics-series"]` | Named `region` via `aria-labelledby`; ships `hidden` | 1.3.1 | `AC6.2.1` | [M] |
| Series caption | `p[data-testid="analytics-series-caption"]` | **Visible** sentence giving the span, the day count, the zero-day count and the peak — the long description for a complex graphic, and the target of the `<svg>`'s `aria-labelledby` | 1.1.1 | `AC6.4.5b`, `FR6.8` | [M] |
| Series drawing | `svg[data-testid="analytics-series-chart"]` | `role="img"` + `aria-labelledby="analytics-series-caption"`; the subtree is flattened, so the axis `<text>` labels are not announced twice | 1.1.1, 4.1.2 | `AC6.4.5b` | [M] |
| Series drawing | `polyline[data-testid="analytics-series-line"]` | `stroke="currentColor"` at `stroke-width: 2` with `vector-effect="non-scaling-stroke"`, so it holds 2 px at any rendered size — a graphical object meeting 3:1 | 1.4.11 | `FR6.6` | [M] |
| Series drawing | the three `text` axis labels | Inside a `role="img"` subtree, so they are presentational to AT while remaining visible to sighted users | 1.1.1 | `AC6.4.5b` | [M] |
| Series values | `ol[data-testid="analytics-series-values"]` | **Every** per-day value the drawing uses is present as text — date and total, an exact text equivalent of the plotted line — so the series is never conveyed by geometry alone. The list is a deliberate subset of the series entry, which `AC2.3.2` has the API return more richly | 1.1.1, 1.3.1 | `AC6.4.5b` | [M] |
| Series values | each `li` | One `li` per series entry, written with `textContent`; 30 entries for 30 days, none skipped or truncated. Each `li` carries only `date` and `total` | 1.1.1 | `AC2.3.1` | [C] |
| Breakdown region | `section[data-testid="analytics-breakdown"]` | Named `region` via `aria-labelledby`; ships `hidden` | 1.3.1 | `AC6.2.1` | [M] |
| Breakdown table | `table.breakdown-table` | A real `<table>` with `<caption>` and `<thead>`; **no `role` attribute** is added to an element that already has the semantics | 1.3.1, 4.1.2 | `FR6.6`, `AC6.4.4` | [M] |
| Breakdown table | `th[scope="col"]` × 3 | Column headers scoped, so a screen reader announces "Count" and "Share" with each cell | 1.3.1 | `FR6.2` | [M] |
| Breakdown table | `td` in the Share column | A real share renders as a percentage written in the cell; a `null` share renders the literal `no share` — never `0%`, never an em dash, never an empty cell | 1.3.1, 1.4.1 | `AC6.2.5`, `AC2.1.4` | [C] |
| Breakdown table | `td` in the Label column | Label text comes from `LABEL_ORDER`; a label the response omitted renders as `null`, never `NaN` and never a blank cell | 1.3.1 | `FR2.7` | [C] |
| Terms region | `section[data-testid="analytics-terms"]` | Named `region` via `aria-labelledby`; ships `hidden` | 1.3.1 | `AC6.2.1` | [M] |
| Terms lists | `ol[data-testid="analytics-positive-terms"]`, `ol[data-testid="analytics-negative-terms"]` | Real ordered lists with `role="list"` restored; rank is carried by the list itself, not by font size, weight or colour | 1.3.1, 1.4.1 | `FR3.5`, `FR6.2` | [M] |
| Terms lists | each `li` | Term text and count are both plain text in the same item, so neither is lost when read flat | 1.3.1 | `FR3.3` | [C] |
| Terms lists | `h4` × 2 under `h3` | Heading level never skipped: `h1` → `h2` Analytics → `h3` Top terms → `h4` per polarity | 1.3.1 | `FR6.8` | [M] |
| Error panel | `section[data-testid="error-panel"]` | Ships `hidden` with empty text; **not shown** in this state, so no alert announces spuriously | 4.1.3 | `AC6.4.1` | [M] |
| Colour | all analytics text | Plain `currentColor`; **no `opacity`** is used on any new text, so contrast is computable under `color-scheme: light dark` | 1.4.3, 1.4.11 | `FR6.8` | [M] |
| Focus | the whole view | Focus moves to `#analytics-view` on keyboard activation; no element inside a `hidden` view ever retains focus | 2.4.3 | ruling 6 | [C] |

---

## 5. S4 — Analytics view, empty

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header / nav | `a[data-testid="nav-analytics"]` | `aria-current="page"` retained while the view is empty | 4.1.2 | `AC6.1.4` | [M] |
| Range control | both `input[type="date"]` | Both hold values here, and the range-state line states the bounded range in words | 3.3.2 | `AC6.3.1` | [C] |
| Range-state line | `p[data-testid="analytics-range-state"]` | Reads `Showing 2026-10-01 to 2026-10-31.`, so the empty result is unambiguously about that range | 1.3.1 | `AC6.3.1` | [C] |
| Empty region | `section[data-testid="analytics-empty"]` | Becomes visible; a **distinct element** from `error-panel`, so an empty answer can never be mistaken for a failure | 1.3.1, 3.3.1 | `AC6.4.1`, `AC6.5.5` | [M] |
| Empty region | `h3#analytics-empty-heading` | Names the region; heading order unbroken from `h2` | 1.3.1 | `FR6.8` | [M] |
| Empty region | the explanation `<p>` | States the cause in plain words — no code, no status number, no jargon — and gives two concrete next steps | 3.3.1, 3.2.4 | `FR6.7`, `NFR4` | [C] |
| Empty region | `a[data-testid="analytics-empty-analyze"]` | A real link with visible text, reachable by `Tab`, activated by `Enter`; it routes through the same view switch as the nav | 2.1.1, 2.4.4 | `AC6.5.4` | [M] |
| Absent regions | summary, series, breakdown, terms | All `hidden`. No table of `0`s, no `no share` column, no empty chart frame, and **no `0%`** anywhere | 1.3.1, 3.3.1 | `AC2.1.4`, `NFR4` | [C] |
| Error panel | `section[data-testid="error-panel"]` | Stays `hidden` — an empty range is an answer, not a failure, and no alert fires | 4.1.3 | `AC6.4.1` | [M] |
| Illustration | — | Deliberately none. The wireframes' own "no icon needed" note stands; no decorative asset is added | 1.1.1 | — | [M] |

---

## 6. S5 — Analytics view, loading

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header / nav | all three links | Nav remains fully operable while a fetch is in flight; navigation is never blocked by a pending request | 2.1.1 | `US6.5` | [C] |
| Range control | `button[data-testid="analytics-range-apply"]` | Carries `disabled` while in flight, and is re-enabled in a `finally` block so a failed fetch cannot strand it | 4.1.2, 2.1.2 | `AC6.3.6` | [C] |
| Loading region | `section[data-testid="analytics-loading"]` | Visible; `role="status"` + `aria-live="polite"`, so the change is announced **without** stealing focus | 4.1.3, 3.2.1 | `AC6.5.1`, `AC6.4.5c` | [M] |
| Loading region | the visible sentence | Text is rewritten on every entry into loading, so a repeat announcement actually re-announces | 4.1.3 | `AC6.5.1` | [C] |
| Skeletons | `div.skeleton` × N | Marked `aria-hidden="true"`, so a screen reader hears the status sentence and not a dozen empty rectangles | 1.1.1 | `AC6.5.1` | [M] |
| Skeletons | `div.skeleton` | No animation is specified at all, so `prefers-reduced-motion` is satisfied without a media query | 2.3.3 | `FR6.8` | [M] |
| Stale content | summary, series, breakdown, terms | Previous figures are cleared rather than left under the skeletons — a stale table beside a spinner is two sections disagreeing about their range | 3.2.1 | `AC6.5.3` | [C] |
| Focus | the whole screen | Focus stays where the user put it (on `Apply`). Focus is never moved to a loading message | 2.4.3 | `US6.5` | [C] |
| Reflow | loading region | Block widths track the regions below them at every width | 1.4.10 | S9 | [V] |

---

## 7. S6 — Analytics view, error (422 and 500)

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header / nav | `a[data-testid="nav-analytics"]` | `aria-current="page"` retained; the error does not navigate away or change the active view | 4.1.2 | `AC6.1.4` | [M] |
| Error panel | `section[data-testid="error-panel"]` | The **existing** element, reused. `role="alert"` unchanged; no second error element is added anywhere on the page | 4.1.3 | `AC6.4.1`, ruling 2 | [M] |
| Error panel | its position in `<main>` | Sits above all three views, so the alert is above the fold and reachable whichever view is active | 2.4.3 | ruling 2 | [M] |
| Error panel | its text content | A status-derived lead-in plus the envelope's `message` verbatim. **No machine code is displayed** — a deliberate divergence from **shipped behaviour**: the existing Analyze flow's `readErrorMessage` already shows `${payload.code}: ${payload.message}` (`app.js:30–40`), so the wireframes' "codes never surface" was never true of the page. The analytics view chooses the quieter rendering | 3.3.1 | `FR6.7`, `NFR4` | [C] |
| Error panel | 422 lead-in vs 500 lead-in | `The date range was refused.` and `The analytics query failed.` are visibly different words, so a rejected question and a broken query are distinguishable **on screen**, not only in the response | 3.3.1 | `AC6.4.2` | [C] |
| Error panel | neither case | Neither reads as an empty success: no `0`s, no `no share`, no empty chart, no silent blank | 3.3.1, 1.3.1 | `AC6.4.2`, `NFR4` | [C] |
| Error panel | recovery | The screen offers `Show all time` and two editable date fields, so the user can correct or widen without leaving the view | 3.3.1, 3.2.4 | `FR6.7`, `AC6.3.4` | [M] |
| Range-state line | `p[data-testid="analytics-range-state"]` | Keeps the **last accepted** range, not the refused pair, so the line never claims a population that does not exist | 1.3.1 | `AC6.3.1` | [C] |
| Absent regions | summary, series, breakdown, terms | Remain `hidden` — a refused query computes nothing and therefore renders nothing | 1.3.1 | `FR2.11`, `AC2.4.3` | [C] |
| Error panel | its red `#b00020` | The message **text** carries the failure; the red border is redundant, so colour is never the only signal. Contrast of `#b00020` on a **dark** canvas is a pre-existing verification item | 1.4.1, 1.4.3 | `AC5.3.2` principle | [V] |
| Focus | the whole screen | Focus is **not** moved to the alert; it stays on the range control the user is editing | 2.4.3 | `US6.5` | [C] |

---

## 8. S7 — Analytics view, partial failure

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header / nav | all three links | Fully operable during and after a partial failure | 2.1.1 | `US6.5` | [C] |
| Partial status | `section[data-testid="analytics-partial"]` | Visible; `role="status"` + `aria-live="polite"` — polite, not assertive, because the alert has already spoken | 4.1.3 | `AC6.5.3` | [M] |
| Partial status | its text | States coverage in the page's own words — `Showing 2 of 3 sections for this range. The term lists could not be read.` — so the user knows **which** part is missing, not merely that something is | 1.3.1, 3.3.1 | `AC6.5.3` | [C] |
| Partial status | its element kind | Polite status, not an alert, and with no red border — so it is not a second error surface | 4.1.3 | ruling 2 | [M] |
| Succeeded regions | whichever response arrived | The successful half renders fully, from the response that arrived, for the same range the range-state line names. When the summary fetch fails and terms succeed, the term lists are the succeeded regions; when terms fail and summary succeeds, summary, series and breakdown are | 1.3.1 | `AC6.5.3`, `AC6.3.2` | [C] |
| Failed regions | the failed half's own positions | Every failed region keeps its heading and reads `not loaded` in place of its data — `analytics-total-not-loaded`, `analytics-series-not-loaded`, `analytics-breakdown-not-loaded` when the summary fetch failed, or both term `<ol>` positions when the terms fetch failed. **Never** left as an empty `<ol>`, `<dl>` or `<table>` with no guidance, and never hidden with no stated reason | 1.3.1 | `AC6.5.3` | [C] |
| Error panel | `section[data-testid="error-panel"]` | Carries the failure message with the section named — the one error surface, still the only one | 4.1.3 | `AC6.4.1`, ruling 2 | [M] |
| Population | all rendered regions | A stale response is discarded rather than rendered, so no two sections ever describe different ranges | 3.2.1 | `AC6.5.2`, `AC6.3.2` | [C] |
| Reflow | partial status | A single `<p>`, wrapping to two lines on a narrow viewport; never truncated | 1.4.10 | S9 | [V] |

---

## 9. S8 — Analytics view, edge case (one day, one row, a real zero share)

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header / nav | `a[data-testid="nav-analytics"]` | `aria-current="page"` retained | 4.1.2 | `AC6.1.4` | [M] |
| Range control | both inputs, equal values | `from` equal to `to` is treated as **one** day, and the caption says `1 day in range` — not zero days and not two | 1.3.1 | `AC2.2.5` | [C] |
| Summary region | `dd[data-testid="analytics-total"]` | Reads `1`. A count is never rendered as a word or padded to a width | 1.3.1 | `FR2.3` | [C] |
| Series region | `svg` containing `circle`, **no** `polyline` | A one-point series renders a marker. A `<polyline>` with one point draws nothing, which would present this state as an empty chart | 1.1.1 | `FR6.2`, `AC6.3.2` | [C] |
| Series region | `p[data-testid="analytics-series-caption"]` | States `Highest 1 on 2026-09-01.`, so the single point is described in words as well as drawn | 1.1.1 | `AC6.4.5b` | [M] |
| Series values | `ol[data-testid="analytics-series-values"]` | Exactly one `li`; the text twin is present even when the drawing is a single point | 1.1.1 | `AC6.4.5b` | [C] |
| Breakdown table | Share cell, `negative` row | Reads **`0.00 %`** — a real zero from a real denominator, rendered as a percentage. It is **not** the `no share` marker | 1.3.1, 1.4.1 | `AC6.2.5`, `FR2.7` | [C] |
| Breakdown table | Share cell, `neutral` row | Reads `0.00 %` for the same reason | 1.3.1 | `AC6.2.5` | [C] |
| Breakdown table | Share cell, `positive` row | Reads `100.00 %`; two decimal places preserve exactly the API's four-decimal fraction | 1.3.1 | `AC2.1.2` | [C] |
| Positive terms | `ol[data-testid="analytics-positive-terms"]` | One item rendered; the response order is used verbatim, so an alphabetical tie-break is preserved as the API stated it | 1.3.1 | `FR3.5`, `AC3.1.2` | [C] |
| Negative terms | `p[data-testid="analytics-negative-terms-empty"]` | Visible and reads `No negative terms in this date range.` — an empty list is explained, never silent | 1.3.1, 3.3.1 | `AC3.1.4`, `AC4.1.6` | [M] |
| Negative terms | `ol[data-testid="analytics-negative-terms"]` | Empty, and `role="list"` still present so it is not a mystery element | 1.3.1 | `AC3.1.4` | [M] |
| Contrast | `0.00 %` vs `no share` | Both are text, so the difference between "no share" and "zero share" is legible in greyscale and to a colour-blind reader | 1.4.1 | `AC6.2.5` | [M] |

---

## 10. S9 — Narrow layout (≤ 520 px, all three views)

| Region | Element | Check | SC | Serves | |
|---|---|---|---|---|---|
| Header | `header` | Title, nav and connection indicator stack in DOM order, which is also visual order; nothing is repositioned with `order` or absolute positioning | 1.3.2 | ruling 7 | [M] |
| Header / nav | `.site-nav` | The three links wrap onto two lines rather than being hidden or collapsed behind a menu — no functionality is lost at any width | 1.4.10, 2.1.1 | `FR6.8` | [M] |
| Range control | `.range-fields` | `repeat(auto-fit, minmax(12rem, 1fr))` stacks the two field pairs below ≈ 392 px, each label staying above its own input | 1.4.10 | `AC6.4.5a` | [M] |
| Range control | `.range-actions` | `flex-wrap: wrap` keeps both buttons reachable; neither shrinks below its label's width nor overlaps | 1.4.4, 1.4.10 | `AC6.3.4` | [M] |
| Summary region | `dl.summary-figures` | `grid-template-columns: max-content 1fr` keeps every `<dt>` beside its own `<dd>` at 320 px; a value is never separated from its name | 1.3.2 | `FR2.3` | [M] |
| Series drawing | `svg.series-chart` | `width: 100%; height: auto` with the `viewBox` scales continuously; `vector-effect="non-scaling-stroke"` holds the stroke at 2 px | 1.4.11, 1.4.10 | `FR6.6` | [M] |
| Series values | `ol.series-values` | Each `<li>` wraps; **nothing is truncated or clipped**, so the text twin is as complete at 320 px as at 46 rem | 1.4.10, 1.1.1 | `AC6.4.5b` | [M] |
| Breakdown table | `table.breakdown-table` | Three columns, `width: 100%`, no horizontal scroll and no content loss at 320 px | 1.4.10 | `FR6.2` | [M] |
| Breakdown table | numeric `<td>` | `font-variant-numeric: tabular-nums` aligns the three percentages without padding hacks or a hidden column | 1.4.1 | `AC6.2.5` | [M] |
| Terms region | `.term-lists` | The two lists stack below ≈ 520 px, positive above negative, preserving DOM and therefore reading order | 1.3.2, 1.4.10 | `FR6.2` | [M] |
| Whole page | `body` | No horizontal scrolling and no loss of content or functionality at 320 px CSS width, and at 400 % browser zoom on a 1280 px viewport | 1.4.10 | `FR6.8` | [V] |
| Whole page | the stylesheet | Wrapping is **content-driven** (`auto-fit` grids and `flex-wrap`); the shipped stylesheet contains **no media query** and none was added (Q11) | 1.4.10 | `FR6.8` | [M] |
| Analyze / History | their regions | Already single-column fluid; no narrow-layout work is needed and none is specified | 1.4.10 | — | [M] |

---

## 11. Focus order across the three views

Tab order follows DOM order, which follows visual order, with no positive
`tabindex` anywhere and no reordering. Each view container is `tabindex="-1"`:
programmatically focusable, **not** in the tab sequence.

### S1 — Analyze active

| # | Element | Note |
|---|---|---|
| 1 | `a[data-testid="nav-analyze"]` | carries `aria-current="page"` |
| 2 | `a[data-testid="nav-history"]` | |
| 3 | `a[data-testid="nav-analytics"]` | |
| 4 | `button[data-testid="connection-status"]` | inside its `role="status"` child, so its accessible name is "OpenRouter: checking…" |
| 5 | `textarea[data-testid="analyze-input"]` | |
| 6 | `button[data-testid="analyze-submit-button"]` | |

End of tab order. `section[data-testid="error-panel"]`, the result panel and the
History view contribute no tab stops, and neither view container is reachable by
`Tab`.

### S2 — History active

| # | Element | Note |
|---|---|---|
| 1 | `a[data-testid="nav-analyze"]` | |
| 2 | `a[data-testid="nav-history"]` | carries `aria-current="page"` |
| 3 | `a[data-testid="nav-analytics"]` | |
| 4 | `button[data-testid="connection-status"]` | |

End of tab order. History rows are not focusable: they are static text, and
making them focusable would add stops that do nothing.

### S3 / S4 / S5 / S6 / S7 / S8 — Analytics active

| # | Element | Note |
|---|---|---|
| 1 | `a[data-testid="nav-analyze"]` | |
| 2 | `a[data-testid="nav-history"]` | |
| 3 | `a[data-testid="nav-analytics"]` | carries `aria-current="page"` |
| 4 | `button[data-testid="connection-status"]` | |
| 5 | `input[data-testid="analytics-range-from"]` | announced "From, edit text, blank" |
| 6 | `input[data-testid="analytics-range-to"]` | announced "To, edit text, blank" |
| 7 | `button[data-testid="analytics-range-apply"]` | `disabled` during loading, so skipped while a fetch is in flight |
| 8 | `button[data-testid="analytics-range-clear"]` | `disabled` when both inputs are empty |
| 9 | `a[data-testid="analytics-empty-analyze"]` | **S4 only** — present in the empty state, absent otherwise |

End of tab order. The loading region, the empty region's explanation, the
summary `<dl>`, the `<svg>`, the table and the two term `<ol>`s contribute **no**
tab stops: none is interactive, and the page specifies no interaction for any of
them. A graphic that captured focus would add a stop with nothing behind it.

### The switch itself

| Step | Event | Focus result |
|---|---|---|
| Keyboard activation of a nav link | user presses `Enter` on the link | focus moves to the newly shown view's container (`#analyze-view` / `#history-view` / `#analytics-view`); the next `Tab` enters that view's first control |
| Pointer activation of a nav link | user clicks the link | focus stays on the link; the view changes underneath, and the next `Tab` continues down the header into the active view |
| View switch while focus is inside the outgoing view | any activation | focus is moved to the incoming view's container, so focus never rests on an element that has just become `hidden` |
| Refetch within Analytics | `Apply` pressed | focus stays on `Apply`; the loading region announces politely and never takes focus |
| Analytics activation with a fetch in flight | user leaves and returns | the previous request is abandoned; a stale response is discarded and never rendered, and focus is untouched |

---

## 12. Checks that apply to every screen, restated as single lines

These are listed once rather than repeated in all nine screens, and are marked as
applying to **all** so they are not mistaken for per-screen items.

| Element | Check | SC | Serves | |
|---|---|---|---|---|
| `html[lang="en"]` | Page language declared; unchanged by this feature | 3.1.1 | — | [M] |
| `section[data-testid="error-panel"]` | Every view activation calls `clearError()` first, so an error raised by one view's data is never present on another view. A stale message from a `hidden` view would be a context-free announcement; clearing on activation prevents it. Full rule: `interaction-spec.md` §13.4 | 4.1.3, 3.3.1 | ruling 2, `AC6.4.1` | [C] |
| every new interactive element | Visible focus indicator: the page sets `outline: none` nowhere, and only `.connection-indicator:focus-visible` carries an explicit rule | 2.4.7 | `FR6.8` | [M] |
| UA focus rings on links, inputs and buttons | Contrast of the UA default indicator against adjacent colours is unverified; verifying it needs a colour picker | 1.4.11 | `FR6.8` | [V] |
| every new text node | Rendered with `textContent`; no `innerHTML`, no HTML template literal, so no markup injection surface exists in the analytics view | 4.1.2 | `AC6.4.4` | [C] |
| `button` padding `0.5rem 1rem` | Height is under the 44 px touch-target guidance. SC 2.5.5 is AAA, not AA; raising it would change the existing Analyse button too, so it is inherited and named | 2.5.5 (AAA) | — | [V] |
| `#b00020` on a light canvas | About 6.6:1 — inherited from the shipped error panel, unchanged | 1.4.3 | `AC6.4.1` | [V] |
| `#b00020` on a dark canvas | Contrast lower than on light; the shipped style predates this feature and is not re-coloured here | 1.4.3 | `AC6.4.1` | [V] |
| `.skeleton` blocks | Muted `currentColor` background with no animation; decorative and `aria-hidden` | 1.4.11 | `AC6.5.1` | [V] |
| whole page | 400 % zoom at a 1280 px viewport produces no horizontal scrolling and no loss of function | 1.4.10 | `FR6.8` | [V] |
| whole page | No time limit, no auto-updating content, no flashing content | 2.2.1, 2.3.1 | — | [M] |

---

## 13. What this checklist cannot claim

| Honest limitation | Why |
|---|---|
| No line here is verified by running a browser | `NFR7` and the two-runtime-dependency cap forbid browser automation; `tests/test_page.py` asserts served markup only |
| The `[M]` lines are decidable **only once the markup exists** — this stage specifies it; it does not ship it | The implementation stage adds the 34 new hooks to `REQUIRED_TEST_IDS` (which pins **14** of the page's 16 existing hooks today, not 12), and the markup they pin |
| The `[C]` lines are decidable by reading `app.js`, so they belong to Code Generation's review, not to a test | Same exemption the story set grants `AC6.5.2` and `AC6.5.3` |
| Focus **visibility** and **contrast** are the two weakest areas | The page has one explicit focus rule and no colour tokens; both need a human with a browser and a colour picker |
| `aria-current="page"` on an in-page view is semantically imprecise | Ruling 7 chose it and this checklist follows the ruling; `"true"` is the exact token for a view that is not a separate document. `AC6.1.4` requires only that the attribute be present. Named in `mockups.md` §9 item 8 |

---

## 14. Manual verification set (the `[V]` lines, gathered)

To be run once, in a browser, as a single manual exercise — not as a test, since
no test in this repository can decide any of them.

1. Tab through all three views; confirm the order in §11 and that focus is visible
   on every stop.
2. Activate each nav link with `Enter` and with a click; confirm focus lands where
   §11 says.
3. With a screen reader (VoiceOver, NVDA or TalkBack): confirm the loading region,
   the partial region and the error panel each announce once, politely or
   assertively as specified; confirm the series is announced as caption-then-list;
   confirm each breakdown cell announces its column header.
4. Confirm no announcement fires on page load other than the existing connection
   status.
5. Set `color-scheme` to dark; check `#b00020` text and border against the dark
   canvas.
6. Check the UA focus-ring contrast at 1.4.11's 3:1.
7. Zoom to 400 % at 1280 px; confirm no horizontal scrolling anywhere.
8. Resize to 320 px; confirm the wrap thresholds in `mockups.md` §8.1 and that
   nothing is truncated.
9. Enable `prefers-reduced-motion`; confirm nothing animates (nothing is specified
   to, so this should pass by construction).
10. Disconnect the network; confirm the analytics view issues only its two
    `/v2` requests and every failure renders as an error rather than an empty
    result.
