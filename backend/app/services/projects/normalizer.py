"""
Project Normalizer
Phase 3 | Feature 18: Project Intelligence
Handles title cleaning, URL categorization, and category validation.
"""

import re
import unicodedata
from typing import Optional, Dict, List, Tuple
from app.schemas.projects import ProjectLinkData

PROJECT_CATEGORIES = {
    "academic",
    "personal",
    "hackathon",
    "research",
    "open_source",
    "internship",
    "professional",
    "freelance",
    "other",
}


def normalize_project_title(raw_title: Optional[str]) -> str:
    """
    Standardizes a project title by stripping enclosing quotes, special brackets,
    redundant whitespace, and trailing separator characters.
    """
    if not raw_title:
        return "Untitled Project"

    title = unicodedata.normalize("NFKC", str(raw_title).strip())
    # Strip quotes, markdown headers, and bullets (including unicode smart quotes)
    title = re.sub(r"^[\#\*\-•·\s\"\'\u201c\u201d\u2018\u2019]+", "", title)
    title = re.sub(r"[\"\'\u201c\u201d\u2018\u2019\s]+$", "", title)
    # Strip pipe or dash trailing suffixes if they contain technology or links
    # e.g. "Nexora AI | Python, React" -> "Nexora AI"
    pipe_match = re.search(r"^(.*?)\s+[\|\–\-]\s+(?:python|react|fastapi|node|java|c\+\+|technolog|github|http).*?$", title, re.IGNORECASE)
    if pipe_match:
        title = pipe_match.group(1).strip()

    title = re.sub(r"\s+", " ", title).strip()
    return title or "Untitled Project"


def classify_project_category(
    text: str,
    section_name: Optional[str] = None,
) -> str:
    """
    Infers project category based on section context and text keywords.
    Defaults to 'other' when evidence is insufficient.
    """
    corpus = f" {section_name or ''} {text} ".lower()

    sec_lower = (section_name or "").lower()
    if any(kw in sec_lower for kw in ("academic", "coursework", "university", "college", "capstone")):
        if not re.search(r"\b(?:published\s+in|ieee|arxiv|journal\s+paper)\b", corpus):
            return "academic"

    if re.search(r"\b(?:hackathon|smart india hackathon|mlh|hack\w+|won\s+\d+|runner\s*up)\b", corpus):
        return "hackathon"
    if re.search(r"\b(?:research\s+project|published|ieee|arxiv|journal|thesis|dissertation)\b", corpus):
        return "research"
    if re.search(r"\b(?:open\s*source|github\s+contribut|pr\s+merged|pypi|npm\s+package)\b", corpus):
        return "open_source"
    if re.search(r"\b(?:internship|intern\s+project|capstone\s+at\s+company)\b", corpus):
        return "internship"
    if re.search(r"\b(?:academic|coursework|university|college|bachelor|master|semester|final\s+year)\b", corpus):
        return "academic"
    if re.search(r"\b(?:freelance|client\s+project|upwork|contract\s+work)\b", corpus):
        return "freelance"
    if re.search(r"\b(?:personal\s+project|side\s+project|hobby|pet\s+project|self-developed)\b", corpus):
        return "personal"
    if re.search(r"\b(?:professional|enterprise|production\s+system|company\s+project)\b", corpus):
        return "professional"

    return "other"


def extract_and_categorize_urls(text: str) -> List[ProjectLinkData]:
    """
    Detects URLs in project text and tags them (github, demo, website, docs, other).
    """
    if not text:
        return []

    url_pattern = r"https?://[^\s\)\],;\"']+"
    matches = re.findall(url_pattern, text)
    links: List[ProjectLinkData] = []
    seen = set()

    for url in matches:
        clean_url = url.rstrip(".")
        if clean_url in seen:
            continue
        seen.add(clean_url)

        url_lower = clean_url.lower()
        if "github.com" in url_lower or "gitlab.com" in url_lower or "bitbucket.org" in url_lower:
            links.append(ProjectLinkData(type="github", url=clean_url))
        elif any(kw in url_lower for kw in ("demo", "vercel.app", "netlify.app", "herokuapp.com", "render.com", "awsapprunner")):
            links.append(ProjectLinkData(type="demo", url=clean_url))
        elif any(kw in url_lower for kw in ("docs", "readme", "notion.site", "gitbook")):
            links.append(ProjectLinkData(type="docs", url=clean_url))
        else:
            links.append(ProjectLinkData(type="website", url=clean_url))

    return links
