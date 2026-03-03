import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { apiGet, getApiBase } from "../lib/api";
import { pushToast } from "../lib/toast";

/* eslint-disable @typescript-eslint/no-explicit-any */

// LS5: Magic link tokens are one-time; no refresh flow. User re-authenticates via new magic link when session expires.

export interface User {
    id: string;
    email: string;
    has_completed_onboarding: boolean;
    resume_url?: string;
    preferences?: Record<string, any>;
    contact?: Record<string, any>;
    headline?: string;
    bio?: string;
    role?: 'user' | 'admin' | 'superadmin';
}

interface AuthContextType {
    user: User | null;
    loading: boolean;
    signInWithMagicLink: (email: string, returnTo?: string) => Promise<{ error: Error | null }>;
    signOut: () => Promise<void>;
    updateUser: (updates: Partial<User>) => void; // Optimistic update
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    signInWithMagicLink: async () => ({ error: null }),
    signOut: async () => { },
    updateUser: () => { },
    refreshUser: async () => { },
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Helper to fetch user profile
    const fetchUser = useCallback(async () => {
        if (import.meta.env.DEV) console.log('[AUTH] Fetching user profile...');
        try {
            const profile = await apiGet<User>("/profile");
            setUser(profile);
            if (import.meta.env.DEV) {
                console.log('[AUTH] User profile loaded:', {
                    id: profile.id,
                    email: profile.email,
                    has_completed_onboarding: profile.has_completed_onboarding
                });
            }

            // Sync extension session state
            localStorage.setItem('jobhuntin-session', JSON.stringify({
                logged_in: true,
                ts: Date.now(),
            }));
        } catch (error) {
            console.error("[AUTH] Failed to fetch user profile:", error);
            // If 401, apiGet handles redirect, but we should clear state
            setUser(null);
            // Store the current URL to redirect back after re-auth
            const returnTo = globalThis.window.location.pathname + globalThis.window.location.search;
            sessionStorage.setItem('returnTo', returnTo);
            // Show user-facing error with redirect option
            const msg = error instanceof Error ? error.message : "Your session has expired";
            pushToast({ title: "Session expired", description: `${msg}. Please sign in again.`, tone: "error" });
            // Redirect to login after short delay
            setTimeout(() => {
                globalThis.window.location.href = '/login';
            }, 2000);
        }
    }, []);

    const ensureCsrfCookie = useCallback(async () => {
        try {
            const base = getApiBase();
            if (!base) return;
            await fetch(`${base.replace(/\/$/, "")}/csrf/prepare`, { credentials: "include" });
        } catch (err) {
            console.warn("CSRF cookie preflight failed", err);
        }
    }, []);

    // Initialize auth
    useEffect(() => {
        const initAuth = async () => {
            if (import.meta.env.DEV) console.log('[AUTH] Initializing auth...');

            // 1. Check for token in URL (Magic Link flow)
            const params = new URLSearchParams(window.location.search);
            const tokenFromUrl = params.get("token");

            if (tokenFromUrl) {
                if (import.meta.env.DEV) console.log('[AUTH] Token found in URL, processing magic link')
                
                // Preserve returnTo before cleaning URL (for magic link flow without api_public_url)
                const returnToFromUrl = params.get("returnTo");
                if (returnToFromUrl) {
                    sessionStorage.setItem('magicLinkReturnTo', returnToFromUrl);
                    if (import.meta.env.DEV) console.log('[AUTH] Stored returnTo from URL:', returnToFromUrl);
                }
                
                // NOTE: Token is now exchanged for httpOnly cookie by the backend.
                // The backend /auth/verify-magic endpoint sets the cookie and redirects.
                // If we receive a token here, it means we're using the legacy flow.
                // We'll send it to the backend to exchange for a cookie.
                try {
                    const base = getApiBase();
                    if (base) {
                        // Exchange token for httpOnly cookie
                        await fetch(`${base.replace(/\/$/, "")}/auth/verify-magic?token=${encodeURIComponent(tokenFromUrl)}`, {
                            credentials: 'include',
                        });
                    }
                } catch (e) {
                    console.error('[AUTH] Failed to exchange token for cookie:', e);
                }
                
                // Clean URL - remove token and returnTo query params but preserve other params
                const searchParams = new URLSearchParams(window.location.search);
                searchParams.delete("token");
                searchParams.delete("returnTo");
                const newSearch = searchParams.toString();
                const newUrl = window.location.pathname + (newSearch ? `?${newSearch}` : '') + window.location.hash;
                window.history.replaceState({}, document.title, newUrl);
                if (import.meta.env.DEV) console.log('[AUTH] URL cleaned, fetching CSRF cookie and user profile');
                await ensureCsrfCookie();
                await fetchUser();
                if (import.meta.env.DEV) console.log('[AUTH] Magic link auth complete');
            } else {
                // 2. Check for existing session via httpOnly cookie
                // The /profile endpoint will return 401 if no valid cookie
                if (import.meta.env.DEV) console.log('[AUTH] Checking for existing session via httpOnly cookie');
                await ensureCsrfCookie();
                await fetchUser();
            }
                
                setAuthToken(tokenFromUrl);
                // Clean URL - remove token and returnTo query params but preserve other params
                const searchParams = new URLSearchParams(window.location.search);
                searchParams.delete("token");
                searchParams.delete("returnTo");
                const newSearch = searchParams.toString();
                const newUrl = window.location.pathname + (newSearch ? `?${newSearch}` : '') + window.location.hash;
                window.history.replaceState({}, document.title, newUrl);
                if (import.meta.env.DEV) console.log('[AUTH] URL cleaned, fetching CSRF cookie and user profile');
                await ensureCsrfCookie();
                await fetchUser();
                if (import.meta.env.DEV) console.log('[AUTH] Magic link auth complete');
            } else {
                // 2. Check local storage
                const token = getAuthToken();
                if (token) {
                    if (import.meta.env.DEV) console.log('[AUTH] Token found in localStorage, refreshing session');
                    await ensureCsrfCookie();
                    await fetchUser();
                } else {
                    if (import.meta.env.DEV) console.log('[AUTH] No token found, user is unauthenticated');
                    localStorage.removeItem('jobhuntin-session');
                }
            }
            setLoading(false);
            if (import.meta.env.DEV) console.log('[AUTH] Auth initialization complete');
        };

        const handleUnauthorized = (event: Event) => {
            if (import.meta.env.DEV) console.log('[AUTH] Unauthorized event received, clearing session');
            const detail = (event as CustomEvent<{ returnTo?: string }>).detail;
            setUser(null);
            sessionStorage.setItem('session_expired', 'true');
            const returnTo = detail?.returnTo ?? encodeURIComponent(window.location.pathname + window.location.search);
            window.location.href = `/login?returnTo=${returnTo}`;
        };

        window.addEventListener("auth:unauthorized", handleUnauthorized as EventListener);
        initAuth();

        return () => {
            window.removeEventListener("auth:unauthorized", handleUnauthorized as EventListener);
        };
    }, [ensureCsrfCookie, fetchUser]);

    const signInWithMagicLink = async (email: string, returnTo = "/app/onboarding") => {
        try {
            const { magicLinkService } = await import("../services/magicLinkService");
            const res = await magicLinkService.sendMagicLink(email, returnTo);
            if (!res.success) {
                return { error: new Error(res.error || "Failed to send magic link") };
            }
            return { error: null };
        } catch (error) {
            return { error: error as Error };
        }
    };

    const signOut = async () => {
        setUser(null);
        // S1: Redirect to API logout to clear httpOnly cookie, then to /login
        const base = getApiBase();
        if (base) {
            window.location.href = `${base.replace(/\/$/, "")}/auth/logout`;
        } else {
            window.location.href = "/login";
        }
    };

    const updateUser = (updates: Partial<User>) => {
        if (user) {
            setUser({ ...user, ...updates });
        }
    };

    const refreshUser = async () => {
        await fetchUser();
    };

    return (
        <AuthContext.Provider value={{ user, loading, signInWithMagicLink, signOut, updateUser, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuthContext = () => useContext(AuthContext);
