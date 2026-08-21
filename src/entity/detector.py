import re
import spacy

from collections import Counter
from src.entity.normalizer import normalize_entity_name
from src.entity.types import EntityRecord

nlp = spacy.load("el_core_news_sm")

WORD_PATTERN = re.compile(
    r"\b[Α-ΩΆΈΉΊΌΎΏΪΫ][α-ωάέήίόύώϊϋΐΰ]+\b"
)

COMMON_FALSE_POSITIVES = {
    "Αυτό",
    "Αυτή",
    "Αυτές",
    "Αυτοί",
    "Αλλά",
    "Από",
    "Αμέσως",
    "Αργότερα",
    "Για",
    "Γιατί",
    "Δεν",
    "Έτσι",
    "Εδώ",
    "Είναι",
    "Είμαστε",
    "Είχε",
    "Είπε",
    "Ένα",
    "Ένας",
    "Έπειτα",
    "Εκείνος",
    "Εκείνη",
    "Η",
    "Ήταν",
    "Θα",
    "Και",
    "Κάποια",
    "Κάποιος",
    "Κάποτε",
    "Καθώς",
    "Κι",
    "Μα",
    "Με",
    "Μετά",
    "Μη",
    "Μια",
    "Μόλις",
    "Ναι",
    "Να",
    "Ο",
    "Οι",
    "Όλοι",
    "Όμως",
    "Όταν",
    "Όχι",
    "Ποιος",
    "Πώς",
    "Πρέπει",
    "Σαν",
    "Σε",
    "Στη",
    "Στην",
    "Στο",
    "Στον",
    "Στους",
    "Τα",
    "Την",
    "Της",
    "Τι",
    "Το",
    "Τον",
    "Του",
    "Τους",
    "Τώρα",
    "Τότε",
    "Ώστε",
    "Εσύ",
    "Εσείς",
    "Είσαι",
    "Είστε",
    "Πού",
    "Ποιοι",
    "Πολύ",
    "Πολλοί",
    "Εκεί",
    "Εκείνοι",
    "Φυσικά",
    "Αυτούς",
    "Έλα",
    "Έλαβα",
    "Όλα",
    "Όλες",
    "Ακόμα",
    "Ακόμη",
    "Μάλιστα",
    "Ακριβώς",
    "Πριν",
    "Πολλές",
    "Λίγο",
    "Λίγοι",
    "Ωστόσο",
    "Ίσως",
    "Χμ",
    "Ωραία",
    "Χμφ",
    "Αν",
    "Αντί",
    "Όπως",
    "Λοιπόν",
    "Αντίθετα",
    "Στην",
    "Στο",
    "Στον",
    "Στους",
    "Στις",
    "Στα",
    "Θέλω",
    "Θέλεις",
    "Όσοι",
    "Όσες",
    "Όσα",
    "Όσο",
    "Παρά",
    "Πολλές",
    "Έχω",
    "Έχεις",
    "Γύρισε",
    "Γύρισα",
    "Μονάχα",
    "Μόνο",
    "Αλήθεια",
    "Έκανε",
    "Έκανα",
    "Έκαναν",
    "Έτσι",
    "Έχουμε",
    "Σίγουρα",
    "Επίσης",
    "Ευχαριστώ",
    "Ευχαριστούμε",
    "Συγγνώμη",
    "Συγγνώμης",
    "Σερ",
    "Σας",
    "Ωραία",
    "Μην",
    "Μη",
    "Κανείς",
    "Κανένας",
    "Σχεδόν",
    "Δύο",
    "Τρεις",
    "Δυστυχώς",
    "Κοίταξε",
    "Κοίταξα",
    "Ξαφνικά",
}


def detect_candidate_entities(
    text: str,
    min_occurrences: int = 2,
) -> list[tuple[str, int]]:
    """Detect probable Greek proper names using capitalization and frequency."""

    matches = WORD_PATTERN.findall(text)
    counts = Counter(
        word
        for word in matches
        if word not in COMMON_FALSE_POSITIVES
    )

    candidates = (
        (word, count)
        for word, count in counts.items()
        if count >= min_occurrences
    )

    return sorted(
        candidates,
        key=lambda item: (-item[1], item[0]),
    )


def detect_ner_entities(
    text: str,
    chunk_size: int = 50000,
) -> list[tuple[str, str]]:
    """
    Detect named entities using spaCy's Greek NER model.

    Large texts are processed in smaller chunks.
    """

    entities: list[tuple[str, str]] = []

    chunks = split_text_into_chunks(
        text,
        chunk_size=chunk_size,
    )

    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        print(f"Processing NER chunk {index}/{total_chunks}...")

        doc = nlp(chunk)

        for ent in doc.ents:
            entity_text = ent.text.strip()

            if entity_text:
                entities.append(
                    (
                        entity_text,
                        ent.label_,
                    )
                )

    return entities


def detect_combined_entities(
    text: str,
    min_occurrences: int = 1,
) -> list[EntityRecord]:
    """
    Combine NER results with heuristic candidate detection.

    NER results take priority. Heuristic candidates that were not
    detected by NER are added as UNKNOWN entities.
    """

    ner_entities = detect_ner_entities(text)

    candidate_entities = detect_candidate_entities(
        text,
        min_occurrences=min_occurrences,
    )

    combined: dict[str, EntityRecord] = {}

    # Add and count NER entities.
    for entity_text, entity_type in ner_entities:
        entity_text = normalize_entity_name(entity_text)

        if not entity_text:
            continue

        if entity_text in combined:
            combined[entity_text]["occurrences"] = (
                combined[entity_text]["occurrences"] + 1
            )
        else:
            combined[entity_text] = {
                "entity": entity_text,
                "type": entity_type,
                "source": "NER",
                "occurrences": 1,
            }

    # Add heuristic entities that NER missed.
    for entity_text, count in candidate_entities:
        entity_text = normalize_entity_name(entity_text)

        if not entity_text:
            continue

        if entity_text in combined:
            # Both detectors saw the same occurrences.
            # Do not add the counts together.
            combined[entity_text]["occurrences"] = max(
                combined[entity_text]["occurrences"],
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
            -int(item["occurrences"]),
            str(item["entity"]),
        ),
    )


def split_text_into_chunks(
    text: str,
    chunk_size: int = 50000,
) -> list[str]:
    """
    Split text into chunks while trying to break at whitespace.
    """

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            whitespace = text.rfind(" ", start, end)

            if whitespace > start:
                end = whitespace

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end

    return chunks
