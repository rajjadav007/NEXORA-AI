"""
AI-Powered Job Complexity & Insights Generator using LangChain and ChatOllama
Phase 6 | Feature 38: Job Description Report
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.job_description_report import (
    COMPLEXITY_LEVELS,
    JobReportAIStructuredOutput,
)
from app.services.quality_score.ai_evaluator import (
    AIOutputValidationError,
    OllamaUnavailableError,
)

logger = logging.getLogger(__name__)

SYSTEM_REPORT_INSIGHTS_PROMPT = """You are a senior Career Intelligence Analyst.
Given structured job role metadata, extracted requirements, and classified skills for a job posting:
1. Estimate the overall job complexity level (exact values: {complexity_levels}) based on:
   - Technical skill breadth & depth
   - Number of mandatory skills
   - Required experience and seniority
   - Role responsibilities & educational requirements
   Provide a concise 1-2 sentence explanation.
2. Generate 4-5 concise, evidence-grounded insights explaining:
   - What the company expects from candidates
   - Most important technical requirements
   - Main responsibilities
   - Key qualifications & important areas of expertise

RULES:
- Base everything strictly on the provided extracted data. Do NOT invent requirements.
- Do NOT claim any specific candidate is eligible.
- Mark insight source_type as "inferred".
Return valid JSON matching the structured schema.
"""

USER_REPORT_INSIGHTS_TEMPLATE = """Generate complexity analysis and job insights for:

Job Title: {job_title}
Company: {company_name}

=== EXTRACTED INTELLIGENCE (FEATURES #35-#37) ===
{context_json}
"""


class JobReportAIInsightsGenerator:
    """Single-pass ChatOllama generator for complexity estimation and job insights."""

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
            ("system", SYSTEM_REPORT_INSIGHTS_PROMPT),
            ("user", USER_REPORT_INSIGHTS_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.0,
            timeout=self.timeout,
        )

    async def generate_insights(
        self,
        job_title: str,
        company_name: str,
        context_summary: Dict[str, Any],
    ) -> JobReportAIStructuredOutput:
        formatted_prompt = self.prompt.format_messages(
            complexity_levels=", ".join(COMPLEXITY_LEVELS),
            job_title=job_title,
            company_name=company_name,
            context_json=json.dumps(context_summary, ensure_ascii=False)[:6500],
        )

        llm = self._get_llm()
        structured_llm = llm.with_structured_output(JobReportAIStructuredOutput)

        try:
            logger.info("Invoking ChatOllama for job report insights with model %s", self.model)
            start = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            logger.info("Job report insights generated in %.2fs", time.time() - start)

            if result is None:
                raise AIOutputValidationError("Model returned an empty response.")
            if isinstance(result, JobReportAIStructuredOutput):
                return result
            if isinstance(result, str):
                return JobReportAIStructuredOutput.model_validate(json.loads(result))
            return JobReportAIStructuredOutput.model_validate(result)

        except (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.TimeoutException,
            ConnectionRefusedError,
            TimeoutError,
            asyncio.TimeoutError,
        ) as conn_err:
            logger.error("Ollama connection/timeout failure during report insights: %s", conn_err)
            raise OllamaUnavailableError(
                f"Ollama service is unavailable at {self.base_url}: {conn_err}"
            ) from conn_err
        except (ValidationError, json.JSONDecodeError, ValueError, TypeError) as val_err:
            logger.error("Job report insights validation failed: %s", val_err)
            raise AIOutputValidationError(
                f"AI returned malformed job report insights: {val_err}"
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
            logger.error("Unexpected error during job report insights: %s", exc)
            raise AIOutputValidationError(f"Failed to generate job report insights: {exc}") from exc
