"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/dashboard/Sidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import StatusPills from "@/components/dashboard/StatusPills";
import StatCards from "@/components/StatCards";
import SalesChart from "@/components/SalesChart";
import ActivityAndMemory from "@/components/ActivityAndMemory";
import BottomSection from "@/components/BottomSection";
import AskMunim from "@/components/AskMunim";
import { useAuth } from "@/context/AuthContext";

export default function DashboardPage() {
  const router = useRouter();
  const { user, businessName, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState("Overview");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?redirect=/dashboard");
    }
  }, [authLoading, user, router]);

  const hour = typeof window !== "undefined" ? new Date().getHours() : 12;
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-[#07110D] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black text-base shadow-[0_0_20px_rgba(182,242,60,0.5)] animate-pulse">
            M
          </div>
          <p className="text-sm font-medium text-[#BAC8C1]">Loading Munim AI Khata...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#07110D] text-[#F0FDF4] flex relative">
      {/* Persistent Left Sidebar (Desktop - Image 5) */}
      <Sidebar />

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

