from typing import NotRequired, TypedDict


class EntitySpan(TypedDict):
    """
    Exact position of one entity occurrence
    inside the normalized source text.

    start:
        Inclusive character offset.

    end:
        Exclusive character offset.
    """

    start: int
    end: int


class EntityRecord(TypedDict):
    entity: str
    type: str
    source: str
    occurrences: int

    original_type: NotRequired[str]
    confidence: NotRequired[str]
    keep: NotRequired[bool]
    contexts: NotRequired[list[str]]

    person_score: NotRequired[int]
    location_score: NotRequired[int]

    classification_reason: NotRequired[str]

    # Exact text positions for detected occurrences.
    spans: NotRequired[list[EntitySpan]]