"""Persistence of analyses.

Single responsibility: translate between the sentiment result and the
`analyses` rows, and hand back records that were read back out of the database
rather than echoed from the in-memory payload. Depends on nothing from the
sentiment engine at runtime — it consumes any object exposing the
`SentimentResult` attributes, which is what makes the engine swappable
(BR3.2, BR3.5, NFR5).
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
_INSERT_SQL = """
INSERT INTO analyses
  (text, label, probabilities, confidence, model, provider, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""


def format_timestamp(moment: datetime) -> str:
    """Render `moment` as an ISO 8601 UTC string ending in `Z` (BR3.2)."""
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def insert_analysis(
    connection: sqlite3.Connection,
    text: str,
    result: SentimentResult,
    now: datetime | None = None,
) -> AnalysisRecord:
    """Store one analysis and return the row as it was persisted.

    `probabilities` is serialised as a JSON object keyed by label, and
    `created_at` is taken from the `now` seam (defaulting to the current UTC
    instant) so timestamps are injectable and deterministic in tests.
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
