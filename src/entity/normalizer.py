import re
import unicodedata


# =========================================================
# Prefixes that may be attached to an entity span
# =========================================================

TITLE_ROLE_PREFIXES = {
    "Σερ", "Σερς",
    "Λαίδη", "Λαίδης", "Λαίδες",
    "Λόρδος", "Λόρδου",

    "Άρχοντας", "Άρχοντα", "Άρχοντά", "Άρχοντες", "Άρχοντές",

    "Βαρόνος", "Βαρόνε", "Βαρόνου",
    "Βαρόνη", "Βαρόνης",

    "Κόμης", "Κόμη", "Κόμισσα",
    "Δούκας", "Δούκα", "Δούκισσα",

    "Σχόλαρχος", "Σχόλαρχε", "Σχολάρχου",
    "Διάκονος", "Διάκονε", "Διακόνου",

    "Μισθοφόρος", "Μισθοφόρε", "Μισθοφόρου",
    "Ιππότης", "Ιππότη", "Ιππότες",

    "Διοικητής", "Διοικητή", "Διοικητού",
    "Στρατηγός", "Στρατηγέ", "Στρατηγού",
    "Λοχαγός", "Λοχαγέ", "Λοχαγού",
    "Καπετάνιος", "Καπετάνιε", "Καπετάνιου",

    "Βασιλιάς", "Βασιλιά", "Βασιλέως",
    "Βασίλισσα", "Βασίλισσας",

    "Πρίγκιπας", "Πρίγκιπα", "Πρίγκιπος",
    "Πριγκίπισσα", "Πριγκίπισσας",
}


ARTICLE_PREPOSITION_PREFIXES = {
    "Ο",
    "Η",
    "Οι",

    "Τον",
    "Την",
    "Τη",

    "Του",
    "Της",
    "Των",

    "Στο",
    "Στη",
    "Στην",
    "Στον",

    "Στους",
    "Στις",
    "Στα",

    "Από",
    "Προς",
    "Με",
}


# =========================================================
# Mixed Greek / Latin confusables
# =========================================================

# Only visually confusable Latin characters are included.
#
# IMPORTANT:
# They are converted only when they occur inside a token
# that already contains Greek characters.
#
# Therefore:
#
#     Oικτίρμονος -> Οικτίρμονος
#
# but a purely Latin word/name remains unchanged.

LATIN_TO_GREEK_CONFUSABLES = {
    "A": "Α",
    "B": "Β",
    "E": "Ε",
    "H": "Η",
    "I": "Ι",
    "K": "Κ",
    "M": "Μ",
    "N": "Ν",
    "O": "Ο",
    "P": "Ρ",
    "T": "Τ",
    "X": "Χ",
    "Y": "Υ",
    "Z": "Ζ",

    "a": "α",
    "e": "ε",
    "i": "ι",
    "o": "ο",
    "p": "ρ",
    "x": "χ",
    "y": "υ",
}


GREEK_CHARACTER_RE = re.compile(
    r"[\u0370-\u03FF\u1F00-\u1FFF]"
)

LATIN_CHARACTER_RE = re.compile(
    r"[A-Za-z]"
)


# =========================================================
# Low-level cleanup
# =========================================================

def _normalize_unicode(
    name: str,
) -> str:
    """
    Apply Unicode NFC normalization and remove invisible
    formatting characters.
    """

    name = unicodedata.normalize(
        "NFC",
        name,
    )

    name = (
        name
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00ad", "")
        .replace("\u2060", "")
    )

    return name


def _normalize_whitespace(
    name: str,
) -> str:
    """
    Collapse repeated whitespace.
    """

    return re.sub(
        r"\s+",
        " ",
        name,
    ).strip()


def _strip_surrounding_punctuation(
    name: str,
) -> str:
    """
    Remove punctuation around an entity without altering
    punctuation inside the entity.
    """

    return name.strip(
        ".,;:!?«»\"'()[]{}—–-"
    ).strip()


# =========================================================
# Mixed-script normalization
# =========================================================

def _normalize_mixed_script_token(
    token: str,
) -> str:
    """
    Repair visually confusable Latin characters when they
    occur inside an otherwise Greek token.

    Examples:

        Oικτίρμονος
        -> Οικτίρμονος

        Ρίκαρνt
        -> Ρίκαρντ

    Purely Latin tokens are intentionally preserved.
    """

    has_greek = bool(
        GREEK_CHARACTER_RE.search(token)
    )

    has_latin = bool(
        LATIN_CHARACTER_RE.search(token)
    )

    if not (
        has_greek
        and has_latin
    ):
        return token

    return "".join(
        LATIN_TO_GREEK_CONFUSABLES.get(
            char,
            char,
        )
        for char in token
    )


def _normalize_mixed_scripts(
    name: str,
) -> str:
    """
    Repair mixed Greek/Latin characters token-by-token.

    Pure Latin tokens are not modified.
    """

    parts = name.split()

    normalized_parts = [
        _normalize_mixed_script_token(part)
        for part in parts
    ]

    return " ".join(
        normalized_parts
    )


# =========================================================
# Prefix stripping
# =========================================================

def _strip_title_role_prefix(
    name: str,
) -> str:
    """
    Remove a title/role only when it appears before at least
    one additional token.

    Examples:

        Σερ Τόρβιλ
        -> Τόρβιλ

        Λαίδη Άντρια
        -> Άντρια

        Διάκονε Γιόρεν
        -> Γιόρεν

    A standalone word is never removed here.

    Example:

        Γεάρχης
        -> Γεάρχης
    """

    parts = name.split()

    if len(parts) < 2:
        return name

    first = parts[0]

    if first in TITLE_ROLE_PREFIXES:
        return " ".join(
            parts[1:]
        ).strip()

    return name


def _strip_article_preposition_prefix(
    name: str,
) -> str:
    """
    Remove a leading article/preposition when it has been
    included inside the extracted entity span.

    Examples:

        Στο Βίλριβ
        -> Βίλριβ

        Τον Ντέρβεν
        -> Ντέρβεν

        Στην Ετέρια
        -> Ετέρια
    """

    parts = name.split()

    if len(parts) < 2:
        return name

    first = parts[0]

    if first in ARTICLE_PREPOSITION_PREFIXES:
        return " ".join(
            parts[1:]
        ).strip()

    return name


def _strip_known_prefixes(
    name: str,
) -> str:
    """
    Repeatedly remove recognized leading articles,
    prepositions, titles and roles.

    Examples:

        Ο Σερ Τόρβιλ
        -> Τόρβιλ

        Στον Βαρόνο Μπέρινον
        -> Μπέρινον
    """

    previous_name = None

    while (
        previous_name != name
        and name
    ):
        previous_name = name

        name = _strip_article_preposition_prefix(
            name
        )

        name = _strip_title_role_prefix(
            name
        )

        name = _normalize_whitespace(
            name
        )

    return name


# =========================================================
# Public API
# =========================================================

def normalize_entity_name(
    name: str,
) -> str:
    """
    Normalize an extracted entity name.

    Processing:

    1. Unicode NFC normalization
    2. Remove invisible Unicode characters
    3. Collapse repeated whitespace
    4. Remove surrounding punctuation
    5. Repair mixed Greek/Latin confusable characters
    6. Remove entity-span articles/prepositions
    7. Remove entity-span titles/roles
    8. Final whitespace/punctuation cleanup

    The function intentionally:
    - preserves Greek accents
    - preserves internal hyphens
    - does not lowercase text
    - preserves purely Latin names
    - does not alter standalone legitimate names
    """

    if not name:
        return ""

    name = _normalize_unicode(
        name
    )

    name = _normalize_whitespace(
        name
    )

    name = _strip_surrounding_punctuation(
        name
    )

    name = _normalize_mixed_scripts(
        name
    )

    name = _strip_known_prefixes(
        name
    )

    name = _normalize_whitespace(
        name
    )

    name = _strip_surrounding_punctuation(
        name
    )

    return name.strip()