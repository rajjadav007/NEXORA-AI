"""
HTML & Structured Metadata Extractor for Job Description URL Import
Phase 6 | Feature 34: Job Description URL Import
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional

from bs4 import BeautifulSoup

from app.services.job_import.fetcher import JobImportBlockedError, JobImportError
from app.schemas.job_description import ALLOWED_EMPLOYMENT_TYPES, JD_MAX_LENGTH, JD_MIN_LENGTH


class JobImportExtractionError(JobImportError):
    def __init__(self, message: str):
        super().__init__(message, status_code=422, code="EXTRACTION_FAILED")


@dataclass
class ExtractedJobData:
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_required: Optional[str] = None
    description: str = ""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    salary_info: Optional[str] = None
    extraction_method: str = "html"


_EMPLOYMENT_MAP = {
    "full_time": "Full-time",
    "full-time": "Full-time",
    "full time": "Full-time",
    "part_time": "Part-time",
    "part-time": "Part-time",
    "part time": "Part-time",
    "contractor": "Contract",
    "contract": "Contract",
    "intern": "Internship",
    "internship": "Internship",
    "temporary": "Temporary",
    "temp": "Temporary",
    "freelance": "Freelance",
}

_WALL_MARKERS = (
    "verify you are human",
    "g-recaptcha",
    "hcaptcha",
    "cf-turnstile",
    "please complete the security check",
    "authwall",
    "sign in to view this job",
    "join linkedin to see",
    "enable javascript and cookies to continue",
)


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in value.splitlines()]
    collapsed = "\n".join(line for line in lines if line)
    return collapsed.strip()


def _html_fragment_to_text(raw_html: str) -> str:
    if not raw_html:
        return ""
    frag = BeautifulSoup(raw_html, "html.parser")
    for tag in frag(["script", "style", "noscript", "iframe", "svg", "object", "embed"]):
        tag.decompose()
    return _clean_text(frag.get_text(separator="\n"))


def _normalize_employment_type(value: Any) -> Optional[str]:
    if isinstance(value, list) and value:
        value = value[0]
    if not isinstance(value, str):
        return None
    cleaned = value.strip().lower()
    if cleaned in _EMPLOYMENT_MAP:
        return _EMPLOYMENT_MAP[cleaned]
    for canonical in ALLOWED_EMPLOYMENT_TYPES:
        if canonical.lower() == cleaned:
            return canonical
    return None


def _extract_location_from_jsonld(data: dict) -> Optional[str]:
    if str(data.get("jobLocationType", "")).upper() == "TELECOMMUTE":
        return "Remote"

    loc = data.get("jobLocation")
    if isinstance(loc, list) and loc:
        loc = loc[0]
    if isinstance(loc, str):
        return loc.strip() or None
    if isinstance(loc, dict):
        addr = loc.get("address")
        if isinstance(addr, str):
            return addr.strip() or None
        if isinstance(addr, dict):
            parts = [
                addr.get("addressLocality"),
                addr.get("addressRegion"),
                addr.get("addressCountry"),
            ]
            joined = ", ".join(str(p).strip() for p in parts if p and str(p).strip())
            if joined:
                return joined
        name = loc.get("name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    return None


def _extract_salary_from_jsonld(data: dict) -> Optional[str]:
    salary = data.get("baseSalary")
    if isinstance(salary, str) and salary.strip():
        return salary.strip()
    if not isinstance(salary, dict):
        return None

    currency = str(salary.get("currency") or "").strip()
    val = salary.get("value")
    if isinstance(val, dict):
        unit = str(val.get("unitText") or "").strip().lower()
        unit_suffix = f" / {unit}" if unit else ""
        min_v = val.get("minValue")
        max_v = val.get("maxValue")
        exact_v = val.get("value")
        if min_v is not None and max_v is not None:
            return f"{currency} {min_v} - {max_v}{unit_suffix}".strip()
        if exact_v is not None:
            return f"{currency} {exact_v}{unit_suffix}".strip()
    elif val is not None:
        return f"{currency} {val}".strip()
    return None


def _extract_experience_from_jsonld(data: dict) -> Optional[str]:
    exp = data.get("experienceRequirements")
    if isinstance(exp, str) and exp.strip():
        return exp.strip()[:100]
    if isinstance(exp, dict):
        months = exp.get("monthsOfExperience")
        if isinstance(months, (int, float)) and months > 0:
            years = round(months / 12, 1)
            return f"{int(years) if years.is_integer() else years}+ years"
    return None


def _extract_skills_list(value: Any) -> List[str]:
    if isinstance(value, str):
        return [s.strip() for s in re.split(r"[,;\n]", value) if s.strip()][:25]
    if isinstance(value, list):
        items = []
        for item in value:
            if isinstance(item, str) and item.strip():
                items.append(item.strip())
            elif isinstance(item, dict) and item.get("name"):
                items.append(str(item["name"]).strip())
        return items[:25]
    return []


def _find_job_posting_jsonld(soup: BeautifulSoup) -> Optional[dict]:
    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\+json", re.I)}):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue

        candidates: List[dict] = []
        if isinstance(parsed, dict):
            if "@graph" in parsed and isinstance(parsed["@graph"], list):
                candidates.extend(item for item in parsed["@graph"] if isinstance(item, dict))
            candidates.append(parsed)
        elif isinstance(parsed, list):
            candidates.extend(item for item in parsed if isinstance(item, dict))

        for item in candidates:
            item_type = item.get("@type")
            if item_type == "JobPosting" or (isinstance(item_type, list) and "JobPosting" in item_type):
                return item
    return None


def _extract_regex_heuristics(text: str) -> tuple[Optional[str], Optional[str]]:
    exp_match = re.search(
        r"\b(\d+\s*(?:\+|to|-)\s*\d*\s*years?\s+(?:of\s+)?experience|\d+\+\s*years?\b)",
        text,
        re.IGNORECASE,
    )
    experience = exp_match.group(1).strip()[:100] if exp_match else None

    salary_match = re.search(
        r"((?:\$|USD|EUR|GBP|INR|₹)\s?\d[\d,]*(?:\s?(?:k|K|LPA))?(?:\s?[-–to]+\s?(?:\$|USD|EUR|GBP|INR|₹)?\s?\d[\d,]*(?:\s?(?:k|K|LPA))?)?(?:\s*(?:/|per)\s*(?:year|yr|month|hr|hour|annum))?)",
        text,
        re.IGNORECASE,
    )
    salary = salary_match.group(1).strip()[:255] if salary_match else None
    return experience, salary


def extract_job_description_from_html(html: str) -> ExtractedJobData:
    """
    Sanitizes HTML and extracts structured job information using JSON-LD JobPosting,
    Open Graph metadata, and semantic HTML fallbacks.
    """
    if not html or not html.strip():
        raise JobImportExtractionError("Retrieved page is empty.")

    soup = BeautifulSoup(html, "html.parser")
    jsonld = _find_job_posting_jsonld(soup)

    # Extract Open Graph / meta tags before stripping tags
    og_title = None
    og_site = None
    og_desc = None
    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").lower()
        content = (meta.get("content") or "").strip()
        if not content:
            continue
        if prop in ("og:title", "twitter:title") and not og_title:
            og_title = content
        elif prop == "og:site_name" and not og_site:
            og_site = content
        elif prop in ("og:description", "description") and not og_desc:
            og_desc = content

    page_title = _clean_text(soup.title.string) if soup.title and soup.title.string else None

    # Strip all executable/non-content tags
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "object", "embed"]):
        tag.decompose()

    body_text = _clean_text(soup.get_text(separator="\n"))
    lower_body = f"{page_title or ''} {body_text[:3000]}".lower()

    if not jsonld and any(marker in lower_body for marker in _WALL_MARKERS):
        raise JobImportBlockedError(
            "This page is protected by a login wall or CAPTCHA/anti-bot check. Please copy and paste the job description manually."
        )

    result = ExtractedJobData()

    if jsonld:
        result.extraction_method = "json_ld"
        result.job_title = _clean_text(str(jsonld.get("title") or "")) or None

        org = jsonld.get("hiringOrganization")
        if isinstance(org, dict):
            result.company_name = _clean_text(str(org.get("name") or "")) or None
        elif isinstance(org, str):
            result.company_name = _clean_text(org) or None

        result.location = _extract_location_from_jsonld(jsonld)
        result.employment_type = _normalize_employment_type(jsonld.get("employmentType"))
        result.experience_required = _extract_experience_from_jsonld(jsonld)
        result.salary_info = _extract_salary_from_jsonld(jsonld)
        result.description = _html_fragment_to_text(str(jsonld.get("description") or ""))
        result.required_skills = _extract_skills_list(jsonld.get("skills"))
        result.preferred_skills = _extract_skills_list(jsonld.get("qualifications"))
    else:
        result.extraction_method = "html_fallback"

    # Fallbacks from semantic HTML / Open Graph
    if not result.job_title:
        h1 = soup.find("h1")
        result.job_title = _clean_text(h1.get_text()) if h1 else (og_title or page_title)

    if not result.company_name and og_site:
        result.company_name = og_site

    if not result.description:
        for selector in (
            soup.find(attrs={"class": re.compile(r"job[-_]?description|description__text", re.I)}),
            soup.find(attrs={"id": re.compile(r"job[-_]?description", re.I)}),
            soup.find("main"),
            soup.find("article"),
        ):
            if selector:
                candidate = _clean_text(selector.get_text(separator="\n"))
                if len(candidate) >= JD_MIN_LENGTH:
                    result.description = candidate
                    break

    if not result.description and len(body_text) >= JD_MIN_LENGTH:
        result.description = body_text
    elif not result.description and og_desc and len(og_desc) >= JD_MIN_LENGTH:
        result.description = og_desc

    if not result.description or len(result.description.strip()) < JD_MIN_LENGTH:
        raise JobImportExtractionError(
            "Could not extract a complete job description from this URL. Please use the manual input tab."
        )

    if len(result.description) > JD_MAX_LENGTH:
        result.description = result.description[:JD_MAX_LENGTH].rstrip()

    if not result.experience_required or not result.salary_info:
        exp_h, sal_h = _extract_regex_heuristics(result.description)
        if not result.experience_required:
            result.experience_required = exp_h
        if not result.salary_info:
            result.salary_info = sal_h

    return result
