"""
Integration Tests for Skill Normalization API Endpoints
Phase 3 | Feature 17: Skill Normalization
"""

import io
import uuid
import pytest
import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)
UPLOAD_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes/upload"
RESUMES_ENDPOINT = f"{settings.API_V1_PREFIX}/resumes"
SKILLS_DICT_ENDPOINT = f"{settings.API_V1_PREFIX}/skills/dictionary"


def create_skills_resume_pdf_bytes() -> bytes:
    """Generates a test PDF resume containing skills and evidence."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Doe")
    page.insert_text((50, 70), "San Francisco, CA | jane.doe@example.com")
    page.insert_text((50, 100), "TECHNICAL SKILLS")
    page.insert_text((50, 120), "Programming Languages: JS, JavaScript, Python, C++, Java")
    page.insert_text((50, 140), "Frameworks: ReactJS, React Native, FastAPI, PyTorch")
    page.insert_text((50, 160), "Databases: Postgre SQL, Redis, MongoDB")
    page.insert_text((50, 180), "Cloud & DevOps: Docker, K8s, AWS")
    page.insert_text((50, 200), "AI & ML: ML, NLP, LLM, Deep Learning")
    page.insert_text((50, 230), "PROFESSIONAL EXPERIENCE")
    page.insert_text((50, 250), "Acme Corp | Senior Software Engineer")
    page.insert_text((50, 270), "- Architected backend services in Python and FastAPI")
    page.insert_text((50, 290), "- Built frontend micro-apps with React")
    stream = doc.write()
    doc.close()
    return stream


def test_skills_api_full_lifecycle():
    # 1. Upload resume
    pdf_bytes = create_skills_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("SkillsResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    staging_id = upload_res.json()["data"]["upload_id"]

    # 2. Save resume permanently to DB
    save_res = client.post(
        f"{RESUMES_ENDPOINT}/{staging_id}/save",
        json={"user_email": "candidate.skills@nexora.ai"},
    )
    assert save_res.status_code == 201
    resume_id = save_res.json()["data"]["id"]

    # 2. Extract and Normalize Skills
    extract_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills/extract"
    extract_res = client.post(extract_url)
    assert extract_res.status_code == 200
    extract_json = extract_res.json()
    assert extract_json["success"] is True
    assert extract_json["total"] > 0
    skills = extract_json["data"]

    canonical_names = {s["canonical_name"] for s in skills}
    # Check alias normalization
    assert "JavaScript" in canonical_names
    assert "FastAPI" in canonical_names
    assert "Docker" in canonical_names
    assert "Kubernetes" in canonical_names  # K8s normalized to Kubernetes
    assert "PostgreSQL" in canonical_names  # Postgre SQL normalized to PostgreSQL
    assert "Machine Learning" in canonical_names  # ML normalized

    # Check false-merge prevention
    assert "Java" in canonical_names
    assert "React" in canonical_names
    assert "React Native" in canonical_names
    assert "Python" in canonical_names
    assert "PyTorch" in canonical_names

    # Check that Java and JavaScript remain separate
    assert "Java" in canonical_names and "JavaScript" in canonical_names

    # 3. Retrieve Normalized Skills
    get_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills"
    get_res = client.get(get_url)
    assert get_res.status_code == 200
    assert len(get_res.json()["data"]) == len(skills)

    # 4. Summary Endpoint
    summary_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills/summary"
    sum_res = client.get(summary_url)
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["total_normalized_skills"] > 0
    assert "category_distribution" in sum_data

    # 5. Direct Normalize Endpoint
    direct_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills/normalize"
    direct_res = client.post(
        direct_url,
        json={"skills": ["JS", "Javascript", "ML", "K8s", "ReactJS", "ReactNative"]},
    )
    assert direct_res.status_code == 200
    direct_skills = {s["canonical_name"] for s in direct_res.json()["data"]}
    assert "JavaScript" in direct_skills
    assert "Machine Learning" in direct_skills
    assert "Kubernetes" in direct_skills
    assert "React" in direct_skills
    assert "React Native" in direct_skills

    # 6. Manual Update
    target_skill = skills[0]
    skill_id = target_skill["id"] or target_skill["canonical_name"]
    patch_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills/{skill_id}"
    patch_res = client.patch(patch_url, json={"category": "Expertise"})
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["category"] == "Expertise"
    assert patch_res.json()["data"]["is_manually_edited"] is True

    # 7. Confirm and Reject Endpoints
    confirm_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills/{skill_id}/confirm"
    conf_res = client.post(confirm_url)
    assert conf_res.status_code == 200
    assert conf_res.json()["data"]["normalization_status"] == "confirmed"

    reject_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills/{skill_id}/reject"
    rej_res = client.post(reject_url)
    assert rej_res.status_code == 200
    assert rej_res.json()["data"]["normalization_status"] == "rejected"

    # 8. Reprocess Endpoint (Preserves manual edits)
    reprocess_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills/reprocess?force_overwrite=false"
    reprocess_res = client.post(reprocess_url)
    assert reprocess_res.status_code == 200

    # 9. Delete Skill
    current_skills = client.get(get_url).json()["data"]
    assert len(current_skills) > 0
    delete_target_id = current_skills[0]["id"]
    delete_url = f"{RESUMES_ENDPOINT}/{resume_id}/skills/{delete_target_id}"
    del_res = client.delete(delete_url)
    assert del_res.status_code == 200


def test_global_dictionary_endpoints():
    # 1. Get Dictionary
    dict_res = client.get(SKILLS_DICT_ENDPOINT)
    assert dict_res.status_code == 200
    dict_json = dict_res.json()
    assert dict_json["success"] is True
    assert dict_json["version"] == "1.0.0"
    assert dict_json["total"] > 50

    # 2. Add New Alias
    alias_url = f"{SKILLS_DICT_ENDPOINT}/alias"
    add_res = client.post(
        alias_url,
        json={"canonical_name": "Python", "alias": "python-core-3"},
    )
    assert add_res.status_code == 201

    # 3. Reject Conflicting Alias
    conflict_res = client.post(
        alias_url,
        json={"canonical_name": "Java", "alias": "JS"},  # JS is already JavaScript
    )
    assert conflict_res.status_code == 400
