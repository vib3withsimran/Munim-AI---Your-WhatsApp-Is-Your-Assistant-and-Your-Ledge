import Link from "next/link";
import { MessageCircle, ArrowRight, Play, CheckCircle2, Zap, ShieldCheck } from "lucide-react";

export default function FinalCTASection() {
  return (
    <section className="relative py-20 sm:py-28 bg-[#07110D] overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-[20%] left-[-10%] w-[500px] h-[500px] bg-[#10B981]/12 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[10%] right-[-10%] w-[550px] h-[550px] bg-[#B6F23C]/14 rounded-full blur-[160px] pointer-events-none" />

      <div className="relative z-10 max-w-5xl mx-auto px-5 sm:px-8">
        <div className="relative bg-[#0B1A13]/95 border-2 border-[#B6F23C]/35 rounded-[32px] p-8 sm:p-14 text-center shadow-[0_25px_65px_rgba(0,0,0,0.85),0_0_40px_rgba(182,242,60,0.2)] overflow-hidden">
          {/* Subtle decorative radial glow inside */}
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 bg-[#B6F23C]/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 max-w-2xl mx-auto space-y-6">
            {/* Top Pill */}
            <div className="inline-flex items-center gap-2 bg-[#10211A] border border-[#224430] rounded-full px-4 py-1.5 shadow-sm">
              <Zap className="w-3.5 h-3.5 text-[#B6F23C]" />
              <span className="text-[#BAC8C1] text-xs font-semibold tracking-wide">
                Bas 5 Minute Setup
              </span>
            </div>

            {/* Heading */}
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#F0FDF4] tracking-tight leading-[1.15]">
              Apni Dukaan Ko Aaj Hi{" "}
              <span className="text-[#B6F23C] drop-shadow-[0_0_20px_rgba(182,242,60,0.3)]">
                Smart
              </span>{" "}
              Banayein
            </h2>

            {/* Subtitle */}
            <p className="text-[#BAC8C1] text-sm sm:text-base lg:text-lg leading-relaxed">
              Bina kisi credit card ya technical knowledge ke — WhatsApp par message bhejiye aur Munim AI turant aapke orders aur baki hisaab manage karna shuru karega.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
              <a
                href="https://wa.me/14155238886?text=Hi+Munim+AI!"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 bg-[#B6F23C] hover:bg-[#c6f663] text-[#07110D] font-extrabold text-sm sm:text-base px-8 py-4 rounded-full transition-all duration-200 shadow-[0_0_25px_rgba(182,242,60,0.4)] hover:shadow-[0_0_35px_rgba(182,242,60,0.6)] hover:scale-105 active:scale-95"
              >
                <MessageCircle className="w-5 h-5" />
                <span>Start on WhatsApp</span>
                <ArrowRight className="w-4 h-4 ml-0.5" />
              </a>

              <Link
                href="/dashboard"
                className="flex items-center gap-2 bg-[#10211A] hover:bg-[#162e24] text-[#F0FDF4] border border-[#BAC8C1]/30 hover:border-[#B6F23C]/50 font-bold text-sm sm:text-base px-7 py-4 rounded-full transition-all duration-200"
              >
                <Play className="w-4 h-4 text-[#B6F23C] fill-current" />
                <span>See Demo</span>
              </Link>
            </div>

            {/* Reassurance Features */}
            <div className="pt-4 flex flex-wrap items-center justify-center gap-6 text-xs text-[#BAC8C1]">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#B6F23C]" />
                <span>Koi App Download Nahi</span>
              </div>
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#B6F23C]" />
                <span>100% Surakshit Data</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#B6F23C]" />
                <span>Hinglish & Hindi Support</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

