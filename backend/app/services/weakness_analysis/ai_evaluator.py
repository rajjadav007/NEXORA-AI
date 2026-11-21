"""
AI-Powered Resume Weakness Evaluator using LangChain and ChatOllama
Phase 4 | Feature 23: Resume Weakness Analysis
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
from app.schemas.weakness_analysis import (
    ResumeWeaknessAIStructuredOutput,
    WeaknessItemAI,
    MissingItemAI,
    WEAKNESS_CATEGORIES,
)
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

SYSTEM_WEAKNESS_PROMPT = """You are a senior Hiring Manager, Technical Recruiter, and Resume Review Expert.
Your task is to analyze candidate resumes and identify critical WEAKNESSES, vague descriptions, missing impact, and missing information across 7 categories:
1. Technical Skills (`technical_skills`): Unorganized lists, buzzword dumping without context, missing proficiency levels, outdated tech without modern equivalents.
2. Projects (`projects`): Vague project descriptions, lack of tech stack specification, missing live links / GitHub repos, absent individual contribution details.
3. Work & Internship Experience (`experience`): Passive duty lists ("Responsible for...", "Helped with..."), lack of quantifiable outcomes / metrics (%, $, latency, throughput, scale), missing business impact, unclear responsibilities.
4. Education Details (`education`): Incomplete degree information, missing graduation year or institution details, unlisted relevant coursework if junior.
5. Achievements & Certifications (`achievements`): Missing dates, unverified issuing bodies, absent competitive or recognized milestones where expected.
6. Professional Summary (`summary`): Generic buzzword-laden summaries ("Hardworking self-starter"), missing target role or core value proposition, or complete absence of a summary.
7. Content Clarity & Relevance (`clarity_relevance`): Jargon overload, spelling/grammar inconsistencies, weak action verbs, awkward formatting structure, redundant statements.

STRICT PRINCIPLES:
- IDENTIFY MISSING INFORMATION SEPARATELY from actual weaknesses. Missing info goes into `missing_information`. Actual content flaws go into `weaknesses`.
- Avoid assuming that missing information is automatically a weakness when it may not be relevant to the candidate (e.g. entry-level candidates may not have 5 years experience or industry awards; certifications are often optional). Mark `is_optional: true` for optional items.
- Focus heavily on identifying VAGUE DESCRIPTIONS and statements lacking MEASURABLE IMPACT. Flag their `weakness_type` appropriately.
- NEVER invent or fabricate missing resume details, fake achievements, or pretend technologies. Ground all evidence strictly in resume text.
- For every weakness, quote the actual vague line or problematic section in `evidence`.
- Provide concrete, actionable `suggested_improvement` with specific rewrite recommendations.
- Assign `priority` as "Critical" (fatal flaws like missing dates or zero metrics in senior roles), "High" (vague major project descriptions), "Medium" (missing summary or soft skill clichés), or "Low" (minor polish).
- Return output strictly matching the provided JSON schema.
"""

USER_WEAKNESS_TEMPLATE = """Evaluate this candidate's resume and identify all substantive weaknesses, vague statements, and missing information:

=== STRUCTURED RESUME DATA ===
{resume_summary}

=== CLEANED RESUME TEXT (EXCERPT) ===
{cleaned_text_excerpt}

Identify all actual weaknesses across the 7 categories (title, category, explanation, evidence, why_it_matters, suggested_improvement, priority, weakness_type).
Separately identify any missing information (section, item, relevance, impact_level, is_optional).
Provide overall_summary and category_recommendations.
"""


class WeaknessAIEvaluator:
    """LangChain + ChatOllama integration for candidate weakness analysis."""

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
            ("system", SYSTEM_WEAKNESS_PROMPT),
            ("user", USER_WEAKNESS_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.1,
            timeout=self.timeout,
        )

    async def evaluate_weaknesses(
        self,
        resume_summary: str,
        cleaned_text: Optional[str] = None,
    ) -> ResumeWeaknessAIStructuredOutput:
        """
        Executes LangChain ChatOllama structured output invocation to detect candidate weaknesses.
        Raises OllamaUnavailableError if Ollama is unreachable.
        Raises AIOutputValidationError if output does not conform to schema.
        """
        cleaned_excerpt = (cleaned_text or "")[:4000]
        formatted_prompt = self.prompt.format_messages(
            resume_summary=resume_summary,
            cleaned_text_excerpt=cleaned_excerpt,
        )

        llm = self._get_llm()
        structured_llm = llm.with_structured_output(ResumeWeaknessAIStructuredOutput)

        try:
            logger.info("Invoking ChatOllama for weakness analysis with model %s at %s", self.model, self.base_url)
            start_time = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            duration = time.time() - start_time
            logger.info("ChatOllama weakness analysis completed in %.2f seconds", duration)

            if isinstance(result, ResumeWeaknessAIStructuredOutput):
                return result
            elif isinstance(result, dict):
                return ResumeWeaknessAIStructuredOutput.model_validate(result)
            else:
                return ResumeWeaknessAIStructuredOutput.model_validate(result)

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionRefusedError) as conn_err:
            logger.error("Ollama connection failure during weakness analysis: %s", conn_err)
            raise OllamaUnavailableError(
                f"Ollama LLM service is unavailable at {self.base_url}. Please ensure Ollama is running."
            ) from conn_err

        except ValidationError as val_err:
            logger.error("Weakness analysis structured output validation error: %s", val_err)
            raise AIOutputValidationError(
                f"Model output did not match expected weakness analysis schema: {str(val_err)}"
            ) from val_err

        except Exception as exc:
            error_str = str(exc).lower()
            if any(term in error_str for term in ["connect", "refused", "timeout", "unavailable", "port 11434"]):
                logger.error("Ollama connection error during weakness analysis: %s", exc)
                raise OllamaUnavailableError(
                    f"Ollama LLM service is unavailable at {self.base_url}: {str(exc)}"
                ) from exc

            logger.error("Unexpected error in WeaknessAIEvaluator: %s", exc)
            raise
