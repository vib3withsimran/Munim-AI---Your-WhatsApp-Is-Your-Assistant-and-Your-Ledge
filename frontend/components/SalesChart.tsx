"use client";

import { useState, useEffect } from "react";
import SplineChart from "./SplineChart";
import { api, DashboardSalesResponse } from "@/lib/api";

const TIME_FILTERS = ["7D", "30D", "3M", "6M"] as const;
type TimeFilter = typeof TIME_FILTERS[number];

export default function SalesChart() {
  const [active, setActive] = useState<TimeFilter>("30D");
  const [salesData, setSalesData] = useState<DashboardSalesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSales = async (period: TimeFilter) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getSales(period);
      setSalesData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load sales data";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSales(active);
  }, [active]);

  const chartData = salesData?.data || [];
  const totalSales = salesData?.total_sales ?? 0;
  const changePct = salesData?.change_percentage ?? 0;
  const isPositive = changePct >= 0;

  return (
    <div className="glass-card p-5 col-span-full xl:col-span-2">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-[#f0fdf4] font-semibold text-base">Sales Overview</h2>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-2xl font-bold text-[#f0fdf4]">
              {loading ? "..." : `₹${Math.round(totalSales).toLocaleString("en-IN")}`}
            </span>
            {!loading && (
              <span
                className={`flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${
                  isPositive
                    ? "text-[#4efa72] bg-[rgba(78,250,114,0.12)]"
                    : "text-[#f87171] bg-[rgba(248,113,113,0.12)]"
                }`}
              >
                {isPositive ? "↑" : "↓"} {Math.abs(changePct)}% vs prev {active}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1 bg-[#0d1410] rounded-lg p-1 border border-[rgba(78,250,114,0.1)]">
          {TIME_FILTERS.map((f) => (
            <button
              key={f}
              onClick={() => setActive(f)}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all duration-200 cursor-pointer ${
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

      {/* Chart Body */}
      {error ? (
        <div className="h-40 flex items-center justify-center p-4 rounded-xl bg-[rgba(248,113,113,0.06)] border border-[rgba(248,113,113,0.15)] text-[#f87171] text-xs">
          <span>⚠️ {error}</span>
          <button
            onClick={() => fetchSales(active)}
            className="ml-3 underline hover:text-[#f0fdf4]"
          >
            Retry
          </button>
        </div>
      ) : loading ? (
        <div className="h-40 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-[#4efa72] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : chartData.length === 0 ? (
        <div className="h-40 flex items-center justify-center text-xs text-[#5d7a63]">
          No sales recorded in this period.
        </div>
      ) : (
        <SplineChart data={chartData} height={160} />
      )}
    </div>
  );
}
