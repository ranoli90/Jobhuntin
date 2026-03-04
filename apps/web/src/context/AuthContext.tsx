import { createContext, useContext, useEffect, useState, ReactNode, useCallback, useRef } from "react";
import { apiGet, getApiBase } from "../lib/api";
import { pushToast } from "../lib/toast";

/* eslint-disable @typescript-eslint/no-explicit-any */

// LS5: Magic link tokens are one-time; no refresh flow. User re-authenticates via new magic link when session expires.

// Session warning threshold (5 minutes before expiry)
const SESSION_WARNING_THRESHOLD_MS = 5 * 60 * 1000;

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
    const sessionExpiryRef = useRef<number | null>(null);
    const warningShownRef = useRef(false);

    // Helper to fetch user profile
    const fetchUser = useCallback(async (isInitialLoad = false) => {
        if (import.meta.env.DEV) console.log('[AUTH] Fetching user profile...');
        try {
            let profile: User;

            if (isInitialLoad) {
                // On initial load, use a direct fetch that does NOT dispatch auth:unauthorized
                // on 401. apiGet() dispatches the event BEFORE the error reaches this catch block,
                // causing an unwanted redirect + "session expired" toast on first visit.
                const base = getApiBase();
                const resp = await fetch(`${base.replace(/\/$/, "")}/profile`, {
                    method: "GET",
                    credentials: "include",
                    headers: { "Content-Type": "application/json" },
                });
                if (!resp.ok) {
                    // Silently handle 401 on initial load — user simply isn't logged in yet
                    if (import.meta.env.DEV) console.log('[AUTH] Initial profile check returned', resp.status);
                    setUser(null);
                    sessionExpiryRef.current = null;
                    return;
                }
                profile = await resp.json();
            } else {
                // Subsequent calls (e.g. refreshUser) — use apiGet which has retry + error handling
                profile = await apiGet<User>("/profile");
            }

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

            // Set session expiry (1 hour from now, matching backend)
            sessionExpiryRef.current = Date.now() + 60 * 60 * 1000;
            warningShownRef.current = false;
        } catch (error) {
            console.error("[AUTH] Failed to fetch user profile:", error);
            // Clear user state
            setUser(null);
            sessionExpiryRef.current = null;

            // Only show toast and redirect if this is not the initial load
            // (user had a session that expired) or if we're not already on the login page
            const isLoginPage = window.location.pathname === '/login';
            if (!isInitialLoad && !isLoginPage) {
                const msg = error instanceof Error ? error.message : "Your session has expired";
                pushToast({ title: "Session expired", description: `${msg}. Please sign in again.`, tone: "error" });
                // Store the current URL to redirect back after re-auth
                const returnTo = window.location.pathname + window.location.search;
                sessionStorage.setItem('returnTo', returnTo);
                // Redirect to login after short delay
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            }
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

    // Session expiration warning
    useEffect(() => {
        const checkSessionExpiry = () => {
            if (!sessionExpiryRef.current || warningShownRef.current) return;

            const timeUntilExpiry = sessionExpiryRef.current - Date.now();

            if (timeUntilExpiry <= 0) {
                // Session expired
                warningShownRef.current = true;
                pushToast({
                    title: "Session expired",
                    description: "Your session has expired. Please sign in again.",
                    tone: "error",
                });
            } else if (timeUntilExpiry <= SESSION_WARNING_THRESHOLD_MS) {
                // Show warning
                warningShownRef.current = true;
                const minutesLeft = Math.ceil(timeUntilExpiry / 60000);
                pushToast({
                    title: "Session expiring soon",
                    description: `Your session will expire in ${minutesLeft} minute${minutesLeft > 1 ? 's' : ''}. Save any work and refresh the page to extend your session.`,
                    tone: "warning",
                });
            }
        };

        // Check every minute
        const interval = setInterval(checkSessionExpiry, 60000);

        // Also check on user activity
        const handleActivity = () => checkSessionExpiry();
        window.addEventListener('click', handleActivity);
        window.addEventListener('keypress', handleActivity);

        return () => {
            clearInterval(interval);
            window.removeEventListener('click', handleActivity);
            window.removeEventListener('keypress', handleActivity);
        };
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
                await fetchUser(true); // Pass true - don't auto-redirect on error
                if (import.meta.env.DEV) console.log('[AUTH] Magic link auth complete');
            } else {
                // 2. Check for existing session via httpOnly cookie
                // The /profile endpoint will return 401 if no valid cookie
                if (import.meta.env.DEV) console.log('[AUTH] Checking for existing session via httpOnly cookie');
                await ensureCsrfCookie();
                await fetchUser(true); // Pass true for initial load - don't redirect if no session
            }
            setLoading(false);
            if (import.meta.env.DEV) console.log('[AUTH] Auth initialization complete');
        };

        const handleUnauthorized = (event: Event) => {
            if (import.meta.env.DEV) console.log('[AUTH] Unauthorized event received, clearing session');
            const detail = (event as CustomEvent<{ returnTo?: string }>).detail;
            setUser(null);
            sessionExpiryRef.current = null;
            sessionStorage.setItem('session_expired', 'true');
            // Don't redirect if already on the login page — prevents infinite redirect loop
            if (window.location.pathname === '/login') return;
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
        sessionExpiryRef.current = null;
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
