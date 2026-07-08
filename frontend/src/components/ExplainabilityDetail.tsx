import type { Candidate } from "../types";

function Bar({ score, max }: { score: number; max: number }) {
  const pct = max > 0 ? Math.min((score / max) * 100, 100) : 0;
  return (
    <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
      <div className="h-full rounded-full bg-ink" style={{ width: `${pct}%` }} />
    </div>
  );
}

function SkillChips({ items, tone }: { items: string[]; tone: "matched" | "missing" }) {
  if (!items.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {items.map((s) => (
        <span
          key={s}
          className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
            tone === "matched" ? "bg-highlight-soft text-amber-900" : "bg-slate-100 text-slate-500"
          }`}
        >
          {s}
        </span>
      ))}
    </div>
  );
}

export function ExplainabilityDetail({ candidate }: { candidate: Candidate }) {
  const { skills, experience, education, keywords, projects } = candidate.dimensions;
  const matched = (skills.detail.matched as string[]) ?? [];
  const missing = (skills.detail.missing as string[]) ?? [];
  const sharedKeywords = (keywords.detail.shared_keywords as string[]) ?? [];
  const projectTitles = (projects.detail.titles as string[]) ?? [];

  return (
    <div className="border-t border-slate-100 pt-5 mt-5 space-y-5">
      <div>
        <div className="flex items-center justify-between text-[13px] mb-1.5">
          <span className="font-medium text-ink">Skills</span>
          <span className="font-mono text-muted tabular-nums">
            {skills.score.toFixed(0)}/{skills.max_points.toFixed(0)}
          </span>
        </div>
        <Bar score={skills.score} max={skills.max_points} />
        <p className="text-[12px] text-muted mt-2">
          Matched {(skills.detail.matched_count as number) ?? 0} of {(skills.detail.required_count as number) ?? 0}{" "}
          required skills.
        </p>
        <SkillChips items={matched} tone="matched" />
        <SkillChips items={missing} tone="missing" />
      </div>

      <div>
        <div className="flex items-center justify-between text-[13px] mb-1.5">
          <span className="font-medium text-ink">Experience</span>
          <span className="font-mono text-muted tabular-nums">
            {experience.score.toFixed(0)}/{experience.max_points.toFixed(0)}
          </span>
        </div>
        <Bar score={experience.score} max={experience.max_points} />
        <p className="text-[12px] text-muted mt-2">
          {experience.detail.note
            ? (experience.detail.note as string)
            : `${candidate.experience_years ?? "?"} years on resume vs. ${
                experience.detail.required_years
              }-year requirement (${experience.detail.source === "estimated_from_dates" ? "estimated from dates listed" : "explicitly stated"}).`}
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between text-[13px] mb-1.5">
          <span className="font-medium text-ink">Education</span>
          <span className="font-mono text-muted tabular-nums">
            {education.score.toFixed(0)}/{education.max_points.toFixed(0)}
          </span>
        </div>
        <Bar score={education.score} max={education.max_points} />
        <p className="text-[12px] text-muted mt-2">
          {(education.detail.note as string) ??
            `${candidate.education_label} vs. ${education.detail.required} required.`}
          {candidate.education_snippet && (
            <span className="text-slate-400"> ("{candidate.education_snippet}")</span>
          )}
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between text-[13px] mb-1.5">
          <span className="font-medium text-ink">Keyword overlap</span>
          <span className="font-mono text-muted tabular-nums">
            {keywords.score.toFixed(0)}/{keywords.max_points.toFixed(0)}
          </span>
        </div>
        <Bar score={keywords.score} max={keywords.max_points} />
        <p className="text-[12px] text-muted mt-2">
          {sharedKeywords.length
            ? `Shared terms: ${sharedKeywords.slice(0, 8).join(", ")}`
            : "No significant term overlap with the job description."}
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between text-[13px] mb-1.5">
          <span className="font-medium text-ink">Projects</span>
          <span className="font-mono text-muted tabular-nums">
            {projects.score.toFixed(0)}/{projects.max_points.toFixed(0)}
          </span>
        </div>
        <Bar score={projects.score} max={projects.max_points} />
        <p className="text-[12px] text-muted mt-2">
          {projects.detail.note ? (projects.detail.note as string) : `${projectTitles.join(", ")}`}
        </p>
      </div>

      <details className="text-[12px] text-slate-400">
        <summary className="cursor-pointer hover:text-slate-600 transition-colors">
          View raw resume excerpt (for verification)
        </summary>
        <p className="mt-2 font-mono text-[11px] leading-relaxed bg-slate-50 rounded-2xl p-3 whitespace-pre-wrap">
          {candidate.raw_text_excerpt}
          {candidate.raw_text_excerpt.length >= 500 && "\u2026"}
        </p>
      </details>
    </div>
  );
}
