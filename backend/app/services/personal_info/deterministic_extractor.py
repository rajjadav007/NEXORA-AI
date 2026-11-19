"""
Deterministic Extractor for Personal Information
Phase 3 | Feature 13: Personal Information Extraction
Extracts emails, phones, country codes, and URLs via high-accuracy deterministic rules and regex.
"""

import re
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlparse

# Email regex matching standard RFC 5322 format
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    re.IGNORECASE,
)

# Phone regex matching international & localized formats
PHONE_REGEX = re.compile(
    r"(?:\+?(\d{1,4}))?[\s.-]?\(?(\d{2,4})\)?[\s.-]?(\d{3,4})[\s.-]?(\d{3,5})",
)

# Generic URL pattern
URL_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{2,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*))",
    re.IGNORECASE,
)

# Known domains
LINKEDIN_DOMAIN = "linkedin.com"
GITHUB_DOMAIN = "github.com"
PORTFOLIO_DOMAINS = {
    "vercel.app",
    "github.io",
    "netlify.app",
    "gitlab.io",
    "devfolio.co",
    "behance.net",
    "dribbble.com",
    "about.me",
}
COMMON_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com",
}


def extract_email(text: str) -> Optional[str]:
    """Extract primary email address from text."""
    if not text:
        return None
    matches = EMAIL_REGEX.findall(text)
    for match in matches:
        clean = match.strip().rstrip(".,;)>]").lower()
        # Verify valid TLD length (at least 2 chars)
        if "." in clean and len(clean.split(".")[-1]) >= 2:
            return clean
    return None


def extract_phone_and_country_code(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract contact phone number and international country code.
    Returns (normalized_phone, country_code).
    """
    if not text:
        return None, None

    # Search lines near the top first (first 25 lines)
    lines = text.split("\n")[:30]
    header_text = "\n".join(lines)

    matches = list(re.finditer(r"(\+?\d[\d\s\-\(\)\.]{7,22}\d)", header_text))
    if not matches:
        matches = list(re.finditer(r"(\+?\d[\d\s\-\(\)\.]{7,22}\d)", text))

    for m in matches:
        candidate = m.group(1).strip()
        # Exclude dates like 2020-2024 or 01-01-2022
        if re.match(r"^\d{4}\s*-\s*\d{4}$", candidate) or re.match(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$", candidate):
            continue

        # Extract only digits and leading plus
        digits_only = re.sub(r"\D", "", candidate)
        if 7 <= len(digits_only) <= 15:
            # Check country code
            country_code = None
            if candidate.startswith("+"):
                # E.g. +91 9876543210 or +1 (555) 123-4567
                cc_match = re.match(r"^\+(\d{1,4})", candidate)
                if cc_match:
                    country_code = f"+{cc_match.group(1)}"
            elif digits_only.startswith("91") and len(digits_only) == 12:
                country_code = "+91"
            elif digits_only.startswith("1") and len(digits_only) == 11:
                country_code = "+1"

            # Return cleaned candidate phone string
            # Normalize internal spaces/hyphens
            cleaned_phone = re.sub(r"\s+", " ", candidate).strip()
            return cleaned_phone, country_code

    return None, None


def extract_urls(text: str) -> Dict[str, Any]:
    """
    Extract and categorize URLs from text into LinkedIn, GitHub, Portfolio, and Other URLs.
    """
    results: Dict[str, Any] = {
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
        "other_urls": [],
    }
    if not text:
        return results

    # Normalize brackets around URLs e.g. [https://...] or (https://...)
    cleaned_input = re.sub(r"[<>\[\]\(\)]", " ", text)
    tokens = re.split(r"[\s\n\r]+", cleaned_input)

    seen_urls = set()

    for token in tokens:
        # Match URL or domain-like path
        token = token.strip(".,;:|")
        if not token:
            continue

        # Avoid matching email addresses (unless it's an HTTP URL like medium.com/@user)
        if "@" in token and not (token.startswith("http://") or token.startswith("https://")):
            continue

        is_url = False
        url_candidate = token

        if token.startswith("http://") or token.startswith("https://"):
            is_url = True
        elif any(
            token.lower().startswith(prefix)
            for prefix in ("www.", "linkedin.com", "github.com", "gitlab.com")
        ):
            is_url = True
            url_candidate = "https://" + token
        elif "." in token:
            # Check if token matches standard URL pattern
            m = URL_REGEX.match(token)
            if m:
                ext = token.split(".")[-1].split("/")[0].lower()
                if ext in {"com", "org", "net", "io", "co", "dev", "me", "app", "ai", "tech", "in", "us", "uk"}:
                    is_url = True
                    url_candidate = "https://" + token

        if not is_url:
            continue

        # Clean URL candidate
        url_candidate = url_candidate.rstrip("/")
        # Verify valid scheme & host
        try:
            parsed = urlparse(url_candidate)
            host = parsed.netloc.lower()
            if not host:
                continue
            # Ignore file names like resume.pdf
            if host.endswith(".pdf") or host.endswith(".docx"):
                continue

            normalized_url = url_candidate
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            # Categorize
            if LINKEDIN_DOMAIN in host:
                if not results["linkedin_url"] and ("/in/" in parsed.path or len(parsed.path) > 1):
                    results["linkedin_url"] = normalized_url
            elif GITHUB_DOMAIN in host:
                if not results["github_url"] and len(parsed.path.strip("/")) > 0:
                    results["github_url"] = normalized_url
            elif any(pd in host for pd in PORTFOLIO_DOMAINS) or any(
                p_kw in host for p_kw in ("portfolio", "personal")
            ):
                if not results["portfolio_url"]:
                    results["portfolio_url"] = normalized_url
                else:
                    results["other_urls"].append(normalized_url)
            else:
                # Discard common generic domains unless user portfolio
                if not results["portfolio_url"] and not any(cd in host for cd in COMMON_EMAIL_DOMAINS):
                    results["portfolio_url"] = normalized_url
                else:
                    results["other_urls"].append(normalized_url)

        except Exception:
            continue

    return results


def extract_deterministic_info(text: str) -> Dict[str, Any]:
    """Execute complete deterministic extraction pipeline on cleaned resume text."""
    email = extract_email(text)
    phone, country_code = extract_phone_and_country_code(text)
    urls = extract_urls(text)

    return {
        "email": email,
        "phone": phone,
        "country_code": country_code,
        "linkedin_url": urls.get("linkedin_url"),
        "github_url": urls.get("github_url"),
        "portfolio_url": urls.get("portfolio_url"),
        "other_urls": urls.get("other_urls", []),
    }
