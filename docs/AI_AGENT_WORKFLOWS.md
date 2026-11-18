# AI_AGENT_WORKFLOWS.md

# Nexora AI: AI Agent Workflows

## 1. Purpose

This document defines the AI agent architecture for Nexora AI.

Nexora AI will use specialized AI agents to perform career-related tasks such as:

- Resume analysis.
- Job description analysis.
- Employer intelligence.
- Resume-to-job matching.
- Skill gap detection.
- Career readiness evaluation.
- Personalized career roadmap generation.
- Skill assessments.
- Interview preparation.
- GitHub project analysis.
- Internship recommendations.
- Career Copilot assistance.

The goal is to create a coordinated AI system where each agent has a clearly defined responsibility.

### Main Objectives

1. Build specialized AI agents for specific tasks.
2. Use LangGraph to coordinate agent workflows.
3. Use LangChain for LLM integration and reusable AI components.
4. Use Ollama for local model inference.
5. Use Python for deterministic calculations.
6. Use PostgreSQL for persistent data.
7. Use RAG for knowledge retrieval.
8. Validate AI-generated outputs.
9. Maintain user privacy and access control.
10. Keep the architecture modular and scalable.

---

## 2. What Is an AI Agent?

An AI agent is a software component that can:

- Receive a task.
- Understand the task.
- Access approved tools.
- Retrieve relevant information.
- Perform an operation.
- Produce a structured result.

In Nexora AI, agents will be specialized.

For example:

The Resume Agent analyzes a user's resume, while the Job Intelligence Agent analyzes job requirements.

The Matching Workflow combines their outputs to calculate how well the candidate matches a job.

### Basic Agent Architecture

```text
             USER REQUEST
                  |
                  v
             AI AGENT
                  |
                  v
             UNDERSTAND
                TASK
                  |
                  v
             SELECT TOOL
                  |
                  v
             EXECUTE TASK
                  |
                  v
             VALIDATE RESULT
                  |
                  v
              FINAL OUTPUT
```

An agent should not have unrestricted access to the database, filesystem, or external services.

---

## 3. Multi-Agent Architecture

Nexora AI will use a centralized orchestration architecture.

A central workflow coordinates specialized agents and services.

### High-Level Architecture

```text
                     USER
                       |
                       v
                 REACT FRONTEND
                       |
                       v
                  FASTAPI API
                       |
                       v
                AI ORCHESTRATOR
                    LANGGRAPH
                       |
          +------------+-------------+
          |            |             |
          v            v             v
      RESUME         JOB          CAREER
      AGENT         AGENT         AGENT
          |            |             |
          v            v             v
      Resume       Job Analysis   Roadmap
      Analysis     Employer       Assessment
                   Research       Readiness
          |            |             |
          +------------+-------------+
                       |
                       v
                 MATCHING ENGINE
                       |
                       v
                 CAREER COPILOT
                       |
                       v
                 OLLAMA LOCAL LLM
                       |
                       v
                  POSTGRESQL
```

This diagram represents logical responsibilities. Agents do not need to run as separate servers or separate LLM instances.

---

## 4. Agent Design Principles

Every agent must have a defined scope.

### 4.1 Single Responsibility

Each agent should focus on one major task.

Example:

- Resume Agent analyzes resumes.
- Job Agent analyzes job descriptions.
- Matching Agent compares resumes and jobs.

### 4.2 Limited Tool Access

Agents should receive only the tools needed for their tasks.

### 4.3 Structured Input and Output

Use Pydantic schemas to validate agent inputs and outputs.

### 4.4 Controlled Execution

Use LangGraph to manage execution order, routing, and validation.

### 4.5 Explainable Results

Important recommendations must include reasons and supporting information.

### 4.6 Human Approval

Require user confirmation before important external or irreversible actions.

### 4.7 Avoid Unnecessary Agents

Not every Python function needs to become an AI agent.

Use normal functions for:

- Calculations.
- Database queries.
- Skill normalization.
- File validation.
- Date comparisons.
- Score generation.

Use an LLM agent only when language understanding, reasoning, or tool selection is genuinely needed.

---

## 5. Complete Agent Catalogue

Nexora AI will initially use the following specialized agents and supporting services.

| No. | Agent / Service | Main Responsibility |
|---:|---|---|
| 1 | Resume Intelligence Agent | Extract resume information |
| 2 | Resume Quality Agent | Analyze resume quality |
| 3 | Job Description Agent | Extract job requirements |
| 4 | Employer Intelligence Agent | Analyze company information |
| 5 | Job Discovery Service | Find and filter jobs |
| 6 | Job Matching Agent | Explain resume-to-job matching |
| 7 | Skill Gap Agent | Identify missing and transferable skills |
| 8 | Career Readiness Service | Calculate role readiness |
| 9 | Career Roadmap Agent | Generate learning roadmaps |
| 10 | Skill Assessment Agent | Generate and evaluate assessments |
| 11 | Interview Agent | Conduct mock interviews |
| 12 | GitHub Analysis Agent | Analyze project repositories |
| 13 | Internship Recommendation Agent | Recommend relevant internships |
| 14 | Application Preparation Agent | Help prepare applications |
| 15 | Career Copilot Agent | Coordinate career assistance |

Some catalogue entries are deterministic services rather than autonomous LLM agents. This is intentional.

---

# PART A: SPECIALIZED AGENTS

## 6. Resume Intelligence Agent

**Related features:** 13–20

### Purpose

Extract structured information from uploaded resumes.

### Responsibilities

- Extract personal information.
- Analyze education.
- Analyze work experience.
- Extract technical skills.
- Extract soft skills.
- Analyze projects.
- Identify certifications.
- Understand resume structure.

### Input

```json
{
  "resume_id": "resume_123",
  "resume_text": "Extracted resume text"
}
```

### Tools

- Resume text extraction service.
- PDF and DOCX processors.
- Ollama LLM.
- Pydantic validation.
- Skill normalization service.
- PostgreSQL repository.

### Workflow

```text
START
  |
Load Resume
  |
Extract Sections
  |
Identify Information
  |
Extract Skills
  |
Normalize Skills
  |
Validate Output
  |
Save Resume Intelligence
  |
END
```

### Output

```json
{
  "skills": [
    "Python",
    "Machine Learning",
    "SQL"
  ],
  "education": [],
  "experience": [],
  "projects": [],
  "certifications": [],
  "status": "completed"
}
```

The output is illustrative. Actual results must be derived from the uploaded resume.

### Important Rules

- Never invent missing resume information.
- Preserve original meaning.
- Return null for unavailable fields.
- Allow users to correct extracted information.
- Store extraction results with the relevant resume version.

---

## 7. Resume Quality Agent

**Related features:** 21–27

### Purpose

Evaluate resume quality and suggest improvements.

### Responsibilities

- Identify resume strengths.
- Identify weaknesses.
- Check ATS compatibility.
- Analyze grammar and clarity.
- Evaluate achievement descriptions.
- Generate improvement recommendations.

### Tools

- Resume Intelligence Service.
- Rule-Based Analysis Engine.
- Ollama.
- Pydantic Validation.

### Workflow

```text
START
  |
Load Structured Resume
  |
Check Resume Structure
  |
Analyze Content
  |
Evaluate Achievements
  |
Check ATS Compatibility
  |
Calculate Quality Score
  |
Generate Recommendations
  |
Validate Report
  |
END
```

### Output

```json
{
  "resume_score": 78,
  "strengths": [
    "Relevant technical skills",
    "Project experience"
  ],
  "weaknesses": [
    "Limited measurable achievements"
  ],
  "recommendations": [
    "Add measurable results to project descriptions"
  ]
}
```

### Scoring Rule

Python calculates the score using documented criteria.

The LLM provides explanations and recommendations.

Do not claim that the score represents a specific company's ATS scoring algorithm.

---

## 8. Job Description Agent

**Related features:** 33–38

### Purpose

Convert unstructured job descriptions into structured job requirements.

### Responsibilities

- Identify job title.
- Identify company name.
- Extract mandatory skills.
- Extract preferred skills.
- Identify experience requirements.
- Identify education requirements.
- Analyze responsibilities.

### Tools

- URL import service.
- Text extraction service.
- Ollama.
- Skill normalization service.
- Pydantic validation.

### Workflow

```text
START
  |
Receive Job Description
  |
Extract Job Information
  |
Identify Requirements
  |
Extract Skills
  |
Separate Mandatory and Preferred
  |
Normalize Skills
  |
Validate Output
  |
Save Job Data
  |
END
```

### Output

```json
{
  "job_title": "AI Engineer Intern",
  "required_skills": [
    "Python",
    "Machine Learning"
  ],
  "preferred_skills": [
    "PyTorch",
    "LangChain"
  ],
  "experience_required": "Entry Level",
  "education_required": "Relevant Degree"
}
```

---

## 9. Employer Intelligence Agent

**Related features:** 39–45

### Purpose

Research companies and understand their hiring requirements.

### Responsibilities

- Analyze public company information.
- Identify technology requirements.
- Understand hiring expectations.
- Analyze fresher opportunities.
- Analyze internship opportunities.
- Generate employer intelligence reports.

### Tools

- Approved web research or job-source integrations.
- Company information retrieval.
- RAG retriever.
- Ollama.
- Source validation service.

### Workflow

```text
START
  |
Receive Company Name
  |
Retrieve Public Sources
  |
Extract Company Information
  |
Analyze Job Listings
  |
Identify Skill Demand
  |
Analyze Fresher Opportunities
  |
Validate Sources
  |
Generate Employer Report
  |
END
```

### Output

```json
{
  "company": "Example Company",
  "technology_requirements": [
    "Python",
    "SQL",
    "Machine Learning"
  ],
  "entry_level_opportunities": [],
  "sources": [],
  "last_checked": "2026-11-18"
}
```

### Rules

- Prefer official company sources.
- Preserve source URLs.
- Record retrieval dates.
- Do not invent hiring requirements.
- Clearly identify unavailable information.

---

## 10. Job Discovery Service

**Related features:** 46–51

### Purpose

Find and filter relevant job opportunities.

This should initially be a normal backend service, not an autonomous AI agent.

### Responsibilities

- Search jobs.
- Filter by role.
- Filter by location.
- Filter by experience.
- Retrieve job details.
- Save jobs.

### Tools

- Approved job APIs.
- Public job sources.
- PostgreSQL.
- Search and filtering functions.

### Workflow

```text
START
  |
Receive Search Filters
  |
Query Job Sources
  |
Normalize Job Data
  |
Remove Duplicates
  |
Apply Filters
  |
Return Job Results
  |
END
```

Use AI only when semantic role interpretation or natural-language search provides additional value.

---

## 11. Job Matching Agent

**Related features:** 52–57

### Purpose

Explain how well a resume matches a selected job.

### Responsibilities

- Analyze matching skills.
- Identify missing skills.
- Compare experience.
- Compare education.
- Evaluate project relevance.
- Explain the final match score.

### Tools

- Resume Intelligence Service.
- Job Description Service.
- Skill Matching Engine.
- Embedding Service.
- Python Scoring Engine.
- Ollama.

### Workflow

```text
START
  |
Load Resume
  |
Load Job
  |
Normalize Skills
  |
Match Required Skills
  |
Match Preferred Skills
  |
Compare Experience
  |
Compare Education
  |
Calculate Match Score
  |
Generate Explanation
  |
Save Result
  |
END
```

### Output

```json
{
  "match_score": 82,
  "matched_skills": [
    "Python",
    "Machine Learning"
  ],
  "missing_skills": [
    "PyTorch"
  ],
  "experience_match": 90,
  "education_match": 85,
  "explanation": "The candidate has relevant technical skills but lacks evidence of PyTorch experience."
}
```

### Scoring Rule

Use deterministic Python calculations for numerical scores.

The LLM must explain the calculated result, not invent it.

The score is a compatibility indicator, not a hiring probability.

---

## 12. Skill Gap Agent

**Related features:** 58–62

### Purpose

Identify the skills a user needs to improve for a selected career role.

### Responsibilities

- Identify missing skills.
- Identify transferable skills.
- Prioritize important skills.
- Generate skill gap reports.
- Compare skill requirements.

### Tools

- Resume Intelligence Service.
- Job Matching Service.
- Skill Taxonomy.
- Embedding Service.
- Python Priority Engine.
- Ollama.

### Workflow

```text
START
  |
Load Current Skills
  |
Load Target Role Requirements
  |
Normalize Skills
  |
Compare Skills
  |
Identify Missing Skills
  |
Identify Transferable Skills
  |
Calculate Priority
  |
Generate Explanation
  |
END
```

### Output

```json
{
  "matched_skills": [
    "Python",
    "SQL"
  ],
  "missing_skills": [
    "PyTorch",
    "Deep Learning"
  ],
  "transferable_skills": [
    "Machine Learning"
  ],
  "priority_skills": [
    "PyTorch"
  ]
}
```

### Important Rule

A related skill is not automatically equivalent to a required skill.

The system should explain why it considers a skill transferable.

---

## 13. Career Readiness Service

**Related features:** 63–66

### Purpose

Calculate how prepared a user is for a selected target role.

This should primarily be a deterministic Python service.

### Responsibilities

- Calculate career readiness.
- Evaluate role readiness.
- Generate readiness breakdown.
- Track readiness progress.

### Inputs

- User skills.
- Target job requirements.
- Experience.
- Education.
- Projects.
- Assessment evidence.

### Workflow

```text
START
  |
Load Career Profile
  |
Load Role Requirements
  |
Load Skill Evidence
  |
Calculate Readiness Factors
  |
Calculate Overall Score
  |
Save Score Snapshot
  |
Return Explanation
  |
END
```

### Output

```json
{
  "target_role": "AI Engineer",
  "readiness_score": 72,
  "breakdown": {
    "skills": 75,
    "experience": 65,
    "projects": 80,
    "education": 70
  }
}
```

Use documented and consistent scoring rules.

Do not ask the LLM to generate numerical readiness scores without calculation logic.

---

## 14. Career Roadmap Agent

**Related features:** 67–72

### Purpose

Generate personalized learning roadmaps based on career goals and skill gaps.

### Responsibilities

- Understand career goals.
- Analyze current skills.
- Prioritize missing skills.
- Retrieve learning resources.
- Recommend projects.
- Generate roadmap stages.
- Support progress updates.

### Tools

- Career Profile Service.
- Skill Gap Service.
- RAG Retriever.
- Learning Resource Database.
- Ollama.
- Pydantic Validation.

### Workflow

```text
START
  |
Load Career Goal
  |
Load Current Skills
  |
Load Skill Gaps
  |
Prioritize Skills
  |
Retrieve Learning Resources
  |
Recommend Projects
  |
Generate Roadmap
  |
Validate Roadmap
  |
Save Roadmap
  |
END
```

### Output

```json
{
  "career_goal": "AI Engineer",
  "stages": [
    {
      "title": "Python Foundations",
      "skills": [
        "Python",
        "NumPy",
        "Pandas"
      ],
      "projects": [
        "Data Analysis Project"
      ]
    },
    {
      "title": "Machine Learning",
      "skills": [
        "Scikit-learn",
        "Model Evaluation"
      ],
      "projects": [
        "Machine Learning Prediction System"
      ]
    }
  ]
}
```

The output is an illustrative structure.

### Rules

- Personalize recommendations using actual skill gaps.
- Avoid recommending skills the user has already demonstrated unnecessarily.
- Include relevant learning resources.
- Avoid fabricated course links.
- Allow users to edit roadmaps.

---

## 15. Skill Assessment Agent

**Related features:** 73–77

### Purpose

Generate and evaluate skill assessments.

### Responsibilities

- Generate technical questions.
- Select difficulty.
- Generate practical challenges.
- Evaluate submitted answers.
- Create feedback.
- Update skill evidence.

### Tools

- Ollama.
- Question Bank.
- Assessment Rules Engine.
- Restricted Code Execution Service.
- Pydantic Validation.

### Workflow

```text
START
  |
Select Skill
  |
Select Difficulty
  |
Generate Questions
  |
Validate Questions
  |
Present Assessment
  |
Receive Answers
  |
Evaluate Answers
  |
Calculate Score
  |
Save Attempt
  |
Update Skill Evidence
  |
END
```

### Evaluation Strategy

| Assessment Type | Evaluation |
|---|---|
| Multiple Choice | Deterministic |
| Short Answer | Rubric + LLM |
| Technical Explanation | Rubric + LLM |
| Coding Challenge | Test Cases + Sandboxed Execution |
| Practical Project | Defined Rubric + Human Review |

### Rules

- Do not treat generated questions as verified certification exams.
- Use consistent evaluation rubrics.
- Never execute untrusted code in the main backend process.
- Allow users to review feedback.

---

## 16. Interview Agent

**Related features:** 79–80

### Purpose

Conduct mock interviews and provide structured feedback.

### Responsibilities

- Generate role-specific questions.
- Ask interview questions.
- Evaluate answers.
- Identify improvement areas.
- Generate interview reports.

### Tools

- Ollama.
- Career Profile Service.
- Job Description Service.
- Interview Question Bank.
- Pydantic Validation.

### Workflow

```text
START
  |
Select Target Role
  |
Select Interview Type
  |
Generate Questions
  |
Ask Question
  |
Receive Answer
  |
Evaluate Answer
  |
Generate Feedback
  |
Continue Interview
  |
Generate Final Report
  |
END
```

### Output

```json
{
  "question": "Explain the difference between supervised and unsupervised learning.",
  "feedback": {
    "relevance": 85,
    "technical_accuracy": 80,
    "clarity": 75
  },
  "improvements": [
    "Include a practical example."
  ]
}
```

Scores should be based on a defined evaluation rubric and should be presented as approximate AI feedback.

---

## 17. GitHub Analysis Agent

**Related feature:** 81

### Purpose

Analyze public or explicitly authorized GitHub repositories.

### Responsibilities

- Read repository metadata.
- Understand project structure.
- Identify technologies.
- Analyze README files.
- Inspect relevant source files.
- Identify project strengths.
- Suggest improvements.

### Tools

- GitHub API or approved repository access.
- Repository File Reader.
- Code Parsing Utilities.
- Ollama.
- Pydantic Validation.

### Workflow

```text
START
  |
Receive Repository URL
  |
Validate Repository Access
  |
Retrieve Repository Metadata
  |
Read README
  |
Inspect Relevant Files
  |
Identify Technology Stack
  |
Analyze Project Structure
  |
Generate Report
  |
END
```

### Rules

- Respect repository permissions and API limits.
- Do not claim to inspect inaccessible files.
- Treat repository content as untrusted input.
- Never execute repository code during ordinary analysis.
- Do not expose private repository data.

---

## 18. Internship Recommendation Agent

**Related feature:** 82

### Purpose

Recommend internships relevant to a user's profile.

### Responsibilities

- Understand user skills.
- Identify target roles.
- Retrieve internship opportunities.
- Compare requirements.
- Rank relevant opportunities.
- Explain recommendations.

### Tools

- Job Discovery Service.
- Resume Intelligence Service.
- Matching Engine.
- Skill Gap Service.
- Ollama.

### Workflow

```text
START
  |
Load User Profile
  |
Load Career Goal
  |
Retrieve Internships
  |
Filter Eligibility
  |
Match Requirements
  |
Rank Opportunities
  |
Generate Explanation
  |
END
```

### Rules

- Show original application links.
- Display availability dates when known.
- Do not claim an opportunity is open without evidence.
- Explain eligibility gaps.
- Avoid inventing internship details.

---

## 19. Application Preparation Agent

**Related feature:** 84

### Purpose

Help users prepare for job and internship applications.

### Responsibilities

- Analyze the target job.
- Suggest resume improvements.
- Draft application messages.
- Prepare cover letters.
- Suggest interview preparation steps.
- Track preparation tasks.

### Tools

- Resume Intelligence Service.
- Job Description Service.
- Matching Engine.
- Ollama.
- Application Tracker.

### Workflow

```text
START
  |
Select Job
  |
Load Resume
  |
Analyze Job Requirements
  |
Identify Application Gaps
  |
Generate Preparation Plan
  |
Draft Application Content
  |
User Reviews Content
  |
Save Application Preparation
  |
END
```

### Human Approval

The user must review generated application content.

The agent should not submit applications automatically without explicit authorization and confirmation.

---

## 20. Career Copilot Agent

**Related feature:** 78

### Purpose

Provide one conversational interface for Nexora AI career services.

The Career Copilot is the main user-facing AI assistant.

It coordinates specialized workflows rather than performing every operation independently.

### Responsibilities

- Understand user requests.
- Identify user intent.
- Retrieve relevant context.
- Select the appropriate workflow.
- Coordinate specialized agents.
- Generate career guidance.
- Explain results.
- Maintain conversation context.

### Available Capabilities

- Resume analysis.
- Job analysis.
- Job matching.
- Skill gap analysis.
- Career readiness.
- Career roadmap.
- Interview preparation.
- GitHub project analysis.
- Internship recommendations.
- Application preparation.

### Copilot Architecture

```text
                  USER MESSAGE
                       |
                       v
                 CAREER COPILOT
                       |
                       v
                  INTENT ROUTER
                       |
       +---------------+----------------+
       |               |                |
       v               v                v
  RESUME TASK       JOB TASK       CAREER TASK
       |               |                |
       v               v                v
  Resume Agent     Job Agent       Career Agent
       |               |                |
       +---------------+----------------+
                       |
                       v
                  CONTEXT MERGE
                       |
                       v
                  RESPONSE LLM
                       |
                       v
                  FINAL RESPONSE
```

### Example User Requests

| User Request | Selected Workflow |
|---|---|
| Analyze my resume | Resume Intelligence |
| Find AI internships | Internship Recommendation |
| Compare my resume with this job | Job Matching |
| Which skills am I missing? | Skill Gap |
| Create a learning plan | Career Roadmap |
| Prepare me for an interview | Interview |
| Analyze my GitHub project | GitHub Analysis |

### Important Rules

- Retrieve only relevant user context.
- Verify authorization before accessing records.
- Do not expose one user's information to another.
- Do not execute sensitive actions without confirmation.
- Provide clear explanations and source references.
- Ask for clarification when essential information is missing.

---

# PART B: AGENT ORCHESTRATION

## 21. LangGraph Orchestration Architecture

LangGraph will coordinate workflows and maintain their state.

### Main Responsibilities

- Route tasks.
- Execute nodes.
- Share validated state.
- Handle conditional paths.
- Validate agent outputs.
- Manage retries.
- Track workflow status.

### Central Workflow

```text
START
  |
Receive Request
  |
Authenticate User
  |
Identify Intent
  |
Select Workflow
  |
  +------------------------------+
  |              |               |
  v              v               v
Resume          Job           Career
Workflow       Workflow       Workflow
  |              |               |
  +--------------+---------------+
                 |
                 v
          Validate Results
                 |
                 v
          Store Final Output
                 |
                 v
          Return API Response
                 |
                END
```

The orchestration layer should coordinate services without giving agents unrestricted access to one another.

---

## 22. Agent Communication

Agents should exchange structured data rather than uncontrolled natural-language messages wherever possible.

### Example

The Resume Agent produces structured resume data.

The Job Description Agent produces structured job requirements.

The Matching Workflow consumes both.

```text
Resume Agent
     |
     v
Resume Schema
     |
     |
Job Agent
     |
     v
Job Schema
     |
     v
Matching Workflow
     |
     v
Match Result Schema
     |
     v
Skill Gap Workflow
```

### Communication Rules

1. Use Pydantic schemas.
2. Validate data at workflow boundaries.
3. Pass record IDs instead of unnecessarily copying large documents.
4. Include provenance for important extracted information.
5. Keep database writes inside authorized services.
6. Avoid passing private information between unrelated workflows.

---

## 23. Agent Tool Architecture

Tools are controlled functions that agents can use.

### Proposed Tool Categories

| Tool | Responsibility |
|---|---|
| Resume Retrieval Tool | Retrieve authorized resume data |
| Job Retrieval Tool | Retrieve job information |
| Company Research Tool | Retrieve public company information |
| Skill Search Tool | Search the skill taxonomy |
| Vector Search Tool | Retrieve relevant knowledge |
| Matching Tool | Calculate job match |
| Readiness Tool | Calculate career readiness |
| Roadmap Tool | Generate roadmap records |
| Assessment Tool | Create assessment tasks |
| GitHub Tool | Retrieve authorized repository information |
| Application Tool | Manage application preparation records |

### Tool Rules

- Validate all tool inputs.
- Verify user permissions.
- Apply request timeouts.
- Restrict external URL access.
- Limit tool execution.
- Record important actions.
- Require user approval for sensitive actions.

Do not allow an LLM to construct arbitrary SQL queries or execute unrestricted shell commands.

---

## 24. Agent State Management

Each workflow should have a defined state schema.

Example:

```python
from typing import TypedDict


class CareerState(TypedDict):
    user_id: str
    task_id: str
    intent: str
    input_data: dict
    retrieved_context: list
    agent_result: dict
    errors: list
    status: str
```

### State Rules

- Keep state limited to required data.
- Avoid storing full documents when IDs are sufficient.
- Do not store secrets in workflow state.
- Validate state updates.
- Persist important workflow results.
- Separate temporary state from long-term database records.

---

## 25. Agent Memory Strategy

Nexora AI should distinguish between different types of memory.

| Memory Type | Purpose | Storage |
|---|---|---|
| Workflow State | Current task information | LangGraph state |
| Conversation History | Previous Copilot messages | PostgreSQL |
| User Career Profile | Skills, goals, preferences | PostgreSQL |
| Knowledge Base | General career knowledge | PostgreSQL + pgvector |
| Resume Data | Extracted resume information | PostgreSQL |
| Application History | Job application progress | PostgreSQL |

### Memory Rules

- Use workflow state for current execution.
- Use PostgreSQL for persistent application data.
- Use pgvector for semantic retrieval.
- Retrieve conversation history selectively.
- Do not treat conversation history as verified resume facts.
- Respect user privacy and deletion requests.

---

## 26. Agent Failure and Retry Handling

Agents can fail because of:

- Invalid LLM output.
- Model timeout.
- Ollama unavailable.
- Missing context.
- Tool failure.
- Database errors.
- External service errors.

### Failure Workflow

```text
Agent Execution
      |
      v
Validate Output
      |
      +------ Valid ------> Continue
      |
      +------ Invalid ----> Retry
                                |
                                v
                          Retry Limit
                                |
                     +----------+----------+
                     |                     |
                     v                     v
                  Retry                  Failed
                     |                     |
                     v                     v
                Agent Node            Error Handler
```

### Retry Rules

- Retry transient failures.
- Set a maximum retry count.
- Avoid infinite graph loops.
- Do not repeat non-idempotent actions blindly.
- Preserve successful intermediate results.
- Return clear failure messages.

---

## 27. Security and Permissions

Every agent must operate under restricted permissions.

### Access Rules

| Operation | Permission |
|---|---|
| Read Own Resume | Authenticated User |
| Read Another User's Resume | Not Allowed |
| Analyze Public Job | Allowed |
| Read Private Repository | Explicit Authorization |
| Update Career Roadmap | User Authorization |
| Create Assessment | Authenticated User |
| Submit Job Application | Explicit User Approval |
| Delete User Data | Authorized User Request |

### Security Requirements

- Authenticate every protected API request.
- Enforce user ownership in database operations.
- Validate agent tool arguments.
- Restrict external network requests.
- Protect API credentials.
- Prevent prompt injection.
- Keep private data out of unnecessary prompts.
- Require confirmation before external side effects.
- Log security events without exposing private content.

---

## 28. Agent Evaluation Strategy

Each agent should have independent evaluation tests.

| Agent | Evaluation Criteria |
|---|---|
| Resume Intelligence | Extraction accuracy |
| Resume Quality | Recommendation relevance |
| Job Description | Requirement extraction accuracy |
| Employer Intelligence | Source reliability |
| Job Matching | Matching accuracy |
| Skill Gap | Missing skill detection |
| Career Readiness | Scoring consistency |
| Career Roadmap | Relevance and feasibility |
| Skill Assessment | Question and evaluation quality |
| Interview | Feedback consistency |
| GitHub Analysis | Evidence-based observations |
| Internship Recommendation | Opportunity relevance |
| Application Preparation | Content quality |
| Career Copilot | Intent routing and answer quality |

### Evaluation Dataset

Create fixed test cases containing:

- Different resume formats.
- Different job descriptions.
- Multiple career roles.
- Different experience levels.
- Similar and unrelated skills.
- Incomplete user profiles.
- Questions with insufficient context.

Record:

- Input.
- Expected result.
- Actual result.
- Accuracy.
- Response time.
- Errors.

Use mocked model outputs for unit tests and real local models for integration tests.

---

# PART C: IMPLEMENTATION

## 29. Recommended Folder Structure

```text
backend/
|
+-- app/
    |
    +-- agents/
    |   |
    |   +-- resume_agent.py
    |   +-- resume_quality_agent.py
    |   +-- job_description_agent.py
    |   +-- employer_intelligence_agent.py
    |   +-- matching_agent.py
    |   +-- skill_gap_agent.py
    |   +-- roadmap_agent.py
    |   +-- assessment_agent.py
    |   +-- interview_agent.py
    |   +-- github_agent.py
    |   +-- internship_agent.py
    |   +-- application_agent.py
    |   +-- copilot_agent.py
    |
    +-- workflows/
    |   |
    |   +-- resume_workflow.py
    |   +-- job_workflow.py
    |   +-- matching_workflow.py
    |   +-- skill_gap_workflow.py
    |   +-- roadmap_workflow.py
    |   +-- assessment_workflow.py
    |   +-- interview_workflow.py
    |   +-- copilot_workflow.py
    |
    +-- tools/
    |   |
    |   +-- resume_tools.py
    |   +-- job_tools.py
    |   +-- skill_tools.py
    |   +-- retrieval_tools.py
    |   +-- github_tools.py
    |   +-- career_tools.py
    |
    +-- ai/
    |   |
    |   +-- llm/
    |   +-- prompts/
    |   +-- schemas/
    |   +-- embeddings/
    |   +-- retrieval/
    |
    +-- services/
    |
    +-- models/
    |
    +-- api/
```

Keep agents, workflows, tools, and business services separate.

Not every agent needs a separate Python file if it is only a small function. Organize modules around real complexity.

---

## 30. Development Phases

Implement the agent system gradually.

| Stage | Agent Development |
|---|---|
| 1 | Resume Intelligence |
| 2 | Resume Quality |
| 3 | Job Description Analysis |
| 4 | Employer Intelligence |
| 5 | Job Matching |
| 6 | Skill Gap Analysis |
| 7 | Career Readiness |
| 8 | Career Roadmap |
| 9 | Skill Assessment |
| 10 | Interview Preparation |
| 11 | GitHub Analysis |
| 12 | Internship Recommendations |
| 13 | Application Preparation |
| 14 | Career Copilot |
| 15 | Agent Testing, Security, and Optimization |

The Job Discovery and Career Readiness modules should remain deterministic services initially.

Build the individual services first, then connect them through LangGraph workflows.

---

## 31. Initial Dependencies

Install the required packages:

```bash
pip install langchain
pip install langchain-ollama
pip install langgraph
pip install pydantic
pip install sentence-transformers
pip install langchain-text-splitters
pip install httpx
```

Additional packages should be introduced only when their functionality is needed.

---

## 32. Local Model Strategy

The initial development machine has:

- 24 GB RAM.
- NVIDIA RTX 2040.
- 4 GB GPU VRAM.

### Initial Model Candidate

`qwen2.5:3b`

Use it for:

- Resume information extraction experiments.
- Job requirement extraction.
- Career explanations.
- Roadmap generation experiments.
- Copilot responses.

### Model Execution Rules

- Start with one model.
- Avoid simultaneous large-model execution.
- Use smaller prompts.
- Limit retrieved context.
- Validate outputs.
- Measure CPU, RAM, GPU, and response time.
- Evaluate alternatives before selecting production models.

Do not create a separate LLM instance for every agent. Reuse the configured model service where practical.

---

## 33. MVP Agent Implementation

The first working version should not implement all agents at once.

### MVP Priority

| Priority | Agent / Service | Reason |
|---|---|---|
| 1 | Resume Intelligence | Foundation for user career data |
| 2 | Resume Quality | Provides immediate resume value |
| 3 | Job Description | Understands employer requirements |
| 4 | Job Matching | Connects resume and job data |
| 5 | Skill Gap | Identifies missing skills |
| 6 | Career Roadmap | Converts gaps into action |
| 7 | Career Copilot | Connects the core capabilities |

Other agents can be introduced after the core workflows work reliably.

### First End-to-End Workflow

```text
USER
 |
 v
UPLOAD RESUME
 |
 v
RESUME INTELLIGENCE
 |
 v
RESUME QUALITY
 |
 v
ADD JOB DESCRIPTION
 |
 v
JOB DESCRIPTION ANALYSIS
 |
 v
JOB MATCHING
 |
 v
SKILL GAP ANALYSIS
 |
 v
CAREER ROADMAP
 |
 v
CAREER COPILOT
```

This workflow delivers the main Nexora AI value before advanced agent capabilities are introduced.

---

## 34. Final Architecture Decisions

| Area | Decision |
|---|---|
| Agent Framework | LangGraph |
| LLM Integration | LangChain |
| Local Model Runtime | Ollama |
| Initial LLM Candidate | Qwen 2.5 3B |
| Backend | FastAPI |
| Programming Language | Python |
| Structured Output | Pydantic |
| Main Database | PostgreSQL |
| Vector Search | pgvector |
| Embeddings | Sentence Transformers |
| Persistent Data | PostgreSQL |
| Workflow State | LangGraph |
| API Communication | REST |

These are the initial architecture decisions and candidates. Model and infrastructure choices should be validated through implementation and evaluation.

---

## 35. Final Development Principles

1. Build specialized agents with clear responsibilities.
2. Use LangGraph for orchestration.
3. Use LangChain for model integration.
4. Use Python for deterministic operations.
5. Use Pydantic for structured validation.
6. Restrict agent tools and permissions.
7. Use RAG when external or stored knowledge is required.
8. Keep user data isolated.
9. Require approval for sensitive external actions.
10. Evaluate every agent independently.
11. Avoid unnecessary autonomous agents.
12. Build the MVP before expanding the agent ecosystem.

**Final Goal:** Build a coordinated AI agent system that connects resume intelligence, employer analysis, job matching, skill development, assessments, and career guidance into one reliable Nexora AI platform.