"""Data model / database behavior: the v3 -> v4 step, its indexes, and read-only.

Every assertion reads the real SQLite file back from disk: the schema objects are
inspected through `sqlite_master`, the rows through a real query, and the
read-only guarantee through a before/after comparison of the row count, the schema
text and a content hash. Nothing here echoes the code that wrote the file.
(`FR5.1`-`FR5.7`, `BR2.7`, `BR5.1`-`BR5.6`, `NFR3`, `NFR-R2`, `AC5.1.1`-`AC5.1.5`,
`AC5.2.1`, `AC5.2.2`)
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from app.db import (
    ANALYSES_COLUMNS,
    ANALYSES_INDEXES,
    SCHEMA_VERSION,
    _rebuild_analyses,
    connect,
    init_db,
)
from app.main import create_app
from tests.conftest import asgi_request

#: The three indexes the step guarantees, matched **by name**. Never "exactly
#: three": `schema_meta` (TEXT PRIMARY KEY) carries an implicit autoindex, so a raw
#: count over `sqlite_master` is never exactly three (`BR5.3`, R-19).
EXPECTED_INDEXES = {
    "idx_analyses_created_at": ("created_at",),
    "idx_analyses_import_id": ("import_id",),
    "idx_analyses_label_created_at": ("label", "created_at"),
}

#: The v3 physical relation: the v1 shape plus the nullable bulk-import grouping
#: column, with no index of any kind.
V3_DDL = """
CREATE TABLE analyses (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT    NOT NULL,
  label         TEXT    NOT NULL CHECK (label IN ('positive','negative','neutral')),
  probabilities TEXT    NOT NULL,
  confidence    REAL    NOT NULL,
  intensity     REAL,
  model         TEXT    NOT NULL,
  provider      TEXT    NOT NULL,
  created_at    TEXT    NOT NULL,
  import_id     TEXT
)
"""

#: The pre-v1 relation, which is the shape that forces the *rebuild* path
#: (`RENAME` -> `CREATE TABLE` -> `COPY` -> `DROP TABLE`) and therefore the one that
#: used to destroy every index (`BR5.4`).
PRE_V1_DDL = """
CREATE TABLE analyses (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  text          TEXT    NOT NULL,
  label         TEXT    NOT NULL CHECK (label IN ('positive','negative','neutral')),
  probabilities TEXT    NOT NULL,
  confidence    REAL    NOT NULL,
  intensity     REAL    NOT NULL,
  model         TEXT    NOT NULL,
  provider      TEXT    NOT NULL,
  created_at    TEXT    NOT NULL,
  import_id     TEXT
)
"""

#: The same relation without the `label` domain, so a store can hold a row the
#: rebuilt relation refuses. That is the "shape the step cannot read" case: the
#: copy aborts, the transaction rolls back and startup halts loudly (`BR5.5`).
PRE_V1_UNDECLARED_LABEL_DDL = PRE_V1_DDL.replace(
    "label         TEXT    NOT NULL CHECK (label IN ('positive','negative','neutral'))",
    "label         TEXT    NOT NULL",
)

_PROBABILITIES = '{"positive": 0.9, "negative": 0.05, "neutral": 0.05}'

_INSERT = (
    "INSERT INTO analyses "
    "(text, label, probabilities, confidence, intensity, model, provider, created_at, import_id) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

_V3_ROWS = (
    (
        "a row written at v3",
        "positive",
        0.90,
        0.60,
        "dummy-keyword-v1",
        "offline",
        "2026-01-01T10:00:00Z",
        None,
    ),
    (
        "another v3 row",
        "negative",
        0.70,
        None,
        "dummy-keyword-v1",
        "offline",
        "2026-01-02T10:00:00Z",
        "imp-1",
    ),
)

#: The same two rows as a pre-v1 store holds them: `intensity` was NOT NULL then,
#: so a pre-v1 row carries a value rather than leaving the retired column unset.
_PRE_V1_ROWS = (
    (
        "a row written before the rebuild",
        "positive",
        0.90,
        0.60,
        "dummy-keyword-v1",
        "offline",
        "2026-01-01T10:00:00Z",
        None,
    ),
    (
        "another pre-v1 row",
        "negative",
        0.70,
        0.10,
        "dummy-keyword-v1",
        "offline",
        "2026-01-02T10:00:00Z",
        "imp-1",
    ),
)


def _write_store(path: Path, ddl: str, rows: tuple = ()) -> None:
    """Write a real store of `ddl` straight to disk, holding `rows`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute(ddl)
        connection.executemany(
            _INSERT,
            [(row[0], row[1], _PROBABILITIES, *row[2:]) for row in rows],
        )
        connection.commit()
    finally:
        connection.close()


@pytest.fixture
def app(tmp_settings):
    """A real application wired to this test's temporary database."""
    return create_app(tmp_settings)


def _index_names(connection: sqlite3.Connection) -> set[str]:
    """Every index name `sqlite_master` records, explicit and implicit alike."""
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'index'").fetchall()
    return {row["name"] for row in rows}


def _index_ddl(connection: sqlite3.Connection, name: str) -> str:
    """The `CREATE INDEX` text `sqlite_master` stores for `name`, or `""`."""
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?", (name,)
    ).fetchone()
    return "" if row is None or row["sql"] is None else str(row["sql"])


def _stored_version(connection: sqlite3.Connection) -> str:
    row = connection.execute("SELECT value FROM schema_meta WHERE key = 'version'").fetchone()
    return row["value"]


def _content_hash(db_path) -> str:
    """A stable digest of every stored row, so an accidental write cannot hide."""
    connection = sqlite3.connect(db_path)
    try:
        digest = hashlib.sha256()
        for row in connection.execute(
            "SELECT id, text, label, probabilities, confidence, model, provider, created_at,"
            " import_id FROM analyses ORDER BY id"
        ):
            digest.update(repr(tuple(row)).encode("utf-8"))
        return digest.hexdigest()
    finally:
        connection.close()


def _schema_digest(db_path) -> str:
    """A digest of the whole recorded schema, so a lost index cannot hide either."""
    connection = sqlite3.connect(db_path)
    try:
        digest = hashlib.sha256()
        for row in connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
        ):
            digest.update(repr(tuple(row)).encode("utf-8"))
        return digest.hexdigest()
    finally:
        connection.close()


def _row_count(db_path) -> int:
    connection = sqlite3.connect(db_path)
    try:
        return connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    finally:
        connection.close()


# -- Additive and idempotent -------------------------------------------------


def test_a_v3_store_is_brought_to_v4_with_every_row_and_column_intact(tmp_path):
    """`BR5.1`, `BR5.5`, `AC5.1.1`: the step is additive, in one transaction."""
    db_path = tmp_path / "v3.db"
    _write_store(db_path, V3_DDL, _V3_ROWS)

    init_db(db_path)

    connection = connect(db_path)
    try:
        assert SCHEMA_VERSION == 4
        assert _stored_version(connection) == "4"
        # No column dropped, renamed or retyped: the relation is unchanged.
        columns = tuple(
            row["name"] for row in connection.execute("PRAGMA table_info(analyses)").fetchall()
        )
        assert columns == ANALYSES_COLUMNS
        rows = connection.execute("SELECT * FROM analyses ORDER BY id").fetchall()
        assert len(rows) == 2
        assert rows[0]["text"] == "a row written at v3"
        assert rows[0]["intensity"] == 0.60
        assert rows[0]["import_id"] is None
        assert rows[1]["text"] == "another v3 row"
        assert rows[1]["import_id"] == "imp-1"
    finally:
        connection.close()


def test_a_store_already_at_v4_is_a_no_op(tmp_path):
    """`BR5.2`, `AC5.1.2`: re-running the step changes and loses nothing."""
    db_path = tmp_path / "twice.db"
    init_db(db_path)

    connection = connect(db_path)
    try:
        connection.execute(
            "INSERT INTO analyses (text, label, probabilities, confidence, model, provider,"
            " created_at, import_id) VALUES (?,?,?,?,?,?,?,?)",
            (
                "kept across restarts",
                "neutral",
                _PROBABILITIES,
                0.5,
                "dummy-keyword-v1",
                "offline",
                "2026-01-01T00:00:00Z",
                None,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    before_rows = _row_count(db_path)
    before_content = _content_hash(db_path)
    before_schema = _schema_digest(db_path)

    init_db(db_path)
    init_db(db_path)

    assert _row_count(db_path) == before_rows == 1
    assert _content_hash(db_path) == before_content
    assert _schema_digest(db_path) == before_schema


def test_the_index_step_runs_on_both_the_fresh_and_the_migrating_path(tmp_path):
    """`BR5.6`, `AC5.1.4`: the index step sits after the migrate-or-create branch."""
    fresh = tmp_path / "fresh.db"
    init_db(fresh)

    migrating = tmp_path / "migrating.db"
    _write_store(migrating, V3_DDL, _V3_ROWS)
    init_db(migrating)

    for path in (fresh, migrating):
        connection = connect(path)
        try:
            names = _index_names(connection)
            for index_name in EXPECTED_INDEXES:
                assert index_name in names, f"{index_name} missing from {path.name}"
        finally:
            connection.close()


def test_the_three_indexes_exist_by_name_with_their_pinned_columns(tmp_path):
    """`BR5.3`, `AC5.2.1`: three named indexes, matched by name and never counted."""
    db_path = tmp_path / "indexed.db"
    _write_store(db_path, V3_DDL, _V3_ROWS)

    init_db(db_path)

    connection = connect(db_path)
    try:
        names = _index_names(connection)
        assert set(EXPECTED_INDEXES) <= names
        for index_name, columns in EXPECTED_INDEXES.items():
            ddl = _index_ddl(connection, index_name)
            assert ddl, f"{index_name} has no recorded DDL"
            assert f"({', '.join(columns)})" in ddl
        # The module publishes the same three names, so the constant and the DDL
        # cannot drift apart.
        assert dict(ANALYSES_INDEXES) == EXPECTED_INDEXES
    finally:
        connection.close()


def test_the_table_rebuild_re_creates_every_index_by_name(tmp_path):
    """`BR5.4`, `AC5.2.2`: the rebuild path re-creates the three indexes explicitly.

    This is the instrument for the dormant loss: `RENAME` -> `CREATE TABLE` ->
    `COPY` -> `DROP TABLE` used to take every index with it, because SQLite's
    `CREATE TABLE` declares no index. The assertion is by name, after a real
    rebuild.
    """
    db_path = tmp_path / "rebuild.db"
    _write_store(db_path, PRE_V1_DDL, _PRE_V1_ROWS)

    init_db(db_path)

    connection = connect(db_path)
    try:
        names = _index_names(connection)
        for index_name in EXPECTED_INDEXES:
            assert index_name in names, f"{index_name} was destroyed by the rebuild"
        # The rebuild preserved every row while it was at it.
        assert connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0] == 2
    finally:
        connection.close()


def test_the_rebuild_issues_the_index_statements_itself_and_leaves_nothing_to_a_later_step(
    tmp_path,
):
    """`BR5.4`, `AC5.2.2`, `FR5.3`: the rebuild creates the three indexes itself.

    The sibling test cannot pin this. It asserts the index names *after*
    `init_db`, but `_ensure_indexes` (`CREATE INDEX IF NOT EXISTS`) runs
    immediately afterwards on both the fresh and the migrating path, so deleting
    the re-creation from `_rebuild_analyses` leaves that suite entirely green.
    Measured: with the three statements removed from the rebuild, all 190 tests
    still pass.

    This test therefore calls the rebuild on its own, with no ensure step in
    reach, and reads the statements it actually issued rather than the schema it
    happened to leave behind.

    Two honest costs of that choice, both accepted. It couples to the private
    `_rebuild_analyses` rather than to a public entry point, so a rename there
    breaks this test — which is the point, since the mechanism is what it pins.
    And it seeds a **v1-shaped** relation, one `init_db` never rebuilds in
    practice, so the rows it copies are not rows the real migration path would
    carry. The sibling test covers the shape the migration actually meets.
    """
    db_path = tmp_path / "mechanism.db"
    _write_store(db_path, V3_DDL, _PRE_V1_ROWS)

    connection = connect(db_path)
    issued: list[str] = []
    try:
        connection.set_trace_callback(issued.append)
        _rebuild_analyses(connection)
        connection.set_trace_callback(None)
        present = _index_names(connection)
    finally:
        connection.close()

    created = [
        statement
        for statement in issued
        if statement.lstrip().upper().startswith("CREATE INDEX") and "analyses" in statement
    ]
    assert created, "the rebuild issued no CREATE INDEX statement of its own"
    for index_name in EXPECTED_INDEXES:
        assert any(index_name in statement for statement in created), (
            f"{index_name} was left to a later step instead of created by the rebuild"
        )
        # And the rebuild alone is sufficient: no ensure step ran to rescue it.
        assert index_name in present


def test_a_store_the_step_cannot_preserve_rolls_back_and_raises_loudly(tmp_path):
    """`BR5.5`, `NFR-R2`, `AC5.1.3`: no partial migration is ever committed."""
    db_path = tmp_path / "unreadable.db"
    # A row whose label the v1 domain refuses: the copy cannot preserve it.
    _write_store(
        db_path,
        PRE_V1_UNDECLARED_LABEL_DDL,
        (
            (
                "a row with an unknown label",
                "ecstatic",
                0.5,
                0.0,
                "dummy-keyword-v1",
                "offline",
                "2026-01-01T10:00:00Z",
                None,
            ),
        ),
    )
    before = _content_hash(db_path)

    with pytest.raises(sqlite3.IntegrityError):
        init_db(db_path)

    # The rollback left the store exactly as it was: the row, and no version bump.
    assert _content_hash(db_path) == before
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            row["name"]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        assert "analyses" in tables
        assert "analyses_pre_v1" not in tables
        assert connection.execute("SELECT label FROM analyses").fetchone()[0] == "ecstatic"
    finally:
        connection.close()


# -- The read-only guarantee --------------------------------------------------


def test_reading_analytics_never_changes_the_store(app, tmp_settings):
    """`BR2.7`, `NFR3`: any number of analytics requests leaves the store identical."""
    _bring_up = asgi_request(app, "GET", "/v1/health")
    assert _bring_up.status_code == 200

    _seed_rows(tmp_settings.db_path)

    before_rows = _row_count(tmp_settings.db_path)
    before_content = _content_hash(tmp_settings.db_path)
    before_schema = _schema_digest(tmp_settings.db_path)
    assert before_rows == 2

    for _ in range(3):
        assert asgi_request(app, "GET", "/v2/analytics/summary").status_code == 200
        assert (
            asgi_request(
                app, "GET", "/v2/analytics/terms", query="from=2026-01-01&to=2026-01-02"
            ).status_code
            == 200
        )
        assert asgi_request(app, "GET", "/v1/analyses").status_code == 200

    assert _row_count(tmp_settings.db_path) == before_rows
    assert _content_hash(tmp_settings.db_path) == before_content
    assert _schema_digest(tmp_settings.db_path) == before_schema


def test_the_analytics_read_path_issues_no_mutating_statement(app, monkeypatch, tmp_settings):
    """`BR2.7`, `BR2.10`, `NFR3`: the read path is SELECT-only, observed on the wire.

    The trace is taken on the very connection the request uses — the one the
    storage seam receives — so this observes the statements the application
    really executed rather than the ones this test would have written.
    """
    assert asgi_request(app, "GET", "/v1/health").status_code == 200
    _seed_rows(tmp_settings.db_path)
    traced: list[str] = []

    class TracingStore:
        """Wraps the real read module and traces the connection it is handed."""

        def __init__(self) -> None:
            from app import analytics

            self._real = analytics.read_summary

        def __call__(self, connection, *args, **kwargs):
            connection.set_trace_callback(traced.append)
            try:
                return self._real(connection, *args, **kwargs)
            finally:
                connection.set_trace_callback(None)

    monkeypatch.setattr("app.routes.read_summary", TracingStore())

    assert (
        asgi_request(
            app, "GET", "/v2/analytics/summary", query="from=2026-01-01&to=2026-01-02"
        ).status_code
        == 200
    )

    assert traced, "the read executed no traced statement at all"
    lowered = [statement.strip().lower() for statement in traced]
    for mutating in ("insert ", "update ", "delete ", "create ", "drop ", "alter ", "replace "):
        assert not any(statement.startswith(mutating) for statement in lowered), lowered


def _seed_rows(db_path) -> None:
    """Write two analyses straight into the store the application serves."""
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            "INSERT INTO analyses (text, label, probabilities, confidence, model, provider,"
            " created_at, import_id) VALUES (?,?,?,?,?,?,?,?)",
            [
                (
                    "wonderful and delightful",
                    "positive",
                    _PROBABILITIES,
                    0.90,
                    "dummy-keyword-v1",
                    "offline",
                    "2026-01-01T09:00:00Z",
                    None,
                ),
                (
                    "awful and terrible",
                    "negative",
                    _PROBABILITIES,
                    0.70,
                    "dummy-keyword-v1",
                    "offline",
                    "2026-01-02T09:00:00Z",
                    None,
                ),
            ],
        )
        connection.commit()
    finally:
        connection.close()
