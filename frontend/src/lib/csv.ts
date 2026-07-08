import type { Candidate } from "../types";

function csvEscape(value: string | number | null): string {
  const s = value === null || value === undefined ? "" : String(value);
  if (/[",\n]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function candidatesToCsv(candidates: Candidate[]): string {
  const headers = [
    "Rank",
    "Name",
    "Email",
    "Phone",
    "Total Score",
    "Label",
    "Skills Score",
    "Experience Score",
    "Education Score",
    "Keywords Score",
    "Projects Score",
    "Matched Skills",
    "Missing Skills",
    "Experience (yrs)",
    "Education",
    "Filename",
  ];

  const rows = candidates.map((c) => [
    c.rank,
    c.display_name,
    c.email ?? "",
    c.phone ?? "",
    c.total_score,
    c.label,
    c.dimensions.skills.score,
    c.dimensions.experience.score,
    c.dimensions.education.score,
    c.dimensions.keywords.score,
    c.dimensions.projects.score,
    (c.dimensions.skills.detail.matched as string[] | undefined)?.join("; ") ?? "",
    (c.dimensions.skills.detail.missing as string[] | undefined)?.join("; ") ?? "",
    c.experience_years ?? "",
    c.education_label,
    c.filename,
  ]);

  return [headers, ...rows].map((row) => row.map(csvEscape).join(",")).join("\n");
}

export function downloadCsv(csv: string, filename: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
