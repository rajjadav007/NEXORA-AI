# LANGCHAIN_LANGGRAPH.md

# Nexora AI: LangChain and LangGraph Architecture

## 1. Purpose

This document defines how Nexora AI will use LangChain and LangGraph to build modular AI workflows.

The objective is to create an AI architecture that can:

- Process resumes.
- Analyze job descriptions.
- Match candidates with jobs.
- Identify skill gaps.
- Generate career roadmaps.
- Evaluate assessments.
- Power the AI Career Copilot.

The system should remain modular, testable, explainable, and compatible with local AI models.

### Core Technology

| Technology | Responsibility |
|---|---|
| Python | Main AI development language |
| FastAPI | Backend API |
| Ollama | Local LLM runtime |
| LangChain | LLM integration and reusable AI components |
| LangGraph | Multi-step AI workflow orchestration |
| Pydantic | Structured output validation |
| PostgreSQL | Persistent application data |
| pgvector | Vector storage and retrieval |
| Sentence Transformers | Embedding generation |

---

## 2. LangChain vs LangGraph

Both frameworks serve different purposes.

### LangChain

LangChain is used to connect language models with application logic.

Responsibilities:

- Connect to Ollama.
- Create reusable prompts.
- Manage model calls.
- Generate structured outputs.
- Integrate embeddings.
- Retrieve relevant documents.
- Build reusable AI components.

Example:

```text
User Input
    |
Prompt Template
    |
Ollama Model
    |
Structured Output
    |
Pydantic Validation
    |
Final Result
```

### LangGraph

LangGraph is used to coordinate multi-step workflows.

Responsibilities:

- Manage workflow states.
- Execute multiple processing steps.
- Control workflow transitions.
- Support conditional routing.
- Handle retries and validation paths.
- Maintain workflow context.
- Coordinate AI agents and tools when needed.

Example:

```text
START
  |
Extract Resume
  |
Analyze Skills
  |
Validate Results
  |
Generate Report
  |
Save Results
  |
END
```

### Main Difference

| LangChain | LangGraph |
|---|---|
| Connects LLMs with application components | Coordinates multi-step workflows |
| Manages prompts and model calls | Manages graph state |
| Supports structured output | Supports conditional execution |
| Supports retrieval | Supports workflow routing |
| Useful for individual AI operations | Useful for complex AI processes |

**Development Rule:** Use LangChain for individual AI operations and LangGraph when a workflow has multiple dependent steps or decisions. Do not use LangGraph for every simple function.

---

## 3. Nexora AI Architecture

### High-Level Architecture

```text
                  NEXORA AI
                      |
                      v
                FASTAPI BACKEND
                      |
                      v
                  AI SERVICE
                      |
             +--------+--------+
             |                 |
             v                 v
          LANGCHAIN         LANGGRAPH
             |                 |
             v                 v
        LLM OPERATIONS     WORKFLOWS
             |                 |
             +--------+--------+
                      |
                      v
                    OLLAMA
                      |
                      v
               LOCAL LLM MODEL
```

### Component Responsibilities

| Component | Responsibility |
|---|---|
| FastAPI | Receive and validate requests |
| AI Service | Provide application-level AI functions |
| LangChain | Manage model calls and prompts |
| LangGraph | Coordinate complex workflows |
| Ollama | Run local LLMs |
| Pydantic | Validate generated data |
| PostgreSQL | Store results |
| pgvector | Retrieve relevant context |

---

## 4. AI Module Structure

Keep AI functionality separate from API routes and database models.

Recommended backend structure:

```text
backend/
|
+-- app/
    |
    +-- api/
    |   +-- routes/
    |
    +-- ai/
    |   |
    |   +-- llm/
    |   |   +-- ollama_client.py
    |   |   +-- model_config.py
    |   |
    |   +-- prompts/
    |   |   +-- resume/
    |   |   +-- jobs/
    |   |   +-- matching/
    |   |   +-- career/
    |   |   +-- copilot/
    |   |
    |   +-- chains/
    |   |   +-- resume_chain.py
    |   |   +-- job_chain.py
    |   |   +-- matching_chain.py
    |   |
    |   +-- graphs/
    |   |   +-- resume_graph.py
    |   |   +-- matching_graph.py
    |   |   +-- roadmap_graph.py
    |   |   +-- copilot_graph.py
    |   |
    |   +-- nodes/
    |   |   +-- resume_nodes.py
    |   |   +-- matching_nodes.py
    |   |   +-- roadmap_nodes.py
    |   |
    |   +-- schemas/
    |   |
    |   +-- retrieval/
    |   |   +-- embedding_service.py
    |   |   +-- retriever.py
    |   |
    |   +-- services/
    |       +-- resume_ai_service.py
    |       +-- matching_ai_service.py
    |       +-- copilot_service.py
    |
    +-- services/
    +-- models/
    +-- schemas/
    +-- database/
```

The exact structure can grow as the project develops. Avoid creating empty modules before they are needed.

---

## 5. Ollama Integration with LangChain

Ollama will provide local LLM inference.

### Model Configuration

Initial candidate:

`qwen2.5:3b`

This is a starting model for experimentation, not a final production selection.

### Install Packages

```bash
pip install langchain langchain-ollama langgraph
```

### Create `ollama_client.py`

```python
from langchain_ollama import ChatOllama


llm = ChatOllama(
    model="qwen2.5:3b",
    base_url="http://localhost:11434",
    temperature=0.2,
)
```

### Test the Model

```python
response = llm.invoke(
    "Explain what a resume-to-job matching system does."
)

print(response.content)
```

### Development Rules

- Keep model configuration centralized.
- Avoid creating a new model client for every request.
- Configure timeouts and error handling.
- Avoid sending unnecessary resume content.
- Test response quality before selecting a model.
- Keep the model replaceable.

---

## 6. Prompt Engineering

Prompts should be stored separately from business logic.

### Recommended Prompt Structure

```text
prompts/
|
+-- resume/
|   +-- extract_resume.txt
|   +-- analyze_resume.txt
|   +-- improve_resume.txt
|
+-- jobs/
|   +-- extract_requirements.txt
|   +-- analyze_job.txt
|
+-- matching/
|   +-- explain_match.txt
|   +-- identify_skill_gaps.txt
|
+-- career/
|   +-- generate_roadmap.txt
|
+-- copilot/
    +-- career_assistant.txt
```

### Prompt Example

`extract_resume.txt`

```text
You are a resume information extraction assistant.

Analyze the supplied resume text.

Extract the following information:

1. Personal information
2. Education
3. Work experience
4. Technical skills
5. Soft skills
6. Projects
7. Certifications

Rules:

- Only extract information supported by the resume.
- Do not invent missing information.
- Use null when a field is unavailable.
- Preserve the meaning of the original content.
- Return valid structured JSON.
```

### Prompt Best Practices

1. Define one clear task per prompt.
2. Provide relevant context.
3. Specify the expected output.
4. Include rules for missing information.
5. Avoid ambiguous instructions.
6. Validate generated results.
7. Treat uploaded documents as untrusted input.

---

## 7. Structured Output with Pydantic

LLM output must be validated before it enters the database.

### Example Schema

```python
from pydantic import BaseModel, Field


class Skill(BaseModel):
    name: str
    category: str | None = None
    confidence: float = Field(ge=0, le=1)


class ResumeAnalysis(BaseModel):
    name: str | None = None
    email: str | None = None
    skills: list[Skill] = []
    education: list[dict] = []
    experience: list[dict] = []
    projects: list[dict] = []
    certifications: list[dict] = []
```

Use independent schemas for education, experience, projects, and certifications as the application matures.

### Structured Model Output

```python
from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm.ollama_client import llm
from app.ai.schemas.resume import ResumeAnalysis


structured_llm = llm.with_structured_output(ResumeAnalysis)

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Extract resume information accurately. "
        "Do not invent missing information."
    ),
    (
        "human",
        "Analyze this resume:\n\n{resume_text}"
    ),
])

resume_chain = prompt | structured_llm
```

Usage:

```python
result = resume_chain.invoke({
    "resume_text": "Python developer with experience in machine learning."
})

print(result.model_dump())
```

**Important:** Structured output support can vary by Ollama model and integration version. Test the selected model. If native structured output is unreliable, use JSON generation followed by explicit parsing, schema validation, and controlled retries.

---

## 8. LangChain Chains

A chain represents a reusable sequence of operations.

### Example Resume Extraction Chain

```text
Resume Text
    |
Prompt Template
    |
Ollama
    |
Structured Output
    |
Pydantic Validation
    |
Resume Data
```

### Example Implementation

```python
from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm.ollama_client import llm


prompt = ChatPromptTemplate.from_template(
    """
    Extract the technical skills from this resume.

    Resume:
    {resume_text}

    Return the skills as a structured list.
    """
)

resume_skill_chain = prompt | llm
```

Usage:

```python
result = resume_skill_chain.invoke({
    "resume_text": "Python, SQL, Machine Learning and React."
})

print(result.content)
```

### When to Use Chains

Use chains for:

- Resume information extraction.
- Job requirement extraction.
- Resume improvement suggestions.
- Interview question generation.
- Skill explanations.
- Simple AI response generation.

For operations involving branching, multiple dependent steps, or recovery logic, consider LangGraph.

---

## 9. LangGraph Fundamentals

LangGraph organizes workflows using:

- State.
- Nodes.
- Edges.
- Conditional edges.
- Graph execution.

### State

State stores information shared between workflow nodes.

Example:

```python
from typing import TypedDict


class ResumeState(TypedDict):
    resume_text: str
    extracted_data: dict
    normalized_skills: list[str]
    analysis_report: dict
    status: str
```

### Nodes

Nodes are Python functions that perform specific operations.

Example:

```python
def extract_resume(state: ResumeState):
    return {
        "extracted_data": {
            "skills": ["Python", "SQL"]
        },
        "status": "extracted",
    }
```

### Edges

Edges define the order in which nodes execute.

Example:

```text
START
  |
Extract Resume
  |
Normalize Skills
  |
Generate Report
  |
END
```

### Conditional Edges

Conditional edges decide the next step based on the current state.

Example:

```text
Validate Output
      |
      +------ Valid ------> Save Results
      |
      +------ Invalid ----> Retry Extraction
```

Use conditional routing when the workflow needs to make decisions.

---

## 10. Resume Analysis LangGraph Workflow

**Related features:** 13–20

### Workflow Objective

Extract and validate structured information from an uploaded resume.

### Architecture

```text
START
  |
Load Resume Text
  |
Extract Information
  |
Normalize Skills
  |
Validate Data
  |
  +------ Valid ------> Save Resume Intelligence
  |
  +------ Invalid ----> Retry / Error
  |
END
```

### State Definition

```python
from typing import TypedDict


class ResumeState(TypedDict):
    resume_text: str
    extracted_data: dict
    normalized_skills: list[str]
    errors: list[str]
    status: str
```

### Node Responsibilities

| Node | Responsibility |
|---|---|
| Load Resume | Load extracted text |
| Extract Information | Use LLM to extract fields |
| Normalize Skills | Standardize skill names |
| Validate Data | Check required output structure |
| Save Results | Persist structured data |

### Example Node

```python
def normalize_skills(state: ResumeState):
    skills = state["extracted_data"].get("skills", [])

    normalized = [
        skill.strip().lower()
        for skill in skills
        if isinstance(skill, str) and skill.strip()
    ]

    return {
        "normalized_skills": normalized
    }
```

### Graph Implementation

```python
from langgraph.graph import StateGraph, START, END


builder = StateGraph(ResumeState)

builder.add_node("load_resume", load_resume)
builder.add_node("extract_information", extract_information)
builder.add_node("normalize_skills", normalize_skills)
builder.add_node("validate_data", validate_data)
builder.add_node("save_results", save_results)

builder.add_edge(START, "load_resume")
builder.add_edge("load_resume", "extract_information")
builder.add_edge("extract_information", "normalize_skills")
builder.add_edge("normalize_skills", "validate_data")

builder.add_conditional_edges(
    "validate_data",
    validation_router,
    {
        "valid": "save_results",
        "invalid": END,
    },
)

builder.add_edge("save_results", END)

resume_graph = builder.compile()
```

The functions above are workflow placeholders. Implement and test each node before compiling the complete graph.

---

## 11. Job Description Analysis Workflow

**Related features:** 33–38

### Objective

Convert unstructured job descriptions into structured job requirements.

### Workflow

```text
START
  |
Load Job Description
  |
Extract Job Role
  |
Extract Requirements
  |
Extract Skills
  |
Normalize Skills
  |
Validate Output
  |
Save Job Data
  |
END
```

### Node Responsibilities

| Node | Operation |
|---|---|
| Load Job Description | Receive text |
| Extract Role | Identify role and title |
| Extract Requirements | Identify education and experience |
| Extract Skills | Identify required and preferred skills |
| Normalize Skills | Map aliases to standard names |
| Validate Output | Validate extracted fields |
| Save Job Data | Store structured job information |

Use LangChain for individual extraction operations and LangGraph to coordinate the full workflow.

---

## 12. Resume-to-Job Matching Workflow

**Related features:** 52–57

### Objective

Compare a user's resume against a selected job.

### Workflow

```text
START
  |
Load Resume
  |
Load Job Description
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
Calculate Score
  |
Generate Explanation
  |
Save Match
  |
END
```

### State

```python
from typing import TypedDict


class MatchingState(TypedDict):
    resume_id: str
    job_id: str
    resume_data: dict
    job_data: dict
    matched_skills: list[str]
    missing_skills: list[str]
    experience_score: float
    education_score: float
    match_score: float
    explanation: str
```

### Responsibilities

- Database services load the correct resume and job.
- Python functions normalize and compare skills.
- Python calculates matching components.
- LangChain generates a readable explanation.
- LangGraph coordinates the workflow.
- PostgreSQL stores the result.

The LLM must not invent the numerical match score.

---

## 13. Career Roadmap Workflow

**Related features:** 67–72

### Objective

Generate a personalized learning plan based on a user's career goal and skill gaps.

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
Generate Roadmap
  |
Validate Roadmap
  |
Save Roadmap
  |
END
```

### Node Responsibilities

| Node | Responsibility |
|---|---|
| Load Career Goal | Retrieve target role |
| Load Skills | Retrieve existing skills |
| Load Skill Gaps | Retrieve missing skills |
| Prioritize Skills | Calculate learning priorities |
| Retrieve Resources | Find relevant resources |
| Generate Roadmap | Use local LLM |
| Validate Roadmap | Check structure and completeness |
| Save Roadmap | Store roadmap and stages |

Use LangGraph because roadmap generation has several dependent steps.

---

## 14. AI Career Copilot Workflow

**Related feature:** 78

The Career Copilot will use a graph to route requests to relevant tools and context.

### Workflow

```text
START
  |
Receive User Message
  |
Identify Intent
  |
  +------------------------+
  |           |            |
  v           v            v
Resume      Job          Career
Analysis    Search       Guidance
  |           |            |
  +-----------+------------+
              |
        Retrieve Context
              |
        Generate Answer
              |
        Validate Response
              |
        Save Conversation
              |
             END
```

### Possible Tools

- Resume analysis service.
- Job discovery service.
- Job matching service.
- Skill gap service.
- Career roadmap service.
- Learning resource retriever.
- Interview preparation service.

### Tool Usage Rules

- Only expose tools needed for the current task.
- Check user authorization before accessing records.
- Validate all tool arguments.
- Require confirmation for sensitive or irreversible actions.
- Do not let the model bypass API authorization.
- Keep external side effects outside uncontrolled LLM execution.

The Copilot should not automatically apply for jobs or modify user records without the appropriate user confirmation.

---

## 15. RAG Integration

RAG allows the Career Copilot to retrieve relevant information before generating an answer.

### Architecture

```text
Knowledge Documents
       |
       v
Text Extraction
       |
       v
Chunking
       |
       v
Embedding Model
       |
       v
PostgreSQL + pgvector
       |
       |
User Question
       |
       v
Query Embedding
       |
       v
Similarity Search
       |
       v
Relevant Context
       |
       v
Ollama
       |
       v
Grounded Answer
```

### LangChain Responsibilities

- Document loaders.
- Text splitters.
- Embedding integration.
- Vector store integration.
- Retriever configuration.
- Prompt construction.

### LangGraph Responsibilities

- Decide whether retrieval is needed.
- Retrieve relevant context.
- Check whether sufficient context exists.
- Generate an answer.
- Route to clarification or fallback when necessary.

### Retrieval Rules

- Preserve document source metadata.
- Filter private data by user ID.
- Use the same embedding model for indexing and querying.
- Avoid sending irrelevant chunks to the LLM.
- Show sources when factual answers depend on retrieved documents.

---

## 16. Model Routing Strategy

Different tasks need different levels of model capability.

Create a centralized model service.

### Proposed Routing

| Task | Processing Strategy |
|---|---|
| Basic Text Cleaning | Python |
| Email and Date Validation | Python |
| Skill Normalization | Python + Skill Dictionary |
| Resume Extraction | Small Local LLM |
| Complex Resume Analysis | Local LLM |
| Semantic Retrieval | Embedding Model |
| Match Score | Python |
| Match Explanation | Local LLM |
| Career Roadmap | Local LLM + LangGraph |
| Copilot | Local LLM + RAG + LangGraph |

### Model Configuration

Keep model configuration in one place.

Example:

```python
MODEL_CONFIG = {
    "resume_extraction": "qwen2.5:3b",
    "career_assistant": "qwen2.5:3b",
    "roadmap_generation": "qwen2.5:3b",
}
```

These are initial configuration examples. Model selection must follow evaluation and hardware testing.

---

## 17. Error Handling and Retry Strategy

AI workflows can fail because of:

- Invalid model output.
- Ollama service unavailable.
- Model timeout.
- Missing resume information.
- Database failure.
- Invalid workflow state.
- Retrieval failure.

### Workflow

```text
AI Operation
     |
     v
Validate Result
     |
     +------ Valid ------> Continue
     |
     +------ Invalid ----> Retry
                              |
                              v
                         Retry Limit
                              |
                    +---------+---------+
                    |                   |
                  Retry               Failed
                    |                   |
                    v                   v
                AI Operation        Error Result
```

### Retry Rules

- Retry transient failures only.
- Limit retry attempts.
- Avoid infinite loops.
- Do not repeat non-idempotent database operations blindly.
- Log safe error details.
- Return understandable error messages.
- Preserve completed workflow results where possible.

For long-running workflows, persist task status and intermediate results in the database.

---

## 18. Workflow Persistence

Some workflows may take longer than a normal API request.

Examples:

- Large resume analysis.
- Multiple job comparisons.
- Employer research.
- Roadmap generation.
- Large-scale document indexing.

### Recommended Architecture

```text
FastAPI
   |
   v
Create Task Record
   |
   v
Workflow Execution
   |
   v
LangGraph
   |
   v
Save Intermediate Results
   |
   v
Save Final Result
   |
   v
Update Task Status
   |
   v
Frontend Retrieves Status
```

Start with simple execution for short workflows.

Introduce durable LangGraph checkpointing and a proper background worker architecture when the application needs:

- Resume after server restart.
- Human approval steps.
- Long-running execution.
- Workflow history.
- Recovery from failures.

Do not assume in-memory workflow state is durable.

---

## 19. Security Guidelines

AI workflows must follow the same security rules as the rest of Nexora AI.

- Never trust uploaded document instructions.
- Treat retrieved documents as untrusted content.
- Prevent prompt injection from external sources.
- Enforce user-level access controls.
- Validate tool arguments.
- Restrict file and URL access.
- Avoid exposing secrets to prompts.
- Do not log sensitive user content unnecessarily.
- Require approval for important external actions.
- Keep database access inside trusted backend services.

The LLM should not receive unrestricted database access.

---

## 20. Testing Strategy

Every chain and graph should be tested independently.

### LangChain Tests

Test:

- Prompt formatting.
- Model availability.
- Structured output.
- JSON parsing.
- Validation failures.
- Timeout handling.

### LangGraph Tests

Test:

- Node execution.
- State updates.
- Conditional routing.
- Invalid output handling.
- Retry limits.
- Database failures.
- Workflow completion.

### AI Quality Tests

Measure:

- Extraction accuracy.
- Skill matching accuracy.
- Hallucination rate.
- Output validity.
- Response time.
- Token usage where available.
- Memory usage.

Use fixed test resumes and job descriptions so model versions can be compared fairly.

Mock Ollama responses in unit tests. Keep separate integration tests that use a real local model.

---

## 21. Development Implementation Order

Implement LangChain and LangGraph gradually.

| Order | Implementation |
|---|---|
| 1 | Connect Ollama with LangChain |
| 2 | Create reusable model configuration |
| 3 | Create prompt templates |
| 4 | Add Pydantic output schemas |
| 5 | Build resume extraction chain |
| 6 | Build resume analysis graph |
| 7 | Build job description extraction chain |
| 8 | Build job analysis graph |
| 9 | Build matching workflow |
| 10 | Build skill gap workflow |
| 11 | Build roadmap workflow |
| 12 | Add embedding and RAG support |
| 13 | Build Career Copilot graph |
| 14 | Add persistence and background execution |
| 15 | Test and optimize workflows |

Do not build all agents at the beginning. First make each core service reliable.

---

## 22. Initial Dependencies

Install the main packages:

```bash
pip install langchain
pip install langchain-ollama
pip install langgraph
pip install pydantic
pip install sentence-transformers
pip install langchain-text-splitters
pip install langchain-community
```

Install vector integration only when needed. For PostgreSQL and pgvector, use the appropriate supported integration for the selected LangChain version.

Keep dependencies pinned in the project's dependency management workflow after testing.

---

## 23. Final Architecture Decision

Nexora AI will follow this architecture:

| Layer | Technology |
|---|---|
| Frontend | React + JavaScript |
| Backend | FastAPI |
| Main AI Runtime | Ollama |
| LLM Integration | LangChain |
| Workflow Orchestration | LangGraph |
| Structured Validation | Pydantic |
| Embeddings | Sentence Transformers |
| Vector Search | PostgreSQL + pgvector |
| Database | PostgreSQL |
| Programming Language | Python |

### Final Development Rules

1. Use LangChain for reusable LLM operations.
2. Use LangGraph for multi-step workflows.
3. Use Python for deterministic calculations.
4. Use Pydantic for output validation.
5. Use RAG when external or stored knowledge is required.
6. Keep model configuration centralized.
7. Keep AI workflows separate from API routes.
8. Do not create unnecessary agents.
9. Add persistence for long-running workflows.
10. Evaluate every workflow before production.

**Final Goal:** Build a modular AI orchestration layer that connects resume intelligence, employer analysis, job matching, skill gap detection, career roadmaps, and AI Copilot capabilities into one reliable Nexora AI system.