from collections import defaultdict

from src.entity.aliases import CANONICAL_ENTITY_ALIASES
from src.entity.types import EntityRecord


def canonicalize_entity_name(
    name: str,
) -> str:
    """
    Return the canonical form of an entity name.

    If no alias mapping exists, return the original name.
    """

    return CANONICAL_ENTITY_ALIASES.get(
        name,
        name,
    )


def canonicalize_entities(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Merge aliases that refer to the same canonical entity.

    Occurrences are summed.
    Existing metadata is preserved from the strongest
    available record where possible.
    """

    grouped: dict[
        str,
        list[EntityRecord],
    ] = defaultdict(list)

    for entity in entities:
        canonical_name = canonicalize_entity_name(
            entity["entity"]
        )

        grouped[
            canonical_name
        ].append(entity)

    canonical_entities: list[EntityRecord] = []

    for canonical_name, group in grouped.items():
        total_occurrences = sum(
            entity.get("occurrences", 0)
            for entity in group
        )

        # Prefer records with stronger confidence.
        confidence_rank = {
            "HIGH": 4,
            "MEDIUM": 3,
            "REVIEW": 2,
            "LOW": 1,
            "REJECT": 0,
            "": 0,
        }

        best_entity = max(
            group,
            key=lambda entity: (
                confidence_rank.get(
                    entity.get("confidence", ""),
                    0,
                ),
                entity.get("occurrences", 0),
            ),
        )

        merged: EntityRecord = {
            **best_entity,
            "entity": canonical_name,
            "occurrences": total_occurrences,
        }

        canonical_entities.append(
            merged
        )

    return sorted(
        canonical_entities,
        key=lambda item: (
            -item.get("occurrences", 0),
            item.get("entity", ""),
        ),
    )