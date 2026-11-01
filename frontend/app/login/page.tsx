"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  Store,
} from "lucide-react";
import { AuthIllustration } from "@/components/auth/AuthIllustration";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, user, loading: authLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationNotice, setVerificationNotice] = useState<string | null>(null);

  // Derived error from URL query params or form state
  const urlError = searchParams.get("error");
  const activeError = error || urlError;

  useEffect(() => {
    if (!authLoading && user) {
      const redirect = searchParams.get("redirect") || "/dashboard";
      router.push(redirect);
    }
  }, [user, authLoading, searchParams, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
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
        const redirect = searchParams.get("redirect") || "/dashboard";
        router.push(redirect);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "An unexpected login error occurred";
      setError(msg);
      setSubmitting(false);
    }
  };

  const handleWhatsAppLogin = () => {
    window.open(
      "https://wa.me/919876543210?text=Hi%20Munim%20AI%2C%20I%20want%20to%20login%20to%20my%20account",
      "_blank"
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Main Glass Card with Glowing Rim & Top-Left Corner Arc */}
      <div className="relative bg-[#07130E]/95 border border-[#1C3B29] hover:border-[#B6F23C]/40 rounded-[28px] sm:rounded-[36px] p-6 sm:p-10 lg:p-12 shadow-[0_25px_70px_rgba(0,0,0,0.85),0_0_50px_rgba(182,242,60,0.12)] backdrop-blur-2xl transition-all overflow-hidden">
        {/* Top-Left Neon Arc Glow Effect */}
        <div className="absolute top-0 left-0 w-44 h-44 bg-gradient-to-br from-[#B6F23C]/25 via-[#22C55E]/10 to-transparent rounded-tl-[36px] pointer-events-none blur-2xl" />
        <div className="absolute -top-[1px] -left-[1px] w-36 h-36 border-t-2 border-l-2 border-[#B6F23C]/70 rounded-tl-[36px] pointer-events-none shadow-[0_0_15px_rgba(182,242,60,0.4)]" />

        {/* Ambient Bottom Right Glow */}
        <div className="absolute -bottom-10 -right-10 w-48 h-48 bg-[#10B981]/15 rounded-full blur-3xl pointer-events-none" />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center relative z-10">
          {/* Left Column: 3D Store Illustration + 4 Checklist Items */}
          <div className="lg:col-span-5 flex flex-col items-center justify-center order-2 lg:order-1 pt-2 lg:pt-0">
            <AuthIllustration type="login" />
          </div>

          {/* Right Column: Brand Badge, Header, Form, and Social */}
          <div className="lg:col-span-7 flex flex-col justify-center order-1 lg:order-2">
            {/* Munim AI Brand Badge */}
            <div className="flex items-center justify-center lg:justify-start gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-xl bg-[#B6F23C] flex items-center justify-center text-[#07110D] font-black shadow-[0_0_14px_rgba(182,242,60,0.5)]">
                <Store className="w-4 h-4 stroke-[2.5]" />
              </div>
              <span className="font-extrabold text-[#F0FDF4] text-lg tracking-tight">
                Munim AI
              </span>
            </div>

            {/* Heading & Subtitle */}
            <div className="text-center lg:text-left mb-6">
              <h1 className="text-2xl sm:text-3xl font-black text-[#F0FDF4] tracking-tight flex items-center justify-center lg:justify-start gap-2">
                <span>Welcome</span>
                <span className="text-[#B6F23C]">Back</span>
                <span>👋</span>
              </h1>
              <p className="text-xs sm:text-sm text-[#BAC8C1] mt-1.5 font-medium">
                Login to your business account
              </p>
            </div>

            {/* Error & Notice Banners */}
            {verificationNotice && (
              <div className="mb-4 p-3.5 rounded-2xl bg-[#F59E0B]/10 border border-[#F59E0B]/30 text-[#F59E0B] text-xs leading-relaxed flex items-start gap-3 animate-in fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-xs mb-0.5">Verify Your Email</p>
                  <p className="text-[#BAC8C1]">{verificationNotice}</p>
                </div>
              </div>
            )}

            {activeError && (
              <div className="mb-4 p-3 rounded-2xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#F87171] text-xs leading-relaxed flex items-center gap-2.5 animate-in fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{activeError}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email Input */}
              <div>
                <label className="block text-xs font-semibold text-[#BAC8C1] mb-1.5">
                  Email Address
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

              {/* Password Input with Eye Toggle */}
              <div>
                <label className="block text-xs font-semibold text-[#BAC8C1] mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    autoComplete="current-password"
                    disabled={submitting}
                    className="w-full bg-[#0B1E15]/90 border border-[#1E3E2B] focus:border-[#B6F23C] focus:ring-1 focus:ring-[#B6F23C]/50 rounded-2xl pl-11 pr-11 py-3.5 text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/50 outline-none transition-all disabled:opacity-50 min-h-[46px]"
                  />
                  <Lock className="w-4 h-4 text-[#BAC8C1]/60 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#BAC8C1]/60 hover:text-[#F0FDF4] p-1 transition-colors focus:outline-none"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Remember Me & Forgot Password Row */}
              <div className="flex items-center justify-between text-xs pt-0.5">
                <label className="flex items-center gap-2 cursor-pointer select-none text-[#BAC8C1] hover:text-[#F0FDF4] transition-colors">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded bg-[#0B1E15] border-[#1E3E2B] text-[#B6F23C] accent-[#B6F23C] focus:ring-0 cursor-pointer"
                  />
                  <span className="font-medium">Remember me</span>
                </label>
                <Link
                  href="/forgot-password"
                  className="text-[#BAC8C1] hover:text-[#B6F23C] transition-colors font-medium"
                >
                  Forgot Password?
                </Link>
              </div>

              {/* Login Button */}
              <button
                type="submit"
                disabled={submitting || authLoading}
                className="w-full mt-2 bg-[#B6F23C] hover:bg-[#c4f64d] disabled:bg-[#B6F23C]/40 text-[#07110D] font-extrabold text-sm py-3.5 rounded-2xl transition-all shadow-[0_0_20px_rgba(182,242,60,0.35)] hover:shadow-[0_0_30px_rgba(182,242,60,0.55)] active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer min-h-[48px]"
              >
                {submitting ? (
                  <>
                    <span className="w-4 h-4 border-2 border-[#07110D] border-t-transparent rounded-full animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  <>
                    <span>Login</span>
                    <ArrowRight className="w-4 h-4 stroke-[2.5]" />
                  </>
                )}
              </button>
            </form>

            {/* Divider: ── or ── */}
            <div className="relative my-5 flex items-center justify-center">
              <div className="w-full border-t border-[#1C3B29]" />
              <span className="bg-[#07130E] px-3 text-xs text-[#BAC8C1]/60 uppercase tracking-widest font-semibold absolute">
                or
              </span>
            </div>

            {/* WhatsApp CTA Button */}
            <button
              type="button"
              onClick={handleWhatsAppLogin}
              className="w-full bg-[#0B1E15] hover:bg-[#11291E] border border-[#224430] hover:border-[#25D366]/60 text-[#F0FDF4] font-semibold text-xs sm:text-sm py-3 rounded-2xl transition-all flex items-center justify-center gap-2.5 shadow-sm active:scale-[0.99] cursor-pointer min-h-[44px]"
            >
              <svg className="w-4 h-4 fill-[#25D366]" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766.001-3.187-2.575-5.77-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.006c.106.005.249-.04.39.298.144.347.491 1.2.534 1.287.043.087.072.188.014.303-.058.116-.087.188-.173.289l-.26.303c-.087.087-.177.181-.076.355.101.173.449.741.964 1.201.662.591 1.221.774 1.394.861.174.087.275.072.376-.043.101-.116.433-.506.549-.68.116-.173.231-.144.39-.087s1.011.477 1.184.564.289.13.332.202c.043.073.043.419-.101.824z" />
              </svg>
              <span>Continue with WhatsApp</span>
            </button>

            {/* Footer Link */}
            <div className="mt-5 text-center text-xs text-[#BAC8C1]">
              Don&apos;t have an account?{" "}
              <Link
                href="/signup"
                className="text-[#B6F23C] font-bold hover:underline ml-1"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-[#07110D] text-[#F0FDF4] flex items-center justify-center py-8 sm:py-12 px-4 relative overflow-hidden">
      {/* Background Radial Green Glows */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 w-[550px] h-[550px] bg-[#B6F23C]/10 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[450px] h-[450px] bg-[#10B981]/10 rounded-full blur-[150px] pointer-events-none" />
      <Suspense fallback={<div className="text-center text-[#BAC8C1]">Loading...</div>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
