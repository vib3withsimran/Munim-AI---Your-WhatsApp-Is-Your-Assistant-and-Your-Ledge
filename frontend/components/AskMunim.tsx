"use client";

import { useState } from "react";
import { Sparkles, Send, X, MessageCircle } from "lucide-react";
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
    setResponse(
      `Direct dashboard AI query is live on WhatsApp! You can send "${query}" directly to your Munim bot on WhatsApp to receive real-time answers.`
    );
  };

  const whatsappNumber = profile?.phone
    ? profile.phone.replace(/[^0-9]/g, "")
    : "14155238886";

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
          placeholder="e.g. Show pending payments, best selling products, or add a new item to catalog..."
          className="flex-1 bg-transparent text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/50 outline-none min-w-0"
        />

        {/* Send Button */}
        <button
          onClick={handleSubmit}
          disabled={!query.trim()}
          className="w-9 h-9 rounded-xl bg-[#B6F23C] hover:bg-[#c6f663] disabled:bg-[#B6F23C]/30 text-[#07110D] flex items-center justify-center transition-all flex-shrink-0 cursor-pointer shadow-[0_0_12px_rgba(182,242,60,0.3)] disabled:cursor-not-allowed"
          title="Send query"
          aria-label="Send query"
        >
          <Send className="w-4 h-4 fill-current ml-0.5" />
        </button>
      </div>

      {/* Quick Suggestions Chips */}
      {!response && (
        <div className="flex items-center gap-2 px-1 overflow-x-auto scrollbar-hide py-1">
          <span className="text-[11px] text-[#BAC8C1]/60 font-semibold whitespace-nowrap">
            Suggestions:
          </span>
          {QUICK_SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setQuery(s)}
              className="text-[11px] text-[#BAC8C1] hover:text-[#B6F23C] bg-[#10211A] hover:bg-[#162e24] border border-[#224430] hover:border-[#B6F23C]/40 px-3 py-1 rounded-full whitespace-nowrap transition-all cursor-pointer"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* WhatsApp Modal / Response Notice */}
      {response && (
        <div className="p-4 rounded-2xl bg-[#0B1A13] border border-[#B6F23C]/30 flex items-start justify-between gap-3 animate-in fade-in">
          <div>
            <p className="text-xs text-[#F0FDF4] leading-relaxed">{response}</p>
            <div className="mt-2.5 flex items-center gap-3">
              <a
                href={`https://wa.me/${whatsappNumber}?text=${encodeURIComponent(query)}`}
                target="_blank"
                rel="noopener noreferrer"
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
              </button>
            </div>
          </div>
          <button
            onClick={() => setResponse(null)}
            className="text-[#BAC8C1] hover:text-white p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

