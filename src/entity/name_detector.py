import re
from dataclasses import dataclass

from src.entity.lexicon import (
    COMMON_NON_ENTITIES,
    KNOWN_ENTITY_TYPES,
    ROLE_WORDS,
    TITLE_WORDS,
)


PREFIX_WORDS = (
    COMMON_NON_ENTITIES
    | TITLE_WORDS
    | ROLE_WORDS
)


# ---------------------------------------------------------
# Greek name patterns
# ---------------------------------------------------------

GREEK_LETTERS = (
    r"Α-ΩΆΈΉΊΌΎΏΪΫ"
    r"α-ωάέήίόύώϊϋΐΰ"
)

GREEK_NAME_WORD = (
    rf"[Α-ΩΆΈΉΊΌΎΏΪΫ]"
    rf"[α-ωάέήίόύώϊϋΐΰ]+"
    rf"(?:[-–—]"
    rf"[{GREEK_LETTERS}]+)*"
)

SINGLE_NAME_PATTERN = re.compile(
    rf"(?<!\w)({GREEK_NAME_WORD})(?!\w)"
)

MULTI_NAME_PATTERN = re.compile(
    rf"(?<!\w)"
    rf"({GREEK_NAME_WORD}"
    rf"(?:\s+{GREEK_NAME_WORD}){{1,2}})"
    rf"(?!\w)"
)

TITLE_NAME_PATTERN = re.compile(
    rf"(?<!\w)"
    rf"(?:Σερ|Λαίδη|Λόρδος|Άρχοντας)"
    rf"\s+"
    rf"({GREEK_NAME_WORD}"
    rf"(?:\s+{GREEK_NAME_WORD})?)"
    rf"(?!\w)"
)


# ---------------------------------------------------------
# Candidate model
# ---------------------------------------------------------

@dataclass
class NameCandidate:
    name: str
    occurrences: int
    context_hits: int
    title_hits: int
    multiword_hits: int

    @property
    def score(self) -> int:
        return (
            self.context_hits * 3
            + self.title_hits * 6
            + self.multiword_hits * 3
        )


# ---------------------------------------------------------
# Normalization
# ---------------------------------------------------------

def normalize_name(name: str) -> str:
    """
    Normalize a recovery name candidate.

    Removes invisible formatting characters and
    collapses repeated whitespace.
    """

    name = (
        name
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00ad", "")
    )

    return " ".join(
        name.strip().split()
    )


# ---------------------------------------------------------
# Candidate validation
# ---------------------------------------------------------

def is_allowed_candidate(
    name: str,
) -> bool:
    """
    Decide whether a detected capitalized expression is
    allowed into the recovery candidate pool.

    Known entities always take priority over exclusions.
    """

    if name in KNOWN_ENTITY_TYPES:
        return True

    parts = name.split()

    if not parts:
        return False

    # Single-word candidate.
    if len(parts) == 1:
        return (
            name not in COMMON_NON_ENTITIES
            and name not in TITLE_WORDS
            and name not in ROLE_WORDS
        )

    # Reject expressions contaminated by an article,
    # title, role, or other common prefix.
    #
    # Examples:
    # Στην Έιλιν
    # Στο Ίστφορτ
    # Διοικητή Όνοξ
    # Σχόλαρχε Κουέντιν
    # Βασιλιά Ρέιμοντ Ράνον
    if parts[0] in PREFIX_WORDS:
        return False

    # Reject phrases made entirely from common words.
    if all(
        part in COMMON_NON_ENTITIES
        for part in parts
    ):
        return False

    return True


# ---------------------------------------------------------
# Occurrence counting
# ---------------------------------------------------------

def _count_exact_occurrences(
    text: str,
    name: str,
) -> int:
    """
    Count exact occurrences of a candidate in the text.
    """

    pattern = re.compile(
        rf"(?<!\w)"
        rf"{re.escape(name)}"
        rf"(?!\w)"
    )

    return len(
        pattern.findall(text)
    )


# ---------------------------------------------------------
# Context scoring
# ---------------------------------------------------------

def _count_context_hits(
    text: str,
    name: str,
) -> int:
    """
    Count contexts that provide evidence that a candidate
    may represent a person.

    Matching is case-sensitive intentionally.
    """

    escaped = re.escape(name)

    patterns = [
        # Article + candidate
        rf"\b(?:ο|η)\s+{escaped}\b",
        rf"\b(?:τον|την)\s+{escaped}\b",
        rf"\b(?:του|της)\s+{escaped}\b",

        # Preposition + personal article
        rf"\bμε\s+(?:τον|την)\s+{escaped}\b",

        # Candidate followed by speech/action verb
        (
            rf"\b(?:ο|η)\s+{escaped}\s+"
            rf"(?:είπε|ρώτησε|απάντησε|φώναξε|"
            rf"ψιθύρισε|μίλησε|κοίταξε|"
            rf"σηκώθηκε|γύρισε|προχώρησε|"
            rf"χαμογέλασε)\b"
        ),

        # Speech verb followed by candidate
        (
            rf"\b(?:είπε|ρώτησε|απάντησε|"
            rf"φώναξε|ψιθύρισε)\s+"
            rf"(?:ο|η)\s+{escaped}\b"
        ),
    ]

    hits = 0

    for pattern in patterns:
        hits += len(
            re.findall(
                pattern,
                text,
            )
        )

    return hits


def _count_title_hits(
    text: str,
    name: str,
) -> int:
    """
    Count explicit title + name occurrences.

    Examples:
    Σερ Ξάνθος
    Λαίδη Κύνθια
    """

    escaped = re.escape(name)

    pattern = (
        rf"\b"
        rf"(?:Σερ|Λαίδη|Λόρδος|Άρχοντας)"
        rf"\s+{escaped}\b"
    )

    return len(
        re.findall(
            pattern,
            text,
        )
    )


# ---------------------------------------------------------
# Fragment detection
# ---------------------------------------------------------

def _is_probable_fragment(
    name: str,
    all_names: set[str],
) -> bool:
    """
    Detect short single-token fragments of longer candidates.

    Examples:
    Έραρ  -> Έραρντ
    Αλβί  -> Αλβίνα
    Μόρτι -> Μόρτιζεν
    """

    parts = name.split()

    if len(parts) != 1:
        return False

    # Avoid aggressively removing legitimate longer names.
    if len(name) > 5:
        return False

    for other in all_names:
        if other == name:
            continue

        other_parts = other.split()

        if len(other_parts) != 1:
            continue

        if (
            len(other) > len(name)
            and other.startswith(name)
        ):
            return True

    return False


def _is_truncated_multiword(
    name: str,
    all_names: set[str],
) -> bool:
    """
    Detect multi-word candidates whose final component
    is a truncated version of another candidate.

    Examples:
    Έραρντ Φεράν -> Έραρντ Φεράνθεον
    Έθρικ Μπόλ   -> Έθρικ Μπόλβαρντ
    Τόρβιλ Θά    -> Τόρβιλ Θάεντ
    """

    parts = name.split()

    if len(parts) < 2:
        return False

    last_part = parts[-1]

    # Long final components are less likely to be truncations.
    if len(last_part) > 6:
        return False

    prefix_parts = parts[:-1]

    for other in all_names:
        if other == name:
            continue

        other_parts = other.split()

        if len(other_parts) != len(parts):
            continue

        if other_parts[:-1] != prefix_parts:
            continue

        other_last = other_parts[-1]

        if (
            len(other_last) > len(last_part)
            and other_last.startswith(last_part)
        ):
            return True

    return False


def _remove_fragments(
    candidate_names: set[str],
) -> set[str]:
    """
    Remove probable single-word and multi-word fragments
    after the complete candidate pool has been collected.
    """

    return {
        name
        for name in candidate_names
        if (
            not _is_probable_fragment(
                name,
                candidate_names,
            )
            and not _is_truncated_multiword(
                name,
                candidate_names,
            )
        )
    }


# ---------------------------------------------------------
# Main recovery detector
# ---------------------------------------------------------

def detect_name_candidates(
    text: str,
    min_occurrences: int = 1,
) -> list[NameCandidate]:
    """
    High-recall recovery detector for character names missed
    by the main NER/POS pipeline.

    The detector intentionally generates possible candidates
    rather than automatically promoting them to PERSON.
    """

    # Remove invisible formatting characters from the text
    # before regex matching.
    clean_text = (
        text
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00ad", "")
    )

    candidate_names: set[str] = set()

    # -----------------------------------------------------
    # 1. Single capitalized words
    # -----------------------------------------------------

    for match in SINGLE_NAME_PATTERN.finditer(
        clean_text
    ):
        name = normalize_name(
            match.group(1)
        )

        if is_allowed_candidate(name):
            candidate_names.add(name)

    # -----------------------------------------------------
    # 2. Two- and three-word capitalized sequences
    # -----------------------------------------------------

    for match in MULTI_NAME_PATTERN.finditer(
        clean_text
    ):
        name = normalize_name(
            match.group(1)
        )

        if is_allowed_candidate(name):
            candidate_names.add(name)

    # -----------------------------------------------------
    # 3. Explicit title + name combinations
    # -----------------------------------------------------

    for match in TITLE_NAME_PATTERN.finditer(
        clean_text
    ):
        name = normalize_name(
            match.group(1)
        )

        if is_allowed_candidate(name):
            candidate_names.add(name)

    # -----------------------------------------------------
    # 4. Remove truncated / fragmented candidates
    # -----------------------------------------------------

    candidate_names = _remove_fragments(
        candidate_names
    )

    # -----------------------------------------------------
    # 5. Build scored candidates
    # -----------------------------------------------------

    candidates: list[NameCandidate] = []

    for name in candidate_names:
        occurrences = _count_exact_occurrences(
            clean_text,
            name,
        )

        if occurrences < min_occurrences:
            continue

        context_hits = _count_context_hits(
            clean_text,
            name,
        )

        title_hits = _count_title_hits(
            clean_text,
            name,
        )

        word_count = len(
            name.split()
        )

        multiword_hits = (
            occurrences
            if word_count >= 2
            else 0
        )

        candidates.append(
            NameCandidate(
                name=name,
                occurrences=occurrences,
                context_hits=context_hits,
                title_hits=title_hits,
                multiword_hits=multiword_hits,
            )
        )

    candidates.sort(
        key=lambda candidate: (
            -candidate.score,
            -candidate.occurrences,
            candidate.name,
        )
    )

    return candidates