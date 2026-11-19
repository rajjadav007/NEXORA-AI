"""
Field Normalizer for Personal Information
Phase 3 | Feature 13: Personal Information Extraction
Normalizes casing, URLs, phone numbers, and whitespace.
"""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urlunparse


def normalize_string(value: Optional[str]) -> Optional[str]:
    """Clean extra spaces and return None for empty strings."""
    if not value or not isinstance(value, str):
        return None
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned if cleaned else None


def normalize_name(value: Optional[str]) -> Optional[str]:
    """Normalize candidate name to title case with clean spacing."""
    clean = normalize_string(value)
    if not clean:
        return None
    # Strip any stray punctuation from the ends
    clean = clean.strip(".,;:|/\\-")
    return clean.title() if clean else None


def normalize_email(value: Optional[str]) -> Optional[str]:
    """Normalize email to clean lowercase format."""
    clean = normalize_string(value)
    if not clean:
        return None
    return clean.lower()


def normalize_phone(value: Optional[str]) -> Optional[str]:
    """Normalize phone number string representation."""
    clean = normalize_string(value)
    if not clean:
        return None
    # Ensure consistent spacing around country code if present
    # E.g. "+919876543210" -> "+91 9876543210"
    m = re.match(r"^(\+\d{1,4})[\s.-]?(\d{6,14})$", clean)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return clean


def normalize_country_code(value: Optional[str]) -> Optional[str]:
    """Normalize country code to standard +XX format."""
    clean = normalize_string(value)
    if not clean:
        return None
    if not clean.startswith("+"):
        clean = f"+{clean}"
    return clean


def normalize_url(value: Optional[str]) -> Optional[str]:
    """Normalize URL by adding scheme, lowercasing domain, and stripping trailing slash."""
    clean = normalize_string(value)
    if not clean:
        return None

    if not clean.startswith("http://") and not clean.startswith("https://"):
        clean = f"https://{clean}"

    try:
        parsed = urlparse(clean)
        # Use https by default
        scheme = "https"
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip("/")
        # Rebuild clean URL without fragments or tracking queries
        normalized = urlunparse((scheme, netloc, path, "", "", ""))
        return normalized
    except Exception:
        return clean.rstrip("/")


def normalize_location(loc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Optional[str]]]:
    """Normalize city, state, country within location dict."""
    if not loc or not isinstance(loc, dict):
        return None

    city = normalize_name(loc.get("city"))
    state = normalize_name(loc.get("state"))
    country = normalize_name(loc.get("country"))

    # If all components are None, return None
    if not city and not state and not country:
        return None

    return {
        "city": city,
        "state": state,
        "country": country,
    }


def normalize_urls_list(urls: Optional[List[str]]) -> List[str]:
    """Deduplicate and normalize a list of URLs."""
    if not urls:
        return []
    normalized: List[str] = []
    seen = set()
    for u in urls:
        norm = normalize_url(u)
        if norm and norm not in seen:
            seen.add(norm)
            normalized.append(norm)
    return normalized
