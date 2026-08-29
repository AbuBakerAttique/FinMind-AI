import os

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "financial_documents"
VECTOR_SIZE = 768

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    timeout=2,
)


def check_qdrant_connection() -> None:
    qdrant_client.get_collections()


def ensure_collection_exists() -> None:
    if qdrant_client.collection_exists(COLLECTION_NAME):
        return

    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )


def store_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("Every chunk must have one embedding.")

    ensure_collection_exists()

    points = []

    for chunk, embedding in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=chunk["id"],
                vector=embedding,
                payload={
                    "document_id": chunk["document_id"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "character_count": chunk["character_count"],
                    "metadata": chunk["metadata"],
                },
            )
        )

    if points:
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True,
        )