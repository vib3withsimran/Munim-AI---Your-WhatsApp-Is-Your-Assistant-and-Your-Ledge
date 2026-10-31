"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

function LoginForm() {
  const searchParams = useSearchParams();
  const { login, user, loading: authLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationNotice, setVerificationNotice] = useState<string | null>(null);

  // If already authenticated and done loading, redirect directly to dashboard
  useEffect(() => {
    if (!authLoading && user) {
      const redirect = searchParams.get("redirect") || "/dashboard";
      window.location.href = redirect;
    }
  }, [user, authLoading, searchParams]);

  // Read error parameter from URL if redirected
  useEffect(() => {
    const errorParam = searchParams.get("error");
    if (errorParam) {
      setError(errorParam);
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setVerificationNotice(null);

    try {
      const result = await login(email, password);

      if (!result.success) {
        if (result.verificationRequired) {
          setVerificationNotice(
            result.error ||
              "Email verification required. Please check your inbox and verify your email before logging in."
          );
        } else {
          setError(result.error || "Failed to log in. Please check your credentials.");
        }
        setSubmitting(false);
      } else {
        // Successful login: perform full browser redirect to ensure all session cookies are sent
        const redirect = searchParams.get("redirect") || "/dashboard";
        window.location.href = redirect;
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An unexpected login error occurred";
      setError(msg);
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto p-6">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <Link href="/" className="inline-flex items-center gap-2.5 group mb-4">
          <div className="w-10 h-10 rounded-xl bg-[#4efa72] flex items-center justify-center text-[#0d1410] font-black text-base shadow-[0_0_15px_rgba(78,250,114,0.5)] group-hover:scale-105 transition-transform">
            M
          </div>
          <span className="font-bold text-[#f0fdf4] text-2xl tracking-tight">
            Munim AI
          </span>
        </Link>
        <h1 className="text-xl font-bold text-[#f0fdf4]">Welcome back to your Khata</h1>
        <p className="text-sm text-[#9db8a0] mt-1">
          Login to access your automated assistant, orders & customer ledger
        </p>
      </div>

      {/* Login Card */}
      <div className="glass-card p-6 sm:p-8 rounded-2xl border border-[rgba(78,250,114,0.15)] bg-[#0d1410]/90 backdrop-blur-xl shadow-2xl">
        {/* Verification Warning Alert */}
        {verificationNotice && (
          <div className="mb-5 p-4 rounded-xl bg-[rgba(251,191,36,0.1)] border border-[rgba(251,191,36,0.3)] text-[#fbbf24] text-xs leading-relaxed flex items-start gap-3 animate-in fade-in">
            <span className="text-base flex-shrink-0">✉️</span>
            <div>
              <p className="font-semibold text-sm mb-1">Verify Your Email</p>
              <p>{verificationNotice}</p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="mb-5 p-3.5 rounded-xl bg-[rgba(248,113,113,0.1)] border border-[rgba(248,113,113,0.3)] text-[#f87171] text-xs leading-relaxed flex items-center gap-2 animate-in fade-in">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[#9db8a0] uppercase tracking-wider mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seller@example.com"
              required
              autoComplete="email"
              disabled={submitting}
              className="w-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] focus:border-[#4efa72] rounded-xl px-4 py-2.5 text-sm text-[#f0fdf4] placeholder:text-[#5d7a63] outline-none transition-all disabled:opacity-50"
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-semibold text-[#9db8a0] uppercase tracking-wider">
                Password
              </label>
            </div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
              disabled={submitting}
              className="w-full bg-[#161e19] border border-[rgba(78,250,114,0.15)] focus:border-[#4efa72] rounded-xl px-4 py-2.5 text-sm text-[#f0fdf4] placeholder:text-[#5d7a63] outline-none transition-all disabled:opacity-50"
            />
          </div>

          <button
            type="submit"
            disabled={submitting || authLoading}
            className="w-full mt-2 bg-[#4efa72] hover:bg-[#3acc5c] disabled:bg-[#3acc5c]/40 text-[#0d1410] font-bold text-sm py-3 rounded-xl transition-all shadow-[0_0_15px_rgba(78,250,114,0.3)] hover:shadow-[0_0_25px_rgba(78,250,114,0.5)] active:scale-[0.98] flex items-center justify-center gap-2 cursor-pointer"
          >
            {submitting ? (
              <>
                <span className="w-4 h-4 border-2 border-[#0d1410] border-t-transparent rounded-full animate-spin" />
                <span>Signing in...</span>
              </>
            ) : (
              <span>Sign In to Dashboard →</span>
            )}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-[rgba(78,250,114,0.1)] text-center text-xs text-[#9db8a0]">
          Don&apos;t have a seller account yet?{" "}
          <Link
            href="/signup"
            className="text-[#4efa72] font-semibold hover:underline"
          >
            Create Seller Account
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-[#071410] text-[#f0fdf4] flex items-center justify-center py-12 px-4 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-[#4efa72]/10 rounded-full blur-3xl pointer-events-none" />
      <Suspense fallback={<div className="text-center text-[#9db8a0]">Loading...</div>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
