from dataclasses import dataclass

from src.entity.lexicon import (
    COMMON_NON_ENTITIES,
    KNOWN_ENTITY_TYPES,
    ROLE_WORDS,
    TITLE_WORDS,
)
from src.entity.name_detector import NameCandidate
from src.entity.types import EntityRecord


@dataclass
class RecoveredCandidate:
    name: str
    occurrences: int
    score: int
    context_hits: int
    title_hits: int
    multiword_hits: int
    reason: str


def _contains_generic_component(name: str) -> bool:
    """
    Reject recovery-only multiword artefacts containing generic
    words, titles, or roles. Explicit known entities are exempt.
    """

    if name in KNOWN_ENTITY_TYPES:
        return False

    parts = name.split()

    return any(
        part in COMMON_NON_ENTITIES
        or part in TITLE_WORDS
        or part in ROLE_WORDS
        for part in parts
    )


def _is_component_of_known_multiword_entity(name: str) -> bool:
    """
    Reject a recovery candidate that is only one component of an
    already known multiword entity.

    Examples:
        Γκρίζοι -> Γκρίζοι Λόφοι
        Απόκρυφου -> Απόκρυφου Μουσείου
        Χρυσής -> Χρυσής Εποχής

    This rule is intentionally used only in recovery promotion.
    The main detector may still keep legitimate standalone names.
    """

    if not name or name in KNOWN_ENTITY_TYPES:
        return False

    candidate_parts = name.split()

    for known_name in KNOWN_ENTITY_TYPES:
        known_parts = known_name.split()

        if len(known_parts) <= len(candidate_parts):
            continue

        window_size = len(candidate_parts)

        for start in range(len(known_parts) - window_size + 1):
            if known_parts[start:start + window_size] == candidate_parts:
                return True

    return False


def build_recovery_candidates(
    existing_entities: list[EntityRecord],
    name_candidates: list[NameCandidate],
    min_score: int = 12,
    min_context_hits: int = 3,
) -> list[RecoveredCandidate]:
    """
    Return only genuinely useful NEW recovery candidates.

    Recovery is intentionally stricter than the main detector.
    A candidate is promoted only when it has strong evidence:

    - title evidence, or
    - repeated multiword evidence, or
    - multiword evidence plus person-context evidence, or
    - strong repeated person-context evidence.

    Weak one-off capitalized phrases stay diagnostic-only.
    """

    existing_names = {
        entity["entity"]
        for entity in existing_entities
    }

    recovered: list[RecoveredCandidate] = []

    for candidate in name_candidates:
        if candidate.name in existing_names:
            continue

        if candidate.name in KNOWN_ENTITY_TYPES:
            continue

        if candidate.name in COMMON_NON_ENTITIES:
            continue

        if _contains_generic_component(candidate.name):
            continue

        if _is_component_of_known_multiword_entity(candidate.name):
            continue

        strong_title = candidate.title_hits >= 1

        repeated_multiword = (
            candidate.multiword_hits >= 2
            and candidate.occurrences >= 2
        )

        contextual_multiword = (
            candidate.multiword_hits >= 1
            and candidate.context_hits >= 1
            and candidate.occurrences >= 1
        )

        strong_context = (
            candidate.context_hits >= min_context_hits
            and candidate.score >= min_score
            and candidate.occurrences >= 2
        )

        if not (
            strong_title
            or repeated_multiword
            or contextual_multiword
            or strong_context
        ):
            continue

        reasons: list[str] = []

        if strong_title:
            reasons.append(
                f"title evidence={candidate.title_hits}"
            )

        if repeated_multiword:
            reasons.append(
                f"repeated multiword evidence={candidate.multiword_hits}"
            )

        elif contextual_multiword:
            reasons.append(
                f"multiword+context evidence={candidate.multiword_hits}/"
                f"{candidate.context_hits}"
            )

        if strong_context:
            reasons.append(
                f"context evidence={candidate.context_hits}"
            )

        recovered.append(
            RecoveredCandidate(
                name=candidate.name,
                occurrences=candidate.occurrences,
                score=candidate.score,
                context_hits=candidate.context_hits,
                title_hits=candidate.title_hits,
                multiword_hits=candidate.multiword_hits,
                reason=", ".join(reasons),
            )
        )

    recovered.sort(
        key=lambda item: (
            -item.score,
            -item.occurrences,
            item.name,
        )
    )

    return recovered
