## Q1. What are the primary entry points and key views for the analytics feature?

A. A new "Analytics" entry point on the existing single-page UI that opens the analytics view.
B. A separate analytics page at its own URL.
C. Both — an entry from the existing page and a dedicated view.
D. Not yet defined
X. Other (please specify)

[Answer]: A

## Q2. What is the core user flow (happy path)?

A. Open the app → go to analytics → see the default date range rendered (series, label breakdown, top terms) → adjust the date range → the view updates.
B. Open the app → set a date range first → then view the analytics.
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q3. What does the information hierarchy look like?

A. Date-range control at the top; then the per-day time series; then the label breakdown; then the two top-term lists.
B. Summary numbers first, then the charts, then the term lists.
C. Not yet defined
X. Other (please specify)

[Answer]: A

## Q4. Are there existing brand guidelines, design systems, or UI patterns to follow?

A. Follow the existing single-page app's plain HTML/CSS and class names; no design system and no front-end library (the project caps runtime dependencies at two, and prior work used native HTML).
B. Introduce a small front-end charting library.
C. Not identified
X. Other (please specify)

[Answer]: A

## Q5. What device/form factors must be supported?

A. Desktop/laptop browser only (localhost, single user), with a usable narrow layout where it is cheap.
B. Desktop only; no responsive work.
C. Mobile and tablet too.
D. Not identified
X. Other (please specify)

[Answer]: A

## Q6. Are there known accessibility requirements (WCAG level, screen reader support, keyboard-only navigation)?

A. WCAG 2.1 AA basics matching the existing page: keyboard operable, visible focus, labels not color-only, adequate contrast.
B. No formal accessibility requirements.
C. Not identified
X. Other (please specify)

[Answer]: A

## Consolidated Summary Confirmation

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct