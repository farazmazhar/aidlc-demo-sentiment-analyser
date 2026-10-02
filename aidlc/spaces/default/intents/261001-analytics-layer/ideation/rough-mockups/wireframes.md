# Wireframes — Analytics View

Low-fidelity wireframes. The analytics view is opened from a new **Analytics** entry point on the existing single-page UI [Q1]. It follows the existing page's plain HTML/CSS and class names, with no design system and no front-end library [Q4]. Desktop/laptop browser first, with a usable narrow layout where it is cheap [Q5]. WCAG 2.1 AA basics match the existing page [Q6].

## Information Architecture Outline

```
Sentiment app (existing single page)
├── Analyze            (existing)
├── History            (existing)
└── Analytics          (new entry point)
    ├── Date-range control
    ├── Summary figures (total, mean confidence, mean intensity)
    ├── Per-day time series
    ├── Label breakdown (per-label counts and shares)
    └── Top terms
        ├── Positive texts
        └── Negative texts
```

Reading order is the hierarchy confirmed in Q3: date-range control, then the per-day time series, then the label breakdown, then the two top-term lists [Q3].

## Screen 1 — Analytics view, populated (success) state

```
+--------------------------------------------------------------------+
| header  Sentiment app                       [ Analyze ] [ Analytics ]|
+--------------------------------------------------------------------+
| main                                                                 |
|                                                                      |
|  Date range: [ from  __________ ] to [ __________ ]   [ Apply ]     |
|                                                                    |
|  Total analyses 128      Mean confidence 0.71     Mean intensity 0.28|
|                                                                      |
|  Per-day series                                                     |
|    4 |      *                                                       |
|    3 |      *      *        *                                      |
|    2 |  *      *      *     *      *                             |
|    1 |  *   *      *                                   *            |
|    0 +----------------------------------------------------          |
|      2026-09-01                          2026-09-30                 |
|                                                                      |
|  Label breakdown                                                    |
|    positive   62%  ####################################             |
|    neutral    30%  ########################                       |
|    negative    8%  #####                                            |
|                                                                      |
|  Top terms: positive        Top terms: negative                     |
|    1. delivery     (12)     1. broken        (9)                    |
|    2. invoice      (10)     2. charge        (7)                    |
|    3. thanks        (7)     3. refund        (5)                    |
|                                                                      |
+--------------------------------------------------------------------+
| footer  running in dummy mode - all analytics computed locally      |
+--------------------------------------------------------------------+
```

## Screen 2 — Analytics view, empty state (no analyses in range)

```
+--------------------------------------------------------------------+
| header  Sentiment app                       [ Analyze ] [ Analytics ]|
+--------------------------------------------------------------------+
| main                                                                 |
|                                                                      |
|  Date range: [ from  __________ ] to [ __________ ]   [ Apply ]     |
|                                                                      |
|     +-------------------------------------------+                    |
|     |            ( no icon needed )            |                    |
|     |  No analyses in this date range.         |                    |
|     |  Analyse or import some text first, or   |                    |
|     |  widen the range above.                  |                    |
|     |            [ Go to Analyze ]             |                    |
|     +-------------------------------------------+                    |
|                                                                      |
+--------------------------------------------------------------------+
```

## Screen 3 — Analytics view, loading state

```
+--------------------------------------------------------------------+
| main                                                                 |
|  Date range: [ from 2026-09-01 ] to [ 2026-09-30 ]    [ Apply ]       |
|                                                                      |
|  Loading analytics for this range...                                 |
|                                                                      |
|  +--------------------------------------------------+                |
|  |  ############################                    |  <- skeleton   |
|  |  ############################                    |     blocks,     |
|  |  ##############################                  |     not colour- |
|  +--------------------------------------------------+     only        |
|                                                                      |
+--------------------------------------------------------------------+
```

## Screen 4 — Analytics view, error state

```
+--------------------------------------------------------------------+
| main                                                                 |
|  Date range: [ from 2026-13-45 ] to [ 2026-09-30 ]    [ Apply ]       |
|                                                                      |
|  [!] Could not read the analytics for this range.                  |
|      The date range is not valid. Use YYYY-MM-DD for both dates.   |
|      [ Clear the range ]                                            |
|                                                                      |
+--------------------------------------------------------------------+
```

Raw error codes are never shown to the user; the message names what went wrong and what to do [Q6].

## Screen 5 — Analytics view, partial / edge state

```
+--------------------------------------------------------------------+
| main                                                                 |
|  Date range: [ from 2026-09-01 ] to [ 2026-09-01 ]    [ Apply ]       |
|                                                                      |
|  Total analyses 1       Mean confidence 0.94     Mean intensity 0.61|
|                                                                      |
|  Per-day series                                                     |
|    1 |  *                                                            |
|    0 +-----------                                                   |
|      2026-09-01                                                     |
|                                                                      |
|  Label breakdown                                                    |
|    positive  100%  ####################                             |
|    neutral     0%                                                    |
|    negative    0%                                                    |
|                                                                      |
|  Top terms: positive        Top terms: negative                     |
|    1. excellent     (1)      ( none )                               |
|                                                                      |
+--------------------------------------------------------------------+
```

Edge cases covered: a single day, a single analysis, all-positive data, empty term lists, and zero-share labels (shown as `0%` plus a visible `0%` text label, never colour alone).

## Narrow layout

Below the existing page's breakpoint the four regions stack in the same order — date range, series, breakdown, term lists — so the reading order from Q3 is unchanged on a narrow screen; the term lists become one after the other rather than side by side. [Q5]

## Accessibility notes (one line per screen)

- **Header** — `h1` page title; `header` + `nav` landmarks; the Analytics entry is a native `<a>` or `<button>` reachable by Tab and activated by Enter.
- **Date-range control** — each date input has a visible `<label for>`; Tab moves between the two inputs and Apply; Apply activates with Enter or Space; an invalid range announces via an `aria-live="polite"` region next to the control.
- **Summary figures** — `h2` heading; plain text values, so nothing depends on colour.
- **Per-day series** — `h2` heading; the text summary (total, range, units) carries the values, and the chart graphic is marked `role="img"` with an `aria-label` long description; each day is also listed as text so keyboard and screen-reader users get the data.
- **Label breakdown** — `h2` heading; a real `<table>` with visible `<th>` headers, plus the percentage written in the cell so the bar is decorative only.
- **Top terms** — `h2` headings; two ordered lists, not tables of divs.
- **Footer** — `footer` landmark; text only.
- **All screens** — contrast at least 4.5:1 for text and 3:1 for UI components; visible focus indicator on every interactive element; no content relies on colour alone.