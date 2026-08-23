from src.entity.types import (
    EntityRecord,
    EntitySpan,
)


def _span_key(
    span: EntitySpan,
) -> tuple[int, int]:
    return (
        span["start"],
        span["end"],
    )


def _spans_overlap(
    left: EntitySpan,
    right: EntitySpan,
) -> bool:
    return (
        left["start"] < right["end"]
        and right["start"] < left["end"]
    )


def _validate_span_bounds(
    span: EntitySpan,
    text_length: int,
) -> bool:
    """
    Check whether a span points to a valid slice
    inside the source text.
    """

    return (
        0 <= span["start"]
        < span["end"]
        <= text_length
    )


def _find_overlapping_pairs(
    spans: list[EntitySpan],
) -> list[
    tuple[
        EntitySpan,
        EntitySpan,
    ]
]:
    """
    Find remaining overlaps inside one canonical entity.

    A correctly canonicalized span list should normally
    contain no overlaps.
    """

    overlaps: list[
        tuple[
            EntitySpan,
            EntitySpan,
        ]
    ] = []

    ordered = sorted(
        spans,
        key=lambda span: (
            span["start"],
            span["end"],
        ),
    )

    for index, left in enumerate(
        ordered
    ):
        for right in ordered[
            index + 1:
        ]:
            if (
                right["start"]
                >= left["end"]
            ):
                break

            if _spans_overlap(
                left,
                right,
            ):
                overlaps.append(
                    (
                        left,
                        right,
                    )
                )

    return overlaps


def _print_span_examples(
    text: str,
    spans: list[EntitySpan],
    max_examples: int = 8,
    context_size: int = 45,
) -> None:
    """
    Print actual source-text fragments referenced by spans.
    """

    for index, span in enumerate(
        spans[:max_examples],
        start=1,
    ):
        start = span["start"]
        end = span["end"]

        detected_text = text[
            start:end
        ]

        context_start = max(
            0,
            start - context_size,
        )

        context_end = min(
            len(text),
            end + context_size,
        )

        context = text[
            context_start:context_end
        ]

        context = (
            context
            .replace("\n", " ")
            .replace("\r", " ")
        )

        print(
            f"  [{index}] "
            f"{start}:{end} "
            f"-> {detected_text!r}"
        )

        print(
            f"      ...{context}..."
        )


def validate_canonical_counts(
    text: str,
    entities: list[EntityRecord],
    names: list[str] | None = None,
) -> None:
    """
    Validate canonical occurrence counts against stored
    character spans.

    Checks:

    - occurrence count vs number of stored spans
    - duplicate exact spans
    - invalid/out-of-range spans
    - remaining overlapping canonical spans
    - actual source text represented by selected spans

    Important:
    This validates span/count consistency.

    It does NOT by itself prove that every detected span is
    semantically the correct character/location. That still
    requires benchmark/ground-truth validation.
    """

    print()
    print("Count validation:")
    print("-" * 70)

    if names:
        requested_names = set(names)

        selected = [
            entity
            for entity in entities
            if entity["entity"]
            in requested_names
        ]
    else:
        selected = list(
            entities
        )

    if not selected:
        print(
            "No matching canonical entities "
            "were found."
        )
        return

    total_checked = 0
    total_ok = 0
    total_warnings = 0

    for entity in selected:
        total_checked += 1

        name = entity["entity"]

        occurrences = entity.get(
            "occurrences",
            0,
        )

        spans = list(
            entity.get(
                "spans",
                [],
            )
        )

        unique_keys = {
            _span_key(span)
            for span in spans
        }

        duplicate_count = (
            len(spans)
            - len(unique_keys)
        )

        invalid_spans = [
            span
            for span in spans
            if not _validate_span_bounds(
                span,
                len(text),
            )
        ]

        overlapping_pairs = (
            _find_overlapping_pairs(
                spans
            )
        )

        count_matches = (
            occurrences
            == len(spans)
        )

        has_problem = (
            not count_matches
            or duplicate_count > 0
            or bool(invalid_spans)
            or bool(overlapping_pairs)
        )

        status = (
            "WARNING"
            if has_problem
            else "OK"
        )

        if has_problem:
            total_warnings += 1
        else:
            total_ok += 1

        print()
        print(
            f"{name}"
        )

        print(
            f"  status:       {status}"
        )

        print(
            f"  occurrences:  {occurrences}"
        )

        print(
            f"  stored spans: {len(spans)}"
        )

        print(
            f"  duplicates:   {duplicate_count}"
        )

        print(
            f"  invalid:      "
            f"{len(invalid_spans)}"
        )

        print(
            f"  overlaps:     "
            f"{len(overlapping_pairs)}"
        )

        # Show textual proof for explicitly
        # requested entities.
        if names and spans:
            print(
                "  source examples:"
            )

            _print_span_examples(
                text,
                spans,
            )

    print()
    print("-" * 70)

    print(
        f"Entities checked: {total_checked}"
    )

    print(
        f"OK:               {total_ok}"
    )

    print(
        f"Warnings:         {total_warnings}"
    )