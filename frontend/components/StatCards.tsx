"use client";

import { useEffect, useRef, useState } from "react";

interface StatCardProps {
  icon: string;
  label: string;
  value: string;
  change: number;
  changeLabel?: string;
  delay?: number;
}

function useCountUp(target: number, duration = 800) {
  const [current, setCurrent] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        setCurrent(target);
        clearInterval(timer);
      } else {
        setCurrent(Math.floor(start));
      }
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);
  return current;
}

function StatCard({ icon, label, value, change, changeLabel = "vs last month", delay = 0 }: StatCardProps) {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const numericValue = parseFloat(value.replace(/[^0-9.]/g, ""));
  const prefix = value.match(/^[₹$£€]/) ? value[0] : "";
  const suffix = value.match(/[KMB]$/) ? value[value.length - 1] : "";
  const animated = useCountUp(visible ? numericValue : 0);

  const isPositive = change >= 0;

  return (
    <div
      ref={ref}
      className="glass-card p-5 flex flex-col gap-3 transition-all duration-300 hover:translate-y-[-2px]"
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Icon + Badge */}
      <div className="flex items-center justify-between">
        <div className="w-10 h-10 rounded-lg bg-[rgba(78,250,114,0.1)] border border-[rgba(78,250,114,0.15)] flex items-center justify-center text-lg">
          {icon}
        </div>
        <span
          className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
            isPositive
              ? "bg-[rgba(78,250,114,0.12)] text-[#4efa72]"
              : "bg-[rgba(248,113,113,0.12)] text-[#f87171]"
          }`}
        >
          {isPositive ? "↑" : "↓"} {Math.abs(change)}%
        </span>
      </div>

      {/* Value */}
      <div>
        <p className="text-2xl font-bold text-[#f0fdf4] tabular-nums leading-none">
          {prefix}
          {animated.toLocaleString("en-IN")}
          {suffix}
        </p>
        <p className="text-sm text-[#9db8a0] mt-1">{label}</p>
      </div>

      {/* Change label */}
      <p className="text-xs text-[#5d7a63]">
        <span className={isPositive ? "text-[#4efa72]" : "text-[#f87171]"}>
          {isPositive ? "▲" : "▼"} {Math.abs(change)}%
        </span>{" "}
        {changeLabel}
      </p>
    </div>
  );
}

export default function StatCards() {
  const stats = [
    { icon: "🛍️", label: "Revenue (this month)", value: "₹86420", change: 18 },
    { icon: "📦", label: "Orders", value: "124", change: 12 },
    { icon: "👥", label: "Active customers", value: "67", change: 24 },
    { icon: "🔔", label: "Pending dues", value: "₹12480", change: 6, isNegative: true },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((s, i) => (
        <StatCard key={s.label} {...s} delay={i * 80} />
      ))}
    </div>
  );
}

