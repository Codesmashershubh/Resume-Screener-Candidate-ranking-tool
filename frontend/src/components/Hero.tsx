import type { CSSProperties } from "react";
import { motion } from "motion/react";
import { FloatingNav } from "./FloatingNav";

interface HeroProps {
  onStart: () => void;
}

/** A quiet, ambient stack of resume-card silhouettes - the one deliberate
 * visual flourish on the page, standing in for "many resumes -> one
 * ranked signal" instead of a generic decorative background. */
function ResumeStack() {
  const cards = [
    { w: 148, top: 40, left: 40, rot: -6, delay: 0, opacity: 0.5 },
    { w: 168, top: 90, left: 110, rot: 4, delay: 0.6, opacity: 0.65 },
    { w: 158, top: 150, left: 55, rot: -2, delay: 1.2, opacity: 0.85 },
    { w: 176, top: 210, left: 120, rot: 3, delay: 1.8, opacity: 1 },
  ];
  return (
    <div className="hidden md:block absolute inset-0 pointer-events-none select-none" aria-hidden="true">
      {cards.map((c, i) => (
        <div
          key={i}
          className="animate-drift absolute rounded-2xl bg-white border border-slate-200 shadow-[0_20px_50px_-15px_rgba(10,27,51,0.15)]"
          style={
            {
              width: c.w,
              height: c.w * 1.28,
              top: c.top,
              left: c.left,
              opacity: c.opacity,
              "--drift-rotate": `${c.rot}deg`,
              transform: `rotate(${c.rot}deg)`,
              animationDelay: `${c.delay}s`,
            } as CSSProperties
          }
        >
          <div className="p-4 space-y-2">
            <div className="w-8 h-8 rounded-full bg-slate-100" />
            <div className="h-1.5 rounded-full bg-slate-100 w-4/5" />
            <div className="h-1.5 rounded-full bg-slate-100 w-3/5" />
            <div className="h-1.5 rounded-full bg-slate-100 w-full mt-3" />
            <div className="h-1.5 rounded-full bg-slate-100 w-4/5" />
            <div className="h-1.5 rounded-full bg-slate-100 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function Hero({ onStart }: HeroProps) {
  return (
    <section className="relative w-full max-w-[1400px] mx-auto rounded-[48px] bg-white border border-slate-200/50 shadow-[0_40px_100px_-20px_rgba(0,0,0,0.03)] overflow-hidden min-h-[560px] md:h-[600px] flex flex-col">
      <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden select-none">
        <div className="absolute -top-32 -right-32 w-[520px] h-[520px] rounded-full bg-gradient-to-br from-slate-50 to-amber-50" />
        <ResumeStack />
      </div>

      <div className="relative z-20 flex-1 px-8 md:px-16 pt-12 md:pt-16 flex flex-col items-start">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="max-w-xl"
        >
          <p className="font-sans text-[12px] font-semibold tracking-wide text-highlight/80 uppercase mb-4">
            Free &middot; Open source &middot; Runs on your own infrastructure
          </p>
          <h1 className="font-display text-[42px] md:text-[56px] font-medium tracking-tight text-ink leading-[1.05]">
            Turn a pile of resumes
            <br />
            into a ranked shortlist
          </h1>
          <p className="font-sans text-[14px] md:text-[15px] text-muted mt-5 max-w-md leading-relaxed">
            Paste a job description, drop in resumes, and get an explainable,
            weighted ranking in seconds - every score broken down so you can
            see exactly why a candidate landed where they did.
          </p>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            onClick={onStart}
            className="mt-8 bg-ink-strong text-white px-6 py-3 rounded-full text-[14px] font-semibold shadow-sm"
          >
            Start screening
          </motion.button>
        </motion.div>
      </div>

      <div className="relative z-30 flex justify-center pb-10">
        <FloatingNav onStart={onStart} />
      </div>
    </section>
  );
}
