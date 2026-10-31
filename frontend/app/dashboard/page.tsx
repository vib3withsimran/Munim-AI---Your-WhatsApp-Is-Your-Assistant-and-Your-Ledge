"use client";

import TopNav from "@/components/TopNav";
import StatCards from "@/components/StatCards";
import SalesChart from "@/components/SalesChart";
import ActivityAndMemory from "@/components/ActivityAndMemory";
import BottomSection from "@/components/BottomSection";
import AskMunim from "@/components/AskMunim";

export default function DashboardPage() {
  const hour = typeof window !== "undefined" ? new Date().getHours() : 12;
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="min-h-screen bg-[#0d1410]">
      <TopNav active="Overview" />

      {/* Page content */}
      <main className="max-w-[1440px] mx-auto px-6 py-6 space-y-5">
        {/* Welcome */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-[#f0fdf4] text-2xl font-bold">
              {greeting}, Neha 👋
            </h1>
            <p className="text-[#9db8a0] text-sm mt-0.5">
              {"Here's what's happening with Neha's Closet today."}
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs text-[#5d7a63]">
            <span>
              Last updated:{" "}
              <span className="text-[#4efa72] font-medium">Just now</span>
            </span>
            <div className="w-1.5 h-1.5 rounded-full bg-[#4efa72] animate-[pulse-green_2s_ease-in-out_infinite]" />
          </div>
        </div>

        {/* Stat Cards */}
        <StatCards />

        {/* Charts Row */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <SalesChart />
          <ActivityAndMemory />
        </div>

        {/* Bottom Widgets */}
        <BottomSection />

        {/* Ask Munim AI bar */}
        <AskMunim />
      </main>
    </div>
  );
}
