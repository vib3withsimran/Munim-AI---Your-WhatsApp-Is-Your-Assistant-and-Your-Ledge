"use client";

import { useState } from "react";
<<<<<<< Updated upstream
import { Sparkles, Send, X, MessageCircle } from "lucide-react";
=======
>>>>>>> Stashed changes
import { useAuth } from "@/context/AuthContext";

const QUICK_SUGGESTIONS = [
  "Show pending payments",
  "Best selling products this week",
  "Customers with dues > ₹3000",
  "Add new item to catalog",
];

export default function AskMunim() {
  const { profile } = useAuth();
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<string | null>(null);

  const handleSubmit = () => {
    if (!query.trim()) return;
<<<<<<< Updated upstream
    setResponse(
      `Direct dashboard AI query is live on WhatsApp! You can send "${query}" directly to your Munim bot on WhatsApp to receive real-time answers.`
    );
  };

  const whatsappNumber = profile?.phone
    ? profile.phone.replace(/[^0-9]/g, "")
    : "14155238886";
=======
    // Transparent state per Phase 4: no fabricated AI queries
    setResponse(
      `Direct dashboard AI query is pending backend /chat endpoint integration. Your assistant is live on WhatsApp — you can send "${query}" directly to your Munim bot on WhatsApp to get real-time answers!`
    );
  };

  const whatsappNumber = profile?.phone ? profile.phone.replace(/[^0-9]/g, "") : "14155238886";
>>>>>>> Stashed changes

  return (
    <div className="w-full space-y-2">
      {/* Ask Munim AI Command Input */}
      <div className="bg-[#0B1A13]/95 border-2 border-[#224430] hover:border-[#B6F23C]/40 rounded-2xl p-2.5 sm:p-3 flex items-center gap-3 shadow-[0_15px_40px_rgba(0,0,0,0.6),0_0_20px_rgba(182,242,60,0.08)] backdrop-blur-xl transition-all">
        {/* Left Badge */}
        <div className="flex items-center gap-2 bg-[#B6F23C]/15 border border-[#B6F23C]/30 text-[#B6F23C] px-3.5 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap flex-shrink-0 shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-[#B6F23C]" />
          <span>Ask Munim AI</span>
        </div>

        {/* Input */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
<<<<<<< Updated upstream
          placeholder="e.g. Show pending payments, best selling products, or add a new item to catalog..."
          className="flex-1 bg-transparent text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/50 outline-none min-w-0"
=======
          placeholder="Ask Munim AI: e.g. Show pending payments, best selling products, or check customer dues..."
          className="flex-1 bg-transparent text-[#f0fdf4] text-sm placeholder:text-[#5d7a63] outline-none min-w-0"
>>>>>>> Stashed changes
        />

        {/* Send Button */}
        <button
          onClick={handleSubmit}
          disabled={!query.trim()}
<<<<<<< Updated upstream
          className="w-9 h-9 rounded-xl bg-[#B6F23C] hover:bg-[#c6f663] disabled:bg-[#B6F23C]/30 text-[#07110D] flex items-center justify-center transition-all flex-shrink-0 cursor-pointer shadow-[0_0_12px_rgba(182,242,60,0.3)] disabled:cursor-not-allowed"
          title="Send query"
          aria-label="Send query"
        >
          <Send className="w-4 h-4 fill-current ml-0.5" />
=======
          className="w-8 h-8 rounded-lg bg-[#4efa72] disabled:bg-[#3acc5c]/40 hover:bg-[#3acc5c] transition-all flex items-center justify-center text-[#0d1410] flex-shrink-0 cursor-pointer"
          title="Submit inquiry"
        >
          <span className="text-sm">➤</span>
>>>>>>> Stashed changes
        </button>
      </div>

      {/* Quick Suggestions Chips */}
      {!response && (
<<<<<<< Updated upstream
        <div className="flex items-center gap-2 px-1 overflow-x-auto scrollbar-hide py-1">
          <span className="text-[11px] text-[#BAC8C1]/60 font-semibold whitespace-nowrap">
            Suggestions:
          </span>
          {QUICK_SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setQuery(s)}
              className="text-[11px] text-[#BAC8C1] hover:text-[#B6F23C] bg-[#10211A] hover:bg-[#162e24] border border-[#224430] hover:border-[#B6F23C]/40 px-3 py-1 rounded-full whitespace-nowrap transition-all cursor-pointer"
=======
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <span className="text-[11px] text-[#5d7a63] mr-1">Suggestions:</span>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => {
                setQuery(s);
              }}
              className="text-[11px] text-[#9db8a0] hover:text-[#4efa72] bg-[rgba(78,250,114,0.05)] hover:bg-[rgba(78,250,114,0.12)] border border-[rgba(78,250,114,0.1)] hover:border-[rgba(78,250,114,0.3)] px-2.5 py-1 rounded-full transition-all duration-200 cursor-pointer"
>>>>>>> Stashed changes
            >
              {s}
            </button>
          ))}
        </div>
      )}

<<<<<<< Updated upstream
      {/* WhatsApp Modal / Response Notice */}
      {response && (
        <div className="p-4 rounded-2xl bg-[#0B1A13] border border-[#B6F23C]/30 flex items-start justify-between gap-3 animate-in fade-in">
          <div>
            <p className="text-xs text-[#F0FDF4] leading-relaxed">{response}</p>
            <div className="mt-2.5 flex items-center gap-3">
=======
      {/* Response / Integration Notice */}
      {response && (
        <div className="mt-3 p-3.5 rounded-lg bg-[rgba(78,250,114,0.06)] border border-[rgba(78,250,114,0.2)] flex items-start justify-between gap-3 animate-in fade-in">
          <div>
            <p className="text-xs text-[#f0fdf4] leading-relaxed">{response}</p>
            <div className="mt-2 flex items-center gap-3">
>>>>>>> Stashed changes
              <a
                href={`https://wa.me/${whatsappNumber}?text=${encodeURIComponent(query)}`}
                target="_blank"
                rel="noopener noreferrer"
<<<<<<< Updated upstream
                className="text-xs bg-[#25D366] text-[#07110D] font-bold px-3.5 py-1.5 rounded-full inline-flex items-center gap-1.5 shadow-sm hover:brightness-105"
              >
                <MessageCircle className="w-3.5 h-3.5" />
                <span>Ask on WhatsApp</span>
              </a>
              <button
                onClick={() => setResponse(null)}
                className="text-xs text-[#BAC8C1] hover:text-white"
              >
                Dismiss
=======
                className="text-xs bg-[#25D366] hover:bg-[#20ba5a] text-[#071410] font-bold px-3 py-1 rounded-md transition-colors inline-flex items-center gap-1.5"
              >
                <span>📱 Ask on WhatsApp</span>
              </a>
              <button
                onClick={() => setResponse(null)}
                className="text-xs text-[#5d7a63] hover:text-[#9db8a0]"
              >
                Clear
>>>>>>> Stashed changes
              </button>
            </div>
          </div>
          <button
            onClick={() => setResponse(null)}
<<<<<<< Updated upstream
            className="text-[#BAC8C1] hover:text-white p-1"
          >
            <X className="w-4 h-4" />
=======
            className="text-xs text-[#5d7a63] hover:text-[#9db8a0]"
          >
            ✕
>>>>>>> Stashed changes
          </button>
        </div>
      )}
    </div>
  );
}
