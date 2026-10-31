import LandingNav from "@/components/LandingNav";
import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import FinalCTASection from "@/components/FinalCTASection";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#071410] text-[#F5F7F4]">
      <LandingNav />
      <main>
        <HeroSection />
        <FeaturesSection />
        <FinalCTASection />
      </main>

      {/* Footer */}
      <footer className="border-t border-[#4efa72]/15 bg-[#050e0b] py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#B5FF4D] flex items-center justify-center text-[#071410] font-black text-xs">
              M
            </div>
            <span className="text-[#BAC8C1] text-sm">
              Munim AI — Aapke Dukaan Ka Digital Munim
            </span>
          </div>
          <div className="flex items-center gap-6">
            {["Features", "How it Works", "Dashboard", "Privacy", "Contact"].map((l) => (
              <a
                key={l}
                href={l === "Dashboard" ? "/dashboard" : `#${l.toLowerCase().replace(/ /g, "-")}`}
                className="text-[#5d7a63] hover:text-[#B5FF4D] text-xs transition-colors"
              >
                {l}
              </a>
            ))}
          </div>
          <p className="text-[#5d7a63] text-xs">Made with ❤️ for India&apos;s home sellers</p>
        </div>
      </footer>
    </div>
  );
}
