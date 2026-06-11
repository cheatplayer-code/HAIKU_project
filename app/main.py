"""Birge API — FastAPI application."""

from fastapi import FastAPI


app = FastAPI(
    title="Birge API",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, object]:
    """Health check endpoint."""
    return {
        "ok": True,
        "service": "birge-api",
        "status": "healthy",
    }
