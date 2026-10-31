"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { User, Session, AuthChangeEvent } from "@supabase/supabase-js";
import { createClient } from "@/lib/supabase/client";
import { api, SellerProfile } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: SellerProfile | null;
  loading: boolean;
  businessName: string;
  sellerInitial: string;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string; verificationRequired?: boolean }>;
  signup: (
    email: string,
    password: string,
    businessName: string,
    phone?: string,
    businessType?: string
  ) => Promise<{ success: boolean; error?: string; verificationRequired?: boolean }>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [supabase] = useState(() => createClient());
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<SellerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    try {
      const data = await api.getProfile();
      setProfile(data);
    } catch {
      // Background profile fetch failed or backend unreachable; fallback to metadata
    }
  }, []);

  useEffect(() => {
    let mounted = true;

    // 1. Get initial session
    supabase.auth.getSession().then((res: { data: { session: Session | null } }) => {
      if (!mounted) return;
      const initialSession = res.data.session;
      setSession(initialSession);
      setUser(initialSession?.user ?? null);
      if (initialSession) {
        fetchProfile();
      }
      setLoading(false);
    });

    // 2. Listen for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event: AuthChangeEvent, newSession: Session | null) => {
      if (!mounted) return;
      setSession(newSession);
      setUser(newSession?.user ?? null);
      if (newSession) {
        fetchProfile();
      } else {
        setProfile(null);
      }
      setLoading(false);
    });

    // 3. Listen for 401 unauthorized events
    const handleUnauthorized = async () => {
      // Check if session really expired before signing out
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        setSession(null);
        setUser(null);
        setProfile(null);
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          window.location.href = "/login?error=Session expired. Please sign in again.";
        }
      }
    };

    window.addEventListener("munim:unauthorized", handleUnauthorized);

    return () => {
      mounted = false;
      subscription.unsubscribe();
      window.removeEventListener("munim:unauthorized", handleUnauthorized);
    };
  }, [supabase, fetchProfile]);

  const login = async (email: string, password: string) => {
    try {
      const cleanEmail = email.trim();
      const { data, error } = await supabase.auth.signInWithPassword({
        email: cleanEmail,
        password,
      });

      if (error) {
        const msg = error.message.toLowerCase();
        if (msg.includes("email not confirmed") || msg.includes("not confirmed")) {
          return {
            success: false,
            verificationRequired: true,
            error: "Email verification required. Please check your inbox and verify your email before logging in.",
          };
        }
        if (msg.includes("invalid login credentials") || msg.includes("invalid credentials")) {
          return {
            success: false,
            error: "Invalid email or password. Please verify your credentials and try again.",
          };
        }
        return { success: false, error: error.message };
      }

      // Successful login
      setSession(data.session);
      setUser(data.user);

      // Trigger profile load in background (non-blocking)
      fetchProfile().catch(() => {});

      return { success: true };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "An unexpected login error occurred";
      return { success: false, error: errorMsg };
    }
  };

  const signup = async (
    email: string,
    password: string,
    businessName: string,
    phone?: string,
    businessType?: string
  ) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: {
            business_name: businessName.trim(),
            phone: phone?.trim() || null,
            business_type: businessType?.trim() || null,
          },
        },
      });

      if (error) {
        return { success: false, error: error.message };
      }

      // With email confirmation enabled, session is null
      const verificationRequired = !data.session;

      if (data.session) {
        setSession(data.session);
        setUser(data.user);
        fetchProfile().catch(() => {});
      }

      return {
        success: true,
        verificationRequired,
      };
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : "Signup failed";
      return { success: false, error: errorMsg };
    }
  };

  const logout = async () => {
    try {
      const token = session?.access_token;
      if (token) {
        fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => {});
      }
    } catch {
      // Ignore background logout network errors
    } finally {
      await supabase.auth.signOut();
      setSession(null);
      setUser(null);
      setProfile(null);
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
  };

  const businessName =
    profile?.business_name ||
    user?.user_metadata?.business_name ||
    (user?.email ? user.email.split("@")[0] : "Seller");

  const sellerInitial = businessName ? businessName[0].toUpperCase() : "M";

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        profile,
        loading,
        businessName,
        sellerInitial,
        login,
        signup,
        logout,
        refreshProfile: fetchProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
