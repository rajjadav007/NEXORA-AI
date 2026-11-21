"""
AI-Powered Resume Achievement Evaluator using LangChain and ChatOllama
Phase 4 | Feature 26: Achievement Analysis
Extracts accomplishments across experience, projects, hackathons, awards,
and leadership; identifies measurable metrics and produces Google X-Y-Z rewrites.
"""

import re
import logging
import time
from typing import Dict, Any, Optional, List

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.achievement_analysis import (
    ResumeAchievementAIStructuredOutput,
    AchievementItemAI,
    ACHIEVEMENT_CATEGORIES,
)
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)

logger = logging.getLogger(__name__)

SYSTEM_ACHIEVEMENT_PROMPT = """You are a Principal Talent Assessor and Executive Achievement Coach.
Your task is to analyze candidate resume data and identify all significant ACCOMPLISHMENTS, MEASURABLE RESULTS, and IMPACT STATEMENTS across 7 categories:
1. Work & Internship Experience (`experience`): Production deployments, scale metrics, latency reductions, client wins, team execution.
2. Academic Projects (`academic_projects`): Research outcomes, capstones, thesis deliverables, high academic project marks.
3. Personal & Professional Projects (`projects`): Open-source builds, deployed architectures, public apps, user adoption.
4. Hackathons & Competitions (`competitions`): Placement (1st, 2nd, finalist), hackathon prototypes built under time constraints.
5. Awards & Recognitions (`awards`): Dean's list, employee of the quarter, competitive scholarships, honors.
6. Certifications (`certifications`): Industry credentials, professional licenses, specialized exam achievements.
7. Leadership & Volunteering (`leadership`): Mentoring, student organization leadership, cross-functional committee leadership.

STRICT PRINCIPLES:
- IDENTIFY MEASURABLE IMPACT: Detect percentages (e.g. 45%), numbers (e.g. 3M RPS, $50K), time saved (e.g. 10 hours/week), user scale (e.g. 50k users), and performance gains.
- IDENTIFY NON-MEASURABLE ACHIEVEMENTS: When an accomplishment lacks quantifiable metrics, set `is_quantified: false` and state in `missing_metrics_note` what metric could be added.
- FACTUAL GROUNDING: NEVER invent numbers, percentages, awards, responsibilities, or accomplishments that do not appear in the candidate's resume.
- VERIFIED EVIDENCE: Distinguish verified resume evidence from missing metrics. Put exact resume quotes in `evidence`.
- SUGGESTED STATEMENTS: For every achievement, provide an improved statement following Google's X-Y-Z formula: "Accomplished [X] as measured by [Y] by doing [Z]" while strictly preserving the candidate's factual meaning.
- Return output strictly matching the provided JSON schema.
"""

USER_ACHIEVEMENT_TEMPLATE = """Evaluate this candidate's resume data and extract all accomplishments:

=== STRUCTURED RESUME DATA ===
{resume_summary}

=== CLEANED RESUME TEXT (EXCERPT) ===
{cleaned_text_excerpt}

Extract accomplishments across the 7 categories. Provide title, category, original_statement, is_quantified, detected metrics (percentages, numbers, time_saved, users_impacted, performance_gain), evidence, impact_level, professional_relevance, quality_rating, suggested_statement (Google X-Y-Z formula), and explanation.
"""


class AchievementAIEvaluator:
    """LangChain + ChatOllama integration for candidate achievement extraction and impact scoring."""

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
            ("system", SYSTEM_ACHIEVEMENT_PROMPT),
            ("user", USER_ACHIEVEMENT_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.1,
            timeout=self.timeout,
        )

    def _detect_metrics_heuristic(self, text: str) -> Dict[str, List[str]]:
        """Extracts numbers, percentages, and scale metrics deterministically."""
        pcts = re.findall(r"\b\d+(?:\.\d+)?%", text)
        numbers = re.findall(r"\b\d+[kKmMbB]?\+?\s*(?:requests|users|clients|rps|transactions|records|queries|dollars|\$)", text, re.IGNORECASE)
        time_m = re.findall(r"\b\d+\s*(?:hours|hrs|minutes|mins|days|weeks|months|seconds|ms)\b", text, re.IGNORECASE)
        perf_m = re.findall(r"\b(?:reduced|improved|optimized|decreased|accelerated|boosted)\s+[^,.]+\b", text, re.IGNORECASE)

        return {
            "percentages": pcts,
            "numbers": numbers,
            "time_saved": time_m,
            "users_impacted": [n for n in numbers if any(k in n.lower() for k in ["users", "clients"])],
            "performance_gain": perf_m,
        }

    def _generate_fallback_achievements(
        self,
        resume_summary: str,
        cleaned_text: Optional[str],
    ) -> ResumeAchievementAIStructuredOutput:
        """Deterministic heuristic fallback if Ollama service is unreachable."""
        text = cleaned_text or resume_summary or ""
        lines = [line.strip().lstrip("-•* ") for line in text.split("\n") if len(line.strip()) > 25]

        items: List[AchievementItemAI] = []
        for line in lines[:8]:
            m = self._detect_metrics_heuristic(line)
            is_quant = bool(m["percentages"] or m["numbers"] or m["time_saved"] or m["performance_gain"])

            # Classify category
            cat = "experience"
            lower = line.lower()
            if any(k in lower for k in ["project", "app", "platform", "system"]):
                cat = "projects"
            elif any(k in lower for k in ["hackathon", "competition", "contest"]):
                cat = "competitions"
            elif any(k in lower for k in ["award", "honor", "scholarship", "dean"]):
                cat = "awards"
            elif any(k in lower for k in ["cert", "license", "certified"]):
                cat = "certifications"

            quality = "Strong" if is_quant else "Moderate"
            impact = "High" if m["percentages"] or m["numbers"] else "Medium"

            metric_str = m["percentages"][0] if m["percentages"] else (m["numbers"][0] if m["numbers"] else "measurable outcomes")
            suggested = f"Delivered key capabilities resulting in {metric_str} by applying technical expertise ({line[:70]}...)."

            items.append(
                AchievementItemAI(
                    title=f"{cat.replace('_', ' ').capitalize()} Accomplishment",
                    category=cat,
                    original_statement=line,
                    is_quantified=is_quant,
                    percentages=m["percentages"],
                    numbers=m["numbers"],
                    time_saved=m["time_saved"],
                    users_impacted=m["users_impacted"],
                    performance_gain=m["performance_gain"],
                    has_verified_metrics=is_quant,
                    missing_metrics_note=None if is_quant else "Add specific percentage, user count, or latency metrics.",
                    evidence=[line[:100]],
                    impact_level=impact,
                    professional_relevance="High",
                    quality_rating=quality,
                    suggested_statement=suggested,
                    explanation="Demonstrates applied capability in production or technical execution.",
                )
            )

        if not items:
            items.append(
                AchievementItemAI(
                    title="Engineering Delivery",
                    category="experience",
                    original_statement="Developed and deployed software solutions.",
                    is_quantified=False,
                    percentages=[],
                    numbers=[],
                    time_saved=[],
                    users_impacted=[],
                    performance_gain=[],
                    has_verified_metrics=False,
                    missing_metrics_note="Specify request volume, user base, or release velocity improvements.",
                    evidence=["Developed and deployed software solutions"],
                    impact_level="Medium",
                    professional_relevance="High",
                    quality_rating="Moderate",
                    suggested_statement="Engineered and delivered core software solutions improving feature velocity.",
                    explanation="Baseline technical execution requiring quantification for executive impact.",
                )
            )

        return ResumeAchievementAIStructuredOutput(
            executive_summary="Candidate demonstrates foundational technical execution with valuable opportunities to quantify delivery scale, performance improvements, and business outcomes.",
            achievements=items,
            category_highlights={
                "experience": "Core delivery roles identified with strong baseline responsibilities.",
                "projects": "Demonstrated technical initiative across project builds.",
            },
        )

    async def evaluate_achievements(
        self,
        resume_summary: str,
        cleaned_text: Optional[str] = None,
    ) -> ResumeAchievementAIStructuredOutput:
        """
        Invokes LangChain ChatOllama structured output to analyze candidate achievements.
        Falls back seamlessly to deterministic extraction if Ollama is unavailable.
        """
        cleaned_excerpt = (cleaned_text or "")[:4000]
        formatted_prompt = self.prompt.format_messages(
            resume_summary=resume_summary,
            cleaned_text_excerpt=cleaned_excerpt,
        )

        try:
            llm = self._get_llm()
            structured_llm = llm.with_structured_output(ResumeAchievementAIStructuredOutput)

            logger.info("Invoking ChatOllama for achievement analysis with model %s at %s", self.model, self.base_url)
            start_time = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            duration = time.time() - start_time
            logger.info("ChatOllama achievement analysis completed in %.2f seconds", duration)

            if isinstance(result, ResumeAchievementAIStructuredOutput):
                return result
            elif isinstance(result, dict):
                return ResumeAchievementAIStructuredOutput.model_validate(result)
            else:
                return ResumeAchievementAIStructuredOutput.model_validate(result)

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionRefusedError) as conn_err:
            logger.warning("Ollama unavailable for achievement analysis, using fallback: %s", conn_err)
            return self._generate_fallback_achievements(resume_summary, cleaned_text)

        except ValidationError as val_err:
            logger.warning("Achievement analysis structured validation error, using fallback: %s", val_err)
            return self._generate_fallback_achievements(resume_summary, cleaned_text)

        except Exception as exc:
            logger.warning("Unexpected error in achievement analysis, using fallback: %s", exc)
            return self._generate_fallback_achievements(resume_summary, cleaned_text)


achievement_ai_evaluator = AchievementAIEvaluator()
