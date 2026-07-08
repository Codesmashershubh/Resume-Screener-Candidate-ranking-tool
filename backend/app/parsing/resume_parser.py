"""
Resume Parser.

Turns raw resume text into structured candidate data: contact info,
skills, education, total experience, and projects. Extraction here is
heuristic/regex-based on purpose - it's transparent (every field can be
traced to a rule) even where it isn't perfect. The UI always shows the
raw extracted text alongside the parsed fields so a reviewer can verify.
"""

from __future__ import annotations
import datetime
import re
from dataclasses import dataclass, field

from .skills_taxonomy import find_skills_in_text
from .patterns import (
    EDUCATION_LABELS,
    extract_education_level,
    extract_education_snippet,
    extract_explicit_experience_years,
    estimate_experience_from_date_ranges,
)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}"
)

_SECTION_KEYWORDS = {
    "summary", "objective", "profile", "resume", "curriculum", "vitae",
    "contact", "information", "experience", "education", "skills",
    "about", "personal", "professional", "career", "references", "cv",
}

_PROJECTS_HEADER_RE = re.compile(r"^\s*(projects?|personal projects?|key projects?)\s*:?\s*$", re.I)
_ANY_SECTION_HEADER_RE = re.compile(
    r"^\s*(experience|work experience|employment|education|skills|"
    r"technical skills|certifications|awards|publications|summary|"
    r"objective|contact|references)\s*:?\s*$",
    re.I,
)
_PROJECT_TITLE_COLON_RE = re.compile(r"^([A-Z][^:]{2,60}):\s*(.+)$")


@dataclass
class ProjectEntry:
    title: str
    snippet: str


@dataclass
class ParsedResume:
    filename: str
    raw_text: str
    name: str | None
    email: str | None
    phone: str | None
    skills: list[str] = field(default_factory=list)
    education_level: int = 0
    education_label: str = "Not specified"
    education_snippet: str | None = None
    experience_years: float | None = None
    experience_source: str = "not_found"  # "stated" | "estimated_from_dates" | "not_found"
    projects: list[ProjectEntry] = field(default_factory=list)


def extract_name(text: str) -> str | None:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:8]:
        if "@" in line or any(ch.isdigit() for ch in line):
            continue
        words = line.split()
        if not (1 < len(words) <= 4 and len(line) < 60):
            continue
        lowered_words = {w.lower().strip(".,") for w in words}
        if lowered_words & _SECTION_KEYWORDS:
            continue
        if all(w[:1].isupper() for w in words if w[:1].isalpha()):
            return line.title() if line.isupper() else line
    return None


def extract_email(text: str) -> str | None:
    match = _EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    match = _PHONE_RE.search(text)
    return match.group(0).strip() if match else None


def extract_experience(text: str) -> tuple[float | None, str]:
    stated = extract_explicit_experience_years(text)
    if stated is not None:
        return float(stated), "stated"

    current_year = datetime.date.today().year
    estimated = estimate_experience_from_date_ranges(text, current_year)
    if estimated is not None:
        return estimated, "estimated_from_dates"

    return None, "not_found"


def extract_projects(text: str, max_projects: int = 8) -> list[ProjectEntry]:
    """Pull individual project entries out of a resume's Projects section.

    Resumes format this section in wildly different ways, so we try a few
    strategies in order of reliability rather than one guess:
      1. "Project Name: description" lines - an explicit, unambiguous signal.
      2. Blank-line-separated paragraphs - first line is the title.
      3. Fallback - couldn't confidently split it, so return the whole
         section as one entry rather than silently dropping the content.
    """
    lines = text.splitlines()
    in_projects_section = False
    collected: list[str] = []

    for line in lines:
        stripped = line.strip()
        if _PROJECTS_HEADER_RE.match(stripped):
            in_projects_section = True
            continue
        if not in_projects_section:
            continue
        if stripped and _ANY_SECTION_HEADER_RE.match(stripped):
            break
        collected.append(line)

    if not collected:
        return []

    def clean(s: str) -> str:
        return s.strip().lstrip("-•*◦‣ ").strip()

    # Strategy 1: explicit "Title: description" lines.
    colon_projects = []
    for raw_line in collected:
        match = _PROJECT_TITLE_COLON_RE.match(clean(raw_line))
        if match:
            colon_projects.append(
                ProjectEntry(title=match.group(1).strip(), snippet=" ".join(match.group(2).split())[:220])
            )
    if colon_projects:
        return colon_projects[:max_projects]

    # Strategy 2: group into paragraphs on blank lines; first line = title.
    entries: list[list[str]] = []
    current: list[str] = []
    for raw_line in collected:
        stripped = raw_line.strip()
        if not stripped:
            if current:
                entries.append(current)
                current = []
            continue
        current.append(clean(raw_line))
    if current:
        entries.append(current)

    if len(entries) > 1:
        projects = []
        for entry in entries[:max_projects]:
            title = entry[0][:80]
            body = " ".join(entry[1:]) if len(entry) > 1 else entry[0]
            projects.append(ProjectEntry(title=title, snippet=" ".join(body.split())[:220]))
        return projects

    # Strategy 3: no reliable separators found - keep the content, labeled generically.
    full_text = " ".join(" ".join(collected).split())
    if full_text:
        return [ProjectEntry(title="Projects", snippet=full_text[:220])]
    return []


def parse_resume(filename: str, text: str) -> ParsedResume:
    education_level = extract_education_level(text)
    experience_years, experience_source = extract_experience(text)

    return ParsedResume(
        filename=filename,
        raw_text=text,
        name=extract_name(text),
        email=extract_email(text),
        phone=extract_phone(text),
        skills=sorted(find_skills_in_text(text)),
        education_level=education_level,
        education_label=EDUCATION_LABELS[education_level],
        education_snippet=extract_education_snippet(text),
        experience_years=experience_years,
        experience_source=experience_source,
        projects=extract_projects(text),
    )
