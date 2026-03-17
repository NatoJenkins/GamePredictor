"""Health check endpoint."""

from fastapi import APIRouter

from api.schemas import HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Return health status for monitoring and Docker health checks."""
    return HealthResponse(status="ok")
