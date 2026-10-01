"""Business logic: the in-app OpenRouter connection, held for the session only.

Every test replaces the code exchange with a double, so no test reaches
OpenRouter and none needs an API key. Nothing here touches a file: the
credential lives in the store's memory and nowhere else, which is what makes a
restart start disconnected. (BR6.1, BR6.2, BR5.1, NFR2)
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from app.session_auth import (
    AUTHORIZE_ENDPOINT,
    NOT_CONNECTED,
    PKCE_METHOD,
    AuthExchangeError,
    SessionAuth,
    code_challenge_for,
    create_code_verifier,
)

CALLBACK = "http://127.0.0.1:8000/auth/callback"
KEY = "sk-or-v1-session-key"


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


def test_code_challenge_is_the_base64url_sha256_of_the_verifier():
    """S256 is exactly base64url(sha256(verifier)), unpadded."""
    assert code_challenge_for("abc123") == "bKE9UspwyIPg8LsQHkJaiehiTeUdstI5JZOvaoQRgJA"


def test_verifiers_are_unique_and_url_safe():
    """A verifier is a fresh, high-entropy token every time."""
    first, second = create_code_verifier(), create_code_verifier()

    assert first != second
    assert len(first) >= 43
    assert all(character.isalnum() or character in "-_" for character in first)


def test_start_returns_the_authorize_url_with_the_s256_challenge():
    """Step 1 of the flow: a well-formed authorization URL, nothing more."""
    auth = SessionAuth(exchanger=FakeExchanger())

    parsed = urlparse(auth.start(CALLBACK))

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == AUTHORIZE_ENDPOINT
    query = parse_qs(parsed.query)
    assert query["callback_url"] == [CALLBACK]
    assert query["code_challenge_method"] == [PKCE_METHOD]
    assert len(query["code_challenge"][0]) >= 43
    assert query["key_label"][0] != ""
    # Starting a flow does not connect anything on its own.
    assert auth.credential() is None
    assert auth.reason() == NOT_CONNECTED


def test_complete_exchanges_the_code_with_the_verifier_it_announced():
    """Step 2: the code is traded with the verifier whose challenge was sent."""
    exchanger = FakeExchanger()
    auth = SessionAuth(exchanger=exchanger)
    challenge = parse_qs(urlparse(auth.start(CALLBACK)).query)["code_challenge"][0]

    credential = auth.complete("the-code")

    assert credential.api_key == KEY
    assert credential.obtained_at.tzinfo is not None
    assert [call[0] for call in exchanger.calls] == ["the-code"]
    assert [call[2] for call in exchanger.calls] == [PKCE_METHOD]
    assert code_challenge_for(exchanger.calls[0][1]) == challenge
    assert auth.credential() is credential
    assert auth.reason() == NOT_CONNECTED


def test_complete_without_a_pending_flow_fails_and_stays_disconnected():
    """A stray callback cannot conjure a credential."""
    auth = SessionAuth(exchanger=FakeExchanger())

    with pytest.raises(AuthExchangeError):
        auth.complete("the-code")

    assert auth.credential() is None
    assert "No OpenRouter authorization is in progress" in auth.reason()


def test_complete_rejects_a_blank_code():
    auth = SessionAuth(exchanger=FakeExchanger())
    auth.start(CALLBACK)

    with pytest.raises(AuthExchangeError):
        auth.complete("   ")

    assert auth.credential() is None


def test_a_code_from_an_earlier_tab_still_completes():
    """OpenRouter's redirect carries no state, so pending verifiers are tried too."""
    seen: list[str] = []

    def exchanger(code: str, verifier: str, method: str) -> str:
        seen.append(verifier)
        if len(seen) == 1:
            # The newest verifier does not own this code.
            raise AuthExchangeError("OpenRouter refused the authorization code (HTTP 403).")
        return KEY

    auth = SessionAuth(exchanger=exchanger)
    auth.start(CALLBACK)  # tab 1
    auth.start(CALLBACK)  # tab 2

    credential = auth.complete("code-from-tab-1")

    assert credential.api_key == KEY
    assert len(seen) == 2  # newest first, then the earlier tab
    assert seen[0] != seen[1]


def test_a_refused_code_records_the_reason_and_keeps_the_app_offline():
    exchanger = FakeExchanger(
        error=AuthExchangeError("OpenRouter refused the authorization code (HTTP 403).")
    )
    auth = SessionAuth(exchanger=exchanger)
    auth.start(CALLBACK)

    with pytest.raises(AuthExchangeError) as excinfo:
        auth.complete("the-code")

    assert "403" in str(excinfo.value)
    assert auth.credential() is None
    assert "403" in auth.reason()


def test_expire_drops_the_credential_and_records_why():
    """This is the signal that turns the page's indicator red again."""
    auth = SessionAuth(exchanger=FakeExchanger())
    auth.start(CALLBACK)
    auth.complete("the-code")
    assert auth.credential() is not None

    auth.expire("OpenRouter rejected the API key (HTTP 401).")

    assert auth.credential() is None
    assert "401" in auth.reason()


def test_disconnect_drops_the_credential_and_the_pending_flow():
    auth = SessionAuth(exchanger=FakeExchanger())
    auth.start(CALLBACK)
    auth.complete("the-code")

    auth.disconnect()

    assert auth.credential() is None
    assert auth.reason() == "Disconnected."
    with pytest.raises(AuthExchangeError):
        auth.complete("the-code")


def test_the_credential_never_renders_its_key():
    """The key is used, never printed (FR1.5, NFR2)."""
    auth = SessionAuth(exchanger=FakeExchanger())
    auth.start(CALLBACK)

    credential = auth.complete("the-code")

    assert KEY not in f"{credential!r} {credential!s}"
    assert "<redacted>" in repr(credential)


def test_pending_verifiers_are_dropped_when_the_code_window_closes():
    """Authorization codes last 10 minutes; so do the pending verifiers."""
    now = [0.0]
    auth = SessionAuth(exchanger=FakeExchanger(), clock=lambda: now[0])
    auth.start(CALLBACK)

    now[0] += 601.0

    with pytest.raises(AuthExchangeError):
        auth.complete("the-code")
