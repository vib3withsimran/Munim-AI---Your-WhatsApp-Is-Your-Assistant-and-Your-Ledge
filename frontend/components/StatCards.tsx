"use client";

import { useEffect, useRef, useState } from "react";
import { api, DashboardSummaryResponse, StatCardItem } from "@/lib/api";

interface StatCardProps {
  icon: string;
  label: string;
  value: string;
  change: number;
  changeLabel?: string;
  delay?: number;
  isNegative?: boolean;
}

function useCountUp(target: number, duration = 800) {
  const [current, setCurrent] = useState(0);
  useEffect(() => {
    let start = 0;
    if (target === 0) {
      setCurrent(0);
      return;
    }
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

function StatCard({
  icon,
  label,
  value,
  change,
  changeLabel = "vs last month",
  delay = 0,
  isNegative = false,
}: StatCardProps) {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const numericValue = parseFloat(value.replace(/[^0-9.]/g, "")) || 0;
  const prefix = value.match(/^[₹$£€]/) ? value[0] : "";
  const suffix = value.match(/[KMB]$/) ? value[value.length - 1] : "";
  const animated = useCountUp(visible ? numericValue : 0);

  // If isNegative is true (e.g. dues), a positive increase in debt is red
  const isPositive = isNegative ? change <= 0 : change >= 0;

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
  const [data, setData] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const summary = await api.getSummary();
      setData(summary);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load summary stats";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="glass-card p-5 animate-pulse space-y-3">
            <div className="flex justify-between items-center">
              <div className="w-10 h-10 rounded-lg bg-[rgba(78,250,114,0.06)]" />
              <div className="w-12 h-5 rounded-full bg-[rgba(78,250,114,0.06)]" />
            </div>
            <div className="w-24 h-7 rounded bg-[rgba(78,250,114,0.06)]" />
            <div className="w-32 h-4 rounded bg-[rgba(78,250,114,0.04)]" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-[rgba(248,113,113,0.08)] border border-[rgba(248,113,113,0.2)] text-[#f87171] text-xs flex items-center justify-between">
        <span>⚠️ {error}</span>
        <button
          onClick={fetchStats}
          className="text-xs bg-[rgba(248,113,113,0.15)] hover:bg-[rgba(248,113,113,0.25)] px-3 py-1 rounded-md transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  const statsList: StatCardItem[] = data?.stats || [
    { icon: "🛍️", label: "Revenue (this month)", value: "₹0", numeric_value: 0, change: 0, change_label: "vs last month", is_negative: false },
    { icon: "📦", label: "Orders", value: "0", numeric_value: 0, change: 0, change_label: "vs last month", is_negative: false },
    { icon: "👥", label: "Active customers", value: "0", numeric_value: 0, change: 0, change_label: "active buyers", is_negative: false },
    { icon: "🔔", label: "Pending dues", value: "₹0", numeric_value: 0, change: 0, change_label: "outstanding", is_negative: true },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {statsList.map((stat, i) => (
        <StatCard
          key={stat.label}
          icon={stat.icon}
          label={stat.label}
          value={stat.value}
          change={stat.change}
          changeLabel={stat.change_label}
          isNegative={stat.is_negative}
          delay={i * 80}
        />
      ))}
    </div>
  );
}
