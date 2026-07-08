import { useState } from "react";
import { ChevronDown, Mail, Phone } from "lucide-react";
import type { Candidate } from "../types";
import { ScoreRing } from "./ScoreRing";
import { ExplainabilityDetail } from "./ExplainabilityDetail";
import { cn } from "../lib/utils";

interface CandidateCardProps {
  candidate: Candidate;
  blind: boolean;
}

const LABEL_STYLES: Record<string, string> = {
  "Excellent Match": "bg-highlight-soft text-amber-900",
  "Strong Match": "bg-slate-100 text-ink",
  "Moderate Match": "bg-slate-100 text-slate-600",
  "Weak Match": "bg-slate-100 text-slate-400",
};

export function CandidateCard({ candidate, blind }: CandidateCardProps) {
  const [expanded, setExpanded] = useState(false);
  const displayName = blind ? `Candidate ${candidate.rank}` : candidate.display_name;

  return (
    <div className="rounded-3xl bg-white border border-slate-200/70 shadow-sm p-5">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-4 text-left"
        aria-expanded={expanded}
      >
        <span className="font-display text-[13px] font-semibold text-slate-300 w-6 shrink-0">
          #{candidate.rank}
        </span>
        <ScoreRing score={candidate.total_score} label={candidate.label} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-display text-[15px] font-medium text-ink truncate">{displayName}</span>
            <span className={cn("text-[11px] font-semibold px-2 py-0.5 rounded-full shrink-0", LABEL_STYLES[candidate.label])}>
              {candidate.label}
            </span>
          </div>
          {!blind && (candidate.email || candidate.phone) && (
            <div className="flex items-center gap-3 mt-1">
              {candidate.email && (
                <span className="flex items-center gap-1 text-[11px] text-muted">
                  <Mail size={11} /> {candidate.email}
                </span>
              )}
              {candidate.phone && (
                <span className="flex items-center gap-1 text-[11px] text-muted">
                  <Phone size={11} /> {candidate.phone}
                </span>
              )}
            </div>
          )}
          <p className="text-[12px] text-muted mt-1.5 line-clamp-2">{candidate.summary}</p>
        </div>
        <ChevronDown
          size={16}
          className={cn("text-slate-300 shrink-0 transition-transform duration-200", expanded && "rotate-180")}
        />
      </button>

      {expanded && <ExplainabilityDetail candidate={candidate} />}
    </div>
  );
}
