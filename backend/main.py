from io import BytesIO
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from pydantic import BaseModel, Field
from backend.services.embedding_service import create_embeddings , create_embedding
from backend.services.text_chunker import chunk_text
from backend.services.vector_store import (
    check_qdrant_connection,
    search_chunks,
    store_chunks,
)
from backend.services.llm_service import (
    extract_growth_values,
    generate_answer,
)
from decimal import Decimal, InvalidOperation
from backend.services.financial_calculator import calculate_growth
class SearchRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=10)

app = FastAPI(
    title="FinMind AI",
    description="A local API for financial document analysis.",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "FinMind AI backend is running!"}


@app.get("/health")
def health_check():
    try:
        check_qdrant_connection()
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="Qdrant is unavailable.",
        ) from error

    return {
        "status": "healthy",
        "services": {
            "api": "healthy",
            "qdrant": "healthy",
        },
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

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            page_chunks = chunk_text(text)

            for page_chunk_index, chunk in enumerate(page_chunks):
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

class GrowthCalculationRequest(BaseModel):
    previous_value: Decimal
    current_value: Decimal



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

    sources = [
        {
            "page_number": result["page_number"],
            "source": result["source"],
            "score": result["score"],
        }
        for result in results
    ]

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
        or extracted.previous_value is None
        or extracted.current_value is None
    ):
        raise HTTPException(
            status_code=422,
            detail="The required financial values were not found.",
        )

    try:
        previous_value = Decimal(extracted.previous_value)
        current_value = Decimal(extracted.current_value)

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
        "previous_period": extracted.previous_period,
        "current_period": extracted.current_period,
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