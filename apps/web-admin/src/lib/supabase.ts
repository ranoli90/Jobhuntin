import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "http://localhost:54321";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "";

// Validate Supabase configuration
if (!import.meta.env.VITE_SUPABASE_URL) {
  console.warn(
    "VITE_SUPABASE_URL not set, falling back to local Supabase CLI (http://localhost:54321). " +
    "Set VITE_SUPABASE_URL in your .env file for production."
  );
}

if (!supabaseAnonKey) {
  console.warn(
    "VITE_SUPABASE_ANON_KEY not set. Supabase client may not function correctly. " +
    "Set VITE_SUPABASE_ANON_KEY in your .env file."
  );
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
