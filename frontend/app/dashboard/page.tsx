"use client";

import { useState, useEffect } from "react";
import TopNav from "@/components/TopNav";
import StatCards from "@/components/StatCards";
import SalesChart from "@/components/SalesChart";
import ActivityAndMemory from "@/components/ActivityAndMemory";
import BottomSection from "@/components/BottomSection";
import AskMunim from "@/components/AskMunim";
import { useAuth } from "@/context/AuthContext";

export default function DashboardPage() {
  const { user, businessName, loading: authLoading } = useAuth();
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!authLoading && !user) {
      window.location.href = "/login?redirect=/dashboard";
    }
  }, [authLoading, user]);

  const hour = typeof window !== "undefined" ? new Date().getHours() : 12;
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const handleRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-[#0d1410] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#4efa72] flex items-center justify-center text-[#0d1410] font-black text-base shadow-[0_0_15px_rgba(78,250,114,0.5)] animate-pulse">
            M
          </div>
          <p className="text-sm text-[#9db8a0]">Loading Munim AI Khata...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0d1410]">
      <TopNav active="Overview" />

      {/* Page content */}
      <main className="max-w-[1440px] mx-auto px-6 py-6 space-y-5">
        {/* Welcome */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-[#f0fdf4] text-2xl font-bold">
              {greeting}, {authLoading ? "..." : businessName} 👋
            </h1>
            <p className="text-[#9db8a0] text-sm mt-0.5">
              {authLoading
                ? "Loading store overview..."
                : `Here's what's happening with ${businessName} today.`}
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs text-[#5d7a63]">
            <button
              onClick={handleRefresh}
              className="hover:text-[#4efa72] transition-colors flex items-center gap-1.5 cursor-pointer bg-[#161e19] px-2.5 py-1 rounded-md border border-[rgba(78,250,114,0.1)] hover:border-[rgba(78,250,114,0.3)]"
              title="Refresh dashboard data"
            >
              <span>↻</span>
              <span>Refresh</span>
            </button>
            <div className="flex items-center gap-2">
              <span>
                Status:{" "}
                <span className="text-[#4efa72] font-medium">Live</span>
              </span>
              <div className="w-1.5 h-1.5 rounded-full bg-[#4efa72] animate-[pulse-green_2s_ease-in-out_infinite]" />
            </div>
          </div>
        </div>

        {/* Stat Cards */}
        <StatCards key={`stats-${refreshKey}`} />

        {/* Charts Row */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <SalesChart key={`sales-${refreshKey}`} />
          <ActivityAndMemory key={`activity-${refreshKey}`} />
        </div>

        {/* Bottom Widgets */}
        <BottomSection key={`breakdown-${refreshKey}`} />

        {/* Ask Munim AI bar */}
        <AskMunim />
      </main>
    </div>
  );
}
