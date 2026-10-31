"use client";

import { useEffect, useState } from "react";
import { api, DashboardActivityResponse, ActivityItem, MemoryHighlight } from "@/lib/api";

export default function ActivityAndMemory() {
  const [data, setData] = useState<DashboardActivityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActivity = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getActivity();
      setData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load activity";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivity();
  }, []);

  const activities: ActivityItem[] = data?.activities || [
    { icon: "💬", color: "#4efa72", label: "New messages", count: 0, delta: "+0" },
    { icon: "📦", color: "#60a5fa", label: "Orders created", count: 0, delta: "+0" },
    { icon: "₹", color: "#fbbf24", label: "Payments received", count: 0, delta: "+0" },
    { icon: "🔔", color: "#f87171", label: "Dues reminders sent", count: 0, delta: "+0" },
    { icon: "✨", color: "#c084fc", label: "Memories updated", count: 0, delta: "+0" },
  ];

  const memories: MemoryHighlight[] = data?.memories || [];

  return (
    <>
      {/* Today's Activity */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[#f0fdf4] font-semibold text-base">Today&apos;s Activity</h2>
          {error && (
            <button
              onClick={fetchActivity}
              className="text-[11px] text-[#f87171] hover:underline"
            >
              Retry
            </button>
          )}
        </div>

        {loading ? (
          <div className="space-y-3 animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[rgba(78,250,114,0.06)]" />
                <div className="flex-1 h-4 bg-[rgba(78,250,114,0.04)] rounded" />
                <div className="w-6 h-4 bg-[rgba(78,250,114,0.06)] rounded" />
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((a) => (
              <div key={a.label} className="flex items-center gap-3">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-sm flex-shrink-0"
                  style={{ background: `${a.color}18`, color: a.color }}
                >
                  {a.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#9db8a0] truncate">{a.label}</p>
                </div>
                <span className="text-base font-bold text-[#f0fdf4] tabular-nums">{a.count}</span>
                <span className="text-xs font-semibold text-[#4efa72] bg-[rgba(78,250,114,0.1)] px-1.5 py-0.5 rounded-md min-w-[36px] text-center">
                  {a.delta}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Memory Highlights */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[#f0fdf4] font-semibold text-base flex items-center gap-2">
            <span className="text-[#4efa72]">✨</span> AI Memory Highlights
          </h2>
          <span className="text-[11px] text-[#5d7a63] font-medium">Meko Engine</span>
        </div>

        {loading ? (
          <div className="space-y-3 animate-pulse">
            {[1, 2].map((i) => (
              <div key={i} className="p-3 rounded-lg bg-[#0d1410] space-y-2">
                <div className="w-3/4 h-4 bg-[rgba(78,250,114,0.06)] rounded" />
                <div className="w-1/3 h-3 bg-[rgba(78,250,114,0.04)] rounded" />
              </div>
            ))}
          </div>
        ) : memories.length === 0 ? (
          <div className="p-4 rounded-xl bg-[#0d1410] border border-[rgba(78,250,114,0.06)] text-center space-y-1.5">
            <p className="text-sm text-[#f0fdf4] font-medium">No memory tags yet</p>
            <p className="text-xs text-[#5d7a63] leading-relaxed">
              When customers share preferences (sizes, favorite colors) on WhatsApp, Munim AI saves them here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {memories.map((m, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-lg bg-[#0d1410] border border-[rgba(78,250,114,0.08)] hover:border-[rgba(78,250,114,0.2)] transition-all"
              >
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center text-sm flex-shrink-0 mt-0.5"
                  style={{ background: `${m.color}18`, color: m.color }}
                >
                  {m.icon}
                </div>
                <div>
                  <p className="text-sm text-[#f0fdf4] font-medium leading-snug">{m.text}</p>
                  <p className="text-xs text-[#5d7a63] mt-0.5">{m.meta}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
