"""
LangGraph Multi-Step Workflow for Resume Improvement Recommendations
Phase 4 | Feature 27: Resume Improvement Recommendations

7-Stage Pipeline:
1. Load previous analysis results (Features #21-#26)
2. Validate available analysis data and coverage
3. Combine findings across 8 target categories
4. Generate recommendations (AI + Heuristic fallback)
5. Remove duplicates and prioritize by importance
6. Validate final output with Pydantic
7. Save recommendations to database
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, TypedDict
from sqlalchemy.orm import Session
from sqlalchemy import select

from langgraph.graph import StateGraph, START, END
from app.core.config import settings

from app.models.resume import Resume
from app.models.quality_score import ResumeQualityScore
from app.models.strength_analysis import ResumeStrengthAnalysis
from app.models.weakness_analysis import ResumeWeaknessAnalysis
from app.models.ats_analysis import ResumeATSAnalysis
from app.models.grammar_analysis import ResumeGrammarAnalysis
from app.models.achievement_analysis import ResumeAchievementAnalysis
from app.models.recommendations import ResumeRecommendationAnalysis

from app.schemas.recommendations import (
    RecommendationItem,
    RecommendationItemAI,
    ResumeRecommendationsAIOutput,
    RecommendationAnalysisData,
)
from app.services.recommendations.categories import (
    RECOMMENDATION_CATEGORIES,
    normalize_category_key,
    get_category_display_name,
)
from app.services.recommendations.ai_generator import RecommendationAIGenerator

logger = logging.getLogger(__name__)


class RecommendationWorkflowState(TypedDict, total=False):
    """LangGraph execution state across all 7 stages."""
    # Inputs
    resume_id: str
    user_id: Optional[str]
    db: Session
    force_recalculate: bool

    # Stage 1: Loaded analyses
    resume_obj: Optional[Dict[str, Any]]
    loaded_analyses: Dict[str, Any]

    # Stage 2: Validation
    available_features: List[str]
    missing_features: List[str]
    coverage_percentage: float
    coverage_summary: Dict[str, Any]
    is_insufficient: bool
    validation_status: str

    # Stage 3: Combined findings
    combined_findings: Dict[str, Any]

    # Stage 4: Raw generated recommendations
    raw_output: Optional[ResumeRecommendationsAIOutput]
    overall_summary: str

    # Stage 5: Deduplicated & prioritized
    processed_recommendations: List[Dict[str, Any]]
    priority_breakdown: Dict[str, int]
    category_breakdown: Dict[str, Any]

    # Stage 6: Validated recommendations
    validated_recommendations: List[Dict[str, Any]]

    # Stage 7: Final persisted result
    final_result: Optional[Dict[str, Any]]
    error: Optional[str]


# ---------------------------------------------------------------------------
# STAGE 1: Load previous analysis results
# ---------------------------------------------------------------------------
async def load_analyses_node(state: RecommendationWorkflowState) -> Dict[str, Any]:
    """Loads existing results from Features #21 to #26 without recalculating them."""
    resume_id_str = state["resume_id"]
    db: Session = state["db"]

    try:
        resume_uuid = uuid.UUID(resume_id_str)
    except ValueError:
        return {"loaded_analyses": {}, "resume_obj": None, "error": f"Invalid resume UUID: {resume_id_str}"}

    resume = db.execute(select(Resume).where(Resume.id == resume_uuid)).scalar_one_or_none()
    resume_obj = None
    if resume:
        resume_obj = {
            "id": str(resume.id),
            "filename": getattr(resume, "filename", getattr(resume, "original_filename", "Resume")),
            "cleaned_text": getattr(resume, "cleaned_text", "") or "",
            "user_id": str(resume.user_id) if getattr(resume, "user_id", None) else None,
        }

    # Query all 6 analyses
    quality = db.execute(select(ResumeQualityScore).where(ResumeQualityScore.resume_id == resume_uuid)).scalar_one_or_none()
    strength = db.execute(select(ResumeStrengthAnalysis).where(ResumeStrengthAnalysis.resume_id == resume_uuid)).scalar_one_or_none()
    weakness = db.execute(select(ResumeWeaknessAnalysis).where(ResumeWeaknessAnalysis.resume_id == resume_uuid)).scalar_one_or_none()
    ats = db.execute(select(ResumeATSAnalysis).where(ResumeATSAnalysis.resume_id == resume_uuid)).scalar_one_or_none()
    grammar = db.execute(select(ResumeGrammarAnalysis).where(ResumeGrammarAnalysis.resume_id == resume_uuid)).scalar_one_or_none()
    achievement = db.execute(select(ResumeAchievementAnalysis).where(ResumeAchievementAnalysis.resume_id == resume_uuid)).scalar_one_or_none()

    loaded = {
        "quality_score": quality,
        "strength_analysis": strength,
        "weakness_analysis": weakness,
        "ats_analysis": ats,
        "grammar_analysis": grammar,
        "achievement_analysis": achievement,
    }

    logger.info("Loaded previous analyses for resume %s: %s", resume_id_str, {k: v is not None for k, v in loaded.items()})
    return {"loaded_analyses": loaded, "resume_obj": resume_obj}


# ---------------------------------------------------------------------------
# STAGE 2: Validate available analysis data
# ---------------------------------------------------------------------------
async def validate_analyses_node(state: RecommendationWorkflowState) -> Dict[str, Any]:
    """Evaluates coverage of previous analyses and configures graceful handling."""
    loaded = state.get("loaded_analyses", {})
    resume_obj = state.get("resume_obj")

    available: List[str] = []
    missing: List[str] = []

    feature_names = {
        "quality_score": "Feature #21: Resume Quality Score",
        "strength_analysis": "Feature #22: Strength Analysis",
        "weakness_analysis": "Feature #23: Weakness Analysis",
        "ats_analysis": "Feature #24: ATS Compatibility Analysis",
        "grammar_analysis": "Feature #25: Grammar & Clarity Analysis",
        "achievement_analysis": "Feature #26: Achievement Analysis",
    }

    for key, name in feature_names.items():
        if loaded.get(key) is not None:
            available.append(name)
        else:
            missing.append(name)

    total_count = len(feature_names)
    available_count = len(available)
    coverage_pct = round((available_count / total_count) * 100.0, 1)
    is_full = available_count == total_count

    if is_full:
        notes = "Complete coverage: All 6 prior analyses are integrated into recommendations."
    elif available_count > 0:
        notes = (
            f"Partial analysis coverage: {available_count}/6 prior analyses available ({coverage_pct}%). "
            f"Missing: {', '.join([k.split(':')[1].strip() for k in missing])}. "
            f"Recommendations generated using all available intelligence."
        )
    else:
        notes = "No prior analyses available. Baseline recommendations will be generated from resume structure."

    coverage_summary = {
        "total_features": total_count,
        "available_features": available,
        "missing_features": missing,
        "coverage_percentage": coverage_pct,
        "is_full_coverage": is_full,
        "coverage_notes": notes,
    }

    # If resume object doesn't exist, insufficient data
    is_insufficient = resume_obj is None

    return {
        "available_features": available,
        "missing_features": missing,
        "coverage_percentage": coverage_pct,
        "coverage_summary": coverage_summary,
        "is_insufficient": is_insufficient,
        "validation_status": "insufficient" if is_insufficient else ("full" if is_full else "partial"),
    }


# ---------------------------------------------------------------------------
# STAGE 3: Combine findings across 8 categories
# ---------------------------------------------------------------------------
async def combine_findings_node(state: RecommendationWorkflowState) -> Dict[str, Any]:
    """Synthesizes insights from loaded analyses into 8 target recommendation categories."""
    loaded = state.get("loaded_analyses", {})
    by_category: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in RECOMMENDATION_CATEGORIES.keys()}

    # 1. From ATS Analysis (Feature #24) -> ats_compatibility, resume_completeness
    ats: Optional[ResumeATSAnalysis] = loaded.get("ats_analysis")
    if ats:
        for issue in getattr(ats, "verified_issues", []) or []:
            by_category["ats_compatibility"].append({
                "source": "Feature #24: ATS Compatibility",
                "title": issue.get("title", "ATS Formatting Issue"),
                "severity": issue.get("severity", "medium"),
                "explanation": issue.get("explanation", ""),
                "evidence": issue.get("evidence", ""),
                "suggested_fix": issue.get("suggested_fix", ""),
            })
        for risk in getattr(ats, "formatting_risks", []) or []:
            by_category["ats_compatibility"].append({
                "source": "Feature #24: ATS Compatibility",
                "title": risk.get("title", "Layout Risk"),
                "severity": risk.get("severity", "medium"),
                "explanation": risk.get("explanation", ""),
                "evidence": risk.get("evidence", ""),
                "suggested_fix": risk.get("suggested_fix", ""),
            })
        for sec in getattr(ats, "detected_sections", []) or []:
            if not sec.get("detected", False):
                by_category["resume_completeness"].append({
                    "source": "Feature #24: ATS Compatibility",
                    "title": f"Missing Standard Section: {sec.get('section_name', 'Section')}",
                    "explanation": f"The '{sec.get('section_name')}' heading was not detected by the ATS parser.",
                    "evidence": "Section detection audit",
                    "suggested_action": f"Add a clearly labeled '{sec.get('section_name')}' section to your resume.",
                })

    # 2. From Achievement Analysis (Feature #26) -> achievements_impact, project_descriptions, work_experience
    ach: Optional[ResumeAchievementAnalysis] = loaded.get("achievement_analysis")
    if ach:
        achievements = getattr(ach, "achievements", []) or []
        for item in achievements:
            if not item.get("is_quantified", True):
                by_category["achievements_impact"].append({
                    "source": "Feature #26: Achievement Analysis",
                    "title": f"Quantify Metric in {item.get('title', 'Accomplishment')}",
                    "statement": item.get("original_statement", ""),
                    "unquantified": True,
                    "evidence": item.get("evidence", item.get("original_statement", "")),
                    "suggested_statement": item.get("suggested_statement", ""),
                })
            cat_key = item.get("category", "")
            if cat_key in ["projects", "academic_projects"]:
                by_category["project_descriptions"].append({
                    "source": "Feature #26: Achievement Analysis",
                    "title": item.get("title", "Project Achievement"),
                    "statement": item.get("original_statement", ""),
                    "evidence": item.get("evidence", ""),
                    "suggested_statement": item.get("suggested_statement", ""),
                })
            elif cat_key == "experience":
                by_category["work_experience"].append({
                    "source": "Feature #26: Achievement Analysis",
                    "title": item.get("title", "Work Experience Achievement"),
                    "statement": item.get("original_statement", ""),
                    "evidence": item.get("evidence", ""),
                    "suggested_statement": item.get("suggested_statement", ""),
                })

    # 3. From Weakness Analysis (Feature #23) -> all relevant categories
    weak: Optional[ResumeWeaknessAnalysis] = loaded.get("weakness_analysis")
    if weak:
        weaknesses = getattr(weak, "weaknesses", []) or []
        for item in weaknesses:
            raw_cat = item.get("category", "")
            norm_cat = normalize_category_key(raw_cat)
            by_category[norm_cat].append({
                "source": "Feature #23: Weakness Analysis",
                "title": item.get("title", "Identified Weakness"),
                "explanation": item.get("explanation", ""),
                "evidence": item.get("evidence", ""),
                "why_it_matters": item.get("why_it_matters", ""),
                "suggested_improvement": item.get("suggested_improvement", ""),
                "priority": item.get("priority", "Medium"),
            })
        for missing in getattr(weak, "missing_information", []) or []:
            by_category["resume_completeness"].append({
                "source": "Feature #23: Weakness Analysis",
                "title": f"Missing Information: {missing.get('item', 'Detail')}",
                "explanation": f"Section '{missing.get('section', 'General')}' lacks {missing.get('item', 'expected details')}.",
                "evidence": f"Section: {missing.get('section', 'N/A')}",
                "suggested_action": f"Provide concrete details for {missing.get('item', 'this section')}.",
            })

    # 4. From Grammar Analysis (Feature #25) -> grammar_clarity
    gram: Optional[ResumeGrammarAnalysis] = loaded.get("grammar_analysis")
    if gram:
        issues = getattr(gram, "issues", []) or []
        for iss in issues[:5]:
            by_category["grammar_clarity"].append({
                "source": "Feature #25: Grammar & Clarity",
                "title": f"Fix {iss.get('category_name', 'Grammar')} in {iss.get('section', 'Resume')}",
                "original_text": iss.get("original_text", ""),
                "suggested_text": iss.get("suggested_text", ""),
                "explanation": iss.get("explanation", ""),
                "severity": iss.get("severity", "medium"),
            })

    # 5. From Strength Analysis (Feature #22) -> technical_skills, work_experience
    stren: Optional[ResumeStrengthAnalysis] = loaded.get("strength_analysis")
    if stren:
        for s in (getattr(stren, "strengths", []) or [])[:3]:
            by_category["technical_skills"].append({
                "source": "Feature #22: Strength Analysis",
                "title": f"Emphasize Demonstrated Strength: {s.get('title', 'Core Competency')}",
                "evidence": s.get("evidence", ""),
                "explanation": s.get("explanation", ""),
            })

    # 6. From Quality Score (Feature #21) -> general & professional_summary
    qual: Optional[ResumeQualityScore] = loaded.get("quality_score")
    if qual:
        for sug in getattr(qual, "improvement_suggestions", []) or []:
            by_category["resume_completeness"].append({
                "source": "Feature #21: Resume Quality Score",
                "title": "Quality Score Improvement Suggestion",
                "explanation": sug,
                "evidence": "Overall Quality Evaluation",
                "suggested_action": sug,
            })
        for missing in getattr(qual, "missing_information", []) or []:
            by_category["resume_completeness"].append({
                "source": "Feature #21: Resume Quality Score",
                "title": f"Missing: {missing}",
                "explanation": f"Quality score audit flagged '{missing}' as absent or incomplete.",
                "evidence": "Quality Score Section Checklist",
                "suggested_action": f"Add {missing} to improve resume completeness.",
            })

    return {
        "combined_findings": {
            "by_category": by_category,
            "counts": {cat: len(items) for cat, items in by_category.items()},
        }
    }


# ---------------------------------------------------------------------------
# STAGE 4: Generate recommendations (AI + Heuristic fallback)
# ---------------------------------------------------------------------------
async def generate_recommendations_node(state: RecommendationWorkflowState) -> Dict[str, Any]:
    """Generates personalized recommendations using LangChain + ChatOllama (with fallback)."""
    generator = RecommendationAIGenerator()
    combined = state.get("combined_findings", {})
    coverage = state.get("coverage_summary", {})
    resume_obj = state.get("resume_obj", {}) or {}

    resume_overview = (
        f"Resume File: {resume_obj.get('filename', 'Resume')}\n"
        f"Text Sample: {resume_obj.get('cleaned_text', '')[:1000]}"
    )

    output = await generator.generate_recommendations(
        resume_overview=resume_overview,
        combined_findings=combined,
        coverage_summary=coverage,
    )

    return {
        "raw_output": output,
        "overall_summary": output.overall_summary,
    }


# ---------------------------------------------------------------------------
# STAGE 5: Remove duplicates and prioritize
# ---------------------------------------------------------------------------
async def deduplicate_and_prioritize_node(state: RecommendationWorkflowState) -> Dict[str, Any]:
    """Deduplicates, assigns stable IDs, and prioritizes recommendations."""
    raw_output: Optional[ResumeRecommendationsAIOutput] = state.get("raw_output")
    raw_items = raw_output.recommendations if raw_output else []

    seen_signatures = set()
    deduped: List[Dict[str, Any]] = []

    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    category_counter: Dict[str, int] = {cat: 0 for cat in RECOMMENDATION_CATEGORIES.keys()}

    for item in raw_items:
        cat_key = normalize_category_key(item.category)
        clean_title = item.title.strip()
        sig = f"{cat_key}::{clean_title.lower()}"

        if sig in seen_signatures:
            continue
        seen_signatures.add(sig)

        category_counter[cat_key] = category_counter.get(cat_key, 0) + 1
        cat_prefix = cat_key[:4].upper()
        rec_id = f"REC-{cat_prefix}-{category_counter[cat_key]:02d}"

        # Standardize priority
        prio = item.priority.capitalize() if item.priority else "Medium"
        if prio not in ["Critical", "High", "Medium", "Low"]:
            prio = "Medium"

        effort = item.estimated_effort.capitalize() if item.estimated_effort else "Medium"
        if effort not in ["Easy", "Medium", "Hard"]:
            effort = "Medium"

        deduped.append({
            "id": rec_id,
            "title": clean_title,
            "category": cat_key,
            "category_name": get_category_display_name(cat_key),
            "explanation": item.explanation.strip(),
            "reason": item.reason.strip(),
            "evidence": item.evidence.strip() if item.evidence else "Resume analysis audit",
            "suggested_action": item.suggested_action.strip(),
            "priority": prio,
            "estimated_effort": effort,
            "related_feature": item.related_feature or "Feature #21-#26",
            "is_completed": False,
            "completed_at": None,
        })

    # Sort primarily by priority (Critical -> High -> Medium -> Low), secondarily by category
    deduped.sort(key=lambda x: (priority_order.get(x["priority"], 99), x["category"]))

    # Calculate aggregate breakdowns
    priority_breakdown = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    category_breakdown = {}

    for cat_k, meta in RECOMMENDATION_CATEGORIES.items():
        category_breakdown[cat_k] = {
            "key": cat_k,
            "name": meta["name"],
            "total_count": 0,
            "completed_count": 0,
            "pending_count": 0,
        }

    for item in deduped:
        p = item["priority"]
        priority_breakdown[p] = priority_breakdown.get(p, 0) + 1

        c = item["category"]
        if c in category_breakdown:
            category_breakdown[c]["total_count"] += 1
            category_breakdown[c]["pending_count"] += 1

    return {
        "processed_recommendations": deduped,
        "priority_breakdown": priority_breakdown,
        "category_breakdown": category_breakdown,
    }


# ---------------------------------------------------------------------------
# STAGE 6: Validate final output
# ---------------------------------------------------------------------------
async def validate_output_node(state: RecommendationWorkflowState) -> Dict[str, Any]:
    """Validates processed recommendations against the strict Pydantic schema."""
    processed = state.get("processed_recommendations", [])
    validated: List[Dict[str, Any]] = []

    for item in processed:
        try:
            valid_model = RecommendationItem(**item)
            validated.append(valid_model.model_dump())
        except Exception as exc:
            logger.warning("Recommendation item failed Pydantic validation: %s. Item: %s", exc, item)
            # Patch and salvage
            item["priority"] = "Medium"
            item["estimated_effort"] = "Medium"
            valid_model = RecommendationItem(**item)
            validated.append(valid_model.model_dump())

    return {"validated_recommendations": validated}


# ---------------------------------------------------------------------------
# STAGE 7: Save recommendations
# ---------------------------------------------------------------------------
async def save_recommendations_node(state: RecommendationWorkflowState) -> Dict[str, Any]:
    """Persists recommendations into PostgreSQL and constructs API return payload."""
    resume_id_str = state["resume_id"]
    resume_uuid = uuid.UUID(resume_id_str)
    user_id_str = state.get("user_id")
    user_uuid = uuid.UUID(user_id_str) if user_id_str else None
    db: Session = state["db"]

    validated = state.get("validated_recommendations", [])
    overall_summary = state.get("overall_summary", "Comprehensive resume improvement roadmap.")
    priority_breakdown = state.get("priority_breakdown", {"Critical": 0, "High": 0, "Medium": 0, "Low": 0})
    category_breakdown = state.get("category_breakdown", {})
    coverage_summary = state.get("coverage_summary", {})

    # Check for existing record to preserve user completion status if already toggled!
    existing = db.execute(
        select(ResumeRecommendationAnalysis).where(ResumeRecommendationAnalysis.resume_id == resume_uuid)
    ).scalar_one_or_none()

    if existing and not state.get("force_recalculate", False):
        # Preserve user completion states on matching recommendation IDs or titles
        completed_titles = {
            r.get("title"): r.get("completed_at")
            for r in getattr(existing, "recommendations", []) or []
            if r.get("is_completed")
        }
        for item in validated:
            if item["title"] in completed_titles:
                item["is_completed"] = True
                item["completed_at"] = completed_titles[item["title"]]

    total_count = len(validated)
    completed_count = sum(1 for r in validated if r.get("is_completed", False))
    pending_count = total_count - completed_count
    completion_percentage = round((completed_count / total_count * 100.0), 1) if total_count > 0 else 0.0

    # Refresh category breakdown completed counts
    for item in validated:
        cat_key = item["category"]
        if cat_key in category_breakdown and item.get("is_completed"):
            category_breakdown[cat_key]["completed_count"] += 1
            category_breakdown[cat_key]["pending_count"] -= 1

    analysis_metadata = {
        "engine": "LangGraph Recommendation Workflow",
        "stages": [
            "load_analyses",
            "validate_analyses",
            "combine_findings",
            "generate_recommendations",
            "deduplicate_and_prioritize",
            "validate_output",
            "save_recommendations",
        ],
        "generated_at": datetime.utcnow().isoformat(),
        "model": settings.OLLAMA_MODEL,
        "is_full_coverage": coverage_summary.get("is_full_coverage", False),
    }

    if existing:
        existing.overall_summary = overall_summary
        existing.total_recommendations_count = total_count
        existing.completed_count = completed_count
        existing.pending_count = pending_count
        existing.completion_percentage = completion_percentage
        existing.priority_breakdown = priority_breakdown
        existing.category_breakdown = category_breakdown
        existing.coverage_summary = coverage_summary
        existing.recommendations = validated
        existing.analysis_metadata = analysis_metadata
        db_record = existing
    else:
        db_record = ResumeRecommendationAnalysis(
            resume_id=resume_uuid,
            user_id=user_uuid,
            overall_summary=overall_summary,
            total_recommendations_count=total_count,
            completed_count=completed_count,
            pending_count=pending_count,
            completion_percentage=completion_percentage,
            priority_breakdown=priority_breakdown,
            category_breakdown=category_breakdown,
            coverage_summary=coverage_summary,
            recommendations=validated,
            analysis_metadata=analysis_metadata,
        )
        db.add(db_record)

    db.commit()
    db.refresh(db_record)

    result_payload: Dict[str, Any] = {
        "id": str(db_record.id),
        "resume_id": str(db_record.resume_id),
        "user_id": str(db_record.user_id) if db_record.user_id else None,
        "overall_summary": db_record.overall_summary,
        "total_recommendations_count": db_record.total_recommendations_count,
        "completed_count": db_record.completed_count,
        "pending_count": db_record.pending_count,
        "completion_percentage": db_record.completion_percentage,
        "priority_breakdown": db_record.priority_breakdown,
        "category_breakdown": db_record.category_breakdown,
        "coverage_summary": db_record.coverage_summary,
        "recommendations": db_record.recommendations,
        "analysis_metadata": db_record.analysis_metadata,
        "created_at": db_record.created_at,
        "updated_at": db_record.updated_at,
    }

    return {"final_result": result_payload}


# ---------------------------------------------------------------------------
# CONDITIONAL NODE: Handle Insufficient Data
# ---------------------------------------------------------------------------
async def handle_insufficient_data_node(state: RecommendationWorkflowState) -> Dict[str, Any]:
    """Fallback handler when resume does not exist or has zero data."""
    coverage = state.get("coverage_summary", {})
    return {
        "raw_output": None,
        "overall_summary": "Resume record could not be found or has not been processed.",
        "processed_recommendations": [],
        "validated_recommendations": [],
        "priority_breakdown": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
        "category_breakdown": {},
        "error": "Resume not found or lacks parsed data.",
    }


def route_after_validation(state: RecommendationWorkflowState) -> str:
    """Conditional router based on validation status."""
    if state.get("is_insufficient", False):
        return "handle_insufficient_data"
    return "combine_findings"


# ---------------------------------------------------------------------------
# BUILD LANGGRAPH WORKFLOW
# ---------------------------------------------------------------------------
def build_recommendation_workflow() -> Any:
    """Compiles and returns the reusable 7-stage LangGraph StateGraph."""
    graph = StateGraph(RecommendationWorkflowState)

    # 1. Register Nodes
    graph.add_node("load_analyses", load_analyses_node)
    graph.add_node("validate_analyses", validate_analyses_node)
    graph.add_node("combine_findings", combine_findings_node)
    graph.add_node("generate_recommendations", generate_recommendations_node)
    graph.add_node("deduplicate_and_prioritize", deduplicate_and_prioritize_node)
    graph.add_node("validate_output", validate_output_node)
    graph.add_node("save_recommendations", save_recommendations_node)
    graph.add_node("handle_insufficient_data", handle_insufficient_data_node)

    # 2. Sequential & Conditional Edges
    graph.add_edge(START, "load_analyses")
    graph.add_edge("load_analyses", "validate_analyses")

    graph.add_conditional_edges(
        "validate_analyses",
        route_after_validation,
        {
            "combine_findings": "combine_findings",
            "handle_insufficient_data": "handle_insufficient_data",
        },
    )

    graph.add_edge("combine_findings", "generate_recommendations")
    graph.add_edge("generate_recommendations", "deduplicate_and_prioritize")
    graph.add_edge("deduplicate_and_prioritize", "validate_output")
    graph.add_edge("validate_output", "save_recommendations")
    graph.add_edge("handle_insufficient_data", "save_recommendations")
    graph.add_edge("save_recommendations", END)

    return graph.compile()


# Singleton compiled graph instance
recommendation_graph = build_recommendation_workflow()
