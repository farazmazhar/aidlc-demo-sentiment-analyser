"""API / endpoint: the in-app OpenRouter connection over the real application.

The code exchange is injected as a double, so no test in this file reaches
OpenRouter and none needs a key. The connected state is observed through
`/auth/status` and `/v1/health`, and the rejected-credential path is driven by a
stub engine rather than a real call. (FR5.1-FR5.4, BR6.1, BR6.2, AC6.1.1-AC6.1.5)
"""

from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

from app.config import Settings
from app.main import create_app
from app.sentiment import SentimentAuthError
from app.session_auth import (
    AUTHORIZE_ENDPOINT,
    NOT_CONNECTED,
    AuthExchangeError,
    SessionAuth,
)
from tests.conftest import asgi_request

KEY = "sk-or-v1-session-key"
CONFIG_KEY = "sk-or-v1-from-config"


class FakeExchanger:
    """Stands in for the HTTPS exchange and records what it was asked to trade."""

    def __init__(self, key: str = KEY, error: Exception | None = None) -> None:
        self.key = key
        self.error = error
        self.calls: list[tuple[str, str, str]] = []

    def __call__(self, code: str, code_verifier: str, method: str) -> str:
        self.calls.append((code, code_verifier, method))
        if self.error is not None:
            raise self.error
        return self.key


def _app(tmp_path, exchanger, mode: str = "offline", api_key: str | None = None):
    settings = Settings(
        mode=mode,
        api_key=api_key,
        db_path=tmp_path / "sentiment.db",
        config_path=tmp_path / "config.local.toml",
    )
    return create_app(settings, session_auth=SessionAuth(exchanger=exchanger))


def _connect(app):
    """Run the two browser steps (start, then callback) with the double in place."""
    return (
        asgi_request(app, "GET", "/auth/openrouter/start"),
        asgi_request(app, "GET", "/auth/callback", query="code=the-code"),
    )


def test_status_starts_offline_and_the_health_payload_agrees(tmp_path):
    """AC5.3.1: with nothing connected the app runs the offline engine, and says so."""
    app = _app(tmp_path, FakeExchanger())

    status = asgi_request(app, "GET", "/auth/status").body

    assert status["connected"] is False
    assert status["mode"] == "offline"
    assert status["source"] is None
    assert status["reason"] == NOT_CONNECTED

    health = asgi_request(app, "GET", "/v1/health").body
    assert set(health) == {"mode", "connected", "reason"}
    assert health["mode"] == "offline"
    assert health["connected"] is False


def test_start_sends_the_browser_to_openrouter_with_a_pkce_challenge(tmp_path):
    """Clicking the indicator is a redirect to OpenRouter, with S256 PKCE."""
    app = _app(tmp_path, FakeExchanger())

    response = asgi_request(app, "GET", "/auth/openrouter/start")

    assert response.status_code == 302
    parsed = urlparse(response.headers["location"])
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == AUTHORIZE_ENDPOINT
    query = parse_qs(parsed.query)
    assert query["callback_url"] == ["http://testserver/auth/callback"]
    assert query["code_challenge_method"] == ["S256"]
    assert len(query["code_challenge"][0]) >= 43
    # A redirect alone leaves the app offline.
    assert asgi_request(app, "GET", "/auth/status").body["connected"] is False


def test_callback_connects_and_the_indicator_turns_green(tmp_path):
    """AC6.1.1: the code is exchanged once, and the app switches to the live engine."""
    exchanger = FakeExchanger()
    app = _app(tmp_path, exchanger)

    _, callback = _connect(app)

    assert callback.status_code == 302
    assert callback.headers["location"] == "/?auth=connected"
    assert [call[0] for call in exchanger.calls] == ["the-code"]
    assert [call[2] for call in exchanger.calls] == ["S256"]

    status = asgi_request(app, "GET", "/auth/status").body
    assert status["connected"] is True
    assert status["source"] == "session"
    assert status["mode"] == "live"

    health = asgi_request(app, "GET", "/v1/health").body
    assert health["mode"] == "live"
    assert health["connected"] is True


def test_no_endpoint_ever_exposes_the_key(tmp_path):
    """AC6.1.3, BR5.1: the credential is used, never rendered."""
    app = _app(tmp_path, FakeExchanger())
    _connect(app)

    for path in ("/auth/status", "/v1/health", "/"):
        response = asgi_request(app, "GET", path)
        body = json.dumps(response.body) if isinstance(response.body, dict) else response.text
        assert KEY not in body


def test_callback_without_a_pending_flow_stays_offline_and_says_why(tmp_path):
    """AC6.1.5: a stray callback reports on the page and leaves the app usable."""
    app = _app(tmp_path, FakeExchanger())

    response = asgi_request(app, "GET", "/auth/callback", query="code=stray")

    assert response.status_code == 302
    assert response.headers["location"] == "/?auth=failed"

    status = asgi_request(app, "GET", "/auth/status").body
    assert status["connected"] is False
    assert "No OpenRouter authorization is in progress" in status["reason"]
    # The reason the page reports comes from the health payload it reads.
    assert (
        "No OpenRouter authorization is in progress"
        in asgi_request(app, "GET", "/v1/health").body["reason"]
    )


def test_callback_without_a_code_stays_offline(tmp_path):
    app = _app(tmp_path, FakeExchanger())

    response = asgi_request(app, "GET", "/auth/callback")

    assert response.headers["location"] == "/?auth=failed"
    status = asgi_request(app, "GET", "/auth/status").body
    assert status["connected"] is False
    assert "without an authorization code" in status["reason"]


def test_a_refused_code_keeps_the_app_offline_and_reports_the_reason(tmp_path):
    exchanger = FakeExchanger(
        error=AuthExchangeError("OpenRouter refused the authorization code (HTTP 403).")
    )
    app = _app(tmp_path, exchanger)
    asgi_request(app, "GET", "/auth/openrouter/start")

    response = asgi_request(app, "GET", "/auth/callback", query="code=the-code")

    assert response.headers["location"] == "/?auth=failed"
    status = asgi_request(app, "GET", "/auth/status").body
    assert status["connected"] is False
    assert "403" in status["reason"]


def test_disconnect_returns_the_app_to_the_offline_engine(tmp_path):
    app = _app(tmp_path, FakeExchanger())
    _connect(app)
    assert asgi_request(app, "GET", "/auth/status").body["connected"] is True

    response = asgi_request(app, "POST", "/auth/disconnect")

    assert response.status_code == 200
    assert response.body["connected"] is False
    assert response.body["mode"] == "offline"
    assert asgi_request(app, "GET", "/v1/health").body["mode"] == "offline"


def test_a_configured_key_is_the_other_way_to_be_live(tmp_path):
    """AC5.1.2: the config file still works, and the app says where the key came from."""
    app = _app(tmp_path, FakeExchanger(), mode="live", api_key=CONFIG_KEY)

    status = asgi_request(app, "GET", "/auth/status").body

    assert status["connected"] is True
    assert status["source"] == "config"
    assert status["mode"] == "live"


def test_live_mode_without_any_key_starts_offline_rather_than_failing(tmp_path):
    """AC5.2.1, AC5.2.3: live requested with no key, offline engine, red indicator."""
    app = _app(tmp_path, FakeExchanger(), mode="live", api_key=None)

    status = asgi_request(app, "GET", "/auth/status").body

    assert status["connected"] is False
    assert status["mode"] == "offline"

    health = asgi_request(app, "GET", "/v1/health").body
    assert health["connected"] is False
    assert health["mode"] == "offline"

    # An explicit submission is refused with the instruction, not answered offline.
    refused = asgi_request(app, "POST", "/v1/analyze", json_body={"text": "hello"})
    assert refused.status_code == 503
    assert refused.body["code"] == "LIVE_KEY_MISSING"


def test_a_rejected_credential_drops_the_session_and_turns_the_indicator_offline(
    tmp_path, monkeypatch
):
    """AC6.1.4: an expiry is what makes the indicator red again, so this is the key path.

    A stub engine raises the same error the live client raises on HTTP 401/403;
    the request must drop the credential, answer in the normal error envelope,
    and leave the app on the offline engine.
    """
    app = _app(tmp_path, FakeExchanger())
    _connect(app)
    assert asgi_request(app, "GET", "/auth/status").body["connected"] is True

    class RejectingClient:
        """Stands in for a live client whose credential OpenRouter has revoked."""

        def analyze(self, text: str):
            raise SentimentAuthError("OpenRouter rejected the API key (HTTP 401).")

    monkeypatch.setattr(
        "app.routes.get_client", lambda settings, credential=None: RejectingClient()
    )

    response = asgi_request(app, "POST", "/v1/analyze", json_body={"text": "hello"})

    assert response.status_code == 503
    assert response.body["code"] == "AUTH_EXPIRED"

    status = asgi_request(app, "GET", "/auth/status").body
    assert status["connected"] is False
    assert status["mode"] == "offline"
    assert "401" in status["reason"]


def test_the_page_can_always_read_the_connection_state(tmp_path):
    """The indicator's data source stays reachable whatever the connection is."""
    app = _app(tmp_path, FakeExchanger())
    _connect(app)

    response = asgi_request(app, "GET", "/auth/status")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
