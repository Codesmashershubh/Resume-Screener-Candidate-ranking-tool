import { useEffect, useState } from "react";

interface ScoreRingProps {
  score: number; // 0-100
  size?: number;
  label?: string;
}

const LABEL_COLORS: Record<string, string> = {
  "Excellent Match": "#0a1b33",
  "Strong Match": "#0a1b33",
  "Moderate Match": "#b45309",
  "Weak Match": "#94a3b8",
};

export function ScoreRing({ score, size = 64, label }: ScoreRingProps) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const stroke = 6;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;

  useEffect(() => {
    // Purposeful, single animation: the score "filling in" on first render,
    // not decorative motion elsewhere on the card.
    const id = requestAnimationFrame(() => setAnimatedScore(score));
    return () => cancelAnimationFrame(id);
  }, [score]);

  const offset = circumference - (Math.min(Math.max(animatedScore, 0), 100) / 100) * circumference;
  const color = (label && LABEL_COLORS[label]) || "#0a1b33";

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#f1f5f9" strokeWidth={stroke} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 900ms cubic-bezier(0.22, 1, 0.36, 1)" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-display text-[15px] font-semibold text-ink tabular-nums">{Math.round(score)}</span>
      </div>
    </div>
  );
}
