"""Term tokenisation and significance filtering.

Single responsibility: turn text into word tokens, and say which of those tokens
carry meaning. Nothing here counts, ranks, weights or scores anything — counting
and ranking belong to `app.analytics`, and scoring belongs to the engines — so
this module stays a leaf that imports nothing from `app` (ADR-002).

The two operations are deliberately separate. :func:`tokenize` is the one
tokeniser in the repository and the offline engine consumes it alone, so its
output is frozen: it applies **no** length filter and **no** stopword filter, and
the engine's scoring is byte-for-byte unchanged by the promotion of the pattern
that used to be private to `app.dummy_client` (`FR4.5`, A4, AC4.2.2, AC4.2.3).
:func:`significant_terms` filters an already-tokenised sequence and never
tokenises again, so a caller cannot accidentally apply the filters twice (A5).
(`FR4.2`-`FR4.6`)
"""

from __future__ import annotations

import re
from collections.abc import Sequence

#: A token is a maximal run of ASCII lowercase letters and apostrophes. Runs
#: containing digits, whitespace or any non-ASCII character are token boundaries,
#: which is also why a term written entirely in a non-Latin script contributes
#: nothing — a recorded, accepted limitation (`FR4.6`).
TOKEN_PATTERN = r"[a-z']+"  # noqa: S105 - a word pattern, not a credential

_TOKEN = re.compile(TOKEN_PATTERN)

#: Terms shorter than this are not terms; the filter is applied after tokenising
#: and never inside it (`FR4.4`).
MIN_TERM_LENGTH = 3

#: One versioned English stopword constant for the whole repository, matched
#: case-insensitively against lowercased tokens. It is a fixed list of function
#: words: it deliberately contains no sentiment word, so `great`, `bad` and
#: `terrible` survive it and remain terms (`FR4.4`).
STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "about",
        "above",
        "after",
        "again",
        "against",
        "all",
        "am",
        "an",
        "and",
        "any",
        "are",
        "aren",
        "as",
        "at",
        "be",
        "because",
        "been",
        "before",
        "being",
        "below",
        "between",
        "both",
        "but",
        "by",
        "can",
        "cannot",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "don",
        "down",
        "during",
        "each",
        "few",
        "for",
        "from",
        "further",
        "had",
        "has",
        "have",
        "having",
        "he",
        "her",
        "here",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "itself",
        "just",
        "let",
        "ll",
        "me",
        "more",
        "most",
        "mustn",
        "my",
        "myself",
        "no",
        "nor",
        "not",
        "now",
        "of",
        "off",
        "on",
        "once",
        "only",
        "or",
        "other",
        "ought",
        "our",
        "ours",
        "ourselves",
        "out",
        "over",
        "own",
        "same",
        "shan",
        "she",
        "should",
        "so",
        "some",
        "such",
        "than",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "themselves",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "through",
        "to",
        "too",
        "under",
        "until",
        "up",
        "very",
        "was",
        "we",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "whom",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
    }
)


def tokenize(text: str) -> list[str]:
    """Return `text`'s lowercased word tokens, in order.

    No length filter and no stopword filter is applied here: the offline engine
    consumes this operation alone and must keep scoring exactly as it did before
    the pattern was promoted here (`FR4.2`, A4).
    """
    return _TOKEN.findall(text.lower())


def significant_terms(tokens: Sequence[str]) -> list[str]:
    """Return the tokens that are terms, in the order they arrived.

    A token is a term when it is at least `MIN_TERM_LENGTH` characters long and
    absent from `STOPWORDS`. This operation never tokenises: a caller that already
    has tokens passes them straight through, so the filters cannot be applied
    twice (`FR4.4`).
    """
    return [
        token
        for token in tokens
        if len(token) >= MIN_TERM_LENGTH and token.lower() not in STOPWORDS
    ]
