"use client";

import { useState } from "react";
import SplineChart from "./SplineChart";

const TIME_FILTERS = ["7D", "30D", "3M", "6M"] as const;

// Mock data
const DATA_MAP: Record<string, { label: string; value: number }[]> = {
  "7D": [
    { label: "Oct 24", value: 68000 },
    { label: "Oct 25", value: 72000 },
    { label: "Oct 26", value: 69500 },
    { label: "Oct 27", value: 78000 },
    { label: "Oct 28", value: 74200 },
    { label: "Oct 29", value: 81000 },
    { label: "Oct 30", value: 86420 },
  ],
  "30D": [
    { label: "Oct 1", value: 42000 },
    { label: "Oct 5", value: 51000 },
    { label: "Oct 10", value: 48000 },
    { label: "Oct 15", value: 62000 },
    { label: "Oct 20", value: 70000 },
    { label: "Oct 25", value: 79000 },
    { label: "Oct 30", value: 86420 },
  ],
  "3M": [
    { label: "Aug", value: 54000 },
    { label: "Sep", value: 68000 },
    { label: "Oct", value: 86420 },
  ],
  "6M": [
    { label: "May", value: 38000 },
    { label: "Jun", value: 45000 },
    { label: "Jul", value: 52000 },
    { label: "Aug", value: 54000 },
    { label: "Sep", value: 68000 },
    { label: "Oct", value: 86420 },
  ],
};

export default function SalesChart() {
  const [active, setActive] = useState<keyof typeof DATA_MAP>("30D");
  const data = DATA_MAP[active];
  const latest = data[data.length - 1].value;

  return (
    <div className="glass-card p-5 col-span-full xl:col-span-2">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-[#f0fdf4] font-semibold text-base">Sales Overview</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-2xl font-bold text-[#f0fdf4]">
              ₹{latest.toLocaleString("en-IN")}
            </span>
            <span className="flex items-center gap-1 text-xs font-semibold text-[#4efa72] bg-[rgba(78,250,114,0.12)] px-2 py-0.5 rounded-full">
              ↑ 18% vs last 30 days
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 bg-[#0d1410] rounded-lg p-1 border border-[rgba(78,250,114,0.1)]">
          {TIME_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setActive(f)}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all duration-200 ${
                active === f
                  ? "bg-[#4efa72] text-[#0d1410]"
                  : "text-[#9db8a0] hover:text-[#f0fdf4]"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <SplineChart data={data} height={160} />
    </div>
  );
}

