# Mockups — `very-cool-sentiment-analysis` v1

Refined from the user stories and the requirements; the classic scope has no rough-mockups stage, so
there is no wireframe input and nothing here invents one. The interface is the existing single page
refined in place (answer Q1 = A): same sections, clarified states, no structural rework.

- **Persona**: the local user (`personas.md`), desktop-first but now responsive (Q5 = C).
- **States specified** (Q2 = B): loading, empty, success, invalid input, live-mode failure — the
  states the app can actually reach. Long-text and offline-versus-live distinctions are covered inside
  the success state and the connection indicator rather than as separate screens.
- **Accessibility target** (Q3 = A): WCAG 2.1 AA with both measured gaps fixed; see
  `accessibility-checklist.md`.

## Screen 1 — Analyse and history (single page)

### Default / empty state (returning user with no rows, first run with no rows)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Sentiment Analysis                          [●] offline engine      │  header: h1 + indicator
├──────────────────────────────────────────────────────────────────────┤
│  Paste a piece of text and I will score it.                          │  lede (no intensity promise)
│                                                                      │
│  ┌────────────────────────────────────────────────┐  ┌────────────┐  │
│  │                                                │  │  Analyse   │  │  form: label + textarea + submit
│  │                                                │  └────────────┘  │
│  └────────────────────────────────────────────────┘                  │
│                                                                      │
│  Result                                                              │  result region (aria-live=polite)
│  ┌────────────────────────────────────────────────┐                  │
│  │ Nothing analysed yet. Enter some text above.   │                  │  empty state, not a blank panel
│  └────────────────────────────────────────────────┘                  │
│                                                                      │
│  History                                                             │  h2
│  ┌────────────────────────────────────────────────┐                  │
│  │ No analyses yet.                               │                  │  empty state
│  └────────────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Loading state

The submit control enters its busy state and the result region announces that work is in progress.
The page does not blank out and the history stays as it was.

```
│  ┌────────────────────────────────────────────────┐  ┌────────────┐  │
│  │ ...the submitted text stays visible...         │  │ Analysing… │  │  button: disabled + aria-busy
│  └────────────────────────────────────────────────┘  └────────────┘  │
│  Result                                                              │
│  ┌────────────────────────────────────────────────┐                  │
│  │ Working…                                       │                  │  aria-live polite announcement
│  └────────────────────────────────────────────────┘                  │
```

### Success state

```
│  Result                                                              │
│  ┌────────────────────────────────────────────────┐                  │
│  │  positive                     confidence 0.86  │                  │  label (largest text) + confidence
│  │  ────────────────────────────────────────────  │                  │
│  │  positive  ████████████████░░░░  0.86          │                  │  bar + number per label
│  │  neutral   ███░░░░░░░░░░░░░░░░░  0.11          │                  │  never colour alone: number + label
│  │  negative  █░░░░░░░░░░░░░░░░░░░  0.03          │                  │
│  │  offline engine · typesafe/jev-1.13 not used    │                  │  which engine answered
│  └────────────────────────────────────────────────┘                  │
```

### Invalid input state

The refusal is text, not a red border; the result region keeps the previous result visible under a
clearly-labelled error.

```
│  ┌────────────────────────────────────────────────┐  ┌────────────┐  │
│  │                                                │  │  Analyse   │  │
│  └────────────────────────────────────────────────┘  └────────────┘  │
│  Result                                                              │
│  ┌────────────────────────────────────────────────┐                  │
│  │ ! That text is empty. Enter something to score.│                  │  role=alert, text + icon
│  └────────────────────────────────────────────────┘                  │
```

### Live-mode failure state (the Q6 ruling: an explicit attempt path)

```
│  Sentiment Analysis    [●] live requested — no key    [Connect]      │  indicator: state + reason + action
│  Result                                                              │
│  ┌────────────────────────────────────────────────┐                  │
│  │ ! Live analysis needs a key. Fill in            │                  │  role=alert, names the file
│  │   config.local.toml, or connect above.          │                  │
│  └────────────────────────────────────────────────┘                  │
```

## Responsive behaviour

The page currently declares a viewport and has no media queries; Q5 = C commits it to full
responsive behaviour.

| Breakpoint | Layout |
|---|---|
| **Phone (< 768px)** | Single column. The form, result and history stack vertically, full width. The indicator moves under the title. Submit becomes full-width. Result bars stay ≥ 24px tall with the number beside them, never inside them. |
| **Tablet (768–1024px)** | Single column, comfortable margins; the result panel and history stay stacked; the indicator sits on the header row's right. |
| **Desktop (> 1024px)** | The layout above: header row, form, result panel, then history. Content column is bounded (max ~72ch) so the result stays scannable. |

No layout relies on hover: every state that hover reveals (the indicator's reason) is also reachable
by focus and is present in the text.

## Design decisions carried by this mockup

1. **The empty state is explicit.** Both the result region and the history say what is missing rather
   than rendering blank boxes — the page loads history before the user acts, so the first paint is the
   empty state.
2. **The result names its engine.** The offline stand-in is labelled where the result is shown, not
   only in the header indicator, because knowing which engine answered is the persona's central need.
3. **No intensity anywhere.** The lede and the result panel lose the intensity promise and line
   (answer Q4 = A); the stored-field consequence is a schema question owned by the stories.
4. **Errors are text plus icon**, announced through the live region, never colour alone.
5. **One page, refined.** Analyse and history keep their sections; nothing gains a route.
