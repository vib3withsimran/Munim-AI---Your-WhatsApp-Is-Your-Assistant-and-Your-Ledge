"use client";

import { useState } from "react";
import Link from "next/link";
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

  return (
    <div className="min-h-screen bg-[#070b09] text-[#f0fdf4] flex justify-center py-0 sm:py-6">
      {/* Mobile Shell Frame */}
      <div className="w-full max-w-[420px] bg-[#0d1410] min-h-screen sm:min-h-[860px] sm:rounded-[40px] sm:border-4 sm:border-[#1a251f] shadow-2xl flex flex-col relative overflow-hidden pb-20">
        
        {/* Status Bar */}
        <div className="pt-3 px-6 pb-2 flex items-center justify-between text-xs text-[#9db8a0] font-medium">
          <span>9:41</span>
          <div className="w-20 h-4 bg-[#070b09] rounded-full mx-auto hidden sm:block" />
          <div className="flex items-center gap-1.5 text-[11px]">
            <span>5G</span>
            <span>100%</span>
          </div>
        </div>

        {/* Top Header */}
        <div className="px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-[#22c55e] flex items-center justify-center text-[#0d1410] font-black text-sm shadow-[0_0_12px_rgba(78,250,114,0.4)]">
              🏪
            </div>
            <span className="font-bold text-base text-[#f0fdf4]">Munim AI</span>
          </div>

          <div className="flex items-center gap-2">
            {/* Notification Bell */}
            <button className="relative w-8 h-8 rounded-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] flex items-center justify-center text-sm">
              🔔
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#ef4444]" />
            </button>

            {/* Avatar */}
            <div className="w-8 h-8 rounded-full bg-[#161e19] border border-[rgba(78,250,114,0.25)] flex items-center justify-center text-xs font-bold text-[#4efa72]">
              {sellerInitial}
            </div>

            {/* Theme Toggle */}
            <button className="w-8 h-8 rounded-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] flex items-center justify-center text-xs">
              ☀️
            </button>
          </div>
        </div>

        {/* Greeting Banner */}
        <div className="px-5 pt-3 pb-2 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-[#f0fdf4] flex items-center gap-1.5">
              Namaste {businessName}! 👋
            </h1>
            <p className="text-xs text-[#9db8a0] mt-0.5">Aaj ka business yahan dekhiye.</p>
          </div>

          {/* AI Active Pill */}
          <div className="bg-[#161e19] border border-[rgba(78,250,114,0.3)] rounded-full px-3 py-1 flex items-center gap-1.5 shadow-[0_0_10px_rgba(78,250,114,0.1)]">
            <span className="w-2 h-2 rounded-full bg-[#4efa72] animate-pulse" />
            <span className="text-[11px] font-semibold text-[#4efa72]">AI Chal Raha Hai</span>
          </div>
        </div>

        {/* 4 Hinglish Stat Cards */}
        <div className="px-5 py-3 grid grid-cols-2 gap-2.5">
          {/* Card 1: Aaj ki Bikri */}
          <div className="glass-card p-3.5 bg-[#121b16] rounded-2xl border border-[rgba(78,250,114,0.15)] flex flex-col items-center text-center">
            <div className="w-8 h-8 rounded-full bg-[#22c55e]/20 text-[#4efa72] flex items-center justify-center text-xs font-bold mb-1.5">
              ₹
            </div>
            <span className="text-[11px] text-[#9db8a0]">Aaj ki Bikri</span>
            <span className="text-lg font-bold text-[#f0fdf4] mt-0.5">₹8,450</span>
            <span className="text-[10px] font-semibold text-[#4efa72] mt-1 bg-[#22c55e]/10 px-2 py-0.5 rounded-full">
              ↑ +18%
            </span>
          </div>

          {/* Card 2: Aaj ke Orders */}
          <div className="glass-card p-3.5 bg-[#121b16] rounded-2xl border border-[rgba(78,250,114,0.15)] flex flex-col items-center text-center">
            <div className="w-8 h-8 rounded-full bg-[#3b82f6]/20 text-[#60a5fa] flex items-center justify-center text-xs font-bold mb-1.5">
              🛒
            </div>
            <span className="text-[11px] text-[#9db8a0]">Aaj ke Orders</span>
            <span className="text-lg font-bold text-[#f0fdf4] mt-0.5">12</span>
            <span className="text-[10px] font-semibold text-[#4efa72] mt-1 bg-[#22c55e]/10 px-2 py-0.5 rounded-full">
              ↑ +12%
            </span>
          </div>

          {/* Card 3: Customers */}
          <div className="glass-card p-3.5 bg-[#121b16] rounded-2xl border border-[rgba(78,250,114,0.15)] flex flex-col items-center text-center">
            <div className="w-8 h-8 rounded-full bg-[#06b6d4]/20 text-[#22d3ee] flex items-center justify-center text-xs font-bold mb-1.5">
              👥
            </div>
            <span className="text-[11px] text-[#9db8a0]">Customers (Baatein)</span>
            <span className="text-lg font-bold text-[#f0fdf4] mt-0.5">28</span>
            <span className="text-[10px] text-[#5d7a63] mt-1">Active chats</span>
          </div>

          {/* Card 4: Baki Paise */}
          <div className="glass-card p-3.5 bg-[#121b16] rounded-2xl border border-[rgba(78,250,114,0.15)] flex flex-col items-center text-center">
            <div className="w-8 h-8 rounded-full bg-[#f59e0b]/20 text-[#fbbf24] flex items-center justify-center text-xs font-bold mb-1.5">
              👛
            </div>
            <span className="text-[11px] text-[#9db8a0]">Baki Paise</span>
            <span className="text-lg font-bold text-[#f0fdf4] mt-0.5">₹4,200</span>
            <span className="text-[10px] font-semibold text-[#f87171] mt-1 bg-[#ef4444]/10 px-2 py-0.5 rounded-full">
              ↑ +6%
            </span>
          </div>
        </div>

        {/* Monthly Chart Card */}
        <div className="px-5 py-2">
          <div className="glass-card p-4 bg-[#121b16] rounded-2xl border border-[rgba(78,250,114,0.18)]">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <span className="text-[#4efa72]">📈</span>
                <span className="text-xs font-bold text-[#f0fdf4]">Is Mahine ki Bikri</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-sm font-black text-[#f0fdf4]">₹86,420</span>
                <span className="text-[10px] font-bold text-[#4efa72] bg-[#22c55e]/15 px-1.5 py-0.5 rounded-full">
                  ↑ +18%
                </span>
              </div>
            </div>
            <SplineChart data={MOBILE_MONTH_DATA} height={100} showTooltip={true} />
          </div>
        </div>

        {/* Aaj Kya Ho Raha Hai? Timeline */}
        <div className="px-5 py-2">
          <div className="glass-card p-4 bg-[#121b16] rounded-2xl border border-[rgba(78,250,114,0.15)]">
            <div className="flex items-center gap-1.5 mb-3">
              <span className="text-sm">🗓️</span>
              <h2 className="text-xs font-bold text-[#f0fdf4] tracking-wide">Aaj Kya Ho Raha Hai?</h2>
            </div>

            <div className="space-y-2">
              {TODAY_TIMELINE.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-[#0d1410] border border-[rgba(78,250,114,0.08)] active:bg-[#161e19] transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold border ${item.bg}`}>
                      {item.icon}
                    </div>
                    <span className="text-xs font-medium text-[#f0fdf4]">{item.text}</span>
                  </div>
                  <span className="text-xs text-[#5d7a63]">›</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 2 Big Thumb CTAs */}
        <div className="px-5 pt-2 pb-4 grid grid-cols-2 gap-3">
          <a
            href="https://wa.me/14155238886?text=Hi+Munim+AI"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 bg-[#22c55e] hover:bg-[#16a34a] text-[#070b09] font-bold text-xs py-3.5 px-3 rounded-2xl shadow-[0_0_15px_rgba(34,197,94,0.35)] transition-all active:scale-95"
          >
            <span className="text-base">📱</span>
            <span>Customer se baat karo</span>
          </a>

          <button
            onClick={() => alert("Product Catalog Form khul gaya")}
            className="flex items-center justify-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] text-[#f0fdf4] font-bold text-xs py-3.5 px-3 rounded-2xl shadow-[0_0_15px_rgba(124,58,237,0.35)] transition-all active:scale-95"
          >
            <span className="text-base font-black">+</span>
            <span>Naya Product jodo</span>
          </button>
        </div>

        {/* Bottom Tab Navigation */}
        <div className="absolute bottom-0 left-0 right-0 h-16 bg-[#0d1410]/95 backdrop-blur-md border-t border-[rgba(78,250,114,0.15)] flex items-center justify-around px-2 z-20">
          {[
            { label: "Home", icon: "🏠" },
            { label: "Orders", icon: "📦" },
            { label: "Customers", icon: "👥" },
            { label: "Reports", icon: "📊" },
          ].map((tab) => {
            const isActive = activeTab === tab.label;
            return (
              <button
                key={tab.label}
                onClick={() => setActiveTab(tab.label)}
                className={`flex flex-col items-center gap-1 transition-all ${
                  isActive ? "text-[#4efa72] scale-105" : "text-[#5d7a63] hover:text-[#9db8a0]"
                }`}
              >
                <span className="text-base leading-none">{tab.icon}</span>
                <span className="text-[10px] font-semibold">{tab.label}</span>
              </button>
            );
          })}
        </div>

      </div>
    </div>
  );
}

