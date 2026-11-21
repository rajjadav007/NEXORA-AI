from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.resumes import router as resumes_router
from app.api.v1.endpoints.personal_info import router as personal_info_router
from app.api.v1.endpoints.education import router as education_router
from app.api.v1.endpoints.experience import router as experience_router
from app.api.v1.endpoints.skills import router as skills_router, dict_router as skills_dict_router
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.certifications import router as certifications_router
from app.api.v1.endpoints.quality_score import router as quality_score_router
from app.api.v1.endpoints.strength_analysis import router as strength_analysis_router
from app.api.v1.endpoints.weakness_analysis import router as weakness_analysis_router
from app.api.v1.endpoints.ats_analysis import router as ats_analysis_router
from app.api.v1.endpoints.grammar_analysis import router as grammar_analysis_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(resumes_router, prefix="/resumes", tags=["Resumes"])
api_router.include_router(personal_info_router, prefix="/resumes", tags=["Personal Information"])
api_router.include_router(education_router, prefix="/resumes", tags=["Education Analysis"])
api_router.include_router(experience_router, prefix="/resumes", tags=["Experience Analysis"])
api_router.include_router(skills_router, prefix="/resumes", tags=["Skill Normalization"])
api_router.include_router(skills_dict_router, prefix="/skills", tags=["Skill Dictionary"])
api_router.include_router(projects_router, prefix="/resumes", tags=["Project Intelligence"])
api_router.include_router(certifications_router, prefix="/resumes", tags=["Certifications & Achievements"])
api_router.include_router(quality_score_router, prefix="/resumes", tags=["Resume Quality Score"])
api_router.include_router(strength_analysis_router, prefix="/resumes", tags=["Resume Strength Analysis"])
api_router.include_router(weakness_analysis_router, prefix="/resumes", tags=["Resume Weakness Analysis"])
api_router.include_router(ats_analysis_router, prefix="/resumes", tags=["Resume ATS Compatibility Analysis"])
api_router.include_router(grammar_analysis_router, prefix="/resumes", tags=["Resume Grammar & Clarity Analysis"])
