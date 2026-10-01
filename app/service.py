"""Analysis orchestration and engine resolution.

Single responsibility: turn submitted text into a persisted analysis — reject
input the engine must not see, resolve and call the engine through the
`SentimentClient` interface, and store the validated result. It depends on the
interface and on the repository, never on the API layer, and the dispatcher
never constructs a concrete client it was not handed (W1, BR1.2-BR1.4, BR2.3,
BR4.1, NFR5).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from app.config import Settings
from app.dummy_client import DummySentimentClient
from app.models import AnalysisRecord
from app.repository import insert_analysis
from app.sentiment import SentimentClient, validate_result
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


def analyze_text(
    client: SentimentClient,
    connection: sqlite3.Connection,
    text: str | None,
    now: datetime | None = None,
) -> AnalysisRecord:
    """Analyse `text` with `client` and return the record as persisted (W1).

    The text is validated first, then the engine answers, then the typed result
    is validated (BR2.3) before a row is written — so a refused request leaves
    the store untouched (BR4.1, NFR-R1). The stored record is read back from the
    database rather than echoed.
    """
    cleaned = require_text(text)
    result = client.analyze(cleaned)
    validate_result(result)
    return insert_analysis(connection, cleaned, result, now=now)
