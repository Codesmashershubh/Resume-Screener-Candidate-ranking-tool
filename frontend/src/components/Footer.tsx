export function Footer() {
  return (
    <footer className="max-w-[1400px] mx-auto px-6 py-10 mt-6">
      <div className="rounded-3xl bg-white border border-slate-200/70 p-6 text-[12px] text-muted leading-relaxed">
        <p className="text-ink font-medium mb-1">Runs entirely on infrastructure you control.</p>
        <p>
          Resumes are parsed and scored on this server and are not sent to any third-party API or
          model provider. Free and open source - no accounts, no API keys, no per-resume cost.
        </p>
        <p className="mt-3">
          This tool is meant to help a human reviewer work faster, not to replace their judgment.
          Scores are heuristic and explainable, not infallible - always sanity-check results,
          especially near cutoff thresholds, and be mindful of applicable employment and
          anti-discrimination requirements in your jurisdiction when using any automated
          screening tool.
        </p>
      </div>
    </footer>
  );
}
