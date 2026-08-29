

from fastapi import FastAPI, File, HTTPException, UploadFile
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from uuid import uuid4

from backend.services.text_chunker import chunk_text
from backend.services.vector_store import check_qdrant_connection



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
                        "id": f"{document_id}-{global_chunk_index}",
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