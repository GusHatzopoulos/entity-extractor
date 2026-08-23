import re
from collections import Counter, defaultdict

import spacy

from src.entity.known_entity import detect_known_entities
from src.entity.lexicon import (
    COMMON_NON_ENTITIES,
    KNOWN_ENTITY_TYPES,
    ROLE_WORDS,
    TITLE_WORDS,
)
from src.entity.normalizer import normalize_entity_name
from src.entity.types import (
    EntityRecord,
    EntitySpan,
)


nlp = spacy.load("el_core_news_sm")


WORD_PATTERN = re.compile(
    r"\b[Α-ΩΆΈΉΊΌΎΏΪΫ]"
    r"[α-ωάέήίόύώϊϋΐΰ]+\b"
)


# =========================================================
# Text chunking
# =========================================================

def split_text_into_chunks(
    text: str,
    chunk_size: int = 50000,
) -> list[tuple[str, int]]:
    """
    Split text into chunks while preserving each
    chunk's global start offset.

    Returns:
        [
            (chunk_text, global_start_offset),
            ...
        ]
    """

    chunks: list[tuple[str, int]] = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(
            start + chunk_size,
            text_length,
        )

        if end < text_length:
            whitespace = text.rfind(
                " ",
                start,
                end,
            )

            if whitespace > start:
                end = whitespace

        chunk = text[start:end]

        if chunk:
            chunks.append(
                (
                    chunk,
                    start,
                )
            )

        start = end

    return chunks


# =========================================================
# Basic validation
# =========================================================

def _should_reject_entity_name(
    name: str,
) -> bool:
    """
    Reject explicit non-entities, standalone titles
    and standalone roles.

    Explicit known entities always have priority.
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


def _is_capitalized_greek_word(
    word: str,
) -> bool:
    """
    Return True when the normalized token looks
    like one capitalized Greek word.
    """

    return bool(
        WORD_PATTERN.fullmatch(word)
    )


# =========================================================
# Span helpers
# =========================================================

def _span_key(
    span: EntitySpan,
) -> tuple[int, int]:
    """
    Return a hashable representation of a span.
    """

    return (
        span["start"],
        span["end"],
    )


def _deduplicate_spans(
    spans: list[EntitySpan],
) -> list[EntitySpan]:
    """
    Remove exact duplicate spans while preserving order.
    """

    seen: set[tuple[int, int]] = set()

    result: list[EntitySpan] = []

    for span in spans:
        key = _span_key(span)

        if key in seen:
            continue

        seen.add(key)

        result.append(span)

    return result

def _span_is_inside(
    inner: EntitySpan,
    outer: EntitySpan,
) -> bool:
    """
    Return True when inner is fully contained
    inside outer.
    """

    return (
        outer["start"] <= inner["start"]
        and inner["end"] <= outer["end"]
    )


def _remove_spans_inside_known_entities(
    spans: list[EntitySpan],
    known_spans: list[EntitySpan],
) -> list[EntitySpan]:
    """
    Remove NER/heuristic spans that are fully contained
    inside an already accepted KNOWN entity span.

    Example:

        Λίαμ Ράλιους Ντέρμοντ
        ^^^^^^^^^^^^^^^^^^^^^ KNOWN

        Λίαμ
        ^^^^ heuristic

    The heuristic Λίαμ span is removed.

    A standalone Λίαμ elsewhere remains untouched.
    """

    filtered: list[EntitySpan] = []

    for span in spans:
        contained = any(
            _span_is_inside(
                span,
                known_span,
            )
            for known_span in known_spans
        )

        if contained:
            continue

        filtered.append(span)

    return _deduplicate_spans(
        filtered
    )

# =========================================================
# Known-entity fragment suppression
# =========================================================

def _is_fragment_of_known_entity(
    name: str,
) -> bool:
    """
    Return True when a MULTI-WORD candidate is only a
    contiguous fragment of a longer known entity.

    Single-word candidates are never rejected here.
    """

    if not name:
        return False

    if name in KNOWN_ENTITY_TYPES:
        return False

    name_parts = name.split()

    if len(name_parts) < 2:
        return False

    for known_name in KNOWN_ENTITY_TYPES:
        known_parts = known_name.split()

        if len(known_parts) <= len(name_parts):
            continue

        window_size = len(name_parts)

        for start in range(
            len(known_parts) - window_size + 1
        ):
            fragment = known_parts[
                start:start + window_size
            ]

            if fragment == name_parts:
                return True

    return False


# =========================================================
# Multiword discovery
# =========================================================

def _collect_multiword_candidates(
    doc,
    chunk_offset: int,
    candidate_counts: Counter[str],
    candidate_spans: dict[
        str,
        list[EntitySpan],
    ],
) -> None:
    """
    Collect conservative 2- and 3-token capitalized
    sequences and store global spans.
    """

    tokens = [
        token
        for token in doc
        if not token.is_space
    ]

    total_tokens = len(tokens)

    for start in range(total_tokens):
        first = normalize_entity_name(
            tokens[start].text.strip()
        )

        if not first:
            continue

        if not _is_capitalized_greek_word(
            first
        ):
            continue

        for size in (2, 3):
            end = start + size

            if end > total_tokens:
                continue

            sequence_tokens = tokens[
                start:end
            ]

            if any(
                token.is_sent_start
                for token in sequence_tokens[1:]
            ):
                continue

            parts: list[str] = []

            valid = True

            for token in sequence_tokens:
                word = normalize_entity_name(
                    token.text.strip()
                )

                if (
                    not word
                    or not _is_capitalized_greek_word(
                        word
                    )
                ):
                    valid = False
                    break

                parts.append(word)

            if not valid:
                continue

            candidate = " ".join(parts)

            if candidate in KNOWN_ENTITY_TYPES:
                candidate_counts[
                    candidate
                ] += 1

            else:
                if any(
                    (
                        part in COMMON_NON_ENTITIES
                        or part in TITLE_WORDS
                        or part in ROLE_WORDS
                    )
                    for part in parts
                ):
                    continue

                candidate_counts[
                    candidate
                ] += 1

            first_token = (
                sequence_tokens[0]
            )

            last_token = (
                sequence_tokens[-1]
            )

            global_start = (
                chunk_offset
                + first_token.idx
            )

            global_end = (
                chunk_offset
                + last_token.idx
                + len(last_token.text)
            )

            span = EntitySpan(
                start=global_start,
                end=global_end,
            )

            candidate_spans[
                candidate
            ].append(span)


# =========================================================
# spaCy detection
# =========================================================

def detect_spacy_entities_and_candidates(
    text: str,
    chunk_size: int = 50000,
) -> tuple[
    list[
        tuple[
            str,
            str,
            EntitySpan,
        ]
    ],
    list[
        tuple[
            str,
            int,
            list[EntitySpan],
        ]
    ],
]:
    """
    Run one spaCy pass over the document.

    Returns:

    NER:
        [
            (
                entity_name,
                entity_type,
                global_span,
            )
        ]

    Heuristics:
        [
            (
                candidate_name,
                occurrence_count,
                global_spans,
            )
        ]
    """

    ner_entities: list[
        tuple[
            str,
            str,
            EntitySpan,
        ]
    ] = []

    candidate_counts: Counter[str] = (
        Counter()
    )

    candidate_spans: dict[
        str,
        list[EntitySpan],
    ] = defaultdict(list)

    multiword_counts: Counter[str] = (
        Counter()
    )

    multiword_spans: dict[
        str,
        list[EntitySpan],
    ] = defaultdict(list)

    pos_counts: dict[
        str,
        Counter[str],
    ] = defaultdict(Counter)

    chunks = split_text_into_chunks(
        text,
        chunk_size=chunk_size,
    )

    total_chunks = len(chunks)

    for index, (
        chunk,
        chunk_offset,
    ) in enumerate(
        chunks,
        start=1,
    ):
        print(
            f"Processing NLP chunk "
            f"{index}/{total_chunks}..."
        )

        doc = nlp(chunk)

        # =================================================
        # Named Entity Recognition
        # =================================================

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

            global_start = (
                chunk_offset
                + ent.start_char
            )

            global_end = (
                chunk_offset
                + ent.end_char
            )

            span = EntitySpan(
                start=global_start,
                end=global_end,
            )

            ner_entities.append(
                (
                    entity_text,
                    ent.label_,
                    span,
                )
            )

        # =================================================
        # Single-word candidates + POS
        # =================================================

        for token in doc:
            word = normalize_entity_name(
                token.text.strip()
            )

            if not word:
                continue

            if _should_reject_entity_name(
                word
            ):
                continue

            if not _is_capitalized_greek_word(
                word
            ):
                continue

            candidate_counts[word] += 1

            pos_counts[word][
                token.pos_
            ] += 1

            global_start = (
                chunk_offset
                + token.idx
            )

            global_end = (
                global_start
                + len(token.text)
            )

            span = EntitySpan(
                start=global_start,
                end=global_end,
            )

            candidate_spans[
                word
            ].append(span)

        # =================================================
        # Multiword candidates
        # =================================================

        _collect_multiword_candidates(
            doc,
            chunk_offset,
            multiword_counts,
            multiword_spans,
        )

    # =====================================================
    # POS filtering
    # =====================================================

    accepted_counts: Counter[str] = (
        Counter()
    )

    accepted_spans: dict[
        str,
        list[EntitySpan],
    ] = defaultdict(list)

    for (
        word,
        total_count,
    ) in candidate_counts.items():

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

        negative_score = (
            reject_like * 2
        )

        accepted = False

        if (
            proper_like >= 1
            and positive_score > negative_score
        ):
            accepted = True

        elif (
            proper_like == 0
            and uncertain_like >= 1
            and reject_like == 0
        ):
            accepted = True

        if accepted:
            spans = _deduplicate_spans(
                candidate_spans[word]
            )

            accepted_counts[word] = len(
                spans
            )

            accepted_spans[word] = (
                spans
            )

    # =====================================================
    # Add multiword candidates
    # =====================================================

    for candidate in multiword_counts:
        if _should_reject_entity_name(
            candidate
        ):
            continue

        spans = _deduplicate_spans(
            multiword_spans[candidate]
        )

        if (
            candidate not in accepted_counts
            or len(spans)
            > accepted_counts[candidate]
        ):
            accepted_counts[
                candidate
            ] = len(spans)

            accepted_spans[
                candidate
            ] = spans

    candidate_entities = sorted(
        [
            (
                name,
                count,
                accepted_spans[name],
            )
            for (
                name,
                count,
            ) in accepted_counts.items()
        ],
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    return (
        ner_entities,
        candidate_entities,
    )


# =========================================================
# Combined detection
# =========================================================

def detect_combined_entities(
    text: str,
    min_occurrences: int = 1,
) -> list[EntityRecord]:
    """
    Combine:

    1. Known entities
    2. spaCy NER
    3. POS-supported single-word candidates
    4. Conservative multiword candidates

    Every layer uses the same global span coordinate
    system.
    """

    (
        ner_entities,
        all_candidates,
    ) = detect_spacy_entities_and_candidates(
        text
    )

    known_entities = detect_known_entities(
        text
    )

    known_spans: list[EntitySpan] = [
        span
        for entity in known_entities
        for span in entity.get(
            "spans",
            [],
        )
    ]

    candidate_entities = [
        (
            name,
            count,
            spans,
        )
        for (
            name,
            count,
            spans,
        ) in all_candidates
        if count >= min_occurrences
    ]

    combined: dict[
        str,
        EntityRecord,
    ] = {}

    # =====================================================
    # Known entities
    # =====================================================

    for entity in known_entities:
        combined[
            entity["entity"]
        ] = entity

    # =====================================================
    # NER entities
    # =====================================================

    for (
        entity_text,
        entity_type,
        span,
    ) in ner_entities:

        entity_text = normalize_entity_name(
            entity_text
        )

        filtered_ner_spans = (
            _remove_spans_inside_known_entities(
                [span],
                known_spans,
            )
        )

        if not filtered_ner_spans:
            continue

        span = filtered_ner_spans[0]

        if not entity_text:
            continue

        if _is_fragment_of_known_entity(
            entity_text
        ):
            continue

        if entity_text in combined:
            existing = combined[
                entity_text
            ]

            # KNOWN entities already contain exact spans
            # from the authoritative dictionary detector.
            if (
                existing.get("source")
                == "KNOWN"
            ):
                continue

            existing_spans: list[
                EntitySpan
            ] = list(
                existing.get(
                    "spans",
                    [],
                )
            )

            existing_spans.append(
                span
            )

            merged_spans = (
                _deduplicate_spans(
                    existing_spans
                )
            )

            existing[
                "spans"
            ] = merged_spans

            existing[
                "occurrences"
            ] = len(
                merged_spans
            )

        else:
            entity_record: EntityRecord = {
                "entity": entity_text,
                "type": entity_type,
                "source": "NER",
                "occurrences": 1,
                "spans": [span],
            }

            combined[
                entity_text
            ] = entity_record

    # =====================================================
    # Heuristic candidates
    # =====================================================

    for (
        entity_text,
        _count,
        spans,
    ) in candidate_entities:

        entity_text = normalize_entity_name(
            entity_text
        )

        if not entity_text:
            continue

        if _is_fragment_of_known_entity(
            entity_text
        ):
            continue

        spans = _deduplicate_spans(
            spans
        )

        spans = (
            _remove_spans_inside_known_entities(
                spans,
                known_spans,
            )
        )

        if not spans:
            continue

        if entity_text in combined:
            existing = combined[
                entity_text
            ]

            if (
                existing.get("source")
                == "KNOWN"
            ):
                continue

            existing_spans: list[
                EntitySpan
            ] = list(
                existing.get(
                    "spans",
                    [],
                )
            )

            merged_spans = (
                _deduplicate_spans(
                    existing_spans
                    + spans
                )
            )

            existing[
                "spans"
            ] = merged_spans

            existing[
                "occurrences"
            ] = len(
                merged_spans
            )

        else:
            entity_record: EntityRecord = {
                "entity": entity_text,
                "type": "UNKNOWN",
                "source": "HEURISTIC",
                "occurrences": len(
                    spans
                ),
                "spans": spans,
            }

            combined[
                entity_text
            ] = entity_record

    return sorted(
        combined.values(),
        key=lambda item: (
            -item["occurrences"],
            item["entity"],
        ),
    )