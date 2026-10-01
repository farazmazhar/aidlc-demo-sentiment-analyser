# Interaction Specification — `very-cool-sentiment-analysis` v1

Component-level specifications for the refined single page, in the format of
`.aidlc/knowledge/aidlc-design-agent/component-spec-template.md`. Every state named here is one the
app can reach (answer Q2 = B). No component is introduced that does not serve a story.

---

## Analyse Form

| Field | Value |
|---|---|
| Component | Analyse form (textarea + submit) |
| Description | Collects the text to score and submits it |
| Category | input |

### States

| State | Description | Trigger |
|---|---|---|
| default | Empty textarea, enabled submit | page load |
| focus | Visible focus ring on textarea and on submit | Tab / click |
| typing | Text present, submit enabled | user input |
| invalid | Submission refused for empty or whitespace-only text | submit with blank value |
| busy | Submit disabled, text remains visible | request in flight |
| disabled | Submit disabled | busy state only |

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| `text` | string | yes | `""` | The text to score |
| `maxLength` | number | no | — | Not set in v1; the provider's text limit is an open requirements question |
| `busy` | boolean | no | `false` | Disables submit and announces work in progress |
| `onSubmit` | function | yes | — | Sends the text to `POST /analyze` |

### Responsive Behaviour

| Breakpoint | Behaviour |
|---|---|
| mobile (<768px) | Textarea full width; submit full width beneath it |
| tablet (768–1024px) | Textarea full width; submit right-aligned beneath |
| desktop (>1024px) | Textarea and submit on one row, submit to the right |

### Accessibility

| Requirement | Implementation |
|---|---|
| ARIA role | Native `<form>`, `<label for>`, `<textarea>`, `<button type="submit">` — no ARIA needed beyond the live region it triggers |
| Keyboard interaction | Tab into the textarea, Enter submits when the control is a button (a textarea keeps Enter for newlines), Space activates the button |
| Label / aria-label | Visible `<label>` "Text to analyse", associated by `for`/`id` |
| Contrast ratio | Text 4.5:1; submit button text and border ≥ 3:1 |
| Screen reader | Busy state sets `aria-busy="true"` on the form region and announces "Analysing" through the result live region |
| Focus management | Focus stays in the textarea after submitting; on refusal, focus moves to the error text in the result region |

### Usage Example

```
<form class="analyse" onsubmit="analyse(event)">
  <label for="text">Text to analyse</label>
  <textarea id="text" name="text"></textarea>
  <button type="submit">Analyse</button>
</form>
```

---

## Result Panel

| Field | Value |
|---|---|
| Component | Result panel |
| Description | Shows the label, confidence and per-label probabilities for the latest analysis |
| Category | display / feedback |

### States

| State | Description | Trigger |
|---|---|---|
| empty | "Nothing analysed yet." | first paint or after a cleared history |
| loading | "Working…" | request in flight |
| success | Label, confidence, three probability rows, engine note | 2xx from `POST /analyze` |
| invalid | Empty-input refusal text | `422 INVALID_TEXT` |
| live-failure | The live-attempt refusal, naming `config.local.toml` | live requested, no usable key |

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| `result` | object | no | — | `{ label, confidence, probabilities, model, provider, created_at }` |
| `state` | enum | yes | `empty` | `empty \| loading \| success \| invalid \| live-failure` |
| `engine` | enum | yes | `offline` | Which engine produced the shown result |

### Responsive Behaviour

| Breakpoint | Behaviour |
|---|---|
| mobile (<768px) | Probability rows stack label-above-bar; numbers stay beside the bar, never inside it |
| tablet (768–1024px) | As desktop, tighter gutters |
| desktop (>1024px) | Label and confidence on one row; three bars beneath |

### Accessibility

| Requirement | Implementation |
|---|---|
| ARIA role | `role="status"` with `aria-live="polite"` for successful updates; `role="alert"` for refusals |
| Keyboard interaction | Not focusable itself; its refusal text receives focus after a failed submit |
| Label / aria-label | Region labelled "Result" by a visible `<h2>` via `aria-labelledby` |
| Contrast ratio | Label text 4.5:1; bars and their borders ≥ 3:1 |
| Screen reader | Announces the label, then the confidence and each probability as text, then which engine answered — the bars are decorative and carry the same numbers as text |
| Focus management | On success, focus stays where it was; the live region announces the outcome |

### Usage Example

```
<section class="result" aria-labelledby="result-heading" role="status" aria-live="polite">
  <h2 id="result-heading">Result</h2>
  <p class="label">positive</p>
  <p class="confidence">confidence 0.86</p>
  <ul class="probabilities">…</ul>
  <p class="engine">offline engine</p>
</section>
```

---

## History List

| Field | Value |
|---|---|
| Component | History list |
| Description | Lists stored analyses newest-first, each row showing its text, label and timestamp |
| Category | display |

### States

| State | Description | Trigger |
|---|---|---|
| empty | "No analyses yet." | no rows stored |
| populated | Rows, newest first | `GET /analyses` returns rows |
| busy | Previous rows stay visible while a refresh is in flight | after a new analysis |
| error | The list says it could not be read | non-2xx from `GET /analyses` |

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| `analyses` | array | yes | `[]` | Stored rows |
| `limit` | number | no | documented default (the number is an open requirements item) | Rows requested from `GET /analyses` |
| `selected` | string | no | `null` | Id of the row whose full result is shown, if any |

### Responsive Behaviour

| Breakpoint | Behaviour |
|---|---|
| mobile (<768px) | One row per analysis; text truncates with a full-text affordance; timestamp moves under the label |
| tablet (768–1024px) | One row per analysis, text and timestamp share the row |
| desktop (>1024px) | As tablet, content column bounded for scannability |

### Accessibility

| Requirement | Implementation |
|---|---|
| ARIA role | `<ul>` of `<li>` rows; no listbox semantics in v1 (selection is not a keyboard mode) |
| Keyboard interaction | Each row's expand control is a native `<button>` reachable by Tab |
| Label / aria-label | Region labelled "History" by its `<h2>` |
| Contrast ratio | Row text 4.5:1; separators ≥ 3:1 |
| Screen reader | Each row reads text (truncated form announced in full), label, and timestamp |
| Focus management | Selecting a row returns focus to that row's button |

---

## Connection Indicator

| Field | Value |
|---|---|
| Component | Connection indicator |
| Description | States which engine is active, whether the live model is connected, and why not |
| Category | feedback |

### States

| State | Description | Trigger |
|---|---|---|
| offline | "offline engine" | no live mode configured |
| live-requested-no-key | "live requested — no key" with a Connect action and the reason in text | live configured, no usable key |
| connecting | "connecting…" | sign-in flow in flight |
| live | "live model connected" | session credential present |
| rejected | "not connected — credential rejected" | provider rejected the credential |

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| `mode` | enum | yes | `offline` | Active engine mode from `/health` |
| `connected` | boolean | yes | `false` | Live connection state |
| `reason` | string | no | — | Text reason, never only a colour |
| `onConnect` | function | no | — | Opens the sign-in flow |

### Responsive Behaviour

| Breakpoint | Behaviour |
|---|---|
| mobile (<768px) | Sits beneath the page title |
| tablet (768–1024px) | Right end of the header row |
| desktop (>1024px) | Right end of the header row |

### Accessibility

| Requirement | Implementation |
|---|---|
| ARIA role | `role="status"` (polite) — it reflects state rather than demanding attention |
| Keyboard interaction | The Connect action is a native `<button>`; the reason is available on focus, not only on hover |
| Label / aria-label | Text label always present; the dot is decorative (`aria-hidden="true"`) |
| Contrast ratio | Text and icon ≥ 4.5:1 — **this is one of the two measured gaps being fixed in v1** (the dark-scheme colours fail today) |
| Screen reader | Announces mode changes: "live model connected", "not connected — credential rejected" |
| Focus management | Focus is not moved when the state changes; the announcement carries it |

---

## Message Banner (refusals and confirmations)

| Field | Value |
|---|---|
| Component | Message banner |
| Description | Carries a refusal or a confirmation as text with an icon |
| Category | feedback |

### States

| State | Description | Trigger |
|---|---|---|
| info | Neutral note (for example, offline disclosure) | state change |
| error | Refusal (empty text, invalid limit, live attempt without a key) | 4xx from the API |

### Props / Inputs

| Prop | Type | Required | Default | Description |
|---|---|---|---|---|
| `kind` | enum | yes | `info` | `info \| error` |
| `code` | string | no | — | The machine code from the error envelope, shown in a small caption for support |
| `message` | string | yes | — | Human-readable text |

### Responsive Behaviour

| Breakpoint | Behaviour |
|---|---|
| mobile (<768px) | Full width, wraps freely |
| tablet (768–1024px) | Full width of the content column |
| desktop (>1024px) | Full width of the content column |

### Accessibility

| Requirement | Implementation |
|---|---|
| ARIA role | `role="alert"` for refusals, `role="status"` for information |
| Keyboard interaction | Read-only; no focusable content except an optional action button |
| Label / aria-label | Not needed — the text is the label |
| Contrast ratio | Text 4.5:1 against the banner background; the icon is not the only signal |
| Screen reader | The full message is announced, including the machine code caption |
| Focus management | On refusal, focus moves to the banner so the keyboard user does not have to hunt for it |

---

## Interaction patterns not used in v1

Modals, wizards, inline editing, drag interactions and progressive disclosure have no story behind
them, so the specification does not introduce them. The sign-in flow remains a full-page navigation
to the provider and back, as it works today.
