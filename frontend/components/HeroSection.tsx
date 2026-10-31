"use client";

import Link from "next/link";

export default function HeroSection() {
  return (
    <section className="relative min-h-[92vh] flex items-center justify-center overflow-hidden bg-[#071410] pt-32 pb-24 lg:pt-36 lg:pb-28">
      {/* Background ambient lighting and glowing emerald wave curves */}
      <div className="absolute top-[-10%] left-[-15%] w-[600px] h-[600px] bg-[#22c55e]/12 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute top-[25%] right-[-10%] w-[650px] h-[650px] bg-[#B5FF4D]/15 rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[25%] w-[500px] h-[500px] bg-[#4efa72]/10 rounded-full blur-[140px] pointer-events-none" />

      {/* Decorative ambient subtle wavy line in background */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none opacity-20"
        viewBox="0 0 1600 900"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M-100 850C300 800 600 500 1100 650C1400 750 1600 500 1700 400"
          stroke="#B5FF4D"
          strokeWidth="2"
          strokeDasharray="8 8"
        />
        <path
          d="M-50 700C350 650 650 350 1150 500C1450 600 1650 350 1750 250"
          stroke="#4efa72"
          strokeWidth="1.5"
        />
      </svg>

      <div className="relative z-10 max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 w-full grid grid-cols-1 lg:grid-cols-12 gap-16 lg:gap-12 items-center">
        {/* Left Column (Span 7) */}
        <div className="lg:col-span-7 flex flex-col items-start space-y-7">
          {/* Top Outlined Pill */}
          <div className="inline-flex items-center gap-2.5 bg-[#0B1B16]/90 border border-[#4efa72]/35 rounded-full px-4 py-1.5 shadow-[0_0_15px_rgba(78,250,114,0.15)]">
            <span className="text-[#B5FF4D] text-xs">✨</span>
            <span className="text-[#BAC8C1] text-xs font-semibold tracking-wide">
              AI-Powered Business Assistant
            </span>
          </div>

          {/* Main Headline */}
          <div className="space-y-2">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-[68px] font-black text-[#F5F7F4] tracking-tight leading-[1.08]">
              Aapke Dukaan Ka
            </h1>
            <div className="relative inline-block">
              <span className="text-4xl sm:text-5xl lg:text-6xl xl:text-[68px] font-black text-[#B5FF4D] tracking-tight leading-[1.08]">
                Digital Munim
              </span>
              {/* Hand-drawn curved neon green underline directly below */}
              <svg
                className="absolute -bottom-3 left-0 w-full h-4 overflow-visible pointer-events-none"
                viewBox="0 0 280 14"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M4 11C80 3 200 3 276 10"
                  stroke="#B5FF4D"
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              </svg>
            </div>
          </div>

          {/* Description */}
          <p className="text-[#BAC8C1] text-base sm:text-lg lg:text-xl max-w-xl leading-relaxed pt-2">
            WhatsApp par hi orders lo, payments track karo,
            <br className="hidden sm:block" />
            customer ki baatein yaad rakho — sab automatic,
            <br className="hidden sm:block" />
            simple aur aapki apni bhasha mein.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-wrap items-center gap-4 pt-2">
            {/* Primary Start on WhatsApp */}
            <a
              href="https://wa.me/14155238886?text=Hi+Munim+AI!"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 bg-[#B5FF4D] hover:bg-[#a3f52f] text-[#071410] font-black text-sm sm:text-base px-8 py-4 rounded-full transition-all duration-200 shadow-[0_0_30px_rgba(181,255,77,0.5)] hover:shadow-[0_0_45px_rgba(181,255,77,0.7)] hover:scale-105 active:scale-95"
            >
              <svg className="w-5 h-5 fill-current" viewBox="0 0 24 24">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.888 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
              </svg>
              <span>Start on WhatsApp</span>
            </a>

            {/* Secondary See Demo */}
            <Link
              href="#demo"
              className="flex items-center gap-2.5 bg-[#10211A]/90 hover:bg-[#162e24] text-[#F5F7F4] border border-[#BAC8C1]/30 hover:border-[#B5FF4D]/60 font-bold text-sm sm:text-base px-8 py-4 rounded-full transition-all duration-200"
            >
              <span>See Demo</span>
              <span className="text-[#B5FF4D] text-xs">▶</span>
            </Link>
          </div>

          {/* Benefit Pills */}
          <div className="flex flex-wrap items-center gap-3.5 pt-4">
            <div className="flex items-center gap-2 bg-[#0B1B16] border border-[#4efa72]/25 rounded-full px-4 py-2 text-xs text-[#BAC8C1] shadow-sm">
              <span className="text-[#B5FF4D]">⚡</span>
              <span className="font-semibold">Simple</span>
            </div>
            <div className="flex items-center gap-2 bg-[#0B1B16] border border-[#4efa72]/25 rounded-full px-4 py-2 text-xs text-[#BAC8C1] shadow-sm">
              <span className="text-[#B5FF4D]">₹</span>
              <span className="font-semibold">Saves Time</span>
            </div>
            <div className="flex items-center gap-2 bg-[#0B1B16] border border-[#4efa72]/25 rounded-full px-4 py-2 text-xs text-[#BAC8C1] shadow-sm">
              <span className="text-[#B5FF4D]">📈</span>
              <span className="font-semibold">Grows Business</span>
            </div>
          </div>
        </div>

        {/* Right Column (Span 5) — Tilted Phone Mockup & Connected Feature Badges */}
        <div className="lg:col-span-5 relative flex items-center justify-center lg:justify-end py-8">
          {/* Ambient Glow behind phone */}
          <div className="absolute w-[360px] h-[520px] bg-[#B5FF4D]/18 rounded-full blur-[100px] pointer-events-none" />

          {/* 3D Tilted Phone Frame */}
          <div
            className="relative w-[300px] sm:w-[330px] bg-[#0c1813] rounded-[44px] p-3 border-2 border-[#4efa72]/45 shadow-[0_25px_65px_rgba(0,0,0,0.85),0_0_40px_rgba(78,250,114,0.3)] transition-transform duration-500 hover:rotate-0"
            style={{
              transform: "perspective(1100px) rotateY(-8deg) rotateX(4deg) rotateZ(-3deg)",
            }}
          >
            {/* Phone Outer Rim Highlight */}
            <div className="absolute inset-0 rounded-[42px] border border-[#B5FF4D]/35 pointer-events-none" />

            {/* Phone Screen Container */}
            <div className="bg-[#071710] rounded-[34px] overflow-hidden flex flex-col text-xs border border-[#163325]">
              {/* Phone Status Notch */}
              <div className="bg-[#0b1b14] px-5 pt-3 pb-1 flex items-center justify-between text-[10px] text-[#BAC8C1]/70">
                <span className="font-semibold">9:41</span>
                <div className="w-20 h-4 bg-[#071410] rounded-full mx-auto" />
                <div className="flex items-center gap-1.5 text-[9px]">
                  <span>5G</span>
                  <span>100%</span>
                </div>
              </div>

              {/* WhatsApp Header */}
              <div className="bg-[#0e271c] px-3.5 py-3 flex items-center justify-between border-b border-[#1b3d2d]">
                <div className="flex items-center gap-2.5">
                  <span className="text-white text-xs font-bold">←</span>
                  <div className="w-8 h-8 rounded-full bg-[#B5FF4D] flex items-center justify-center text-[#071410] font-black text-sm shadow-[0_0_8px_rgba(181,255,77,0.5)]">
                    🏪
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-xs leading-tight">Munim AI</h3>
                    <p className="text-[#B5FF4D] text-[10px] leading-tight">Business Assistant</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-[#BAC8C1] text-xs">
                  <span>📞</span>
                  <span>⋮</span>
                </div>
              </div>

              {/* Chat Conversation Body */}
              <div className="p-4 space-y-4 bg-[#081711] flex flex-col justify-end min-h-[360px]">
                {/* Customer Incoming Message */}
                <div className="self-end max-w-[88%] bg-[#1b4e35] text-[#F5F7F4] rounded-2xl rounded-tr-xs px-4 py-3 shadow-md border border-[#2b6d4b]/40">
                  <p className="text-xs leading-relaxed">
                    5 blue kurti aur 3 black kurti bhej do
                  </p>
                  <p className="text-[9px] text-[#B5FF4D]/80 text-right mt-1 font-medium">
                    10:24 AM ✓✓
                  </p>
                </div>

                {/* Munim AI Response Message */}
                <div className="self-start max-w-[92%] bg-[#0f281d] text-[#F5F7F4] rounded-2xl rounded-tl-xs px-4 py-3.5 shadow-md border border-[#4efa72]/35">
                  <p className="text-xs font-bold text-[#B5FF4D] mb-2 flex items-center gap-1.5">
                    <span>✅</span> Order likh liya!
                  </p>
                  <div className="space-y-1 text-xs text-[#BAC8C1] pl-1">
                    <p>• Blue Kurti × 5</p>
                    <p>• Black Kurti × 3</p>
                  </div>
                  <div className="mt-3 pt-2 border-t border-[#1b3d2d] flex items-center justify-between">
                    <span className="text-xs font-black text-white">Kul: ₹4,900</span>
                    <span className="text-[9px] text-[#BAC8C1]/60">10:24 AM</span>
                  </div>
                  <p className="text-xs text-[#B5FF4D] mt-1.5 font-semibold">Bheju?</p>
                </div>

                {/* Bottom Quick Reply Chips */}
                <div className="flex items-center gap-2.5 pt-2">
                  <button className="flex-1 bg-[#B5FF4D] hover:bg-[#a3f52f] text-[#071410] font-black text-xs py-2 px-3 rounded-full text-center transition-all shadow-[0_0_12px_rgba(181,255,77,0.35)]">
                    Haan, bhejo
                  </button>
                  <button className="flex-1 bg-[#10211A] text-[#BAC8C1] border border-[#4efa72]/30 text-xs py-2 px-3 rounded-full text-center font-medium">
                    Badalna hai
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 3 Floating Feature Badges with Glowing Connectors */}
          <div className="hidden sm:flex flex-col gap-6 absolute -right-4 lg:-right-10 z-20">
            {/* Badge 1: Orders Automatic */}
            <div className="flex items-center gap-3.5 bg-[#10211A]/95 border border-[#B5FF4D]/40 rounded-2xl p-3 pr-5 shadow-[0_0_22px_rgba(78,250,114,0.22)] backdrop-blur-md hover:scale-105 transition-transform">
              <div className="w-10 h-10 rounded-xl bg-[#B5FF4D]/15 text-[#B5FF4D] flex items-center justify-center text-lg border border-[#B5FF4D]/35">
                🛒
              </div>
              <div>
                <h4 className="text-white font-bold text-sm">Orders</h4>
                <p className="text-[#BAC8C1] text-xs">Automatic</p>
              </div>
            </div>

            {/* Badge 2: Payments Track */}
            <div className="flex items-center gap-3.5 bg-[#10211A]/95 border border-[#B5FF4D]/40 rounded-2xl p-3 pr-5 shadow-[0_0_22px_rgba(78,250,114,0.22)] backdrop-blur-md translate-x-3 hover:scale-105 transition-transform">
              <div className="w-10 h-10 rounded-xl bg-[#B5FF4D]/15 text-[#B5FF4D] flex items-center justify-center text-lg border border-[#B5FF4D]/35">
                ₹
              </div>
              <div>
                <h4 className="text-white font-bold text-sm">Payments</h4>
                <p className="text-[#BAC8C1] text-xs">Track</p>
              </div>
            </div>

            {/* Badge 3: Customers Yaad Rakho */}
            <div className="flex items-center gap-3.5 bg-[#10211A]/95 border border-[#B5FF4D]/40 rounded-2xl p-3 pr-5 shadow-[0_0_22px_rgba(78,250,114,0.22)] backdrop-blur-md hover:scale-105 transition-transform">
              <div className="w-10 h-10 rounded-xl bg-[#B5FF4D]/15 text-[#B5FF4D] flex items-center justify-center text-lg border border-[#B5FF4D]/35">
                👥
              </div>
              <div>
                <h4 className="text-white font-bold text-sm">Customers</h4>
                <p className="text-[#BAC8C1] text-xs">Yaad Rakho</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
