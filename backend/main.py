from fastapi import FastAPI

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