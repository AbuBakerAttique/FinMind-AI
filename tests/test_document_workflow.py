from fastapi.testclient import TestClient

from backend import main


client = TestClient(main.app)


class FakePage:
    def extract_text(self):
        return "Revenue increased during the financial year."


class FakePdfReader:
    def __init__(self, _file_stream):
        self.pages = [FakePage()]


def test_successful_document_upload(monkeypatch):
    stored_data = {}

    monkeypatch.setattr(
        main,
        "PdfReader",
        FakePdfReader,
    )

    monkeypatch.setattr(
        main,
        "chunk_text",
        lambda _text: [
            "Revenue increased during the financial year."
        ],
    )

    monkeypatch.setattr(
        main,
        "create_embeddings",
        lambda texts: [[0.1] * 768 for _text in texts],
    )

    def fake_store_chunks(chunks, embeddings):
        stored_data["chunks"] = chunks
        stored_data["embeddings"] = embeddings

    monkeypatch.setattr(
        main,
        "store_chunks",
        fake_store_chunks,
    )

    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "financial-report.pdf",
                b"fake PDF content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "financial-report.pdf"
    assert data["total_pages"] == 1
    assert data["total_chunks"] == 1
    assert data["document_id"]

    assert len(stored_data["chunks"]) == 1
    assert len(stored_data["embeddings"]) == 1
    assert len(stored_data["embeddings"][0]) == 768

    stored_chunk = stored_data["chunks"][0]

    assert stored_chunk["document_id"] == data["document_id"]
    assert stored_chunk["chunk_index"] == 0
    assert stored_chunk["metadata"]["page_number"] == 1
    assert stored_chunk["metadata"]["source"] == (
        "financial-report.pdf"
    )


def test_lists_stored_documents(monkeypatch):
    fake_documents = [
        {
            "document_id": "document-123",
            "filename": "report.pdf",
            "chunk_count": 5,
            "total_pages": 2,
        }
    ]

    monkeypatch.setattr(
        main,
        "get_stored_documents",
        lambda: fake_documents,
    )

    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == {
        "documents_count": 1,
        "documents": fake_documents,
    }


def test_deletes_existing_document(monkeypatch):
    deleted_document_ids = []

    monkeypatch.setattr(
        main,
        "get_stored_documents",
        lambda: [
            {
                "document_id": "document-123",
                "filename": "report.pdf",
                "chunk_count": 5,
                "total_pages": 2,
            }
        ],
    )

    monkeypatch.setattr(
        main,
        "delete_document",
        lambda document_id: deleted_document_ids.append(
            document_id
        ),
    )

    response = client.delete(
        "/documents/document-123"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Document deleted successfully.",
        "document_id": "document-123",
    }

    assert deleted_document_ids == ["document-123"]


def test_delete_returns_404_for_missing_document(
    monkeypatch,
):
    monkeypatch.setattr(
        main,
        "get_stored_documents",
        lambda: [],
    )

    response = client.delete(
        "/documents/missing-document"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


def test_searches_selected_document(monkeypatch):
    fake_results = [
        {
            "score": 0.91,
            "text": "Total net sales were 416161 million.",
            "page_number": 1,
            "source": "report.pdf",
            "chunk_index": 2,
        }
    ]

    search_arguments = {}

    monkeypatch.setattr(
        main,
        "create_embedding",
        lambda _question: [0.2] * 768,
    )

    def fake_search_chunks(
        query_vector,
        document_id,
        limit,
    ):
        search_arguments["query_vector"] = query_vector
        search_arguments["document_id"] = document_id
        search_arguments["limit"] = limit

        return fake_results

    monkeypatch.setattr(
        main,
        "search_chunks",
        fake_search_chunks,
    )

    response = client.post(
        "/documents/search",
        json={
            "document_id": "document-123",
            "question": "What were total net sales?",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["document_id"] == "document-123"
    assert data["results_count"] == 1
    assert data["results"] == fake_results

    assert search_arguments["document_id"] == "document-123"
    assert search_arguments["limit"] == 5
    assert len(search_arguments["query_vector"]) == 768


def test_ask_returns_answer_and_unique_sources(
    monkeypatch,
):
    fake_results = [
        {
            "score": 0.80,
            "text": "First result from page one.",
            "page_number": 1,
            "source": "report.pdf",
            "chunk_index": 0,
        },
        {
            "score": 0.95,
            "text": "Better result from page one.",
            "page_number": 1,
            "source": "report.pdf",
            "chunk_index": 1,
        },
        {
            "score": 0.75,
            "text": "Result from page two.",
            "page_number": 2,
            "source": "report.pdf",
            "chunk_index": 2,
        },
    ]

    monkeypatch.setattr(
        main,
        "create_embedding",
        lambda _question: [0.2] * 768,
    )

    monkeypatch.setattr(
        main,
        "search_chunks",
        lambda query_vector, document_id, limit: fake_results,
    )

    monkeypatch.setattr(
        main,
        "generate_answer",
        lambda question, search_results: (
            "Total net sales increased."
        ),
    )

    response = client.post(
        "/documents/ask",
        json={
            "document_id": "document-123",
            "question": "Did total net sales increase?",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "Total net sales increased."
    assert len(data["sources"]) == 2

    page_one_source = next(
        source
        for source in data["sources"]
        if source["page_number"] == 1
    )

    assert page_one_source["score"] == 0.95
    assert page_one_source["source"] == "report.pdf"