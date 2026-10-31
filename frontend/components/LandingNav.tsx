"use client";

import Link from "next/link";
import { useState } from "react";

export default function LandingNav() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="fixed top-4 left-1/2 -translate-x-1/2 w-[92%] max-w-6xl z-50">
      <nav className="bg-[#071410]/90 backdrop-blur-xl border border-[#4efa72]/25 rounded-full px-5 sm:px-7 py-2.5 shadow-[0_10px_35px_rgba(0,0,0,0.6),0_0_20px_rgba(78,250,114,0.1)] flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-xl bg-[#B5FF4D] flex items-center justify-center text-[#071410] font-black text-sm shadow-[0_0_12px_rgba(181,255,77,0.5)] group-hover:scale-105 transition-transform">
            M
          </div>
          <span className="font-bold text-[#F5F7F4] text-base sm:text-lg tracking-tight">
            Munim AI
          </span>
        </Link>

        {/* Desktop Links */}
        <div className="hidden md:flex items-center gap-8 text-sm font-medium">
          <a
            href="#features"
            className="text-[#BAC8C1] hover:text-[#B5FF4D] transition-colors"
          >
            Features
          </a>
          <a
            href="#workflow"
            className="text-[#BAC8C1] hover:text-[#B5FF4D] transition-colors"
          >
            Kaise Kaam Karta Hai?
          </a>
          <Link
            href="/dashboard"
            className="text-[#BAC8C1] hover:text-[#B5FF4D] transition-colors"
          >
            Dashboard
          </Link>
        </div>

        {/* Right CTA */}
        <div className="hidden md:flex items-center gap-4">
          <Link
            href="/dashboard"
            className="text-xs sm:text-sm font-semibold text-[#BAC8C1] hover:text-[#F5F7F4] transition-colors"
          >
            Login
          </Link>
          <a
            href="https://wa.me/14155238886?text=Hi+Munim+AI!"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 bg-[#B5FF4D] hover:bg-[#a3f52f] text-[#071410] font-black text-xs sm:text-sm px-5 py-2 rounded-full transition-all shadow-[0_0_15px_rgba(181,255,77,0.4)] hover:shadow-[0_0_25px_rgba(181,255,77,0.6)] hover:scale-105 active:scale-95"
          >
            <span>Start Free</span>
          </a>
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden text-[#BAC8C1] p-1.5 focus:outline-none"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle Navigation"
        >
          {mobileOpen ? "✕" : "☰"}
        </button>
      </nav>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden mt-2 bg-[#0a1812]/98 border border-[#4efa72]/20 rounded-2xl p-4 space-y-3 shadow-2xl backdrop-blur-2xl">
          <a
            href="#features"
            className="block text-sm text-[#BAC8C1] hover:text-[#B5FF4D] py-1"
            onClick={() => setMobileOpen(false)}
          >
            Features
          </a>
          <a
            href="#workflow"
            className="block text-sm text-[#BAC8C1] hover:text-[#B5FF4D] py-1"
            onClick={() => setMobileOpen(false)}
          >
            Kaise Kaam Karta Hai?
          </a>
          <Link
            href="/dashboard"
            className="block text-sm text-[#BAC8C1] hover:text-[#B5FF4D] py-1"
            onClick={() => setMobileOpen(false)}
          >
            Dashboard
          </Link>
          <a
            href="https://wa.me/14155238886?text=Hi+Munim+AI!"
            className="block w-full text-center bg-[#B5FF4D] text-[#071410] font-bold text-sm py-2.5 rounded-full mt-2"
          >
            📱 Start Free on WhatsApp
          </a>
        </div>
      )}
    </header>
  );
}
