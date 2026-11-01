"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import {
  Mail,
  AlertCircle,
  ArrowRight,
  Store,
  CheckCircle2,
} from "lucide-react";

function ForgotPasswordForm() {
  const { resetPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError("Please enter your registered email address.");
      return;
    }

    setSubmitting(true);
    setError(null);

    const result = await resetPassword(email);
    setSubmitting(false);

    if (!result.success) {
      setError(result.error || "Failed to dispatch reset email. Please try again.");
    } else {
      setSent(true);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto p-4 sm:p-6">
      {/* Main Glass Card */}
      <div className="relative bg-[#07130E]/95 border border-[#1C3B29] hover:border-[#B6F23C]/40 rounded-[28px] p-6 sm:p-8 shadow-[0_25px_70px_rgba(0,0,0,0.85),0_0_50px_rgba(182,242,60,0.12)] backdrop-blur-2xl transition-all overflow-hidden">
        {/* Top-Left Corner Glow */}
        <div className="absolute top-0 left-0 w-36 h-36 bg-gradient-to-br from-[#B6F23C]/20 to-transparent rounded-tl-[28px] pointer-events-none blur-xl" />

        {/* Brand Badge */}
        <div className="flex items-center justify-center gap-2 mb-4 relative z-10">
          <div className="w-8 h-8 rounded-xl bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black shadow-[0_0_14px_rgba(182,242,60,0.5)]">
            <Store className="w-4 h-4 stroke-[2.5]" />
          </div>
          <span className="font-extrabold text-[#F0FDF4] text-lg tracking-tight">
            Munim AI
          </span>
        </div>

        {/* Header */}
        <div className="text-center mb-6 relative z-10">
          <h1 className="text-2xl font-black text-[#F0FDF4] tracking-tight">
            Reset Password
          </h1>
          <p className="text-xs text-[#BAC8C1] mt-1.5 font-medium">
            Enter your email to receive password reset instructions
          </p>
        </div>

        {sent ? (
          /* Success Screen */
          <div className="text-center py-2 space-y-4 relative z-10 animate-in fade-in">
            <div className="w-14 h-14 rounded-full bg-[#B6F23C]/15 border border-[#B6F23C]/40 text-[#B6F23C] flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(182,242,60,0.25)]">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#F0FDF4]">Check Your Inbox</h2>
              <p className="text-xs text-[#BAC8C1] mt-1 leading-relaxed">
                If an account exists with <span className="text-[#B6F23C] font-semibold">{email}</span>, we have dispatched a password recovery link.
              </p>
            </div>
            <Link
              href="/login"
              className="inline-flex items-center justify-center gap-2 w-full bg-[#B6F23C] hover:bg-[#c4f64d] text-[#07110D] font-extrabold text-sm py-3.5 rounded-2xl transition-all shadow-[0_0_20px_rgba(182,242,60,0.35)] cursor-pointer"
            >
              <span>Return to Login</span>
              <ArrowRight className="w-4 h-4 stroke-[2.5]" />
            </Link>
          </div>
        ) : (
          /* Request Form */
          <form onSubmit={handleSubmit} className="space-y-4 relative z-10">
            {error && (
              <div className="p-3 rounded-2xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#F87171] text-xs leading-relaxed flex items-center gap-2.5 animate-in fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-[#BAC8C1] mb-1.5">
                Registered Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seller@example.com"
                  required
                  autoComplete="email"
                  disabled={submitting}
                  className="w-full bg-[#0B1E15]/90 border border-[#1E3E2B] focus:border-[#B6F23C] focus:ring-1 focus:ring-[#B6F23C]/50 rounded-2xl pl-11 pr-4 py-3.5 text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/50 outline-none transition-all disabled:opacity-50 min-h-[46px]"
                />
                <Mail className="w-4 h-4 text-[#BAC8C1]/60 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 bg-[#B6F23C] hover:bg-[#c4f64d] disabled:bg-[#B6F23C]/40 text-[#07110D] font-extrabold text-sm py-3.5 rounded-2xl transition-all shadow-[0_0_20px_rgba(182,242,60,0.35)] hover:shadow-[0_0_30px_rgba(182,242,60,0.55)] active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer min-h-[48px]"
            >
              {submitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-[#07110D] border-t-transparent rounded-full animate-spin" />
                  <span>Sending Link...</span>
                </>
              ) : (
                <>
                  <span>Send Reset Instructions</span>
                  <ArrowRight className="w-4 h-4 stroke-[2.5]" />
                </>
              )}
            </button>

            <div className="mt-5 text-center text-xs text-[#BAC8C1]">
              Remember your password?{" "}
              <Link href="/login" className="text-[#B6F23C] font-bold hover:underline ml-1">
                Back to Login
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-screen bg-[#07110D] text-[#F0FDF4] flex items-center justify-center py-8 sm:py-12 px-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 w-[550px] h-[550px] bg-[#B6F23C]/10 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[450px] h-[450px] bg-[#10B981]/10 rounded-full blur-[150px] pointer-events-none" />
      <Suspense fallback={<div className="text-center text-[#BAC8C1]">Loading...</div>}>
        <ForgotPasswordForm />
      </Suspense>
    </div>
  );
}

