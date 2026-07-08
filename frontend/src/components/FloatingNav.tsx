import { motion } from "motion/react";
import { ChevronRight } from "lucide-react";

interface FloatingNavProps {
  onStart: () => void;
}

export function FloatingNav({ onStart }: FloatingNavProps) {
  return (
    <motion.nav
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.5, ease: "easeOut" }}
      className="flex items-center bg-white/90 backdrop-blur-2xl px-1.5 py-1.5 rounded-full shadow-[0_12px_40px_rgba(0,0,0,0.08)] border border-slate-200/40"
    >
      <div className="w-9 h-9 flex items-center justify-center rounded-full bg-white border border-slate-100 shadow-sm text-ink text-sm">
        ✦
      </div>
      <a
        href="#how-it-works"
        className="ml-2 px-3 py-2 text-[12px] font-semibold text-slate-500 hover:text-ink transition-colors"
      >
        How it works
      </a>
      <a
        href="#methodology"
        className="px-3 py-2 text-[12px] font-semibold text-slate-500 hover:text-ink transition-colors"
      >
        Method
      </a>
      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.98 }}
        onClick={onStart}
        className="ml-1 flex items-center gap-1 bg-white px-5 py-2 rounded-full text-[12px] font-semibold text-ink border border-slate-200/60 shadow-sm hover:border-slate-300 transition-all"
      >
        Start screening
        <ChevronRight size={14} />
      </motion.button>
    </motion.nav>
  );
}
