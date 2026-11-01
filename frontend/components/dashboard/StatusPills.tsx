"use client";

import { MessageCircle, ChevronDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { MOCK_SELLER } from "@/lib/mocks/dashboard";

export default function StatusPills() {
  const { profile } = useAuth();

  const phoneDisplay = profile?.phone
    ? profile.phone.startsWith("+")
      ? profile.phone
      : `+${profile.phone}`
    : MOCK_SELLER.phone;

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Pill 1: Munim AI Active */}
      <div className="flex items-center gap-2.5 bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/40 rounded-2xl px-4 py-2 transition-all shadow-sm">
        <div className="relative flex items-center justify-center">
          <div className="w-2.5 h-2.5 rounded-full bg-[#B6F23C] shadow-[0_0_8px_rgba(182,242,60,0.8)]" />
          <div className="w-2.5 h-2.5 rounded-full bg-[#B6F23C] animate-ping absolute opacity-75" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-bold text-[#F0FDF4] leading-tight">
            Munim AI Active
          </p>
          <p className="text-[10px] text-[#BAC8C1] leading-tight">
            Auto-replies ON · Memory ON
          </p>
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-[#BAC8C1]/60 ml-1" />
      </div>

      {/* Pill 2: WhatsApp Connected */}
      <div className="flex items-center gap-2.5 bg-[#0B1A13]/90 border border-[#224430] hover:border-[#25D366]/40 rounded-2xl px-4 py-2 transition-all shadow-sm">
        <div className="w-6 h-6 rounded-full bg-[#25D366]/20 border border-[#25D366]/40 flex items-center justify-center text-[#25D366] flex-shrink-0">
          <MessageCircle className="w-3.5 h-3.5" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-bold text-[#F0FDF4] leading-tight">
            WhatsApp Connected
          </p>
          <p className="text-[10px] text-[#BAC8C1] leading-tight">
            {phoneDisplay}
          </p>
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-[#BAC8C1]/60 ml-1" />
      </div>
    </div>
  );
}

