# Nexora AI
# API Documentation

**Document:** API_DOCUMENTATION.md  
**Project:** Nexora AI  
**Version:** 1.0  
**API Style:** REST API  
**Backend Framework:** FastAPI  
**Language:** Python  
**Database:** PostgreSQL  
**Authentication:** JWT or Secure Session-Based Authentication, final strategy to be selected  
**API Version:** v1  
**Status:** Proposed

---

# 1. Introduction

This document defines the API architecture and endpoint specifications for Nexora AI.

The backend will expose REST APIs through FastAPI. The frontend will communicate with these APIs to access application functionality.

The API layer will handle:

- User authentication.
- User profile management.
- Resume upload and processing.
- Resume intelligence.
- Job description analysis.
- Employer intelligence.
- Job discovery.
- Job matching.
- Skill gap analysis.
- Career readiness.
- Personalized career roadmaps.
- Skill assessments.
- AI Career Copilot.
- Internship recommendations.
- Application tracking.

The API must provide consistent request validation, response formats, authentication, authorization, and error handling.

# 2. API Architecture

## 2.1 Base URL

Development:

```text
http://localhost:8000/api/v1
```

Production:

```text
https://your-domain.com/api/v1
```

The production domain will be configured during deployment.

## 2.2 API Communication Flow

```text
React Frontend
      |
      | HTTP Request
      v
FastAPI Backend
      |
      v
API Router
      |
      v
Authentication and Validation
      |
      v
Business Service
      |
      +------> PostgreSQL
      |
      +------> AI Engine
      |
      +------> File Storage
      |
      v
Structured API Response
      |
      v
React Frontend
```

## 2.3 HTTP Methods

| Method | Purpose |
|---|---|
| GET | Retrieve information |
| POST | Create or process information |
| PUT | Replace an existing resource |
| PATCH | Partially update a resource |
| DELETE | Delete a resource |

## 2.4 Common Response Format

Successful response:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {}
}
```

Error response:

```json
{
  "success": false,
  "message": "Request failed",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": "The provided input is invalid"
  }
}
```

Paginated response:

```json
{
  "success": true,
  "message": "Records retrieved successfully",
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "limit": 10,
      "total": 100,
      "total_pages": 10
    }
  }
}
```

All endpoints should follow a consistent response structure.

# 3. Authentication and Authorization

Authentication is required for private user operations.

## 3.1 Authentication Strategy

The initial implementation will use a secure authentication mechanism supported by FastAPI.

The final choice between JWT and secure cookie-based sessions will be made before implementing authentication.

For JWT-based authentication, protected requests can use:

```http
Authorization: Bearer <access_token>
```

For cookie-based authentication, use secure, HTTP-only cookies and appropriate CSRF protection.

## 3.2 Authentication Requirements

- User registration.
- User login.
- User logout.
- Current user information.
- Password recovery.
- Token or session validation.
- Protected API access.
- User-level resource ownership.

## 3.3 Access Levels

| Access Type | Description |
|---|---|
| Public | Accessible without authentication |
| Authenticated | Requires a valid user session |
| Owner Only | Requires ownership of the requested resource |
| Admin | Reserved for future administrative functionality |

Every private resource must be checked against the authenticated user.

# 4. API Module Overview

| Module | Endpoint Prefix | Purpose |
|---|---|---|
| Authentication | `/auth` | Account and session management |
| User Profile | `/users` | User profile management |
| Resume Management | `/resumes` | Resume upload and storage |
| Resume Intelligence | `/resume-analysis` | Resume extraction and analysis |
| Job Description | `/job-descriptions` | Job requirement analysis |
| Employer Intelligence | `/companies` | Company research |
| Job Discovery | `/jobs` | Job and internship search |
| Job Matching | `/matching` | Candidate-job comparison |
| Skill Intelligence | `/skills` | Skills and skill gaps |
| Career Readiness | `/readiness` | Role readiness evaluation |
| Career Goals | `/career-goals` | Career goal management |
| Roadmaps | `/roadmaps` | Learning roadmaps |
| Assessments | `/assessments` | Skill assessment |
| Career Copilot | `/copilot` | AI career assistant |
| Applications | `/applications` | Job application tracking |

# 5. AUTHENTICATION APIs

## 5.1 User Registration

**Endpoint:** `/auth/register`

**Method:** POST

**Access:** Public

**Purpose:** Create a new user account.

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "full_name": "Example User"
}
```

Response:

```json
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "is_verified": false
  }
}
```

Validation:
- Email must be valid.
- Email must be unique.
- Password must meet security requirements.
- Required fields must be provided.

## 5.2 User Login

**Endpoint:** `/auth/login`

**Method:** POST

**Access:** Public

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123"
}
```

Response for a JWT-based implementation:

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "token",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "email": "user@example.com"
    }
  }
}
```

For cookie-based authentication, the session cookie will be set through the HTTP response instead.

## 5.3 User Logout

**Endpoint:** `/auth/logout`

**Method:** POST

**Access:** Authenticated

Purpose:
- End the active session.
- Revoke or invalidate the relevant session or refresh token where applicable.

## 5.4 Get Current User

**Endpoint:** `/auth/me`

**Method:** GET

**Access:** Authenticated

Response:

```json
{
  "success": true,
  "message": "User retrieved successfully",
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "is_active": true
  }
}
```

## 5.5 Forgot Password

**Endpoint:** `/auth/forgot-password`

**Method:** POST

**Access:** Public

Request:

```json
{
  "email": "user@example.com"
}
```

The response should not reveal whether an email address belongs to a registered account.

## 5.6 Reset Password

**Endpoint:** `/auth/reset-password`

**Method:** POST

**Access:** Public with valid reset token

Request:

```json
{
  "token": "reset-token",
  "new_password": "NewStrongPassword123"
}
```

# 6. USER PROFILE APIs

## 6.1 Get User Profile

**Endpoint:** `/users/me`

**Method:** GET

**Access:** Authenticated

Response:

```json
{
  "success": true,
  "data": {
    "full_name": "Example User",
    "phone": null,
    "location": "Bengaluru",
    "headline": "Aspiring AI Engineer",
    "linkedin_url": null,
    "github_url": null,
    "portfolio_url": null,
    "preferred_roles": [
      "AI Engineer",
      "Machine Learning Engineer"
    ]
  }
}
```

## 6.2 Update User Profile

**Endpoint:** `/users/me`

**Method:** PATCH

**Access:** Authenticated

Request:

```json
{
  "full_name": "Example User",
  "location": "Bengaluru",
  "headline": "Aspiring AI Engineer",
  "github_url": "https://github.com/example",
  "preferred_roles": [
    "AI Engineer",
    "Machine Learning Engineer"
  ]
}
```

## 6.3 Delete User Account

**Endpoint:** `/users/me`

**Method:** DELETE

**Access:** Authenticated

Purpose:
- Initiate account deletion.
- Apply the documented data deletion and retention policy.
- Remove or anonymize associated data as required.

# 7. RESUME MANAGEMENT APIs

## 7.1 Upload Resume

**Endpoint:** `/resumes`

**Method:** POST

**Access:** Authenticated

**Content-Type:** `multipart/form-data`

Request:

```text
file: resume.pdf
```

Response:

```json
{
  "success": true,
  "message": "Resume uploaded successfully",
  "data": {
    "resume_id": "uuid",
    "filename": "resume.pdf",
    "processing_status": "uploaded"
  }
}
```

Validation:
- PDF and DOCX only.
- Maximum file size must follow configured limits.
- File content must be validated.
- Uploaded files must be stored privately.

## 7.2 Get All Resumes

**Endpoint:** `/resumes`

**Method:** GET

**Access:** Authenticated

Query parameters:

| Parameter | Type | Description |
|---|---|---|
| page | Integer | Page number |
| limit | Integer | Records per page |
| status | String | Processing status |

## 7.3 Get Resume Details

**Endpoint:** `/resumes/{resume_id}`

**Method:** GET

**Access:** Owner Only

## 7.4 Get Resume Preview

**Endpoint:** `/resumes/{resume_id}/preview`

**Method:** GET

**Access:** Owner Only

Purpose:
- Return authorized preview information.
- Provide extracted text or a secure document preview reference.

## 7.5 Delete Resume

**Endpoint:** `/resumes/{resume_id}`

**Method:** DELETE

**Access:** Owner Only

Purpose:
- Delete the resume according to the configured retention policy.
- Remove associated stored files and derived records where required.

## 7.6 Get Resume Versions

**Endpoint:** `/resumes/{resume_id}/versions`

**Method:** GET

**Access:** Owner Only

## 7.7 Upload New Resume Version

**Endpoint:** `/resumes/{resume_id}/versions`

**Method:** POST

**Access:** Owner Only

**Content-Type:** `multipart/form-data`

# 8. RESUME INTELLIGENCE APIs

## 8.1 Start Resume Processing

**Endpoint:** `/resume-analysis/{resume_id}/process`

**Method:** POST

**Access:** Owner Only

Purpose:
- Extract resume text.
- Clean the text.
- Create structured resume information.

Response:

```json
{
  "success": true,
  "message": "Resume processing started",
  "data": {
    "resume_id": "uuid",
    "status": "processing"
  }
}
```

If processing is asynchronous, return a processing identifier and expose a status endpoint.

## 8.2 Get Processing Status

**Endpoint:** `/resume-analysis/{resume_id}/status`

**Method:** GET

**Access:** Owner Only

Response:

```json
{
  "success": true,
  "data": {
    "resume_id": "uuid",
    "status": "completed",
    "progress": 100
  }
}
```

## 8.3 Personal Information Extraction (Phase 3 | Feature 13)

### 8.3.1 Extract Personal Information
**Endpoint:** `/resumes/{resume_id}/personal-info/extract`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters:**
- `reprocess` (boolean, default: false): Re-extract and refresh fields
- `force_overwrite` (boolean, default: false): Overwrite manual corrections

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Personal information extracted successfully",
  "data": {
    "id": "uuid",
    "resume_id": "uuid",
    "user_id": "uuid",
    "full_name": "Raj Jadav",
    "first_name": "Raj",
    "last_name": "Jadav",
    "email": "raj.jadav@example.com",
    "phone": "+91 9876543210",
    "country_code": "+91",
    "location": {
      "city": "Bengaluru",
      "state": "Karnataka",
      "country": "India"
    },
    "linkedin_url": "https://linkedin.com/in/rajjadav",
    "github_url": "https://github.com/rajjadav",
    "portfolio_url": "https://rajjadav.dev",
    "other_urls": ["https://medium.com/@rajjadav"],
    "extraction_status": "completed",
    "confidence": {
      "full_name": 0.98,
      "email": 1.0,
      "phone": 0.95,
      "location": 0.85
    },
    "is_manually_edited": false,
    "manually_edited_fields": []
  }
}
```

### 8.3.2 Get Extracted Personal Information
**Endpoint:** `/resumes/{resume_id}/personal-info`  
**Method:** GET  
**Access:** Authenticated User / Owner  

### 8.3.3 Update Personal Information Manually
**Endpoint:** `/resumes/{resume_id}/personal-info`  
**Method:** PATCH  
**Access:** Authenticated User / Owner  
**Request Body:**
```json
{
  "full_name": "Raj Jadav",
  "email": "new.email@example.com",
  "phone": "+91 9876543210",
  "location": {
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India"
  }
}
```

### 8.3.4 Reprocess Personal Information
**Endpoint:** `/resumes/{resume_id}/personal-info/reprocess`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters:**
- `force_overwrite` (boolean, default: false): Overwrite manual edits if true

## 8.4 Education Analysis (Phase 3 | Feature 14)

### 8.4.1 Extract Education Records
**Endpoint:** `/resumes/{resume_id}/education/extract`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters:**
- `reprocess` (boolean, default: false): Re-extract and refresh records
- `force_overwrite` (boolean, default: false): Overwrite manual user corrections

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Education extracted successfully",
  "data": [
    {
      "id": "uuid",
      "resume_id": "uuid",
      "user_id": "uuid",
      "degree": "Bachelor of Computer Applications (BCA)",
      "normalized_degree": "Bachelor of Computer Applications",
      "degree_level": "undergraduate",
      "field_of_study": "Computer Applications",
      "specialization": null,
      "institution": "Bangalore University",
      "location": "Bengaluru",
      "start_date": "2020",
      "end_date": "2023",
      "graduation_status": "completed",
      "grade": {
        "value": 8.42,
        "type": "cgpa",
        "scale": 10.0,
        "raw_grade": "CGPA: 8.42 / 10.0"
      },
      "achievements": [],
      "coursework": ["Data Structures", "Algorithms", "DBMS"],
      "honors": [],
      "source_evidence": ["Bachelor of Computer Applications (BCA)..."],
      "extraction_confidence": 0.98,
      "is_manually_edited": false,
      "manually_edited_fields": [],
      "created_at": "2026-11-19T22:50:00Z",
      "updated_at": "2026-11-19T22:50:00Z"
    }
  ],
  "total": 1,
  "extraction_status": "completed"
}
```

### 8.4.2 Get Education Records
**Endpoint:** `/resumes/{resume_id}/education`  
**Method:** GET  
**Access:** Authenticated User / Owner  
**Response (200 OK):** Chronologically sorted education records (ongoing/expected first, then descending by end date).

### 8.4.3 Reprocess Education Extraction
**Endpoint:** `/resumes/{resume_id}/education/reprocess`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters or JSON Body:**
- `force_overwrite` (boolean, default: false): If false, preserves records with `is_manually_edited == True`

### 8.4.4 Add Education Entry Manually
**Endpoint:** `/resumes/{resume_id}/education`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Request Body:**
```json
{
  "degree": "Master of Computer Applications",
  "institution": "Indian Institute of Science",
  "location": "Bengaluru, India",
  "start_date": "2023",
  "end_date": "2025",
  "graduation_status": "ongoing",
  "grade": {
    "value": 9.2,
    "type": "cgpa",
    "scale": 10.0
  },
  "achievements": ["Dean's Merit List"],
  "coursework": ["Distributed Systems"],
  "honors": ["Gold Medalist"]
}
```

### 8.4.5 Update Education Entry
**Endpoint:** `/resumes/{resume_id}/education/{education_id}`  
**Method:** PATCH  
**Access:** Authenticated User / Owner  
**Request Body:** Partial dictionary of fields to update (`degree`, `institution`, `location`, `grade`, `graduation_status`, etc.). Marks `is_manually_edited = True`.

### 8.4.6 Delete Education Entry
**Endpoint:** `/resumes/{resume_id}/education/{education_id}`  
**Method:** DELETE  
**Access:** Authenticated User / Owner  

## 8.5 Experience Analysis (Phase 3 | Feature 15)

### 8.5.1 Extract Experience Records
**Endpoint:** `/resumes/{resume_id}/experience/extract`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters:**
- `reprocess` (boolean, default: false): Re-extract and refresh records
- `force_overwrite` (boolean, default: false): Overwrite manual user corrections

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Experience extracted successfully",
  "data": [
    {
      "id": "uuid",
      "resume_id": "uuid",
      "user_id": "uuid",
      "company": "Acme Technologies",
      "job_title": "AI Engineer Intern",
      "employment_type": "internship",
      "location": "Bengaluru, India",
      "start_date": "2025-06",
      "end_date": "2025-09",
      "is_current": false,
      "duration_months": 3,
      "responsibilities": ["Developed Python-based AI applications"],
      "technical_contributions": ["Implemented model inference pipelines"],
      "technologies": ["Python", "FastAPI", "LangChain"],
      "achievements": ["Improved inference latency by 35%"],
      "measurable_impact": ["35% latency improvement"],
      "source_evidence": ["AI Engineer Intern at Acme Technologies"],
      "extraction_confidence": 0.95,
      "is_manually_edited": false,
      "manually_edited_fields": [],
      "created_at": "2026-11-20T15:00:00Z",
      "updated_at": "2026-11-20T15:00:00Z"
    }
  ],
  "summary": {
    "total_experience_months": 3,
    "total_experience_years": 0.2,
    "employment_count": 1,
    "full_time_count": 0,
    "internship_count": 1,
    "freelance_count": 0,
    "contract_count": 0,
    "apprenticeship_count": 0,
    "research_count": 0,
    "volunteer_count": 0,
    "other_count": 0,
    "most_recent_role": {
      "company": "Acme Technologies",
      "job_title": "AI Engineer Intern"
    },
    "identified_technologies": ["Python", "FastAPI", "LangChain"],
    "career_progression_observations": [
      "Candidate has 1 professional role as AI Engineer Intern at Acme Technologies."
    ],
    "extraction_status": "completed"
  },
  "total": 1,
  "extraction_status": "completed"
}
```

### 8.5.2 Get Experience Records
**Endpoint:** `/resumes/{resume_id}/experience`  
**Method:** GET  
**Access:** Authenticated User / Owner  
**Response (200 OK):** Chronologically sorted experience records and summary metrics.

### 8.5.3 Reprocess Experience Extraction
**Endpoint:** `/resumes/{resume_id}/experience/reprocess`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters or JSON Body:**
- `force_overwrite` (boolean, default: false): If false, preserves records with `is_manually_edited == True`

### 8.5.4 Add Experience Entry Manually
**Endpoint:** `/resumes/{resume_id}/experience`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Request Body:**
```json
{
  "company": "Example Systems",
  "job_title": "Senior AI Engineer",
  "employment_type": "full_time",
  "location": "Bengaluru, India",
  "start_date": "2024-01",
  "end_date": null,
  "is_current": true,
  "responsibilities": ["Architected distributed model inference services"],
  "technical_contributions": ["Deployed FastAPI microservices with Docker"],
  "technologies": ["Python", "FastAPI", "Docker", "PyTorch"],
  "achievements": ["Reduced latency by 40%"],
  "measurable_impact": ["40% latency reduction"]
}
```

### 8.5.5 Update Experience Entry
**Endpoint:** `/resumes/{resume_id}/experience/{experience_id}`  
**Method:** PATCH  
**Access:** Authenticated User / Owner  
**Request Body:** Partial dictionary of fields to update (`company`, `job_title`, `employment_type`, `location`, `start_date`, `end_date`, `is_current`, `responsibilities`, etc.). Marks `is_manually_edited = True`.

### 8.5.6 Delete Experience Entry
**Endpoint:** `/resumes/{resume_id}/experience/{experience_id}`  
**Method:** DELETE  
**Access:** Authenticated User / Owner  

### 8.5.7 Get Experience Summary
**Endpoint:** `/resumes/{resume_id}/experience/summary`  
**Method:** GET  
**Access:** Authenticated User / Owner  
**Response (200 OK):** Non-overlapping aggregate duration, breakdown counts by employment type, top technologies, and career observations.

### 8.5.8 Get Career Progression
**Endpoint:** `/resumes/{resume_id}/experience/progression`  
**Method:** GET  
**Access:** Authenticated User / Owner  
**Response (200 OK):** Chronological career transitions, internal promotions, employment gaps, and factual career progression observations.

## 8.6 Skill Normalization Endpoints (Phase 3 | Feature 17)

### 8.6.1 Extract and Normalize Skills
**Endpoint:** `/resumes/{resume_id}/skills/extract`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters:**
- `reprocess` (bool, default=false): Re-extract and renormalize skills from resume text.
- `force_overwrite` (bool, default=false): Overwrite user manual edits if true.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Skills extracted and normalized successfully",
  "data": [
    {
      "id": "e8f9a0b1-c2d3-4e5f-6a7b-8c9d0e1f2a3b",
      "resume_id": "c47d757f-a84e-49ee-9616-5628ca99c7c7",
      "skill_id": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
      "original_name": "JS",
      "canonical_name": "JavaScript",
      "category": "Programming Languages",
      "skill_type": "technical",
      "normalization_method": "alias_match",
      "confidence_score": 1.0,
      "normalization_status": "normalized",
      "source_sections": ["skills", "experience"],
      "source_evidence": ["Programming Languages: JS, JavaScript, Python", "Built frontend micro-apps with React and JS"],
      "aliases_detected": ["JS", "JavaScript"],
      "occurrence_count": 2,
      "is_manually_edited": false,
      "manually_edited_fields": [],
      "dictionary_version": "1.0.0"
    }
  ],
  "summary": {
    "total_original_skills": 18,
    "total_normalized_skills": 12,
    "aliases_matched": 6,
    "duplicates_consolidated": 6,
    "pending_reviews": 0,
    "unknown_skills": 0,
    "category_distribution": {
      "Programming Languages": 4,
      "Frameworks & Libraries": 4,
      "Databases": 2,
      "Cloud & DevOps": 2
    },
    "skill_type_distribution": {
      "technical": 12
    }
  },
  "total": 12,
  "extraction_status": "completed"
}
```

### 8.6.2 Get Normalized Skills
**Endpoint:** `/resumes/{resume_id}/skills`  
**Method:** GET  
**Access:** Authenticated User / Owner  

### 8.6.3 Direct Skill List Normalization
**Endpoint:** `/resumes/{resume_id}/skills/normalize`  
**Method:** POST  
**Request Body:**
```json
{
  "skills": ["JS", "Javascript", "ML", "K8s", "ReactJS", "ReactNative"],
  "context_text": "Experienced full-stack engineer building AI platforms"
}
```

### 8.6.4 Reprocess Skill Normalization
**Endpoint:** `/resumes/{resume_id}/skills/reprocess`  
**Method:** POST  
**Query Parameters:** `force_overwrite` (bool, default=false)

### 8.6.5 Get Normalization Summary
**Endpoint:** `/resumes/{resume_id}/skills/summary`  
**Method:** GET  

### 8.6.6 Get Pending Review Skills
**Endpoint:** `/resumes/{resume_id}/skills/pending-reviews`  
**Method:** GET  

### 8.6.7 Confirm Proposed Skill Mapping
**Endpoint:** `/resumes/{resume_id}/skills/{skill_id}/confirm`  
**Method:** POST  
**Request Body (optional):**
```json
{
  "canonical_name": "R"
}
```

### 8.6.8 Reject Proposed Skill Mapping
**Endpoint:** `/resumes/{resume_id}/skills/{skill_id}/reject`  
**Method:** POST  

### 8.6.9 Manually Update Skill Record
**Endpoint:** `/resumes/{resume_id}/skills/{skill_id}`  
**Method:** PATCH  
**Request Body:**
```json
{
  "canonical_name": "Python",
  "category": "Programming Languages",
  "skill_type": "technical"
}
```

### 8.6.10 Delete Normalized Skill Record
**Endpoint:** `/resumes/{resume_id}/skills/{skill_id}`  
**Method:** DELETE  

### 8.6.11 Get Global Canonical Skill Dictionary
**Endpoint:** `/skills/dictionary`  
**Method:** GET  

### 8.6.12 Add Alias to Canonical Dictionary
**Endpoint:** `/skills/dictionary/alias`  
**Method:** POST  
**Request Body:**
```json
{
  "canonical_name": "Python",
  "alias": "py3",
  "category": "Programming Languages"
}
```

## 8.7 Project Intelligence Endpoints (Phase 3 | Feature 18)

### 8.7.1 Extract and Structure Projects
**Endpoint:** `/resumes/{resume_id}/projects/extract`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters:**
- `reprocess` (bool, default=false): Re-run project extraction from resume text.
- `force_overwrite` (bool, default=false): Overwrite user manual edits if true.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Projects extracted and structured successfully",
  "data": [
    {
      "id": "e9a0b1c2-d3e4-4f5a-6b7c-8d9e0f1a2b3c",
      "resume_id": "c47d757f-a84e-49ee-9616-5628ca99c7c7",
      "project_title": "Cloud Task Orchestrator | Python, FastAPI, Docker, Redis",
      "normalized_title": "Cloud Task Orchestrator",
      "project_category": "personal",
      "short_description": "Architected distributed job queue processing 50,000 tasks/second across 4 worker nodes.",
      "detailed_description": "Architected distributed job queue processing 50,000 tasks/second across 4 worker nodes.\n- Reduced end-to-end task dispatch latency by 45% using Redis streams and async workers.",
      "problem_statement": "High latency and dropped jobs during peak burst traffic.",
      "proposed_solution": "Implemented distributed asynchronous event-driven task queue with Redis streams.",
      "domain": "Cloud Infrastructure",
      "project_role": "Backend Lead",
      "team_type": "team",
      "team_size": 3,
      "start_date": "Jan 2023",
      "end_date": null,
      "is_ongoing": true,
      "technologies": ["Python", "FastAPI", "Docker", "Redis"],
      "skills": [
        {
          "original_name": "FastAPI",
          "canonical_id": "b1c2d3e4-f5a6-7b8c-9d0e-1f2a3b4c5d6e",
          "canonical_name": "FastAPI",
          "category": "Frameworks & Libraries",
          "confidence": 1.0,
          "is_explicit": true
        }
      ],
      "responsibilities": [
        "Architected distributed job queue processing 50,000 tasks/second across 4 worker nodes.",
        "Reduced end-to-end task dispatch latency by 45% using Redis streams."
      ],
      "achievements": [],
      "measurable_outcomes": [
        "Reduced end-to-end task dispatch latency by 45% using Redis streams and async workers.",
        "Architected distributed job queue processing 50,000 tasks/second across 4 worker nodes."
      ],
      "project_links": [
        {
          "type": "github",
          "url": "https://github.com/janedoe/task-orchestrator"
        },
        {
          "type": "demo",
          "url": "https://task-orchestrator.demo.app"
        }
      ],
      "source_section": "PROJECTS",
      "source_evidence": ["Cloud Task Orchestrator | Python, FastAPI, Docker, Redis (Jan 2023 - Present)"],
      "confidence": 0.95,
      "extraction_method": "hybrid",
      "review_status": "confirmed",
      "is_manually_edited": false,
      "manually_edited_fields": []
    }
  ],
  "summary": {
    "total_projects": 2,
    "categories": {"personal": 1, "academic": 1},
    "domains_count": 2,
    "unique_technologies_count": 6,
    "github_repos_count": 1,
    "live_demos_count": 1,
    "pending_review_count": 0
  },
  "total": 2,
  "extraction_status": "completed"
}
```

### 8.7.2 Get All Projects for Resume
**Endpoint:** `/resumes/{resume_id}/projects`  
**Method:** GET  
**Access:** Authenticated User / Owner  

### 8.7.3 Get Project Analytics Summary
**Endpoint:** `/resumes/{resume_id}/projects/summary`  
**Method:** GET  
**Access:** Authenticated User / Owner  

### 8.7.4 Get Single Project Details
**Endpoint:** `/resumes/{resume_id}/projects/{project_id}`  
**Method:** GET  
**Access:** Authenticated User / Owner  

### 8.7.5 Get Project Canonical Skill Links
**Endpoint:** `/resumes/{resume_id}/projects/{project_id}/skills`  
**Method:** GET  
**Access:** Authenticated User / Owner  

### 8.7.6 Add Project Manually
**Endpoint:** `/resumes/{resume_id}/projects`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Request Body:**
```json
{
  "project_title": "Distributed Task Queue",
  "project_category": "personal",
  "short_description": "Async task queue engine",
  "domain": "Cloud Infrastructure",
  "technologies": ["Python", "FastAPI", "Redis"],
  "team_type": "individual"
}
```

### 8.7.7 Update Project Manually
**Endpoint:** `/resumes/{resume_id}/projects/{project_id}`  
**Method:** PATCH  
**Access:** Authenticated User / Owner  
**Request Body:** Partial project fields to update.

### 8.7.8 Confirm Project Review
**Endpoint:** `/resumes/{resume_id}/projects/{project_id}/confirm`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Request Body (Optional):** `{"notes": "Verified details"}`

### 8.7.9 Delete Project
**Endpoint:** `/resumes/{resume_id}/projects/{project_id}`  
**Method:** DELETE  
**Access:** Authenticated User / Owner  

### 8.7.10 Reprocess Projects
**Endpoint:** `/resumes/{resume_id}/projects/reprocess`  
**Method:** POST  
**Access:** Authenticated User / Owner  
**Query Parameters:**
- `force_overwrite` (bool, default=false): When false, preserves user-edited records.


## 8.6 Get Extracted Resume Information
**Endpoint:** `/resume-analysis/{resume_id}/extracted`

**Method:** GET

**Access:** Owner Only

Response:

```json
{
  "success": true,
  "data": {
    "personal_information": {
      "name": "Example User",
      "email": "user@example.com",
      "phone": null
    },
    "education": [],
    "experience": [],
    "skills": [],
    "projects": [],
    "certifications": []
  }
}
```

## 8.4 Update Extracted Information

**Endpoint:** `/resume-analysis/{resume_id}/extracted`

**Method:** PATCH

**Access:** Owner Only

Purpose:
- Allow users to correct extracted information.
- Preserve user-confirmed data.
- Keep a record of updated information where required.

## 8.5 Get Resume Analysis

**Endpoint:** `/resume-analysis/{resume_id}`

**Method:** GET

**Access:** Owner Only

## 8.6 Start Resume Quality Analysis

**Endpoint:** `/resume-analysis/{resume_id}/quality`

**Method:** POST

**Access:** Owner Only

Purpose:
- Calculate resume quality.
- Analyze strengths and weaknesses.
- Evaluate ATS compatibility.
- Analyze grammar and clarity.
- Evaluate achievements.
- Generate recommendations.

## 8.7 Get Resume Quality Report

**Endpoint:** `/resume-analysis/{resume_id}/quality`

**Method:** GET

**Access:** Owner Only

## 8.8 Get Resume Analytics

**Endpoint:** `/resume-analysis/{resume_id}/analytics`

**Method:** GET

**Access:** Owner Only

## 8.9 Export Resume Report

**Endpoint:** `/resume-analysis/{resume_id}/export`

**Method:** GET

**Access:** Owner Only

Query parameters:

| Parameter | Type | Description |
|---|---|---|
| format | String | `pdf` |

Response:
- PDF file download or authorized file response.

# 9. JOB DESCRIPTION ANALYZER APIs

## 9.1 Create Job Description

**Endpoint:** `/job-descriptions`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "job_title": "AI Engineer Intern",
  "description": "We are looking for a candidate with Python, machine learning and NLP experience."
}
```

## 9.2 Import Job Description URL

**Endpoint:** `/job-descriptions/import`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "url": "https://example.com/careers/ai-engineer-intern"
}
```

Requirements:
- Process only supported, accessible URLs.
- Validate URLs to reduce server-side request forgery risks.
- Respect website access restrictions.
- Report extraction failures clearly.
- Preserve the original source URL.

## 9.3 Analyze Job Description

**Endpoint:** `/job-descriptions/{job_description_id}/analyze`

**Method:** POST

**Access:** Owner Only

Purpose:
- Extract job role.
- Identify requirements.
- Extract mandatory skills.
- Extract preferred skills.
- Generate a structured report.

## 9.4 Get Job Description Analysis

**Endpoint:** `/job-descriptions/{job_description_id}/analysis`

**Method:** GET

**Access:** Owner Only

## 9.5 List Job Descriptions

**Endpoint:** `/job-descriptions`

**Method:** GET

**Access:** Authenticated

## 9.6 Delete Job Description

**Endpoint:** `/job-descriptions/{job_description_id}`

**Method:** DELETE

**Access:** Owner Only

# 10. EMPLOYER INTELLIGENCE APIs

## 10.1 Search Companies

**Endpoint:** `/companies/search`

**Method:** GET

**Access:** Authenticated

Query parameters:

| Parameter | Type | Description |
|---|---|---|
| query | String | Company name |
| industry | String | Industry filter |
| location | String | Location filter |
| page | Integer | Page number |
| limit | Integer | Result limit |

## 10.2 Get Company Details

**Endpoint:** `/companies/{company_id}`

**Method:** GET

**Access:** Authenticated

## 10.3 Research Company

**Endpoint:** `/companies/{company_id}/research`

**Method:** POST

**Access:** Authenticated

Purpose:
- Collect available public company information.
- Identify company hiring pages.
- Collect relevant sources.
- Generate a structured company research report.

## 10.4 Get Company Research Report

**Endpoint:** `/companies/{company_id}/research`

**Method:** GET

**Access:** Authenticated

## 10.5 Discover Company Jobs

**Endpoint:** `/companies/{company_id}/jobs`

**Method:** GET

**Access:** Authenticated

## 10.6 Analyze Employer Requirements

**Endpoint:** `/companies/{company_id}/requirements/analyze`

**Method:** POST

**Access:** Authenticated

Purpose:
- Analyze available job postings.
- Identify frequently requested skills.
- Identify role-specific requirements.

## 10.7 Get Employer Intelligence Report

**Endpoint:** `/companies/{company_id}/intelligence`

**Method:** GET

**Access:** Authenticated

The report should distinguish source-supported findings from AI-generated interpretation.

# 11. JOB DISCOVERY APIs

## 11.1 Search Jobs

**Endpoint:** `/jobs`

**Method:** GET

**Access:** Authenticated

Query parameters:

| Parameter | Type | Description |
|---|---|---|
| query | String | Job title or keyword |
| location | String | Job location |
| job_type | String | Internship, full-time, etc. |
| experience_level | String | Experience requirement |
| work_mode | String | Remote, hybrid, onsite |
| page | Integer | Page number |
| limit | Integer | Result limit |

## 11.2 Get Job Details

**Endpoint:** `/jobs/{job_id}`

**Method:** GET

**Access:** Authenticated

## 11.3 Save Job

**Endpoint:** `/jobs/{job_id}/save`

**Method:** POST

**Access:** Authenticated

## 11.4 Remove Saved Job

**Endpoint:** `/jobs/{job_id}/save`

**Method:** DELETE

**Access:** Authenticated

## 11.5 Get Saved Jobs

**Endpoint:** `/jobs/saved`

**Method:** GET

**Access:** Authenticated

## 11.6 Get Job Filters

**Endpoint:** `/jobs/filters`

**Method:** GET

**Access:** Authenticated

Purpose:
- Return supported job types.
- Return experience levels.
- Return locations where available.
- Return work modes.

# 12. JOB MATCHING APIs

## 12.1 Generate Job Match

**Endpoint:** `/matching`

**Method:** POST

**Access:** Owner Only

Request:

```json
{
  "resume_id": "resume-uuid",
  "job_id": "job-uuid"
}
```

Response:

```json
{
  "success": true,
  "message": "Job matching completed",
  "data": {
    "match_id": "match-uuid",
    "overall_score": 78.5,
    "skill_score": 82.0,
    "experience_score": 70.0,
    "education_score": 85.0,
    "explanation": {
      "matched_skills": [
        "Python",
        "Machine Learning"
      ],
      "missing_skills": [
        "Docker"
      ],
      "summary": "The profile matches several key requirements."
    }
  }
}
```

Scores must use documented scoring rules. They represent profile compatibility, not the probability of receiving an offer.

## 12.2 Get Match Details

**Endpoint:** `/matching/{match_id}`

**Method:** GET

**Access:** Owner Only

## 12.3 Get User Match History

**Endpoint:** `/matching/history`

**Method:** GET

**Access:** Authenticated

Query parameters:

- `page`
- `limit`
- `job_id`

## 12.4 Compare Multiple Jobs

**Endpoint:** `/matching/compare`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "resume_id": "resume-uuid",
  "job_ids": [
    "job-uuid-1",
    "job-uuid-2"
  ]
}
```

# 13. SKILL INTELLIGENCE APIs

## 13.1 Get User Skills

**Endpoint:** `/skills/me`

**Method:** GET

**Access:** Authenticated

## 13.2 Add User Skill

**Endpoint:** `/skills/me`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "skill_name": "Python",
  "proficiency_level": "intermediate"
}
```

## 13.3 Update User Skill

**Endpoint:** `/skills/me/{skill_id}`

**Method:** PATCH

**Access:** Owner Only

## 13.4 Delete User Skill

**Endpoint:** `/skills/me/{skill_id}`

**Method:** DELETE

**Access:** Owner Only

## 13.5 Generate Skill Gap Report

**Endpoint:** `/skills/gaps`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "resume_id": "resume-uuid",
  "job_id": "job-uuid"
}
```

## 13.6 Get Skill Gap Report

**Endpoint:** `/skills/gaps/{gap_id}`

**Method:** GET

**Access:** Owner Only

## 13.7 Compare Skill Gaps

**Endpoint:** `/skills/gaps/compare`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "resume_id": "resume-uuid",
  "job_ids": [
    "job-uuid-1",
    "job-uuid-2"
  ]
}
```

# 14. CAREER READINESS APIs

## 14.1 Calculate Career Readiness

**Endpoint:** `/readiness`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "resume_id": "resume-uuid",
  "job_id": "job-uuid"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "readiness_id": "uuid",
    "target_role": "AI Engineer Intern",
    "readiness_score": 72.5,
    "breakdown": {
      "skills": 75,
      "experience": 65,
      "education": 85,
      "projects": 70
    }
  }
}
```

The scoring criteria and weights must be documented and versioned.

## 14.2 Get Readiness Result

**Endpoint:** `/readiness/{readiness_id}`

**Method:** GET

**Access:** Owner Only

## 14.3 Get Readiness History

**Endpoint:** `/readiness/history`

**Method:** GET

**Access:** Authenticated

## 14.4 Get Readiness Progress

**Endpoint:** `/readiness/progress`

**Method:** GET

**Access:** Authenticated

# 15. CAREER GOAL APIs

## 15.1 Create Career Goal

**Endpoint:** `/career-goals`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "target_role": "Machine Learning Engineer",
  "target_level": "Entry Level",
  "target_date": "2027-06-30",
  "description": "Prepare for entry-level machine learning roles."
}
```

## 15.2 Get Career Goals

**Endpoint:** `/career-goals`

**Method:** GET

**Access:** Authenticated

## 15.3 Update Career Goal

**Endpoint:** `/career-goals/{goal_id}`

**Method:** PATCH

**Access:** Owner Only

## 15.4 Delete Career Goal

**Endpoint:** `/career-goals/{goal_id}`

**Method:** DELETE

**Access:** Owner Only

# 16. PERSONALIZED ROADMAP APIs

## 16.1 Generate Career Roadmap

**Endpoint:** `/roadmaps/generate`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "career_goal_id": "goal-uuid",
  "resume_id": "resume-uuid"
}
```

Response:

```json
{
  "success": true,
  "message": "Career roadmap generated",
  "data": {
    "roadmap_id": "roadmap-uuid",
    "title": "Machine Learning Engineer Roadmap",
    "status": "active",
    "items": []
  }
}
```

## 16.2 Get User Roadmaps

**Endpoint:** `/roadmaps`

**Method:** GET

**Access:** Authenticated

## 16.3 Get Roadmap Details

**Endpoint:** `/roadmaps/{roadmap_id}`

**Method:** GET

**Access:** Owner Only

## 16.4 Update Roadmap Item

**Endpoint:** `/roadmaps/{roadmap_id}/items/{item_id}`

**Method:** PATCH

**Access:** Owner Only

Request:

```json
{
  "status": "completed"
}
```

## 16.5 Get Roadmap Progress

**Endpoint:** `/roadmaps/{roadmap_id}/progress`

**Method:** GET

**Access:** Owner Only

# 17. SKILL ASSESSMENT APIs

## 17.1 Generate Skill Assessment

**Endpoint:** `/assessments/generate`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "skill_id": "skill-uuid",
  "difficulty": "intermediate",
  "assessment_type": "technical"
}
```

## 17.2 Get Available Assessments

**Endpoint:** `/assessments`

**Method:** GET

**Access:** Authenticated

## 17.3 Get Assessment Details

**Endpoint:** `/assessments/{assessment_id}`

**Method:** GET

**Access:** Authenticated

Assessment answers and private evaluation material must not be exposed before submission.

## 17.4 Start Assessment Attempt

**Endpoint:** `/assessments/{assessment_id}/attempts`

**Method:** POST

**Access:** Authenticated

## 17.5 Submit Assessment

**Endpoint:** `/assessments/attempts/{attempt_id}/submit`

**Method:** POST

**Access:** Owner Only

Request:

```json
{
  "answers": [
    {
      "question_id": "question-1",
      "answer": "Example answer"
    }
  ]
}
```

## 17.6 Get Assessment Result

**Endpoint:** `/assessments/attempts/{attempt_id}/result`

**Method:** GET

**Access:** Owner Only

## 17.7 Get Skill Evidence

**Endpoint:** `/skills/evidence`

**Method:** GET

**Access:** Authenticated

# 18. AI CAREER COPILOT APIs

## 18.1 Create Conversation

**Endpoint:** `/copilot/conversations`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "title": "AI Engineer Career Preparation",
  "conversation_type": "career_guidance"
}
```

## 18.2 Get Conversations

**Endpoint:** `/copilot/conversations`

**Method:** GET

**Access:** Authenticated

## 18.3 Get Conversation Messages

**Endpoint:** `/copilot/conversations/{conversation_id}/messages`

**Method:** GET

**Access:** Owner Only

## 18.4 Send Copilot Message

**Endpoint:** `/copilot/chat`

**Method:** POST

**Access:** Owner Only

Request:

```json
{
  "conversation_id": "conversation-uuid",
  "message": "How can I improve my AI Engineer profile?"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "message_id": "uuid",
    "role": "assistant",
    "content": "Based on your available profile information...",
    "conversation_id": "conversation-uuid"
  }
}
```

The AI should use only authorized user context and relevant source information.

## 18.5 Start Mock Interview

**Endpoint:** `/copilot/mock-interviews`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "target_role": "AI Engineer Intern",
  "difficulty": "intermediate",
  "interview_type": "technical"
}
```

## 18.6 Submit Interview Answer

**Endpoint:** `/copilot/mock-interviews/{interview_id}/answers`

**Method:** POST

**Access:** Owner Only

Request:

```json
{
  "question_id": "question-uuid",
  "answer": "My answer to the interview question."
}
```

## 18.7 Get Interview Feedback

**Endpoint:** `/copilot/mock-interviews/{interview_id}/feedback`

**Method:** GET

**Access:** Owner Only

## 18.8 Analyze GitHub Repository

**Endpoint:** `/copilot/github/analyze`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "repository_url": "https://github.com/example/project"
}
```

Requirements:
- Validate repository URLs.
- Analyze only accessible repository content.
- Respect access permissions and rate limits.
- Never request or expose private repository credentials through ordinary request fields.

## 18.9 Get Internship Recommendations

**Endpoint:** `/copilot/internships/recommend`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "resume_id": "resume-uuid",
  "target_role": "AI Engineer Intern",
  "location": "Bengaluru"
}
```

# 19. APPLICATION TRACKING APIs

## 19.1 Create Application

**Endpoint:** `/applications`

**Method:** POST

**Access:** Authenticated

Request:

```json
{
  "job_id": "job-uuid",
  "job_title": "AI Engineer Intern",
  "company_name": "Example Company",
  "application_status": "interested"
}
```

## 19.2 Get Applications

**Endpoint:** `/applications`

**Method:** GET

**Access:** Authenticated

Query parameters:

- `status`
- `page`
- `limit`

## 19.3 Get Application Details

**Endpoint:** `/applications/{application_id}`

**Method:** GET

**Access:** Owner Only

## 19.4 Update Application

**Endpoint:** `/applications/{application_id}`

**Method:** PATCH

**Access:** Owner Only

Request:

```json
{
  "application_status": "applied",
  "applied_at": "2026-11-18T10:00:00Z",
  "notes": "Application submitted."
}
```

## 19.5 Delete Application

**Endpoint:** `/applications/{application_id}`

**Method:** DELETE

**Access:** Owner Only

# 20. ASYNCHRONOUS PROCESSING APIs

Some AI workflows may take longer than normal HTTP requests.

For long-running tasks, the backend should return a task identifier rather than keeping the original request open indefinitely.

## 20.1 Get Processing Task Status

**Endpoint:** `/tasks/{task_id}`

**Method:** GET

**Access:** Authenticated, with task ownership verification

Response:

```json
{
  "success": true,
  "data": {
    "task_id": "uuid",
    "status": "processing",
    "progress": 60,
    "result": null,
    "error": null
  }
}
```

Possible statuses:

- queued
- processing
- completed
- failed
- cancelled

The task system can initially use a simple background processing approach. A dedicated queue can be introduced when required.

# 21. API STATUS CODES

| Status Code | Meaning |
|---|---|
| 200 | Successful request |
| 201 | Resource created |
| 202 | Request accepted for processing |
| 204 | Successful request with no response body |
| 400 | Bad request |
| 401 | Authentication required |
| 403 | Permission denied |
| 404 | Resource not found |
| 409 | Resource conflict |
| 413 | File too large |
| 415 | Unsupported media type |
| 422 | Validation error |
| 429 | Too many requests |
| 500 | Internal server error |
| 502 | Upstream service error |
| 503 | Service temporarily unavailable |
| 504 | Upstream request timeout |

# 22. ERROR HANDLING

All API errors must use a consistent structure.

Example:

```json
{
  "success": false,
  "message": "Resume processing failed",
  "error": {
    "code": "RESUME_PROCESSING_FAILED",
    "details": "The uploaded document could not be processed."
  }
}
```

Common error codes:

| Error Code | Description |
|---|---|
| INVALID_CREDENTIALS | Login details are incorrect |
| EMAIL_ALREADY_EXISTS | Email is already registered |
| AUTHENTICATION_REQUIRED | User is not authenticated |
| PERMISSION_DENIED | User cannot access the resource |
| RESOURCE_NOT_FOUND | Requested resource does not exist |
| INVALID_FILE_TYPE | Unsupported file format |
| FILE_TOO_LARGE | File exceeds the configured limit |
| RESUME_PROCESSING_FAILED | Resume processing failed |
| AI_MODEL_UNAVAILABLE | Local model runtime is unavailable |
| AI_OUTPUT_INVALID | AI output failed validation |
| JOB_NOT_FOUND | Job listing was not found |
| INVALID_REQUEST | Request data is invalid |
| RATE_LIMIT_EXCEEDED | Request limit exceeded |
| INTERNAL_SERVER_ERROR | Unexpected backend error |

Do not expose stack traces, database credentials, tokens, or private internal information in API responses.

# 23. API SECURITY REQUIREMENTS

## 23.1 Authentication

- Protect private endpoints.
- Validate sessions or access tokens.
- Expire and revoke sessions appropriately.
- Use secure password hashing.

## 23.2 Authorization

- Verify ownership of resumes.
- Verify ownership of analysis reports.
- Verify ownership of conversations.
- Verify ownership of roadmaps.
- Verify ownership of applications.
- Verify ownership of assessment attempts.

## 23.3 Input Validation

- Validate JSON request bodies.
- Validate UUID parameters.
- Validate URLs.
- Validate file types and sizes.
- Restrict allowed values for status fields.
- Apply maximum input lengths.

## 23.4 AI Security

- Treat uploaded documents as untrusted input.
- Prevent document instructions from overriding system-level AI rules.
- Validate model outputs before saving them.
- Do not expose private user context to other users.
- Apply timeouts and resource limits to model calls.

## 23.5 External URL Security

For job imports and GitHub analysis:

- Restrict allowed URL schemes.
- Block access to internal and private network addresses.
- Validate redirects.
- Apply request timeouts.
- Limit response sizes.
- Avoid exposing backend network resources.

# 24. API PAGINATION

Large result sets should use pagination.

Example request:

```text
GET /api/v1/jobs?page=1&limit=20
```

Example response:

```json
{
  "success": true,
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

Rules:

- Default page: 1.
- Default limit: 20.
- Maximum limit: 100.
- Reject invalid pagination values.

# 25. API DOCUMENTATION AND TESTING

FastAPI will generate interactive API documentation.

Development Swagger UI:

```text
http://localhost:8000/docs
```

Alternative ReDoc:

```text
http://localhost:8000/redoc
```

Testing tools:

- Pytest.
- FastAPI TestClient or HTTPX.
- Postman.
- Vitest for frontend API integration.

Testing must cover:

- Valid requests.
- Invalid requests.
- Authentication.
- Authorization.
- Resource ownership.
- Database operations.
- File uploads.
- AI service failures.
- Rate limiting.
- Pagination.
- Error responses.

# 26. API IMPLEMENTATION PRIORITY

Implement APIs in the following order.

| Priority | API Module | Related Phase |
|---|---|---|
| 1 | Authentication and User Profile | Phase 15, foundational work |
| 2 | Resume Management | Phase 2 |
| 3 | Resume Intelligence | Phases 3–5 |
| 4 | Job Description Analyzer | Phase 6 |
| 5 | Employer Intelligence | Phase 7 |
| 6 | Job Discovery | Phase 8 |
| 7 | Job Matching | Phase 9 |
| 8 | Skill Intelligence | Phase 10 |
| 9 | Career Readiness | Phase 11 |
| 10 | Career Goals and Roadmaps | Phase 12 |
| 11 | Skill Assessments | Phase 13 |
| 12 | AI Career Copilot | Phase 14 |
| 13 | Application Tracking | Phase 14 |

Security, authentication, validation, and error handling must be implemented throughout development rather than postponed until the final phase.

# 27. API DEVELOPMENT RULES

Every new endpoint must follow these rules:

1. Use the `/api/v1` prefix.
2. Use appropriate HTTP methods.
3. Define Pydantic request schemas.
4. Define response schemas.
5. Validate user permissions.
6. Keep route handlers small.
7. Place business logic in service classes or functions.
8. Use repositories for database access where appropriate.
9. Handle errors consistently.
10. Add tests.
11. Document request and response examples.
12. Avoid exposing internal implementation details.

# 28. FINAL API ARCHITECTURE GOAL

The Nexora AI API layer will connect the frontend, backend services, AI engine, and database.

The API must support the complete user journey:

**User Registration → Resume Upload → Resume Analysis → Job Description Analysis → Employer Research → Job Discovery → Job Matching → Skill Gap Analysis → Career Readiness → Personalized Roadmap → Skill Assessment → AI Career Copilot → Application Tracking**

All APIs must remain secure, documented, testable, and consistent.

This document serves as the initial API design reference. Exact schemas, status codes, authentication behavior, and implementation details must be validated during development and updated whenever the API contract changes.