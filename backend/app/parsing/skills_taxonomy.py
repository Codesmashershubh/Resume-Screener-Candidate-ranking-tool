"""
Skills taxonomy shared by resume parsing and job-description analysis.

Organized by category so the same source of truth can power:
  - skill extraction from free text (resumes, job descriptions)
  - the "disciplines we understand" showcase in the UI
  - category-level reporting

Matching is case-insensitive except for a small set of short, ambiguous
tokens (e.g. "Go", "R", "C") which are matched case-sensitively so we
don't flag every sentence that happens to contain the word "go".
"""

from __future__ import annotations
import re

SKILLS_BY_CATEGORY: dict[str, list[str]] = {
    "Engineering": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go",
        "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "HTML", "CSS",
        "Tailwind CSS", "React", "Vue.js", "Angular", "Next.js", "Svelte",
        "Node.js", "Express.js", "Django", "Flask", "FastAPI", "Spring Boot",
        ".NET", "Ruby on Rails", "GraphQL", "REST APIs", "Microservices",
        "Git", "Docker", "Kubernetes", "CI/CD", "Jenkins", "Terraform",
        "AWS", "Azure", "Google Cloud Platform", "Linux", "Bash",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Elasticsearch",
        "Unit Testing", "System Design", "Object-Oriented Programming",
        "Software Architecture",
    ],
    "Data & Analytics": [
        "SQL", "Machine Learning", "Deep Learning", "Natural Language Processing",
        "Computer Vision", "Data Analysis", "Data Visualization",
        "Data Engineering", "ETL", "Pandas", "NumPy", "Scikit-learn",
        "TensorFlow", "PyTorch", "Tableau", "Power BI", "Excel", "Statistics",
        "A/B Testing", "Big Data", "Apache Spark", "Data Warehousing", "R",
    ],
    "Product & Design": [
        "Product Management", "Product Strategy", "Roadmapping",
        "User Research", "UX Design", "UI Design", "Wireframing",
        "Prototyping", "Figma", "Adobe XD", "Sketch", "Design Systems",
        "Usability Testing", "Agile", "Scrum", "JIRA", "Confluence",
    ],
    "Marketing & Growth": [
        "SEO", "SEM", "Content Marketing", "Social Media Marketing",
        "Email Marketing", "Google Analytics", "Growth Marketing",
        "Brand Strategy", "Copywriting", "Marketing Automation", "HubSpot",
        "Paid Advertising", "Community Management",
    ],
    "Sales & Business": [
        "Sales", "Business Development", "Account Management", "CRM",
        "Salesforce", "Negotiation", "Lead Generation", "Customer Success",
        "Client Relations", "B2B Sales",
    ],
    "Finance & Operations": [
        "Financial Modeling", "Financial Analysis", "Budgeting", "Forecasting",
        "Accounting", "QuickBooks", "SAP", "Supply Chain Management",
        "Operations Management", "Project Management", "Six Sigma",
        "Inventory Management",
    ],
    "People & Leadership": [
        "Leadership", "Team Management", "Communication",
        "Cross-functional Collaboration", "Mentoring", "Recruiting",
        "Public Speaking", "Stakeholder Management", "Problem Solving",
        "Strategic Planning",
    ],
}

# Common abbreviations / alternate spellings -> canonical skill name.
ALIASES: dict[str, str] = {
    "js": "JavaScript", "javascript": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "nlp": "Natural Language Processing",
    "k8s": "Kubernetes",
    "ci/cd": "CI/CD", "cicd": "CI/CD",
    "gcp": "Google Cloud Platform",
    "postgres": "PostgreSQL",
    "reactjs": "React", "react.js": "React",
    "vuejs": "Vue.js",
    "nodejs": "Node.js", "node": "Node.js",
    "oop": "Object-Oriented Programming",
    "ui/ux": "UX Design", "ux/ui": "UX Design",
    "sklearn": "Scikit-learn",
}

# Short tokens that would false-positive constantly if matched case-insensitively
# inside ordinary sentences (e.g. "go to market", "we can C the difference").
_CASE_SENSITIVE_SKILLS = {"Go", "R", "C"}

ALL_SKILLS: list[str] = sorted({s for skills in SKILLS_BY_CATEGORY.values() for s in skills})

_SKILL_TO_CATEGORY: dict[str, str] = {
    s: cat for cat, skills in SKILLS_BY_CATEGORY.items() for s in skills
}


def category_of(skill: str) -> str | None:
    return _SKILL_TO_CATEGORY.get(skill)


def _pattern_for(token: str, case_sensitive: bool) -> re.Pattern:
    escaped = re.escape(token)
    # \b doesn't work well around tokens that start/end with punctuation
    # (C++, C#, .NET), so we use lookaround on non-word-ish boundaries instead.
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", flags)


# Compiled once at import time, with the IGNORECASE flag already baked into
# each pattern - find_skills_in_text() below never compiles a regex at
# request time, it only calls .search() on pre-built patterns. This matters
# on a 0.1 CPU free-tier instance: the naive version (recompiling ~170
# patterns per resume) was the single biggest CPU cost in the parsing path.
_SKILL_PATTERNS: dict[str, re.Pattern] = {
    skill: _pattern_for(skill, skill in _CASE_SENSITIVE_SKILLS) for skill in ALL_SKILLS
}
_ALIAS_PATTERNS: dict[str, re.Pattern] = {
    alias: _pattern_for(alias, False) for alias in ALIASES if alias not in _CASE_SENSITIVE_SKILLS
}


def find_skills_in_text(text: str) -> set[str]:
    """Scan free text and return the set of canonical skill names found."""
    if not text:
        return set()
    found: set[str] = set()

    for skill, pattern in _SKILL_PATTERNS.items():
        if pattern.search(text):
            found.add(skill)

    for alias, pattern in _ALIAS_PATTERNS.items():
        if pattern.search(text):
            found.add(ALIASES[alias])

    return found
