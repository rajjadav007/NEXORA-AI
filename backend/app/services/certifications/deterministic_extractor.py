"""
Deterministic Extractor for Certifications and Achievements
Phase 3 | Feature 19: Certifications & Achievements Intelligence
Extracts structured certification and achievement fields using regex, known issuer/event registries,
dates, URLs, credential IDs, and strict ranking terminology.
"""

import re
from typing import Optional, Dict, Any, List, Tuple

# Known Certification Authorities and Issuers
KNOWN_ISSUERS = {
    "amazon web services": "Amazon Web Services (AWS)",
    "aws": "Amazon Web Services (AWS)",
    "google cloud": "Google Cloud",
    "google": "Google",
    "microsoft azure": "Microsoft",
    "azure": "Microsoft",
    "microsoft": "Microsoft",
    "meta": "Meta",
    "cisco": "Cisco",
    "comptia": "CompTIA",
    "oracle": "Oracle",
    "ibm": "IBM",
    "red hat": "Red Hat",
    "linux foundation": "The Linux Foundation",
    "coursera": "Coursera",
    "edx": "edX",
    "udemy": "Udemy",
    "scrum.org": "Scrum.org",
    "scrum alliance": "Scrum Alliance",
    "project management institute": "Project Management Institute (PMI)",
    "pmi": "Project Management Institute (PMI)",
    "deeplearning.ai": "DeepLearning.AI",
    "freecodecamp": "freeCodeCamp",
    "stanford": "Stanford University",
    "harvard": "Harvard University",
    "mit": "MIT",
    "kaggle": "Kaggle",
    "datacamp": "DataCamp",
    "hashicorp": "HashiCorp",
}

# Certification category keywords
CATEGORY_KEYWORDS = [
    ("cloud", ["aws", "azure", "google cloud", "gcp", "cloud practitioner", "solutions architect", "sysops"]),
    ("ai_ml", ["machine learning", "deep learning", "ai", "artificial intelligence", "nlp", "computer vision", "tensorflow", "pytorch", "llm"]),
    ("data_science", ["data science", "data analyst", "data engineer", "big data", "analytics", "power bi", "tableau"]),
    ("security", ["security+", "cissp", "ceh", "cybersecurity", "ethical hacking", "cism", "comptia security"]),
    ("programming", ["python", "java", "javascript", "golang", "c++", "c#", "rust", "full stack", "front-end", "backend", "web development"]),
    ("project_management", ["pmp", "scrum master", "csm", "pmi-acp", "prince2", "agile", "project management"]),
    ("technical", ["kubernetes", "docker", "devops", "linux", "cka", "ckad", "networking", "ccna", "ccnp"]),
    ("course", ["specialization", "course certificate", "bootcamp", "nanodegree", "online course", "coursera", "udemy"]),
    ("training", ["training", "workshop", "fellowship", "internship certificate"]),
    ("professional", ["certified professional", "chartered", "licensed", "professional certification"]),
]

# Regex patterns for deterministic extraction
URL_REGEX = re.compile(r"https?://[^\s<>\"')]+", re.IGNORECASE)
DOI_REGEX = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", re.IGNORECASE)

DATE_PATTERN = re.compile(
    r"\b(?:issued|awarded|date|received)?\s*[:\s]*((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}|\d{1,2}/\d{4})\b",
    re.IGNORECASE,
)
EXPIRY_PATTERN = re.compile(
    r"\b(?:expires|expiry|valid\s+(?:thru|through|until|to))\s*[:\s]*((?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}|\d{1,2}/\d{4}|\d{4})\b",
    re.IGNORECASE,
)
YEAR_RANGE = re.compile(r"\b(20\d{2}|19\d{2})\s*(?:[-–—]|to)\s*(20\d{2}|present|current)\b", re.IGNORECASE)
STANDALONE_YEAR = re.compile(r"\b(20\d{2})\b")

CREDENTIAL_ID_PATTERN = re.compile(
    r"(?:credential\s*id|license\s*(?:number|id|no)?|badge\s*id|certificate\s*no\.?)[:\s]+([A-Za-z0-9\-_]{5,40})",
    re.IGNORECASE,
)

TEAM_SIZE_PATTERN = re.compile(
    r"(?:team\s*of\s*(\d{1,2})|led\s*a?\s*team\s*of\s*(\d{1,2})|(\d{1,2})[- ]member\s*team)",
    re.IGNORECASE,
)


def extract_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extracts issue date and expiry date from text block."""
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None

    exp_match = EXPIRY_PATTERN.search(text)
    if exp_match:
        expiry_date = exp_match.group(1).strip()

    date_match = DATE_PATTERN.search(text)
    if date_match:
        issue_date = date_match.group(1).strip()
    else:
        year_match = STANDALONE_YEAR.search(text)
        if year_match:
            issue_date = year_match.group(1).strip()

    return issue_date, expiry_date


def detect_completion_status(text: str, expiry_date: Optional[str] = None) -> str:
    """Detects completion status: in_progress, expired, or completed."""
    lower = text.lower()
    if any(k in lower for k in ["in progress", "currently pursuing", "in-progress", "pursuing", "candidate", "expected"]):
        return "in_progress"
    if expiry_date and any(k in lower for k in ["expired", "lapsed"]):
        return "expired"
    return "completed"


def detect_certification_category(title: str, issuer: Optional[str] = None, text: str = "") -> str:
    """Classifies certification into one of supported categories."""
    combined = f"{title} {issuer or ''} {text}".lower()
    for cat, kws in CATEGORY_KEYWORDS:
        if any(kw in combined for kw in kws):
            return cat
    return "other"


def extract_deterministic_certification(block_text: str, section_name: str = "certifications") -> Dict[str, Any]:
    """
    Parses a single candidate certification block.
    Extracts name, organization, dates, credential ID, URL, status, and category.
    """
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]
    if not lines:
        return {}

    first_line = lines[0]
    # Clean leading bullet chars
    first_line = re.sub(r"^(\*|\-|\u2022|\d+[\.\)])\s+", "", first_line).strip()

    cert_name = first_line
    issuing_org: Optional[str] = None

    # Check explicit separators in title line: "Name | Issuer" or "Name issued by Issuer"
    if "|" in cert_name:
        parts = cert_name.split("|")
        cert_name = "|".join(parts[:-1]).strip()
        candidate_org = parts[-1].strip()
        for k, v in KNOWN_ISSUERS.items():
            if k in candidate_org.lower():
                issuing_org = v
                break
        if not issuing_org and len(candidate_org) < 60:
            issuing_org = candidate_org
    elif re.search(r"\bissued by\b", cert_name, re.IGNORECASE):
        parts = re.split(r"\bissued by\b", cert_name, flags=re.IGNORECASE)
        cert_name = parts[0].strip()
        candidate_org = parts[1].strip()
        for k, v in KNOWN_ISSUERS.items():
            if k in candidate_org.lower():
                issuing_org = v
                break
        if not issuing_org and len(candidate_org) < 60:
            issuing_org = candidate_org
    else:
        # Check parenthetical: "AWS Solutions Architect (Amazon Web Services)"
        paren_match = re.search(r"\(([^)]+)\)$", cert_name)
        if paren_match:
            paren_content = paren_match.group(1).strip()
            for k, v in KNOWN_ISSUERS.items():
                if k in paren_content.lower():
                    issuing_org = v
                    cert_name = cert_name[:paren_match.start()].strip()
                    break

        if not issuing_org:
            # Check hyphen separator only if right side matches a known issuer
            match_hyphen = re.match(r"^(.+?)\s*(?:[-–—])\s+(.+)$", cert_name)
            if match_hyphen:
                candidate_name, candidate_org = match_hyphen.group(1).strip(), match_hyphen.group(2).strip()
                for k, v in KNOWN_ISSUERS.items():
                    if k in candidate_org.lower():
                        issuing_org = v
                        cert_name = candidate_name
                        break

    # If issuer not found from title line, scan the entire block for known issuers
    if not issuing_org:
        block_lower = block_text.lower()
        for k, v in KNOWN_ISSUERS.items():
            if k in block_lower:
                issuing_org = v
                break

    # Clean certification name formatting
    cert_name = re.sub(r"^\*\*(.+?)\*\*.*$", r"\1", cert_name).strip()
    cert_name = cert_name.strip(" *-_:,")

    # Dates
    issue_date, expiry_date = extract_dates(block_text)

    # Credential ID
    credential_id: Optional[str] = None
    cred_match = CREDENTIAL_ID_PATTERN.search(block_text)
    if cred_match:
        credential_id = cred_match.group(1).strip()

    # Credential URL
    credential_url: Optional[str] = None
    url_match = URL_REGEX.search(block_text)
    if url_match:
        credential_url = url_match.group(0).strip(".,)")

    # Status & Category
    completion_status = detect_completion_status(block_text, expiry_date)
    category = detect_certification_category(cert_name, issuing_org, block_text)

    return {
        "certification_name": cert_name,
        "normalized_name": cert_name,
        "issuing_organization": issuing_org,
        "certification_category": category,
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "credential_id": credential_id,
        "credential_url": credential_url,
        "completion_status": completion_status,
        "source_section": section_name,
        "source_evidence": lines,
    }


# =========================================================================
# ACHIEVEMENTS EXTRACTION
# =========================================================================

# Strict ranking keywords
RANKING_PATTERNS = [
    ("1st Place", [r"\b1st\s*place\b", r"\bfirst\s*place\b", r"\bwinner\b", r"\bgrand\s*prize\b", r"\bchampion\b", r"\bgold\s*medal\b"]),
    ("2nd Place", [r"\b2nd\s*place\b", r"\bsecond\s*place\b", r"\b1st\s*runner[\s-]*up\b", r"\brunner[\s-]*up\b", r"\bsilver\s*medal\b"]),
    ("3rd Place", [r"\b3rd\s*place\b", r"\bthird\s*place\b", r"\b2nd\s*runner[\s-]*up\b", r"\bbronze\s*medal\b"]),
    ("Finalist", [r"\bfinalist\b", r"\btop\s*(?:3|5|10|20|50|100)\b", r"\btop\s*\d+%\b", r"\bhonorable\s*mention\b", r"\bsemi[\s-]*finalist\b"]),
    ("Participant", [r"\bparticipant\b", r"\bparticipated\b", r"\battended\b"]),
    ("Volunteer", [r"\bvolunteer\b", r"\bmentored\b", r"\borganizer\b", r"\bstudent\s*coordinator\b"]),
]


def detect_achievement_type_and_rank(text: str) -> Tuple[str, Optional[str]]:
    """
    Strictly separates Winner / Awards / Ranking from Participation / Volunteer.
    Returns: (achievement_type, rank_or_position)
    """
    lower = text.lower()

    # 1. Check for awards / winners first
    for rank_name, patterns in RANKING_PATTERNS[:3]:  # 1st, 2nd, 3rd Place
        for p in patterns:
            if re.search(p, lower):
                return "award", rank_name

    # 1b. Check academic honors / awards (Dean's List, Gold Medal, Valedictorian, Best Paper, Award)
    if any(k in lower for k in ["dean's list", "valedictorian", "gold medal", "best paper", "award", "honor"]):
        # Extract rank if mentioned like "top 5%"
        top_match = re.search(r"\btop\s*(?:\d+%|\d+)\b", lower)
        rank_pos = top_match.group(0).capitalize() if top_match else "Honoree"
        return "award", rank_pos

    # 2. Check for finalist / rankings
    for rank_name, patterns in [RANKING_PATTERNS[3]]:  # Finalist
        for p in patterns:
            match = re.search(p, lower)
            if match:
                return "ranking", match.group(0).capitalize()

    # 3. Check for publication
    if any(k in lower for k in ["publication", "published in", "ieee", "arxiv", "acm", "conference proceedings", "journal"]):
        return "publication", None

    # 4. Check for scholarships
    if any(k in lower for k in ["scholarship", "fellowship grant", "tuition grant"]):
        return "scholarship", "Recipient"

    # 5. Check for participation (MUST NOT be elevated to award)
    for rank_name, patterns in [RANKING_PATTERNS[4]]:  # Participant
        for p in patterns:
            if re.search(p, lower):
                return "participation", "Participant"

    # 6. Check volunteer
    for rank_name, patterns in [RANKING_PATTERNS[5]]:
        for p in patterns:
            if re.search(p, lower):
                return "recognition", rank_name

    # 7. Check generic awards / honors
    if any(k in lower for k in ["award", "honor", "dean's list", "merit", "best project", "best paper"]):
        return "award", "Honoree"

    return "recognition", None


def detect_achievement_category(title: str, text: str = "") -> str:
    """Classifies achievement category."""
    combined = f"{title} {text}".lower()

    if any(k in combined for k in ["hackathon", "mlh", "hack", "smart india hackathon"]):
        return "hackathon"
    if any(k in combined for k in ["competition", "contest", "coding challenge", "icpc", "codeforces", "leetcode", "olympiad"]):
        return "competition"
    if any(k in combined for k in ["paper", "publication", "ieee", "arxiv", "journal", "acm", "research publication"]):
        return "publication"
    if any(k in combined for k in ["scholarship", "fellowship"]):
        return "scholarship"
    if any(k in combined for k in ["dean's list", "valedictorian", "academic excellence", "cgpa", "rank in department"]):
        return "academic"
    if any(k in combined for k in ["president", "lead", "head of", "secretary", "captain", "founded", "founder"]):
        return "leadership"
    if any(k in combined for k in ["volunteer", "ngo", "community service", "social work"]):
        return "volunteer"
    if any(k in combined for k in ["open source contributor", "community", "meetup speaker"]):
        return "community"
    if any(k in combined for k in ["patent", "research", "laboratory"]):
        return "research"
    if any(k in combined for k in ["employee of the month", "star performer", "spot award", "client appreciation"]):
        return "professional"
    return "other"


def extract_deterministic_achievement(block_text: str, section_name: str = "achievements") -> Dict[str, Any]:
    """
    Parses a single candidate achievement block.
    Extracts title, event, organizer, rank, type, dates, team info, URLs, role, and category.
    """
    lines = [l.strip() for l in block_text.split("\n") if l.strip()]
    if not lines:
        return {}

    first_line = lines[0]
    # Clean bullet points
    first_line = re.sub(r"^(\*|\-|\u2022|\d+[\.\)])\s+", "", first_line).strip()
    first_line = re.sub(r"^\*\*(.+?)\*\*.*$", r"\1", first_line).strip()

    title = first_line
    event_name: Optional[str] = None
    organization: Optional[str] = None

    # Check separators like "Title - Event/Org" or "Title at Event"
    match_event = re.match(r"^(.+?)\s*(?:[-–—|:]|\bat\b|\bby\b)\s+(.+)$", title, re.IGNORECASE)
    if match_event:
        title = match_event.group(1).strip()
        trailing = match_event.group(2).strip()
        if len(trailing) < 80:
            event_name = trailing

    # Detect rank and type
    achieve_type, rank_position = detect_achievement_type_and_rank(block_text)

    # Dates
    issue_date, _ = extract_dates(block_text)

    # URLs or DOI
    url: Optional[str] = None
    doi_match = DOI_REGEX.search(block_text)
    if doi_match:
        url = f"https://doi.org/{doi_match.group(0)}"
    else:
        url_match = URL_REGEX.search(block_text)
        if url_match:
            url = url_match.group(0).strip(".,)")

    # Team size
    team_size: Optional[int] = None
    team_match = TEAM_SIZE_PATTERN.search(block_text)
    if team_match:
        for g in team_match.groups():
            if g:
                try:
                    team_size = int(g)
                    break
                except ValueError:
                    pass

    # Role
    candidate_role: Optional[str] = None
    role_match = re.search(r"\b(?:role|as|contributed as)[:\s]+([A-Za-z\s]{3,30})\b", block_text, re.IGNORECASE)
    if role_match:
        candidate_role = role_match.group(1).strip()

    category = detect_achievement_category(title, block_text)

    # Description (joined remaining lines if present)
    desc = " ".join(lines[1:]) if len(lines) > 1 else None

    return {
        "achievement_title": title,
        "normalized_title": title,
        "achievement_category": category,
        "event_name": event_name,
        "organization": organization,
        "achievement_type": achieve_type,
        "rank_or_position": rank_position,
        "achievement_date": issue_date,
        "description": desc,
        "team_size": team_size,
        "candidate_role": candidate_role,
        "achievement_url": url,
        "source_section": section_name,
        "source_evidence": lines,
    }
