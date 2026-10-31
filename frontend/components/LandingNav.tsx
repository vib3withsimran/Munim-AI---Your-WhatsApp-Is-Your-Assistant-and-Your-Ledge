"use client";

import Link from "next/link";
import { useState, useEffect } from "react";

export default function LandingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler);
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#071410]/95 backdrop-blur-md border-b border-[#4efa72]/15 shadow-[0_4px_20px_rgba(0,0,0,0.5)]"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-[#B5FF4D] flex items-center justify-center shadow-[0_0_16px_rgba(181,255,77,0.45)]">
            <span className="text-[#071410] font-black text-base">M</span>
          </div>
          <span className="font-bold text-[#F5F7F4] text-lg tracking-tight">Munim AI</span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm text-[#BAC8C1] hover:text-[#B5FF4D] transition-colors">
            Features
          </a>
          <a href="#features" className="text-sm text-[#BAC8C1] hover:text-[#B5FF4D] transition-colors">
            Kaise Kaam Karta Hai?
          </a>
          <Link href="/dashboard" className="text-sm text-[#BAC8C1] hover:text-[#B5FF4D] transition-colors">
            Dashboard
          </Link>
        </div>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/dashboard"
            className="text-sm text-[#BAC8C1] hover:text-[#F5F7F4] transition-colors px-4 py-2"
          >
            Login
          </Link>
          <a
            href="https://wa.me/14155238886?text=Hi+Munim+AI!"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 bg-[#B5FF4D] hover:bg-[#a3f52f] text-[#071410] font-bold text-sm px-5 py-2 rounded-full transition-all shadow-[0_0_16px_rgba(181,255,77,0.4)] hover:shadow-[0_0_24px_rgba(181,255,77,0.6)]"
          >
            <span>📱 Start Free</span>
          </a>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-[#BAC8C1] p-2"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? "✕" : "☰"}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-[#071410]/98 border-b border-[#4efa72]/15 px-6 py-4 space-y-3">
          {["Features", "Kaise Kaam Karta Hai?", "Dashboard"].map((l) => (
            <Link
              key={l}
              href={l === "Dashboard" ? "/dashboard" : `#${l === "Features" ? "features" : "features"}`}
              className="block text-sm text-[#BAC8C1] hover:text-[#B5FF4D] py-1"
              onClick={() => setMobileOpen(false)}
            >
              {l}
            </Link>
          ))}
          <a
            href="https://wa.me/14155238886?text=Hi+Munim+AI!"
            className="block w-full text-center bg-[#B5FF4D] text-[#071410] font-bold text-sm px-4 py-2.5 rounded-full mt-2"
          >
            📱 Start Free on WhatsApp
          </a>
        </div>
      )}
    </nav>
  );
}

