"use client";

import { useState } from "react";

const BEFORE = [
  "📔 Register mein haath se hisaab likhna",
  "😰 WhatsApp messages kho jana ya bhool jana",
  "😬 Baki paise yaad na rehna",
  "❌ Calculation mistakes",
  "⏰ 2-3 ghante daily record karna",
  "🤷 Customer ka purana order dhundhna padta hai",
];

const AFTER = [
  "✅ Automatic order booking, zero typing",
  "✅ Har message record, kuch kho nahi sakta",
  "✅ Instant dues alert, 1-click WhatsApp reminder",
  "✅ AI calculation, zero human error",
  "✅ 0 extra time — sab khud hota hai",
  "✅ Customer history ek click mein",
];

const TESTIMONIALS = [
  {
    name: "Ritu Aggarwal",
    business: "Kurti Boutique, Jaipur",
    avatar: "RA",
    color: "#4efa72",
    quote:
      "Pehle raat ko register likhna padta tha. Ab seedha WhatsApp message aata hai aur Munim AI khud hi sab note kar leta hai. Mujhe kuch nahi karna!",
    metric: "3 ghante bachaye roz",
  },
  {
    name: "Priya Bakshi",
    business: "Home Bakery, Delhi",
    avatar: "PB",
    color: "#60a5fa",
    quote:
      "Meri customers Hindi mein order karti hain. Munim AI sab samajhta hai — English ya Hindi, kuch bhi bolo. Orders perfectly record hote hain.",
    metric: "Koi order miss nahi hua",
  },
  {
    name: "Sunita Patel",
    business: "Imitation Jewellery, Surat",
    avatar: "SP",
    color: "#fbbf24",
    quote:
      "Dues reminder feature best hai! Ab manually message nahi karna padta. Ek click mein WhatsApp reminder chali jaati hai. Customers bhi khush hain.",
    metric: "₹18,000 dues recover kiye",
  },
];

const FAQS = [
  {
    q: "Kya mujhe computer chalana aana chahiye?",
    a: "Bilkul nahi! Sirf WhatsApp use karna aana chahiye. Baki sab Munim AI khud karta hai.",
  },
  {
    q: "Customer ko pata chalega ki AI reply kar raha hai?",
    a: "Aap decide karte hain. Reply style bilkul aapki bhasha mein hoga — Hindi, Hinglish ya English.",
  },
  {
    q: "Kya mera data safe hai?",
    a: "100% safe. Aapka data sirf aapka hai. #private command se koi bhi conversation private rakho.",
  },
  {
    q: "Agar customer Hindi mein bole toh?",
    a: "No problem! Munim AI Hindi, Hinglish, English — teeno samajhta hai perfectly.",
  },
  {
    q: "Kya ye free hai?",
    a: "30 din free trial! Phir affordable plans from ₹299/month — ek order se hi recover ho jaata hai.",
  },
];

export default function ExtraSections() {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  return (
    <>
      {/* Before vs After */}
      <section className="py-20 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 bg-[rgba(78,250,114,0.1)] border border-[rgba(78,250,114,0.2)] rounded-full px-4 py-1.5 mb-4">
              <span className="text-[#4efa72] text-xs font-semibold">Real Fark</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-black text-[#f0fdf4]">
              Purana Tarika vs{" "}
              <span className="text-[#4efa72]">Munim AI</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {/* Before */}
            <div className="glass-card p-6 border-[rgba(248,113,113,0.2)]">
              <div className="flex items-center gap-2 mb-5">
                <div className="w-8 h-8 rounded-full bg-[rgba(248,113,113,0.15)] flex items-center justify-center text-sm">😩</div>
                <h3 className="text-[#f87171] font-bold text-lg">Purana Tarika</h3>
              </div>
              <div className="space-y-3">
                {BEFORE.map((b) => (
                  <div key={b} className="flex items-start gap-2 text-sm text-[#9db8a0]">
                    <span className="flex-shrink-0">{b.split(" ")[0]}</span>
                    <span>{b.slice(b.indexOf(" ") + 1)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* After */}
            <div className="glass-card p-6 border-[rgba(78,250,114,0.3)] shadow-[0_0_30px_rgba(78,250,114,0.1)]">
              <div className="flex items-center gap-2 mb-5">
                <div className="w-8 h-8 rounded-full bg-[rgba(78,250,114,0.15)] flex items-center justify-center text-sm">🚀</div>
                <h3 className="text-[#4efa72] font-bold text-lg">Munim AI</h3>
              </div>
              <div className="space-y-3">
                {AFTER.map((a) => (
                  <div key={a} className="flex items-start gap-2 text-sm text-[#f0fdf4]">
                    <span className="flex-shrink-0">{a.split(" ")[0]}</span>
                    <span>{a.slice(a.indexOf(" ") + 1)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-4xl md:text-5xl font-black text-[#f0fdf4]">
              Real{" "}
              <span className="text-[#4efa72]">Dukaandaron</span> ki Baatein
            </h2>
            <p className="text-[#9db8a0] mt-3">Jinke business Munim AI ne badal diye</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t) => (
              <div key={t.name} className="glass-card p-6 flex flex-col">
                {/* Quote */}
                <p className="text-[#9db8a0] text-sm leading-relaxed flex-1 italic">
                  &ldquo;{t.quote}&rdquo;
                </p>

                {/* Metric pill */}
                <div
                  className="inline-flex items-center gap-1.5 mt-4 mb-4 px-3 py-1 rounded-full text-xs font-semibold self-start"
                  style={{ background: `${t.color}15`, color: t.color, border: `1px solid ${t.color}30` }}
                >
                  ↑ {t.metric}
                </div>

                {/* Author */}
                <div className="flex items-center gap-3 pt-4 border-t border-[rgba(78,250,114,0.1)]">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center font-black text-[#0d1410] text-sm flex-shrink-0"
                    style={{ background: t.color }}
                  >
                    {t.avatar}
                  </div>
                  <div>
                    <p className="text-[#f0fdf4] font-semibold text-sm">{t.name}</p>
                    <p className="text-[#5d7a63] text-xs">{t.business}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Privacy Section */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="glass-card p-8 md:p-12 flex flex-col md:flex-row items-center gap-8 border-[rgba(78,250,114,0.2)]">
            <div className="text-6xl flex-shrink-0">🔒</div>
            <div>
              <h2 className="text-2xl md:text-3xl font-black text-[#f0fdf4] mb-3">
                Aapka Data, Sirf <span className="text-[#4efa72]">Aapka</span>
              </h2>
              <p className="text-[#9db8a0] text-base leading-relaxed max-w-2xl">
                <strong className="text-[#f0fdf4]">#private command</strong> se koi bhi conversation instantly private ho jaati hai — AI record nahi karta, store nahi karta.
                Bank details, personal baatein, sab secure. Cloud backup with end-to-end security.
              </p>
              <div className="flex flex-wrap gap-3 mt-5">
                {["🔒 Private Conversations", "☁️ Secure Cloud Backup", "🛡️ Data aapka", "✅ GDPR Compliant"].map((b) => (
                  <span key={b} className="text-xs text-[#9db8a0] bg-[rgba(78,250,114,0.06)] border border-[rgba(78,250,114,0.12)] px-3 py-1.5 rounded-full">
                    {b}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="pricing" className="py-20">
        <div className="max-w-3xl mx-auto px-6">
          <h2 className="text-center text-4xl font-black text-[#f0fdf4] mb-10">
            Aapke <span className="text-[#4efa72]">Sawaal</span>, Hamare Jawaab
          </h2>
          <div className="space-y-3">
            {FAQS.map((faq, i) => (
              <div key={i} className="glass-card overflow-hidden">
                <button
                  className="w-full flex items-center justify-between px-5 py-4 text-left"
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                >
                  <span className="text-[#f0fdf4] font-medium text-sm pr-4">{faq.q}</span>
                  <span
                    className={`text-[#4efa72] text-lg flex-shrink-0 transition-transform ${openFaq === i ? "rotate-45" : ""}`}
                  >
                    +
                  </span>
                </button>
                {openFaq === i && (
                  <div className="px-5 pb-4 border-t border-[rgba(78,250,114,0.08)]">
                    <p className="text-[#9db8a0] text-sm leading-relaxed pt-3">{faq.a}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="glass-card p-10 md:p-16 relative overflow-hidden border-[rgba(78,250,114,0.2)] shadow-[0_0_60px_rgba(78,250,114,0.1)]">
            <div className="absolute inset-0 bg-gradient-radial-green pointer-events-none" />
            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-black text-[#f0fdf4] mb-4">
                Aaj Hi Shuru Karen
              </h2>
              <p className="text-[#9db8a0] text-lg mb-8 max-w-xl mx-auto">
                30 din ka free trial. Koi credit card nahi. Seedha WhatsApp se start.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <a
                  href="https://wa.me/14155238886?text=Hi+Munim+AI!"
                  target="_blank"
                  className="flex items-center gap-2.5 bg-[#4efa72] hover:bg-[#3acc5c] text-[#0d1410] font-bold text-base px-8 py-4 rounded-xl transition-all shadow-[0_0_30px_rgba(78,250,114,0.5)] hover:shadow-[0_0_50px_rgba(78,250,114,0.7)]"
                >
                  <span className="text-xl">📱</span> WhatsApp pe Start Karen
                </a>
                <a
                  href="/dashboard"
                  className="flex items-center gap-2 border border-[rgba(78,250,114,0.25)] text-[#f0fdf4] font-semibold text-base px-8 py-4 rounded-xl hover:border-[rgba(78,250,114,0.5)] transition-all"
                >
                  📊 Dashboard Dekhein
                </a>
              </div>
              <p className="text-[#5d7a63] text-sm mt-6">
                1,200+ sellers already use Munim AI ·{" "}
                <span className="text-[#4efa72]">4.9 ★</span> rating
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

