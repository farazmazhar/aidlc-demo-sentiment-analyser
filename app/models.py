"""Request/response schemas and the persisted record shape.

Single responsibility: define the wire and storage shape of one analysis in a
single place, so the API contract and the stored row contract (FR3.2, FR3.6)
cannot drift apart.

Only stdlib types are used here: FastAPI accepts a plain dataclass as a request
body, and the response shape is `AnalysisRecord.to_dict()`. That keeps the
codebase free of a direct dependency on the validation library that FastAPI
happens to use internally (NFR3).

The retired `intensity` attribute is absent from this shape on purpose: the v1
contract no longer produces it, so new rows leave it unset and a pre-v1 row is
read without it being invented (BR3.4, AC7.1.3).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

#: The exact field set of a returned/stored record (BR3.2, AC2.1.2; FR3.2).
RECORD_FIELDS = (
    "id",
    "text",
    "label",
    "probabilities",
    "confidence",
    "model",
    "provider",
    "created_at",
    "import_id",
)

#: The recorded wire value for a row migrated from a store that predates the
#: `provider` column. No engine can be named for such a row, so the contract
#: carries the explicit sentinel `unknown` rather than JSON null (which the
#: contract's `provider: type: string` does not admit) or a fabricated engine
#: name (AC7.1.2). `contract-summary.md` and `entities.md` record it.
UNKNOWN_PROVIDER = "unknown"


@dataclass
class AnalyzeRequest:
    """Body of `POST /v1/analyze`: the text to analyse (FR4.1).

    Only presence and type are enforced at the HTTP boundary. Emptiness —
    including whitespace-only text — is a domain rule enforced by the service,
    so every rejection of the text travels through one code path and one error
    envelope (BR4.1, BR4.3).
    """

    text: str


#: The body fields `POST /v1/analyze` declares, derived from the dataclass so the
#: declared set cannot drift from the shape. The contract sets
#: `additionalProperties: false`, so a field outside this set is refused rather
#: than silently dropped (BR4.3).
ANALYZE_FIELDS = tuple(field.name for field in fields(AnalyzeRequest))


def undeclared_body_fields(body: object) -> list[str]:
    """Return the keys `body` carries that the contract does not declare (BR4.3).

    Only a JSON object can carry an undeclared field; any other shape is left to
    the request-body validator, which already refuses it.
    """
    if not isinstance(body, Mapping):
        return []
    return [str(key) for key in body if key not in ANALYZE_FIELDS]


@dataclass(frozen=True)
class AnalysisRecord:
    """One stored analysis, with the encodings pinned by the row contract.

    `probabilities` is a JSON object keyed by label (never an array) and
    `created_at` is an ISO 8601 UTC string ending in `Z` (FR3.2, BR3.2).

    `provider` names the engine that produced the row. A row migrated from a
    store that predates the column carries `UNKNOWN_PROVIDER` (`"unknown"`) —
    an explicit sentinel the contract records, never a fabricated engine name and
    never the literal string `"None"` (BR3.4, AC7.1.2).

    `import_id` groups the rows persisted by one bulk-import request; it is
    `None` for a row produced by single analysis (FR3.1, FR3.2). It is additive,
    so an existing client tolerates the extra nullable field (A6).
    """

    id: int
    text: str
    label: str
    probabilities: dict[str, float]
    confidence: float
    model: str
    provider: str
    created_at: str
    import_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the record as JSON-ready primitives, in the pinned field order."""
        return {
            "id": self.id,
            "text": self.text,
            "label": self.label,
            "probabilities": dict(self.probabilities),
            "confidence": self.confidence,
            "model": self.model,
            "provider": self.provider,
            "created_at": self.created_at,
            "import_id": self.import_id,
        }

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> AnalysisRecord:
        """Build a record from a database row, decoding the stored encodings.

        A pre-v1 row may still carry the retired `intensity` column. It is
        deliberately not read: the value stays in the file untouched rather than
        being surfaced or back-filled (BR3.4). A missing `provider` — the column
        the in-place migration adds to a store that predates it — becomes the
        recorded `UNKNOWN_PROVIDER` sentinel rather than the string `"None"`.
        A row written by single analysis carries `import_id = NULL`, read back as
        `None` (FR3.1).
        """
        provider = row["provider"]
        import_id = row["import_id"]
        return cls(
            id=int(row["id"]),
            text=str(row["text"]),
            label=str(row["label"]),
            probabilities={
                str(label): float(value)
                for label, value in json.loads(row["probabilities"]).items()
            },
            confidence=float(row["confidence"]),
            model=str(row["model"]),
            provider=UNKNOWN_PROVIDER if provider is None else str(provider),
            created_at=str(row["created_at"]),
            import_id=None if import_id is None else str(import_id),
        )
