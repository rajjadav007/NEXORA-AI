"""
AI-Powered Job Requirement Extractor using LangChain and ChatOllama
Phase 6 | Feature 36: Job Requirement Extraction
"""

import asyncio
import json
import logging
import time
from typing import Optional

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.job_requirement_analysis import (
    IMPORTANCE_LEVELS,
    JobRequirementAIStructuredOutput,
    TECHNICAL_SKILL_CATEGORIES,
)
from app.services.quality_score.ai_evaluator import (
    AIOutputValidationError,
    OllamaUnavailableError,
)

logger = logging.getLogger(__name__)

SYSTEM_REQUIREMENT_EXTRACTION_PROMPT = """You are a senior Technical Recruiter & Job Requirement Intelligence Engine.
Analyze the job description and extract structured employer requirements.

TECHNICAL SKILL CATEGORIES (prefer these exact category names; support custom skills):
{technical_categories}
Examples:
- Programming Language: Python, Java, JavaScript, C++, SQL, Go, TypeScript
- AI & Machine Learning: Machine Learning, Deep Learning, Generative AI, NLP, Computer Vision, Large Language Models
- Framework & Library: LangChain, LangGraph, TensorFlow, PyTorch, Scikit-learn, FastAPI, React
- Tool & Platform: Git, Docker, Kubernetes, AWS, Azure, Google Cloud, Ollama
- Database: PostgreSQL, MySQL, MongoDB, Redis, Vector Databases

IMPORTANCE CLASSIFICATION (use exact values: {importance_levels}):
- "Mandatory": explicitly required ("required", "must have", "essential", "strong proficiency in").
- "Preferred": explicitly preferred/bonus ("preferred", "nice to have", "advantage", "plus", "bonus").
- "Optional": explicitly optional.
- "Unspecified": mentioned without clear mandatory/preferred signal.
CRITICAL: NEVER classify every mentioned skill as Mandatory. Follow the actual wording.

EDUCATION & EXPERIENCE:
- Extract minimum_level, required_degree, preferred_degree, required_fields, required_certifications, preferred_certifications ONLY if stated.
- Extract minimum_years, maximum_years, professional_experience, internship_experience, project_experience, fresher_eligible, domain_experience ONLY if stated.
- Do NOT invent qualifications, years, or soft skills absent from the text. Use null or [] when unavailable.

SOFT SKILLS & DOMAIN KNOWLEDGE:
- Soft skills (e.g., Communication, Problem-solving, Teamwork, Leadership, Analytical thinking, Adaptability, Critical thinking, Time management) ONLY when supported by text.
- Domain knowledge (e.g., Artificial Intelligence, Machine Learning, Generative AI, Data Science, Data Analytics, Cloud Computing, Software Engineering, Cybersecurity, Finance, Healthcare, or custom domains).

For EVERY requirement item provide: name, category, importance, evidence (short supporting phrase from text), confidence (0.0-1.0), source_type ("explicit" or "inferred").
Return valid JSON matching the structured schema.
"""

USER_REQUIREMENT_EXTRACTION_TEMPLATE = """Extract structured requirements from this job posting:

Job Title: {job_title}
Company: {company_name}
Employment Type: {employment_type}
Experience Required (provided): {experience_required}

=== JOB DESCRIPTION ===
{description}
"""


class JobRequirementAIExtractor:
    """LangChain + ChatOllama integration for structured job requirement extraction."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or max(settings.OLLAMA_TIMEOUT_SECONDS, 30.0)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_REQUIREMENT_EXTRACTION_PROMPT),
            ("user", USER_REQUIREMENT_EXTRACTION_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.0,
            timeout=self.timeout,
        )

    async def extract_requirements(
        self,
        description: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        employment_type: Optional[str] = None,
        experience_required: Optional[str] = None,
    ) -> JobRequirementAIStructuredOutput:
        """
        Invoke ChatOllama with structured output to extract job requirements.
        Raises OllamaUnavailableError on connection/timeout failures.
        Raises AIOutputValidationError on malformed or invalid model responses.
        """
        formatted_prompt = self.prompt.format_messages(
            technical_categories=", ".join(TECHNICAL_SKILL_CATEGORIES),
            importance_levels=", ".join(IMPORTANCE_LEVELS),
            job_title=job_title or "Not provided",
            company_name=company_name or "Not provided",
            employment_type=employment_type or "Not provided",
            experience_required=experience_required or "Not provided",
            description=(description or "")[:8000],
        )

        llm = self._get_llm()
        structured_llm = llm.with_structured_output(JobRequirementAIStructuredOutput)

        try:
            logger.info("Invoking ChatOllama for job requirement extraction with model %s", self.model)
            start = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            logger.info("Job requirement extraction completed in %.2fs", time.time() - start)

            if result is None:
                raise AIOutputValidationError("Model returned an empty response.")
            if isinstance(result, JobRequirementAIStructuredOutput):
                return result
            if isinstance(result, str):
                return JobRequirementAIStructuredOutput.model_validate(json.loads(result))
            return JobRequirementAIStructuredOutput.model_validate(result)

        except (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.TimeoutException,
            ConnectionRefusedError,
            TimeoutError,
            asyncio.TimeoutError,
        ) as conn_err:
            logger.error("Ollama connection/timeout failure during requirement extraction: %s", conn_err)
            raise OllamaUnavailableError(
                f"Ollama LLM service is unavailable or timed out at {self.base_url}."
            ) from conn_err

        except (ValidationError, json.JSONDecodeError, ValueError, TypeError) as val_err:
            logger.error("Job requirement extraction validation error: %s", val_err)
            raise AIOutputValidationError(
                f"Model output failed structured validation: {val_err}"
            ) from val_err

        except AIOutputValidationError:
            raise

        except Exception as exc:
            error_str = str(exc).lower()
            if any(term in error_str for term in ("connect", "refused", "timeout", "timed out", "unavailable", "11434")):
                logger.error("Ollama network/timeout error: %s", exc)
                raise OllamaUnavailableError(
                    f"Ollama LLM service is unavailable at {self.base_url}: {exc}"
                ) from exc
            if any(term in error_str for term in ("json", "parse", "validation", "schema")):
                logger.error("AI output parsing error: %s", exc)
                raise AIOutputValidationError(f"Malformed AI response: {exc}") from exc
            logger.error("Unexpected error in JobRequirementAIExtractor: %s", exc)
            raise
