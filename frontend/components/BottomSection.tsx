"use client";

import DonutChart from "./DonutChart";

const ORDER_STATUSES = [
  { label: "Completed", value: 82, color: "#4efa72" },
  { label: "Processing", value: 18, color: "#60a5fa" },
  { label: "Pending Payment", value: 12, color: "#fbbf24" },
  { label: "Cancelled", value: 10, color: "#f87171" },
];
const TOTAL = 124;

const TOP_PRODUCTS = [
  { name: "Blue Kurti", sold: 48, revenue: 38352, emoji: "👘" },
  { name: "Anarkali Kurti", sold: 27, revenue: 32130, emoji: "🥻" },
  { name: "Black Kurti", sold: 21, revenue: 16758, emoji: "🖤" },
];

const DUES = [
  { initials: "RS", name: "Riya Sharma", orders: 2, amount: 4200, phone: "919876543210" },
  { initials: "AK", name: "Aditi Khanna", orders: 1, amount: 3800, phone: "919812345678" },
  { initials: "SM", name: "Sneha Mehta", orders: 1, amount: 2480, phone: "919987654321" },
];

const INITIALS_COLORS = ["#4efa72", "#60a5fa", "#fbbf24", "#c084fc", "#f87171"];

export default function BottomSection() {
  const totalDues = DUES.reduce((s, d) => s + d.amount, 0);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {/* Orders by Status */}
      <div className="glass-card p-5">
        <h2 className="text-[#f0fdf4] font-semibold text-base mb-4">Orders by Status</h2>
        <div className="flex items-center gap-4">
          <DonutChart data={ORDER_STATUSES} total={TOTAL} size={136} />
          <div className="flex-1 space-y-2.5">
            {ORDER_STATUSES.map((s) => (
              <div key={s.label} className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: s.color }} />
                <span className="text-xs text-[#9db8a0] flex-1">{s.label}</span>
                <span className="text-xs font-semibold text-[#f0fdf4] tabular-nums">{s.value}</span>
                <span className="text-[10px] text-[#5d7a63] w-10 text-right">
                  ({Math.round((s.value / TOTAL) * 100)}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Selling Products */}
      <div className="glass-card p-5">
        <h2 className="text-[#f0fdf4] font-semibold text-base mb-4">Top Selling Products</h2>
        <div className="space-y-3">
          {TOP_PRODUCTS.map((p, i) => (
            <div key={p.name} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-[rgba(78,250,114,0.04)] transition-all">
              <div className="w-10 h-10 rounded-lg bg-[rgba(78,250,114,0.06)] border border-[rgba(78,250,114,0.1)] flex items-center justify-center text-xl flex-shrink-0">
                {p.emoji}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#f0fdf4] truncate">{p.name}</p>
                <p className="text-xs text-[#5d7a63]">{p.sold} sold</p>
              </div>
              <p className="text-sm font-bold text-[#4efa72] tabular-nums">₹{p.revenue.toLocaleString("en-IN")}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Pending Dues */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-[#f0fdf4] font-semibold text-base">Pending Dues</h2>
            <p className="text-xs text-[#f87171] font-semibold mt-0.5">₹{totalDues.toLocaleString("en-IN")} total</p>
          </div>
          <button className="text-xs text-[#4efa72] font-medium hover:underline flex items-center gap-1">
            View All →
          </button>
        </div>
        <div className="space-y-3">
          {DUES.map((d, i) => (
            <div key={d.name} className="flex items-center gap-3">
              <div
                className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-[#0d1410] flex-shrink-0"
                style={{ background: INITIALS_COLORS[i % INITIALS_COLORS.length] }}
              >
                {d.initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[#f0fdf4] truncate">{d.name}</p>
                <p className="text-xs text-[#5d7a63]">
                  {d.orders} order{d.orders > 1 ? "s" : ""} · ₹{d.amount.toLocaleString("en-IN")}
                </p>
              </div>
              <a
                href={`https://wa.me/${d.phone}?text=Namaste! Aapke paas ₹${d.amount} baki hai. Kripya payment karein.`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 bg-[#25D366] hover:bg-[#1ebc5b] text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 shadow-[0_0_8px_rgba(37,211,102,0.3)] hover:shadow-[0_0_14px_rgba(37,211,102,0.5)] flex-shrink-0"
              >
                📱 Remind
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

