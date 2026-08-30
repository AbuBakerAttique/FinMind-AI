def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be between 0 and chunk_size"
        )

    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):
        current_words = []
        current_length = 0
        end = start

        while end < len(words):
            word = words[end]
            added_length = len(word)

            if current_words:
                added_length += 1

            if (
                current_words
                and current_length + added_length > chunk_size
            ):
                break

            current_words.append(word)
            current_length += added_length
            end += 1

        chunks.append(" ".join(current_words))

        if end >= len(words):
            break

        next_start = end
        overlap_length = 0

        while next_start > start:
            previous_word = words[next_start - 1]
            added_length = len(previous_word)

            if overlap_length:
                added_length += 1

            if overlap_length + added_length > overlap:
                break

            overlap_length += added_length
            next_start -= 1

        if next_start == start:
            next_start = end

        start = next_start

    return chunks