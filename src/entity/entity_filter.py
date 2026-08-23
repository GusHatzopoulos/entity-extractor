from src.entity.context_analyzer import get_entity_contexts
from src.entity.lexicon import (
    COMMON_NON_ENTITIES,
    KNOWN_ENTITY_TYPES,
)
from src.entity.types import EntityRecord


def evaluate_entity(
    entity: EntityRecord,
    text: str,
) -> EntityRecord:
    """
    Add filtering, confidence, and context metadata to an entity.

    Design goals:
    - KNOWN entities are authoritative.
    - Explicit common-noise entries are rejected.
    - NER PERSON is no longer trusted automatically at HIGH confidence.
    - Confidence reflects repetition plus contextual evidence.
    - Low-confidence items remain in diagnostic exports unless rejected
      explicitly; publication filtering is handled later by final_selector.
    """

    name = entity["entity"]
    entity_type = entity["type"]
    source = entity["source"]
    occurrences = entity["occurrences"]

    keep = True
    confidence = "REVIEW"

    # -----------------------------------------------------
    # Authoritative known entities
    # -----------------------------------------------------

    if name in KNOWN_ENTITY_TYPES:
        keep = True
        confidence = "HIGH"

    # -----------------------------------------------------
    # Explicit noise
    # -----------------------------------------------------

    elif name in COMMON_NON_ENTITIES:
        keep = False
        confidence = "REJECT"

    # -----------------------------------------------------
    # Initial confidence before context reclassification
    # -----------------------------------------------------

    elif source == "NER":
        # Repetition gives useful evidence, but a single spaCy PERSON
        # prediction must not automatically become publication-grade.
        if occurrences >= 5:
            confidence = "MEDIUM"
        elif occurrences >= 2:
            confidence = "REVIEW"
        else:
            confidence = "LOW"

    elif source == "HEURISTIC":
        if occurrences >= 5:
            confidence = "REVIEW"
        elif occurrences >= 2:
            confidence = "LOW"
        else:
            confidence = "LOW"

    # -----------------------------------------------------
    # Context collection
    # -----------------------------------------------------

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
    Evaluate entities and remove only explicit rejected noise.

    This stage intentionally remains recall-oriented.
    The final publication precision gate lives in final_selector.py.
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
