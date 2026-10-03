"""Business logic: tokenisation, significance filtering and scoring parity.

These are the lower-level tests for the promoted tokeniser, written after the
behaviour exists. The parity half is the load-bearing part: the offline engine's
scoring must be byte-for-byte what it was before `_WORD` was promoted out of
`app/dummy_client`, and the engine's only claim on this module is that it still
calls the same one operation.
(`FR4.2`-`FR4.6`, `A4`, `A5`, `AC4.2.1`-`AC4.2.3`)
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

from app import dummy_client, terms
from app.dummy_client import DummySentimentClient
from app.sentiment import SentimentResult

#: The pattern the offline engine used to own privately, reproduced here so the
#: parity assertion compares the promotion against the thing it replaced rather
#: than against itself.
LEGACY_WORD = re.compile(r"[a-z']+")

#: `tokenize` on inputs whose hand-read answer is unambiguous, including every
#: boundary the pattern defines (A4, FR4.2).
TOKENIZATION_CASES = (
    ("", []),
    ("I love this", ["i", "love", "this"]),
    ("LoVe THIS", ["love", "this"]),
    ("don't", ["don't"]),
    ("it's a well-known bug!", ["it's", "a", "well", "known", "bug"]),
    ("well_known", ["well", "known"]),
    ("release2today", ["release", "today"]),
    ("  spaces   everywhere  ", ["spaces", "everywhere"]),
    ("wonderful!!! really???", ["wonderful", "really"]),
    # `ñ` is not an ASCII lowercase letter, so it is a token boundary: the accent
    # truncates the run rather than transliterating it (FR4.6, A4).
    ("café mañana", ["caf", "ma", "ana"]),
    ("a-b", ["a", "b"]),
    # Apostrophes are part of a run, so leading and trailing ones are kept.
    ("'quoted'", ["'quoted'"]),
)

#: A corpus that exercises the engine's decision surface, so parity covers more
#: than the tokeniser's own edges: ties, wins, losses and keyword repetitions.
SCORING_CORPUS = (
    "",
    "I love this",
    "this is awful",
    "good and bad",
    "great good great",
    "wonderful and dreadful",
    "LoVe THIS LoVe",
    "don't think it's bad",
    "nothing in particular",
    "amazing!!! horrible???",
    "awful awful bad terrible",
    "the product is wonderful and the support is lovely",
    "poor quality, sad outcome, useless result",
    "perfect and terrible at the same time",
    "GLoRiOuS",
    "123456 789",
    "— em dash —",
)


def _legacy_analyze(text: str) -> SentimentResult:
    """Score `text` exactly as the engine scored it before the promotion.

    This is a transcription of the engine's own scoring over the pattern it used
    to own privately; it exists so the parity assertion compares two independent
    implementations rather than one implementation with itself.
    """
    words = LEGACY_WORD.findall(text.lower())
    positive_hits = sum(1 for word in words if word in dummy_client.POSITIVE_WORDS)
    negative_hits = sum(1 for word in words if word in dummy_client.NEGATIVE_WORDS)

    if positive_hits > negative_hits:
        label = "positive"
    elif negative_hits > positive_hits:
        label = "negative"
    else:
        label = "neutral"

    probabilities = dict(dummy_client.LABEL_PROBABILITIES[label])
    return SentimentResult(
        label=label,
        probabilities=probabilities,
        confidence=probabilities[label],
        model=dummy_client.MODEL,
        provider=dummy_client.PROVIDER,
    )


def source_of(module) -> str:
    """The module's source text, read for the assertions above."""

    return Path(module.__file__).read_text(encoding="utf-8")


def test_tokenize_returns_the_hand_read_tokens_for_every_case():
    """FR4.2, A4: maximal runs of ASCII lowercase letters and apostrophes."""
    for text, expected in TOKENIZATION_CASES:
        assert terms.tokenize(text) == expected, text


def test_tokenize_applies_neither_a_length_nor_a_stopword_filter():
    """A4, AC4.2.2: filtering is `significant_terms`' job, never the tokeniser's."""
    tokens = terms.tokenize("a an the of wonderful and lovely")

    assert tokens == ["a", "an", "the", "of", "wonderful", "and", "lovely"]
    assert "a" in tokens
    assert "the" in tokens


def test_significant_terms_drops_short_tokens_and_stopwords_and_keeps_the_order():
    """FR4.4: a term is at least three characters and not a stopword."""
    tokens = ["wonderful", "a", "and", "ok", "terrible", "the", "great"]

    assert terms.significant_terms(tokens) == ["wonderful", "terrible", "great"]


def test_significant_terms_never_retokenises_and_keeps_repeats():
    """A5: the filter takes a token sequence and returns one token per kept input."""
    result = terms.significant_terms(["great", "great", "bad", "and"])

    # Repeats are kept here; counting belongs to the analytics read layer.
    assert result == ["great", "great", "bad"]


def test_significant_terms_leaves_an_all_stopword_sequence_empty():
    """FR4.4: a sequence with nothing significant is an empty list, not `None`."""
    assert terms.significant_terms(["a", "an", "and", "the", "of"]) == []


def test_the_stopword_set_contains_no_sentiment_word():
    """FR4.4: the list is function words, so `great`/`bad`/`terrible` stay terms."""
    for word in ("great", "bad", "terrible", "awful", "wonderful", "delightful"):
        assert word not in terms.STOPWORDS, word
        assert word in terms.significant_terms([word])


def test_the_private_pattern_is_gone_and_only_one_tokeniser_exists():
    """AC4.2.1: the private `_WORD` is deleted and no module duplicates the pattern."""
    assert not hasattr(dummy_client, "_WORD")
    # The engine imports the public operation, and holds no compiled pattern.
    assert dummy_client.tokenize is terms.tokenize
    assert "re.compile" not in source_of(dummy_client)
    # And the pattern is declared once, in the module that owns it.
    assert terms.TOKEN_PATTERN == r"[a-z']+"


def test_the_offline_engine_scoring_is_unchanged_by_the_promotion():
    """A4, AC4.2.3: every scoring decision is byte-for-byte what it was.

    This is the end-to-end parity instrument. It scores the same corpus twice — once
    through the real engine, which now calls the promoted `tokenize`, and once
    through the pattern it used to own privately — and compares the whole typed
    result, so a change to the label, any probability, the confidence, the model or
    the provider would show up here. The tokeniser-parity sweep below is the
    sharper half: it is sensitive to tokenisation changes that happen not to move
    any decision in this corpus.
    """
    engine = DummySentimentClient()

    for text in SCORING_CORPUS:
        assert engine.analyze(text) == _legacy_analyze(text), text


def _alphabet_sweep(max_length: int) -> list[str]:
    """Every string up to `max_length` over an alphabet of tokeniser-relevant symbols.

    The symbols are chosen so that each one decides a different part of the pattern:
    an ASCII letter, an upper-case letter that lowercasing must reach, a digit that
    must *break* a run, an apostrophe that must *continue* one, separators that must
    break a run, and a non-ASCII letter that must break one (FR4.2, FR4.6).
    """
    alphabet = ("a", "z", "A", "9", "'", "-", "_", ".", " ", "é")
    strings: list[str] = []
    for length in range(1, max_length + 1):
        strings.extend("".join(combo) for combo in itertools.product(alphabet, repeat=length))
    return strings


def test_the_promoted_tokeniser_reproduces_the_pattern_it_replaced():
    """A4, AC4.2.2: byte-for-byte parity with the private `_WORD` it replaced.

    This is the sharp parity instrument, and it is exhaustive over every string of
    one to three symbols drawn from an alphabet that exercises every boundary the
    pattern defines — lowercasing, digits breaking a run, apostrophes continuing
    one, punctuation and non-ASCII letters breaking one. Every one of those 1,110
    inputs must tokenise to exactly what the pattern used privately, so no future
    edit to the tokeniser can change what the engine sees without this failing
    first.
    """
    sweep = _alphabet_sweep(max_length=3)
    assert len(sweep) == 1110

    for text in sweep:
        assert terms.tokenize(text) == LEGACY_WORD.findall(text.lower()), repr(text)


def test_the_offline_engine_never_calls_the_significance_filter():
    """A4, AC4.2.2: the engine consumes `tokenize` alone."""
    source = source_of(dummy_client)

    assert "tokenize(" in source
    assert "significant_terms" not in source
    assert "MIN_TERM_LENGTH" not in source
    assert "STOPWORDS" not in source
