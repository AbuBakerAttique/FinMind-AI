import os

from qdrant_client import QdrantClient


QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    timeout=2,
)


def check_qdrant_connection() -> None:
    qdrant_client.get_collections()