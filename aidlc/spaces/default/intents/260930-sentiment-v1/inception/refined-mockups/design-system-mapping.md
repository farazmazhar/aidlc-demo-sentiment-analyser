# Design System Mapping — `very-cool-sentiment-analysis` v1

## What exists today

**No design system, no component library, no token file.** The page is one HTML document
(`app/static/index.html`) that styles itself with class-named native elements — `connection-indicator`,
`connection-dot`, `lede`, `probabilities`, `history-item`, `history-text`, `history-meta` — plus a
`<template>` for history rows and one script (`app/static/app.js`). There is no CSS asset in
`app/static/`, no framework (no Tailwind, no Bootstrap, no component package in `pyproject.toml`) and
no icon set.

This is a deliberate v1 constraint, not an oversight: the project caps its dependencies at two runtime
packages, the interface is one page, and the persona is one local user. Introducing a design system
would add weight with no consumer.

## Decision

**Stay on native HTML elements plus the page's own class names, and standardise the small set of
tokens the page already depends on.** The mapping below is therefore from specification component →
native element → class name, not to library components. Anything that cannot be expressed natively
(the probability bars) is decorative markup with the same information available as text.

## Component mapping

| Spec component | Native element | Existing class / id | Notes |
|---|---|---|---|
| Analyse form | `<form>`, `<label for>`, `<textarea>`, `<button type="submit">` | (page form) | Adds a visible `<label>`; the current page relies on the lede for context |
| Result panel | `<section role="status" aria-live="polite">` with `<h2>` | result ids (`result-probabilities`) | Gains the live region and the engine note |
| Probability row | `<li>` with text + decorative bar | `.probabilities` | The number is always text; the bar is decoration and must not be the only signal |
| History list | `<ul>` / `<li>` from a `<template>` | `.history-item`, `.history-text`, `.history-meta` | Keeps today's template pattern; rows gain a native expand button |
| Connection indicator | `<span role="status">` with text and a decorative dot | `.connection-indicator`, `.connection-dot` | Gains meeting contrast and the 44×44 floor; the dot stays `aria-hidden` |
| Message banner | `<p role="alert">` or `role="status"` | (new) | Replaces bare machine codes rendered as text |
| Headings and regions | `<h1>`, `<h2>`, `<main>`, `<header>` | `h1` present today | Region headings make the page navigable by heading |

## Tokens to standardise (the minimum v1 needs)

| Token | Value / rule | Why |
|---|---|---|
| Text colour, primary | ≥ 4.5:1 against the page background | WCAG 1.4.3, and the measured gap in the dark scheme |
| Text colour, muted | ≥ 4.5:1 for body-size text, or ≥ 3:1 only for text ≥ 24px | Keeps the lede and history meta legible |
| State colours (offline / connecting / live / rejected) | Each ≥ 4.5:1 as text and ≥ 3:1 as a dot, and never the only signal | The indicator must read correctly without colour perception |
| Focus ring | ≥ 2px, ≥ 3:1 against the adjacent background | WCAG 2.4.7, and `outline: none` is not permitted |
| Target size | ≥ 44×44 CSS px for the indicator and the submit control | The project's adopted floor (stricter than WCAG 2.2 AA's 24×24) |
| Spacing scale | One scale (for example 4/8/12/16/24/32 px) used for the page's gutters | The page is rebuilt responsively in v1; ad-hoc spacing is what breaks at 200% zoom |
| Type scale | One heading size, one body size, one small size; body ≥ 16px | Resize-text and scannability |
| Content column | Bounded width (≈ 72ch) with the result panel full-width inside it | Scannability on a wide desktop window |

## Responsive mapping

The breakpoints in `mockups.md` become the layout rules: phone (<768px) stacks and widens controls,
tablet (768–1024px) tightens gutters, desktop (>1024px) is the default layout. Nothing is hidden at
any breakpoint, and no state is revealed by hover alone.

## What this mapping explicitly rejects

- A CSS framework or component library (dependency weight, no second page to justify it).
- Icon fonts or SVG sprite sets: the only icon is the decorative state dot, which carries no meaning
  on its own.
- A `role="listbox"` history widget: rows are a plain list with one native button each, because the
  page has no keyboard selection model to expose.
