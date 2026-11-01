"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
<<<<<<< Updated upstream
import { useRouter } from "next/navigation";
import {
  Bell,
  MessageCircle,
  ChevronDown,
  ShoppingBag,
  Package,
  Users,
  Wallet,
  ChevronRight,
  Sparkles,
  Home,
  Layers,
  Grid,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
  MOCK_TOP_PRODUCTS,
} from "@/lib/mocks/dashboard";

export default function MobileDashboardPage() {
  const router = useRouter();
  const { businessName, sellerInitial, user, loading: authLoading } = useAuth();
  const [activeRange, setActiveRange] = useState<"7D" | "30D" | "3M">("30D");
  const [activeBottomNav, setActiveBottomNav] = useState("Home");

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?redirect=/mobile");
    }
  }, [authLoading, user, router]);

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
=======
import { useAuth } from "@/context/AuthContext";
import SplineChart from "@/components/SplineChart";

const MOBILE_MONTH_DATA = [
  { label: "W1", value: 42000 },
  { label: "W2", value: 55000 },
  { label: "W3", value: 68000 },
  { label: "W4", value: 76000 },
  { label: "Oct 30", value: 86420 },
];

const TODAY_TIMELINE = [
  { icon: "✓", bg: "bg-[#22c55e]/20 text-[#4efa72] border-[#22c55e]/30", text: "5 Orders complete ho gaye" },
  { icon: "📦", bg: "bg-[#f59e0b]/20 text-[#fbbf24] border-[#f59e0b]/30", text: "3 naye Orders aaye hain" },
  { icon: "₹", bg: "bg-[#3b82f6]/20 text-[#60a5fa] border-[#3b82f6]/30", text: "2 Payments mile hain" },
  { icon: "🔔", bg: "bg-[#ef4444]/20 text-[#f87171] border-[#ef4444]/30", text: "2 Customers ke paise abhi baki hain" },
];

export default function MobileDashboardPage() {
  const { businessName, sellerInitial } = useAuth();
  const [activeTab, setActiveTab] = useState("Home");
>>>>>>> Stashed changes

  return (
    <div className="min-h-screen bg-[#07110D] text-[#F0FDF4] flex justify-center py-0 sm:py-6">
      {/* Mobile Shell Frame */}
      <div className="w-full max-w-[420px] bg-[#07110D] min-h-screen sm:min-h-[890px] sm:rounded-[44px] sm:border-2 sm:border-[#224430] shadow-[0_25px_65px_rgba(0,0,0,0.85),0_0_40px_rgba(182,242,60,0.15)] flex flex-col relative overflow-hidden pb-24">
        {/* Status Bar */}
        <div className="pt-3 px-6 pb-1 flex items-center justify-between text-xs text-[#BAC8C1]/80 font-medium select-none">
          <span className="font-semibold text-xs">9:41</span>
          <div className="w-20 h-4 bg-[#0B1A13] rounded-full mx-auto hidden sm:block border border-[#224430]" />
          <div className="flex items-center gap-1.5 text-[10px]">
            <span>5G</span>
            <div className="w-5 h-2.5 rounded-sm border border-[#BAC8C1] p-0.5 flex items-center">
              <div className="h-full w-full bg-[#B6F23C] rounded-xs" />
            </div>
          </div>
        </div>

        {/* Top Header */}
        <div className="px-5 py-3 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black shadow-[0_0_12px_rgba(182,242,60,0.4)]">
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M12 0l2.5 8.5L23 11l-7.5 4.5L17.5 24 12 18.5 6.5 24l2-8.5L1 11l8.5-2.5L12 0z" />
              </svg>
            </div>
            <span className="font-extrabold text-base text-[#F0FDF4]">Munim AI</span>
          </Link>

          <div className="flex items-center gap-2.5">
            <button
              className="relative w-8 h-8 rounded-full bg-[#10211A] border border-[#224430] flex items-center justify-center text-[#BAC8C1]"
              aria-label="Notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#EF4444]" />
            </button>
<<<<<<< Updated upstream
            <div className="w-8 h-8 rounded-full bg-[#B6F23C] text-[#07110D] font-black text-xs flex items-center justify-center shadow-[0_0_8px_rgba(182,242,60,0.35)]">
              {sellerInitial || "NC"}
=======

            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-[#161e19] border border-[rgba(78,250,114,0.25)] flex items-center justify-center text-xs font-bold text-[#4efa72]">
              {sellerInitial}
>>>>>>> Stashed changes
            </div>
          </div>
        </div>

        {/* Greeting Banner */}
<<<<<<< Updated upstream
        <div className="px-5 pt-2 pb-3">
          <h1 className="text-xl font-black text-[#F0FDF4] flex items-center gap-1.5">
            Good afternoon, {businessName || "Neha"} 👋
          </h1>
          <p className="text-xs text-[#BAC8C1] mt-0.5">
            Here&apos;s what&apos;s happening with {businessName || "Neha's Closet"} today.
          </p>
        </div>

        {/* 2-Column Status Pills */}
        <div className="px-5 pb-3 grid grid-cols-2 gap-2.5">
          {/* Pill 1: Munim AI Active */}
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-2.5 h-2.5 rounded-full bg-[#B6F23C] animate-pulse shadow-[0_0_6px_rgba(182,242,60,0.8)] flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-[11px] font-bold text-[#F0FDF4] truncate">
                  Munim AI Active
                </p>
                <p className="text-[9px] text-[#BAC8C1] truncate">Auto-replies ON</p>
              </div>
            </div>
            <ChevronDown className="w-3 h-3 text-[#BAC8C1]/60 flex-shrink-0 ml-1" />
=======
        <div className="px-5 pt-3 pb-2 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-[#f0fdf4] flex items-center gap-1.5">
              Namaste {businessName}! 👋
            </h1>
            <p className="text-xs text-[#9db8a0] mt-0.5">Aaj ka business yahan dekhiye.</p>
>>>>>>> Stashed changes
          </div>

          {/* Pill 2: WhatsApp Connected */}
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-5 h-5 rounded-full bg-[#25D366]/20 text-[#25D366] flex items-center justify-center flex-shrink-0">
                <MessageCircle className="w-3 h-3" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-bold text-[#F0FDF4] truncate">
                  WhatsApp
                </p>
                <p className="text-[9px] text-[#BAC8C1] truncate">Connected</p>
              </div>
            </div>
            <ChevronDown className="w-3 h-3 text-[#BAC8C1]/60 flex-shrink-0 ml-1" />
          </div>
        </div>

        {/* 2x2 KPI Stat Cards */}
        <div className="px-5 pb-3 grid grid-cols-2 gap-2.5">
          {/* Revenue */}
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-1">
              <ShoppingBag className="w-4 h-4 text-[#B6F23C]" />
              <span className="text-[10px] font-bold text-[#B6F23C] bg-[#B6F23C]/15 px-1.5 py-0.5 rounded-md">
                ↑ +18%
              </span>
            </div>
            <div>
              <p className="text-lg font-black text-[#F0FDF4] leading-tight">₹86,420</p>
              <p className="text-[10px] text-[#BAC8C1] mt-0.5">Revenue (this month)</p>
            </div>
          </div>

          {/* Orders */}
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-1">
              <Package className="w-4 h-4 text-[#B6F23C]" />
              <span className="text-[10px] font-bold text-[#B6F23C] bg-[#B6F23C]/15 px-1.5 py-0.5 rounded-md">
                ↑ +12%
              </span>
            </div>
            <div>
              <p className="text-lg font-black text-[#F0FDF4] leading-tight">124</p>
              <p className="text-[10px] text-[#BAC8C1] mt-0.5">Orders</p>
            </div>
          </div>

          {/* Active Customers */}
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-1">
              <Users className="w-4 h-4 text-[#B6F23C]" />
              <span className="text-[10px] font-bold text-[#B6F23C] bg-[#B6F23C]/15 px-1.5 py-0.5 rounded-md">
                ↑ +24%
              </span>
            </div>
            <div>
              <p className="text-lg font-black text-[#F0FDF4] leading-tight">67</p>
              <p className="text-[10px] text-[#BAC8C1] mt-0.5">Active customers</p>
            </div>
          </div>

          {/* Pending Dues */}
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-1">
              <Wallet className="w-4 h-4 text-[#B6F23C]" />
              <span className="text-[10px] font-bold text-[#F87171] bg-[#EF4444]/15 px-1.5 py-0.5 rounded-md">
                ↑ +6%
              </span>
            </div>
            <div>
              <p className="text-lg font-black text-[#F0FDF4] leading-tight">₹12,480</p>
              <p className="text-[10px] text-[#BAC8C1] mt-0.5">Pending dues</p>
            </div>
          </div>
        </div>

        {/* Sales Overview Chart */}
        <div className="px-5 pb-3">
          <div className="bg-[#0B1A13] border border-[#224430] rounded-3xl p-4">
            <div className="flex items-center justify-between mb-2">
              <div>
                <p className="text-xs font-bold text-[#BAC8C1]">Sales Overview</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-xl font-black text-[#F0FDF4]">₹86,420</span>
                  <span className="text-[10px] font-bold text-[#B6F23C]">
                    ↑ +18% vs last 30 days
                  </span>
                </div>
              </div>

              {/* Range Pills */}
              <div className="flex items-center gap-1 bg-[#10211A] border border-[#224430] p-0.5 rounded-full">
                {(["7D", "30D", "3M"] as const).map((r) => (
                  <button
                    key={r}
                    onClick={() => setActiveRange(r)}
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold transition-all ${
                      activeRange === r
                        ? "bg-[#B6F23C] text-[#07110D]"
                        : "text-[#BAC8C1]"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            {/* Neon Spline Chart SVG */}
            <div className="h-28 w-full relative pt-2">
              <svg
                className="w-full h-full overflow-visible"
                viewBox="0 0 320 100"
                preserveAspectRatio="none"
              >
                <defs>
                  <linearGradient id="mobileSalesGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#B6F23C" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#B6F23C" stopOpacity="0.0" />
                  </linearGradient>
                </defs>
                <line x1="0" y1="20" x2="320" y2="20" stroke="#224430" strokeDasharray="3 3" opacity="0.3" />
                <line x1="0" y1="50" x2="320" y2="50" stroke="#224430" strokeDasharray="3 3" opacity="0.3" />
                <line x1="0" y1="80" x2="320" y2="80" stroke="#224430" strokeDasharray="3 3" opacity="0.3" />

                <path
                  d="M0 70 C40 70 60 50 100 55 C140 60 170 30 210 35 C250 40 280 15 320 12 L320 100 L0 100 Z"
                  fill="url(#mobileSalesGrad)"
                />
                <path
                  d="M0 70 C40 70 60 50 100 55 C140 60 170 30 210 35 C250 40 280 15 320 12"
                  fill="none"
                  stroke="#B6F23C"
                  strokeWidth="2.5"
                  className="drop-shadow-[0_0_8px_rgba(182,242,60,0.6)]"
                />
                <circle cx="320" cy="12" r="3.5" fill="#B6F23C" stroke="#07110D" strokeWidth="2" />
              </svg>

              <div className="absolute right-0 top-1 bg-[#10211A] border border-[#B6F23C]/50 rounded-lg px-2 py-1 shadow-lg text-right">
                <p className="text-[8px] text-[#BAC8C1]">Oct 30</p>
                <p className="text-[10px] font-black text-[#B6F23C]">₹86,420</p>
              </div>
            </div>

            <div className="flex justify-between text-[8px] text-[#BAC8C1]/60 pt-2 border-t border-[#224430]/40">
              <span>Oct 1</span>
              <span>Oct 5</span>
              <span>Oct 10</span>
              <span>Oct 15</span>
              <span>Oct 20</span>
              <span>Oct 25</span>
              <span>Oct 30</span>
            </div>
          </div>
        </div>

        {/* 2-Column Orders by Status + Top Products */}
        <div className="px-5 pb-3 grid grid-cols-2 gap-2.5">
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#F0FDF4]">Orders by Status</span>
              <ChevronRight className="w-3.5 h-3.5 text-[#BAC8C1]/60" />
            </div>

            <div className="space-y-1.5 text-[10px]">
              <div className="flex items-center justify-between">
                <span className="text-[#BAC8C1] flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#B6F23C]" />
                  Completed
                </span>
                <span className="font-bold text-[#F0FDF4]">82</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#BAC8C1] flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#60A5FA]" />
                  Processing
                </span>
                <span className="font-bold text-[#F0FDF4]">18</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#BAC8C1] flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#FDBA74]" />
                  Pending Pay
                </span>
                <span className="font-bold text-[#F0FDF4]">12</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#BAC8C1] flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#C084FC]" />
                  Cancelled
                </span>
                <span className="font-bold text-[#F0FDF4]">10</span>
              </div>
            </div>
          </div>

          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-[#F0FDF4]">Top Products</span>
              <ChevronRight className="w-3.5 h-3.5 text-[#BAC8C1]/60" />
            </div>

            <div className="space-y-1.5 text-[10px]">
              {MOCK_TOP_PRODUCTS.map((p) => (
                <div key={p.name} className="flex items-center justify-between">
                  <span className="text-[#BAC8C1] truncate max-w-[85px]">{p.name}</span>
                  <span className="font-bold text-[#F0FDF4]">
                    ₹{Math.round(p.revenue / 1000)}k
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Today's Activity (4 Icons Row) */}
        <div className="px-5 pb-3">
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-3">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-xs font-bold text-[#F0FDF4]">Today&apos;s Activity</span>
              <button className="text-[10px] font-bold text-[#B6F23C] flex items-center gap-0.5">
                <span>View All</span>
                <ChevronRight className="w-3 h-3" />
              </button>
            </div>

            <div className="grid grid-cols-4 gap-2 text-center">
              <div className="bg-[#10211A] border border-[#224430] rounded-xl p-2 flex flex-col items-center">
                <MessageCircle className="w-4 h-4 text-[#B6F23C] mb-1" />
                <span className="text-xs font-black text-[#F0FDF4]">42</span>
                <span className="text-[9px] text-[#BAC8C1]">Messages</span>
              </div>
              <div className="bg-[#10211A] border border-[#224430] rounded-xl p-2 flex flex-col items-center">
                <Package className="w-4 h-4 text-[#B6F23C] mb-1" />
                <span className="text-xs font-black text-[#F0FDF4]">9</span>
                <span className="text-[9px] text-[#BAC8C1]">Orders</span>
              </div>
              <div className="bg-[#10211A] border border-[#224430] rounded-xl p-2 flex flex-col items-center">
                <Wallet className="w-4 h-4 text-[#B6F23C] mb-1" />
                <span className="text-xs font-black text-[#F0FDF4]">8</span>
                <span className="text-[9px] text-[#BAC8C1]">Payments</span>
              </div>
              <div className="bg-[#10211A] border border-[#224430] rounded-xl p-2 flex flex-col items-center">
                <Bell className="w-4 h-4 text-[#B6F23C] mb-1" />
                <span className="text-xs font-black text-[#F0FDF4]">3</span>
                <span className="text-[9px] text-[#BAC8C1]">Reminders</span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Memory Highlights */}
        <div className="px-5 pb-4">
          <div className="bg-[#0B1A13] border border-[#224430] rounded-2xl p-3 flex items-center justify-between">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-7 h-7 rounded-full bg-[#B6F23C]/15 border border-[#B6F23C]/30 text-[#B6F23C] flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-[#F0FDF4] truncate">
                  Priya prefers blue kurtis, size M
                </p>
                <p className="text-[9px] text-[#BAC8C1]/70">Updated today</p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-[#BAC8C1]/60 flex-shrink-0" />
          </div>
        </div>

        {/* Fixed Mobile Bottom Tab Bar */}
        <div className="fixed sm:absolute bottom-0 inset-x-0 bg-[#0B1A13]/95 border-t border-[#224430] px-4 py-2.5 backdrop-blur-xl flex items-center justify-around z-50">
          {[
            { label: "Home", icon: Home },
            { label: "Orders", icon: Package },
            { label: "Customers", icon: Users },
            { label: "Inventory", icon: Layers },
            { label: "More", icon: Grid },
          ].map((item) => {
            const isActive = activeBottomNav === item.label;
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                onClick={() => setActiveBottomNav(item.label)}
                className={`flex flex-col items-center gap-1 cursor-pointer transition-colors ${
                  isActive ? "text-[#B6F23C]" : "text-[#BAC8C1]/60 hover:text-[#BAC8C1]"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-[10px] font-semibold">{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

