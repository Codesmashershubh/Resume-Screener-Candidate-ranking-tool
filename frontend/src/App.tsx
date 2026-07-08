import { useEffect, useRef, useState } from "react";
import { Loader2, AlertTriangle } from "lucide-react";
import { Hero } from "./components/Hero";
import { CategoryMarquee } from "./components/CategoryMarquee";
import { JDInput } from "./components/JDInput";
import { WeightsPanel } from "./components/WeightsPanel";
import { ResumeDropzone } from "./components/ResumeDropzone";
import { ResultsSummary } from "./components/ResultsSummary";
import { CandidateCard } from "./components/CandidateCard";
import { HistoryPanel } from "./components/HistoryPanel";
import { Footer } from "./components/Footer";
import { analyzeResumes, ApiError, checkHealth, fetchHistoryItem } from "./lib/api";
import { DEFAULT_WEIGHTS, type AnalyzeResponse, type Weights } from "./types";

const MAX_FILES = 15;
const MAX_FILE_SIZE_BYTES = 4 * 1024 * 1024;

export default function App() {
  const [jdText, setJdText] = useState("");
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS);
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [blind, setBlind] = useState(false);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  const [backendAsleep, setBackendAsleep] = useState(false);

  const workspaceRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    checkHealth().then((up) => setBackendAsleep(!up));
  }, []);

  function scrollToWorkspace() {
    workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function handleAnalyze() {
    if (!jdText.trim()) {
      setError("Add a job description first.");
      return;
    }
    if (files.length === 0) {
      setError("Upload at least one resume.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await analyzeResumes(jdText, weights, files);
      setResult(data);
      setHistoryRefreshKey((k) => k + 1);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong while analyzing. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectHistory(sessionId: string) {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHistoryItem(sessionId);
      setResult(data);
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch {
      setError("Could not load that session - it may have expired.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen px-4 md:px-6 py-8">
      <Hero onStart={scrollToWorkspace} />
      <CategoryMarquee />

      <main ref={workspaceRef} id="how-it-works" className="max-w-3xl mx-auto mt-20 space-y-14">
        <div>
          <h2 className="font-display text-2xl font-medium text-ink text-center">How it works</h2>
          <p className="text-[13px] text-muted text-center mt-2 max-w-lg mx-auto">
            Three steps, all running on this server - nothing is sent to a third-party AI provider.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-5">
          {[
            { n: 1, title: "Describe the role", body: "Paste the job description - requirements and all." },
            { n: 2, title: "Upload resumes", body: "Drop in as many candidates as you're screening." },
            { n: 3, title: "Get a ranked, explained shortlist", body: "Every score is broken down and adjustable." },
          ].map((step) => (
            <div key={step.n} className="rounded-3xl bg-white border border-slate-200/70 p-5">
              <span className="font-display text-[13px] font-semibold text-highlight">
                0{step.n}
              </span>
              <p className="font-display text-[15px] font-medium text-ink mt-2">{step.title}</p>
              <p className="text-[12px] text-muted mt-1 leading-relaxed">{step.body}</p>
            </div>
          ))}
        </div>

        {backendAsleep && (
          <div className="flex items-center gap-2 rounded-2xl bg-amber-50 border border-amber-200/60 px-4 py-3 text-[12px] text-amber-800">
            <AlertTriangle size={14} className="shrink-0" />
            The backend looks asleep (normal on a free-tier deploy after inactivity) - the first
            request below may take up to a minute while it wakes up.
          </div>
        )}

        <JDInput value={jdText} onChange={setJdText} />
        <div id="methodology">
          <WeightsPanel weights={weights} onChange={setWeights} />
        </div>
        <ResumeDropzone
          files={files}
          onChange={setFiles}
          maxFiles={MAX_FILES}
          maxSizeBytes={MAX_FILE_SIZE_BYTES}
        />

        {error && (
          <div className="flex items-center gap-2 rounded-2xl bg-red-50 border border-red-200/60 px-4 py-3 text-[12px] text-red-700">
            <AlertTriangle size={14} className="shrink-0" />
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-ink-strong text-white py-4 rounded-full text-[14px] font-semibold shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading && <Loader2 size={16} className="animate-spin" />}
          {loading ? "Analyzing\u2026" : "Analyze & rank candidates"}
        </button>

        <HistoryPanel onSelect={handleSelectHistory} refreshKey={historyRefreshKey} />
      </main>

      {result && (
        <section ref={resultsRef} id="results" className="max-w-3xl mx-auto mt-16 space-y-5">
          <h2 className="font-display text-2xl font-medium text-ink text-center mb-2">Results</h2>

          <div className="rounded-3xl bg-white border border-slate-200/70 p-5 text-[12px] text-muted">
            <p className="text-ink font-medium mb-1">Detected from the job description</p>
            <p>
              Required skills: {result.job_description.required_skills.join(", ") || "none detected"}
              {result.job_description.nice_to_have_skills.length > 0 &&
                ` \u00b7 Nice to have: ${result.job_description.nice_to_have_skills.join(", ")}`}
              {result.job_description.required_experience_years != null &&
                ` \u00b7 ${result.job_description.required_experience_years}+ years experience`}
              {` \u00b7 ${result.job_description.required_education_label}`}
            </p>
          </div>

          {result.errors.length > 0 && (
            <div className="rounded-2xl bg-amber-50 border border-amber-200/60 px-4 py-3 text-[12px] text-amber-800">
              {result.errors.map((e) => (
                <p key={e.filename}>
                  {e.filename}: {e.error}
                </p>
              ))}
            </div>
          )}

          <ResultsSummary candidates={result.candidates} blind={blind} onToggleBlind={() => setBlind((v) => !v)} />

          <div className="space-y-3">
            {result.candidates.map((c) => (
              <CandidateCard key={c.filename} candidate={c} blind={blind} />
            ))}
          </div>
        </section>
      )}

      <Footer />
    </div>
  );
}
