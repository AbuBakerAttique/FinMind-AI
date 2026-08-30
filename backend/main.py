from decimal import Decimal, InvalidOperation
from io import BytesIO
from uuid import uuid4
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from pypdf import PdfReader
from pypdf.errors import PdfReadError


from dotenv import load_dotenv

load_dotenv()

from backend.services.embedding_service import (
    create_embedding,
    create_embeddings,
)
from backend.services.embedding_service import (
    create_embedding,
    create_embeddings,
)
from backend.services.financial_calculator import calculate_growth
from backend.services.llm_service import (
    check_ollama_connection,
    extract_growth_values,
    generate_answer,
)
from backend.services.text_chunker import chunk_text
from backend.services.vector_store import (
    check_qdrant_connection,
    delete_document,
    get_stored_documents,
    search_chunks,
    store_chunks,
)
from fastapi.middleware.cors import CORSMiddleware
class SearchRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)


class GrowthCalculationRequest(BaseModel):
    previous_value: Decimal
    current_value: Decimal


app = FastAPI(
    title="FinMind AI",
    description="A local API for financial document analysis.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FinMind AI backend is running!"}


@app.get("/health")
def health_check(response: Response):
    services = {
        "api": "healthy",
        "qdrant": "healthy",
        "ollama": "healthy",
    }

    try:
        check_qdrant_connection()
    except Exception:
        services["qdrant"] = "unhealthy"

    try:
        check_ollama_connection()
    except Exception:
        services["ollama"] = "unhealthy"

    if "unhealthy" in services.values():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "unhealthy",
            "services": services,
        }

    return {
        "status": "healthy",
        "services": services,
    }


@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    document_id = str(uuid4())

    try:
        reader = PdfReader(BytesIO(file_content))
        chunks = []
        global_chunk_index = 0

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            text = page.extract_text() or ""
            page_chunks = chunk_text(text)

            for page_chunk_index, chunk in enumerate(
                page_chunks
            ):
                chunks.append(
                    {
                        "id": str(uuid4()),
                        "document_id": document_id,
                        "chunk_index": global_chunk_index,
                        "text": chunk,
                        "character_count": len(chunk),
                        "metadata": {
                            "page_number": page_number,
                            "page_chunk_index": page_chunk_index,
                            "source": file.filename,
                        },
                    }
                )

                global_chunk_index += 1

        embeddings = create_embeddings(
            [chunk["text"] for chunk in chunks]
        )

        store_chunks(chunks, embeddings)

    except PdfReadError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "total_pages": len(reader.pages),
        "total_chunks": len(chunks),
        "chunks": chunks,
    }


@app.get("/documents")
def list_documents():
    documents = get_stored_documents()

    return {
        "documents_count": len(documents),
        "documents": documents,
    }


@app.delete("/documents/{document_id}")
def remove_document(document_id: str):
    documents = get_stored_documents()

    document_exists = any(
        document["document_id"] == document_id
        for document in documents
    )

    if not document_exists:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    delete_document(document_id)

    return {
        "message": "Document deleted successfully.",
        "document_id": document_id,
    }


@app.post("/documents/search")
def search_document(request: SearchRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="The question cannot be empty.",
        )

    query_vector = create_embedding(question)

    results = search_chunks(
        query_vector=query_vector,
        document_id=request.document_id,
        limit=request.limit,
    )

    return {
        "document_id": request.document_id,
        "question": question,
        "results_count": len(results),
        "results": results,
    }


@app.post("/documents/ask")
def ask_document(request: SearchRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="The question cannot be empty.",
        )

    query_vector = create_embedding(question)

    results = search_chunks(
        query_vector=query_vector,
        document_id=request.document_id,
        limit=request.limit,
    )

    answer = generate_answer(
        question=question,
        search_results=results,
    )

    unique_sources = {}

    for result in results:
        source_key = (
            result["source"],
            result["page_number"],
        )

        existing_source = unique_sources.get(source_key)

        if (
            existing_source is None
            or result["score"] > existing_source["score"]
        ):
            unique_sources[source_key] = {
                "page_number": result["page_number"],
                "source": result["source"],
                "score": result["score"],
            }

    sources = list(unique_sources.values())

    return {
        "document_id": request.document_id,
        "question": question,
        "answer": answer,
        "sources": sources,
    }


@app.post("/calculations/growth")
def calculate_financial_growth(
    request: GrowthCalculationRequest,
):
    try:
        result = calculate_growth(
            previous_value=request.previous_value,
            current_value=request.current_value,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        key: str(value)
        for key, value in result.items()
    }


@app.post("/documents/calculate-growth")
def calculate_document_growth(request: SearchRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="The question cannot be empty.",
        )

    query_vector = create_embedding(question)

    results = search_chunks(
        query_vector=query_vector,
        document_id=request.document_id,
        limit=request.limit,
    )

    extracted = extract_growth_values(
        question=question,
        search_results=results,
    )

    if (
        not extracted.found
        or extracted.previous is None
        or extracted.current is None
    ):
        raise HTTPException(
            status_code=422,
            detail="The required financial values were not found.",
        )

    try:
        previous_value = Decimal(
            extracted.previous.value
        )
        current_value = Decimal(
            extracted.current.value
        )

        calculation = calculate_growth(
            previous_value=previous_value,
            current_value=current_value,
        )

    except (InvalidOperation, ValueError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    return {
        "metric": extracted.metric,
        "previous_period": extracted.previous.period,
        "current_period": extracted.current.period,
        "unit": extracted.unit,
        "calculation": {
            key: str(value)
            for key, value in calculation.items()
        },
        "formula": (
            "percentage_change = "
            "(current_value - previous_value) "
            "/ previous_value * 100"
        ),
        "citation": {
            "page_number": extracted.page_number,
        },
    }