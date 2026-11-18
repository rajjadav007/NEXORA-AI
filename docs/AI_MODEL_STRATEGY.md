# AI_MODEL_STRATEGY.md

# Nexora AI: AI Model Strategy

## 1. Purpose

This document defines how Nexora AI will use Artificial Intelligence and Machine Learning to power its career intelligence features.

The main objectives are:

- Use local AI models wherever possible.
- Avoid paid API dependencies during initial development.
- Build modular AI workflows.
- Use pretrained models instead of training large models from scratch.
- Combine LLMs, embeddings, traditional algorithms, and deterministic Python logic.
- Keep the architecture flexible enough to support better models in the future.

The AI system must produce useful, explainable, and evidence-based career recommendations.

---

## 2. AI Architecture Overview

Nexora AI will use multiple AI components instead of depending on a single LLM.

### Main AI components

| Component | Responsibility |
|---|---|
| Local LLM | Text understanding, reasoning, and generation |
| Embedding Model | Semantic similarity and document retrieval |
| NLP Processing | Text extraction, cleaning, and normalization |
| Matching Engine | Resume-to-job matching |
| Recommendation Engine | Skill and career recommendations |
| Assessment Engine | Generate and evaluate skill assessments |
| Agent Workflows | Coordinate multi-step AI tasks |

### High-level architecture

```text
                  NEXORA AI
                      |
               AI ENGINE LAYER
                      |
        +-------------+-------------+
        |             |             |
      Local LLM    Embeddings     NLP Engine
        |             |             |
      Ollama      Sentence       Python NLP
        |         Transformers
        |             |
        +-------------+-------------+
                      |
                AI WORKFLOWS
                      |
          +-----------+-----------+
          |           |           |
      Resume AI    Job AI     Career AI
          |           |           |
          +-----------+-----------+
                      |
              LangChain + LangGraph
                      |
                FastAPI Backend
```

---

## 3. Local LLM Strategy

### 3.1 Model Runtime

**Primary runtime: Ollama**

Ollama will manage and run local language models.

Responsibilities:

- Download and manage local models.
- Run inference on the development machine.
- Provide a local API for FastAPI.
- Support different models for different tasks.
- Allow model replacement without changing the entire application.

Local API example:

```text
http://localhost:11434
```

### 3.2 Candidate LLM Models

These are initial candidates for testing, not final locked selections.

| Model | Proposed Use | Priority |
|---|---|---|
| Qwen 2.5 3B Instruct | Lightweight extraction and generation | High |
| Qwen 2.5 7B Instruct | Complex reasoning and career analysis | High |
| Gemma 3 4B | Alternative for structured analysis | Medium |
| Llama 3.2 3B | Lightweight assistant workflows | Medium |

Model availability, supported context length, license, quantization, and performance must be verified before adoption.

### 3.3 Recommended Initial Setup

Start with one lightweight model.

**Initial candidate: Qwen 2.5 3B Instruct**

Reasons:

- Suitable starting point for local experimentation.
- Lower memory requirements than larger models.
- Useful for structured text generation and extraction experiments.
- Helps establish the AI workflow before introducing larger models.

After testing, compare it with a 7B model for complex tasks.

Do not load multiple large models simultaneously on the development machine.

---

## 4. Hardware-Aware Model Strategy

### Development Machine

| Hardware | Specification |
|---|---|
| Operating System | Windows |
| RAM | 24 GB |
| GPU | NVIDIA RTX 2040 |
| GPU VRAM | 4 GB |
| Model Runtime | Ollama |

### Hardware Constraints

The 4 GB GPU VRAM is limited for running larger LLMs.

Therefore:

- Prefer smaller quantized models.
- Use 3B to 4B models as initial candidates.
- Test 7B models with quantization and partial CPU offloading.
- Keep enough RAM available for the frontend, backend, database, and development tools.
- Avoid loading multiple models at the same time.
- Measure actual memory usage during inference.

A model may run even when it does not fit entirely in GPU memory, but inference can become slower when CPU offloading is required.

### Model Selection Rule

Choose models based on:

1. Output accuracy.
2. Response time.
3. RAM consumption.
4. GPU memory consumption.
5. Structured output reliability.
6. License compatibility.
7. Stability across repeated tests.

The largest model is not automatically the best model.

---

## 5. Embedding Model Strategy

### 5.1 Purpose

Embedding models convert text into numerical vectors.

Nexora AI will use embeddings for:

- Resume-to-job semantic matching.
- Skill similarity detection.
- Finding related skills.
- Learning resource retrieval.
- Career knowledge retrieval.
- Context retrieval for AI Copilot.

### 5.2 Candidate Embedding Models

| Model | Proposed Use | Priority |
|---|---|---|
| EmbeddingGemma | General semantic search | High |
| all-MiniLM-L6-v2 | Lightweight baseline | High |
| BGE-small-en-v1.5 | English semantic retrieval | Medium |
| nomic-embed-text | Local embedding experiments | Medium |

These are candidates for evaluation. Select the final model after testing retrieval quality on Nexora AI data.

### 5.3 Recommended Initial Approach

Start with `all-MiniLM-L6-v2` as a lightweight baseline.

Evaluate EmbeddingGemma and other candidates before finalizing the production embedding model.

Important:

- Use the same embedding model for document storage and query generation.
- Keep track of the model name and embedding dimensions.
- Rebuild stored embeddings when changing to an incompatible model.
- Do not compare vectors generated by different embedding models directly.

---

## 6. AI and NLP Libraries

| Library | Responsibility |
|---|---|
| LangChain | LLM integration and reusable AI components |
| LangGraph | Multi-step AI workflows and state management |
| Sentence Transformers | Text embeddings |
| spaCy | NLP processing and entity extraction |
| Pydantic | Structured output validation |
| PyMuPDF | PDF text extraction |
| python-docx | DOCX text extraction |
| scikit-learn | Similarity and traditional ML algorithms |
| RapidFuzz | Fuzzy text and skill matching |

Use these libraries where they provide a clear benefit. Do not add unnecessary AI frameworks.

---

## 7. AI Model Responsibilities

Different features require different techniques.

### 7.1 Resume Intelligence

**Features:** 13 to 20

Responsibilities:

- Extract personal information.
- Identify education details.
- Understand work experience.
- Extract technical and soft skills.
- Identify projects.
- Analyze certifications.
- Understand resume structure.

Proposed approach:

```text
Resume File
    |
Text Extraction
    |
Text Cleaning
    |
Section Detection
    |
LLM + NLP Extraction
    |
Pydantic Validation
    |
Structured Resume Data
    |
PostgreSQL
```

Model responsibilities:

- LLM: Understand resume content and extract structured information.
- spaCy: Support entity and text processing.
- Python: Validate dates, email addresses, links, and other fields.
- Pydantic: Validate the final output structure.

Do not rely entirely on LLM output for factual information.

### 7.2 Resume Quality Analysis

**Features:** 21 to 27

The system evaluates:

- Resume quality.
- Strengths and weaknesses.
- ATS-related formatting issues.
- Grammar and clarity.
- Achievement quality.
- Improvement recommendations.

Proposed approach:

| Task | Technique |
|---|---|
| Resume Quality Score | Rule-based scoring |
| Strength Analysis | LLM |
| Weakness Analysis | LLM + rules |
| ATS Compatibility | Structure and formatting checks |
| Grammar and Clarity | NLP + LLM |
| Achievement Analysis | LLM |
| Improvement Suggestions | LLM |

Important: Nexora AI must not claim to reproduce the exact scoring system of every ATS platform.

The ATS analysis should identify common compatibility issues, not guarantee ATS acceptance.

### 7.3 Job Description Intelligence

**Features:** 33 to 38

Responsibilities:

- Extract job roles.
- Identify required skills.
- Identify preferred skills.
- Understand experience requirements.
- Extract education requirements.
- Generate structured job reports.

Proposed approach:

```text
Job Description
      |
Text Cleaning
      |
LLM Extraction
      |
Skill Normalization
      |
Requirement Validation
      |
Structured Job Data
```

Use Python rules to validate experience ranges, dates, and other structured values.

### 7.4 Employer Intelligence

**Features:** 39 to 45

Responsibilities:

- Analyze company information.
- Understand employer requirements.
- Identify demanded skills.
- Research fresher and internship opportunities.
- Generate employer intelligence reports.

Proposed approach:

- Use verified public information as the source.
- Extract company requirements using an LLM.
- Normalize skills using a common skill taxonomy.
- Store source links and retrieval dates.
- Clearly separate verified information from AI-generated interpretation.

The LLM must not invent company policies, hiring requirements, or job openings.

### 7.5 Job Matching Engine

**Features:** 52 to 57

This is one of the most important Nexora AI components.

The matching engine compares:

- Resume skills.
- Required job skills.
- Preferred skills.
- Experience.
- Education.
- Relevant projects.

Use a hybrid matching system.

#### Hybrid Matching Architecture

```text
             Resume Data
                  |
                  |
             Job Data
                  |
                  v
           Skill Normalization
                  |
          +-------+-------+
          |               |
      Exact Match    Semantic Match
          |               |
          +-------+-------+
                  |
           Experience Check
                  |
            Education Check
                  |
            Weighted Scoring
                  |
             Match Score
                  |
          Match Explanation
```

#### Proposed Scoring Model

The initial scoring weights are configurable design assumptions and must be validated through testing.

| Matching Factor | Initial Weight |
|---|---:|
| Required Skill Match | 40% |
| Preferred Skill Match | 20% |
| Experience Match | 20% |
| Education Match | 10% |
| Project Relevance | 10% |
| Total | 100% |

Formula:

```text
Match Score =
    (Required Skill Score * 0.40)
  + (Preferred Skill Score * 0.20)
  + (Experience Score * 0.20)
  + (Education Score * 0.10)
  + (Project Relevance Score * 0.10)
```

Each component should be normalized to a score between 0 and 100.

The final score should include an explanation showing:

- Matching skills.
- Missing required skills.
- Matching experience.
- Relevant projects.
- Reasons for the final score.

Do not present the score as a guaranteed hiring probability.

### 7.6 Skill Gap Intelligence

**Features:** 58 to 62

Responsibilities:

- Detect missing skills.
- Identify transferable skills.
- Prioritize skills.
- Compare skill requirements.
- Generate skill gap reports.

Proposed approach:

```text
Resume Skills
      |
      v
Required Job Skills
      |
      v
Skill Normalization
      |
      v
Skill Comparison
      |
  +---+---+
  |       |
Matched  Missing
Skills   Skills
  |       |
  +---+---+
      |
Priority Analysis
      |
Skill Gap Report
```

Use a combination of:

- Exact skill matching.
- Skill aliases.
- Semantic similarity.
- LLM-based contextual interpretation.
- Python-based priority calculations.

### 7.7 Career Readiness Score

**Features:** 63 to 66

The readiness score measures how prepared a candidate is for a selected role.

Possible factors:

- Required skill coverage.
- Experience relevance.
- Project relevance.
- Education requirements.
- Assessment evidence.
- Skill gaps.

Use deterministic scoring logic rather than asking an LLM to invent a readiness score.

The LLM can explain the result, but Python should calculate it.

### 7.8 Personalized Career Roadmap

**Features:** 67 to 72

Responsibilities:

- Understand career goals.
- Generate personalized learning plans.
- Recommend learning resources.
- Suggest practical projects.
- Prioritize skills.
- Track progress.

Proposed approach:

- Python: Determine missing and priority skills.
- Embeddings: Retrieve relevant learning resources.
- LLM: Generate a structured roadmap.
- LangGraph: Coordinate multi-step planning.
- PostgreSQL: Store roadmap and progress.

Recommendations should include the reason each resource or project is relevant.

### 7.9 Skill Assessment and Verification

**Features:** 73 to 77

Responsibilities:

- Generate assessments.
- Generate technical questions.
- Create practical challenges.
- Evaluate answers.
- Maintain skill evidence.

Proposed approach:

| Task | Technique |
|---|---|
| Question Generation | LLM |
| Difficulty Selection | Python rules |
| Answer Evaluation | Rules + LLM |
| Code Evaluation | Sandboxed execution |
| Score Calculation | Deterministic logic |
| Skill Evidence | Database records |

Never execute user-submitted code directly inside the main backend process.

Use a restricted execution environment when practical coding assessments are introduced.

### 7.10 AI Career Copilot

**Features:** 78 to 84

Responsibilities:

- Answer career questions.
- Provide resume guidance.
- Help prepare for interviews.
- Analyze GitHub projects.
- Recommend internships.
- Support job applications.
- Track career preparation.

Proposed approach:

```text
User Message
     |
     v
Intent Detection
     |
     v
Context Retrieval
     |
     v
LangGraph Workflow
     |
     +------------------+
     |                  |
 Resume Context     Job Context
     |                  |
     +--------+---------+
              |
         Local LLM
              |
       Response Validation
              |
         Final Answer
```

The Copilot should use the user's saved data only when it is relevant and authorized.

---

## 8. LangChain and LangGraph Strategy

### 8.1 LangChain

Use LangChain for:

- Ollama integration.
- Prompt templates.
- Structured output.
- Embedding integration.
- Retrieval workflows.
- Reusable model components.

### 8.2 LangGraph

Use LangGraph for workflows that involve multiple dependent steps.

Examples:

**Resume Analysis Workflow**

```text
START
  |
Extract Resume Text
  |
Identify Sections
  |
Extract Information
  |
Normalize Skills
  |
Validate Output
  |
Generate Resume Report
  |
Save Results
  |
END
```

**Job Matching Workflow**

```text
START
  |
Load Resume
  |
Load Job Description
  |
Extract Requirements
  |
Normalize Skills
  |
Calculate Match
  |
Identify Skill Gaps
  |
Generate Explanation
  |
Save Match Result
  |
END
```

**Career Roadmap Workflow**

```text
START
  |
Select Career Goal
  |
Analyze Current Skills
  |
Identify Missing Skills
  |
Prioritize Learning
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

Do not use LangGraph for every simple AI operation. Use normal Python functions for straightforward tasks.

---

## 9. Retrieval-Augmented Generation (RAG)

RAG will help Nexora AI generate answers using relevant information from trusted sources.

### Proposed RAG use cases

- Learning resource recommendations.
- Career guidance.
- Technical interview preparation.
- Skill explanations.
- Resume guidance.
- Career Copilot context retrieval.

### RAG Architecture

```text
Documents / Knowledge Sources
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
Question Embedding
      |
      v
Vector Retrieval
      |
      v
Relevant Context
      |
      v
Local LLM
      |
      v
Grounded Response
```

### Initial RAG Technology

| Component | Technology |
|---|---|
| Embeddings | Sentence Transformers |
| Vector Storage | PostgreSQL + pgvector |
| Chunking | Python |
| Retrieval | Similarity Search |
| Generation | Ollama |
| Orchestration | LangChain |

RAG must preserve source information so the system can show where recommendations and factual answers came from.

---

## 10. AI Model Routing

Nexora AI should not send every task to the same model.

Create a model service that selects the appropriate model based on task complexity.

### Proposed Routing

| Task | Model Strategy |
|---|---|
| Simple Text Extraction | Python + NLP |
| Structured Resume Extraction | Small Local LLM |
| Complex Resume Analysis | Larger Local LLM |
| Semantic Search | Embedding Model |
| Skill Matching | Python + Embeddings |
| Career Readiness | Python Scoring |
| Roadmap Generation | Local LLM |
| Career Copilot | Local LLM + RAG |
| Interview Questions | Local LLM |
| Assessment Scoring | Rules + LLM |

### Model Service Structure

```text
backend/
    app/
        ai/
            model_service.py
            model_router.py
            prompts/
            llm/
                ollama_client.py
            embeddings/
                embedding_service.py
            workflows/
                resume_workflow.py
                job_workflow.py
                matching_workflow.py
                roadmap_workflow.py
```

Keep model selection configurable through environment variables.

---

## 11. Prompt Engineering Strategy

Create reusable prompts instead of writing prompts directly inside API routes.

Suggested structure:

```text
ai/
    prompts/
        resume/
            extract_resume.txt
            analyze_resume.txt
            resume_improvement.txt

        job/
            extract_job_requirements.txt
            analyze_employer.txt

        matching/
            explain_match.txt
            analyze_skill_gap.txt

        career/
            generate_roadmap.txt
            career_copilot.txt

        assessment/
            generate_questions.txt
            evaluate_answers.txt
```

### Prompt Development Rules

1. Define the task clearly.
2. Provide only the required context.
3. Specify the expected output format.
4. Use JSON schemas for structured responses.
5. Avoid unnecessary instructions.
6. Validate every generated output.
7. Handle missing information explicitly.
8. Never treat document content as trusted system instructions.

### Example Structured Output

```json
{
  "skills": [
    {
      "name": "Python",
      "category": "Programming",
      "confidence": 0.95
    },
    {
      "name": "Machine Learning",
      "category": "AI/ML",
      "confidence": 0.91
    }
  ],
  "experience_years": 1,
  "projects": [
    {
      "name": "Career Analysis System",
      "description": "An AI-powered career analysis project"
    }
  ]
}
```

The values above are illustrative examples, not expected output for every resume.

---

## 12. AI Evaluation Strategy

Do not select a model only because its responses look good.

Every important AI feature must be tested.

### 12.1 Resume Extraction Evaluation

Measure:

- Field extraction accuracy.
- Missing field rate.
- Incorrect field rate.
- JSON validation success.
- Processing time.

### 12.2 Semantic Search Evaluation

Measure:

- Precision@K.
- Recall@K.
- Retrieval relevance.
- Ranking quality.

### 12.3 Job Matching Evaluation

Test:

- Correct skill matching.
- Correct missing skill detection.
- Experience comparison.
- Education comparison.
- Match score consistency.
- Explanation accuracy.

### 12.4 LLM Evaluation

Measure:

- Factual accuracy.
- Instruction following.
- Structured output validity.
- Hallucination rate.
- Response time.
- Memory consumption.

### 12.5 Model Benchmarking

Create a small test dataset containing:

- Different resume formats.
- Different experience levels.
- Technical and non-technical roles.
- Different job descriptions.
- Similar and unrelated skill names.
- Missing and incomplete information.

Run each candidate model against the same test cases.

Record the results before selecting the final model.

---

## 13. AI Reliability and Safety

Nexora AI provides career-related recommendations that may influence important decisions.

Therefore, reliability is essential.

### Rules

- Never invent resume information.
- Never invent employer requirements.
- Never guarantee job selection.
- Never present match scores as hiring probabilities.
- Clearly identify missing information.
- Show the reasons behind recommendations.
- Preserve source links for external information.
- Validate LLM-generated JSON.
- Handle model timeouts and invalid responses.
- Keep user resume data private.
- Do not use one user's private data in another user's response.

### Human Review

Allow users to review and correct extracted resume information before it becomes the basis for further analysis.

AI-generated career recommendations should be treated as guidance, not guaranteed outcomes.

---

## 14. AI Performance Optimization

The initial development environment has limited GPU memory.

Apply these optimization practices:

- Use quantized models where suitable.
- Prefer smaller models for simple tasks.
- Reuse loaded models where practical.
- Avoid unnecessary repeated inference.
- Cache reusable embeddings.
- Limit input context to relevant information.
- Process long documents in sections.
- Use background tasks for longer workflows.
- Set inference timeouts.
- Monitor CPU, RAM, and GPU usage.
- Avoid simultaneous large-model requests on the initial machine.

Do not generate embeddings repeatedly for unchanged documents.

---

## 15. Initial AI Dependencies

Proposed Python packages:

```bash
pip install langchain
pip install langchain-ollama
pip install langgraph
pip install sentence-transformers
pip install transformers
pip install torch
pip install spacy
pip install scikit-learn
pip install pydantic
pip install pymupdf
pip install python-docx
pip install pgvector
```

Install packages in a Python virtual environment.

Some packages may require separate installation instructions depending on the operating system, Python version, and CUDA setup.

Ollama itself must be installed separately.

---

## 16. AI Development Phases

| Phase | AI Work |
|---|---|
| Phase 1 | Set up AI module structure |
| Phase 2 | Build document extraction pipeline |
| Phase 3 | Implement resume information extraction |
| Phase 4 | Build resume quality analysis |
| Phase 5 | Generate resume intelligence reports |
| Phase 6 | Implement job description extraction |
| Phase 7 | Build employer research workflows |
| Phase 8 | Integrate job discovery |
| Phase 9 | Build hybrid job matching |
| Phase 10 | Implement skill gap intelligence |
| Phase 11 | Build deterministic readiness scoring |
| Phase 12 | Generate personalized career roadmaps |
| Phase 13 | Implement skill assessments |
| Phase 14 | Build LangGraph-powered Career Copilot |
| Phase 15 | Optimize, test, secure, and deploy AI services |

AI work should follow the product's 15-phase development roadmap.

---

## 17. Future Model Improvements

The architecture should allow future upgrades without rewriting the entire application.

Possible improvements:

- Better multilingual embedding models.
- More capable local LLMs.
- Fine-tuned models for resume extraction.
- Specialized reranking models.
- Advanced recommendation algorithms.
- Improved job matching models.
- Voice-based career assistance.
- More advanced interview evaluation.

Fine-tuning should be considered only after collecting suitable, permissioned training data and establishing a reliable evaluation dataset.

Do not train a large foundation model from scratch.

---

## 18. Final AI Technology Stack

| Layer | Selected Technology / Candidate |
|---|---|
| LLM Runtime | Ollama |
| Initial LLM Candidate | Qwen 2.5 3B Instruct |
| Alternative LLM Candidates | Qwen 2.5 7B, Gemma 3 4B |
| Embeddings | Sentence Transformers |
| Initial Embedding Candidate | all-MiniLM-L6-v2 |
| Alternative Embedding Candidate | EmbeddingGemma |
| AI Framework | LangChain |
| Agent Workflow | LangGraph |
| NLP | spaCy |
| ML Algorithms | scikit-learn |
| Vector Database | PostgreSQL + pgvector |
| Structured Validation | Pydantic |
| PDF Processing | PyMuPDF |
| DOCX Processing | python-docx |
| Backend | FastAPI |
| Programming Language | Python |

---

## 19. Final Development Principles

Nexora AI will follow these principles:

1. Local-first AI development.
2. Free and open-source tools wherever practical.
3. Use pretrained models instead of training from scratch.
4. Use deterministic Python logic for calculations.
5. Use LLMs for language understanding and generation.
6. Use embeddings for semantic retrieval and similarity.
7. Use LangGraph only for workflows that need orchestration.
8. Validate every important AI output.
9. Keep models replaceable through a modular architecture.
10. Evaluate model quality before production use.

**Final Goal:** Build a reliable, modular, and explainable AI engine that connects resumes, jobs, employer requirements, skill gaps, assessments, and career development into one unified career intelligence platform.