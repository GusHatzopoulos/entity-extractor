import argparse
from pathlib import Path
from time import perf_counter

from src.entity.canonicalizer import canonicalize_entities
from src.entity.context_classifier import reclassify_entities
from src.entity.detector import detect_combined_entities
from src.entity.entity_filter import filter_entities
from src.entity.final_selector import select_final_entities
from src.entity.name_detector import detect_name_candidates
from src.entity.recovery_merger import build_recovery_candidates

from src.entity.count_validator import validate_canonical_counts

from src.exporters.appendix_exporter import export_appendix_to_xlsx
from src.exporters.csv_exporter import export_entities_to_csv
from src.exporters.excel_exporter import export_entities_to_xlsx

from src.extractors.docx_extractor import extract_text_from_docx
from src.extractors.pdf_extractor import extract_text_from_pdf
from src.extractors.txt_extractor import extract_text_from_txt

from src.text_cleaner import clean_extracted_text


# =========================================================
# Supported input formats
# =========================================================

EXTRACTORS = {
    ".docx": extract_text_from_docx,
    ".pdf": extract_text_from_pdf,
    ".txt": extract_text_from_txt,
}


# =========================================================
# Main
# =========================================================

def main() -> None:
    total_start = perf_counter()

    # -----------------------------------------------------
    # Arguments
    # -----------------------------------------------------

    parser = argparse.ArgumentParser(
        description=(
            "Extract text and named entities "
            "from a supported document."
        )
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        default=Path("data/input/HCprint.docx"),
        help="Path to a supported input file.",
    )

    parser.add_argument(
        "--validate-counts",
        action="store_true",
        help=(
            "Validate canonical occurrence counts "
            "against stored text spans."
        ),
    )

    parser.add_argument(
        "--validate-name",
        action="append",
        default=[],
        help=(
            "Canonical entity name to inspect during "
            "count validation. Can be supplied more "
            "than once."
        ),
    )

    args = parser.parse_args()
    input_file = args.input_file

    extractor = EXTRACTORS.get(
        input_file.suffix.lower()
    )

    if extractor is None:
        parser.error(
            f"Unsupported file type: "
            f"{input_file.suffix or '(none)'}"
        )

    # -----------------------------------------------------
    # Input
    # -----------------------------------------------------

    print()
    print(f"Input file: {input_file}")
    print()

    # =====================================================
    # 1. Text extraction / cleanup
    # =====================================================

    extraction_start = perf_counter()

    print("Reading document...")

    text = extractor(input_file)

    text = clean_extracted_text(
        text
    )

    extraction_time = (
        perf_counter()
        - extraction_start
    )

    print(
        f"Text extraction completed: "
        f"{len(text):,} characters"
    )

    # =====================================================
    # 2. Entity detection / NLP
    # =====================================================

    print()
    print("Detecting entities...")
    print()

    detection_start = perf_counter()

    entities = detect_combined_entities(
        text,
        min_occurrences=1,
    )

    detection_time = (
        perf_counter()
        - detection_start
    )

    # =====================================================
    # 3. Filtering / classification / canonicalization
    # =====================================================

    classification_start = perf_counter()

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

    if args.validate_counts:
        validate_canonical_counts(
            text,
            final_entities,
            names=(
                args.validate_name
                if args.validate_name
                else None
            ),
        )

    classification_time = (
        perf_counter()
        - classification_start
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

    # =====================================================
    # 4. Output paths
    # =====================================================

    output_directory = Path("output")

    csv_output_file = (
        output_directory
        / f"{input_file.stem}_entities.csv"
    )

    xlsx_output_file = (
        output_directory
        / f"{input_file.stem}_entities.xlsx"
    )

    appendix_output_path = (
        output_directory
        / f"{input_file.stem}_appendix.xlsx"
    )

    # =====================================================
    # 5. Export
    # =====================================================

    export_start = perf_counter()

    print()
    print("Exporting results...")

    # Diagnostic/raw classified exports
    export_entities_to_csv(
        classified_entities,
        csv_output_file,
    )

    export_entities_to_xlsx(
        classified_entities,
        xlsx_output_file,
    )

    # Canonicalized appendix
    export_appendix_to_xlsx(
        final_entities,
        appendix_output_path,
    )

    export_time = (
        perf_counter()
        - export_start
    )

    print(
        f"Appendix XLSX exported to: "
        f"{appendix_output_path}"
    )

    print(
        f"CSV exported to: "
        f"{csv_output_file}"
    )

    print(
        f"XLSX exported to: "
        f"{xlsx_output_file}"
    )

    # =====================================================
    # 6. Diagnostic preview
    # =====================================================

    print()
    print("Preview:")
    print("-" * 70)
    print("Preview omitted during processing.")

    print()
    print("Combined entities:")
    print("-" * 70)

    if classified_entities:
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

    # =====================================================
    # 7. Recovery detection
    # =====================================================

    print()
    print(
        "Detecting recovery name candidates..."
    )

    recovery_start = perf_counter()

    existing_entity_names = {
        entity["entity"]
        for entity in classified_entities
    }

    name_candidates = detect_name_candidates(
        text,
        min_occurrences=1,
        excluded_names=existing_entity_names,
    )

    recovered_candidates = (
        build_recovery_candidates(
            classified_entities,
            name_candidates,
        )
    )

    recovery_time = (
        perf_counter()
        - recovery_start
    )

    # -----------------------------------------------------
    # New recovery candidates
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # All recovery candidates
    # -----------------------------------------------------

    print()
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

    # =====================================================
    # 8. Performance report
    # =====================================================

    total_time = (
        perf_counter()
        - total_start
    )

    print()
    print("Performance:")
    print("-" * 70)

    print(
        f"Text extraction:       "
        f"{extraction_time:8.2f} s"
    )

    print(
        f"Detection / NLP:       "
        f"{detection_time:8.2f} s"
    )

    print(
        f"Filter / classify:     "
        f"{classification_time:8.2f} s"
    )

    print(
        f"Exports:               "
        f"{export_time:8.2f} s"
    )

    print(
        f"Recovery detection:    "
        f"{recovery_time:8.2f} s"
    )

    print("-" * 70)

    print(
        f"Total runtime:         "
        f"{total_time:8.2f} s"
    )

    print()
    print("Done.")


# =========================================================
# Entry point
# =========================================================

if __name__ == "__main__":
    main()