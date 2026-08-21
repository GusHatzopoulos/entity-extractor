import re
import unicodedata


def normalize_entity_name(name: str) -> str:
    """
    Normalize an extracted entity name without destroying
    Greek accents or changing the actual spelling.

    The function:
    - removes leading/trailing whitespace
    - collapses repeated whitespace
    - applies Unicode NFC normalization
    - removes surrounding punctuation
    """

    name = unicodedata.normalize("NFC", name)

    name = re.sub(r"\s+", " ", name).strip()

    name = name.strip(
        ".,;:!?«»\"'()[]{}—–-"
    )

    return name.strip()