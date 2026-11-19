"""
Validation Engine for Personal Information
Phase 3 | Feature 13: Personal Information Extraction
Validates format, boundaries, syntax, and rejects hallucinated or malformed entries.
"""

import re
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

COUNTRY_CODE_REGEX = re.compile(r"^\+\d{1,4}$")


def validate_email(email: Optional[str]) -> Optional[str]:
    """Validates email format. Returns sanitized email if valid, otherwise None."""
    if not email or not isinstance(email, str):
        return None
    email_clean = email.strip()
    if not EMAIL_REGEX.match(email_clean):
        return None
    # Check domain parts
    domain = email_clean.split("@")[-1]
    if "." not in domain or len(domain.split(".")[-1]) < 2:
        return None
    return email_clean


def validate_phone(phone: Optional[str]) -> Optional[str]:
    """Validates phone number. Must contain 7 to 15 digits."""
    if not phone or not isinstance(phone, str):
        return None
    digits = re.sub(r"\D", "", phone)
    if not (7 <= len(digits) <= 15):
        return None
    return phone.strip()


def validate_country_code(country_code: Optional[str]) -> Optional[str]:
    """Validates international phone country code (+XX)."""
    if not country_code or not isinstance(country_code, str):
        return None
    code_clean = country_code.strip()
    if not COUNTRY_CODE_REGEX.match(code_clean):
        return None
    return code_clean


def validate_name(name: Optional[str]) -> Optional[str]:
    """Validates candidate name. Must be reasonable length and not contain URLs or email chars."""
    if not name or not isinstance(name, str):
        return None
    name_clean = name.strip()
    if len(name_clean) < 2 or len(name_clean) > 100:
        return None
    # Cannot contain @ or digits or url markers
    if "@" in name_clean or any(c.isdigit() for c in name_clean):
        return None
    if any(m in name_clean.lower() for m in ("http://", "https://", "www.", ".com", ".org")):
        return None
    return name_clean


def validate_url(url: Optional[str]) -> Optional[str]:
    """Validates URL syntax. Must have valid scheme and netloc with a top-level domain."""
    if not url or not isinstance(url, str):
        return None
    clean = url.strip()
    try:
        parsed = urlparse(clean)
        if parsed.scheme not in ("http", "https"):
            return None
        if not parsed.netloc or "." not in parsed.netloc:
            return None
        # Reject invalid characters
        if " " in clean or "\n" in clean or "\t" in clean:
            return None
        return clean
    except Exception:
        return None


def validate_location(location: Optional[Dict[str, Any]]) -> Optional[Dict[str, Optional[str]]]:
    """Validates location components."""
    if not location or not isinstance(location, dict):
        return None

    def _val_loc_part(part: Any) -> Optional[str]:
        if not part or not isinstance(part, str):
            return None
        cleaned = part.strip()
        if len(cleaned) < 2 or len(cleaned) > 100:
            return None
        if "@" in cleaned or any(cleaned.lower().startswith(p) for p in ("http", "www")):
            return None
        return cleaned

    city = _val_loc_part(location.get("city"))
    state = _val_loc_part(location.get("state"))
    country = _val_loc_part(location.get("country"))

    if not city and not state and not country:
        return None

    return {
        "city": city,
        "state": state,
        "country": country,
    }


def validate_urls_list(urls: Optional[List[str]]) -> List[str]:
    """Validates a list of other URLs."""
    if not urls:
        return []
    valid_list: List[str] = []
    for u in urls:
        valid_u = validate_url(u)
        if valid_u and valid_u not in valid_list:
            valid_list.append(valid_u)
    return valid_list
