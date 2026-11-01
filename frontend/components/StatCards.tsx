"use client";

import { useEffect, useState } from "react";
import { ShoppingBag, Package, Users, Wallet, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { api, DashboardSummaryResponse } from "@/lib/api";
import { MOCK_KPI_STATS } from "@/lib/mocks/dashboard";

interface StatItem {
  id: string;
  label: string;
  value: string;
  numeric_value: number;
  change: number;
  change_label: string;
  is_negative: boolean;
  icon: React.ElementType;
}

const DEFAULT_STATS: StatItem[] = [
  {
    id: "revenue",
    label: MOCK_KPI_STATS[0].label,
    value: MOCK_KPI_STATS[0].value,
    numeric_value: MOCK_KPI_STATS[0].numericValue,
    change: MOCK_KPI_STATS[0].change,
    change_label: MOCK_KPI_STATS[0].changeLabel,
    is_negative: false,
    icon: ShoppingBag,
  },
  {
    id: "orders",
    label: MOCK_KPI_STATS[1].label,
    value: MOCK_KPI_STATS[1].value,
    numeric_value: MOCK_KPI_STATS[1].numericValue,
    change: MOCK_KPI_STATS[1].change,
    change_label: MOCK_KPI_STATS[1].changeLabel,
    is_negative: false,
    icon: Package,
  },
  {
    id: "customers",
    label: MOCK_KPI_STATS[2].label,
    value: MOCK_KPI_STATS[2].value,
    numeric_value: MOCK_KPI_STATS[2].numericValue,
    change: MOCK_KPI_STATS[2].change,
    change_label: MOCK_KPI_STATS[2].changeLabel,
    is_negative: false,
    icon: Users,
  },
  {
    id: "dues",
    label: MOCK_KPI_STATS[3].label,
    value: MOCK_KPI_STATS[3].value,
    numeric_value: MOCK_KPI_STATS[3].numericValue,
    change: MOCK_KPI_STATS[3].change,
    change_label: MOCK_KPI_STATS[3].changeLabel,
    is_negative: true,
    icon: Wallet,
  },
];

export default function StatCards() {
  const [stats, setStats] = useState<StatItem[]>(DEFAULT_STATS);

  useEffect(() => {
    let isMounted = true;
    async function loadStats() {
      try {
        const res: DashboardSummaryResponse = await api.getSummary();
        if (isMounted && res?.stats && res.stats.length >= 4) {
          const icons = [ShoppingBag, Package, Users, Wallet];
          const mapped = res.stats.map((s, idx) => ({
            id: s.label.toLowerCase().replace(/[^a-z]/g, ""),
            label: s.label,
            value: s.value,
            numeric_value: s.numeric_value || 0,
            change: s.change || 0,
            change_label: s.change_label || "",
            is_negative: Boolean(s.is_negative),
            icon: icons[idx % icons.length],
          }));
          setStats(mapped);
        }
      } catch {
        // Fallback gracefully to mock data
      }
    }
    loadStats();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((item) => {
        const Icon = item.icon;
        const isPositiveChange = item.is_negative ? item.change <= 0 : item.change >= 0;
        const changeDisplay = Math.abs(item.change);

        return (
          <div
            key={item.id}
            className="bg-[#0B1A13]/90 hover:bg-[#10241A] border border-[#224430] hover:border-[#B6F23C]/50 rounded-2xl p-5 transition-all duration-300 shadow-[0_4px_24px_rgba(0,0,0,0.35)] hover:shadow-[0_0_25px_rgba(182,242,60,0.15)] hover:-translate-y-0.5 flex flex-col justify-between min-h-[135px]"
          >
            {/* Top Row: Icon + Delta Tag */}
            <div className="flex items-center justify-between mb-2">
              <div className="w-10 h-10 rounded-xl bg-[#10211A] border border-[#224430] flex items-center justify-center text-[#B6F23C] shadow-sm">
                <Icon className="w-5 h-5 text-[#B6F23C]" />
              </div>

              <div
                className={`flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full border ${
                  isPositiveChange
                    ? "bg-[#B6F23C]/15 border-[#B6F23C]/30 text-[#B6F23C]"
                    : "bg-[#EF4444]/15 border-[#EF4444]/30 text-[#F87171]"
                }`}
              >
                {isPositiveChange ? (
                  <ArrowUpRight className="w-3.5 h-3.5" />
                ) : (
                  <ArrowDownRight className="w-3.5 h-3.5" />
                )}
                <span>+{changeDisplay}%</span>
              </div>
            </div>

            {/* Bottom Row: Metric Value + Label */}
            <div>
              <p className="text-2xl sm:text-[26px] font-black text-[#F0FDF4] tracking-tight leading-none">
                {item.value}
              </p>
              <p className="text-xs sm:text-sm text-[#BAC8C1] font-medium mt-1.5">
                {item.label}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

