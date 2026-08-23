import re
import unicodedata
from collections import defaultdict

from src.entity.aliases import CANONICAL_ENTITY_ALIASES
from src.entity.types import (
    EntityRecord,
    EntitySpan,
)


def _comparison_key(
    name: str,
) -> str:
    """
    Build a comparison-only key.

    It is intentionally used for grouping/lookup only; it never
    changes the spelling shown to the user.

    This merges manuscript variants such as:
        ΑΛΒΙΝΑ / Αλβίνα
        ΚΟΥΕΝΤΙΝ / Κουέντιν
        ΛΑΝΣ / Λανς

    Accents and casing are ignored only for comparison.
    """

    normalized = unicodedata.normalize(
        "NFD",
        name,
    )

    without_marks = "".join(
        char
        for char in normalized
        if unicodedata.category(char) != "Mn"
    )

    without_marks = unicodedata.normalize(
        "NFC",
        without_marks,
    )

    without_marks = re.sub(
        r"\s+",
        " ",
        without_marks,
    ).strip()

    return without_marks.casefold()


_ALIAS_BY_KEY = {
    _comparison_key(alias): canonical
    for alias, canonical
    in CANONICAL_ENTITY_ALIASES.items()
}


def canonicalize_entity_name(
    name: str,
) -> str:
    """
    Return the explicit canonical alias when available.

    Lookup is exact first and accent/case-insensitive second.
    """

    exact = CANONICAL_ENTITY_ALIASES.get(
        name
    )

    if exact is not None:
        return exact

    return _ALIAS_BY_KEY.get(
        _comparison_key(name),
        name,
    )


def _spans_overlap(
    left: EntitySpan,
    right: EntitySpan,
) -> bool:
    return (
        left["start"] < right["end"]
        and right["start"] < left["end"]
    )


def _span_length(
    span: EntitySpan,
) -> int:
    return (
        span["end"]
        - span["start"]
    )


def _deduplicate_exact_spans(
    spans: list[EntitySpan],
) -> list[EntitySpan]:
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
    Keep one occurrence for overlapping detections of the
    same canonical entity, preferring the longest span.
    """

    if not spans:
        return []

    unique_spans = _deduplicate_exact_spans(
        spans
    )

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
        if any(
            _spans_overlap(
                candidate,
                existing,
            )
            for existing in accepted
        ):
            continue

        accepted.append(candidate)

    return sorted(
        accepted,
        key=lambda span: (
            span["start"],
            span["end"],
        ),
    )


def _display_rank(
    entity: EntityRecord,
    canonical_name: str,
) -> tuple[int, int, int, int]:
    """
    Prefer stable human-readable spellings for a merged group.

    Priority:
    1. exact canonical target
    2. non-ALL-CAPS spelling
    3. stronger source
    4. more occurrences
    """

    name = entity["entity"]

    source_rank = {
        "KNOWN": 3,
        "NER": 2,
        "HEURISTIC": 1,
        "": 0,
    }

    return (
        int(name == canonical_name),
        int(not name.isupper()),
        source_rank.get(
            entity.get("source", ""),
            0,
        ),
        entity.get("occurrences", 0),
    )


def canonicalize_entities(
    entities: list[EntityRecord],
) -> list[EntityRecord]:
    """
    Merge aliases and case/accent variants while preserving
    span-aware occurrence counting.
    """

    grouped: dict[
        str,
        list[
            tuple[
                str,
                EntityRecord,
            ]
        ],
    ] = defaultdict(list)

    canonical_display_by_key: dict[
        str,
        str,
    ] = {}

    for entity in entities:
        canonical_name = canonicalize_entity_name(
            entity["entity"]
        )

        group_key = _comparison_key(
            canonical_name
        )

        grouped[group_key].append(
            (
                canonical_name,
                entity,
            )
        )

        # Explicit alias target wins as the display spelling.
        if (
            canonical_name
            != entity["entity"]
            or group_key
            not in canonical_display_by_key
        ):
            canonical_display_by_key[
                group_key
            ] = canonical_name

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

    for group_key, grouped_items in grouped.items():
        canonical_names = [
            item[0]
            for item in grouped_items
        ]

        group = [
            item[1]
            for item in grouped_items
        ]

        canonical_name = (
            canonical_display_by_key.get(
                group_key
            )
            or max(
                group,
                key=lambda entity: (
                    int(
                        not entity["entity"].isupper()
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
            )["entity"]
        )

        # If the chosen display is still ALL CAPS but a normal-cased
        # variant exists, prefer the normal-cased manuscript form.
        best_display_entity = max(
            group,
            key=lambda entity: _display_rank(
                entity,
                canonical_name,
            ),
        )

        if (
            canonical_name.isupper()
            and not best_display_entity[
                "entity"
            ].isupper()
        ):
            canonical_name = (
                best_display_entity[
                    "entity"
                ]
            )

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
                records_without_spans += (
                    entity.get(
                        "occurrences",
                        0,
                    )
                )

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
            canonical_spans = []

            total_occurrences = sum(
                entity.get(
                    "occurrences",
                    0,
                )
                for entity in group
            )

        merged: EntityRecord = {
            **best_entity,
            "entity": canonical_name,
            "occurrences": total_occurrences,
        }

        if canonical_spans:
            merged["spans"] = (
                canonical_spans
            )

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
