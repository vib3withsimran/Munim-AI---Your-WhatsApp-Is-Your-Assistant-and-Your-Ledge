"use client";

import { useState, useEffect } from "react";
<<<<<<< Updated upstream
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { TrendingUp } from "lucide-react";
import { api, DashboardSalesResponse } from "@/lib/api";
import { MOCK_SALES_SERIES } from "@/lib/mocks/dashboard";
=======
import SplineChart from "./SplineChart";
import { api, DashboardSalesResponse } from "@/lib/api";
>>>>>>> Stashed changes

const TIME_FILTERS = ["7D", "30D", "3M", "6M"] as const;
type TimeFilter = typeof TIME_FILTERS[number];

export default function SalesChart() {
<<<<<<< Updated upstream
  const [activeRange, setActiveRange] = useState<TimeFilter>("30D");
  const [chartData, setChartData] = useState(MOCK_SALES_SERIES["30D"]);
  const [totalSales, setTotalSales] = useState(86420);
  const [changePct, setChangePct] = useState(18);

  useEffect(() => {
    let isMounted = true;
    async function fetchSales() {
      try {
        const res: DashboardSalesResponse = await api.getSales(activeRange);
        if (isMounted && res?.data && res.data.length > 0) {
          setChartData(res.data);
          setTotalSales(res.total_sales || 86420);
          setChangePct(res.change_percentage || 18);
        } else if (isMounted) {
          setChartData(MOCK_SALES_SERIES[activeRange] || MOCK_SALES_SERIES["30D"]);
        }
      } catch {
        if (isMounted) {
          setChartData(MOCK_SALES_SERIES[activeRange] || MOCK_SALES_SERIES["30D"]);
        }
      }
    }
    fetchSales();
    return () => {
      isMounted = false;
    };
  }, [activeRange]);
=======
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
>>>>>>> Stashed changes

  return (
    <div className="bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/40 rounded-3xl p-5 sm:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.35)] flex flex-col justify-between transition-all duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="text-base sm:text-lg font-bold text-[#F0FDF4] tracking-tight">
            Sales Overview
          </h2>
          <div className="flex items-center gap-2 mt-1">
<<<<<<< Updated upstream
            <span className="text-2xl sm:text-3xl font-black text-[#F0FDF4] tracking-tight">
              ₹{totalSales.toLocaleString("en-IN")}
            </span>
            <span className="text-xs font-bold text-[#B6F23C] bg-[#B6F23C]/15 border border-[#B6F23C]/30 px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              <span>+{changePct}% vs last {activeRange}</span>
=======
            <span className="text-2xl font-bold text-[#f0fdf4]">
              {loading ? "..." : `₹${Math.round(totalSales).toLocaleString("en-IN")}`}
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream

        {/* Time Filter Pills */}
        <div className="flex items-center gap-1.5 bg-[#10211A] border border-[#224430] p-1 rounded-full self-start sm:self-auto">
          {TIME_FILTERS.map((range) => {
            const isActive = activeRange === range;
            return (
              <button
                key={range}
                onClick={() => setActiveRange(range)}
                className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
                  isActive
                    ? "bg-[#B6F23C] text-[#07110D] shadow-[0_0_10px_rgba(182,242,60,0.4)]"
                    : "text-[#BAC8C1] hover:text-[#F0FDF4]"
                }`}
              >
                {range}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-56 sm:h-64 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="salesOverviewGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#B6F23C" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#B6F23C" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#224430"
              strokeOpacity={0.4}
              vertical={false}
            />
            <XAxis
              dataKey="label"
              stroke="#BAC8C1"
              strokeOpacity={0.6}
              fontSize={11}
              tickLine={false}
              axisLine={false}
              dy={8}
            />
            <YAxis
              stroke="#BAC8C1"
              strokeOpacity={0.6}
              fontSize={11}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => `₹${val >= 1000 ? `${(val / 1000).toFixed(0)}K` : val}`}
              dx={-5}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-[#0B1A13] border border-[#B6F23C]/50 rounded-xl px-3 py-2 shadow-2xl backdrop-blur-xl">
                      <p className="text-[10px] text-[#BAC8C1] uppercase tracking-wider font-semibold">
                        {data.label}
                      </p>
                      <p className="text-sm font-black text-[#B6F23C] mt-0.5">
                        ₹{Number(data.value).toLocaleString("en-IN")}
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#B6F23C"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#salesOverviewGrad)"
              activeDot={{
                r: 6,
                fill: "#B6F23C",
                stroke: "#07110D",
                strokeWidth: 2,
                className: "drop-shadow-[0_0_8px_rgba(182,242,60,0.8)]",
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
=======
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
>>>>>>> Stashed changes
    </div>
  );
}
