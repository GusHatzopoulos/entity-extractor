import re
from functools import lru_cache


# =========================================================
# Sentence splitting
# =========================================================

SENTENCE_SPLIT_PATTERN = re.compile(
    r"(?<=[.!;?])\s+"
)


@lru_cache(maxsize=2)
def split_sentences(
    text: str,
) -> tuple[str, ...]:
    """
    Split text into sentences once and cache the result.

    The same large document is normally queried many times
    while entities are being filtered/classified. Caching
    prevents the complete document from being split again
    for every entity.
    """

    return tuple(
        SENTENCE_SPLIT_PATTERN.split(text)
    )


# =========================================================
# Entity contexts
# =========================================================

def get_entity_contexts(
    text: str,
    entity_name: str,
    max_contexts: int = 12,
) -> list[str]:
    """
    Return sentences containing an exact entity occurrence.

    Sentence splitting is cached, so repeated calls for the
    same document do not repeatedly split the full text.
    """

    if not entity_name:
        return []

    entity_pattern = re.compile(
        rf"(?<!\w)"
        rf"{re.escape(entity_name)}"
        rf"(?!\w)"
    )

    contexts: list[str] = []

    for sentence in split_sentences(text):
        if not entity_pattern.search(sentence):
            continue

        cleaned = " ".join(
            sentence.split()
        ).strip()

        if cleaned:
            contexts.append(cleaned)

        if len(contexts) >= max_contexts:
            break

    return contexts


# =========================================================
# Cache management
# =========================================================

def clear_context_cache() -> None:
    """
    Clear cached sentence splits.

    Useful when processing many different documents in the
    same Python process.
    """

    split_sentences.cache_clear()