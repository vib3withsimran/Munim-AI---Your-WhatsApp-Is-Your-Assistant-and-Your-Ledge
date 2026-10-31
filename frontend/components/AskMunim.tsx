"use client";

import { useState } from "react";

const SUGGESTIONS = [
  "Show pending payments",
  "Best selling products this week",
  "Customers with dues > ₹3000",
  "Add new item to catalog",
];

export default function AskMunim() {
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponse(null);
    // Mock response — replace with real API call later
    await new Promise((r) => setTimeout(r, 900));
    setResponse(
      `Munim AI ne dhundha: "${query}" ke liye 3 results mile hain. Riya Sharma (₹4,200), Aditi Khanna (₹3,800), Sneha Mehta (₹2,480).`
    );
    setLoading(false);
  };

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
          placeholder="e.g. Show pending payments, best selling products, or add a new item to catalog..."
          className="flex-1 bg-transparent text-[#f0fdf4] text-sm placeholder:text-[#5d7a63] outline-none min-w-0"
        />
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || loading}
          className="w-8 h-8 rounded-lg bg-[#4efa72] disabled:bg-[#3acc5c]/40 hover:bg-[#3acc5c] transition-all flex items-center justify-center text-[#0d1410] flex-shrink-0"
        >
          {loading ? (
            <span className="animate-spin text-xs">⟳</span>
          ) : (
            <span className="text-sm">➤</span>
          )}
        </button>
      </div>

      {/* Quick suggestions */}
      {!response && (
        <div className="flex items-center gap-2 mt-3 flex-wrap">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => {
                setQuery(s);
              }}
              className="text-[11px] text-[#9db8a0] hover:text-[#4efa72] bg-[rgba(78,250,114,0.05)] hover:bg-[rgba(78,250,114,0.12)] border border-[rgba(78,250,114,0.1)] hover:border-[rgba(78,250,114,0.3)] px-2.5 py-1 rounded-full transition-all duration-200"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="mt-3 p-3 rounded-lg bg-[rgba(78,250,114,0.06)] border border-[rgba(78,250,114,0.15)]">
          <p className="text-sm text-[#f0fdf4]">{response}</p>
          <button
            onClick={() => setResponse(null)}
            className="text-xs text-[#5d7a63] hover:text-[#9db8a0] mt-2"
          >
            ✕ Clear
          </button>
        </div>
      )}
    </div>
  );
}

