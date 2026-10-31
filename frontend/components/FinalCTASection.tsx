"use client";

import Link from "next/link";
import SplineChart from "./SplineChart";

const DASHBOARD_CHART_DATA = [
  { label: "W1", value: 42000 },
  { label: "W2", value: 55000 },
  { label: "W3", value: 68000 },
  { label: "W4", value: 76000 },
  { label: "Oct 30", value: 86420 },
];

export default function FinalCTASection() {
  return (
    <section className="relative py-24 bg-[#071410] overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-[10%] left-[-10%] w-[550px] h-[550px] bg-[#4efa72]/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[10%] right-[-5%] w-[600px] h-[600px] bg-[#B5FF4D]/12 rounded-full blur-[160px] pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-6 space-y-16">
        {/* Main Grid: Left Column Copy & CTAs + Right Column Tilted Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column (Span 5) */}
          <div className="lg:col-span-5 flex flex-col items-start space-y-6">
            {/* Outlined Pill */}
            <div className="inline-flex items-center gap-2 bg-[#0B1B16] border border-[#4efa72]/30 rounded-full px-4 py-1.5 shadow-[0_0_15px_rgba(78,250,114,0.12)]">
              <span className="text-[#B5FF4D] text-xs">✨</span>
              <span className="text-[#BAC8C1] text-xs font-semibold tracking-wide">
                Business Ko Digital Banayein
              </span>
            </div>

            {/* Large Heading */}
            <div className="space-y-1">
              <h2 className="text-4xl sm:text-5xl font-black text-[#F5F7F4] tracking-tight leading-[1.15]">
                Aaj Hi{" "}
                <span className="relative inline-block text-[#B5FF4D]">
                  Munim AI
                  <svg
                    className="absolute -bottom-2 left-0 w-full h-3 overflow-visible pointer-events-none"
                    viewBox="0 0 180 12"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M2 9.5C45 2.5 135 2.5 178 8"
                      stroke="#B5FF4D"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </span>
                <br />
                Shuru Karein
              </h2>
            </div>

            {/* Description */}
            <p className="text-[#BAC8C1] text-base sm:text-lg leading-relaxed max-w-md pt-1">
              Apni dukaan ka kaam WhatsApp se hi manage karein — simple, tez aur bina kisi technical jhanjhat ke.
            </p>

            {/* Two CTA Buttons */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              {/* Primary WhatsApp Button */}
              <a
                href="https://wa.me/14155238886?text=Hi+Munim+AI!"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2.5 bg-[#B5FF4D] hover:bg-[#a3f52f] text-[#071410] font-bold text-sm sm:text-base px-7 py-3.5 rounded-full transition-all duration-200 shadow-[0_0_25px_rgba(181,255,77,0.45)] hover:shadow-[0_0_35px_rgba(181,255,77,0.65)] hover:scale-[1.02] active:scale-[0.98]"
              >
                <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.888 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                </svg>
                <span>WhatsApp par Shuru Karein</span>
              </a>

              {/* Secondary Demo Button */}
              <Link
                href="/dashboard"
                className="flex items-center gap-2 bg-[#10211A]/80 hover:bg-[#162e24] text-[#F5F7F4] border border-[#BAC8C1]/30 hover:border-[#B5FF4D]/60 font-semibold text-sm sm:text-base px-6 py-3.5 rounded-full transition-all duration-200"
              >
                <span>Demo Dekhein</span>
                <span className="text-[#B5FF4D] text-xs">▶</span>
              </Link>
            </div>

            {/* Three Trust Pills */}
            <div className="flex flex-wrap items-center gap-3 pt-4">
              <div className="flex items-center gap-1.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-3.5 py-1.5 text-xs text-[#BAC8C1]">
                <span className="text-[#B5FF4D]">⚡</span>
                <span>5 Minute Setup</span>
              </div>
              <div className="flex items-center gap-1.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-3.5 py-1.5 text-xs text-[#BAC8C1]">
                <span className="text-[#B5FF4D]">💳</span>
                <span>No Technical Skills</span>
              </div>
              <div className="flex items-center gap-1.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-3.5 py-1.5 text-xs text-[#BAC8C1]">
                <span className="text-[#B5FF4D]">🛡️</span>
                <span>Secure & Reliable</span>
              </div>
            </div>
          </div>

          {/* Right Column (Span 7) — Glowing Tilted Dashboard Mockup */}
          <div className="lg:col-span-7 relative flex items-center justify-center py-6">
            {/* Ambient Background Glow */}
            <div className="absolute w-[480px] h-[340px] bg-[#B5FF4D]/15 rounded-full blur-[100px] pointer-events-none" />

            {/* Tilted Dashboard Container */}
            <div
              className="relative w-full max-w-[620px] bg-[#0c1813] border-2 border-[#4efa72]/40 rounded-2xl sm:rounded-3xl shadow-[0_25px_60px_rgba(0,0,0,0.8),0_0_35px_rgba(78,250,114,0.22)] overflow-hidden transition-transform duration-500 hover:rotate-0"
              style={{
                transform: "perspective(1200px) rotateY(-5deg) rotateX(3deg) rotateZ(1deg)",
              }}
            >
              {/* Dashboard Layout: Left Sidebar + Right Main Panel */}
              <div className="flex h-full min-h-[360px] sm:min-h-[400px]">
                {/* Left Mini Sidebar */}
                <div className="w-16 sm:w-20 bg-[#08120e] border-r border-[#1a3327] py-4 flex flex-col items-center justify-between flex-shrink-0">
                  <div className="space-y-4 flex flex-col items-center w-full">
                    <div className="w-8 h-8 rounded-xl bg-[#B5FF4D] text-[#071410] font-black flex items-center justify-center text-xs shadow-[0_0_10px_rgba(181,255,77,0.5)]">
                      M
                    </div>
                    <div className="w-full space-y-2 px-2">
                      <div className="w-full py-1.5 rounded-lg bg-[#B5FF4D]/15 text-[#B5FF4D] text-[10px] font-bold text-center flex flex-col items-center">
                        <span>🏠</span>
                        <span className="text-[9px] mt-0.5">Home</span>
                      </div>
                      <div className="w-full py-1 rounded-lg text-[#BAC8C1]/60 text-[9px] text-center flex flex-col items-center">
                        <span>📦</span>
                        <span>Orders</span>
                      </div>
                      <div className="w-full py-1 rounded-lg text-[#BAC8C1]/60 text-[9px] text-center flex flex-col items-center">
                        <span>👥</span>
                        <span>Cust</span>
                      </div>
                      <div className="w-full py-1 rounded-lg text-[#BAC8C1]/60 text-[9px] text-center flex flex-col items-center">
                        <span>🏪</span>
                        <span>Stock</span>
                      </div>
                      <div className="w-full py-1 rounded-lg text-[#BAC8C1]/60 text-[9px] text-center flex flex-col items-center">
                        <span>₹</span>
                        <span>Pay</span>
                      </div>
                      <div className="w-full py-1 rounded-lg text-[#BAC8C1]/60 text-[9px] text-center flex flex-col items-center">
                        <span>📊</span>
                        <span>Reports</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Main Dashboard Area */}
                <div className="flex-1 p-4 sm:p-5 flex flex-col justify-between space-y-3.5 bg-[#0a1711]">
                  {/* Top Bar Greeting */}
                  <div className="flex items-center justify-between pb-2 border-b border-[#162e22]">
                    <div>
                      <h4 className="text-white font-bold text-xs sm:text-sm flex items-center gap-1">
                        Namaste Neha! 👋
                      </h4>
                      <p className="text-[#BAC8C1] text-[10px]">Aaj ka business yahan dekhiye.</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[#BAC8C1] text-xs">🔔</span>
                      <div className="w-6 h-6 rounded-full bg-[#B5FF4D] text-[#071410] font-black text-[10px] flex items-center justify-center">
                        N
                      </div>
                    </div>
                  </div>

                  {/* 4 KPI Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div className="bg-[#10211A] border border-[#4efa72]/20 rounded-xl p-2.5">
                      <p className="text-[#BAC8C1] text-[9px]">Aaj ki Bikri</p>
                      <p className="text-white font-bold text-xs sm:text-sm mt-0.5">₹8,450</p>
                      <span className="text-[#B5FF4D] text-[8px] font-semibold">↑ +18%</span>
                    </div>
                    <div className="bg-[#10211A] border border-[#4efa72]/20 rounded-xl p-2.5">
                      <p className="text-[#BAC8C1] text-[9px]">Orders</p>
                      <p className="text-white font-bold text-xs sm:text-sm mt-0.5">12</p>
                      <span className="text-[#B5FF4D] text-[8px] font-semibold">↑ +12%</span>
                    </div>
                    <div className="bg-[#10211A] border border-[#4efa72]/20 rounded-xl p-2.5">
                      <p className="text-[#BAC8C1] text-[9px]">Customers</p>
                      <p className="text-white font-bold text-xs sm:text-sm mt-0.5">28</p>
                      <span className="text-[#BAC8C1] text-[8px]">Active</span>
                    </div>
                    <div className="bg-[#10211A] border border-[#4efa72]/20 rounded-xl p-2.5">
                      <p className="text-[#BAC8C1] text-[9px]">Baki Paise</p>
                      <p className="text-white font-bold text-xs sm:text-sm mt-0.5">₹4,200</p>
                      <span className="text-[#f87171] text-[8px] font-semibold">↑ +6%</span>
                    </div>
                  </div>

                  {/* Sales Chart Container with SplineChart */}
                  <div className="bg-[#10211A] border border-[#4efa72]/20 rounded-xl p-3 flex-1 flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1">
                        <span className="text-[#B5FF4D] text-xs">📈</span>
                        <span className="text-white font-bold text-[11px]">Is Mahine ki Bikri</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-white font-black text-xs">₹86,420</span>
                        <span className="text-[#B5FF4D] text-[9px] font-bold bg-[#B5FF4D]/15 px-1.5 py-0.5 rounded-full">
                          ↑ +18%
                        </span>
                      </div>
                    </div>
                    <div className="w-full overflow-hidden">
                      <SplineChart data={DASHBOARD_CHART_DATA} height={120} accentColor="#B5FF4D" showTooltip={true} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Thin Horizontal Divider */}
        <div className="border-t border-[#4efa72]/15" />

        {/* Bottom Trust & Category Row */}
        <div className="flex flex-col lg:flex-row items-center justify-between gap-8 pt-2">
          {/* Left: Laurel Wreath + "Bharat ke 10,000+ vyapariyon ka bharosa" */}
          <div className="flex items-center gap-3 flex-shrink-0">
            {/* Laurel Left */}
            <svg className="w-8 h-12 stroke-[#B5FF4D] fill-none opacity-80" viewBox="0 0 32 48" strokeWidth="1.5">
              <path d="M26 4C20 12 10 24 10 38c0 4 2 6 4 6M18 10c-3 4-8 10-8 16M14 18c-2 3-5 8-5 13M12 28c-1 2-3 6-3 9" strokeLinecap="round" />
            </svg>

            <div className="text-center sm:text-left">
              <p className="text-[#BAC8C1] text-xs leading-none">Bharat ke</p>
              <p className="text-2xl sm:text-3xl font-black text-[#B5FF4D] tracking-tight leading-tight">
                10,000+
              </p>
              <p className="text-[#BAC8C1] text-xs leading-none">vyapariyon ka bharosa</p>
            </div>

            {/* Laurel Right */}
            <svg className="w-8 h-12 stroke-[#B5FF4D] fill-none opacity-80 scale-x-[-1]" viewBox="0 0 32 48" strokeWidth="1.5">
              <path d="M26 4C20 12 10 24 10 38c0 4 2 6 4 6M18 10c-3 4-8 10-8 16M14 18c-2 3-5 8-5 13M12 28c-1 2-3 6-3 9" strokeLinecap="round" />
            </svg>
          </div>

          {/* Right: Four Business Categories with Outline Icons */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full lg:w-auto">
            {/* Category 1: Kapde ki dukaan */}
            <div className="flex items-center gap-2.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-4 py-2 text-xs text-[#F5F7F4] shadow-sm hover:border-[#B5FF4D]/40 transition-colors">
              <span className="text-[#B5FF4D] text-sm">👗</span>
              <span className="font-semibold whitespace-nowrap">Kapde ki dukaan</span>
            </div>

            {/* Category 2: General Store */}
            <div className="flex items-center gap-2.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-4 py-2 text-xs text-[#F5F7F4] shadow-sm hover:border-[#B5FF4D]/40 transition-colors">
              <span className="text-[#B5FF4D] text-sm">🏪</span>
              <span className="font-semibold whitespace-nowrap">General Store</span>
            </div>

            {/* Category 3: Cosmetics & Gifts */}
            <div className="flex items-center gap-2.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-4 py-2 text-xs text-[#F5F7F4] shadow-sm hover:border-[#B5FF4D]/40 transition-colors">
              <span className="text-[#B5FF4D] text-sm">💄</span>
              <span className="font-semibold whitespace-nowrap">Cosmetics & Gifts</span>
            </div>

            {/* Category 4: Wholesale */}
            <div className="flex items-center gap-2.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-4 py-2 text-xs text-[#F5F7F4] shadow-sm hover:border-[#B5FF4D]/40 transition-colors">
              <span className="text-[#B5FF4D] text-sm">📦</span>
              <span className="font-semibold whitespace-nowrap">Wholesale</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

