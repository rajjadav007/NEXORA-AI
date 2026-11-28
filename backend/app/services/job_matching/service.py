"""
Resume-to-Job Matching Engine Service
Phase 7 | Feature 39: Deterministic, evidence-backed candidate-to-job matching & scoring.
"""

import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.certifications import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.job_requirement_analysis import JobRequirementAnalysis
from app.models.job_skill_classification import JobSkillClassification
from app.models.project import Project
from app.models.resume import Resume
from app.models.skills import ResumeSkill
from app.schemas.job_match import (
    CategoryScoreBreakdown,
    EducationMatchSummary,
    ExperienceMatchSummary,
    JobMatchData,
    JobMatchSummaryCounts,
    RelevantProjectItem,
    RequirementMatchItem,
    ScoreBreakdownSchema,
)
from app.services.skills.dictionary import skill_dictionary
from app.services.skills.formatter import normalize_skill_text

logger = logging.getLogger(__name__)

CALCULATION_VERSION = "1.0.0"

CATEGORY_WEIGHTS: Dict[str, Tuple[str, float]] = {
    "technical_skills": ("Technical Skills", 0.40),
    "relevant_experience": ("Relevant Experience", 0.25),
    "projects": ("Relevant Projects", 0.15),
    "education": ("Education", 0.10),
    "other_requirements": ("Other Requirements", 0.10),
}

_IMPORTANCE_WEIGHT = {
    "Mandatory": 3.0,
    "Preferred": 2.0,
    "Optional": 1.0,
    "Unspecified": 1.0,
}

_DEGREE_LEVEL_RANK = {
    "high_school": 1,
    "secondary": 1,
    "diploma": 2,
    "associate": 2,
    "undergraduate": 3,
    "bachelor": 3,
    "bachelors": 3,
    "b.tech": 3,
    "b.e": 3,
    "b.sc": 3,
    "b.a": 3,
    "postgraduate": 4,
    "master": 4,
    "masters": 4,
    "m.tech": 4,
    "m.sc": 4,
    "mba": 4,
    "m.a": 4,
    "doctorate": 5,
    "phd": 5,
    "ph.d": 5,
}

_STOPWORDS = {
    "and", "or", "the", "a", "an", "in", "of", "for", "with", "to", "on", "at",
    "by", "from", "as", "is", "are", "be", "must", "have", "has", "experience",
    "knowledge", "skills", "skill", "ability", "strong", "good", "required",
    "preferred", "years", "year", "degree", "field", "related", "working",
}


class MatchPrerequisiteError(Exception):
    """Raised when required resume or job analysis data is missing."""

    def __init__(self, missing_items: List[str]):
        self.missing_items = missing_items
        super().__init__(
            "Cannot compute match because required analysis data is missing: "
            + "; ".join(missing_items)
        )


def _canonicalize_skill(raw_name: str) -> Tuple[str, Optional[str]]:
    """Return (canonical_lower, canonical_category) using Feature 17 dictionary."""
    cleaned = normalize_skill_text(raw_name or "")
    if not cleaned:
        return (raw_name or "").strip().lower(), None
    match = skill_dictionary.lookup(cleaned)
    if match:
        spec, _method, _conf = match
        return spec["name"].strip().lower(), spec.get("category")
    return cleaned.lower(), None


def _tokenize(text: str) -> Set[str]:
    tokens = re.findall(r"[a-z0-9\+\#\.]+", (text or "").lower())
    return {t for t in tokens if len(t) > 1 and t not in _STOPWORDS}


def _infer_degree_rank(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    lower = text.strip().lower()
    for key, rank in _DEGREE_LEVEL_RANK.items():
        if key in lower:
            return rank
    return None


def _parse_years_from_text(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = re.search(r"(\d+)\s*\+?\s*(?:years?|yrs?)", text.lower())
    return int(m.group(1)) if m else None


class JobMatchingService:
    """Deterministic, evidence-backed Resume-to-Job Matching Engine."""

    def _load_resume_context(self, db: Session, resume_id: uuid.UUID) -> Dict[str, Any]:
        skills = db.execute(
            select(ResumeSkill).where(ResumeSkill.resume_id == resume_id)
        ).scalars().all()
        experiences = db.execute(
            select(Experience).where(Experience.resume_id == resume_id)
        ).scalars().all()
        educations = db.execute(
            select(Education).where(Education.resume_id == resume_id)
        ).scalars().all()
        projects = db.execute(
            select(Project).where(Project.resume_id == resume_id)
        ).scalars().all()
        certifications = db.execute(
            select(Certification).where(Certification.resume_id == resume_id)
        ).scalars().all()

        if not (skills or experiences or educations or projects or certifications):
            raise MatchPrerequisiteError(
                ["Resume structured analysis (extract skills, experience, education, or projects first)"]
            )

        return {
            "skills": skills,
            "experiences": experiences,
            "educations": educations,
            "projects": projects,
            "certifications": certifications,
        }

    def _load_job_context(self, db: Session, jd: JobDescription) -> Dict[str, Any]:
        req_analysis = db.execute(
            select(JobRequirementAnalysis).where(
                JobRequirementAnalysis.job_description_id == jd.id
            )
        ).scalar_one_or_none()
        skill_cls = db.execute(
            select(JobSkillClassification).where(
                JobSkillClassification.job_description_id == jd.id
            )
        ).scalar_one_or_none()

        if not req_analysis and not skill_cls:
            raise MatchPrerequisiteError(
                ["Job description analysis (run Job Requirement Extraction or Skill Classification first)"]
            )

        return {
            "req_analysis": req_analysis,
            "skill_cls": skill_cls,
        }

    def _compute_input_hash(
        self,
        resume: Resume,
        jd: JobDescription,
        r_ctx: Dict[str, Any],
        j_ctx: Dict[str, Any],
    ) -> str:
        parts = [
            CALCULATION_VERSION,
            str(resume.id),
            str(resume.updated_at.isoformat()),
            str(jd.id),
            jd.content_hash,
            str(len(r_ctx["skills"])),
            ",".join(sorted(s.canonical_name for s in r_ctx["skills"])),
            str(len(r_ctx["experiences"])),
            str(sum(e.duration_months or 0 for e in r_ctx["experiences"])),
            str(len(r_ctx["educations"])),
            str(len(r_ctx["projects"])),
            str(len(r_ctx["certifications"])),
        ]
        if j_ctx["req_analysis"]:
            parts.append(j_ctx["req_analysis"].updated_at.isoformat())
        if j_ctx["skill_cls"]:
            parts.append(j_ctx["skill_cls"].updated_at.isoformat())
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def _build_candidate_skill_index(self, r_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build explicit skill evidence index from ResumeSkill, Experience.technologies,
        Project.technologies, and Certification.related_skills.
        Never infers skills from job titles or project titles alone.
        """
        canonical_map: Dict[str, Dict[str, Any]] = {}
        category_map: Dict[str, List[str]] = {}

        def _register(raw_name: str, source: str, evidence_items: List[str], cat_hint: Optional[str] = None) -> None:
            canon_key, dict_cat = _canonicalize_skill(raw_name)
            if not canon_key:
                return
            category = dict_cat or cat_hint or "Other"
            entry = canonical_map.setdefault(
                canon_key,
                {"display": raw_name.strip(), "category": category, "evidence": []},
            )
            for ev in evidence_items:
                if ev and ev not in entry["evidence"]:
                    entry["evidence"].append(ev)
            if not evidence_items:
                tag = f"Listed in {source}: {raw_name.strip()}"
                if tag not in entry["evidence"]:
                    entry["evidence"].append(tag)
            category_map.setdefault(category.lower(), [])
            if entry["display"] not in category_map[category.lower()]:
                category_map[category.lower()].append(entry["display"])

        for sk in r_ctx["skills"]:
            ev = list(sk.source_evidence or [])
            if not ev:
                sections = ", ".join(sk.source_sections or ["skills"])
                ev = [f"Resume skill ({sections}): {sk.canonical_name}"]
            _register(sk.canonical_name, "resume_skills", ev, sk.category)
            if sk.original_name and sk.original_name.lower() != sk.canonical_name.lower():
                _register(sk.original_name, "resume_skills", ev, sk.category)

        for exp in r_ctx["experiences"]:
            role_label = exp.job_title or exp.company or "Experience"
            for tech in exp.technologies or []:
                _register(tech, f"experience ({role_label})", [f"Experience ({role_label}): {tech}"])

        for proj in r_ctx["projects"]:
            for tech in proj.technologies or []:
                _register(tech, f"project ({proj.project_title})", [f"Project ({proj.project_title}): {tech}"])

        for cert in r_ctx["certifications"]:
            for rel in cert.related_skills or []:
                name = rel.get("name") if isinstance(rel, dict) else str(rel)
                if name:
                    _register(name, f"certification ({cert.certification_name})", [f"Certification ({cert.certification_name}): {name}"])

        return {"by_name": canonical_map, "by_category": category_map}

    def _collect_job_technical_skills(self, jd: JobDescription, j_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Merge technical skills from Feature #36 and #37, preserving priority/importance."""
        merged: Dict[str, Dict[str, Any]] = {}
        req_analysis = j_ctx["req_analysis"]
        skill_cls = j_ctx["skill_cls"]

        if req_analysis:
            for item in req_analysis.technical_skills or []:
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                canon_key, _ = _canonicalize_skill(name)
                merged[canon_key] = {
                    "name": name,
                    "category": item.get("category") or "Other",
                    "importance": item.get("importance") or "Unspecified",
                }

        if skill_cls:
            for item in skill_cls.skills or []:
                cat = str(item.get("category") or "Other")
                if cat in ("Soft Skill", "Domain Knowledge"):
                    continue
                name = str(item.get("name", "")).strip()
                if not name:
                    continue
                canon_key, _ = _canonicalize_skill(name)
                existing = merged.get(canon_key)
                classification = item.get("classification") or "Unspecified"
                if existing:
                    if existing["importance"] == "Unspecified" and classification != "Unspecified":
                        existing["importance"] = classification
                else:
                    merged[canon_key] = {
                        "name": name,
                        "category": cat,
                        "importance": classification,
                    }

        if not merged:
            for s in jd.mandatory_skills or []:
                canon_key, _ = _canonicalize_skill(str(s))
                merged[canon_key] = {"name": str(s), "category": "Other", "importance": "Mandatory"}
            for s in jd.preferred_skills or []:
                canon_key, _ = _canonicalize_skill(str(s))
                merged.setdefault(canon_key, {"name": str(s), "category": "Other", "importance": "Preferred"})

        return list(merged.values())

    def _evaluate_technical_skills(
        self,
        job_skills: List[Dict[str, Any]],
        skill_index: Dict[str, Any],
        has_any_resume_skills: bool,
    ) -> Tuple[List[RequirementMatchItem], Optional[float], Dict[str, int]]:
        items: List[RequirementMatchItem] = []
        counts = {"matched": 0, "partial": 0, "missing": 0, "not_verifiable": 0}
        if not job_skills:
            return items, None, counts

        by_name = skill_index["by_name"]
        by_category = skill_index["by_category"]
        earned_weight = 0.0
        total_weight = 0.0

        for j_skill in job_skills:
            name = j_skill["name"]
            importance = j_skill.get("importance", "Unspecified")
            weight = _IMPORTANCE_WEIGHT.get(importance, 1.0)
            canon_key, dict_cat = _canonicalize_skill(name)
            cat_key = (dict_cat or j_skill.get("category") or "Other").lower()

            if not has_any_resume_skills:
                counts["not_verifiable"] += 1
                items.append(
                    RequirementMatchItem(
                        requirement=name,
                        category="technical_skill",
                        importance=importance,
                        status="Not Verifiable",
                        score_ratio=0.0,
                        reason="No extracted skills or technologies found in resume to verify.",
                    )
                )
                continue

            if canon_key in by_name:
                match_entry = by_name[canon_key]
                counts["matched"] += 1
                earned_weight += weight * 1.0
                total_weight += weight
                items.append(
                    RequirementMatchItem(
                        requirement=name,
                        category="technical_skill",
                        importance=importance,
                        status="Matched",
                        score_ratio=1.0,
                        matched_with=match_entry["display"],
                        evidence=match_entry["evidence"][:3],
                        reason="Direct skill match found in resume.",
                    )
                )
                continue

            # Check related skills in the same canonical category (excluding generic "other")
            related = by_category.get(cat_key, []) if cat_key != "other" else []
            if related:
                counts["partial"] += 1
                earned_weight += weight * 0.5
                total_weight += weight
                items.append(
                    RequirementMatchItem(
                        requirement=name,
                        category="technical_skill",
                        importance=importance,
                        status="Partially Matched",
                        score_ratio=0.5,
                        matched_with=related[0],
                        evidence=[f"Related {cat_key} skill in resume: {', '.join(related[:3])}"],
                        reason=f"Candidate has related {cat_key} skills, but {name} is not explicitly listed.",
                    )
                )
            else:
                counts["missing"] += 1
                total_weight += weight
                items.append(
                    RequirementMatchItem(
                        requirement=name,
                        category="technical_skill",
                        importance=importance,
                        status="Missing",
                        score_ratio=0.0,
                        reason=f"No evidence of {name} found in resume skills, experience, or projects.",
                    )
                )

        score = round((earned_weight / total_weight) * 100.0, 2) if total_weight > 0 else None
        return items, score, counts

    def _evaluate_experience(
        self,
        jd: JobDescription,
        j_ctx: Dict[str, Any],
        r_ctx: Dict[str, Any],
        job_skills: List[Dict[str, Any]],
    ) -> Tuple[ExperienceMatchSummary, List[RequirementMatchItem], Optional[float], Dict[str, int]]:
        req_analysis = j_ctx["req_analysis"]
        exp_req = req_analysis.experience if req_analysis else {}
        min_years = exp_req.get("minimum_years") if isinstance(exp_req, dict) else None
        max_years = exp_req.get("maximum_years") if isinstance(exp_req, dict) else None
        fresher_eligible = exp_req.get("fresher_eligible") if isinstance(exp_req, dict) else None

        if min_years is None and jd.experience_required:
            min_years = _parse_years_from_text(jd.experience_required)

        experiences = r_ctx["experiences"]
        durations = [e.duration_months for e in experiences if e.duration_months is not None]
        total_months = sum(durations) if durations else None
        total_years = round(total_months / 12.0, 1) if total_months is not None else None

        job_skill_keys = {_canonicalize_skill(s["name"])[0] for s in job_skills}
        title_tokens = _tokenize(jd.job_title)
        relevant_roles: List[Dict[str, Any]] = []

        for exp in experiences:
            exp_tech_keys = {_canonicalize_skill(t)[0] for t in (exp.technologies or [])}
            overlap_skills = sorted(job_skill_keys & exp_tech_keys)
            role_tokens = _tokenize(exp.job_title or "")
            title_overlap = len(title_tokens & role_tokens) > 0
            if overlap_skills or title_overlap:
                relevant_roles.append(
                    {
                        "job_title": exp.job_title,
                        "company": exp.company,
                        "duration_months": exp.duration_months,
                        "matched_technologies": overlap_skills,
                    }
                )

        req_items: List[RequirementMatchItem] = []
        counts = {"matched": 0, "partial": 0, "missing": 0, "not_verifiable": 0}

        if min_years is None and not experiences:
            return (
                ExperienceMatchSummary(
                    status="Not Verifiable",
                    fresher_eligible=fresher_eligible,
                    summary="No explicit years of experience requirement specified.",
                ),
                req_items,
                None,
                counts,
            )

        if min_years is not None:
            req_label = f"{min_years}+ years of experience"
            if not experiences or total_years is None:
                status = "Not Verifiable"
                score = None
                counts["not_verifiable"] += 1
                summary = f"Job requires {min_years}+ years, but resume experience durations are unavailable."
                req_items.append(
                    RequirementMatchItem(
                        requirement=req_label,
                        category="experience",
                        importance="Mandatory",
                        status="Not Verifiable",
                        score_ratio=0.0,
                        reason=summary,
                    )
                )
            elif total_years >= min_years:
                status = "Matched"
                score = 100.0 if relevant_roles or not job_skill_keys else 80.0
                counts["matched"] += 1
                summary = f"Candidate has {total_years} years of experience, meeting the {min_years}+ year requirement."
                req_items.append(
                    RequirementMatchItem(
                        requirement=req_label,
                        category="experience",
                        importance="Mandatory",
                        status="Matched",
                        score_ratio=1.0,
                        matched_with=f"{total_years} years ({len(experiences)} roles)",
                        evidence=[f"Total documented experience: {total_years} years"],
                        reason=summary,
                    )
                )
            elif total_years >= min_years * 0.5 or relevant_roles:
                ratio = round(min(0.85, max(0.35, total_years / max(min_years, 1))), 2)
                status = "Partially Matched"
                score = round(ratio * 100.0, 2)
                counts["partial"] += 1
                summary = f"Candidate has {total_years} years of experience against {min_years}+ years required."
                req_items.append(
                    RequirementMatchItem(
                        requirement=req_label,
                        category="experience",
                        importance="Mandatory",
                        status="Partially Matched",
                        score_ratio=ratio,
                        matched_with=f"{total_years} years",
                        evidence=[f"Total documented experience: {total_years} years"],
                        reason=summary,
                    )
                )
            else:
                status = "Missing"
                score = 0.0
                counts["missing"] += 1
                summary = f"Candidate has {total_years} years of experience, below the {min_years}+ year requirement."
                req_items.append(
                    RequirementMatchItem(
                        requirement=req_label,
                        category="experience",
                        importance="Mandatory",
                        status="Missing",
                        score_ratio=0.0,
                        matched_with=f"{total_years} years",
                        reason=summary,
                    )
                )
        else:
            # No explicit min_years, evaluate role/technology relevance if experiences exist
            if not experiences:
                status = "Not Verifiable"
                score = None
                counts["not_verifiable"] += 1
                summary = "No experience records found in resume."
            elif relevant_roles:
                status = "Matched"
                score = 100.0
                counts["matched"] += 1
                summary = f"Found {len(relevant_roles)} relevant experience role(s) matching target domain/skills."
            else:
                status = "Partially Matched"
                score = 50.0
                counts["partial"] += 1
                summary = f"Candidate has {len(experiences)} experience role(s), though direct skill/title overlap is limited."

        return (
            ExperienceMatchSummary(
                status=status,
                candidate_total_months=total_months,
                candidate_total_years=total_years,
                required_min_years=min_years,
                required_max_years=max_years,
                fresher_eligible=fresher_eligible,
                relevant_roles=relevant_roles,
                summary=summary,
            ),
            req_items,
            score,
            counts,
        )

    def _evaluate_education(
        self,
        jd: JobDescription,
        j_ctx: Dict[str, Any],
        r_ctx: Dict[str, Any],
    ) -> Tuple[EducationMatchSummary, List[RequirementMatchItem], Optional[float], Dict[str, int]]:
        req_analysis = j_ctx["req_analysis"]
        edu_req = req_analysis.education if req_analysis else {}
        required_degree = None
        required_fields: List[str] = []
        req_certs: List[str] = []

        if isinstance(edu_req, dict):
            required_degree = edu_req.get("required_degree") or edu_req.get("minimum_level")
            required_fields = list(edu_req.get("required_fields") or [])
            req_certs = list(edu_req.get("required_certifications") or [])

        if not required_degree and jd.education_required:
            required_degree = jd.education_required

        educations = r_ctx["educations"]
        certifications = r_ctx["certifications"]
        candidate_degrees = [
            {
                "degree": e.normalized_degree or e.degree,
                "degree_level": e.degree_level,
                "field_of_study": e.field_of_study,
                "institution": e.institution,
            }
            for e in educations
        ]

        cert_names_lower = {
            (c.normalized_name or c.certification_name).lower(): c.certification_name
            for c in certifications
        }
        certs_matched: List[str] = []
        certs_missing: List[str] = []
        req_items: List[RequirementMatchItem] = []
        counts = {"matched": 0, "partial": 0, "missing": 0, "not_verifiable": 0}

        for cert in req_certs:
            cert_low = cert.lower()
            matched_cert = next(
                (orig for k, orig in cert_names_lower.items() if cert_low in k or k in cert_low),
                None,
            )
            if matched_cert:
                certs_matched.append(matched_cert)
                counts["matched"] += 1
                req_items.append(
                    RequirementMatchItem(
                        requirement=f"Certification: {cert}",
                        category="certification",
                        importance="Mandatory",
                        status="Matched",
                        score_ratio=1.0,
                        matched_with=matched_cert,
                        evidence=[f"Resume certification: {matched_cert}"],
                    )
                )
            elif not certifications and not educations:
                counts["not_verifiable"] += 1
                req_items.append(
                    RequirementMatchItem(
                        requirement=f"Certification: {cert}",
                        category="certification",
                        importance="Mandatory",
                        status="Not Verifiable",
                        score_ratio=0.0,
                        reason="No certifications or education records extracted to verify.",
                    )
                )
            else:
                certs_missing.append(cert)
                counts["missing"] += 1
                req_items.append(
                    RequirementMatchItem(
                        requirement=f"Certification: {cert}",
                        category="certification",
                        importance="Mandatory",
                        status="Missing",
                        score_ratio=0.0,
                        reason=f"Required certification '{cert}' not found in resume.",
                    )
                )

        if not required_degree and not required_fields and not req_certs:
            return (
                EducationMatchSummary(
                    status="Not Verifiable",
                    candidate_degrees=candidate_degrees,
                    summary="No explicit education requirement specified in the job description.",
                ),
                req_items,
                None,
                counts,
            )

        if not required_degree and not required_fields:
            # Only certifications were required
            cert_score = (
                round((len(certs_matched) / len(req_certs)) * 100.0, 2)
                if req_certs and (certifications or educations)
                else None
            )
            edu_status: Any = "Matched" if certs_matched and not certs_missing else (
                "Partially Matched" if certs_matched else ("Missing" if certs_missing else "Not Verifiable")
            )
            return (
                EducationMatchSummary(
                    status=edu_status,
                    candidate_degrees=candidate_degrees,
                    certifications_matched=certs_matched,
                    certifications_missing=certs_missing,
                    summary="Evaluated required certifications against candidate profile.",
                ),
                req_items,
                cert_score,
                counts,
            )

        if not educations:
            counts["not_verifiable"] += 1
            req_items.append(
                RequirementMatchItem(
                    requirement=required_degree or ", ".join(required_fields),
                    category="education",
                    importance="Mandatory",
                    status="Not Verifiable",
                    score_ratio=0.0,
                    reason="No education records found in resume to verify degree requirement.",
                )
            )
            return (
                EducationMatchSummary(
                    status="Not Verifiable",
                    required_degree=required_degree,
                    required_fields=required_fields,
                    candidate_degrees=[],
                    certifications_matched=certs_matched,
                    certifications_missing=certs_missing,
                    summary="Education requirement cannot be verified because resume has no extracted education records.",
                ),
                req_items,
                None,
                counts,
            )

        req_rank = _infer_degree_rank(required_degree)
        cand_ranks = [
            _infer_degree_rank(e.degree_level) or _infer_degree_rank(e.normalized_degree or e.degree) or 0
            for e in educations
        ]
        max_cand_rank = max(cand_ranks) if cand_ranks else 0

        field_matched = not required_fields
        matched_degree_label = None
        for e in educations:
            cand_field = f"{e.field_of_study or ''} {e.specialization or ''} {e.degree or ''}".lower()
            if any(_tokenize(rf) & _tokenize(cand_field) for rf in required_fields):
                field_matched = True
                matched_degree_label = e.normalized_degree or e.degree
                break
        if not matched_degree_label and educations:
            matched_degree_label = educations[0].normalized_degree or educations[0].degree

        degree_ok = req_rank is None or max_cand_rank >= req_rank
        if degree_ok and field_matched:
            status = "Matched"
            score = 100.0
            counts["matched"] += 1
            summary = f"Candidate education ({matched_degree_label}) satisfies {required_degree or 'field'} requirement."
            ratio = 1.0
        elif degree_ok or field_matched:
            status = "Partially Matched"
            score = 50.0
            counts["partial"] += 1
            summary = f"Candidate education ({matched_degree_label}) partially aligns with {required_degree or ', '.join(required_fields)}."
            ratio = 0.5
        else:
            status = "Missing"
            score = 0.0
            counts["missing"] += 1
            summary = f"Candidate education does not meet {required_degree or ', '.join(required_fields)}."
            ratio = 0.0

        req_items.append(
            RequirementMatchItem(
                requirement=required_degree or ", ".join(required_fields),
                category="education",
                importance="Mandatory",
                status=status,
                score_ratio=ratio,
                matched_with=matched_degree_label,
                evidence=[f"Education: {matched_degree_label}"] if matched_degree_label else [],
                reason=summary,
            )
        )

        return (
            EducationMatchSummary(
                status=status,
                required_degree=required_degree,
                required_fields=required_fields,
                candidate_degrees=candidate_degrees,
                certifications_matched=certs_matched,
                certifications_missing=certs_missing,
                summary=summary,
            ),
            req_items,
            score,
            counts,
        )

    def _evaluate_projects(
        self,
        jd: JobDescription,
        r_ctx: Dict[str, Any],
        job_skills: List[Dict[str, Any]],
    ) -> Tuple[List[RelevantProjectItem], Optional[float], Dict[str, int]]:
        projects = r_ctx["projects"]
        counts = {"matched": 0, "partial": 0, "missing": 0, "not_verifiable": 0}
        if not projects:
            return [], None, counts

        job_skill_keys = {_canonicalize_skill(s["name"])[0]: s["name"] for s in job_skills}
        jd_tokens = _tokenize(f"{jd.job_title} {jd.raw_description[:400]}")
        relevant_items: List[RelevantProjectItem] = []

        for proj in projects:
            proj_tech_keys = {_canonicalize_skill(t)[0] for t in (proj.technologies or [])}
            matched_keys = job_skill_keys.keys() & proj_tech_keys
            matched_skills = [job_skill_keys[k] for k in sorted(matched_keys)]

            desc_tokens = _tokenize(f"{proj.short_description or ''} {proj.domain or ''}")
            domain_overlap = len(jd_tokens & desc_tokens)

            if job_skill_keys:
                skill_ratio = min(1.0, len(matched_keys) / min(len(job_skill_keys), 4))
            else:
                skill_ratio = 0.5 if domain_overlap > 0 else 0.0

            relevance = round(min(100.0, skill_ratio * 85.0 + min(15.0, domain_overlap * 5.0)), 2)
            evidence = [f"Technologies: {', '.join(proj.technologies[:5])}"] if proj.technologies else []
            relevant_items.append(
                RelevantProjectItem(
                    project_id=str(proj.id),
                    project_title=proj.project_title,
                    project_category=proj.project_category,
                    relevance_score=relevance,
                    matched_skills=matched_skills,
                    evidence=evidence,
                )
            )

        relevant_items.sort(key=lambda p: p.relevance_score, reverse=True)
        top_score = relevant_items[0].relevance_score if relevant_items else 0.0
        if top_score >= 60:
            counts["matched"] += 1
        elif top_score > 0:
            counts["partial"] += 1
        else:
            counts["missing"] += 1

        return relevant_items, top_score, counts

    def _evaluate_other_requirements(
        self,
        j_ctx: Dict[str, Any],
        r_ctx: Dict[str, Any],
    ) -> Tuple[List[RequirementMatchItem], Optional[float], Dict[str, int]]:
        req_analysis = j_ctx["req_analysis"]
        items: List[RequirementMatchItem] = []
        counts = {"matched": 0, "partial": 0, "missing": 0, "not_verifiable": 0}
        if not req_analysis:
            return items, None, counts

        other_reqs: List[Tuple[str, Dict[str, Any]]] = []
        for s in req_analysis.soft_skills or []:
            other_reqs.append(("soft_skill", s))
        for d in req_analysis.domain_knowledge or []:
            other_reqs.append(("domain_knowledge", d))
        for o in req_analysis.other_requirements or []:
            other_reqs.append(("other", o))

        if not other_reqs:
            return items, None, counts

        evidence_corpus = " ".join(
            [
                " ".join(" ".join(e.responsibilities or []) for e in r_ctx["experiences"]),
                " ".join(" ".join(p.responsibilities or []) + " " + (p.domain or "") for p in r_ctx["projects"]),
                " ".join(s.canonical_name for s in r_ctx["skills"]),
            ]
        ).lower()
        corpus_tokens = _tokenize(evidence_corpus)

        earned = 0.0
        total = 0.0
        for cat, req in other_reqs:
            name = str(req.get("name", "")).strip()
            if not name:
                continue
            importance = req.get("importance") or "Unspecified"
            req_tokens = _tokenize(name)

            if not corpus_tokens or not req_tokens:
                counts["not_verifiable"] += 1
                items.append(
                    RequirementMatchItem(
                        requirement=name,
                        category=cat,
                        importance=importance,
                        status="Not Verifiable",
                        score_ratio=0.0,
                        reason="Insufficient structured resume text to verify this requirement.",
                    )
                )
                continue

            overlap = len(req_tokens & corpus_tokens) / len(req_tokens)
            if overlap >= 0.6:
                counts["matched"] += 1
                earned += 1.0
                total += 1.0
                items.append(
                    RequirementMatchItem(
                        requirement=name,
                        category=cat,
                        importance=importance,
                        status="Matched",
                        score_ratio=1.0,
                        evidence=["Supported by resume experience/project descriptions."],
                    )
                )
            elif overlap > 0:
                counts["partial"] += 1
                earned += 0.5
                total += 1.0
                items.append(
                    RequirementMatchItem(
                        requirement=name,
                        category=cat,
                        importance=importance,
                        status="Partially Matched",
                        score_ratio=0.5,
                        reason="Partial keyword overlap found in resume experience/projects.",
                    )
                )
            else:
                counts["not_verifiable"] += 1
                items.append(
                    RequirementMatchItem(
                        requirement=name,
                        category=cat,
                        importance=importance,
                        status="Not Verifiable",
                        score_ratio=0.0,
                        reason="Not explicitly verifiable from structured resume sections.",
                    )
                )

        score = round((earned / total) * 100.0, 2) if total > 0 else None
        return items, score, counts

    def _compute_score_breakdown(
        self,
        category_results: Dict[str, Tuple[Optional[float], Dict[str, int], Optional[str]]],
    ) -> ScoreBreakdownSchema:
        total_applied = 0.0
        weighted_sum = 0.0
        categories: Dict[str, CategoryScoreBreakdown] = {}

        for key, (label, cfg_weight) in CATEGORY_WEIGHTS.items():
            raw_score, counts, note = category_results[key]
            available = raw_score is not None
            if available:
                total_applied += cfg_weight

        norm_factor = round(1.0 / total_applied, 4) if total_applied > 0 else 0.0

        for key, (label, cfg_weight) in CATEGORY_WEIGHTS.items():
            raw_score, counts, note = category_results[key]
            available = raw_score is not None
            applied_weight = round(cfg_weight * norm_factor, 4) if (available and total_applied > 0) else 0.0
            contribution = round((raw_score or 0.0) * applied_weight, 2) if available else 0.0
            if available:
                weighted_sum += contribution

            categories[key] = CategoryScoreBreakdown(
                category=key,
                label=label,
                configured_weight=cfg_weight,
                applied_weight=applied_weight,
                raw_score=raw_score,
                weighted_contribution=contribution,
                available=available,
                matched_count=counts["matched"],
                partial_count=counts["partial"],
                missing_count=counts["missing"],
                not_verifiable_count=counts["not_verifiable"],
                notes=note,
            )

        overall = round(min(100.0, max(0.0, weighted_sum)), 2)
        return ScoreBreakdownSchema(
            overall_score=overall,
            total_configured_weight=1.0,
            total_applied_weight=round(total_applied, 4),
            normalization_factor=norm_factor,
            categories=categories,
        )

    def _build_insights(
        self,
        skill_items: List[RequirementMatchItem],
        exp_summary: ExperienceMatchSummary,
        edu_summary: EducationMatchSummary,
        relevant_projects: List[RelevantProjectItem],
    ) -> Tuple[List[str], List[str]]:
        strengths: List[str] = []
        improvements: List[str] = []

        matched_mandatory = [s.requirement for s in skill_items if s.status == "Matched" and s.importance == "Mandatory"]
        matched_other = [s.requirement for s in skill_items if s.status == "Matched" and s.importance != "Mandatory"]
        missing_mandatory = [s.requirement for s in skill_items if s.status == "Missing" and s.importance == "Mandatory"]
        missing_preferred = [s.requirement for s in skill_items if s.status == "Missing" and s.importance == "Preferred"]
        partial_skills = [s.requirement for s in skill_items if s.status == "Partially Matched"]

        if matched_mandatory:
            strengths.append(f"Meets mandatory technical skills: {', '.join(matched_mandatory[:6])}.")
        if matched_other:
            strengths.append(f"Demonstrates additional matching skills: {', '.join(matched_other[:5])}.")
        if exp_summary.status == "Matched":
            strengths.append(exp_summary.summary)
        if edu_summary.status == "Matched":
            strengths.append(edu_summary.summary)
        if relevant_projects and relevant_projects[0].relevance_score >= 50:
            strengths.append(
                f"Relevant project '{relevant_projects[0].project_title}' demonstrates applied skills."
            )

        if missing_mandatory:
            improvements.append(f"Missing mandatory technical skills: {', '.join(missing_mandatory[:6])}.")
        if missing_preferred:
            improvements.append(f"Missing preferred skills: {', '.join(missing_preferred[:5])}.")
        if partial_skills:
            improvements.append(
                f"Strengthen direct evidence for partially matched skills: {', '.join(partial_skills[:5])}."
            )
        if exp_summary.status in ("Missing", "Partially Matched"):
            improvements.append(exp_summary.summary)
        if edu_summary.status in ("Missing", "Partially Matched"):
            improvements.append(edu_summary.summary)

        return strengths, improvements

    def _to_data(
        self,
        record: JobMatch,
        resume: Resume,
        jd: JobDescription,
        cached: bool,
    ) -> JobMatchData:
        details = record.match_details or {}
        matched = [RequirementMatchItem(**i) for i in (record.matched_requirements or [])]
        partial = [RequirementMatchItem(**i) for i in (record.partially_matched_requirements or [])]
        missing = [RequirementMatchItem(**i) for i in (record.missing_requirements or [])]
        not_verifiable = [RequirementMatchItem(**i) for i in (record.not_verifiable_requirements or [])]

        return JobMatchData(
            id=str(record.id),
            user_id=str(record.user_id) if record.user_id else "",
            resume_id=str(record.resume_id),
            job_description_id=str(record.job_description_id),
            resume_filename=resume.original_filename,
            job_title=jd.job_title,
            company_name=jd.company_name,
            overall_match_score=record.overall_match_score,
            score_breakdown=ScoreBreakdownSchema(**(record.score_breakdown or {})),
            summary_counts=JobMatchSummaryCounts(
                matched_count=len(matched),
                partially_matched_count=len(partial),
                missing_count=len(missing),
                not_verifiable_count=len(not_verifiable),
                total_requirements=len(matched) + len(partial) + len(missing) + len(not_verifiable),
            ),
            matching_skills=[i for i in matched if i.category == "technical_skill"],
            partially_matching_skills=[i for i in partial if i.category == "technical_skill"],
            missing_skills=[i for i in missing if i.category == "technical_skill"],
            matched_requirements=matched,
            partially_matched_requirements=partial,
            missing_requirements=missing,
            not_verifiable_requirements=not_verifiable,
            experience_match=ExperienceMatchSummary(**details.get("experience_match", {"status": "Not Verifiable", "summary": ""})),
            education_match=EducationMatchSummary(**details.get("education_match", {"status": "Not Verifiable", "summary": ""})),
            relevant_projects=[RelevantProjectItem(**p) for p in details.get("relevant_projects", [])],
            strengths=list(details.get("strengths", [])),
            improvement_areas=list(details.get("improvement_areas", [])),
            evidence_from_resume=record.evidence_from_resume or {},
            calculation_version=record.calculation_version,
            version_number=record.version_number,
            cached=cached,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def get_saved_match(
        self,
        db: Session,
        match_id: uuid.UUID,
        user_uuid: uuid.UUID,
    ) -> Optional[JobMatchData]:
        record = db.execute(
            select(JobMatch).where(JobMatch.id == match_id)
        ).scalar_one_or_none()
        if not record:
            return None
        if record.user_id and record.user_id != user_uuid:
            raise PermissionError("Access denied: You do not own this job match.")
        resume = db.execute(select(Resume).where(Resume.id == record.resume_id)).scalar_one()
        jd = db.execute(select(JobDescription).where(JobDescription.id == record.job_description_id)).scalar_one()
        return self._to_data(record, resume, jd, cached=True)

    def compute_and_save(
        self,
        db: Session,
        user_uuid: uuid.UUID,
        resume: Resume,
        jd: JobDescription,
        regenerate: bool = False,
    ) -> JobMatchData:
        r_ctx = self._load_resume_context(db, resume.id)
        j_ctx = self._load_job_context(db, jd)
        input_hash = self._compute_input_hash(resume, jd, r_ctx, j_ctx)

        existing = db.execute(
            select(JobMatch).where(
                JobMatch.resume_id == resume.id,
                JobMatch.job_description_id == jd.id,
            )
        ).scalar_one_or_none()

        if existing and existing.input_hash == input_hash and not regenerate:
            logger.info("Returning cached JobMatch %s", existing.id)
            return self._to_data(existing, resume, jd, cached=True)

        skill_index = self._build_candidate_skill_index(r_ctx)
        has_any_resume_skills = len(skill_index["by_name"]) > 0
        job_skills = self._collect_job_technical_skills(jd, j_ctx)

        skill_items, skill_score, skill_counts = self._evaluate_technical_skills(
            job_skills, skill_index, has_any_resume_skills
        )
        exp_summary, exp_items, exp_score, exp_counts = self._evaluate_experience(
            jd, j_ctx, r_ctx, job_skills
        )
        edu_summary, edu_items, edu_score, edu_counts = self._evaluate_education(
            jd, j_ctx, r_ctx
        )
        relevant_projects, proj_score, proj_counts = self._evaluate_projects(
            jd, r_ctx, job_skills
        )
        other_items, other_score, other_counts = self._evaluate_other_requirements(
            j_ctx, r_ctx
        )

        breakdown = self._compute_score_breakdown(
            {
                "technical_skills": (
                    skill_score,
                    skill_counts,
                    None if skill_score is not None else "No verifiable technical skill requirements.",
                ),
                "relevant_experience": (
                    exp_score,
                    exp_counts,
                    exp_summary.summary,
                ),
                "projects": (
                    proj_score,
                    proj_counts,
                    None if proj_score is not None else "No project records found in resume.",
                ),
                "education": (
                    edu_score,
                    edu_counts,
                    edu_summary.summary,
                ),
                "other_requirements": (
                    other_score,
                    other_counts,
                    None if other_score is not None else "No verifiable soft-skill or domain requirements.",
                ),
            }
        )

        all_items = skill_items + exp_items + edu_items + other_items
        matched_reqs = [i.model_dump() for i in all_items if i.status == "Matched"]
        partial_reqs = [i.model_dump() for i in all_items if i.status == "Partially Matched"]
        missing_reqs = [i.model_dump() for i in all_items if i.status == "Missing"]
        not_verifiable_reqs = [i.model_dump() for i in all_items if i.status == "Not Verifiable"]

        strengths, improvements = self._build_insights(
            skill_items, exp_summary, edu_summary, relevant_projects
        )

        evidence_from_resume = {
            "skills_count": len(r_ctx["skills"]),
            "experience_count": len(r_ctx["experiences"]),
            "total_experience_years": exp_summary.candidate_total_years,
            "education_count": len(r_ctx["educations"]),
            "projects_count": len(r_ctx["projects"]),
            "certifications_count": len(r_ctx["certifications"]),
        }
        match_details = {
            "experience_match": exp_summary.model_dump(),
            "education_match": edu_summary.model_dump(),
            "relevant_projects": [p.model_dump() for p in relevant_projects],
            "strengths": strengths,
            "improvement_areas": improvements,
        }

        if existing:
            existing.user_id = user_uuid
            existing.overall_match_score = breakdown.overall_score
            existing.score_breakdown = breakdown.model_dump()
            existing.matched_requirements = matched_reqs
            existing.partially_matched_requirements = partial_reqs
            existing.missing_requirements = missing_reqs
            existing.not_verifiable_requirements = not_verifiable_reqs
            existing.evidence_from_resume = evidence_from_resume
            existing.match_details = match_details
            existing.calculation_version = CALCULATION_VERSION
            existing.version_number = (existing.version_number or 1) + 1
            existing.input_hash = input_hash
            existing.updated_at = datetime.now(timezone.utc)
            record = existing
        else:
            record = JobMatch(
                user_id=user_uuid,
                resume_id=resume.id,
                job_description_id=jd.id,
                overall_match_score=breakdown.overall_score,
                score_breakdown=breakdown.model_dump(),
                matched_requirements=matched_reqs,
                partially_matched_requirements=partial_reqs,
                missing_requirements=missing_reqs,
                not_verifiable_requirements=not_verifiable_reqs,
                evidence_from_resume=evidence_from_resume,
                match_details=match_details,
                calculation_version=CALCULATION_VERSION,
                version_number=1,
                input_hash=input_hash,
            )
            db.add(record)

        db.commit()
        db.refresh(record)
        return self._to_data(record, resume, jd, cached=False)


job_matching_service = JobMatchingService()
