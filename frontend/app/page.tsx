import LandingNav from "@/components/LandingNav";
import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import ExtraSections from "@/components/ExtraSections";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#0d1410]">
      <LandingNav />
      <HeroSection />
      <FeaturesSection />
      <ExtraSections />

      {/* Footer */}
      <footer className="border-t border-[rgba(78,250,114,0.08)] py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#4efa72] flex items-center justify-center text-[#0d1410] font-black text-xs">M</div>
            <span className="text-[#9db8a0] text-sm">Munim AI — Aapke Dukaan Ka Digital Munim</span>
          </div>
          <div className="flex items-center gap-6">
            {["Privacy", "Terms", "Contact"].map((l) => (
              <a key={l} href="#" className="text-[#5d7a63] hover:text-[#9db8a0] text-sm transition-colors">
                {l}
              </a>
            ))}
          </div>
          <p className="text-[#5d7a63] text-xs">Made with ❤️ for India's home sellers</p>
        </div>
      </footer>
    </div>
  );
}
