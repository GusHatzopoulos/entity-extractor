from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

from src.entity.types import EntityRecord


def _write_appendix_sheet(
    worksheet: Worksheet,
    entities: list[EntityRecord],
) -> None:
    worksheet.append(
        [
            "Name",
            "Occurrences",
        ]
    )

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for entity in entities:
        worksheet.append(
            [
                entity.get("entity", ""),
                entity.get("occurrences", 0),
            ]
        )

    worksheet.column_dimensions["A"].width = 35
    worksheet.column_dimensions["B"].width = 15

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions


def export_appendix_to_xlsx(
    entities: list[EntityRecord],
    output_path: str | Path,
) -> None:
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    persons = sorted(
        (
            entity
            for entity in entities
            if entity.get("type") == "PERSON"
        ),
        key=lambda entity: (
            -entity.get("occurrences", 0),
            entity.get("entity", ""),
        ),
    )

    locations = sorted(
        (
            entity
            for entity in entities
            if entity.get("type") in {"LOCATION", "GPE"}
        ),
        key=lambda entity: (
            -entity.get("occurrences", 0),
            entity.get("entity", ""),
        ),
    )

    workbook = Workbook()

    characters_sheet = workbook.active

    if characters_sheet is None:
        raise RuntimeError(
            "Could not create the Characters worksheet."
        )

    characters_sheet.title = "Characters"

    locations_sheet = workbook.create_sheet(
        title="Locations"
    )

    _write_appendix_sheet(
        characters_sheet,
        persons,
    )

    _write_appendix_sheet(
        locations_sheet,
        locations,
    )

    workbook.save(path)