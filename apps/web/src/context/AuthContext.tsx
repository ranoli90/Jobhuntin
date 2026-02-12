import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { apiGet, clearAuthToken, getAuthToken, setAuthToken } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */

export interface User {
    id: string;
    email: string;
    has_completed_onboarding: boolean;
    resume_url?: string;
    preferences?: Record<string, any>;
    contact?: Record<string, any>;
    headline?: string;
    bio?: string;
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
        try {
            const profile = await apiGet<User>("/profile");
            setUser(profile);

            // Sync extension session state
            localStorage.setItem('jobhuntin-session', JSON.stringify({
                logged_in: true,
                ts: Date.now(),
            }));
        } catch (error) {
            console.error("Failed to fetch user profile:", error);
            // If 401, apiGet handles redirect, but we should clear state
            clearAuthToken();
            setUser(null);
            localStorage.removeItem('jobhuntin-session');
        }
    }, []);

    // Initialize auth
    useEffect(() => {
        const initAuth = async () => {
            // 1. Check for token in URL (Magic Link flow)
            const params = new URLSearchParams(window.location.search);
            const tokenFromUrl = params.get("token");

            if (tokenFromUrl) {
                setAuthToken(tokenFromUrl);
                // Clean URL
                const newUrl = window.location.pathname + window.location.hash;
                window.history.replaceState({}, document.title, newUrl);
                await fetchUser();
            } else {
                // 2. Check local storage
                const token = getAuthToken();
                if (token) {
                    await fetchUser();
                } else {
                    localStorage.removeItem('jobhuntin-session');
                }
            }
            setLoading(false);
        };

        initAuth();
    }, [fetchUser]);

    const signInWithMagicLink = async (email: string, returnTo = "/app/onboarding") => {
        try {
            const { magicLinkService } = await import("../services/magicLinkService");
            const res = await magicLinkService.sendMagicLink(email, returnTo);
            if (!res.success) {
                return { error: new Error(res.error || "Failed to send magic link") };
            }
            return { error: null };
        } catch (err: any) {
            return { error: err };
        }
    };

    const signOut = async () => {
        clearAuthToken();
        setUser(null);
        localStorage.removeItem('jobhuntin-session');
        window.location.href = "/login";
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
