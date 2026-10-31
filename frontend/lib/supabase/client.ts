import { createBrowserClient } from "@supabase/ssr";

let client: ReturnType<typeof createBrowserClient> | null = null;

export function createClient() {
  const url =
    process.env.NEXT_PUBLIC_SUPABASE_URL ||
    "https://yomqkdgofwsmzrpbxxag.supabase.co";
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    "sb_publishable_0GCSSdcJzjRl7mu8ZBq33g_nhq2Yncm";

  if (typeof window === "undefined") {
    return createBrowserClient(url, key);
  }

  if (!client) {
    client = createBrowserClient(url, key, {
      isSingleton: true,
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  }

  return client;
}
