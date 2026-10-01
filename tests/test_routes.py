"""API / endpoint: the versioned `/v1` surface over real storage.

These are the acceptance tests for the HTTP contract, and they are written
against the contract's stated behaviour: paths, schemas, statuses and the single
envelope. Every request goes through the real ASGI application (routing,
validation, handler, service, repository, SQLite) and every assertion is on the
parsed response or on a row read back from the database.
(FR4.1-FR4.6, FR1.3, FR1.6, BR3.5, BR3.6, BR4.1-BR4.4, AC2.1.2, AC2.2.1,
AC2.2.2, AC4.1.1-AC4.1.4, AC5.2.2, AC5.3.1)
"""

from __future__ import annotations

import re
import sqlite3

import pytest

from app.config import Settings
from app.main import create_app
from app.models import UNKNOWN_PROVIDER
from tests.conftest import asgi_request

ISO_8601_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

#: The contract's record field set: no `intensity` (BR3.4, AC2.1.2); the additive
#: `import_id` is null for single analyses (FR3.2).
RECORD_FIELDS = {
    "id",
    "text",
    "label",
    "probabilities",
    "confidence",
    "model",
    "provider",
    "created_at",
    "import_id",
}

#: The contract's error envelope: exactly these two keys (BR4.3).
ENVELOPE_FIELDS = {"code", "message"}


@pytest.fixture
def app(tmp_settings):
    """A real application wired to this test's temporary database."""
    return create_app(tmp_settings)


@pytest.fixture
def live_app_without_key(tmp_path):
    """An application that requested live mode but has no usable key (BR1.4)."""
    return create_app(
        Settings(
            mode="live",
            api_key=None,
            db_path=tmp_path / "sentiment.db",
            config_path=tmp_path / "config.local.toml",
        )
    )


def _row_count(db_path) -> int:
    connection = sqlite3.connect(db_path)
    try:
        return connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    finally:
        connection.close()


#: A store written before `provider` existed — a shape the startup migration
#: brings to v1 while preserving every row (AC7.1.2, R-01, R-04).
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


def _write_legacy_store_without_provider(db_path) -> None:
    """Write a real pre-v1 store whose `provider` column does not exist yet."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(PRE_V1_MISSING_PROVIDER_DDL)
        connection.execute(
            "INSERT INTO analyses (text, label, probabilities, confidence, intensity, "
            "model, created_at) VALUES (?,?,?,?,?,?,?)",
            (
                "a row without a provider",
                "neutral",
                '{"positive": 0.1, "negative": 0.1, "neutral": 0.8}',
                0.8,
                0.0,
                "dummy-keyword-v1",
                "2026-09-29T12:00:00Z",
            ),
        )
        connection.commit()
    finally:
        connection.close()


def test_v1_analyze_returns_the_stored_record_field_set(app, tmp_settings):
    """`POST /v1/analyze` stores the text and returns exactly the stored record."""
    response = asgi_request(app, "POST", "/v1/analyze", json_body={"text": "I love this"})

    assert response.status_code == 200
    assert set(response.body) == RECORD_FIELDS
    assert "intensity" not in response.body
    assert response.body["id"] == 1
    assert response.body["text"] == "I love this"
    assert response.body["label"] == "positive"
    assert sorted(response.body["probabilities"]) == ["negative", "neutral", "positive"]
    assert response.body["probabilities"] == {
        "positive": 0.85,
        "negative": 0.05,
        "neutral": 0.10,
    }
    assert response.body["confidence"] == 0.85
    assert response.body["model"] == "dummy-keyword-v1"
    assert response.body["provider"] == "offline"
    assert response.body["import_id"] is None  # single analysis: additive null (FR3.2)
    assert ISO_8601_UTC.match(response.body["created_at"])

    # The same record is what the history route reads back out of SQLite.
    history = asgi_request(app, "GET", "/v1/analyses")
    assert history.body == [response.body]
    assert _row_count(tmp_settings.db_path) == 1


def test_v1_analyze_refuses_empty_text_and_stores_nothing(app, tmp_settings):
    """Empty or whitespace-only text is a 422 envelope and writes no row (BR4.1)."""
    for json_body in ({"text": ""}, {"text": "   "}, {}):
        response = asgi_request(app, "POST", "/v1/analyze", json_body=json_body)

        assert response.status_code == 422
        assert set(response.body) == ENVELOPE_FIELDS
        assert response.body["code"] in {"INVALID_TEXT", "VALIDATION_FAILED"}
        assert response.body["message"]

    assert _row_count(tmp_settings.db_path) == 0


def test_unknown_request_body_fields_are_refused_through_the_envelope(app, tmp_settings):
    """The contract sets `additionalProperties: false`, so an extra field is a refusal (BR4.3)."""
    response = asgi_request(app, "POST", "/v1/analyze", json_body={"text": "hi", "extra": 123})

    assert response.status_code == 422
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "VALIDATION_FAILED"
    assert "extra" in response.body["message"]
    # A refused body writes nothing.
    assert _row_count(tmp_settings.db_path) == 0

    # The declared body itself still works.
    accepted = asgi_request(app, "POST", "/v1/analyze", json_body={"text": "hi"})
    assert accepted.status_code == 200
    assert accepted.body["text"] == "hi"


def test_a_body_that_is_not_the_declared_object_is_refused(app, tmp_settings):
    """The contract's body is a JSON object; an absent or non-object body is a 422 envelope."""
    absent = asgi_request(app, "POST", "/v1/analyze")
    not_an_object = asgi_request(app, "POST", "/v1/analyze", json_body="just a string")

    for response in (absent, not_an_object):
        assert response.status_code == 422
        assert set(response.body) == ENVELOPE_FIELDS
        assert response.body["code"] == "VALIDATION_FAILED"

    assert _row_count(tmp_settings.db_path) == 0


def test_v1_analyses_is_a_bare_array_newest_first(app):
    """`GET /v1/analyses` returns the records themselves, newest first (AC4.1.1)."""
    empty = asgi_request(app, "GET", "/v1/analyses")
    assert empty.status_code == 200
    assert empty.body == []

    submitted = [f"analysis number {index}" for index in range(4)]
    for text in submitted:
        assert asgi_request(app, "POST", "/v1/analyze", json_body={"text": text}).status_code == 200

    response = asgi_request(app, "GET", "/v1/analyses")

    assert response.status_code == 200
    assert isinstance(response.body, list)
    assert [record["text"] for record in response.body] == list(reversed(submitted))
    assert [record["id"] for record in response.body] == [4, 3, 2, 1]
    assert set(response.body[0]) == RECORD_FIELDS


def test_a_migrated_row_without_a_provider_is_reported_as_unknown(tmp_path):
    """A migrated row's unknown provider is the recorded sentinel, never `None` (R-02)."""
    db_path = tmp_path / "sentiment.db"
    _write_legacy_store_without_provider(db_path)

    migrated = create_app(
        Settings(
            mode="offline",
            api_key=None,
            db_path=db_path,
            config_path=tmp_path / "config.local.toml",
        )
    )
    response = asgi_request(migrated, "GET", "/v1/analyses")

    assert response.status_code == 200
    assert len(response.body) == 1
    record = response.body[0]
    # The record keeps its pinned field set; only the value is unknown.
    assert set(record) == RECORD_FIELDS
    # A schema-conformant string the contract records, not JSON null and not the
    # literal string `"None"` (R-02).
    assert record["provider"] == UNKNOWN_PROVIDER
    assert record["text"] == "a row without a provider"
    assert record["label"] == "neutral"


def test_v1_analyses_honours_the_limit_and_applies_the_documented_default(app):
    """`limit=n` returns at most n rows; an absent limit applies 50 (BR3.5, D2)."""
    from app.repository import DEFAULT_LIST_LIMIT

    assert DEFAULT_LIST_LIMIT == 50
    for index in range(3):
        asgi_request(app, "POST", "/v1/analyze", json_body={"text": f"entry {index}"})

    assert len(asgi_request(app, "GET", "/v1/analyses", query="limit=2").body) == 2
    assert len(asgi_request(app, "GET", "/v1/analyses", query="limit=1").body) == 1
    # An absent limit is the named default, not an implementer's choice.
    defaulted = asgi_request(app, "GET", "/v1/analyses").body
    assert len(defaulted) == 3
    assert len(asgi_request(app, "GET", "/v1/analyses", query="limit=50").body) == 3


def test_v1_analyses_rejects_a_limit_below_one_or_not_a_number(app):
    """A bad limit is `422 VALIDATION_FAILED` and is never silently clamped (BR3.6)."""
    for query in ("limit=0", "limit=-1", "limit=abc"):
        response = asgi_request(app, "GET", "/v1/analyses", query=query)

        assert response.status_code == 422
        assert set(response.body) == ENVELOPE_FIELDS
        assert response.body["code"] == "VALIDATION_FAILED"
        assert "limit" in response.body["message"]


def test_v1_health_reports_the_active_engine_and_connection_state(app, tmp_path):
    """`/v1/health` reports the mode, the flag and a reason only when offline (AC5.3.1)."""
    offline = asgi_request(app, "GET", "/v1/health")

    assert offline.status_code == 200
    assert set(offline.body) == {"mode", "connected", "reason"}
    assert offline.body["mode"] == "offline"
    assert offline.body["connected"] is False
    assert offline.body["reason"]

    live_app = create_app(
        Settings(
            mode="live",
            api_key="sk-or-v1-not-used-here",
            db_path=tmp_path / "live.db",
            config_path=tmp_path / "config.local.toml",
        )
    )
    live = asgi_request(live_app, "GET", "/v1/health")

    assert live.body["mode"] == "live"
    assert live.body["connected"] is True
    # The contract's `Health.reason` is present when not connected, so a connected
    # payload must not carry a "not connected" reason (AC5.3.1).
    assert set(live.body) == {"mode", "connected"}
    # Never credential material.
    assert "sk-or-v1-not-used-here" not in str(live.body)


def test_live_attempt_without_a_key_is_refused_with_an_instruction(live_app_without_key, tmp_path):
    """A live attempt with no usable key is 503 LIVE_KEY_MISSING (BR1.4, D1, AC5.2.2)."""
    response = asgi_request(
        live_app_without_key, "POST", "/v1/analyze", json_body={"text": "hello"}
    )

    assert response.status_code == 503
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "LIVE_KEY_MISSING"
    assert "config.local.toml" in response.body["message"]
    assert _row_count(tmp_path / "sentiment.db") == 0

    # The health endpoint already says the app is offline before the attempt, and
    # the reason names no credential material.
    health = asgi_request(live_app_without_key, "GET", "/v1/health").body
    assert set(health) == {"mode", "connected", "reason"}
    assert health["mode"] == "offline"
    assert health["connected"] is False


def test_invalid_text_is_still_refused_before_the_live_key_refusal(live_app_without_key):
    """Input validation comes first in W1, even when live mode is also unusable."""
    response = asgi_request(live_app_without_key, "POST", "/v1/analyze", json_body={"text": "  "})

    assert response.status_code == 422
    assert response.body["code"] == "INVALID_TEXT"


def test_a_live_engine_failure_is_answered_in_the_envelope(app, monkeypatch):
    """BR4.3: a non-auth live failure is a 503 with its own code, not a bare 500."""
    from app.sentiment import SentimentEngineError

    class FailingClient:
        """Stands in for a live client whose provider cannot be reached."""

        def analyze(self, text: str):
            raise SentimentEngineError("The sentiment engine could not be reached.")

    monkeypatch.setattr("app.routes.get_client", lambda settings, credential=None: FailingClient())

    response = asgi_request(app, "POST", "/v1/analyze", json_body={"text": "hello"})

    assert response.status_code == 503
    assert set(response.body) == ENVELOPE_FIELDS
    assert response.body["code"] == "SENTIMENT_ENGINE_ERROR"
    assert response.body["message"]
    # The failure names no internal detail and stores nothing.
    assert "Traceback" not in response.body["message"]


def test_the_server_binds_loopback_only():
    """BR5.2, NFR5.1: the one bind constant is the loopback address, never a public one."""
    from app.main import HOST, PORT

    assert HOST == "127.0.0.1"
    assert isinstance(PORT, int)


def test_pre_v1_data_paths_are_no_longer_served(app):
    """The unversioned data routes are gone; the surface is `/v1` only (BR4.2)."""
    assert asgi_request(app, "GET", "/analyses").status_code == 404
    assert asgi_request(app, "GET", "/health").status_code == 404
    assert asgi_request(app, "POST", "/analyze", json_body={"text": "hi"}).status_code == 404
    # The page and its assets stay unversioned.
    assert asgi_request(app, "GET", "/").status_code == 200


def test_every_app_raised_failure_uses_the_one_envelope(app, live_app_without_key):
    """Every refusal the app raises carries exactly `{code, message}` (BR4.3)."""
    failures = [
        asgi_request(app, "POST", "/v1/analyze", json_body={"text": ""}),
        asgi_request(app, "GET", "/v1/analyses", query="limit=0"),
        asgi_request(live_app_without_key, "POST", "/v1/analyze", json_body={"text": "hello"}),
    ]

    for response in failures:
        assert set(response.body) == ENVELOPE_FIELDS
        assert isinstance(response.body["code"], str)
        assert isinstance(response.body["message"], str)
        assert response.body["message"]
