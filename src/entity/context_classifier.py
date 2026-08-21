import re

from src.entity.types import EntityRecord


PERSON_CONTEXT_PATTERNS = [
    r"\bείπε\s+(?:ο|η)\s+{name}\b",
    r"\bρώτησε\s+(?:ο|η)\s+{name}\b",
    r"\bαπάντησε\s+(?:ο|η)\s+{name}\b",
    r"\bφώναξε\s+(?:ο|η)\s+{name}\b",
    r"\bψιθύρισε\s+(?:ο|η)\s+{name}\b",
    r"\bκοίταξε\s+(?:ο|η)\s+{name}\b",
    r"\b(?:ο|η)\s+{name}\s+είπε\b",
    r"\b(?:ο|η)\s+{name}\s+ρώτησε\b",
    r"\b(?:ο|η)\s+{name}\s+απάντησε\b",
    r"\b(?:ο|η)\s+{name}\s+κοίταξε\b",
]


def looks_like_person(
    entity: EntityRecord,
) -> bool:
    """
    Check whether the stored contexts provide evidence
    that an entity is a person.
    """

    name = re.escape(entity["entity"])

    contexts = entity.get("contexts", [])

    for context in contexts:
        for pattern in PERSON_CONTEXT_PATTERNS:
            regex = pattern.format(name=name)

            if re.search(
                regex,
                context,
                flags=re.IGNORECASE,
            ):
                return True

    return False


def reclassify_entity(
    entity: EntityRecord,
) -> EntityRecord:
    """
    Reclassify entities using contextual evidence.
    """

    if looks_like_person(entity):
        entity["type"] = "PERSON"

        if entity.get("source") == "NER":
            entity["confidence"] = "HIGH"
        else:
            entity["confidence"] = "MEDIUM"

    return entity


def reclassify_entities(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Apply context-based reclassification to all entities.
    """

    return [
        reclassify_entity(entity)
        for entity in entities
    ]