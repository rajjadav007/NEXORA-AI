from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.resumes import router as resumes_router
from app.api.v1.endpoints.personal_info import router as personal_info_router
from app.api.v1.endpoints.education import router as education_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(resumes_router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(personal_info_router, prefix="/resumes", tags=["Personal Information"])
api_router.include_router(education_router, prefix="/resumes", tags=["Education Analysis"])
