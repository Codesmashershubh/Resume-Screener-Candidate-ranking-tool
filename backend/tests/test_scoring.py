"""
Tests for the parsing + scoring pipeline.

Runs with plain `python3 tests/test_scoring.py` (zero dependencies - the
whole scoring engine is pure stdlib) and is also pytest-compatible:
`pip install pytest && pytest` once you have a virtualenv set up.
"""

from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.parsing.jd_analyzer import analyze_job_description
from app.parsing.resume_parser import parse_resume
from app.scoring.matching_engine import rank_candidates, DEFAULT_WEIGHTS, normalize_weights
from app.scoring import nlp_utils as nlp
from app.parsing.skills_taxonomy import find_skills_in_text

JD_TEXT = """Senior Frontend Engineer

We are looking for a Senior Frontend Engineer with 4+ years of experience.
Required: React, TypeScript, CSS, Git, REST APIs.
Bachelor's degree in Computer Science or related field required.
Nice to have: GraphQL, Next.js, Docker.
"""

STRONG_RESUME = """Jane Doe
jane@email.com | (415) 555-0142

SUMMARY
Frontend engineer with 5+ years of experience building React applications.

EXPERIENCE
Senior Frontend Engineer, Acme Corp, Jan 2020 - Present
- Led migration to React and TypeScript, built REST API integrations with Git-based CI

EDUCATION
Bachelor of Science in Computer Science, State University, 2018

PROJECTS
Component Library: Built with React, TypeScript and CSS, used across teams.

SKILLS
React, TypeScript, CSS, Git, REST APIs, GraphQL, Docker
"""

WEAK_RESUME = """John Smith
john@email.com

SUMMARY
Marketing coordinator with experience in SEO and content strategy.

SKILLS
SEO, Content Marketing, Google Analytics
"""


def test_skill_extraction_basic():
    skills = find_skills_in_text("Built REST APIs with FastAPI, deployed on AWS.")
    assert skills == {"REST APIs", "FastAPI", "AWS"}


def test_skill_extraction_ignores_ambiguous_lowercase_tokens():
    # "go" should not match the Go language when used as an ordinary verb
    assert "Go" not in find_skills_in_text("We need to go to market quickly.")
    assert "Go" in find_skills_in_text("Backend services written in Go.")


def test_tfidf_ranks_relevant_document_higher():
    jd = "Python developer with AWS and React experience"
    close_match = "Experienced Python engineer, built APIs and deployed on AWS"
    far_match = "Marketing specialist skilled in SEO and copywriting"
    vecs = nlp.compute_tfidf([nlp.tokenize(d) for d in (jd, close_match, far_match)])
    sim_close = nlp.cosine_similarity(vecs[0], vecs[1])
    sim_far = nlp.cosine_similarity(vecs[0], vecs[2])
    assert sim_close > sim_far
    assert sim_far == 0.0


def test_weights_normalize_to_100():
    normalized = normalize_weights({"skills": 4, "experience": 2, "education": 1, "keywords": 2, "projects": 1})
    assert abs(sum(normalized.values()) - 100.0) < 1e-9


def test_weights_normalize_handles_all_zero_gracefully():
    # Should fall back to defaults rather than dividing by zero.
    normalized = normalize_weights({"skills": 0, "experience": 0, "education": 0, "keywords": 0, "projects": 0})
    assert abs(sum(normalized.values()) - 100.0) < 1e-9


def test_resume_parser_extracts_expected_fields():
    parsed = parse_resume("jane.txt", STRONG_RESUME)
    assert parsed.name == "Jane Doe"
    assert parsed.email == "jane@email.com"
    assert "(415) 555-0142" in (parsed.phone or "")
    assert {"React", "TypeScript", "CSS", "Git"}.issubset(set(parsed.skills))
    assert parsed.education_level == 3
    assert parsed.experience_years == 5.0
    assert parsed.experience_source == "stated"
    assert len(parsed.projects) == 1
    assert parsed.projects[0].title == "Component Library"


def test_ranking_orders_strong_candidate_first():
    jd = analyze_job_description(JD_TEXT)
    resumes = [parse_resume("weak.txt", WEAK_RESUME), parse_resume("strong.txt", STRONG_RESUME)]
    ranked = rank_candidates(jd, resumes, DEFAULT_WEIGHTS)

    assert ranked[0].filename == "strong.txt"
    assert ranked[0].rank == 1
    assert ranked[1].filename == "weak.txt"
    assert ranked[0].total_score > ranked[1].total_score
    assert ranked[0].total_score >= 70  # should land in Strong/Excellent territory
    assert ranked[1].total_score < 40   # should land in Weak territory


def test_score_never_exceeds_100_or_goes_negative():
    jd = analyze_job_description(JD_TEXT)
    resumes = [parse_resume("weak.txt", WEAK_RESUME), parse_resume("strong.txt", STRONG_RESUME)]
    for candidate in rank_candidates(jd, resumes, DEFAULT_WEIGHTS):
        assert 0.0 <= candidate.total_score <= 100.01  # tiny float slack


def test_jd_analyzer_separates_required_from_nice_to_have():
    jd = analyze_job_description(JD_TEXT)
    assert "React" in jd.required_skills
    assert "TypeScript" in jd.required_skills
    assert "Docker" in jd.nice_to_have_skills
    assert "Docker" not in jd.required_skills
    assert jd.required_experience_years == 4
    assert jd.required_education_level == 3


ALL_TESTS = [obj for name, obj in list(globals().items()) if name.startswith("test_")]


def _run_as_script():
    passed, failed = 0, 0
    for test_fn in ALL_TESTS:
        try:
            test_fn()
            print(f"PASS  {test_fn.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL  {test_fn.__name__}: {exc}")
            failed += 1
        except Exception as exc:
            print(f"ERROR {test_fn.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    _run_as_script()
