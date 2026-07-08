import { RotateCcw } from "lucide-react";
import type { Weights } from "../types";
import { DEFAULT_WEIGHTS } from "../types";

interface WeightsPanelProps {
  weights: Weights;
  onChange: (weights: Weights) => void;
}

const DIMENSION_LABELS: Record<keyof Weights, string> = {
  skills: "Skill match",
  experience: "Experience",
  education: "Education",
  keywords: "Keyword overlap",
  projects: "Projects",
};

export function WeightsPanel({ weights, onChange }: WeightsPanelProps) {
  const total = Object.values(weights).reduce((a, b) => a + b, 0) || 1;

  function setWeight(key: keyof Weights, raw: number) {
    onChange({ ...weights, [key]: raw });
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-lg font-medium text-ink">Scoring weights</h3>
        <button
          type="button"
          onClick={() => onChange(DEFAULT_WEIGHTS)}
          className="flex items-center gap-1 text-[12px] font-semibold text-muted hover:text-ink transition-colors"
        >
          <RotateCcw size={12} />
          Reset to default
        </button>
      </div>
      <div className="rounded-3xl bg-white border border-slate-200/70 shadow-sm p-5 space-y-4">
        {(Object.keys(DIMENSION_LABELS) as (keyof Weights)[]).map((key) => {
          const pct = Math.round((weights[key] / total) * 100);
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[13px] font-medium text-ink">{DIMENSION_LABELS[key]}</span>
                <span className="text-[12px] font-mono text-muted tabular-nums">{pct}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                value={weights[key]}
                onChange={(e) => setWeight(key, Number(e.target.value))}
                aria-label={`${DIMENSION_LABELS[key]} weight`}
                className="w-full h-1.5 rounded-full appearance-none bg-slate-100 accent-ink cursor-pointer"
              />
            </div>
          );
        })}
        <p className="text-[11px] text-slate-400 pt-1">
          Weights are normalized to add up to 100% automatically - relative proportions are what matter.
        </p>
      </div>
    </div>
  );
}
