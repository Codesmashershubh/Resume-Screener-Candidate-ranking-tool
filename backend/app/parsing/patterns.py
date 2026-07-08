"""
Shared regex patterns and ordinal scales used by BOTH the JD analyzer and
the resume parser. Kept in one place deliberately: a job's "required
education level" and a candidate's "education level" must be measured on
the exact same scale, or the comparison in the scoring engine is meaningless.
"""

from __future__ import annotations
import re

EDUCATION_LEVELS: dict[str, int] = {
    "phd": 5, "ph.d": 5, "doctorate": 5, "doctoral": 5,
    "master's": 4, "masters": 4, "master of": 4, "mba": 4,
    "m.s.": 4, "m.a.": 4, "msc": 4, "m.tech": 4, "m.eng": 4,
    "bachelor's": 3, "bachelors": 3, "bachelor of": 3, "b.s.": 3, "b.a.": 3,
    "bsc": 3, "b.tech": 3, "b.e.": 3, "undergraduate degree": 3,
    "associate degree": 2, "associate's": 2, "diploma": 2,
    "high school": 1, "ged": 1, "secondary school": 1,
}

EDUCATION_LABELS: dict[int, str] = {
    5: "Doctorate", 4: "Master's degree", 3: "Bachelor's degree",
    2: "Associate degree / Diploma", 1: "High school diploma", 0: "Not specified",
}

# Ordered so the FIRST match wins when scanning left-to-right in a sentence
# (used to grab a "details" snippet, not just the level).
_DEGREE_SNIPPET_PATTERNS: list[tuple[re.Pattern, int]] = [
    (re.compile(r"(ph\.?d\.?|doctorate|doctoral)[^\n,.;]{0,60}", re.I), 5),
    (re.compile(r"(master'?s?|mba|m\.s\.|m\.a\.|msc|m\.tech|m\.eng)[^\n,.;]{0,60}", re.I), 4),
    (re.compile(r"(bachelor'?s?|b\.s\.|b\.a\.|bsc|b\.tech|b\.e\.)[^\n,.;]{0,60}", re.I), 3),
    (re.compile(r"(associate'?s?\s+degree|diploma)[^\n,.;]{0,60}", re.I), 2),
    (re.compile(r"(high school|secondary school)[^\n,.;]{0,60}", re.I), 1),
]

EXPERIENCE_PATTERNS: list[str] = [
    r"(\d+)\s*\+?\s*(?:to|-)\s*\d+\s*\+?\s*years?",                 # "3-5 years" -> lower bound
    r"(?:minimum(?:\s+of)?|at least|min\.?)\s*(\d+)\s*\+?\s*years?",
    r"(\d+)\s*\+\s*years?",                                         # "3+ years"
    r"(\d+)\s*years?\s+(?:of\s+)?(?:relevant\s+)?experience",
]

_YEAR_RANGE_RE = re.compile(
    r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current|now)",
    re.IGNORECASE,
)


def extract_education_level(text: str) -> int:
    """Highest education level keyword found anywhere in the text (0 if none)."""
    lowered = text.lower()
    return max((lvl for kw, lvl in EDUCATION_LEVELS.items() if kw in lowered), default=0)


def extract_education_snippet(text: str) -> str | None:
    """A short, human-readable snippet around the highest-level degree mention."""
    best_level = -1
    best_snippet = None
    for pattern, level in _DEGREE_SNIPPET_PATTERNS:
        match = pattern.search(text)
        if match and level > best_level:
            best_level = level
            best_snippet = " ".join(match.group(0).split())
    return best_snippet


def extract_explicit_experience_years(text: str) -> int | None:
    """Look for an explicit statement like '5+ years of experience'."""
    for pattern in EXPERIENCE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def estimate_experience_from_date_ranges(text: str, current_year: int) -> float | None:
    """Span (earliest start -> latest end/'present') across all date ranges found.

    This is a year-level approximation, not a precise sum of individual role
    durations (which would require reliably parsing every role's start/end
    and handling overlaps - too fragile to do well from free-form resume
    text). It's shown to the user as an estimate, not a hard fact.
    """
    spans: list[tuple[int, int]] = []
    for match in _YEAR_RANGE_RE.finditer(text):
        start_year = int(match.group(1))
        end_token = match.group(2).lower()
        end_year = current_year if end_token in ("present", "current", "now") else int(match.group(2))
        if 0 <= (end_year - start_year) <= 50:
            spans.append((start_year, end_year))
    if not spans:
        return None
    return float(max(e for _, e in spans) - min(s for s, _ in spans))
