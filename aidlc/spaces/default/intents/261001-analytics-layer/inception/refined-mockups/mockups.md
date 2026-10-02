# Mockups — Analytics View (Refined)

> **Intent:** `261001-analytics-layer` · stage `refined-mockups` (inception) ·
> brownfield extension of an existing single-page shell.
>
> **Fidelity:** mid-to-high structural fidelity. Real copy, real numbers, real
> element and attribute names, real class names. ASCII rendering stands in for
> the page's inline `<style>`; no visual invention beyond what the shipped file
> already does.
>
> **Upstream:** `ideation/rough-mockups/wireframes.md`,
> `ideation/rough-mockups/user-flow.md`, `inception/user-stories/stories.md`
> (`US6.*`), `inception/requirements-analysis/requirements.md` (`FR6.*` plus
> its Revision 2 corrections), and the seven human rulings recorded in
> `refined-mockups-questions.md`.
>
> **Ground truth read before drawing:** `app/static/index.html` (193 lines),
> `app/static/app.js` (201 lines), `tests/test_page.py` (77 lines).

---

## 0. What the shipped page actually is

Every number and hook claim in this document was checked against the source, not
assumed. These are the facts the mockups are built on.

| Fact | Evidence |
|---|---|
| The page is a `position: fixed` connection button, then one `<main>` | `index.html:110–130` |
| `<main>` holds `h1`, `.lede`, the analyze `form`, `error-panel`, `result-panel`, a History `section`, and the `history-item` `<template>` | `index.html:130–189` |
| **No `header`, no `nav`, no `footer`** — zero occurrences of any of the three elements | `grep -cE "<(header\|nav\|footer)" index.html` → `0` |
| **Zero media queries** in the page | `grep -c "@media" index.html` → `0` |
| 16 **distinct** `data-testid` values in the markup (19 occurrences: `error-panel` appears 3×, `result-panel` 2×, because the `<style>` block also selects them) | `index.html` |
| `REQUIRED_TEST_IDS` pins **14** of those 16. The two unpinned are `history-item-text` and `history-item-meta` — both live inside the `<template>` and are reached by `app.js` at clone time | `tests/test_page.py:17–32` |
| The `<template data-testid="history-item">` lives **inside `<main>`**, as the last child before `</main>`, not in `</body>` at large | `index.html:183–188` (inside `<main>`, which opens at `:130` and closes at `:189`) |
| `:root` declares exactly two custom properties: `color-scheme` and `font-family`. There are no colour, spacing or type tokens to reuse | `index.html:8–11` |
| Seven class names exist: `.lede`, `.probabilities`, `.history-item`, `.history-text`, `.history-meta`, `.connection-indicator`, `.connection-dot` | `index.html` |
| `app.js:10` holds `const API = "/v1"`; the backend holds `v1_router = APIRouter(prefix=V1_PREFIX)` at `app/routes.py:134`. Two independent copies of the prefix | `app.js:10`, `app/routes.py:134` |
| All rendering uses `textContent` / `replaceChildren` / `document.createElement`. There is no `innerHTML`, no template-literal HTML, and no `insertAdjacentHTML` anywhere in the script | `app.js` |
| `LABEL_ORDER = ["positive", "negative", "neutral"]` is already fixed in the script | `app.js:9` |
| `tests/test_page.py:64–68` asserts `"intensity" not in markup.lower()` — the *whole served page*, including the `<style>` block and HTML comments, may not contain that substring | `tests/test_page.py` |

### 0.1 Corrections to the brief's own summary

Two numbers in the dispatch brief are wrong against the file, and both are
recorded here so a later reader does not inherit them:

- The brief says `REQUIRED_TEST_IDS` pins **12** of the 16 hooks. **It pins 14.** The
  12 figure is the brief's error, not subtraction the brief describes: the tuple has
  14 entries (`tests/test_page.py:17–32`), and the two hooks it does **not** pin are
  `history-item-text` and `history-item-meta`, both inside the `<template>`. Nothing
  in this stage changes the count.
- The brief says there is **one** fixed button plus `<main>`. Accurate. It does
  not mention that the `<template data-testid="history-item">` also lives **inside
  `<main>`** (`index.html:183–188`); this spec moves it (§2.4) and says why.

---

## 1. Corrections to the Ideation wireframes

The rough wireframes were drawn against an assumed page. Six of their decisions
are wrong, four because a human ruling overrode them and two because the shipped
code contradicts them. Every correction is stated here and again inline at the
point of the change, so a reader holding the wireframes open sees exactly what
moved.

| # | Wireframes said | This spec says | Closed by |
|---|---|---|---|
| C1 | `header` with `[ Analyze ] [ Analytics ]`, and a `footer` reading `running in dummy mode - all analytics computed locally` | A `header` **and** a real `nav` exist, with **three** links: Analyze, History, Analytics. The **footer is not carried forward** — see §1.1 | Ruling 1, ruling 7 |
| C2 | Summary figures read `Total analyses 128 · Mean confidence 0.71 · Mean intensity 0.28` | `Mean intensity` is **gone**. The summary region carries `Total analyses` and `Mean confidence` only | `FR2.3`, Requirements `Out of Scope`, `AC2.1.3` (see §1.2) |
| C3 | Breakdown shares drawn as `62%`, `30%`, `8%`, and the edge case showing `neutral 0%` / `negative 0%` | A share is a **fraction in `[0,1]`** (`FR2.7`). It is rendered as a percentage for display. A **`null`** share renders the explicit marker `no share` and is *never* `0%`. A share that is genuinely `0.0` still renders as a real percentage | Ruling 3, `FR2.7`, `AC6.2.5` (see §1.3) |
| C4 | A line-ish ASCII plot with axis ticks | An **SVG `<polyline>`**, drawn from the same values a text list carries | Ruling 4 (Q4 answer A), `FR6.6`, `NFR6` (see §1.4) |
| C5 | `[ Apply ]` only | The range control carries **Apply** *and* **`Show all time`**, because `AC6.3.4` requires a way back to the default | `AC6.3.4`, ruling 6 |
| C6 | `Apply` submits, and the empty state offers `[ Go to Analyze ]` as the recovery | Retained, but `Go to Analyze` is a real in-page link `href="#analyze"`, consistent with the nav's fragment links, not a scripted jump | Ruling 6 |

Two more corrections are *not* rulings — they are defects in the wireframes that
this stage found against the shipped code, and they are stated for the same
honesty reason:

| # | Wireframes said | This spec says | Evidence |
|---|---|---|---|
| C7 | "Raw error codes are never shown to the user; the message names what went wrong and what to do." | **The wireframes were wrong about the shipped page.** `readErrorMessage` composes `` `${payload.code}: ${payload.message}` `` (`app.js:33–34`), so the existing Analyze flow already shows a machine code to the user. The analytics path **diverges from that shipped behaviour**: it shows a status-derived lead-in plus `payload.message`, and never the code. The code stays in the server log (`US8.8.1`) | `app.js:30–40`, `app.js:42–45` |
| C8 | Label breakdown order `positive, neutral, negative` | Order is **`positive, negative, neutral`**, because `LABEL_ORDER` in the shipped script already fixes it and the same labels must not appear in two orders on one page | `app.js:9` |
| C9 | Breakdown carries a `####` bar glyph per label | The breakdown is a plain table of `Count` and `Share`. The bar is dropped (§1.5) | §1.5 |

### 1.1 C1 — the footer is dropped, and that is a decision, not an oversight

The wireframes drew a `footer` reading `running in dummy mode - all analytics
computed locally`. No ruling asked for a footer, no `FR6` requirement mentions
one, and the state it would have carried **already has a home**: the connection
indicator reads `Offline engine (OpenRouter not connected)` or
`OpenRouter: connected`, in words, and is announced through a `role="status"`
region (`index.html:119–127`, `app.js:144–153`). A footer would therefore be a
second, less accurate restatement of a live element.

The footer is consequently **not specified in this stage**. It is listed in §8
as an open point, because a reviewer reading the wireframes will look for it and
should be told that its removal was deliberate rather than forgotten.

### 1.2 C2 — `Mean intensity` is gone, and the shipped test enforces it

`FR2.3` enumerates the summary response's fields exactly: `total`, `counts`,
`shares`, `mean_confidence`, `mean_confidence_row_count`, `series`. There is no
intensity field. The requirements' `Out of Scope` says so in as many words: the
column "is never written, never read, and null on every row the application has
produced". The persona file records why it was dangerous — `PN2`: "`AVG(intensity)`
returns `null` forever; a UI would show a confident empty number". `AC2.1.3`
pins the surviving mean over `confidence`.

**The column does not appear in any mockup in this document.** And there is a
hard mechanical constraint a later stage must honour:
`tests/test_page.py:64` asserts `"intensity" not in markup.lower()` against the
**whole served page**. So the analytics markup must not use the word in an `id`,
a `class`, a `data-testid`, an `aria-label`, an HTML comment, or a CSS comment
either. Naming this here because it is invisible in the requirements text and
would otherwise be discovered as a red test.

### 1.3 C3 — the no-share marker, and why `0.00%` still appears in one state

Ruling 3 has two halves and the wireframes conflated them. Separated:

- A share is a fraction rounded to 4 dp (`FR2.7`, `AC2.1.2`). The view displays
  it as a percentage. **Two decimal places** — `0.01 %` is exactly `0.0001` of
  the fraction, so 2 dp loses nothing the API stated. One decimal place would
  discard a digit of precision the API deliberately rounded to, which is the
  project's refuse-never-fabricate stance applied to formatting.
- A share is `null` when `total` is 0 (`FR2.7`, `AC2.1.4`). `null` renders the
  marker **`no share`**. It never renders as `0%`, `0.00%`, `—`, or an empty
  cell, because a zero denominator has no answer and the marker is the honest
  way to say so.
- **A share that is genuinely `0.0` is not `null`.** With `total = 128` and
  `counts.neutral = 0`, the API returns `0.0000` and the view renders
  **`0.00%`**. The wireframes' edge-state `0%` was *correct* for that state and
  stays correct here. Only the empty state changes.

The consequence the reader should take away: **§4 (empty) shows `no share`;
§7.1 (edge) shows `0.00 %` for the same label in the same column.** That contrast
is deliberate and is the clearest single illustration of `FR2.7` in the document.

Two derived facts worth stating: the displayed percentages are each rounded
independently from a 4-dp fraction, so in the populated state they read
`51.56 % + 27.34 % + 21.09 % = 99.99 %`. That is arithmetic rounding, not a
defect — and note it lands *below* 100, which is the more convincing direction to
see it in — and it is why the breakdown carries **no** "total share" row that
would have to reconcile to 100. And because `mean_confidence_row_count` always
equals `total` (`FR2.8` as corrected in Requirements Revision 2), it is **not
rendered as a third summary figure** — it would restate `Total analyses` and
imply a denominator nobody can vary.

### 1.4 C4 — the series is an SVG polyline, and its text twin is the real data

Ruling 4 chose option A. The polyline is a native `<svg>` with a `<polyline>`,
one point per series entry, drawn from the `total` of each day — the same values
the text list carries, in the same order, so the two cannot disagree. No chart
library exists in the project and none may be added (`FR6.6`, `C-6`); the
runtime dependency cap of two (`NFR6`, `C-6`) forbids it and the page tests
would not be able to observe it.

Three points about the drawing that the ASCII in §3 makes concrete:

- **Which quantity is plotted.** One polyline was ruled, so one series is
  plotted: analyses per day. Per-day `counts`, `shares` and `mean_confidence`
  are in the response (`AC2.3.2`) and are **deliberately not rendered per day**
  (§8, open point 3). The text list therefore carries only `date` and `total` —
  an **exact text equivalent of the plotted line**, not a full mirror of the
  payload. A later stage must not read the list as "everything the series
  entry holds": `AC2.3.2` has the **API** return more per day
  (`date`, `total`, `counts`, `shares`, `mean_confidence`,
  `mean_confidence_row_count`), and the view renders a subset of that on
  purpose.
- **A one-day series cannot be a polyline.** `<polyline>` needs two points. The
  edge state (§7) renders a single `<circle>` instead; two or more days render
  the polyline.
- **The graphic is not the data.** It carries `role="img"` with
  `aria-labelledby` pointing at a visible one-line caption, which flattens the
  subtree so the SVG's own axis text is not announced separately. The complete
  data is the `<ol>` immediately below it (`AC6.4.5b`).

### 1.5 C9 — the breakdown bar is dropped

The wireframes drew `####################################` beside each label. The
breakdown is a real `<table>` whose `Share` cell already carries the exact value,
so a bar would encode the same number a second time, in a visual channel with no
text equivalent, on a page that has one ruled graphic already. Nielsen's
aesthetic-and-minimalist-design heuristic applies: every element must earn its
place.

Reinstatement is a one-column change if the human wants it (§8, open point 4).

---

## 2. The shell: header, nav, three views

Rulings 6 and 7 turn a page of always-visible sections into three views switched
by a nav. This is the structure every screen below sits inside.

### 2.1 Region structure

```
<body>
├── <header>                                  <- new; role="banner"
│   ├── <h1>Sentiment analysis</h1>           <- moved out of <main> (ruling 7)
│   ├── <nav aria-label="Views">              <- new; role="navigation"
│   │   ├── <a href="#analyze"   aria-current="page">Analyze</a>
│   │   ├── <a href="#history">                 History</a>
│   │   └── <a href="#analytics">              Analytics</a>
│   └── <button data-testid="connection-status">   <- moved in; position:fixed dropped
└── <main>                                    <- unchanged element
    ├── <p class="lede">                      <- moved into the Analyze view
    ├── <section data-testid="error-panel" role="alert" hidden>   <- moved above the views
    ├── <section id="analyze-view"   ...>     <- new wrapper
    ├── <section id="history-view"   ... hidden>   <- new wrapper
    └── <section id="analytics-view" ... hidden>   <- new
<template data-testid="history-item">          <- moved to end of <body>
```

### 2.2 Shell mockup — Analyze view active (the page's default state)

```
+----------------------------------------------------------------------+
| Sentiment analysis                                        <- h1       |
| [ Analyze ]  [ History ]  [ Analytics ]                     <- nav     |
| (o) OpenRouter: checking...                        <- connection     |
+----------------------------------------------------------------------+
|                                                                      |
|  Analyze                                          <- h2 (new)        |
|                                                                      |
|  Submit a short piece of text to get a typed label, its confidence  |
|  and the per-label probabilities. Each result shows which engine     |
|  produced it. History is stored locally.             <- .lede        |
|                                                                      |
|  Text to analyse                                                    |
|  +----------------------------------------------------------+         |
|  | e.g. I love how this turned out                            |         |
|  +----------------------------------------------------------+         |
|  [ Analyse ]                                                       |
|                                                                      |
+----------------------------------------------------------------------+
```

Only two things differ from the shipped page above the fold: the `h1` and the
new nav are now in a `header`, and the connection indicator is in flow instead of
pinned over the top-left corner. The Analyze view's own content is unchanged.

### 2.3 Shell mockup — History view active

```
+----------------------------------------------------------------------+
| Sentiment analysis                                                    |
| [ Analyze ]  [ History *]  [ Analytics ]                              |
| (o) OpenRouter: connected                                             |
+----------------------------------------------------------------------+
|                                                                      |
|  History                                <- h2, already exists as       |
|                                            #history-heading            |
|  No analyses yet.                     <- data-testid="history-empty"  |
|                                                                      |
+----------------------------------------------------------------------+
```

The existing History `<section aria-labelledby="history-heading">` **becomes**
`#history-view`. Its `h2` is not duplicated: `aria-labelledby="history-heading"`
points at the heading that is already there, so the view is named by its own
content and no second `History` heading enters the document.

### 2.4 Two placement decisions worth stating

- **`error-panel` moves above the three views**, staying a direct child of
  `<main>`. It is app-wide (ruling 2), so it cannot live inside any one view —
  a failure raised from the Analytics view would otherwise be invisible while the
  user is on Analyze. Placing it immediately after the `header` keeps it above the
  fold on every view. `tests/test_page.py` asserts only that
  `data-testid="error-panel"` is present, so its position is free.
- **The `<template>` moves out of `<main>`** to the end of `<body>`. It is a
  render source, not view content, and `<template>` content is never displayed
  regardless of an ancestor's `hidden`. Keeping it outside any view stops a later
  reader assuming it belongs to one. Nothing tests its position.
- **The panel is app-wide in *position*, not in *persistence*.** Sitting above
  the three views (previous bullet) is what makes it visible from all three; it
  does not mean a message outlives the view that raised it. Every view activation
  calls `clearError()` first, so the panel reports only the active view's most
  recent outcome — an analytics `500` is gone once the user switches to Analyze
  or History, and an Analyze error is gone once they switch away. The full rule
  is `interaction-spec.md` §13.4. Stated here because "one error surface app-wide"
  (ruling 2) could otherwise be read as "one error persists app-wide".

---

## 3. Screen A — Analytics view, populated

Range in effect: **all time** (both inputs empty). Data: the fixture in §3.0.

### 3.0 The fixture every number below comes from

Declared so that every figure in this document is checkable rather than decorative.

**`GET /v2/analytics/summary` (no bounds)**

| Field | Value |
|---|---|
| `total` | `128` |
| `counts` | `positive: 66`, `negative: 35`, `neutral: 27` |
| `shares` | `positive: 0.5156`, `negative: 0.2734`, `neutral: 0.2109` |
| `mean_confidence` | `0.7125` |
| `mean_confidence_row_count` | `128` |
| `series` | 30 entries, `2026-09-01` to `2026-09-30`, ascending, five zero-filled internal gaps (`02, 07, 13, 19, 25`), peak `11` on `2026-09-16` |

Per-day `total` values, which sum to `128` exactly:

```
day  01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30
     01 00 07 02 06 08 00 02 01 09 04 03 00 02 07 11 02 04 00 01 03 08 07 04 00 02 09 10 08 07
```

**`GET /v2/analytics/terms` (no bounds)** — top 10 per list, `limit` not sent, so
the server's default of 10 (`FR3.3`) applies. `neutral`-labelled rows contribute
to neither list (`FR3.6`).

```
positive: delivery 12, invoice 10, thanks 7, excellent 6, quick 4, smooth 4,
          clear 3, support 3, bright 2, clean 2
negative: broken 9, charge 7, refund 5, late 4, slow 4,
          delay 3, error 3, missing 3, noisy 2, wrong 2
```

Ties are broken alphabetically (`FR3.5`): `quick` before `smooth`, `clear`
before `support`, `bright` before `clean`, `late` before `slow`, `delay` before
`error` before `missing`, `noisy` before `wrong`. The fixture is shaped so the
tie-break is visible in the rendered list.

### 3.1 The screen

```
+----------------------------------------------------------------------+
| Sentiment analysis                                                    |
| [ Analyze ]  [ History ]  [ Analytics *]                              |
| (o) OpenRouter: connected                                             |
+----------------------------------------------------------------------+
|                                                                      |
|  Analytics                                         <- h2              |
|                                                                      |
|  +-----------------------------------------------------+            |
|  | From        [            ]   To        [            ]|  <- 2 date  |
|  | [ Apply ] [ Show all time ]                          |  <- inputs  |
|  | Showing all stored analyses (all time).              |  <- range    |
|  +-----------------------------------------------------+    state     |
|                                                                      |
|  Summary                                          <- h3              |
|  Total analyses          128                                         |
|  Mean confidence          0.7125                                      |
|                                                                      |
|  Per-day series                                    <- h3              |
|  Analyses per day, 2026-09-01 to 2026-09-30. 30 days in range,        |
|  including 5 with no analyses. Highest 11 on 2026-09-16.             |
|   11 |                / \                        /\                   |
|    8 |       /\     /     \      /\/\/\/    \_   /  \                  |
|    4 |   /\ /  \   /       \/\/            /\  \  /    \ /\            |
|    0 +------------------------------------------------------          |
|      2026-09-01                                    2026-09-30         |
|                                                                      |
|    1. 2026-09-01 - 1 analysis                                       |
|    2. 2026-09-02 - 0 analyses                          <- zero-fill  |
|    3. 2026-09-03 - 7 analyses                                       |
|       ... 24 more entries, including the 11 on 2026-09-16 ...        |
|   30. 2026-09-30 - 7 analyses                                       |
|                                                                      |
|  Label breakdown                                 <- h3              |
|  Counts and shares by label for the selected range.                  |
|  +-----------------+-----------+--------------+                      |
|  | Label           | Count     | Share        |                      |
|  +-----------------+-----------+--------------+                      |
|  | positive        | 66        | 51.56 %      |                      |
|  | negative        | 35        | 27.34 %      |                      |
|  | neutral         | 27        | 21.09 %      |                      |
|  +-----------------+-----------+--------------+                      |
|                                                                      |
|  Top terms                                         <- h3              |
|  Most frequent terms, up to 10 per list, for the selected range.     |
|  +-----------------------+  +-----------------------+               |
|  | Positive texts  <- h4 |  | Negative texts  <- h4 |               |
|  | 1. delivery      12    |  | 1. broken         9   |               |
|  | 2. invoice       10    |  | 2. charge         7   |               |
|  | 3. thanks         7    |  | 3. refund         5   |               |
|  | 4. excellent      6    |  | 4. late           4   |               |
|  | 5. quick          4    |  | 5. slow           4   |               |
|  | 6. smooth         4    |  | 6. delay          3   |               |
|  | 7. clear          3    |  | 7. error          3   |               |
|  | 8. support        3    |  | 8. missing        3   |               |
|  | 9. bright         2    |  | 9. noisy          2   |               |
|  | 10. clean         2    |  | 10. wrong         2   |               |
|  +-----------------------+  +-----------------------+               |
+----------------------------------------------------------------------+
```

### 3.2 The polyline, drawn from those values

Not decorative geometry — the exact `points` attribute the script will set, from
the §3.0 series, in a `viewBox="0 0 640 160"` with the x-axis at `y=120`.

**The scale, stated once and used by both axes' points below.** The domain is
`[0, max(total)]`, where `max(total)` is the largest value **actually plotted**
(`11` in §3.0) — the same ceiling §8 states and the same ceiling §7.1's one-day
case uses (`1`). The linear map onto `[120, 0]` is therefore

```
x = 640 * i / (n - 1)          for i = 0 .. n-1
y = 120 * (1 - total[i] / max(total))
```

so `y(0) = 120` (the baseline) and `y(max(total)) = 0` (the top rule). There is no
"rounded up to a nice number" domain: the ceiling is the plotted maximum itself,
which is why the top `<text>` below reads `11` and not `12`. An earlier draft of
this document printed points computed with `y = 120 − 10·v`, a map whose domain
maximum is `12`; that encoded a ceiling the §3.0 fixture never reaches and
disagreed with §8, so the points were recomputed from the formula above.

```html
<svg class="series-chart" role="img" aria-labelledby="analytics-series-caption"
     viewBox="0 0 640 160" data-testid="analytics-series-chart">
  <text x="0" y="12">11</text>
  <polyline data-testid="analytics-series-line" fill="none" stroke="currentColor"
            stroke-width="2" vector-effect="non-scaling-stroke"
            points="0,109.1 22.1,120 44.1,43.6 66.2,98.2 88.3,54.5 110.3,32.7
                    132.4,120 154.5,98.2 176.6,109.1 198.6,21.8 220.7,76.4
                    242.8,87.3 264.8,120 286.9,98.2 309,43.6 331,0 353.1,98.2
                    375.2,76.4 397.2,120 419.3,109.1 441.4,87.3 463.4,32.7
                    485.5,43.6 507.6,76.4 529.7,120 551.7,98.2 573.8,21.8
                    595.9,10.9 617.9,32.7 640,43.6"/>
  <text x="0" y="150">2026-09-01</text>
  <text x="640" y="150" text-anchor="end">2026-09-30</text>
</svg>
```

Three details that are load-bearing rather than stylistic:

- **Thirty points, thirty `<li>`s.** The polyline is derived from the same array
  that fills the list, in one pass. There is no second computation to drift.
- **`vector-effect="non-scaling-stroke"`** keeps the stroke at 2 px when the SVG
  is scaled down to a 320 px viewport, which `stroke-width` in user units would
  otherwise halve — WCAG 2.1 SC 1.4.11 (Non-text Contrast) applied to a graphical
  object.
- **`role="img"` flattens the subtree.** The three `<text>` axis labels are for
  sighted users; because the `<svg>` is a single `img` node named by the visible
  caption, a screen reader announces the caption and the list, not the axis
  numbers twice.

### 3.3 Regions in the populated state

| # | Region | Visible | Notes |
|---|---|---|---|
| 1 | Date-range control | yes | both inputs empty; `Show all time` disabled |
| 2 | Range-state line | yes | `Showing all stored analyses (all time).` |
| 3 | Loading region | no | `hidden` |
| 4 | Empty region | no | `hidden` — `total` is 128 |
| 5 | Partial-failure status | no | `hidden` |
| 6 | Summary figures | yes | 2 figures, not 3 |
| 7 | Per-day series | yes | polyline + caption + 30-item list |
| 8 | Label breakdown | yes | 3 rows, `LABEL_ORDER` |
| 9 | Positive terms | yes | 10 items |
| 10 | Negative terms | yes | 10 items |
| 11 | Error panel | no | `hidden` — nothing failed |

### 3.4 The range-state line earns its place

It is the mechanism that makes ruling 5 real. Both inputs start empty, so the
user must be able to tell what "empty" actually means — otherwise an empty input
is indistinguishable from a forgotten one. The line always states the range in
effect:

| Inputs | Line reads |
|---|---|
| both empty | `Showing all stored analyses (all time).` |
| `from` only | `Showing 2026-09-01 onwards, with no end date.` |
| `to` only | `Showing everything up to 2026-09-30, with no start date.` |
| both set | `Showing 2026-09-01 to 2026-09-30.` |

It closes a real hazard: `<input type="date">` reports `""` for a half-typed date,
so a partially typed end date would otherwise widen the range with no word to the
user. The line makes the resolved bound explicit every time, which is what
`AC6.3.1`'s "shows an unbounded state rather than a range someone invented" asks
for.

### 3.5 Where the "all time" wording actually lives

Ruling 5 asked for both inputs empty with an "all time" placeholder; Q9 then
ruled on how to deliver the wording. The first half is implemented literally;
**the placeholder mechanism was impossible as first written, and this is worth
saying plainly: browsers do not render `placeholder` on `<input type="date">`.**
The attribute is either ignored or replaced by the browser's own locale format
hint (`mm/dd/yyyy`, `dd/mm/yyyy`), so a `placeholder="all time"` would be
invisible — a promise the page does not keep.

The **accepted substitute** is therefore **visible text beside the control**: the
"all time" wording is carried by the range-state line, which appears in every
state and is the thing a sighted user reads. The inputs stay genuinely empty and
remain `type="date"` (Q9 keeps the native picker and keyboard behaviour). No
`placeholder` attribute is set on either input. If a later stage sets one anyway
for the DOM, it must not be the only carrier of the wording — this paragraph is
the guard. Flagged in §8 as open point 1.

---

## 4. Screen B — Analytics view, empty

Range: `from=2026-10-01`, `to=2026-10-31`. Response: `total 0`, all `counts` 0,
all `shares` **`null`**, `mean_confidence` `null`, **`series: []`**, and both term
lists `[]`.

```
+----------------------------------------------------------------------+
| Sentiment analysis                                                    |
| [ Analyze ]  [ History ]  [ Analytics *]                              |
+----------------------------------------------------------------------+
|  Analytics                                                           |
|                                                                      |
|  From  [ 10/01/2026 ]   To  [ 10/31/2026 ]                           |
|  [ Apply ] [ Show all time ]                                          |
|  Showing 2026-10-01 to 2026-10-31.                                    |
|                                                                      |
|  +-----------------------------------------------------+            |
|  | Nothing to show                                     |            |
|  |                                                     |            |
|  | No analyses fall inside this date range. Analytics   |            |
|  | counts stored rows, and there are none in October    |            |
|  | 2026.                                             |            |
|  |                                                     |            |
|  | [ Go to Analyze ]                                   |            |
|  +-----------------------------------------------------+            |
+----------------------------------------------------------------------+
```

What is **not** on this screen, and why:

- **No breakdown table.** With every share `null`, the table would render three
  rows reading `0` and `no share` — a plausible-looking table describing an
  absence. `NFR4` and `AC8.4.2` forbid a failure or an absence wearing an empty
  success's clothes; showing the empty region instead is the same refusal applied
  to a legitimately empty answer.
- **No polyline, no `<ol>`.** The series is `[]`. There is nothing to draw, and a
  chart frame around nothing is the "silent blank" `FR6.7` rules out.
- **No `0%`.** The wireframes' edge discussion of a zero-share label does not
  apply here. `total` is 0, so every share is `null` and every share would be
  `no share`. `AC2.1.4` pins `null`, not `0.0`.

The wireframes' `( no icon needed )` note stands and is honoured: there is no
illustration, because there is no asset pipeline to add one and an emoji or glyph
would be decoration that earns nothing. The heading, the explanation and the
action are the whole empty state.

---

## 5. Screen C — Analytics view, loading

```
+----------------------------------------------------------------------+
| Sentiment analysis                                                    |
| [ Analyze ]  [ History ]  [ Analytics *]                              |
+----------------------------------------------------------------------+
|  Analytics                                                           |
|                                                                      |
|  From  [ 10/01/2026 ]   To  [ 10/31/2026 ]                           |
|  [ Apply (disabled) ] [ Show all time ]                               |
|  Showing 2026-10-01 to 2026-10-31.                                    |
|                                                                      |
|  Loading analytics for this range...   <- role="status", announces    |
|                                                                      |
|  Summary                                                            |
|  Total analyses            -                                          |
|  Mean confidence          -                                           |
|                                                                      |
|  Per-day series                                                       |
|  #################################################################### |
|  ####################################################################  |
|                                                                      |
|  Label breakdown                                                      |
|  #####################   ######   #########                           |
|                                                                      |
|  Top terms                                                            |
|  ##################     ##################                           |
+----------------------------------------------------------------------+
```

- `analytics-loading` is a **distinct region** with `role="status"` and
  `aria-live="polite"`, so `AC6.5.1` (a loading state is shown *and* announced)
  and `AC6.5.5` (loading, empty and error are each a distinct assertable region)
  are satisfied by different elements.
- **Skeleton blocks are drawn with `#` in this document and implemented as CSS
  on the shipped plain-class vocabulary** — a `.skeleton` class with a muted
  `currentColor` background. They are marked
  `aria-hidden="true"`, because a screen reader must hear the status line, not
  eleven meaningless rectangles. They are not the loading state's announcement;
  the `role="status"` line is.
- **`Apply` is disabled** while in flight, mirroring the shipped
  `submitButton.disabled = true` in `app.js:127–134`. That is `AC6.3.6`'s
  "disabled or active state is asserted as part of `US6.5`'s markup contract".
- No prior range's numbers are left on screen. Skeletons replace them, because a
  stale table beside a spinner is `AC6.5.3`'s "two sections silently disagreeing
  about which range they describe".

---

## 6. Screen D — Analytics view, error

Range: `from=2026-09-30`, `to=2026-09-01` — valid dates, inverted order.
Response: `422`, envelope `{code: "VALIDATION_FAILED", message: …}` with the
message text naming **both** parameters (Requirements Revision 2, ruled at
`user-stories` Q11 — the envelope has no `field` member, so the message is the
only place two fields can be named).

```
+----------------------------------------------------------------------+
| Sentiment analysis                                                    |
| [ Analyze ]  [ History ]  [ Analytics *]                              |
+----------------------------------------------------------------------+
|  Analytics                                                           |
|                                                                      |
|  !  The date range was refused.                                      |
|     query.from must not be later than query.to.                      |
|     ^-- section[data-testid="error-panel"], role="alert"             |
|        the ONE error surface for the whole page                      |
|                                                                      |
|  From  [ 09/30/2026 ]   To  [ 09/01/2026 ]                           |
|  [ Apply ] [ Show all time ]                                          |
|  Showing 2026-09-01 to 2026-09-30.   <- last known good range        |
+----------------------------------------------------------------------+
```

- **One error surface.** Ruling 2: the analytics view uses the existing
  `section[data-testid="error-panel"]` with its existing `role="alert"`. There is
  no second panel, no per-section alert, and no analytics-specific error element.
  The panel sits above the views so it is visible from all three.
- **No machine code on screen.** `readErrorMessage` would have produced
  `VALIDATION_FAILED: …`; the analytics path does not. It renders a
  **status-derived lead-in** plus `payload.message`. This corrects wireframe
  claim C7, and it is what makes `AC6.4.2` decidable: a `422` and a `500` carry
  different lead-ins, so they are distinguishable on screen and not only in the
  response. **The divergence is from shipped behaviour, not from the wireframes
  alone:** the existing Analyze flow (`app.js:30–40`) already surfaces
  `${payload.code}: ${payload.message}`, so "raw codes are never shown" was never
  true of the page this view is being added to. The analytics view chooses the
  quieter rendering deliberately; it does not inherit the shipped one, and it does
  not silently "fix" the Analyze flow either.
- The literal envelope message text is fixed at Contract Design; this mockup
  shows an illustrative rendering. The view never rewrites the message, only
  prefixes it.
- The **range-state line keeps the last range the API accepted**, not the range
  the user just typed and which was refused. Showing the refused pair there would
  claim a population that does not exist.

---

## 7. Screen E — Analytics view, partial failure

Range `from=2026-09-01`, `to=2026-09-30`. `/v2/analytics/summary` answers `200`;
`/v2/analytics/terms` answers `500` carrying the storage-failure machine code.

```
+----------------------------------------------------------------------+
| Sentiment analysis                                                    |
| [ Analyze ]  [ History ]  [ Analytics *]                              |
+----------------------------------------------------------------------+
|  Analytics                                                           |
|                                                                      |
|  Showing 2 of 3 sections for this range. The term lists could not be |
|  read.          <- analytics-partial, role="status" (polite)          |
|                                                                      |
|  Summary                                                            |
|  Total analyses          128                                         |
|  Mean confidence          0.7125                                      |
|                                                                      |
|  Per-day series                                    <- populated       |
|  ( polyline + 30-item list, exactly as in Screen A )                  |
|                                                                      |
|  Label breakdown                                 <- populated         |
|  positive 66  51.56 % / negative 35  27.34 % / neutral 27  21.09 %  |
|                                                                      |
|  Top terms                                         <- h3              |
|  +-----------------------+  +-----------------------+               |
|  | Positive texts        |  | Negative texts        |               |
|  | not loaded            |  | not loaded            |               |
|  +-----------------------+  +-----------------------+               |
+----------------------------------------------------------------------+
```

This state required a judgement call, and the reasoning is on the record because
it sits between two requirements that pull in opposite directions.

- `AC6.5.3` requires the successful section to show and the failed one to be
  marked, and requires the partial state to be a **distinct region**
  (`AC6.5.5`).
- Ruling 2 requires **one error surface app-wide** and forbids a second error
  panel.

Resolution: the error still renders in the **one** `error-panel`; what the
analytics view adds is a **`role="status"` partial region**, which is a status
announcement and not an alert. It is a distinct element with its own
`data-testid="analytics-partial"`, so `AC6.5.5` is satisfied, and it is not a
second error panel, because it is polite rather than assertive and it states
*coverage* ("showing 2 of 3 sections") rather than a failure message.

**The failed half is marked `not loaded` in place, whichever half it is.** The
rule is symmetric and is the same one the term lists already follow:

- **Terms fail** (this screen): the two term `<ol>`s stay hidden and each list
  position reads `not loaded`; the summary, series and breakdown render from the
  successful response.
- **Summary fails** (the mirror, `interaction-spec.md` §13.1 step 2′): the
  summary `<dl>`, the series (caption + `<svg>` + `<ol>`) and the breakdown
  `<table>` all stay hidden, and each of those three regions keeps its heading and
  reads `not loaded` in its data position
  (`analytics-total-not-loaded`, `analytics-series-not-loaded`,
  `analytics-breakdown-not-loaded`); the two term lists render.

A region with no in-place reason would be exactly the "silent blank" `FR6.7` and
`NFR4` rule out, and `AC6.5.3`'s "marked" requirement is about the *failed
region's own content*, not only about the polite coverage line above it. The
marker is a state label, not a second error message: the cause still lives in the
one `error-panel`.

The mirror state reads, in the same shape as this screen, as:

```
+----------------------------------------------------------------------+
| Sentiment analysis                                                    |
| [ Analyze ]  [ History ]  [ Analytics *]                              |
+----------------------------------------------------------------------+
|  Analytics                                                           |
|                                                                      |
|  Showing 1 of 3 sections for this range. The summary figures, the    |
|  per-day series and the label breakdown could not be read.           |
|                     <- analytics-partial, role="status" (polite)      |
|                                                                      |
|  Summary                                                             |
|  Total analyses           not loaded                                 |
|  Mean confidence          not loaded                                 |
|                                                                      |
|  Per-day series                                                        |
|  not loaded                                                          |
|                                                                      |
|  Label breakdown                                                       |
|  not loaded                                                          |
|                                                                      |
|  Top terms                                           <- populated      |
|  +-----------------------+  +-----------------------+               |
|  | Positive texts        |  | Negative texts        |               |
|  | 1. delivery      12    |  | 1. broken         9   |               |
|  | ...                    |  | ...                    |               |
|  +-----------------------+  +-----------------------+               |
+----------------------------------------------------------------------+
```

(Shown as a second, compact mockup because the reverse direction is the one the
review found unspecified; it is a rendering of the same partial-failure state
with the two fetches' roles exchanged.)

This reading is listed in §8 as open point 2, because it is the one place where
a reviewer could reasonably read `analytics-partial` as a second error surface.

### 7.1 The edge case the wireframes drew — and what changed in it

The wireframes' Screen 5 covered "a single day, a single analysis, all-positive
data, empty term lists, and zero-share labels (shown as `0%` plus a visible `0%`
text label)". Range `from=2026-09-01`, `to=2026-09-01`, one stored row.

```
+----------------------------------------------------------------------+
| Sentiment analysis                                                    |
| [ Analyze ]  [ History ]  [ Analytics *]                              |
+----------------------------------------------------------------------+
|  Analytics                                                           |
|                                                                      |
|  From  [ 09/01/2026 ]   To  [ 09/01/2026 ]                            |
|  [ Apply ] [ Show all time ]                                          |
|  Showing 2026-09-01 to 2026-09-01.                                    |
|                                                                      |
|  Summary                                                            |
|  Total analyses          1                                            |
|  Mean confidence          0.9400                                      |
|                                                                      |
|  Per-day series                                    <- h3              |
|  Analyses per day, 2026-09-01 to 2026-09-01. 1 day in range.         |
|  Highest 1 on 2026-09-01.                                             |
|    1 |        o                    <- a <circle>, NOT a <polyline>   |
|    0 +---------------                                                  |
|      2026-09-01                                                       |
|                                                                      |
|    1. 2026-09-01 - 1 analysis                                         |
|                                                                      |
|  Label breakdown                                 <- h3              |
|  +-----------------+-----------+--------------+                      |
|  | Label           | Count     | Share        |                      |
|  +-----------------+-----------+--------------+                      |
|  | positive        | 1         | 100.00 %     |                      |
|  | negative        | 0         | 0.00 %       |  <- a REAL zero    |
|  | neutral         | 0         | 0.00 %       |  <- not "no share" |
|  +-----------------+-----------+--------------+                      |
|                                                                      |
|  Top terms                                                            |
|  +-----------------------+  +-----------------------+               |
|  | Positive texts        |  | Negative texts        |               |
|  | 1. excellent      1    |  | No negative terms in   |               |
|  +-----------------------+  | this date range.       |               |
|                              +-----------------------+               |
+----------------------------------------------------------------------+
```

**The single most important line in this document is `0.00 %` above.** Here
`total = 1`, so the denominator is real, so the API answered `0.0000`, so the view
renders a percentage. Screen B's `no share` and this screen's `0.00 %` are the
same cell in the same column answering two different questions. Confusing them in
either direction is the failure `AC6.2.5` exists to prevent.

Three other edge properties are visible here and are specified because they can
fail:

- **A single-day series is a `<circle>`.** `<polyline points="…">` with one point
  draws nothing at all, which would render the edge state as a blank chart.
- **`from` equal to `to` is one day, not zero and not two** (`AC2.2.5`). The
  caption says `1 day in range`.
- **An empty term list gets a sentence**, not `( none )` and not a bare empty
  `<ol>`. The wireframes' `( none )` was a placeholder; a full sentence is what
  the empty-state guidance asks for and what a screen reader reads usefully.

---

## 8. Narrow layout, and the breakpoint

### 8.1 The breakpoint, stated precisely

**There is no `@media` query, and that is the specification — not an omission.**
The shipped page contains **zero media queries** (`grep -c "@media"
app/static/index.html` → `0`), and **no media query was added**. Adding one would
make the analytics view the only breakpoint-aware thing in the file, against a
layout that is already a single fluid column capped at `max-width: 46rem`
(`index.html:12–17`). Content dictates breakpoints, not device names, and this
content has no device-shaped requirement. The narrow layout is therefore
**content-driven**: it is produced by two wrap thresholds implemented with
`auto-fit` grids and `flex-wrap`, which need no query:

| Region | Rule | Wraps below |
|---|---|---|
| Date-range fields | `grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr))` | two fields stop fitting at ≈ **392 px** (24.5 rem) |
| Term lists | `grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr))` | the two lists stop fitting at ≈ **520 px** (32.5 rem) |
| Summary figures | `grid-template-columns: max-content 1fr` | never splits a label from its value |
| Polyline | `width: 100%; height: auto` with a `viewBox` | scales continuously; stroke held at 2 px by `vector-effect` |
| Breakdown table | `width: 100%`, three columns | fits at 320 px with no horizontal scroll |

**The narrow layout is therefore the default behaviour below roughly 520 px, and
the mockups in §3–§7 are the wide layout.** A reviewer who wants a named media
query has one: `@media (max-width: 30rem)` on the analytics view for vertical
rhythm only. It is listed in §9 as open point 5 rather than specified, because it
is not needed and the knowledge guidance's 768/1024 breakpoints would invent
structure this page does not have.

### 8.2 Narrow mockup — Analytics, populated, at 320 px

```
+--------------------------------+
| Sentiment analysis             |
| [ Analyze ] [ History ]        |
| [ Analytics * ]                |
| (o) OpenRouter: connected      |
+--------------------------------+
| Analytics                      |
|                                |
| From                           |
| [ 09/01/2026 ]                 |   <- fields stack below ~392px
| To                             |
| [ 09/30/2026 ]                 |
| [ Apply ]                      |
| [ Show all time ]              |   <- actions wrap to own lines
| Showing 2026-09-01 to          |
| 2026-09-30.                    |
|                                |
| Summary                        |
| Total analyses                 |   <- label and value stay
| 128                            |      on one row
| Mean confidence                |
| 0.7125                         |
|                                |
| Per-day series                 |
| Analyses per day,              |
| 2026-09-01 to 2026-09-30.      |
| 30 days in range, including    |
| 5 with no analyses. Highest    |
| 11 on 2026-09-16.              |
|  ##########################    |   <- polyline scales to
|  ##########################       ~300px wide, ~75px tall,
|  #######   ######   #######      stroke still 2px
| 2026-09-01        2026-09-30    |
|                                |
|  1. 2026-09-01 - 1 analysis    |   <- each list item wraps,
|  2. 2026-09-02 - 0 analyses       never truncated
|  ...                           |
|                                |
| Label breakdown                |
| +------------+----+-----------+ |   <- no horizontal scroll
| | Label      |Count| Share     |      at 320px
| +------------+----+-----------+
| | positive   | 66 | 51.56 %   |
| | negative   | 35 | 27.34 %   |
| | neutral    | 27 | 21.09 %   |
| +------------+----+-----------+
|                                |
| Top terms                      |   <- lists stack below ~520px
| Positive texts                 |
|  1. delivery      12           |
|  ...                           |
| Negative texts                 |
|  1. broken         9           |
|  ...                           |
+--------------------------------+
```

What is verified at 320 px against WCAG 2.1 SC 1.4.10 (Reflow): no horizontal
scrolling, no loss of content or functionality, no truncation of the series list
or the term lists, and both tables remain real tables. The Analyze and History
views need no narrow-layout work at all — they are already a single fluid column.

---

## 8a. What the team's affirmed practices require of this markup (team-practices)

The practices below were affirmed on 2026-10-02 and constrain the markup and script
this stage specifies. Each is cited from `aidlc/spaces/default/memory/team.md` and
`project.md` rather than restated, so a reader can check it at source.

- **Read-path boundary** (`team.md ## Code Style`, "Where reads go"): aggregate read
  queries live in the dedicated read module beside `repository` and are called from
  the route. Nothing in this design adds a query to the route layer; the view
  consumes the two `/v2` endpoints and nothing else.
- **Parameter-bound SQL only** (`team.md ## Code Style`): the view is a consumer, so
  it carries no SQL — recorded here because the read module it depends on does.
- **Refuse, never substitute** (`team.md ## Code Style`): the no-share marker in
  §1.3 is this convention applied to the view. A `null` share is rendered as
  "no share", never as `0.00 %`.
- **No junk-drawer module** (`team.md ## Code Style`): any helper the view needs
  lives with the concept it serves; no new `utils.js`-style file is specified.
- **`textContent` everywhere** (`team.md ## Code Style`, no XSS sink): every value
  this design renders is written with `textContent`. No `innerHTML`, and no
  markup assembled as a string.
- **No new front-end dependency** (`project.md ## Mandated`, the two-runtime-package
  cap; `FR6.6`, `NFR6`): the SVG polyline, the table and the lists are all native
  HTML and SVG. No charting library, no framework, no build step.
- **`data-testid` hooks join the pinned constant** (`team.md ## Testing Posture`;
  `FR6.9`, `AC6.1.2`): every new hook named in `design-system-mapping.md` is added to
  `REQUIRED_TEST_IDS` in `tests/test_page.py`, the constant that currently pins 14 of
  the 16 existing hooks.
- **Accessibility basics per region** (`team.md ## Testing Posture`, and the
  granularity correction carried from this workflow's earlier review):
  `accessibility-checklist.md` is written one line per screen per region, not one
  bundled line per screen.

## 9. Open points carried to a later stage

1. **The "all time" placeholder — accepted as visible text.** Ruling 5 asked for
   a placeholder on both date inputs; Q9 ruled that the placeholder mechanism was
   impossible as first written (browsers do not render `placeholder` on
   `type="date"`), so **visible text was the accepted substitute**. This spec
   delivers the wording with visible text in `analytics-range-state` and sets no
   `placeholder` attribute (§3.5).
2. **`analytics-partial` as a second surface.** It is a `role="status"` region,
   not an alert, and the error still renders in the one `error-panel`. If the
   ruling was meant to forbid *any* second error-ish element, say so and the
   partial state folds into the error panel's message text instead — at the cost
   of `AC6.5.5`'s distinct-region requirement.
3. **Per-day `counts`, `shares` and `mean_confidence` are not rendered.** They
   are in every series entry (`AC2.3.2`) and the text list carries only `date` and
   `total`, making it an exact text equivalent of the plotted line. Add them per
   day and the list roughly triples in length.
4. **The breakdown bar.** Dropped in §1.5. Reinstatement is one column.
5. **A named media query — not added, by ruling.** §8.1 specifies content-driven
   wrap thresholds instead, and the shipped stylesheet contains **no** media query,
   so none was added (Q11). If a `@media (max-width: 30rem)` is ever wanted for
   vertical rhythm, it is one rule.
6. **The footer — not carried forward, by ruling.** Removed in §1.1 and accepted
   as a deliberate omission (Q11). If it is wanted for its "computed locally"
   reassurance, that reassurance belongs on the connection indicator, which already
   says it in words.
7. **Three-view fetch changes — accepted, and changes to existing behaviour
   caused by the nav ruling (Q10).** `refreshHistory()` and `refreshConnection()`
   currently run on **page load** (`app.js:193–194`). Under a view model:
   History fetches on **activation** rather than page load; Analytics fetches on
   activation rather than page load, and refetches on **every** activation as well
   as on Apply — so the data is never stale after an analysis performed in the
   Analyze view. Both are **changes to existing behaviour caused by the nav ruling
   (ruling 6), not requested by any story and not covered by any acceptance
   criterion.** The behaviour that changes: **the history list currently loads
   with the page**; under this ruling it loads when History is activated. Stated
   here so the change is on the record as a consequence rather than discovered as a
   regression.
8. **`aria-current="page"` on an in-page view.** Ruling 7 chose `"page"`. The
   three views are three regions of one document with no URL change, so `"true"`
   is the semantically exact token. This spec follows the ruling and uses
   `"page"`; `AC6.1.4` requires only that the attribute be present.
9. **Analytics errors diverge from shipped behaviour.** The analytics path drops
   the machine-code prefix that the existing Analyze path shows via
   `readErrorMessage` (`app.js:30–40`, §1 C7). Aligning the Analyze path too is out
   of this feature's scope and is named here so the inconsistency is a decision on
   the record rather than a surprise.
10. **The 4-dp share rounding has no stated tie rule — registered for
    `requirements.md` Revision 3 (cited, not decided).** `FR2.7` fixes
    four-decimal rounding but states **no tie rule**, and a tie is reachable: over
    a denominator of 128, a count of 36 is exactly `0.28125`, so **half-up
    (`0.2813`) and half-even (`0.2812`) disagree**. `FR8.2` requires a hand-pinned
    share value, so the mockups' own fixture must avoid a tie until an upstream
    rule exists — which §3.0 does (`66`, `35` and `27` over `128`), so the mockups
    do not silently take a side. This is **cited as an open item registered for
    `requirements.md` Revision 3, not decided here**; it is not this stage's to
    settle.
