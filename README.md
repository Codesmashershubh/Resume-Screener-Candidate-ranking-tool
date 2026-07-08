# Resume Screener

A free, explainable, self-hosted tool for screening resumes and ranking
candidates against a job description. Upload a JD and a batch of resumes,
get a ranked shortlist with a full breakdown of *why* each candidate scored
what they scored.

No paid APIs, no accounts, no per-resume cost. Everything runs on infrastructure
you control.

## Why this exists / how it's built

This started from a PRD calling for a hybrid deterministic + embedding-based
scoring engine (FastAPI + spaCy + sentence-transformers + MongoDB). A few
deliberate substitutions were made, explained here so they're not a surprise:

| PRD said | This uses | Why |
|---|---|---|
| sentence-transformers embeddings | Hand-rolled TF-IDF + cosine similarity (pure Python, no dependencies) | No model download (sentence-transformers pulls 90MB+ on first run), fully transparent math for the explainability layer, and it keeps memory use low enough to run on a 512 MB free-tier instance. |
| spaCy | Regex/taxonomy-based extraction | Same reasoning - spaCy's models are a multi-hundred-MB download; a curated ~150-skill taxonomy plus pattern matching gets most of the value with zero downloads. |
| MongoDB / Supabase | SQLite | Zero signup, zero external service, works offline. See **Deployment** below for the one real trade-off this brings on Render's free tier. |

The result is a system that's genuinely free to run indefinitely (not just
free during a trial), and where every number the UI shows can be traced back
to a specific rule or formula - which matters more for a hiring tool than a
marginally-better black-box similarity score.

## Features

- **Resume parsing** - PDF, DOCX, and TXT. Extracts name, email, phone,
  skills (from a ~150-term taxonomy across 7 disciplines), education level,
  total experience, and individual projects.
- **Job description analysis** - separates required vs. nice-to-have skills,
  detects required years of experience and education level, extracts top
  keywords.
- **Matching engine** - five weighted dimensions: Skills (40%), Experience
  (25%), Education (10%), Keyword overlap (15%), Projects (10%). Weights are
  adjustable per-run in the UI.
- **Ranking** - candidates sorted best-first with a plain-language label
  (Excellent / Strong / Moderate / Weak Match).
- **Explainability** - every score expands into matched/missing skills,
  an experience and education comparison, shared keywords, and a raw-text
  excerpt so you can verify anything the parser claims.
- **Blind review mode** - hides names/contact info in the results view until
  you choose to reveal them, so you can read rankings before names bias you.
- **CSV export** and a **history panel** of recent screenings (see the
  Render free-tier caveat below).

## Project structure

```
backend/    FastAPI app - parsing, scoring, and the HTTP API
frontend/   React + TypeScript + Tailwind v4 UI
sample-data/  A sample JD and 5 sample resumes to try immediately
render.yaml   Optional one-step deploy to Render's free tier
```

## Quickstart (local)

Requires Python 3.10+ and Node 18+.

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, paste `sample-data/job-description.txt`, upload
the five sample resumes, and click **Analyze & rank candidates**.

Run the backend test suite any time with zero extra installs:
```bash
cd backend && python3 tests/test_scoring.py
```

## Deployment (Render, free tier)

This was built and tuned specifically to run on Render's **Free** instance
type (512 MB RAM, 0.1 CPU) for the backend, and a **Free static site** for
the frontend. Two things to know going in:

1. **Cold starts.** Free web services spin down after 15 minutes of
   inactivity and take 30-60 seconds to wake back up on the next request.
   The UI shows a "backend looks asleep" notice when this is detected. This
   is a Render free-tier characteristic, not something a lighter app can
   avoid - the workaround is a paid instance (or an external uptime pinger,
   which isn't included here since it works against the spirit of a free
   tier).
2. **Ephemeral disk.** Free web services can't attach a persistent disk, so
   the SQLite history file is wiped on every redeploy/restart/cold-start.
   Screening itself is unaffected (each request is fully self-contained),
   but the "recent screenings" list will reset more often than you'd expect
   for a low-traffic deployment. To fix this: attach a persistent disk on a
   paid instance and set `DATABASE_PATH` to a path inside it, or swap
   `backend/app/database.py` for Render's free Postgres (works without a
   disk since it's a separate managed service - just note free Postgres
   itself expires 30 days after creation).

### Option A: manual (recommended the first time)

1. Push this repo to GitHub.
2. In Render: **New -> Web Service**, point at the repo, set:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Instance type: Free
3. In Render: **New -> Static Site**, point at the repo, set:
   - Root directory: `frontend`
   - Build command: `npm install && npm run build`
   - Publish directory: `dist`
4. Once both are live, copy each URL and set:
   - On the backend service: env var `ALLOWED_ORIGINS` = your frontend's URL
   - On the frontend service: env var `VITE_API_URL` = your backend's URL,
     then **manually trigger a redeploy** (Vite bakes this in at build time,
     so just changing the env var isn't enough).

### Option B: Blueprint (one step, with a manual follow-up)

Push to GitHub, then in Render choose **New -> Blueprint** and point it at
this repo - it reads `render.yaml` and provisions both services. You'll
still need to do step 4 above once, since neither service's URL exists
until after the first deploy.

## Scoring methodology

For a batch of resumes against one job description:

- **Skills (40%)** - the fraction of the JD's required skills found on the
  resume (both sides use the same ~150-term taxonomy across Engineering,
  Data & Analytics, Product & Design, Marketing & Growth, Sales & Business,
  Finance & Operations, and People & Leadership).
- **Experience (25%)** - resume years vs. required years, capped at full
  credit once met. If the JD doesn't state a requirement, full credit is
  given by default (you can't fault a candidate for an unstated bar).
  Years come from an explicit statement on the resume if present ("5+ years
  of experience"), otherwise from the overall span between the earliest
  start date and latest end date/"Present" found in the text - see
  **Limitations** below for what that trade-off means in practice.
- **Education (10%)** - ordinal comparison (High School < Associate <
  Bachelor's < Master's < Doctorate) between what's required and what's on
  the resume.
- **Keyword overlap (15%)** - TF-IDF cosine similarity between the full JD
  text and the full resume text, computed fresh across the JD + the whole
  batch so it reflects what's actually distinctive in *this* candidate pool.
- **Projects (10%)** - partly presence/count of a Projects section, partly
  TF-IDF relevance of that section's text to the JD.

Weights are configurable per run in the UI and always renormalized to sum
to 100.

## Limitations (read this before relying on it for real hiring decisions)

- **Parsing is heuristic, not perfect.** Name/education/experience
  extraction uses regex and layout patterns, not a trained model. Unusual
  resume formats (heavy graphics, multi-column layouts, non-English
  resumes) will parse worse. The raw-text excerpt in each candidate's
  explainability panel exists specifically so you can verify anything that
  looks off.
- **No OCR.** Scanned/image-only PDFs will be rejected with a clear error
  rather than silently scoring as blank.
- **Experience estimation can overcount.** When a resume has no explicit
  "X years of experience" statement, the fallback estimates experience from
  the *overall span* of dates found (earliest start to latest end/Present),
  not a role-by-role sum filtered by relevance. A candidate with a long
  employment history that includes unrelated roles can score higher on this
  dimension than their relevant experience alone would warrant. Always
  check the note next to the Experience score, which says whether the
  number was stated or estimated.
- **This is a decision-support tool, not a decision-maker.** Treat scores as
  a starting point for a human reviewer, not a pass/fail gate - and be
  mindful of applicable employment and anti-discrimination requirements in
  your jurisdiction when using any automated screening process.

## Extending this

- Swap `backend/app/scoring/nlp_utils.py`'s TF-IDF for real sentence
  embeddings (sentence-transformers, or an API-based embedding model) if
  you're deploying somewhere with more memory and don't mind the download.
- Swap SQLite for Postgres in `backend/app/database.py` for durable history
  on a platform with ephemeral disks.
- The skills taxonomy (`backend/app/parsing/skills_taxonomy.py`) is a plain
  Python dict - extend it with domain-specific skills for your use case.
- The PRD this was built from also flagged bias detection, multi-language
  support, GitHub integration, and AI-generated interview questions as
  future work. Blind review mode here is a small, concrete step toward the
  first one; the rest are open.

## License

MIT - see `LICENSE`.
