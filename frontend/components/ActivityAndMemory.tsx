"use client";

const activities = [
  { icon: "💬", color: "#4efa72", label: "New messages", count: 42, delta: "+11" },
  { icon: "📦", color: "#60a5fa", label: "Orders created", count: 9, delta: "+3" },
  { icon: "₹", color: "#fbbf24", label: "Payments received", count: 8, delta: "+2" },
  { icon: "🔔", color: "#f87171", label: "Dues reminders sent", count: 3, delta: "+3" },
  { icon: "✨", color: "#c084fc", label: "Memories updated", count: 6, delta: "+6" },
];

const memories = [
  { icon: "👤", color: "#60a5fa", text: "Priya prefers blue kurtis, size M", meta: "Updated today" },
  { icon: "🏷️", color: "#4efa72", text: "Exchange policy (7 days) added", meta: "Promoted to business knowledge" },
  { icon: "📈", color: "#fbbf24", text: "High interest in Anarkali collection", meta: "Seen in 12 conversations" },
];

export default function ActivityAndMemory() {
  return (
    <>
      {/* Today's Activity */}
      <div className="glass-card p-5">
        <h2 className="text-[#f0fdf4] font-semibold text-base mb-4">Today's Activity</h2>
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
      </div>

      {/* AI Memory Highlights */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[#f0fdf4] font-semibold text-base flex items-center gap-2">
            <span className="text-[#4efa72]">✨</span> AI Memory Highlights
          </h2>
          <button className="text-[#4efa72] text-xs font-medium hover:underline">›</button>
        </div>
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
      </div>
    </>
  );
}

