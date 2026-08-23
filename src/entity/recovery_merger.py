from dataclasses import dataclass

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


def build_recovery_candidates(
    existing_entities: list[EntityRecord],
    name_candidates: list[NameCandidate],
    min_score: int = 12,
    min_context_hits: int = 3,
) -> list[RecoveredCandidate]:
    """
    Return only NEW recovery candidates that are not already present
    in the main classified entity list.

    The goal is high recall without automatically promoting
    everything to PERSON.
    """

    existing_names = {
        entity["entity"]
        for entity in existing_entities
    }

    recovered: list[RecoveredCandidate] = []

    for candidate in name_candidates:
        if candidate.name in existing_names:
            continue

        strong_title = candidate.title_hits >= 1

        strong_multiword = (
            candidate.multiword_hits >= 1
            and candidate.occurrences >= 1
        )

        strong_context = (
            candidate.context_hits >= min_context_hits
            and candidate.score >= min_score
            and candidate.occurrences >= 2
        )

        if not (
            strong_title
            or strong_multiword
            or strong_context
        ):
            continue

        reasons: list[str] = []

        if strong_title:
            reasons.append(
                f"title evidence={candidate.title_hits}"
            )

        if strong_multiword:
            reasons.append(
                f"multiword evidence={candidate.multiword_hits}"
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