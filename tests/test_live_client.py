"""Business logic: the live Jev client, exercised through an injected transport.

The transport is injected, so both the request this client builds and the answer
it reads are asserted with no network call at all (BR7.2, AC9.1.1). The outbound
timeout is the one named constant that transport carries (D4, NFR-P2).
"""

from __future__ import annotations

import json
import urllib.error
from dataclasses import fields

import pytest

from app.dummy_client import DummySentimentClient
from app.openrouter_client import (
    AUTH_REJECTED_STATUSES,
    CHOICE_QUESTION_KEY,
    ENDPOINT,
    LIVE_TIMEOUT_SECONDS,
    PROVIDER,
    OpenRouterJevSentimentClient,
)
from app.sentiment import LABELS, SentimentAuthError, SentimentClient, SentimentEngineError

KEY = "sk-or-v1-live-key"

ANSWER = {
    "answers": {
        CHOICE_QUESTION_KEY: {
            "type": "choice",
            "choice": "negative",
            "probabilities": {"positive": 0.1, "negative": 0.75, "neutral": 0.15},
            "confidence": 0.75,
        }
    }
}


class StubTransport:
    """Records the request it was handed and replays one recorded answer."""

    def __init__(self, status: int = 200, body: bytes = b"", error: Exception | None = None):
        self.status = status
        self.body = body
        self.error = error
        self.calls: list[tuple[str, bytes, dict[str, str], float]] = []

    def __call__(
        self, url: str, payload: bytes, headers: dict[str, str], timeout: float
    ) -> tuple[int, bytes]:
        self.calls.append((url, payload, headers, timeout))
        if self.error is not None:
            raise self.error
        return self.status, self.body


def _bytes(payload: object) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _client(transport: StubTransport, **kwargs: object) -> OpenRouterJevSentimentClient:
    return OpenRouterJevSentimentClient(api_key=KEY, transport=transport, **kwargs)


def test_request_asks_one_choice_question_with_exactly_the_three_labels():
    """BR2.1, AC3.1.1: the question carries exactly the three allowed options."""
    transport = StubTransport(body=_bytes(ANSWER))

    result = _client(transport).analyze("something awful")

    assert result.label == "negative"
    assert result.probabilities == {"positive": 0.1, "negative": 0.75, "neutral": 0.15}
    assert result.confidence == 0.75
    assert result.provider == PROVIDER == "openrouter"

    url, payload, headers, _timeout = transport.calls[0]
    assert url == ENDPOINT
    assert headers["Authorization"] == f"Bearer {KEY}"
    assert headers["Content-Type"] == "application/json"

    request = json.loads(payload.decode("utf-8"))
    assert request["state"] == {"text": "something awful"}
    assert list(request["questions"]) == [CHOICE_QUESTION_KEY]
    question = request["questions"][CHOICE_QUESTION_KEY]
    assert question["type"] == "choice"
    assert list(question["criteria"]) == list(LABELS)


def test_the_transport_carries_the_one_named_timeout():
    """D4: the live call's timeout is one named constant, ten seconds."""
    assert LIVE_TIMEOUT_SECONDS == 10.0

    transport = StubTransport(body=_bytes(ANSWER))
    _client(transport).analyze("text")

    assert transport.calls[0][3] == LIVE_TIMEOUT_SECONDS


def test_the_timeout_is_injectable_along_with_the_transport():
    """The wait is bounded in one place, so a test can shorten it."""
    transport = StubTransport(body=_bytes(ANSWER))

    _client(transport, timeout=2.5).analyze("text")

    assert transport.calls[0][3] == 2.5


def test_confidence_falls_back_to_the_chosen_option_when_the_answer_omits_it():
    """An omitted optional confidence is read from the typed probabilities."""
    payload = json.loads(json.dumps(ANSWER))
    del payload["answers"][CHOICE_QUESTION_KEY]["confidence"]
    transport = StubTransport(body=_bytes(payload))

    assert _client(transport).analyze("text").confidence == 0.75


@pytest.mark.parametrize(
    "payload",
    [
        {},  # no `answers` object at all
        {"answers": []},  # `answers` is not an object
        {"answers": {CHOICE_QUESTION_KEY: {"type": "free_text", "text": "positive"}}},
        {
            "answers": {
                CHOICE_QUESTION_KEY: {
                    "type": "choice",
                    "choice": "ecstatic",
                    "probabilities": {"positive": 0.1, "negative": 0.1, "neutral": 0.8},
                }
            }
        },
        {
            "answers": {
                CHOICE_QUESTION_KEY: {
                    "type": "choice",
                    "choice": "positive",
                    "probabilities": {"positive": 1.0},
                }
            }
        },
        {
            "answers": {
                CHOICE_QUESTION_KEY: {
                    "type": "choice",
                    "choice": "positive",
                    "probabilities": ["positive"],
                }
            }
        },
    ],
)
def test_an_unreadable_answer_fails_rather_than_guessing(payload):
    """BR2.2, BR2.3, AC3.1.2: no label is ever inferred from prose or a fragment."""
    transport = StubTransport(body=_bytes(payload))

    with pytest.raises(SentimentEngineError):
        _client(transport).analyze("text")


@pytest.mark.parametrize("status", sorted(AUTH_REJECTED_STATUSES))
def test_a_provider_rejected_credential_raises_the_auth_signal(status):
    """BR6.2: 401/403 is the signal that drops the session credential."""
    transport = StubTransport(status=status)

    with pytest.raises(SentimentAuthError):
        _client(transport).analyze("text")


def test_transport_and_response_failures_are_engine_errors():
    """A non-2xx status, an unreachable provider and a non-JSON body all fail."""
    server_error = StubTransport(status=500, body=b"boom")
    with pytest.raises(SentimentEngineError) as excinfo:
        _client(server_error).analyze("text")
    assert not isinstance(excinfo.value, SentimentAuthError)
    assert "500" in str(excinfo.value)

    unreachable = StubTransport(error=urllib.error.URLError("no route to host"))
    with pytest.raises(SentimentEngineError):
        _client(unreachable).analyze("text")

    not_json = StubTransport(status=200, body=b"<html>not json</html>")
    with pytest.raises(SentimentEngineError):
        _client(not_json).analyze("text")

    not_an_object = StubTransport(status=200, body=b"[1, 2, 3]")
    with pytest.raises(SentimentEngineError):
        _client(not_an_object).analyze("text")


def test_a_key_is_required_and_never_rendered():
    """BR5.1: an empty key cannot build the client, and a real one never prints."""
    with pytest.raises(SentimentEngineError):
        OpenRouterJevSentimentClient(api_key="")

    client = _client(StubTransport(body=_bytes(ANSWER)))

    assert KEY not in f"{client!r} {client!s}"
    assert "<redacted>" in repr(client)


def test_both_implementations_share_the_interface_and_the_result_shape():
    """AC3.1.3: one interface, two implementations, one typed result shape."""
    offline = DummySentimentClient()
    live = _client(StubTransport(body=_bytes(ANSWER)))

    assert isinstance(offline, SentimentClient)
    assert isinstance(live, SentimentClient)

    offline_result = offline.analyze("wonderful")
    live_result = live.analyze("awful")
    assert type(offline_result) is type(live_result)
    assert {field.name for field in fields(offline_result)} == {
        "label",
        "probabilities",
        "confidence",
        "model",
        "provider",
    }
