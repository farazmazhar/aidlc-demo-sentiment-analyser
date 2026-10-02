# Design System Mapping — Analytics View (Refined)

> **This project has no design system.**
>
> There is no component library, no token file, no theme layer, no icon set, no
> typography scale and no external stylesheet. `app/static/index.html` ships one
> inline `<style>` block with seven class selectors and six bare-element
> selectors, and a `:root` block that declares exactly **two** custom properties:
> `color-scheme: light dark` and `font-family`. Nothing else exists to map onto.
>
> So this document is a **mapping, not an adoption.** It does not import,
> subscribe to, or conform to a design system, and it must not be read as evidence
> that the project has one. What it does is record, for every component this stage
> specifies: which **native HTML element** realises it, which **class name** styles
> it, and which **accessibility attribute** carries its semantics — reusing the
> seven existing class names where they fit and adding new ones written in the same
> flat, single-word style.

---

## 1. What already exists, exactly

### 1.1 Custom properties

| Declaration | Location | Reusable? |
|---|---|---|
| `color-scheme: light dark` | `index.html:9` | global; inherited, nothing to map |
| `font-family: system-ui, -apple-system, "Segoe UI", sans-serif` | `index.html:10` | global; inherited, nothing to map |

**There are no colour, spacing, radius, shadow or type tokens.** Any new rule that
needs a value must use a literal in the same manner as the existing rules — the
shipped file already writes `1px solid currentColor`, `border-radius: 6px`,
`rgba(128, 128, 128, 0.4)`, `#b00020` and `#1a7f37` as literals inside rules, and
that is the convention the analytics styles follow. Introducing a `:root` token
layer would be creating a design system, which this stage is explicitly not doing.

### 1.2 Class names in the shipped page

| Class | Styles | Analytics use |
|---|---|---|
| `.lede` | `margin-top: 0; opacity: 0.85` | **moves into the Analyze view**; not reused for analytics text, because `opacity` cannot be contrast-checked under `color-scheme: light dark` |
| `.probabilities` | list reset on the result panel's `<ul>` | **the direct precedent** for `.series-values` and the two term `<ol>`s |
| `.history-item` | top rule, block padding | not needed; analytics rows have no rule between them |
| `.history-text` | `display: block; font-weight: 600` | not needed |
| `.history-meta` | `opacity: 0.85; font-size: 0.9rem` | not reused, for the same `opacity` reason |
| `.connection-indicator` | the whole pill, including the now-removed `position: fixed` | used unchanged, in the new `header` |
| `.connection-dot` | `0.6rem` circle | used unchanged |

### 1.3 Bare-element selectors already in the file

| Selector | Declarations | What it means for the analytics markup |
|---|---|---|
| `body` | `margin: 0 auto; max-width: 46rem; padding: 3.5rem 1.25rem 4rem; line-height: 1.5` | the single fluid column; the `header` and all three views sit inside it, so the whole page is one measure at every width |
| `h1` | `margin-bottom: 0.25rem` | the `h1` is now in the `header`; the rule follows it |
| `form` | `display: grid; gap: 0.5rem; margin: 1.5rem 0` | **applies to the new analytics range form too** — see §4 |
| `textarea` | `font: inherit; padding: 0.6rem; resize: vertical` | unaffected; the analytics view adds no textarea |
| `button` | `font: inherit; padding: 0.5rem 1rem; justify-self: start; cursor: pointer` | applies to both new range buttons; `justify-self` makes them left-aligned inside the grid form. Not restated in a new rule |
| `section[data-testid="result-panel"], section[data-testid="error-panel"]` | border, radius, padding, margin | **the panel recipe the empty region reuses** (§3) |
| `section[data-testid="error-panel"]` | `border-color: #b00020; color: #b00020` | untouched; the analytics view reuses the element, not a new red rule |

### 1.4 The one trap this mapping must state

**No rule anywhere in the file may set `display` on an element that is toggled
with the `hidden` attribute.** The UA stylesheet's `[hidden] { display: none }`
has the same specificity as any plain-class selector placed on it later, so a
single new `display: flex` on a view, a region or the range form silently breaks
its own hiding. This matters because this stage introduces **eleven** new
`hidden`-toggled elements (three views, four analytics regions, two list-empty
paragraphs, the error panel's existing toggle). The shipped `form` rule already
sets `display: grid`, which is why the range form is never itself `hidden` — only
the sections around it are.

---

## 2. New class names introduced

Twelve, all flat single words or two joined words, matching the shipped naming
style (`.connection-indicator` is the longest existing name at two words).

| Class | Purpose | Why a new name rather than a reused one |
|---|---|---|
| `.site-nav` | the `nav` and its links | `.probabilities` and the history classes are component-specific; a nav needs its own hook, and it also carries the `[aria-current="page"]` rule |
| `.view` | shared spacing for the three view wrappers | the three views need identical vertical rhythm without three near-identical id selectors |
| `.range-fields` | the two date field pairs | the shipped file has no grouped-field pattern to reuse |
| `.range-field` | one label-above-input pair | ditto |
| `.range-actions` | the button row | keeps `Apply` and `Show all time` on one line that wraps |
| `.range-state` | the range-state paragraph | needs `margin-top` tuning distinct from body copy |
| `.summary-figures` | the `<dl>` grid | `max-content 1fr` has no existing analogue |
| `.series-chart` | the `<svg>` | `width: 100%; height: auto; display: block` is new |
| `.series-values` | the per-day `<ol>` | a copy of the `.probabilities` list reset, scoped to the series |
| `.breakdown-table` | the `<table>` | `width: 100%; border-collapse: collapse` is new; `tabular-nums` is new |
| `.term-lists` | the two-list grid | `repeat(auto-fit, minmax(16rem, 1fr))` is new |
| `.skeleton` | the loading placeholder block | a muted `currentColor` background is new |

**Deliberately not introduced:** a visually-hidden utility class. Every text
alternative in this design is either visible or genuinely decorative and marked
`aria-hidden="true"` (the skeletons, the connection dot), so the utility would have
exactly one theoretical user and none in practice.

**Deliberately not introduced:** any colour literal of its own. The analytics
regions use `currentColor`; the red error styling is inherited from the existing
`error-panel` rule and is not duplicated.

---

## 3. Component → element → class → accessibility attribute

Every row names the accessibility attribute the element actually carries. Where
an element carries none, that is stated rather than left blank, because "no
attribute needed" is a decision.

### 3.1 Shell

| Component | Native element | Class | Accessibility attribute carried |
|---|---|---|---|
| Site header | `<header>` | — | implicit `role="banner"`; no explicit `role` |
| Page title | `<h1>` | — | none — heading level only |
| Primary navigation | `<nav>` | `.site-nav` | `aria-label="Views"` → implicit `role="navigation"`, named |
| Nav entry, active | `<a href="#analyze">` | `.site-nav` child | `aria-current="page"`, selected by the CSS rule `.site-nav a[aria-current="page"]` |
| Nav entry, inactive | `<a>` | `.site-nav` child | **none** — the attribute is *absent*, not `"false"` |
| Connection indicator | `<button type="button">` | `.connection-indicator` | none on the button; its inner `<span>` carries `role="status"` + `aria-live="polite"` (shipped, unchanged) |
| View wrapper | `<section>` | `.view` | `aria-labelledby` → implicit `role="region"`, named by its own `h2` |
| View heading | `<h2>` | — | none; referenced by the view's `aria-labelledby` |
| Template (row source) | `<template>` | — | none; not rendered. Currently inside `<main>`; §2.4 of `mockups.md` moves it to the end of `<body>` |

### 3.2 Analytics regions

| Component | Native element | Class | Accessibility attribute carried |
|---|---|---|---|
| Range control | `<form novalidate>` | — | implicit `role="form"`, **unnamed** (the surrounding region is already named "Analytics") |
| Field pair | `<div>` | `.range-field` | none — presentational grouping only, no `role` |
| Date input | `<input type="date">` | — | named by its sibling `<label for>`; **no `placeholder`**, because browsers do not render one on `type="date"` — visible text beside the control is the accepted substitute for the ruled "all time" wording |
| Field label | `<label for>` | — | `for` is the association, not an ARIA attribute |
| Apply | `<button type="submit">` | — | none; the accessible name is the visible text |
| Show all time | `<button type="button">` | — | none |
| Button row | `<div>` | `.range-actions` | none |
| Range-state line | `<p>` | `.range-state` | none — not a live region. It is read on demand, not announced |
| Loading region | `<section>` | — | `role="status"` + `aria-live="polite"` |
| Skeleton block | `<div>` | `.skeleton` | `aria-hidden="true"` — decorative |
| Empty region | `<section>` | — | `aria-labelledby` → named `region`; **not** a live region |
| Empty heading | `<h3>` | — | none |
| Empty action | `<a href="#analyze">` | — | none |
| Partial status | `<section>` | — | `role="status"` + `aria-live="polite"` — polite, because the alert already spoke |
| Summary region | `<section>` | — | `aria-labelledby` → named `region` |
| Summary name/value list | `<dl>` | `.summary-figures` | none — native description-list semantics |
| Summary term | `<dt>` | — | none |
| Summary value | `<dd>` | — | none |
| Series region | `<section>` | — | `aria-labelledby` → named `region` |
| Series caption | `<p>` | — | **target of `aria-labelledby`** from the `<svg>`; no attribute of its own |
| Series drawing | `<svg>` | `.series-chart` | `role="img"` + `aria-labelledby="analytics-series-caption"` — flattens the subtree so the axis `<text>` is not announced twice |
| Series line | `<polyline>` | — | none; presentational, inside a `role="img"` subtree |
| Series marker (one-day case) | `<circle>` | — | none; same subtree |
| Axis label | `<text>` | — | none; same subtree |
| Series values | `<ol>` | `.series-values` | `role="list"`, restored because `.series-values` removes the list marker |
| Series value row | `<li>` | — | none. Carries only `date` and `total` — the text equivalent of the plotted line, not the whole series entry (`AC2.3.2` has the API return more per day) |
| Breakdown region | `<section>` | — | `aria-labelledby` → named `region` |
| Breakdown table | `<table>` | `.breakdown-table` | none — native `table` role; **no `role` attribute**, which would be ARIA misuse |
| Breakdown caption | `<caption>` | — | none; supplies the table's accessible name |
| Column header | `<th scope="col">` | — | `scope="col"` — the association, not ARIA |
| Breakdown row | `<tr>` | — | none |
| Breakdown cell | `<td>` | — | none |
| Terms region | `<section>` | — | `aria-labelledby` → named `region` |
| Terms container | `<div>` | `.term-lists` | none — presentational grid |
| Polarity block | `<div>` | — | none |
| Polarity heading | `<h4>` | — | none |
| Term list | `<ol>` | `.series-values` | `role="list"`, restored |
| Term row | `<li>` | — | none |
| List-empty message | `<p>` | — | none; toggled with `hidden` |
| Not-loaded marker | `<p>` | — | none; toggled with `hidden`. One per failed region — the summary `<dl>`, the series caption/chart/list, the breakdown `<table>`, or a term list position — so a partial failure marks its failed half in place (`interaction-spec.md` §13.1, §13.4). Same plain-`<p>` shape as the list-empty message; no class, no live region, no red |
| Error panel | `<section>` | — | `role="alert"` (shipped, reused unchanged) |

### 3.3 Attribute discipline

| Rule | Applied as |
|---|---|
| No `role` on an element that already has the right native semantics | The only `role` attributes introduced are `img` (on `<svg>`, which has none), `status` (on a `<section>` that has none), and `list` (restored after a list style is removed). Every other role is implicit |
| No `aria-label` where visible text exists | There are **no** `aria-label` attributes in the analytics markup. The two names that are not visible text are supplied by `aria-label="Views"` (the nav) and `aria-labelledby` (the series caption, which is visible) |
| `aria-labelledby` preferred over `aria-label` for visible text | `Views` is the exception: a nav's visible content is three links, not a name, so a label is required |
| No `aria-describedby` anywhere | The range-state line and the caption are read in DOM order immediately after the thing they describe; describing them by reference would duplicate |
| No `aria-hidden` on anything carrying data | Only the skeletons and the connection dot are hidden from assistive technology, and neither carries data |
| No `tabindex` except `-1` | `tabindex="-1"` on the three view containers only, for programmatic focus. No `tabindex="0"`, no positive values, so the natural tab order is untouched |
| No `aria-current="false"` | The attribute appears on one link or on none |
| `hidden` is an attribute, not a class | Every toggle in §1.4 uses the `hidden` attribute, which the UA stylesheet honours and no new rule may override |

---

## 4. Brownfield consequences a later stage inherits

| # | Consequence | Handling |
|---|---|---|
| B1 | `form { display: grid; gap: 0.5rem; margin: 1.5rem 0; }` is a **bare-element** selector, so it applies to the new range form as well as the analyze form | Accepted rather than weakened. The range form's children are `.range-fields`, `.range-actions` and the range-state `<p>`, which stack vertically as grid rows with a `0.5rem` gap — a correct layout. `button { justify-self: start }` then left-aligns both buttons inside `.range-actions`. Overriding the shared `form` rule for one form would change the analyze form too |
| B2 | `button { padding: 0.5rem 1rem }` gives the new buttons the same height as the existing Analyse button — under the 44 px touch-target guidance | Inherited on purpose. A new `min-height` rule would change the existing button, which is out of this feature's scope. Named as a carried-forward verification item |
| B3 | `.connection-indicator` is `position: fixed; top: 0.75rem; left: 0.75rem; z-index: 10` | Those four declarations are removed (ruling 7). `min-height`, `min-width`, `font`, `padding`, `border`, `border-radius`, `background: Canvas`, `cursor`, `color`, the `[data-connected="true"]` variant and the `:focus-visible` outline are all kept verbatim |
| B4 | `body { padding: 3.5rem 1.25rem 4rem }` existed to clear the pinned indicator | Harmless once B3 is applied. Whether to reduce the top padding is a cosmetic call; not specified, because specifying it would be specifying a visual decision this stage has no basis to make |
| B5 | `.probabilities` is the page's only list-reset class | `.series-values` and the two term `<ol>`s duplicate those four declarations rather than reusing the name, because `.probabilities` is semantically about probability rows and reusing it would make the CSS lie |
| B6 | `#history-list { list-style: none; padding: 0 }` is an **id** selector | The analytics lists use classes. No new id selectors are introduced for styling; the ids that exist (`#analytics-*`) exist only as `label for` targets and `aria-labelledby` targets, which is what ids are for |
| B7 | `tests/test_page.py:64` forbids the substring `intensity` in the whole page, `<style>` and comments included | No new class, id, hook, comment or label contains it — see `mockups.md` §1.2 |
| B8 | `app.js` sets every value through `textContent` | No new render path uses `innerHTML`, `insertAdjacentHTML` or an HTML template literal. The SVG `points` attribute is set with `setAttribute` from `Number(...).toFixed(1)` values |
| B9 | `.error-panel`'s red is `#b00020` on both border and text | Reused by reference, never duplicated into a new rule. Whether `#b00020` meets SC 1.4.3 on a dark canvas is a verification item on the *shipped* styling, not a design change here |
| B10 | The shipped stylesheet contains **no media query** (`grep -c "@media" index.html` → `0`) | No media query is added. The narrow layout is content-driven (`auto-fit` grids and `flex-wrap`), so the stylesheet still contains none. Accepted as a deliberate omission (Q11); see `mockups.md` §8.1 |
| B11 | `readErrorMessage` surfaces `${payload.code}: ${payload.message}` on the shipped Analyze flow (`app.js:30–40`) | The analytics view **diverges** deliberately: status-derived lead-in plus `payload.message`, no machine code. The shipped Analyze rendering is not changed; the divergence is from shipped behaviour, not from the wireframes alone |
| B12 | The wireframes' `footer` is not carried forward | Deliberate omission (Q11); the "computed locally" state already lives on the connection indicator. No `footer` element is added |

---

## 5. What this mapping deliberately does not do

| Not done | Why |
|---|---|
| Introduce CSS custom properties for colour or spacing | That is creating a design system, which this project does not have and this stage was told not to invent |
| Adopt a component library or a class-naming convention from any framework | `FR6.6` forbids a new front-end dependency and the two-runtime-dependency cap forbids one |
| Add a build step, a preprocessor or an external stylesheet | `AC6.1.3`: the view's assets come from the same route as the page's existing script and style, with the same content type |
| Add an icon set, an illustration or a font | The empty state has no illustration (the wireframes' own "no icon needed" note); no new glyph has anywhere to come from |
| Restyle the analyze form, the result panel or the history list | Out of scope. Only the wrapper and the `h2` nesting change, and both are recorded in `mockups.md` §2 |
| Change any colour already in the file | B9 |
| Define states as CSS classes (`.is-loading`, `.is-error`) | The page's idiom is the `hidden` attribute plus `data-*` attributes, as on `.connection-indicator[data-connected="true"]`. Introducing a parallel class-based state system would be a second convention on a one-stylesheet page |

---

## 6. Summary

- **Native elements used:** `header`, `nav`, `a`, `button`, `section`, `p`,
  `form`, `label`, `input`, `div`, `h1`–`h4`, `dl`, `dt`, `dd`, `ol`, `li`,
  `table`, `caption`, `thead`, `tbody`, `tr`, `th`, `td`, `svg`, `text`,
  `polyline`, `circle`, `template`. **No element is invented and no `div` is given
  a role to stand in for a semantic one.**
- **Class names added:** 12, in the shipped flat style (§2).
- **Class names reused:** `.connection-indicator`, `.connection-dot`,
  `.probabilities` (as the pattern for three list resets), `.lede` (moved, not
  restyled).
- **Custom properties added:** none.
- **Design systems adopted:** none. There is none to adopt.
