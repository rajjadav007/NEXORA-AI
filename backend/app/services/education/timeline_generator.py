"""
Education Timeline Generator
Phase 3 | Feature 14: Education Analysis
Sorts education entries chronologically and validates date consistency.
"""

import re
from typing import List, Dict, Any


def _parse_year(date_str: Any) -> int:
    """Extract 4-digit year as integer, or 0 if missing."""
    if not date_str or not isinstance(date_str, str):
        return 0
    m = re.search(r"\b((?:19|20)\d{2})\b", date_str)
    return int(m.group(1)) if m else 0


def generate_education_timeline(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts education entries chronologically for display:
    1. Ongoing / Expected entries first.
    2. Then descending by start_date / end_date year.
    3. Entries with missing dates placed at the end.
    """
    if not entries:
        return []

    def sort_key(entry: Dict[str, Any]):
        status = entry.get("graduation_status", "completed")
        is_ongoing = 1 if status in ("ongoing", "expected") else 0
        start_year = _parse_year(entry.get("start_date"))
        end_year = _parse_year(entry.get("end_date"))
        primary_year = start_year or end_year
        return (is_ongoing, primary_year, end_year)

    sorted_entries = sorted(entries, key=sort_key, reverse=True)
    return sorted_entries


def detect_timeline_overlaps(entries: List[Dict[str, Any]]) -> List[str]:
    """
    Identifies overlapping educational periods across different degrees.
    Returns list of human-readable overlap descriptions.
    """
    overlaps = []
    n = len(entries)
    for i in range(n):
        for j in range(i + 1, n):
            e1 = entries[i]
            e2 = entries[j]
            s1 = _parse_year(e1.get("start_date"))
            e_end1 = _parse_year(e1.get("end_date")) or s1
            s2 = _parse_year(e2.get("start_date"))
            e_end2 = _parse_year(e2.get("end_date")) or s2

            if s1 and e_end1 and s2 and e_end2:
                # Check for overlap: max(s1, s2) <= min(e_end1, e_end2)
                if max(s1, s2) < min(e_end1, e_end2):
                    d1 = e1.get("degree") or "Degree 1"
                    d2 = e2.get("degree") or "Degree 2"
                    overlaps.append(f"Overlap detected between {d1} ({s1}-{e_end1}) and {d2} ({s2}-{e_end2})")

    return overlaps
