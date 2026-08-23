import re
from collections import defaultdict

from src.entity.lexicon import KNOWN_ENTITY_TYPES
from src.entity.types import (
    EntityRecord,
    EntitySpan,
)


def _spans_overlap(
    left: EntitySpan,
    right: EntitySpan,
) -> bool:
    """
    Return True when two spans overlap.
    """

    return (
        left["start"] < right["end"]
        and right["start"] < left["end"]
    )


def _span_length(
    span: EntitySpan,
) -> int:
    """
    Return span length.
    """

    return (
        span["end"]
        - span["start"]
    )


def _keep_longest_non_overlapping_matches(
    matches: list[
        tuple[
            str,
            str,
            EntitySpan,
        ]
    ],
) -> list[
    tuple[
        str,
        str,
        EntitySpan,
    ]
]:
    """
    Resolve overlapping known-entity matches.

    When multiple known entities overlap at the same
    textual occurrence, prefer the longest span.

    Example:

        Λίαμ Ράλιους Ντέρμοντ

    Possible raw known matches:

        Λίαμ
        Ντέρμοντ
        Λίαμ Ράλιους Ντέρμοντ

    Result:

        Λίαμ Ράλιους Ντέρμοντ

    Standalone occurrences of Λίαμ or Ντέρμοντ elsewhere
    remain untouched.
    """

    ordered = sorted(
        matches,
        key=lambda item: (
            -_span_length(item[2]),
            item[2]["start"],
            item[0],
        ),
    )

    accepted: list[
        tuple[
            str,
            str,
            EntitySpan,
        ]
    ] = []

    for candidate in ordered:
        candidate_span = candidate[2]

        overlaps_existing = any(
            _spans_overlap(
                candidate_span,
                accepted_span,
            )
            for (
                _accepted_name,
                _accepted_type,
                accepted_span,
            ) in accepted
        )

        if overlaps_existing:
            continue

        accepted.append(
            candidate
        )

    return sorted(
        accepted,
        key=lambda item: (
            item[2]["start"],
            item[2]["end"],
        ),
    )


def detect_known_entities(
    text: str,
) -> list[EntityRecord]:
    """
    Detect explicitly known entities from KNOWN_ENTITY_TYPES.

    KNOWN_ENTITY_TYPES is authoritative.

    Matching is:
    - exact
    - case-sensitive
    - word-boundary protected

    Every accepted occurrence stores its exact global span.

    Overlapping known matches are resolved by keeping the
    longest entity at that textual position.
    """

    raw_matches: list[
        tuple[
            str,
            str,
            EntitySpan,
        ]
    ] = []

    # =====================================================
    # Collect every raw known-entity match
    # =====================================================

    for (
        entity_name,
        entity_type,
    ) in KNOWN_ENTITY_TYPES.items():

        pattern = re.compile(
            rf"(?<!\w)"
            rf"{re.escape(entity_name)}"
            rf"(?!\w)"
        )

        for match in pattern.finditer(
            text
        ):
            span = EntitySpan(
                start=match.start(),
                end=match.end(),
            )

            raw_matches.append(
                (
                    entity_name,
                    entity_type,
                    span,
                )
            )

    if not raw_matches:
        return []

    # =====================================================
    # Longest-match overlap resolution
    # =====================================================

    accepted_matches = (
        _keep_longest_non_overlapping_matches(
            raw_matches
        )
    )

    # =====================================================
    # Group accepted occurrences by entity
    # =====================================================

    grouped_spans: dict[
        tuple[str, str],
        list[EntitySpan],
    ] = defaultdict(list)

    for (
        entity_name,
        entity_type,
        span,
    ) in accepted_matches:

        grouped_spans[
            (
                entity_name,
                entity_type,
            )
        ].append(span)

    # =====================================================
    # Build EntityRecords
    # =====================================================

    results: list[EntityRecord] = []

    for (
        entity_name,
        entity_type,
    ), spans in grouped_spans.items():

        entity_record: EntityRecord = {
            "entity": entity_name,
            "type": entity_type,
            "source": "KNOWN",
            "occurrences": len(spans),
            "spans": spans,
            "confidence": "HIGH",
            "classification_reason": (
                "known entity dictionary match: "
                f"{entity_type}"
            ),
            "person_score": 0,
            "location_score": 0,
            "keep": True,
        }

        results.append(
            entity_record
        )

    return sorted(
        results,
        key=lambda item: (
            -item["occurrences"],
            item["entity"],
        ),
    )