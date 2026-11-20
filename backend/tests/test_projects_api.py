"""
Integration Tests for Project Intelligence API Endpoints
Phase 3 | Feature 18: Project Intelligence
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


def create_projects_resume_pdf_bytes() -> bytes:
    """Generates a test PDF resume containing detailed academic, personal, and work projects."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Jane Doe")
    page.insert_text((50, 70), "San Francisco, CA | jane.doe@example.com | github.com/janedoe")
    
    page.insert_text((50, 100), "TECHNICAL SKILLS")
    page.insert_text((50, 115), "Languages & Tools: Python, Go, JavaScript, React, Docker, Redis, PostgreSQL")

    page.insert_text((50, 140), "PROJECTS")

    # Project 1: Cloud Task Orchestrator (Personal / Team)
    page.insert_text((50, 160), "Cloud Task Orchestrator | Python, FastAPI, Docker, Redis (Jan 2023 - Present)")
    page.insert_text((50, 175), "GitHub: https://github.com/janedoe/task-orchestrator | Demo: https://task-orchestrator.demo.app")
    page.insert_text((50, 190), "- Architected distributed job queue processing 50,000 tasks/second across 4 worker nodes.")
    page.insert_text((50, 205), "- Reduced end-to-end task dispatch latency by 45% using Redis streams and async workers.")
    page.insert_text((50, 220), "- Collaborated in a team of 3 developers to configure CI/CD pipeline with Docker and GitHub Actions.")

    # Project 2: Smart Vision Object Tracker (Academic)
    page.insert_text((50, 250), "Smart Vision Object Tracker | PyTorch, OpenCV (Sep 2022 - Dec 2022)")
    page.insert_text((50, 265), "Completed as undergraduate final year capstone project at University.")
    page.insert_text((50, 280), "- Trained YOLOv8 deep learning model achieving 94.2% mAP on custom drone aerial dataset.")
    page.insert_text((50, 295), "- Won 1st prize at College Engineering Capstone Showcase.")

    page.insert_text((50, 325), "PROFESSIONAL EXPERIENCE")
    page.insert_text((50, 340), "Acme Corp | Software Engineer (2023 - Present)")
    page.insert_text((50, 355), "- Developed internal customer analytics dashboard using React and Python.")

    stream = doc.write()
    doc.close()
    return stream


def test_projects_api_full_lifecycle():
    # 1. Upload resume
    pdf_bytes = create_projects_resume_pdf_bytes()
    upload_res = client.post(
        UPLOAD_ENDPOINT,
        files={"file": ("ProjectsResume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    staging_id = upload_res.json()["data"]["upload_id"]

    # 2. Save resume permanently to DB
    save_res = client.post(
        f"{RESUMES_ENDPOINT}/{staging_id}/save",
        json={"user_email": "candidate.projects@nexora.ai"},
    )
    assert save_res.status_code == 201
    resume_id = save_res.json()["data"]["id"]

    # 3. Extract and Structure Projects
    extract_url = f"{RESUMES_ENDPOINT}/{resume_id}/projects/extract"
    extract_res = client.post(extract_url)
    assert extract_res.status_code == 200
    extract_json = extract_res.json()
    assert extract_json["success"] is True
    assert extract_json["total"] >= 1
    projects = extract_json["data"]

    titles = [p["project_title"] for p in projects]
    assert any("Cloud Task Orchestrator" in t for t in titles)

    orchestrator = next(p for p in projects if "Cloud Task Orchestrator" in p["project_title"])
    assert orchestrator["normalized_title"] == "Cloud Task Orchestrator"
    assert orchestrator["confidence"] >= 0.70
    assert len(orchestrator["technologies"]) >= 2
    assert any(tech in ("Python", "FastAPI", "Docker", "Redis") for tech in orchestrator["technologies"])

    # Check external links
    links = orchestrator.get("project_links") or []
    assert len(links) >= 1
    assert any("github.com" in l.get("url", "") for l in links)

    # Check linked canonical skills from Feature #17
    skills = orchestrator.get("skills") or []
    canon_names = {s.get("canonical_name") for s in skills}
    assert "FastAPI" in canon_names or "Docker" in canon_names or "Python" in canon_names

    # 4. GET all projects
    get_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/projects")
    assert get_res.status_code == 200
    get_json = get_res.json()
    assert get_json["success"] is True
    assert get_json["total"] == len(projects)

    # 5. GET Project Summary
    summary_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/projects/summary")
    assert summary_res.status_code == 200
    summary_json = summary_res.json()
    assert summary_json["total_projects"] >= 1
    assert summary_json["unique_technologies_count"] >= 1

    # 6. GET Single Project Details
    proj_id = orchestrator["id"]
    single_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/projects/{proj_id}")
    assert single_res.status_code == 200
    assert single_res.json()["data"]["id"] == proj_id

    # 7. GET Project Canonical Skills
    skills_res = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/projects/{proj_id}/skills")
    assert skills_res.status_code == 200
    assert isinstance(skills_res.json(), list)

    # 8. Update Project Manually
    patch_payload = {
        "project_title": "Enterprise Cloud Task Orchestrator",
        "domain": "Distributed Cloud Infrastructure",
        "team_size": 5,
    }
    patch_res = client.patch(
        f"{RESUMES_ENDPOINT}/{resume_id}/projects/{proj_id}",
        json=patch_payload,
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()["data"]
    assert updated_data["project_title"] == "Enterprise Cloud Task Orchestrator"
    assert updated_data["domain"] == "Distributed Cloud Infrastructure"
    assert updated_data["team_size"] == 5
    assert updated_data["is_manually_edited"] is True

    # 9. Confirm Project
    confirm_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/projects/{proj_id}/confirm",
        json={"notes": "Verified candidate lead role"},
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["data"]["review_status"] == "confirmed"

    # 10. Add Project Manually
    new_proj_payload = {
        "project_title": "Decentralized Identity Protocol",
        "project_category": "open_source",
        "short_description": "Self-sovereign identity verification on EVM chains",
        "domain": "Web3 & Cryptography",
        "technologies": ["Solidity", "TypeScript", "Rust"],
        "team_type": "individual",
    }
    add_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/projects",
        json=new_proj_payload,
    )
    assert add_res.status_code == 201
    created_proj = add_res.json()["data"]
    assert created_proj["project_title"] == "Decentralized Identity Protocol"
    created_id = created_proj["id"]

    # 11. Reprocess Projects (Ensure manual edits are preserved)
    reprocess_res = client.post(
        f"{RESUMES_ENDPOINT}/{resume_id}/projects/reprocess?force_overwrite=false"
    )
    assert reprocess_res.status_code == 200
    reprocessed_projects = reprocess_res.json()["data"]
    reprocessed_titles = {p["project_title"] for p in reprocessed_projects}

    # Edited project must retain edited title because force_overwrite=false
    assert "Enterprise Cloud Task Orchestrator" in reprocessed_titles
    # Manually created project must still exist
    assert "Decentralized Identity Protocol" in reprocessed_titles

    # 12. Delete Project
    del_res = client.delete(f"{RESUMES_ENDPOINT}/{resume_id}/projects/{created_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Check 404 on deleted project
    get_deleted = client.get(f"{RESUMES_ENDPOINT}/{resume_id}/projects/{created_id}")
    assert get_deleted.status_code == 404


def test_projects_api_validation_errors():
    # Invalid UUID format
    bad_res = client.get(f"{RESUMES_ENDPOINT}/not-a-valid-uuid/projects")
    assert bad_res.status_code == 400

    # Nonexistent UUID
    fake_uuid = str(uuid.uuid4())
    not_found_res = client.get(f"{RESUMES_ENDPOINT}/{fake_uuid}/projects")
    assert not_found_res.status_code == 404
