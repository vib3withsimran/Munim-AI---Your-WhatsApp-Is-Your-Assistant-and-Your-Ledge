"use client";

import { useState, useEffect } from "react";
<<<<<<< Updated upstream
import { useRouter } from "next/navigation";
import Sidebar from "@/components/dashboard/Sidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import StatusPills from "@/components/dashboard/StatusPills";
=======
import TopNav from "@/components/TopNav";
>>>>>>> Stashed changes
import StatCards from "@/components/StatCards";
import SalesChart from "@/components/SalesChart";
import ActivityAndMemory from "@/components/ActivityAndMemory";
import BottomSection from "@/components/BottomSection";
import AskMunim from "@/components/AskMunim";
import { useAuth } from "@/context/AuthContext";

export default function DashboardPage() {
<<<<<<< Updated upstream
  const router = useRouter();
  const { user, businessName, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState("Overview");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?redirect=/dashboard");
    }
  }, [authLoading, user, router]);
=======
  const { user, businessName, loading: authLoading } = useAuth();
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (!authLoading && !user) {
      window.location.href = "/login?redirect=/dashboard";
    }
  }, [authLoading, user]);
>>>>>>> Stashed changes

  const hour = typeof window !== "undefined" ? new Date().getHours() : 12;
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

<<<<<<< Updated upstream
  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-[#07110D] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black text-base shadow-[0_0_20px_rgba(182,242,60,0.5)] animate-pulse">
            M
          </div>
          <p className="text-sm font-medium text-[#BAC8C1]">Loading Munim AI Khata...</p>
=======
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
>>>>>>> Stashed changes
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#07110D] text-[#F0FDF4] flex relative">
      {/* Persistent Left Sidebar (Desktop - Image 5) */}
      <Sidebar />

<<<<<<< Updated upstream
      {/* Main Dashboard Canvas */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Header Row with Pill Tabs and User Actions */}
        <div className="px-5 sm:px-8 bg-[#07110D]/90 backdrop-blur-xl sticky top-0 z-30">
          <DashboardHeader
            activeTab={activeTab}
            onTabChange={setActiveTab}
            onToggleMobileMenu={() => setMobileMenuOpen(!mobileMenuOpen)}
          />
        </div>

        {/* Dashboard Main Scroll Area */}
        <main className="flex-1 max-w-[1440px] w-full mx-auto px-5 sm:px-8 py-6 space-y-6">
          {/* Welcome Banner + Status Badges */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-black text-[#F0FDF4] tracking-tight flex items-center gap-2">
                <span>{greeting}, {businessName || "Neha"}</span>
                <span className="text-2xl">👋</span>
              </h1>
              <p className="text-xs sm:text-sm text-[#BAC8C1] mt-1">
                Here&apos;s what&apos;s happening with {businessName || "Neha's Closet"} today.
              </p>
            </div>

            {/* Right Status Badges (Munim AI Active, WhatsApp Connected) */}
            <StatusPills />
          </div>

          {/* 4 KPI Stat Cards */}
          <StatCards />
=======
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
>>>>>>> Stashed changes

          {/* Middle Row: Sales Overview Spline + Today's Activity & AI Memory */}
          <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
            <div className="xl:col-span-6">
              <SalesChart />
            </div>
            <div className="xl:col-span-6">
              <ActivityAndMemory />
            </div>
          </div>

          {/* Bottom Breakdown Widgets: Orders by Status, Top Products, Pending Dues */}
          <BottomSection />

          {/* Floating Command Bar: Ask Munim AI */}
          <div className="pt-2">
            <AskMunim />
          </div>
        </main>
      </div>
    </div>
  );
}

