from src.entity.types import EntityRecord


FINAL_ENTITY_TYPES = {
    "PERSON",
    "LOCATION",
    "GPE",
}


def _is_known_entity(
    entity: EntityRecord,
) -> bool:
    """
    Explicit project knowledge is authoritative.
    """

    return (
        entity.get("source") == "KNOWN"
        and entity.get("type") in FINAL_ENTITY_TYPES
        and entity.get("keep", True)
    )


def _has_context_evidence(
    entity: EntityRecord,
    threshold: int = 3,
) -> bool:
    """
    Return True when PERSON/LOCATION scoring produced meaningful evidence.
    """

    return max(
        entity.get("person_score", 0),
        entity.get("location_score", 0),
    ) >= threshold


def _is_supported_ner_person(
    entity: EntityRecord,
) -> bool:
    """
    Conservative publication gate for spaCy PERSON detections.

    Keep when at least one of the following is true:
    - context classifier upgraded confidence to HIGH/MEDIUM
    - meaningful person/location contextual evidence exists
    - the name repeats enough times to be unlikely to be accidental noise

    Single-occurrence NER PERSON with no context evidence is kept out of
    the publication appendix but remains available in diagnostic exports.
    """

    if (
        entity.get("source") != "NER"
        or entity.get("type") != "PERSON"
        or not entity.get("keep", True)
    ):
        return False

    confidence = entity.get(
        "confidence",
        "REVIEW",
    )

    occurrences = entity.get(
        "occurrences",
        0,
    )

    person_score = entity.get(
        "person_score",
        0,
    )

    location_score = entity.get(
        "location_score",
        0,
    )

    if confidence in {
        "HIGH",
        "MEDIUM",
    }:
        return True

    if person_score >= 3 and person_score > location_score:
        return True

    # Repetition alone is allowed only at a conservative threshold.
    if occurrences >= 3:
        return True

    return False


def _is_supported_ner_location(
    entity: EntityRecord,
) -> bool:
    """
    Conservative publication gate for spaCy LOCATION/GPE detections.

    LOCATION/GPE is more error-prone than PERSON in this corpus, so
    repetition alone is not enough. Require contextual support or an
    explicit confidence upgrade by the classifier.
    """

    if (
        entity.get("source") != "NER"
        or entity.get("type") not in {"LOCATION", "GPE"}
        or not entity.get("keep", True)
    ):
        return False

    confidence = entity.get(
        "confidence",
        "REVIEW",
    )

    location_score = entity.get(
        "location_score",
        0,
    )

    person_score = entity.get(
        "person_score",
        0,
    )

    if confidence in {
        "HIGH",
        "MEDIUM",
    }:
        return True

    if (
        location_score >= 3
        and location_score > person_score
    ):
        return True

    return False


def _is_supported_heuristic_entity(
    entity: EntityRecord,
) -> bool:
    """
    Heuristic entities require real contextual evidence.

    Repetition by itself is not enough for publication.
    """

    if (
        entity.get("source") != "HEURISTIC"
        or entity.get("type") not in FINAL_ENTITY_TYPES
        or not entity.get("keep", True)
    ):
        return False

    confidence = entity.get(
        "confidence",
        "REVIEW",
    )

    occurrences = entity.get(
        "occurrences",
        0,
    )

    person_score = entity.get(
        "person_score",
        0,
    )

    location_score = entity.get(
        "location_score",
        0,
    )

    strongest_score = max(
        person_score,
        location_score,
    )

    if confidence in {
        "HIGH",
        "MEDIUM",
    }:
        return strongest_score >= 3

    if (
        confidence == "REVIEW"
        and occurrences >= 2
        and strongest_score >= 3
    ):
        return True

    return False


def _is_final_entity(
    entity: EntityRecord,
) -> bool:
    """
    Final publication decision.
    """

    if not entity.get(
        "keep",
        True,
    ):
        return False

    if (
        entity.get("type")
        not in FINAL_ENTITY_TYPES
    ):
        return False

    if _is_known_entity(entity):
        return True

    if _is_supported_ner_person(entity):
        return True

    if _is_supported_ner_location(entity):
        return True

    if _is_supported_heuristic_entity(entity):
        return True

    return False


def select_final_entities(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Select publication-oriented PERSON / LOCATION / GPE entities.

    Diagnostic exports remain broader. This function is the final
    precision gate for the book appendix.
    """

    selected = [
        entity
        for entity in entities
        if _is_final_entity(entity)
    ]

    return sorted(
        selected,
        key=lambda item: (
            item.get("type", ""),
            -item.get(
                "occurrences",
                0,
            ),
            item.get(
                "entity",
                "",
            ),
        ),
    )


def select_persons(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Return only PERSON entities.
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
    Return LOCATION/GPE entities.
    """

    return [
        entity
        for entity in entities
        if entity.get("type") in {
            "LOCATION",
            "GPE",
        }
    ]
