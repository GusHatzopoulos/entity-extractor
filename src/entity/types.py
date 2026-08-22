from typing import NotRequired, TypedDict


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