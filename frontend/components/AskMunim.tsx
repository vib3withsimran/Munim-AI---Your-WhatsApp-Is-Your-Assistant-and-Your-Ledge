"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

const SUGGESTIONS = [
  "Show pending payments",
  "Best selling products this week",
  "Customers with dues > ₹3000",
  "Add new item to catalog",
];

export default function AskMunim() {
  const { profile } = useAuth();
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const [response, setResponse] = useState<string | null>(null);

  const handleSubmit = () => {
    if (!query.trim()) return;
    // Transparent state per Phase 4: no fabricated AI queries
    setResponse(
      `Direct dashboard AI query is pending backend /chat endpoint integration. Your assistant is live on WhatsApp — you can send "${query}" directly to your Munim bot on WhatsApp to get real-time answers!`
    );
  };

  const whatsappNumber = profile?.phone ? profile.phone.replace(/[^0-9]/g, "") : "14155238886";

  return (
    <div className="glass-card p-4">
      <div
        className={`flex items-center gap-3 rounded-xl border transition-all duration-300 px-4 py-3 ${
          focused
            ? "border-[rgba(78,250,114,0.4)] shadow-[0_0_20px_rgba(78,250,114,0.15)]"
            : "border-[rgba(78,250,114,0.15)]"
        } bg-[#0d1410]`}
      >
        <span className="text-[#4efa72] text-lg flex-shrink-0">✨</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Ask Munim AI: e.g. Show pending payments, best selling products, or check customer dues..."
          className="flex-1 bg-transparent text-[#f0fdf4] text-sm placeholder:text-[#5d7a63] outline-none min-w-0"
        />
        <button
          onClick={handleSubmit}
          disabled={!query.trim()}
          className="w-8 h-8 rounded-lg bg-[#4efa72] disabled:bg-[#3acc5c]/40 hover:bg-[#3acc5c] transition-all flex items-center justify-center text-[#0d1410] flex-shrink-0 cursor-pointer"
          title="Submit inquiry"
        >
          <span className="text-sm">➤</span>
        </button>
      </div>

      {/* Quick suggestions */}
      {!response && (
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          <span className="text-[11px] text-[#5d7a63] mr-1">Suggestions:</span>
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => {
                setQuery(s);
              }}
              className="text-[11px] text-[#9db8a0] hover:text-[#4efa72] bg-[rgba(78,250,114,0.05)] hover:bg-[rgba(78,250,114,0.12)] border border-[rgba(78,250,114,0.1)] hover:border-[rgba(78,250,114,0.3)] px-2.5 py-1 rounded-full transition-all duration-200 cursor-pointer"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Response / Integration Notice */}
      {response && (
        <div className="mt-3 p-3.5 rounded-lg bg-[rgba(78,250,114,0.06)] border border-[rgba(78,250,114,0.2)] flex items-start justify-between gap-3 animate-in fade-in">
          <div>
            <p className="text-xs text-[#f0fdf4] leading-relaxed">{response}</p>
            <div className="mt-2 flex items-center gap-3">
              <a
                href={`https://wa.me/${whatsappNumber}?text=${encodeURIComponent(query)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs bg-[#25D366] hover:bg-[#20ba5a] text-[#071410] font-bold px-3 py-1 rounded-md transition-colors inline-flex items-center gap-1.5"
              >
                <span>📱 Ask on WhatsApp</span>
              </a>
              <button
                onClick={() => setResponse(null)}
                className="text-xs text-[#5d7a63] hover:text-[#9db8a0]"
              >
                Clear
              </button>
            </div>
          </div>
          <button
            onClick={() => setResponse(null)}
            className="text-xs text-[#5d7a63] hover:text-[#9db8a0]"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
