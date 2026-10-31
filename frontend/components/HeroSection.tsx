"use client";

import Link from "next/link";

export default function HeroSection() {
  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden bg-[#071410] pt-24 pb-16">
      {/* Background radial and ambient green glows */}
      <div className="absolute top-[-10%] left-[-10%] w-[550px] h-[550px] bg-[#4efa72]/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-[40%] right-[-5%] w-[650px] h-[650px] bg-[#4efa72]/12 rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[30%] w-[450px] h-[450px] bg-[#22c55e]/10 rounded-full blur-[130px] pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-6 w-full grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
        {/* Left Column (Span 7) */}
        <div className="lg:col-span-7 flex flex-col items-start space-y-6">
          {/* Top Outlined Pill */}
          <div className="inline-flex items-center gap-2 bg-[#0B1B16]/80 border border-[#4efa72]/30 rounded-full px-4 py-1.5 shadow-[0_0_15px_rgba(78,250,114,0.12)]">
            <span className="text-[#B5FF4D] text-xs">✨</span>
            <span className="text-[#BAC8C1] text-xs font-semibold tracking-wide">
              AI-Powered Business Assistant
            </span>
          </div>

          {/* Main Headline */}
          <div className="space-y-1">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-[#F5F7F4] tracking-tight leading-[1.15]">
              Aapke Dukaan Ka
            </h1>
            <div className="relative inline-block">
              <span className="text-4xl sm:text-5xl lg:text-6xl font-black text-[#B5FF4D] tracking-tight leading-[1.15]">
                Digital Munim
              </span>
              {/* Curved Green Underline */}
              <svg
                className="absolute -bottom-2 left-0 w-full h-3 overflow-visible pointer-events-none"
                viewBox="0 0 260 12"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M2 9.5C65 2.5 195 2.5 258 8"
                  stroke="#B5FF4D"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                />
              </svg>
            </div>
          </div>

          {/* Description */}
          <p className="text-[#BAC8C1] text-base sm:text-lg max-w-xl leading-relaxed pt-2">
            WhatsApp par hi orders lo, payments track karo,
            <br className="hidden sm:block" />
            customer ki baatein yaad rakho — sab automatic,
            <br className="hidden sm:block" />
            simple aur aapki apni bhasha mein.
          </p>

          {/* Two Buttons */}
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
              <span>Start on WhatsApp</span>
            </a>

            {/* Secondary See Demo Button */}
            <Link
              href="#demo"
              className="flex items-center gap-2 bg-[#10211A]/80 hover:bg-[#162e24] text-[#F5F7F4] border border-[#BAC8C1]/30 hover:border-[#B5FF4D]/60 font-semibold text-sm sm:text-base px-6 py-3.5 rounded-full transition-all duration-200"
            >
              <span>See Demo</span>
              <span className="text-[#B5FF4D] text-xs">▶</span>
            </Link>
          </div>

          {/* Benefit Pills */}
          <div className="flex flex-wrap items-center gap-3 pt-4">
            <div className="flex items-center gap-1.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-3.5 py-1.5 text-xs text-[#BAC8C1]">
              <span className="text-[#B5FF4D]">⚡</span>
              <span>Simple</span>
            </div>
            <div className="flex items-center gap-1.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-3.5 py-1.5 text-xs text-[#BAC8C1]">
              <span className="text-[#B5FF4D]">₹</span>
              <span>Saves Time</span>
            </div>
            <div className="flex items-center gap-1.5 bg-[#0B1B16] border border-[#4efa72]/20 rounded-full px-3.5 py-1.5 text-xs text-[#BAC8C1]">
              <span className="text-[#B5FF4D]">📈</span>
              <span>Grows Business</span>
            </div>
          </div>
        </div>

        {/* Right Column (Span 5) — Tilted Phone Mockup & Floating Badges */}
        <div className="lg:col-span-5 relative flex items-center justify-center lg:justify-end py-6">
          {/* Ambient Glow behind phone */}
          <div className="absolute w-[320px] h-[480px] bg-[#B5FF4D]/15 rounded-full blur-[90px] pointer-events-none" />

          {/* 3D Tilted Phone Frame */}
          <div
            className="relative w-[300px] sm:w-[320px] bg-[#091510] rounded-[42px] p-3.5 border-2 border-[#4efa72]/40 shadow-[0_20px_60px_rgba(0,0,0,0.8),0_0_30px_rgba(78,250,114,0.25)] transition-transform duration-500 hover:rotate-0"
            style={{
              transform: "perspective(1200px) rotateY(-8deg) rotateX(4deg) rotateZ(-2deg)",
            }}
          >
            {/* Phone Outer Rim Highlight */}
            <div className="absolute inset-0 rounded-[40px] border border-[#B5FF4D]/30 pointer-events-none" />

            {/* Phone Screen */}
            <div className="bg-[#0b1b14] rounded-[32px] overflow-hidden flex flex-col text-xs border border-[#163325]">
              {/* Phone Status Notch */}
              <div className="bg-[#0b1b14] px-5 pt-2.5 pb-1 flex items-center justify-between text-[10px] text-[#BAC8C1]/70">
                <span>9:41</span>
                <div className="w-20 h-3.5 bg-[#071410] rounded-full mx-auto" />
                <div className="flex items-center gap-1">
                  <span>📶</span>
                  <span>🔋</span>
                </div>
              </div>

              {/* WhatsApp Header */}
              <div className="bg-[#10291e] px-3 py-2.5 flex items-center justify-between border-b border-[#1b3d2d]">
                <div className="flex items-center gap-2">
                  <span className="text-white text-xs">←</span>
                  <div className="w-7 h-7 rounded-full bg-[#B5FF4D] flex items-center justify-center text-[#071410] font-black text-xs shadow-[0_0_8px_rgba(181,255,77,0.5)]">
                    🏪
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-[11px] leading-tight">Munim AI</h3>
                    <p className="text-[#B5FF4D] text-[9px] leading-tight">Business Assistant</p>
                  </div>
                </div>
                <div className="flex items-center gap-2.5 text-[#BAC8C1] text-xs">
                  <span>📞</span>
                  <span>⋮</span>
                </div>
              </div>

              {/* Chat Conversation Body */}
              <div className="p-3.5 space-y-3.5 min-h-[310px] bg-[#071710] flex flex-col justify-end">
                {/* Customer Incoming Message */}
                <div className="self-end max-w-[85%] bg-[#1d5036] text-[#F5F7F4] rounded-2xl rounded-tr-xs px-3.5 py-2.5 shadow-sm border border-[#2b6d4b]/40">
                  <p className="text-[11px] leading-snug">5 blue kurti aur 3 black kurti bhej do</p>
                  <p className="text-[8px] text-[#B5FF4D]/80 text-right mt-1">10:24 AM ✓✓</p>
                </div>

                {/* Munim AI Response Message */}
                <div className="self-start max-w-[90%] bg-[#0e241a] text-[#F5F7F4] rounded-2xl rounded-tl-xs px-3.5 py-2.5 shadow-sm border border-[#4efa72]/30">
                  <p className="text-[11px] font-semibold text-[#B5FF4D] mb-1.5 flex items-center gap-1">
                    <span>✅</span> Order likh liya!
                  </p>
                  <div className="space-y-0.5 text-[10px] text-[#BAC8C1]">
                    <p>• Blue Kurti × 5</p>
                    <p>• Black Kurti × 3</p>
                  </div>
                  <div className="mt-2 pt-1.5 border-t border-[#1b3d2d] flex items-center justify-between">
                    <span className="text-[10px] font-bold text-white">Kul: ₹4,900</span>
                    <span className="text-[8px] text-[#BAC8C1]/60">10:24 AM</span>
                  </div>
                  <p className="text-[10px] text-[#B5FF4D] mt-1 font-medium">Bheju?</p>
                </div>

                {/* Bottom Quick Reply Chips */}
                <div className="flex items-center gap-2 pt-1">
                  <button className="flex-1 bg-[#B5FF4D] hover:bg-[#a3f52f] text-[#071410] font-bold text-[10px] py-1.5 px-3 rounded-full text-center transition-all shadow-[0_0_10px_rgba(181,255,77,0.3)]">
                    Haan, bhejo
                  </button>
                  <button className="flex-1 bg-[#10211A] text-[#BAC8C1] border border-[#4efa72]/20 text-[10px] py-1.5 px-3 rounded-full text-center">
                    Badalna hai
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 3 Floating Feature Badges to the right of the phone */}
          <div className="hidden sm:flex flex-col gap-5 absolute -right-6 lg:-right-12 z-20">
            {/* Badge 1: Orders Automatic */}
            <div className="flex items-center gap-3 bg-[#10211A]/95 border border-[#B5FF4D]/35 rounded-2xl p-2.5 pr-4 shadow-[0_0_20px_rgba(78,250,114,0.18)] backdrop-blur-md">
              <div className="w-9 h-9 rounded-xl bg-[#B5FF4D]/15 text-[#B5FF4D] flex items-center justify-center text-base border border-[#B5FF4D]/30">
                🛒
              </div>
              <div>
                <h4 className="text-white font-bold text-xs">Orders</h4>
                <p className="text-[#BAC8C1] text-[10px]">Automatic</p>
              </div>
            </div>

            {/* Badge 2: Payments Track */}
            <div className="flex items-center gap-3 bg-[#10211A]/95 border border-[#B5FF4D]/35 rounded-2xl p-2.5 pr-4 shadow-[0_0_20px_rgba(78,250,114,0.18)] backdrop-blur-md translate-x-2">
              <div className="w-9 h-9 rounded-xl bg-[#B5FF4D]/15 text-[#B5FF4D] flex items-center justify-center text-base border border-[#B5FF4D]/30">
                ₹
              </div>
              <div>
                <h4 className="text-white font-bold text-xs">Payments</h4>
                <p className="text-[#BAC8C1] text-[10px]">Track</p>
              </div>
            </div>

            {/* Badge 3: Customers Yaad Rakho */}
            <div className="flex items-center gap-3 bg-[#10211A]/95 border border-[#B5FF4D]/35 rounded-2xl p-2.5 pr-4 shadow-[0_0_20px_rgba(78,250,114,0.18)] backdrop-blur-md">
              <div className="w-9 h-9 rounded-xl bg-[#B5FF4D]/15 text-[#B5FF4D] flex items-center justify-center text-base border border-[#B5FF4D]/30">
                👥
              </div>
              <div>
                <h4 className="text-white font-bold text-xs">Customers</h4>
                <p className="text-[#BAC8C1] text-[10px]">Yaad Rakho</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
