"use client";

const FEATURES = [
  {
    icon: "📱",
    color: "#25D366",
    title: "WhatsApp se Orders",
    desc: "Customers ka message, seedha order mein. Zero extra app.",
  },
  {
    icon: "🗂️",
    color: "#4efa72",
    title: "Automatic Record",
    desc: "Orders, payments aur customers sab apne aap update.",
  },
  {
    icon: "👥",
    color: "#60a5fa",
    title: "Customer Ki Yaad",
    desc: "Har customer ka purana order, preference aur details hamesha available.",
  },
  {
    icon: "📦",
    color: "#fbbf24",
    title: "Inventory (Stock)",
    desc: "Kitna maal bacha hai, hamesha pata rahe.",
  },
  {
    icon: "🔔",
    color: "#f87171",
    title: "Baki (Dues) Alert",
    desc: "Jin customers ke paise pending hain, unki reminder list.",
  },
  {
    icon: "📊",
    color: "#c084fc",
    title: "Simple Reports",
    desc: "Roz, hafte aur mahine ki bikri ka saaf hisaab.",
  },
];

const STEPS = [
  {
    num: 1,
    icon: "📱",
    color: "#25D366",
    title: "Customer message karta hai",
    desc: "Seedha WhatsApp par — koi extra app nahi, koi training nahi",
  },
  {
    num: 2,
    icon: "✨",
    color: "#4efa72",
    title: "Munim AI message samajhkar record karta hai",
    desc: "AI automatically order, payment ya query identify karta hai",
  },
  {
    num: 3,
    icon: "📊",
    color: "#60a5fa",
    title: "Dashboard par milein updates",
    desc: "Aapko orders, payments aur customer data instant milta hai",
  },
];

export default function FeaturesSection() {
  return (
    <>
      {/* Features */}
      <section id="features" className="py-24 relative">
        <div className="max-w-7xl mx-auto px-6">
          {/* Badge */}
          <div className="flex justify-center mb-4">
            <div className="inline-flex items-center gap-2 bg-[rgba(78,250,114,0.1)] border border-[rgba(78,250,114,0.2)] rounded-full px-4 py-1.5">
              <span className="text-[#4efa72] text-xs">✨</span>
              <span className="text-[#4efa72] text-xs font-semibold">Sab Kuch Ek Jagah</span>
            </div>
          </div>

          <h2 className="text-center text-4xl md:text-5xl font-black text-[#f0fdf4] mb-3">
            Aapke Business ke Liye,{" "}
            <span className="text-[#4efa72]">Smart Features</span>
          </h2>
          <p className="text-center text-[#9db8a0] text-lg max-w-xl mx-auto mb-14">
            Munim AI aapke roz ke kaam ko asaan, tez aur organized banata hai.
          </p>

          {/* Grid */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f, i) => (
              <div
                key={f.title}
                className="glass-card p-6 group cursor-default"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-4 transition-transform group-hover:scale-110"
                  style={{ background: `${f.color}1a`, boxShadow: `0 0 12px ${f.color}30` }}
                >
                  {f.icon}
                </div>
                <h3 className="text-[#f0fdf4] font-bold text-base mb-2">{f.title}</h3>
                <p className="text-[#9db8a0] text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section id="how-it-works" className="py-20 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            {/* Left text */}
            <div className="lg:w-64 flex-shrink-0">
              <p className="text-[#4efa72] text-sm font-semibold mb-2">Kaise Kaam Karta Hai?</p>
              <h2 className="text-3xl md:text-4xl font-black text-[#f0fdf4]">
                Bas{" "}
                <span className="text-[#4efa72]">3 Simple</span>
                <br />
                Steps
              </h2>
              <div className="w-16 h-1 bg-gradient-to-r from-[#4efa72] to-transparent rounded-full mt-3" />
            </div>

            {/* Steps */}
            <div className="flex-1 flex flex-col md:flex-row items-center gap-4 md:gap-0">
              {STEPS.map((step, i) => (
                <div key={step.num} className="flex flex-col md:flex-row items-center flex-1">
                  <div className="glass-card p-6 flex flex-col items-center text-center flex-1 relative">
                    {/* Step number badge */}
                    <div
                      className="absolute -top-3 -right-3 w-7 h-7 rounded-full flex items-center justify-center text-[#0d1410] font-black text-xs border-2 border-[#0d1410]"
                      style={{ background: step.color, boxShadow: `0 0 10px ${step.color}60` }}
                    >
                      {step.num}
                    </div>
                    <div
                      className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl mb-4"
                      style={{ background: `${step.color}15` }}
                    >
                      {step.icon}
                    </div>
                    <h3 className="text-[#f0fdf4] font-bold text-sm mb-2">{step.title}</h3>
                    <p className="text-[#9db8a0] text-xs leading-relaxed">{step.desc}</p>
                  </div>
                  {/* Arrow between steps */}
                  {i < STEPS.length - 1 && (
                    <div className="flex items-center justify-center w-10 h-10 text-[#4efa72] text-xl flex-shrink-0 my-4 md:my-0">
                      →
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

