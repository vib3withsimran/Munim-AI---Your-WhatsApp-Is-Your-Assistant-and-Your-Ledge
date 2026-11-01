import {
  MessageCircle,
  Layers,
  Users,
  Package,
  Bell,
  BarChart3,
  Sparkles,
  ChevronRight,
} from "lucide-react";

interface FeatureItem {
  id: string;
  title: string;
  desc: string;
  icon: React.ReactNode;
}

const FEATURES: FeatureItem[] = [
  {
    id: "orders",
    title: "WhatsApp se Orders",
    desc: "Customers ka message, seedha order mein.",
    icon: <MessageCircle className="w-7 h-7 text-[#B6F23C]" />,
  },
  {
    id: "record",
    title: "Automatic Record",
    desc: "Orders, payments aur customers sab apne aap update.",
    icon: <Layers className="w-7 h-7 text-[#B6F23C]" />,
  },
  {
    id: "memory",
    title: "Customer Ki Yaad",
    desc: "Har customer ka purana order, preference aur details hamesha available.",
    icon: <Users className="w-7 h-7 text-[#B6F23C]" />,
  },
  {
    id: "inventory",
    title: "Inventory (Stock)",
    desc: "Kitna maal bacha hai, hamesha pata rahe.",
    icon: <Package className="w-7 h-7 text-[#B6F23C]" />,
  },
  {
    id: "dues",
    title: "Baki (Dues) Alert",
    desc: "Jin customers ke paise pending hain, unki reminder list.",
    icon: (
      <div className="relative">
        <Bell className="w-7 h-7 text-[#B6F23C]" />
        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-[#0B1A13]" />
      </div>
    ),
  },
  {
    id: "reports",
    title: "Simple Reports",
    desc: "Roz, hafte aur mahine ki bikri ka saaf hisaab.",
    icon: <BarChart3 className="w-7 h-7 text-[#B6F23C]" />,
  },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="relative py-20 sm:py-28 bg-[#07110D] overflow-hidden">
      {/* Ambient background glows */}
      <div className="absolute top-[25%] left-[5%] w-[500px] h-[500px] bg-[#10B981]/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[20%] right-[5%] w-[550px] h-[550px] bg-[#B6F23C]/10 rounded-full blur-[150px] pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-5 sm:px-8 lg:px-12 space-y-20 sm:space-y-24">
        {/* Section Header */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          {/* Centered Pill */}
          <div className="inline-flex items-center gap-2 bg-[#0B1A13] border border-[#224430] rounded-full px-4 py-1.5 shadow-[0_0_15px_rgba(182,242,60,0.1)]">
            <Sparkles className="w-3.5 h-3.5 text-[#B6F23C]" />
            <span className="text-[#BAC8C1] text-xs font-semibold tracking-wide">
              Sab Kuch Ek Jagah
            </span>
          </div>

          {/* Heading */}
          <div className="space-y-1 sm:space-y-2">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#F0FDF4] tracking-tight leading-[1.15]">
              Aapke Business ke Liye,{" "}
              <span className="relative inline-block text-[#B6F23C]">
                Smart Features
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
            </h2>
          </div>

          {/* Subtitle */}
          <p className="text-[#BAC8C1] text-base sm:text-lg lg:text-xl pt-2">
            Munim AI aapke roz ke kaam ko asaan, tez aur organized banata hai.
          </p>
        </div>

        {/* 6 Feature Cards (3 columns x 2 rows) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
          {FEATURES.map((item) => (
            <div
              key={item.id}
              className="bg-[#0B1A13]/90 hover:bg-[#10241A] border border-[#224430] hover:border-[#B6F23C]/50 rounded-2xl p-6 sm:p-7 transition-all duration-300 shadow-[0_4px_24px_rgba(0,0,0,0.35)] hover:shadow-[0_0_30px_rgba(182,242,60,0.18)] hover:-translate-y-1 flex items-center gap-5 min-h-[120px]"
            >
              <div className="w-14 h-14 rounded-2xl bg-[#10211A] border border-[#224430] flex items-center justify-center flex-shrink-0 shadow-[0_0_15px_rgba(182,242,60,0.12)]">
                {item.icon}
              </div>
              <div className="space-y-1 flex-1 min-w-0">
                <h3 className="text-[#F0FDF4] font-bold text-lg leading-tight">
                  {item.title}
                </h3>
                <p className="text-[#BAC8C1] text-xs sm:text-sm leading-relaxed">
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Workflow Section: "Bas 3 Simple Steps" */}
        <div id="workflow" className="pt-4 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
          {/* Left Title */}
          <div className="lg:col-span-4 space-y-2">
            <span className="text-[#B6F23C] text-xs font-bold tracking-widest uppercase">
              Kaise Kaam Karta Hai?
            </span>
            <div className="relative inline-block">
              <h3 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#F0FDF4] tracking-tight leading-tight">
                Bas 3 Simple Steps
              </h3>
              <svg
                className="absolute -bottom-3 left-0 w-full h-3.5 sm:h-4 overflow-visible pointer-events-none text-[#B6F23C]"
                viewBox="0 0 220 12"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  d="M3 8.5C55 2.5 150 2.5 217 8"
                  stroke="currentColor"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                />
              </svg>
            </div>
          </div>

          {/* Right Wide Workflow Container */}
          <div className="lg:col-span-8 bg-[#0B1A13]/90 border border-[#224430] rounded-3xl p-6 sm:p-10 shadow-[0_15px_40px_rgba(0,0,0,0.6)]">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8 md:gap-4">
              {/* Step 1 */}
              <div className="flex-1 flex flex-col items-center text-center space-y-3.5 w-full">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full bg-[#10211A] border-2 border-[#B6F23C]/50 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(182,242,60,0.25)]">
                    <MessageCircle className="w-8 h-8 text-[#B6F23C]" />
                  </div>
                  <span className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-[#B6F23C] text-[#07110D] text-xs font-black flex items-center justify-center border-2 border-[#0B1A13] shadow-md">
                    1
                  </span>
                </div>
                <p className="text-[#F0FDF4] text-sm sm:text-base font-bold max-w-[200px] leading-snug">
                  Customer message karta hai
                </p>
              </div>

              <div className="text-[#B6F23C] rotate-90 md:rotate-0 opacity-80 flex-shrink-0">
                <ChevronRight className="w-6 h-6" />
              </div>

              {/* Step 2 */}
              <div className="flex-1 flex flex-col items-center text-center space-y-3.5 w-full">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full bg-[#10211A] border-2 border-[#B6F23C]/50 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(182,242,60,0.25)]">
                    <Sparkles className="w-8 h-8 text-[#B6F23C]" />
                  </div>
                  <span className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-[#B6F23C] text-[#07110D] text-xs font-black flex items-center justify-center border-2 border-[#0B1A13] shadow-md">
                    2
                  </span>
                </div>
                <p className="text-[#F0FDF4] text-sm sm:text-base font-bold max-w-[220px] leading-snug">
                  Munim AI message samajhkar record karta hai
                </p>
              </div>

              <div className="text-[#B6F23C] rotate-90 md:rotate-0 opacity-80 flex-shrink-0">
                <ChevronRight className="w-6 h-6" />
              </div>

              {/* Step 3 */}
              <div className="flex-1 flex flex-col items-center text-center space-y-3.5 w-full">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full bg-[#10211A] border-2 border-[#B6F23C]/50 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(182,242,60,0.25)]">
                    <BarChart3 className="w-8 h-8 text-[#B6F23C]" />
                  </div>
                  <span className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-[#B6F23C] text-[#07110D] text-xs font-black flex items-center justify-center border-2 border-[#0B1A13] shadow-md">
                    3
                  </span>
                </div>
                <p className="text-[#F0FDF4] text-sm sm:text-base font-bold max-w-[230px] leading-snug">
                  Aapko orders, payments aur updates dashboard par milte hain
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

