export interface Weights {
  skills: number;
  experience: number;
  education: number;
  keywords: number;
  projects: number;
}

export const DEFAULT_WEIGHTS: Weights = {
  skills: 40,
  experience: 25,
  education: 10,
  keywords: 15,
  projects: 10,
};

export interface DimensionScore {
  score: number;
  max_points: number;
  detail: Record<string, unknown>;
}

export interface ProjectEntry {
  title: string;
  snippet: string;
}

export interface Candidate {
  filename: string;
  display_name: string;
  email: string | null;
  phone: string | null;
  total_score: number;
  label: string;
  rank: number;
  summary: string;
  dimensions: {
    skills: DimensionScore;
    experience: DimensionScore;
    education: DimensionScore;
    keywords: DimensionScore;
    projects: DimensionScore;
  };
  skills: string[];
  education_label: string;
  education_snippet: string | null;
  experience_years: number | null;
  experience_source: "stated" | "estimated_from_dates" | "not_found";
  projects: ProjectEntry[];
  raw_text_excerpt: string;
}

export interface JobRequirementsOut {
  required_skills: string[];
  nice_to_have_skills: string[];
  required_experience_years: number | null;
  required_education_label: string;
  top_keywords: string[];
}

export interface FileError {
  filename: string;
  error: string;
}

export interface AnalyzeResponse {
  session_id: string;
  created_at: string;
  job_description: JobRequirementsOut;
  weights: Weights;
  candidates: Candidate[];
  errors: FileError[];
}

export interface HistoryItem {
  session_id: string;
  created_at: string;
  jd_excerpt: string;
  candidate_count: number;
  top_candidate_name: string | null;
  top_candidate_score: number | null;
}
