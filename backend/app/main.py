"""
FastAPI application.

Endpoints:
    GET  /api/health            - liveness check
    POST /api/analyze           - upload a JD + resumes, get ranked, explained results
    GET  /api/history           - list past sessions (see database.py for the
                                   ephemeral-filesystem caveat on Render Free)
    GET  /api/history/{id}      - full result of a past session
    DELETE /api/history/{id}    - remove a past session

Memory discipline for the free-tier target (512 MB RAM):
    Resumes are processed one at a time in a single pass - read bytes,
    extract text, immediately drop the bytes - rather than reading every
    upload into memory up front. Batch size and per-file size are capped
    in schemas.py specifically to keep worst-case memory bounded on a
    512 MB instance.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config, database
from .parsing.jd_analyzer import analyze_job_description
from .parsing.resume_parser import parse_resume
from .parsing.text_extraction import ExtractionError, extract_text
from .scoring.matching_engine import DEFAULT_WEIGHTS, rank_candidates
from .schemas import (
    MAX_FILE_SIZE_BYTES,
    MAX_JD_LENGTH_CHARS,
    MAX_RESUME_TEXT_CHARS,
    MAX_RESUMES_PER_BATCH,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume_screener")

app = FastAPI(title="Resume Screening & Candidate Ranking API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    database.init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(
    jd_text: str = Form(...),
    skills_weight: float = Form(DEFAULT_WEIGHTS["skills"]),
    experience_weight: float = Form(DEFAULT_WEIGHTS["experience"]),
    education_weight: float = Form(DEFAULT_WEIGHTS["education"]),
    keywords_weight: float = Form(DEFAULT_WEIGHTS["keywords"]),
    projects_weight: float = Form(DEFAULT_WEIGHTS["projects"]),
    resumes: list[UploadFile] = File(...),
) -> dict:
    jd_text = (jd_text or "").strip()
    if not jd_text:
        raise HTTPException(400, "Job description text is required.")
    if len(jd_text) > MAX_JD_LENGTH_CHARS:
        raise HTTPException(400, f"Job description is too long (max {MAX_JD_LENGTH_CHARS:,} characters).")

    if not resumes:
        raise HTTPException(400, "At least one resume file is required.")
    if len(resumes) > MAX_RESUMES_PER_BATCH:
        raise HTTPException(
            400,
            f"Too many resumes in one batch ({len(resumes)}). "
            f"This deployment is tuned for a 512 MB instance - max {MAX_RESUMES_PER_BATCH} per batch.",
        )

    weights = {
        "skills": skills_weight,
        "experience": experience_weight,
        "education": education_weight,
        "keywords": keywords_weight,
        "projects": projects_weight,
    }

    parsed_resumes = []
    errors = []

    for upload in resumes:
        filename = upload.filename or "unnamed"
        try:
            content = await upload.read()
            if len(content) > MAX_FILE_SIZE_BYTES:
                raise ExtractionError(
                    f"File is too large ({len(content) / 1_048_576:.1f} MB). "
                    f"Max {MAX_FILE_SIZE_BYTES / 1_048_576:.0f} MB per resume."
                )

            text = extract_text(filename, content)
            del content  # drop raw bytes before parsing; we only need text from here on

            if len(text) > MAX_RESUME_TEXT_CHARS:
                text = text[:MAX_RESUME_TEXT_CHARS]

            parsed_resumes.append(parse_resume(filename, text))
        except ExtractionError as exc:
            errors.append({"filename": filename, "error": str(exc)})
        except Exception:
            logger.exception("Unexpected error parsing %s", filename)
            errors.append({"filename": filename, "error": "Unexpected error while reading this file."})
        finally:
            await upload.close()

    if not parsed_resumes:
        raise HTTPException(
            422, {"message": "None of the uploaded files could be read.", "errors": errors}
        )

    jd = analyze_job_description(jd_text)
    ranked = rank_candidates(jd, parsed_resumes, weights)

    resumes_by_filename = {r.filename: r for r in parsed_resumes}

    candidates_out = []
    for score in ranked:
        resume = resumes_by_filename[score.filename]
        candidates_out.append(
            {
                "filename": score.filename,
                "display_name": score.display_name,
                "email": resume.email,
                "phone": resume.phone,
                "total_score": score.total_score,
                "label": score.label,
                "rank": score.rank,
                "summary": score.summary,
                "dimensions": {
                    name: {"score": d.score, "max_points": d.max_points, "detail": d.detail}
                    for name, d in score.dimensions.items()
                },
                "skills": resume.skills,
                "education_label": resume.education_label,
                "education_snippet": resume.education_snippet,
                "experience_years": resume.experience_years,
                "experience_source": resume.experience_source,
                "projects": [{"title": p.title, "snippet": p.snippet} for p in resume.projects],
                "raw_text_excerpt": resume.raw_text[:500],
            }
        )

    session_id = str(uuid4())
    result = {
        "session_id": session_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "job_description": {
            "required_skills": jd.required_skills,
            "nice_to_have_skills": jd.nice_to_have_skills,
            "required_experience_years": jd.required_experience_years,
            "required_education_label": jd.required_education_label,
            "top_keywords": jd.top_keywords,
        },
        "weights": weights,
        "candidates": candidates_out,
        "errors": errors,
    }

    database.save_session(session_id, jd_text, result)
    return result


@app.get("/api/history")
def get_history() -> list[dict]:
    return database.list_sessions()


@app.get("/api/history/{session_id}")
def get_history_item(session_id: str) -> dict:
    result = database.get_session(session_id)
    if result is None:
        raise HTTPException(404, "Session not found (it may have expired - see README re: Render free tier).")
    return result


@app.delete("/api/history/{session_id}")
def delete_history_item(session_id: str) -> dict:
    database.delete_session(session_id)
    return {"deleted": session_id}
