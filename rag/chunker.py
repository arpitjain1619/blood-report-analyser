def chunk_text(text: str, chunk_size: int = 100, overlap: int = 20) -> list:
    """
    Splits text into overlapping chunks, measured in words.

    chunk_size = how many words per chunk
    overlap = how many words repeat at the start of the next chunk
              (helps avoid cutting a sentence's meaning in half at chunk boundaries)
    """
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break
        start = end - overlap  # step forward, but overlap with the previous chunk

    return chunks
