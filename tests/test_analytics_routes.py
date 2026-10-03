"""API / endpoint: the `/v2` analytics surface over real storage.

These are the acceptance tests for the `/v2` contract, written against the
requirement rather than against the implementation: each one states the behaviour
the contract names and asserts it through the real ASGI application, so routing,
validation, handler, read module and real SQLite are all exercised. Nothing here
reads a value back out of a double; the only substitution is at the storage seam,
where a hand-written class stands in for the driver.
(`BR1.1`-`BR1.5`, `BR2.1`-`BR2.8`, `BR3.1`-`BR3.5`, `BR4.1`-`BR4.5`,
`AC2.1.1`-`AC2.4.5`, `AC3.1.1`-`AC3.1.3`, `AC4.1.1`, `AC8.4.1`)
"""

from __future__ import annotations

import socket
import sqlite3
import threading
from datetime import UTC, datetime, timedelta

import pytest

from app import analytics
from app.db import init_db
from app.main import create_app
from tests.conftest import asgi_request, concurrent_requests


def _today() -> str:
    """The current UTC calendar day, written `YYYY-MM-DD`.

    Pinned relative to now rather than to a fixed literal so the unbounded-range
    assertions (`BR1.3`) describe a span whose last day really is today.
    """
    return datetime.now(UTC).date().isoformat()


def _days_ago(days: int) -> str:
    """The UTC calendar day `days` before today, written `YYYY-MM-DD`."""
    return (datetime.now(UTC).date() - timedelta(days=days)).isoformat()


#: The summary payload is exactly these six fields; `resolved_range` is an
#: in-process value and is deliberately absent from the wire (`FR2.3`, contract §7).
SUMMARY_FIELDS = {
    "total",
    "counts",
    "shares",
    "mean_confidence",
    "mean_confidence_row_count",
    "series",
}

#: Every series entry carries all six of its fields, none omitted when the value
#: is zero or null (`BR3.5`).
SERIES_ENTRY_FIELDS = {
    "date",
    "total",
    "counts",
    "shares",
    "mean_confidence",
    "mean_confidence_row_count",
}

#: The terms payload is exactly two lists; there is no `neutral` list (`FR3.6`).
TERMS_FIELDS = {"positive", "negative"}

#: One ranked term entry carries a term and its count and nothing else (`BR2.5`).
TERM_ENTRY_FIELDS = {"term", "count"}

#: The frozen error envelope: exactly these two keys, at the top level, with no
#: `field` member and no `errors`/`details` array (`BR4.1`).
ENVELOPE_FIELDS = {"code", "message"}

#: `created_at` is second-precision UTC ISO 8601 ending in `Z` (`BR3.2`).
_JANUARY_PROBABILITIES = '{"positive": 0.9, "negative": 0.05, "neutral": 0.05}'

_INSERT_ROW = (
    "INSERT INTO analyses "
    "(text, label, probabilities, confidence, model, provider, created_at, import_id) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)


#: The `app` fixture is defined once per module; this one wires a real
#: application to the test's temporary store.
@pytest.fixture
def app(tmp_settings):
    """A real application wired to this test's temporary database."""
    return create_app(tmp_settings)


def _bring_up(app, tmp_settings) -> None:
    """Run real startup so the store exists, then return its path."""
    assert asgi_request(app, "GET", "/v1/health").status_code == 200


def _seed(db_path, rows) -> None:
    """Write analysis rows straight into the store the application serves."""
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            _INSERT_ROW,
            [
                (
                    text,
                    label,
                    _JANUARY_PROBABILITIES,
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


#: Four rows spanning four UTC calendar days, one of them absent. The aggregate
#: values are pinned by hand below rather than read back out of the module.
JANUARY_ROWS = (
    ("alpha", "positive", 0.90, "2026-01-01T10:00:00Z", None),
    ("beta", "negative", 0.60, "2026-01-01T23:59:59Z", None),
    ("gamma", "positive", 0.30, "2026-01-03T12:00:00Z", "imp-1"),
    ("delta", "neutral", 0.50, "2026-01-04T00:00:00Z", "imp-1"),
)

#: Rows whose text pins the term ranking: two positive rows share `wonderful`,
#: and the two negative rows share `awful`. `and` is a stopword, so it must not
#: appear in any list.
TERM_ROWS = (
    ("wonderful and delightful", "positive", 0.90, "2026-01-01T09:00:00Z", None),
    ("wonderful and great", "positive", 0.80, "2026-01-01T10:00:00Z", None),
    ("awful and terrible", "negative", 0.70, "2026-01-02T09:00:00Z", "imp-a"),
    ("awful and bad", "negative", 0.60, "2026-01-02T10:00:00Z", "imp-a"),
    ("ordinary and plain", "neutral", 0.50, "2026-01-02T11:00:00Z", None),
)


# -- Step 2: the summary endpoint --------------------------------------------


def test_summary_over_a_bounded_range_reports_the_hand_pinned_aggregates(app, tmp_settings):
    """`BR2.1`-`BR2.3`, `BR3.1`: totals, label mix, mean and one entry per day.

    Rows: two on 2026-01-01, none on 2026-01-02, one on 2026-01-03, one on
    2026-01-04. So `total` is 4, the mix is 2/1/1, the mean is
    (0.90 + 0.60 + 0.30 + 0.50) / 4 = 0.575, and the series runs 2026-01-01 to
    2026-01-04 inclusive with 2026-01-02 zero-filled.
    """
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    response = asgi_request(
        app, "GET", "/v2/analytics/summary", query="from=2026-01-01&to=2026-01-04"
    )

    assert response.status_code == 200
    body = response.body
    assert set(body) == SUMMARY_FIELDS
    assert "resolved_range" not in body

    assert body["total"] == 4
    assert body["counts"] == {"positive": 2, "negative": 1, "neutral": 1}
    assert body["shares"] == {"positive": 0.5, "negative": 0.25, "neutral": 0.25}
    assert body["mean_confidence"] == 0.575
    assert body["mean_confidence_row_count"] == 4

    series = body["series"]
    assert [entry["date"] for entry in series] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
    ]
    for entry in series:
        assert set(entry) == SERIES_ENTRY_FIELDS

    first = series[0]
    assert first["total"] == 2
    assert first["counts"] == {"positive": 1, "negative": 1, "neutral": 0}
    # A label with no rows still carries a share: the denominator is the day's
    # total, which is 2, not 0 (`BR2.2`).
    assert first["shares"] == {"positive": 0.5, "negative": 0.5, "neutral": 0.0}
    assert first["mean_confidence"] == 0.75
    assert first["mean_confidence_row_count"] == 2


def test_a_day_with_no_rows_inside_a_matched_range_is_zero_filled(app, tmp_settings):
    """`BR3.2`: the gap day reports zeros, null shares, a null mean and row count 0."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    body = asgi_request(
        app, "GET", "/v2/analytics/summary", query="from=2026-01-01&to=2026-01-04"
    ).body

    gap = body["series"][1]
    assert gap["date"] == "2026-01-02"
    assert gap["total"] == 0
    assert gap["counts"] == {"positive": 0, "negative": 0, "neutral": 0}
    # A zero denominator has no answer: `null`, never a fabricated 0.0.
    assert gap["shares"] == {"positive": None, "negative": None, "neutral": None}
    assert gap["mean_confidence"] is None
    assert gap["mean_confidence_row_count"] == 0


def test_summary_bounds_are_inclusive_utc_calendar_days(app, tmp_settings):
    """`BR1.1`: a row at 23:59:59Z on the `to` day is in range; the next day is not."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    body = asgi_request(
        app, "GET", "/v2/analytics/summary", query="from=2026-01-01&to=2026-01-03"
    ).body

    assert body["total"] == 3
    assert [entry["date"] for entry in body["series"]] == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
    ]
    # 2026-01-04 is outside the `to` bound, so it is neither counted nor listed.
    assert all(entry["date"] != "2026-01-04" for entry in body["series"])


def test_summary_with_neither_bound_runs_from_the_earliest_stored_day_through_today(
    app, tmp_settings
):
    """`BR1.3`, `BR3.1`: the unbounded span starts at the earliest stored day."""
    _bring_up(app, tmp_settings)
    _seed(
        tmp_settings.db_path,
        (
            ("earlier", "positive", 0.50, f"{_days_ago(2)}T08:00:00Z", None),
            ("later", "negative", 0.50, f"{_today()}T08:00:00Z", None),
        ),
    )

    body = asgi_request(app, "GET", "/v2/analytics/summary").body

    assert body["total"] == 2
    assert body["counts"] == {"positive": 1, "negative": 1, "neutral": 0}
    # Earliest stored day through today inclusive, so the middle day is filled.
    assert [entry["date"] for entry in body["series"]] == [_days_ago(2), _days_ago(1), _today()]
    assert body["series"][1]["total"] == 0
    assert body["series"][1]["mean_confidence"] is None


def test_a_single_summary_bound_is_never_dropped(app, tmp_settings):
    """`BR1.2`: a lone `to` starts at the beginning of history; a lone `from` runs to now."""
    _bring_up(app, tmp_settings)
    _seed(
        tmp_settings.db_path,
        (
            ("first", "positive", 0.40, f"{_days_ago(3)}T08:00:00Z", None),
            ("middle", "neutral", 0.50, f"{_days_ago(2)}T08:00:00Z", None),
            ("last", "negative", 0.60, f"{_today()}T08:00:00Z", None),
        ),
    )

    only_to = asgi_request(app, "GET", "/v2/analytics/summary", query=f"to={_days_ago(2)}").body
    assert only_to["total"] == 2
    assert [entry["date"] for entry in only_to["series"]] == [_days_ago(3), _days_ago(2)]

    only_from = asgi_request(app, "GET", "/v2/analytics/summary", query=f"from={_days_ago(2)}").body
    assert only_from["total"] == 2
    assert [entry["date"] for entry in only_from["series"]] == [
        _days_ago(2),
        _days_ago(1),
        _today(),
    ]


def test_summary_over_a_range_matching_no_rows_is_an_empty_success(app, tmp_settings):
    """`BR3.3`, `BR4.4`: no match is a 200 with total 0 and an empty series, never a 404."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    response = asgi_request(
        app, "GET", "/v2/analytics/summary", query="from=2026-02-01&to=2026-02-05"
    )

    assert response.status_code == 200
    assert set(response.body) == SUMMARY_FIELDS
    assert response.body["total"] == 0
    assert response.body["counts"] == {"positive": 0, "negative": 0, "neutral": 0}
    assert response.body["shares"] == {"positive": None, "negative": None, "neutral": None}
    assert response.body["mean_confidence"] is None
    assert response.body["mean_confidence_row_count"] == 0
    # Never a store-wide zero-filled span.
    assert response.body["series"] == []


def test_summary_for_an_unmatched_import_id_is_an_empty_success(app, tmp_settings):
    """`BR1.3`, `BR4.4`: an unmatched `import_id` is an empty population, not an error."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    unmatched = asgi_request(app, "GET", "/v2/analytics/summary", query="import_id=no-such-import")
    assert unmatched.status_code == 200
    assert unmatched.body["total"] == 0
    assert unmatched.body["series"] == []

    matched = asgi_request(app, "GET", "/v2/analytics/summary", query="import_id=imp-1")
    assert matched.status_code == 200
    assert matched.body["total"] == 2
    assert matched.body["counts"] == {"positive": 1, "negative": 0, "neutral": 1}
    # A matched `import_id` with no bounds spans its own rows (2026-01-03..04).
    assert [entry["date"] for entry in matched.body["series"]] == ["2026-01-03", "2026-01-04"]


def test_summary_refuses_a_malformed_bound_naming_the_parameter(app, tmp_settings):
    """`BR4.1`, `BR4.2`: 422 `VALIDATION_FAILED`, nothing computed, message names it."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    for query, expected in (
        ("from=not-a-date", "query.from"),
        ("from=2026-13-45", "query.from"),
        ("to=2026-02-30", "query.to"),
    ):
        response = asgi_request(app, "GET", "/v2/analytics/summary", query=query)

        assert response.status_code == 422, query
        assert set(response.body) == ENVELOPE_FIELDS
        assert response.body["code"] == "VALIDATION_FAILED"
        assert expected in response.body["message"]
        # No `field` member exists on the frozen envelope.
        assert "field" not in response.body


def test_summary_refuses_an_inverted_range_naming_both_bounds(app, tmp_settings):
    """`BR1.4`, `BR4.3`: one 422 whose message names `query.from` *and* `query.to`."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    response = asgi_request(
        app, "GET", "/v2/analytics/summary", query="from=2026-01-04&to=2026-01-01"
    )

    assert response.status_code == 422
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "VALIDATION_FAILED"
    assert "query.from" in response.body["message"]
    assert "query.to" in response.body["message"]


def test_summary_answers_a_storage_failure_with_its_own_machine_code(app, monkeypatch):
    """`BR4.5`: `500 STORAGE_FAILURE` is distinct from every validation code."""

    class FailingStore:
        """Stands in for a store that cannot answer the read."""

        def read_summary(self, *args, **kwargs):
            raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr("app.routes.read_summary", FailingStore().read_summary)

    response = asgi_request(app, "GET", "/v2/analytics/summary")

    assert response.status_code == 500
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "STORAGE_FAILURE"
    assert response.body["code"] != "VALIDATION_FAILED"
    # The envelope carries no internal detail.
    assert "database is locked" not in response.body["message"]


# -- Step 3: the terms endpoint ----------------------------------------------


def test_terms_ranks_by_count_descending_with_alphabetical_ties(app, tmp_settings):
    """`BR2.4`, `BR2.5`: count descending, ties alphabetical, `term` and `count` only."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, TERM_ROWS)

    response = asgi_request(
        app, "GET", "/v2/analytics/terms", query="from=2026-01-01&to=2026-01-02"
    )

    assert response.status_code == 200
    assert set(response.body) == TERMS_FIELDS
    assert response.body["positive"] == [
        {"term": "wonderful", "count": 2},
        {"term": "delightful", "count": 1},
        {"term": "great", "count": 1},
    ]
    assert response.body["negative"] == [
        {"term": "awful", "count": 2},
        {"term": "bad", "count": 1},
        {"term": "terrible", "count": 1},
    ]
    for entry in response.body["positive"] + response.body["negative"]:
        assert set(entry) == TERM_ENTRY_FIELDS
    # The stopword is filtered out and neutral rows contribute to neither list.
    assert all(entry["term"] != "and" for entry in response.body["positive"])
    assert all(entry["term"] != "plain" for entry in response.body["negative"])


def test_terms_honours_the_limit_per_list_without_clamping_an_oversized_one(app, tmp_settings):
    """`BR2.6`: the default is 10 per list, `limit` is honoured and never clamped."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, TERM_ROWS)

    defaulted = asgi_request(
        app, "GET", "/v2/analytics/terms", query="from=2026-01-01&to=2026-01-02"
    ).body
    assert len(defaulted["positive"]) == 3
    assert len(defaulted["negative"]) == 3

    limited = asgi_request(
        app, "GET", "/v2/analytics/terms", query="from=2026-01-01&to=2026-01-02&limit=2"
    ).body
    assert limited["positive"] == [
        {"term": "wonderful", "count": 2},
        {"term": "delightful", "count": 1},
    ]
    assert limited["negative"] == [
        {"term": "awful", "count": 2},
        {"term": "bad", "count": 1},
    ]

    oversized = asgi_request(
        app, "GET", "/v2/analytics/terms", query="from=2026-01-01&to=2026-01-02&limit=999"
    ).body
    assert len(oversized["positive"]) == 3
    assert len(oversized["negative"]) == 3


def test_terms_refuses_a_limit_below_one_or_not_a_number_naming_the_parameter(app, tmp_settings):
    """`BR2.6`, `BR4.2`: 422 `VALIDATION_FAILED` naming `query.limit`, never clamped."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, TERM_ROWS)

    for query in ("limit=0", "limit=-3", "limit=abc"):
        response = asgi_request(app, "GET", "/v2/analytics/terms", query=query)

        assert response.status_code == 422, query
        assert set(response.body) == ENVELOPE_FIELDS
        assert response.body["code"] == "VALIDATION_FAILED"
        assert "limit" in response.body["message"]


def test_terms_over_an_empty_range_is_two_empty_lists_and_nothing_else(app, tmp_settings):
    """`BR4.4`: the terms empty body is exactly `{positive: [], negative: []}`."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, TERM_ROWS)

    response = asgi_request(
        app, "GET", "/v2/analytics/terms", query="from=2026-03-01&to=2026-03-02"
    )

    assert response.status_code == 200
    assert response.body == {"positive": [], "negative": []}


def test_terms_for_a_label_with_no_rows_in_range_is_an_empty_array(app, tmp_settings):
    """`BR2.4`: a label with no rows yields `[]`, never `null` and never padded."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, TERM_ROWS)

    body = asgi_request(
        app, "GET", "/v2/analytics/terms", query="from=2026-01-01&to=2026-01-01"
    ).body

    assert body["positive"] == [
        {"term": "wonderful", "count": 2},
        {"term": "delightful", "count": 1},
        {"term": "great", "count": 1},
    ]
    assert body["negative"] == []


def test_terms_filters_by_import_id_and_refuses_an_inverted_range(app, tmp_settings):
    """`BR3.2`: `import_id` narrows the population; the inverted-range refusal is shared."""
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, TERM_ROWS)

    filtered = asgi_request(app, "GET", "/v2/analytics/terms", query="import_id=imp-a")
    assert filtered.status_code == 200
    assert filtered.body["positive"] == []
    assert filtered.body["negative"] == [
        {"term": "awful", "count": 2},
        {"term": "bad", "count": 1},
        {"term": "terrible", "count": 1},
    ]

    unmatched = asgi_request(app, "GET", "/v2/analytics/terms", query="import_id=absent")
    assert unmatched.status_code == 200
    assert unmatched.body == {"positive": [], "negative": []}

    inverted = asgi_request(
        app, "GET", "/v2/analytics/terms", query="from=2026-01-04&to=2026-01-01"
    )
    assert inverted.status_code == 422
    assert inverted.body["code"] == "VALIDATION_FAILED"
    assert "query.from" in inverted.body["message"]
    assert "query.to" in inverted.body["message"]


def test_terms_answers_a_storage_failure_with_the_same_machine_code(app, monkeypatch):
    """`BR4.5`: the storage failure is the same `500 STORAGE_FAILURE` on both endpoints."""

    class FailingStore:
        """Stands in for a store that cannot answer the read."""

        def read_terms(self, *args, **kwargs):
            raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr("app.routes.read_terms", FailingStore().read_terms)

    response = asgi_request(app, "GET", "/v2/analytics/terms")

    assert response.status_code == 500
    assert response.body == {"code": "STORAGE_FAILURE", "message": response.body["message"]}
    assert set(response.body) == ENVELOPE_FIELDS


# -- The contract's static half ----------------------------------------------


def test_a_storage_failure_is_logged_through_the_module_logger_with_its_code(
    app, monkeypatch, caplog
):
    """`BR4.6`, `NFR8.1`, `NFR8.2`: the wire surface and the log agree.

    The envelope carries the machine code, and the **log record carries the same
    code**, so an operator can match a server-side line to a response body. The
    record is emitted through the module logger rather than swallowed, and it holds
    no credential and no interpolated statement text (`NFR8.3`).
    """

    class FailingStore:
        """Stands in for a store that cannot answer the read."""

        def read_summary(self, *args, **kwargs):
            raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr("app.routes.read_summary", FailingStore().read_summary)

    with caplog.at_level("ERROR", logger="app.routes"):
        response = asgi_request(app, "GET", "/v2/analytics/summary")

    assert response.status_code == 500
    assert response.body["code"] == "STORAGE_FAILURE"

    records = [r for r in caplog.records if r.name == "app.routes" and r.levelname == "ERROR"]
    assert records, "the storage failure was swallowed rather than logged"
    logged = "\n".join(r.getMessage() for r in records)
    # The same code travels on both surfaces.
    assert "STORAGE_FAILURE" in logged
    # The record is written through a logger, never printed.
    assert not any("print" in (r.funcName or "") for r in records)
    # No credential material and no interpolated statement text (`NFR8.3`).
    assert "sk-or-v1" not in logged
    assert "SELECT" not in logged.upper()


def test_v1_routes_are_untouched_by_the_v2_surface(app):
    """`BR4.7`, `AC8.5.2`: `/v1` keeps its paths, shapes and envelope."""
    assert asgi_request(app, "GET", "/v1/health").status_code == 200
    assert asgi_request(app, "GET", "/v1/analyses").body == []
    assert asgi_request(app, "GET", "/v1/analyses", query="limit=0").status_code == 422
    assert asgi_request(app, "GET", "/analytics/summary").status_code == 404


def test_the_view_prefix_constant_equals_the_router_prefix():
    """`BR2.13`, `AC6.2.3`: the two independent copies of the prefix are asserted equal."""
    from pathlib import Path

    from app.routes import V2_PREFIX

    static = Path(__file__).parent.parent / "app" / "static" / "app.js"
    script = static.read_text(encoding="utf-8")
    assert 'const API_V2 = "/v2";' in script
    assert V2_PREFIX == "/v2"


# -- Step 14: the concurrency test that reproduces R-01 -----------------------


class _OverlappingRead:
    """The real summary read, held at the storage seam until both requests arrive.

    Two-party barrier, so the overlap is **made** rather than raced for: neither
    request can leave the read until the other has entered it, which forces the
    application to serve them from two worker threads at the same instant instead
    of reusing one. The read itself is the application's own, and the assertions
    read the response the application produced — the barrier only decides *when*
    they happen (AC7.7.1).
    """

    def __init__(self, real, barrier: threading.Barrier) -> None:
        self._real = real
        self._barrier = barrier

    def __call__(self, connection, *args, **kwargs):
        self._barrier.wait(timeout=30)
        return self._real(connection, *args, **kwargs)


def test_the_driver_opens_connections_that_may_be_used_and_closed_on_another_thread(
    tmp_settings, tmp_db_path
):
    """`FR1.6`, `BR6.2`, `BR6.3`: the thread-affinity decision, proved by its effect.

    This is the load-bearing instrument for R-01, and it is deterministic rather
    than raced for. `app.db.connect` is the repository's only `sqlite3.connect`
    site, so the decision is proved *there*: a connection it opens is used and
    closed from a different thread — exactly what FastAPI does to a request-scoped
    connection, because a synchronous dependency and a synchronous handler are
    dispatched to worker threads that are not guaranteed to match.

    With the driver's default `check_same_thread=True` this raises
    `sqlite3.ProgrammingError`, so the test goes **red** the moment the decision is
    reverted and green only because it is applied (BR6.3).
    """
    from app import db

    init_db(tmp_db_path)
    opened_on: list[int] = []
    used_on: list[int] = []
    both_running = threading.Barrier(2)
    connection: list[sqlite3.Connection] = []
    failure: list[BaseException] = []

    def open_it() -> None:
        try:
            opened_on.append(threading.get_ident())
            connection.append(db.connect(tmp_db_path))
            # Hold this thread until the other is running, so the connection is
            # provably created and used on two different threads.
            both_running.wait(timeout=30)
        except BaseException as exc:  # pragma: no cover - only on a barrier timeout
            failure.append(exc)

    def use_and_close_it() -> None:
        try:
            both_running.wait(timeout=30)
            used_on.append(threading.get_ident())
            assert connection[0].execute("SELECT COUNT(*) FROM analyses").fetchone()[0] == 0
            connection[0].close()
        except BaseException as exc:  # pragma: no cover - only on a barrier timeout
            failure.append(exc)

    # Plain threads, not a pool: a pool reuses an idle worker, so the two ids could
    # match and the assertion would prove nothing.
    opener = threading.Thread(target=open_it)
    user = threading.Thread(target=use_and_close_it)
    opener.start()
    user.start()
    opener.join(timeout=30)
    user.join(timeout=30)

    assert failure == []
    assert len(opened_on) == len(used_on) == 1
    # The connection was used and closed from a thread that did not open it, which
    # is what the driver's default same-thread guard refuses.
    assert opened_on[0] != used_on[0]


def test_two_overlapping_analytics_requests_never_raise_a_cross_thread_error(
    app, monkeypatch, tmp_settings
):
    """`FR1.6`, `BR6.3`, `AC7.7.1`, `AC8.4.1`: two real overlapping reads, both answered.

    Both requests are issued on separate threads through the replaced harness, both
    are held inside the read until they overlap, and both must answer `200` with no
    exception escaping a worker thread. This is the end-to-end half of the R-01
    story; `test_the_driver_opens_connections_that_may_be_used_and_closed_on_another_thread`
    is the half that is red the moment the thread-affinity decision is reverted.
    """
    from app import analytics

    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    barrier = threading.Barrier(2)
    monkeypatch.setattr(
        "app.routes.read_summary", _OverlappingRead(analytics.read_summary, barrier)
    )

    outcomes = concurrent_requests(
        app,
        [
            ("GET", "/v2/analytics/summary", "from=2026-01-01&to=2026-01-02"),
            ("GET", "/v2/analytics/summary", "from=2026-01-01&to=2026-01-04"),
        ],
    )

    first, second = outcomes
    # Neither request failed: the barrier released, so both reads really ran.
    assert first.error is None, first.error
    assert second.error is None, second.error
    assert first.response.status_code == 200
    assert second.response.status_code == 200
    # They are genuinely concurrent: different threads, intersecting intervals.
    assert first.thread_id != second.thread_id
    assert first.overlaps(second), (first, second)
    # And they describe different populations, so this is two real reads.
    assert first.response.body["total"] == 2
    assert second.response.body["total"] == 4


def test_the_analytics_reads_survive_being_issued_against_one_started_application(
    app, tmp_settings
):
    """`BR6.3`: the same overlap without any seam at all still answers `200`.

    The barrier version above is what forces the overlap; this one shows the fix is
    not an artefact of that seam. Twenty-four genuinely concurrent requests against
    one application, one lifespan entry, no substitution.
    """
    _bring_up(app, tmp_settings)
    _seed(tmp_settings.db_path, JANUARY_ROWS)

    outcomes = concurrent_requests(
        app,
        [
            ("GET", "/v2/analytics/summary", "from=2026-01-01&to=2026-01-04"),
            ("GET", "/v2/analytics/summary", "from=2026-01-01&to=2026-01-02"),
            ("GET", "/v2/analytics/summary", "from=2026-01-03&to=2026-01-04"),
            ("GET", "/v2/analytics/terms", "from=2026-01-01&to=2026-01-04"),
            ("GET", "/v2/analytics/terms", "import_id=imp-1"),
            ("GET", "/v1/analyses", ""),
        ]
        * 4,
    )

    assert len(outcomes) == 24
    assert all(outcome.error is None for outcome in outcomes), [
        outcome.error for outcome in outcomes if outcome.error is not None
    ]
    assert all(outcome.response.status_code == 200 for outcome in outcomes)
    # Every request saw the same store: the row count never moved under them, and
    # each range reported its own population rather than another request's.
    totals = {
        outcome.response.body["total"] for outcome in outcomes if "total" in outcome.response.body
    }
    assert totals == {4, 2}


def test_schema_initialisation_is_hoisted_out_of_the_per_request_path(app, monkeypatch):
    """`AC7.7.2`, `BR6.4`: one lifespan entry, so no request can migrate the file.

    Two simultaneous `init_db` calls contend for the same SQLite file and raise
    "database is locked"; hoisting startup out of the request path is what keeps the
    concurrency test red for the *connection* reason rather than a schema one.
    """
    from app import db

    calls: list[object] = []
    real_init = db.init_db

    def counting_init(db_path):
        calls.append(db_path)
        real_init(db_path)

    monkeypatch.setattr("app.db.init_db", counting_init)

    outcomes = concurrent_requests(
        app,
        [("GET", "/v2/analytics/summary", ""), ("GET", "/v2/analytics/terms", "")],
    )

    assert len(calls) == 1
    assert all(outcome.error is None for outcome in outcomes)
    assert all(outcome.response.status_code == 200 for outcome in outcomes)
    # The two requests really did overlap rather than queueing.
    first, second = outcomes
    assert first.overlaps(second)


def test_the_analytics_endpoints_are_proved_offline_by_an_armed_guard():
    """`FR8.1`, `AC1.1.5` (`BR2.8`, `BR6.6`): in-process, and the guard is armed.

    `AC1.1.5` is the criterion that carries both halves at once -- every aggregate
    is computed in-process with no network call, socket or credential anywhere in
    the analytics path (`BR2.8`), and the suite is green with the offline guard
    proven armed rather than merely assumed (`BR6.6`).

    The proof is the guard itself: a connection attempt raised *inside* a test is
    turned into a failure, so a passing analytics run cannot have reached the
    network. Without this, "offline" would be an unverified claim about the code
    rather than a property the suite demonstrates. The sibling `FR8.1` criteria
    assert the coverage; this one asserts the arming.
    """
    with (
        socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe,
        pytest.raises(
            AssertionError,
        ),
    ):
        probe.connect(("127.0.0.1", 9))

    # And the analytics path holds nothing that could have needed one: no HTTP
    # client, no credential, no model inference. The read module imports neither.
    assert not hasattr(analytics, "requests")
    assert not hasattr(analytics, "httpx")
    assert not hasattr(analytics, "api_key")
