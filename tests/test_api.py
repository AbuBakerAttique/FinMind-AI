from fastapi.testclient import TestClient

from backend import main


client = TestClient(main.app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "FinMind AI backend is running!"
    }


def test_health_endpoint(monkeypatch):
    monkeypatch.setattr(
        main,
        "check_qdrant_connection",
        lambda: None,
    )

    monkeypatch.setattr(
        main,
        "check_ollama_connection",
        lambda: None,
    )

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "qdrant": "healthy",
            "ollama": "healthy",
        },
    }


def test_health_returns_503_when_qdrant_is_unavailable(
    monkeypatch,
):
    def fail_qdrant_connection():
        raise ConnectionError("Qdrant is unavailable")

    monkeypatch.setattr(
        main,
        "check_qdrant_connection",
        fail_qdrant_connection,
    )

    response = client.get("/health")

    assert response.status_code == 503


def test_health_returns_503_when_ollama_is_unavailable(
    monkeypatch,
):
    def fail_ollama_connection():
        raise ConnectionError("Ollama is unavailable")

    monkeypatch.setattr(
        main,
        "check_qdrant_connection",
        lambda: None,
    )

    monkeypatch.setattr(
        main,
        "check_ollama_connection",
        fail_ollama_connection,
    )

    response = client.get("/health")

    assert response.status_code == 503


def test_upload_rejects_non_pdf_file():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "notes.txt",
                b"This is not a PDF.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only PDF files are allowed."
    )


def test_upload_rejects_empty_pdf():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "empty.pdf",
                b"",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "The uploaded PDF is empty."
    )


def test_ask_requires_document_id():
    response = client.post(
        "/documents/ask",
        json={
            "question": "What was the total revenue?",
            "limit": 5,
        },
    )

    assert response.status_code == 422


def test_ask_requires_question():
    response = client.post(
        "/documents/ask",
        json={
            "document_id": "test-document-id",
            "limit": 5,
        },
    )

    assert response.status_code == 422


def test_growth_calculation_requires_question():
    response = client.post(
        "/documents/calculate-growth",
        json={
            "document_id": "test-document-id",
            "limit": 5,
        },
    )

    assert response.status_code == 422