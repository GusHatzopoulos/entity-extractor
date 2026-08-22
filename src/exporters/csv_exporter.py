import csv
from collections.abc import Sequence
from pathlib import Path

from src.entity.types import EntityRecord


def export_entities_to_csv(
    entities: Sequence[EntityRecord],
    output_path: str | Path,
) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "entity",
        "original_type",
        "type",
        "source",
        "occurrences",
        "confidence",
        "person_score",
        "location_score",
        "classification_reason",
        "keep",
    ]

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for entity in entities:
            writer.writerow(
                {
                    "entity": entity.get("entity", ""),
                    "original_type": entity.get(
                        "original_type",
                        "",
                    ),
                    "type": entity.get("type", ""),
                    "source": entity.get("source", ""),
                    "occurrences": entity.get(
                        "occurrences",
                        0,
                    ),
                    "confidence": entity.get(
                        "confidence",
                        "",
                    ),
                    "person_score": entity.get(
                        "person_score",
                        0,
                    ),
                    "location_score": entity.get(
                        "location_score",
                        0,
                    ),
                    "classification_reason": entity.get(
                        "classification_reason",
                        "",
                    ),
                    "keep": entity.get("keep", ""),
                }
            )