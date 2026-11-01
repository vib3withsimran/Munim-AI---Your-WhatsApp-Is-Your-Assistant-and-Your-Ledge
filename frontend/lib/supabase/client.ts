import { createBrowserClient } from "@supabase/ssr";
import { env } from "@/lib/env";

let browserClient: ReturnType<typeof createBrowserClient> | null = null;

/**
 * Returns a singleton Supabase client for the browser.
 * Ensures consistent session persistence and prevents redundant client creation.
 */
export function createClient() {
  if (typeof window === "undefined") {
    return createBrowserClient(env.supabaseUrl, env.supabaseAnonKey);
  }

  if (!browserClient) {
    browserClient = createBrowserClient(env.supabaseUrl, env.supabaseAnonKey, {
      isSingleton: true,
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  }

  return browserClient;
}
