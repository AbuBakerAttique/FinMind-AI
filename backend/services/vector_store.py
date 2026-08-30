import os

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)
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
def search_chunks(
    query_vector: list[float],
    document_id: str,
    limit: int = 5,
) -> list[dict]:
    response = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    results = []

    for point in response.points:
        payload = point.payload or {}
        metadata = payload.get("metadata", {})

        results.append(
            {
                "score": point.score,
                "text": payload.get("text", ""),
                "page_number": metadata.get("page_number"),
                "source": metadata.get("source"),
                "chunk_index": payload.get("chunk_index"),
            }
        )

    return results


def get_stored_documents() -> list[dict]:
    ensure_collection_exists()

    documents = {}
    offset = None

    while True:
        points, offset = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            payload = point.payload or {}
            metadata = payload.get("metadata", {})
            document_id = payload.get("document_id")

            if not document_id:
                continue

            if document_id not in documents:
                documents[document_id] = {
                    "document_id": document_id,
                    "filename": metadata.get("source"),
                    "chunk_count": 0,
                    "page_numbers": set(),
                }

            documents[document_id]["chunk_count"] += 1

            page_number = metadata.get("page_number")

            if page_number is not None:
                documents[document_id]["page_numbers"].add(
                    page_number
                )

        if offset is None:
            break

    result = []

    for document in documents.values():
        page_numbers = document.pop("page_numbers")

        document["total_pages"] = (
            max(page_numbers) if page_numbers else 0
        )

        result.append(document)

    return result



def delete_document(document_id: str) -> None:
    qdrant_client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )
        ),
        wait=True,
    )