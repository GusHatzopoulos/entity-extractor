from pathlib import Path


def extract_text_from_txt(file_path: str | Path) -> str:
    """
    Extract text from a UTF-8 plain text file.

    Args:
        file_path: Path to the TXT file.

    Returns:
        The extracted text as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the provided file is not a TXT file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() != ".txt":
        raise ValueError(f"Expected a .txt file, received: {path.suffix}")

    return path.read_text(encoding="utf-8")