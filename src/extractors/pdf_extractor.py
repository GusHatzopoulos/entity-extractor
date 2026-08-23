from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(
    file_path: str | Path,
) -> str:
    """
    Extract text from a text-based PDF document.

    This extractor does not perform OCR.
    Scanned/image-only PDFs require a separate OCR pipeline.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"PDF path is not a file: {path}"
        )

    reader = PdfReader(path)

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ValueError(
                "The PDF is encrypted and cannot be read."
            ) from exc

    pages_text: list[str] = []

    total_pages = len(reader.pages)

    if total_pages == 0:
        raise ValueError(
            "The PDF contains no pages."
        )

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:
            raise RuntimeError(
                f"Failed to extract text from PDF page "
                f"{page_number}/{total_pages}."
            ) from exc

        page_text = page_text.strip()

        if page_text:
            pages_text.append(page_text)

    text = "\n\n".join(pages_text).strip()

    if not text:
        raise ValueError(
            "No extractable text was found in this PDF. "
            "The document may be scanned/image-only and "
            "may require OCR."
        )

    return text