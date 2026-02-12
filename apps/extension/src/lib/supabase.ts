// Supabase client is no longer used for authentication.
// This file is kept as a dummy to avoid breaking imports during migration.
// Extension now uses JWT tokens synced from the web app.

export const supabase = {
    auth: {
        getSession: async () => ({ data: { session: null }, error: null }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => { } } } }),
        signOut: async () => { },
        setSession: async () => ({ data: { session: null }, error: null }),
    }
} as any;
