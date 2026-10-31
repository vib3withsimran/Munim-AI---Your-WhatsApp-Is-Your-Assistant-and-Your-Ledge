"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

function SignupForm() {
  const { signup, user, loading: authLoading } = useAuth();

  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [businessType, setBusinessType] = useState("Clothing & Apparel");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationRequired, setVerificationRequired] = useState(false);

  // If already authenticated, redirect directly to dashboard
  useEffect(() => {
    if (!authLoading && user) {
      window.location.href = "/dashboard";
    }
  }, [user, authLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!businessName || !email || !password) {
      setError("Please fill in business name, email, and password.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);
    setError(null);

    const result = await signup(email, password, businessName, phone, businessType);

    setLoading(false);

    if (!result.success) {
      setError(result.error || "Signup failed. Please try again.");
    } else {
      if (result.verificationRequired) {
        setVerificationRequired(true);
      } else {
        window.location.href = "/dashboard";
      }
    }
  };

  return (
    <div className="w-full max-w-md mx-auto p-6">
      {/* Brand Header */}
      <div className="text-center mb-6">
        <Link href="/" className="inline-flex items-center gap-2.5 group mb-3">
          <div className="w-10 h-10 rounded-xl bg-[#4efa72] flex items-center justify-center text-[#0d1410] font-black text-base shadow-[0_0_15px_rgba(78,250,114,0.5)] group-hover:scale-105 transition-transform">
            M
          </div>
          <span className="font-bold text-[#f0fdf4] text-2xl tracking-tight">
            Munim AI
          </span>
        </Link>
        <h1 className="text-xl font-bold text-[#f0fdf4]">Start Your Digital Khata</h1>
        <p className="text-sm text-[#9db8a0] mt-1">
          Automate customer WhatsApp replies & ledger in minutes
        </p>
      </div>

      {/* Card */}
      <div className="glass-card p-6 sm:p-8 rounded-2xl border border-[rgba(78,250,114,0.15)] bg-[#0d1410]/90 backdrop-blur-xl shadow-2xl">
        {verificationRequired ? (
          /* Email Verification Notice */
          <div className="text-center py-4 space-y-4">
            <div className="w-16 h-16 rounded-full bg-[rgba(78,250,114,0.15)] border border-[rgba(78,250,114,0.3)] text-[#4efa72] text-3xl flex items-center justify-center mx-auto shadow-[0_0_20px_rgba(78,250,114,0.2)]">
              ✉️
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#f0fdf4]">Check Your Email</h2>
              <p className="text-xs text-[#9db8a0] mt-1 leading-relaxed">
                We sent a confirmation link to:
              </p>
              <p className="text-sm font-semibold text-[#4efa72] mt-0.5">{email}</p>
            </div>
            <div className="p-3.5 rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(78,250,114,0.1)] text-xs text-[#9db8a0] text-left leading-relaxed">
              <p className="font-semibold text-[#f0fdf4] mb-1">What&apos;s next?</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Click the confirmation link in your email.</li>
                <li>Your account will be activated instantly.</li>
                <li>Sign in with your email and password.</li>
              </ol>
            </div>
            <Link
              href="/login"
              className="inline-block w-full bg-[#4efa72] hover:bg-[#3acc5c] text-[#0d1410] font-bold text-sm py-2.5 rounded-xl transition-all cursor-pointer"
            >
              Go to Login Page →
            </Link>
          </div>
        ) : (
          /* Signup Form */
          <>
            {error && (
              <div className="mb-4 p-3.5 rounded-xl bg-[rgba(248,113,113,0.1)] border border-[rgba(248,113,113,0.3)] text-[#f87171] text-xs leading-relaxed flex items-center gap-2">
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-[#9db8a0] uppercase tracking-wider mb-1">
                  Business / Store Name *
                </label>
                <input
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="e.g. Neha's Boutique"
                  required
                  className="w-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] focus:border-[#4efa72] rounded-xl px-4 py-2 text-sm text-[#f0fdf4] placeholder:text-[#5d7a63] outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#9db8a0] uppercase tracking-wider mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seller@example.com"
                  required
                  autoComplete="email"
                  className="w-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] focus:border-[#4efa72] rounded-xl px-4 py-2 text-sm text-[#f0fdf4] placeholder:text-[#5d7a63] outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#9db8a0] uppercase tracking-wider mb-1">
                  Password (min. 6 characters) *
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={6}
                  autoComplete="new-password"
                  className="w-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] focus:border-[#4efa72] rounded-xl px-4 py-2 text-sm text-[#f0fdf4] placeholder:text-[#5d7a63] outline-none transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-[#9db8a0] uppercase tracking-wider mb-1">
                    WhatsApp Phone
                  </label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="919876543210"
                    className="w-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] focus:border-[#4efa72] rounded-xl px-3 py-2 text-sm text-[#f0fdf4] placeholder:text-[#5d7a63] outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-[#9db8a0] uppercase tracking-wider mb-1">
                    Business Type
                  </label>
                  <select
                    value={businessType}
                    onChange={(e) => setBusinessType(e.target.value)}
                    className="w-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] focus:border-[#4efa72] rounded-xl px-3 py-2 text-sm text-[#f0fdf4] outline-none transition-all"
                  >
                    <option value="Clothing & Apparel">Clothing & Apparel</option>
                    <option value="Jewelry & Accessories">Jewelry & Accessories</option>
                    <option value="Home Decor & Handcraft">Home Decor & Handcraft</option>
                    <option value="Food & Bakery">Food & Bakery</option>
                    <option value="Retail & Kirana">Retail & Kirana</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-3 bg-[#4efa72] hover:bg-[#3acc5c] disabled:bg-[#3acc5c]/40 text-[#0d1410] font-bold text-sm py-3 rounded-xl transition-all shadow-[0_0_15px_rgba(78,250,114,0.3)] hover:shadow-[0_0_25px_rgba(78,250,114,0.5)] active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-[#0d1410] border-t-transparent rounded-full animate-spin" />
                    <span>Creating Account...</span>
                  </>
                ) : (
                  <span>Register Store →</span>
                )}
              </button>
            </form>

            <div className="mt-5 pt-5 border-t border-[rgba(78,250,114,0.1)] text-center text-xs text-[#9db8a0]">
              Already have an account?{" "}
              <Link href="/login" className="text-[#4efa72] font-semibold hover:underline">
                Sign In
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-[#071410] text-[#f0fdf4] flex items-center justify-center py-12 px-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-[#4efa72]/10 rounded-full blur-3xl pointer-events-none" />
      <Suspense fallback={<div className="text-center text-[#9db8a0]">Loading...</div>}>
        <SignupForm />
      </Suspense>
    </div>
  );
}
