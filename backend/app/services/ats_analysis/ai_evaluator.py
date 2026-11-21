"""
AI-Powered ATS Contextual Feedback Engine using LangChain and ChatOllama
Phase 4 | Feature 24: ATS Compatibility Analysis
Reuses existing Ollama + LangChain infrastructure for qualitative explanations,
before/after rewrite recommendations, and keyword advice ONLY. Never determines scores.
"""

import logging
import time
from typing import Dict, Any, Optional, List

import httpx
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ats_analysis import (
    ATSAIStructuredFeedback,
    AIFeedback,
    RecommendationItem,
)

logger = logging.getLogger(__name__)

SYSTEM_ATS_FEEDBACK_PROMPT = """You are an Executive Career Coach and Applicant Tracking System (ATS) optimization specialist.
The candidate's resume has already been evaluated by a transparent deterministic ATS scoring engine.
Your sole job is to provide CONTEXTUAL EXPLANATIONS and ACTIONABLE BEFORE-AND-AFTER RECOMMENDATIONS.

RULES:
- Do NOT generate or change any numeric score or grade. The deterministic score is already final.
- Clearly explain how hiring managers and ATS search filters will interpret the candidate's resume.
- For each recommendation, provide:
  * title: concise issue title
  * category: relevant section (e.g. Work Experience, Skills, Contact Info, Layout)
  * priority: Critical, High, Medium, or Low
  * current_state: quote or summarize the problematic current phrasing from the resume
  * recommended_rewrite: provide an exact, polished ATS-friendly replacement
- Provide practical keyword optimization advice without promoting keyword stuffing.
- Ground all advice strictly in the provided resume data and deterministic findings.
"""

USER_ATS_FEEDBACK_TEMPLATE = """Review the candidate's resume and deterministic ATS audit findings:

=== DETERMINISTIC ATS AUDIT ===
ATS Score: {ats_score}/100 ({score_grade})
Category Scores:
{category_scores_summary}

Verified Content Issues:
{verified_issues_summary}

Formatting & Layout Risks:
{formatting_risks_summary}

Detected Keywords: {keywords_summary}

=== RESUME TEXT EXCERPT ===
{resume_excerpt}

Generate:
1. An executive 2-3 sentence summary explaining the candidate's ATS readiness and primary obstacles.
2. 3 to 5 targeted recommendations with specific 'current_state' quotes and exact 'recommended_rewrite' examples.
3. Concrete keyword optimization advice.
"""


class ATSAIEvaluator:
    """LangChain + ChatOllama integration for ATS qualitative feedback."""

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
            ("system", SYSTEM_ATS_FEEDBACK_PROMPT),
            ("user", USER_ATS_FEEDBACK_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.1,
            timeout=self.timeout,
        )

    def _generate_fallback_feedback(
        self,
        ats_score: int,
        score_grade: str,
        verified_issues: List[Any],
        formatting_risks: List[Any],
    ) -> AIFeedback:
        """Deterministic fallback if Ollama is unavailable."""
        all_issues = list(verified_issues) + list(formatting_risks)
        recs: List[RecommendationItem] = []

        for issue in all_issues[:5]:
            recs.append(
                RecommendationItem(
                    title=getattr(issue, "title", "ATS Optimization"),
                    category=getattr(issue, "category_name", "General"),
                    priority=getattr(issue, "severity", "Medium"),
                    current_state="; ".join(getattr(issue, "evidence", ["Current formatting"]))[:150],
                    recommended_rewrite=getattr(issue, "suggested_fix", "Update to standard format."),
                )
            )

        if not recs:
            recs.append(
                RecommendationItem(
                    title="Maintain Clean Standard Structure",
                    category="Overall Layout",
                    priority="Low",
                    current_state="Clean single-column structure detected.",
                    recommended_rewrite="Continue using standard headings and outcome-oriented bullet points.",
                )
            )

        summary = (
            f"Resume achieved a deterministic ATS score of {ats_score}/100 ({score_grade}). "
            f"Identified {len(verified_issues)} verified content gaps and {len(formatting_risks)} layout risks. "
            "Resolving highlighted issues will improve recruiter screening pass rates."
        )

        advice = (
            "Align technical skills with targeted job descriptions. Use exact industry-standard "
            "keywords and quantify accomplishments with measurable metrics (scale, %, $)."
        )

        return AIFeedback(
            executive_summary=summary,
            tailored_recommendations=recs,
            keyword_optimization_advice=advice,
        )

    async def generate_feedback(
        self,
        ats_score: int,
        score_grade: str,
        category_scores: Dict[str, Any],
        verified_issues: List[Any],
        formatting_risks: List[Any],
        keywords: List[str],
        cleaned_text: Optional[str] = None,
    ) -> AIFeedback:
        """
        Calls LangChain ChatOllama with structured output to synthesize qualitative feedback.
        Falls back seamlessly to deterministic templates if Ollama is unavailable.
        """
        # Prepare summaries
        cat_lines = [f"- {c.name}: {c.score:.1f}/{c.max_score:.1f} ({c.status})" for c in category_scores.values()]
        issues_lines = [f"- [{i.severity}] {i.title}: {i.explanation}" for i in verified_issues]
        risks_lines = [f"- [{r.severity}] {r.title}: {r.explanation}" for r in formatting_risks]

        formatted_prompt = self.prompt.format_messages(
            ats_score=ats_score,
            score_grade=score_grade,
            category_scores_summary="\n".join(cat_lines) if cat_lines else "All categories evaluated.",
            verified_issues_summary="\n".join(issues_lines) if issues_lines else "None detected.",
            formatting_risks_summary="\n".join(risks_lines) if risks_lines else "None detected.",
            keywords_summary=", ".join(keywords[:20]) if keywords else "None",
            resume_excerpt=(cleaned_text or "")[:3000],
        )

        try:
            llm = self._get_llm()
            structured_llm = llm.with_structured_output(ATSAIStructuredFeedback)

            logger.info("Invoking ChatOllama for ATS feedback with model %s at %s", self.model, self.base_url)
            start_time = time.time()
            result = await structured_llm.ainvoke(formatted_prompt)
            duration = time.time() - start_time
            logger.info("ChatOllama ATS feedback completed in %.2f seconds", duration)

            if isinstance(result, dict):
                structured = ATSAIStructuredFeedback.model_validate(result)
            elif isinstance(result, ATSAIStructuredFeedback):
                structured = result
            else:
                structured = ATSAIStructuredFeedback.model_validate(result)

            recommendations = [
                RecommendationItem(
                    title=r.title,
                    category=r.category,
                    priority=r.priority,
                    current_state=r.current_state,
                    recommended_rewrite=r.recommended_rewrite,
                )
                for r in structured.tailored_recommendations
            ]

            return AIFeedback(
                executive_summary=structured.executive_summary,
                tailored_recommendations=recommendations,
                keyword_optimization_advice=structured.keyword_optimization_advice,
            )

        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, ConnectionRefusedError) as conn_err:
            logger.warning("Ollama unavailable for ATS feedback, using deterministic fallback: %s", conn_err)
            return self._generate_fallback_feedback(ats_score, score_grade, verified_issues, formatting_risks)

        except ValidationError as val_err:
            logger.warning("ATS feedback schema validation issue, using deterministic fallback: %s", val_err)
            return self._generate_fallback_feedback(ats_score, score_grade, verified_issues, formatting_risks)

        except Exception as exc:
            logger.warning("Unexpected error in ATS feedback generation, using deterministic fallback: %s", exc)
            return self._generate_fallback_feedback(ats_score, score_grade, verified_issues, formatting_risks)


ats_ai_evaluator = ATSAIEvaluator()
