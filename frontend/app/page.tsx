import Link from "next/link";
import LandingNav from "@/components/LandingNav";
import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import FinalCTASection from "@/components/FinalCTASection";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#07110D] text-[#F0FDF4] selection:bg-[#B6F23C] selection:text-[#07110D]">
      <LandingNav />
      <main>
        <HeroSection />
        <FeaturesSection />
        <FinalCTASection />
      </main>

      {/* Footer */}
      <footer className="border-t border-[#224430]/70 bg-[#050E0B] py-10 sm:py-12">
        <div className="max-w-7xl mx-auto px-5 sm:px-8 lg:px-12 flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Brand info */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black text-xs shadow-[0_0_12px_rgba(182,242,60,0.4)]">
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 0l2.5 8.5L23 11l-7.5 4.5L17.5 24 12 18.5 6.5 24l2-8.5L1 11l8.5-2.5L12 0z" />
              </svg>
            </div>
            <div>
              <span className="font-extrabold text-[#F0FDF4] text-sm tracking-tight">
                Munim AI
              </span>
              <p className="text-[#BAC8C1] text-xs">
                Aapke Dukaan Ka Digital Munim
              </p>
            </div>
          </div>

          {/* Quick links */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-medium text-[#BAC8C1]">
            <a href="#features" className="hover:text-[#B6F23C] transition-colors">
              Features
            </a>
            <a href="#workflow" className="hover:text-[#B6F23C] transition-colors">
              Kaise Kaam Karta Hai?
            </a>
            <Link href="/dashboard" className="hover:text-[#B6F23C] transition-colors">
              Dashboard
            </Link>
            <Link href="/login" className="hover:text-[#B6F23C] transition-colors">
              Login
            </Link>
          </div>

          {/* Copyright */}
          <p className="text-[#BAC8C1]/60 text-xs text-center md:text-right">
            © 2026 Munim AI. Made with ❤️ for Indian Vyaparis.
          </p>
        </div>
      </footer>
    </div>
  );
}
