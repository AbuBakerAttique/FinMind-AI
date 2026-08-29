
from fastapi import FastAPI, File, HTTPException, UploadFile
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError


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

        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                    "character_count": len(text),
                }
            )

    except PdfReadError:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )

    return {
        "filename": file.filename,
        "total_pages": len(pages),
        "pages": pages,
    }