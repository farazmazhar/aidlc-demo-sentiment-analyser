# Requirements Analysis — Clarifying Questions

> Standard depth, brownfield. The intent description is the authoritative source
> and says plainly: *"If any requirement is ambiguous, ask me before building
> rather than guessing."* Every question below is a point the description leaves
> open and that no upstream artifact settles.

## Q1 — Where do the eight affirmed practices obligations land?

**Asked and answered at the start of this stage.** Practices Discovery affirmed
eight obligations that are not among the four stated capabilities: the dependency
lockfile with hashes, the platform-neutral verification script, secret scanning, a
dependency audit, a `LICENSE`, `ruff TID` banned-api entries, the startup loopback
bind check, and the ASGI harness fix that makes R-01 reproducible.

A. All eight are requirements of this feature and ship inside it
B. Only those the analytics work touches ship here; the rest become follow-up work
C. Only the ones this feature cannot ship without; the rest become follow-up work
D. None ship here; they are team hygiene for a later scope
E. Other (please specify)

[Answer]: A. All eight are requirements of this feature and ship inside it.

## Q2 — What counts as a "significant" term?

The description requires only "reuse a simple tokenizer" with no external
services. That leaves the whole definition open, and intent-capture flagged it as
the one assumption to be pinned here. The repo has exactly one tokenizer,
`_WORD = re.compile(r"[a-z']+")`, which is underscore-private inside the offline
engine and does none of the filtering below.

A. Lowercase word tokens of 4 or more characters, minus a small fixed English stopword list
B. Same, but 3 or more characters and a larger stopword list
C. Any token of 3 or more characters, no stopword list at all
D. 4 or more characters, minus stopwords, and each term reported with its count and its share of that label's tokens
E. Other (please specify)

[Answer]: B. Lowercase word tokens of 3 or more characters, minus a larger fixed English stopword list. No stemming. The promoted public tokenizer replaces the private `_WORD` regex in the offline engine; neither module imports the other's private name.

## Q3 — How is the `from` / `to` range interpreted?

`created_at` is stored as ISO-8601 with a `Z` suffix and normalised to
`%Y-%m-%dT%H:%M:%SZ`, so a range filter is a plain string comparison. What the
parameter values mean is still unstated.

A. Calendar dates in UTC as `YYYY-MM-DD`; both ends inclusive, so `to` covers that whole day
B. Calendar dates in UTC; `from` inclusive, `to` exclusive
C. Full ISO timestamps, not dates, compared directly against `created_at`
D. Calendar dates interpreted in the browser's local time
E. Other (please specify)

[Answer]: A. UTC calendar dates written `YYYY-MM-DD`, both ends inclusive, so `to` covers that entire calendar day — a UTC day bounds `T00:00:00Z` to `T23:59:59.999999Z`.

## Q4 — What happens when only one bound is supplied?

The description shows `?from=&to=&import_id=` with both optional-looking and no
statement about a half-open range.

A. `from` alone means that day to now; `to` alone means everything up to and including that day
B. A single bound is refused with 422
C. A single bound is ignored and the full history is returned
D. A single bound falls back to a fixed default window
E. Other (please specify)

[Answer]: A. `from` alone means that calendar day through now; `to` alone means everything from the beginning of history up to and including that calendar day. Neither bound is ever silently dropped.

## Q5 — What does an empty result set look like?

The suite's strongest existing convention is "refuse, never substitute" — `None`
for an empty aggregate rather than a fabricated `0.0`. That convention has to be
applied to shares, where the denominator is zero.

A. `total` 0, every per-label count 0, `mean_confidence` null, shares null rather than 0.0, per-day array empty
B. Same, but shares reported as 0.0
C. A 404 through the error envelope
D. A 200 with an added `empty: true` flag in the payload
E. Other (please specify)

[Answer]: A. `total` 0, every per-label count 0, `mean_confidence` null, and per-label shares **null rather than 0.0** because the denominator is zero and the refuse-never-substitute convention forbids a fabricated number. The per-day series is an empty array. A 200, never a 404.

## Q6 — Does the per-day series fill gaps?

A range spanning days with no analyses either reports those days or omits them,
and the two give different shapes to the page's chart.

A. One entry per calendar day in the range, zero-filled, so the series is continuous
B. Only days that actually have rows, sparse
C. One entry per day, but the range is capped at the most recent N days
D. Sparse, plus an explicit note of the first and last day in the range
E. Other (please specify)

[Answer]: A. One entry per calendar day in the requested range, zero-filled, so the series is continuous. A day with no analyses reports total 0, all label counts 0, shares null and `mean_confidence` null — identical to the empty-result shape.

## Q7 — What does `limit` do on the terms endpoint?

The description gives the terms endpoint `?from=&to=&limit=` and asks for
"positive vs negative" lists, so the limit could apply per list or to the whole
payload.

A. Defaults to 10 and applies per list, so the response carries up to 10 positive and 10 negative terms; validated `ge=1` exactly like the existing history `limit`
B. Defaults to 10 and applies to the combined output across both lists
C. A fixed top 10 and `limit` is not exposed
D. Per list, default 10, and the payload also states the total distinct term count in range
E. Other (please specify)

[Answer]: A. Defaults to 10 and applies **per list**, so the response carries up to 10 positive and 10 negative terms. Validated `ge=1` exactly like the existing history `limit`: below 1 or non-numeric answers 422 naming `field == "query.limit"`, never a silent clamp.

## Q8 — How are terms ranked, and how are ties broken?

A. By count descending; ties broken alphabetically for a stable, testable order
B. By count descending; ties broken by the term's first appearance in the data
C. By count descending; ties broken by length, then alphabetically
D. By share of the label's tokens, then by count
E. Other (please specify)

[Answer]: A. Ordered by count descending, ties broken alphabetically — a total, stable order that can be pinned with a hand-written expected value, as the affirmed testing posture requires.

## Q9 — Does the terms endpoint accept `import_id`?

The description gives `import_id` to the summary endpoint only. The page is meant
to show both together, so a range that filters one and not the other is possible.

A. No — the terms endpoint takes only `from`, `to` and `limit`, as described
B. Yes — add `import_id` so both endpoints filter identically
C. No now, but record it as a named follow-up
D. Yes, and require it — terms are meaningless without it
E. Other (please specify)

[Answer]: B. Yes — the terms endpoint also accepts `import_id`, extending the description's `?from=&to=&limit=`, so summary and terms filter identically and the page can never show two different populations at once.

## Q10 — What is the page's default date range?

Rough Mockups left this open. It is the first thing the page shows, so it decides
what the developer sees before touching the control.

A. All history, no bounds
B. The last 30 days
C. The last 7 days
D. Since the first stored analysis
E. Other (please specify)

[Answer]: A. All history, no date bounds, so the first view shows everything stored. The date-range control narrows from there.

## Q11 — What happens on a malformed date or a bad `import_id`?

Existing boundary discipline is specific: a non-numeric `limit` answers 422 naming
`field == "query.limit"` and never a silent clamp, and a refusal carries a
row-count assertion of zero. That pattern needs extending to the new parameters.

A. 422 through the existing error envelope naming `field == "query.from"` / `"query.to"` / `"query.import_id"`, with nothing computed
B. 422 through the envelope, but with a generic message that does not name the field
C. 400 with the envelope
D. The bad parameter is ignored and the default range is used
E. Other (please specify)

[Answer]: A. 422 through the existing error envelope naming `field == "query.from"` / `"query.to"` / `"query.import_id"`, with nothing computed — extending the existing discipline that a non-numeric `limit` names its own field and is never silently clamped.

## Q12 — When neither date bound is supplied, what is the series' day range?

Q6 requires one entry per calendar day in the requested range, but Q10 makes the
page default to all history with no bounds — and an unbounded range has no days to
enumerate. Without a ruling, "all history" is not a renderable series.

A. From the **first stored analysis date through today**, inclusive
B. Today only
C. A fixed default window, such as the last 30 days
D. No series at all when the range is unbounded
E. Other (please specify)

[Answer]: A. From the first stored analysis date through today, inclusive. An empty store yields an empty series, matching the Q5 empty-result shape.

## Q13 — How is `mean_confidence` computed when some rows carry no confidence?

A mean drawn from a subset of rows, presented as if it described them all, is
exactly the kind of fabricated number the refuse-never-substitute convention
forbids.

A. Average over the rows that **have** a confidence value, and report how many rows contributed
B. Average over the rows that have a value, reporting nothing about coverage
C. `mean_confidence` is null unless **every** row in range has a value
D. Other (please specify)

[Answer]: A. Average over only the rows carrying a confidence value, with the contributing row count reported alongside so a subset mean can never be read as a whole-range mean. An empty contributor set yields null.

## Consolidated Summary Confirmation

- **The eight affirmed practices obligations all ship inside this feature** — lockfile with hashes, platform-neutral verification script, secret scanning, dependency audit, `LICENSE`, `ruff TID` banned-api entries, startup loopback bind check, and the ASGI harness fix that makes R-01 reproducible. This knowingly roughly doubles the work beyond the analytics layer itself.
- **A "significant" term is a lowercase word token of 3 or more characters, minus a fixed in-repo English stopword list.** No stemming. The tokenizer is promoted to a public module beside `sentiment.py`; the private `_WORD` regex in the offline engine is neither imported across a module boundary nor copied.
- **`from` and `to` are UTC calendar dates written `YYYY-MM-DD`, both ends inclusive** — `to` covers that entire calendar day, bounding `T00:00:00Z` to `T23:59:59.999999Z`.
- **A single bound is never dropped.** `from` alone runs from that day to now; `to` alone runs from the beginning of history through that day.
- **An empty result is a 200, never a 404.** `total` 0, every per-label count 0, `mean_confidence` null, and per-label shares **null rather than 0.0** because the denominator is zero.
- **The per-day series is continuous and zero-filled** — one entry per calendar day in the resolved range, where a day with no analyses reports the same shape as an empty result.
- **With neither bound supplied, the series spans the first stored analysis date through today inclusive.** An empty store yields an empty series.
- **`mean_confidence` averages only rows carrying a confidence value**, with the contributing row count reported alongside, so a subset mean can never be read as a whole-range mean.
- **`limit` defaults to 10 and applies per list** — up to 10 positive and 10 negative terms — validated `ge=1` exactly like the existing history `limit`.
- **Terms are ordered by count descending with ties broken alphabetically**, a total and stable order that a hand-written expected value can pin.
- **The terms endpoint also accepts `import_id`**, extending the description's `?from=&to=&limit=`, so summary and terms always filter identically and the page can never show two populations at once.
- **The page defaults to all history with no bounds**, so the first view shows everything stored and the date-range control narrows from there.
- **A malformed date or unparseable `import_id` answers 422 through the existing envelope**, naming `field == "query.from"` / `"query.to"` / `"query.import_id"` and computing nothing — never a silent clamp or a silent default.

Does this all look correct before I generate the requirements artifact?

- `Looks correct`
- `Request changes`

[Answer]: Looks correct
