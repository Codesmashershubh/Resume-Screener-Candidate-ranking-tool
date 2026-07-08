import type { LucideIcon } from "lucide-react";
import {
  Code2,
  LineChart,
  Palette,
  Megaphone,
  Handshake,
  Landmark,
  Users,
} from "lucide-react";
import { SKILL_CATEGORIES } from "../lib/categories";

const ICONS: Record<string, LucideIcon> = {
  Engineering: Code2,
  "Data & Analytics": LineChart,
  "Product & Design": Palette,
  "Marketing & Growth": Megaphone,
  "Sales & Business": Handshake,
  "Finance & Operations": Landmark,
  "People & Leadership": Users,
};

const GRADIENTS: Record<string, string> = {
  Engineering: "from-blue-200 to-blue-400",
  "Data & Analytics": "from-violet-200 to-violet-400",
  "Product & Design": "from-fuchsia-200 to-fuchsia-400",
  "Marketing & Growth": "from-rose-200 to-rose-400",
  "Sales & Business": "from-emerald-200 to-emerald-400",
  "Finance & Operations": "from-amber-200 to-amber-400",
  "People & Leadership": "from-sky-200 to-sky-400",
};

function CategoryCard({ name }: { name: string }) {
  const Icon = ICONS[name] ?? Code2;
  return (
    <div className="group relative h-24 w-44 shrink-0 flex flex-col items-center justify-center gap-1.5 rounded-full bg-white border border-slate-200/60 shadow-sm hover:border-slate-300 transition-all overflow-hidden">
      <div
        className={`absolute inset-0 bg-gradient-to-br ${GRADIENTS[name]} scale-150 opacity-0 group-hover:scale-100 group-hover:opacity-100 transition-all duration-300`}
      />
      <div className="relative z-10 text-ink group-hover:text-white transition-colors duration-300">
        <Icon size={18} />
      </div>
      <span className="relative z-10 text-[11px] font-semibold text-ink group-hover:text-white text-center px-3 leading-tight transition-colors duration-300">
        {name}
      </span>
    </div>
  );
}

export function CategoryMarquee() {
  const items = [...SKILL_CATEGORIES, ...SKILL_CATEGORIES];
  return (
    <div
      className="relative w-full max-w-[1400px] mx-auto mt-10 overflow-hidden"
      style={{ maskImage: "linear-gradient(to right, transparent, black 8%, black 92%, transparent)" }}
    >
      <div className="marquee-track flex items-center gap-4 w-max">
        {items.map((name, i) => (
          <CategoryCard key={`${name}-${i}`} name={name} />
        ))}
      </div>
    </div>
  );
}
