/**
 * Centralized Environment Configuration for Munim AI Frontend
 *
 * Validates required environment variables and provides clear, helpful
 * error messages in development and production if any are missing.
 */

export interface AppEnv {
  supabaseUrl: string;
  supabaseAnonKey: string;
  apiUrl: string;
}

function getEnvVar(key: string, fallback?: string): string {
  const value = process.env[key] || fallback;
  if (!value) {
    if (typeof window !== "undefined") {
      console.error(
        `[Munim AI Configuration Error] Missing environment variable: ${key}.\n` +
          `Please check your frontend/.env.local file or server environment settings.`
      );
    }
    return "";
  }
  return value;
}

export const env: AppEnv = {
  get supabaseUrl(): string {
    return getEnvVar(
      "NEXT_PUBLIC_SUPABASE_URL",
      "https://yomqkdgofwsmzrpbxxag.supabase.co"
    );
  },
  get supabaseAnonKey(): string {
    return (
      getEnvVar("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY") ||
      getEnvVar("NEXT_PUBLIC_SUPABASE_ANON_KEY") ||
      "sb_publishable_0GCSSdcJzjRl7mu8ZBq33g_nhq2Yncm"
    );
  },
  get apiUrl(): string {
    return (
      getEnvVar("NEXT_PUBLIC_API_URL") ||
      getEnvVar("NEXT_PUBLIC_API_BASE_URL") ||
      "http://localhost:8000"
    );
  },
};

export function validateConfig(): { valid: boolean; missing: string[] } {
  const missing: string[] = [];
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
    missing.push("NEXT_PUBLIC_SUPABASE_URL");
  }
  if (
    !process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY &&
    !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  ) {
    missing.push("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY");
  }
  return {
    valid: missing.length === 0,
    missing,
  };
}

