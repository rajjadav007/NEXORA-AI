"""
Integration Tests for Job Description Input Endpoints
Phase 6 | Feature 33: Job Description Input
"""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.job_description import JobDescription
from app.models.user import User
from app.schemas.job_description import JD_MIN_LENGTH, JD_MAX_LENGTH

client = TestClient(app)
ENDPOINT = f"{settings.API_V1_PREFIX}/job-descriptions"

VALID_DESCRIPTION = (
    "We are seeking a Backend Engineer to build scalable Python and FastAPI microservices, "
    "design PostgreSQL schemas, and collaborate with product teams on AI-driven workflows."
)


def _cleanup_user(user_id: str) -> None:
    db = SessionLocal()
    try:
        uid = uuid.UUID(user_id)
        jds = db.execute(select(JobDescription).where(JobDescription.user_id == uid)).scalars().all()
        for jd in jds:
            db.delete(jd)
        user = db.execute(select(User).where(User.id == uid)).scalar_one_or_none()
        if user:
            db.delete(user)
        db.commit()
    finally:
        db.close()


def test_create_valid_job_description_and_db_persistence():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}
    payload = {
        "job_title": "Senior Backend Engineer",
        "company_name": "Nexora Labs",
        "description": VALID_DESCRIPTION,
        "location": "San Francisco, CA (Hybrid)",
        "employment_type": "Full-time",
    }

    try:
        res = client.post(ENDPOINT, json=payload, headers=headers)
        assert res.status_code == 201, res.text
        body = res.json()
        assert body["success"] is True
        data = body["data"]
        assert data["job_title"] == "Senior Backend Engineer"
        assert data["company_name"] == "Nexora Labs"
        assert data["description"] == VALID_DESCRIPTION
        assert data["character_count"] == len(VALID_DESCRIPTION)
        assert data["location"] == "San Francisco, CA (Hybrid)"
        assert data["employment_type"] == "Full-time"
        assert data["source_type"] == "manual"
        assert data["analysis_status"] == "PENDING"
        assert data["user_id"] == user_id

        # Verify database persistence directly
        db = SessionLocal()
        try:
            record = db.execute(
                select(JobDescription).where(JobDescription.id == uuid.UUID(data["id"]))
            ).scalar_one_or_none()
            assert record is not None
            assert record.raw_description == VALID_DESCRIPTION
            assert record.requirements == []
            assert record.mandatory_skills == []
            assert record.preferred_skills == []
        finally:
            db.close()

        # Verify GET detail & list
        detail_res = client.get(f"{ENDPOINT}/{data['id']}", headers=headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["data"]["id"] == data["id"]

        list_res = client.get(ENDPOINT, headers=headers)
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 1
    finally:
        _cleanup_user(user_id)


def test_create_job_description_missing_optional_fields():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}
    payload = {
        "job_title": "AI Engineer",
        "company_name": "OpenTech",
        "description": VALID_DESCRIPTION,
    }

    try:
        res = client.post(ENDPOINT, json=payload, headers=headers)
        assert res.status_code == 201, res.text
        data = res.json()["data"]
        assert data["location"] is None
        assert data["employment_type"] is None
    finally:
        _cleanup_user(user_id)


def test_empty_and_whitespace_job_description_rejected():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    for bad_desc in ["", "   \n\t  "]:
        res = client.post(
            ENDPOINT,
            json={
                "job_title": "Data Scientist",
                "company_name": "Acme",
                "description": bad_desc,
            },
            headers=headers,
        )
        assert res.status_code == 422


def test_character_limits_validation():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    try:
        # Below minimum
        too_short = "x" * (JD_MIN_LENGTH - 1)
        res_short = client.post(
            ENDPOINT,
            json={
                "job_title": "Software Engineer",
                "company_name": "Acme",
                "description": too_short,
            },
            headers=headers,
        )
        assert res_short.status_code == 422

        # Above maximum
        too_long = "x" * (JD_MAX_LENGTH + 1)
        res_long = client.post(
            ENDPOINT,
            json={
                "job_title": "Software Engineer",
                "company_name": "Acme",
                "description": too_long,
            },
            headers=headers,
        )
        assert res_long.status_code == 422

        # Exact minimum passes
        exact_min = "a" * JD_MIN_LENGTH
        res_min = client.post(
            ENDPOINT,
            json={
                "job_title": "Software Engineer",
                "company_name": "Acme",
                "description": exact_min,
            },
            headers=headers,
        )
        assert res_min.status_code == 201
    finally:
        _cleanup_user(user_id)


def test_invalid_input_fields_rejected():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    # Invalid employment_type
    res_type = client.post(
        ENDPOINT,
        json={
            "job_title": "Software Engineer",
            "company_name": "Acme",
            "description": VALID_DESCRIPTION,
            "employment_type": "InvalidType",
        },
        headers=headers,
    )
    assert res_type.status_code == 422

    # Missing required job_title
    res_missing = client.post(
        ENDPOINT,
        json={
            "company_name": "Acme",
            "description": VALID_DESCRIPTION,
        },
        headers=headers,
    )
    assert res_missing.status_code == 422


def test_duplicate_submission_prevented():
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    payload = {
        "job_title": "Platform Engineer",
        "company_name": "CloudCorp",
        "description": VALID_DESCRIPTION,
    }

    try:
        res1 = client.post(ENDPOINT, json=payload, headers={"X-User-Id": user_a})
        assert res1.status_code == 201

        # Same user, same content -> 409 Conflict
        res_dup = client.post(ENDPOINT, json=payload, headers={"X-User-Id": user_a})
        assert res_dup.status_code == 409
        assert "already been saved" in res_dup.json()["detail"].lower()

        # Different user, same content -> 201 Created
        res_other = client.post(ENDPOINT, json=payload, headers={"X-User-Id": user_b})
        assert res_other.status_code == 201
    finally:
        _cleanup_user(user_a)
        _cleanup_user(user_b)


def test_user_authorization_and_error_handling():
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())

    try:
        # Unauthenticated request -> 401
        res_unauth = client.post(
            ENDPOINT,
            json={
                "job_title": "ML Engineer",
                "company_name": "AI Inc",
                "description": VALID_DESCRIPTION,
            },
        )
        assert res_unauth.status_code == 401
        assert client.get(ENDPOINT).status_code == 401

        # Invalid user UUID -> 400
        assert client.get(ENDPOINT, headers={"X-User-Id": "not-a-uuid"}).status_code == 400

        # Create as user A
        create_res = client.post(
            ENDPOINT,
            json={
                "job_title": "ML Engineer",
                "company_name": "AI Inc",
                "description": VALID_DESCRIPTION,
            },
            headers={"X-User-Id": user_a},
        )
        assert create_res.status_code == 201
        jd_id = create_res.json()["data"]["id"]

        # User B cannot see user A's JD in list
        list_b = client.get(ENDPOINT, headers={"X-User-Id": user_b})
        assert list_b.status_code == 200
        assert list_b.json()["total"] == 0

        # User B gets 403 on detail and delete
        assert client.get(f"{ENDPOINT}/{jd_id}", headers={"X-User-Id": user_b}).status_code == 403
        assert client.delete(f"{ENDPOINT}/{jd_id}", headers={"X-User-Id": user_b}).status_code == 403

        # Invalid JD ID -> 400; nonexistent JD ID -> 404
        assert client.get(f"{ENDPOINT}/invalid-id", headers={"X-User-Id": user_a}).status_code == 400
        assert client.get(f"{ENDPOINT}/{uuid.uuid4()}", headers={"X-User-Id": user_a}).status_code == 404

        # Owner can delete
        del_res = client.delete(f"{ENDPOINT}/{jd_id}", headers={"X-User-Id": user_a})
        assert del_res.status_code == 200
        assert client.get(f"{ENDPOINT}/{jd_id}", headers={"X-User-Id": user_a}).status_code == 404
    finally:
        _cleanup_user(user_a)
        _cleanup_user(user_b)
