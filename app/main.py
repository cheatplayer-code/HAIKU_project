"""Birge API — FastAPI application."""

from fastapi import FastAPI

from app.api.routes import router as api_router


app = FastAPI(
    title="Birge API",
    version="0.1.0",
)

app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, object]:
    """Health check endpoint."""
    return {
        "ok": True,
        "service": "birge-api",
        "status": "healthy",
    }
