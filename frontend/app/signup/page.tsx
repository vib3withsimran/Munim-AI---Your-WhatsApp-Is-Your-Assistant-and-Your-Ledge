"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  Store,
  User,
  Phone,
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import { AuthIllustration } from "@/components/auth/AuthIllustration";

function SignupForm() {
  const router = useRouter();
  const { signup, user, loading: authLoading } = useAuth();

  const [businessName, setBusinessName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationRequired, setVerificationRequired] = useState(false);

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (!authLoading && user) {
      router.push("/dashboard");
    }
  }, [user, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Form Validations
    if (!businessName.trim()) {
      setError("Please enter your business or store name.");
      return;
    }

    if (!email.trim()) {
      setError("Please enter a valid email address.");
      return;
    }

    if (!password) {
      setError("Please enter a password.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please re-enter.");
      return;
    }

    setSubmitting(true);

    try {
      const cleanPhone = phone ? phone.replace(/\D/g, "") : undefined;
      const formattedPhone = cleanPhone ? `+91${cleanPhone}` : undefined;

      const result = await signup(
        email,
        password,
        businessName,
        ownerName || undefined,
        formattedPhone
      );

      setSubmitting(false);

      if (!result.success) {
        setError(result.error || "Signup failed. Please try again.");
      } else {
        if (result.verificationRequired) {
          setVerificationRequired(true);
        } else {
          router.push("/dashboard");
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Signup failed";
      setError(msg);
      setSubmitting(false);
    }
  };

  const handleWhatsAppSignup = () => {
    window.open(
      "https://wa.me/919876543210?text=Hi%20Munim%20AI%2C%20I%20want%20to%20create%20my%20account",
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
          {/* Left Column: 3D Store Illustration + 3 Feature Badges */}
          <div className="lg:col-span-5 flex flex-col items-center justify-center order-2 lg:order-1 pt-2 lg:pt-0">
            <AuthIllustration type="signup" />
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
            <div className="text-center lg:text-left mb-5">
              <h1 className="text-2xl sm:text-3xl font-black text-[#F0FDF4] tracking-tight flex items-center justify-center lg:justify-start gap-2">
                <span>Create Your</span>
                <span className="text-[#B6F23C]">Account</span>
                <span>🚀</span>
              </h1>
              <p className="text-xs sm:text-sm text-[#BAC8C1] mt-1.5 font-medium">
                Get started with Munim AI in just a few steps
              </p>
            </div>

            {verificationRequired ? (
              /* Email Verification Required View */
              <div className="text-center py-4 space-y-4 animate-in fade-in">
                <div className="w-16 h-16 rounded-full bg-[#B6F23C]/15 border-2 border-[#B6F23C]/40 text-[#B6F23C] text-3xl flex items-center justify-center mx-auto shadow-[0_0_25px_rgba(182,242,60,0.25)]">
                  <Mail className="w-8 h-8" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-[#F0FDF4]">Check Your Email</h2>
                  <p className="text-xs text-[#BAC8C1] mt-1 leading-relaxed">
                    We sent a confirmation link to activate your seller account:
                  </p>
                  <p className="text-sm font-bold text-[#B6F23C] mt-1 break-all">
                    {email}
                  </p>
                </div>
                <div className="p-4 rounded-2xl bg-[#0B1E15] border border-[#1E3E2B] text-xs text-[#BAC8C1] text-left leading-relaxed space-y-2">
                  <p className="font-bold text-[#F0FDF4] flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-[#B6F23C]" />
                    <span>Next steps to get started:</span>
                  </p>
                  <ol className="list-decimal list-inside space-y-1 text-[#BAC8C1]">
                    <li>Click the confirmation link in your email.</li>
                    <li>Your WhatsApp Dukaan will be activated.</li>
                    <li>Sign in and access your automated ledger!</li>
                  </ol>
                </div>
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center gap-2 w-full bg-[#B6F23C] hover:bg-[#c4f64d] text-[#07110D] font-extrabold text-sm py-3.5 rounded-2xl transition-all shadow-[0_0_20px_rgba(182,242,60,0.35)] cursor-pointer"
                >
                  <span>Go to Login</span>
                  <ArrowRight className="w-4 h-4 stroke-[2.5]" />
                </Link>
              </div>
            ) : (
              <>
                {/* Error Banner */}
                {error && (
                  <div className="mb-4 p-3 rounded-2xl bg-[#EF4444]/10 border border-[#EF4444]/30 text-[#F87171] text-xs leading-relaxed flex items-center gap-2.5 animate-in fade-in">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Form Fields */}
                <form onSubmit={handleSubmit} className="space-y-3">
                  {/* Field 1: Business Name */}
                  <div>
                    <label className="block text-xs font-semibold text-[#BAC8C1] mb-1">
                      Business Name *
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        value={businessName}
                        onChange={(e) => setBusinessName(e.target.value)}
                        placeholder="e.g. Gupta General Store"
                        required
                        disabled={submitting}
                        className="w-full bg-[#0B1E15]/90 border border-[#1E3E2B] focus:border-[#B6F23C] focus:ring-1 focus:ring-[#B6F23C]/50 rounded-2xl pl-11 pr-4 py-2.5 text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/40 outline-none transition-all disabled:opacity-50 min-h-[44px]"
                      />
                      <Store className="w-4 h-4 text-[#BAC8C1]/60 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>

                  {/* Field 2: Owner Name */}
                  <div>
                    <label className="block text-xs font-semibold text-[#BAC8C1] mb-1">
                      Your Name
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        value={ownerName}
                        onChange={(e) => setOwnerName(e.target.value)}
                        placeholder="e.g. Neha Gupta"
                        disabled={submitting}
                        className="w-full bg-[#0B1E15]/90 border border-[#1E3E2B] focus:border-[#B6F23C] focus:ring-1 focus:ring-[#B6F23C]/50 rounded-2xl pl-11 pr-4 py-2.5 text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/40 outline-none transition-all disabled:opacity-50 min-h-[44px]"
                      />
                      <User className="w-4 h-4 text-[#BAC8C1]/60 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>

                  {/* Field 3: Email */}
                  <div>
                    <label className="block text-xs font-semibold text-[#BAC8C1] mb-1">
                      Email Address *
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
                        className="w-full bg-[#0B1E15]/90 border border-[#1E3E2B] focus:border-[#B6F23C] focus:ring-1 focus:ring-[#B6F23C]/50 rounded-2xl pl-11 pr-4 py-2.5 text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/40 outline-none transition-all disabled:opacity-50 min-h-[44px]"
                      />
                      <Mail className="w-4 h-4 text-[#BAC8C1]/60 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    </div>
                  </div>

                  {/* Field 4: WhatsApp Phone Number (Optional) */}
                  <div>
                    <label className="block text-xs font-semibold text-[#BAC8C1] mb-1">
                      WhatsApp Phone Number
                    </label>
                    <div className="relative flex items-center">
                      <div className="absolute left-3.5 flex items-center gap-1.5 pointer-events-none text-[#BAC8C1]/70 text-xs font-bold">
                        <Phone className="w-3.5 h-3.5" />
                        <span>+91</span>
                        <div className="h-3 w-[1px] bg-[#1E3E2B] ml-1" />
                      </div>
                      <input
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="9876543210"
                        disabled={submitting}
                        className="w-full bg-[#0B1E15]/90 border border-[#1E3E2B] focus:border-[#B6F23C] focus:ring-1 focus:ring-[#B6F23C]/50 rounded-2xl pl-20 pr-4 py-2.5 text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/40 outline-none transition-all disabled:opacity-50 min-h-[44px]"
                      />
                    </div>
                  </div>

                  {/* Fields 5 & 6: Password & Confirm Password (2-col grid) */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {/* Password */}
                    <div>
                      <label className="block text-xs font-semibold text-[#BAC8C1] mb-1">
                        Password *
                      </label>
                      <div className="relative">
                        <input
                          type={showPassword ? "text" : "password"}
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="Min 6 chars"
                          required
                          minLength={6}
                          autoComplete="new-password"
                          disabled={submitting}
                          className="w-full bg-[#0B1E15]/90 border border-[#1E3E2B] focus:border-[#B6F23C] focus:ring-1 focus:ring-[#B6F23C]/50 rounded-2xl pl-10 pr-9 py-2.5 text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/40 outline-none transition-all disabled:opacity-50 min-h-[44px]"
                        />
                        <Lock className="w-3.5 h-3.5 text-[#BAC8C1]/60 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#BAC8C1]/60 hover:text-[#F0FDF4] p-1 transition-colors focus:outline-none"
                          aria-label={showPassword ? "Hide password" : "Show password"}
                        >
                          {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>

                    {/* Confirm Password */}
                    <div>
                      <label className="block text-xs font-semibold text-[#BAC8C1] mb-1">
                        Confirm Password *
                      </label>
                      <div className="relative">
                        <input
                          type={showConfirmPassword ? "text" : "password"}
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          placeholder="Re-enter password"
                          required
                          minLength={6}
                          autoComplete="new-password"
                          disabled={submitting}
                          className="w-full bg-[#0B1E15]/90 border border-[#1E3E2B] focus:border-[#B6F23C] focus:ring-1 focus:ring-[#B6F23C]/50 rounded-2xl pl-10 pr-9 py-2.5 text-sm text-[#F0FDF4] placeholder:text-[#BAC8C1]/40 outline-none transition-all disabled:opacity-50 min-h-[44px]"
                        />
                        <Lock className="w-3.5 h-3.5 text-[#BAC8C1]/60 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[#BAC8C1]/60 hover:text-[#F0FDF4] p-1 transition-colors focus:outline-none"
                          aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                        >
                          {showConfirmPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Primary CTA Button: Create Account → */}
                  <button
                    type="submit"
                    disabled={submitting || authLoading}
                    className="w-full mt-3 bg-[#B6F23C] hover:bg-[#c4f64d] disabled:bg-[#B6F23C]/40 text-[#07110D] font-extrabold text-sm py-3.5 rounded-2xl transition-all shadow-[0_0_20px_rgba(182,242,60,0.35)] hover:shadow-[0_0_30px_rgba(182,242,60,0.55)] active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer min-h-[48px]"
                  >
                    {submitting ? (
                      <>
                        <span className="w-4 h-4 border-2 border-[#07110D] border-t-transparent rounded-full animate-spin" />
                        <span>Creating Account...</span>
                      </>
                    ) : (
                      <>
                        <span>Create Account</span>
                        <ArrowRight className="w-4 h-4 stroke-[2.5]" />
                      </>
                    )}
                  </button>
                </form>

                {/* Divider: ── or ── */}
                <div className="relative my-4 flex items-center justify-center">
                  <div className="w-full border-t border-[#1C3B29]" />
                  <span className="bg-[#07130E] px-3 text-xs text-[#BAC8C1]/60 uppercase tracking-widest font-semibold absolute">
                    or
                  </span>
                </div>

                {/* WhatsApp CTA Button */}
                <button
                  type="button"
                  onClick={handleWhatsAppSignup}
                  className="w-full bg-[#0B1E15] hover:bg-[#11291E] border border-[#224430] hover:border-[#25D366]/60 text-[#F0FDF4] font-semibold text-xs sm:text-sm py-3 rounded-2xl transition-all flex items-center justify-center gap-2.5 shadow-sm active:scale-[0.99] cursor-pointer min-h-[44px]"
                >
                  <svg className="w-4 h-4 fill-[#25D366]" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12.031 6.172c-3.181 0-5.767 2.586-5.768 5.766-.001 1.298.38 2.27 1.019 3.287l-.582 2.128 2.182-.573c.978.58 1.911.928 3.145.929 3.178 0 5.767-2.587 5.768-5.766.001-3.187-2.575-5.77-5.764-5.771zm3.392 8.244c-.144.405-.837.774-1.17.824-.299.045-.677.063-1.092-.069-.252-.08-.575-.187-.988-.365-1.739-.751-2.874-2.502-2.961-2.617-.087-.116-.708-.94-.708-1.793s.448-1.273.607-1.446c.159-.173.346-.217.462-.217l.332.006c.106.005.249-.04.39.298.144.347.491 1.2.534 1.287.043.087.072.188.014.303-.058.116-.087.188-.173.289l-.26.303c-.087.087-.177.181-.076.355.101.173.449.741.964 1.201.662.591 1.221.774 1.394.861.174.087.275.072.376-.043.101-.116.433-.506.549-.68.116-.173.231-.144.39-.087s1.011.477 1.184.564.289.13.332.202c.043.073.043.419-.101.824z" />
                  </svg>
                  <span>Continue with WhatsApp</span>
                </button>

                {/* Footer Link */}
                <div className="mt-4 text-center text-xs text-[#BAC8C1]">
                  Already have an account?{" "}
                  <Link
                    href="/login"
                    className="text-[#B6F23C] font-bold hover:underline ml-1"
                  >
                    Login
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <div className="min-h-screen bg-[#07110D] text-[#F0FDF4] flex items-center justify-center py-8 sm:py-12 px-4 relative overflow-hidden">
      {/* Background Radial Green Glows */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 w-[550px] h-[550px] bg-[#B6F23C]/10 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[450px] h-[450px] bg-[#10B981]/10 rounded-full blur-[150px] pointer-events-none" />
      <Suspense fallback={<div className="text-center text-[#BAC8C1]">Loading...</div>}>
        <SignupForm />
      </Suspense>
    </div>
  );
}
