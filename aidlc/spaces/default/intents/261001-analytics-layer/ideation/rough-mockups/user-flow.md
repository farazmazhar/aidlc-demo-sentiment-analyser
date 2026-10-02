# User Flow — Analytics

## Core flow (happy path)

The confirmed flow is: open the app, go to analytics, see the default date range rendered, adjust the date range, and the view updates. [Q2]

```
        +---------------------------+
        |  Developer opens the app  |
        +-------------+-------------+
                      |
                      v
        +---------------------------+
        | Single page renders:      |
        | Analyze + History         |
        +-------------+-------------+
                      |
                      v
        +---------------------------+
        | Selects "Analytics"      |   [Q1 - new entry point]
        +-------------+-------------+
                      |
                      v
        +---------------------------+
        | Analytics view loads:     |
        | - default date range      |
        | - loading skeletons      |
        +-------------+-------------+
                      |
                      v
        +---------------------------+
        | Summary + series +        |   default range, no user
        | breakdown + top terms     |   input needed
        +-------------+-------------+
                      |
        +-------------+-------------+
        |                           |
        v                           v
  +-------------+             +----------------+
  | Adjusts the |             | Done - reads   |
  | date range  |             | the analytics  |
  +------+------+             +----------------+
         |
         v
  +----------------+
  | Range valid?  |
  +---+--------+---+
      |        |
   no  |        | yes
      v        v
  +-------------------+   +----------------+
  | Error message     |   | View updates   |
  | + "Clear range"  |   | for new range  |
  +-------------------+   +-------+--------+
                                   |
                                   v
                           +---------------+
                           | Done          |
                           +---------------+
```

## Error and recovery paths

| Condition | What the developer sees | Recovery |
|-----------|-------------------------|----------|
| Date range is malformed or `from` is after `to` | Inline message naming the problem and the expected `YYYY-MM-DD` format, announced politely | Clear the range, or correct and re-apply |
| No analyses exist in the range | Empty state with an explanation and a "Go to Analyze" action | Widen the range, or analyse/import text first |
| Analytics request fails | Error state with the reason in plain language (no raw codes or stack traces) | Retry, or adjust the range |
| Term list is empty for one polarity | `( none )` text in that list, while the other list still renders | Nothing required; widen the range to populate it |

## Data flow behind the view

```
  stored analyses (SQLite)
            |
            |  additive migration makes them addressable  [U1]
            v
  GET /v2/analytics/summary  +  GET /v2/analytics/terms
            |                              |
            +--------------+---------------+
                           |
                    both read stored rows
                    in-process, no external service
                           |
                           v
                analytics view renders
                (series, breakdown, top terms)
```

Both requests are read-only, computed in-process from stored rows, and follow the existing `/v1` JSON conventions and the single error envelope. The date-range control and every data-fetching control stay on the view; nothing is submitted automatically. [Q6]

## Consistency with the rest of the app

- The same labels, controls, and focus behaviour as the existing page; the analytics view is an entry point inside the existing single-page shell rather than a separate site. [Q1] [Q4]
- Every figure is available as text, so the view is usable with a keyboard and a screen reader. [Q6]
- Desktop-first layout, stacking in the same order on a narrow screen. [Q5]