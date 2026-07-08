import { useEffect, useState, type MouseEvent } from "react";
import { Clock, Trash2 } from "lucide-react";
import type { HistoryItem } from "../types";
import { deleteHistoryItem, fetchHistory } from "../lib/api";

interface HistoryPanelProps {
  onSelect: (sessionId: string) => void;
  refreshKey: number;
}

export function HistoryPanel({ onSelect, refreshKey }: HistoryPanelProps) {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchHistory()
      .then((data) => !cancelled && setItems(data))
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  async function handleDelete(e: MouseEvent, sessionId: string) {
    e.stopPropagation();
    await deleteHistoryItem(sessionId).catch(() => undefined);
    setItems((prev) => prev?.filter((i) => i.session_id !== sessionId) ?? null);
  }

  if (error || (items && items.length === 0)) return null;

  return (
    <div>
      <h3 className="font-display text-lg font-medium text-ink mb-3">Recent screenings</h3>
      <p className="text-[12px] text-muted mb-3">
        Stored on this server while it stays warm. On a free-tier deploy the list resets after the
        service spins down from inactivity - see the README for details.
      </p>
      <div className="space-y-2">
        {items?.map((item) => (
          <div
            key={item.session_id}
            role="button"
            tabIndex={0}
            onClick={() => onSelect(item.session_id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") onSelect(item.session_id);
            }}
            className="w-full flex items-center justify-between gap-3 bg-white border border-slate-200/70 rounded-2xl px-4 py-3 text-left hover:border-slate-300 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3 min-w-0">
              <Clock size={14} className="text-slate-300 shrink-0" />
              <div className="min-w-0">
                <p className="text-[13px] text-ink truncate">{item.jd_excerpt || "Untitled screening"}</p>
                <p className="text-[11px] text-muted">
                  {item.candidate_count} candidate{item.candidate_count === 1 ? "" : "s"}
                  {item.top_candidate_score != null && ` \u00b7 top score ${item.top_candidate_score.toFixed(0)}`}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={(e) => handleDelete(e, item.session_id)}
              aria-label="Delete this session"
              className="text-slate-300 hover:text-ink transition-colors shrink-0"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
