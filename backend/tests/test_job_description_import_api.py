"""
Integration & Unit Tests for Job Description URL Import
Phase 6 | Feature 34: Job Description URL Import
"""

import json
import uuid
from contextlib import asynccontextmanager
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.database.session import SessionLocal
from app.main import app
from app.models.job_description import JobDescription
from app.models.user import User

client = TestClient(app)
BASE_ENDPOINT = f"{settings.API_V1_PREFIX}/job-descriptions"
IMPORT_ENDPOINT = f"{BASE_ENDPOINT}/import"


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


class _MockStreamResponse:
    def __init__(self, status_code=200, headers=None, chunks=None, encoding="utf-8"):
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html; charset=utf-8"}
        self._chunks = chunks if chunks is not None else [b""]
        self.encoding = encoding

    async def aiter_bytes(self):
        for c in self._chunks:
            yield c


class _MockAsyncClient:
    def __init__(self, handler):
        self._handler = handler

    @asynccontextmanager
    async def stream(self, method, url):
        res = self._handler(method, url)
        if isinstance(res, Exception):
            raise res
        yield res

    async def aclose(self):
        return None


def _public_dns_mock(host, *args, **kwargs):
    return [(2, 1, 6, "", ("93.184.216.34", 0))]


def test_import_valid_public_url_jsonld_and_save_persistence():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}
    jsonld = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": "Senior Python Engineer",
        "hiringOrganization": {"@type": "Organization", "name": "Acme Robotics"},
        "jobLocation": {"@type": "Place", "address": {"addressLocality": "Austin", "addressRegion": "TX"}},
        "employmentType": "FULL_TIME",
        "experienceRequirements": "5+ years of backend engineering experience",
        "baseSalary": {
            "@type": "MonetaryAmount",
            "currency": "USD",
            "value": {"minValue": 140000, "maxValue": 175000, "unitText": "YEAR"},
        },
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "qualifications": ["Docker", "Kubernetes"],
        "description": (
            "<p>Build resilient microservices with <strong>Python</strong> and FastAPI.</p>"
            "<img src=x onerror=alert('xss') />"
            "<p>Collaborate across teams to ship reliable career intelligence features.</p>"
        ),
    }
    html = f"""
    <html>
      <head>
        <title>Senior Python Engineer - Acme Robotics</title>
        <script type="application/ld+json">{json.dumps(jsonld)}</script>
      </head>
      <body><script>evil()</script><h1>Senior Python Engineer</h1></body>
    </html>
    """.encode("utf-8")

    mock_client = _MockAsyncClient(lambda m, u: _MockStreamResponse(200, chunks=[html]))

    try:
        with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock), \
             patch("app.services.job_import.fetcher.httpx.AsyncClient", return_value=mock_client):
            imp_res = client.post(
                IMPORT_ENDPOINT,
                json={"url": "https://careers.acmerobotics.com/jobs/senior-python"},
                headers=headers,
            )
        assert imp_res.status_code == 200, imp_res.text
        preview = imp_res.json()["data"]
        assert preview["job_title"] == "Senior Python Engineer"
        assert preview["company_name"] == "Acme Robotics"
        assert preview["location"] == "Austin, TX"
        assert preview["employment_type"] == "Full-time"
        assert preview["salary_info"] == "USD 140000 - 175000 / year"
        assert "5+ years" in preview["experience_required"]
        assert "alert('xss')" not in preview["description"]
        assert preview["required_skills"] == ["Python", "FastAPI", "PostgreSQL"]
        assert preview["preferred_skills"] == ["Docker", "Kubernetes"]

        # Persist edited preview via existing Feature #33 endpoint
        with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock):
            save_res = client.post(
                BASE_ENDPOINT,
                json={
                    "job_title": preview["job_title"],
                    "company_name": preview["company_name"],
                    "location": preview["location"],
                    "employment_type": preview["employment_type"],
                    "description": preview["description"],
                    "source_url": preview["source_url"],
                    "source_type": "url",
                    "experience_required": preview["experience_required"],
                    "salary_info": preview["salary_info"],
                    "mandatory_skills": preview["required_skills"],
                    "preferred_skills": preview["preferred_skills"],
                },
                headers=headers,
            )
        assert save_res.status_code == 201, save_res.text
        saved = save_res.json()["data"]
        assert saved["source_type"] == "url"
        assert saved["source_url"] == "https://careers.acmerobotics.com/jobs/senior-python"
        assert saved["salary_info"] == "USD 140000 - 175000 / year"

        db = SessionLocal()
        try:
            row = db.execute(select(JobDescription).where(JobDescription.id == uuid.UUID(saved["id"]))).scalar_one()
            assert row.source_type == "url"
            assert row.salary_info == "USD 140000 - 175000 / year"
            assert row.mandatory_skills == ["Python", "FastAPI", "PostgreSQL"]
        finally:
            db.close()
    finally:
        _cleanup_user(user_id)


def test_import_invalid_and_unsupported_urls():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    for bad_url in [
        "not-a-url",
        "ftp://example.com/job",
        "javascript:alert(1)",
        "https://user:pass@example.com/job",
        "https://example.com:8080/job",
    ]:
        res = client.post(IMPORT_ENDPOINT, json={"url": bad_url}, headers=headers)
        assert res.status_code == 400, f"Expected 400 for {bad_url}, got {res.status_code}"

    res_unsupported = client.post(
        IMPORT_ENDPOINT,
        json={"url": "https://www.youtube.com/watch?v=123"},
        headers=headers,
    )
    assert res_unsupported.status_code == 422
    assert "unsupported" in res_unsupported.json()["detail"].lower()


def test_import_ssrf_private_ip_localhost_and_metadata_blocked():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    for ssrf_url in [
        "http://localhost/admin",
        "http://127.0.0.1/secret",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/internal",
        "http://192.168.1.10/config",
        "http://internal.service.local/api",
    ]:
        res = client.post(IMPORT_ENDPOINT, json={"url": ssrf_url}, headers=headers)
        assert res.status_code == 400, f"Expected 400 SSRF block for {ssrf_url}, got {res.status_code}"

    # DNS resolving to private IP
    with patch(
        "app.services.job_import.fetcher.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("127.0.0.1", 0))],
    ):
        res_dns = client.post(
            IMPORT_ENDPOINT,
            json={"url": "https://rebind.example.com/job"},
            headers=headers,
        )
        assert res_dns.status_code == 400


def test_import_redirect_to_private_ip_blocked():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    mock_client = _MockAsyncClient(
        lambda m, u: _MockStreamResponse(
            status_code=302,
            headers={"location": "http://127.0.0.1/internal-admin"},
        )
    )

    with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock), \
         patch("app.services.job_import.fetcher.httpx.AsyncClient", return_value=mock_client):
        res = client.post(
            IMPORT_ENDPOINT,
            json={"url": "https://careers.example.com/redirect"},
            headers=headers,
        )
    assert res.status_code == 400
    assert "private" in res.json()["detail"].lower() or "localhost" in res.json()["detail"].lower()


def test_import_inaccessible_timeout_and_captcha_pages():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    # 403 Forbidden
    with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock), \
         patch(
             "app.services.job_import.fetcher.httpx.AsyncClient",
             return_value=_MockAsyncClient(lambda m, u: _MockStreamResponse(status_code=403)),
         ):
        res_403 = client.post(IMPORT_ENDPOINT, json={"url": "https://www.linkedin.com/jobs/view/123"}, headers=headers)
        assert res_403.status_code == 422

    # Timeout
    with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock), \
         patch(
             "app.services.job_import.fetcher.httpx.AsyncClient",
             return_value=_MockAsyncClient(lambda m, u: httpx.ReadTimeout("timed out")),
         ):
        res_timeout = client.post(IMPORT_ENDPOINT, json={"url": "https://www.indeed.com/viewjob?jk=1"}, headers=headers)
        assert res_timeout.status_code == 504

    # CAPTCHA wall
    captcha_html = b"<html><title>Security Check</title><body>Please verify you are human (cf-turnstile)</body></html>"
    with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock), \
         patch(
             "app.services.job_import.fetcher.httpx.AsyncClient",
             return_value=_MockAsyncClient(lambda m, u: _MockStreamResponse(200, chunks=[captcha_html])),
         ):
        res_cap = client.post(IMPORT_ENDPOINT, json={"url": "https://wellfound.com/jobs/123"}, headers=headers)
        assert res_cap.status_code == 422
        assert "manual" in res_cap.json()["detail"].lower()


def test_import_large_response_and_missing_metadata_fallback():
    user_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id}

    # Oversized Content-Length -> 413
    with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock), \
         patch(
             "app.services.job_import.fetcher.httpx.AsyncClient",
             return_value=_MockAsyncClient(
                 lambda m, u: _MockStreamResponse(
                     200,
                     headers={"content-type": "text/html", "content-length": str(5 * 1024 * 1024)},
                 )
             ),
         ):
        res_big = client.post(IMPORT_ENDPOINT, json={"url": "https://careers.example.com/big"}, headers=headers)
        assert res_big.status_code == 413

    # Missing JSON-LD -> HTML fallback works when body has >= 50 chars
    fallback_html = (
        b"<html><head><meta property='og:site_name' content='NaukriTech'></head>"
        b"<body><h1>Data Engineer</h1><main>Build ETL pipelines in Python and Spark with 3+ years experience. "
        b"Compensation $130,000 / year.</main></body></html>"
    )
    with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock), \
         patch(
             "app.services.job_import.fetcher.httpx.AsyncClient",
             return_value=_MockAsyncClient(lambda m, u: _MockStreamResponse(200, chunks=[fallback_html])),
         ):
        res_fb = client.post(IMPORT_ENDPOINT, json={"url": "https://www.naukri.com/job-listings-1"}, headers=headers)
        assert res_fb.status_code == 200
        data = res_fb.json()["data"]
        assert data["extraction_method"] == "html_fallback"
        assert data["job_title"] == "Data Engineer"
        assert data["company_name"] == "NaukriTech"

    # Malformed/empty description -> 422
    empty_html = b"<html><body><h1>Title</h1><p>Short</p></body></html>"
    with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock), \
         patch(
             "app.services.job_import.fetcher.httpx.AsyncClient",
             return_value=_MockAsyncClient(lambda m, u: _MockStreamResponse(200, chunks=[empty_html])),
         ):
        res_empty = client.post(IMPORT_ENDPOINT, json={"url": "https://careers.example.com/empty"}, headers=headers)
        assert res_empty.status_code == 422


def test_import_duplicate_url_and_auth():
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    job_url = "https://careers.example.com/jobs/staff-ai"
    desc = "We are seeking a Staff AI Engineer with Python, FastAPI, PostgreSQL, and distributed systems expertise."

    try:
        # Unauthenticated -> 401
        assert client.post(IMPORT_ENDPOINT, json={"url": job_url}).status_code == 401

        # Save once as user A
        with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock):
            save_res = client.post(
                BASE_ENDPOINT,
                json={
                    "job_title": "Staff AI Engineer",
                    "company_name": "Example Corp",
                    "description": desc,
                    "source_url": job_url,
                    "source_type": "url",
                },
                headers={"X-User-Id": user_a},
            )
            assert save_res.status_code == 201

        # Duplicate URL on /import for user A -> 409
        with patch("app.services.job_import.fetcher.socket.getaddrinfo", side_effect=_public_dns_mock):
            dup_imp = client.post(IMPORT_ENDPOINT, json={"url": job_url}, headers={"X-User-Id": user_a})
            assert dup_imp.status_code == 409

            # User B is not blocked by User A's URL
            html = f"<html><body><h1>Staff AI Engineer</h1><main>{desc}</main></body></html>".encode("utf-8")
            with patch(
                "app.services.job_import.fetcher.httpx.AsyncClient",
                return_value=_MockAsyncClient(lambda m, u: _MockStreamResponse(200, chunks=[html])),
            ):
                ok_b = client.post(IMPORT_ENDPOINT, json={"url": job_url}, headers={"X-User-Id": user_b})
                assert ok_b.status_code == 200
    finally:
        _cleanup_user(user_a)
        _cleanup_user(user_b)
