"""
Resume Analytics Dashboard Aggregation Service
Phase 5 | Feature 28: Resume Analytics Dashboard
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.resume import Resume
from app.models.quality_score import ResumeQualityScore
from app.models.strength_analysis import ResumeStrengthAnalysis
from app.models.weakness_analysis import ResumeWeaknessAnalysis
from app.models.ats_analysis import ResumeATSAnalysis
from app.models.grammar_analysis import ResumeGrammarAnalysis
from app.models.achievement_analysis import ResumeAchievementAnalysis
from app.models.recommendations import ResumeRecommendationAnalysis

logger = logging.getLogger(__name__)


class ResumeAnalyticsService:
    """
    Aggregates existing resume analysis results across Phase 4 features
    into a unified visual analytics dashboard payload.
    Never invents scores or calls LLMs unnecessarily.
    """

    def get_dashboard_analytics(
        self,
        resume_id: str,
        db: Session,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieves existing resume analysis results from PostgreSQL,
        aggregates available metrics, and returns structured dashboard data.
        """
        try:
            resume_uuid = uuid.UUID(resume_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resume ID format: {resume_id}",
            )

        # 1. Fetch Resume with all analysis relations in one query
        resume = db.execute(
            select(Resume)
            .options(
                joinedload(Resume.quality_score),
                joinedload(Resume.strength_analysis),
                joinedload(Resume.weakness_analysis),
                joinedload(Resume.ats_analysis),
                joinedload(Resume.grammar_analysis),
                joinedload(Resume.achievement_analysis),
                joinedload(Resume.recommendation_analysis),
            )
            .where(Resume.id == resume_uuid)
        ).unique().scalar_one_or_none()

        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found.",
            )

        # 2. Query available resumes for the user to support resume switcher dropdown
        available_resumes_list: List[Dict[str, Any]] = []
        user_uuid = resume.user_id
        if user_uuid:
            sibling_resumes = db.execute(
                select(Resume)
                .where(Resume.user_id == user_uuid)
                .order_by(Resume.created_at.desc())
            ).scalars().all()
            for r in sibling_resumes:
                available_resumes_list.append({
                    "id": str(r.id),
                    "filename": r.original_filename,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "is_active": (r.id == resume_uuid),
                })
        else:
            # Standalone or anonymous session
            available_resumes_list.append({
                "id": str(resume.id),
                "filename": resume.original_filename,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "is_active": True,
            })

        # 3. Extract loaded analyses
        quality: Optional[ResumeQualityScore] = resume.quality_score
        strength: Optional[ResumeStrengthAnalysis] = resume.strength_analysis
        weakness: Optional[ResumeWeaknessAnalysis] = resume.weakness_analysis
        ats: Optional[ResumeATSAnalysis] = resume.ats_analysis
        grammar: Optional[ResumeGrammarAnalysis] = resume.grammar_analysis
        achievement: Optional[ResumeAchievementAnalysis] = resume.achievement_analysis
        recommendations: Optional[ResumeRecommendationAnalysis] = resume.recommendation_analysis

        # 4. Determine Feature Coverage & Last Analyzed Date
        feature_checks = [
            ("Feature #21: Resume Quality Score", quality),
            ("Feature #22: Strength Analysis", strength),
            ("Feature #23: Weakness Analysis", weakness),
            ("Feature #24: ATS Compatibility Analysis", ats),
            ("Feature #25: Grammar & Clarity Analysis", grammar),
            ("Feature #26: Achievement Analysis", achievement),
        ]

        available_features: List[str] = []
        missing_features: List[str] = []
        all_timestamps: List[datetime] = []

        for name, obj in feature_checks:
            if obj is not None:
                available_features.append(name)
                if hasattr(obj, "updated_at") and obj.updated_at:
                    all_timestamps.append(obj.updated_at)
                elif hasattr(obj, "created_at") and obj.created_at:
                    all_timestamps.append(obj.created_at)
            else:
                missing_features.append(name)

        coverage_count = len(available_features)
        total_features = len(feature_checks)

        if coverage_count == total_features:
            analysis_status = "COMPLETE"
        elif coverage_count > 0:
            analysis_status = "PARTIAL"
        else:
            analysis_status = "NOT_ANALYZED"

        last_analyzed_date = (
            max(all_timestamps).isoformat()
            if all_timestamps
            else (resume.updated_at.isoformat() if resume.updated_at else resume.created_at.isoformat())
        )

        resume_header = {
            "resume_id": str(resume.id),
            "filename": resume.original_filename,
            "file_type": resume.file_type.upper(),
            "file_size": resume.file_size,
            "last_analyzed_date": last_analyzed_date,
            "analysis_status": analysis_status,
            "coverage_count": coverage_count,
            "total_features": total_features,
            "available_features": available_features,
            "missing_features": missing_features,
            "available_resumes": available_resumes_list,
        }

        # 5. Build Analytics Summary Cards (Only genuine existing data)
        # Card 1: Overall Quality Score (Feature #21)
        if quality:
            quality_card = {
                "score": round(float(quality.overall_score), 1),
                "max_score": 100.0,
                "grade_or_rating": quality.rating_level,
                "available": True,
                "label": "Overall Quality Score",
                "description": f"Comprehensive multi-dimensional score ({quality.rating_level})",
            }
        else:
            quality_card = {
                "score": None,
                "max_score": 100.0,
                "grade_or_rating": "Not Evaluated",
                "available": False,
                "label": "Overall Quality Score",
                "description": "Evaluate resume quality to unlock overall score",
            }

        # Card 2: ATS Compatibility Score (Feature #24 or fallback to quality category)
        if ats:
            ats_card = {
                "score": float(ats.ats_score),
                "max_score": 100.0,
                "grade_or_rating": ats.score_grade,
                "available": True,
                "label": "ATS Compatibility Score",
                "description": f"Parsing & layout compatibility ({ats.score_grade})",
            }
        elif quality and quality.category_scores and "ats_compatibility" in quality.category_scores:
            ats_cat = quality.category_scores["ats_compatibility"]
            ats_score_val = float(ats_cat.get("score_percentage", 0.0))
            ats_card = {
                "score": round(ats_score_val, 1),
                "max_score": 100.0,
                "grade_or_rating": ats_cat.get("rating", "Standard"),
                "available": True,
                "label": "ATS Compatibility Score",
                "description": "Derived from Quality Score ATS section",
            }
        else:
            ats_card = {
                "score": None,
                "max_score": 100.0,
                "grade_or_rating": "Not Evaluated",
                "available": False,
                "label": "ATS Compatibility Score",
                "description": "Run ATS analysis to detect parsing risks and keywords",
            }

        # Card 3: Readability Score (Feature #25 or quality clarity)
        if grammar:
            readability_val = None
            if grammar.readability_metrics and "readability_score" in grammar.readability_metrics:
                readability_val = float(grammar.readability_metrics["readability_score"])
            else:
                readability_val = float(grammar.writing_score)

            readability_card = {
                "score": round(readability_val, 1),
                "max_score": 100.0,
                "grade_or_rating": grammar.writing_grade,
                "available": True,
                "label": "Readability Score",
                "description": f"Clarity, grammar & tone quality ({grammar.writing_grade})",
            }
        elif quality and quality.category_scores and "clarity_and_conciseness" in quality.category_scores:
            clarity_cat = quality.category_scores["clarity_and_conciseness"]
            clarity_score_val = float(clarity_cat.get("score_percentage", 0.0))
            readability_card = {
                "score": round(clarity_score_val, 1),
                "max_score": 100.0,
                "grade_or_rating": clarity_cat.get("rating", "Standard"),
                "available": True,
                "label": "Readability Score",
                "description": "Derived from Quality Score Clarity section",
            }
        else:
            readability_card = {
                "score": None,
                "max_score": 100.0,
                "grade_or_rating": "Not Evaluated",
                "available": False,
                "label": "Readability Score",
                "description": "Run Grammar & Clarity analysis to measure reading ease",
            }

        # Card 4: Content Completeness Score (Feature #21 or ATS section completeness)
        completeness_val: Optional[float] = None
        completeness_rating: Optional[str] = None
        completeness_available = False

        if quality and quality.category_scores and "content_completeness" in quality.category_scores:
            comp_cat = quality.category_scores["content_completeness"]
            completeness_val = round(float(comp_cat.get("score_percentage", 0.0)), 1)
            completeness_rating = comp_cat.get("rating", "Standard")
            completeness_available = True
        elif ats and ats.detected_sections:
            total_sec = len(ats.detected_sections)
            detected_sec = sum(1 for s in ats.detected_sections if s.get("detected", False))
            completeness_val = round((detected_sec / total_sec * 100.0), 1) if total_sec > 0 else 0.0
            completeness_rating = "Complete" if completeness_val >= 90 else ("Moderate" if completeness_val >= 60 else "Incomplete")
            completeness_available = True

        content_completeness_card = {
            "score": completeness_val,
            "max_score": 100.0,
            "grade_or_rating": completeness_rating or "Not Evaluated",
            "available": completeness_available,
            "label": "Content Completeness Score",
            "description": f"Standard section coverage & depth ({completeness_rating or 'Pending'})",
        }

        summary_cards = {
            "quality_score": quality_card,
            "ats_compatibility": ats_card,
            "readability": readability_card,
            "content_completeness": content_completeness_card,
        }

        # 6. Visual Analytics
        # A. Quality Category Breakdown (from Feature #21)
        quality_category_bars: List[Dict[str, Any]] = []
        if quality and quality.category_scores:
            for cat_k, cat_data in quality.category_scores.items():
                if isinstance(cat_data, dict):
                    quality_category_bars.append({
                        "category_key": cat_k,
                        "category_name": cat_data.get("category_name", cat_k.replace("_", " ").title()),
                        "score": round(float(cat_data.get("score", 0.0)), 1),
                        "max_score": round(float(cat_data.get("max_score", 10.0)), 1),
                        "score_percentage": round(float(cat_data.get("score_percentage", 0.0)), 1),
                        "rating": cat_data.get("rating", "Average"),
                        "weight_percentage": round(float(cat_data.get("weight_percentage", 12.5)), 1),
                    })

        # B. Available Score Distribution (cross-feature distribution)
        score_distribution: List[Dict[str, Any]] = [
            {
                "metric": "Overall Quality",
                "score": round(float(quality.overall_score), 1) if quality else None,
                "max_score": 100.0,
                "percentage": round(float(quality.overall_score), 1) if quality else None,
                "status": quality.rating_level if quality else "Not Evaluated",
                "available": quality is not None,
            },
            {
                "metric": "ATS Compatibility",
                "score": float(ats.ats_score) if ats else (ats_card["score"] if ats_card["available"] else None),
                "max_score": 100.0,
                "percentage": float(ats.ats_score) if ats else (ats_card["score"] if ats_card["available"] else None),
                "status": ats.score_grade if ats else (ats_card["grade_or_rating"] if ats_card["available"] else "Not Evaluated"),
                "available": ats is not None or ats_card["available"],
            },
            {
                "metric": "Grammar & Tone",
                "score": float(grammar.writing_score) if grammar else (readability_card["score"] if readability_card["available"] else None),
                "max_score": 100.0,
                "percentage": float(grammar.writing_score) if grammar else (readability_card["score"] if readability_card["available"] else None),
                "status": grammar.writing_grade if grammar else (readability_card["grade_or_rating"] if readability_card["available"] else "Not Evaluated"),
                "available": grammar is not None or readability_card["available"],
            },
            {
                "metric": "Achievements Impact",
                "score": float(achievement.achievement_score) if achievement else None,
                "max_score": 100.0,
                "percentage": float(achievement.achievement_score) if achievement else None,
                "status": achievement.score_grade if achievement else "Not Evaluated",
                "available": achievement is not None,
            },
            {
                "metric": "Recommendations Completed",
                "score": float(recommendations.completion_percentage) if recommendations else None,
                "max_score": 100.0,
                "percentage": float(recommendations.completion_percentage) if recommendations else None,
                "status": f"{recommendations.completed_count}/{recommendations.total_recommendations_count} items" if recommendations else "Not Evaluated",
                "available": recommendations is not None,
            },
        ]

        # C. Strengths and Weaknesses Overview
        strengths_list = getattr(strength, "strengths", []) or [] if strength else []
        weaknesses_list = getattr(weakness, "weaknesses", []) or [] if weakness else []
        missing_info_list = getattr(weakness, "missing_information", []) or [] if weakness else []

        strengths_by_cat: Dict[str, int] = {}
        for s in strengths_list:
            c = s.get("category", "General")
            strengths_by_cat[c] = strengths_by_cat.get(c, 0) + 1

        weaknesses_by_cat: Dict[str, int] = {}
        weaknesses_by_prio: Dict[str, int] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for w in weaknesses_list:
            c = w.get("category", "General")
            weaknesses_by_cat[c] = weaknesses_by_cat.get(c, 0) + 1
            p = (w.get("priority") or "Medium").capitalize()
            if p in weaknesses_by_prio:
                weaknesses_by_prio[p] += 1
            else:
                weaknesses_by_prio["Medium"] += 1

        strengths_vs_weaknesses = {
            "strengths_count": len(strengths_list),
            "weaknesses_count": len(weaknesses_list),
            "missing_info_count": len(missing_info_list),
            "strengths_by_category": strengths_by_cat,
            "weaknesses_by_category": weaknesses_by_cat,
            "weaknesses_by_priority": weaknesses_by_prio,
        }

        visual_analytics = {
            "quality_category_breakdown": quality_category_bars,
            "score_distribution": score_distribution,
            "strengths_vs_weaknesses": strengths_vs_weaknesses,
        }

        # 7. Resume Insights
        key_strengths: List[Dict[str, Any]] = []
        for s in strengths_list[:5]:
            key_strengths.append({
                "title": s.get("title", "Demonstrated Strength"),
                "category": s.get("category", "Core Competency"),
                "explanation": s.get("explanation", ""),
                "evidence": s.get("evidence", ""),
                "professional_value": s.get("professional_value", None),
            })

        important_weaknesses: List[Dict[str, Any]] = []
        for w in weaknesses_list[:5]:
            important_weaknesses.append({
                "title": w.get("title", "Resume Content Gap"),
                "category": w.get("category", "General"),
                "explanation": w.get("explanation", ""),
                "suggested_improvement": w.get("suggested_improvement", ""),
                "priority": (w.get("priority") or "Medium").capitalize(),
            })

        main_improvement_areas: List[Dict[str, Any]] = []
        if recommendations and recommendations.recommendations:
            # Pick top pending or critical recommendations
            for r in recommendations.recommendations[:5]:
                main_improvement_areas.append({
                    "title": r.get("title", "Improvement Action"),
                    "category": r.get("category_name", r.get("category", "General")),
                    "suggested_action": r.get("suggested_action", ""),
                    "priority": r.get("priority", "Medium"),
                    "estimated_effort": r.get("estimated_effort", "Medium"),
                })
        elif quality and quality.improvement_suggestions:
            for idx, sug in enumerate(quality.improvement_suggestions[:5]):
                main_improvement_areas.append({
                    "title": f"Quality Suggestion #{idx+1}",
                    "category": "Overall Quality",
                    "suggested_action": sug,
                    "priority": "High" if idx < 2 else "Medium",
                    "estimated_effort": "Easy",
                })

        # Feature Summaries
        feature_summaries: Dict[str, Any] = {}
        if quality:
            feature_summaries["quality"] = {
                "overall_score": quality.overall_score,
                "rating_level": quality.rating_level,
                "rubric_version": quality.rubric_version,
                "strengths_count": len(quality.strengths or []),
                "missing_count": len(quality.missing_information or []),
            }
        if ats:
            feature_summaries["ats"] = {
                "ats_score": ats.ats_score,
                "score_grade": ats.score_grade,
                "issues_count": len(ats.verified_issues or []),
                "formatting_risks_count": len(ats.formatting_risks or []),
                "detected_sections_count": sum(1 for s in (ats.detected_sections or []) if s.get("detected")),
            }
        if grammar:
            feature_summaries["grammar"] = {
                "writing_score": grammar.writing_score,
                "writing_grade": grammar.writing_grade,
                "issues_count": len(grammar.issues or []),
                "overall_assessment": grammar.overall_assessment,
            }
        if achievement:
            feature_summaries["achievement"] = {
                "achievement_score": achievement.achievement_score,
                "score_grade": achievement.score_grade,
                "total_count": achievement.total_achievements_count,
                "quantified_count": achievement.quantified_count,
                "quantification_rate": achievement.quantification_rate,
            }
        if recommendations:
            feature_summaries["recommendations"] = {
                "total_count": recommendations.total_recommendations_count,
                "completed_count": recommendations.completed_count,
                "pending_count": recommendations.pending_count,
                "completion_percentage": recommendations.completion_percentage,
                "overall_summary": recommendations.overall_summary,
            }

        resume_insights = {
            "key_strengths": key_strengths,
            "important_weaknesses": important_weaknesses,
            "main_improvement_areas": main_improvement_areas,
            "feature_summaries": feature_summaries,
        }

        has_any_analysis = bool(quality or strength or weakness or ats or grammar or achievement or recommendations)

        return {
            "resume_id": str(resume.id),
            "resume_header": resume_header,
            "summary_cards": summary_cards,
            "visual_analytics": visual_analytics,
            "resume_insights": resume_insights,
            "generated_at": datetime.utcnow().isoformat(),
            "has_any_analysis": has_any_analysis,
        }


analytics_service = ResumeAnalyticsService()
