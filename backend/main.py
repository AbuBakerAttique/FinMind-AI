

from fastapi import FastAPI, File, HTTPException, UploadFile
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


from backend.services.text_chunker import chunk_text

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
    return {"status": "healthy"}

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

    try:
        reader = PdfReader(BytesIO(file_content))
        chunks = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            page_chunks = chunk_text(text)

            for chunk_index, chunk in enumerate(page_chunks):
                chunks.append(
                    {
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                        "text": chunk,
                        "character_count": len(chunk),
                    }
                )
        

    except PdfReadError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )

    return {
        "filename": file.filename,
        "total_pages": len(reader.pages),
        "total_chunks": len(chunks),
        "chunks": chunks,
    }