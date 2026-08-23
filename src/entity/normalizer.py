import re
import unicodedata


def normalize_entity_name(name: str) -> str:
    """
    Normalize an extracted entity name without destroying
    Greek accents or changing the actual spelling.

    The function:
    - applies Unicode NFC normalization
    - removes invisible Unicode characters
    - removes soft hyphens
    - collapses repeated whitespace
    - removes surrounding punctuation
    """

    name = unicodedata.normalize("NFC", name)

    # Remove invisible / formatting Unicode characters.
    name = (
        name
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00ad", "")
    )

    # Collapse repeated whitespace.
    name = re.sub(r"\s+", " ", name).strip()

    # Remove surrounding punctuation.
    name = name.strip(
        ".,;:!?«»\"'()[]{}—–-"
    )

    return name.strip()