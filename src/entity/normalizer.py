import re
import unicodedata


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
    "Ο", "Η", "Οι",
    "Τον", "Την", "Τη",
    "Του", "Της", "Των",
    "Στο", "Στη", "Στην", "Στον",
    "Στους", "Στις", "Στα",
    "Από", "Προς", "Με",
}

TITLE_ROLE_PREFIX_KEYS = {
    value.casefold()
    for value in TITLE_ROLE_PREFIXES
}

ARTICLE_PREPOSITION_PREFIX_KEYS = {
    value.casefold()
    for value in ARTICLE_PREPOSITION_PREFIXES
}


LATIN_TO_GREEK_CONFUSABLES = {
    "A": "Α", "B": "Β", "E": "Ε", "H": "Η", "I": "Ι",
    "K": "Κ", "M": "Μ", "N": "Ν", "O": "Ο", "P": "Ρ",
    "T": "Τ", "X": "Χ", "Y": "Υ", "Z": "Ζ",
    "a": "α", "e": "ε", "i": "ι", "o": "ο",
    "p": "ρ", "x": "χ", "y": "υ",
}

GREEK_CHARACTER_RE = re.compile(
    r"[\u0370-\u03FF\u1F00-\u1FFF]"
)

LATIN_CHARACTER_RE = re.compile(
    r"[A-Za-z]"
)


def _normalize_unicode(
    name: str,
) -> str:
    name = unicodedata.normalize(
        "NFC",
        name,
    )

    return (
        name
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00ad", "")
        .replace("\u2060", "")
    )


def _normalize_whitespace(
    name: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        name,
    ).strip()


def _strip_surrounding_punctuation(
    name: str,
) -> str:
    return name.strip(
        ".,;:!?«»\"'()[]{}—–-"
    ).strip()


def _normalize_mixed_script_token(
    token: str,
) -> str:
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
    return " ".join(
        _normalize_mixed_script_token(part)
        for part in name.split()
    )


def _strip_title_role_prefix(
    name: str,
) -> str:
    """
    Strip title/role prefixes case-insensitively.

    Examples:
        Σερ Τόρβιλ -> Τόρβιλ
        σερ Χέρολντ -> Χέρολντ
        Άρχοντας Λίαμ -> Λίαμ
        άρχοντας Λίαμ -> Λίαμ
    """

    parts = name.split()

    if len(parts) < 2:
        return name

    if (
        parts[0].casefold()
        in TITLE_ROLE_PREFIX_KEYS
    ):
        return " ".join(
            parts[1:]
        ).strip()

    return name


def _strip_article_preposition_prefix(
    name: str,
) -> str:
    """
    Strip leading articles/prepositions case-insensitively.
    """

    parts = name.split()

    if len(parts) < 2:
        return name

    if (
        parts[0].casefold()
        in ARTICLE_PREPOSITION_PREFIX_KEYS
    ):
        return " ".join(
            parts[1:]
        ).strip()

    return name


def _strip_known_prefixes(
    name: str,
) -> str:
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


def normalize_entity_name(
    name: str,
) -> str:
    """
    Normalize an extracted entity name without destructive
    linguistic transformations.

    This function:
    - normalizes Unicode
    - removes invisible formatting characters
    - repairs mixed Greek/Latin confusables
    - strips articles/prepositions/titles/roles
      case-insensitively
    - preserves accents
    - preserves internal hyphens
    - preserves original entity casing
    """

    if not name:
        return ""

    name = _normalize_unicode(name)
    name = _normalize_whitespace(name)
    name = _strip_surrounding_punctuation(name)
    name = _normalize_mixed_scripts(name)
    name = _strip_known_prefixes(name)
    name = _normalize_whitespace(name)
    name = _strip_surrounding_punctuation(name)

    return name.strip()
