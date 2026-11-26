"""
AI-Powered Skill Classifier using LangChain and ChatOllama
Phase 6 | Feature 37: Mandatory & Preferred Skills Classification
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.job_skill_classification import (
    CLASSIFICATION_TYPES,
    PROFICIENCY_LEVELS,
    SkillClassificationAIStructuredOutput,
)
from app.services.quality_score.ai_evaluator import (
    AIOutputValidationError,
    OllamaUnavailableError,
)

logger = logging.getLogger(__name__)

SYSTEM_SKILL_CLASSIFICATION_PROMPT = """You are a senior Technical Recruiter & Skill Intelligence Engine.
Classify each skill from the extracted job requirements using the original job description as supporting evidence.

CLASSIFICATION RULES (use exact values: {classification_types}):
1. "Mandatory": Explicitly required by the employer (e.g., "Must have Python", "Python programming is required", "Strong knowledge of ML is essential", "Candidates must have experience with SQL").
2. "Preferred": Improves a candidate's chances but is not compulsory (e.g., "Experience with LangChain is preferred", "Knowledge of Docker is an advantage", "Familiarity with AWS is beneficial", "Exposure to RAG is a plus", "nice to have").
3. "Optional": Explicitly optional or additional (e.g., "optional", "additional", "if applicable"). Do NOT assume every unclassified skill is Optional.
4. "Unspecified": Mentioned in the job description without clear mandatory, preferred, or optional importance, OR when statements are genuinely ambiguous.

PRIORITY SCORING RULES (0 to 100, representing requirement priority, NOT candidate proficiency):
- Mandatory: 80-100 (priority_level: "High")
- Preferred: 40-79 (priority_level: "Medium")
- Optional: 1-39 (priority_level: "Low")
- Unspecified: null (priority_level: "Low")

EXPECTED PROFICIENCY PER SKILL (use exact values: {proficiency_levels}):
- Only assign "Beginner", "Intermediate", "Advanced", or "Expert" when supported by the job description.
- Otherwise use "Unspecified". Do NOT invent proficiency levels.

CONFLICT & DEDUPLICATION RULES:
- Avoid duplicate skills.
- If a skill has conflicting statements (e.g., mentioned as required in one section and preferred in another), resolve based on explicit requirement priority (Mandatory > Preferred > Optional) and cite the decisive evidence.
- Keep "source_type" as "explicit" when directly stated in the text, or "inferred" when deduced from context.
- "confidence_score" (0.0 to 1.0) reflects your certainty in the classification, separate from priority_score.
- "evidence" must be a short supporting quote or phrase from the original job description.

Return valid JSON matching the structured schema.
"""

USER_SKILL_CLASSIFICATION_TEMPLATE = """Classify the skills for this job posting using the extracted requirements and original job description:

Job Title: {job_title}
Company: {company_name}

=== FEATURE #36 EXTRACTED SKILLS ===
{extracted_skills_json}

=== ORIGINAL JOB DESCRIPTION ===
{description}
"""


class SkillClassificationAIExtractor:
    """LangChain + ChatOllama integration for evidence-based skill classification."""

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
            ("system", SYSTEM_SKILL_CLASSIFICATION_PROMPT),
            ("user", USER_SKILL_CLASSIFICATION_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.0,
            timeout=self.timeout,
        )

    async def classify_skills(
        self,
        description: str,
        extracted_skills: List[Dict[str, Any]],
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> SkillClassificationAIStructuredOutput:
        """
        Invoke ChatOllama with structured output to classify extracted skills.
        Raises OllamaUnavailableError on connection/timeout failures.
        Raises AIOutputValidationError on malformed or invalid model responses.
        """
        formatted_prompt = self.prompt.format_messages(
            classification_types=", ".join(CLASSIFICATION_TYPES),
            proficiency_levels=", ".join(PROFICIENCY_LEVELS),
            job_title=job_title or "Not provided",
            company_name=company_name or "Not provided",
            extracted_skills_json=json.dumps(extracted_skills, ensure_ascii=False)[:6000],
            description=(description or "")[:8000],
        )

        llm = self._get_llm()
        structured_llm = llm.with_structured_output(SkillClassificationAIStructuredOutput)

        try:
            logger.info("Invoking ChatOllama for skill classification with model %s", self.model)
            start = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            logger.info("Skill classification completed in %.2fs", time.time() - start)

            if result is None:
                raise AIOutputValidationError("Model returned an empty response.")
            if isinstance(result, SkillClassificationAIStructuredOutput):
                return result
            if isinstance(result, str):
                return SkillClassificationAIStructuredOutput.model_validate(json.loads(result))
            return SkillClassificationAIStructuredOutput.model_validate(result)

        except (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.TimeoutException,
            ConnectionRefusedError,
            TimeoutError,
            asyncio.TimeoutError,
        ) as conn_err:
            logger.error("Ollama connection/timeout failure during skill classification: %s", conn_err)
            raise OllamaUnavailableError(
                f"Ollama service is unavailable at {self.base_url}: {conn_err}"
            ) from conn_err
        except (ValidationError, json.JSONDecodeError, ValueError, TypeError) as val_err:
            logger.error("Skill classification output validation failed: %s", val_err)
            raise AIOutputValidationError(
                f"AI returned malformed skill classification output: {val_err}"
            ) from val_err
        except AIOutputValidationError:
            raise
        except Exception as exc:
            err_name = type(exc).__name__.lower()
            err_msg = str(exc).lower()
            if "connect" in err_name or "timeout" in err_name or "connection" in err_msg or "timed out" in err_msg:
                raise OllamaUnavailableError(
                    f"Ollama service is unavailable at {self.base_url}: {exc}"
                ) from exc
            logger.error("Unexpected error during skill classification: %s", exc)
            raise AIOutputValidationError(f"Failed to classify skills with Ollama: {exc}") from exc
