import { FileText } from "lucide-react";

interface JDInputProps {
  value: string;
  onChange: (value: string) => void;
}

const EXAMPLE_JD = `Senior Frontend Engineer

We're looking for a Senior Frontend Engineer with 4+ years of experience building production web applications.

Required:
- React, TypeScript, CSS, Git, REST APIs
- Bachelor's degree in Computer Science or a related field

Nice to have:
- GraphQL, Next.js, Docker`;

export function JDInput({ value, onChange }: JDInputProps) {
  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <label htmlFor="jd-text" className="font-display text-lg font-medium text-ink">
          Job description
        </label>
        <button
          type="button"
          onClick={() => onChange(EXAMPLE_JD)}
          className="text-[12px] font-semibold text-muted hover:text-ink transition-colors"
        >
          Use an example
        </button>
      </div>
      <div className="relative rounded-3xl bg-white border border-slate-200/70 shadow-sm focus-within:border-slate-400 transition-colors">
        <FileText size={16} className="absolute top-4 left-4 text-slate-300" />
        <textarea
          id="jd-text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Paste the job description here - requirements, must-have skills, years of experience, education, anything you'd normally screen for."
          rows={9}
          className="w-full resize-y bg-transparent rounded-3xl pl-11 pr-4 py-4 text-[14px] leading-relaxed text-ink placeholder:text-slate-400 focus:outline-none"
        />
      </div>
    </div>
  );
}
