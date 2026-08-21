import argparse
from pathlib import Path

from src.entity.detector import detect_combined_entities
from src.entity.context_classifier import reclassify_entities
from src.entity.entity_filter import filter_entities
from src.exporters.csv_exporter import export_entities_to_csv
from src.extractors.docx_extractor import extract_text_from_docx
from src.extractors.txt_extractor import extract_text_from_txt


EXTRACTORS = {
    ".docx": extract_text_from_docx,
    ".txt": extract_text_from_txt,
}


def main() -> None:

    parser = argparse.ArgumentParser(
        description="Extract text and named entities from a document."
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        default=Path("data/input/HCprint.docx"),
        help="Path to a supported input file.",
    )

    args = parser.parse_args()
    input_file = args.input_file

    extractor = EXTRACTORS.get(input_file.suffix.lower())

    if extractor is None:
        parser.error(
            f"Unsupported file type: "
            f"{input_file.suffix or '(none)'}"
        )

    print()
    print(f"Input file: {input_file}")
    print()

    print("Reading document...")

    text = extractor(input_file)

    print(
        f"Text extraction completed: "
        f"{len(text):,} characters"
    )
    print()

    print("Detecting entities...")
    print()

    entities = detect_combined_entities(
        text,
        min_occurrences=1,
    )

    filtered_entities = filter_entities(
        entities,
        text,
    )

    classified_entities = reclassify_entities(
        filtered_entities
    )

    print()
    print(
        f"Entity detection completed: "
        f"{len(entities):,} raw entities"
    )

    print(
        f"Entities kept after filtering: "
        f"{len(classified_entities):,}"
    )


    output_file = (
        Path("output")
        / f"{input_file.stem}_entities.csv"
    )

    print()
    print("Exporting results...")

    export_entities_to_csv(
        classified_entities,
        output_file,
    )

    print(f"Results exported to: {output_file}")

    print()
    print("Preview:")
    print("-" * 70)
    print(text[:2000])

    print()
    print("Combined entities:")
    print("-" * 70)

    if entities:
        print(
            f"{'ENTITY':<30}"
            f"{'TYPE':<15}"
            f"{'SOURCE':<12}"
            f"{'COUNT':>8}"
        )

        print("-" * 70)

        for item in classified_entities[:100]:
            print(
                f"{str(item['entity']):<30}"
                f"{str(item['type']):<15}"
                f"{str(item['source']):<12}"
                f"{int(item['occurrences']):>8}"
            )
    else:
        print("No entities found.")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
