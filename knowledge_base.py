import re

CHUNK_SIZE = 1000


def split_into_chunks(text):
    """
    Split large website text into smaller chunks.
    """

    text = re.sub(r"\s+", " ", text)

    chunks = []

    for i in range(0, len(text), CHUNK_SIZE):
        chunk = text[i:i + CHUNK_SIZE]
        chunks.append(chunk)

    return chunks


def find_relevant_chunks(chunks, question, top_k=3):
    """
    Simple keyword matching.
    """

    question_words = question.lower().split()

    scored_chunks = []

    for chunk in chunks:
        score = 0
        chunk_lower = chunk.lower()

        for word in question_words:
            if word in chunk_lower:
                score += 1

        scored_chunks.append((score, chunk))

    scored_chunks.sort(reverse=True, key=lambda x: x[0])

    return [chunk for score, chunk in scored_chunks[:top_k]]


if __name__ == "__main__":

    sample_text = """
    Welcome to our website.

    Refund policy:
    Products can be returned within 30 days.

    Contact us anytime.
    """

    chunks = split_into_chunks(sample_text)

    results = find_relevant_chunks(
        chunks,
        "What is the refund policy?"
    )

    print(results)