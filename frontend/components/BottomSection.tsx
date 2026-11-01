"use client";

import { useEffect, useState } from "react";
import { MessageCircle, ChevronRight, ArrowRight } from "lucide-react";
import { api, DashboardBreakdownResponse } from "@/lib/api";
import {
  MOCK_ORDER_STATUSES,
  MOCK_TOP_PRODUCTS,
  MOCK_PENDING_DUES,
} from "@/lib/mocks/dashboard";

export default function BottomSection() {
  const [orderStatuses, setOrderStatuses] = useState(MOCK_ORDER_STATUSES);
  const [topProducts, setTopProducts] = useState(MOCK_TOP_PRODUCTS);
  const [pendingDues, setPendingDues] = useState(MOCK_PENDING_DUES);
  const [totalOrders, setTotalOrders] = useState(124);
  const [totalDues, setTotalDues] = useState(12480);

  useEffect(() => {
    let isMounted = true;
    async function fetchBreakdown() {
      try {
        const res: DashboardBreakdownResponse = await api.getBreakdown();
        if (isMounted) {
          if (res?.order_statuses && res.order_statuses.length > 0) {
            setOrderStatuses(res.order_statuses);
          }
          if (res?.top_products && res.top_products.length > 0) {
            setTopProducts(res.top_products);
          }
          if (res?.pending_dues && res.pending_dues.length > 0) {
            setPendingDues(res.pending_dues);
          }
          if (res?.total_orders) setTotalOrders(res.total_orders);
          if (res?.total_pending_dues) setTotalDues(res.total_pending_dues);
        }
      } catch {
        // Fallback to mocks
      }
    }
    fetchBreakdown();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {/* 1. Orders by Status Card */}
      <div className="bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/40 rounded-3xl p-5 sm:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.35)] flex flex-col justify-between transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base sm:text-lg font-bold text-[#F0FDF4] tracking-tight">
            Orders by Status
          </h2>
          <ChevronRight className="w-4 h-4 text-[#BAC8C1]/60 hover:text-[#B6F23C] transition-colors cursor-pointer" />
        </div>

        <div className="flex items-center gap-5 my-auto">
          {/* Donut SVG Ring */}
          <div className="relative w-32 h-32 flex-shrink-0 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                stroke="#10211A"
                strokeWidth="14"
              />
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                stroke="#B6F23C"
                strokeWidth="14"
                strokeDasharray={`${66 * 2.387} ${100 * 2.387}`}
                strokeDashoffset="0"
              />
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                stroke="#60A5FA"
                strokeWidth="14"
                strokeDasharray={`${15 * 2.387} ${100 * 2.387}`}
                strokeDashoffset={`-${66 * 2.387}`}
              />
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                stroke="#FDBA74"
                strokeWidth="14"
                strokeDasharray={`${10 * 2.387} ${100 * 2.387}`}
                strokeDashoffset={`-${(66 + 15) * 2.387}`}
              />
              <circle
                cx="50"
                cy="50"
                r="38"
                fill="transparent"
                stroke="#C084FC"
                strokeWidth="14"
                strokeDasharray={`${9 * 2.387} ${100 * 2.387}`}
                strokeDashoffset={`-${(66 + 15 + 10) * 2.387}`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className="text-lg font-black text-[#F0FDF4] leading-tight">
                {totalOrders}
              </span>
              <span className="text-[10px] text-[#BAC8C1] uppercase tracking-wider font-semibold">
                Orders
              </span>
            </div>
          </div>

          {/* Legend Items */}
          <div className="flex-1 space-y-2">
            {orderStatuses.map((s) => (
              <div key={s.label} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                    style={{ backgroundColor: s.color }}
                  />
                  <span className="text-[#BAC8C1] font-medium">{s.label}</span>
                </div>
                <div className="flex items-center gap-1.5 font-bold">
                  <span className="text-[#F0FDF4]">{s.value}</span>
                  <span className="text-[#BAC8C1]/60 text-[11px]">({s.percentage}%)</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Top Selling Products Card */}
      <div className="bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/40 rounded-3xl p-5 sm:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.35)] flex flex-col justify-between transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base sm:text-lg font-bold text-[#F0FDF4] tracking-tight">
            Top Selling Products
          </h2>
          <ChevronRight className="w-4 h-4 text-[#BAC8C1]/60 hover:text-[#B6F23C] transition-colors cursor-pointer" />
        </div>

        <div className="space-y-3 my-auto">
          {topProducts.map((p) => (
            <div
              key={p.name}
              className="flex items-center justify-between gap-3 p-2 rounded-2xl hover:bg-[#10211A] transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-[#10211A] border border-[#224430] flex items-center justify-center text-lg flex-shrink-0">
                  {p.emoji || "👗"}
                </div>
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm font-bold text-[#F0FDF4] truncate">
                    {p.name}
                  </p>
                  <p className="text-[11px] text-[#BAC8C1]/70">{p.sold} sold</p>
                </div>
              </div>

              <p className="text-xs sm:text-sm font-black text-[#F0FDF4] tabular-nums">
                ₹{Math.round(p.revenue).toLocaleString("en-IN")}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 3. Pending Dues Card */}
      <div className="bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/40 rounded-3xl p-5 sm:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.35)] flex flex-col justify-between transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#F0FDF4] tracking-tight">
              Pending Dues
            </h2>
            <p className="text-xs font-semibold text-[#F87171] mt-0.5">
              ₹{totalDues.toLocaleString("en-IN")}
            </p>
          </div>
          <button className="text-xs font-bold text-[#B6F23C] hover:underline flex items-center gap-1 cursor-pointer">
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="space-y-3 my-auto">
          {pendingDues.map((d, i) => (
            <div
              key={`${d.name}-${i}`}
              className="flex items-center justify-between gap-2.5 p-2 rounded-2xl hover:bg-[#10211A] transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-9 h-9 rounded-full bg-[#10211A] border border-[#224430] flex items-center justify-center text-xs font-bold text-[#BAC8C1] flex-shrink-0">
                  {d.initials}
                </div>
                <div className="min-w-0">
                  <p className="text-xs sm:text-sm font-bold text-[#F0FDF4] truncate">
                    {d.name}
                  </p>
                  <p className="text-[11px] text-[#BAC8C1]/70">
                    {d.orders} order{d.orders > 1 ? "s" : ""} · ₹
                    {Math.round(d.amount).toLocaleString("en-IN")}
                  </p>
                </div>
              </div>

              {d.phone && (
                <a
                  href={`https://wa.me/${d.phone.replace(/[^0-9]/g, "")}?text=Namaste! Aapke paas ₹${Math.round(
                    d.amount
                  )} baki hai. Kripya payment karein.`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 bg-[#25D366]/15 hover:bg-[#25D366]/25 border border-[#25D366]/35 text-[#25D366] px-3 py-1.5 rounded-full text-xs font-bold transition-all flex-shrink-0"
                >
                  <MessageCircle className="w-3.5 h-3.5" />
                  <span>Remind</span>
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

