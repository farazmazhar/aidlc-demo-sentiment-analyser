"""The sentiment-engine interface.

Single responsibility: define what a sentiment engine is, so that everything
above it (service, routes, page) can depend on one small abstraction instead of
a concrete implementation. Two implementations exist — `DummySentimentClient`
(offline default) and `OpenRouterJevSentimentClient` (opt-in live) — and nothing
outside this module needs to know which one is active. (FR2.1, FR2.3, FR2.4, NFR5)

The typed result is the whole contract: chosen label, one probability per label,
and a confidence. There is no free-text field to parse and no score question —
a result that cannot be read this way is a failure, never a guess (BR2.2, BR2.3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

#: The closed set of labels the app produces and stores (FR2.4, BR2.3).
LABELS: tuple[str, ...] = ("positive", "negative", "neutral")


@dataclass(frozen=True)
class SentimentResult:
    """A typed sentiment decision.

    `label` is one of `LABELS`, `probabilities` is keyed by label with every
    label present, `confidence` is the engine's confidence in the chosen label,
    and `model`/`provider` name the engine that produced it (FR2.3, FR2.4, FR3.5).
    """

    label: str
    probabilities: dict[str, float]
    confidence: float
    model: str
    provider: str


class SentimentEngineError(RuntimeError):
    """Raised when an engine cannot produce a typed decision.

    Covers a network failure, a non-2xx response, and a response that carries no
    usable typed Choice result (FR2.3). Nothing is persisted when this is raised,
    so the app never stores a fabricated label.
    """


class SentimentAuthError(SentimentEngineError):
    """Raised when OpenRouter rejects the credential (HTTP 401/403).

    Kept distinct from a plain engine failure so the session credential can be
    dropped on this signal alone: after that the app falls back to the offline
    dummy engine and the page shows the connection as red again (BR6.2).
    Nothing is persisted when this is raised.
    """


def validate_result(result: SentimentResult) -> None:
    """Reject an incomplete typed decision before anything is stored (BR2.3).

    A result is valid only when its label is one of the three allowed values and
    it carries a probability for every one of them. Anything else is an engine
    failure — the app refuses the attempt rather than inventing the missing value
    (BR2.2).
    """
    if result.label not in LABELS:
        raise SentimentEngineError(
            f"The sentiment engine chose an unsupported label {result.label!r}."
        )

    missing = [label for label in LABELS if label not in result.probabilities]
    if missing:
        raise SentimentEngineError(
            f"The sentiment engine's answer omitted probabilities for {', '.join(missing)}."
        )


@runtime_checkable
class SentimentClient(Protocol):
    """The one interface every sentiment engine implements (FR2.1)."""

    def analyze(self, text: str) -> SentimentResult:
        """Return the sentiment decision for `text`."""
        ...
