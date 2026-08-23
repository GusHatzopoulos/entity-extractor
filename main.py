import argparse

from pathlib import Path

from src.entity.detector import detect_combined_entities
from src.entity.context_classifier import reclassify_entities
from src.entity.entity_filter import filter_entities
from src.exporters.csv_exporter import export_entities_to_csv
from src.extractors.docx_extractor import extract_text_from_docx
from src.extractors.txt_extractor import extract_text_from_txt
from src.exporters.excel_exporter import export_entities_to_xlsx
from src.entity.final_selector import select_final_entities
from src.exporters.appendix_exporter import export_appendix_to_xlsx
from src.entity.name_detector import detect_name_candidates
from src.entity.recovery_merger import build_recovery_candidates
from src.text_cleaner import clean_extracted_text
from src.entity.canonicalizer import canonicalize_entities


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
    text = clean_extracted_text(text)

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

    canonical_entities = canonicalize_entities(
        classified_entities
    )

    final_entities = select_final_entities(
        canonical_entities
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

    print(
    f"Final persons/locations: "
    f"{len(final_entities):,}"
)


    csv_output_file = (
    Path("output")
    / f"{input_file.stem}_entities.csv"
    )

    xlsx_output_file = (
        Path("output")
        / f"{input_file.stem}_entities.xlsx"
    )

    appendix_output_path = (
        Path("output")
        / f"{input_file.stem}_appendix.xlsx"
    )

    print()
    print("Exporting results...")

    export_entities_to_csv(
        classified_entities,
        csv_output_file,
    )

    export_entities_to_xlsx(
        classified_entities,
        xlsx_output_file,
    )

    export_appendix_to_xlsx(
        canonical_entities,
        appendix_output_path,
    )

    print(
        f"Appendix XLSX exported to: "
        f"{appendix_output_path}"
    )

    print(f"CSV exported to: {csv_output_file}")
    print(f"XLSX exported to: {xlsx_output_file}")

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

    print()
    print("Detecting recovery name candidates...")

    name_candidates = detect_name_candidates(
        text,
        min_occurrences=1,
    )

    recovered_candidates = build_recovery_candidates(
        classified_entities,
        name_candidates,
    )

    print()
    print(
        f"New recovery candidates found: "
        f"{len(recovered_candidates):,}"
    )

    print()
    print("New recovery candidates:")
    print("-" * 70)

    for candidate in recovered_candidates[:100]:
        print(
            f"{candidate.name:<30} "
            f"count={candidate.occurrences:<5} "
            f"score={candidate.score:<4} "
            f"context={candidate.context_hits:<4} "
            f"title={candidate.title_hits:<3} "
            f"multi={candidate.multiword_hits:<3} "
            f"{candidate.reason}"
    )

    print(
        f"Recovery name candidates found: "
        f"{len(name_candidates):,}"
    )

    print()
    print("Top recovery candidates:")
    print("-" * 70)

    for candidate in name_candidates[:100]:
        print(
            f"{candidate.name:<30} "
            f"count={candidate.occurrences:<5} "
            f"score={candidate.score:<4} "
            f"context={candidate.context_hits:<4} "
            f"title={candidate.title_hits:<3} "
            f"multi={candidate.multiword_hits:<3}"
        )


if __name__ == "__main__":
    main()
