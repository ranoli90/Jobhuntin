import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL ?? "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ?? "";


// Validate Supabase configuration
const isSupabaseConfigured = supabaseUrl && supabaseAnonKey;

if (!isSupabaseConfigured) {
  console.warn(
    "Supabase configuration missing. VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are not set. Supabase features will be disabled."
  );
}

// Export a safe client that warns on use if not configured
export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
    },
  })
  : new Proxy(
    {},
    {
      get: (_target, prop) => {
        // Allow internal properties to avoid crashes
        if (typeof prop === 'string' && prop === 'then') return undefined;

        return (...args: any[]) => {
          console.error(
            `Attempted to call Supabase.${String(prop)} but Supabase is not configured.`
          );
          return Promise.reject(new Error("Supabase is not configured"));
        };
      },
    }
  ) as ReturnType<typeof createClient>;
