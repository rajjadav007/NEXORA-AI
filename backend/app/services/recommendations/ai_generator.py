"""
AI-Powered Resume Improvement Recommendations Generator using LangChain and ChatOllama.
Phase 4 | Feature 27: Resume Improvement Recommendations
"""

import json
import logging
import time
from typing import Optional, List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from app.core.config import settings
from app.schemas.recommendations import (
    ResumeRecommendationsAIOutput,
    RecommendationItemAI,
)
from app.services.quality_score.ai_evaluator import (
    OllamaUnavailableError,
    AIOutputValidationError,
)
from app.services.recommendations.categories import (
    normalize_category_key,
    get_category_display_name,
)

logger = logging.getLogger(__name__)

SYSTEM_RECOMMENDATION_PROMPT = """You are a Senior Career Strategist, Principal Technical Recruiter, and ATS Systems Architect.
Your task is to synthesize the prior analysis findings of a candidate's resume (Quality Score, Strengths, Weaknesses, ATS Compatibility, Grammar/Clarity, and Achievement Analysis) and produce an intelligent, personalized, and prioritized set of actionable improvement recommendations.

COVERAGE AREAS (Produce recommendations across these 8 categories where applicable):
1. `technical_skills`: Technical skills presentation (grouping by category/proficiency, adding relevant modern tools).
2. `professional_summary`: Professional summary (impactful opening, target role alignment, unique value proposition).
3. `project_descriptions`: Project descriptions (tech stack clarity, architectural highlights, live/repo links, business context).
4. `work_experience`: Work & internship experience (action verbs, ownership scope, clear responsibilities, career progression).
5. `achievements_impact`: Achievements & measurable impact (quantification using Google's X-Y-Z formula, percentages, metrics, business scale).
6. `ats_compatibility`: ATS compatibility (standard section titles, clean single-column format, keyword density, parser-safe layout).
7. `grammar_clarity`: Grammar & clarity (eliminating passive voice, removing wordiness, fixing typos, professional tone).
8. `resume_completeness`: Resume completeness (missing sections, complete contact details, dates, education consistency).

REQUIREMENTS PER RECOMMENDATION:
- Title: Concise, imperative, and action-oriented (e.g. "Add Quantifiable Metrics to CloudStream Project")
- Category: One of the 8 categories above
- Detailed Explanation: Clear explanation of what is lacking or suboptimal in the resume
- Reason for Recommendation: Why this change matters for hiring managers, recruiters, or ATS algorithms
- Supporting Resume Evidence: Specific text quote or concrete reference from the candidate's existing resume
- Suggested Action: Exact, high-impact instruction or example template to fix the problem
- Priority: "Critical" (must fix immediately / recruiter dealbreaker), "High" (major impact on interview rate), "Medium" (noticeable improvement), or "Low" (nice-to-have refinement)
- Estimated Effort: "Easy" (<15 min), "Medium" (30-60 min), or "Hard" (>1 hr rewrite)
- Related Analysis Feature: Name the source analysis (e.g., "Feature #24: ATS Compatibility Analysis", "Feature #26: Achievement Analysis", etc.)

FACTUAL INTEGRITY:
- Base all recommendations on the candidate's actual findings and resume content provided.
- Do NOT invent fictional companies or fake credentials.
- Strictly return valid JSON matching the schema.
"""

USER_RECOMMENDATION_TEMPLATE = """Synthesize these resume analysis findings into personalized, prioritized recommendations:

=== RESUME OVERVIEW ===
{resume_overview}

=== COMBINED FINDINGS FROM FEATURES #21 TO #26 ===
{combined_findings}

=== ANALYSIS COVERAGE STATUS ===
{coverage_status}

Generate prioritized recommendations across the 8 categories. Ensure clear evidence, reasons, actionable steps, and appropriate priorities.
"""


class RecommendationAIGenerator:
    """LangChain + ChatOllama integration for generating resume recommendations."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or max(settings.OLLAMA_TIMEOUT_SECONDS, 35.0)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_RECOMMENDATION_PROMPT),
            ("user", USER_RECOMMENDATION_TEMPLATE),
        ])

    def _get_llm(self) -> ChatOllama:
        return ChatOllama(
            base_url=self.base_url,
            model=self.model,
            temperature=0.2,
            timeout=self.timeout,
        )

    def generate_heuristic_recommendations(
        self,
        combined_findings: Dict[str, Any],
        coverage_summary: Dict[str, Any],
    ) -> ResumeRecommendationsAIOutput:
        """
        Deterministic high-quality recommendation generator when Ollama is unreachable.
        Synthesizes recommendations directly from the structured findings of Features #21 to #26.
        """
        recommendations: List[RecommendationItemAI] = []
        findings_by_cat = combined_findings.get("by_category", {})

        # 1. ATS Compatibility Recommendations
        ats_findings = findings_by_cat.get("ats_compatibility", [])
        if ats_findings:
            for item in ats_findings[:3]:
                severity = item.get("severity", "medium").lower()
                priority = "Critical" if severity in ["high", "critical"] else "High"
                recommendations.append(
                    RecommendationItemAI(
                        title=f"Fix ATS Formatting: {item.get('title', 'Resolve ATS Parsing Issue')}",
                        category="ats_compatibility",
                        explanation=item.get("explanation", "ATS parsers may fail to extract your resume sections cleanly."),
                        reason="Modern Applicant Tracking Systems filter out non-standard layouts, tables, and unconventional headings before a human recruiter reads them.",
                        evidence=item.get("evidence", item.get("title", "ATS compatibility findings")),
                        suggested_action=item.get("suggested_fix", "Use standard single-column layout with conventional section headings like 'Work Experience' and 'Education'."),
                        priority=priority,
                        estimated_effort="Easy",
                        related_feature="Feature #24: ATS Compatibility Analysis",
                    )
                )
        else:
            recommendations.append(
                RecommendationItemAI(
                    title="Optimize ATS Layout and Standard Section Headers",
                    category="ats_compatibility",
                    explanation="Ensure standard single-column layout and conventional section titles like 'Work Experience', 'Education', and 'Skills'.",
                    reason="Automated ATS parsers discard graphics, tables, and non-standard icons.",
                    evidence="Document structural layout check",
                    suggested_action="Use simple clean headers and avoid multi-column tables or text boxes.",
                    priority="High",
                    estimated_effort="Easy",
                    related_feature="Feature #24: ATS Compatibility Analysis",
                )
            )

        # 2. Achievements and Measurable Impact Recommendations
        achieve_findings = findings_by_cat.get("achievements_impact", [])
        if achieve_findings:
            for item in achieve_findings[:3]:
                unquantified = item.get("unquantified", False)
                title = f"Quantify Impact: {item.get('title', 'Add measurable metrics to achievements')}"
                evidence = item.get("evidence", item.get("statement", ""))
                suggested = item.get("suggested_statement") or "Use Google's X-Y-Z formula: Accomplished [X] as measured by [Y] by doing [Z]."
                recommendations.append(
                    RecommendationItemAI(
                        title=title,
                        category="achievements_impact",
                        explanation="Recruiters look for verifiable numbers, scale, and business outcomes rather than passive job descriptions.",
                        reason="Quantified bullets increase recruiter engagement and interview callbacks by up to 40%.",
                        evidence=evidence,
                        suggested_action=f"Revise bullet point using concrete figures: {suggested}",
                        priority="High" if unquantified else "Medium",
                        estimated_effort="Medium",
                        related_feature="Feature #26: Achievement Analysis",
                    )
                )
        else:
            recommendations.append(
                RecommendationItemAI(
                    title="Incorporate Measurable Impact and Percentages in Bullets",
                    category="achievements_impact",
                    explanation="Express key achievements using Google's X-Y-Z formula: 'Accomplished [X] as measured by [Y] by doing [Z]'.",
                    reason="Quantified accomplishments provide objective proof of capability.",
                    evidence="Experience bullet points analysis",
                    suggested_action="Add metrics such as percentage performance improvements, latency cuts, revenue increases, or user adoption scale.",
                    priority="High",
                    estimated_effort="Medium",
                    related_feature="Feature #26: Achievement Analysis",
                )
            )

        # 3. Weakness Analysis / Missing Sections Recommendations
        weakness_findings = findings_by_cat.get("weaknesses", [])
        for item in weakness_findings[:3]:
            cat = normalize_category_key(item.get("category", "resume_completeness"))
            recommendations.append(
                RecommendationItemAI(
                    title=item.get("title", "Address Resume Content Gap"),
                    category=cat,
                    explanation=item.get("explanation", "Identified resume content gap requiring clarification."),
                    reason=item.get("why_it_matters", "Clear, comprehensive resumes build recruiter trust and show strong domain competence."),
                    evidence=item.get("evidence", ""),
                    suggested_action=item.get("suggested_improvement", "Add missing details and clarify project or role scope."),
                    priority=item.get("priority", "Medium"),
                    estimated_effort="Medium",
                    related_feature="Feature #23: Weakness Analysis",
                )
            )

        # 4. Grammar and Clarity Recommendations
        grammar_findings = findings_by_cat.get("grammar_clarity", [])
        if grammar_findings:
            first_issue = grammar_findings[0]
            recommendations.append(
                RecommendationItemAI(
                    title="Refine Sentence Clarity and Grammar",
                    category="grammar_clarity",
                    explanation=f"Found {len(grammar_findings)} phrasing or grammatical areas to tighten.",
                    reason="Flawless grammar and active voice demonstrate attention to detail and strong written communication.",
                    evidence=first_issue.get("original_text", "Grammar & clarity analysis detections"),
                    suggested_action=first_issue.get("suggested_text", "Replace passive verbs with crisp active action verbs and ensure consistent tense."),
                    priority="Medium",
                    estimated_effort="Easy",
                    related_feature="Feature #25: Grammar & Clarity Analysis",
                )
            )
        else:
            recommendations.append(
                RecommendationItemAI(
                    title="Audit Active Voice and Concise Phrasing",
                    category="grammar_clarity",
                    explanation="Eliminate redundant phrases and ensure consistent past tense for prior roles and present tense for current position.",
                    reason="Crisp, concise prose keeps recruiters engaged during 6-second initial resume scans.",
                    evidence="General resume writing tone audit",
                    suggested_action="Proofread bullet points for active action verbs and remove filler phrases like 'responsibilities included'.",
                    priority="Low",
                    estimated_effort="Easy",
                    related_feature="Feature #25: Grammar & Clarity Analysis",
                )
            )

        # 5. Technical Skills Presentation
        skills_findings = findings_by_cat.get("technical_skills", [])
        if skills_findings or not any(r.category == "technical_skills" for r in recommendations):
            recommendations.append(
                RecommendationItemAI(
                    title="Organize Technical Skills by Category and Proficiency",
                    category="technical_skills",
                    explanation="Skills should be structured into clear domains (e.g. Languages, Frameworks, Cloud/DevOps, Databases) rather than an unorganized list.",
                    reason="Allows recruiters and engineering managers to verify your technical stack match in under 5 seconds.",
                    evidence="Skills section listing",
                    suggested_action="Group skills into: Languages (Python, Java), Frameworks (FastAPI, React), and Tools & Cloud (Docker, AWS, PostgreSQL).",
                    priority="Medium",
                    estimated_effort="Easy",
                    related_feature="Feature #22: Strength Analysis & Feature #21: Quality Score",
                )
            )

        # 6. Professional Summary
        summary_findings = findings_by_cat.get("professional_summary", [])
        if summary_findings or not any(r.category == "professional_summary" for r in recommendations):
            recommendations.append(
                RecommendationItemAI(
                    title="Craft a Targeted Professional Summary",
                    category="professional_summary",
                    explanation="A 2-3 sentence executive hook highlighting years of experience, core technical specialties, and major career accomplishments.",
                    reason="Recruiters scan the top third of the resume first; a strong summary immediately positions your candidacy.",
                    evidence="Summary section check",
                    suggested_action="Write: '[Role Title] with [X] years experience building [specialty], proven track record of [key metric accomplishment] using [core tech stack].'",
                    priority="High",
                    estimated_effort="Easy",
                    related_feature="Feature #21: Resume Quality Score",
                )
            )

        # 7. Project Descriptions
        proj_findings = findings_by_cat.get("project_descriptions", [])
        if proj_findings or not any(r.category == "project_descriptions" for r in recommendations):
            recommendations.append(
                RecommendationItemAI(
                    title="Highlight Architecture and Live Links in Project Descriptions",
                    category="project_descriptions",
                    explanation="Provide direct GitHub/live deployment links, specify architecture choices, and detail the problem solved.",
                    reason="Engineers want to see code quality, system design thinking, and tangible evidence of working software.",
                    evidence="Project descriptions section",
                    suggested_action="For each project, include: 1 sentence problem/solution, tech stack tags, GitHub link, and 2 bullets detailing technical challenges overcome.",
                    priority="High",
                    estimated_effort="Medium",
                    related_feature="Feature #26: Achievement Analysis",
                )
            )

        # 8. Work and Internship Experience
        work_findings = findings_by_cat.get("work_experience", [])
        if work_findings or not any(r.category == "work_experience" for r in recommendations):
            recommendations.append(
                RecommendationItemAI(
                    title="Strengthen Work Experience with Active Voice and Results",
                    category="work_experience",
                    explanation="Ensure every bullet point starts with a strong action verb (e.g. 'Architected', 'Reduced', 'Spearheaded') rather than 'Responsible for'.",
                    reason="Action verbs project leadership and initiative, making your personal contribution distinct from general team duties.",
                    evidence="Work experience section bullets",
                    suggested_action="Audit bullet points to remove 'Worked on' and 'Helped with', replacing them with precise verbs describing your exact impact.",
                    priority="Medium",
                    estimated_effort="Medium",
                    related_feature="Feature #23: Weakness Analysis",
                )
            )

        # 9. Resume Completeness
        completeness_findings = findings_by_cat.get("resume_completeness", [])
        if completeness_findings:
            item = completeness_findings[0]
            recommendations.append(
                RecommendationItemAI(
                    title=f"Complete Missing Section: {item.get('title', 'Add Missing Information')}",
                    category="resume_completeness",
                    explanation=item.get("explanation", "Ensure all core resume sections are populated with verifiable details."),
                    reason="Missing key sections like location, graduation date, or clear dates creates uncertainty for background checks and ATS screening.",
                    evidence=item.get("evidence", "Resume section inspection"),
                    suggested_action=item.get("suggested_action", "Fill in missing information with accurate, verified facts."),
                    priority="Critical" if "contact" in item.get("title", "").lower() else "Medium",
                    estimated_effort="Easy",
                    related_feature="Feature #21: Resume Quality Score",
                )
            )
        else:
            recommendations.append(
                RecommendationItemAI(
                    title="Verify Complete Contact Information and Section Hygiene",
                    category="resume_completeness",
                    explanation="Confirm phone number, professional email, LinkedIn profile, and GitHub/portfolio URL are present and active.",
                    reason="Recruiters require frictionless contact avenues; missing contact channels can lead to skipped candidates.",
                    evidence="Header contact information check",
                    suggested_action="Include verified email, phone, city/state, LinkedIn URL, and portfolio link at top of resume.",
                    priority="Medium",
                    estimated_effort="Easy",
                    related_feature="Feature #21: Resume Quality Score",
                )
            )

        coverage_pct = coverage_summary.get("coverage_percentage", 100.0)
        overall_summary = (
            f"Synthesized comprehensive improvement roadmap across 8 key resume dimensions. "
            f"Coverage based on {len(coverage_summary.get('available_features', []))}/6 prior analyses ({coverage_pct:.0f}%). "
            f"Prioritizing high-impact ATS fixes, achievement quantification, and skills structure will significantly elevate recruiter callback rates."
        )

        return ResumeRecommendationsAIOutput(
            overall_summary=overall_summary,
            recommendations=recommendations,
        )

    async def generate_recommendations(
        self,
        resume_overview: str,
        combined_findings: Dict[str, Any],
        coverage_summary: Dict[str, Any],
    ) -> ResumeRecommendationsAIOutput:
        """
        Invokes LangChain ChatOllama structured output to generate personalized recommendations.
        Seamlessly falls back to heuristic generation if Ollama is unreachable.
        """
        try:
            llm = self._get_llm()
            structured_llm = llm.with_structured_output(ResumeRecommendationsAIOutput)
            chain = self.prompt | structured_llm

            logger.info("Invoking ChatOllama for resume recommendations with model %s at %s", self.model, self.base_url)
            start_time = time.time()

            result = await chain.ainvoke({
                "resume_overview": resume_overview[:2000],
                "combined_findings": json.dumps(combined_findings, indent=2)[:4000],
                "coverage_status": json.dumps(coverage_summary, indent=2),
            })
            duration = time.time() - start_time
            logger.info("ChatOllama recommendation generation completed in %.2f seconds", duration)

            if isinstance(result, ResumeRecommendationsAIOutput) and result.recommendations:
                return result
            elif isinstance(result, dict) and "recommendations" in result:
                return ResumeRecommendationsAIOutput(**result)
            else:
                raise AIOutputValidationError("LLM response did not contain valid recommendations.")

        except OllamaUnavailableError as conn_err:
            logger.warning("Ollama unavailable for recommendations, using heuristic fallback: %s", conn_err)
            return self.generate_heuristic_recommendations(combined_findings, coverage_summary)

        except Exception as exc:
            err_str = str(exc).lower()
            if any(term in err_str for term in ["connect", "refused", "timeout", "unavailable", "11434"]):
                logger.warning("Ollama connection error (%s), using heuristic fallback", exc)
                return self.generate_heuristic_recommendations(combined_findings, coverage_summary)
            logger.error("LLM recommendation generation error: %s, using fallback", exc)
            return self.generate_heuristic_recommendations(combined_findings, coverage_summary)
