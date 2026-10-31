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
          ? "bg-[#0d1410]/95 backdrop-blur-md border-b border-[rgba(78,250,114,0.12)] shadow-[0_4px_20px_rgba(0,0,0,0.4)]"
          : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-[#4efa72] flex items-center justify-center shadow-[0_0_16px_rgba(78,250,114,0.5)]">
            <span className="text-[#0d1410] font-black text-base">M</span>
          </div>
          <span className="font-bold text-[#f0fdf4] text-lg tracking-tight">Munim AI</span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-8">
          {["Features", "How it Works", "Testimonials", "Pricing"].map((l) => (
            <a
              key={l}
              href={`#${l.toLowerCase().replace(/ /g, "-")}`}
              className="text-sm text-[#9db8a0] hover:text-[#4efa72] transition-colors"
            >
              {l}
            </a>
          ))}
        </div>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-3">
          <Link
            href="/dashboard"
            className="text-sm text-[#9db8a0] hover:text-[#f0fdf4] transition-colors px-4 py-2"
          >
            Login
          </Link>
          <a
            href="https://wa.me/14155238886?text=Hi+Munim+AI!"
            target="_blank"
            className="flex items-center gap-2 bg-[#4efa72] hover:bg-[#3acc5c] text-[#0d1410] font-semibold text-sm px-4 py-2 rounded-lg transition-all shadow-[0_0_16px_rgba(78,250,114,0.4)] hover:shadow-[0_0_24px_rgba(78,250,114,0.6)]"
          >
            📱 Start Free
          </a>
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden text-[#9db8a0] p-2"
          onClick={() => setMobileOpen(!mobileOpen)}
        >
          {mobileOpen ? "✕" : "☰"}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-[#0d1410]/98 border-b border-[rgba(78,250,114,0.12)] px-6 py-4 space-y-3">
          {["Features", "How it Works", "Testimonials", "Pricing"].map((l) => (
            <a
              key={l}
              href={`#${l.toLowerCase().replace(/ /g, "-")}`}
              className="block text-sm text-[#9db8a0] hover:text-[#4efa72] py-1"
              onClick={() => setMobileOpen(false)}
            >
              {l}
            </a>
          ))}
          <a
            href="https://wa.me/14155238886?text=Hi+Munim+AI!"
            className="block w-full text-center bg-[#4efa72] text-[#0d1410] font-semibold text-sm px-4 py-2.5 rounded-lg mt-2"
          >
            📱 Start Free on WhatsApp
          </a>
        </div>
      )}
    </nav>
  );
}

