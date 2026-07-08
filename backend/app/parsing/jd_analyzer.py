"""
Job Description Analyzer.

Turns raw job-description text into structured requirements:
  - required skills (matched against the shared skills taxonomy)
  - "nice to have" skills (mentioned near preferred/bonus language)
  - required years of experience
  - required education level
  - top keywords (for the keyword-overlap scoring dimension)
"""

from __future__ import annotations
from dataclasses import dataclass, field

from .skills_taxonomy import find_skills_in_text
from .patterns import (
    EDUCATION_LABELS,
    extract_education_level,
    extract_explicit_experience_years,
)
from ..scoring import nlp_utils as nlp

_PREFERRED_MARKERS = (
    "nice to have", "preferred", "bonus", "a plus", "is a plus",
    "good to have", "desirable", "ideally",
)


@dataclass
class JobRequirements:
    raw_text: str
    required_skills: list[str] = field(default_factory=list)
    nice_to_have_skills: list[str] = field(default_factory=list)
    required_experience_years: int | None = None
    required_education_level: int = 0
    required_education_label: str = "Not specified"
    top_keywords: list[str] = field(default_factory=list)
    tfidf_vector: dict[str, float] = field(default_factory=dict)


def _split_preferred_section(text: str) -> tuple[str, str]:
    """Best-effort split of JD text into (must-have text, nice-to-have text).

    Looks for a line containing a "preferred/bonus/nice to have" marker and
    treats everything from there to the next blank line as the nice-to-have
    block. Everything else counts as required. This is a heuristic, not a
    guarantee - JDs are free text and don't follow one universal structure.
    """
    lines = text.splitlines()
    required_lines: list[str] = []
    preferred_lines: list[str] = []
    in_preferred_block = False

    for line in lines:
        lowered = line.lower()
        if any(marker in lowered for marker in _PREFERRED_MARKERS):
            in_preferred_block = True
            preferred_lines.append(line)
            continue
        if in_preferred_block and line.strip() == "":
            in_preferred_block = False
        (preferred_lines if in_preferred_block else required_lines).append(line)

    return "\n".join(required_lines), "\n".join(preferred_lines)


def analyze_job_description(text: str) -> JobRequirements:
    text = text or ""
    required_text, preferred_text = _split_preferred_section(text)

    required_skills = find_skills_in_text(required_text)
    preferred_skills = find_skills_in_text(preferred_text) - required_skills

    tokens = nlp.tokenize(text)
    tfidf_vector = nlp.compute_tfidf([tokens])[0] if tokens else {}
    top_keywords = nlp.top_terms(tfidf_vector, n=15)

    # Fallback: if the JD is oddly worded and the taxonomy scan comes up
    # completely empty, fall back to top TF-IDF keywords so the "skill
    # match" dimension still has something to compare against, instead of
    # silently scoring everyone 0%.
    if not required_skills and not preferred_skills:
        required_skills = set(top_keywords[:8])

    education_level = extract_education_level(text)

    return JobRequirements(
        raw_text=text,
        required_skills=sorted(required_skills),
        nice_to_have_skills=sorted(preferred_skills),
        required_experience_years=extract_explicit_experience_years(text),
        required_education_level=education_level,
        required_education_label=EDUCATION_LABELS[education_level],
        top_keywords=top_keywords,
        tfidf_vector=tfidf_vector,
    )
