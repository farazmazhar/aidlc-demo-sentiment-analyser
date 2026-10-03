"""The analytics read layer.

Single responsibility: answer the two `/v2` analytics questions — "what happened
in this range" and "which terms led" — from stored analysis rows, entirely in
process. No sentiment logic, no engine call, no HTTP client, no socket and no
credential appear anywhere in this module, and it performs **no** write, no DDL
and no access bookkeeping of any kind (BR2.7, BR2.8, NFR2, NFR3).

**The connection is received, never owned.** Every entry point takes the
connection the HTTP edge opened and never opens, closes or owns one itself
(BR6.1); connection lifetime stays wholly at `app.routes.get_connection`.

**The work is bounded, and the statement count is a function of the query shape,
not of the range.** The summary is one grouped read over the resolved range, and
the series is then grown to its final shape in memory — one entry per UTC day,
zero-filled where the grouped result has none — so neither the store's row count
nor the length of the resolved range adds a statement (BR3.4, NFR1.3, NFR9.4).

**Every value reaches a statement as a bound parameter.** There is no statement
text built from any value, including the range bounds, which travel as two ISO
timestamps with documented sentinels for "unbounded" (BR2.9, FR1.4).
(`FR1.1`-`FR1.4`, `FR2.1`-`FR2.13`, `FR3.1`-`FR3.8`)
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from app.models import (
    AnalyticsSeriesEntry,
    AnalyticsSummary,
    AnalyticsTerms,
    TermFrequencyEntry,
)
from app.sentiment import LABELS
from app.terms import significant_terms, tokenize

#: The labels that own a term list. There is no `neutral` list: a neutral row
#: contributes to neither (FR3.6, BR2.4).
TERM_LABELS: tuple[str, ...] = ("positive", "negative")

#: Entries materialised per list when the caller names no limit (FR3.3).
DEFAULT_TERM_LIMIT = 10

#: Every 4-decimal answer is rounded to this many places (FR2.7, FR2.8).
SCALE = Decimal("0.0001")

#: A stored `created_at` is always written `YYYY-MM-DDTHH:MM:SSZ` with UTC
#: calendar dates in `YYYY-MM-DD` form, so a bound that sorts below every one of
#: them is the empty string and a bound that sorts above every one of them is
#: `~` (0x7E), which is greater than every digit a date can start with. The two
#: sentinels let one statement serve both the bounded and the unbounded case with
#: every bound still travelling as a parameter (BR2.9).
_LOWER_UNBOUNDED = ""
_UPPER_UNBOUNDED = "~"

#: A range bound is a UTC calendar day written exactly this way; anything else is
#: refused rather than guessed at (BR1.1, BR4.2).
_DATE_PATTERN = re.compile(r"\A\d{4}-\d{2}-\d{2}\Z")

#: The shared head of the summary read: per UTC day and per label, the row count
#: and the confidence sum. Both aggregates come back in the same pass, so the
#: whole summary — totals, mix, mean, per-day buckets — is derived from one
#: statement (BR2.1, BR2.3, BR3.4).
_SUMMARY_HEAD = """
SELECT substr(created_at, 1, 10) AS day,
       label,
       COUNT(*)              AS row_count,
       SUM(confidence)       AS confidence_sum
FROM analyses
WHERE created_at >= ? AND created_at < ?
"""

#: The grouped read, and the same read narrowed to one import's rows. Two
#: literals composed from `SUMMARY_HEAD` rather than one statement built at call
#: time, so the `import_id` index stays usable and no value is ever concatenated
#: into statement text (BR2.9).
_SUMMARY_GROUPED = f"{_SUMMARY_HEAD}\nGROUP BY day, label\nORDER BY day"

_SUMMARY_GROUPED_BY_IMPORT = (
    f"{_SUMMARY_HEAD}\n  AND import_id = ?\nGROUP BY day, label\nORDER BY day"
)

#: The one read the term lists are built from: the text and label of the rows in
#: range. Term extraction, counting and ranking are all in process (FR3.3, FR3.5).
_TERM_HEAD = """
SELECT label, text
FROM analyses
WHERE created_at >= ? AND created_at < ?
"""

_TERM_TEXT = _TERM_HEAD
_TERM_TEXT_BY_IMPORT = f"{_TERM_HEAD}\n  AND import_id = ?"


class RangeError(ValueError):
    """A range bound that cannot be read, or a range that runs backwards.

    The message names the offending parameter(s) itself, because the error
    envelope has no `field` member (`BR4.1`, `BR4.3`).
    """


@dataclass(frozen=True)
class ResolvedRange:
    """The resolved day bounds of a request.

    `None` on either end means "unbounded in that direction" and is never
    dropped: a caller that supplied only `from` keeps an unbounded-below range
    that still starts the series at `from` (`BR1.2`). `start` is inclusive; `end`
    is inclusive and is turned into an exclusive upper timestamp when it becomes
    a bound parameter, so a row at `23:59:59Z` on the `to` day is in range
    (`BR1.1`).
    """

    start: date | None = None
    end: date | None = None


def resolve_range(from_bound: str | None, to_bound: str | None) -> ResolvedRange:
    """Resolve the inclusive UTC day bounds both analytics endpoints share.

    A bound that cannot be read as a UTC calendar date is refused by name before
    anything is computed; a range whose `from` is later than its `to` is refused
    by naming **both** bounds (`BR1.1`, `BR1.4`, `BR4.2`, `BR4.3`). Both endpoints
    call this one function, which is what keeps their two populations identical
    (`BR1.5`).
    """
    start = _parse_bound(from_bound, "query.from")
    end = _parse_bound(to_bound, "query.to")
    if start is not None and end is not None and start > end:
        raise RangeError("query.from and query.to: 'from' must not be a later UTC day than 'to'.")
    return ResolvedRange(start=start, end=end)


def read_summary(
    connection: sqlite3.Connection,
    resolved: ResolvedRange,
    import_id: str | None = None,
    today: date | None = None,
) -> AnalyticsSummary:
    """Aggregate the rows of `resolved` (optionally one import's) into a summary.

    One grouped statement carries the per-day and per-label counts and confidence
    sums; everything else — the range totals, the label mix, the shares, the mean
    and the zero-filled series — is computed in process from those rows, so the
    statement count does not grow with the number of days in the range
    (`BR3.4`).

    `today` is the seam the unbounded case resolves against; it defaults to the
    current UTC day so a caller does not have to supply it, and tests pin it
    (`BR1.3`).
    """
    statement = _SUMMARY_GROUPED_BY_IMPORT if import_id is not None else _SUMMARY_GROUPED
    parameters = _range_parameters(resolved)
    if import_id is not None:
        parameters = (*parameters, import_id)

    rows = connection.execute(statement, parameters).fetchall()

    per_day: dict[str, dict[str, int]] = {}
    per_day_confidence: dict[str, float] = {}
    counts = dict.fromkeys(LABELS, 0)
    confidence_total = 0.0
    for row in rows:
        day = str(row["day"])
        label = str(row["label"])
        bucket = per_day.setdefault(day, dict.fromkeys(LABELS, 0))
        bucket[label] += int(row["row_count"])
        day_confidence = float(row["confidence_sum"])
        per_day_confidence[day] = per_day_confidence.get(day, 0.0) + day_confidence
        counts[label] += int(row["row_count"])
        confidence_total += day_confidence

    total = sum(counts.values())
    shares = _shares(counts, total)
    mean = _round_half_up(confidence_total / total) if total else None

    return AnalyticsSummary(
        total=total,
        counts=counts,
        shares=shares,
        mean_confidence=mean,
        mean_confidence_row_count=total,
        series=_build_series(per_day, per_day_confidence, resolved, import_id, today),
    )


def read_terms(
    connection: sqlite3.Connection,
    resolved: ResolvedRange,
    import_id: str | None = None,
    limit: int = DEFAULT_TERM_LIMIT,
) -> AnalyticsTerms:
    """Rank the significant terms of the rows in `resolved`, per label.

    The rows are read once; tokenising, filtering, counting and ranking all happen
    in process, and the payload is bounded by `limit` rather than by the size of
    the store (`FR3.3`, `NFR1.2`). Only rows carrying a label in `TERM_LABELS`
    contribute, so a neutral row reaches neither list (`BR2.4`). `limit` is
    honoured, never clamped: an oversized limit returns every available term
    (`BR2.6`).
    """
    statement = _TERM_TEXT_BY_IMPORT if import_id is not None else _TERM_TEXT
    parameters = _range_parameters(resolved)
    if import_id is not None:
        parameters = (*parameters, import_id)

    rows = connection.execute(statement, parameters).fetchall()

    frequencies: dict[str, Counter[str]] = {label: Counter() for label in TERM_LABELS}
    for row in rows:
        label = str(row["label"])
        if label in frequencies:
            frequencies[label].update(significant_terms(tokenize(str(row["text"]))))

    return AnalyticsTerms(
        positive=_rank(frequencies["positive"], limit),
        negative=_rank(frequencies["negative"], limit),
    )


# -- range bounds as bound parameters ---------------------------------------


def _parse_bound(raw: str | None, field: str) -> date | None:
    """Read one bound as a UTC calendar day, refusing anything unreadable by name."""
    if raw is None:
        return None
    if not _DATE_PATTERN.match(raw):
        raise RangeError(f"{field}: expected a UTC calendar date written YYYY-MM-DD.")
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise RangeError(f"{field}: {raw!r} is not a real UTC calendar date.") from exc


def _range_parameters(resolved: ResolvedRange) -> tuple[str, str]:
    """The two bound parameters for `resolved`, half-open at the upper end.

    The upper bound is the **day after** `to` at `T00:00:00Z`, which is what makes
    the bound inclusive of the whole of the `to` day: a row written at
    `23:59:59Z` on that day sorts below it and the following day does not
    (`BR1.1`).
    """
    lower = (
        f"{resolved.start.isoformat()}T00:00:00Z"
        if resolved.start is not None
        else _LOWER_UNBOUNDED
    )
    upper = (
        f"{(resolved.end + timedelta(days=1)).isoformat()}T00:00:00Z"
        if resolved.end is not None
        else _UPPER_UNBOUNDED
    )
    return (lower, upper)


# -- in-process aggregation ---------------------------------------------------


def _shares(counts: dict[str, int], total: int) -> dict[str, float | None]:
    """Each label's four-decimal share of `total`, or `null` when `total` is 0.

    Every label of the closed vocabulary is present. A label with no rows still
    carries a share of `0.0` when the denominator is non-zero — the denominator,
    not the numerator, is what decides whether there is an answer (`BR2.2`).
    """
    if total == 0:
        return dict.fromkeys(counts, None)
    return {label: _round_half_up(count / total) for label, count in counts.items()}


def _round_half_up(value: float) -> float:
    """Round `value` to four decimals, ties away from zero.

    Half-up is the ruled tie rule, so `0.28125` becomes `0.2813` and not the
    half-even `0.2812`. `Decimal` is fed the shortest decimal string for the float
    rather than the binary value, so the rounding sees the number a reader would
    write down (FR2.7, FR2.8, R-06).
    """
    return float(Decimal(str(value)).quantize(SCALE, rounding=ROUND_HALF_UP))


def _build_series(
    per_day: dict[str, dict[str, int]],
    per_day_confidence: dict[str, float],
    resolved: ResolvedRange,
    import_id: str | None,
    today: date | None,
) -> list[AnalyticsSeriesEntry]:
    """Grow the grouped result into one entry per UTC day of the resolved range.

    A range that matched no row yields an **empty** series — never a zero-filled
    span, never a 404 (`BR3.3`). A range that matched at least one row yields one
    entry per day from the resolved range's first day to its last, ascending and
    continuous, with every absent day zero-filled whether it is an internal gap
    or an edge day (`BR3.1`, `BR3.2`).

    The resolved range's edges follow `BR1.3`: a supplied bound wins; with no
    `to`, an import's own rows end the range while a store-wide read runs through
    today inclusive; with no `from`, the range starts at the earliest day the read
    saw.
    """
    if not per_day:
        return []

    current_day = datetime.now(UTC).date() if today is None else today
    days = sorted(per_day)
    first = resolved.start if resolved.start is not None else date.fromisoformat(days[0])
    last = resolved.end
    if last is None:
        last = (
            date.fromisoformat(days[-1])
            if import_id is not None
            else max(current_day, date.fromisoformat(days[-1]))
        )
    # A range whose last day precedes its first simply contributes no entry: the
    # walk below never runs, which is the empty series of BR3.3 rather than an
    # error.
    series: list[AnalyticsSeriesEntry] = []
    day = first
    while day <= last:
        key = day.isoformat()
        counts = per_day.get(key)
        if counts is None:
            series.append(_zero_entry(key))
        else:
            day_total = sum(counts.values())
            series.append(
                AnalyticsSeriesEntry(
                    date=key,
                    total=day_total,
                    counts=dict(counts),
                    shares=_shares(counts, day_total),
                    mean_confidence=_round_half_up(per_day_confidence[key] / day_total),
                    mean_confidence_row_count=day_total,
                )
            )
        day += timedelta(days=1)
    return series


def _zero_entry(day: str) -> AnalyticsSeriesEntry:
    """The entry for a day inside a matched range that held no rows.

    All counts 0, every share `null`, the mean `null` and the row count `0` —
    which is that day's total. A zero denominator has no answer and the project
    refuses to state a fabricated `0.0` for it (`BR3.2`).
    """
    return AnalyticsSeriesEntry(
        date=day,
        total=0,
        counts=dict.fromkeys(LABELS, 0),
        shares=dict.fromkeys(LABELS, None),
        mean_confidence=None,
        mean_confidence_row_count=0,
    )


def _rank(frequencies: Counter[str], limit: int) -> list[TermFrequencyEntry]:
    """Materialise at most `limit` terms, count descending then alphabetical.

    The order is total and stable, so a hand-written expected value can pin it
    (`BR2.5`). An oversized `limit` returns every available term rather than a
    padded list (`BR2.6`).
    """
    ordered = sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))
    return [TermFrequencyEntry(term=term, count=count) for term, count in ordered[:limit]]
