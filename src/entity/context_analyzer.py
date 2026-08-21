import re


SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!;?])\s+")


def get_entity_contexts(
    text: str,
    entity_name: str,
    max_contexts: int = 3,
) -> list[str]:
    """
    Return a small number of sentences containing the entity.
    """

    sentences = SENTENCE_SPLIT_PATTERN.split(text)

    contexts = []

    for sentence in sentences:
        if entity_name in sentence:
            cleaned = " ".join(sentence.split()).strip()

            if cleaned:
                contexts.append(cleaned)

        if len(contexts) >= max_contexts:
            break

    return contexts