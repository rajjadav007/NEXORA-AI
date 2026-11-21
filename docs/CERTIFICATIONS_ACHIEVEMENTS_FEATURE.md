# Feature #19: Certifications & Achievements Intelligence Engine

## 1. Feature Objective
The Certifications & Achievements Intelligence Engine analyzes cleaned resume text to extract structured information about candidate credentials, licenses, online courses, training certificates, hackathon rankings, competition awards, academic honors, scholarships, and research publications. It distinguishes completed certifications from courses still in progress, separates competitive awards and rankings from simple participation, links technologies directly to Feature #17 canonical skills, and connects hackathon/competition awards to Feature #18 candidate projects.

---

## 2. Architecture & Pipeline
```
Cleaned Resume Text
        |
        v
Section Detector & Chunker (`section_detector.py`)
- Detects Certifications sections (Licenses, Credentials, Online Courses, etc.)
- Detects Achievements sections (Awards & Honors, Hackathons, Competitions, Publications)
- Segments sections into isolated candidate blocks
        |
        v
Deterministic Extractor (`deterministic_extractor.py`)
- Extracts titles, issuing organizations, dates, expiry dates, completion status
- Extracts Credential IDs and verification URLs (Credly, Coursera, Udemy, etc.)
- Extracts hackathon/competition rank (Winner, 1st/2nd/3rd Place, Finalist vs Participant)
- Extracts research publications (Title, Conference/Journal, DOI/URL, authors)
        |
        v
Feature #17 Skill Linker (`skill_linker.py`)
- Maps extracted technologies to canonical skills using Feature #17 skill dictionary
- Assigns canonical ID, canonical name, and verified category
        |
        v
Feature #18 Project Linker (`project_linker.py`)
- Matches hackathon and competition accomplishments to known candidate projects
- Assigns related_project_id and project title
        |
        v
AI Semantic Extractor (`ai_extractor.py`)
- Local Ollama fallback (`qwen2.5:3b`) with prompt injection defense
- Handles non-standard narratives and complex accomplishment descriptions
        |
        v
Deduplicator (`deduplicator.py`)
- Consolidates credentials and accomplishments mentioned across multiple sections
- Merges credential IDs, URLs, dates, and evidence
        |
        v
Evidence-Based Confidence Scorer (`confidence_scorer.py`)
- Computes structural confidence score [0.0 - 1.0] without relying on LLM self-reporting
        |
        v
Manual Edit Protection & Persistence (`service.py`)
- Protects user modifications during reprocessing
- Stores to PostgreSQL `certifications` and `achievements` tables
        |
        v
Interactive Frontend Component (`CertificationsAchievementsSection.jsx`)
- Analytics metric counters, category and status filter tabs, search filter
- Rich certification and achievement cards with verify links, skill badges, and review status
- Add/Edit modals with project-linking selector and delete workflow
```

---

## 3. Supported Categories

### 3.1 Certification Categories
1. **Cloud Certification** (`cloud`): AWS, Azure, GCP, Cloud Practitioner, Solutions Architect.
2. **AI/ML Certification** (`ai_ml`): Machine Learning, Deep Learning, TensorFlow, PyTorch.
3. **Data Science** (`data_science`): Data Analytics, Big Data, Tableau, Power BI.
4. **Security** (`security`): Security+, CISSP, CEH, Cybersecurity.
5. **Programming** (`programming`): Python, Java, JavaScript, Full Stack.
6. **Project Management** (`project_management`): PMP, Scrum Master (CSM), Agile, Prince2.
7. **Technical** (`technical`): Kubernetes (CKA), Docker, Linux, Networking (CCNA).
8. **Professional** (`professional`): Certified Professional, Chartered, Licensed.
9. **Online Course Certificate** (`course`): Specializations, Bootcamps, Nanodegrees.
10. **Training Certificate** (`training`): Workshops, Fellowships, Internship Certificates.
11. **Other** (`other`): Unclassified credentials.

### 3.2 Achievement Categories
1. **Hackathon** (`hackathon`): MLH, Smart India Hackathon, PennApps, HackMIT.
2. **Competition** (`competition`): Coding contests, ICPC, LeetCode, Codeforces.
3. **Academic** (`academic`): Dean's List, Valedictorian, Department Gold Medal.
4. **Scholarship** (`scholarship`): Merit scholarships, fellowship grants.
5. **Publication** (`publication`): IEEE, ACM, Springer, arXiv, journals, conferences.
6. **Research** (`research`): Lab investigations, patents.
7. **Leadership** (`leadership`): President, Team Lead, Student Head.
8. **Community** (`community`): Meetup speaker, open-source community contributions.
9. **Volunteer** (`volunteer`): NGO, social service recognition.
10. **Professional** (`professional`): Employee of the month, corporate spot awards.
11. **Other** (`other`): General honors and accomplishments.

---

## 4. Database Schema
Stored in PostgreSQL tables:

### Table `certifications`
- `id` (UUID, Primary Key)
- `resume_id` (UUID, Foreign Key to `resumes.id`, ON DELETE CASCADE, Index)
- `user_id` (UUID, Foreign Key to `users.id`, ON DELETE SET NULL, Index)
- `certification_name` (VARCHAR(255))
- `normalized_name` (VARCHAR(255), Index)
- `issuing_organization` (VARCHAR(255), Index)
- `certification_category` (VARCHAR(50), Index)
- `issue_date` (VARCHAR(50))
- `expiry_date` (VARCHAR(50))
- `credential_id` (VARCHAR(150))
- `credential_url` (TEXT)
- `completion_status` (VARCHAR(30), Index) — `completed`, `in_progress`, `expired`
- `related_skills` (JSONB) — Feature #17 canonical skills
- `source_section` (VARCHAR(100))
- `source_evidence` (JSONB)
- `confidence` (FLOAT)
- `extraction_method` (VARCHAR(50))
- `review_status` (VARCHAR(30), Index) — `pending`, `confirmed`, `needs_review`
- `is_manually_edited` (BOOLEAN)
- `manually_edited_fields` (JSONB)
- `created_at` / `updated_at` (TIMESTAMPTZ)

### Table `achievements`
- `id` (UUID, Primary Key)
- `resume_id` (UUID, Foreign Key to `resumes.id`, ON DELETE CASCADE, Index)
- `user_id` (UUID, Foreign Key to `users.id`, ON DELETE SET NULL, Index)
- `achievement_title` (VARCHAR(255))
- `normalized_title` (VARCHAR(255), Index)
- `achievement_category` (VARCHAR(50), Index)
- `event_name` (VARCHAR(255))
- `organization` (VARCHAR(255), Index)
- `achievement_type` (VARCHAR(50)) — `award`, `ranking`, `participation`, `publication`, `scholarship`, `recognition`
- `rank_or_position` (VARCHAR(100))
- `achievement_date` (VARCHAR(50))
- `description` (TEXT)
- `team_name` (VARCHAR(100))
- `team_size` (INTEGER)
- `candidate_role` (VARCHAR(100))
- `related_project_id` (UUID, Foreign Key to `projects.id`, ON DELETE SET NULL, Index)
- `related_skills` (JSONB) — Feature #17 canonical skills
- `achievement_url` (TEXT)
- `source_section` (VARCHAR(100))
- `source_evidence` (JSONB)
- `confidence` (FLOAT)
- `extraction_method` (VARCHAR(50))
- `review_status` (VARCHAR(30), Index)
- `is_manually_edited` (BOOLEAN)
- `manually_edited_fields` (JSONB)
- `created_at` / `updated_at` (TIMESTAMPTZ)

---

## 5. API Endpoints

### Certifications Endpoints
- `POST /api/v1/resumes/{resume_id}/certifications/extract`: Extract certifications.
- `GET /api/v1/resumes/{resume_id}/certifications`: List certifications.
- `GET /api/v1/resumes/{resume_id}/certifications/summary`: Certification metrics summary.
- `GET /api/v1/resumes/{resume_id}/certifications/pending-reviews`: Pending review certifications.
- `GET /api/v1/resumes/{resume_id}/certifications/{id}`: Single certification record.
- `GET /api/v1/resumes/{resume_id}/certifications/{id}/skills`: Linked canonical skills.
- `POST /api/v1/resumes/{resume_id}/certifications`: Add certification manually.
- `PATCH /api/v1/resumes/{resume_id}/certifications/{id}`: Update certification.
- `POST /api/v1/resumes/{resume_id}/certifications/{id}/confirm`: Confirm certification.
- `DELETE /api/v1/resumes/{resume_id}/certifications/{id}`: Delete certification.
- `POST /api/v1/resumes/{resume_id}/certifications/reprocess`: Reprocess with manual edit preservation.

### Achievements Endpoints
- `POST /api/v1/resumes/{resume_id}/achievements/extract`: Extract achievements.
- `GET /api/v1/resumes/{resume_id}/achievements`: List achievements.
- `GET /api/v1/resumes/{resume_id}/achievements/summary`: Achievement metrics summary.
- `GET /api/v1/resumes/{resume_id}/achievements/pending-reviews`: Pending review achievements.
- `GET /api/v1/resumes/{resume_id}/achievements/{id}`: Single achievement record.
- `GET /api/v1/resumes/{resume_id}/achievements/{id}/skills`: Linked canonical skills.
- `POST /api/v1/resumes/{resume_id}/achievements`: Add achievement manually.
- `PATCH /api/v1/resumes/{resume_id}/achievements/{id}`: Update achievement.
- `POST /api/v1/resumes/{resume_id}/achievements/{id}/confirm`: Confirm achievement.
- `DELETE /api/v1/resumes/{resume_id}/achievements/{id}`: Delete achievement.
- `POST /api/v1/resumes/{resume_id}/achievements/reprocess`: Reprocess with manual edit preservation.

### Combined Summary Endpoint
- `GET /api/v1/resumes/{resume_id}/certifications-achievements/summary`: Combined overview metrics.

---

## 6. Verification & Test Coverage
- **Unit Tests (`backend/tests/services/test_certifications_achievements.py`)**: 9 passed (1.56s).
- **API Tests (`backend/tests/test_certifications_api.py`)**: 2 passed (2.15s).
- **Full Backend Regression**: 255 passed, 0 failures (8.41s).
- **Frontend Unit Tests (`frontend/tests/certifications.test.mjs`)**: 10 passed.
- **Frontend Full Suite**: 65 passed, 0 failures (300ms).
- **Frontend Production Build**: `vite build` completed cleanly with 0 errors.
