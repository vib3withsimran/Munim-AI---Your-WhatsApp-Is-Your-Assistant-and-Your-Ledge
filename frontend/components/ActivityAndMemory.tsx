"use client";

import { useEffect, useState } from "react";
import {
  MessageSquare,
  Package,
  CreditCard,
  Bell,
  Sparkles,
  User,
  Tag,
  TrendingUp,
  ChevronRight,
} from "lucide-react";
import { api, DashboardActivityResponse } from "@/lib/api";
import { MOCK_ACTIVITIES, MOCK_MEMORIES } from "@/lib/mocks/dashboard";

interface MemoryItem {
  text: string;
  meta: string;
  icon?: string;
  color?: string;
}

export default function ActivityAndMemory() {
  const [activities, setActivities] = useState(MOCK_ACTIVITIES);
  const [memories, setMemories] = useState<MemoryItem[]>(MOCK_MEMORIES);

  useEffect(() => {
    let isMounted = true;
    async function fetchActivity() {
      try {
        const res: DashboardActivityResponse = await api.getActivity();
        if (isMounted) {
          if (res?.activities && res.activities.length > 0) {
            setActivities(res.activities);
          }
          if (res?.memories && res.memories.length > 0) {
            setMemories(res.memories);
          }
        }
      } catch {
        // Fallback to rich mocks
      }
    }
    fetchActivity();
    return () => {
      isMounted = false;
    };
  }, []);

  const activityIcons: Record<string, React.ElementType> = {
    "New messages": MessageSquare,
    "Orders created": Package,
    "Payments received": CreditCard,
    "Dues reminders sent": Bell,
    "Memories updated": Sparkles,
  };

  const memoryIcons = [User, Tag, TrendingUp];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* 1. Today's Activity Card */}
      <div className="bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/40 rounded-3xl p-5 sm:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.35)] flex flex-col justify-between transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base sm:text-lg font-bold text-[#F0FDF4] tracking-tight">
            Today&apos;s Activity
          </h2>
          <span className="text-[11px] text-[#B6F23C] font-semibold bg-[#B6F23C]/10 border border-[#B6F23C]/20 px-2 py-0.5 rounded-full">
            Live
          </span>
        </div>

        <div className="space-y-3">
          {activities.map((item) => {
            const Icon = activityIcons[item.label] || MessageSquare;
            return (
              <div
                key={item.label}
                className="flex items-center justify-between gap-3 p-2 rounded-xl hover:bg-[#10211A] transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-[#10211A] border border-[#224430] flex items-center justify-center text-[#B6F23C] flex-shrink-0">
                    <Icon className="w-4 h-4 text-[#B6F23C]" />
                  </div>
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-sm font-black text-[#F0FDF4] tabular-nums">
                      {item.count}
                    </span>
                    <span className="text-xs text-[#BAC8C1] truncate">{item.label}</span>
                  </div>
                </div>

                <span className="text-xs font-bold text-[#B6F23C] bg-[#B6F23C]/15 border border-[#B6F23C]/25 px-2 py-0.5 rounded-md min-w-[32px] text-center">
                  {item.delta}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. AI Memory Highlights Card */}
      <div className="bg-[#0B1A13]/90 border border-[#224430] hover:border-[#B6F23C]/40 rounded-3xl p-5 sm:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.35)] flex flex-col justify-between transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base sm:text-lg font-bold text-[#F0FDF4] tracking-tight flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#B6F23C]" />
            <span>AI Memory Highlights</span>
          </h2>
          <ChevronRight className="w-4 h-4 text-[#BAC8C1]/60 hover:text-[#B6F23C] transition-colors cursor-pointer" />
        </div>

        <div className="space-y-3">
          {memories.map((m, i) => {
            const Icon = memoryIcons[i % memoryIcons.length];
            return (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded-2xl bg-[#10211A] border border-[#224430] hover:border-[#B6F23C]/35 transition-all"
              >
                <div className="w-7 h-7 rounded-full bg-[#B6F23C]/15 border border-[#B6F23C]/30 text-[#B6F23C] flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs sm:text-sm font-semibold text-[#F0FDF4] leading-snug">
                    {m.text}
                  </p>
                  <p className="text-[11px] text-[#BAC8C1]/70 mt-1">{m.meta}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
