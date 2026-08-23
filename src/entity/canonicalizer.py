from collections import defaultdict

from src.entity.aliases import CANONICAL_ENTITY_ALIASES
from src.entity.types import (
    EntityRecord,
    EntitySpan,
)


# =========================================================
# Canonical name
# =========================================================

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


# =========================================================
# Span helpers
# =========================================================

def _spans_overlap(
    left: EntitySpan,
    right: EntitySpan,
) -> bool:
    """
    Return True when two textual spans overlap.
    """

    return (
        left["start"] < right["end"]
        and right["start"] < left["end"]
    )


def _span_length(
    span: EntitySpan,
) -> int:
    """
    Return the number of characters covered by a span.
    """

    return (
        span["end"]
        - span["start"]
    )


def _deduplicate_exact_spans(
    spans: list[EntitySpan],
) -> list[EntitySpan]:
    """
    Remove exact duplicate spans.
    """

    seen: set[
        tuple[int, int]
    ] = set()

    result: list[EntitySpan] = []

    for span in spans:
        key = (
            span["start"],
            span["end"],
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(span)

    return result


def _merge_overlapping_spans(
    spans: list[EntitySpan],
) -> list[EntitySpan]:
    """
    Convert overlapping detections of the same canonical
    entity into one textual occurrence.

    The longest span in each overlapping group is retained.

    Example:

        Τόρβιλ
        Θάεντ
        Τόρβιλ Θάεντ

    when they refer to the same textual phrase, they count
    as ONE canonical occurrence.

    A standalone Τόρβιλ elsewhere remains a separate
    occurrence.
    """

    if not spans:
        return []

    unique_spans = (
        _deduplicate_exact_spans(
            spans
        )
    )

    # Prefer longer detections first.
    ordered = sorted(
        unique_spans,
        key=lambda span: (
            -_span_length(span),
            span["start"],
            span["end"],
        ),
    )

    accepted: list[EntitySpan] = []

    for candidate in ordered:

        overlaps_existing = any(
            _spans_overlap(
                candidate,
                existing,
            )
            for existing in accepted
        )

        if overlaps_existing:
            continue

        accepted.append(
            candidate
        )

    return sorted(
        accepted,
        key=lambda span: (
            span["start"],
            span["end"],
        ),
    )


# =========================================================
# Canonical entity merging
# =========================================================

def canonicalize_entities(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Merge aliases referring to the same canonical entity.

    When span information is available, occurrence counts
    are calculated from unique non-overlapping textual
    occurrences instead of blindly summing alias counts.

    Example:

        Τόρβιλ
        Θάεντ
        Τόρβιλ Θάεντ

    can all canonicalize to:

        Τόρβιλ Θάεντ

    without triple-counting the same phrase.
    """

    grouped: dict[
        str,
        list[EntityRecord],
    ] = defaultdict(list)

    for entity in entities:

        canonical_name = (
            canonicalize_entity_name(
                entity["entity"]
            )
        )

        grouped[
            canonical_name
        ].append(entity)

    canonical_entities: list[
        EntityRecord
    ] = []

    confidence_rank = {
        "HIGH": 4,
        "MEDIUM": 3,
        "REVIEW": 2,
        "LOW": 1,
        "REJECT": 0,
        "": 0,
    }

    source_rank = {
        "KNOWN": 3,
        "NER": 2,
        "HEURISTIC": 1,
        "": 0,
    }

    for (
        canonical_name,
        group,
    ) in grouped.items():

        # -------------------------------------------------
        # Select strongest metadata record
        # -------------------------------------------------

        best_entity = max(
            group,
            key=lambda entity: (
                confidence_rank.get(
                    entity.get(
                        "confidence",
                        "",
                    ),
                    0,
                ),
                source_rank.get(
                    entity.get(
                        "source",
                        "",
                    ),
                    0,
                ),
                entity.get(
                    "occurrences",
                    0,
                ),
            ),
        )

        # -------------------------------------------------
        # Collect all available spans
        # -------------------------------------------------

        all_spans: list[
            EntitySpan
        ] = []

        records_without_spans = 0

        for entity in group:

            entity_spans = entity.get(
                "spans",
                [],
            )

            if entity_spans:
                all_spans.extend(
                    entity_spans
                )
            else:
                # Compatibility fallback for records
                # produced by older/non-span-aware code.
                records_without_spans += (
                    entity.get(
                        "occurrences",
                        0,
                    )
                )

        # -------------------------------------------------
        # Span-aware occurrence counting
        # -------------------------------------------------

        if all_spans:

            canonical_spans = (
                _merge_overlapping_spans(
                    all_spans
                )
            )

            total_occurrences = (
                len(canonical_spans)
                + records_without_spans
            )

        else:
            # Backwards-compatible fallback.
            canonical_spans = []

            total_occurrences = sum(
                entity.get(
                    "occurrences",
                    0,
                )
                for entity in group
            )

        # -------------------------------------------------
        # Build canonical record
        # -------------------------------------------------

        merged: EntityRecord = {
            **best_entity,
            "entity": canonical_name,
            "occurrences": (
                total_occurrences
            ),
        }

        if canonical_spans:
            merged[
                "spans"
            ] = canonical_spans

        canonical_entities.append(
            merged
        )

    return sorted(
        canonical_entities,
        key=lambda item: (
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