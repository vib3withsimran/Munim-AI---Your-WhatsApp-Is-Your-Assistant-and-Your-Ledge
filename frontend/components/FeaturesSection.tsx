"use client";

const FEATURES = [
  {
    icon: (
      <svg className="w-7 h-7 stroke-[#B5FF4D] fill-none" viewBox="0 0 24 24" strokeWidth="2">
        <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" />
      </svg>
    ),
    title: "WhatsApp se Orders",
    desc: "Customers ka message, seedha order mein.",
  },
  {
    icon: (
      <svg className="w-7 h-7 stroke-[#B5FF4D] fill-none" viewBox="0 0 24 24" strokeWidth="2">
        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
      </svg>
    ),
    title: "Automatic Record",
    desc: "Orders, payments aur customers sab apne aap update.",
  },
  {
    icon: (
      <svg className="w-7 h-7 stroke-[#B5FF4D] fill-none" viewBox="0 0 24 24" strokeWidth="2">
        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
      </svg>
    ),
    title: "Customer Ki Yaad",
    desc: "Har customer ka purana order, preference aur details hamesha available.",
  },
  {
    icon: (
      <svg className="w-7 h-7 stroke-[#B5FF4D] fill-none" viewBox="0 0 24 24" strokeWidth="2">
        <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
        <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
        <line x1="12" y1="22.08" x2="12" y2="12" />
      </svg>
    ),
    title: "Inventory (Stock)",
    desc: "Kitna maal bacha hai, hamesha pata rahe.",
  },
  {
    icon: (
      <div className="relative">
        <svg className="w-7 h-7 stroke-[#B5FF4D] fill-none" viewBox="0 0 24 24" strokeWidth="2">
          <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 01-3.46 0" />
        </svg>
        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-[#10211A]" />
      </div>
    ),
    title: "Baki (Dues) Alert",
    desc: "Jin customers ke paise pending hain, unki reminder list.",
  },
  {
    icon: (
      <svg className="w-7 h-7 stroke-[#B5FF4D] fill-none" viewBox="0 0 24 24" strokeWidth="2">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
    title: "Simple Reports",
    desc: "Roz, hafte aur mahine ki bikri ka saaf hisaab.",
  },
];

export default function FeaturesSection() {
  return (
    <section id="features" className="relative py-28 bg-[#071410] overflow-hidden">
      {/* Ambient background light */}
      <div className="absolute top-[20%] left-[5%] w-[550px] h-[550px] bg-[#4efa72]/8 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[15%] right-[5%] w-[550px] h-[550px] bg-[#22c55e]/8 rounded-full blur-[150px] pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 space-y-24">
        {/* Section Header */}
        <div className="text-center space-y-5 max-w-3xl mx-auto">
          {/* Centered Pill */}
          <div className="inline-flex items-center gap-2 bg-[#0B1B16] border border-[#4efa72]/30 rounded-full px-4 py-1.5 shadow-[0_0_15px_rgba(78,250,114,0.12)]">
            <span className="text-[#B5FF4D] text-xs">✨</span>
            <span className="text-[#BAC8C1] text-xs font-semibold tracking-wide">
              Sab Kuch Ek Jagah
            </span>
          </div>

          {/* Heading */}
          <div className="space-y-2">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#F5F7F4] tracking-tight leading-[1.15]">
              Aapke Business ke Liye,{" "}
              <span className="relative inline-block text-[#B5FF4D]">
                Smart Features
                <svg
                  className="absolute -bottom-3 left-0 w-full h-4 overflow-visible pointer-events-none"
                  viewBox="0 0 240 14"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M4 11C60 3 180 3 236 10"
                    stroke="#B5FF4D"
                    strokeWidth="4"
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

        {/* Six Feature Cards (3 columns x 2 rows) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((item, idx) => (
            <div
              key={idx}
              className="bg-[#10211A]/95 hover:bg-[#142921] border border-[#4efa72]/20 hover:border-[#B5FF4D]/50 rounded-2xl p-7 transition-all duration-300 shadow-[0_4px_25px_rgba(0,0,0,0.35)] hover:shadow-[0_0_30px_rgba(78,250,114,0.18)] hover:-translate-y-1 flex items-center gap-5 min-h-[120px]"
            >
              <div className="w-14 h-14 rounded-2xl bg-[#0B1B16] border border-[#4efa72]/30 flex items-center justify-center flex-shrink-0 shadow-[0_0_15px_rgba(78,250,114,0.12)]">
                {item.icon}
              </div>
              <div className="space-y-1 flex-1 min-w-0">
                <h3 className="text-[#F5F7F4] font-bold text-lg leading-tight">
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
        <div id="workflow" className="pt-6 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Title */}
          <div className="lg:col-span-4 space-y-2.5">
            <span className="text-[#B5FF4D] text-xs font-black tracking-widest uppercase">
              Kaise Kaam Karta Hai?
            </span>
            <div className="relative inline-block">
              <h3 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#F5F7F4] tracking-tight leading-tight">
                Bas 3 Simple Steps
              </h3>
              <svg
                className="absolute -bottom-3 left-0 w-full h-4 overflow-visible pointer-events-none"
                viewBox="0 0 220 14"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M4 11C55 3 165 3 216 10"
                  stroke="#B5FF4D"
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              </svg>
            </div>
          </div>

          {/* Right Wide Workflow Container */}
          <div className="lg:col-span-8 bg-[#10211A] border border-[#4efa72]/30 rounded-3xl p-6 sm:p-10 shadow-[0_15px_40px_rgba(0,0,0,0.6)]">
            <div className="flex flex-col md:flex-row items-center justify-between gap-8 md:gap-4">
              {/* Step 1 */}
              <div className="flex-1 flex flex-col items-center text-center space-y-4 w-full">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full bg-[#1b3d2d] border-2 border-[#B5FF4D]/50 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(181,255,77,0.25)]">
                    <svg className="w-8 h-8 fill-[#B5FF4D]" viewBox="0 0 24 24">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.888 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                    </svg>
                  </div>
                  <span className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-[#B5FF4D] text-[#071410] text-xs font-black flex items-center justify-center border-2 border-[#10211A] shadow-md">
                    1
                  </span>
                </div>
                <p className="text-[#F5F7F4] text-sm sm:text-base font-bold max-w-[200px] leading-snug">
                  Customer message karta hai
                </p>
              </div>

              {/* Chevron Arrow */}
              <div className="text-[#B5FF4D] text-2xl font-black rotate-90 md:rotate-0 opacity-80 flex-shrink-0">
                ›
              </div>

              {/* Step 2 */}
              <div className="flex-1 flex flex-col items-center text-center space-y-4 w-full">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full bg-[#1b3d2d] border-2 border-[#B5FF4D]/50 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(181,255,77,0.25)]">
                    <span className="text-3xl text-[#B5FF4D]">✨</span>
                  </div>
                  <span className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-[#B5FF4D] text-[#071410] text-xs font-black flex items-center justify-center border-2 border-[#10211A] shadow-md">
                    2
                  </span>
                </div>
                <p className="text-[#F5F7F4] text-sm sm:text-base font-bold max-w-[220px] leading-snug">
                  Munim AI message samajhkar record karta hai
                </p>
              </div>

              {/* Chevron Arrow */}
              <div className="text-[#B5FF4D] text-2xl font-black rotate-90 md:rotate-0 opacity-80 flex-shrink-0">
                ›
              </div>

              {/* Step 3 */}
              <div className="flex-1 flex flex-col items-center text-center space-y-4 w-full">
                <div className="relative">
                  <div className="w-16 h-16 rounded-full bg-[#1b3d2d] border-2 border-[#B5FF4D]/50 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(181,255,77,0.25)]">
                    <svg className="w-7 h-7 stroke-[#B5FF4D] fill-none" viewBox="0 0 24 24" strokeWidth="2.5">
                      <line x1="18" y1="20" x2="18" y2="10" />
                      <line x1="12" y1="20" x2="12" y2="4" />
                      <line x1="6" y1="20" x2="6" y2="14" />
                    </svg>
                  </div>
                  <span className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-[#B5FF4D] text-[#071410] text-xs font-black flex items-center justify-center border-2 border-[#10211A] shadow-md">
                    3
                  </span>
                </div>
                <p className="text-[#F5F7F4] text-sm sm:text-base font-bold max-w-[230px] leading-snug">
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
