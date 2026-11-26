"""
AI-Powered Job Role Extractor using LangChain and ChatOllama
Phase 6 | Feature 35: Job Role Extraction
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
from app.schemas.job_role_analysis import (
    JobRoleAIStructuredOutput,
    SENIORITY_LEVELS,
    STANDARDIZED_ROLES,
    WORK_ARRANGEMENTS,
)
from app.services.quality_score.ai_evaluator import (
    AIOutputValidationError,
    OllamaUnavailableError,
)

logger = logging.getLogger(__name__)

SYSTEM_ROLE_EXTRACTION_PROMPT = """You are a senior Career Intelligence & Job Taxonomy Engine.
Extract structured role metadata from the provided job description.

STANDARDIZED ROLES (prefer one of these exact names when applicable; if none fit, provide a concise custom role name, or "Other" if ambiguous):
{standardized_roles}

SENIORITY LEVELS (use exact match; use "Unknown" when evidence is insufficient — NEVER assume "Fresher" or "Entry Level" without explicit evidence):
{seniority_levels}

WORK ARRANGEMENTS (use exact match):
{work_arrangements}

STRICT RULES:
1. Ground every extracted field in the provided job description text and metadata.
2. NEVER invent experience years, responsibilities, or seniority levels not supported by the text.
3. Use null for unavailable nullable fields (job_title, department, category, industry, employment_type, role_summary, minimum_years, maximum_years, experience description).
4. Use "Unknown" for seniority or work_arrangement when not determinable.
5. Extract concise, factual responsibilities directly from the posting; return [] if none are stated.
6. Set confidence_score between 0.0 and 1.0 reflecting clarity and completeness of the role signals.
7. Return valid JSON matching the structured schema.
"""

USER_ROLE_EXTRACTION_TEMPLATE = """Analyze this job posting and extract structured role information:

Job Title (provided): {job_title}
Company: {company_name}
Location: {location}
Employment Type (provided): {employment_type}
Experience Required (provided): {experience_required}

=== JOB DESCRIPTION ===
{description}
"""


class JobRoleAIExtractor:
    """LangChain + ChatOllama integration for structured job role extraction."""

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
            ("system", SYSTEM_ROLE_EXTRACTION_PROMPT),
            ("user", USER_ROLE_EXTRACTION_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.0,
            timeout=self.timeout,
        )

    async def extract_role(
        self,
        description: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        location: Optional[str] = None,
        employment_type: Optional[str] = None,
        experience_required: Optional[str] = None,
    ) -> JobRoleAIStructuredOutput:
        """
        Invoke ChatOllama with structured output to extract job role metadata.
        Raises OllamaUnavailableError on connection/timeout failures.
        Raises AIOutputValidationError on malformed or invalid model responses.
        """
        formatted_prompt = self.prompt.format_messages(
            standardized_roles=", ".join(STANDARDIZED_ROLES),
            seniority_levels=", ".join(SENIORITY_LEVELS),
            work_arrangements=", ".join(WORK_ARRANGEMENTS),
            job_title=job_title or "Not provided",
            company_name=company_name or "Not provided",
            location=location or "Not provided",
            employment_type=employment_type or "Not provided",
            experience_required=experience_required or "Not provided",
            description=(description or "")[:8000],
        )

        llm = self._get_llm()
        structured_llm = llm.with_structured_output(JobRoleAIStructuredOutput)

        try:
            logger.info("Invoking ChatOllama for job role extraction with model %s", self.model)
            start = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            logger.info("Job role extraction completed in %.2fs", time.time() - start)

            if result is None:
                raise AIOutputValidationError("Model returned an empty response.")
            if isinstance(result, JobRoleAIStructuredOutput):
                return result
            if isinstance(result, str):
                return JobRoleAIStructuredOutput.model_validate(json.loads(result))
            return JobRoleAIStructuredOutput.model_validate(result)

        except (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.TimeoutException,
            ConnectionRefusedError,
            TimeoutError,
            asyncio.TimeoutError,
        ) as conn_err:
            logger.error("Ollama connection/timeout failure during role extraction: %s", conn_err)
            raise OllamaUnavailableError(
                f"Ollama LLM service is unavailable or timed out at {self.base_url}."
            ) from conn_err

        except (ValidationError, json.JSONDecodeError, ValueError, TypeError) as val_err:
            logger.error("Job role extraction structured output validation error: %s", val_err)
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
            logger.error("Unexpected error in JobRoleAIExtractor: %s", exc)
            raise
