import re

from src.entity.types import EntityRecord


PERSON_CONTEXT_PATTERNS = [
    (r"\bείπε\s+(?:ο|η)\s+{name}\b", 3, "speech verb + article"),
    (r"\bρώτησε\s+(?:ο|η)\s+{name}\b", 3, "speech verb + article"),
    (r"\bαπάντησε\s+(?:ο|η)\s+{name}\b", 3, "speech verb + article"),
    (r"\bφώναξε\s+(?:ο|η)\s+{name}\b", 3, "speech verb + article"),
    (r"\bψιθύρισε\s+(?:ο|η)\s+{name}\b", 3, "speech verb + article"),

    (r"\b(?:ο|η)\s+{name}\s+είπε\b", 3, "article + name + speech verb"),
    (r"\b(?:ο|η)\s+{name}\s+ρώτησε\b", 3, "article + name + speech verb"),
    (r"\b(?:ο|η)\s+{name}\s+απάντησε\b", 3, "article + name + speech verb"),

    (r"\b(?:ο|η)\s+{name}\s+κοίταξε\b", 2, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+σηκώθηκε\b", 2, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+γύρισε\b", 2, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+προχώρησε\b", 2, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+χαμογέλασε\b", 2, "article + name + action verb"),

    (r"\bτον\s+{name}\b", 1, "personal article"),
    (r"\bτην\s+{name}\b", 1, "personal article"),
    (r"\bτου\s+{name}\b", 1, "personal article"),
    (r"\bτης\s+{name}\b", 1, "personal article"),
    (r"\bμε\s+τον\s+{name}\b", 2, "preposition + personal article"),
    (r"\bμε\s+την\s+{name}\b", 2, "preposition + personal article"),
    (r"\bδίπλα\s+στον\s+{name}\b", 2, "spatial relation + personal article"),
    (r"\bδίπλα\s+στην\s+{name}\b", 2, "spatial relation + personal article"),
]


def get_person_context_score(
    entity: EntityRecord,
) -> tuple[int, list[str]]:
    """
    Calculate contextual evidence that an entity is a person.
    """

    name = re.escape(entity["entity"])
    contexts = entity.get("contexts", [])

    score = 0
    reasons: list[str] = []

    for context in contexts:
        for pattern, points, reason in PERSON_CONTEXT_PATTERNS:
            regex = pattern.format(name=name)

            if re.search(
                regex,
                context,
                flags=re.IGNORECASE,
            ):
                score += points

                if reason not in reasons:
                    reasons.append(reason)

    return score, reasons


def reclassify_entity(
    entity: EntityRecord,
) -> EntityRecord:
    """
    Reclassify an entity using contextual evidence.
    """

    score, reasons = get_person_context_score(entity)

    if score >= 3:
        entity["type"] = "PERSON"
        entity["confidence"] = "HIGH"
        entity["classification_reason"] = (
            f"context person score={score}: "
            + ", ".join(reasons)
        )

    elif score >= 2:
        entity["type"] = "PERSON"
        entity["confidence"] = "MEDIUM"
        entity["classification_reason"] = (
            f"context person score={score}: "
            + ", ".join(reasons)
        )

    else:
        entity["classification_reason"] = (
            f"context person score={score}"
        )

    entity["context_score"] = score

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