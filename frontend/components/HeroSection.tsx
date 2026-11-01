import Link from "next/link";
import {
  MessageCircle,
  Play,
  Zap,
  TrendingUp,
  ShoppingCart,
  CreditCard,
  Users,
  Shirt,
  ShoppingBasket,
  Sparkles,
  Package,
} from "lucide-react";

export default function HeroSection() {
  return (
    <section className="relative min-h-[92vh] flex flex-col justify-center overflow-hidden bg-[#07110D] pt-28 pb-16 lg:pt-36 lg:pb-24">
      {/* Background ambient lighting and glowing emerald wave curves */}
      <div className="absolute top-[-10%] left-[-10%] w-[550px] h-[550px] bg-[#10B981]/12 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-[20%] right-[-10%] w-[600px] h-[600px] bg-[#B6F23C]/14 rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[20%] w-[500px] h-[500px] bg-[#10B981]/10 rounded-full blur-[130px] pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-8 lg:px-12 w-full space-y-16 lg:space-y-20">
        {/* Main 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          {/* Left Column (Span 6) */}
          <div className="lg:col-span-6 flex flex-col items-start space-y-6 sm:space-y-7">
            {/* Top Outlined Pill: AI-Powered Business Assistant */}
            <div className="inline-flex items-center gap-2 bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/50 rounded-full px-4 py-1.5 shadow-[0_0_15px_rgba(182,242,60,0.1)] transition-colors">
              <span className="text-[#B6F23C] text-xs">✨</span>
              <span className="text-[#BAC8C1] text-xs font-semibold tracking-wide">
                AI-Powered Business Assistant
              </span>
            </div>

            {/* Headline: Aapke Dukaan Ka Digital Munim */}
            <div className="space-y-1 sm:space-y-2">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-[#F0FDF4] tracking-tight leading-[1.1]">
                Aapke Dukaan Ka
                <br />
                <span className="relative inline-block text-[#B6F23C] drop-shadow-[0_0_25px_rgba(182,242,60,0.35)]">
                  Digital Munim
                  {/* Hand-drawn curved neon green underline directly below */}
                  <svg
                    className="absolute -bottom-3 left-0 w-full h-3.5 sm:h-4 overflow-visible pointer-events-none text-[#B6F23C]"
                    viewBox="0 0 240 12"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    aria-hidden="true"
                  >
                    <path
                      d="M3 8.5C65 2.5 160 2.5 237 8"
                      stroke="currentColor"
                      strokeWidth="3.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </span>
              </h1>
            </div>

            {/* Description */}
            <p className="text-[#BAC8C1] text-base sm:text-lg lg:text-xl max-w-xl leading-relaxed pt-1">
              WhatsApp par hi orders lo, payments track karo, customer ki baatein yaad rakho — sab automatic, simple aur aapki apni bhasha mein.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center gap-3.5 sm:gap-4 pt-1 w-full sm:w-auto">
              {/* Primary Start on WhatsApp */}
              <a
                href="https://wa.me/14155238886?text=Hi+Munim+AI!"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto flex items-center justify-center gap-2.5 bg-[#B6F23C] hover:bg-[#c6f663] text-[#07110D] font-black text-sm sm:text-base px-8 py-3.5 rounded-full transition-all duration-200 shadow-[0_0_25px_rgba(182,242,60,0.4)] hover:shadow-[0_0_35px_rgba(182,242,60,0.6)] hover:scale-105 active:scale-95 min-h-[48px]"
              >
                <MessageCircle className="w-5 h-5 fill-current" />
                <span>Start on WhatsApp</span>
              </a>

              {/* Secondary See Demo */}
              <Link
                href="/dashboard"
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-[#0B1A13]/90 hover:bg-[#142921] text-[#F0FDF4] border border-[#BAC8C1]/30 hover:border-[#B6F23C]/60 font-bold text-sm sm:text-base px-7 py-3.5 rounded-full transition-all duration-200 min-h-[48px]"
              >
                <span>See Demo</span>
                <Play className="w-4 h-4 text-[#B6F23C] fill-current" />
              </Link>
            </div>

            {/* Benefit Pills: Simple, Saves Time, Grows Business */}
            <div className="flex flex-wrap items-center gap-2.5 sm:gap-3 pt-2">
              <div className="flex items-center gap-2 bg-[#0B1A13] border border-[#224430] rounded-full px-4 py-1.5 text-xs text-[#BAC8C1] shadow-sm">
                <Zap className="w-3.5 h-3.5 text-[#B6F23C]" />
                <span className="font-semibold">Simple</span>
              </div>
              <div className="flex items-center gap-2 bg-[#0B1A13] border border-[#224430] rounded-full px-4 py-1.5 text-xs text-[#BAC8C1] shadow-sm">
                <span className="text-[#B6F23C] font-bold">₹</span>
                <span className="font-semibold">Saves Time</span>
              </div>
              <div className="flex items-center gap-2 bg-[#0B1A13] border border-[#224430] rounded-full px-4 py-1.5 text-xs text-[#BAC8C1] shadow-sm">
                <TrendingUp className="w-3.5 h-3.5 text-[#B6F23C]" />
                <span className="font-semibold">Grows Business</span>
              </div>
            </div>
          </div>

          {/* Right Column (Span 6) — 3D Tilted Smartphone Mockup + 3 Connected Badges */}
          <div className="lg:col-span-6 relative flex items-center justify-center lg:justify-end py-6">
            {/* Ambient Background Glow */}
            <div className="absolute w-[400px] h-[520px] bg-[#B6F23C]/18 rounded-full blur-[110px] pointer-events-none" />

            {/* Smartphone Chassis */}
            <div
              className="relative w-[295px] sm:w-[325px] bg-[#0c1813] rounded-[44px] p-3 border-2 border-[#B6F23C]/45 shadow-[0_25px_65px_rgba(0,0,0,0.85),0_0_40px_rgba(182,242,60,0.25)] transition-transform duration-500 hover:[transform:none] lg:[transform:perspective(1100px)_rotateY(-7deg)_rotateX(4deg)] z-10"
            >
              <div className="bg-[#071710] rounded-[34px] overflow-hidden flex flex-col text-xs border border-[#163325]">
                {/* Phone Notch */}
                <div className="bg-[#0b1b14] px-5 pt-3 pb-1 flex items-center justify-between text-[10px] text-[#BAC8C1]/70">
                  <span className="font-semibold">9:41</span>
                  <div className="w-20 h-4 bg-[#071410] rounded-full mx-auto" />
                  <div className="flex items-center gap-1.5 text-[9px]">
                    <span>5G</span>
                    <span>100%</span>
                  </div>
                </div>

                {/* WhatsApp Chat Header */}
                <div className="bg-[#0e271c] px-3.5 py-3 flex items-center justify-between border-b border-[#1b3d2d]">
                  <div className="flex items-center gap-2.5">
                    <span className="text-white text-xs font-bold">←</span>
                    <div className="w-8 h-8 rounded-full bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black text-sm shadow-[0_0_8px_rgba(182,242,60,0.5)]">
                      🏪
                    </div>
                    <div>
                      <h3 className="text-white font-bold text-xs leading-tight">Munim AI</h3>
                      <p className="text-[#B6F23C] text-[10px] leading-tight">Business Assistant</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-[#BAC8C1] text-xs">
                    <span>📞</span>
                    <span>⋮</span>
                  </div>
                </div>

                {/* Chat Conversation */}
                <div className="p-4 space-y-4 bg-[#081711] flex flex-col justify-end min-h-[360px]">
                  {/* Customer Message */}
                  <div className="self-end max-w-[88%] bg-[#1b4e35] text-[#F5F7F4] rounded-2xl rounded-tr-xs px-4 py-3 shadow-md border border-[#2b6d4b]/40">
                    <p className="text-xs leading-relaxed">
                      5 blue kurti aur 3 black kurti bhej do
                    </p>
                    <p className="text-[9px] text-[#B6F23C]/80 text-right mt-1 font-medium">
                      10:24 AM ✓✓
                    </p>
                  </div>

                  {/* Munim AI Response Message */}
                  <div className="self-start max-w-[92%] bg-[#0f281d] text-[#F5F7F4] rounded-2xl rounded-tl-xs px-4 py-3.5 shadow-md border border-[#B6F23C]/35">
                    <p className="text-xs font-bold text-[#B6F23C] mb-2 flex items-center gap-1.5">
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
                    <p className="text-xs text-[#B6F23C] mt-1.5 font-semibold">Bheju?</p>
                  </div>

                  {/* Quick Reply Chips */}
                  <div className="flex items-center gap-2.5 pt-2">
                    <button className="flex-1 bg-[#B6F23C] hover:bg-[#c6f663] text-[#07110D] font-black text-xs py-2 px-3 rounded-full text-center transition-all shadow-[0_0_12px_rgba(182,242,60,0.35)]">
                      Haan, bhejo
                    </button>
                    <button className="flex-1 bg-[#10211A] text-[#BAC8C1] border border-[#224430] text-xs py-2 px-3 rounded-full text-center font-medium">
                      Badalna hai
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* 3 Floating Badges connected to phone on desktop */}
            <div className="hidden sm:flex flex-col gap-6 absolute -right-4 lg:-right-8 z-20">
              {/* Badge 1: Orders Automatic */}
              <div className="flex items-center gap-3.5 bg-[#0B1A13]/95 border border-[#B6F23C]/40 rounded-2xl p-3 pr-5 shadow-[0_0_22px_rgba(182,242,60,0.22)] backdrop-blur-md hover:scale-105 transition-transform">
                <div className="w-10 h-10 rounded-xl bg-[#B6F23C]/15 text-[#B6F23C] flex items-center justify-center text-lg border border-[#B6F23C]/35">
                  <ShoppingCart className="w-5 h-5 text-[#B6F23C]" />
                </div>
                <div>
                  <h4 className="text-white font-bold text-sm">Orders</h4>
                  <p className="text-[#BAC8C1] text-xs">Automatic</p>
                </div>
              </div>

              {/* Badge 2: Payments Track */}
              <div className="flex items-center gap-3.5 bg-[#0B1A13]/95 border border-[#B6F23C]/40 rounded-2xl p-3 pr-5 shadow-[0_0_22px_rgba(182,242,60,0.22)] backdrop-blur-md translate-x-3 hover:scale-105 transition-transform">
                <div className="w-10 h-10 rounded-xl bg-[#B6F23C]/15 text-[#B6F23C] flex items-center justify-center text-lg border border-[#B6F23C]/35">
                  <CreditCard className="w-5 h-5 text-[#B6F23C]" />
                </div>
                <div>
                  <h4 className="text-white font-bold text-sm">Payments</h4>
                  <p className="text-[#BAC8C1] text-xs">Track</p>
                </div>
              </div>

              {/* Badge 3: Customers Yaad Rakho */}
              <div className="flex items-center gap-3.5 bg-[#0B1A13]/95 border border-[#B6F23C]/40 rounded-2xl p-3 pr-5 shadow-[0_0_22px_rgba(182,242,60,0.22)] backdrop-blur-md hover:scale-105 transition-transform">
                <div className="w-10 h-10 rounded-xl bg-[#B6F23C]/15 text-[#B6F23C] flex items-center justify-center text-lg border border-[#B6F23C]/35">
                  <Users className="w-5 h-5 text-[#B6F23C]" />
                </div>
                <div>
                  <h4 className="text-white font-bold text-sm">Customers</h4>
                  <p className="text-[#BAC8C1] text-xs">Yaad Rakho</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Business-Type Strip */}
        <div className="pt-8 border-t border-[#224430]/60">
          <div className="w-full grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
            <div className="flex items-center justify-center sm:justify-start gap-3 bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/50 rounded-2xl px-4 py-3 text-xs sm:text-sm text-[#F0FDF4] shadow-sm transition-all duration-200">
              <Shirt className="w-5 h-5 text-[#B6F23C] flex-shrink-0" />
              <span className="font-bold whitespace-nowrap">Kapde ki dukaan</span>
            </div>

            <div className="flex items-center justify-center sm:justify-start gap-3 bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/50 rounded-2xl px-4 py-3 text-xs sm:text-sm text-[#F0FDF4] shadow-sm transition-all duration-200">
              <ShoppingBasket className="w-5 h-5 text-[#B6F23C] flex-shrink-0" />
              <span className="font-bold whitespace-nowrap">General Store</span>
            </div>

            <div className="flex items-center justify-center sm:justify-start gap-3 bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/50 rounded-2xl px-4 py-3 text-xs sm:text-sm text-[#F0FDF4] shadow-sm transition-all duration-200">
              <Sparkles className="w-5 h-5 text-[#B6F23C] flex-shrink-0" />
              <span className="font-bold whitespace-nowrap">Cosmetics & Gifts</span>
            </div>

            <div className="flex items-center justify-center sm:justify-start gap-3 bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/50 rounded-2xl px-4 py-3 text-xs sm:text-sm text-[#F0FDF4] shadow-sm transition-all duration-200">
              <Package className="w-5 h-5 text-[#B6F23C] flex-shrink-0" />
              <span className="font-bold whitespace-nowrap">Wholesale</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

