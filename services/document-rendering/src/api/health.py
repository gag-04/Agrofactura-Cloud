"""Health probe router for Cloud Native orchestrators."""

from datetime import datetime, timezone

from fastapi import APIRouter

from src.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Healthcheck probe endpoint."""
    return HealthResponse(
        status="healthy",
        service="document-rendering-service",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
