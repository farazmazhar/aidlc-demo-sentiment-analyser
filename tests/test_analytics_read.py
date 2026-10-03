"""Repository / data access: the analytics read module against real SQLite.

The lower-level tests for `app.analytics`, written after the behaviour exists.
Every aggregate asserted here was computed by hand before the assertion was
written, because the suite's whole count says nothing about whether a date bucket,
an average or an empty range is right: there was no `AVG(`, no `GROUP BY` and no
`strftime(` anywhere in this repository before this module.
(`FR1.1`-`FR1.4`, `FR2.1`-`FR2.13`, `FR3.1`-`FR3.8`, `NFR1`, `NFR9`, `AC8.1.1`-`AC8.1.4`)
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.analytics import (
    DEFAULT_TERM_LIMIT,
    RangeError,
    read_summary,
    read_terms,
    resolve_range,
)
from app.db import connect, init_db
from app.sentiment import LABELS

#: The budget both endpoints answer inside, measured over the 10,000-row /
#: 365-day fixture (NFR1.1, NFR1.2, BR3.6).
BUDGET_MS = 200

#: The span the performance fixture is pinned to, so the series length — and
#: therefore the measured work — is a fixed quantity rather than an artefact of
#: the day the suite happens to run (NFR1.4).
FIXTURE_ROWS = 10_000
FIXTURE_DAYS = 365

_PROBABILITIES = '{"positive": 0.9, "negative": 0.05, "neutral": 0.05}'

_INSERT_ROW = (
    "INSERT INTO analyses "
    "(text, label, probabilities, confidence, model, provider, created_at, import_id) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)


def _today() -> str:
    """The current UTC calendar day, written `YYYY-MM-DD`."""
    return datetime.now(UTC).date().isoformat()


def _days_ago(days: int) -> str:
    """The UTC calendar day `days` before today, written `YYYY-MM-DD`."""
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


def _store(tmp_path, rows) -> Path:
    """Write a real SQLite file holding `rows`, and return its path.

    `rows` are `(text, label, confidence, created_at, import_id)` tuples. The file
    is created through the application's own schema step, so every assertion reads
    back exactly the schema the application ships.
    """
    db_path = tmp_path / "sentiment.db"
    init_db(db_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            _INSERT_ROW,
            [
                (
                    text,
                    label,
                    _PROBABILITIES,
                    confidence,
                    "dummy-keyword-v1",
                    "offline",
                    created_at,
                    import_id,
                )
                for text, label, confidence, created_at, import_id in rows
            ],
        )
        connection.commit()
    finally:
        connection.close()
    return db_path


def _open(db_path) -> sqlite3.Connection:
    return connect(db_path)


# -- range resolution ---------------------------------------------------------


def test_a_range_with_both_bounds_resolves_to_inclusive_utc_days():
    """BR1.1: the resolved range is every UTC day from `from` through `to`."""
    resolved = resolve_range("2026-01-01", "2026-01-31")

    assert resolved.start.isoformat() == "2026-01-01"
    assert resolved.end.isoformat() == "2026-01-31"


@pytest.mark.parametrize(
    ("raw", "field"),
    [
        ("not-a-date", "query.from"),
        ("2026-1-1", "query.from"),
        ("20260101", "query.from"),
        ("2026-13-01", "query.from"),
        ("2026-02-30", "query.from"),
        ("2026-01-01T00:00:00Z", "query.from"),
        (" ", "query.to"),
        ("01-01-2026", "query.to"),
        ("2026-99-99", "query.to"),
    ],
)
def test_an_unreadable_bound_is_refused_by_name(raw, field):
    """BR4.1, BR4.2: the message names the offending parameter, not a `field` member."""
    with pytest.raises(RangeError) as caught:
        resolve_range(raw, None) if field == "query.from" else resolve_range(None, raw)

    assert field in str(caught.value)


def test_an_inverted_range_is_refused_naming_both_bounds():
    """BR1.4, BR4.3: one refusal naming `query.from` *and* `query.to`."""
    with pytest.raises(RangeError) as caught:
        resolve_range("2026-01-04", "2026-01-01")

    message = str(caught.value)
    assert "query.from" in message
    assert "query.to" in message


def test_a_single_bound_is_kept_as_a_half_open_span():
    """BR1.2: one supplied bound never becomes an unbounded range."""
    only_from = resolve_range("2026-01-01", None)
    assert only_from.start.isoformat() == "2026-01-01"
    assert only_from.end is None

    only_to = resolve_range(None, "2026-01-31")
    assert only_to.start is None
    assert only_to.end.isoformat() == "2026-01-31"

    neither = resolve_range(None, None)
    assert neither.start is None
    assert neither.end is None


# -- the aggregates -----------------------------------------------------------


def test_the_summary_aggregates_are_the_hand_computed_values(tmp_path):
    """BR2.1-BR2.3, BR3.1, BR3.2: the whole six-field answer, computed by hand.

    Rows: two on 2026-01-01, none on 2026-01-02, one on 2026-01-03, one on
    2026-01-04. So `total` is 4; the mix is 2 positive, 1 negative, 1 neutral; the
    shares are 2/4 = 0.5, 1/4 = 0.25 and 1/4 = 0.25; the mean over **all four** rows
    is (0.90 + 0.60 + 0.30 + 0.50) / 4 = 0.575 with a row count of 4.
    """
    db_path = _store(
        tmp_path,
        (
            ("alpha", "positive", 0.90, "2026-01-01T10:00:00Z", None),
            ("beta", "negative", 0.60, "2026-01-01T23:59:59Z", None),
            ("gamma", "positive", 0.30, "2026-01-03T12:00:00Z", None),
            ("delta", "neutral", 0.50, "2026-01-04T00:00:00Z", None),
        ),
    )
    connection = _open(db_path)
    try:
        summary = read_summary(connection, resolve_range("2026-01-01", "2026-01-04"))
    finally:
        connection.close()

    assert summary.total == 4
    assert summary.counts == {"positive": 2, "negative": 1, "neutral": 1}
    assert summary.shares == {"positive": 0.5, "negative": 0.25, "neutral": 0.25}
    assert summary.mean_confidence == 0.575
    assert summary.mean_confidence_row_count == 4

    assert [entry.date for entry in summary.series] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
    ]
    gap = summary.series[1]
    assert gap.total == 0
    assert gap.counts == dict.fromkeys(LABELS, 0)
    assert gap.shares == dict.fromkeys(LABELS, None)
    assert gap.mean_confidence is None
    assert gap.mean_confidence_row_count == 0
    first = summary.series[0]
    assert first.mean_confidence == 0.75
    # A label with no rows still has a share: the denominator is the day's total.
    assert first.shares == {"positive": 0.5, "negative": 0.5, "neutral": 0.0}


def test_a_share_and_a_mean_tie_round_half_up_not_half_even(tmp_path):
    """FR2.7, FR2.8, R-06: 36/128 = 0.28125 rounds to 0.2813, not 0.2812.

    Half-even would give 0.2812 here, so this dataset pins the ruled tie rule: 36
    rows at confidence 1.0 and 92 at 0.0 make both the positive share and the mean
    land exactly on a four-decimal tie.
    """
    rows = [("great", "positive", 1.0, "2026-01-01T00:00:00Z", None)] * 36
    rows += [("awful", "negative", 0.0, "2026-01-01T00:00:00Z", None)] * 92
    db_path = _store(tmp_path, rows)
    connection = _open(db_path)
    try:
        summary = read_summary(connection, resolve_range("2026-01-01", "2026-01-01"))
    finally:
        connection.close()

    assert summary.total == 128
    assert summary.shares["positive"] == 0.2813
    assert summary.mean_confidence == 0.2813


def test_an_unbounded_read_runs_from_the_earliest_stored_day_through_today(tmp_path):
    """BR1.3: with neither bound, the span is the earliest stored day..today."""
    db_path = _store(
        tmp_path,
        (
            ("earlier", "positive", 0.5, f"{_days_ago(2)}T08:00:00Z", None),
            ("later", "negative", 0.5, f"{_today()}T08:00:00Z", None),
        ),
    )
    connection = _open(db_path)
    try:
        summary = read_summary(connection, resolve_range(None, None))
    finally:
        connection.close()

    assert [entry.date for entry in summary.series] == [_days_ago(2), _days_ago(1), _today()]
    assert summary.series[1].total == 0
    assert summary.total == 2


def test_a_matched_import_spans_its_own_rows_and_an_unmatched_one_is_empty(tmp_path):
    """BR1.3, BR4.4: an import's span is its own rows; an unmatched id is empty."""
    db_path = _store(
        tmp_path,
        (
            ("kept", "positive", 0.5, "2026-01-03T00:00:00Z", "imp-1"),
            ("also kept", "negative", 0.5, "2026-01-04T00:00:00Z", "imp-1"),
            ("loose", "neutral", 0.5, "2026-01-05T00:00:00Z", None),
        ),
    )
    connection = _open(db_path)
    try:
        matched = read_summary(connection, resolve_range(None, None), import_id="imp-1")
        unmatched = read_summary(connection, resolve_range(None, None), import_id="absent")
    finally:
        connection.close()

    assert [entry.date for entry in matched.series] == ["2026-01-03", "2026-01-04"]
    assert matched.total == 2
    assert unmatched.total == 0
    assert unmatched.series == []
    assert unmatched.shares == dict.fromkeys(LABELS, None)
    assert unmatched.mean_confidence is None


def test_a_row_at_the_end_of_the_to_day_is_in_range_and_the_next_day_is_not(tmp_path):
    """BR1.1: the upper bound is the day *after* `to` at midnight."""
    db_path = _store(
        tmp_path,
        (
            ("last second", "positive", 0.5, "2026-01-03T23:59:59Z", None),
            ("next midnight", "positive", 0.5, "2026-01-04T00:00:00Z", None),
        ),
    )
    connection = _open(db_path)
    try:
        summary = read_summary(connection, resolve_range("2026-01-01", "2026-01-03"))
    finally:
        connection.close()

    assert summary.total == 1
    assert [entry.date for entry in summary.series] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
    ]


# -- term ranking -------------------------------------------------------------


def test_terms_rank_by_count_then_alphabetically_and_exclude_neutral_rows(tmp_path):
    """BR2.4, BR2.5: count descending, ties alphabetical, neutral contributes to neither."""
    db_path = _store(
        tmp_path,
        (
            ("wonderful and delightful", "positive", 0.9, "2026-01-01T09:00:00Z", None),
            ("wonderful and great", "positive", 0.8, "2026-01-01T10:00:00Z", None),
            ("awful and terrible", "negative", 0.7, "2026-01-02T09:00:00Z", None),
            ("ordinary and plain", "neutral", 0.5, "2026-01-02T11:00:00Z", None),
        ),
    )
    connection = _open(db_path)
    try:
        terms = read_terms(connection, resolve_range("2026-01-01", "2026-01-02"))
    finally:
        connection.close()

    assert [(entry.term, entry.count) for entry in terms.positive] == [
        ("wonderful", 2),
        ("delightful", 1),
        ("great", 1),
    ]
    assert [(entry.term, entry.count) for entry in terms.negative] == [
        ("awful", 1),
        ("terrible", 1),
    ]


def test_the_default_limit_is_ten_per_list_and_an_oversized_one_is_honoured(tmp_path):
    """BR2.6: the default is `DEFAULT_TERM_LIMIT`; an oversized limit is not clamped."""
    # Letter-only terms: a digit is a token boundary, so `term01` would tokenise to
    # `term` and there would be nothing to rank (FR4.2).
    vocabulary = (
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
        "india",
        "juliet",
        "kilo",
        "lima",
        "mike",
        "november",
        "oscar",
    )
    db_path = _store(
        tmp_path,
        [(" ".join(vocabulary), "positive", 0.5, "2026-01-01T00:00:00Z", None)],
    )
    connection = _open(db_path)
    try:
        defaulted = read_terms(connection, resolve_range(None, None))
        oversized = read_terms(connection, resolve_range(None, None), limit=999)
        narrowed = read_terms(connection, resolve_range(None, None), limit=2)
    finally:
        connection.close()

    assert DEFAULT_TERM_LIMIT == 10
    assert len(defaulted.positive) == 10
    # Every available term comes back when the limit exceeds what exists.
    assert len(oversized.positive) == len(vocabulary)
    # Alphabetical tie-break, since all fifteen counts are 1.
    assert [(entry.term, entry.count) for entry in narrowed.positive] == [
        ("alpha", 1),
        ("bravo", 1),
    ]


def test_a_label_with_no_rows_yields_an_empty_list_and_not_none(tmp_path):
    """BR2.4: empty, never `null`, never padded."""
    db_path = _store(
        tmp_path,
        (("wonderful", "positive", 0.9, "2026-01-01T00:00:00Z", None),),
    )
    connection = _open(db_path)
    try:
        terms = read_terms(connection, resolve_range("2026-01-01", "2026-01-02"))
        empty = read_terms(connection, resolve_range("2026-03-01", "2026-03-02"))
    finally:
        connection.close()

    assert [entry.term for entry in terms.negative] == []
    assert empty.to_dict() == {"positive": [], "negative": []}


# -- bounded work -------------------------------------------------------------


def _trace(connection: sqlite3.Connection, resolved, today: str) -> list[str]:
    """Every statement the summary executes over `resolved`, with `today` pinned."""
    traced: list[str] = []
    connection.set_trace_callback(traced.append)
    try:
        read_summary(connection, resolved, today=datetime.fromisoformat(today).date())
    finally:
        connection.set_trace_callback(None)
    return [statement.strip() for statement in traced if "analyses" in statement]


def _performance_store(tmp_path) -> Path:
    """The pinned fixture: 10,000 analyses over exactly 365 distinct UTC days."""
    db_path = tmp_path / "performance.db"
    init_db(db_path)
    start = datetime.now(UTC).date() - timedelta(days=FIXTURE_DAYS - 1)
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            _INSERT_ROW,
            [
                (
                    f"a stored analysis number {index}",
                    LABELS[index % 3],
                    _PROBABILITIES,
                    (index % 100) / 100.0,
                    "dummy-keyword-v1",
                    "offline",
                    f"{(start + timedelta(days=index % FIXTURE_DAYS)).isoformat()}T12:00:00Z",
                    None,
                )
                for index in range(FIXTURE_ROWS)
            ],
        )
        connection.commit()
    finally:
        connection.close()
    return db_path


def test_the_statement_count_does_not_grow_with_the_number_of_days(tmp_path):
    """BR3.4, NFR1.3, AC8.1.2: the count is a function of the query shape, not the range.

    The same endpoint is traced over a 7-day range and over a 365-day range. The
    grouped read is one statement either way, which is the observable form of "no
    query per day": the series is grown in memory, so widening the range changes the
    response and not the number of statements the store sees.
    """
    db_path = _performance_store(tmp_path)
    today = _today()
    connection = _open(db_path)
    try:
        narrow = _trace(connection, resolve_range(_days_ago(6), _days_ago(0)), today)
        wide = _trace(connection, resolve_range(_days_ago(364), _days_ago(0)), today)
    finally:
        connection.close()

    assert len(narrow) == len(wide) == 1
    assert "GROUP BY" in wide[0]


def test_the_unbounded_series_length_is_the_fixture_span_not_the_row_count(tmp_path):
    """NFR1.4, AC8.1.2, BR3.1: 365 entries over 10,000 rows."""
    db_path = _performance_store(tmp_path)
    connection = _open(db_path)
    try:
        summary = read_summary(connection, resolve_range(None, None))
    finally:
        connection.close()

    assert summary.total == FIXTURE_ROWS
    assert len(summary.series) == FIXTURE_DAYS
    assert summary.series[0].date == _days_ago(FIXTURE_DAYS - 1)
    assert summary.series[-1].date == _today()
    assert sum(entry.total for entry in summary.series) == FIXTURE_ROWS


#: The timing scenario, run as a **separate interpreter with no pytest and no
#: coverage plugin**: `--cov` inflates wall time, so a budget measured inside the
#: instrumented suite describes the instrument rather than the application
#: (NFR1.2, AC8.1.4, BR3.6). Both endpoints are exercised end to end through the
#: real ASGI application over the pinned 10,000-row / 365-day fixture.
_TIMING_SCENARIO = """
import json, sqlite3, sys, time
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, {root!r})
from app.config import Settings
from app.main import create_app
from tests.conftest import application_started, asgi_request

tmp = Path(sys.argv[1])
today = datetime.now(UTC).date()
start = today - timedelta(days={days} - 1)
db_path = tmp / "sentiment.db"
app = create_app(Settings(
    mode="offline", api_key=None, db_path=db_path, config_path=tmp / "config.local.toml"
))
asgi_request(app, "GET", "/v1/health")   # real startup: creates and indexes the file

connection = sqlite3.connect(db_path)
try:
    connection.executemany(
        "INSERT INTO analyses (text, label, probabilities, confidence, model, provider,"
        " created_at, import_id) VALUES (?,?,?,?,?,?,?,?)",
        [
            (
                "a stored analysis about wonderful and dreadful and ordinary things",
                ("positive", "negative", "neutral")[index % 3],
                '{{"positive": 0.9, "negative": 0.05, "neutral": 0.05}}',
                (index % 100) / 100.0,
                "dummy-keyword-v1",
                "offline",
                f"{{(start + timedelta(days=index % {days})).isoformat()}}T12:00:00Z",
                None,
            )
            for index in range({rows})
        ],
    )
    connection.commit()
finally:
    connection.close()

with application_started(app):
    import asyncio
    from tests.conftest import _serve
    measurements = {{}}
    for label, path in (
        ("summary", "/v2/analytics/summary"),
        ("terms", "/v2/analytics/terms"),
    ):
        started = time.perf_counter()
        response = asyncio.run(_serve(app, "GET", path, "", b"", None))
        measurements[label] = ((time.perf_counter() - started) * 1000.0, response.status_code)
    unbounded = asyncio.run(_serve(app, "GET", "/v2/analytics/summary", "", b"", None))
    measurements["series_length"] = (0.0, len(unbounded.body["series"]))

print(json.dumps(measurements))
"""


def test_each_analytics_endpoint_answers_inside_the_budget(tmp_path):
    """NFR1.1, NFR1.2, AC8.1.1, AC8.1.3, AC8.1.4: both endpoints under 200 ms.

    Measured in a separate interpreter with no pytest and therefore no coverage
    instrumentation, over the pinned 10,000-row / 365-day fixture. The measurement
    asserts three things at once: the summary and terms endpoints both answer
    inside the budget, both answer `200`, and the unbounded summary's series length
    is the fixture's span rather than the store's row count.
    """
    scenario = _TIMING_SCENARIO.format(
        root=str(Path(__file__).parent.parent), rows=FIXTURE_ROWS, days=FIXTURE_DAYS
    )
    completed = subprocess.run(
        [sys.executable, "-c", scenario, str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(Path(__file__).parent.parent),
    )

    assert completed.returncode == 0, completed.stderr
    measured = json.loads(completed.stdout.strip().splitlines()[-1])

    summary_ms, summary_status = measured["summary"]
    terms_ms, terms_status = measured["terms"]
    assert summary_status == 200
    assert terms_status == 200
    assert summary_ms < BUDGET_MS, f"summary took {summary_ms:.1f} ms"
    assert terms_ms < BUDGET_MS, f"terms took {terms_ms:.1f} ms"
    assert measured["series_length"][1] == FIXTURE_DAYS
