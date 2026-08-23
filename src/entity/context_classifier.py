import re

from src.entity.types import EntityRecord
from src.entity.lexicon import KNOWN_ENTITY_TYPES


PERSON_CONTEXT_PATTERNS = [
    # Strong speech evidence
    (r"\bείπε\s+(?:ο|η)\s+{name}\b", 4, "speech verb + article"),
    (r"\bρώτησε\s+(?:ο|η)\s+{name}\b", 4, "speech verb + article"),
    (r"\bαπάντησε\s+(?:ο|η)\s+{name}\b", 4, "speech verb + article"),
    (r"\bφώναξε\s+(?:ο|η)\s+{name}\b", 4, "speech verb + article"),
    (r"\bψιθύρισε\s+(?:ο|η)\s+{name}\b", 4, "speech verb + article"),
    (r"\bμίλησε\s+(?:ο|η)\s+{name}\b", 4, "speech verb + article"),

    # Name followed by speech verb
    (r"\b(?:ο|η)\s+{name}\s+είπε\b", 4, "article + name + speech verb"),
    (r"\b(?:ο|η)\s+{name}\s+ρώτησε\b", 4, "article + name + speech verb"),
    (r"\b(?:ο|η)\s+{name}\s+απάντησε\b", 4, "article + name + speech verb"),
    (r"\b(?:ο|η)\s+{name}\s+φώναξε\b", 4, "article + name + speech verb"),

    # Character actions
    (r"\b(?:ο|η)\s+{name}\s+κοίταξε\b", 3, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+σηκώθηκε\b", 3, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+γύρισε\b", 3, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+προχώρησε\b", 3, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+χαμογέλασε\b", 3, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+έγνεψε\b", 3, "article + name + action verb"),
    (r"\b(?:ο|η)\s+{name}\s+αναστέναξε\b", 3, "article + name + action verb"),

    # Coordinated people
    (
        r"\b(?:ο|η)\s+\w+\s+και\s+(?:ο|η)\s+{name}\b",
        4,
        "coordinated personal articles",
    ),
    (
        r"\b(?:ο|η)\s+{name}\s+και\s+(?:ο|η)\s+\w+\b",
        4,
        "coordinated personal articles",
    ),

    # Personal articles / relations
    (r"\bτον\s+{name}\b", 1, "personal article"),
    (r"\bτην\s+{name}\b", 1, "personal article"),
    (r"\bτου\s+{name}\b", 1, "personal article"),
    (r"\bτης\s+{name}\b", 1, "personal article"),
    (r"\bμε\s+τον\s+{name}\b", 2, "preposition + personal article"),
    (r"\bμε\s+την\s+{name}\b", 2, "preposition + personal article"),
    (
        r"\bδίπλα\s+στον\s+{name}\b",
        3,
        "spatial relation + personal article",
    ),
    (
        r"\bδίπλα\s+στην\s+{name}\b",
        3,
        "spatial relation + personal article",
    ),
]


LOCATION_CONTEXT_PATTERNS = [
    # Movement
    (r"\bπρος\s+(?:το|την|τη|τον)\s+{name}\b", 4, "movement toward location"),
    (r"\bπήγε\s+(?:στο|στη|στην|στον)\s+{name}\b", 4, "movement to location"),
    (r"\bέφτασε\s+(?:στο|στη|στην|στον)\s+{name}\b", 4, "arrival at location"),
    (r"\bταξίδεψε\s+(?:στο|στη|στην|στον|προς)\s+{name}\b", 4, "travel to location"),

    # Presence
    (r"\bβρισκόταν\s+(?:στο|στη|στην|στον)\s+{name}\b", 4, "presence at location"),
    (r"\bβρίσκονταν\s+(?:στο|στη|στην|στον)\s+{name}\b", 4, "presence at location"),
    (r"\bέμενε\s+(?:στο|στη|στην|στον)\s+{name}\b", 4, "residence at location"),

    # Origin
    (r"\bαπό\s+(?:το|τη|την|τον)\s+{name}\b", 3, "origin from location"),
    (r"\bέφυγε\s+από\s+(?:το|τη|την|τον)\s+{name}\b", 4, "departure from location"),

    # Strong structural evidence
    (r"\bκάστρο\s+{name}\b", 8, "named castle"),
    (r"\bκάστρο\s+(?:του|της)\s+{name}\b", 8, "castle relation"),
    (r"\bπόλη\s+{name}\b", 8, "named city"),
    (r"\bπόλη\s+(?:του|της)\s+{name}\b", 8, "city relation"),
    (r"\bχωριό\s+{name}\b", 8, "named village"),
    (r"\bχωριό\s+(?:του|της)\s+{name}\b", 8, "village relation"),
    (r"\bβασίλειο\s+{name}\b", 8, "named kingdom"),
    (r"\bβασίλειο\s+(?:του|της)\s+{name}\b", 8, "kingdom relation"),
    (r"\bπεριοχή\s+{name}\b", 7, "named region"),
    (r"\bπεριοχή\s+(?:του|της)\s+{name}\b", 7, "region relation"),
    (r"\bεπικράτεια\s+(?:του|της)\s+{name}\b", 8, "territory relation"),

    # Geographic relations
    (
        r"\bβόρεια\s+(?:του|της|από\s+το|από\s+τη|από\s+την)\s+{name}\b",
        5,
        "geographic relation",
    ),
    (
        r"\bνότια\s+(?:του|της|από\s+το|από\s+τη|από\s+την)\s+{name}\b",
        5,
        "geographic relation",
    ),
    (
        r"\bανατολικά\s+(?:του|της|από\s+το|από\s+τη|από\s+την)\s+{name}\b",
        5,
        "geographic relation",
    ),
    (
        r"\bδυτικά\s+(?:του|της|από\s+το|από\s+τη|από\s+την)\s+{name}\b",
        5,
        "geographic relation",
    ),
]


def score_patterns(
    entity: EntityRecord,
    patterns: list[tuple[str, int, str]],
) -> tuple[int, list[str]]:
    """
    Score entity contexts against a set of regex patterns.
    """

    name = re.escape(entity["entity"])
    contexts = entity.get("contexts", [])

    score = 0
    reasons: list[str] = []

    for context in contexts:
        for pattern, points, reason in patterns:
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
    Reclassify an entity using competing PERSON and LOCATION evidence.
    """

    original_type = entity["type"]
    entity["original_type"] = original_type

    known_type = KNOWN_ENTITY_TYPES.get(entity["entity"])

    if known_type is not None:
        entity["type"] = known_type
        entity["confidence"] = "HIGH"
        entity["classification_reason"] = (
            f"known entity override: {known_type}"
        )
        entity["person_score"] = 0
        entity["location_score"] = 0

        return entity

    person_score, person_reasons = score_patterns(
        entity,
        PERSON_CONTEXT_PATTERNS,
    )

    location_score, location_reasons = score_patterns(
        entity,
        LOCATION_CONTEXT_PATTERNS,
    )

    entity["person_score"] = person_score
    entity["location_score"] = location_score

    # Strong PERSON advantage
    if (
        location_score >= 8
        and location_score >= person_score
    ):
        entity["type"] = "LOCATION"
        entity["confidence"] = "HIGH"
        entity["classification_reason"] = (
            f"strong structural LOCATION evidence "
            f"({location_score} vs {person_score}): "
            + ", ".join(location_reasons)
        )

        return entity
    if (
        person_score >= 6
        and person_score >= location_score + 3
    ):
        entity["type"] = "PERSON"
        entity["confidence"] = "HIGH"
        entity["classification_reason"] = (
            f"PERSON evidence wins "
            f"({person_score} vs {location_score}): "
            + ", ".join(person_reasons)
        )

    # Moderate PERSON advantage
    elif (
        person_score >= 3
        and person_score > location_score
    ):
        entity["type"] = "PERSON"
        entity["confidence"] = "MEDIUM"
        entity["classification_reason"] = (
            f"PERSON evidence stronger "
            f"({person_score} vs {location_score}): "
            + ", ".join(person_reasons)
        )

    # Strong LOCATION advantage
    elif (
        location_score >= 6
        and location_score >= person_score + 3
    ):
        entity["type"] = "LOCATION"
        entity["confidence"] = "HIGH"
        entity["classification_reason"] = (
            f"LOCATION evidence wins "
            f"({location_score} vs {person_score}): "
            + ", ".join(location_reasons)
        )

    # Moderate LOCATION advantage
    elif (
        location_score >= 3
        and location_score > person_score
    ):
        entity["type"] = "LOCATION"
        entity["confidence"] = "MEDIUM"
        entity["classification_reason"] = (
            f"LOCATION evidence stronger "
            f"({location_score} vs {person_score}): "
            + ", ".join(location_reasons)
        )

    else:
        entity["classification_reason"] = (
            f"no decisive context: "
            f"PERSON={person_score}, "
            f"LOCATION={location_score}"
        )

    return entity




def reclassify_entities(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Apply context-based multi-class reclassification.
    """

    return [
        reclassify_entity(entity)
        for entity in entities
    ]