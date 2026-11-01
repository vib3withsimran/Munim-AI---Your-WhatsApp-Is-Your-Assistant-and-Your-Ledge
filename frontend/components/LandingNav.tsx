"use client";

import Link from "next/link";
import { useState } from "react";
import { MessageCircle, Menu, X, ArrowRight } from "lucide-react";

export default function LandingNav() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="fixed top-4 inset-x-0 mx-auto w-[92%] max-w-5xl z-50">
      <nav
        aria-label="Main Navigation"
        className="bg-[#07110D]/90 backdrop-blur-xl border border-[#224430]/80 rounded-full px-4 sm:px-6 py-2.5 shadow-[0_12px_40px_rgba(0,0,0,0.65),0_0_24px_rgba(182,242,60,0.08)] flex items-center justify-between transition-all"
      >
        {/* Brand Logo with Asterisk Icon */}
        <Link href="/" className="flex items-center gap-2.5 group focus:outline-none">
          <div className="w-8 h-8 rounded-xl bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black shadow-[0_0_14px_rgba(182,242,60,0.5)] group-hover:scale-105 transition-transform">
            <svg
              className="w-4 h-4 fill-current"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M12 0l2.5 8.5L23 11l-7.5 4.5L17.5 24 12 18.5 6.5 24l2-8.5L1 11l8.5-2.5L12 0z" />
            </svg>
          </div>
          <span className="font-extrabold text-[#F0FDF4] text-base sm:text-lg tracking-tight">
            Munim AI
          </span>
        </Link>

        {/* Desktop Nav Links */}
        <div className="hidden md:flex items-center gap-7 text-sm font-medium">
          <a
            href="#features"
            className="text-[#BAC8C1] hover:text-[#B6F23C] transition-colors"
          >
            Features
          </a>
          <a
            href="#workflow"
            className="text-[#BAC8C1] hover:text-[#B6F23C] transition-colors"
          >
            Kaise Kaam Karta Hai?
          </a>
          <Link
            href="/dashboard"
            className="text-[#BAC8C1] hover:text-[#B6F23C] transition-colors"
          >
            Dashboard
          </Link>
        </div>

        {/* Desktop Right Actions */}
        <div className="hidden md:flex items-center gap-3.5">
          <Link
            href="/login"
            className="text-xs sm:text-sm font-semibold text-[#BAC8C1] hover:text-[#F0FDF4] px-3 py-1.5 transition-colors"
          >
            Login
          </Link>
          <a
            href="https://wa.me/14155238886?text=Hi+Munim+AI!"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 bg-[#B6F23C] hover:bg-[#c6f663] text-[#07110D] font-bold text-xs sm:text-sm px-4 sm:px-5 py-2 rounded-full transition-all duration-200 shadow-[0_0_18px_rgba(182,242,60,0.35)] hover:shadow-[0_0_26px_rgba(182,242,60,0.55)] hover:scale-105 active:scale-95"
          >
            <MessageCircle className="w-3.5 h-3.5" />
            <span>WhatsApp par Shuru Karein</span>
          </a>
        </div>

        {/* Mobile Hamburger Toggle */}
        <button
          className="md:hidden text-[#BAC8C1] hover:text-[#F0FDF4] p-1.5 focus:outline-none min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer"
          onClick={() => setMobileOpen((open) => !open)}
          aria-expanded={mobileOpen}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </nav>

      {/* Mobile Menu Drawer */}
      {mobileOpen && (
        <div className="md:hidden mt-2 bg-[#0B1A13]/95 border border-[#224430] rounded-2xl p-4 space-y-3 shadow-2xl backdrop-blur-2xl animate-in fade-in slide-in-from-top-2 duration-200">
          <a
            href="#features"
            className="block text-sm text-[#BAC8C1] hover:text-[#B6F23C] py-2 px-3 rounded-lg hover:bg-white/5 transition-colors"
            onClick={() => setMobileOpen(false)}
          >
            Features
          </a>
          <a
            href="#workflow"
            className="block text-sm text-[#BAC8C1] hover:text-[#B6F23C] py-2 px-3 rounded-lg hover:bg-white/5 transition-colors"
            onClick={() => setMobileOpen(false)}
          >
            Kaise Kaam Karta Hai?
          </a>
          <Link
            href="/dashboard"
            className="block text-sm text-[#BAC8C1] hover:text-[#B6F23C] py-2 px-3 rounded-lg hover:bg-white/5 transition-colors"
            onClick={() => setMobileOpen(false)}
          >
            Dashboard
          </Link>
          <div className="pt-2 border-t border-[#224430]/70 flex flex-col gap-2">
            <Link
              href="/login"
              className="text-center text-sm font-semibold text-[#BAC8C1] hover:text-[#F0FDF4] py-2"
              onClick={() => setMobileOpen(false)}
            >
              Login
            </Link>
            <a
              href="https://wa.me/14155238886?text=Hi+Munim+AI!"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 w-full bg-[#B6F23C] text-[#07110D] font-bold text-sm py-2.5 rounded-full shadow-[0_0_16px_rgba(182,242,60,0.35)]"
              onClick={() => setMobileOpen(false)}
            >
              <MessageCircle className="w-4 h-4" />
              <span>WhatsApp par Shuru Karein</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      )}
    </header>
  );
}

