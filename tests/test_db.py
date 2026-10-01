"""Data model / database behavior: first-run creation, idempotency, migration.

Verified by reading the real SQLite file back — the schema and rows asserted on
here are read from disk, not echoed from the code that wrote them.
(FR3.1, FR3.3, FR3.6, BR3.1, BR3.3, BR3.4, NFR-R2, AC7.1.1-AC7.1.3)
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db import ANALYSES_COLUMNS, SCHEMA_VERSION, connect, init_db
from app.models import UNKNOWN_PROVIDER

FIXED_CREATED_AT = "2026-09-29T12:00:00Z"
OLD_PROBABILITIES = '{"positive": 0.9, "negative": 0.05, "neutral": 0.05}'

#: The shape this repository shipped before the v1 contract: `intensity` is NOT
#: NULL and `label` carries no CHECK constraint.
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

#: The same shape but with a column the v1 contract requires missing, and the
#: retired column already nullable — one half of the case the rebuild owns.
PRE_V1_MISSING_PROVIDER_DDL = """
CREATE TABLE analyses (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT    NOT NULL,
  label         TEXT    NOT NULL,
  probabilities TEXT    NOT NULL,
  confidence    REAL    NOT NULL,
  intensity     REAL,
  model         TEXT    NOT NULL,
  created_at    TEXT    NOT NULL
)
"""

#: Both migration triggers set at once: `provider` is missing *and* the retired
#: `intensity` still carries NOT NULL. Neither strategy may abort the other
#: (R-01).
PRE_V1_MISSING_PROVIDER_NOT_NULL_DDL = """
CREATE TABLE analyses (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT    NOT NULL,
  label         TEXT    NOT NULL,
  probabilities TEXT    NOT NULL,
  confidence    REAL    NOT NULL,
  intensity     REAL    NOT NULL,
  model         TEXT    NOT NULL,
  created_at    TEXT    NOT NULL
)
"""

_INSERT_PRE_V1_ROW = (
    "INSERT INTO analyses "
    "(text, label, probabilities, confidence, intensity, model, provider, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)

_PRE_V1_ROW = (
    "a row written before v1",
    "positive",
    OLD_PROBABILITIES,
    0.9,
    0.6,
    "dummy-keyword-v1",
    "local-dummy",
    FIXED_CREATED_AT,
)


def _table_names(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row["name"] for row in rows}


def _columns(connection: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(
        row["name"] for row in connection.execute("PRAGMA table_info(analyses)").fetchall()
    )


def _not_null(connection: sqlite3.Connection, column: str) -> bool:
    for row in connection.execute("PRAGMA table_info(analyses)").fetchall():
        if row["name"] == column:
            return bool(row["notnull"])
    raise AssertionError(f"no column named {column!r}")


def _create_pre_v1_store(path: Path, ddl: str, insert_sql: str, values: tuple) -> None:
    """Write a real pre-v1 store straight to disk, with one row in it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute(ddl)
        connection.execute(insert_sql, values)
        connection.commit()
    finally:
        connection.close()


def test_init_creates_the_v1_schema_on_first_run(tmp_db_path):
    """AC7.1.1: a fresh checkout with no `data/` directory reaches a usable state."""
    assert not tmp_db_path.parent.exists()
    assert not tmp_db_path.exists()

    init_db(tmp_db_path)

    assert tmp_db_path.is_file()
    connection = connect(tmp_db_path)
    try:
        assert {"analyses", "schema_meta"} <= _table_names(connection)
        assert _columns(connection) == ANALYSES_COLUMNS
        assert not _not_null(connection, "intensity")
        assert _not_null(connection, "provider")

        version = connection.execute(
            "SELECT value FROM schema_meta WHERE key = 'version'"
        ).fetchone()
        assert version["value"] == str(SCHEMA_VERSION)

        # A new row may leave the retired attribute unset (BR3.4).
        connection.execute(
            "INSERT INTO analyses (text, label, probabilities, confidence, model, "
            "provider, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                "v1 row",
                "neutral",
                OLD_PROBABILITIES,
                0.8,
                "dummy-keyword-v1",
                "offline",
                FIXED_CREATED_AT,
            ),
        )
        assert (
            connection.execute("SELECT intensity FROM analyses WHERE text = 'v1 row'").fetchone()[
                "intensity"
            ]
            is None
        )

        # The `label` domain is enforced by the schema itself, not only by code.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO analyses (text, label, probabilities, confidence, model, "
                "provider, created_at) VALUES (?,?,?,?,?,?,?)",
                (
                    "bad label",
                    "ecstatic",
                    "{}",
                    0.5,
                    "dummy-keyword-v1",
                    "offline",
                    FIXED_CREATED_AT,
                ),
            )
    finally:
        connection.close()


def test_init_is_idempotent(tmp_db_path):
    """Re-running the init step leaves existing rows and the schema intact."""
    init_db(tmp_db_path)
    connection = connect(tmp_db_path)
    try:
        connection.execute(
            "INSERT INTO analyses (text, label, probabilities, confidence, model, "
            "provider, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                "a pre-existing row",
                "neutral",
                OLD_PROBABILITIES,
                0.8,
                "dummy-keyword-v1",
                "offline",
                FIXED_CREATED_AT,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    init_db(tmp_db_path)
    init_db(tmp_db_path)

    connection = connect(tmp_db_path)
    try:
        count = connection.execute("SELECT COUNT(*) AS n FROM analyses").fetchone()["n"]
        assert count == 1
        assert _columns(connection) == ANALYSES_COLUMNS
        meta_rows = connection.execute("SELECT key, value FROM schema_meta").fetchall()
        assert [(row["key"], row["value"]) for row in meta_rows] == [
            ("version", str(SCHEMA_VERSION))
        ]
    finally:
        connection.close()


def test_migration_rebuilds_a_pre_v1_store_and_keeps_every_row(tmp_db_path):
    """AC7.1.3, NFR-R2: an existing store reaches v1 with its rows untouched."""
    _create_pre_v1_store(tmp_db_path, PRE_V1_DDL, _INSERT_PRE_V1_ROW, _PRE_V1_ROW)

    init_db(tmp_db_path)

    connection = connect(tmp_db_path)
    try:
        # The rebuilt table is exactly the v1 shape...
        assert _columns(connection) == ANALYSES_COLUMNS
        assert _not_null(connection, "provider")
        assert not _not_null(connection, "intensity")
        # ...the row survived with the value it already held, un-back-filled...
        row = connection.execute("SELECT * FROM analyses WHERE id = 1").fetchone()
        assert row["text"] == _PRE_V1_ROW[0]
        assert row["label"] == "positive"
        assert row["intensity"] == 0.6
        assert row["provider"] == "local-dummy"
        assert row["created_at"] == FIXED_CREATED_AT
        # ...and a row written after the migration leaves the retired attribute unset.
        connection.execute(
            "INSERT INTO analyses (text, label, probabilities, confidence, model, "
            "provider, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                "v1 row",
                "neutral",
                OLD_PROBABILITIES,
                0.8,
                "dummy-keyword-v1",
                "offline",
                FIXED_CREATED_AT,
            ),
        )
        assert (
            connection.execute("SELECT intensity FROM analyses WHERE text = 'v1 row'").fetchone()[
                "intensity"
            ]
            is None
        )
        assert connection.execute("SELECT COUNT(*) AS n FROM analyses").fetchone()["n"] == 2
    finally:
        connection.close()


def test_migration_rebuilds_a_store_missing_provider_to_the_v1_shape(tmp_path):
    """AC7.1.2, R-04: the missing column is added and the v1 constraints restored."""
    db_path = tmp_path / "pre.db"
    _create_pre_v1_store(
        db_path,
        PRE_V1_MISSING_PROVIDER_DDL,
        "INSERT INTO analyses (text, label, probabilities, confidence, intensity, model, "
        "created_at) VALUES (?,?,?,?,?,?,?)",
        (
            "a row without a provider",
            "neutral",
            OLD_PROBABILITIES,
            0.8,
            0.0,
            "dummy-keyword-v1",
            FIXED_CREATED_AT,
        ),
    )

    init_db(db_path)

    connection = connect(db_path)
    try:
        # The store ends up exactly the v1 relation, not merely readable as one:
        # column order, nullability and the label domain all match the DDL (R-04).
        assert _columns(connection) == ANALYSES_COLUMNS
        assert _not_null(connection, "provider")
        assert not _not_null(connection, "intensity")

        row = connection.execute("SELECT * FROM analyses WHERE id = 1").fetchone()
        assert row["text"] == "a row without a provider"
        assert row["intensity"] == 0.0
        # No engine can be named for the old row, so the recorded sentinel is
        # written rather than a NULL the v1 NOT NULL constraint refuses (R-01, R-02).
        assert row["provider"] == UNKNOWN_PROVIDER

        connection.execute("UPDATE analyses SET provider = ? WHERE id = 1", ("offline",))
        connection.commit()
        assert (
            connection.execute("SELECT provider FROM analyses WHERE id = 1").fetchone()["provider"]
            == "offline"
        )
    finally:
        connection.close()


def test_migration_composes_a_missing_column_and_a_constraint_change(tmp_path):
    """R-01: a store that both lacks `provider` and has `intensity NOT NULL` migrates."""
    db_path = tmp_path / "both_triggers.db"
    _create_pre_v1_store(
        db_path,
        PRE_V1_MISSING_PROVIDER_NOT_NULL_DDL,
        "INSERT INTO analyses (text, label, probabilities, confidence, intensity, model, "
        "created_at) VALUES (?,?,?,?,?,?,?)",
        (
            "a row with both triggers set",
            "positive",
            OLD_PROBABILITIES,
            0.9,
            0.6,
            "dummy-keyword-v1",
            FIXED_CREATED_AT,
        ),
    )

    init_db(db_path)  # must not raise sqlite3.IntegrityError: NOT NULL provider

    connection = connect(db_path)
    try:
        assert _columns(connection) == ANALYSES_COLUMNS
        assert _not_null(connection, "provider")
        assert not _not_null(connection, "intensity")
        row = connection.execute("SELECT * FROM analyses WHERE id = 1").fetchone()
        assert row["text"] == "a row with both triggers set"
        assert row["intensity"] == 0.6
        assert row["provider"] == UNKNOWN_PROVIDER
    finally:
        connection.close()


def test_a_migration_that_cannot_preserve_every_row_fails_loudly(tmp_path):
    """NFR-R2: a schema change keeps existing rows or fails visibly."""
    db_path = tmp_path / "incompatible.db"
    _create_pre_v1_store(
        db_path,
        PRE_V1_DDL,
        _INSERT_PRE_V1_ROW,
        (
            "a row with an unknown label",
            "ecstatic",
            OLD_PROBABILITIES,
            0.5,
            0.0,
            "dummy-keyword-v1",
            "local-dummy",
            FIXED_CREATED_AT,
        ),
    )

    with pytest.raises(sqlite3.IntegrityError):
        init_db(db_path)

    # The failure rolled back: the pre-v1 table and its row are still there.
    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute("SELECT text, label FROM analyses WHERE id = 1").fetchone()
        assert row == ("a row with an unknown label", "ecstatic")
    finally:
        connection.close()
