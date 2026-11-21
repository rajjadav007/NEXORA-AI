"""
AI-Powered Resume Strength Evaluator using LangChain and ChatOllama
Phase 4 | Feature 22: Resume Strength Analysis
Reuses the Ollama and LangChain infrastructure established in Feature #21.
"""

import json
import logging
import time
from typing import Dict, Any, Optional

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.strength_analysis import (
    ResumeStrengthAIStructuredOutput,
    StrengthItemAI,
    STRENGTH_CATEGORIES,
)
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

SYSTEM_STRENGTH_PROMPT = """You are a senior Executive Talent Assessor and Career Intelligence Engine.
Your task is to analyze candidate resumes and identify their most compelling, distinct professional STRENGTHS across 7 categories:
1. Technical Skills (`technical_skills`): Core technologies, frameworks, architectural mastery, systems design.
2. Projects (`projects`): Non-trivial technical builds, open-source work, full-stack systems, measurable product results.
3. Work & Internship Experience (`experience`): Professional roles, delivery track record, quantified achievements, domain depth.
4. Education (`education`): Relevant degrees, academic excellence, rigorous coursework, prestigious institutions.
5. Achievements & Certifications (`achievements`): Industry credentials, competitive hackathons, awards, publications.
6. Leadership & Teamwork (`leadership`): ONLY when backed by resume evidence (leading teams, mentoring, orchestrating cross-functional initiatives). DO NOT fabricate if absent.
7. Communication & Problem-Solving (`communication`): ONLY when backed by resume evidence (client interfacing, incident triage, technical writing, stakeholder management). DO NOT fabricate if absent.

STRICT PRINCIPLES:
- NEVER invent or assume skills, companies, tools, metrics, or achievements that do not appear in the candidate's resume.
- Cite specific, tangible evidence (numbers, percentages, technologies, exact quotes) in the `evidence` field for every single strength.
- Distinguish `demonstrated` strengths (backed by verified metrics, production tenure, or completed projects) from `potential` strengths (early-stage foundational knowledge or high trajectory).
- If the resume is blank, extremely sparse, or lacks substantive detail to identify meaningful strengths, set `is_sufficient_evidence` to false and state the reason.
- Assign `confidence_level` as "High" (deep evidence), "Medium" (clear evidence), or "Low" (implied/limited evidence).
- Return output strictly matching the provided JSON schema.
"""

USER_STRENGTH_TEMPLATE = """Evaluate this candidate's resume and extract their most compelling strengths:

=== STRUCTURED RESUME DATA ===
{resume_summary}

=== CLEANED RESUME TEXT (EXCERPT) ===
{cleaned_text_excerpt}

Identify all substantiated strengths across the 7 categories. Provide title, category, detailed explanation, explicit evidence items, professional value, confidence level, and whether each strength is demonstrated or potential. Also provide top_strengths_summary and category_takeaways.
"""


class StrengthAIEvaluator:
    """LangChain + ChatOllama integration for candidate strength analysis."""

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
            ("system", SYSTEM_STRENGTH_PROMPT),
            ("user", USER_STRENGTH_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.1,
            timeout=self.timeout,
        )

    async def evaluate_strengths(
        self,
        resume_summary: str,
        cleaned_text: Optional[str] = None,
    ) -> ResumeStrengthAIStructuredOutput:
        """
        Executes LangChain ChatOllama structured output invocation to detect candidate strengths.
        Raises OllamaUnavailableError if Ollama is unreachable.
        Raises AIOutputValidationError if output does not conform to schema.
        """
        cleaned_excerpt = (cleaned_text or "")[:4000]
        formatted_prompt = self.prompt.format_messages(
            resume_summary=resume_summary,
            cleaned_text_excerpt=cleaned_excerpt,
        )

        llm = self._get_llm()
        structured_llm = llm.with_structured_output(ResumeStrengthAIStructuredOutput)

        try:
            logger.info("Invoking ChatOllama for strength analysis with model %s at %s", self.model, self.base_url)
            start_time = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            duration = time.time() - start_time
            logger.info("ChatOllama strength analysis completed in %.2f seconds", duration)

            if isinstance(result, ResumeStrengthAIStructuredOutput):
                return result
            elif isinstance(result, dict):
                return ResumeStrengthAIStructuredOutput.model_validate(result)
            else:
                return ResumeStrengthAIStructuredOutput.model_validate(result)

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionRefusedError) as conn_err:
            logger.error("Ollama connection failure during strength analysis: %s", conn_err)
            raise OllamaUnavailableError(
                f"Ollama LLM service is unavailable at {self.base_url}. Please ensure Ollama is running."
            ) from conn_err

        except ValidationError as val_err:
            logger.error("Strength analysis structured output validation error: %s", val_err)
            raise AIOutputValidationError(
                f"Model output did not match expected strength analysis schema: {str(val_err)}"
            ) from val_err

        except Exception as exc:
            error_str = str(exc).lower()
            if any(term in error_str for term in ["connect", "refused", "timeout", "unavailable", "port 11434"]):
                logger.error("Ollama connection error during strength analysis: %s", exc)
                raise OllamaUnavailableError(
                    f"Ollama LLM service is unavailable at {self.base_url}: {str(exc)}"
                ) from exc

            logger.error("Unexpected error in StrengthAIEvaluator: %s", exc)
            raise
