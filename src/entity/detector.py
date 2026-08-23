import re
from collections import Counter, defaultdict

import spacy

from src.entity.lexicon import (COMMON_NON_ENTITIES, KNOWN_ENTITY_TYPES, ROLE_WORDS, TITLE_WORDS)
from src.entity.normalizer import normalize_entity_name
from src.entity.types import EntityRecord

nlp = spacy.load("el_core_news_sm")

WORD_PATTERN = re.compile(
    r"\b[Α-ΩΆΈΉΊΌΎΏΪΫ][α-ωάέήίόύώϊϋΐΰ]+\b"
)

def split_text_into_chunks(
    text: str,
    chunk_size: int = 50000,
) -> list[str]:
    """
    Split text into chunks while trying to avoid
    cutting a word in the middle.
    """

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            whitespace = text.rfind(
                " ",
                start,
                end,
            )

            if whitespace > start:
                end = whitespace

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end

    return chunks

def _should_reject_entity_name(
    name: str,
) -> bool:
    """
    Reject known non-entities, standalone titles, and roles.

    Explicit known entities always take priority.
    """

    if name in KNOWN_ENTITY_TYPES:
        return False

    if name in COMMON_NON_ENTITIES:
        return True

    if name in TITLE_WORDS:
        return True

    if name in ROLE_WORDS:
        return True

    return False

def detect_spacy_entities_and_candidates(
    text: str,
    chunk_size: int = 50000,
) -> tuple[
    list[tuple[str, str]],
    list[tuple[str, int]],
]:
    """
    Run one spaCy pass over the text.

    Collect:
    - NER entities
    - capitalized heuristic candidates
    - POS distribution for every candidate

    A candidate is kept only when its overall POS evidence
    supports noun/proper-name-like usage.
    """

    ner_entities: list[tuple[str, str]] = []

    candidate_counts: Counter[str] = Counter()

    pos_counts: dict[str, Counter[str]] = defaultdict(
        Counter
    )

    chunks = split_text_into_chunks(
        text,
        chunk_size=chunk_size,
    )

    total_chunks = len(chunks)

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        print(
            f"Processing NLP chunk "
            f"{index}/{total_chunks}..."
        )

        doc = nlp(chunk)

        # -------------------------
        # Named Entity Recognition
        # -------------------------

        for ent in doc.ents:
            entity_text = normalize_entity_name(
                ent.text.strip()
            )

            if not entity_text:
                continue

            if _should_reject_entity_name(
                entity_text
            ):
                continue

            ner_entities.append(
                (
                    entity_text,
                    ent.label_,
                )
            )

        # -------------------------
        # Candidate POS statistics
        # -------------------------

        for token in doc:
            word = normalize_entity_name(
                token.text.strip()
            )

            if not word:
                continue

            if _should_reject_entity_name(word):
                continue

            if not WORD_PATTERN.fullmatch(word):
                continue

            candidate_counts[word] += 1
            pos_counts[word][token.pos_] += 1

    # -------------------------
    # POS-distribution filtering
    # -------------------------

    candidate_entities: list[
        tuple[str, int]
    ] = []

    for word, total_count in candidate_counts.items():
        distribution = pos_counts[word]

        proper_like = (
            distribution["PROPN"]
            + distribution["NOUN"]
        )

        uncertain_like = (
            distribution["ADJ"]
            + distribution["X"]
        )

        reject_like = (
            distribution["VERB"]
            + distribution["AUX"]
            + distribution["ADV"]
            + distribution["PRON"]
            + distribution["DET"]
            + distribution["ADP"]
            + distribution["CCONJ"]
            + distribution["SCONJ"]
        )

        positive_score = (
            proper_like * 2
            + uncertain_like
        )

        negative_score = reject_like * 2

        # Strong noun / proper-name evidence.
        if (
            proper_like >= 1
            and positive_score > negative_score
        ):
            candidate_entities.append(
                (
                    word,
                    total_count,
                )
            )

        # Unknown / fictional-name fallback.
        #
        # Keep even a single ADJ/X occurrence when there is
        # no VERB/ADV/PRON/etc. evidence against it.
        elif (
            proper_like == 0
            and uncertain_like >= 1
            and reject_like == 0
        ):
            candidate_entities.append(
                (
                    word,
                    total_count,
                )
            )

    candidate_entities.sort(
        key=lambda item: (
            -item[1],
            item[0],
        )
    )

    return (
        ner_entities,
        candidate_entities,
    )


def detect_combined_entities(
    text: str,
    min_occurrences: int = 1,
) -> list[EntityRecord]:
    """
    Combine spaCy NER with POS-supported heuristic detection.

    NER classification takes priority.
    Heuristic candidates missed by NER are added as UNKNOWN.
    """

    ner_entities, all_candidates = (
        detect_spacy_entities_and_candidates(text)
    )

    candidate_entities = [
        (name, count)
        for name, count in all_candidates
        if count >= min_occurrences
    ]

    combined: dict[str, EntityRecord] = {}

    # Aggregate NER results.
    for entity_text, entity_type in ner_entities:
        entity_text = normalize_entity_name(
            entity_text
        )

        if not entity_text:
            continue

        if entity_text in combined:
            combined[entity_text][
                "occurrences"
            ] += 1

        else:
            combined[entity_text] = {
                "entity": entity_text,
                "type": entity_type,
                "source": "NER",
                "occurrences": 1,
            }

    # Merge POS-supported candidates.
    for entity_text, count in candidate_entities:
        entity_text = normalize_entity_name(
            entity_text
        )

        if not entity_text:
            continue

        if entity_text in combined:
            combined[entity_text][
                "occurrences"
            ] = max(
                combined[entity_text][
                    "occurrences"
                ],
                count,
            )

        else:
            combined[entity_text] = {
                "entity": entity_text,
                "type": "UNKNOWN",
                "source": "HEURISTIC",
                "occurrences": count,
            }

    return sorted(
        combined.values(),
        key=lambda item: (
            -item["occurrences"],
            item["entity"],
        ),
    )