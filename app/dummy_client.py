"""The offline, keyword-based sentiment client.

Single responsibility: produce a deterministic sentiment decision with no
network access, no credentials and no external state, so that development and
the whole test suite run offline by default. (FR2.1, FR2.2, FR2.3, NFR1)
"""

from __future__ import annotations

from app.sentiment import SentimentResult
from app.terms import tokenize

#: Held to a few obvious words on purpose: the dummy engine exists to be
#: predictable, not accurate (FR2.2).
POSITIVE_WORDS = frozenset(
    {
        "amazing",
        "awesome",
        "brilliant",
        "delightful",
        "excellent",
        "fantastic",
        "glad",
        "good",
        "great",
        "happy",
        "love",
        "lovely",
        "perfect",
        "pleased",
        "wonderful",
    }
)

NEGATIVE_WORDS = frozenset(
    {
        "angry",
        "awful",
        "bad",
        "broken",
        "disappointing",
        "hate",
        "horrible",
        "miserable",
        "poor",
        "sad",
        "terrible",
        "unhappy",
        "useless",
        "worst",
    }
)

#: Fixed per-label probability triples (FR2.2).
LABEL_PROBABILITIES: dict[str, dict[str, float]] = {
    "positive": {"positive": 0.85, "negative": 0.05, "neutral": 0.10},
    "negative": {"positive": 0.05, "negative": 0.85, "neutral": 0.10},
    "neutral": {"positive": 0.15, "negative": 0.15, "neutral": 0.70},
}

MODEL = "dummy-keyword-v1"

#: Recorded on every offline result so a stored row says which engine produced
#: it (FR3.5, BR3.2). The retired intensity values are gone with the field itself.
PROVIDER = "offline"


class DummySentimentClient:
    """Classify by counting positive and negative keyword occurrences (FR2.2)."""

    model = MODEL
    provider = PROVIDER

    def analyze(self, text: str) -> SentimentResult:
        """Return the fixed-shape decision for `text`.

        More positive than negative keywords gives `positive`, the reverse
        gives `negative`, and anything else — including a tie — is `neutral`.

        Tokenising is delegated to the one public tokeniser, `app.terms.tokenize`,
        and this engine consumes **only** that operation: it never applies the
        term-length or stopword filters, so its scoring is byte-for-byte what it
        was before the pattern was promoted out of this module (FR4.2, A4).
        """
        words = tokenize(text)
        positive_hits = sum(1 for word in words if word in POSITIVE_WORDS)
        negative_hits = sum(1 for word in words if word in NEGATIVE_WORDS)

        if positive_hits > negative_hits:
            label = "positive"
        elif negative_hits > positive_hits:
            label = "negative"
        else:
            label = "neutral"

        probabilities = dict(LABEL_PROBABILITIES[label])
        return SentimentResult(
            label=label,
            probabilities=probabilities,
            confidence=probabilities[label],
            model=self.model,
            provider=self.provider,
        )
