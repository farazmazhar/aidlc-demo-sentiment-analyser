"""SQLite connection handling, schema creation and the in-place migration.

Single responsibility: own the shape and lifecycle of the local database file
(`data/sentiment.db`) so that a fresh checkout reaches a usable state with no
manual setup step, and a store written before the v1 contract is brought up to
it without losing a row. (FR3.1, FR3.3, FR3.6, BR3.1, BR3.3, NFR-R2)

Schema history, recorded in `schema_meta`:

* version 1 — the pre-v1 shape: `intensity REAL NOT NULL`, no migration step.
* version 2 — the v1 contract shape: `provider` present and NOT NULL,
  `intensity` nullable so a new row can leave the retired attribute unset while
  a pre-v1 row keeps the value it already holds (BR3.4, AC7.1.3).
* version 3 — the bulk-import shape: a nullable `import_id TEXT` groups the rows
  persisted by one import request and is NULL for single-analysis rows
  (FR3.1, FR3.3).
* version 4 — the analytics-read shape: **no column changes at all**, only the
  three named indexes the analytics read path relies on. The step is additive
  and idempotent (FR5.1, FR5.4).

Any existing store that is not already exactly the v1 relation is rebuilt with
the v1 DDL, so the physical constraints — `provider NOT NULL`, `intensity`
nullable and the `label` domain — always match the schema version recorded in
`schema_meta` (AC7.1.2, R-04). The rebuild composes with the missing-column
case: a pre-v1 store that lacks `provider` *and* carries `intensity NOT NULL`
first gains the missing column and is then rebuilt, so neither trigger aborts
the other (R-01).

SQLite's `CREATE TABLE` declares no index, so the rebuild path used to destroy
every index on `analyses` with the table it dropped. The indexes are therefore
created as explicit statements *after* the migrate-or-create branch, which is
the same placement `schema_meta` already uses, and `_rebuild_analyses` re-creates
all three by name as steps after the copy (FR5.2, FR5.3, FR5.5).

**Connection model (the thread-affinity decision, stated here rather than
inherited).** :func:`connect` is the only `sqlite3.connect` site in the
repository, so it is where the thread-affinity choice belongs: the connection is
opened with `check_same_thread=False`. That flag is only safe because of the
invariant below, which the HTTP edge (`get_connection`) upholds and which a later
change must not break:

* exactly one connection is created per request and is closed in that request's
  own `finally`;
* no connection is ever cached, pooled, stored on a module global, or shared
  between two concurrent requests.

If pooling or a shared connection is ever introduced, the same-thread guard must
be re-enabled or the sharing made thread-safe. The flag is not a licence to share
one connection across threads (FR1.6, R-01).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.models import UNKNOWN_PROVIDER

#: Schema version recorded in `schema_meta`; a hook for later migrations.
SCHEMA_VERSION = 4

#: The v1 physical schema. `intensity` stays for pre-v1 rows but is nullable, so
#: new rows simply do not set it (BR3.4). `import_id` is nullable: it is set only
#: when a row is written by bulk import (FR3.1).
CREATE_ANALYSES_TABLE = """
CREATE TABLE IF NOT EXISTS analyses (
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

CREATE_SCHEMA_META_TABLE = """
CREATE TABLE IF NOT EXISTS schema_meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
)
"""

#: Column order of the `analyses` table, pinned so tests can assert the contract.
ANALYSES_COLUMNS = (
    "id",
    "text",
    "label",
    "probabilities",
    "confidence",
    "intensity",
    "model",
    "provider",
    "created_at",
    "import_id",
)

#: The columns the v1 DDL declares NOT NULL. The primary key (`id`), the retired
#: `intensity` and the bulk-import grouping key (`import_id`) are the only columns
#: allowed to hold NULL.
_V1_NOT_NULL_COLUMNS = frozenset(
    {"text", "label", "probabilities", "confidence", "model", "provider", "created_at"}
)

#: The three indexes the analytics read path depends on, mapped to the columns each
#: one covers (FR5.2). They are matched **by name**, never counted: `schema_meta`
#: carries an implicit `sqlite_autoindex_schema_meta_1`, so "exactly three
#: indexes" is false against a real store (BR5.3, R-19).
ANALYSES_INDEXES: dict[str, tuple[str, ...]] = {
    "idx_analyses_created_at": ("created_at",),
    "idx_analyses_import_id": ("import_id",),
    "idx_analyses_label_created_at": ("label", "created_at"),
}

#: Marker that the v1 DDL actually enforces the label domain at the schema level.
_V1_LABEL_CHECK = "CHECK (label IN"

#: `ALTER TABLE ... ADD COLUMN` statements, one per column of the pinned order.
#:
#: A column added to a table that already holds rows cannot carry NOT NULL
#: without a default, so this preparatory step adds it nullable and every
#: existing row stays readable (AC7.1.2). It is only ever a staging step before
#: the rebuild restores the full v1 shape, so the nullable intermediate state
#: never survives startup (R-04). These are literal statements, never
#: string-built from input.
_ADD_COLUMN_SQL: dict[str, str] = {
    "id": "ALTER TABLE analyses ADD COLUMN id INTEGER",
    "text": "ALTER TABLE analyses ADD COLUMN text TEXT",
    "label": "ALTER TABLE analyses ADD COLUMN label TEXT",
    "probabilities": "ALTER TABLE analyses ADD COLUMN probabilities TEXT",
    "confidence": "ALTER TABLE analyses ADD COLUMN confidence REAL",
    "intensity": "ALTER TABLE analyses ADD COLUMN intensity REAL",
    "model": "ALTER TABLE analyses ADD COLUMN model TEXT",
    "provider": "ALTER TABLE analyses ADD COLUMN provider TEXT",
    "created_at": "ALTER TABLE analyses ADD COLUMN created_at TEXT",
    "import_id": "ALTER TABLE analyses ADD COLUMN import_id TEXT",
}

_MOVE_OLD_TABLE_ASIDE = "ALTER TABLE analyses RENAME TO analyses_pre_v1"

#: Copy every row into the freshly created v1 table. `provider` is the one
#: column a pre-v1 store can lack: no engine can be named for its rows, so the
#: recorded `unknown` sentinel is written rather than a NULL the v1 NOT NULL
#: constraint refuses (R-01, R-02). The statement is a literal; only the
#: sentinel travels as a bound parameter.
_COPY_ROWS_INTO_V1_TABLE = (
    "INSERT INTO analyses "
    "(id, text, label, probabilities, confidence, intensity, model, provider, "
    "created_at, import_id) "
    "SELECT id, text, label, probabilities, confidence, intensity, model, "
    "COALESCE(provider, ?), created_at, import_id FROM analyses_pre_v1"
)

_DROP_OLD_TABLE = "DROP TABLE analyses_pre_v1"

#: The three index-creating statements, one per named index. SQLite's
#: `CREATE TABLE` has no index declaration, so these are statements in their own
#: right; the names are interpolated into the DDL because an index name cannot be
#: a bound parameter, and the column lists come from `ANALYSES_INDEXES` rather
#: than from any caller (FR5.2, FR5.3).
_CREATE_INDEX_SQL = (
    "CREATE INDEX {name} ON analyses ({columns})",
    "CREATE INDEX IF NOT EXISTS {name} ON analyses ({columns})",
)


def _index_statements(template: str) -> list[str]:
    """Render every named index as one literal `CREATE INDEX` statement."""
    return [
        template.format(name=name, columns=", ".join(columns))
        for name, columns in ANALYSES_INDEXES.items()
    ]


#: Used by `_ensure_indexes`, which must be a no-op on an already-v4 store
#: (`BR5.2`).
_CREATE_INDEX_IF_ABSENT = tuple(_index_statements(_CREATE_INDEX_SQL[1]))

#: Used by `_rebuild_analyses`, which has just dropped the table the indexes hung
#: off, so the names are free and a plain `CREATE INDEX` both re-creates them and
#: proves they really were destroyed (`BR5.4`).
_CREATE_INDEX = tuple(_index_statements(_CREATE_INDEX_SQL[0]))

_RECORD_SCHEMA_VERSION = (
    "INSERT INTO schema_meta (key, value) VALUES ('version', ?) "
    "ON CONFLICT(key) DO UPDATE SET value = excluded.value"
)


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open (creating if needed) the SQLite database at `db_path`.

    The parent directory is created on demand so the caller never has to
    prepare `data/` by hand (NFR6). Rows come back as `sqlite3.Row`, which the
    repository maps to `AnalysisRecord`.

    **Thread affinity is decided here, deliberately.** The connection is opened
    with `check_same_thread=False`, because FastAPI runs a synchronous dependency
    and a synchronous handler on worker threads that are not guaranteed to be the
    same one, so the driver's default same-thread guard would refuse a connection
    the application legitimately hands between threads. The choice is safe only
    while the connection stays **request-scoped**: one connection per request,
    closed in that request's own `finally`, never cached, pooled, stored on a
    module global or shared between two concurrent requests (the invariant the
    module docstring records). Re-enable the guard or make any sharing
    thread-safe before introducing pooling (FR1.6, R-01).
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str | Path) -> None:
    """Create the database file and bring its schema to the current version.

    Idempotent: runs on every application start (from the lifespan). A new store
    is created directly at the current shape; an existing one is migrated in
    place, keeping every row. The index step runs **after** the migrate-or-create
    branch — the placement `schema_meta` already uses — so both paths end up with
    the three named indexes (FR5.5, BR5.6). The whole step runs in one
    transaction and the version bump lands inside it, so a failure stops startup
    loudly instead of leaving a half-migrated file (BR3.1, BR3.3, BR5.5, NFR-R2).
    """
    connection = connect(db_path)
    try:
        connection.execute("BEGIN")
        try:
            if _table_exists(connection, "analyses"):
                _migrate_analyses(connection)
            else:
                connection.execute(CREATE_ANALYSES_TABLE)
            connection.execute(CREATE_SCHEMA_META_TABLE)
            _ensure_indexes(connection)
            connection.execute(_RECORD_SCHEMA_VERSION, (str(SCHEMA_VERSION),))
        except BaseException:
            connection.rollback()
            raise
        connection.commit()
    finally:
        connection.close()


def _ensure_indexes(connection: sqlite3.Connection) -> None:
    """Create the three named indexes if the store does not already carry them.

    Placed after the migrate-or-create branch so the fresh path and the migrating
    path both end up indexed, and written with `IF NOT EXISTS` so a store already
    at v4 changes nothing (BR5.2, BR5.6).
    """
    for statement in _CREATE_INDEX_IF_ABSENT:
        connection.execute(statement)


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    """Whether a table of `name` exists in this database."""
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone()
    return row is not None


def _column_info(connection: sqlite3.Connection) -> dict[str, tuple[str, bool]]:
    """Map each existing column, in order, to `(declared type, NOT NULL)`."""
    rows = connection.execute("PRAGMA table_info(analyses)").fetchall()
    return {str(row["name"]): (str(row["type"]).upper(), bool(row["notnull"])) for row in rows}


def _create_sql(connection: sqlite3.Connection) -> str:
    """The `CREATE TABLE analyses` text SQLite stores, or `""` when absent."""
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'analyses'"
    ).fetchone()
    if row is None or row["sql"] is None:  # pragma: no cover - a table always has its DDL text
        return ""
    return str(row["sql"])


def _is_v1_shape(connection: sqlite3.Connection, info: dict[str, tuple[str, bool]]) -> bool:
    """Whether the physical `analyses` table is already exactly the v1 relation.

    Checks the pinned column order, every column's NOT NULL flag, and that the
    label domain is enforced. A store that is merely *readable* as v1 — a column
    appended nullable by a previous in-place migration, say — is not the v1
    relation and is rebuilt so the recorded schema version stays truthful
    (AC7.1.2, R-04).
    """
    if tuple(info) != ANALYSES_COLUMNS:
        return False
    for column in ANALYSES_COLUMNS:
        if info[column][1] != (column in _V1_NOT_NULL_COLUMNS):
            return False
    return _V1_LABEL_CHECK in _create_sql(connection)


def _migrate_analyses(connection: sqlite3.Connection) -> None:
    """Bring an existing `analyses` table to the v1 shape, keeping every row.

    The two strategies compose in one order (R-01): a required column that is
    missing is added in place first, nullable, so the rebuild's row copy can
    reference it; then, unless the table is already exactly v1, it is rebuilt
    with the v1 DDL and every row is copied across. A store that both lacks
    `provider` and carries `intensity NOT NULL` therefore migrates without the
    copy aborting on either trigger.
    """
    info = _column_info(connection)
    if _is_v1_shape(connection, info):
        return

    for column in ANALYSES_COLUMNS:
        if column not in info:
            connection.execute(_ADD_COLUMN_SQL[column])

    _rebuild_analyses(connection)


def _rebuild_analyses(connection: sqlite3.Connection) -> None:
    """Replace `analyses` with the v1 DDL, copying every existing row across.

    A row with no `provider` gets the recorded `unknown` sentinel; every other
    value is copied unchanged, so a pre-v1 row keeps the `intensity` it already
    holds (BR3.4, AC7.1.3).

    Dropping the old table takes its indexes with it, and `CREATE TABLE` declares
    no index, so all three are re-created **explicitly as statements after the
    copy**. Without this the rebuild silently destroyed every index on `analyses`
    with no warning possible (FR5.3, BR5.4).
    """
    connection.execute(_MOVE_OLD_TABLE_ASIDE)
    connection.execute(CREATE_ANALYSES_TABLE)
    connection.execute(_COPY_ROWS_INTO_V1_TABLE, (UNKNOWN_PROVIDER,))
    connection.execute(_DROP_OLD_TABLE)
    for statement in _CREATE_INDEX:
        connection.execute(statement)
