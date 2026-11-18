# PRIVACY_DATA_HANDLING.md

# Nexora AI: Privacy and Data Handling Policy

## 1. Purpose

This document defines how Nexora AI collects, processes, stores, protects, shares, and deletes user information.

Nexora AI is an AI-powered career intelligence platform that processes personal career information to provide:

- Resume analysis.
- Job description analysis.
- Employer intelligence.
- Resume-to-job matching.
- Skill gap detection.
- Career readiness evaluation.
- Personalized career roadmaps.
- Skill assessments.
- Mock interviews.
- GitHub project analysis.
- Internship recommendations.
- AI Career Copilot assistance.

Because the platform processes personal resumes and career information, privacy must be part of the system architecture from the beginning.

### Main Objectives

1. Collect only necessary information.
2. Explain why information is collected.
3. Protect personal and career information.
4. Give users control over their data.
5. Process resumes securely.
6. Restrict access to authorized services.
7. Control third-party data sharing.
8. Define data retention periods.
9. Support data export and deletion.
10. Maintain transparency in AI processing.

**Important:** This document is an internal product and engineering specification. It is not a final legal privacy notice or a certification of legal compliance.

---

## 2. Privacy Principles

Nexora AI will follow these principles.

### 2.1 Data Minimization

Collect only information required to provide the requested functionality.

### 2.2 Purpose Limitation

Use information only for clearly defined platform purposes.

### 2.3 Transparency

Explain what information is collected and how it is used.

### 2.4 User Control

Allow users to manage, export, and request deletion of their information.

### 2.5 Security

Protect information against unauthorized access, disclosure, alteration, and loss.

### 2.6 Limited Retention

Do not retain personal information indefinitely without a defined reason.

### 2.7 AI Transparency

Explain when AI processes user information and distinguish AI-generated suggestions from verified facts.

### 2.8 Accountability

Maintain appropriate records of data access, processing, and deletion operations.

---

## 3. Types of Data Collected

Nexora AI may collect different categories of information depending on the features a user chooses to use.

### 3.1 Account Information

| Data | Purpose |
|---|---|
| Full Name | User identification |
| Email Address | Account communication and login |
| Password Hash | Authentication |
| Account ID | Internal user identification |
| Account Created Date | Account management |

Passwords must never be stored in plain text.

### 3.2 Profile Information

| Data | Purpose |
|---|---|
| Education | Career analysis |
| Experience | Job matching |
| Location Preferences | Job discovery |
| Career Goals | Roadmap generation |
| Target Job Roles | Career recommendations |
| Preferred Skills | Career planning |

Only collect optional profile information when the user provides it or enables the related feature.

### 3.3 Resume Information

A resume may contain:

- Name.
- Email.
- Phone number.
- Location.
- Education.
- Work experience.
- Technical skills.
- Projects.
- Certifications.
- Professional links.

Purpose:

- Resume analysis.
- Skill extraction.
- Resume quality evaluation.
- Job matching.
- Career readiness.
- Personalized recommendations.

### 3.4 Job and Employer Information

Nexora AI may process:

- Job titles.
- Job descriptions.
- Required skills.
- Preferred skills.
- Experience requirements.
- Company information.
- Internship details.
- Public job listing URLs.

Purpose:

- Job analysis.
- Employer intelligence.
- Job matching.
- Internship recommendations.

### 3.5 AI Conversation Information

The Career Copilot may process:

- User messages.
- AI responses.
- Relevant conversation history.
- Career-related questions.
- Selected resume or job context.

Purpose:

- Maintain conversational context.
- Provide relevant career guidance.
- Support multi-step career workflows.

### 3.6 Assessment Information

The platform may collect:

- Assessment questions.
- User answers.
- Assessment scores.
- Feedback.
- Skill evidence.
- Completion timestamps.

Purpose:

- Evaluate skill knowledge.
- Track progress.
- Improve career readiness estimates.

### 3.7 GitHub Information

When users provide a repository URL or authorize access, the platform may process:

- Repository name.
- README content.
- Public source files.
- Programming languages.
- Project structure.
- Repository metadata.

Purpose:

- Analyze projects.
- Identify technologies.
- Evaluate project descriptions.
- Recommend portfolio improvements.

Private repository access must require explicit authorization.

### 3.8 Technical Information

Depending on the implementation, the platform may process:

- IP address.
- Browser information.
- Device information.
- Request timestamps.
- Session identifiers.
- Application logs.
- Security events.

Purpose:

- Account security.
- Debugging.
- Performance monitoring.
- Abuse prevention.

Do not collect unnecessary device or tracking information.

---

## 4. Data Collection Rules

Nexora AI should not require users to provide every possible piece of information during registration.

### Required Information

For the initial account:

- Email address.
- Password.
- Name, if required by the product design.

### Optional Information

- Phone number.
- Location.
- Education details.
- Experience.
- GitHub profile.
- LinkedIn profile.
- Career goals.
- Preferred job roles.

### Feature-Based Collection

Collect information when the user uses the relevant feature.

Example:

| Feature | Required Information |
|---|---|
| Resume Analysis | Uploaded resume |
| Job Matching | Resume and job description |
| Career Roadmap | Career goal and relevant skill profile |
| Mock Interview | Target role and interview preferences |
| GitHub Analysis | Repository URL or authorized access |
| Internship Recommendations | Career profile and job preferences |

Do not collect private information simply because it might become useful in a future feature.

---

## 5. Data Processing Architecture

Nexora AI uses a modular backend and AI processing architecture.

### Data Processing Flow

```text
                  USER
                    |
                    v
              REACT FRONTEND
                    |
                    v
              FASTAPI BACKEND
                    |
                    v
             AUTHORIZATION
                    |
                    v
              DATA VALIDATION
                    |
          +---------+---------+
          |         |         |
          v         v         v
       DATABASE   STORAGE   AI ENGINE
          |         |         |
          v         v         v
       PROFILE   RESUMES   LANGGRAPH
          |         |         |
          +---------+---------+
                    |
                    v
              VALIDATE OUTPUT
                    |
                    v
              STORE RESULTS
                    |
                    v
              RETURN RESPONSE
```

### Processing Rules

- Verify user identity before processing private data.
- Verify resource ownership.
- Process only the information needed for the requested task.
- Validate AI outputs.
- Store results under the correct user account.
- Avoid unnecessary copies of private information.
- Record processing status and relevant metadata.

---

## 6. Resume Data Handling

Resume information is one of the most sensitive data categories in Nexora AI.

### 6.1 Resume Upload

When a user uploads a resume:

1. Validate file type.
2. Validate file size.
3. Verify file integrity.
4. Assign a server-generated identifier.
5. Store the file privately.
6. Extract text.
7. Process extracted information.
8. Save structured analysis results.

Supported initial formats:

- PDF.
- DOCX.

### 6.2 Resume Storage

Store resume files separately from database records.

Example:

```text
Private File Storage
    |
    +-- user_101/
    |     |
    |     +-- resume_501.pdf
    |     +-- resume_502.docx
    |
    +-- user_102/
          |
          +-- resume_601.pdf
```

This is a conceptual layout. Production storage should use private object storage and server-generated object keys rather than trusting user-supplied folder names.

### 6.3 Resume Processing

The AI engine may process:

- Extracted resume text.
- Education.
- Experience.
- Skills.
- Projects.
- Certifications.
- Resume structure.

Do not send the entire resume to every AI workflow when only a small portion is required.

### 6.4 Resume Versioning

When a user uploads an updated resume:

- Create a new resume version.
- Preserve version relationships.
- Associate analysis with the correct version.
- Avoid silently replacing the previous file.
- Allow the user to manage old versions.

### 6.5 Resume Privacy Rules

- Resume files must remain private.
- Users can access only their own resumes.
- Resume content must not be used for unrelated purposes.
- Do not expose resume text in application logs.
- External AI processing must follow the applicable consent and provider configuration.
- Support deletion of files and associated analysis.

---

## 7. AI Data Processing and Privacy

Nexora AI uses Ollama, LangChain, LangGraph, and potentially other AI inference providers.

AI processing requires special attention because user information may be included in model prompts.

### 7.1 Local AI Processing

During local development, Ollama runs on the user's configured machine.

```text
FASTAPI
   |
   v
LANGCHAIN
   |
   v
OLLAMA
   |
   v
LOCAL MODEL
```

Local inference can reduce external data transfers, but it does not automatically guarantee privacy.

The application must still secure:

- Local files.
- Database access.
- Model logs.
- Application logs.
- Network connections.
- Backups.

### 7.2 Hosted AI Processing

If Nexora AI uses an external inference provider:

- Identify the provider.
- Document what data is transmitted.
- Review provider retention and training policies.
- Review data processing terms.
- Configure privacy controls.
- Minimize transmitted information.
- Obtain appropriate user consent where required.

Do not claim that user data is never shared with third parties if external AI providers or other processors receive it.

### 7.3 AI Prompt Data Minimization

Before sending information to a model:

- Include only relevant resume sections.
- Remove unnecessary contact information.
- Avoid sending passwords or session identifiers.
- Avoid sending unrelated conversations.
- Use record identifiers where actual content is not required.
- Apply appropriate retention settings.

### 7.4 AI Output Handling

AI-generated information must be treated as a recommendation, not verified personal or professional truth.

The application should:

- Validate structured output.
- Distinguish extracted facts from AI interpretations.
- Avoid inventing user qualifications.
- Allow users to correct inaccurate information.
- Preserve sources where available.
- Avoid presenting predictions as guaranteed outcomes.

---

## 8. Third-Party Data Sharing

Nexora AI may integrate with external services.

Possible integrations include:

- AI inference providers.
- GitHub.
- Job listing providers.
- Email services.
- Object storage.
- Monitoring providers.
- Hosting providers.

### Data Sharing Policy

| Service | Potential Data Shared | Purpose |
|---|---|---|
| Ollama | AI prompts and relevant context | Local inference |
| Hosted AI Provider | Selected prompt content | Remote inference |
| GitHub | Repository URL or authorized access token | Project analysis |
| Job Sources | Search filters | Job discovery |
| Email Provider | Email address and message content | Account communication |
| File Storage | Uploaded files | Resume storage |
| Monitoring Provider | Technical event information | Error monitoring |

The actual data shared depends on the integrations enabled.

### Third-Party Rules

- Use only required integrations.
- Review provider security and privacy policies.
- Do not expose API credentials.
- Restrict access permissions.
- Avoid sending unnecessary personal information.
- Document data transfers.
- Allow users to disconnect integrations where applicable.

---

## 9. Consent and User Control

Users should understand how their information is used.

### 9.1 Account Consent

Explain the information needed to create and operate an account.

### 9.2 Resume Processing Consent

Explain that uploaded resumes will be processed to provide resume analysis and career-related features.

### 9.3 External AI Processing

If resume or career information is sent to an external AI provider, clearly disclose this processing and obtain the appropriate consent where required.

### 9.4 GitHub Authorization

Require explicit authorization before accessing private repositories.

### 9.5 Optional Features

Users should be able to choose whether to use optional features such as:

- GitHub analysis.
- Mock interviews.
- Internship recommendations.
- Career Copilot.
- External integrations.

### 9.6 Consent Records

Store relevant consent information.

Example:

```json
{
  "user_id": "user_123",
  "consent_type": "external_ai_processing",
  "version": "1.0",
  "granted": true,
  "granted_at": "2026-11-18T10:30:00Z",
  "withdrawn_at": null
}
```

The example is illustrative. Actual consent records should also identify the applicable notice version and processing purpose.

Do not treat acceptance of general terms as automatic consent for every optional processing activity.

---

## 10. Data Retention Policy

Nexora AI should define retention periods for every major data category.

The following are proposed product defaults, not legal requirements. Final periods must be selected based on operational needs, applicable law, and user expectations.

| Data | Proposed Retention |
|---|---|
| Account Information | Until account deletion |
| User Profile | Until account deletion |
| Active Resume | Until user deletes it or deletes the account |
| Old Resume Versions | Until user deletes them or deletes the account |
| Resume Analysis | While the associated resume is retained |
| Job Search History | Configurable retention period |
| Saved Jobs | Until user removes them or deletes the account |
| Career Roadmaps | Until user deletes them or deletes the account |
| Assessment Results | Until user deletes them or deletes the account |
| Copilot Conversations | Configurable retention period |
| Application Records | Until user deletes them or deletes the account |
| Security Logs | Defined security retention period |
| Backups | Defined backup retention schedule |

### Retention Rules

- Define retention for each data category.
- Avoid indefinite retention without a reason.
- Support user deletion requests.
- Remove expired records according to policy.
- Ensure backups follow a documented retention schedule.
- Document legally required retention exceptions.

---

## 11. Data Deletion

Users should be able to request deletion of their account and associated personal information.

### Account Deletion Workflow

```text
USER
 |
 v
REQUEST DELETION
 |
 v
VERIFY IDENTITY
 |
 v
SHOW DELETION IMPACT
 |
 v
USER CONFIRMS
 |
 v
REVOKE ACTIVE SESSIONS
 |
 v
DELETE USER FILES
 |
 v
DELETE DATABASE RECORDS
 |
 v
DELETE RELATED EMBEDDINGS
 |
 v
PROCESS BACKUP RETENTION
 |
 v
RECORD DELETION STATUS
```

### Data to Consider for Deletion

- Account information.
- User profile.
- Resumes.
- Resume versions.
- Resume analysis.
- Skills and career history.
- Career roadmaps.
- Assessment results.
- Conversations.
- Application records.
- Uploaded files.
- Vector embeddings.
- Associated integration tokens.

### Deletion Requirements

- Verify the user's identity.
- Explain what will be deleted.
- Revoke active sessions.
- Delete associated files.
- Delete associated database records.
- Remove associated embeddings.
- Revoke integration access where applicable.
- Handle backups according to the documented retention schedule.
- Record completion without retaining unnecessary personal content.

If certain records must be retained for legal or security reasons, document the reason, restrict their use, and apply an appropriate retention period.

---

## 12. Data Export and Portability

Users should be able to obtain a copy of their available personal data.

### Exportable Data

- Account profile.
- Resume metadata.
- Extracted resume information.
- Career skills.
- Career goals.
- Roadmaps.
- Assessment history.
- Application history.
- Copilot conversation history, where supported.

### Export Workflow

```text
USER
 |
 v
REQUEST DATA EXPORT
 |
 v
VERIFY USER
 |
 v
COLLECT AUTHORIZED DATA
 |
 v
GENERATE EXPORT
 |
 v
PROVIDE SECURE DOWNLOAD
 |
 v
EXPIRE DOWNLOAD LINK
```

### Export Security

- Export only the requesting user's data.
- Require authentication.
- Use private storage.
- Use short-lived download links.
- Avoid public export URLs.
- Record export activity.
- Delete temporary export files after the configured period.

---

## 13. Database Privacy

PostgreSQL stores user information and career intelligence.

### Privacy Requirements

- Every private record must have an ownership relationship.
- Use backend authorization checks.
- Restrict database access.
- Avoid exposing internal IDs unnecessarily.
- Apply deletion rules consistently.
- Use encryption in transit.
- Protect database backups.
- Restrict administrative access.

### Data Relationships

```text
USER
 |
 +-- USER PROFILE
 |
 +-- RESUMES
 |     |
 |     +-- RESUME VERSIONS
 |     |
 |     +-- RESUME ANALYSIS
 |
 +-- CAREER SKILLS
 |
 +-- CAREER GOALS
 |
 +-- ROADMAPS
 |
 +-- ASSESSMENTS
 |
 +-- APPLICATIONS
 |
 +-- CONVERSATIONS
       |
       +-- MESSAGES
```

The database schema must preserve ownership and relationships throughout the data lifecycle.

### Vector Data Privacy

pgvector embeddings may represent personal resume or conversation content.

Therefore:

- Apply the same access restrictions as source records.
- Store ownership metadata.
- Filter retrieval by authorized user context.
- Delete embeddings when the associated source is deleted.
- Avoid using private embeddings in unrelated user searches.

---

## 14. Logging and Privacy

Logs help developers troubleshoot application issues, but they can also expose personal information.

### Safe Logging

Log:

- Request identifiers.
- Processing status.
- Error codes.
- Workflow duration.
- Model availability.
- Security events.
- Non-sensitive record identifiers.

### Avoid Logging

- Passwords.
- Session tokens.
- Reset tokens.
- Complete resume text.
- Private messages.
- Full authentication headers.
- Sensitive GitHub tokens.
- Unnecessary contact details.

### Example Safe Log

```json
{
  "event": "resume_analysis_completed",
  "user_id": "user_123",
  "resume_id": "resume_501",
  "status": "success",
  "duration_ms": 4200
}
```

Use access controls and retention policies for logs.

---

## 15. Data Encryption

Nexora AI should protect personal information during transmission and storage.

### 15.1 Encryption in Transit

Use HTTPS/TLS for:

- Frontend to backend communication.
- Backend to hosted database connections.
- Backend to external AI providers.
- Backend to object storage.
- Other network communications.

### 15.2 Encryption at Rest

Use provider-supported encryption for:

- Database storage.
- Object storage.
- Backups.
- Persistent disks.

### 15.3 Application-Level Encryption

Consider additional encryption for particularly sensitive fields when required by the threat model.

Protect encryption keys separately from encrypted data.

### Encryption Rules

- Never store encryption keys in source code.
- Use managed key services where available.
- Restrict key access.
- Rotate keys according to policy.
- Define recovery procedures.

Encryption does not replace access control.

---

## 16. Privacy and AI Agent Permissions

AI agents must process only information required for their assigned tasks.

| Agent | Permitted Data |
|---|---|
| Resume Intelligence Agent | Authorized resume content |
| Resume Quality Agent | Authorized resume analysis |
| Job Description Agent | Submitted job descriptions |
| Employer Intelligence Agent | Relevant public company information |
| Job Matching Agent | Authorized resume and job data |
| Skill Gap Agent | Authorized skills and target role |
| Career Readiness Service | Relevant career profile and evidence |
| Career Roadmap Agent | Career goals and skill gaps |
| Assessment Agent | Selected skill and assessment context |
| Interview Agent | Selected role and interview context |
| GitHub Analysis Agent | Public or authorized repository content |
| Internship Recommendation Agent | Relevant career profile and opportunities |
| Application Preparation Agent | Selected job and authorized resume data |
| Career Copilot Agent | Approved workflows and relevant conversation context |

### Agent Privacy Rules

1. Never retrieve another user's private information.
2. Avoid sending unnecessary resume details to models.
3. Never expose private prompts to unrelated workflows.
4. Restrict tool permissions.
5. Validate workflow ownership.
6. Do not store unnecessary duplicate content.
7. Respect data deletion requests.
8. Keep AI logs free of sensitive information.

---

## 17. Privacy Risk Assessment

Identify and reduce privacy risks before introducing new features.

| Risk | Potential Impact | Mitigation |
|---|---|---|
| Resume exposure | Personal information disclosure | Private storage and authorization |
| Cross-user retrieval | Unauthorized data access | Ownership filters and isolation tests |
| External AI data sharing | Unintended third-party processing | Disclosure, minimization, provider review |
| Prompt injection | Unauthorized tool behavior | Untrusted input handling and restricted tools |
| Excessive retention | Unnecessary personal data storage | Retention and deletion policies |
| Insecure logs | Personal data leakage | Redaction and access control |
| GitHub token exposure | Repository compromise | Secure token storage and limited permissions |
| Backup exposure | Large-scale data disclosure | Encryption and restricted access |
| Unauthorized exports | Personal information disclosure | Authentication and short-lived links |

Review privacy risks whenever a new data source or external integration is introduced.

---

## 18. Privacy Testing Strategy

Privacy must be verified through automated and manual tests.

### Data Collection Tests

- [ ] Only required registration fields are collected.
- [ ] Optional fields remain optional.
- [ ] Feature-specific data is collected only when needed.
- [ ] Consent records are stored correctly.

### Resume Privacy Tests

- [ ] Resume files are private.
- [ ] Users can access only their own resumes.
- [ ] Resume text is not exposed in logs.
- [ ] Old resume versions follow retention rules.
- [ ] Resume deletion removes associated data.

### AI Privacy Tests

- [ ] Only relevant context is sent to models.
- [ ] External AI processing is disclosed.
- [ ] User-specific retrieval is enforced.
- [ ] Prompt injection does not bypass permissions.
- [ ] AI outputs do not expose unrelated user information.

### Data Lifecycle Tests

- [ ] Data export returns only the user's data.
- [ ] Account deletion removes associated records.
- [ ] Related embeddings are deleted.
- [ ] Integration tokens are revoked.
- [ ] Backup retention follows documented policy.

### Logging Tests

- [ ] Passwords are never logged.
- [ ] Session tokens are never logged.
- [ ] Resume content is not logged unnecessarily.
- [ ] Sensitive error details are not exposed.

---

## 19. Legal and Regulatory Considerations

Nexora AI should be designed with applicable privacy and data protection requirements in mind.

Because the initial target market includes India, review the applicable requirements of the Digital Personal Data Protection Act, 2023, its rules and commencement notifications, and other applicable Indian laws.

Depending on the users and markets served, other privacy laws may also apply.

Before public launch:

- Review applicable legal requirements.
- Prepare a user-facing privacy notice.
- Define the purposes of processing.
- Document consent and other applicable legal grounds.
- Define data retention and deletion procedures.
- Review processor and third-party agreements.
- Establish a process for privacy requests.
- Define security incident handling.
- Assess additional requirements for users who are children.
- Obtain qualified legal advice where needed.

This document does not determine the platform's legal role, lawful basis, or compliance status.

---

## 20. Recommended Implementation Order

Privacy controls should be implemented alongside the existing 15-phase roadmap.

| Phase | Privacy Implementation |
|---|---|
| 1 | Secure configuration and data access design |
| 2 | Resume file privacy and validation |
| 3 | Resume data minimization and ownership |
| 4 | Controlled resume analysis processing |
| 5 | Private reports and export controls |
| 6 | Job description input handling |
| 7 | External company data source documentation |
| 8 | Job search history and preference handling |
| 9 | Private matching results |
| 10 | Skill gap data ownership |
| 11 | Career readiness data protection |
| 12 | Career goal and roadmap privacy |
| 13 | Assessment history privacy |
| 14 | Copilot conversation and AI processing privacy |
| 15 | Account deletion, security monitoring, retention and deployment controls |

---

## 21. Final Privacy Decisions

| Area | Initial Decision |
|---|---|
| Data Collection | Minimum necessary information |
| Resume Storage | Private file storage |
| Database | PostgreSQL |
| Vector Search | pgvector with ownership filters |
| AI Processing | Local Ollama initially |
| External AI | Disclosed and controlled |
| Conversation History | User-specific storage |
| Consent | Purpose-specific records where required |
| Data Export | Authenticated export |
| Data Deletion | Controlled deletion workflow |
| Data Retention | Defined per data category |
| Encryption | TLS and provider-supported encryption |
| Logging | Sensitive data redaction |
| User Access | Ownership-based authorization |

---

## 22. Final Privacy Principle

**Users should know what information Nexora AI collects, why it is needed, where it is processed, how long it is retained, and how they can control it.**

Privacy must be designed into every feature, database table, AI workflow, and external integration.