import re
import unicodedata

from src.entity.lexicon import KNOWN_ENTITY_TYPES


# =========================================================
# Greek character ranges
# =========================================================

GREEK_CHARS = (
    "Α-ΩΆΈΉΊΌΎΏΪΫ"
    "α-ωάέήίόύώϊϋΐΰ"
)


# =========================================================
# Explicit confirmed typography fixes
# =========================================================
#
# These are forms observed in the manuscript that are
# typographical word-break artefacts, not real hyphenated
# words/entities.
#
# IMPORTANT:
# Do not add legitimate hyphenated entity names here.
# =========================================================

KNOWN_HYPHENATION_FIXES = {
    "Μα-τωμένα": "Ματωμένα",
    "Ξεχα-σμένου": "Ξεχασμένου",
    "Ξε-χασμένου": "Ξεχασμένου",
    "Ανατο-λικού": "Ανατολικού",
    "Ανατολι-κού": "Ανατολικού",
    "Βα-σιλέως": "Βασιλέως",
    "Αγήμα-τος": "Αγήματος",
    "Πρώ-της": "Πρώτης",
}


# =========================================================
# Regex patterns
# =========================================================

LINE_BREAK_HYPHEN_PATTERN = re.compile(
    rf"([{GREEK_CHARS}]+)"
    rf"[-‐-‒–—]"
    rf"\s*\n\s*"
    rf"([{GREEK_CHARS}]+)"
)


INTERNAL_HYPHEN_PATTERN = re.compile(
    rf"(?<!\w)"
    rf"([{GREEK_CHARS}]{{2,}})"
    rf"[-‐-‒–—]"
    rf"([{GREEK_CHARS}]{{2,}})"
    rf"(?!\w)"
)


MULTIPLE_SPACES_PATTERN = re.compile(
    r"[ \t]+"
)


MULTIPLE_NEWLINES_PATTERN = re.compile(
    r"\n{3,}"
)


# =========================================================
# Unicode cleanup
# =========================================================

def _normalize_unicode(
    text: str,
) -> str:
    """
    Normalize Unicode and remove invisible formatting
    characters that can interfere with entity matching.
    """

    text = unicodedata.normalize(
        "NFC",
        text,
    )

    text = (
        text
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00ad", "")
        .replace("\u2060", "")
    )

    return text


# =========================================================
# Explicit typography corrections
# =========================================================

def _apply_known_hyphenation_fixes(
    text: str,
) -> str:
    """
    Apply manuscript-specific corrections for confirmed
    word-break artefacts.
    """

    for broken, corrected in (
        KNOWN_HYPHENATION_FIXES.items()
    ):
        text = text.replace(
            broken,
            corrected,
        )

    return text


# =========================================================
# Line-break dehyphenation
# =========================================================

def _join_line_break_hyphenation(
    text: str,
) -> str:
    """
    Join Greek words split specifically across a line break.

    Example:

        Μα-
        τωμένα

    becomes:

        Ματωμένα

    This is safer than removing every internal hyphen.
    """

    previous_text = None

    # Repeat because one document can contain nested /
    # repeated extraction artefacts.
    while previous_text != text:
        previous_text = text

        text = LINE_BREAK_HYPHEN_PATTERN.sub(
            r"\1\2",
            text,
        )

    return text


# =========================================================
# Evidence-based internal dehyphenation
# =========================================================

def _known_unhyphenated_forms() -> set[str]:
    """
    Build unhyphenated variants of known entities.

    These are used only as evidence.

    We do NOT globally rewrite every known hyphenated
    entity.
    """

    forms: set[str] = set()

    for entity_name in KNOWN_ENTITY_TYPES:
        joined = re.sub(
            r"[-‐-‒–—]",
            "",
            entity_name,
        )

        if joined != entity_name:
            forms.add(joined)

    return forms


def _join_supported_internal_hyphens(
    text: str,
) -> str:
    """
    Remove an internal hyphen only when there is supporting
    evidence that the joined form exists elsewhere in the
    same document.

    This protects legitimate hyphenated names and places.
    """

    original_text = text

    replacements: dict[str, str] = {}

    for match in INTERNAL_HYPHEN_PATTERN.finditer(
        original_text
    ):
        hyphenated = match.group(0)

        joined = (
            match.group(1)
            + match.group(2)
        )

        joined_pattern = re.compile(
            rf"(?<!\w)"
            rf"{re.escape(joined)}"
            rf"(?!\w)"
        )

        if joined_pattern.search(original_text):
            replacements[hyphenated] = joined

    for old, new in replacements.items():
        text = text.replace(
            old,
            new,
        )

    return text


# =========================================================
# Whitespace cleanup
# =========================================================

def _normalize_whitespace(
    text: str,
) -> str:
    """
    Normalize whitespace without destroying paragraph
    boundaries.
    """

    lines: list[str] = []

    for line in text.splitlines():
        line = MULTIPLE_SPACES_PATTERN.sub(
            " ",
            line,
        ).strip()

        lines.append(line)

    text = "\n".join(lines)

    text = MULTIPLE_NEWLINES_PATTERN.sub(
        "\n\n",
        text,
    )

    return text.strip()


# =========================================================
# Public API
# =========================================================

def clean_extracted_text(
    text: str,
) -> str:
    """
    Clean extracted document text before NLP/entity
    detection.

    Processing order:

    1. Unicode normalization
    2. Confirmed manuscript-specific hyphenation fixes
    3. Line-break dehyphenation
    4. Conservative evidence-based internal dehyphenation
    5. Whitespace normalization

    The function intentionally does not lowercase the text
    and does not remove punctuation globally.
    """

    if not text:
        return ""

    text = _normalize_unicode(
        text
    )

    text = _apply_known_hyphenation_fixes(
        text
    )

    text = _join_line_break_hyphenation(
        text
    )

    text = _join_supported_internal_hyphens(
        text
    )

    text = _normalize_whitespace(
        text
    )

    return text