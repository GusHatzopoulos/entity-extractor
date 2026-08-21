from typing import NotRequired, TypedDict


class EntityRecord(TypedDict):
    entity: str
    type: str
    source: str
    occurrences: int

    confidence: NotRequired[str]
    keep: NotRequired[bool]
    contexts: NotRequired[list[str]]