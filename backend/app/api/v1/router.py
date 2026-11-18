from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.core.config import settings

api_router = APIRouter()


@api_router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Service health check endpoint.
    """
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        project=settings.PROJECT_NAME,
        version="0.1.0"
    )
