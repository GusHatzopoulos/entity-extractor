import re
from collections import Counter

from src.entity.lexicon import KNOWN_ENTITY_TYPES
from src.entity.types import EntityRecord


def detect_known_entities(
    text: str,
) -> list[EntityRecord]:
    """
    Detect all explicitly known entities from KNOWN_ENTITY_TYPES.

    This detector is authoritative:
    if an entity is present in KNOWN_ENTITY_TYPES and appears
    in the text, it is returned with the configured type.

    Matching is exact and case-sensitive.
    """

    results: list[EntityRecord] = []

    for entity_name, entity_type in KNOWN_ENTITY_TYPES.items():
        pattern = re.compile(
            rf"(?<!\w)"
            rf"{re.escape(entity_name)}"
            rf"(?!\w)"
        )

        matches = pattern.findall(text)

        if not matches:
            continue

        results.append(
            {
                "entity": entity_name,
                "type": entity_type,
                "source": "KNOWN",
                "occurrences": len(matches),
                "confidence": "HIGH",
                "classification_reason": (
                    f"known entity dictionary match: {entity_type}"
                ),
                "person_score": 0,
                "location_score": 0,
                "keep": True,
            }
        )

    return sorted(
        results,
        key=lambda item: (
            -item["occurrences"],
            item["entity"],
        ),
    )