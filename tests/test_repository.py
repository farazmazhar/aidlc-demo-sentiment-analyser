"""Repository / data access: stored-row round trip, listing and the retired column.

Both the fresh-store and migrated-store tests read the values back out of the
real SQLite file, so the assertions are about what was persisted, not about what
was passed in. (FR3.2, FR3.4, FR3.5, FR3.6, BR3.2, BR3.4, BR3.5)
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.db import connect, init_db
from app.repository import DEFAULT_LIST_LIMIT, insert_analysis, list_analyses
from app.sentiment import SentimentResult

# Three distinct instants so newest-first ordering is observable.
EARLIEST = datetime(2026, 9, 29, 10, 0, 0, tzinfo=UTC)
MIDDLE = datetime(2026, 9, 29, 11, 0, 0, tzinfo=UTC)
LATEST = datetime(2026, 9, 29, 12, 0, 0, tzinfo=UTC)

PRE_V1_DDL = """
CREATE TABLE analyses (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT    NOT NULL,
  label         TEXT    NOT NULL,
  probabilities TEXT    NOT NULL,
  confidence    REAL    NOT NULL,
  intensity     REAL    NOT NULL,
  model         TEXT    NOT NULL,
  provider      TEXT    NOT NULL,
  created_at    TEXT    NOT NULL
)
"""


def _result(label: str = "positive") -> SentimentResult:
    """A real engine result object, used as input data for the repository."""
    return SentimentResult(
        label=label,
        probabilities={"positive": 0.7, "negative": 0.2, "neutral": 0.1},
        confidence=0.7,
        model="dummy-keyword-v1",
        provider="offline",
    )


def test_insert_returns_the_stored_row_with_every_v1_field(tmp_db_path):
    """BR3.2: every field of the returned record comes back out of the database."""
    init_db(tmp_db_path)
    connection = connect(tmp_db_path)
    try:
        record = insert_analysis(connection, text="I love this", result=_result(), now=MIDDLE)

        assert record.id == 1
        assert record.text == "I love this"
        assert record.label == "positive"
        assert record.probabilities == {"positive": 0.7, "negative": 0.2, "neutral": 0.1}
        assert record.confidence == 0.7
        assert record.model == "dummy-keyword-v1"
        assert record.provider == "offline"
        assert record.created_at == "2026-09-29T11:00:00Z"
        assert not hasattr(record, "intensity")

        row = connection.execute("SELECT * FROM analyses WHERE id = 1").fetchone()
        assert row["text"] == "I love this"
        # `probabilities` is stored as a JSON object keyed by label...
        assert row["probabilities"].startswith('{"positive"')
        # ...and the retired attribute is left unset rather than invented (BR3.4).
        assert row["intensity"] is None
    finally:
        connection.close()


def test_list_analyses_is_newest_first_and_honours_the_limit(tmp_db_path):
    """BR3.5: the history comes back newest-first and honours the caller's limit."""
    init_db(tmp_db_path)
    connection = connect(tmp_db_path)
    try:
        for text, moment in (("first", EARLIEST), ("second", MIDDLE), ("third", LATEST)):
            insert_analysis(connection, text=text, result=_result(), now=moment)

        all_records = list_analyses(connection)
        two_newest = list_analyses(connection, limit=2)

        assert [record.text for record in all_records] == ["third", "second", "first"]
        assert [record.created_at for record in all_records] == [
            "2026-09-29T12:00:00Z",
            "2026-09-29T11:00:00Z",
            "2026-09-29T10:00:00Z",
        ]
        assert [record.text for record in two_newest] == ["third", "second"]
    finally:
        connection.close()


def test_the_default_list_limit_is_the_documented_fifty():
    """D2: an absent limit has a named default rather than an implementer's choice."""
    assert DEFAULT_LIST_LIMIT == 50


def test_a_pre_v1_row_reads_back_without_the_retired_attribute(tmp_path):
    """AC7.1.3: the value a pre-v1 row holds is neither surfaced nor back-filled."""
    db_path = tmp_path / "data" / "sentiment.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    pre_v1 = sqlite3.connect(db_path)
    try:
        pre_v1.execute(PRE_V1_DDL)
        pre_v1.execute(
            "INSERT INTO analyses (text, label, probabilities, confidence, intensity, "
            "model, provider, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (
                "a pre-v1 row",
                "positive",
                '{"positive": 0.9, "negative": 0.05, "neutral": 0.05}',
                0.9,
                0.6,
                "dummy-keyword-v1",
                "local-dummy",
                "2026-09-29T09:00:00Z",
            ),
        )
        pre_v1.commit()
    finally:
        pre_v1.close()

    init_db(db_path)
    connection = connect(db_path)
    try:
        records = list_analyses(connection)

        assert len(records) == 1
        assert records[0].text == "a pre-v1 row"
        assert records[0].provider == "local-dummy"
        assert not hasattr(records[0], "intensity")

        # The retired value is still exactly what the old row held.
        row = connection.execute("SELECT intensity FROM analyses WHERE id = 1").fetchone()
        assert row["intensity"] == 0.6

        # A row written now leaves it unset.
        insert_analysis(connection, text="a v1 row", result=_result(), now=LATEST)
        fresh = connection.execute(
            "SELECT intensity FROM analyses WHERE text = 'a v1 row'"
        ).fetchone()
        assert fresh["intensity"] is None
    finally:
        connection.close()


def test_probabilities_survive_as_a_label_keyed_object(tmp_db_path):
    """BR3.2: the stored probabilities keep every label and its value."""
    init_db(tmp_db_path)
    connection = connect(tmp_db_path)
    try:
        insert_analysis(connection, text="text", result=_result("negative"), now=EARLIEST)

        stored = list_analyses(connection)[0]

        assert stored.label == "negative"
        assert sorted(stored.probabilities) == ["negative", "neutral", "positive"]
        assert sum(stored.probabilities.values()) == 1.0
    finally:
        connection.close()


def test_the_repository_creates_the_parent_directory(tmp_path: Path):
    """NFR6: opening a store under a missing directory needs no manual setup."""
    db_path = tmp_path / "nested" / "data" / "sentiment.db"
    assert not db_path.parent.exists()

    connection = connect(db_path)
    try:
        assert db_path.parent.is_dir()
    finally:
        connection.close()
