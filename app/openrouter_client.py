"""The live Jev client, through the OpenRouter Decisions API.

Single responsibility: turn one piece of text into a typed `SentimentResult` by
asking the Jev model a Choice question (positive / negative / neutral) and
reading the answer's typed fields. It never parses free text from the model, and
it raises `SentimentEngineError` rather than guessing when the typed result is
unavailable. (FR2.1, FR2.2, FR2.3, FR2.4, FR3.5, NFR3)

Two seams make this testable without a network:

* the transport is injected — the one outbound call is a plain callable, so a
  test hands it a recorded answer and asserts the request it was given (BR7.2);
* the timeout is one named constant carried by that transport, so the wait is
  bounded in exactly one place (D4).

HTTP is done with the standard library, so no HTTP-client dependency is added.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Protocol

from app.sentiment import (
    LABELS,
    SentimentAuthError,
    SentimentEngineError,
    SentimentResult,
)

#: The Decisions endpoint and the model id fixed by the requirements (FR2.2, FR1.4).
ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"

#: The outbound call's one timeout, in seconds (D4, NFR-P2).
LIVE_TIMEOUT_SECONDS = 10.0

#: Statuses that mean "this credential is no longer accepted", as opposed to a
#: transient engine failure. They drop the session credential so the app falls
#: back to the offline engine instead of retrying a dead key forever (BR6.2).
AUTH_REJECTED_STATUSES = frozenset({401, 403})

#: Recorded on every live result (FR3.5, BR3.2).
PROVIDER = "openrouter"

#: The question key, echoed back as the key of the response's `answers` object,
#: and the one instructions line sent with it.
CHOICE_QUESTION_KEY = "sentiment"
CHOICE_INSTRUCTIONS = "Which single sentiment label best describes the text?"

#: One `choice` question whose options are exactly the app's labels (BR2.1).
CHOICE_CRITERIA: dict[str, str] = {
    "positive": (
        "The text expresses a positive feeling: praise, satisfaction, affection, "
        "approval, gratitude or happiness."
    ),
    "negative": (
        "The text expresses a negative feeling: criticism, dissatisfaction, "
        "dislike, disapproval, anger or unhappiness."
    ),
    "neutral": (
        "The text expresses no clear positive or negative feeling: factual, mixed, or indifferent."
    ),
}


class HttpTransport(Protocol):
    """One HTTP POST, injected so the live path is testable with no network."""

    def __call__(
        self, url: str, payload: bytes, headers: dict[str, str], timeout: float
    ) -> tuple[int, bytes]:
        """Return `(status, body)`; raise `OSError` when the call cannot be made."""
        ...


def urllib_transport(
    url: str, payload: bytes, headers: dict[str, str], timeout: float
) -> tuple[int, bytes]:
    """The production transport: one POST with the standard library.

    An HTTP error status is returned as `(status, body)` rather than raised, so
    the client decides what each status means; a connection failure surfaces as
    the `OSError` the standard library raises, which the client maps as well.
    """
    # The endpoint is a hardcoded https constant, never caller-supplied.
    request = urllib.request.Request(  # noqa: S310
        url, data=payload, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return int(response.status), response.read()
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read()


class OpenRouterJevSentimentClient:
    """The live sentiment engine (FR2.2)."""

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        transport: HttpTransport = urllib_transport,
        timeout: float = LIVE_TIMEOUT_SECONDS,
    ) -> None:
        if not api_key:
            raise SentimentEngineError(
                "OpenRouterJevSentimentClient requires an API key; none was supplied."
            )
        self._api_key = api_key
        self._model = model or DEFAULT_MODEL
        self._transport = transport
        self._timeout = timeout

    def __repr__(self) -> str:
        """Render the client with the key redacted (BR5.1, NFR2)."""
        return f"OpenRouterJevSentimentClient(model={self._model!r}, api_key=<redacted>)"

    __str__ = __repr__

    def analyze(self, text: str) -> SentimentResult:
        """Return the typed Jev decision for `text` (FR2.3, FR2.4)."""
        payload = self._post_decisions(text)
        answers = payload.get("answers")
        if not isinstance(answers, dict):
            raise SentimentEngineError(
                "The sentiment engine response carried no typed 'answers' object."
            )

        label, probabilities, confidence = self._read_choice(answers)
        return SentimentResult(
            label=label,
            probabilities=probabilities,
            confidence=confidence,
            model=self._model,
            provider=PROVIDER,
        )

    # -- transport ---------------------------------------------------------

    def _request_body(self, text: str) -> bytes:
        """Build the one Choice question this client asks (BR2.1)."""
        return json.dumps(
            {
                "model": self._model,
                "state": {"text": text},
                "questions": {
                    CHOICE_QUESTION_KEY: {
                        "type": "choice",
                        "instructions": CHOICE_INSTRUCTIONS,
                        "criteria": CHOICE_CRITERIA,
                    },
                },
            }
        ).encode("utf-8")

    def _post_decisions(self, text: str) -> dict[str, Any]:
        """POST the question set and return the decoded response body."""
        body = self._request_body(text)
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            status, raw = self._transport(ENDPOINT, body, headers, self._timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise SentimentEngineError(
                f"The sentiment engine could not be reached: {exc}."
            ) from exc

        if status in AUTH_REJECTED_STATUSES:
            raise SentimentAuthError(f"OpenRouter rejected the API key (HTTP {status}).")
        if not 200 <= status < 300:
            raise SentimentEngineError(f"The sentiment engine answered HTTP {status}.")

        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise SentimentEngineError(
                "The sentiment engine returned a body that is not JSON."
            ) from exc
        if not isinstance(decoded, dict):
            raise SentimentEngineError(
                "The sentiment engine returned a JSON value that is not an object."
            )
        return decoded

    # -- typed answer reading ---------------------------------------------

    @staticmethod
    def _read_choice(
        answers: dict[str, Any],
    ) -> tuple[str, dict[str, float], float]:
        """Read the Choice answer's label, per-option probabilities, confidence.

        Every rule that makes an unreadable or incomplete answer a failure lives
        here rather than in a guess (BR2.2, BR2.3).
        """
        answer = answers.get(CHOICE_QUESTION_KEY)
        if not isinstance(answer, dict) or answer.get("type") != "choice":
            raise SentimentEngineError("The sentiment engine returned no typed choice answer.")

        label = answer.get("choice")
        if label not in LABELS:
            raise SentimentEngineError(
                f"The sentiment engine chose an unsupported label {label!r}."
            )

        raw_probabilities = answer.get("probabilities")
        if not isinstance(raw_probabilities, dict):
            raise SentimentEngineError(
                "The sentiment engine's choice answer carried no per-option probabilities."
            )
        missing = [name for name in LABELS if name not in raw_probabilities]
        if missing:
            raise SentimentEngineError(
                "The sentiment engine's choice answer omitted probabilities for "
                f"{', '.join(missing)}."
            )
        probabilities = {name: float(raw_probabilities[name]) for name in LABELS}

        confidence = answer.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            # The API marks `confidence` optional; the chosen option's own
            # probability is the typed equivalent, and it is never invented.
            confidence = probabilities[label]

        return label, probabilities, float(confidence)
