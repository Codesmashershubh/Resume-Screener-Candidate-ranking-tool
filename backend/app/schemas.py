"""
Request/response schemas and hard limits for the API.

The limits here (MAX_RESUMES_PER_BATCH, MAX_FILE_SIZE_BYTES) exist
specifically because the default deployment target is a free-tier instance
with 512 MB of RAM and 0.1 shared CPU. They're conservative on purpose -
loosen them in your own deployment via the environment variables in
config.py if you're running on a bigger instance.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator

MAX_RESUMES_PER_BATCH = 15
MAX_FILE_SIZE_BYTES = 4 * 1024 * 1024        # 4 MB per resume
MAX_JD_LENGTH_CHARS = 20_000                  # ~3,500 words, generous for any JD
MAX_RESUME_TEXT_CHARS = 50_000                # bounds worst-case pathological input


class WeightsInput(BaseModel):
    skills: float = Field(default=40.0, ge=0)
    experience: float = Field(default=25.0, ge=0)
    education: float = Field(default=10.0, ge=0)
    keywords: float = Field(default=15.0, ge=0)
    projects: float = Field(default=10.0, ge=0)

    @field_validator("skills", "experience", "education", "keywords", "projects")
    @classmethod
    def _cap_individual_weight(cls, v: float) -> float:
        return min(v, 1000.0)  # guard against absurd values; normalization handles the rest


class DimensionScoreOut(BaseModel):
    score: float
    max_points: float
    detail: dict


class CandidateOut(BaseModel):
    filename: str
    display_name: str
    email: str | None
    phone: str | None
    total_score: float
    label: str
    rank: int
    summary: str
    dimensions: dict[str, DimensionScoreOut]
    skills: list[str]
    education_label: str
    education_snippet: str | None
    experience_years: float | None
    experience_source: str
    projects: list[dict]
    raw_text_excerpt: str


class JobRequirementsOut(BaseModel):
    required_skills: list[str]
    nice_to_have_skills: list[str]
    required_experience_years: int | None
    required_education_label: str
    top_keywords: list[str]


class FileError(BaseModel):
    filename: str
    error: str


class AnalyzeResponse(BaseModel):
    session_id: str
    created_at: str
    job_description: JobRequirementsOut
    weights: dict[str, float]
    candidates: list[CandidateOut]
    errors: list[FileError]


class HistoryItem(BaseModel):
    session_id: str
    created_at: str
    jd_excerpt: str
    candidate_count: int
    top_candidate_name: str | None
    top_candidate_score: float | None
