"use client";

import { useState, useEffect } from "react";

const TYPING_MESSAGES = [
  "5 blue kurti aur 3 black kurti bhej do",
  "Kya pink anarkali available hai?",
  "Maine 599 UPI se bhej diya",
  "2 kurti size M medium chahiye",
];

const BOT_REPLIES: Record<string, string> = {
  "5 blue kurti aur 3 black kurti bhej do": "✅ Order likh liya!\n\n• Blue Kurti × 5\n• Black Kurti × 3\n\nKul: ₹4,900\nBheju?",
  "Kya pink anarkali available hai?": "🌸 Haanji! Pink Anarkali available hai — ₹899 (Sizes: S, M, L, XL)\n\nSize batao, order karo?",
  "Maine 599 UPI se bhej diya": "✅ Payment received! ₹599 record ho gaya.\n\nAapka parcel kal dispatch hoga. 🚚",
  "2 kurti size M medium chahiye": "✅ Order note kar liya!\n\n• Kurti × 2 (Size: M)\n\nKul: ₹1,198\n\nDelivery address bhejiye?",
};

export default function HeroSection() {
  const [msgIdx, setMsgIdx] = useState(0);
  const [userMsg, setUserMsg] = useState("");
  const [botMsg, setBotMsg] = useState<string | null>(null);
  const [typing, setTyping] = useState(true);
  const [charIdx, setCharIdx] = useState(0);
  const [sent, setSent] = useState(false);
  const [replying, setReplying] = useState(false);

  // Typewriter effect
  useEffect(() => {
    if (!typing) return;
    if (charIdx < TYPING_MESSAGES[msgIdx].length) {
      const t = setTimeout(() => {
        setUserMsg((p) => p + TYPING_MESSAGES[msgIdx][charIdx]);
        setCharIdx((c) => c + 1);
      }, 60);
      return () => clearTimeout(t);
    } else {
      const t = setTimeout(() => {
        setTyping(false);
        setSent(true);
        setReplying(true);
        setTimeout(() => {
          setBotMsg(BOT_REPLIES[TYPING_MESSAGES[msgIdx]] ?? "Samajh gaya! ✅");
          setReplying(false);
        }, 1200);
      }, 500);
      return () => clearTimeout(t);
    }
  }, [typing, charIdx, msgIdx]);

  // Cycle to next message
  useEffect(() => {
    if (!sent || replying) return;
    const t = setTimeout(() => {
      const next = (msgIdx + 1) % TYPING_MESSAGES.length;
      setMsgIdx(next);
      setUserMsg("");
      setBotMsg(null);
      setSent(false);
      setTyping(true);
      setCharIdx(0);
    }, 3000);
    return () => clearTimeout(t);
  }, [sent, replying, msgIdx]);

  return (
    <section className="relative min-h-screen flex items-center overflow-hidden">
      {/* Background glows */}
      <div className="absolute inset-0 bg-gradient-radial-green pointer-events-none" />
      <div className="absolute top-1/3 left-1/4 w-96 h-96 bg-[#4efa72] opacity-5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-[#4efa72] opacity-8 rounded-full blur-2xl pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto px-6 pt-24 pb-16 grid lg:grid-cols-2 gap-12 lg:gap-16 items-center w-full">
        {/* Left: Copy */}
        <div className="animate-slide-up">
          {/* Tag */}
          <div className="inline-flex items-center gap-2 bg-[rgba(78,250,114,0.1)] border border-[rgba(78,250,114,0.25)] rounded-full px-4 py-1.5 mb-6">
            <span className="text-[#4efa72] text-xs">✨</span>
            <span className="text-[#4efa72] text-xs font-semibold">AI-Powered Business Assistant</span>
          </div>

          {/* Headline */}
          <h1 className="text-5xl xl:text-6xl font-black text-[#f0fdf4] leading-tight">
            Aapke Dukaan Ka
            <br />
            <span className="text-[#4efa72] relative">
              Digital Munim
              <span
                className="absolute bottom-0 left-0 right-0 h-1 rounded-full"
                style={{
                  background: "linear-gradient(90deg, #4efa72, #3acc5c)",
                  boxShadow: "0 0 12px rgba(78,250,114,0.6)",
                }}
              />
            </span>
          </h1>

          {/* Sub */}
          <p className="text-[#9db8a0] text-lg mt-6 leading-relaxed max-w-md">
            WhatsApp par hi orders lo, payments track karo, customer ki baatein yaad rakho — sab automatic,
            simple aur <strong className="text-[#f0fdf4]">aapki apni bhasha mein.</strong>
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap items-center gap-4 mt-8">
            <a
              href="https://wa.me/14155238886?text=Hi+Munim+AI!"
              target="_blank"
              className="flex items-center gap-2.5 bg-[#4efa72] hover:bg-[#3acc5c] text-[#0d1410] font-bold text-base px-6 py-3.5 rounded-xl transition-all shadow-[0_0_24px_rgba(78,250,114,0.45)] hover:shadow-[0_0_36px_rgba(78,250,114,0.65)] hover:translate-y-[-1px]"
            >
              <span className="text-lg">📱</span> Start on WhatsApp
            </a>
            <a
              href="#demo"
              className="flex items-center gap-2 border border-[rgba(78,250,114,0.25)] text-[#f0fdf4] hover:border-[rgba(78,250,114,0.5)] hover:text-[#4efa72] font-semibold text-base px-6 py-3.5 rounded-xl transition-all bg-[rgba(78,250,114,0.04)]"
            >
              See Demo <span className="text-[#4efa72]">▶</span>
            </a>
          </div>

          {/* Badges */}
          <div className="flex items-center gap-4 mt-8">
            {[
              { icon: "⚡", label: "Simple" },
              { icon: "₹", label: "Saves Time" },
              { icon: "📊", label: "Grows Business" },
            ].map((b) => (
              <div
                key={b.label}
                className="flex items-center gap-1.5 bg-[rgba(78,250,114,0.06)] border border-[rgba(78,250,114,0.12)] rounded-full px-3 py-1.5"
              >
                <span className="text-[#4efa72] text-sm">{b.icon}</span>
                <span className="text-[#9db8a0] text-xs font-medium">{b.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Phone Mock */}
        <div className="flex justify-center items-center">
          <div className="relative animate-[float_6s_ease-in-out_infinite]">
            {/* Glow under phone */}
            <div className="absolute inset-0 bg-[#4efa72] opacity-15 blur-3xl rounded-full scale-75 translate-y-8 pointer-events-none" />

            {/* Phone frame */}
            <div className="relative w-[280px] bg-[#111] rounded-[2.5rem] border-4 border-[#2a2a2a] shadow-[0_40px_80px_rgba(0,0,0,0.6)] overflow-hidden">
              {/* Phone top bar */}
              <div className="bg-[#0d1410] px-4 py-3 flex items-center gap-2 border-b border-[#1e2d21]">
                <div className="w-8 h-8 rounded-full bg-[#4efa72] flex items-center justify-center text-[#0d1410] font-black text-sm">M</div>
                <div>
                  <p className="text-[#f0fdf4] text-xs font-semibold">Munim AI</p>
                  <p className="text-[#4efa72] text-[10px]">Business Assistant</p>
                </div>
                <div className="ml-auto flex items-center gap-2 text-[#5d7a63] text-xs">
                  📞 ⋮
                </div>
              </div>

              {/* Chat area */}
              <div className="bg-[#0a1f0e] px-3 py-4 min-h-[280px] flex flex-col justify-end gap-3">
                {/* User bubble */}
                {userMsg && (
                  <div className="flex justify-end">
                    <div className="bg-[#005c4b] text-[#f0fdf4] text-xs rounded-[12px_12px_2px_12px] px-3 py-2 max-w-[80%] leading-snug whitespace-pre-wrap">
                      {userMsg}
                      {!sent && <span className="inline-block w-0.5 h-3 bg-[#f0fdf4] ml-0.5 animate-[pulse-green_0.8s_ease-in-out_infinite]" />}
                      {sent && <span className="block text-right text-[#4efa72] text-[9px] mt-1">10:24 AM ✓✓</span>}
                    </div>
                  </div>
                )}

                {/* Typing indicator */}
                {replying && (
                  <div className="flex gap-2 items-start">
                    <div className="w-6 h-6 rounded-full bg-[#4efa72] flex items-center justify-center text-[#0d1410] text-[10px] font-black flex-shrink-0">M</div>
                    <div className="bg-[#1e3a26] rounded-[12px_12px_12px_2px] px-3 py-2.5 flex items-center gap-1">
                      {[0, 1, 2].map((i) => (
                        <div
                          key={i}
                          className="w-1.5 h-1.5 rounded-full bg-[#4efa72] opacity-70"
                          style={{ animation: `pulse-green 1.2s ease-in-out ${i * 0.2}s infinite` }}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Bot reply */}
                {botMsg && !replying && (
                  <div className="flex gap-2 items-start">
                    <div className="w-6 h-6 rounded-full bg-[#4efa72] flex items-center justify-center text-[#0d1410] text-[10px] font-black flex-shrink-0">M</div>
                    <div className="bg-[#1e3a26] border border-[rgba(78,250,114,0.2)] text-[#f0fdf4] text-xs rounded-[12px_12px_12px_2px] px-3 py-2 max-w-[80%] leading-snug whitespace-pre-wrap">
                      {botMsg}
                      <p className="text-[#5d7a63] text-[9px] mt-1">10:24 AM</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Phone bottom bar */}
              <div className="bg-[#0d1410] border-t border-[#1e2d21] px-3 py-2 flex items-center gap-2">
                <div className="flex-1 bg-[#111a14] rounded-full px-3 py-1.5 text-[#5d7a63] text-[11px]">
                  Type a message...
                </div>
                <div className="w-7 h-7 rounded-full bg-[#4efa72] flex items-center justify-center text-[#0d1410] text-sm font-bold">➤</div>
              </div>
            </div>

            {/* Floating badges */}
            <div className="absolute -right-8 top-16 glass-card px-3 py-2 flex items-center gap-2 text-xs shadow-lg">
              <span className="text-[#4efa72]">🛒</span>
              <div>
                <p className="text-[#f0fdf4] font-semibold">Orders</p>
                <p className="text-[#5d7a63] text-[10px]">Automatic</p>
              </div>
            </div>
            <div className="absolute -right-8 top-40 glass-card px-3 py-2 flex items-center gap-2 text-xs shadow-lg">
              <span className="text-[#fbbf24]">₹</span>
              <div>
                <p className="text-[#f0fdf4] font-semibold">Payments</p>
                <p className="text-[#5d7a63] text-[10px]">Track</p>
              </div>
            </div>
            <div className="absolute -right-8 top-64 glass-card px-3 py-2 flex items-center gap-2 text-xs shadow-lg">
              <span className="text-[#60a5fa]">👥</span>
              <div>
                <p className="text-[#f0fdf4] font-semibold">Customers</p>
                <p className="text-[#5d7a63] text-[10px]">Yaad Rakho</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

