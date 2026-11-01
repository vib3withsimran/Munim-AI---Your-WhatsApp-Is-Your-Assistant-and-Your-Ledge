"use client";

import React from "react";
import { Zap, Users, ShieldCheck, Check } from "lucide-react";

interface AuthIllustrationProps {
  type: "login" | "signup";
}

export function AuthIllustration({ type }: AuthIllustrationProps) {
  return (
    <div className="flex flex-col items-center justify-center w-full max-w-[340px] mx-auto select-none">
      {/* 3D Scene Wrapper with relative positioning */}
      <div className="relative w-full aspect-[1/0.88] flex items-center justify-center mb-6">
        {/* Floating Top Badge */}
        {type === "login" ? (
          /* Floating 3D Chart Badge */
          <div className="absolute -top-3 left-6 z-20 animate-bounce duration-1000 [animation-duration:3s]">
            {/* Sparkles */}
            <div className="absolute -top-2 -left-2 text-[#B6F23C] text-sm animate-pulse">✨</div>
            <div className="absolute -bottom-1 -right-2 text-[#34D399] text-xs">✦</div>

            <div className="relative bg-[#0E261A]/95 border-2 border-[#B6F23C]/60 rounded-2xl p-3 shadow-[0_0_25px_rgba(182,242,60,0.45)] backdrop-blur-md flex items-end gap-1.5 h-14 w-16 justify-center">
              <div className="w-2.5 bg-gradient-to-t from-[#15803D] to-[#86EFAC] rounded-t-sm h-4 shadow-[0_0_8px_rgba(134,239,172,0.6)]" />
              <div className="w-2.5 bg-gradient-to-t from-[#16A34A] to-[#B6F23C] rounded-t-sm h-7 shadow-[0_0_12px_rgba(182,242,60,0.8)]" />
              <div className="w-2.5 bg-gradient-to-t from-[#22C55E] to-[#BEF264] rounded-t-sm h-10 shadow-[0_0_16px_rgba(190,242,100,1)]" />
            </div>
          </div>
        ) : (
          /* Floating 3D Clipboard Badge */
          <div className="absolute -top-3 left-6 z-20 animate-bounce duration-1000 [animation-duration:3s]">
            <div className="absolute -top-2 -left-2 text-[#B6F23C] text-sm animate-pulse">✨</div>
            <div className="relative bg-[#0E261A]/95 border-2 border-[#B6F23C]/60 rounded-2xl p-3 shadow-[0_0_25px_rgba(182,242,60,0.45)] backdrop-blur-md w-16 h-16 flex flex-col justify-center items-center">
              {/* Clipboard Clip */}
              <div className="absolute -top-2 w-6 h-3 bg-[#34D399] rounded-t-md border border-[#B6F23C]/80" />
              {/* Checklist lines */}
              <div className="space-y-1.5 w-full mt-1">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-[#B6F23C] flex items-center justify-center text-[7px] text-[#07110D] font-black">✓</div>
                  <div className="h-1 bg-[#86EFAC]/70 rounded w-full" />
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-[#B6F23C] flex items-center justify-center text-[7px] text-[#07110D] font-black">✓</div>
                  <div className="h-1 bg-[#86EFAC]/70 rounded w-3/4" />
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-[#B6F23C] flex items-center justify-center text-[7px] text-[#07110D] font-black">✓</div>
                  <div className="h-1 bg-[#86EFAC]/70 rounded w-4/5" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 3D Isometric Dukaan / Storefront SVG */}
        <div className="relative w-64 h-56 flex items-center justify-center">
          {/* Floor Radial Glow */}
          <div className="absolute bottom-4 w-48 h-12 bg-[#B6F23C]/20 rounded-full blur-xl pointer-events-none" />
          <div className="absolute bottom-2 w-44 h-8 bg-black/60 rounded-full blur-md pointer-events-none" />

          <svg
            viewBox="0 0 260 220"
            className="w-full h-full drop-shadow-[0_20px_35px_rgba(0,0,0,0.8)] overflow-visible"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            {/* Ground shadow polygon */}
            <path
              d="M 20 185 L 120 150 L 245 185 L 140 215 Z"
              fill="rgba(0,0,0,0.4)"
              filter="blur(4px)"
            />

            {/* Building Left (Side) Wall (in isometric shadow) */}
            <path
              d="M 30 110 L 85 90 L 85 180 L 30 170 Z"
              fill="url(#sideWallGrad)"
              stroke="#132B20"
              strokeWidth="1.5"
            />

            {/* Building Front Wall */}
            <path
              d="M 85 90 L 220 115 L 220 190 L 85 180 Z"
              fill="url(#frontWallGrad)"
              stroke="#1C3D2E"
              strokeWidth="1.5"
            />

            {/* Warm Interior Windows & Door */}
            {/* Window Left */}
            <rect
              x="100"
              y="125"
              width="45"
              height="35"
              rx="4"
              fill="url(#warmGlowGrad)"
              stroke="#F59E0B"
              strokeWidth="1.5"
              className="drop-shadow-[0_0_12px_rgba(245,158,11,0.6)]"
            />
            {/* Window panes */}
            <line x1="122.5" y1="125" x2="122.5" y2="160" stroke="#78350F" strokeWidth="1.2" />
            <line x1="100" y1="142.5" x2="145" y2="142.5" stroke="#78350F" strokeWidth="1.2" />

            {/* Door (Open / Glowing) */}
            <path
              d="M 160 130 L 205 136 L 205 188 L 160 183 Z"
              fill="url(#warmGlowGrad)"
              stroke="#F59E0B"
              strokeWidth="1.5"
              className="drop-shadow-[0_0_16px_rgba(251,191,36,0.7)]"
            />
            {/* Door frame & handle */}
            <line x1="182" y1="133" x2="182" y2="185" stroke="#78350F" strokeWidth="1.2" />
            <circle cx="178" cy="160" r="2" fill="#78350F" />

            {/* Overhanging Striped Awning / Canopy Roof */}
            {/* Awning 3D Top Slope */}
            <path
              d="M 18 105 L 80 75 L 230 102 L 180 128 Z"
              fill="url(#roofTopGrad)"
              stroke="#2E6948"
              strokeWidth="1.5"
            />

            {/* Awning Front Face with Alternating Lime & Forest Stripes */}
            {/* Stripe 1 (Side turn) */}
            <path d="M 18 105 L 45 116 L 40 126 L 15 115 Z" fill="#0E2D1D" />
            <path d="M 45 116 L 70 122 L 65 132 L 40 126 Z" fill="#B6F23C" />
            {/* Stripe 2 (Front facing) */}
            <path d="M 70 122 L 105 125 L 100 137 L 65 132 Z" fill="#154B2F" />
            <path d="M 105 125 L 140 127 L 136 139 L 100 137 Z" fill="#B6F23C" />
            <path d="M 140 127 L 175 128 L 172 140 L 136 139 Z" fill="#154B2F" />
            <path d="M 175 128 L 210 129 L 208 141 L 172 140 Z" fill="#B6F23C" />
            <path d="M 210 129 L 235 127 L 232 138 L 208 141 Z" fill="#154B2F" />

            {/* Scalloped edge trim highlights */}
            <path
              d="M 15 115 Q 27.5 123 40 126 Q 52.5 130 65 132 Q 82.5 136 100 137 Q 118 138 136 139 Q 154 140 172 140 Q 190 141 208 141 Q 220 140 232 138"
              stroke="#B6F23C"
              strokeWidth="2"
              fill="none"
              className="drop-shadow-[0_0_8px_rgba(182,242,60,0.8)]"
            />

            {/* Potted Plant on Left */}
            <ellipse cx="28" cy="180" rx="9" ry="4" fill="#0A1810" />
            {/* Clay / Ceramic Pot */}
            <path d="M 21 172 L 35 172 L 32 186 L 24 186 Z" fill="#3A4D3E" stroke="#1F2F24" strokeWidth="1" />
            {/* Foliage / Leaves */}
            <circle cx="28" cy="165" r="9" fill="#166534" />
            <circle cx="24" cy="160" r="7" fill="#22C55E" />
            <circle cx="32" cy="162" r="7" fill="#86EFAC" className="opacity-90" />
            <circle cx="28" cy="155" r="5" fill="#B6F23C" />

            {/* Chalkboard Menu Stand on Right */}
            {/* Stand legs */}
            <line x1="225" y1="170" x2="220" y2="198" stroke="#3A2D1F" strokeWidth="2.5" strokeLinecap="round" />
            <line x1="242" y1="172" x2="246" y2="198" stroke="#3A2D1F" strokeWidth="2.5" strokeLinecap="round" />
            {/* Board Frame */}
            <rect
              x="221"
              y="160"
              width="23"
              height="30"
              rx="2"
              fill="#111B15"
              stroke="#523E28"
              strokeWidth="2"
              transform="rotate(6 232 175)"
            />
            {/* Chalk lines */}
            <line x1="225" y1="168" x2="238" y2="169" stroke="#86EFAC" strokeWidth="1.2" strokeLinecap="round" />
            <line x1="225" y1="173" x2="236" y2="174" stroke="#86EFAC" strokeWidth="1.2" strokeLinecap="round" />
            <line x1="225" y1="178" x2="234" y2="179" stroke="#86EFAC" strokeWidth="1.2" strokeLinecap="round" />

            {/* Gradient Definitions */}
            <defs>
              <linearGradient id="sideWallGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#122A1E" />
                <stop offset="100%" stopColor="#08150E" />
              </linearGradient>
              <linearGradient id="frontWallGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#1E3E2E" />
                <stop offset="100%" stopColor="#10251A" />
              </linearGradient>
              <linearGradient id="roofTopGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#25543B" />
                <stop offset="100%" stopColor="#0E281B" />
              </linearGradient>
              <radialGradient id="warmGlowGrad" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#FEF08A" />
                <stop offset="45%" stopColor="#F59E0B" />
                <stop offset="100%" stopColor="#B45309" />
              </radialGradient>
            </defs>
          </svg>
        </div>
      </div>

      {/* Feature Section Below Illustration */}
      {type === "login" ? (
        /* Login Checklist Pill Container */
        <div className="w-full bg-[#0A1A12]/90 border border-[#1C3B29] rounded-2xl p-4 shadow-lg space-y-3">
          {[
            "Manage Orders",
            "Track Payments",
            "Keep Customer Records",
            "Grow Your Business",
          ].map((item, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full bg-[#183925] border border-[#B6F23C]/40 text-[#B6F23C] flex items-center justify-center shrink-0 shadow-[0_0_8px_rgba(182,242,60,0.3)]">
                <Check className="w-3 h-3 stroke-[3]" />
              </div>
              <span className="text-xs sm:text-sm font-semibold text-[#F0FDF4] tracking-tight">
                {item}
              </span>
            </div>
          ))}
        </div>
      ) : (
        /* Signup 3 Badges Vertical Stack */
        <div className="w-full space-y-2.5">
          <div className="flex items-center gap-3 bg-[#0A1A12]/80 border border-[#1C3B29] rounded-2xl p-3 shadow-md">
            <div className="w-9 h-9 rounded-xl bg-[#B6F23C]/15 border border-[#B6F23C]/30 text-[#B6F23C] flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(182,242,60,0.25)]">
              <Zap className="w-4 h-4 fill-[#B6F23C]" />
            </div>
            <div>
              <p className="text-xs font-bold text-[#F0FDF4]">Quick Setup</p>
              <p className="text-[11px] text-[#BAC8C1]">in 2 minutes</p>
            </div>
          </div>

          <div className="flex items-center gap-3 bg-[#0A1A12]/80 border border-[#1C3B29] rounded-2xl p-3 shadow-md">
            <div className="w-9 h-9 rounded-xl bg-[#34D399]/15 border border-[#34D399]/30 text-[#34D399] flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(52,211,153,0.25)]">
              <Users className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-bold text-[#F0FDF4]">No Technical</p>
              <p className="text-[11px] text-[#BAC8C1]">Knowledge Needed</p>
            </div>
          </div>

          <div className="flex items-center gap-3 bg-[#0A1A12]/80 border border-[#1C3B29] rounded-2xl p-3 shadow-md">
            <div className="w-9 h-9 rounded-xl bg-[#22C55E]/15 border border-[#22C55E]/30 text-[#22C55E] flex items-center justify-center shrink-0 shadow-[0_0_12px_rgba(34,197,94,0.25)]">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-bold text-[#F0FDF4]">Safe & Secure</p>
              <p className="text-[11px] text-[#BAC8C1]">Your data is protected</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

