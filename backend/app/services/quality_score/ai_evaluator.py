"""
AI-Powered Resume Quality Evaluator using LangChain and ChatOllama
Phase 4 | Feature 21: Resume Quality Score Engine
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
from app.schemas.quality_score import (
    ResumeQualityAIStructuredOutput,
    CategoryEvaluationAI,
)

logger = logging.getLogger(__name__)


class OllamaUnavailableError(Exception):
    """Raised when Ollama server is unreachable, connection times out, or service is down."""
    pass


class AIOutputValidationError(Exception):
    """Raised when Ollama output fails Pydantic schema validation."""
    pass


SYSTEM_EVALUATOR_PROMPT = """You are an objective, senior Career & Resume Evaluation Intelligence Engine.
Your task is to analyze candidate resumes and evaluate their quality across 8 structured dimensions:
1. Completeness: Presence and depth of all core sections (contact, summary, skills, experience, education, projects, achievements).
2. Professional Summary: Clarity of career identity, target role positioning, value proposition, avoiding generic buzzwords.
3. Technical Skills: Categorization, relevance, depth, modern tech stack coverage, contextual backing.
4. Work Experience: Action-oriented bullet points, measurable impact (quantified metrics, scale, revenue), career progression.
5. Project Descriptions: Technical complexity, problem statements, technology stack used, tangible outcomes.
6. Education: Degree, institution, field of study, graduation timeline, relevant academic distinction.
7. Achievements: Demonstrable external validation (certifications, competitions, awards, hackathons, publications).
8. Content Clarity: Conciseness, readability, bullet structure, avoidance of length padding and filler text.

SCORING PRINCIPLES:
- DO NOT reward a resume simply for being long. Long, rambling resumes with no metrics or achievements must receive LOWER clarity and impact scores.
- Evaluate tangible evidence: specific technologies, numbers, outcomes, and clear causality.
- Provide constructive, specific, professional explanations and actionable suggestions.
- For each category, provide a `score_ratio` strictly between 0.0 (completely missing/poor) and 1.0 (outstanding/exceptional).
- Return your output matching the required structured schema.
"""

USER_EVALUATOR_TEMPLATE = """Please evaluate this candidate's resume based on the structured sections and cleaned text below:

=== STRUCTURED RESUME DATA SUMMARY ===
{resume_summary}

=== OBJECTIVE DETERMINISTIC FINDINGS ===
{deterministic_findings}

=== CLEANED RESUME TEXT (EXCERPT) ===
{cleaned_text_excerpt}

Analyze each of the 8 categories with a score_ratio (0.0 to 1.0), diagnostic explanation, strengths, and targeted improvements. Also supply top overall strengths, missing critical information, and priority improvements.
"""


class QualityScoreAIEvaluator:
    """LangChain + ChatOllama integration for qualitative resume evaluation."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        # Quality score evaluation benefits from adequate timeout for multi-category reasoning
        self.timeout = timeout or max(settings.OLLAMA_TIMEOUT_SECONDS, 30.0)

        # Build LangChain prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_EVALUATOR_PROMPT),
            ("user", USER_EVALUATOR_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        """Instantiates ChatOllama with deterministic temperature."""
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.1,
            timeout=self.timeout,
        )

    async def evaluate_resume(
        self,
        resume_summary: str,
        deterministic_findings: Dict[str, Any],
        cleaned_text: Optional[str] = None,
    ) -> ResumeQualityAIStructuredOutput:
        """
        Executes LangChain ChatOllama structured output invocation.
        Raises OllamaUnavailableError if Ollama is unreachable.
        Raises AIOutputValidationError if output does not conform to schema.
        """
        cleaned_excerpt = (cleaned_text or "")[:4000]
        formatted_prompt = self.prompt.format_messages(
            resume_summary=resume_summary,
            deterministic_findings=json.dumps(deterministic_findings, indent=2),
            cleaned_text_excerpt=cleaned_excerpt,
        )

        llm = self._get_llm()
        structured_llm = llm.with_structured_output(ResumeQualityAIStructuredOutput)

        try:
            logger.info("Invoking ChatOllama for resume quality scoring with model %s at %s", self.model, self.base_url)
            start_time = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            duration = time.time() - start_time
            logger.info("ChatOllama quality score completed in %.2f seconds", duration)

            if isinstance(result, ResumeQualityAIStructuredOutput):
                return result
            elif isinstance(result, dict):
                return ResumeQualityAIStructuredOutput.model_validate(result)
            else:
                # If result is somehow not the expected model
                return ResumeQualityAIStructuredOutput.model_validate(result)

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionRefusedError) as conn_err:
            logger.error("Ollama connection failure: %s", conn_err)
            raise OllamaUnavailableError(
                f"Ollama LLM service is unavailable at {self.base_url}. Please ensure Ollama is running."
            ) from conn_err

        except ValidationError as val_err:
            logger.error("AI structured output validation error: %s", val_err)
            raise AIOutputValidationError(
                f"Model output did not match expected quality score schema: {str(val_err)}"
            ) from val_err

        except Exception as exc:
            error_str = str(exc).lower()
            if any(term in error_str for term in ["connect", "refused", "timeout", "unavailable", "port 11434"]):
                logger.error("Ollama connection or network error: %s", exc)
                raise OllamaUnavailableError(
                    f"Ollama LLM service is unavailable at {self.base_url}: {str(exc)}"
                ) from exc

            logger.error("Unexpected error in QualityScoreAIEvaluator: %s", exc)
            raise
