import re


SENTENCE_SPLIT_PATTERN = re.compile(
    r"(?<=[.!;?])\s+"
)


def get_entity_contexts(
    text: str,
    entity_name: str,
    max_contexts: int = 12,
) -> list[str]:
    """
    Return sentences containing an exact entity occurrence.
    """

    entity_pattern = re.compile(
        rf"(?<!\w){re.escape(entity_name)}(?!\w)"
    )

    contexts: list[str] = []

    for sentence in SENTENCE_SPLIT_PATTERN.split(text):
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