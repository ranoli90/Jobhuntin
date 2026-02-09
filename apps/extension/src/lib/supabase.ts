import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
    console.error("Missing Supabase URL or Anon Key")
}

const storageAdapter = {
    getItem: async (key: string) => {
        const result = await chrome.storage.local.get(key)
        return (result[key] as string) || null
    },
    setItem: async (key: string, value: string) => {
        await chrome.storage.local.set({ [key]: value })
    },
    removeItem: async (key: string) => {
        await chrome.storage.local.remove(key)
    },
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
        storage: storageAdapter,
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
    },
})
