
from fastapi import FastAPI

app = FastAPI(
    title="Offer Evidence Verifier",
    description="Evidence-based internship and job offer verification API",
    version="0.1.0"
)

@app.get("/")
def home():
    return {
        "message": "Offer Evidence Verifier API is running",
        "status": "success"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0"
    }
