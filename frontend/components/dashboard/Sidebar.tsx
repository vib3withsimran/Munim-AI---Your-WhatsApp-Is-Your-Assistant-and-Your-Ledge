"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Package,
  Layers,
  Users,
  CreditCard,
  TrendingUp,
  Sparkles,
  Zap,
  Settings,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: number;
}

const PRIMARY_NAV: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Conversations", href: "/dashboard", icon: MessageSquare, badge: 12 },
  { label: "Orders", href: "/dashboard", icon: Package },
  { label: "Inventory", href: "/dashboard", icon: Layers },
  { label: "Customers", href: "/dashboard", icon: Users },
  { label: "Payments", href: "/dashboard", icon: CreditCard },
  { label: "Insights", href: "/dashboard", icon: TrendingUp },
  { label: "AI & Memory", href: "/dashboard", icon: Sparkles },
];

const SECONDARY_NAV: NavItem[] = [
  { label: "Automations", href: "/dashboard", icon: Zap },
  { label: "Settings", href: "/dashboard", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, businessName, sellerInitial, user } = useAuth();

  return (
    <aside className="hidden lg:flex flex-col justify-between w-60 xl:w-64 bg-[#07110D] border-r border-[#224430]/70 p-4 min-h-screen sticky top-0 flex-shrink-0 z-40 select-none">
      <div className="space-y-6">
        {/* Brand Header */}
        <Link href="/" className="flex items-center gap-2.5 px-2 py-1 group">
          <div className="w-8 h-8 rounded-xl bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black shadow-[0_0_14px_rgba(182,242,60,0.45)] group-hover:scale-105 transition-transform">
            <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 0l2.5 8.5L23 11l-7.5 4.5L17.5 24 12 18.5 6.5 24l2-8.5L1 11l8.5-2.5L12 0z" />
            </svg>
          </div>
          <span className="font-extrabold text-[#F0FDF4] text-lg tracking-tight">
            Munim AI
          </span>
        </Link>

        {/* Primary Menu */}
        <nav aria-label="Sidebar Navigation" className="space-y-1">
          {PRIMARY_NAV.map((item) => {
            const isActive = item.label === "Dashboard" && pathname === "/dashboard";
            const Icon = item.icon;
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? "bg-[#B6F23C]/15 text-[#B6F23C] border border-[#B6F23C]/35 shadow-[0_0_15px_rgba(182,242,60,0.1)]"
                    : "text-[#BAC8C1] hover:text-[#F0FDF4] hover:bg-[#10211A]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? "text-[#B6F23C]" : "text-[#BAC8C1]/70"}`} />
                  <span>{item.label}</span>
                </div>
                {Boolean(item.badge) && (
                  <span className="bg-[#B6F23C] text-[#07110D] font-extrabold text-[11px] px-2 py-0.5 rounded-full leading-none shadow-[0_0_8px_rgba(182,242,60,0.4)]">
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Section Divider */}
        <div className="pt-2 border-t border-[#224430]/60 space-y-1">
          {SECONDARY_NAV.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.label}
                href={item.href}
                className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-[#BAC8C1] hover:text-[#F0FDF4] hover:bg-[#10211A] transition-all"
              >
                <Icon className="w-4 h-4 text-[#BAC8C1]/70" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* User Card & Logout */}
      <div className="pt-4 border-t border-[#224430]/70 flex items-center justify-between gap-3 px-1">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-full bg-[#B6F23C] text-[#07110D] font-black text-xs flex items-center justify-center flex-shrink-0 shadow-[0_0_10px_rgba(182,242,60,0.35)]">
            {sellerInitial || "NC"}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-bold text-[#F0FDF4] truncate">{businessName || "Neha's Closet"}</p>
            <p className="text-[10px] text-[#BAC8C1]/60 truncate">{user?.email || "seller@munim.ai"}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="text-[#BAC8C1] hover:text-[#F87171] p-1.5 rounded-lg hover:bg-[#EF4444]/10 transition-colors cursor-pointer"
          title="Sign Out"
          aria-label="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}

