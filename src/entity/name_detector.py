import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

from src.entity.lexicon import (
    COMMON_NON_ENTITIES,
    KNOWN_ENTITY_TYPES,
    ROLE_WORDS,
    TITLE_WORDS,
)


# =========================================================
# Prefixes / descriptive aliases
# =========================================================

PREFIX_WORDS = (
    COMMON_NON_ENTITIES
    | TITLE_WORDS
    | ROLE_WORDS
)


EPITHET_ALIASES = {
    "Μέγα Βάλλεν": "Βάλλεν",
    "Ξεχασμένος Ήρωας Βάλλεν": "Βάλλεν",
    "Ξεχασμένου Ήρωα Βάλλεν": "Βάλλεν",
}


# =========================================================
# Greek-token patterns
# =========================================================

GREEK_LETTERS = (
    r"Α-ΩΆΈΉΊΌΎΏΪΫ"
    r"α-ωάέήίόύώϊϋΐΰ"
)

GREEK_NAME_WORD = (
    rf"[Α-ΩΆΈΉΊΌΎΏΪΫ]"
    rf"[α-ωάέήίόύώϊϋΐΰ]+"
    rf"(?:[-–—][{GREEK_LETTERS}]+)*"
)

CAPITALIZED_WORD_PATTERN = re.compile(
    rf"(?<!\w)"
    rf"({GREEK_NAME_WORD})"
    rf"(?!\w)"
)


# =========================================================
# Candidate model
# =========================================================

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


@dataclass
class CandidateStats:
    occurrences: int = 0
    context_hits: int = 0
    title_hits: int = 0
    multiword_hits: int = 0


# =========================================================
# Normalization
# =========================================================

def normalize_name(
    name: str,
) -> str:
    name = unicodedata.normalize(
        "NFC",
        name,
    )

    name = (
        name
        .replace("\u200b", "")
        .replace("\ufeff", "")
        .replace("\u00ad", "")
    )

    return " ".join(
        name.strip().split()
    )


def clean_input_text(
    text: str,
) -> str:
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


# =========================================================
# Candidate validation
# =========================================================

def is_allowed_candidate(
    name: str,
) -> bool:
    if not name:
        return False

    if name in KNOWN_ENTITY_TYPES:
        return True

    if name in COMMON_NON_ENTITIES:
        return False

    parts = name.split()

    if not parts:
        return False

    if len(parts) == 1:
        return (
            name not in TITLE_WORDS
            and name not in ROLE_WORDS
        )

    # Reject:
    # Στην Έιλιν
    # Διοικητή Όνοξ
    # Βασιλιά Ρέιμοντ Ρανόν
    if parts[0] in PREFIX_WORDS:
        return False

    if all(
        part in COMMON_NON_ENTITIES
        for part in parts
    ):
        return False

    return True


# =========================================================
# Fragment detection
# =========================================================

def _is_probable_fragment(
    name: str,
    all_names: set[str],
) -> bool:
    parts = name.split()

    if len(parts) != 1:
        return False

    if len(name) > 5:
        return False

    for other in all_names:
        if other == name:
            continue

        if " " in other:
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
    parts = name.split()

    if len(parts) < 2:
        return False

    last_part = parts[-1]

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
    names: set[str],
) -> set[str]:
    return {
        name
        for name in names
        if (
            not _is_probable_fragment(
                name,
                names,
            )
            and not _is_truncated_multiword(
                name,
                names,
            )
        )
    }


# =========================================================
# Local evidence
# =========================================================

PERSON_ARTICLE_PATTERN = re.compile(
    r"(?:"
    r"\bο\s+$|"
    r"\bη\s+$|"
    r"\bτον\s+$|"
    r"\bτην\s+$|"
    r"\bτου\s+$|"
    r"\bτης\s+$|"
    r"\bμε\s+τον\s+$|"
    r"\bμε\s+την\s+$"
    r")"
)


TITLE_PREFIX_PATTERN = re.compile(
    r"(?:"
    r"\bΣερ\s+$|"
    r"\bΛαίδη\s+$|"
    r"\bΛόρδος\s+$|"
    r"\bΆρχοντας\s+$"
    r")"
)


ACTION_AFTER_PATTERN = re.compile(
    r"^\s+(?:"
    r"είπε|"
    r"ρώτησε|"
    r"απάντησε|"
    r"φώναξε|"
    r"ψιθύρισε|"
    r"μίλησε|"
    r"κοίταξε|"
    r"σηκώθηκε|"
    r"γύρισε|"
    r"προχώρησε|"
    r"χαμογέλασε"
    r")\b"
)


def _local_evidence(
    text: str,
    start: int,
    end: int,
) -> tuple[int, int]:
    """
    Calculate person-context and title evidence from a
    small local window instead of rescanning the full book.
    """

    before = text[
        max(0, start - 50):start
    ]

    after = text[
        end:min(len(text), end + 40)
    ]

    context_hits = 0
    title_hits = 0

    if PERSON_ARTICLE_PATTERN.search(before):
        context_hits += 1

    if ACTION_AFTER_PATTERN.search(after):
        context_hits += 1

    if TITLE_PREFIX_PATTERN.search(before):
        title_hits += 1

    return (
        context_hits,
        title_hits,
    )


# =========================================================
# Single-pass candidate indexing
# =========================================================

def _index_candidates(
    text: str,
    excluded_names: set[str],
) -> dict[str, CandidateStats]:
    """
    Scan the text once.

    From each sequence of capitalized Greek words, create:
    - single-word candidates
    - two-word candidates
    - three-word candidates

    Statistics are collected immediately so the book does
    not need to be rescanned for every candidate.
    """

    stats: dict[
        str,
        CandidateStats,
    ] = defaultdict(CandidateStats)

    tokens = list(
        CAPITALIZED_WORD_PATTERN.finditer(text)
    )

    token_count = len(tokens)

    for index, token_match in enumerate(tokens):
        # -------------------------------------------------
        # Single-word candidate
        # -------------------------------------------------

        raw_name = normalize_name(
            token_match.group(1)
        )

        if (
            raw_name not in excluded_names
            and is_allowed_candidate(raw_name)
        ):
            candidate_stats = stats[raw_name]

            candidate_stats.occurrences += 1

            context_hits, title_hits = (
                _local_evidence(
                    text,
                    token_match.start(),
                    token_match.end(),
                )
            )

            candidate_stats.context_hits += (
                context_hits
            )

            candidate_stats.title_hits += (
                title_hits
            )

        # -------------------------------------------------
        # Two- and three-word candidates
        # -------------------------------------------------

        for size in (2, 3):
            final_index = index + size - 1

            if final_index >= token_count:
                break

            selected = tokens[
                index:index + size
            ]

            # Every word must be separated only by
            # whitespace. If punctuation exists between
            # them they are not one candidate.
            valid_sequence = True

            for left, right in zip(
                selected,
                selected[1:],
            ):
                separator = text[
                    left.end():right.start()
                ]

                if (
                    not separator
                    or not separator.isspace()
                ):
                    valid_sequence = False
                    break

            if not valid_sequence:
                break

            raw_multi_name = " ".join(
                match.group(1)
                for match in selected
            )

            raw_multi_name = normalize_name(
                raw_multi_name
            )

            # Epithets are descriptive variants of an
            # already existing entity. Do not create a
            # separate recovery candidate.
            if raw_multi_name in EPITHET_ALIASES:
                continue

            if raw_multi_name in excluded_names:
                continue

            if not is_allowed_candidate(
                raw_multi_name
            ):
                continue

            candidate_stats = stats[
                raw_multi_name
            ]

            candidate_stats.occurrences += 1
            candidate_stats.multiword_hits += 1

            start = selected[0].start()
            end = selected[-1].end()

            context_hits, title_hits = (
                _local_evidence(
                    text,
                    start,
                    end,
                )
            )

            candidate_stats.context_hits += (
                context_hits
            )

            candidate_stats.title_hits += (
                title_hits
            )

    return stats


# =========================================================
# Main recovery detector
# =========================================================

def detect_name_candidates(
    text: str,
    min_occurrences: int = 1,
    excluded_names: set[str] | None = None,
) -> list[NameCandidate]:
    """
    Fast high-recall recovery detector.

    Unlike the previous implementation, this version does
    not perform multiple full-text regex scans for every
    candidate.

    existing/known entity names can be excluded before
    expensive recovery processing.
    """

    clean_text = clean_input_text(text)

    excluded = set(
        excluded_names or set()
    )

    # Known entities do not need recovery.
    excluded.update(
        KNOWN_ENTITY_TYPES.keys()
    )

    indexed_stats = _index_candidates(
        clean_text,
        excluded,
    )

    candidate_names = set(
        indexed_stats.keys()
    )

    candidate_names = _remove_fragments(
        candidate_names
    )

    candidates: list[NameCandidate] = []

    for name in candidate_names:
        candidate_stats = indexed_stats[
            name
        ]

        if (
            candidate_stats.occurrences
            < min_occurrences
        ):
            continue

        candidates.append(
            NameCandidate(
                name=name,
                occurrences=(
                    candidate_stats.occurrences
                ),
                context_hits=(
                    candidate_stats.context_hits
                ),
                title_hits=(
                    candidate_stats.title_hits
                ),
                multiword_hits=(
                    candidate_stats.multiword_hits
                ),
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