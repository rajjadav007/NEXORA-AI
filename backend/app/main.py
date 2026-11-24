from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import api_router

logger = setup_logging(settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting %s in %s environment", settings.APP_NAME, settings.APP_ENV)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.APP_NAME,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global unhandled exception handler
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception processing request %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # API v1 router
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Direct alias for /api/resumes/... to support unversioned paths (e.g. GET /api/resumes/{id}/analytics/dashboard)
    from app.api.v1.endpoints.analytics import router as direct_analytics_router
    from app.api.v1.endpoints.improvements import router as direct_improvements_router
    from app.api.v1.endpoints.reports import router as direct_reports_router
    application.include_router(direct_analytics_router, prefix="/api/resumes", tags=["Resume Analytics Dashboard Alias"], include_in_schema=False)
    application.include_router(direct_improvements_router, prefix="/api/resumes", tags=["Resume Improvement Tracker Alias"], include_in_schema=False)
    application.include_router(direct_reports_router, prefix="/api/resumes", tags=["AI Resume Report Alias"], include_in_schema=False)

    # Root endpoint
    @application.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.APP_NAME,
            "environment": settings.APP_ENV,
            "status": "online",
            "api_v1": settings.API_V1_PREFIX,
            "docs": "/docs",
        }

    return application


app = create_application()
