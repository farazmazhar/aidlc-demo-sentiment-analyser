"""Persistence of analyses.

Single responsibility: translate between the sentiment result and the
`analyses` rows, and hand back records that were read back out of the database
rather than echoed from the in-memory payload. Depends on nothing from the
sentiment engine at runtime — it consumes any object exposing the
`SentimentResult` attributes, which is what makes the engine swappable
(BR3.2, BR3.5, NFR5). It also owns the `import_id` grouping key: rows written by
one bulk-import request share it, and `list_analyses_by_import_id` reads exactly
those rows back (FR1.3, FR2.2, FR2.6).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.models import AnalysisRecord

if TYPE_CHECKING:  # pragma: no cover - typing only, no runtime engine dependency
    from app.sentiment import SentimentResult

#: Default page size for the history view (BR3.5, D2). Documented, not implied.
DEFAULT_LIST_LIMIT = 50

#: The retired `intensity` column is deliberately absent: a new row leaves it
#: unset rather than writing a value the v1 contract no longer produces (BR3.4).
#: `import_id` is written only by bulk import; single analysis binds NULL
#: (FR1.3, FR3.1).
_INSERT_SQL = """
INSERT INTO analyses
  (text, label, probabilities, confidence, model, provider, created_at, import_id)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""


def format_timestamp(moment: datetime) -> str:
    """Render `moment` as an ISO 8601 UTC string ending in `Z` (BR3.2)."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def insert_analysis(
    connection: sqlite3.Connection,
    text: str,
    result: SentimentResult,
    now: datetime | None = None,
    import_id: str | None = None,
) -> AnalysisRecord:
    """Store one analysis and return the row as it was persisted.

    `probabilities` is serialised as a JSON object keyed by label, and
    `created_at` is taken from the `now` seam (defaulting to the current UTC
    instant) so timestamps are injectable and deterministic in tests. `import_id`
    groups the rows of one bulk-import request and defaults to `None` for single
    analysis (FR1.3, FR3.1).
    """
    created_at = format_timestamp(now if now is not None else datetime.now(UTC))
    with connection:
        cursor = connection.execute(
            _INSERT_SQL,
            (
                text,
                result.label,
                json.dumps(dict(result.probabilities)),
                result.confidence,
                result.model,
                result.provider,
                created_at,
                import_id,
            ),
        )
        row_id = cursor.lastrowid

    row = connection.execute("SELECT * FROM analyses WHERE id = ?", (row_id,)).fetchone()
    return AnalysisRecord.from_row(row)


def list_analyses(
    connection: sqlite3.Connection, limit: int = DEFAULT_LIST_LIMIT
) -> list[AnalysisRecord]:
    """Return stored analyses newest-first, at most `limit` of them (BR3.5)."""
    rows = connection.execute(
        "SELECT * FROM analyses ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [AnalysisRecord.from_row(row) for row in rows]


def list_analyses_by_import_id(
    connection: sqlite3.Connection, import_id: str
) -> list[AnalysisRecord]:
    """Return the rows persisted under one `import_id`, newest-first (FR2.2, FR2.6).

    Scoped strictly to the grouping key, so rows written by single analysis
    (`import_id IS NULL`) are never returned. An unknown id yields an empty list,
    which the export route turns into a `404` (FR2.4).
    """
    rows = connection.execute(
        "SELECT * FROM analyses WHERE import_id = ? ORDER BY id DESC", (import_id,)
    ).fetchall()
    return [AnalysisRecord.from_row(row) for row in rows]
