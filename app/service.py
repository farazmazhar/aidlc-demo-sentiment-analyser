"""Analysis orchestration and engine resolution.

Single responsibility: turn submitted text into a persisted analysis — reject
input the engine must not see, resolve and call the engine through the
`SentimentClient` interface, and store the validated result. It depends on the
interface and on the repository, never on the API layer, and the dispatcher
never constructs a concrete client it was not handed (W1, BR1.2-BR1.4, BR2.3,
BR4.1, NFR5). The bulk path (`import_texts`) reuses the same per-text seam, one
row at a time, and aggregates the outcome into an `ImportSummary` (FR1.3-FR1.5).
"""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from app.config import Settings
from app.dummy_client import DummySentimentClient
from app.models import AnalysisRecord
from app.repository import insert_analysis
from app.sentiment import LABELS, SentimentClient, SentimentEngineError, validate_result
from app.session_auth import SessionCredential


class InvalidTextError(ValueError):
    """Raised when the submitted text is missing, empty or whitespace-only.

    Rejecting this before the engine is called and before anything is written
    pins the invalid-input boundary of `POST /v1/analyze` (BR4.1, W1 step 2).
    """


class LiveKeyMissingError(RuntimeError):
    """Raised when live mode was requested but no usable key exists.

    This is the explicit refusal that replaced the silent fallback: the request
    fails with an instruction naming the config file, and nothing is stored
    (BR1.4, D1, AC5.2.2).
    """


def effective_connection(
    settings: Settings,
    credential: SessionCredential | None,
    reason: str,
) -> dict[str, object]:
    """Describe the engine the app is actually using right now.

    The single connection-state payload: the health endpoint, the page's
    indicator and the startup log all read this one function, so they cannot
    disagree (NFR6.1). A credential obtained in this session wins over the config
    file; otherwise the config decides; anything else is offline (BR1.2, BR1.3,
    BR1.1). `reason` is reported only when the app is not connected, so the
    payload can never name a live engine and a disconnection at the same time
    (AC5.3.1).
    """
    if credential is not None:
        source: str | None = "session"
    elif settings.mode == "live" and settings.api_key:
        source = "config"
    else:
        source = None

    return {
        "mode": "live" if source is not None else "offline",
        "connected": source is not None,
        "source": source,
        "model": settings.model,
        "reason": None if source is not None else reason,
    }


def get_client(settings: Settings, credential: SessionCredential | None = None) -> SentimentClient:
    """Resolve the engine the app is using (BR1.2, BR1.3, BR1.1, BR1.4).

    This is the only place a concrete client is chosen, so replacing the engine
    never touches the routes, the repository or the page (NFR5). The order is
    the one `rules.md` pins: a usable session credential, then a configured live
    mode with a key, then offline — and a live request with neither raises
    instead of quietly answering from the offline engine.
    """
    if credential is not None:
        return _live_client(credential.api_key, settings.model)
    if settings.mode == "live" and settings.api_key:
        return _live_client(settings.api_key, settings.model)
    if settings.mode == "live":
        raise LiveKeyMissingError(
            "Live mode was requested but no OpenRouter API key is available. "
            f"Put your key in {settings.config_path} or connect from the page."
        )
    return DummySentimentClient()


def _live_client(api_key: str, model: str) -> SentimentClient:
    """Build the live client.

    Imported inside the function so the offline path never even loads the live
    client module (NFR1).
    """
    from app.openrouter_client import OpenRouterJevSentimentClient

    return OpenRouterJevSentimentClient(api_key=api_key, model=model)


def require_text(text: str | None) -> str:
    """Return the trimmed text, or raise `InvalidTextError` (BR4.1).

    Shared by the route and the dispatcher so the invalid-input boundary is
    enforced once, before any engine resolution or store work (W1 step 2).
    """
    cleaned = text.strip() if isinstance(text, str) else ""
    if not cleaned:
        raise InvalidTextError("Text to analyse must not be empty or whitespace-only.")
    return cleaned


@dataclass(frozen=True)
class ImportSummary:
    """The aggregate result of one bulk-import request (FR1.5).

    `import_id` groups every row the request persisted; `imported` and `skipped`
    count the rows, `label_counts` breaks the imported rows down over the closed
    label set (zeros included), and `mean_confidence` is the arithmetic mean of
    the imported rows' confidence values — `None` when nothing was imported, so
    there is no division by zero (A3).
    """

    import_id: str
    imported: int
    skipped: int
    label_counts: dict[str, int] = field(default_factory=dict)
    mean_confidence: float | None = None

    def to_dict(self) -> dict[str, object]:
        """Return the summary as JSON-ready primitives in the pinned key order."""
        return {
            "import_id": self.import_id,
            "imported": self.imported,
            "skipped": self.skipped,
            "label_counts": dict(self.label_counts),
            "mean_confidence": self.mean_confidence,
        }


def new_import_id() -> str:
    """Generate the opaque, server-side grouping key for one import (A1)."""
    return uuid.uuid4().hex


def import_texts(
    client: SentimentClient,
    connection: sqlite3.Connection,
    texts: Iterable[str],
    now: datetime | None = None,
) -> ImportSummary:
    """Analyse and persist `texts` under one `import_id`, skipping the unanalyzable.

    Rows are processed sequentially in request order (NFR7). Blank or
    whitespace-only text is skipped without reaching the engine, and a row whose
    engine call fails is skipped without aborting the request — the successfully
    persisted rows are kept and the others are unaffected (FR1.3, FR1.4). Every
    success travels the same `analyze_text` seam and the same `import_id` (FR1.3).
    """
    import_id = new_import_id()
    imported = 0
    skipped = 0
    confidence_total = 0.0
    label_counts = dict.fromkeys(LABELS, 0)

    for text in texts:
        cleaned = text.strip() if isinstance(text, str) else ""
        if not cleaned:
            skipped += 1
            continue
        try:
            record = analyze_text(client, connection, cleaned, now=now, import_id=import_id)
        except (InvalidTextError, SentimentEngineError):
            skipped += 1
            continue
        imported += 1
        confidence_total += record.confidence
        label_counts[record.label] += 1

    return ImportSummary(
        import_id=import_id,
        imported=imported,
        skipped=skipped,
        label_counts=label_counts,
        mean_confidence=confidence_total / imported if imported else None,
    )


def analyze_text(
    client: SentimentClient,
    connection: sqlite3.Connection,
    text: str | None,
    now: datetime | None = None,
    import_id: str | None = None,
) -> AnalysisRecord:
    """Analyse `text` with `client` and return the record as persisted (W1).

    The text is validated first, then the engine answers, then the typed result
    is validated (BR2.3) before a row is written — so a refused request leaves
    the store untouched (BR4.1, NFR-R1). The stored record is read back from the
    database rather than echoed. `import_id` is threaded through to storage and
    defaults to `None`, which is the single-analysis case (FR1.3).
    """
    cleaned = require_text(text)
    result = client.analyze(cleaned)
    validate_result(result)
    return insert_analysis(connection, cleaned, result, now=now, import_id=import_id)
