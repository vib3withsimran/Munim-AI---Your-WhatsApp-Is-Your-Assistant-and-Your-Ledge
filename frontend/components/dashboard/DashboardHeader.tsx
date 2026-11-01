"use client";

import { useState } from "react";
import Link from "next/link";
import { Bell, Menu } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const HEADER_TABS = [
  "Overview",
  "Conversations",
  "Orders",
  "Inventory",
  "Customers",
  "Payments",
  "Insights",
  "Settings",
] as const;

export default function DashboardHeader({
  activeTab = "Overview",
  onTabChange,
  onToggleMobileMenu,
}: {
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  onToggleMobileMenu?: () => void;
}) {
  const { sellerInitial, businessName } = useAuth();
  const [hasNotifications] = useState(true);

  return (
    <header className="w-full flex items-center justify-between gap-4 py-3 border-b border-[#224430]/60">
      {/* Mobile Hamburger */}
      <div className="flex items-center gap-3 lg:hidden">
        <button
          onClick={onToggleMobileMenu}
          className="p-2 rounded-xl bg-[#10211A] border border-[#224430] text-[#BAC8C1] hover:text-white"
          aria-label="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black text-xs shadow-[0_0_10px_rgba(182,242,60,0.4)]">
            M
          </div>
          <span className="font-bold text-[#F0FDF4] text-sm">Munim AI</span>
        </Link>
      </div>

      {/* Pill Navigation Tabs (matches Image 5 top pill row) */}
      <nav aria-label="Dashboard Tabs" className="hidden lg:flex items-center gap-2 overflow-x-auto scrollbar-hide py-1">
        {HEADER_TABS.map((tab) => {
          const isActive = tab === activeTab;
          return (
            <button
              key={tab}
              onClick={() => onTabChange?.(tab)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                isActive
                  ? "bg-[#224430] text-[#B6F23C] border border-[#B6F23C]/40 shadow-[0_0_12px_rgba(182,242,60,0.2)]"
                  : "text-[#BAC8C1] hover:text-[#F0FDF4] hover:bg-[#10211A]"
              }`}
            >
              {tab}
            </button>
          );
        })}
      </nav>

      {/* Right User Actions (Bell + Avatar) */}
      <div className="flex items-center gap-3 ml-auto flex-shrink-0">
        <button
          className="relative w-9 h-9 rounded-full bg-[#10211A] border border-[#224430] hover:border-[#B6F23C]/40 flex items-center justify-center text-[#BAC8C1] hover:text-[#F0FDF4] transition-all cursor-pointer"
          title="Notifications"
          aria-label="Notifications"
        >
          <Bell className="w-4 h-4" />
          {hasNotifications && (
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#EF4444] ring-2 ring-[#07110D]" />
          )}
        </button>

        <div
          className="w-9 h-9 rounded-full bg-[#B6F23C] text-[#07110D] font-black text-xs flex items-center justify-center shadow-[0_0_10px_rgba(182,242,60,0.35)] select-none cursor-default"
          title={businessName}
        >
          {sellerInitial || "NC"}
        </div>
      </div>
    </header>
  );
}

