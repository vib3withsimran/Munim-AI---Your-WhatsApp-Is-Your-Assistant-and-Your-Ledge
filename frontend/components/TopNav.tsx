"use client";

import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";

const NAV_ITEMS = [
  { label: "Overview", href: "/dashboard", icon: "⊡" },
  { label: "Conversations", href: "/dashboard", icon: "💬", badge: 0 },
  { label: "Orders", href: "/dashboard", icon: "📦" },
  { label: "Inventory", href: "/dashboard", icon: "🏪" },
  { label: "Customers", href: "/dashboard", icon: "👥" },
  { label: "Payments", href: "/dashboard", icon: "₹" },
  { label: "Insights", href: "/dashboard", icon: "📊" },
  { label: "Settings", href: "/dashboard", icon: "⚙" },
];

export default function TopNav({ active = "Overview" }: { active?: string }) {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const { user, profile, businessName, sellerInitial, logout } = useAuth();

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  // Close menu on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const storePhone = profile?.phone
    ? profile.phone.startsWith("+")
      ? profile.phone
      : `+${profile.phone}`
    : "WhatsApp Connected";

  return (
    <header
      className={`sticky top-0 z-50 w-full transition-all duration-300 ${
        scrolled
          ? "bg-[#0d1410]/95 backdrop-blur-md border-b border-[rgba(78,250,114,0.15)] shadow-[0_4px_20px_rgba(0,0,0,0.4)]"
          : "bg-[#0d1410]/80 backdrop-blur-sm border-b border-[rgba(78,250,114,0.08)]"
      }`}
    >
      <div className="flex items-center h-14 px-6 gap-2">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 mr-6 flex-shrink-0">
          <div className="w-8 h-8 rounded-lg bg-[#4efa72] flex items-center justify-center shadow-[0_0_12px_rgba(78,250,114,0.5)]">
            <span className="text-[#0d1410] font-black text-sm">M</span>
          </div>
          <span className="font-bold text-[#f0fdf4] text-base tracking-tight">Munim AI</span>
        </Link>

        {/* Nav Items */}
        <nav className="flex items-center gap-1 flex-1 overflow-x-auto scrollbar-hide">
          {NAV_ITEMS.map((item) => {
            const isActive = item.label === active;
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`relative flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200 ${
                  isActive
                    ? "bg-[rgba(78,250,114,0.15)] text-[#4efa72] border border-[rgba(78,250,114,0.3)]"
                    : "text-[#9db8a0] hover:text-[#f0fdf4] hover:bg-[rgba(255,255,255,0.05)]"
                }`}
              >
                <span className="text-xs">{item.icon}</span>
                {item.label}
                {Boolean(item.badge) && (
                  <span className="ml-0.5 bg-[#4efa72] text-[#0d1410] text-[10px] font-bold px-1.5 py-0.5 rounded-full leading-none">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right Side */}
        <div className="flex items-center gap-3 ml-4 flex-shrink-0">
          {/* AI Status */}
          <div className="hidden md:flex items-center gap-2 bg-[#161e19] border border-[rgba(78,250,114,0.2)] rounded-full px-3 py-1.5">
            <div className="w-2 h-2 rounded-full bg-[#4efa72] animate-[pulse-green_2s_ease-in-out_infinite] shadow-[0_0_6px_rgba(78,250,114,0.7)]" />
            <div>
              <p className="text-[#4efa72] text-[11px] font-semibold leading-tight">Munim AI Active</p>
              <p className="text-[#5d7a63] text-[10px] leading-tight">Auto-replies ON</p>
            </div>
          </div>

          {/* WhatsApp Connected */}
          <div className="hidden lg:flex items-center gap-2 bg-[#161e19] border border-[rgba(78,250,114,0.12)] rounded-full px-3 py-1.5">
            <div className="w-6 h-6 rounded-full bg-[#25D366] flex items-center justify-center text-[11px]">📱</div>
            <div>
              <p className="text-[#f0fdf4] text-[11px] font-semibold leading-tight">{businessName}</p>
              <p className="text-[#5d7a63] text-[10px] leading-tight">{storePhone}</p>
            </div>
          </div>

          {/* User Profile & Logout Dropdown */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="w-8 h-8 rounded-full bg-gradient-to-br from-[#4efa72] to-[#3acc5c] flex items-center justify-center text-[#0d1410] font-black text-sm cursor-pointer shadow-[0_0_10px_rgba(78,250,114,0.3)] hover:scale-105 transition-transform"
              title="Seller Account Menu"
              aria-label="Seller Account Menu"
            >
              {sellerInitial}
            </button>

            {menuOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-[#0f1712] border border-[rgba(78,250,114,0.2)] rounded-xl shadow-2xl p-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="pb-2 mb-2 border-b border-[rgba(78,250,114,0.1)]">
                  <p className="text-xs font-bold text-[#f0fdf4] truncate">{businessName}</p>
                  <p className="text-[11px] text-[#5d7a63] truncate">{user?.email}</p>
                </div>

                <div className="py-1">
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      logout();
                    }}
                    className="w-full text-left px-2 py-1.5 rounded-lg text-xs font-semibold text-[#f87171] hover:bg-[rgba(248,113,113,0.1)] transition-colors flex items-center gap-2 cursor-pointer"
                  >
                    <span>🚪</span>
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
