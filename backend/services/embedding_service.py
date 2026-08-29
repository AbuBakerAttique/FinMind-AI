import os

from ollama import Client


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = "nomic-embed-text"

ollama_client = Client(host=OLLAMA_URL)


def create_embedding(text: str) -> list[float]:
    if not text.strip():
        raise ValueError("Cannot create an embedding from empty text.")

    response = ollama_client.embed(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.embeddings[0]


def create_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Cannot create embeddings from empty text.")

    response = ollama_client.embed(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    return response.embeddings