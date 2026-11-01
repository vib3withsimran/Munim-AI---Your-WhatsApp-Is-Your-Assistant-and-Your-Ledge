"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
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
  ownerName: string;
  sellerInitial: string;
  login: (
    email: string,
    password: string
  ) => Promise<{ success: boolean; error?: string; verificationRequired?: boolean }>;
  signup: (
    email: string,
    password: string,
    businessName: string,
    ownerName?: string,
    phone?: string,
    businessType?: string
  ) => Promise<{ success: boolean; error?: string; verificationRequired?: boolean }>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ success: boolean; error?: string }>;
  updatePassword: (password: string) => Promise<{ success: boolean; error?: string }>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [supabase] = useState(() => createClient());
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<SellerProfile | null>(null);
  const [loading, setLoading] = useState(true);

  // Background fetch of profile from FastAPI backend
  const fetchProfile = useCallback(async () => {
    try {
      const data = await api.getProfile();
      setProfile(data);
    } catch {
      // Backend unreachable or seller has no profile yet; fall back to auth user metadata
    }
  }, []);

  useEffect(() => {
    let mounted = true;

    // 1. Initial session load
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

    // 2. Listen to Supabase auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      async (event: AuthChangeEvent, newSession: Session | null) => {
        if (!mounted) return;
        setSession(newSession);
        setUser(newSession?.user ?? null);

        if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
          if (newSession) {
            fetchProfile();
          }
        } else if (event === "SIGNED_OUT") {
          setProfile(null);
        }

        setLoading(false);
      }
    );

    // 3. Listen for 401 unauthorized events emitted from api.ts
    const handleUnauthorized = async () => {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        setSession(null);
        setUser(null);
        setProfile(null);
        if (
          typeof window !== "undefined" &&
          !window.location.pathname.startsWith("/login") &&
          !window.location.pathname.startsWith("/signup")
        ) {
          window.location.replace(
            `/login?error=${encodeURIComponent(
              "Session expired. Please sign in again."
            )}`
          );
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

  const login = useCallback(
    async (email: string, password: string) => {
      try {
        const cleanEmail = email.trim().toLowerCase();
        const { data, error } = await supabase.auth.signInWithPassword({
          email: cleanEmail,
          password,
        });

        if (error) {
          const msg = error.message.toLowerCase();
          if (
            msg.includes("email not confirmed") ||
            msg.includes("not confirmed")
          ) {
            return {
              success: false,
              verificationRequired: true,
              error:
                "Email verification required. Please check your inbox and verify your email before logging in.",
            };
          }
          if (
            msg.includes("invalid login credentials") ||
            msg.includes("invalid credentials")
          ) {
            return {
              success: false,
              error:
                "Invalid email or password. Please verify your credentials and try again.",
            };
          }
          return { success: false, error: error.message };
        }

        setSession(data.session);
        setUser(data.user);
        fetchProfile().catch(() => {});

        return { success: true };
      } catch (err: unknown) {
        const errorMsg =
          err instanceof Error ? err.message : "An unexpected login error occurred";
        return { success: false, error: errorMsg };
      }
    },
    [supabase, fetchProfile]
  );

  const signup = useCallback(
    async (
      email: string,
      password: string,
      businessName: string,
      ownerName?: string,
      phone?: string,
      businessType?: string
    ) => {
      try {
        const cleanEmail = email.trim().toLowerCase();
        const redirectUrl =
          typeof window !== "undefined"
            ? `${window.location.origin}/auth/callback?next=/dashboard`
            : undefined;

        const { data, error } = await supabase.auth.signUp({
          email: cleanEmail,
          password,
          options: {
            data: {
              business_name: businessName.trim(),
              owner_name: ownerName?.trim() || null,
              your_name: ownerName?.trim() || null,
              phone: phone?.trim() || null,
              business_type: businessType?.trim() || "General Store",
            },
            emailRedirectTo: redirectUrl,
          },
        });

        if (error) {
          return { success: false, error: error.message };
        }

        // Check for duplicate identities
        if (
          data.user &&
          Array.isArray(data.user.identities) &&
          data.user.identities.length === 0
        ) {
          return {
            success: false,
            error: "An account with this email already exists. Please log in.",
          };
        }

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
        const errorMsg =
          err instanceof Error ? err.message : "Signup failed";
        return { success: false, error: errorMsg };
      }
    },
    [supabase, fetchProfile]
  );

  const logout = useCallback(async () => {
    try {
      await api.logoutBackend();
      await supabase.auth.signOut();
    } catch {
      // Ignored: clear client state regardless
    } finally {
      setSession(null);
      setUser(null);
      setProfile(null);
      if (typeof window !== "undefined") {
        window.location.replace("/login");
      }
    }
  }, [supabase]);

  const resetPassword = useCallback(
    async (email: string) => {
      try {
        const redirectUrl =
          typeof window !== "undefined"
            ? `${window.location.origin}/auth/callback?next=/reset-password`
            : undefined;

        const { error } = await supabase.auth.resetPasswordForEmail(
          email.trim().toLowerCase(),
          {
            redirectTo: redirectUrl,
          }
        );

        if (error) {
          return { success: false, error: error.message };
        }
        return { success: true };
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Password reset failed";
        return { success: false, error: msg };
      }
    },
    [supabase]
  );

  const updatePassword = useCallback(
    async (newPassword: string) => {
      try {
        const { error } = await supabase.auth.updateUser({
          password: newPassword,
        });

        if (error) {
          return { success: false, error: error.message };
        }
        return { success: true };
      } catch (err: unknown) {
        const msg =
          err instanceof Error ? err.message : "Failed to update password";
        return { success: false, error: msg };
      }
    },
    [supabase]
  );

  // Derive businessName from profile, user_metadata, or fallback
  const businessName = useMemo(() => {
    return (
      profile?.business_name ||
      (user?.user_metadata?.business_name as string) ||
      ""
    );
  }, [profile, user]);

  // Derive ownerName from user_metadata
  const ownerName = useMemo(() => {
    return (
      (user?.user_metadata?.owner_name as string) ||
      (user?.user_metadata?.your_name as string) ||
      ""
    );
  }, [user]);

  // Compute 2-letter seller initial
  const sellerInitial = useMemo(() => {
    const source = businessName || ownerName;
    if (source) {
      const words = source.trim().split(/\s+/);
      if (words.length >= 2) {
        return `${words[0][0]}${words[1][0]}`.toUpperCase();
      }
      return source.slice(0, 2).toUpperCase();
    }
    return "NC";
  }, [businessName, ownerName]);

  const value = useMemo(
    () => ({
      user,
      session,
      profile,
      loading,
      businessName,
      ownerName,
      sellerInitial,
      login,
      signup,
      logout,
      resetPassword,
      updatePassword,
      refreshProfile: fetchProfile,
    }),
    [
      user,
      session,
      profile,
      loading,
      businessName,
      ownerName,
      sellerInitial,
      login,
      signup,
      logout,
      resetPassword,
      updatePassword,
      fetchProfile,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
