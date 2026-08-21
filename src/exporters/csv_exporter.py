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

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "entity",
                "type",
                "source",
                "occurrences",
                "confidence",
                "context_score",
                "classification_reason",
                "keep",
            ],
        )

        writer.writeheader()

        for entity in entities:
            writer.writerow(
                {
                    "entity": entity.get("entity", ""),
                    "type": entity.get("type", ""),
                    "source": entity.get("source", ""),
                    "occurrences": entity.get("occurrences", 0),
                    "confidence": entity.get("confidence", ""),
                    "context_score": entity.get("context_score", 0),
                    "classification_reason": entity.get(
                        "classification_reason",
                        "",
                    ),
                    "keep": entity.get("keep", ""),
                }
            )