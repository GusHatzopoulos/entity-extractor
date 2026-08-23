from src.entity.context_analyzer import get_entity_contexts
from src.entity.lexicon import (COMMON_NON_ENTITIES, KNOWN_ENTITY_TYPES)
from src.entity.types import EntityRecord


def evaluate_entity(
    entity: EntityRecord,
    text: str,
) -> EntityRecord:
    """
    Add filtering, confidence, and context metadata to an entity.
    """

    name = entity["entity"]
    entity_type = entity["type"]
    source = entity["source"]
    occurrences = entity["occurrences"]

    keep = True
    confidence = "REVIEW"

    if name in KNOWN_ENTITY_TYPES:
        keep = True
        confidence = "HIGH"

    elif name in COMMON_NON_ENTITIES:
        keep = False
        confidence = "REJECT"

    elif source == "NER" and entity_type == "PERSON":
        confidence = "HIGH"

    elif source == "NER" and occurrences >= 5:
        confidence = "MEDIUM"

    elif source == "HEURISTIC" and occurrences >= 5:
        confidence = "REVIEW"

    elif source == "HEURISTIC" and occurrences < 2:
        confidence = "LOW"

    contexts = get_entity_contexts(
        text,
        name,
        max_contexts=12,
    )

    return {
        **entity,
        "confidence": confidence,
        "keep": keep,
        "contexts": contexts,
    }


def filter_entities(
    entities: list[EntityRecord],
    text: str,
) -> list[EntityRecord]:
    """
    Evaluate entities and remove rejected false positives.
    """

    evaluated: list[EntityRecord] = [
        evaluate_entity(entity, text)
        for entity in entities
    ]

    kept: list[EntityRecord] = [
        entity
        for entity in evaluated
        if entity.get("keep", True)
    ]

    return sorted(
        kept,
        key=lambda item: (
            -item["occurrences"],
            item["entity"],
        ),
    )
