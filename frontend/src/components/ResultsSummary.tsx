import { Eye, EyeOff, Download } from "lucide-react";
import type { Candidate } from "../types";
import { candidatesToCsv, downloadCsv } from "../lib/csv";

interface ResultsSummaryProps {
  candidates: Candidate[];
  blind: boolean;
  onToggleBlind: () => void;
}

export function ResultsSummary({ candidates, blind, onToggleBlind }: ResultsSummaryProps) {
  const avg = candidates.length
    ? candidates.reduce((sum, c) => sum + c.total_score, 0) / candidates.length
    : 0;
  const top = candidates[0];

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl bg-white border border-slate-200/70 shadow-sm px-6 py-4">
      <div className="flex flex-wrap gap-8">
        <div>
          <p className="text-[11px] text-muted uppercase tracking-wide">Candidates</p>
          <p className="font-display text-xl font-medium text-ink">{candidates.length}</p>
        </div>
        <div>
          <p className="text-[11px] text-muted uppercase tracking-wide">Average score</p>
          <p className="font-display text-xl font-medium text-ink">{avg.toFixed(0)}</p>
        </div>
        <div>
          <p className="text-[11px] text-muted uppercase tracking-wide">Top match</p>
          <p className="font-display text-xl font-medium text-ink">
            {top ? `${top.total_score.toFixed(0)}` : "-"}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onToggleBlind}
          aria-pressed={blind}
          className="flex items-center gap-1.5 bg-white px-4 py-2 rounded-full text-[12px] font-semibold text-ink border border-slate-200/60 shadow-sm hover:border-slate-300 transition-all"
        >
          {blind ? <EyeOff size={13} /> : <Eye size={13} />}
          {blind ? "Blind review on" : "Blind review off"}
        </button>
        <button
          type="button"
          onClick={() => downloadCsv(candidatesToCsv(candidates), "ranked-candidates.csv")}
          className="flex items-center gap-1.5 bg-ink-strong text-white px-4 py-2 rounded-full text-[12px] font-semibold shadow-sm"
        >
          <Download size={13} />
          Export CSV
        </button>
      </div>
    </div>
  );
}
