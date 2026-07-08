import type { AnalyzeResponse, HistoryItem, Weights } from "../types";

// Vite build-time env var. Falls back to localhost for local dev.
// On Render, set VITE_API_URL to your backend's onrender.com URL and
// rebuild the static site (Vite bakes this in at build time).
const API_URL = (import.meta.env.VITE_API_URL as string | undefined) || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (body?.detail?.message) return body.detail.message as string;
    return JSON.stringify(body);
  } catch {
    return res.statusText || "Request failed";
  }
}

export async function analyzeResumes(
  jdText: string,
  weights: Weights,
  files: File[],
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("jd_text", jdText);
  form.append("skills_weight", String(weights.skills));
  form.append("experience_weight", String(weights.experience));
  form.append("education_weight", String(weights.education));
  form.append("keywords_weight", String(weights.keywords));
  form.append("projects_weight", String(weights.projects));
  for (const file of files) {
    form.append("resumes", file);
  }

  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/analyze`, { method: "POST", body: form });
  } catch {
    // fetch() itself threw - the backend is unreachable (down, wrong URL,
    // CORS misconfiguration, or - on a Render free instance - possibly
    // still waking up from a cold start).
    throw new ApiError("Could not reach the backend. It may still be starting up - try again in a moment.", 0);
  }
  if (!res.ok) {
    throw new ApiError(await parseErrorBody(res), res.status);
  }
  return res.json();
}

export async function fetchHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_URL}/api/history`);
  if (!res.ok) throw new ApiError(await parseErrorBody(res), res.status);
  return res.json();
}

export async function fetchHistoryItem(sessionId: string): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_URL}/api/history/${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new ApiError(await parseErrorBody(res), res.status);
  return res.json();
}

export async function deleteHistoryItem(sessionId: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/history/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new ApiError(await parseErrorBody(res), res.status);
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_URL}/api/health`, { signal: AbortSignal.timeout(5000) });
    return res.ok;
  } catch {
    return false;
  }
}
