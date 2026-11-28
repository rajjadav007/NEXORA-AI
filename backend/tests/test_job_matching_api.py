"""
Integration & Unit Tests for Resume-to-Job Matching Engine
Phase 7 | Feature 39: Resume-to-Job Matching Engine
"""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.database.session import SessionLocal
from app.main import app
from app.models.certifications import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.job_requirement_analysis import JobRequirementAnalysis
from app.models.job_skill_classification import JobSkillClassification
from app.models.project import Project
from app.models.resume import Resume
from app.models.skills import ResumeSkill
from app.models.user import User

client = TestClient(app)
MATCH_ENDPOINT = f"{settings.API_V1_PREFIX}/job-matches"
JD_ENDPOINT = f"{settings.API_V1_PREFIX}/job-descriptions"


def _cleanup_user(user_id: str) -> None:
    db = SessionLocal()
    try:
        uid = uuid.UUID(user_id)
        for model in (
            JobMatch,
            JobSkillClassification,
            JobRequirementAnalysis,
            JobDescription,
            Certification,
            Project,
            Education,
            Experience,
            ResumeSkill,
            Resume,
        ):
            rows = db.execute(select(model).where(model.user_id == uid)).scalars().all()
            for row in rows:
                db.delete(row)
        user = db.execute(select(User).where(User.id == uid)).scalar_one_or_none()
        if user:
            db.delete(user)
        db.commit()
    finally:
        db.close()


def _seed_user(user_id: str) -> uuid.UUID:
    uid = uuid.UUID(user_id)
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.id == uid)).scalar_one_or_none()
        if not user:
            db.add(User(id=uid, email=f"test_{user_id[:8]}@nexora.local"))
            db.commit()
        return uid
    finally:
        db.close()


def _seed_resume(
    user_id: str,
    with_skills: bool = True,
    with_experience: bool = True,
    with_education: bool = True,
    with_projects: bool = True,
    exp_months: int = 36,
) -> str:
    uid = _seed_user(user_id)
    db = SessionLocal()
    try:
        resume = Resume(
            user_id=uid,
            original_filename="candidate_resume.pdf",
            storage_key=f"test/{uuid.uuid4()}.pdf",
            file_type="pdf",
            file_size=12345,
            processing_status="COMPLETED",
        )
        db.add(resume)
        db.flush()

        if with_skills:
            db.add_all(
                [
                    ResumeSkill(
                        resume_id=resume.id,
                        user_id=uid,
                        original_name="Python",
                        canonical_name="Python",
                        category="Programming Language",
                        source_sections=["skills", "experience"],
                        source_evidence=["Built backend services in Python"],
                    ),
                    ResumeSkill(
                        resume_id=resume.id,
                        user_id=uid,
                        original_name="MySQL",
                        canonical_name="MySQL",
                        category="Database",
                        source_sections=["skills"],
                        source_evidence=["Managed MySQL databases"],
                    ),
                ]
            )

        if with_experience:
            db.add(
                Experience(
                    resume_id=resume.id,
                    user_id=uid,
                    company="Acme Tech",
                    job_title="Backend Engineer",
                    duration_months=exp_months,
                    technologies=["Python", "FastAPI"],
                    responsibilities=["Designed REST APIs and microservices"],
                )
            )

        if with_education:
            db.add(
                Education(
                    resume_id=resume.id,
                    user_id=uid,
                    degree="B.Tech in Computer Science",
                    normalized_degree="Bachelor of Technology",
                    degree_level="undergraduate",
                    field_of_study="Computer Science",
                    institution="State University",
                )
            )

        if with_projects:
            db.add(
                Project(
                    resume_id=resume.id,
                    user_id=uid,
                    project_title="Distributed Kubernetes Orchestrator",
                    normalized_title="distributed kubernetes orchestrator",
                    project_category="personal",
                    short_description="Built a Python automation dashboard",
                    technologies=["Python", "FastAPI"],
                )
            )

        db.commit()
        return str(resume.id)
    finally:
        db.close()


def _seed_jd(
    user_id: str,
    with_analysis: bool = True,
    with_education_req: bool = True,
    min_years: int = 2,
    skills: list | None = None,
    job_title: str = "Senior Backend Engineer",
) -> str:
    res = client.post(
        JD_ENDPOINT,
        json={
            "job_title": job_title,
            "company_name": "Nexora Labs",
            "description": (
                "We need a Backend Engineer with Python, PostgreSQL, and Docker. "
                "Bachelor's degree in Computer Science required. 2+ years of experience."
            ),
        },
        headers={"X-User-Id": user_id},
    )
    assert res.status_code == 201, res.text
    jd_id = res.json()["data"]["id"]

    if with_analysis:
        uid = uuid.UUID(user_id)
        db = SessionLocal()
        try:
            tech_skills = skills or [
                {"name": "Python", "category": "Programming Language", "importance": "Mandatory"},
                {"name": "PostgreSQL", "category": "Database", "importance": "Mandatory"},
                {"name": "Docker", "category": "Tool & Platform", "importance": "Preferred"},
                {"name": "Kubernetes", "category": "Tool & Platform", "importance": "Optional"},
            ]
            edu_payload = (
                {
                    "minimum_level": "Bachelor",
                    "required_degree": "Bachelor's degree",
                    "required_fields": ["Computer Science"],
                    "required_certifications": [],
                    "preferred_certifications": [],
                }
                if with_education_req
                else {
                    "minimum_level": None,
                    "required_degree": None,
                    "required_fields": [],
                    "required_certifications": [],
                    "preferred_certifications": [],
                }
            )
            db.add(
                JobRequirementAnalysis(
                    job_description_id=uuid.UUID(jd_id),
                    user_id=uid,
                    technical_skills=tech_skills,
                    education=edu_payload,
                    experience={"minimum_years": min_years, "fresher_eligible": False},
                    soft_skills=[{"name": "Executive stakeholder alignment", "category": "Soft Skill", "importance": "Preferred"}],
                    domain_knowledge=[],
                    other_requirements=[],
                    content_hash="hash-req",
                    analysis_metadata={"model_used": "test"},
                )
            )
            db.add(
                JobSkillClassification(
                    job_description_id=uuid.UUID(jd_id),
                    user_id=uid,
                    classification_summary={"mandatory_count": 2, "preferred_count": 1, "optional_count": 1},
                    skills=[
                        {"name": s["name"], "category": s["category"], "classification": s["importance"]}
                        for s in tech_skills
                    ],
                    content_hash="hash-cls",
                    analysis_metadata={"model_used": "test"},
                )
            )
            db.commit()
        finally:
            db.close()

    return jd_id


def test_successful_match_categories_and_no_title_assumption():
    user_id = str(uuid.uuid4())
    try:
        resume_id = _seed_resume(user_id)
        jd_id = _seed_jd(user_id)

        res = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": resume_id, "job_description_id": jd_id},
            headers={"X-User-Id": user_id},
        )
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["success"] is True
        data = body["data"]

        assert 0 <= data["overall_match_score"] <= 100
        assert data["cached"] is False
        assert data["version_number"] == 1

        # Python is Matched; PostgreSQL is Partially Matched (MySQL is in Database category);
        # Docker & Kubernetes are Missing (even though project title has "Kubernetes"!).
        matched_names = {s["requirement"] for s in data["matching_skills"]}
        partial_names = {s["requirement"] for s in data["partially_matching_skills"]}
        missing_names = {s["requirement"] for s in data["missing_skills"]}
        not_verifiable_names = {r["requirement"] for r in data["not_verifiable_requirements"]}

        assert "Python" in matched_names
        assert "PostgreSQL" in partial_names
        assert "Docker" in missing_names
        assert "Kubernetes" in missing_names
        assert "Executive stakeholder alignment" in not_verifiable_names

        assert data["experience_match"]["status"] == "Matched"
        assert data["education_match"]["status"] == "Matched"
        assert len(data["relevant_projects"]) == 1
        assert len(data["strengths"]) >= 1
        assert len(data["improvement_areas"]) >= 1
    finally:
        _cleanup_user(user_id)


def test_unavailable_categories_normalized_without_penalty():
    user_id = str(uuid.uuid4())
    try:
        # Resume with skills and experience, but NO education & NO projects
        resume_id = _seed_resume(
            user_id,
            with_skills=True,
            with_experience=True,
            with_education=False,
            with_projects=False,
            exp_months=48,
        )
        # Job requires Python (Matched) and 2+ years exp (Matched), plus Bachelor's (Not Verifiable due to no edu records)
        jd_id = _seed_jd(
            user_id,
            with_education_req=True,
            min_years=2,
            skills=[{"name": "Python", "category": "Programming Language", "importance": "Mandatory"}],
        )

        res = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": resume_id, "job_description_id": jd_id},
            headers={"X-User-Id": user_id},
        )
        assert res.status_code == 200, res.text
        data = res.json()["data"]

        # Both available categories (technical_skills=100, relevant_experience=100) normalize to 100.0
        # without penalizing for unavailable education/projects!
        assert data["overall_match_score"] == 100.0
        assert data["education_match"]["status"] == "Not Verifiable"
        assert data["score_breakdown"]["categories"]["education"]["available"] is False
        assert data["score_breakdown"]["categories"]["projects"]["available"] is False
    finally:
        _cleanup_user(user_id)


def test_missing_prerequisites_return_422():
    user_id = str(uuid.uuid4())
    try:
        empty_resume_id = _seed_resume(
            user_id,
            with_skills=False,
            with_experience=False,
            with_education=False,
            with_projects=False,
        )
        analyzed_resume_id = _seed_resume(user_id)
        unanalyzed_jd_id = _seed_jd(user_id, with_analysis=False, job_title="Unanalyzed Role")
        analyzed_jd_id = _seed_jd(user_id, with_analysis=True, job_title="Analyzed Role")

        # Missing resume analysis
        res1 = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": empty_resume_id, "job_description_id": analyzed_jd_id},
            headers={"X-User-Id": user_id},
        )
        assert res1.status_code == 422

        # Missing job analysis
        res2 = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": analyzed_resume_id, "job_description_id": unanalyzed_jd_id},
            headers={"X-User-Id": user_id},
        )
        assert res2.status_code == 422
    finally:
        _cleanup_user(user_id)


def test_invalid_ids_and_unauthorized_access():
    owner_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    try:
        resume_id = _seed_resume(owner_id)
        jd_id = _seed_jd(owner_id)

        # Missing auth
        no_auth = client.post(MATCH_ENDPOINT, json={"resume_id": resume_id, "job_description_id": jd_id})
        assert no_auth.status_code == 401

        # Invalid resume ID format & nonexistent UUID
        bad_res = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": "not-a-uuid", "job_description_id": jd_id},
            headers={"X-User-Id": owner_id},
        )
        assert bad_res.status_code == 400

        missing_res = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": str(uuid.uuid4()), "job_description_id": jd_id},
            headers={"X-User-Id": owner_id},
        )
        assert missing_res.status_code == 404

        # Invalid job ID format & nonexistent UUID
        bad_jd = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": resume_id, "job_description_id": "../etc"},
            headers={"X-User-Id": owner_id},
        )
        assert bad_jd.status_code == 400

        missing_jd = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": resume_id, "job_description_id": str(uuid.uuid4())},
            headers={"X-User-Id": owner_id},
        )
        assert missing_jd.status_code == 404

        # Unauthorized user attempting to match owner's resume
        unauth = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": resume_id, "job_description_id": jd_id},
            headers={"X-User-Id": other_id},
        )
        assert unauth.status_code == 403
    finally:
        _cleanup_user(owner_id)
        _cleanup_user(other_id)


def test_persistence_caching_and_regeneration():
    user_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    try:
        resume_id = _seed_resume(user_id)
        jd_id = _seed_jd(user_id)

        # 1. Create
        res1 = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": resume_id, "job_description_id": jd_id},
            headers={"X-User-Id": user_id},
        )
        assert res1.status_code == 200
        match_id = res1.json()["data"]["id"]

        # 2. Repeated call returns cached without duplicate row
        res2 = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": resume_id, "job_description_id": jd_id},
            headers={"X-User-Id": user_id},
        )
        assert res2.status_code == 200
        assert res2.json()["data"]["id"] == match_id
        assert res2.json()["data"]["cached"] is True
        assert res2.json()["data"]["version_number"] == 1

        # 3. Regenerate updates same row and increments version
        res3 = client.post(
            MATCH_ENDPOINT,
            json={"resume_id": resume_id, "job_description_id": jd_id, "regenerate": True},
            headers={"X-User-Id": user_id},
        )
        assert res3.status_code == 200
        assert res3.json()["data"]["id"] == match_id
        assert res3.json()["data"]["cached"] is False
        assert res3.json()["data"]["version_number"] == 2

        # 4. Retrieve by ID & list
        get_res = client.get(f"{MATCH_ENDPOINT}/{match_id}", headers={"X-User-Id": user_id})
        assert get_res.status_code == 200
        assert get_res.json()["data"]["id"] == match_id

        list_res = client.get(MATCH_ENDPOINT, headers={"X-User-Id": user_id})
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 1

        # 5. Other user cannot GET match
        unauth_get = client.get(f"{MATCH_ENDPOINT}/{match_id}", headers={"X-User-Id": other_id})
        assert unauth_get.status_code == 403
    finally:
        _cleanup_user(user_id)
        _cleanup_user(other_id)
