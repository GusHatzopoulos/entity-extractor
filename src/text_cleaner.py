import re
import unicodedata

from src.entity.lexicon import KNOWN_ENTITY_TYPES


GREEK_CHARS = (
    "Α-ΩΆΈΉΊΌΎΏΪΫ"
    "α-ωάέήίόύώϊϋΐΰ"
)

HYPHENATED_GREEK_WORD_PATTERN = re.compile(
    rf"(?<!\w)"
    rf"([{GREEK_CHARS}]{{2,}})"
    rf"[-‐-‒–—]"
    rf"([{GREEK_CHARS}]{{2,}})"
    rf"(?!\w)"
)

LINE_BREAK_HYPHEN_PATTERN = re.compile(
    rf"([{GREEK_CHARS}]+)"
    rf"[-‐-‒–—]"
    rf"\s*\n\s*"
    rf"([{GREEK_CHARS}]+)"
)


def _normalize_unicode(text: str) -> str:
    """
    Normalize Unicode and remove invisible formatting characters.
    """

    text = unicodedata.normalize(
        "NFC",
        text,
    )

    return (
        text
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00ad", "")
    )


def _join_line_break_hyphenation(
    text: str,
) -> str:
    """
    Join words that were hyphenated because of a line break.

    Example:
        Φε-
        ράνθεον

    becomes:
        Φεράνθεον
    """

    return LINE_BREAK_HYPHEN_PATTERN.sub(
        r"\1\2",
        text,
    )


def _known_unhyphenated_names() -> set[str]:
    """
    Build normalized forms of known entities.

    Example:
        Αζάκου-μα -> Αζάκουμα
    """

    normalized: set[str] = set()

    for name in KNOWN_ENTITY_TYPES:
        normalized.add(
            re.sub(
                r"[-‐-‒–—]",
                "",
                name,
            )
        )

    return normalized


def _join_supported_internal_hyphens(
    text: str,
) -> str:
    """
    Remove an internal hyphen only when there is evidence that
    the joined form is the real word/name.

    Evidence:
    - the unhyphenated form also appears elsewhere in the text, or
    - the unhyphenated form is a known entity.

    This avoids blindly destroying legitimate hyphenated words.
    """

    known_names = _known_unhyphenated_names()

    # Snapshot before replacements so evidence is stable.
    original_text = text

    replacements: dict[str, str] = {}

    for match in HYPHENATED_GREEK_WORD_PATTERN.finditer(
        original_text
    ):
        hyphenated = match.group(0)

        joined = (
            match.group(1)
            + match.group(2)
        )

        plain_pattern = re.compile(
            rf"(?<!\w)"
            rf"{re.escape(joined)}"
            rf"(?!\w)"
        )

        exists_without_hyphen = bool(
            plain_pattern.search(original_text)
        )

        is_known_entity = (
            joined in known_names
        )

        if (
            exists_without_hyphen
            or is_known_entity
        ):
            replacements[hyphenated] = joined

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    return text


def clean_extracted_text(
    text: str,
) -> str:
    """
    Clean extracted document text before entity detection.

    The cleaning is intentionally conservative:
    - Unicode normalization
    - invisible-character removal
    - soft-hyphen removal
    - line-break dehyphenation
    - evidence-based internal dehyphenation

    It does not lowercase or alter normal punctuation.
    """

    text = _normalize_unicode(text)

    text = _join_line_break_hyphenation(
        text
    )

    text = _join_supported_internal_hyphens(
        text
    )

    return text