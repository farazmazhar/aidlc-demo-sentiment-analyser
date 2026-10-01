"""Business logic: analysis orchestration and engine resolution.

The stub engines used here are hand-written doubles; the values they supply are
asserted on *after* they travelled through the real repository and back out of
SQLite, so the seams are the ones the app really uses.
(FR2.1, FR2.4, FR3.2, FR4.1, BR1.1-BR1.4, BR2.3, BR4.1, NFR-R1)
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.config import Settings
from app.db import connect, init_db
from app.dummy_client import DummySentimentClient
from app.openrouter_client import OpenRouterJevSentimentClient
from app.repository import list_analyses
from app.sentiment import SentimentClient, SentimentEngineError, SentimentResult
from app.service import (
    InvalidTextError,
    LiveKeyMissingError,
    analyze_text,
    effective_connection,
    get_client,
    require_text,
)
from app.session_auth import SessionCredential

FIXED_NOW = datetime(2026, 9, 29, 12, 0, 0, tzinfo=UTC)


class DuckTypedClient:
    """A minimal engine that satisfies the interface without being a dummy client."""

    def analyze(self, text: str) -> SentimentResult:
        return SentimentResult(
            label="negative",
            probabilities={"positive": 0.1, "negative": 0.8, "neutral": 0.1},
            confidence=0.8,
            model="stub-engine-v9",
            provider="stub-provider",
        )


class IncompleteClient:
    """An engine that answers with a fragment instead of a typed decision."""

    def analyze(self, text: str) -> SentimentResult:
        return SentimentResult(
            label="negative",
            probabilities={"positive": 0.1, "negative": 0.9},  # `neutral` missing
            confidence=0.9,
            model="stub-engine-v9",
            provider="stub-provider",
        )


class UnsupportedLabelClient:
    """An engine that answers with a label outside the closed three-value set."""

    def analyze(self, text: str) -> SentimentResult:
        return SentimentResult(
            label="ecstatic",
            probabilities={"positive": 0.1, "negative": 0.1, "neutral": 0.8},
            confidence=0.8,
            model="stub-engine-v9",
            provider="stub-provider",
        )


def _row_count(connection) -> int:
    return connection.execute("SELECT COUNT(*) AS n FROM analyses").fetchone()["n"]


def _credential() -> SessionCredential:
    return SessionCredential(api_key="sk-or-v1-session", obtained_at=FIXED_NOW)


def test_invalid_text_is_refused_before_the_engine_and_the_store(tmp_db_path):
    """BR4.1: whitespace-only or missing text never reaches the engine or the store."""
    init_db(tmp_db_path)
    connection = connect(tmp_db_path)
    try:
        assert _row_count(connection) == 0

        for invalid_text in ("", "   ", "\n\t ", None):
            with pytest.raises(InvalidTextError):
                require_text(invalid_text)
            with pytest.raises(InvalidTextError):
                analyze_text(DummySentimentClient(), connection, invalid_text, now=FIXED_NOW)

        assert _row_count(connection) == 0
    finally:
        connection.close()


def test_analysis_persists_and_returns_the_stored_record(tmp_db_path):
    """FR4.1: one analysis lands exactly one stored row and returns that row."""
    init_db(tmp_db_path)
    connection = connect(tmp_db_path)
    try:
        record = analyze_text(
            DummySentimentClient(), connection, "  I love this app  ", now=FIXED_NOW
        )

        assert _row_count(connection) == 1
        assert record.text == "I love this app"  # stored stripped
        assert record.label == "positive"
        assert record.created_at == "2026-09-29T12:00:00Z"
        assert record.probabilities == {
            "positive": 0.85,
            "negative": 0.05,
            "neutral": 0.10,
        }
        assert [item.to_dict() for item in list_analyses(connection)] == [record.to_dict()]
    finally:
        connection.close()


def test_a_different_engine_reaches_storage_behind_the_interface(tmp_db_path):
    """FR2.1: the dispatcher only ever sees the interface, never a concrete client."""
    init_db(tmp_db_path)
    connection = connect(tmp_db_path)
    try:
        stub = DuckTypedClient()
        assert isinstance(stub, SentimentClient)

        record = analyze_text(stub, connection, "a wholly unremarkable sentence")

        stored = list_analyses(connection)[0]
        assert stored.id == record.id
        assert stored.label == "negative"
        assert stored.probabilities == {"positive": 0.1, "negative": 0.8, "neutral": 0.1}
        assert stored.confidence == 0.8
        assert stored.model == "stub-engine-v9"
        assert stored.provider == "stub-provider"
    finally:
        connection.close()


@pytest.mark.parametrize("client", [IncompleteClient(), UnsupportedLabelClient()])
def test_an_invalid_result_is_refused_and_nothing_is_stored(tmp_db_path, client):
    """BR2.3: a fragment or an unknown label is a failure, never a stored guess."""
    init_db(tmp_db_path)
    connection = connect(tmp_db_path)
    try:
        with pytest.raises(SentimentEngineError):
            analyze_text(client, connection, "text", now=FIXED_NOW)

        assert _row_count(connection) == 0
    finally:
        connection.close()


def test_get_client_resolves_the_credential_precedence(tmp_path):
    """BR1.1-BR1.4: session credential, then configured key, then offline, then refuse."""
    offline = Settings(
        mode="offline", db_path=tmp_path / "a.db", config_path=tmp_path / "config.local.toml"
    )
    configured = Settings(
        mode="live",
        api_key="sk-or-v1-from-config",
        db_path=tmp_path / "b.db",
        config_path=tmp_path / "config.local.toml",
    )
    requested_without_key = Settings(
        mode="live",
        api_key=None,
        db_path=tmp_path / "c.db",
        config_path=tmp_path / "config.local.toml",
    )

    assert isinstance(get_client(offline), DummySentimentClient)

    # A session credential activates the live engine regardless of the file's mode.
    session_client = get_client(offline, _credential())
    assert isinstance(session_client, OpenRouterJevSentimentClient)
    assert "sk-or-v1-session" not in repr(session_client)

    assert isinstance(get_client(configured), OpenRouterJevSentimentClient)

    with pytest.raises(LiveKeyMissingError) as excinfo:
        get_client(requested_without_key)
    assert "config.local.toml" in str(excinfo.value)


def test_effective_connection_is_the_one_connection_payload(tmp_path):
    """NFR6.1: the health endpoint, the page and the log read one payload."""
    offline = Settings(mode="offline", db_path=tmp_path / "a.db")
    configured = Settings(mode="live", api_key="sk-or-v1-from-config", db_path=tmp_path / "b.db")
    requested_without_key = Settings(mode="live", api_key=None, db_path=tmp_path / "c.db")

    idle = effective_connection(offline, None, "Not connected to OpenRouter.")
    assert idle["mode"] == "offline"
    assert idle["connected"] is False
    assert idle["source"] is None
    assert idle["reason"] == "Not connected to OpenRouter."

    from_config = effective_connection(configured, None, "")
    assert from_config["mode"] == "live"
    assert from_config["source"] == "config"

    from_session = effective_connection(requested_without_key, _credential(), "")
    assert from_session["mode"] == "live"
    assert from_session["source"] == "session"

    # A requested live mode without a key still reports the offline engine,
    # because that is the engine the app is actually running (BR1.1).
    unusable = effective_connection(requested_without_key, None, "…")
    assert unusable["mode"] == "offline"
    assert unusable["connected"] is False

    # A reason is reported only when the app is not connected, so a connected
    # payload can never also say it is disconnected (AC5.3.1).
    assert from_config["reason"] is None
    assert from_session["reason"] is None
    assert unusable["reason"] == "…"
