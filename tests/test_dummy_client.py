"""Business logic: the offline dummy sentiment engine.

Every assertion is about a value the engine produced from input text; the
network guard armed in `conftest.py` is what makes the offline claim real rather
than assumed. (FR2.1-FR2.4, FR3.5, BR7.2, NFR1)
"""

from __future__ import annotations

import socket

import pytest

from app.dummy_client import LABEL_PROBABILITIES, MODEL, PROVIDER, DummySentimentClient
from app.sentiment import LABELS, SentimentClient

text_with_positive_keyword = "The sunset was wonderful"
text_with_negative_keyword = "The soup was terrible"
text_with_no_keywords = "The parcel arrived on Tuesday"


def test_dummy_labels_positive_keyword():
    """A positive keyword wins when no negative keyword is present (FR2.2)."""
    assert DummySentimentClient().analyze(text_with_positive_keyword).label == "positive"


def test_dummy_labels_negative_keyword():
    """A negative keyword wins when no positive keyword is present (FR2.2)."""
    assert DummySentimentClient().analyze(text_with_negative_keyword).label == "negative"


def test_dummy_labels_neutral_otherwise():
    """Text with no keywords — and a tie — is neutral (FR2.2)."""
    client = DummySentimentClient()

    assert client.analyze(text_with_no_keywords).label == "neutral"
    assert client.analyze("wonderful but terrible").label == "neutral"


def test_dummy_fixed_probabilities_per_label():
    """Each label always yields its own fixed, label-keyed triple summing to 1."""
    client = DummySentimentClient()

    for text in (
        text_with_positive_keyword,
        text_with_negative_keyword,
        text_with_no_keywords,
    ):
        result = client.analyze(text)
        assert result.probabilities == LABEL_PROBABILITIES[result.label]
        assert sorted(result.probabilities) == sorted(LABELS)
        assert sum(result.probabilities.values()) == pytest.approx(1.0)
        assert result.confidence == result.probabilities[result.label]

    # Determinism: the same input twice gives the same triple.
    assert (
        client.analyze(text_with_positive_keyword).probabilities
        == client.analyze(text_with_positive_keyword).probabilities
    )


def test_dummy_result_names_the_offline_engine():
    """The result carries the provenance a stored row records (FR3.5, BR3.2)."""
    result = DummySentimentClient().analyze(text_with_positive_keyword)

    assert result.model == MODEL
    assert result.provider == PROVIDER == "offline"


def test_dummy_makes_no_network_call():
    """Analysing text offline needs no key and never opens a connection (NFR1)."""
    # Prove the session guard is armed: a connection attempt inside a test is
    # turned into a failure rather than silently reaching the network.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe, pytest.raises(AssertionError):
        probe.connect(("127.0.0.1", 9))

    # No credentials are needed to construct or use the engine...
    client = DummySentimentClient()
    assert isinstance(client, SentimentClient)
    assert not hasattr(client, "api_key")

    # ...and an analysis completes while the guard is armed, which is only
    # possible because no network access is attempted.
    assert client.analyze(text_with_positive_keyword).label == "positive"
