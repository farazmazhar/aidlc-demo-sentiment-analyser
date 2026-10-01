"""API / endpoint: the bulk CSV import/export surface over real storage.

Acceptance tests written against the FR1/FR2/FR3 acceptance criteria *before*
the implementation (the team's custom ordering). Every request goes through the
real in-process ASGI application (`create_app` + `asgi_request`) and every
assertion is on the parsed response or on rows read back out of real SQLite.
(FR1.1-FR1.7, FR2.1-FR2.6, FR3.1-FR3.4)

No network is touched: the session-wide `offline_guard` in `tests/conftest.py`
makes an accidental socket connection fail the run.
"""

from __future__ import annotations

import csv
import io
import sqlite3

import pytest

from app.main import create_app
from app.sentiment import SentimentEngineError
from tests.conftest import asgi_request

#: The contract's import-summary shape: the grouping id, the two counts, the
#: per-label breakdown and the mean confidence (FR1.5).
IMPORT_SUMMARY_FIELDS = {
    "import_id",
    "imported",
    "skipped",
    "label_counts",
    "mean_confidence",
}

#: The contract's error envelope: exactly these two keys (BR4.3, NFR3).
ENVELOPE_FIELDS = {"code", "message"}

#: The dummy engine's confidence for the three deterministic classifications
#: used below: positive/negative hit one keyword (0.85), neutral ties (0.70).
POSITIVE_CONFIDENCE = 0.85
NEGATIVE_CONFIDENCE = 0.85
NEUTRAL_CONFIDENCE = 0.70


@pytest.fixture
def app(tmp_settings):
    """A real application wired to this test's temporary database."""
    return create_app(tmp_settings)


def _import(app, body: bytes, content_type: str = "text/csv"):
    """Send a raw CSV body to the bulk-import endpoint through the harness."""
    return asgi_request(app, "POST", "/v1/analyses/import", body=body, content_type=content_type)


def _export(app, import_id: str):
    """Read one import back as CSV."""
    return asgi_request(app, "GET", "/v1/analyses/export", query=f"import_id={import_id}")


def _rows_for_import(db_path, import_id: str):
    """Read the persisted rows for `import_id` straight out of SQLite, oldest first."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(
            "SELECT * FROM analyses WHERE import_id = ? ORDER BY id ASC", (import_id,)
        ).fetchall()
    finally:
        connection.close()


def _row_count(db_path) -> int:
    connection = sqlite3.connect(db_path)
    try:
        return connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    finally:
        connection.close()


# -- FR1: bulk import ---------------------------------------------------------


def test_import_persists_rows_under_one_import_id_and_reports_the_breakdown(app, tmp_settings):
    """FR1.3, FR1.5: one shared id; imported/skipped, per-label counts, mean confidence."""
    response = _import(app, b"I love this\nThis is terrible\nJust a sentence\n")

    assert response.status_code == 200
    assert set(response.body) == IMPORT_SUMMARY_FIELDS
    assert isinstance(response.body["import_id"], str)
    assert response.body["import_id"]
    assert response.body["imported"] == 3
    assert response.body["skipped"] == 0
    assert response.body["label_counts"] == {"positive": 1, "negative": 1, "neutral": 1}
    assert response.body["mean_confidence"] == pytest.approx(
        (POSITIVE_CONFIDENCE + NEGATIVE_CONFIDENCE + NEUTRAL_CONFIDENCE) / 3
    )

    rows = _rows_for_import(tmp_settings.db_path, response.body["import_id"])
    assert [row["text"] for row in rows] == [
        "I love this",
        "This is terrible",
        "Just a sentence",
    ]
    assert [row["label"] for row in rows] == ["positive", "negative", "neutral"]
    assert all(row["import_id"] == response.body["import_id"] for row in rows)


def test_an_exact_text_first_row_is_a_header_and_is_not_analyzed(app, tmp_settings):
    """FR1.2: the exact-`text` first row is a header, skipped before analysis."""
    response = _import(app, b"text\nI love this\n")

    assert response.status_code == 200
    assert response.body["imported"] == 1
    rows = _rows_for_import(tmp_settings.db_path, response.body["import_id"])
    assert [row["text"] for row in rows] == ["I love this"]


def test_a_first_row_that_is_not_exactly_text_is_a_data_row(app, tmp_settings):
    """FR1.2, A4: only the exact `text` first row is a header; anything else is data."""
    response = _import(app, b"textual data\nI love this\n")

    assert response.status_code == 200
    assert response.body["imported"] == 2
    rows = _rows_for_import(tmp_settings.db_path, response.body["import_id"])
    assert [row["text"] for row in rows] == ["textual data", "I love this"]


def test_csv_quoting_round_trips_commas_and_newlines(app, tmp_settings):
    """FR1.2: the stdlib csv module handles quoted commas and newlines."""
    response = _import(app, b'text\n"hello, world"\n"line one\nline two"\n')

    assert response.status_code == 200
    assert response.body["imported"] == 2
    rows = _rows_for_import(tmp_settings.db_path, response.body["import_id"])
    assert [row["text"] for row in rows] == ["hello, world", "line one\nline two"]


def test_blank_and_engine_failing_rows_are_skipped_without_aborting(app, tmp_settings, monkeypatch):
    """FR1.4: blank text and a per-row engine failure are skipped, not fatal."""
    from app.dummy_client import DummySentimentClient

    class FailingOnBoom:
        """A stand-in engine that fails only for the row containing `boom`."""

        def analyze(self, text: str):
            if "boom" in text:
                raise SentimentEngineError("The sentiment engine could not be reached.")
            return DummySentimentClient().analyze(text)

    monkeypatch.setattr("app.routes.get_client", lambda settings, credential=None: FailingOnBoom())

    response = _import(app, b"text\nI love this\n\nboom row\nJust a sentence\n")

    assert response.status_code == 200
    assert response.body["imported"] == 2
    assert response.body["skipped"] == 2
    assert response.body["label_counts"] == {"positive": 1, "negative": 0, "neutral": 1}
    assert response.body["mean_confidence"] == pytest.approx(
        (POSITIVE_CONFIDENCE + NEUTRAL_CONFIDENCE) / 2
    )

    # The successful rows are kept and unaffected by the skipped ones.
    rows = _rows_for_import(tmp_settings.db_path, response.body["import_id"])
    assert [row["text"] for row in rows] == ["I love this", "Just a sentence"]


def test_import_with_only_a_header_returns_200_and_a_zero_breakdown(app, tmp_settings):
    """FR1.6, A3: zero rows imported still returns 200, an id, zeros and a null mean."""
    response = _import(app, b"text\n")

    assert response.status_code == 200
    assert response.body["imported"] == 0
    assert response.body["skipped"] == 0
    assert response.body["label_counts"] == {"positive": 0, "negative": 0, "neutral": 0}
    assert response.body["mean_confidence"] is None
    assert response.body["import_id"]
    assert _rows_for_import(tmp_settings.db_path, response.body["import_id"]) == []


def test_import_of_an_empty_body_returns_200_and_a_zero_breakdown(app, tmp_settings):
    """FR1.6, A3: an empty body is zero rows, not an error; the mean is null."""
    response = _import(app, b"")

    assert response.status_code == 200
    assert response.body["imported"] == 0
    assert response.body["skipped"] == 0
    assert response.body["mean_confidence"] is None
    assert _row_count(tmp_settings.db_path) == 0


@pytest.mark.parametrize("content_type", ["application/json", "application/xml"])
def test_import_refuses_an_unsupported_content_type(app, tmp_settings, content_type):
    """FR1.7: a content type that is neither text/csv nor text/plain is a 422 envelope."""
    response = _import(app, b"I love this\n", content_type=content_type)

    assert response.status_code == 422
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "VALIDATION_FAILED"
    assert response.body["message"]
    assert _row_count(tmp_settings.db_path) == 0


def test_import_accepts_a_text_plain_body(app, tmp_settings):
    """FR1.7: `text/plain` is an accepted content type for the CSV body."""
    response = _import(app, b"I love this\n", content_type="text/plain")

    assert response.status_code == 200
    assert response.body["imported"] == 1


def test_import_refuses_a_body_that_is_not_valid_utf8_csv(app, tmp_settings):
    """FR1.7: a body that cannot be parsed as CSV is a 422 envelope and stores nothing."""
    response = _import(app, b"\xff\xfe\x00not csv")

    assert response.status_code == 422
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "VALIDATION_FAILED"
    assert _row_count(tmp_settings.db_path) == 0


# -- FR2: bulk export ---------------------------------------------------------


def test_export_returns_the_imported_rows_as_csv_newest_first(app, tmp_settings):
    """FR2.2, FR2.3: CSV body, the pinned columns, newest first, attachment headers."""
    imported = _import(app, b"I love this\nThis is terrible\nJust a sentence\n").body

    response = _export(app, imported["import_id"])

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        f'attachment; filename="analyses-{imported["import_id"]}.csv"'
    )

    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0] == [
        "id",
        "text",
        "label",
        "confidence",
        "model",
        "provider",
        "created_at",
    ]
    data = rows[1:]
    # Newest first: descending id, so the last imported row is the first data row.
    assert [row[0] for row in data] == ["3", "2", "1"]
    assert [row[1] for row in data] == [
        "Just a sentence",
        "This is terrible",
        "I love this",
    ]
    assert [row[2] for row in data] == ["neutral", "negative", "positive"]
    assert all(row[5] == "offline" for row in data)
    assert all(row[6].endswith("Z") for row in data)


def test_export_quotes_fields_containing_commas(app, tmp_settings):
    """FR2.3: export quoting is produced by the stdlib csv module."""
    imported = _import(app, b'text\n"hello, world"\n').body

    response = _export(app, imported["import_id"])

    assert response.status_code == 200
    assert '"hello, world"' in response.text


def test_export_includes_only_rows_for_the_import_id(app, tmp_settings):
    """FR2.6: rows from single analysis (null import_id) are never returned."""
    imported = _import(app, b"I love this\nThis is terrible\n").body
    asgi_request(app, "POST", "/v1/analyze", json_body={"text": "Just a sentence"})

    response = _export(app, imported["import_id"])

    assert response.status_code == 200
    data = list(csv.reader(io.StringIO(response.text)))[1:]
    assert [row[1] for row in data] == ["This is terrible", "I love this"]
    assert len(data) == 2


def test_export_of_an_unknown_import_id_is_a_404_envelope(app):
    """FR2.4: an unknown import id is a 404 through the envelope, new code."""
    response = _export(app, "no-such-import")

    assert response.status_code == 404
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "IMPORT_NOT_FOUND"
    assert response.body["message"]


def test_export_requires_the_import_id_parameter(app):
    """FR2.5: a missing `import_id` is a 422 envelope; the parameter is required."""
    response = asgi_request(app, "GET", "/v1/analyses/export")

    assert response.status_code == 422
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "VALIDATION_FAILED"
    assert "import_id" in response.body["message"]


# -- FR3: record contract back-compatibility ---------------------------------


def test_single_analysis_records_carry_a_null_import_id(app):
    """FR3.2: the additive `import_id` field is returned as null for single analyses."""
    created = asgi_request(app, "POST", "/v1/analyze", json_body={"text": "I love this"})

    assert created.status_code == 200
    assert created.body["import_id"] is None

    history = asgi_request(app, "GET", "/v1/analyses")
    assert history.status_code == 200
    assert history.body[0]["import_id"] is None
