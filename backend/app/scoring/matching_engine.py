"""
Matching Engine, Ranking System, and Explainability Layer.

This is the "hybrid deterministic + embedding-based" core described in the
PRD:
  - Skills, Experience, Education -> deterministic, rule-based comparisons.
  - Keywords                       -> embedding-based (TF-IDF cosine similarity).
  - Projects                       -> a blend: presence/count is deterministic,
                                       relevance to the JD is embedding-based.

Every DimensionScore carries a `detail` payload with exactly the numbers
used to produce it, so the UI's explainability panel never has to guess
"why" a candidate got a given score.
"""

from __future__ import annotations
from dataclasses import dataclass, field

from ..parsing.jd_analyzer import JobRequirements
from ..parsing.resume_parser import ParsedResume
from ..parsing.patterns import EDUCATION_LABELS
from . import nlp_utils as nlp

DEFAULT_WEIGHTS: dict[str, float] = {
    "skills": 40.0,
    "experience": 25.0,
    "education": 10.0,
    "keywords": 15.0,
    "projects": 10.0,
}

_RANK_THRESHOLDS = [
    (80.0, "Excellent Match"),
    (65.0, "Strong Match"),
    (50.0, "Moderate Match"),
    (0.0, "Weak Match"),
]


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Scale whatever weights are given so they sum to 100, keeping ratios."""
    total = sum(max(weights.get(k, 0.0), 0.0) for k in DEFAULT_WEIGHTS)
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: max(weights.get(k, 0.0), 0.0) / total * 100.0 for k in DEFAULT_WEIGHTS}


def label_for_score(score: float) -> str:
    for threshold, label in _RANK_THRESHOLDS:
        if score >= threshold:
            return label
    return "Weak Match"


@dataclass
class DimensionScore:
    score: float
    max_points: float
    detail: dict = field(default_factory=dict)


@dataclass
class CandidateScore:
    filename: str
    display_name: str
    total_score: float
    label: str
    dimensions: dict[str, DimensionScore]
    summary: str
    rank: int = 0


def _score_skills(jd: JobRequirements, resume: ParsedResume, max_points: float) -> DimensionScore:
    required = set(jd.required_skills)
    candidate_skills = set(resume.skills)
    matched = sorted(required & candidate_skills)
    missing = sorted(required - candidate_skills)
    extra = sorted(candidate_skills - required)

    ratio = (len(matched) / len(required)) if required else 1.0
    return DimensionScore(
        score=round(ratio * max_points, 2),
        max_points=max_points,
        detail={
            "matched": matched,
            "missing": missing,
            "extra": extra,
            "required_count": len(required),
            "matched_count": len(matched),
        },
    )


def _score_experience(jd: JobRequirements, resume: ParsedResume, max_points: float) -> DimensionScore:
    required_years = jd.required_experience_years
    candidate_years = resume.experience_years

    if required_years is None:
        return DimensionScore(
            score=max_points,
            max_points=max_points,
            detail={
                "required_years": None,
                "candidate_years": candidate_years,
                "note": "No specific experience requirement detected in the job "
                        "description - full credit given by default.",
            },
        )
    if candidate_years is None:
        return DimensionScore(
            score=0.0,
            max_points=max_points,
            detail={
                "required_years": required_years,
                "candidate_years": None,
                "note": "Could not detect years of experience on this resume.",
            },
        )

    ratio = min(candidate_years / required_years, 1.0) if required_years > 0 else 1.0
    return DimensionScore(
        score=round(ratio * max_points, 2),
        max_points=max_points,
        detail={
            "required_years": required_years,
            "candidate_years": candidate_years,
            "meets_requirement": candidate_years >= required_years,
            "source": resume.experience_source,
        },
    )


def _score_education(jd: JobRequirements, resume: ParsedResume, max_points: float) -> DimensionScore:
    required_level = jd.required_education_level
    candidate_level = resume.education_level

    if required_level == 0:
        return DimensionScore(
            score=max_points,
            max_points=max_points,
            detail={
                "required": "Not specified",
                "candidate": resume.education_label,
                "note": "No specific education requirement detected - full credit given by default.",
            },
        )

    ratio = min(candidate_level / required_level, 1.0)
    return DimensionScore(
        score=round(ratio * max_points, 2),
        max_points=max_points,
        detail={
            "required": EDUCATION_LABELS[required_level],
            "candidate": resume.education_label,
            "meets_requirement": candidate_level >= required_level,
        },
    )


def _score_keywords(jd_vector: dict, resume_vector: dict, max_points: float) -> DimensionScore:
    similarity = nlp.cosine_similarity(jd_vector, resume_vector)
    shared = nlp.shared_top_terms(jd_vector, resume_vector, n=8)
    return DimensionScore(
        score=round(similarity * max_points, 2),
        max_points=max_points,
        detail={"similarity": round(similarity, 3), "shared_keywords": shared},
    )


def _score_projects(jd_tokens: list[str], resume: ParsedResume, max_points: float) -> DimensionScore:
    count = len(resume.projects)
    if count == 0:
        return DimensionScore(
            score=0.0,
            max_points=max_points,
            detail={"count": 0, "note": "No dedicated Projects section detected on this resume."},
        )

    presence_points = max_points * 0.4 * min(count / 3, 1.0)

    projects_text = " ".join(p.snippet for p in resume.projects)
    tokens_proj = nlp.tokenize(projects_text)
    relevance = 0.0
    if tokens_proj and jd_tokens:
        vecs = nlp.compute_tfidf([jd_tokens, tokens_proj])
        relevance = nlp.cosine_similarity(vecs[0], vecs[1])
    relevance_points = max_points * 0.6 * relevance

    return DimensionScore(
        score=round(presence_points + relevance_points, 2),
        max_points=max_points,
        detail={
            "count": count,
            "relevance": round(relevance, 3),
            "titles": [p.title for p in resume.projects],
        },
    )


def _build_summary(name: str, total: float, label: str, dims: dict[str, DimensionScore]) -> str:
    skills = dims["skills"].detail
    exp = dims["experience"].detail
    sentences = [f"{name} scored {total:.0f}/100 ({label})."]

    if skills["required_count"]:
        tail = f", missing {', '.join(skills['missing'][:5])}." if skills["missing"] else "."
        sentences.append(
            f"Matched {skills['matched_count']} of {skills['required_count']} required skills{tail}"
        )

    if exp.get("required_years") is not None:
        if exp.get("candidate_years") is not None:
            verb = "meets" if exp.get("meets_requirement") else "falls short of"
            sentences.append(
                f"Experience ({exp['candidate_years']:.0f} yrs) {verb} the {exp['required_years']}-year requirement."
            )
        else:
            sentences.append("Years of experience could not be detected on this resume.")

    return " ".join(sentences)


def score_candidate(
    jd: JobRequirements,
    jd_vector: dict,
    jd_tokens: list[str],
    resume: ParsedResume,
    resume_vector: dict,
    weights: dict[str, float],
) -> CandidateScore:
    w = normalize_weights(weights)
    dims = {
        "skills": _score_skills(jd, resume, w["skills"]),
        "experience": _score_experience(jd, resume, w["experience"]),
        "education": _score_education(jd, resume, w["education"]),
        "keywords": _score_keywords(jd_vector, resume_vector, w["keywords"]),
        "projects": _score_projects(jd_tokens, resume, w["projects"]),
    }
    total = round(sum(d.score for d in dims.values()), 2)
    label = label_for_score(total)
    display_name = resume.name or resume.filename
    summary = _build_summary(display_name, total, label, dims)

    return CandidateScore(
        filename=resume.filename,
        display_name=display_name,
        total_score=total,
        label=label,
        dimensions=dims,
        summary=summary,
    )


def rank_candidates(
    jd: JobRequirements,
    resumes: list[ParsedResume],
    weights: dict[str, float] | None = None,
) -> list[CandidateScore]:
    """Score every resume against the JD and return them ranked best-first.

    TF-IDF vectors are fit fresh on (JD + this specific batch of resumes)
    rather than reused from JD-only analysis, so IDF weighting reflects
    what's actually distinctive within *this* candidate pool - exactly
    what a ranking (as opposed to a one-off similarity check) needs.
    """
    weights = weights or DEFAULT_WEIGHTS
    jd_tokens = nlp.tokenize(jd.raw_text)
    token_lists = [jd_tokens] + [nlp.tokenize(r.raw_text) for r in resumes]
    vectors = nlp.compute_tfidf(token_lists)
    jd_vector, resume_vectors = vectors[0], vectors[1:]

    scored = [
        score_candidate(jd, jd_vector, jd_tokens, resume, vec, weights)
        for resume, vec in zip(resumes, resume_vectors)
    ]
    scored.sort(key=lambda c: c.total_score, reverse=True)
    for i, candidate in enumerate(scored, start=1):
        candidate.rank = i
    return scored
