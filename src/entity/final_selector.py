from src.entity.types import EntityRecord


FINAL_ENTITY_TYPES = {
    "PERSON",
    "LOCATION",
    "GPE",
}


def select_final_entities(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Keep only character names and places/locations
    for the final user-facing output.
    """

    selected = [
        entity
        for entity in entities
        if entity.get("type") in FINAL_ENTITY_TYPES
    ]

    return sorted(
        selected,
        key=lambda item: (
            item["type"],
            -item["occurrences"],
            item["entity"],
        ),
    )


def select_persons(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Return only detected persons/characters.
    """

    return [
        entity
        for entity in entities
        if entity.get("type") == "PERSON"
    ]


def select_locations(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Return only locations.
    """

    return [
        entity
        for entity in entities
        if entity.get("type") in {"LOCATION", "GPE"}
    ]
