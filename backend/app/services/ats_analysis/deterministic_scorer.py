"""
Deterministic ATS Compatibility Evaluation Engine
Phase 4 | Feature 24: ATS Compatibility Analysis
Pure Python deterministic scoring rubric; evaluates formatting, layout,
section detection, contact info, experience, education, skills, and parsing hazards.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import fitz  # PyMuPDF
try:
    import docx
except ImportError:
    docx = None

from app.schemas.ats_analysis import (
    ATS_CATEGORIES,
    ATSCategoryScore,
    ATSIssue,
    SectionDetectionItem,
    KeywordFindings,
)

logger = logging.getLogger(__name__)

STANDARD_SECTION_NAMES = {
    "contact_info": "Contact Information",
    "summary": "Professional Summary",
    "experience": "Work Experience",
    "education": "Education",
    "skills": "Technical Skills",
    "projects": "Projects",
    "certifications": "Certifications & Achievements",
}

STANDARD_HEADINGS_REGEX = {
    "summary": re.compile(r"^(professional\s+summary|summary|profile|about\s+me|career\s+objective|objective)\b", re.IGNORECASE),
    "experience": re.compile(r"^(work\s+experience|professional\s+experience|experience|employment\s+history|work\s+history)\b", re.IGNORECASE),
    "education": re.compile(r"^(education|academic\s+background|academic\s+history|academics)\b", re.IGNORECASE),
    "skills": re.compile(r"^(technical\s+skills|skills|technologies|core\s+competencies|technical\s+proficiencies)\b", re.IGNORECASE),
    "projects": re.compile(r"^(projects|technical\s+projects|personal\s+projects|academic\s+projects)\b", re.IGNORECASE),
    "certifications": re.compile(r"^(certifications|achievements|licenses\s+(&|and)\s+certifications|honors\s+(&|and)\s+awards)\b", re.IGNORECASE),
}

ACTION_VERBS = [
    "engineered", "developed", "spearheaded", "optimized", "architected",
    "implemented", "designed", "led", "automated", "scaled", "collaborated",
    "managed", "deployed", "reduced", "increased", "delivered", "configured",
    "maintained", "mentored", "orchestrated", "streamlined", "analyzed",
]


class ATSDeterministicScorer:
    """Evaluates resumes deterministically across 8 categories summing to 100 points."""

    def evaluate(
        self,
        resume: Any,
        file_path: Optional[Path] = None,
        cleaned_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs the complete deterministic ATS evaluation."""
        verified_issues: List[ATSIssue] = []
        formatting_risks: List[ATSIssue] = []
        category_scores: Dict[str, ATSCategoryScore] = {}

        # 1. Contact Information Completeness (Max 15 pts)
        contact_score, contact_status, contact_feedback = self._evaluate_contact_info(
            resume, verified_issues
        )
        category_scores["contact_info"] = ATSCategoryScore(
            key="contact_info",
            name=ATS_CATEGORIES["contact_info"]["name"],
            score=contact_score,
            max_score=ATS_CATEGORIES["contact_info"]["max_score"],
            status=contact_status,
            feedback=contact_feedback,
        )

        # 2. Standard Section Detection & Headings (Max 15 pts)
        detected_sections, missing_sections, section_score, section_status, section_feedback = self._evaluate_sections(
            resume, cleaned_text, verified_issues, formatting_risks
        )
        category_scores["standard_sections"] = ATSCategoryScore(
            key="standard_sections",
            name=ATS_CATEGORIES["standard_sections"]["name"],
            score=section_score,
            max_score=ATS_CATEGORIES["standard_sections"]["max_score"],
            status=section_status,
            feedback=section_feedback,
        )

        # 3. Work Experience Structure & Formatting (Max 20 pts)
        exp_score, exp_status, exp_feedback = self._evaluate_experience(
            resume, verified_issues
        )
        category_scores["experience_formatting"] = ATSCategoryScore(
            key="experience_formatting",
            name=ATS_CATEGORIES["experience_formatting"]["name"],
            score=exp_score,
            max_score=ATS_CATEGORIES["experience_formatting"]["max_score"],
            status=exp_status,
            feedback=exp_feedback,
        )

        # 4. Education Section Structure (Max 10 pts)
        edu_score, edu_status, edu_feedback = self._evaluate_education(
            resume, verified_issues
        )
        category_scores["education_structure"] = ATSCategoryScore(
            key="education_structure",
            name=ATS_CATEGORIES["education_structure"]["name"],
            score=edu_score,
            max_score=ATS_CATEGORIES["education_structure"]["max_score"],
            status=edu_status,
            feedback=edu_feedback,
        )

        # 5. Technical Skills Presentation (Max 15 pts)
        skills_score, skills_status, skills_feedback = self._evaluate_skills(
            resume, verified_issues
        )
        category_scores["skills_presentation"] = ATSCategoryScore(
            key="skills_presentation",
            name=ATS_CATEGORIES["skills_presentation"]["name"],
            score=skills_score,
            max_score=ATS_CATEGORIES["skills_presentation"]["max_score"],
            status=skills_status,
            feedback=skills_feedback,
        )

        # 6. Professional Summary Presence (Max 10 pts)
        sum_score, sum_status, sum_feedback = self._evaluate_summary(
            resume, verified_issues
        )
        category_scores["professional_summary"] = ATSCategoryScore(
            key="professional_summary",
            name=ATS_CATEGORIES["professional_summary"]["name"],
            score=sum_score,
            max_score=ATS_CATEGORIES["professional_summary"]["max_score"],
            status=sum_status,
            feedback=sum_feedback,
        )

        # 7. Projects & Certifications (Max 5 pts)
        proj_score, proj_status, proj_feedback = self._evaluate_projects_certifications(
            resume, verified_issues
        )
        category_scores["credentials_projects"] = ATSCategoryScore(
            key="credentials_projects",
            name=ATS_CATEGORIES["credentials_projects"]["name"],
            score=proj_score,
            max_score=ATS_CATEGORIES["credentials_projects"]["max_score"],
            status=proj_status,
            feedback=proj_feedback,
        )

        # 8. File Layout & Parsing Safety (Max 10 pts)
        layout_score, layout_status, layout_feedback = self._evaluate_file_layout(
            resume, file_path, cleaned_text, formatting_risks
        )
        category_scores["formatting_parsing_safety"] = ATSCategoryScore(
            key="formatting_parsing_safety",
            name=ATS_CATEGORIES["formatting_parsing_safety"]["name"],
            score=layout_score,
            max_score=ATS_CATEGORIES["formatting_parsing_safety"]["max_score"],
            status=layout_status,
            feedback=layout_feedback,
        )

        # Compute total score out of 100
        raw_total = sum(c.score for c in category_scores.values())
        ats_score = int(round(max(0.0, min(100.0, raw_total))))

        # Determine score grade
        if ats_score >= 85:
            grade = "Excellent"
            interpretation = "Excellent ATS compatibility. High probability of accurate field parsing and recruiter indexing."
        elif ats_score >= 70:
            grade = "Good"
            interpretation = "Good ATS parseability with a few minor formatting or content gaps to resolve."
        elif ats_score >= 50:
            grade = "Needs Work"
            interpretation = "Moderate parsing risks. Multiple sections or formatting structures may fail ATS extraction."
        else:
            grade = "Poor"
            interpretation = "High risk of ATS rejection. Critical sections or layout structures severely impair automated parsing."

        # Compute keywords and action verbs
        keyword_findings = self._extract_keyword_findings(resume, cleaned_text)

        return {
            "ats_score": ats_score,
            "score_grade": grade,
            "score_interpretation": interpretation,
            "category_scores": category_scores,
            "verified_issues": verified_issues,
            "formatting_risks": formatting_risks,
            "detected_sections": detected_sections,
            "missing_sections": missing_sections,
            "keyword_findings": keyword_findings,
        }

    # =========================================================================
    # INDIVIDUAL CATEGORY EVALUATORS
    # =========================================================================

    def _evaluate_contact_info(
        self, resume: Any, issues: List[ATSIssue]
    ) -> Tuple[float, str, str]:
        score = 0.0
        p_info = getattr(resume, "personal_information", None)

        email = getattr(p_info, "email", None) if p_info else None
        phone = getattr(p_info, "phone", None) if p_info else None
        location = getattr(p_info, "location", None) if p_info else None
        linkedin = getattr(p_info, "linkedin_url", None) if p_info else None
        github = getattr(p_info, "github_url", None) if p_info else None
        portfolio = getattr(p_info, "portfolio_url", None) if p_info else None

        # Email (+5)
        if email and "@" in email:
            score += 5.0
        else:
            issues.append(
                ATSIssue(
                    id="contact_missing_email",
                    category="contact_info",
                    category_name=ATS_CATEGORIES["contact_info"]["name"],
                    title="Missing or Unrecognized Email Address",
                    issue_type="verified_issue",
                    severity="Critical",
                    explanation="ATS parsers use email as the primary candidate identifier to link profiles and send communications.",
                    evidence=[email or "No email detected in contact block"],
                    suggested_fix="Place a standard email address (e.g. name@example.com) clearly in the header.",
                )
            )

        # Phone (+4)
        if phone and len(re.sub(r"\D", "", phone)) >= 7:
            score += 4.0
        else:
            issues.append(
                ATSIssue(
                    id="contact_missing_phone",
                    category="contact_info",
                    category_name=ATS_CATEGORIES["contact_info"]["name"],
                    title="Missing or Incomplete Phone Number",
                    issue_type="verified_issue",
                    severity="Critical",
                    explanation="Recruiters require a valid phone number for candidate outreach and automated SMS screening.",
                    evidence=[phone or "No valid phone number detected"],
                    suggested_fix="Include a phone number with area code in your contact header.",
                )
            )

        # Location (+3)
        if location and len(location.strip()) > 2:
            score += 3.0
        else:
            issues.append(
                ATSIssue(
                    id="contact_missing_location",
                    category="contact_info",
                    category_name=ATS_CATEGORIES["contact_info"]["name"],
                    title="Missing Candidate Location",
                    issue_type="verified_issue",
                    severity="Warning",
                    explanation="Location filters (City, State / Country) are frequently applied by ATS algorithms to match local or regional reqs.",
                    evidence=["No geographic location detected"],
                    suggested_fix="Add your City and State/Country (e.g., 'San Francisco, CA' or 'London, UK'). Full street address is not needed.",
                )
            )

        # Professional Link (+3)
        if linkedin or github or portfolio:
            score += 3.0
        else:
            issues.append(
                ATSIssue(
                    id="contact_missing_links",
                    category="contact_info",
                    category_name=ATS_CATEGORIES["contact_info"]["name"],
                    title="No Professional Profile Link Found",
                    issue_type="verified_issue",
                    severity="Info",
                    explanation="Recruiters look for clickable LinkedIn, GitHub, or portfolio links to verify credentials.",
                    evidence=["No LinkedIn, GitHub, or portfolio URL found"],
                    suggested_fix="Add a clean LinkedIn or GitHub URL to your contact header.",
                )
            )

        status = "Pass" if score >= 12.0 else "Warning" if score >= 8.0 else "Fail"
        feedback = f"Contact information earns {score:.1f}/15.0 pts."
        return score, status, feedback

    def _evaluate_sections(
        self,
        resume: Any,
        cleaned_text: Optional[str],
        issues: List[ATSIssue],
        risks: List[ATSIssue],
    ) -> Tuple[List[SectionDetectionItem], List[str], float, str, str]:
        sections: List[SectionDetectionItem] = []
        missing_sections: List[str] = []

        # Check structured presence
        has_contact = bool(getattr(resume, "personal_information", None))
        has_summary = bool(
            getattr(resume.personal_information, "summary", None)
            if getattr(resume, "personal_information", None) else False
        )
        has_exp = bool(getattr(resume, "experience_records", None) and len(resume.experience_records) > 0)
        has_edu = bool(getattr(resume, "education_records", None) and len(resume.education_records) > 0)
        has_skills = bool(getattr(resume, "resume_skills", None) and len(resume.resume_skills) > 0)
        has_projects = bool(getattr(resume, "projects", None) and len(resume.projects) > 0)
        has_certs = bool(
            (getattr(resume, "certifications", None) and len(resume.certifications) > 0) or
            (getattr(resume, "achievements", None) and len(resume.achievements) > 0)
        )

        section_presence = [
            ("contact_info", "Contact Information", has_contact, True),
            ("summary", "Professional Summary", has_summary, False),
            ("experience", "Work Experience", has_exp, True),
            ("education", "Education", has_edu, True),
            ("skills", "Technical Skills", has_skills, True),
            ("projects", "Projects", has_projects, False),
            ("certifications", "Certifications & Achievements", has_certs, False),
        ]

        # Scan text for potential non-standard headings
        text_lines = (cleaned_text or "").split("\n")
        detected_text_headings: Dict[str, str] = {}
        unusual_headings_found: List[str] = []

        for line in text_lines:
            stripped = line.strip().rstrip(":")
            if 3 <= len(stripped) <= 40:
                for sec_key, pattern in STANDARD_HEADINGS_REGEX.items():
                    if pattern.match(stripped):
                        detected_text_headings[sec_key] = stripped
                # Check for creative non-standard headings
                if re.match(r"^(where\s+i've\s+been|my\s+journey|things\s+i\s+know|past\s+adventures|life\s+story)\b", stripped, re.IGNORECASE):
                    unusual_headings_found.append(stripped)

        if unusual_headings_found:
            risks.append(
                ATSIssue(
                    id="unusual_section_headings",
                    category="standard_sections",
                    category_name=ATS_CATEGORIES["standard_sections"]["name"],
                    title="Unusual Section Heading Detected",
                    issue_type="formatting_risk",
                    severity="Warning",
                    explanation="Older ATS parsers look for standard headings (e.g. 'Work Experience', 'Education'). Creative headings risk section omission.",
                    evidence=unusual_headings_found[:3],
                    suggested_fix="Replace creative titles with conventional ATS headers: 'Experience', 'Education', 'Skills'.",
                )
            )

        core_count = 0
        for key, name, present, is_core in section_presence:
            heading = detected_text_headings.get(key)
            if present:
                sections.append(
                    SectionDetectionItem(
                        section_key=key,
                        section_name=name,
                        detected=True,
                        heading_text=heading or name,
                        is_standard_heading=True,
                        status="Standard",
                    )
                )
                if is_core:
                    core_count += 1
            else:
                sections.append(
                    SectionDetectionItem(
                        section_key=key,
                        section_name=name,
                        detected=False,
                        heading_text=None,
                        is_standard_heading=False,
                        status="Missing",
                    )
                )
                missing_sections.append(name)
                if is_core:
                    issues.append(
                        ATSIssue(
                            id=f"missing_section_{key}",
                            category="standard_sections",
                            category_name=ATS_CATEGORIES["standard_sections"]["name"],
                            title=f"Missing Core Section: {name}",
                            issue_type="verified_issue",
                            severity="Critical" if key in ["experience", "education", "skills"] else "Warning",
                            explanation=f"The {name} section is expected by virtually all ATS parsers and hiring managers.",
                            evidence=[f"No records found for {name}"],
                            suggested_fix=f"Add a distinct '{name}' section with clearly labeled headers.",
                        )
                    )

        # 4 core sections * 3.75 = 15 points
        score = min(15.0, core_count * 3.75)
        status = "Pass" if score >= 12.0 else "Warning" if score >= 7.5 else "Fail"
        feedback = f"Detected {len([s for s in sections if s.detected])} sections ({core_count}/4 core sections present)."
        return sections, missing_sections, score, status, feedback

    def _evaluate_experience(
        self, resume: Any, issues: List[ATSIssue]
    ) -> Tuple[float, str, str]:
        score = 0.0
        records = getattr(resume, "experience_records", []) or []

        if not records:
            issues.append(
                ATSIssue(
                    id="exp_no_records",
                    category="experience_formatting",
                    category_name=ATS_CATEGORIES["experience_formatting"]["name"],
                    title="No Work Experience Records Found",
                    issue_type="verified_issue",
                    severity="Critical",
                    explanation="ATS parsers heavily index job titles, tenure, and employer names to score relevance for open positions.",
                    evidence=["No experience entries parsed"],
                    suggested_fix="Add an 'Experience' or 'Work Experience' section with role title, company name, and employment dates.",
                )
            )
            return 0.0, "Fail", "No work experience records found."

        # Titles (+5)
        has_titles = any(getattr(r, "job_title", None) or getattr(r, "title", None) for r in records)
        if has_titles:
            score += 5.0
        else:
            issues.append(
                ATSIssue(
                    id="exp_missing_titles",
                    category="experience_formatting",
                    category_name=ATS_CATEGORIES["experience_formatting"]["name"],
                    title="Missing Clear Job Titles",
                    issue_type="verified_issue",
                    severity="Critical",
                    explanation="Job titles are primary search vectors for ATS talent matching.",
                    evidence=["Entries lack explicit job titles"],
                    suggested_fix="Format each experience entry starting with standard job title (e.g. 'Software Engineer').",
                )
            )

        # Companies (+5)
        has_comp = any(getattr(r, "company_name", None) or getattr(r, "company", None) for r in records)
        if has_comp:
            score += 5.0
        else:
            issues.append(
                ATSIssue(
                    id="exp_missing_company",
                    category="experience_formatting",
                    category_name=ATS_CATEGORIES["experience_formatting"]["name"],
                    title="Missing Company / Employer Names",
                    issue_type="verified_issue",
                    severity="Warning",
                    explanation="ATS parsers verify company background to calculate industry tenure.",
                    evidence=["Entries lack distinct employer names"],
                    suggested_fix="Clearly separate company name from the role title.",
                )
            )

        # Dates (+5)
        has_dates = any(getattr(r, "start_date", None) for r in records)
        if has_dates:
            score += 5.0
        else:
            issues.append(
                ATSIssue(
                    id="exp_missing_dates",
                    category="experience_formatting",
                    category_name=ATS_CATEGORIES["experience_formatting"]["name"],
                    title="Missing Employment Dates",
                    issue_type="verified_issue",
                    severity="Warning",
                    explanation="Without dates (Month Year - Month Year), ATS parsers cannot calculate years of experience.",
                    evidence=["Roles lack clear start and end dates"],
                    suggested_fix="Include dates for every role, e.g. 'Jan 2022 - Present' or '2021 - 2023'.",
                )
            )

        # Bullet points (+5)
        has_bullets = any(
            (getattr(r, "key_responsibilities", None) and len(r.key_responsibilities) > 0) or
            len(getattr(r, "description", "") or "") > 30
            for r in records
        )
        if has_bullets:
            score += 5.0
        else:
            issues.append(
                ATSIssue(
                    id="exp_no_bullets",
                    category="experience_formatting",
                    category_name=ATS_CATEGORIES["experience_formatting"]["name"],
                    title="Sparse Experience Descriptions",
                    issue_type="verified_issue",
                    severity="Warning",
                    explanation="ATS parsers extract keywords from achievement bullet points.",
                    evidence=["Work entries lack bullet points or descriptive text"],
                    suggested_fix="Provide 2-5 bullet points per role highlighting measurable contributions.",
                )
            )

        status = "Pass" if score >= 15.0 else "Warning" if score >= 10.0 else "Fail"
        feedback = f"Work experience structure scored {score:.1f}/20.0 pts across {len(records)} roles."
        return score, status, feedback

    def _evaluate_education(
        self, resume: Any, issues: List[ATSIssue]
    ) -> Tuple[float, str, str]:
        score = 0.0
        records = getattr(resume, "education_records", []) or []

        if not records:
            issues.append(
                ATSIssue(
                    id="edu_no_records",
                    category="education_structure",
                    category_name=ATS_CATEGORIES["education_structure"]["name"],
                    title="No Education Records Found",
                    issue_type="verified_issue",
                    severity="Warning",
                    explanation="ATS requirements often filter for minimum degree levels (e.g. B.S., M.S., High School).",
                    evidence=["No education entries detected"],
                    suggested_fix="Add an 'Education' section specifying degree and university.",
                )
            )
            return 0.0, "Fail", "No education records found."

        # Degree (+4)
        has_degree = any(getattr(r, "degree_name", None) or getattr(r, "degree", None) for r in records)
        if has_degree:
            score += 4.0
        else:
            issues.append(
                ATSIssue(
                    id="edu_missing_degree",
                    category="education_structure",
                    category_name=ATS_CATEGORIES["education_structure"]["name"],
                    title="Missing Degree Title",
                    issue_type="verified_issue",
                    severity="Warning",
                    explanation="ATS parsers search for degree keywords (Bachelor, Master, B.S., B.A.).",
                    evidence=["Education record lacks degree title"],
                    suggested_fix="Specify standard degree naming (e.g. 'Bachelor of Science in Computer Science').",
                )
            )

        # Institution (+4)
        has_inst = any(getattr(r, "institution_name", None) or getattr(r, "institution", None) for r in records)
        if has_inst:
            score += 4.0
        else:
            issues.append(
                ATSIssue(
                    id="edu_missing_institution",
                    category="education_structure",
                    category_name=ATS_CATEGORIES["education_structure"]["name"],
                    title="Missing University / Institution Name",
                    issue_type="verified_issue",
                    severity="Warning",
                    explanation="Institutional accreditation is indexed during candidate background verification.",
                    evidence=["Education record lacks institution name"],
                    suggested_fix="State the full college or institution name clearly.",
                )
            )

        # Dates (+2)
        has_dates = any(getattr(r, "end_date", None) or getattr(r, "graduation_year", None) for r in records)
        if has_dates:
            score += 2.0
        else:
            issues.append(
                ATSIssue(
                    id="edu_missing_dates",
                    category="education_structure",
                    category_name=ATS_CATEGORIES["education_structure"]["name"],
                    title="Missing Graduation or Attendance Year",
                    issue_type="verified_issue",
                    severity="Info",
                    explanation="Graduation year establishes candidate timeline and graduation status.",
                    evidence=["Education record lacks graduation year"],
                    suggested_fix="Include graduation year or expected completion date (e.g., 'May 2024').",
                )
            )

        status = "Pass" if score >= 8.0 else "Warning" if score >= 4.0 else "Fail"
        feedback = f"Education formatting scored {score:.1f}/10.0 pts across {len(records)} entries."
        return score, status, feedback

    def _evaluate_skills(
        self, resume: Any, issues: List[ATSIssue]
    ) -> Tuple[float, str, str]:
        score = 0.0
        skills = getattr(resume, "resume_skills", []) or []
        count = len(skills)

        if count >= 3:
            score += 5.0
        else:
            issues.append(
                ATSIssue(
                    id="skills_too_few",
                    category="skills_presentation",
                    category_name=ATS_CATEGORIES["skills_presentation"]["name"],
                    title="Few or Missing Technical Skills",
                    issue_type="verified_issue",
                    severity="Critical",
                    explanation="ATS ranking algorithms calculate query match percentage against required skill keywords.",
                    evidence=[f"Only {count} skill(s) detected"],
                    suggested_fix="Include a dedicated 'Skills' section listing 8-20 relevant technologies.",
                )
            )

        # Organization & categorization (+5)
        categories = set(getattr(s, "category", "general") for s in skills)
        if len(categories) > 1 or count >= 8:
            score += 5.0
        else:
            score += 2.5

        # Standard terminology (+5)
        canonical_count = sum(1 for s in skills if getattr(s, "canonical_name", None))
        if canonical_count >= 3:
            score += 5.0
        else:
            score += 2.5

        status = "Pass" if score >= 12.0 else "Warning" if score >= 7.5 else "Fail"
        feedback = f"Skills section scored {score:.1f}/15.0 pts ({count} skills detected)."
        return score, status, feedback

    def _evaluate_summary(
        self, resume: Any, issues: List[ATSIssue]
    ) -> Tuple[float, str, str]:
        p_info = getattr(resume, "personal_information", None)
        summary = (getattr(p_info, "summary", "") or "").strip() if p_info else ""

        if not summary:
            issues.append(
                ATSIssue(
                    id="summary_missing",
                    category="professional_summary",
                    category_name=ATS_CATEGORIES["professional_summary"]["name"],
                    title="Missing Professional Summary",
                    issue_type="verified_issue",
                    severity="Warning",
                    explanation="A well-crafted summary allows ATS algorithms to immediately classify your primary role and specialization.",
                    evidence=["No summary paragraph detected"],
                    suggested_fix="Add a 2-4 sentence executive summary highlighting your role, domain depth, and top skills.",
                )
            )
            return 0.0, "Fail", "Missing professional summary (0.0/10.0 pts)."

        words = len(summary.split())
        score = 5.0  # Present

        if 25 <= words <= 150:
            score += 5.0
            feedback = f"Optimal summary length ({words} words)."
        elif words < 25:
            score += 2.5
            feedback = f"Summary is short ({words} words; recommended 30-100 words)."
        else:
            score += 3.0
            feedback = f"Summary is lengthy ({words} words; recommended under 150 words)."

        status = "Pass" if score >= 8.0 else "Warning"
        return score, status, feedback

    def _evaluate_projects_certifications(
        self, resume: Any, issues: List[ATSIssue]
    ) -> Tuple[float, str, str]:
        score = 0.0
        projects = getattr(resume, "projects", []) or []
        certs = getattr(resume, "certifications", []) or []
        achievements = getattr(resume, "achievements", []) or []

        has_proj = len(projects) > 0
        has_cred = (len(certs) + len(achievements)) > 0

        if has_proj:
            score += 3.0
        if has_cred:
            score += 2.0

        if not has_proj and not has_cred:
            issues.append(
                ATSIssue(
                    id="credentials_none",
                    category="credentials_projects",
                    category_name=ATS_CATEGORIES["credentials_projects"]["name"],
                    title="No Projects or Certifications Found",
                    issue_type="verified_issue",
                    severity="Info",
                    explanation="Verified projects and industry certifications provide secondary keyword validation.",
                    evidence=["No project or certification entries detected"],
                    suggested_fix="List notable technical projects with technologies used and links.",
                )
            )

        status = "Pass" if score >= 3.0 else "Warning"
        feedback = f"Projects & Credentials earned {score:.1f}/5.0 pts ({len(projects)} projects, {len(certs)} certs)."
        return score, status, feedback

    def _evaluate_file_layout(
        self,
        resume: Any,
        file_path: Optional[Path],
        cleaned_text: Optional[str],
        risks: List[ATSIssue],
    ) -> Tuple[float, str, str]:
        score = 10.0
        notes = []

        # If file_path is available, run deep binary layout inspection
        if file_path and file_path.exists():
            ext = file_path.suffix.lower()
            if ext == ".pdf":
                try:
                    doc = fitz.open(str(file_path))
                    page_count = len(doc)

                    # 1. Page count check
                    if page_count > 3:
                        score -= 2.0
                        risks.append(
                            ATSIssue(
                                id="layout_length_excessive",
                                category="formatting_parsing_safety",
                                category_name=ATS_CATEGORIES["formatting_parsing_safety"]["name"],
                                title=f"Excessive Document Length ({page_count} pages)",
                                issue_type="formatting_risk",
                                severity="Warning",
                                explanation="Standard ATS resumes are 1-2 pages. Documents exceeding 3 pages suffer drop-offs in recruiter reviews.",
                                evidence=[f"Page count: {page_count}"],
                                suggested_fix="Condense experience to 1-2 pages focusing on your last 10 years of work.",
                            )
                        )
                        notes.append(f"{page_count} pages (length warning)")

                    # 2. Text layer readability
                    total_chars = sum(len(page.get_text()) for page in doc)
                    if total_chars < 80:
                        score -= 5.0
                        risks.append(
                            ATSIssue(
                                id="layout_unreadable_text",
                                category="formatting_parsing_safety",
                                category_name=ATS_CATEGORIES["formatting_parsing_safety"]["name"],
                                title="Scanned or Unreadable PDF Text Layer",
                                issue_type="formatting_risk",
                                severity="Critical",
                                explanation="ATS parsers cannot read scanned images without an embedded text layer. Resume will be rejected as empty.",
                                evidence=[f"Only {total_chars} text characters found across document"],
                                suggested_fix="Export resume as text-based PDF directly from Word, Google Docs, or LaTeX.",
                            )
                        )
                        notes.append("Unreadable text layer")

                    # 3. Tables check
                    has_complex_tables = False
                    for page in doc:
                        try:
                            tables = page.find_tables()
                            if tables and len(tables.tables) > 1:
                                has_complex_tables = True
                                break
                        except Exception:
                            pass

                    if has_complex_tables:
                        score -= 3.0
                        risks.append(
                            ATSIssue(
                                id="layout_complex_tables",
                                category="formatting_parsing_safety",
                                category_name=ATS_CATEGORIES["formatting_parsing_safety"]["name"],
                                title="Complex Multi-Cell Tables Detected",
                                issue_type="formatting_risk",
                                severity="Warning",
                                explanation="Tables can cause ATS parsers to scramble column reading order or skip table cells entirely.",
                                evidence=["Embedded tables detected in PDF"],
                                suggested_fix="Use clean left-aligned text with standard tabs/margins rather than nested tables.",
                            )
                        )
                        notes.append("Tables detected")

                    # 4. Multi-column layout check
                    has_multi_column = False
                    for page in doc:
                        blocks = page.get_text("blocks")
                        # check for distinct text blocks with significant horizontal displacement on similar vertical lines
                        col_left = [b for b in blocks if len(b) > 4 and b[0] < 220 and len(b[4].strip()) > 15]
                        col_right = [b for b in blocks if len(b) > 4 and b[0] > 280 and len(b[4].strip()) > 15]
                        if len(col_left) >= 2 and len(col_right) >= 2:
                            # check vertical overlap
                            overlap = False
                            for bl in col_left:
                                for br in col_right:
                                    if max(bl[1], br[1]) < min(bl[3], br[3]):
                                        overlap = True
                                        break
                                if overlap:
                                    break
                            if overlap:
                                has_multi_column = True
                                break

                    if has_multi_column:
                        score -= 3.0
                        risks.append(
                            ATSIssue(
                                id="layout_multi_column",
                                category="formatting_parsing_safety",
                                category_name=ATS_CATEGORIES["formatting_parsing_safety"]["name"],
                                title="Multi-Column Layout Detected",
                                issue_type="formatting_risk",
                                severity="Warning",
                                explanation="Multi-column resumes often get read horizontally across columns by ATS parsers, mingling disparate sections.",
                                evidence=["Side-by-side columns detected in layout"],
                                suggested_fix="Switch to a clean single-column format for optimal ATS parsing fidelity.",
                            )
                        )
                        notes.append("Multi-column layout detected")

                    doc.close()
                except Exception as e:
                    logger.warning("Error inspecting PDF layout: %s", e)

            elif ext == ".docx" and docx is not None:
                try:
                    d = docx.Document(str(file_path))
                    if len(d.tables) > 1:
                        score -= 2.0
                        risks.append(
                            ATSIssue(
                                id="layout_docx_tables",
                                category="formatting_parsing_safety",
                                category_name=ATS_CATEGORIES["formatting_parsing_safety"]["name"],
                                title="Multiple Tables Detected in DOCX",
                                issue_type="formatting_risk",
                                severity="Warning",
                                explanation="Tables in Word documents may scramble sequential text extraction in legacy parsers.",
                                evidence=[f"{len(d.tables)} tables in document"],
                                suggested_fix="Use standard paragraph margins instead of tables for layout.",
                            )
                        )
                        notes.append("DOCX tables detected")
                except Exception as e:
                    logger.warning("Error inspecting DOCX layout: %s", e)

        # Fallback check on cleaned_text if no file path
        if not file_path and cleaned_text:
            if len(cleaned_text.strip()) < 100:
                score -= 5.0
                risks.append(
                    ATSIssue(
                        id="layout_low_content",
                        category="formatting_parsing_safety",
                        category_name=ATS_CATEGORIES["formatting_parsing_safety"]["name"],
                        title="Low Content Density",
                        issue_type="formatting_risk",
                        severity="Warning",
                        explanation="Extracted text is unusually sparse.",
                        evidence=[f"{len(cleaned_text)} characters in text"],
                        suggested_fix="Ensure all sections contain complete text details.",
                    )
                )

        score = max(0.0, score)
        status = "Pass" if score >= 8.0 else "Warning" if score >= 5.0 else "Fail"
        feedback = f"Layout safety scored {score:.1f}/10.0 pts. " + ("; ".join(notes) if notes else "Clean single-column structure.")
        return score, status, feedback

    # =========================================================================
    # KEYWORDS & ACTION VERBS
    # =========================================================================

    def _extract_keyword_findings(
        self, resume: Any, cleaned_text: Optional[str]
    ) -> KeywordFindings:
        skills = getattr(resume, "resume_skills", []) or []
        tech_keywords = [
            getattr(s, "canonical_name", None) or getattr(s, "original_name", str(s))
            for s in skills[:25]
        ]

        text = (cleaned_text or "").lower()
        found_verbs: List[str] = []
        for verb in ACTION_VERBS:
            if re.search(r"\b" + verb + r"\b", text):
                found_verbs.append(verb.capitalize())

        # Recommend high-frequency verbs if underrepresented
        missing_verbs = [v.capitalize() for v in ACTION_VERBS if v.capitalize() not in found_verbs][:5]

        count = len(tech_keywords) + len(found_verbs)
        density_note = (
            "Strong keyword density with measurable action verbs."
            if len(found_verbs) >= 4 and len(tech_keywords) >= 8
            else "Consider incorporating more high-impact action verbs and industry-standard technical keywords."
        )

        return KeywordFindings(
            total_detected_keywords=count,
            top_technical_keywords=tech_keywords[:15],
            top_action_verbs=found_verbs,
            recommended_keywords=missing_verbs,
            keyword_density_note=density_note,
        )


ats_deterministic_scorer = ATSDeterministicScorer()
